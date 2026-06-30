from datetime import timedelta
from urllib import request
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q, Count, F, Case, When, Value, IntegerField
from asgiref.sync import async_to_sync
from rest_framework import generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import (
    Comment,
    Group,
    GroupMembership,
    Post,
    ChatSettings,
    Message,
    Contest,
    ContestEntry,
    ContestVote,
    GroupChat,
    ChatRole,
    ChatMember,
    ChatAdminLog,
    PrivateChat,
    ChatTypingStatus,
    PrivateChatUserSettings,
    Follow,
    PostLike,
    PostDislike,
    Repost,
    Achievement,
    UserAchievement,
    UploadedFile,
    Favorite,
    ChatInvite,
    Reaction,
    Attachment,
    EmailLog,
    ChatFolder,
    ChatFolderChat,
    PostMedia,
    PostAttachment,
    PostComment,
    PostCommentLike,
    PostCommentDislike,
    FeedView,
    Bookmark,
    Report,
    Hashtag,
    PostHashtag,
    UserMention,
)
from .models import MessageReadStatus
from rest_framework.pagination import PageNumberPagination
from .serializers import FeedPostSerializer, PrivateChatCreateSerializer
from users.models import User
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    GroupSerializer,
    GroupCreateSerializer,
    GroupMembershipSerializer,
    PostSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
    ChatSettingsSerializer,
    MessageSerializer,
    ContestSerializer,
    ContestEntrySerializer,
    ContestVoteSerializer,
    GroupChatSerializer,
    GroupChatCreateSerializer,
    GroupChatSettingsSerializer,
    ChatRoleSerializer,
    ChatMemberSerializer,
    ChatAdminLogSerializer,
    PrivateChatSerializer,
    PrivateChatCreateSerializer,
    PrivateChatUserSettingsSerializer,
    FollowSerializer,
    PostLikeSerializer,
    PostDislikeSerializer,
    RepostSerializer,
    AchievementSerializer,
    UserAchievementSerializer,
    UploadedFileSerializer,
    FavoriteSerializer,
    ChatInviteSerializer,
    ChatInviteCreateSerializer,
    ReactionSerializer,
    ReactionCreateSerializer,
    AttachmentSerializer,
    AttachmentCreateSerializer,
    EmailLogSerializer,
    EmailLogCreateSerializer,
    ChatFolderSerializer,
    ChatFolderCreateSerializer,
    ChatFolderPreviewSerializer,
    FeedPostSerializer,
    PostMediaSerializer,
    PostAttachmentSerializer,
    PostCommentSerializer,
    PostCommentCreateSerializer,
    BookmarkSerializer,
    BookmarkCreateSerializer,
    ReportSerializer,
    ReportCreateSerializer,
    HashtagSerializer,
)
from .permissions import IsChatOwner, HasChatPermission, IsChatMember
from core.redis_events import (
    publish_post_created,
    publish_message_sent,
    publish_user_online,
    publish_user_offline,
)
from notifications.services import notification_service
from .serializers import FeedPostSerializer

