from datetime import timedelta
from urllib import request
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q, Count, F, Case, When, Value, IntegerField
from rest_framework import generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import (
    Comment, Group, GroupMembership, Post, ChatSettings, Message, Contest, ContestEntry, ContestVote,
    GroupChat, ChatRole, ChatMember, ChatAdminLog, PrivateChat, ChatTypingStatus, PrivateChatUserSettings,
    Follow, PostLike, PostDislike, Repost, Achievement, UserAchievement, UploadedFile, Favorite,
    ChatInvite, Reaction, Attachment, EmailLog, ChatFolder, ChatFolderChat,
    PostMedia, PostAttachment, PostComment, PostCommentLike, PostCommentDislike,
    FeedView, Bookmark, Report, Hashtag, PostHashtag, UserMention
)
from .models import MessageReadStatus
from rest_framework.pagination import PageNumberPagination
from .serializers import FeedPostSerializer
from users.models import User
from .serializers import (
    CommentSerializer, CommentCreateSerializer,
    GroupSerializer, GroupCreateSerializer, GroupMembershipSerializer,
    PostSerializer, PostCreateSerializer,
    ChatSettingsSerializer,
    MessageSerializer,
    ContestSerializer, ContestEntrySerializer, ContestVoteSerializer,
    GroupChatSerializer, GroupChatCreateSerializer, ChatRoleSerializer, ChatMemberSerializer, ChatAdminLogSerializer,
    PrivateChatSerializer, PrivateChatUserSettingsSerializer,
    FollowSerializer, PostLikeSerializer, PostDislikeSerializer, RepostSerializer,
    AchievementSerializer, UserAchievementSerializer, UploadedFileSerializer, FavoriteSerializer,
    ChatInviteSerializer, ChatInviteCreateSerializer,
    ReactionSerializer, ReactionCreateSerializer,
    AttachmentSerializer, AttachmentCreateSerializer,
    EmailLogSerializer, EmailLogCreateSerializer,
    ChatFolderSerializer, ChatFolderCreateSerializer, ChatFolderPreviewSerializer,
    FeedPostSerializer, PostMediaSerializer, PostAttachmentSerializer, PostCommentSerializer,
    PostCommentCreateSerializer, BookmarkSerializer, BookmarkCreateSerializer,
    ReportSerializer, ReportCreateSerializer, HashtagSerializer
)
from .permissions import IsChatOwner, HasChatPermission, IsChatMember
from core.redis_events import publish_post_created, publish_message_sent, publish_user_online, publish_user_offline
from notifications.services import notification_service
from .serializers import FeedPostSerializer

