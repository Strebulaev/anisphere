from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import models
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Comment, Group, GroupMembership, Post, ChatSettings, Message, Contest, ContestEntry, ContestVote
from .models import GroupChat, ChatRole, ChatMember, ChatAdminLog, PrivateChat, ChatTypingStatus, PrivateChatUserSettings, PrivateChatUserSettings
from users.models import User
from .serializers import (
    CommentSerializer, CommentCreateSerializer,
    GroupSerializer, GroupCreateSerializer, GroupMembershipSerializer,
    PostSerializer, PostCreateSerializer,
    ChatSettingsSerializer,
    MessageSerializer,
    ContestSerializer, ContestEntrySerializer, ContestVoteSerializer,
    GroupChatSerializer, GroupChatCreateSerializer, ChatRoleSerializer, ChatMemberSerializer, ChatAdminLogSerializer,
    PrivateChatSerializer, PrivateChatUserSettingsSerializer
)
from .permissions import IsChatOwner, HasChatPermission, IsChatMember
from core.redis_events import publish_post_created, publish_message_sent, publish_user_online, publish_user_offline
from notifications.services import notification_service


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
                models.Q(user1=user) | models.Q(user2=user)
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


class PostViewSet(ModelViewSet):
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateSerializer
        return PostSerializer

    def get_queryset(self):
        queryset = Post.objects.filter(is_deleted=False).select_related('author', 'anime', 'group')

        # Фильтр по группе
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        # Фильтр по аниме
        anime_id = self.request.query_params.get('anime')
        if anime_id:
            queryset = queryset.filter(anime_id=anime_id)

        # Лента пользователя (посты от подписок + собственные)
        if self.request.query_params.get('feed') == 'true':
            # Для простоты - все посты, кроме своих групп
            # TODO: Добавить систему подписок
            queryset = queryset.exclude(group__isnull=False)

        return queryset

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)

        # Публикуем событие создания поста
        publish_post_created({
            'post_id': post.id,
            'author_id': post.author.id,
            'author_username': post.author.username,
            'text': post.text[:200] if post.text else '',
            'created_at': post.created_at.isoformat()
        })


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

            # Публикуем событие отправки сообщения
            publish_message_sent({
                'message_id': message.id,
                'chat_id': chat_id,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'text': message.text[:200] if message.text else '',
                'created_at': message.created_at.isoformat()
            })

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
        ).prefetch_related('members', 'members__user')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Получить сообщения чата"""
        chat = self.get_object()
        messages = Message.objects.filter(chat=chat).order_by('-created_at')[:100]
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class PrivateChatViewSet(ModelViewSet):
    queryset = PrivateChat.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return PrivateChatSerializer

    def get_queryset(self):
        return PrivateChat.objects.filter(
            models.Q(user1=self.request.user) | models.Q(user2=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save()


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
        for user_id in participants:
            try:
                user = User.objects.get(id=user_id)
                ChatMember.objects.create(
                    user=user,
                    chat=chat,
                    can_send_messages=True,
                    can_send_media=chat.can_send_media
                )
            except User.DoesNotExist:
                continue

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