# ==================== UNREAD CHATS ====================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_unread_chats(request):
    """Получить чаты с непрочитанными сообщениями (из БД)"""
    from .models import MessageReadStatus

    try:
        user = request.user
        chats_data = []

        # Получаем ID чатов, где пользователь участник
        member_chat_ids = ChatMember.objects.filter(user=user).values_list(
            "chat_id", flat=True
        )
        private_chat_ids = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).values_list("id", flat=True)

        # Получаем все сообщения, отправленные НЕ пользователем
        unread_message_chats = Message.objects.filter(
            Q(chat_id__in=member_chat_ids) | Q(private_chat_id__in=private_chat_ids)
        ).exclude(sender=user)

        # Исключаем уже прочитанные
        read_message_ids = MessageReadStatus.objects.filter(user=user).values_list(
            "message_id", flat=True
        )
        unread_message_chats = unread_message_chats.exclude(id__in=read_message_ids)

        # Группируем по чатам
        unread_by_chat = {}
        for msg in unread_message_chats.select_related("chat", "private_chat"):
            if msg.chat_id:
                chat_id = msg.chat_id
                chat_type = "group"
            else:
                chat_id = msg.private_chat_id
                chat_type = "private"

            if chat_id not in unread_by_chat:
                unread_by_chat[chat_id] = {"type": chat_type, "count": 0}
            unread_by_chat[chat_id]["count"] += 1

        # Получаем данные чатов
        for chat_id, data in unread_by_chat.items():
            if data["type"] == "group":
                chat = GroupChat.objects.filter(id=chat_id).first()
                if chat:
                    chats_data.append(
                        {
                            "id": chat.id,
                            "type": "group",
                            "name": chat.name,
                            "avatar_url": chat.avatar.url if chat.avatar else None,
                            "unread_count": data["count"],
                        }
                    )
            else:
                chat = PrivateChat.objects.filter(id=chat_id).first()
                if chat:
                    other_user = chat.user1 if chat.user2 == user else chat.user2
                    chats_data.append(
                        {
                            "id": chat.id,
                            "type": "private",
                            "name": other_user.display_name or other_user.username,
                            "avatar_url": other_user.avatar.url
                            if other_user.avatar
                            else None,
                            "unread_count": data["count"],
                        }
                    )

        return Response(chats_data)
    except Exception as e:
        print(f"DEBUG: Ошибка get_unread_chats: {e}")
        import traceback

        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
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
            unread_messages = Message.objects.filter(chat=chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )

            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))

            if read_statuses:
                MessageReadStatus.objects.bulk_create(
                    read_statuses, ignore_conflicts=True
                )

            # Отправляем WebSocket событие
            try:
                from core.redis_events import event_publisher

                event_publisher.publish_event(
                    "unread_count_updated",
                    {"chat_id": chat_id, "chat_type": "group", "user_id": user.id},
                )
            except Exception as ws_err:
                print(f"DEBUG: Error sending WS event: {ws_err}")

            return Response({"message": "Групповой чат отмечен как прочитанный"})

        # Пробуем личный чат
        private_chat = PrivateChat.objects.filter(
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        ).first()

        if private_chat:
            # Создаём статусы прочтения для всех непрочитанных сообщений
            unread_messages = Message.objects.filter(private_chat=private_chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )

            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))

            if read_statuses:
                MessageReadStatus.objects.bulk_create(
                    read_statuses, ignore_conflicts=True
                )

            # Отправляем WebSocket событие
            try:
                from core.redis_events import event_publisher

                event_publisher.publish_event(
                    "unread_count_updated",
                    {"chat_id": chat_id, "chat_type": "private", "user_id": user.id},
                )
            except Exception as ws_err:
                print(f"DEBUG: Error sending WS event: {ws_err}")

            return Response({"message": "Личный чат отмечен как прочитанный"})

        return Response({"error": "Чат не найден"}, status=404)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_private_chat_read(request, chat_id):
    """Отметить личный чат как прочитанный"""
    # Просто вызываем ту же логику, что и в mark_chat_read
    return _mark_chat_as_read(request, chat_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_group_chat_read(request, chat_id):
    """Отметить групповой чат как прочитанный"""
    # Просто вызываем ту же логику, что и в mark_chat_read
    return _mark_chat_as_read(request, chat_id)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Получить общее количество непрочитанных сообщений (из БД)"""
    from django.db.models import Count, Q, OuterRef, Exists

    try:
        user = request.user
        chat_id = request.query_params.get("chat_id")

        if chat_id:
            # Получаем непрочитанные для конкретного чата
            unread_count = 0

            # Пробуем групповой чат
            chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
            if chat:
                unread_count = (
                    Message.objects.filter(chat=chat)
                    .exclude(Q(sender=user) | Q(read_statuses__user=user))
                    .count()
                )
            else:
                # Пробуем личный чат
                private_chat = PrivateChat.objects.filter(
                    Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
                ).first()
                if private_chat:
                    unread_count = (
                        Message.objects.filter(private_chat=private_chat)
                        .exclude(Q(sender=user) | Q(read_statuses__user=user))
                        .count()
                    )

            return Response({"unread_count": unread_count})
        else:
            # Общее количество непрочитанных
            # Групповые чаты
            group_unread = (
                Message.objects.filter(chat__members__user=user)
                .exclude(Q(sender=user) | Q(read_statuses__user=user))
                .distinct()
                .count()
            )

            # Личные чаты
            private_unread = (
                Message.objects.filter(private_chat__user1=user)
                .exclude(Q(sender=user) | Q(read_statuses__user=user))
                .distinct()
                .count()
            )

            private_unread2 = (
                Message.objects.filter(private_chat__user2=user)
                .exclude(Q(sender=user) | Q(read_statuses__user=user))
                .distinct()
                .count()
            )

            total_unread = group_unread + private_unread + private_unread2

            return Response({"unread_count": total_unread})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return Response({"unread_count": 0, "error": str(e)})


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
            group_chats = (
                GroupChat.objects.filter(members__user=user)
                .select_related("created_by")
                .prefetch_related("members__user")
            )

            # Добавляем групповые чаты
            for chat in group_chats:
                # Получаем последнее сообщение
                try:
                    last_message = (
                        Message.objects.filter(chat=chat)
                        .order_by("-created_at")
                        .first()
                    )
                except:
                    last_message = None

                # Аватарка: своя → постер аниме → None
                avatar_url = None
                if chat.avatar:
                    avatar_url = request.build_absolute_uri(chat.avatar.url)
                elif chat.anime and chat.anime.poster:
                    try:
                        avatar_url = request.build_absolute_uri(chat.anime.poster.url)
                    except Exception:
                        avatar_url = getattr(chat.anime, "poster_url", None)
                elif chat.franchise_id and chat.anime is None:
                    # Франшизный чат без аниме - берём постер первого аниме франшизы
                    try:
                        from anime.models import Anime as AnimeModel

                        first = (
                            AnimeModel.objects.filter(franchise_id=chat.franchise_id)
                            .exclude(poster="")
                            .order_by("franchise_order", "id")
                            .first()
                        )
                        if first and first.poster:
                            avatar_url = request.build_absolute_uri(first.poster.url)
                    except Exception:
                        pass

                chat_data = {
                    "id": chat.id,
                    "type": "group",
                    "name": chat.name,
                    "avatar_url": avatar_url,
                    "franchise_id": chat.franchise_id,
                    "discussion_type": chat.discussion_type,
                    "participants_usernames": [
                        member.user.username for member in chat.members.all()
                    ],
                    "last_message_text": last_message.text if last_message else None,
                    "last_message_sender": last_message.sender.username
                    if last_message
                    else None,
                    "updated_at": (chat.last_message_at or chat.created_at).isoformat(),
                    "created_at": chat.created_at.isoformat(),
                }
                chats_data.append(chat_data)

                print(f"DEBUG: Добавлен групповой чат {chat.id}: {chat.name}")
        except Exception as e:
            print(f"DEBUG: Ошибка при получении групповых чатов: {e}")

        try:
            # Личные чаты пользователя
            private_chats = PrivateChat.objects.filter(
                Q(user1=user) | Q(user2=user)
            ).select_related("user1", "user2")

            # Импортируем online_status
            from core.online_status import online_status

            # Добавляем личные чаты
            for chat in private_chats:
                other_user = chat.user1 if chat.user2 == user else chat.user2

                # Проверяем онлайн статус через Redis
                is_online = online_status.is_online(other_user.id)

                # Получаем кастомные настройки пользователя
                try:
                    user_settings = PrivateChatUserSettings.objects.get(
                        chat=chat, user=user
                    )
                    custom_name = user_settings.custom_name
                    custom_avatar = (
                        user_settings.custom_avatar.url
                        if user_settings.custom_avatar
                        else None
                    )
                except PrivateChatUserSettings.DoesNotExist:
                    custom_name = None
                    custom_avatar = None

                # Получаем последнее сообщение
                try:
                    last_message = (
                        Message.objects.filter(private_chat=chat)
                        .order_by("-created_at")
                        .first()
                    )
                except:
                    last_message = None

                chat_data = {
                    "id": chat.id,
                    "type": "private",
                    "name": custom_name,  # Кастомное название пользователя
                    "avatar_url": custom_avatar
                    or (other_user.avatar.url if other_user.avatar else None),
                    "participants_usernames": [other_user.username],
                    "other_user": {
                        "id": other_user.id,
                        "username": other_user.username,
                        "display_name": other_user.display_name or other_user.username,
                        "avatar": other_user.avatar.url if other_user.avatar else None,
                        "is_online": is_online,
                    },
                    "last_message_text": last_message.text if last_message else None,
                    "last_message_sender": last_message.sender.username
                    if last_message
                    else None,
                    "updated_at": chat.last_message_at.isoformat()
                    if chat.last_message_at
                    else chat.created_at.isoformat(),
                    "created_at": chat.created_at.isoformat(),
                }
                chats_data.append(chat_data)

                print(f"DEBUG: Добавлен личный чат {chat.id}")
        except Exception as e:
            print(f"DEBUG: Ошибка при получении личных чатов: {e}")

        # Сортируем по времени последнего обновления
        chats_data.sort(key=lambda x: x["updated_at"], reverse=True)

        print(f"DEBUG: Всего найдено чатов: {len(chats_data)}")

        return Response(chats_data)


@api_view(["GET"])
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
                user_settings = PrivateChatUserSettings.objects.get(
                    chat=private_chat, user=request.user
                )
                custom_name = user_settings.custom_name
                custom_avatar_url = (
                    user_settings.custom_avatar.url
                    if user_settings.custom_avatar
                    else None
                )
            except PrivateChatUserSettings.DoesNotExist:
                custom_name = None
                custom_avatar_url = None

            # Проверяем онлайн статус через Redis
            from core.online_status import online_status

            is_online = online_status.is_online(other_user.id)

            # Получаем счётчик непрочитанных сообщений от other_user (упрощённо)
            try:
                from .chat_cache import ChatCacheService

                unread_count_for_other = ChatCacheService.get_unread_count(
                    other_user.id, private_chat.id
                )
            except Exception as e:
                print(f"DEBUG: Ошибка подсчёта непрочитанных: {e}")
                unread_count_for_other = 0

            # Создаем словарь с данными
            chat_data = {
                "id": private_chat.id,
                "type": "private",
                "name": custom_name,  # Кастомное название пользователя
                "avatar_url": custom_avatar_url
                or (other_user.avatar.url if other_user.avatar else None),
                "user1": private_chat.user1.id,
                "user2": private_chat.user2.id,
                "created_at": private_chat.created_at,
                "last_message_at": private_chat.last_message_at,
                "unread_count": unread_count_for_other,  # Непрочитанные у другого пользователя
                "other_user": {
                    "id": other_user.id,
                    "username": other_user.username,
                    "display_name": other_user.display_name or other_user.username,
                    "avatar": other_user.avatar.url if other_user.avatar else None,
                    "is_online": is_online,
                },
            }

            print(
                f"DEBUG: Возвращаем данные личного чата: name={custom_name}, avatar_url={custom_avatar_url}"
            )
            return Response(chat_data)

        except PrivateChat.DoesNotExist:
            print(f"DEBUG: Личный чат {pk} не найден или нет доступа")
            pass

        # 2. Проверяем групповые чаты
        try:
            group_chat = GroupChat.objects.get(id=pk, members__user=request.user)
            print(f"DEBUG: Найден групповой чат: {group_chat.id}")

            # Сериализуем данные
            serializer = GroupChatSerializer(group_chat, context={"request": request})
            data = serializer.data
            data["type"] = "group"  # Добавляем тип чата

            print(f"DEBUG: Возвращаем данные группового чата")
            return Response(data)

        except GroupChat.DoesNotExist:
            print(f"DEBUG: Групповой чат {pk} не найден или нет доступа")
            pass

        # 3. Если ничего не нашли
        return Response(
            {
                "error": "Чат не найден",
                "message": f"Чат с ID {pk} не существует или у вас нет к нему доступа",
                "user_id": request.user.id,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        print(f"DEBUG: Ошибка в get_chat_detail: {str(e)}")
        import traceback

        traceback.print_exc()

        return Response(
            {"error": f"Ошибка сервера: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        content_type_str = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")

        if not content_type_str or not object_id:
            return Comment.objects.none()

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            return Comment.objects.filter(
                content_type=content_type, object_id=object_id, is_deleted=False
            ).select_related("author")
        except ContentType.DoesNotExist:
            return Comment.objects.none()

    def perform_create(self, serializer):
        content_type_str = self.request.data.get("content_type")
        object_id = self.request.data.get("object_id")

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            serializer.save(
                author=self.request.user, content_type=content_type, object_id=object_id
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


# ==================== FOLLOW VIEW SET ====================


class FollowViewSet(ModelViewSet):
    """ViewSet для подписок/подписчиков"""

    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)

    def get_followers_queryset(self):
        """Получить подписчиков текущего пользователя"""
        return Follow.objects.filter(following=self.request.user)

    def get_following_queryset(self):
        """Получить подписки текущего пользователя"""
        return Follow.objects.filter(follower=self.request.user)

    @action(detail=False, methods=["get"])
    def check(self, request):
        """Проверить, подписан ли текущий пользователь на указанного"""
        following_id = request.query_params.get("following_id")
        if not following_id:
            return Response({"error": "following_id required"}, status=400)

        try:
            target_user = User.objects.get(id=following_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        is_following = Follow.objects.filter(
            follower=request.user, following=target_user
        ).exists()

        return Response(
            {"is_following": is_following, "following_id": int(following_id)}
        )

    @action(detail=False, methods=["get"])
    def followers(self, request):
        """Получить список подписчиков"""
        follows = self.get_followers_queryset().select_related("follower")
        data = []
        for follow in follows:
            data.append(
                {
                    "id": follow.id,
                    "user": {
                        "id": follow.follower.id,
                        "username": follow.follower.username,
                        "display_name": follow.follower.display_name,
                        "avatar_url": follow.follower.avatar.url
                        if follow.follower.avatar
                        else None,
                    },
                    "created_at": follow.created_at.isoformat(),
                }
            )
        return Response(data)

    @action(detail=False, methods=["get"])
    def following(self, request):
        """Получить список подписок"""
        follows = self.get_following_queryset().select_related("following")
        data = []
        for follow in follows:
            data.append(
                {
                    "id": follow.id,
                    "user": {
                        "id": follow.following.id,
                        "username": follow.following.username,
                        "display_name": follow.following.display_name,
                        "avatar_url": follow.following.avatar.url
                        if follow.following.avatar
                        else None,
                    },
                    "created_at": follow.created_at.isoformat(),
                }
            )
        return Response(data)

    @action(detail=False, methods=["get"])
    def is_following(self, request):
        """Проверить, подписан ли текущий пользователь на указанного"""
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id required"}, status=400)

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        is_following = Follow.objects.filter(
            follower=request.user, following=target_user
        ).exists()

        return Response({"is_following": is_following})


# ==================== POST COMMENTS VIEW SET ====================


class PostCommentViewSet(ModelViewSet):
    """ViewSet для комментариев к постам (ленты)"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostCommentCreateSerializer
        return PostCommentSerializer

    def get_queryset(self):
        post_pk = self.kwargs.get("post_pk")
        if not post_pk:
            return PostComment.objects.none()

        # Получаем ВСЕ комментарии (и корневые, и ответы)
        queryset = PostComment.objects.filter(
            post_id=post_pk, is_deleted=False
        ).select_related("author", "parent", "parent__author")

        # Сортировка: всегда по дате (новые сверху)
        queryset = queryset.order_by("-created_at")

        return queryset

    def perform_create(self, serializer):
        post_pk = self.kwargs.get("post_pk")
        post = Post.objects.get(id=post_pk)

        if not post.allow_comments:
            raise PermissionDenied("Комментарии к этому посту закрыты")

        # parent is already resolved by the serializer from validated_data['parent']
        # We just pass post and author; serializer.create() handles path/level/counters
        comment = serializer.save(
            post=post,
            author=self.request.user,
        )

        # Отправляем уведомление автору поста о новом комментарии
        if post.author_id != self.request.user.id:
            try:
                from notifications.services import NotificationService

                NotificationService.create_notification(
                    user=post.author,
                    notification_type="comment",
                    title="Новый комментарий",
                    content=f"{self.request.user.username} прокомментировал ваш пост",
                    link=f"/post/{post.id}",
                    icon="💬",
                )
            except Exception as e:
                print(f"Failed to send comment notification: {e}")
            
        # Если это ответ на комментарий, отправляем уведомление автору родительского комментария
        if comment.parent_id:
            try:
                parent_comment = PostComment.objects.get(id=comment.parent_id)
                if (
                    parent_comment.author_id != self.request.user.id
                    and parent_comment.author_id != post.author_id
                ):
                    from notifications.services import NotificationService

                    NotificationService.create_notification(
                        user=parent_comment.author,
                        notification_type="reply",
                        title="Ответ на ваш комментарий",
                        content=f"{self.request.user.username} ответил на ваш комментарий",
                        link=f"/post/{post.id}#comment-{comment.id}",
                        icon="↩️",
                    )
            except PostComment.DoesNotExist:
                pass
            except Exception as e:
                print(f"Failed to send reply notification: {e}")

    def perform_destroy(self, instance):
        # Мягкое удаление
        instance.is_deleted = True
        instance.content = "[комментарий удалён]"
        instance.author = None  # Скрываем автора
        instance.save()

        # Обновляем счётчики
        post = instance.post
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=["comments_count"])

        if instance.parent:
            instance.parent.replies_count = max(0, instance.parent.replies_count - 1)
            instance.parent.save(update_fields=["replies_count"])