# ==================== UNREAD CHATS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_chats(request):
    """Получить чаты с непрочитанными сообщениями (из БД)"""
    from .models import MessageReadStatus

    try:
        user = request.user
        chats_data = []

        # Получаем ID чатов, где пользователь участник
        member_chat_ids = ChatMember.objects.filter(user=user).values_list('chat_id', flat=True)
        private_chat_ids = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).values_list('id', flat=True)

        # Получаем все сообщения, отправленные НЕ пользователем
        unread_message_chats = Message.objects.filter(
            Q(chat_id__in=member_chat_ids) | Q(private_chat_id__in=private_chat_ids)
        ).exclude(sender=user)

        # Исключаем уже прочитанные
        read_message_ids = MessageReadStatus.objects.filter(user=user).values_list('message_id', flat=True)
        unread_message_chats = unread_message_chats.exclude(id__in=read_message_ids)

        # Группируем по чатам
        unread_by_chat = {}
        for msg in unread_message_chats.select_related('chat', 'private_chat'):
            if msg.chat_id:
                chat_id = msg.chat_id
                chat_type = 'group'
            else:
                chat_id = msg.private_chat_id
                chat_type = 'private'
            
            if chat_id not in unread_by_chat:
                unread_by_chat[chat_id] = {'type': chat_type, 'count': 0}
            unread_by_chat[chat_id]['count'] += 1

        # Получаем данные чатов
        for chat_id, data in unread_by_chat.items():
            if data['type'] == 'group':
                chat = GroupChat.objects.filter(id=chat_id).first()
                if chat:
                    chats_data.append({
                        'id': chat.id,
                        'type': 'group',
                        'name': chat.name,
                        'avatar_url': chat.avatar.url if chat.avatar else None,
                        'unread_count': data['count']
                    })
            else:
                chat = PrivateChat.objects.filter(id=chat_id).first()
                if chat:
                    other_user = chat.user1 if chat.user2 == user else chat.user2
                    chats_data.append({
                        'id': chat.id,
                        'type': 'private',
                        'name': other_user.display_name or other_user.username,
                        'avatar_url': other_user.avatar.url if other_user.avatar else None,
                        'unread_count': data['count']
                    })

        return Response(chats_data)
    except Exception as e:
        print(f"DEBUG: Ошибка get_unread_chats: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_chat_read(request, chat_id):
    """Отметить чат как прочитанный (через БД)"""
    return _mark_chat_as_read(request, chat_id)


def _mark_chat_as_read(request, chat_id):
    """Внутренняя функция для отметки чата как прочитанного (через БД)"""
    try:
        user = request.user

        # Пробуем групповой чат
        chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
        if chat:
            # Создаём статусы прочтения для всех непрочитанных сообщений
            unread_messages = Message.objects.filter(
                chat=chat
            ).exclude(
                Q(sender=user) | 
                Q(read_statuses__user=user)
            )
            
            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))
            
            if read_statuses:
                MessageReadStatus.objects.bulk_create(read_statuses, ignore_conflicts=True)
            
            # Отправляем WebSocket событие
            try:
                from core.redis_events import event_publisher
                event_publisher.publish_event('unread_count_updated', {
                    'chat_id': chat_id,
                    'chat_type': 'group',
                    'user_id': user.id
                })
            except Exception as ws_err:
                print(f"DEBUG: Error sending WS event: {ws_err}")
            
            return Response({'message': 'Групповой чат отмечен как прочитанный'})
        
        # Пробуем личный чат
        private_chat = PrivateChat.objects.filter(
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        ).first()
        
        if private_chat:
            # Создаём статусы прочтения для всех непрочитанных сообщений
            unread_messages = Message.objects.filter(
                private_chat=private_chat
            ).exclude(
                Q(sender=user) | 
                Q(read_statuses__user=user)
            )

            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))
            
            if read_statuses:
                MessageReadStatus.objects.bulk_create(read_statuses, ignore_conflicts=True)
            
            # Отправляем WebSocket событие
            try:
                from core.redis_events import event_publisher
                event_publisher.publish_event('unread_count_updated', {
                    'chat_id': chat_id,
                    'chat_type': 'private',
                    'user_id': user.id
                })
            except Exception as ws_err:
                print(f"DEBUG: Error sending WS event: {ws_err}")
            
            return Response({'message': 'Личный чат отмечен как прочитанный'})
        
        return Response({'error': 'Чат не найден'}, status=404)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_private_chat_read(request, chat_id):
    """Отметить личный чат как прочитанный"""
    # Просто вызываем ту же логику, что и в mark_chat_read
    return _mark_chat_as_read(request, chat_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_group_chat_read(request, chat_id):
    """Отметить групповой чат как прочитанный"""
    # Просто вызываем ту же логику, что и в mark_chat_read
    return _mark_chat_as_read(request, chat_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Получить общее количество непрочитанных сообщений (из БД)"""
    from django.db.models import Count, Q, OuterRef, Exists
    
    try:
        user = request.user
        chat_id = request.query_params.get('chat_id')
        
        if chat_id:
            # Получаем непрочитанные для конкретного чата
            unread_count = 0
            
            # Пробуем групповой чат
            chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
            if chat:
                unread_count = Message.objects.filter(
                    chat=chat
                ).exclude(
                    Q(sender=user) | 
                    Q(read_statuses__user=user)
                ).count()
            else:
                # Пробуем личный чат
                private_chat = PrivateChat.objects.filter(
                    Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
                ).first()
                if private_chat:
                    unread_count = Message.objects.filter(
                        private_chat=private_chat
                    ).exclude(
                        Q(sender=user) | 
                        Q(read_statuses__user=user)
                    ).count()
            
            return Response({'unread_count': unread_count})
        else:
            # Общее количество непрочитанных
            # Групповые чаты
            group_unread = Message.objects.filter(
                chat__members__user=user
            ).exclude(
                Q(sender=user) | 
                Q(read_statuses__user=user)
            ).distinct().count()
            
            # Личные чаты
            private_unread = Message.objects.filter(
                private_chat__user1=user
            ).exclude(
                Q(sender=user) | 
                Q(read_statuses__user=user)
            ).distinct().count()
            
            private_unread2 = Message.objects.filter(
                private_chat__user2=user
            ).exclude(
                Q(sender=user) | 
                Q(read_statuses__user=user)
            ).distinct().count()
            
            total_unread = group_unread + private_unread + private_unread2
            
            return Response({'unread_count': total_unread})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'unread_count': 0, 'error': str(e)})


class CombinedChatsView(generics.ListAPIView):
    """Объединенный список всех чатов пользователя"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает пустой queryset, так как мы формируем данные вручную"""
        return GroupChat.objects.none()

    def list(self, request):
        """Получить все чаты пользователя (групповые и личные)"""
        user = request.user
        chats_data = []

        try:
            # Групповые чаты пользователя
            group_chats = GroupChat.objects.filter(
                members__user=user
            ).select_related('created_by').prefetch_related('members__user')

            # Добавляем групповые чаты
            for chat in group_chats:
                # Получаем последнее сообщение
                try:
                    last_message = Message.objects.filter(chat=chat).order_by('-created_at').first()
                except:
                    last_message = None

                chat_data = {
                    'id': chat.id,
                    'type': 'group',
                    'name': chat.name,
                    'avatar_url': chat.avatar.url if chat.avatar else None,
                    'participants_usernames': [member.user.username for member in chat.members.all()],
                    'last_message_text': last_message.text if last_message else None,
                    'last_message_sender': last_message.sender.username if last_message else None,
                    'updated_at': chat.created_at.isoformat(),  # Используем created_at
                    'created_at': chat.created_at.isoformat()
                }
                chats_data.append(chat_data)
                
                print(f"DEBUG: Добавлен групповой чат {chat.id}: {chat.name}")
        except Exception as e:
            print(f"DEBUG: Ошибка при получении групповых чатов: {e}")

        try:
            # Личные чаты пользователя
            private_chats = PrivateChat.objects.filter(
                Q(user1=user) | Q(user2=user)
            ).select_related('user1', 'user2')

            # Импортируем online_status
            from core.online_status import online_status

            # Добавляем личные чаты
            for chat in private_chats:
                other_user = chat.user1 if chat.user2 == user else chat.user2

                # Проверяем онлайн статус через Redis
                is_online = online_status.is_online(other_user.id)

                # Получаем кастомные настройки пользователя
                try:
                    user_settings = PrivateChatUserSettings.objects.get(chat=chat, user=user)
                    custom_name = user_settings.custom_name
                    custom_avatar = user_settings.custom_avatar.url if user_settings.custom_avatar else None
                except PrivateChatUserSettings.DoesNotExist:
                    custom_name = None
                    custom_avatar = None

                # Получаем последнее сообщение
                try:
                    last_message = Message.objects.filter(private_chat=chat).order_by('-created_at').first()
                except:
                    last_message = None

                chat_data = {
                    'id': chat.id,
                    'type': 'private',
                    'name': custom_name,  # Кастомное название пользователя
                    'avatar_url': custom_avatar or (other_user.avatar.url if other_user.avatar else None),
                    'participants_usernames': [other_user.username],
                    'other_user': {
                        'id': other_user.id,
                        'username': other_user.username,
                        'display_name': other_user.display_name or other_user.username,
                        'avatar': other_user.avatar.url if other_user.avatar else None,
                        'is_online': is_online
                    },
                    'last_message_text': last_message.text if last_message else None,
                    'last_message_sender': last_message.sender.username if last_message else None,
                    'updated_at': chat.last_message_at.isoformat() if chat.last_message_at else chat.created_at.isoformat(),
                    'created_at': chat.created_at.isoformat()
                }
                chats_data.append(chat_data)
                
                print(f"DEBUG: Добавлен личный чат {chat.id}")
        except Exception as e:
            print(f"DEBUG: Ошибка при получении личных чатов: {e}")

        # Сортируем по времени последнего обновления
        chats_data.sort(key=lambda x: x['updated_at'], reverse=True)
        
        print(f"DEBUG: Всего найдено чатов: {len(chats_data)}")
        
        return Response(chats_data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_detail(request, pk):
    """Получить детали чата по ID"""
    try:
        print(f"DEBUG: Запрос деталей чата {pk} от пользователя {request.user.id}")
        
        # 1. Проверяем личные чаты
        try:
            private_chat = PrivateChat.objects.get(
                Q(id=pk) & (Q(user1=request.user) | Q(user2=request.user))
            )
            print(f"DEBUG: Найден личный чат: {private_chat.id}")

            # Получаем другого пользователя
            other_user = private_chat.other_user(request.user)
            
            # Получаем кастомные настройки пользователя
            try:
                user_settings = PrivateChatUserSettings.objects.get(chat=private_chat, user=request.user)
                custom_name = user_settings.custom_name
                custom_avatar_url = user_settings.custom_avatar.url if user_settings.custom_avatar else None
            except PrivateChatUserSettings.DoesNotExist:
                custom_name = None
                custom_avatar_url = None

            # Проверяем онлайн статус через Redis
            from core.online_status import online_status
            is_online = online_status.is_online(other_user.id)

            # Получаем счётчик непрочитанных сообщений от other_user (упрощённо)
            try:
                from .chat_cache import ChatCacheService
                unread_count_for_other = ChatCacheService.get_unread_count(other_user.id, private_chat.id)
            except Exception as e:
                print(f"DEBUG: Ошибка подсчёта непрочитанных: {e}")
                unread_count_for_other = 0

            # Создаем словарь с данными
            chat_data = {
                'id': private_chat.id,
                'type': 'private',
                'name': custom_name,  # Кастомное название пользователя
                'avatar_url': custom_avatar_url or (other_user.avatar.url if other_user.avatar else None),
                'user1': private_chat.user1.id,
                'user2': private_chat.user2.id,
                'created_at': private_chat.created_at,
                'last_message_at': private_chat.last_message_at,
                'unread_count': unread_count_for_other,  # Непрочитанные у другого пользователя
                'other_user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'display_name': other_user.display_name or other_user.username,
                    'avatar': other_user.avatar.url if other_user.avatar else None,
                    'is_online': is_online
                }
            }

            print(f"DEBUG: Возвращаем данные личного чата: name={custom_name}, avatar_url={custom_avatar_url}")
            return Response(chat_data)
            
        except PrivateChat.DoesNotExist:
            print(f"DEBUG: Личный чат {pk} не найден или нет доступа")
            pass

        # 2. Проверяем групповые чаты
        try:
            group_chat = GroupChat.objects.get(
                id=pk,
                members__user=request.user
            )
            print(f"DEBUG: Найден групповой чат: {group_chat.id}")

            # Сериализуем данные
            serializer = GroupChatSerializer(
                group_chat,
                context={'request': request}
            )
            data = serializer.data
            data['type'] = 'group'  # Добавляем тип чата
            
            print(f"DEBUG: Возвращаем данные группового чата")
            return Response(data)
            
        except GroupChat.DoesNotExist:
            print(f"DEBUG: Групповой чат {pk} не найден или нет доступа")
            pass
        
        # 3. Если ничего не нашли
        return Response(
            {
                'error': 'Чат не найден',
                'message': f'Чат с ID {pk} не существует или у вас нет к нему доступа',
                'user_id': request.user.id
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        print(f"DEBUG: Ошибка в get_chat_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response(
            {'error': f'Ошибка сервера: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        content_type_str = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')

        if not content_type_str or not object_id:
            return Comment.objects.none()

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            return Comment.objects.filter(
                content_type=content_type,
                object_id=object_id,
                is_deleted=False
            ).select_related('author')
        except ContentType.DoesNotExist:
            return Comment.objects.none()

    def perform_create(self, serializer):
        content_type_str = self.request.data.get('content_type')
        object_id = self.request.data.get('object_id')

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            serializer.save(
                author=self.request.user,
                content_type=content_type,
                object_id=object_id
            )
        except ContentType.DoesNotExist:
            raise serializer.ValidationError("Invalid content_type")


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.filter(is_deleted=False)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        # Только автор может редактировать
        if self.get_object().author != self.request.user:
            self.permission_denied(self.request, message="Cannot edit others' comments")
        serializer.save()


# ==================== POST COMMENTS VIEW SET ====================

class PostCommentViewSet(ModelViewSet):
    """ViewSet для комментариев к постам (ленты)"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostCommentCreateSerializer
        return PostCommentSerializer

    def get_queryset(self):
        post_pk = self.kwargs.get('post_pk')
        if not post_pk:
            return PostComment.objects.none()

        # Получаем корневые комментарии (без parent)
        queryset = PostComment.objects.filter(
            post_id=post_pk,
            parent__isnull=True,
            is_deleted=False
        ).select_related('author')

        # Сортировка
        sort = self.request.query_params.get('sort', 'best')
        if sort == 'new':
            queryset = queryset.order_by('-created_at')
        else:  # 'best' - по лайкам
            queryset = queryset.annotate(
                likes_count_annotation=Count('likes')
            ).order_by('-likes_count_annotation', '-created_at')

        return queryset

    def perform_create(self, serializer):
        post_pk = self.kwargs.get('post_pk')
        post = Post.objects.get(id=post_pk)

        if not post.allow_comments:
            raise PermissionDenied("Комментарии к этому посту закрыты")

        # parent is already resolved by the serializer from validated_data['parent']
        # We just pass post and author; serializer.create() handles path/level/counters
        serializer.save(
            post=post,
            author=self.request.user,
        )

    def perform_destroy(self, instance):
        # Мягкое удаление
        instance.is_deleted = True
        instance.content = '[комментарий удалён]'
        instance.author = None  # Скрываем автора
        instance.save()

        # Обновляем счётчики
        post = instance.post
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])

        if instance.parent:
            instance.parent.replies_count = max(0, instance.parent.replies_count - 1)
            instance.parent.save(update_fields=['replies_count'])


# ==================== COMMENT LIKES ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """Лайкнуть/дизлайкнуть комментарий (лайк)"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({'error': 'Комментарий не найден'}, status=404)

    # Нельзя лайкать свой комментарий
    if comment.author == request.user:
        return Response({'error': 'Нельзя лайкать свой комментарий'}, status=400)

    # Проверяем текущую реакцию
    existing_like = PostCommentLike.objects.filter(
        user=request.user,
        comment=comment
    ).first()

    existing_dislike = PostCommentDislike.objects.filter(
        user=request.user,
        comment=comment
    ).first()

    if existing_like:
        # Удаляем лайк
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=['likes_count'])
        return Response({
            'success': True,
            'liked': False,
            'likes_count': comment.likes_count,
            'dislikes_count': comment.dislikes_count
        })

    # Удаляем дизлайк, если есть
    if existing_dislike:
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)

    # Создаём лайк
    PostCommentLike.objects.create(user=request.user, comment=comment)
    comment.likes_count += 1
    comment.save(update_fields=['likes_count', 'dislikes_count'])

    return Response({
        'success': True,
        'liked': True,
        'likes_count': comment.likes_count,
        'dislikes_count': comment.dislikes_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    """Дизлайкнуть комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({'error': 'Комментарий не найден'}, status=404)

    # Нельзя дизлайкать свой комментарий
    if comment.author == request.user:
        return Response({'error': 'Нельзя дизлайкать свой комментарий'}, status=400)

    # Проверяем текущую реакцию
    existing_dislike = PostCommentDislike.objects.filter(
        user=request.user,
        comment=comment
    ).first()

    existing_like = PostCommentLike.objects.filter(
        user=request.user,
        comment=comment
    ).first()

    if existing_dislike:
        # Удаляем дизлайк
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=['dislikes_count'])
        return Response({
            'success': True,
            'disliked': False,
            'likes_count': comment.likes_count,
            'dislikes_count': comment.dislikes_count
        })

    # Удаляем лайк, если есть
    if existing_like:
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)

    # Создаём дизлайк
    PostCommentDislike.objects.create(user=request.user, comment=comment)
    comment.dislikes_count += 1
    comment.save(update_fields=['likes_count', 'dislikes_count'])

    return Response({
        'success': True,
        'disliked': True,
        'likes_count': comment.likes_count,
        'dislikes_count': comment.dislikes_count
    })


# ==================== POST ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    """Закрепить пост в профиле"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({'error': 'Нельзя закреплять чужие посты'}, status=403)

    # Проверяем, не истекло ли время на редактирование (5 минут)
    if (timezone.now() - post.created_at).total_seconds() > 300:
        return Response({'error': 'Время на закрепление истекло'}, status=400)

    # Снимаем закрепление с другого поста, если есть
    Post.objects.filter(author=request.user, is_pinned=True).update(is_pinned=False, pinned_at=None)

    # Закрепляем текущий пост
    post.is_pinned = True
    post.pinned_at = timezone.now()
    post.save(update_fields=['is_pinned', 'pinned_at'])

    return Response({
        'success': True,
        'message': 'Пост закреплён',
        'is_pinned': True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    """Открепить пост от профиля"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({'error': 'Нельзя откреплять чужие посты'}, status=403)

    post.is_pinned = False
    post.pinned_at = None
    post.save(update_fields=['is_pinned', 'pinned_at'])

    return Response({
        'success': True,
        'message': 'Пост откреплён',
        'is_pinned': False
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    """Пожаловаться на пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Нельзя жаловаться на свой пост
    if post.author == request.user:
        return Response({'error': 'Нельзя жаловаться на свой пост'}, status=400)

    reason = request.data.get('reason')
    if reason not in ['spam', 'copyright', 'harassment', 'inappropriate', 'other']:
        return Response({'error': 'Неверная причина жалобы'}, status=400)

    comment = request.data.get('comment', '')

    # Проверяем, не жаловался ли уже пользователь
    existing_report = Report.objects.filter(
        reporter=request.user,
        content_type='post',
        content_id=post_id,
        status='pending'
    ).first()

    if existing_report:
        return Response({'error': 'Вы уже отправили жалобу на этот пост'}, status=400)

    report = Report.objects.create(
        reporter=request.user,
        content_type='post',
        content_id=post_id,
        reason=reason,
        comment=comment,
        status='pending'
    )

    # Запускаем фоновое задание для уведомления модераторов
    try:
        from social.tasks import notify_moderators_new_report
        notify_moderators_new_report.delay(report.id)
    except Exception:
        pass  # Celery может быть недоступен

    return Response({
        'success': True,
        'message': 'Жалоба отправлена',
        'report_id': report.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bookmark(request, post_id):
    """Добавить пост в закладки"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    folder = request.data.get('folder', '')

    # Проверяем, не добавлено ли уже
    existing_bookmark = Bookmark.objects.filter(
        user=request.user,
        post=post
    ).first()

    if existing_bookmark:
        # Обновляем папку
        existing_bookmark.folder = folder
        existing_bookmark.save(update_fields=['folder'])
        return Response({
            'success': True,
            'message': 'Закладка обновлена',
            'bookmarked': True,
            'folder': folder
        })

    bookmark = Bookmark.objects.create(
        user=request.user,
        post=post,
        folder=folder
    )

    return Response({
        'success': True,
        'message': 'Пост добавлен в закладки',
        'bookmarked': True,
        'folder': folder
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, post_id):
    """Удалить пост из закладок"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    deleted, _ = Bookmark.objects.filter(
        user=request.user,
        post=post
    ).delete()

    if deleted:
        return Response({
            'success': True,
            'message': 'Пост удалён из закладок',
            'bookmarked': False
        })

    return Response({
        'success': True,
        'message': 'Пост не был в закладках',
        'bookmarked': False
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarks_folders(request):
    """Получить список папок закладок"""
    folders_data = Bookmark.objects.filter(user=request.user).values_list('folder', flat=True)
    folders = list(set(folders_data))
    folders = [f for f in folders if f]  # Убираем пустые

    # Добавляем стандартные папки
    default_folders = ['watch_later', 'favorite', 'recipes']
    all_folders = list(set(folders + default_folders))

    result = []
    for folder in all_folders:
        count = Bookmark.objects.filter(user=request.user, folder=folder).count()
        result.append({
            'name': folder,
            'count': count
        })

    # Добавляем общее количество
    total_count = Bookmark.objects.filter(user=request.user).count()
    result.insert(0, {'name': 'all', 'count': total_count})

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likers(request, post_id):
    """Получить список пользователей, лайкнувших пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    likes = PostLike.objects.filter(post=post).select_related('user__profile')[:100]

    users = []
    for like in likes:
        users.append({
            'id': like.user.id,
            'username': like.user.username,
            'avatar': like.user.profile.avatar.url if hasattr(like.user, 'profile') and like.user.profile.avatar else None,
            'liked_at': like.created_at.isoformat()
        })

    return Response({
        'count': post.likes_count,
        'users': users
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_dislikers(request, post_id):
    """Получить список пользователей, дизлайкнувших пост (только для модераторов)"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Только модераторы могут видеть дизлайки
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({'error': 'Доступ запрещён'}, status=403)

    dislikes = PostDislike.objects.filter(post=post).select_related('user__profile')[:100]

    users = []
    for dislike in dislikes:
        users.append({
            'id': dislike.user.id,
            'username': dislike.user.username,
            'avatar': dislike.user.profile.avatar.url if hasattr(dislike.user, 'profile') and dislike.user.profile.avatar else None,
            'disliked_at': dislike.created_at.isoformat()
        })

    return Response({
        'count': post.dislikes_count,
        'users': users
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def repost_post(request, post_id):
    """Репостнуть пост"""
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Нельзя репостнуть свой пост
    if original_post.author == request.user:
        return Response({'error': 'Нельзя репостнуть свой пост'}, status=400)

    # Нельзя репостнуть системный пост
    if original_post.post_type == 'system':
        return Response({'error': 'Нельзя репостнуть системный пост'}, status=400)

    # Нельзя репостнуть приватный пост
    if original_post.visibility == 'private':
        return Response({'error': 'Нельзя репостнуть приватный пост'}, status=400)

    comment = request.data.get('comment', '')

    # Проверяем, не репостнул ли уже
    existing_repost = Repost.objects.filter(
        user=request.user,
        original_post=original_post
    ).first()

    if existing_repost:
        return Response({'error': 'Вы уже репостнули этот пост'}, status=400)

    # Создаём репост
    with transaction.atomic():
        # Создаём новый пост-репост
        repost_post = Post.objects.create(
            author=request.user,
            post_type='repost',
            text=comment,
            status='published',
            visibility='public',
            allow_comments=True,
            original_post=original_post,
            repost_comment=comment
        )

        # Создаём запись о репосте
        Repost.objects.create(
            user=request.user,
            original_post=original_post,
            comment=comment
        )

        # Обновляем счётчик репостов
        original_post.reposts_count += 1
        original_post.save(update_fields=['reposts_count'])

    return Response({
        'success': True,
        'message': 'Пост репостнут',
        'repost_id': repost_post.id,
        'original_post_id': original_post.id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unrepost_post(request, post_id):
    """Удалить репост"""
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    repost = Repost.objects.filter(
        user=request.user,
        original_post=original_post
    ).first()

    if not repost:
        return Response({'error': 'Вы не репостнули этот пост'}, status=400)

    # Удаляем пост-репост
    Post.objects.filter(
        author=request.user,
        type='repost'
    ).filter(attachments__content_type='repost', attachments__object_id=original_post.id).delete()

    # Удаляем запись о репосте
    repost.delete()

    # Обновляем счётчик
    original_post.reposts_count = max(0, original_post.reposts_count - 1)
    original_post.save(update_fields=['reposts_count'])

    return Response({
        'success': True,
        'message': 'Репост удалён'
    })


# ==================== COMMENT ACTIONS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_comment_replies(request, comment_id):
    """Получить ответы на комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({'error': 'Комментарий не найден'}, status=404)

    max_depth = 3
    replies = PostComment.objects.filter(
        parent=comment,
        is_deleted=False
    ).select_related('author__profile').annotate(
        likes_count_annotation=Count('likes')
    ).order_by('-likes_count_annotation', 'created_at')[:20]

    # Добавляем флаг о глубине
    for reply in replies:
        if reply.level >= max_depth:
            reply.has_more_replies = True

    serializer = PostCommentSerializer(replies, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    """Пожаловаться на комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({'error': 'Комментарий не найден'}, status=404)

    # Нельзя жаловаться на свой комментарий
    if comment.author == request.user:
        return Response({'error': 'Нельзя жаловаться на свой комментарий'}, status=400)

    reason = request.data.get('reason')
    if reason not in ['spam', 'copyright', 'harassment', 'inappropriate', 'other']:
        return Response({'error': 'Неверная причина жалобы'}, status=400)

    comment_text = request.data.get('comment', '')

    # Проверяем, не жаловался ли уже пользователь
    existing_report = Report.objects.filter(
        reporter=request.user,
        content_type='comment',
        content_id=comment_id,
        status='pending'
    ).first()

    if existing_report:
        return Response({'error': 'Вы уже отправили жалобу на этот комментарий'}, status=400)

    report = Report.objects.create(
        reporter=request.user,
        content_type='comment',
        content_id=comment_id,
        reason=reason,
        comment=comment_text,
        status='pending'
    )

    return Response({
        'success': True,
        'message': 'Жалоба отправлена',
        'report_id': report.id
    })


# ==================== FEED STATISTICS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feed_statistics(request):
    """Получить статистику ленты пользователя"""
    user = request.user

    # Количество постов
    posts_count = Post.objects.filter(author=user, status='published').count()

    # Количество лайков полученных
    likes_received = PostLike.objects.filter(post__author=user).count()

    # Количество комментариев полученных
    comments_received = PostComment.objects.filter(post__author=user).count()

    # Количество репостов полученных
    reposts_received = Repost.objects.filter(original_post__author=user).count()

    # Количество закладок
    bookmarks_count = Bookmark.objects.filter(user=user).count()

    # Новые посты в ленте (подсчитываем по подпискам)
    from social.models import Follow
    following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    new_posts_count = Post.objects.filter(
        author_id__in=following_ids,
        status='published',
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()

    return Response({
        'posts_count': posts_count,
        'likes_received': likes_received,
        'comments_received': comments_received,
        'reposts_received': reposts_received,
        'bookmarks_count': bookmarks_count,
        'new_posts_count': new_posts_count
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_popular_posts(request):
    """Получить популярные посты"""
    period = request.query_params.get('period', 'day')  # day, week, month, all

    if period == 'day':
        since = timezone.now() - timedelta(days=1)
    elif period == 'week':
        since = timezone.now() - timedelta(days=7)
    elif period == 'month':
        since = timezone.now() - timedelta(days=30)
    else:
        since = None

    queryset = Post.objects.filter(status='published', post_type__in=['text', 'image', 'video', 'anime'])

    if since:
        queryset = queryset.filter(created_at__gte=since)

    # Сортировка по популярности (лайки + комментарии + репосты) / время
    queryset = queryset.annotate(
        popularity=F('likes_count') + F('comments_count') + F('reposts_count')
    ).order_by('-popularity')[:50]

    serializer = PostSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    """Получить посты конкретного пользователя"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    posts = Post.objects.filter(
        author=user,
        status='published'
    ).order_by('-created_at')

    # Пагинация
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))
    offset = (page - 1) * limit

    total = posts.count()
    posts = posts[offset:offset + limit]

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response({
        'count': total,
        'page': page,
        'limit': limit,
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_group_posts(request, group_id):
    """Получить посты группы"""
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({'error': 'Группа не найдена'}, status=404)

    # Проверяем доступность группы
    if group.is_private:
        if not request.user.is_authenticated:
            return Response({'error': 'Группа приватная'}, status=403)
        
        is_member = GroupMembership.objects.filter(group=group, user=request.user).exists()
        if not is_member:
            return Response({'error': 'Вы не состоите в группе'}, status=403)

    posts = Post.objects.filter(
        group=group,
        status='published'
    ).order_by('-created_at')

    # Пагинация
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))
    offset = (page - 1) * limit

    total = posts.count()
    posts = posts[offset:offset + limit]

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response({
        'count': total,
        'page': page,
        'limit': limit,
        'results': serializer.data
    })


# ==================== CONTENT MODERATION ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hide_post_from_feed(request, post_id):
    """Скрыть пост из ленты"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Добавляем запись в HiddenPost или используем существующую модель
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    
    # Создаём запись о скрытии
    # Здесь можно использовать любую модель для хранения скрытых постов
    # Пока просто возвращаем успех
    # В будущем можно добавить модель HiddenPost

    return Response({
        'success': True,
        'message': 'Пост скрыт из ленты'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_post_not_interested(request, post_id):
    """Отметить пост как "Не интересно" (влияет на рекомендации)"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Здесь можно сохранить информацию о том, что пользователю не интересен этот пост
    # Для влияния на алгоритмы рекомендаций
    # В будущем добавить модель UserInterest с полем not_interested

    return Response({
        'success': True,
        'message': 'Пост отмечен как неинтересный'
    })


# ==================== POST EDITING ====================

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    """Редактировать пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({'error': 'Нельзя редактировать чужие посты'}, status=403)

    # Проверяем время на редактирование (5 минут)
    if (timezone.now() - post.created_at).total_seconds() > 300:
        return Response({'error': 'Время на редактирование истекло'}, status=400)

    # Нельзя менять тип поста
    new_type = request.data.get('post_type')
    if new_type and new_type != post.post_type:
        return Response({'error': 'Нельзя менять тип поста'}, status=400)

    # Обновляем данные
    if 'title' in request.data:
        post.title = request.data['title'][:200] if request.data['title'] else None

    if 'text' in request.data:
        text = request.data['text']
        if text and len(text) > 5000:
            return Response({'error': 'Максимум 5000 символов'}, status=400)
        post.text = text

    if 'visibility' in request.data:
        if request.data['visibility'] in ['public', 'followers', 'friends', 'private']:
            post.visibility = request.data['visibility']

    if 'allow_comments' in request.data:
        post.allow_comments = bool(request.data['allow_comments'])

    if 'is_spoiler' in request.data:
        post.is_spoiler = bool(request.data['is_spoiler'])

    post.edited_at = timezone.now()
    post.save()

    return Response({
        'success': True,
        'message': 'Пост обновлён',
        'post': PostSerializer(post, context={'request': request}).data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    """Редактировать комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({'error': 'Комментарий не найден'}, status=404)

    # Проверяем права
    if comment.author != request.user:
        return Response({'error': 'Нельзя редактировать чужие комментарии'}, status=403)

    # Проверяем время на редактирование (10 минут)
    if (timezone.now() - comment.created_at).total_seconds() > 600:
        return Response({'error': 'Время на редактирование истекло'}, status=400)

    # Обновляем контент
    content = request.data.get('content')
    if not content:
        return Response({'error': 'Комментарий не может быть пустым'}, status=400)

    if len(content) > 2000:
        return Response({'error': 'Максимум 2000 символов'}, status=400)

    comment.content = content
    comment.is_edited = True
    comment.save()

    return Response({
        'success': True,
        'message': 'Комментарий обновлён',
        'comment': PostCommentSerializer(comment, context={'request': request}).data
    })


# ==================== HASHTAGS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_hashtag_posts(request, tag_name):
    """Получить посты по хэштегу"""
    # Убираем # из начала если есть
    tag = tag_name.lstrip('#')
    
    # Сначала пробуем получить из кэша
    try:
        from .feed_cache import feed_cache
        post_ids = feed_cache.get_hashtag_posts(tag, limit=50)
        
        if post_ids:
            posts = Post.objects.filter(
                id__in=post_ids,
                status='published'
            ).select_related('author__profile', 'anime')
            
            serializer = PostSerializer(posts, many=True, context={'request': request})
            return Response(serializer.data)
    except Exception:
        pass

    # Если нет в кэше, получаем из БД
    hashtag = Hashtag.objects.filter(name__iexact=tag).first()
    if not hashtag:
        return Response({'results': [], 'count': 0})
    
    post_ids = PostHashtag.objects.filter(
        hashtag=hashtag
    ).values_list('post_id', flat=True).order_by('-post__created_at')
    
    posts = Post.objects.filter(
        id__in=post_ids,
        status='published'
    ).select_related('author__profile', 'anime')
    
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response({
        'results': serializer.data,
        'count': len(serializer.data),
        'hashtag': tag
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def search_hashtags(request):
    """Поиск хэштегов"""
    query = request.query_params.get('q', '')
    limit = int(request.query_params.get('limit', 10))
    
    if len(query) < 2:
        return Response({'results': []})
    
    hashtags = Hashtag.objects.filter(
        name__icontains=query
    ).order_by('-posts_count')[:limit]
    
    results = []
    for tag in hashtags:
        results.append({
            'id': tag.id,
            'name': tag.name,
            'posts_count': tag.posts_count
        })
    
    return Response({'results': results})


# ==================== POST VIEWS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_post_view(request, post_id):
    """Отследить просмотр поста"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    # Проверяем, не是自己的 пост
    if post.author == request.user:
        return Response({'success': True, 'message': 'Просмотр засчитан (автор)'})

    # Проверяем, не просматривал ли уже
    existing_view = FeedView.objects.filter(
        user=request.user,
        post=post
    ).first()

    if existing_view:
        return Response({'success': True, 'message': 'Уже просмотрено'})

    # Создаём запись о просмотре
    FeedView.objects.create(
        user=request.user,
        post=post
    )

    # Увеличиваем счётчик просмотров
    post.views_count += 1
    post.save(update_fields=['views_count'])

    return Response({
        'success': True,
        'message': 'Просмотр засчитан',
        'views_count': post.views_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_viewers(request, post_id):
    """Получить список пользователей, просмотревших пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    views = FeedView.objects.filter(post=post).select_related('user__profile')[:100]

    users = []
    for view in views:
        users.append({
            'id': view.user.id,
            'username': view.user.username,
            'avatar': view.user.profile.avatar.url if hasattr(view.user, 'profile') and view.user.profile.avatar else None,
            'viewed_at': view.viewed_at.isoformat()
        })

    return Response({
        'count': post.views_count,
        'users': users
    })


# ==================== NOTIFICATIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notification_settings(request):
    """Получить настройки уведомлений для ленты"""
    profile = request.user.profile if hasattr(request.user, 'profile') else None

    settings = {
        'notify_likes': getattr(profile, 'notify_likes', True) if profile else True,
        'notify_comments': getattr(profile, 'notify_comments', True) if profile else True,
        'notify_mentions': True,  # Всегда включены
        'email_digest': getattr(profile, 'email_digest', 'never') if profile else 'never',
    }

    return Response(settings)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_notification_settings(request):
    """Обновить настройки уведомлений для ленты"""
    profile = request.user.profile if hasattr(request.user, 'profile') else None

    if not profile:
        return Response({'error': 'Профиль не найден'}, status=404)

    if 'notify_likes' in request.data:
        profile.notify_likes = bool(request.data['notify_likes'])

    if 'notify_comments' in request.data:
        profile.notify_comments = bool(request.data['notify_comments'])

    if 'email_digest' in request.data:
        if request.data['email_digest'] in ['never', 'daily', 'weekly']:
            profile.email_digest = request.data['email_digest']

    profile.save()

    return Response({
        'success': True,
        'message': 'Настройки обновлены'
    })

    def perform_destroy(self, instance):
        # Только автор или модератор может удалить
        if instance.author != self.request.user:
            # Проверяем модерацию - для простоты, пока только автор
            self.permission_denied(self.request, message="Cannot delete others' comments")
        instance.is_deleted = True
        instance.save()


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GroupCreateSerializer
        return GroupSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        group = self.get_object()
        if group.memberships.filter(user=request.user).exists():
            return Response({"detail": "Already a member"}, status=status.HTTP_400_BAD_REQUEST)

        membership = GroupMembership.objects.create(user=request.user, group=group)
        group.update_members_count()
        return Response(GroupMembershipSerializer(membership).data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        group = self.get_object()
        membership = group.memberships.filter(user=request.user).first()
        if not membership:
            return Response({"detail": "Not a member"}, status=status.HTTP_400_BAD_REQUEST)

        membership.delete()
        group.update_members_count()
        return Response({"detail": "Left group"})

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        memberships = group.memberships.all()
        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class GroupSearchView(APIView):
    """Поиск групп"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Поиск групп по названию"""
        search = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))

        if not search:
            return Response({'results': []})

        # Фильтруем группы
        queryset = Group.objects.filter(
            Q(name__icontains=search) | Q(description__icontains=search),
            is_private=False
        ).select_related('creator')

        # Ограничиваем результат
        queryset = queryset[:limit]

        # Сериализуем
        serializer = GroupSerializer(queryset, many=True)

        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })


class PostViewSet(ModelViewSet):
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateSerializer
        return PostSerializer

    def get_queryset(self):
        queryset = Post.objects.filter(
            is_deleted=False,
            status='published'
        ).select_related(
            'author', 'anime', 'group', 'playlist', 'reactor_post'
        ).prefetch_related(
            'media_files', 'attachments', 'hashtag_links__hashtag'
        ).order_by('-created_at')

        # Фильтр по группе (преобразуем 'true' string в None или целое число)
        group_filter = self.request.query_params.get('group')
        if group_filter and group_filter != 'true':
            try:
                group_id = int(group_filter)
                queryset = queryset.filter(group_id=group_id)
            except (ValueError, TypeError):
                pass
        elif group_filter == 'true':
            # Если group=true, показываем только посты в группах
            queryset = queryset.exclude(group__isnull=True)

        # Фильтр по аниме
        anime_id = self.request.query_params.get('anime')
        if anime_id:
            try:
                queryset = queryset.filter(anime_id=int(anime_id))
            except (ValueError, TypeError):
                pass

        # Лента пользователя (посты от подписок)
        if self.request.query_params.get('feed') == 'true':
            queryset = queryset.exclude(group__isnull=False)

        return queryset

    def _handle_media_uploads(self, request, post, replace=False):
        """Create PostMedia records for any files named media_*. If replace=True, clear existing media first."""
        if replace:
            post.media_files.all().delete()

        for key, file in request.FILES.items():
            if key.startswith('media_'):
                # determine type from mime
                if file.content_type.startswith('image'):
                    media_type = 'image'
                elif file.content_type.startswith('video'):
                    media_type = 'video'
                else:
                    # default fallback
                    media_type = 'image'

                # Calculate file size in bytes
                file_size = file.size
                PostMedia.objects.create(
                    post=post,
                    media_type=media_type,
                    file=file,
                    file_size=file_size
                )

    def _update_post_type(self, post):
        """Guess post_type based on attached data if it was not explicitly set."""
        new_type = post.post_type
        # priority: playlist > anime > reactor_post > media
        if post.playlist:
            new_type = 'playlist'
        elif post.anime:
            new_type = 'anime'
        elif post.reactor_post:
            new_type = 'repost'
        else:
            media_qs = post.media_files.all()
            if media_qs.exists():
                # if any video exists, mark video, else image
                if media_qs.filter(media_type='video').exists():
                    new_type = 'video'
                else:
                    new_type = 'image'
        if new_type != post.post_type:
            post.post_type = new_type
            post.save(update_fields=['post_type'])

    def create(self, request, *args, **kwargs):
        try:
            # strip media_x fields before validation; they are handled separately
            data = request.data.copy()
            for key in list(data.keys()):
                if key.startswith('media_'):
                    data.pop(key)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            post = serializer.instance
            self._handle_media_uploads(request, post)
            # ensure type is correct after attachments/media
            self._update_post_type(post)

            headers = self.get_success_headers(serializer.data)
            out_serializer = PostSerializer(post, context={'request': request})
            return Response(out_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            return Response({'error': str(exc)}, status=500)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user, status='published')

        # Публикуем событие создания поста
        try:
            publish_post_created({
                'post_id': post.id,
                'author_id': post.author.id,
                'author_username': post.author.username,
                'text': post.text[:200] if post.text else '',
                'created_at': post.created_at.isoformat()
            })
        except Exception as e:
            # Redis недоступен, просто логируем
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to publish post created event: {e}')
        return post

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            # strip media fields from data before validation
            data = request.data.copy()
            for key in list(data.keys()):
                if key.startswith('media_'):
                    data.pop(key)

            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            self._handle_media_uploads(request, instance, replace=not partial)
            self._update_post_type(instance)
            out = PostSerializer(instance, context={'request': request})
            return Response(out.data)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            return Response({'error': str(exc)}, status=500)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_id')
        print(f"DEBUG: Получаем сообщения для чата {chat_id}, пользователь {self.request.user}")

        # Определяем тип чата по ID (можно добавить префикс или параметр типа)
        # Для простоты проверяем оба типа
        try:
            # Сначала пытаемся найти групповой чат
            chat = GroupChat.objects.get(id=chat_id)
            # Проверяем, что пользователь участник
            if not ChatMember.objects.filter(chat=chat, user=self.request.user).exists():
                return Message.objects.none()
            return Message.objects.filter(chat=chat, is_deleted=False).select_related('sender', 'reply_to')
        except GroupChat.DoesNotExist:
            # Если не найден групповой, ищем личный
            try:
                private_chat = PrivateChat.objects.get(id=chat_id)
                # Проверяем доступ к личному чату
                if self.request.user not in [private_chat.user1, private_chat.user2]:
                    return Message.objects.none()
                return Message.objects.filter(private_chat=private_chat, is_deleted=False).select_related('sender', 'reply_to')
            except PrivateChat.DoesNotExist:
                return Message.objects.none()

    def perform_create(self, serializer):
        from .chat_cache import ChatCacheService

        chat_id = self.request.data.get('chat_id') or self.request.data.get('private_chat') or self.request.data.get('chat')
        print(f"DEBUG: Создаем сообщение для чата {chat_id}, пользователь {self.request.user}")
        print(f"DEBUG: Данные запроса: {self.request.data}")

        if not chat_id:
            raise PermissionError("Не указан ID чата")

        try:
            # Определяем тип чата
            chat = None
            private_chat = None

            try:
                chat = GroupChat.objects.get(id=chat_id)
                # Проверяем, что пользователь участник группового чата
                member = ChatMember.objects.filter(chat=chat, user=self.request.user).first()
                if not member:
                    raise PermissionError("Пользователь не является участником чата")
                if member.is_banned:
                    raise PermissionError("Пользователь забанен в чате")
                if member.is_muted and (member.muted_until is None or member.muted_until > timezone.now()):
                    raise PermissionError("Пользователь заглушен в чате")
                if not member.can_send_messages:
                    raise PermissionError("Пользователь не может отправлять сообщения")

                message = serializer.save(chat=chat, sender=self.request.user)

            except GroupChat.DoesNotExist:
                try:
                    private_chat = PrivateChat.objects.get(id=chat_id)
                    # Проверяем доступ к личному чату
                    if self.request.user not in [private_chat.user1, private_chat.user2]:
                        raise PermissionError("Нет доступа к чату")

                    # Проверяем, не заблокирован ли чат
                    other_user = private_chat.user1 if private_chat.user2 == self.request.user else private_chat.user2
                    settings = private_chat.get_user_settings(self.request.user)
                    if settings.get('blocked', False):
                        raise PermissionError("Чат заблокирован")

                    message = serializer.save(private_chat=private_chat, sender=self.request.user)

                except PrivateChat.DoesNotExist:
                    raise PermissionError("Чат не найден")

            # Обновляем время последнего сообщения
            if chat:
                chat.save(update_fields=['last_message_at'])
            elif private_chat:
                private_chat.last_message_at = timezone.now()
                private_chat.save(update_fields=['last_message_at'])

            print("DEBUG: Сообщение успешно сохранено")

            # Добавляем сообщение в кэш
            ChatCacheService.add_message_to_cache(chat_id, message)

            # Увеличиваем счётчики непрочитанных для участников
            if chat:
                for member in chat.members.exclude(user=self.request.user):
                    ChatCacheService.increment_unread(member.user_id, chat_id)
            elif private_chat:
                receiver = private_chat.user1 if private_chat.user2 == self.request.user else private_chat.user2
                ChatCacheService.increment_unread(receiver.id, chat_id)

            # Публикуем событие отправки сообщения
            publish_message_sent({
                'message_id': message.id,
                'chat_id': chat_id,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'text': message.text[:200] if message.text else '',
                'created_at': message.created_at.isoformat()
            })

            # Запускаем фоновую задачу для обработки сообщения
            from .tasks import process_new_message
            process_new_message.delay(message.id)

            # Отправляем уведомления
            self.send_notifications(message, chat, private_chat)

        except PermissionError as e:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(str(e))
        except Exception as e:
            print(f"DEBUG: Ошибка при сохранении: {e}")
            raise

    def send_notifications(self, message, group_chat=None, private_chat=None):
        """Отправить уведомления о новом сообщении"""
        if private_chat:
            # Личный чат
            receiver = private_chat.user1 if private_chat.user2 == message.sender else private_chat.user2
            settings = private_chat.get_user_settings(receiver)

            if settings.get('notifications', True) and not settings.get('blocked', False):
                # Отправляем уведомление
                pass

        elif group_chat:
            # Групповой чат
            for member in group_chat.members.exclude(user=message.sender):
                # Проверяем настройки уведомлений участника
                if member.can_send_messages and not member.is_muted:
                    # Отправляем уведомление
                    pass


class ChatRoleViewSet(ModelViewSet):
    serializer_class = ChatRoleSerializer
    permission_classes = [IsChatOwner]

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_pk')
        return ChatRole.objects.filter(chat_id=chat_id)

    def perform_create(self, serializer):
        chat_id = self.kwargs.get('chat_pk')
        chat = GroupChat.objects.get(id=chat_id)
        serializer.save(chat=chat, created_by=self.request.user)


class GroupChatViewSet(ModelViewSet):
    queryset = GroupChat.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GroupChatCreateSerializer
        return GroupChatSerializer

    def get_queryset(self):
        return GroupChat.objects.filter(
            members__user=self.request.user
        ).prefetch_related('members', 'members__user').order_by('-last_message_at', '-created_at')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Отметить сообщения группового чата как прочитанные"""
        from .chat_cache import ChatCacheService
        from .models import Message, MessageReadStatus
        
        try:
            chat = GroupChat.objects.get(id=pk)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)

        # Проверяем доступ
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'error': 'Нет доступа к чату'}, status=403)

        # Получаем все непрочитанные сообщения от других пользователей
        unread_messages = Message.objects.filter(
            chat=chat
        ).exclude(sender=request.user)

        # Создаём записи MessageReadStatus для каждого непрочитанного сообщения
        for message in unread_messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=request.user
            )
            
        # Сбрасываем счётчик непрочитанных
        ChatCacheService.reset_unread(request.user.id, chat.id)
        
        return Response({'message': 'Сообщения отмечены как прочитанные'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Получить сообщения чата"""
        chat = self.get_object()
        messages = Message.objects.filter(chat=chat).order_by('-created_at')[:100]
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave_chat(self, request, pk=None):
        """Покинуть групповой чат"""
        chat = self.get_object()
        
        try:
            member = ChatMember.objects.get(chat=chat, user=request.user)
            member.delete()
            return Response({'message': 'Вы покинули чат'})
        except ChatMember.DoesNotExist:
            return Response({'error': 'Вы не являетесь участником чата'}, status=400)


class PrivateChatViewSet(ModelViewSet):
    queryset = PrivateChat.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return PrivateChatSerializer

    def get_queryset(self):
        return PrivateChat.objects.filter(
            models.Q(user1=self.request.user) | models.Q(user2=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        """Создание личного чата"""
        try:
            from core.redis_events import publish_chat_created
        except Exception:
            publish_chat_created = lambda x: None

        user2_id = request.data.get('user2')
        
        if not user2_id:
            return Response({'error': 'Укажите пользователя для создания чата'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, не создаем ли чат с самим собой
        if user2 == request.user:
            return Response({'error': 'Нельзя создать чат с самим собой'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, не существует ли уже чат
        existing_chat = PrivateChat.objects.filter(
            models.Q(user1=request.user, user2=user2) | 
            models.Q(user1=user2, user2=request.user)
        ).first()
        
        if existing_chat:
            # Возвращаем существующий чат
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data)

        # Создаем новый чат
        chat = PrivateChat.objects.create(user1=request.user, user2=user2)
        
        # Публикуем событие о создании чата для обоих пользователей
        try:
            publish_chat_created({
                'chat_id': chat.id,
                'chat_type': 'private',
                'created_by': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'display_name': request.user.display_name or request.user.username,
                    'avatar': request.user.avatar.url if request.user.avatar else None
                },
                'participants': [request.user.id, user2.id],
                'other_user': {
                    'id': user2.id,
                    'username': user2.username,
                    'display_name': user2.display_name or user2.username,
                    'avatar': user2.avatar.url if user2.avatar else None
                },
                'created_at': chat.created_at.isoformat()
            })
        except Exception as e:
            print(f"DEBUG: Error publishing chat created event: {e}")
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

@action(detail=True, methods=['post'])
def mark_as_read(self, request, pk=None):
    """Отметить сообщения личного чата как прочитанные и вернуть IDs прочитанных сообщений"""
    from .chat_cache import ChatCacheService
    from .models import Message, MessageReadStatus
    from core.redis_events import event_publisher
    
    try:
        chat = PrivateChat.objects.get(id=pk)
    except PrivateChat.DoesNotExist:
        return Response({'error': 'Чат не найден'}, status=404)

    # Проверяем доступ
    if request.user not in [chat.user1, chat.user2]:
        return Response({'error': 'Нет доступа к чату'}, status=403)

    # Получаем IDs сообщений для отметки (или все непрочитанные)
    message_ids = request.data.get('message_ids', [])
    
    if message_ids:
        # Отмечаем только указанные сообщения
        unread_messages = Message.objects.filter(
            private_chat=chat,
            id__in=message_ids
        ).exclude(sender=request.user)
    else:
        # Отмечаем все непрочитанные
        unread_messages = Message.objects.filter(
            private_chat=chat
        ).exclude(
            Q(sender=request.user) | 
            Q(read_statuses__user=request.user)
        )

    # Создаём записи MessageReadStatus
    read_message_ids = []
    for message in unread_messages:
        _, created = MessageReadStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        if created:
            read_message_ids.append(message.id)

    # Сбрасываем счётчик непрочитанных в кэше
    ChatCacheService.reset_unread(request.user.id, chat.id)
    
    # Отправляем WebSocket событие другим участникам чата
    if read_message_ids:
        try:
            # Определяем другого пользователя
            other_user_id = chat.user2_id if chat.user1_id == request.user.id else chat.user1_id
            
            # Публикуем событие через Redis
            event_publisher.publish_event('messages_read', {
                'chat_id': chat.id,
                'chat_type': 'private',
                'user_id': request.user.id,
                'message_ids': read_message_ids,
                'read_at': timezone.now().isoformat()
            }, target_users=[other_user_id])
            
        except Exception as e:
            print(f"Error sending WS event: {e}")
    
    return Response({
        'message': 'Сообщения отмечены как прочитанные',
        'read_message_ids': read_message_ids
    })


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.filter(is_deleted=False)
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем по чатам, к которым у пользователя есть доступ
        user = self.request.user
        group_chats = GroupChat.objects.filter(members__user=user).values_list('id', flat=True)
        private_chats = PrivateChat.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).values_list('id', flat=True)

        return Message.objects.filter(
            models.Q(chat_id__in=list(group_chats)) |
            models.Q(private_chat_id__in=list(private_chats))
        ).select_related('sender', 'chat', 'private_chat')

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


class CreateGroupChatView(APIView):
    """Создание группового чата с поддержкой FormData"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import json
        from core.redis_events import event_publisher

        # Получаем данные из FormData
        name = request.data.get('name')
        description = request.data.get('description', '')
        avatar = request.data.get('avatar')

        print(f"DEBUG: Создание чата - name={name}, avatar={avatar}")
        print(f"DEBUG: avatar type = {type(avatar)}")
        if avatar:
            print(f"DEBUG: avatar.name = {avatar.name}, avatar.size = {avatar.size}")

        # Парсим participants из строки если нужно
        participants_raw = request.data.get('participants')
        if isinstance(participants_raw, str):
            try:
                participants = json.loads(participants_raw)
            except json.JSONDecodeError:
                participants = []
        elif isinstance(participants_raw, list):
            participants = participants_raw
        else:
            participants = []

        # Валидация
        if not name:
            return Response({'error': 'Название чата обязательно'}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем чат
        chat = GroupChat.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        print(f"DEBUG: Чат создан, id={chat.id}")

        # Сохраняем аватарку если есть
        if avatar:
            print(f"DEBUG: Сохраняем аватарку: {avatar}")
            print(f"DEBUG: avatar type = {type(avatar)}")
            print(f"DEBUG: avatar.name = {avatar.name}")
            try:
                chat.avatar.save(avatar.name, avatar, save=True)
                print(f"DEBUG: Аватарка сохранена, путь: {chat.avatar}")
                print(f"DEBUG: Аватарка URL: {chat.avatar.url}")
            except Exception as e:
                print(f"DEBUG: Ошибка сохранения аватарки: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("DEBUG: Аватарка не выбрана, генерируем дефолтную")
            # Генерируем дефолтную аватарку
            try:
                from social.serializers import GroupChatCreateSerializer
                serializer = GroupChatCreateSerializer()
                serializer._generate_default_avatar(chat)
                print(f"DEBUG: Дефолтная аватарка сгенерирована, путь: {chat.avatar}")
            except Exception as e:
                print(f"DEBUG: Ошибка генерации аватарки: {e}")

        # Добавляем создателя как админа
        ChatMember.objects.create(
            user=request.user,
            chat=chat,
            is_admin=True
        )

        # Добавляем участников
        participant_ids = [request.user.id]
        for user_id in participants:
            try:
                user = User.objects.get(id=user_id)
                member, created = ChatMember.objects.get_or_create(
                    user=user,
                    chat=chat,
                    defaults={
                        'can_send_messages': True,
                        'can_send_media': chat.can_send_media,
                        'is_admin': False,
                        'is_muted': False
                    }
                )
                participant_ids.append(user_id)
                print(f"DEBUG: Добавлен участник {user_id} в группу {chat.id}")
            except User.DoesNotExist:
                print(f"DEBUG: Пользователь {user_id} не найден")
                continue

        # Публикуем событие о создании группы для всех участников
        try:
            event_publisher.publish_event('group_chat_created', {
                'chat_id': chat.id,
                'chat_type': 'group',
                'created_by': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'display_name': request.user.display_name or request.user.username,
                    'avatar': request.user.avatar.url if request.user.avatar else None
                },
                'chat_name': chat.name,
                'participants': participant_ids,
                'created_at': chat.created_at.isoformat()
            })
        except Exception as e:
            print(f"DEBUG: Error publishing group chat created event: {e}")

        # Логируем
        ChatAdminLog.objects.create(
            chat=chat,
            user=request.user,
            action='chat_created',
            details={'chat_name': chat.name, 'participants_count': len(participants) + 1}
        )

        return Response(GroupChatSerializer(chat).data, status=status.HTTP_201_CREATED)


# Настройки чатов
class PrivateChatSettingsView(APIView):
    """Персональные настройки личного чата (только для того, кто изменяет)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """Получить настройки чата для текущего пользователя"""
        try:
            chat = PrivateChat.objects.get(id=chat_id)
        except PrivateChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)

        # Проверяем доступ
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа к чату'}, status=403)

        # Получаем или создаем настройки
        settings, created = PrivateChatUserSettings.objects.get_or_create(
            chat=chat,
            user=request.user,
            defaults={'notifications_enabled': True}
        )

        serializer = PrivateChatUserSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)

    def put(self, request, chat_id):
        """Обновить настройки чата (только для текущего пользователя)"""
        try:
            chat = PrivateChat.objects.get(id=chat_id)
        except PrivateChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)

        # Проверяем доступ
        if request.user not in [chat.user1, chat.user2]:
            return Response({'error': 'Нет доступа к чату'}, status=403)

        # Обрабатываем FormData
        custom_name = request.data.get('custom_name', '')
        avatar = request.data.get('custom_avatar')
        notifications = request.data.get('notifications_enabled')

        # Обновляем или создаем настройки
        settings, created = PrivateChatUserSettings.objects.update_or_create(
            chat=chat,
            user=request.user,
            defaults={
                'custom_name': custom_name,
                'notifications_enabled': notifications if notifications is not None else True
            }
        )

        # Сохраняем аватарку если есть
        if avatar and hasattr(avatar, 'name'):
            settings.custom_avatar.save(avatar.name, avatar, save=True)

        serializer = PrivateChatUserSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)


class GroupChatSettingsView(APIView):
    """Общие настройки группового чата (для всех участников)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """Получить настройки чата"""
        try:
            chat = GroupChat.objects.get(id=chat_id)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)

        # Проверяем, что пользователь участник
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'error': 'Нет доступа к чату'}, status=403)

        serializer = GroupChatSerializer(chat, context={'request': request})
        return Response(serializer.data)

    def put(self, request, chat_id):
        """Обновить настройки чата (общие для всех)"""
        try:
            chat = GroupChat.objects.get(id=chat_id)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)

        # Проверяем, что пользователь участник
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'error': 'Нет доступа к чату'}, status=403)

        # Проверяем права на изменение настроек (владелец или админ)
        member = ChatMember.objects.get(chat=chat, user=request.user)
        is_owner = chat.created_by == request.user
        is_admin = member.is_admin

        if not (is_owner or is_admin):
            return Response({'error': 'Нет прав на изменение настроек чата'}, status=403)

        serializer = GroupChatSerializer(
            chat,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            # Обрабатываем аватарку отдельно если это FormData
            avatar = request.data.get('avatar')
            if avatar and hasattr(avatar, 'name'):
                chat.avatar.save(avatar.name, avatar, save=True)

            serializer.save()

            # Логируем
            ChatAdminLog.objects.create(
                chat=chat,
                user=request.user,
                action='chat_updated',
                details={'updated_fields': list(request.data.keys())}
            )
            
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


class ChatSettingsListView(APIView):
    """Список настроек всех чатов пользователя"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить все настройки чатов пользователя"""
        # Настройки личных чатов
        private_settings = PrivateChatUserSettings.objects.filter(user=request.user)

        # Настройки групповых чатов (общие)
        group_chats = GroupChat.objects.filter(members__user=request.user)

        return Response({
            'private_chats': PrivateChatUserSettingsSerializer(
                private_settings, many=True, context={'request': request}
            ).data,
            'group_chats': GroupChatSerializer(
                group_chats, many=True, context={'request': request}
            ).data
        })


# ==================== FOLLOW SYSTEM ====================

class FollowViewSet(ModelViewSet):
    """Подписки на пользователей"""
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)

    def perform_create(self, serializer):
        following_id = self.request.data.get('following')
        if following_id == self.request.user.id:
            raise ValidationError("Нельзя подписаться на самого себя")
        serializer.save(follower=self.request.user)

    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Получить подписчиков пользователя"""
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                user_id = request.user.id
        else:
            user_id = request.user.id
        
        follows = Follow.objects.filter(following_id=user_id).select_related('follower__profile')
        serializer = FollowSerializer(follows, many=True)
        return Response(serializer.data)