# ==================== COMMENT LIKES ====================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """Лайкнуть/дизлайкнуть комментарий (лайк)"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    # Нельзя лайкать свой комментарий
    if comment.author == request.user:
        return Response({"error": "Нельзя лайкать свой комментарий"}, status=400)

    # Проверяем текущую реакцию
    existing_like = PostCommentLike.objects.filter(
        user=request.user, comment=comment
    ).first()

    existing_dislike = PostCommentDislike.objects.filter(
        user=request.user, comment=comment
    ).first()

    if existing_like:
        # Удаляем лайк
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=["likes_count"])
        return Response(
            {
                "success": True,
                "liked": False,
                "likes_count": comment.likes_count,
                "dislikes_count": comment.dislikes_count,
            }
        )

    # Удаляем дизлайк, если есть
    if existing_dislike:
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)

    # Создаём лайк
    PostCommentLike.objects.create(user=request.user, comment=comment)
    comment.likes_count += 1
    comment.save(update_fields=["likes_count", "dislikes_count"])

    return Response(
        {
            "success": True,
            "liked": True,
            "likes_count": comment.likes_count,
            "dislikes_count": comment.dislikes_count,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    """Дизлайкнуть комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    # Нельзя дизлайкать свой комментарий
    if comment.author == request.user:
        return Response({"error": "Нельзя дизлайкать свой комментарий"}, status=400)

    # Проверяем текущую реакцию
    existing_dislike = PostCommentDislike.objects.filter(
        user=request.user, comment=comment
    ).first()

    existing_like = PostCommentLike.objects.filter(
        user=request.user, comment=comment
    ).first()

    if existing_dislike:
        # Удаляем дизлайк
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=["dislikes_count"])
        return Response(
            {
                "success": True,
                "disliked": False,
                "likes_count": comment.likes_count,
                "dislikes_count": comment.dislikes_count,
            }
        )

    # Удаляем лайк, если есть
    if existing_like:
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)

    # Создаём дизлайк
    PostCommentDislike.objects.create(user=request.user, comment=comment)
    comment.dislikes_count += 1
    comment.save(update_fields=["likes_count", "dislikes_count"])

    return Response(
        {
            "success": True,
            "disliked": True,
            "likes_count": comment.likes_count,
            "dislikes_count": comment.dislikes_count,
        }
    )


# ==================== POST ACTIONS ====================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    """Закрепить пост в профиле"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({"error": "Нельзя закреплять чужие посты"}, status=403)

    # Снимаем закрепление с другого поста, если есть
    Post.objects.filter(author=request.user, is_pinned=True).update(
        is_pinned=False, pinned_at=None
    )

    # Закрепляем текущий пост
    post.is_pinned = True
    post.pinned_at = timezone.now()
    post.save(update_fields=["is_pinned", "pinned_at"])

    return Response({"success": True, "message": "Пост закреплён", "is_pinned": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    """Открепить пост от профиля"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({"error": "Нельзя откреплять чужие посты"}, status=403)

    # Открепляем пост
    post.is_pinned = False
    post.pinned_at = None
    post.save(update_fields=["is_pinned", "pinned_at"])

    return Response({"success": True, "message": "Пост откреплён", "is_pinned": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    """Пожаловаться на пост"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Нельзя жаловаться на свой пост
    if post.author == request.user:
        return Response({"error": "Нельзя жаловаться на свой пост"}, status=400)

    reason = request.data.get("reason", "other")
    if reason not in ["spam", "copyright", "harassment", "inappropriate", "other"]:
        return Response({"error": "Неверная причина жалобы"}, status=400)

    comment = request.data.get("comment", "")

    # Проверяем, не жаловался ли уже пользователь
    existing_report = Report.objects.filter(
        reporter=request.user, content_type="post", content_id=post_id, status="pending"
    ).first()

    if existing_report:
        return Response({"error": "Вы уже отправили жалобу на этот пост"}, status=400)

    try:
        report = Report.objects.create(
            reporter=request.user,
            content_type="post",
            content_id=post_id,
            reason=reason,
            comment=comment,
            status="pending",
        )

        logger.info(f"Report created: {report.id} by {request.user.username} on post {post_id}")
        
        # Отправляем уведомление модераторам НАПРЯМУЮ (без Celery)
        try:
            from notifications.models import Notification

            # Ищем модератора - сначала по is_staff/is_superuser
            moderator = User.objects.filter(
                models.Q(is_staff=True) | models.Q(is_superuser=True)
            ).first()

            if moderator:
                reason_display = dict(Report.REASON_CHOICES).get(reason, reason)

                # Создаём уведомление
                Notification.objects.create(
                    user=moderator,
                    type="system",
                    title=f"🚨 Новая жалоба: Пост",
                    content=f"Причина: {reason_display}\nЖалоба от: @{request.user.username}\nID поста: {post_id}",
                    link=f"/admin/social/report/{report.id}/",
                )
                logger.info(f"Moderator notification sent to {moderator.username}")
            else:
                logger.warning("No moderator found for report notification")
        except Exception as e:
            logger.warning(f"Failed to send moderator notification: {e}")
        
        return Response(
            {"success": True, "message": "Жалоба отправлена", "report_id": report.id}
        )
    except Exception as e:
        logger.error(f"Error creating report: {e}", exc_info=True)
        return Response({"error": "Ошибка при создании жалобы", "detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_bookmark(request, post_id):
    """Добавить пост в закладки"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    folder = request.data.get("folder", "")

    # Проверяем, не добавлено ли уже
    existing_bookmark = Bookmark.objects.filter(user=request.user, post=post).first()

    if existing_bookmark:
        # Обновляем папку
        existing_bookmark.folder = folder
        existing_bookmark.save(update_fields=["folder"])
        return Response(
            {
                "success": True,
                "message": "Закладка обновлена",
                "bookmarked": True,
                "folder": folder,
            }
        )

    bookmark = Bookmark.objects.create(user=request.user, post=post, folder=folder)

    return Response(
        {
            "success": True,
            "message": "Пост добавлен в закладки",
            "bookmarked": True,
            "folder": folder,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, post_id):
    """Удалить пост из закладок"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    deleted, _ = Bookmark.objects.filter(user=request.user, post=post).delete()

    if deleted:
        return Response(
            {"success": True, "message": "Пост удалён из закладок", "bookmarked": False}
        )

    return Response(
        {"success": True, "message": "Пост не был в закладках", "bookmarked": False}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bookmarks_folders(request):
    """Получить список папок закладок"""
    folders_data = Bookmark.objects.filter(user=request.user).values_list(
        "folder", flat=True
    )
    folders = list(set(folders_data))
    folders = [f for f in folders if f]  # Убираем пустые

    # Добавляем стандартные папки
    default_folders = ["watch_later", "favorite", "recipes"]
    all_folders = list(set(folders + default_folders))

    result = []
    for folder in all_folders:
        count = Bookmark.objects.filter(user=request.user, folder=folder).count()
        result.append({"name": folder, "count": count})

    # Добавляем общее количество
    total_count = Bookmark.objects.filter(user=request.user).count()
    result.insert(0, {"name": "all", "count": total_count})

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_likers(request, post_id):
    """Получить список пользователей, лайкнувших пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    likes = PostLike.objects.filter(post=post).select_related("user__profile")[:100]

    users = []
    for like in likes:
        users.append(
            {
                "id": like.user.id,
                "username": like.user.username,
                "avatar": like.user.profile.avatar.url
                if hasattr(like.user, "profile") and like.user.profile.avatar
                else None,
                "liked_at": like.created_at.isoformat(),
            }
        )

    return Response({"count": post.likes_count, "users": users})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_dislikers(request, post_id):
    """Получить список пользователей, дизлайкнувших пост (только для модераторов)"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Только модераторы могут видеть дизлайки
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"error": "Доступ запрещён"}, status=403)

    dislikes = PostDislike.objects.filter(post=post).select_related("user__profile")[
        :100
    ]

    users = []
    for dislike in dislikes:
        users.append(
            {
                "id": dislike.user.id,
                "username": dislike.user.username,
                "avatar": dislike.user.profile.avatar.url
                if hasattr(dislike.user, "profile") and dislike.user.profile.avatar
                else None,
                "disliked_at": dislike.created_at.isoformat(),
            }
        )

    return Response({"count": post.dislikes_count, "users": users})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def repost_post(request, post_id):
    """Репостнуть пост в ленту или в чат"""
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Нельзя репостнуть свой пост
    if original_post.author == request.user:
        return Response({"error": "Нельзя репостнуть свой пост"}, status=400)

    # Нельзя репостнуть системный пост
    if original_post.post_type == "system":
        return Response({"error": "Нельзя репостнуть системный пост"}, status=400)

    # Нельзя репостнуть приватный пост
    if original_post.visibility == "private":
        return Response({"error": "Нельзя репостнуть приватный пост"}, status=400)

    comment = request.data.get("comment", "")
    chat_id = request.data.get("chat_id")
    repost_type = request.data.get("type", "feed")  # 'feed' или 'chat'

    # Если указан chat_id, пересылаем в чат
    if chat_id or repost_type == "chat":
        # Определяем тип чата
        chat = None
        chat_type = None

        try:
            chat = GroupChat.objects.get(id=chat_id)
            chat_type = "group"
        except (GroupChat.DoesNotExist, TypeError, ValueError):
            try:
                chat = PrivateChat.objects.get(id=chat_id)
                chat_type = "private"
            except (PrivateChat.DoesNotExist, TypeError, ValueError):
                return Response({"error": "Чат не найден"}, status=404)

        # Проверяем доступ к чату
        if chat_type == "group":
            if not chat.members.filter(user=request.user).exists():
                return Response({"error": "Вы не состоите в этом чате"}, status=403)
        else:
            if chat.user1 != request.user and chat.user2 != request.user:
                return Response({"error": "Вы не состоите в этом чате"}, status=403)

        # Создаём сообщение с постом
        message = Message.objects.create(
            sender=request.user,
            shared_post=original_post,
            text=comment,
            chat=chat if chat_type == "group" else None,
            private_chat=chat if chat_type == "private" else None,
        )

        # Обновляем счётчик репостов/шерингов
        original_post.shares_count += 1
        original_post.save(update_fields=["shares_count"])

        from .serializers import MessageSerializer

        return Response(
            {
                "success": True,
                "message": "Пост переслан в чат",
                "message_id": message.id,
                "message": MessageSerializer(
                    message, context={"request": request}
                ).data,
            }
        )

    # Обычный репост в ленту
    # Проверяем, не репостнул ли уже
    existing_repost = Repost.objects.filter(
        user=request.user, original_post=original_post
    ).first()

    if existing_repost:
        return Response({"error": "Вы уже репостнули этот пост"}, status=400)

    # Создаём репост
    with transaction.atomic():
        # Создаём новый пост-репост
        new_post = Post.objects.create(
            author=request.user,
            post_type="repost",
            text=comment,
            status="published",
            visibility="public",
            allow_comments=True,
            original_post=original_post,
            repost_comment=comment,
        )

        # Создаём запись о репосте
        Repost.objects.create(
            user=request.user, original_post=original_post, comment=comment
        )

        # Обновляем счётчик репостов
        original_post.reposts_count += 1
        original_post.save(update_fields=["reposts_count"])

    return Response(
        {
            "success": True,
            "message": "Пост репостнут",
            "repost_id": new_post.id,
            "original_post_id": original_post.id,
            "post": PostSerializer(new_post, context={"request": request}).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unrepost_post(request, post_id):
    """Удалить репост"""
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    repost = Repost.objects.filter(
        user=request.user, original_post=original_post
    ).first()

    if not repost:
        return Response({"error": "Вы не репостнули этот пост"}, status=400)

    # Удаляем пост-репост
    Post.objects.filter(author=request.user, type="repost").filter(
        attachments__content_type="repost", attachments__object_id=original_post.id
    ).delete()

    # Удаляем запись о репосте
    repost.delete()

    # Обновляем счётчик
    original_post.reposts_count = max(0, original_post.reposts_count - 1)
    original_post.save(update_fields=["reposts_count"])

    return Response({"success": True, "message": "Репост удалён"})


# ==================== COMMENT ACTIONS ====================


@api_view(["GET"])
@permission_classes([AllowAny])
def get_comment_replies(request, comment_id):
    """Получить ответы на комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    max_depth = 3
    replies = (
        PostComment.objects.filter(parent=comment, is_deleted=False)
        .select_related("author__profile")
        .annotate(likes_count_annotation=Count("likes"))
        .order_by("-likes_count_annotation", "created_at")[:20]
    )

    # Добавляем флаг о глубине
    for reply in replies:
        if reply.level >= max_depth:
            reply.has_more_replies = True

    serializer = PostCommentSerializer(replies, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    """Пожаловаться на комментарий"""
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    # Нельзя жаловаться на свой комментарий
    if comment.author == request.user:
        return Response({"error": "Нельзя жаловаться на свой комментарий"}, status=400)

    reason = request.data.get("reason")
    if reason not in ["spam", "copyright", "harassment", "inappropriate", "other"]:
        return Response({"error": "Неверная причина жалобы"}, status=400)

    comment_text = request.data.get("comment", "")

    # Проверяем, не жаловался ли уже пользователь
    existing_report = Report.objects.filter(
        reporter=request.user,
        content_type="comment",
        content_id=comment_id,
        status="pending",
    ).first()

    if existing_report:
        return Response(
            {"error": "Вы уже отправили жалобу на этот комментарий"}, status=400
        )

    report = Report.objects.create(
        reporter=request.user,
        content_type="comment",
        content_id=comment_id,
        reason=reason,
        comment=comment_text,
        status="pending",
    )

    return Response(
        {"success": True, "message": "Жалоба отправлена", "report_id": report.id}
    )


# ==================== FEED STATISTICS ====================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feed_statistics(request):
    """Получить статистику ленты пользователя"""
    user = request.user

    # Количество постов
    posts_count = Post.objects.filter(author=user, status="published").count()

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

    following_ids = Follow.objects.filter(follower=user).values_list(
        "following_id", flat=True
    )
    new_posts_count = Post.objects.filter(
        author_id__in=following_ids,
        status="published",
        created_at__gte=timezone.now() - timedelta(days=1),
    ).count()

    return Response(
        {
            "posts_count": posts_count,
            "likes_received": likes_received,
            "comments_received": comments_received,
            "reposts_received": reposts_received,
            "bookmarks_count": bookmarks_count,
            "new_posts_count": new_posts_count,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_popular_posts(request):
    """Получить популярные посты"""
    period = request.query_params.get("period", "day")  # day, week, month, all

    if period == "day":
        since = timezone.now() - timedelta(days=1)
    elif period == "week":
        since = timezone.now() - timedelta(days=7)
    elif period == "month":
        since = timezone.now() - timedelta(days=30)
    else:
        since = None

    queryset = Post.objects.filter(
        status="published", post_type__in=["text", "image", "video", "anime"]
    )

    if since:
        queryset = queryset.filter(created_at__gte=since)

    # Сортировка по популярности (лайки + комментарии + репосты) / время
    queryset = queryset.annotate(
        popularity=F("likes_count") + F("comments_count") + F("reposts_count")
    ).order_by("-popularity")[:50]

    serializer = PostSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    """Получить посты конкретного пользователя"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=404)

    try:
        posts = (
            Post.objects.filter(author=user, status="published", is_deleted=False)
            .select_related("author", "anime", "group", "playlist", "reactor_post")
            .prefetch_related("media_files")
            .order_by("-created_at")
        )

        # Пагинация
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        offset = (page - 1) * limit

        total = posts.count()
        posts_page = posts[offset : offset + limit]

        try:
            serializer = PostSerializer(
                posts_page, many=True, context={"request": request}
            )
            return Response(
                {
                    "count": total,
                    "page": page,
                    "limit": limit,
                    "results": serializer.data,
                }
            )
        except Exception as e:
            logger.error(f"Serialization error for user {user_id}: {e}", exc_info=True)
            return Response(
                {"error": "Ошибка сериализации постов", "detail": str(e)}, status=500
            )
    except Exception as e:
        logger.error(f"Error in get_user_posts for user {user_id}: {e}", exc_info=True)
        return Response(
            {"error": "Ошибка при загрузке постов", "detail": str(e)}, status=500
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_group_posts(request, group_id):
    """Получить посты группы"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({"error": "Группа не найдена"}, status=404)

    try:
        # Проверяем доступность группы
        if group.is_private:
            if not request.user.is_authenticated:
                return Response({"error": "Группа приватная"}, status=403)

            is_member = GroupMembership.objects.filter(
                group=group, user=request.user
            ).exists()
            if not is_member:
                return Response({"error": "Вы не состоите в группе"}, status=403)

        posts = (
            Post.objects.filter(group=group, status="published", is_deleted=False)
            .select_related("author", "anime", "group", "playlist", "reactor_post")
            .prefetch_related("media_files", "attachments", "hashtag_links__hashtag")
            .order_by("-created_at")
        )

        # Пагинация
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        offset = (page - 1) * limit

        total = posts.count()
        posts_page = posts[offset : offset + limit]

        serializer = PostSerializer(posts_page, many=True, context={"request": request})
        return Response(
            {"count": total, "page": page, "limit": limit, "results": serializer.data}
        )
    except Exception as e:
        logger.error(
            f"Error in get_group_posts for group {group_id}: {e}", exc_info=True
        )
        return Response(
            {"error": "Ошибка при загрузке постов группы", "detail": str(e)}, status=500
        )


# ==================== CONTENT MODERATION ====================


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_reports(request):
    """Получить список жалоб (только для модераторов/админов)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Фильтры
        status_filter = request.query_params.get("status")  # pending, resolved, all
        content_type_filter = request.query_params.get("content_type")  # post, comment
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))
        
        # Базовый queryset
        queryset = Report.objects.select_related(
            'reporter', 'resolved_by'
        ).order_by('-created_at')
        
        # Фильтр по статусу
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        # Фильтр по типу контента
        if content_type_filter:
            queryset = queryset.filter(content_type=content_type_filter)
        
        # Пагинация
        total = queryset.count()
        reports_page = queryset[(page - 1) * per_page:page * per_page]
        
        # Формируем ответ
        reports = []
        for report in reports_page:
            report_data = {
                'id': report.id,
                'reporter': {
                    'id': report.reporter.id,
                    'username': report.reporter.username,
                    'display_name': report.reporter.display_name
                },
                'content_type': report.content_type,
                'content_id': report.content_id,
                'reason': report.reason,
                'reason_display': dict(Report.REASON_CHOICES).get(report.reason),
                'comment': report.comment,
                'status': report.status,
                'status_display': dict(Report.STATUS_CHOICES).get(report.status),
                'created_at': report.created_at.isoformat(),
                'resolved_by': {
                    'id': report.resolved_by.id,
                    'username': report.resolved_by.username
                } if report.resolved_by else None,
                'resolved_at': report.resolved_at.isoformat() if report.resolved_at else None,
            }
            reports.append(report_data)
        
        return Response({
            'count': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'results': reports,
        })
    except Exception as e:
        logger.error(f"Error in get_reports: {e}", exc_info=True)
        return Response({"error": "Ошибка при загрузке жалоб", "detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def resolve_report(request, report_id):
    """Решить жалобу (только для модераторов/админов)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return Response({"error": "Жалоба не найдена"}, status=404)
    
    status = request.data.get("status")
    if status not in ["resolved", "rejected"]:
        return Response({"error": "Неверный статус"}, status=400)
    
    # Обновляем жалобу
    report.status = status
    report.resolved_by = request.user
    report.resolved_at = timezone.now()
    report.save()
    
    logger.info(f"Report {report_id} resolved by {request.user.username} as {status}")
    
    return Response({
        "success": True,
        "message": "Жалоба рассмотрена",
        "report": {
            "id": report.id,
            "status": report.status,
            "resolved_by": request.user.username,
            "resolved_at": report.resolved_at.isoformat()
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hide_post_from_feed(request, post_id):
    """Скрыть пост из ленты"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Добавляем запись в HiddenPost или используем существующую модель
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission

    # Создаём запись о скрытии
    # Здесь можно использовать любую модель для хранения скрытых постов
    # Пока просто возвращаем успех
    # В будущем можно добавить модель HiddenPost

    return Response({"success": True, "message": "Пост скрыт из ленты"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_post_not_interested(request, post_id):
    """Отметить пост как "Не интересно" (влияет на рекомендации)"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Здесь можно сохранить информацию о том, что пользователю не интересен этот пост
    # Для влияния на алгоритмы рекомендаций
    # В будущем добавить модель UserInterest с полем not_interested

    return Response({"success": True, "message": "Пост отмечен как неинтересный"})


# ==================== POST EDITING ====================


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    """Редактировать пост (полное редактирование как при создании)"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Импорты моделей
    from anime.models import Anime
    from playlists.models import Playlist
    from reactor.models import ReactorPost
    
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Проверяем права
    if post.author != request.user:
        return Response({"error": "Нельзя редактировать чужие посты"}, status=403)

    # Проверяем время на редактирование (5 минут)
    if (timezone.now() - post.created_at).total_seconds() > 300:
        return Response({"error": "Время на редактирование истекло"}, status=400)

    # Нельзя менять тип поста
    new_type = request.data.get("post_type")
    if new_type and new_type != post.post_type:
        return Response({"error": "Нельзя менять тип поста"}, status=400)

    # ===== ОБНОВЛЕНИЕ ОСНОВНЫХ ПОЛЕЙ =====
    if "title" in request.data:
        post.title = request.data["title"][:200] if request.data["title"] else None

    if "text" in request.data:
        text = request.data["text"]
        if text and len(text) > 5000:
            return Response({"error": "Максимум 5000 символов"}, status=400)
        post.text = text

    if "visibility" in request.data:
        if request.data["visibility"] in ["public", "followers", "friends", "private"]:
            post.visibility = request.data["visibility"]

    if "allow_comments" in request.data:
        post.allow_comments = bool(request.data["allow_comments"])

    # ВАЖНО: spoiler_for - это ForeignKey на Anime, а не текст!
    # Используем spoiler_description для текстового описания
    if "is_spoiler" in request.data:
        post.is_spoiler = bool(request.data["is_spoiler"])

    if "spoiler_description" in request.data:
        post.spoiler_description = request.data["spoiler_description"][:255]

    # ===== ОБНОВЛЕНИЕ МЕДИАФАЙЛОВ =====
    # Если переданы новые медиафайлы - удаляем старые и добавляем новые
    has_new_media = any(key.startswith("media_") for key in request.FILES.keys())
    if has_new_media:
        # Удаляем старые медиафайлы
        post.media_files.all().delete()
        
        # Создаём новые медиафайлы
        VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v", ".ogv", ".flv"}
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".tiff", ".avif"}
        
        import os
        import imghdr
        from mimetypes import guess_type
        from io import BytesIO

        try:
            from PIL import Image
        except:
            Image = None

        for key, file in request.FILES.items():
            if not key.startswith("media_"):
                continue

            ext = os.path.splitext(file.name)[1].lower()
            content_type = (file.content_type or "").lower()

            # Определяем тип медиа
            if content_type.startswith("video") or ext in VIDEO_EXTENSIONS:
                media_type = "video"
            elif content_type.startswith("image") or ext in IMAGE_EXTENSIONS:
                media_type = "image"
            else:
                # Пытаемся определить по сигнатуре
                try:
                    head = file.read(4096)
                    file.seek(0)
                    img_type = imghdr.what(None, h=head)
                    if img_type:
                        media_type = "image"
                    elif len(head) >= 12 and b"ftyp" in head[4:12]:
                        media_type = "video"
                    elif head.startswith(b"\x1a\x45\xdf\xa3"):
                        media_type = "video"
                    else:
                        media_type = "image"
                except:
                    try:
                        file.seek(0)
                    except:
                        pass
                    media_type = "image"

            # Размер файла
            file_size = getattr(file, "size", None) or 0
            mime_type = content_type or (guess_type(file.name)[0] or "")

            # Размеры для изображений
            width = height = None
            if media_type == "image" and Image is not None:
                try:
                    data = file.read()
                    file.seek(0)
                    img = Image.open(BytesIO(data))
                    width, height = img.size
                    try:
                        img.close()
                    except:
                        pass
                except:
                    try:
                        file.seek(0)
                    except:
                        pass

            PostMedia.objects.create(
                post=post,
                media_type=media_type,
                file=file,
                file_size=file_size,
                mime_type=mime_type,
                width=width,
                height=height,
            )

    # ===== ОБНОВЛЕНИЕ ПРИВЯЗОК (через PostAttachment) =====
    # Удаляем старые attachments если переданы новые
    has_new_attachments = (
        "anime_ids" in request.data or 
        "anime_ids[]" in request.data or
        "playlist_ids" in request.data or 
        "playlist_ids[]" in request.data or
        "reactor_ids" in request.data or
        "reactor_ids[]" in request.data
    )
    if has_new_attachments:
        post.attachments.all().delete()
    
    # Аниме (множественное) - поддерживаем anime_ids и anime_ids[]
    # Для multipart/form-data используем request.POST.getlist, для JSON - request.data
    if hasattr(request, 'POST') and request.POST:
        anime_raw = request.POST.getlist('anime_ids[]') or request.POST.getlist('anime_ids') or []
    else:
        anime_raw = request.data.get("anime_ids[]") or request.data.get("anime_ids") or []
    
    if isinstance(anime_raw, str):
        anime_ids = [anime_raw]
    elif hasattr(anime_raw, '__iter__') and not isinstance(anime_raw, dict):
        anime_ids = list(anime_raw)
    else:
        anime_ids = []
    
    # Фильтруем пустые значения
    anime_ids = [aid for aid in anime_ids if aid]
    
    # Также поддерживаем множественные рейтинги
    if hasattr(request, 'POST') and request.POST:
        anime_ratings_raw = request.POST.getlist('anime_ratings[]') or request.POST.getlist('anime_ratings') or []
    else:
        anime_ratings_raw = request.data.get("anime_ratings[]") or request.data.get("anime_ratings") or []
    
    if isinstance(anime_ratings_raw, str):
        anime_ratings = [anime_ratings_raw]
    elif hasattr(anime_ratings_raw, '__iter__') and not isinstance(anime_ratings_raw, dict):
        anime_ratings = list(anime_ratings_raw)
    else:
        anime_ratings = []
    
    for idx, anime_id in enumerate(anime_ids):
        try:
            anime = Anime.objects.get(id=anime_id)
            PostAttachment.objects.create(
                post=post,
                content_type="anime",
                object_id=anime.id,
                metadata={"title": anime.title_ru or anime.title_en}
            )
        except Anime.DoesNotExist:
            pass
    
    # Для обратной совместимости устанавливаем первое аниме в старое поле
    post.anime = None
    if anime_ids:
        try:
            post.anime = Anime.objects.filter(id=anime_ids[0]).first()
            # Устанавливаем рейтинг для первого аниме
            if anime_ratings and len(anime_ratings) > 0 and anime_ratings[0]:
                try:
                    post.anime_rating = int(anime_ratings[0])
                except (ValueError, TypeError):
                    post.anime_rating = None
        except:
            pass

    # Плейлисты (множественное) - поддерживаем playlist_ids и playlist_ids[]
    if hasattr(request, 'POST') and request.POST:
        playlist_raw = request.POST.getlist('playlist_ids[]') or request.POST.getlist('playlist_ids') or []
    else:
        playlist_raw = request.data.get("playlist_ids[]") or request.data.get("playlist_ids") or []
    
    if isinstance(playlist_raw, str):
        playlist_ids = [playlist_raw]
    elif hasattr(playlist_raw, '__iter__') and not isinstance(playlist_raw, dict):
        playlist_ids = list(playlist_raw)
    else:
        playlist_ids = []
    
    # Фильтруем пустые значения
    playlist_ids = [pid for pid in playlist_ids if pid]
    
    for playlist_id in playlist_ids:
        try:
            playlist = Playlist.objects.get(id=playlist_id)
            if playlist.user != request.user and playlist.visibility != "public":
                return Response({"error": "Нет доступа к плейлисту"}, status=403)
            PostAttachment.objects.create(
                post=post,
                content_type="playlist",
                object_id=playlist.id,
                metadata={"title": playlist.title}
            )
        except Playlist.DoesNotExist:
            pass
    
    # Для обратной совместимости
    post.playlist = None
    if playlist_ids:
        try:
            post.playlist = Playlist.objects.filter(id=playlist_ids[0]).first()
        except:
            pass

    # Shorts/Reactor (множественное) - поддерживаем reactor_ids и reactor_ids[]
    if hasattr(request, 'POST') and request.POST:
        reactor_raw = request.POST.getlist('reactor_ids[]') or request.POST.getlist('reactor_ids') or []
    else:
        reactor_raw = request.data.get("reactor_ids[]") or request.data.get("reactor_ids") or []
    
    if isinstance(reactor_raw, str):
        reactor_ids = [reactor_raw]
    elif hasattr(reactor_raw, '__iter__') and not isinstance(reactor_raw, dict):
        reactor_ids = list(reactor_raw)
    else:
        reactor_ids = []
    
    # Фильтруем пустые значения
    reactor_ids = [rid for rid in reactor_ids if rid]
    
    for reactor_id in reactor_ids:
        try:
            reactor = ReactorPost.objects.get(id=reactor_id)
            PostAttachment.objects.create(
                post=post,
                content_type="shorts",
                object_id=reactor.id,
                metadata={"title": reactor.title}
            )
        except ReactorPost.DoesNotExist:
            pass

    # Для обратной совместимости
    post.reactor_post = None
    if reactor_ids:
        try:
            post.reactor_post = ReactorPost.objects.filter(id=reactor_ids[0]).first()
        except:
            pass

    # Рейтинг аниме (старый формат, для обратной совместимости)
    if "anime_rating" in request.data and not anime_ratings:
        rating = request.data.get("anime_rating")
        if rating is None or rating == "":
            post.anime_rating = None
        else:
            try:
                rating_val = int(rating)
                if 1 <= rating_val <= 10:
                    post.anime_rating = rating_val
                else:
                    return Response({"error": "Рейтинг должен быть от 1 до 10"}, status=400)
            except (ValueError, TypeError):
                return Response({"error": "Неверный формат рейтинга"}, status=400)

    # Обновляем тип поста на основе медиа и привязок
    media_qs = post.media_files.all()
    if post.playlist:
        post.post_type = "playlist"
    elif post.anime:
        post.post_type = "anime"
    elif post.reactor_post:
        post.post_type = "repost"
    elif media_qs.exists():
        if media_qs.filter(media_type="video").exists():
            post.post_type = "video"
        else:
            post.post_type = "image"
        
        # Синхронизируем legacy поля
        first = media_qs.order_by("order").first()
        if first:
            if first.media_type == "video":
                post.video_file = first.file
                post.video_url = first.url or ""
                post.image_file = None
                post.image_url = ""
            else:
                post.image_file = first.file
                post.image_url = first.url or ""
                post.video_file = None
                post.video_url = ""

    post.edited_at = timezone.now()
    post.save()

    try:
        from .serializers import PostSerializer
        serializer_data = PostSerializer(post, context={"request": request}).data
        return Response({
            "success": True,
            "message": "Пост обновлён",
            "post": serializer_data,
        })
    except Exception as e:
        logger.error(f"Error serializing post {post.id} after edit: {e}")
        return Response({
            "success": True,
            "message": "Пост обновлён",
            "post": {
                "id": post.id,
                "title": post.title,
                "text": post.text,
                "edited_at": post.edited_at.isoformat() if post.edited_at else None,
            },
        })


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    """Редактировать комментарий"""
    try:
        comment = PostComment.objects.select_related('parent').get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    # Проверяем права
    if comment.author != request.user:
        return Response({"error": "Нельзя редактировать чужие комментарии"}, status=403)

    # Проверяем время на редактирование (10 минут)
    if (timezone.now() - comment.created_at).total_seconds() > 600:
        return Response({"error": "Время на редактирование истекло"}, status=400)

    # Обновляем контент
    content = request.data.get("content")
    if not content:
        return Response({"error": "Комментарий не может быть пустым"}, status=400)

    if len(content) > 2000:
        return Response({"error": "Максимум 2000 символов"}, status=400)

    comment.content = content
    comment.is_edited = True
    comment.save()

    # Обновляем replies_count родителя если это ответ
    if comment.parent:
        comment.parent.replies_count = comment.parent.replies.filter(is_deleted=False).count()
        comment.parent.save(update_fields=["replies_count"])

    return Response(
        {
            "success": True,
            "message": "Комментарий обновлён",
            "comment": PostCommentSerializer(
                comment, context={"request": request}
            ).data,
        }
    )


# ==================== HASHTAGS ====================


@api_view(["GET"])
@permission_classes([AllowAny])
def get_hashtag_posts(request, tag_name):
    """Получить посты по хэштегу"""
    # Убираем # из начала если есть
    tag = tag_name.lstrip("#")

    # Сначала пробуем получить из кэша
    try:
        from .feed_cache import feed_cache

        post_ids = feed_cache.get_hashtag_posts(tag, limit=50)

        if post_ids:
            posts = Post.objects.filter(
                id__in=post_ids, status="published"
            ).select_related("author__profile", "anime")

            serializer = PostSerializer(posts, many=True, context={"request": request})
            return Response(serializer.data)
    except Exception:
        pass

    # Если нет в кэше, получаем из БД
    hashtag = Hashtag.objects.filter(name__iexact=tag).first()
    if not hashtag:
        return Response({"results": [], "count": 0})

    post_ids = (
        PostHashtag.objects.filter(hashtag=hashtag)
        .values_list("post_id", flat=True)
        .order_by("-post__created_at")
    )

    posts = Post.objects.filter(id__in=post_ids, status="published").select_related(
        "author__profile", "anime"
    )

    serializer = PostSerializer(posts, many=True, context={"request": request})
    return Response(
        {"results": serializer.data, "count": len(serializer.data), "hashtag": tag}
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def search_hashtags(request):
    """Поиск хэштегов"""
    query = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit", 10))

    if len(query) < 2:
        return Response({"results": []})

    hashtags = Hashtag.objects.filter(name__icontains=query).order_by("-posts_count")[
        :limit
    ]

    results = []
    for tag in hashtags:
        results.append({"id": tag.id, "name": tag.name, "posts_count": tag.posts_count})

    return Response({"results": results})


# ==================== POST VIEWS ====================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_post_view(request, post_id):
    """Отследить просмотр поста"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    # Проверяем, не是自己的 пост
    if post.author == request.user:
        return Response({"success": True, "message": "Просмотр засчитан (автор)"})

    # Проверяем, не просматривал ли уже
    existing_view = FeedView.objects.filter(user=request.user, post=post).first()

    if existing_view:
        return Response({"success": True, "message": "Уже просмотрено"})

    # Создаём запись о просмотре
    FeedView.objects.create(user=request.user, post=post)

    # Увеличиваем счётчик просмотров
    post.views_count += 1
    post.save(update_fields=["views_count"])

    return Response(
        {
            "success": True,
            "message": "Просмотр засчитан",
            "views_count": post.views_count,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_viewers(request, post_id):
    """Получить список пользователей, просмотревших пост"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    views = FeedView.objects.filter(post=post).select_related("user__profile")[:100]

    users = []
    for view in views:
        users.append(
            {
                "id": view.user.id,
                "username": view.user.username,
                "avatar": view.user.profile.avatar.url
                if hasattr(view.user, "profile") and view.user.profile.avatar
                else None,
                "viewed_at": view.viewed_at.isoformat(),
            }
        )

    return Response({"count": post.views_count, "users": users})


# ==================== NOTIFICATIONS ====================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_notification_settings(request):
    """Получить настройки уведомлений для ленты"""
    profile = request.user.profile if hasattr(request.user, "profile") else None

    settings = {
        "notify_likes": getattr(profile, "notify_likes", True) if profile else True,
        "notify_comments": getattr(profile, "notify_comments", True)
        if profile
        else True,
        "notify_mentions": True,  # Всегда включены
        "email_digest": getattr(profile, "email_digest", "never")
        if profile
        else "never",
    }

    return Response(settings)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_notification_settings(request):
    """Обновить настройки уведомлений для ленты"""
    profile = request.user.profile if hasattr(request.user, "profile") else None

    if not profile:
        return Response({"error": "Профиль не найден"}, status=404)

    if "notify_likes" in request.data:
        profile.notify_likes = bool(request.data["notify_likes"])

    if "notify_comments" in request.data:
        profile.notify_comments = bool(request.data["notify_comments"])

    if "email_digest" in request.data:
        if request.data["email_digest"] in ["never", "daily", "weekly"]:
            profile.email_digest = request.data["email_digest"]

    profile.save()

    return Response({"success": True, "message": "Настройки обновлены"})

    def perform_destroy(self, instance):
        # Только автор или модератор может удалить
        if instance.author != self.request.user:
            # Проверяем модерацию - для простоты, пока только автор
            self.permission_denied(
                self.request, message="Cannot delete others' comments"
            )
        instance.is_deleted = True
        instance.save()


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GroupCreateSerializer
        return GroupSerializer

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        
        # Добавляем создателя как администратора
        GroupMembership.objects.create(user=self.request.user, group=group, role='admin')
        
        # Обновляем счётчик участников
        group.update_members_count()
        
        return group

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        group = self.get_object()
        if group.memberships.filter(user=request.user).exists():
            return Response(
                {"detail": "Already a member"}, status=status.HTTP_400_BAD_REQUEST
            )

        membership = GroupMembership.objects.create(user=request.user, group=group)
        group.update_members_count()
        return Response(GroupMembershipSerializer(membership).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        membership = group.memberships.filter(user=request.user).first()
        if not membership:
            return Response(
                {"detail": "Not a member"}, status=status.HTTP_400_BAD_REQUEST
            )

        membership.delete()
        group.update_members_count()
        return Response({"detail": "Left group"})

    @action(detail=True, methods=["get"])
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
        search = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))

        if not search:
            return Response({"results": []})

        # Фильтруем группы
        queryset = Group.objects.filter(
            Q(name__icontains=search) | Q(description__icontains=search),
            is_private=False,
        ).select_related("creator")

        # Ограничиваем результат
        queryset = queryset[:limit]

        # Сериализуем
        serializer = GroupSerializer(queryset, many=True)

        return Response({"results": serializer.data, "count": len(serializer.data)})


class PostViewSet(ModelViewSet):
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    lookup_value_regex = r'\d+'  # Только целые числа для pk

    def retrieve(self, request, *args, **kwargs):
        """Получение одного поста с подробным логом ошибок"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            instance = self.get_object()
            logger.info(f"Retrieving post {instance.id} for user {request.user.id}")
            
            serializer = self.get_serializer(instance, context={"request": request})
            return Response(serializer.data)
        except Post.DoesNotExist:
            logger.warning(f"Post {kwargs.get('pk')} not found")
            return Response({"error": "Пост не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error retrieving post {kwargs.get('pk')}: {e}\n{error_traceback}")
            return Response(
                {"error": f"Ошибка получения поста: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление поста (is_deleted=True)"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            instance = self.get_object()
            logger.info(f"Deleting post {instance.id} by user {request.user.id}")
            
            if instance.author != request.user:
                from rest_framework.exceptions import PermissionDenied
                logger.warning(f"User {request.user.id} tried to delete post {instance.id} owned by {instance.author.id}")
                raise PermissionDenied("Вы можете удалять только свои посты")
            
            # Мягкое удаление: меняем статус и отметку времени
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.save(update_fields=["is_deleted", "deleted_at"])
            logger.info(f"Post {instance.id} marked as deleted")
            
            # Обновляем счётчик комментариев у автора, если есть
            try:
                if hasattr(instance, 'author') and instance.author:
                    from users.models import User
                    User.objects.filter(id=instance.author_id).update(
                        posts_count=models.F('posts_count') - 1
                    )
            except Exception as counter_err:
                logger.warning(f"Failed to update posts_count: {counter_err}")
            
            # Публикуем событие удаления
            try:
                from core.redis_events import publish_post_deleted
                publish_post_deleted(instance.id)
                logger.info(f"Post deleted event published for post {instance.id}")
            except Exception as e:
                logger.warning(f"Failed to publish post_deleted event: {e}")
            
            return Response({"success": True, "message": "Пост удалён", "post_id": instance.id}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error deleting post {kwargs.get('pk', 'unknown')} by user {request.user.id}: {e}\n{error_traceback}")
            return Response({"error": str(e), "detail": "Ошибка при удалении поста"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_serializer_class(self):
        # use lightweight serializer for incoming data but return full representation when listing/retrieving
        if self.action == "create":
            return PostCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PostUpdateSerializer
        return PostSerializer

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def public_retrieve(self, request, pk=None):
        """Публичный просмотр поста (без аутентификации)"""
        try:
            post = self.get_queryset().get(id=pk)

            # Проверяем права доступа
            if post.visibility == "private":
                return Response(
                    {"error": "Пост недоступен"}, status=status.HTTP_403_FORBIDDEN
                )

            if post.group and not post.group.is_public:
                return Response(
                    {"error": "Группа недоступна"}, status=status.HTTP_403_FORBIDDEN
                )

            # Получаем полные данные с отношениями
            from .serializers import PostSerializer

            serializer = PostSerializer(post, context={"request": request})
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response(
                {"error": "Пост не найден"}, status=status.HTTP_404_NOT_FOUND
            )

    def get_queryset(self):
        queryset = (
            Post.objects.filter(is_deleted=False, status="published")
            .select_related("author", "anime", "group", "playlist", "reactor_post", "original_post")
            .prefetch_related(
                "media_files", 
                "attachments", 
                "hashtag_links__hashtag",
                "likes",
                "dislikes",
            )
            .order_by("-created_at")
        )

        # Фильтр по группе (преобразуем 'true' string в None или целое число)
        group_filter = self.request.query_params.get("group")
        if group_filter and group_filter != "true":
            try:
                group_id = int(group_filter)
                queryset = queryset.filter(group_id=group_id)
            except (ValueError, TypeError):
                pass
        elif group_filter == "true":
            # Если group=true, показываем только посты в группах
            queryset = queryset.exclude(group__isnull=True)

        # Фильтр по аниме
        anime_id = self.request.query_params.get("anime")
        if anime_id:
            try:
                queryset = queryset.filter(anime_id=int(anime_id))
            except (ValueError, TypeError):
                pass

        # Лента пользователя (посты от подписок)
        if self.request.query_params.get("feed") == "true":
            queryset = queryset.exclude(group__isnull=False)

        return queryset

    def update(self, request, *args, **kwargs):
        # similar override for updates
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        post = serializer.instance
        output = PostSerializer(post, context={"request": request})
        return Response(output.data)

    def _handle_media_uploads(self, request, post, replace=False):
        """Create PostMedia records for any files named media_*. If replace=True, clear existing media first."""
        if replace:
            post.media_files.all().delete()

        # known video and image extensions for fallback when browser sends octet-stream
        VIDEO_EXTENSIONS = {
            ".mp4",
            ".webm",
            ".mov",
            ".avi",
            ".mkv",
            ".m4v",
            ".ogv",
            ".flv",
        }
        IMAGE_EXTENSIONS = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
            ".svg",
            ".tiff",
            ".avif",
        }

        import os
        import imghdr
        from mimetypes import guess_type
        from io import BytesIO

        try:
            from PIL import Image
        except Exception:
            Image = None

        for key, file in request.FILES.items():
            if not key.startswith("media_"):
                continue

            ext = os.path.splitext(file.name)[1].lower()
            content_type = (file.content_type or "").lower()

            # initial guess: MIME first, then extension
            if content_type.startswith("video") or ext in VIDEO_EXTENSIONS:
                media_type = "video"
            elif content_type.startswith("image") or ext in IMAGE_EXTENSIONS:
                media_type = "image"
            else:
                media_type = None

            # If still unknown, try to sniff file signature
            try:
                # read small chunk for sniffing, then rewind
                head = file.read(4096)
                file.seek(0)

                # image signatures
                img_type = imghdr.what(None, h=head)
                if img_type:
                    media_type = "image"

                # mp4/f4v/3gp: 'ftyp' usually at offset 4
                if media_type is None:
                    if len(head) >= 12 and b"ftyp" in head[4:12]:
                        media_type = "video"
                    # webm/ebml signature
                    elif head.startswith(b"\x1a\x45\xdf\xa3"):
                        media_type = "video"
                    # mkv/ogg/avi heuristics
                    elif head.startswith(b"RIFF") and b"AVI " in head[8:16]:
                        media_type = "video"

            except Exception:
                try:
                    file.seek(0)
                except Exception:
                    pass

            # fallback to image if still unknown
            if not media_type:
                media_type = "image"

            # Calculate file size in bytes
            file_size = getattr(file, "size", None) or 0

            # determine mime_type: prefer provided, else guess from name
            mime_type = content_type or (guess_type(file.name)[0] or "")

            # try to populate image dimensions if possible
            width = height = duration = None
            if media_type == "image" and Image is not None:
                try:
                    # PIL may close the file object when the image is closed, which
                    # would delete a TemporaryUploadedFile and later cause errors
                    # such as "I/O operation on closed file" or missing temp file.
                    # To avoid that we work on a copy of the data stored in memory
                    # rather than passing the original file directly.
                    data = file.read()
                    file.seek(0)
                    img = Image.open(BytesIO(data))
                    width, height = img.size
                    # closing the image is safe now since it wraps a BytesIO
                    try:
                        img.close()
                    except Exception:
                        pass
                except Exception:
                    # if anything goes wrong we still want to rewind the original
                    try:
                        file.seek(0)
                    except Exception:
                        pass

            PostMedia.objects.create(
                post=post,
                media_type=media_type,
                file=file,
                file_size=file_size,
                mime_type=mime_type,
                width=width,
                height=height,
                duration=duration,
            )

    def _update_post_type(self, post):
        """Определяет post_type на основе прикреплённого контента НЕ трогая медиа"""
        new_type = post.post_type
        media_qs = post.media_files.all()

        # Приоритет: playlist > anime > reactor_post > media
        if post.playlist_id:
            new_type = "playlist"
        elif post.anime_id:
            new_type = "anime"
        elif post.reactor_post_id:
            new_type = "repost"
        elif media_qs.exists():
            # Если есть видео - video, иначе image
            if media_qs.filter(media_type="video").exists():
                new_type = "video"
            else:
                new_type = "image"

        # !!! УБРАЛИ синхронизацию legacy полей - это вызывает конфликт
        # Оставить только обновление post_type
        if new_type != post.post_type:
            post.post_type = new_type
            post.save(update_fields=["post_type"])

    def create(self, request, *args, **kwargs):
        try:
            # strip media_x fields before validation; they are handled separately
            data = {k: v for k, v in request.data.items() if not k.startswith("media_")}

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            post = serializer.instance
            
            self._handle_media_uploads(request, post)
            self._update_post_type(post)

            headers = self.get_success_headers(serializer.data)
            out_serializer = PostSerializer(post, context={"request": request})
            
            return Response(
                out_serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except Exception as exc:
            import traceback

            traceback.print_exc()
            return Response({"error": str(exc)}, status=500)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user, status="published")

        # Публикуем событие создания поста
        try:
            publish_post_created(
                {
                    "post_id": post.id,
                    "author_id": post.author.id,
                    "author_username": post.author.username,
                    "text": post.text[:200] if post.text else "",
                    "created_at": post.created_at.isoformat(),
                }
            )
        except Exception as e:
            # Redis недоступен, просто логируем
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to publish post created event: {e}")
        return post

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            
            # 1. Сначала проверяем, хочет ли пользователь удалить медиа
            # Если переданы новые файлы - заменяем старые
            has_new_media = any(k.startswith('media_') for k in request.FILES.keys())
            
            if has_new_media:
                # Пользователь добавил новые файлы - удаляем старые и добавляем новые
                instance.media_files.all().delete()
                self._handle_media_uploads(request, instance, replace=False)
            # else: ничего не делаем - медиа остаются как были
            
            # 2. Обработка остальных полей и attachments (через сериализатор)
            # Берём данные БЕЗ media_ полей
            data = {k: v for k, v in request.data.items() if not k.startswith('media_')}
            
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # 3. Перезагрузка поста с полным prefetch
            post = Post.objects.select_related(
                "author", "anime", "group", "playlist", "reactor_post", "original_post"
            ).prefetch_related(
                "media_files", 
                "attachments",  # ВАЖНО: attachments должны быть загружены!
                "hashtag_links__hashtag",
            ).get(id=instance.id)
            
            # 4. Обновление типа поста
            self._update_post_type(post)
            
            # 5. Возврат с полным сериализатором
            out_serializer = PostSerializer(post, context={"request": request})
            return Response(out_serializer.data)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            return Response({"error": str(exc)}, status=500)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        topic_id = self.request.query_params.get("topic_id")
        print(
            f"DEBUG: Получаем сообщения для чата {chat_id}, топик '{topic_id}', пользователь {self.request.user}"
        )

        try:
            chat = GroupChat.objects.get(id=chat_id)
            if not ChatMember.objects.filter(
                chat=chat, user=self.request.user
            ).exists():
                return Message.objects.none()

            qs = Message.objects.filter(chat=chat, is_deleted=False).select_related(
                "sender", "reply_to__sender"
            )

            # Фильтрация по topic_id для franchise discussion:
            # - topic_id = 'main' - показываем ВСЕ сообщения (главный топик = вся лента)
            # - topic_id = число - показываем ТОЛЬКО сообщения этого топика
            # - topic_id не передан - показываем все сообщения (для обратной совместимости)
            if topic_id is not None and topic_id != "":
                if topic_id == "main" or topic_id == "0":
                    # Главный топик - показываем ВСЕ сообщения (без фильтрации по topic_id)
                    pass
                else:
                    try:
                        tid = int(topic_id)
                        qs = qs.filter(topic_id=tid)
                    except ValueError:
                        pass

            print(f"DEBUG: Найдено сообщений: {qs.count()}")
            return qs
        except GroupChat.DoesNotExist:
            try:
                private_chat = PrivateChat.objects.get(id=chat_id)
                if self.request.user not in [private_chat.user1, private_chat.user2]:
                    return Message.objects.none()
                return Message.objects.filter(
                    private_chat=private_chat, is_deleted=False
                ).select_related("sender", "reply_to__sender")
            except PrivateChat.DoesNotExist:
                return Message.objects.none()

    def perform_create(self, serializer):
        from .chat_cache import ChatCacheService

        chat_id = (
            self.request.data.get("chat_id")
            or self.request.data.get("private_chat")
            or self.request.data.get("chat")
        )
        topic_id = self.request.data.get("topic_id")
        print(
            f"DEBUG: Создаем сообщение для чата {chat_id}, топик {topic_id}, пользователь {self.request.user}"
        )
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
                member = ChatMember.objects.filter(
                    chat=chat, user=self.request.user
                ).first()
                if not member:
                    raise PermissionError("Пользователь не является участником чата")
                if member.is_banned:
                    raise PermissionError("Пользователь забанен в чате")
                if member.is_muted and (
                    member.muted_until is None or member.muted_until > timezone.now()
                ):
                    raise PermissionError("Пользователь заглушен в чате")
                if not member.can_send_messages:
                    raise PermissionError("Пользователь не может отправлять сообщения")

                message = serializer.save(
                    chat=chat, sender=self.request.user, topic_id=topic_id
                )

            except GroupChat.DoesNotExist:
                try:
                    private_chat = PrivateChat.objects.get(id=chat_id)
                    # Проверяем доступ к личному чату
                    if self.request.user not in [
                        private_chat.user1,
                        private_chat.user2,
                    ]:
                        raise PermissionError("Нет доступа к чату")

                    # Проверяем, не заблокирован ли чат
                    other_user = (
                        private_chat.user1
                        if private_chat.user2 == self.request.user
                        else private_chat.user2
                    )
                    settings = private_chat.get_user_settings(self.request.user)
                    if settings.get("blocked", False):
                        raise PermissionError("Чат заблокирован")

                    message = serializer.save(
                        private_chat=private_chat,
                        sender=self.request.user,
                        topic_id=topic_id,
                    )

                except PrivateChat.DoesNotExist:
                    raise PermissionError("Чат не найден")

            # Обновляем время последнего сообщения
            if chat:
                chat.save(update_fields=["last_message_at"])
            elif private_chat:
                private_chat.last_message_at = timezone.now()
                private_chat.save(update_fields=["last_message_at"])

            print("DEBUG: Сообщение успешно сохранено")

            # Обработка множественных вложений (anime_ids[], playlist_ids[], shorts_ids[], post_ids[])
            from .models import MessageAttachment, Attachment
            import os
            from mimetypes import guess_type
            
            # Прикреплённые файлы (attachment_ids[])
            attachment_ids = self.request.data.getlist('attachment_ids[]') or self.request.data.get('attachment_ids', [])
            if isinstance(attachment_ids, str):
                attachment_ids = [attachment_ids]
            
            # Медиафайлы из FormData (media_0, media_1, etc)
            media_files_uploaded = []
            for key in self.request.FILES.keys():
                if key.startswith('media_'):
                    media_files_uploaded.append(self.request.FILES[key])
            
            # Обрабатываем загруженные медиафайлы
            for media_file in media_files_uploaded:
                # Определяем тип файла
                content_type = media_file.content_type or ''
                ext = os.path.splitext(media_file.name)[1].lower()
                
                if content_type.startswith('image/') or ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    att_type = 'image'
                elif content_type.startswith('video/') or ext in ['.mp4', '.webm', '.mov', '.avi']:
                    att_type = 'video'
                else:
                    att_type = 'file'
                
                # Создаём вложение
                attachment = Attachment.objects.create(
                    message=message,
                    type=att_type,
                    file=media_file,
                    file_name=media_file.name,
                    file_size=media_file.size,
                    mime_type=content_type or guess_type(media_file.name)[0] or ''
                )
            
            # Аниме
            anime_ids = self.request.data.getlist('anime_ids[]') or self.request.data.get('anime_ids', [])
            if isinstance(anime_ids, str):
                anime_ids = [anime_ids]
            for anime_id in anime_ids:
                if anime_id:
                    try:
                        from anime.models import Anime
                        anime = Anime.objects.get(id=anime_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='anime',
                            object_id=int(anime_id),
                            metadata={'title': anime.title_ru or anime.title_en}
                        )
                    except Anime.DoesNotExist:
                        pass
            
            # Плейлисты
            playlist_ids = self.request.data.getlist('playlist_ids[]') or self.request.data.get('playlist_ids', [])
            if isinstance(playlist_ids, str):
                playlist_ids = [playlist_ids]
            for playlist_id in playlist_ids:
                if playlist_id:
                    try:
                        from playlists.models import Playlist
                        playlist = Playlist.objects.get(id=playlist_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='playlist',
                            object_id=int(playlist_id),
                            metadata={'title': playlist.title}
                        )
                    except Playlist.DoesNotExist:
                        pass

            # Shorts
            shorts_ids = self.request.data.getlist('shorts_ids[]') or self.request.data.get('shorts_ids', [])
            if isinstance(shorts_ids, str):
                shorts_ids = [shorts_ids]
            for shorts_id in shorts_ids:
                if shorts_id:
                    try:
                        from reactor.models import ReactorPost
                        shorts = ReactorPost.objects.get(id=shorts_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='shorts',
                            object_id=int(shorts_id),
                            metadata={'title': shorts.title}
                        )
                    except ReactorPost.DoesNotExist:
                        pass

            # Посты
            post_ids = self.request.data.getlist('post_ids[]') or self.request.data.get('post_ids', [])
            if isinstance(post_ids, str):
                post_ids = [post_ids]
            for post_id in post_ids:
                if post_id:
                    try:
                        post = Post.objects.get(id=post_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='post',
                            object_id=int(post_id),
                            metadata={'text': post.text[:100] if post.text else ''}
                        )
                    except Post.DoesNotExist:
                        pass

            # Добавляем сообщение в кэш
            ChatCacheService.add_message_to_cache(chat_id, message)

            # Увеличиваем счётчики непрочитанных для участников
            if chat:
                for member in chat.members.exclude(user=self.request.user):
                    ChatCacheService.increment_unread(member.user_id, chat_id)
            elif private_chat:
                receiver = (
                    private_chat.user1
                    if private_chat.user2 == self.request.user
                    else private_chat.user2
                )
                ChatCacheService.increment_unread(receiver.id, chat_id)
            
            # Публикуем событие отправки сообщения
            publish_message_sent(
                {
                    "message_id": message.id,
                    "chat_id": chat_id,
                    "sender_id": message.sender.id,
                    "sender_username": message.sender.username,
                    "text": message.text[:200] if message.text else "",
                    "created_at": message.created_at.isoformat(),
                }
            )

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
        from notifications.services import NotificationService

        if private_chat:
            # Личный чат - отправляем уведомление получателю
            receiver = (
                private_chat.user1
                if private_chat.user2 == message.sender
                else private_chat.user2
            )
            settings = private_chat.get_user_settings(receiver)

            if settings.get("notifications", True) and not settings.get(
                "blocked", False
            ):
                NotificationService.create_notification(
                    user=receiver,
                    notification_type="message",
                    title=f"Новое сообщение от {message.sender.username}",
                    content=message.text[:100] if message.text else "Новое сообщение",
                    link=f"/chats/{private_chat.id}",
                    icon="✉️",
                    content_object=message,
                )
            
        elif group_chat:
            # Групповой чат - отправляем уведомления участникам
            for member in group_chat.members.exclude(user=message.sender):
                # Проверяем настройки уведомлений участника
                if member.can_send_messages and not member.is_muted:
                    # Проверяем настройки уведомлений пользователя
                    user_settings = (
                        member.user.notif_settings
                        if hasattr(member.user, "notif_settings")
                        else None
                    )
                    if user_settings and not user_settings.push_enabled:
                        continue

                    NotificationService.create_notification(
                        user=member.user,
                        notification_type="group_message",
                        title=f"Новое сообщение в {group_chat.name}",
                        content=f"{message.sender.username}: {message.text[:80]}"
                        if message.text
                        else "Новое сообщение",
                        link=f"/chats/{group_chat.id}",
                        icon="👥",
                        content_object=message,
                    )


class MessageDetailView(generics.DestroyAPIView):
    """View для удаления сообщений"""

    permission_classes = [IsAuthenticated]
    queryset = Message.objects.filter(is_deleted=False)

    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление сообщения"""
        message = self.get_object()

        # Проверяем права: только отправитель может удалить
        if message.sender != request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Вы можете удалять только свои сообщения")

        # Мягкое удаление
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.deleted_by = request.user
        message.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

        # Отправляем WebSocket событие
        try:
            chat_id = message.chat_id or message.private_chat_id
            if chat_id:
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat_id}",
                    {
                        "type": "message_deleted",
                        "message_id": message.id,
                    },
                )
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")

        return Response({"message": "Сообщение удалено"}, status=204)


class ChatRoleViewSet(ModelViewSet):
    serializer_class = ChatRoleSerializer
    permission_classes = [IsChatOwner]

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_pk")
        return ChatRole.objects.filter(chat_id=chat_id)

    def perform_create(self, serializer):
        chat_id = self.kwargs.get("chat_pk")
        chat = GroupChat.objects.get(id=chat_id)
        serializer.save(chat=chat, created_by=self.request.user)


class GroupChatViewSet(ModelViewSet):
    queryset = GroupChat.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GroupChatCreateSerializer
        return GroupChatSerializer

    def get_queryset(self):
        try:
            return (
                GroupChat.objects.filter(members__user=self.request.user)
                .select_related("created_by")
                .prefetch_related("members", "members__user")
                .order_by("-last_message_at", "-created_at")
            )
        except Exception as e:
            print(f"DEBUG GroupChatViewSet get_queryset error: {e}")
            import traceback

            traceback.print_exc()
            return GroupChat.objects.none()

    def perform_create(self, serializer):
        """Создание группового чата"""
        try:
            chat = serializer.save(created_by=self.request.user)

            # Создаём запись о создателе как админе
            ChatMember.objects.create(
                user=self.request.user, chat=chat, is_admin=True, is_owner=True
            )

            # Логируем создание
            ChatAdminLog.objects.create(
                chat=chat,
                user=self.request.user,
                action="chat_created",
                details={"chat_name": chat.name},
            )
        except Exception as e:
            print(f"DEBUG GroupChatViewSet perform_create error: {e}")
            import traceback

            traceback.print_exc()
            raise

    @action(detail=True, methods=["post"])
    def leave_group_chat(self, request, pk=None):
        """Выход пользователя из группового чата
        
        Логика:
        - Для обсуждений аниме: просто удаляем участника, чат остаётся
        - Для обычных групп: просто удаляем участника, чат остаётся
        - Создатель не может покинуть чат (должен передать права или удалить)
        """
        try:
            chat = GroupChat.objects.get(pk=pk)
            
            # Проверяем, что пользователь является участником
            member = ChatMember.objects.filter(chat=chat, user=request.user).first()
            if not member:
                return Response(
                    {"error": "Вы не являетесь участником этого чата"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Создатель не может покинуть чат (должен передать права или удалить)
            if member.is_owner:
                return Response(
                    {"error": "Создатель чата не может его покинуть. Сначала передайте права или удалите чат."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Для обсуждений аниме - просто удаляем участника, чат остаётся
            # Для обычных групп - также просто удаляем участника, чат остаётся
            
            # Удаляем участника из чата
            member.delete()
            
            # Если это обсуждение аниме, не удаляем чат полностью
            if chat.discussion_type == 'anime':
                # Чат остаётся в системе, просто без этого участника
                pass
            
            # Обновляем last_message_at чата
            chat.save(update_fields=["last_message_at"])
            
            # Отправляем WebSocket событие
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat.id}",
                    {
                        "type": "member_left",
                        "user_id": request.user.id,
                        "username": request.user.username,
                        "chat_id": chat.id,
                    },
                )
            except Exception as ws_err:
                print(f"WS error: {ws_err}")
            
            return Response({
                "message": "Вы успешно покинули чат",
                "chat_id": chat.id,
                "action": "left"
            })
        except GroupChat.DoesNotExist:
            return Response(
                {"error": "Чат не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"DEBUG leave_group_chat error: {e}")
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def delete_group_chat(self, request, pk=None):
        """Удаление группового чата создателем
        
        Логика:
        - Обычные группы: удаляем полностью (даже если остался 1 участник)
        - Группы обсуждений аниме (discussion_type='anime'): не удаляем, просто убираем всех участников
        """
        try:
            chat = GroupChat.objects.get(pk=pk)
            
            # Проверяем, что пользователь является создателем
            member = ChatMember.objects.filter(chat=chat, user=request.user).first()
            if not member or not member.is_owner:
                return Response(
                    {"error": "Только создатель чата может его удалить"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Получаем chat_id для WebSocket события
            chat_id = chat.id
            
            # Проверяем, является ли чат обсуждением аниме
            is_anime_discussion = chat.discussion_type == 'anime'
            
            if is_anime_discussion:
                # Для обсуждений аниме: не удаляем чат, просто удаляем всех участников
                # 1. Удаляем все сообщения
                Message.objects.filter(chat=chat).delete()
                
                # 2. Удаляем всех участников
                ChatMember.objects.filter(chat=chat).delete()
                
                # 3. Обновляем last_message_at
                chat.last_message_at = None
                chat.save(update_fields=['last_message_at'])
                
                # Отправляем WebSocket событие об удалении участников
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"chat_{chat_id}",
                        {
                            "type": "chat_cleared",
                            "chat_id": chat_id,
                            "message": "Все участники покинули чат обсуждения",
                        },
                    )
                except Exception as ws_err:
                    print(f"WS error: {ws_err}")
                
                return Response({
                    "message": "Чат обсуждения очищен от участников",
                    "chat_id": chat_id,
                    "action": "cleared"  # indicating chat was cleared, not deleted
                })
            else:
                # Для обычных групп: удаляем полностью
                # 1. Удаляем все сообщения
                Message.objects.filter(chat=chat).delete()
                
                # 2. Удаляем всех участников
                ChatMember.objects.filter(chat=chat).delete()
                
                # 3. Удаляем чат
                chat.delete()
                
                # Отправляем WebSocket событие об удалении чата
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"chat_{chat_id}",
                        {
                            "type": "chat_deleted",
                            "chat_id": chat_id,
                        },
                    )
                except Exception as ws_err:
                    print(f"WS error: {ws_err}")
                
                return Response({
                    "message": "Чат успешно удалён",
                    "chat_id": chat_id,
                    "action": "deleted"
                })
        except GroupChat.DoesNotExist:
            return Response(
                {"error": "Чат не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"DEBUG delete_group_chat error: {e}")
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrivateChatViewSet(ModelViewSet):
    """ViewSet для личных чатов"""

    queryset = PrivateChat.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PrivateChatSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return PrivateChatCreateSerializer
        return PrivateChatSerializer

    def get_queryset(self):
        """Возвращает только личные чаты текущего пользователя"""
        try:
            return (
                PrivateChat.objects.filter(
                    Q(user1=self.request.user) | Q(user2=self.request.user)
                )
                .select_related("user1", "user2")
                .order_by("-last_message_at", "-created_at")
            )
        except Exception as e:
            print(f"DEBUG PrivateChatViewSet get_queryset error: {e}")
            import traceback

            traceback.print_exc()
            return PrivateChat.objects.none()

    def create(self, request, *args, **kwargs):
        """Создаёт новый личный чат или возвращает существующий"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()

        # Проверяем не существует ли уже чат (двойная проверка)
        existing_chat = (
            PrivateChat.objects.filter(
                Q(user1=request.user, user2_id=serializer.validated_data["user2"].id)
                | Q(user1_id=serializer.validated_data["user2"].id, user2=request.user)
            )
            .order_by("-created_at")
            .first()
        )

        if existing_chat and existing_chat.id != chat.id:
            chat = existing_chat

        # Возвращаем данные через PrivateChatSerializer
        return Response(
            PrivateChatSerializer(chat, context={"request": request}).data, status=201
        )
