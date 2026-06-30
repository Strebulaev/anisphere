from rest_framework import serializers
from django.db.models import Q, Count, Prefetch
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
    MessageReadStatus,
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
    UserPostHidden,
    UserPostNotInterested,
    UserNotificationSettings,
)
from users.models import User


# ==================== REPORT SERIALIZER ====================


class ReportSerializer(serializers.ModelSerializer):
    """Serializer для жалоб"""

    reporter_username = serializers.CharField(
        source="reporter.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "content_type",
            "content_id",
            "reason",
            "reason_display",
            "comment",
            "status",
            "status_display",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)
    replies_count = serializers.SerializerMethodField()
    is_reply = serializers.ReadOnlyField()
    parent_id = serializers.IntegerField(source="parent.id", read_only=True)
    parent_username = serializers.CharField(
        source="parent.author.username", read_only=True
    )
    reply_to_data = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_username",
            "author_avatar",
            "author_is_premium",
            "text",
            "parent",
            "parent_id",
            "parent_username",
            "is_reply",
            "replies_count",
            "reply_to",
            "reply_to_data",
            "created_at",
            "updated_at",
            "is_deleted",
            "is_edited",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_replies_count(self, obj):
        if hasattr(obj, "replies"):
            return obj.replies.filter(is_deleted=False).count()
        return obj.replies.count() if hasattr(obj, "replies") else 0

    def get_reply_to_data(self, obj):
        """Получаем данные о комментарии, на который ответили"""
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "author_id": obj.reply_to.author_id,
                "author_username": obj.reply_to.author.username,
                "author_avatar": obj.reply_to.author.avatar.url
                if obj.reply_to.author.avatar
                else None,
                "text": obj.reply_to.text,
                "created_at": obj.reply_to.created_at.isoformat()
                if obj.reply_to.created_at
                else None,
            }
        return None


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["text", "parent", "content_type", "object_id"]

    def validate(self, data):
        # Проверяем, что object_id существует для указанного content_type
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                model_class.objects.get(pk=object_id)
            except model_class.DoesNotExist:
                raise serializers.ValidationError("Object does not exist.")

        # Проверяем, что родительский комментарий существует и принадлежит тому же объекту
        parent = data.get("parent")
        if parent:
            if parent.content_type != content_type or parent.object_id != object_id:
                raise serializers.ValidationError(
                    "Parent comment must be on the same object."
                )

        return data

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class GroupSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source="creator.username", read_only=True)
    is_member = serializers.SerializerMethodField()
    is_moderator = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "avatar_url",
            "avatar_file",
            "banner_url",
            "banner_file",
            "is_private",
            "creator",
            "creator_username",
            "moderators",
            "members_count",
            "posts_count",
            "is_member",
            "is_moderator",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "creator",
            "members_count",
            "posts_count",
            "created_at",
            "updated_at",
        ]

    def get_is_member(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user).exists()
        return False

    def get_is_moderator(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return (
                obj.moderators.filter(pk=request.user.pk).exists()
                or obj.creator == request.user
            )
        return False


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name", "description", "avatar_url", "banner_url", "is_private", "anime"]
        read_only_fields = ["slug", "creator", "members_count", "posts_count", "created_at", "updated_at"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            "id",
            "user",
            "user_username",
            "group",
            "group_name",
            "role",
            "joined_at",
        ]
        read_only_fields = ["id", "joined_at"]


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(
        source="author.display_name", read_only=True
    )
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)
    anime_title = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_poster = serializers.ImageField(source="anime.poster", read_only=True)
    anime = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_avatar = serializers.ImageField(source="group.avatar_file", read_only=True)
    media_url = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    original_post_data = serializers.SerializerMethodField()
    media_files = serializers.SerializerMethodField()
    attachments_data = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    edited_at_display = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()
    spoiler_for = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "author_username",
            "author_display_name",
            "author_avatar",
            "author_is_premium",
            "title",
            "text",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "anime",
            "anime_title",
            "anime_poster",
            "anime_rating",
            "group",
            "group_name",
            "group_avatar",
            "reactor_post",
            "post_type",
            "original_post",
            "original_post_data",
            "repost_comment",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "shares_count",
            "is_liked",
            "is_disliked",
            "is_favorited",
            "is_bookmarked",
            "is_following",
            "is_pinned",
            "is_deleted",
            "allow_comments",
            "status",
            "visibility",
            "is_spoiler",
            "spoiler_for",
            "spoiler_description",
            "media_files",
            "attachments_data",
            "content_preview",
            "media_url",
            "hashtags",
            "created_at",
            "updated_at",
            "edited_at",
            "edited_at_display",
            "published_at",
            "can_edit",
            "can_delete",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "likes_count",
            "published_at",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "shares_count",
        ]

    def get_group(self, obj):
        if not obj.group:
            return None

        try:
            return {
                "id": obj.group.id,
                "name": obj.group.name or "",
                "avatar": obj.group.avatar_file.url if obj.group.avatar_file else None,
            }
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting group for post {obj.id}: {e}")
            return None

    def get_anime(self, obj):
        """Сначала ищем в attachments, потом в ForeignKey"""
        # Проверяем attachments через prefetch
        if hasattr(obj, '_prefetched_objects_cache') and 'attachments' in obj._prefetched_objects_cache:
            attachments = obj.attachments.filter(content_type='anime')
        else:
            from .models import PostAttachment
            attachments = PostAttachment.objects.filter(post=obj, content_type='anime')

        first_attachment = attachments.first()
        if first_attachment:
            try:
                from anime.models import Anime
                anime = Anime.objects.get(id=first_attachment.object_id)
                poster_url = None
                # Сначала проверяем локальный файл
                if anime.poster:
                    try:
                        if anime.poster.storage.exists(anime.poster.name):
                            poster_url = anime.poster.url
                            request = self.context.get("request")
                            if request and poster_url and not poster_url.startswith("http"):
                                poster_url = request.build_absolute_uri(poster_url)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Error getting poster for anime {anime.id}: {e}")
                        poster_url = None
                if not poster_url:
                    poster_url = anime.poster_url or None

                return {
                    "id": anime.id,
                    "title_ru": anime.title_ru or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "poster_url": poster_url,
                }
            except Anime.DoesNotExist:
                pass

        # Fallback к ForeignKey
        if obj.anime:
            poster_url = None
            if obj.anime.poster:
                try:
                    if obj.anime.poster.storage.exists(obj.anime.poster.name):
                        poster_url = obj.anime.poster.url
                        request = self.context.get("request")
                        if request and poster_url and not poster_url.startswith("http"):
                            poster_url = request.build_absolute_uri(poster_url)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error getting poster for anime {obj.anime.id}: {e}")
                    poster_url = None
            if not poster_url:
                poster_url = obj.anime.poster_url or None

            return {
                "id": obj.anime.id,
                "title_ru": obj.anime.title_ru or "",
                "title_en": obj.anime.title_en or "",
                "poster": poster_url,
                "poster_url": poster_url,
            }
        return None

    def get_playlist(self, obj):
        """Возвращает данные плейлиста ТОЛЬКО если нет attachments"""
        # Если есть attachments с плейлистами - не показываем старый playlist
        if hasattr(obj, 'attachments') and obj.attachments.filter(content_type='playlist').exists():
            return None
        
        if not obj.playlist:
            return None

        try:
            poster_url = None
            if obj.playlist.cover_image:
                try:
                    request = self.context.get("request")
                    poster_url = obj.playlist.cover_image.url
                    if request and poster_url and not poster_url.startswith("http"):
                        poster_url = request.build_absolute_uri(poster_url)
                except Exception:
                    pass

            return {
                "id": obj.playlist.id,
                "title": obj.playlist.title or "",
                "anime_count": obj.playlist.items.count() if hasattr(obj.playlist, "items") else 0,
                "poster_url": poster_url,
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting playlist for post {obj.id}: {e}")
            return None

    def get_reactor_post(self, obj):
        if not obj.reactor_post:
            return None

        try:
            return {
                "id": obj.reactor_post.id,
                "title": obj.reactor_post.title or "",
                "video_url": obj.reactor_post.video_url or "",
                "user": {
                    "id": obj.reactor_post.user.id,
                    "username": obj.reactor_post.user.username,
                },
            }
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting reactor_post for post {obj.id}: {e}")
            return None

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_disliked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.dislikes.filter(user=request.user).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return False
        # protect against cases where the GenericRelation hasn't been added
        favs = getattr(obj, "favorites", None)
        if favs is None:
            return False
        try:
            return favs.filter(user=request.user).exists()
        except Exception:
            # if the relation is misconfigured or the field isn't a queryset
            return False

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated and obj.author:
            return obj.author.following.filter(follower=request.user).exists()
        return False

    def get_original_post_data(self, obj):
        if obj.original_post:
            return PostSerializer(obj.original_post, context=self.context).data
        return None

    def get_media_files(self, obj):
        try:
            media = obj.media_files.all() if hasattr(obj, "media_files") else []
            return PostMediaSerializer(media, many=True, context=self.context).data
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error serializing media files for post {obj.id}: {e}")
            return []

    def get_attachments_data(self, obj):
        """Возвращает ВСЕ attachments для поста"""
        try:
            # Используем prefetch_related если доступен
            if hasattr(obj, '_prefetched_objects_cache') and 'attachments' in obj._prefetched_objects_cache:
                attachments = obj.attachments.all()
            elif hasattr(obj, 'attachments'):
                attachments = obj.attachments.all()
            else:
                from .models import PostAttachment
                attachments = PostAttachment.objects.filter(post_id=obj.id)
            
            # DEBUG лог
            import logging
            logger = logging.getLogger(__name__)
            attachments_list = list(attachments)
            logger.info(f"DEBUG: Post {obj.id} has {len(attachments_list)} attachments")
            
            result = PostAttachmentSerializer(
                attachments_list, many=True, context=self.context
            ).data
            
            logger.info(f"DEBUG: Attachments data: {result}")
            return result
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting attachments for post {obj.id}: {e}")
            return []

    def get_content_preview(self, obj):
        text = obj.text or ""
        if len(text) > 200:
            return text[:200] + "..."
        return text

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request and request.user == obj.author:
            from django.utils import timezone
            from datetime import timedelta

            return (timezone.now() - obj.created_at) < timedelta(minutes=5)
        return False

    def get_can_delete(self, obj):
        request = self.context.get("request")
        if request and (request.user == obj.author or request.user.is_staff):
            return True
        return False

    def get_hashtags(self, obj):
        if hasattr(obj, "hashtag_links"):
            return [link.hashtag.name for link in obj.hashtag_links.all()]
        return []

    def get_spoiler_for(self, obj):
        """Возвращает информацию об аниме, к которому относится спойлер"""
        if obj.spoiler_for:
            return {
                "id": obj.spoiler_for.id,
                "title_ru": obj.spoiler_for.title_ru,
                "title_en": obj.spoiler_for.title_en,
            }
        return None

    def get_edited_at_display(self, obj):
        if obj.edited_at:
            from django.utils import timezone

            delta = timezone.now() - obj.edited_at
            if delta.days > 1:
                return f"(изменено {obj.edited_at.strftime('%d.%m.%y')})"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"(изменено {hours}ч назад)"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"(изменено {minutes}м назад)"
            else:
                return "(изменено сейчас)"
        return None


# Alias for feed - uses the same serializer
FeedPostSerializer = PostSerializer


class PostCreateSerializer(serializers.ModelSerializer):
    # Убираем ListField - обрабатываем raw данные в create()
    anime_ids = serializers.CharField(required=False, write_only=True)
    playlist_ids = serializers.CharField(required=False, write_only=True)
    reactor_ids = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Post
        fields = [
            "title",
            "text",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "anime",
            "anime_rating",
            "group",
            "playlist",
            "reactor_post",
            "post_type",
            "original_post",
            "repost_comment",
            "visibility",
            "allow_comments",
            "is_spoiler",
            "spoiler_description",
            "spoiler_for",
            # Новые поля для множественных привязок
            "anime_ids",
            "playlist_ids",
            "reactor_ids",
        ]

    def create(self, validated_data):
        # Получаем request из контекста
        request = self.context.get('request')
        
        # Извлекаем множественные ID - убираем из validated_data чтобы не передавать в Post.objects.create()
        anime_ids = validated_data.pop("anime_ids", [])
        playlist_ids = validated_data.pop("playlist_ids", [])
        reactor_ids = validated_data.pop("reactor_ids", [])
        
        if request:
            # Для FormData с множественными значениями используем getlist()
            # Поддерживаем оба формата: 'anime_ids' и 'anime_ids[]'
            anime_raw = request.data.getlist('anime_ids[]') or request.data.getlist('anime_ids') or []
            playlist_raw = request.data.getlist('playlist_ids[]') or request.data.getlist('playlist_ids') or []
            reactor_raw = request.data.getlist('reactor_ids[]') or request.data.getlist('reactor_ids') or []
            
            # Преобразуем в списки целых чисел
            if anime_raw:
                anime_ids = [int(x) for x in anime_raw if x]
            else:
                anime_ids = []
            
            if playlist_raw:
                playlist_ids = [int(x) for x in playlist_raw if x]
            else:
                playlist_ids = []
            
            if reactor_raw:
                reactor_ids = [int(x) for x in reactor_raw if x]
            else:
                reactor_ids = []
        
        # Создаём пост
        post = super().create(validated_data)

        # Создаём attachments для множественных привязок
        if anime_ids:
            from anime.models import Anime

            for anime_id in anime_ids:
                try:
                    anime = Anime.objects.get(id=anime_id)
                    attachment = PostAttachment(
                        post=post,
                        object_id=anime.id,
                        content_type="anime",
                        metadata={"title": anime.title_ru or anime.title_en},
                    )
                    attachment.save()
                except Anime.DoesNotExist:
                    pass
            # Для обратной совместимости устанавливаем первое аниме
            try:
                post.anime = Anime.objects.get(id=anime_ids[0])
                post.save(update_fields=["anime"])
            except (Anime.DoesNotExist, IndexError):
                pass

        if playlist_ids:
            from playlists.models import Playlist

            for playlist_id in playlist_ids:
                try:
                    playlist = Playlist.objects.get(id=playlist_id)
                    attachment = PostAttachment(
                        post=post,
                        object_id=playlist.id,
                        content_type="playlist",
                        metadata={"title": playlist.title},
                    )
                    attachment.save()
                except Playlist.DoesNotExist:
                    pass
            # Для обратной совместимости
            try:
                post.playlist = Playlist.objects.get(id=playlist_ids[0])
                post.save(update_fields=["playlist"])
            except (Playlist.DoesNotExist, IndexError):
                pass

        if reactor_ids:
            from reactor.models import ReactorPost

            for reactor_id in reactor_ids:
                try:
                    reactor = ReactorPost.objects.get(id=reactor_id)
                    attachment = PostAttachment(
                        post=post,
                        object_id=reactor.id,
                        content_type="shorts",
                        metadata={"title": reactor.title},
                    )
                    attachment.save()
                except ReactorPost.DoesNotExist:
                    pass
            # Для обратной совместимости
            try:
                post.reactor_post = ReactorPost.objects.get(id=reactor_ids[0])
                post.save(update_fields=["reactor_post"])
            except (ReactorPost.DoesNotExist, IndexError):
                pass

        return post


class PostUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления поста - обрабатывает attachments правильно"""
    
    # Поля для attachments
    anime_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        allow_empty=True
    )
    playlist_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        allow_empty=True
    )
    
    # Для обратной совместимости - single anime_id
    anime_id = serializers.IntegerField(
        required=False,
        write_only=True,
        allow_null=True
    )
    playlist_id = serializers.IntegerField(
        required=False,
        write_only=True,
        allow_null=True
    )

    # Для чтения - возвращаем attachments_data
    attachments_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "title",
            "text",
            "visibility",
            "allow_comments",
            "is_spoiler",
            "spoiler_description",
            "spoiler_for",
            # Attachments - новые поля
            "anime_ids",
            "playlist_ids",
            # Для обратной совместимости
            "anime_id",
            "playlist_id",
            # Для чтения
            "attachments_data",
        ]

    def update(self, instance, validated_data):
        request = self.context.get('request')
        
        # Импорты моделей
        from anime.models import Anime
        from playlists.models import Playlist
        
        # Проверяем request.data напрямую - важно для FormData
        # Если поле передано (даже пустым) - обновляем, если нет - не трогаем
        anime_ids_changed = False
        playlist_ids_changed = False
        anime_ids = None
        playlist_ids = None
        
        if request and hasattr(request.data, 'getlist'):
            # Проверяем через getlist для FormData
            # ВАЖНО: getlist возвращает [] если ключа нет, или [''] если ключ есть но пустой
            anime_raw = request.data.getlist('anime_ids[]') or request.data.getlist('anime_ids')
            playlist_raw = request.data.getlist('playlist_ids[]') or request.data.getlist('playlist_ids')
            
            # Проверяем ЧЕРЕЗ getlist - если вернул что-то (даже ['']) значит поле было передано
            anime_ids_changed = bool(anime_raw) or 'anime_ids[]' in request.data or 'anime_ids' in request.data
            playlist_ids_changed = bool(playlist_raw) or 'playlist_ids[]' in request.data or 'playlist_ids' in request.data
            
            # ОЧИЩАЕМ пустые строки и '0' (маркер удаления) из списков
            if anime_ids_changed:
                # Фильтруем None, пустые строки, пробелы и '0'
                anime_ids = [int(x) for x in anime_raw if x and str(x).strip() and str(x).strip() != '0'] if anime_raw else []
            if playlist_ids_changed:
                playlist_ids = [int(x) for x in playlist_raw if x and str(x).strip() and str(x).strip() != '0'] if playlist_raw else []
        else:
            # Fallback для JSON
            anime_ids = validated_data.get("anime_ids")
            playlist_ids = validated_data.get("playlist_ids")
            anime_ids_changed = anime_ids is not None
            playlist_ids_changed = playlist_ids is not None
        
        # DEBUG логи
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"UPDATE POST {instance.id}: anime_ids_changed={anime_ids_changed}, anime_ids={anime_ids}")
        logger.info(f"UPDATE POST {instance.id}: playlist_ids_changed={playlist_ids_changed}, playlist_ids={playlist_ids}")
        
        # Обновляем основное поле anime
        if anime_ids_changed:
            if anime_ids:
                try:
                    instance.anime = Anime.objects.get(id=anime_ids[0])
                except (Anime.DoesNotExist, IndexError):
                    instance.anime = None
            else:
                instance.anime = None
            instance.save(update_fields=["anime"])
        
        # Обновляем основное поле playlist
        if playlist_ids_changed:
            if playlist_ids:
                try:
                    instance.playlist = Playlist.objects.get(id=playlist_ids[0])
                except (Playlist.DoesNotExist, IndexError):
                    instance.playlist = None
            else:
                instance.playlist = None
            instance.save(update_fields=["playlist"])
        
        # Обновляем обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем attachments ТОЛЬКО если поля были переданы
        if anime_ids_changed or playlist_ids_changed:
            self._update_attachments(instance, anime_ids, playlist_ids)
        
        return instance

    def _update_attachments(self, post, anime_ids, playlist_ids):
        """Обновляем PostAttachment записи"""
        from anime.models import Anime
        from playlists.models import Playlist

        # Очищаем старые attachments
        PostAttachment.objects.filter(post=post).delete()

        # Создаем новые
        if anime_ids:
            for anime_id in anime_ids:
                try:
                    anime = Anime.objects.get(id=anime_id)
                    PostAttachment.objects.create(
                        post=post,
                        object_id=anime.id,
                        content_type="anime",
                        metadata={"title": anime.title_ru or anime.title_en},
                    )
                except Anime.DoesNotExist:
                    pass
        
        if playlist_ids:
            for playlist_id in playlist_ids:
                try:
                    playlist = Playlist.objects.get(id=playlist_id)
                    PostAttachment.objects.create(
                        post=post,
                        object_id=playlist.id,
                        content_type="playlist",
                        metadata={"title": playlist.title},
                    )
                except Playlist.DoesNotExist:
                    pass

    def get_attachments_data(self, obj):
        from .serializers import PostAttachmentSerializer
        attachments = obj.attachments.all().distinct()
        return PostAttachmentSerializer(attachments, many=True, context=self.context).data


class PostMediaSerializer(serializers.ModelSerializer):
    # provide a consistently named public URL for frontend consumers
    file_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    media_type_display = serializers.CharField(
        source="get_media_type_display", read_only=True
    )

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "media_type",
            "media_type_display",
            "file",
            "file_url",
            "url",
            "thumbnail",
            "thumbnail_url",
            "caption",
            "order",
            "width",
            "height",
            "duration",
            "file_size",
            "mime_type",
        ]
        read_only_fields = ["id", "file_size", "mime_type"]

    def _make_absolute(self, path_or_url):
        if not path_or_url:
            return None
        request = self.context.get("request")
        if (
            request
            and hasattr(path_or_url, "startswith")
            and path_or_url.startswith("/")
        ):
            return request.build_absolute_uri(path_or_url)
        return path_or_url

    def get_file_url(self, obj):
        if obj.file:
            # return absolute URL to stored file
            return self._make_absolute(obj.file.url)
        # fall back to external url field
        return obj.url or None

    def get_url(self, obj):
        # `url` used by frontend; prefer file_url if available
        if obj.file:
            return self._make_absolute(obj.file.url)
        return obj.url or None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class PostAttachmentSerializer(serializers.ModelSerializer):
    content_type_display = serializers.CharField(
        source="get_content_type_display", read_only=True
    )
    anime_data = serializers.SerializerMethodField()
    playlist_data = serializers.SerializerMethodField()
    shorts_data = serializers.SerializerMethodField()

    class Meta:
        model = PostAttachment
        fields = [
            "id",
            "content_type",
            "content_type_display",
            "object_id",
            "metadata",
            "anime_data",
            "playlist_data",
            "shorts_data",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_anime_data(self, obj):
        if obj.content_type == "anime":
            try:
                from anime.serializers import AnimeSerializer
                from anime.models import Anime

                anime = Anime.objects.get(id=obj.object_id)
                return AnimeSerializer(anime).data
            except (ImportError, Anime.DoesNotExist, Exception):
                return None
        return None

    def get_playlist_data(self, obj):
        if obj.content_type == "playlist":
            try:
                from playlists.serializers import PlaylistSerializer
                from playlists.models import Playlist

                playlist = Playlist.objects.get(id=obj.object_id)
                return PlaylistSerializer(playlist).data
            except (ImportError, Playlist.DoesNotExist, Exception):
                return None
        return None

    def get_shorts_data(self, obj):
        if obj.content_type == "shorts":
            try:
                from reactor.serializers import ReactorPostSerializer
                from reactor.models import ReactorPost

                shorts = ReactorPost.objects.get(id=obj.object_id)
                return ReactorPostSerializer(shorts).data
            except (ImportError, ReactorPost.DoesNotExist, Exception):
                return None
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_avatar = serializers.ImageField(source="sender.avatar", read_only=True)
    sender_nickname = serializers.CharField(source="sender.nickname", read_only=True)
    reply_text = serializers.CharField(source="reply_to.text", read_only=True)
    reply_sender_username = serializers.CharField(
        source="reply_to.sender.username", read_only=True
    )
    reply_to_message = serializers.SerializerMethodField()
    media_url = serializers.ImageField(source="media", read_only=True)
    shared_post_data = PostSerializer(source="shared_post", read_only=True)
    shared_anime_title = serializers.CharField(
        source="shared_anime.title_ru", read_only=True
    )
    shared_anime_poster = serializers.ImageField(
        source="shared_anime.poster", read_only=True
    )
    shared_anime_data = serializers.SerializerMethodField()
    shared_playlist_data = serializers.SerializerMethodField()
    shared_shorts_data = serializers.SerializerMethodField()
    pinned_by_username = serializers.CharField(
        source="pinned_by.username", read_only=True
    )
    forwarded_from_data = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    # Добавляем поля для статуса прочтения и идентификации "моего" сообщения
    is_read_by_other = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "chat",
            "private_chat",
            "sender",
            "sender_id",
            "sender_username",
            "sender_nickname",
            "sender_avatar",
            "text",
            "topic_id",
            "media",
            "media_type",
            "media_url",
            "location_latitude",
            "location_longitude",
            "location_name",
            "shared_post",
            "shared_post_data",
            "shared_anime",
            "shared_anime_title",
            "shared_anime_poster",
            "shared_anime_data",
            "shared_playlist",
            "shared_playlist_data",
            "shared_shorts",
            "shared_shorts_data",
            "reply_to",
            "reply_text",
            "reply_sender_username",
            "reply_to_message",
            "is_edited",
            "edited_at",
            "is_deleted",
            "deleted_at",
            "deleted_by",
            "is_pinned",
            "pinned_by",
            "pinned_by_username",
            "pinned_at",
            "forwarded_from",
            "forwarded_from_data",
            "reactions",
            "attachments",
            "created_at",
            "updated_at",
            # Новые поля
            "is_read_by_other",
            "read_count",
            "is_mine",
        ]
        read_only_fields = [
            "id",
            "sender",
            "is_edited",
            "edited_at",
            "is_deleted",
            "deleted_at",
            "deleted_by",
            "is_pinned",
            "pinned_by",
            "pinned_at",
            "forwarded_from",
            "created_at",
            "updated_at",
        ]

    def get_is_read_by_other(self, obj):
        """
        Проверяет, прочитано ли сообщение получателем (для личных чатов)
        Возвращает True, если сообщение прочитано собеседником
        """
        request = self.context.get("request")
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        # Если сообщение отправлено текущим пользователем,
        # проверяем, прочитал ли его получатель
        if obj.sender_id == request.user.id:
            # Для личного чата
            if obj.private_chat:
                # Определяем получателя (не отправителя)
                if obj.private_chat.user1_id == request.user.id:
                    other_user_id = obj.private_chat.user2_id
                else:
                    other_user_id = obj.private_chat.user1_id

                # Проверяем, есть ли запись о прочтении
                is_read = MessageReadStatus.objects.filter(
                    message=obj, user_id=other_user_id
                ).exists()

                # DEBUG лог
                print(f"DEBUG: is_read_by_other for msg {obj.id}: other_user={other_user_id}, is_read={is_read}")
                
                return is_read

            # Для группового чата - проверяем, прочитал ли кто-то кроме отправителя
            elif obj.chat:
                return (
                    MessageReadStatus.objects.filter(message=obj)
                    .exclude(user_id=request.user.id)
                    .exists()
                )

        # Если сообщение от другого пользователя,
        # для получателя это поле не нужно, но возвращаем False
        return False

    def get_read_count(self, obj):
        """
        Количество пользователей, прочитавших сообщение (для групповых чатов)
        """
        if obj.chat:
            return obj.read_statuses.count()
        return 0

    def get_is_mine(self, obj):
        """
        Определяет, является ли сообщение отправленным текущим пользователем.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.sender_id == request.user.id

    def get_reply_to_message(self, obj):
        """Получаем полные данные о цитируемом сообщении"""
        if obj.reply_to:
            reply_sender_avatar = None
            if obj.reply_to.sender.avatar:
                try:
                    reply_sender_avatar = obj.reply_to.sender.avatar.url
                    request = self.context.get("request")
                    if (
                        request
                        and reply_sender_avatar
                        and not reply_sender_avatar.startswith("http")
                    ):
                        reply_sender_avatar = request.build_absolute_uri(
                            reply_sender_avatar
                        )
                except Exception:
                    pass

            reply_media = None
            if obj.reply_to.media:
                try:
                    reply_media = obj.reply_to.media.url
                    request = self.context.get("request")
                    if request and reply_media and not reply_media.startswith("http"):
                        reply_media = request.build_absolute_uri(reply_media)
                except Exception:
                    pass

            return {
                "id": obj.reply_to.id,
                "text": obj.reply_to.text,
                "sender_id": obj.reply_to.sender.id,
                "sender_username": obj.reply_to.sender.username,
                "sender_avatar": reply_sender_avatar,
                "media": reply_media,
                "media_type": obj.reply_to.media_type,
                "created_at": obj.reply_to.created_at,
            }
        return None

    def get_forwarded_from_data(self, obj):
        """Получаем данные о пересланном сообщении"""
        if obj.forwarded_from:
            return {
                "id": obj.forwarded_from.id,
                "text": obj.forwarded_from.text,
                "sender": UserSimpleSerializer(obj.forwarded_from.sender).data,
                "media_type": obj.forwarded_from.media_type,
                "media_url": obj.forwarded_from.media.url
                if obj.forwarded_from.media
                else None,
            }
        return None

    def get_attachments(self, obj):
        """Получаем вложения сообщения (медиафайлы + контент: аниме, плейлисты, shorts, посты)"""
        # Файловые вложения
        file_attachments = obj.attachments.all()
        attachments_data = AttachmentSerializer(file_attachments, many=True, context=self.context).data
        
        # Контент-вложения (аниме, плейлисты, shorts, посты)
        content_attachments = obj.content_attachments.all().select_related(
            'message'
        )

        for ca in content_attachments:
            attachment_data = {
                'id': ca.id,
                'type': ca.content_type,
                'object_id': ca.object_id,
                'data': None,
            }
            
            if ca.content_type == 'anime':
                from anime.models import Anime
                try:
                    anime = Anime.objects.get(id=ca.object_id)
                    attachment_data['data'] = {
                        'id': anime.id,
                        'title_ru': anime.title_ru,
                        'title_en': anime.title_en,
                        'poster_url': anime.poster.url if anime.poster else anime.poster_url,
                        'kind': anime.kind,
                        'year': anime.year,
                    }
                except Anime.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'playlist':
                from playlists.models import Playlist
                try:
                    playlist = Playlist.objects.get(id=ca.object_id)
                    items = playlist.items.select_related('anime')[:4]
                    posters = []
                    for item in items:
                        if item.anime:
                            poster = item.anime.poster.url if item.anime.poster else item.anime.poster_url
                            if poster:
                                posters.append(poster)
                    
                    attachment_data['data'] = {
                        'id': playlist.id,
                        'title': playlist.title,
                        'description': playlist.description,
                        'poster_url': posters[0] if posters else None,
                        'posters': posters,
                        'items_count': playlist.items.count(),
                        'user': {
                            'id': playlist.user.id,
                            'username': playlist.user.username,
                        } if playlist.user else None,
                    }
                except Playlist.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'shorts':
                from reactor.models import ReactorPost
                try:
                    shorts = ReactorPost.objects.get(id=ca.object_id)
                    attachment_data['data'] = {
                        'id': shorts.id,
                        'video_url': shorts.video_url,
                        'thumbnail_url': shorts.thumbnail_url,
                        'text': shorts.text,
                        'author': {
                            'id': shorts.author.id,
                            'username': shorts.author.username,
                            'avatar_url': shorts.author.avatar.url if shorts.author.avatar else None,
                        } if shorts.author else None,
                        'anime': {
                            'id': shorts.anime.id,
                            'title_ru': shorts.anime.title_ru,
                        } if shorts.anime else None,
                        'likes_count': shorts.likes_count,
                        'views_count': shorts.views_count,
                    }
                except ReactorPost.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'post':
                try:
                    post = Post.objects.get(id=ca.object_id)
                    attachment_data['data'] = {
                        'id': post.id,
                        'text': post.text[:200],
                        'author': {
                            'id': post.author.id,
                            'username': post.author.username,
                            'avatar_url': post.author.avatar.url if post.author.avatar else None,
                        } if post.author else None,
                        'likes_count': post.likes_count,
                        'comments_count': post.comments_count,
                    }
                except Post.DoesNotExist:
                    pass
            
            if attachment_data['data']:
                attachments_data.append(attachment_data)
        
        return attachments_data

    def get_shared_anime_data(self, obj):
        """Получаем данные прикреплённого аниме"""
        if obj.shared_anime:
            return {
                "id": obj.shared_anime.id,
                "title_ru": obj.shared_anime.title_ru,
                "title_en": obj.shared_anime.title_en,
                "poster_url": obj.shared_anime.poster.url
                if obj.shared_anime.poster
                else obj.shared_anime.poster_url,
                "kind": obj.shared_anime.kind,
                "year": obj.shared_anime.year,
            }
        return None

    def get_shared_playlist_data(self, obj):
        """Получаем данные прикреплённого плейлиста"""
        if obj.shared_playlist:
            # Получаем первые 4 постера из плейлиста
            items = (
                obj.shared_playlist.items.select_related("anime")[:4]
                if hasattr(obj.shared_playlist, "items")
                else []
            )
            posters = []
            for item in items:
                if item.anime:
                    poster = (
                        item.anime.poster.url
                        if item.anime.poster
                        else item.anime.poster_url
                    )
                    if poster:
                        posters.append(poster)

            return {
                "id": obj.shared_playlist.id,
                "title": obj.shared_playlist.title,
                "description": obj.shared_playlist.description,
                "poster_url": posters[0] if posters else None,
                "posters": posters,
                "items_count": len(items),
                "user": {
                    "id": obj.shared_playlist.user.id,
                    "username": obj.shared_playlist.user.username,
                }
                if obj.shared_playlist.user
                else None,
            }
        return None

    def get_shared_shorts_data(self, obj):
        """Получаем данные прикреплённого shorts (Reactor поста)"""
        if obj.shared_shorts:
            return {
                "id": obj.shared_shorts.id,
                "video_url": obj.shared_shorts.video_url,
                "thumbnail_url": obj.shared_shorts.thumbnail_url,
                "text": obj.shared_shorts.text,
                "author": {
                    "id": obj.shared_shorts.author.id,
                    "username": obj.shared_shorts.author.username,
                    "avatar_url": obj.shared_shorts.author.avatar.url
                    if obj.shared_shorts.author.avatar
                    else None,
                }
                if obj.shared_shorts.author
                else None,
                "anime": {
                    "id": obj.shared_shorts.anime.id,
                    "title_ru": obj.shared_shorts.anime.title_ru,
                }
                if obj.shared_shorts.anime
                else None,
                "likes_count": obj.shared_shorts.likes_count,
                "views_count": obj.shared_shorts.views_count,
            }
        return None

    def validate(self, data):
        text = data.get("text", "").strip()
        media = data.get("media")
        location_latitude = data.get("location_latitude")
        shared_post = data.get("shared_post")
        shared_anime = data.get("shared_anime")
        shared_playlist = data.get("shared_playlist")
        shared_shorts = data.get("shared_shorts")

        # Проверяем есть ли вложения (anime_ids, playlist_ids и т.д.)
        # Проверяем оба формата: с [] и без (для обратной совместимости)
        request = self.context.get("request")
        has_attachments = False
        if request and hasattr(request.data, 'getlist'):
            # Проверяем через getlist для FormData
            anime_ids = request.data.getlist('anime_ids[]') or request.data.getlist('anime_ids')
            playlist_ids = request.data.getlist('playlist_ids[]') or request.data.getlist('playlist_ids')
            reactor_ids = request.data.getlist('reactor_ids[]') or request.data.getlist('reactor_ids')
            has_attachments = bool(anime_ids or playlist_ids or reactor_ids)
        else:
            has_attachments = (
                data.get('anime_ids') or 
                data.get('playlist_ids') or 
                data.get('reactor_ids')
            )

        # Проверяем есть ли media_* файлы (media_0, media_1, etc)
        has_media_files = False
        if request and hasattr(request, 'FILES'):
            for key in request.FILES.keys():
                if key.startswith('media_'):
                    has_media_files = True
                    break

        # Сообщение должно содержать что-то из: текст, медиа, геолокация, пост, аниме, плейлист, shorts, или вложения
        if not any(
            [
                text,
                media,
                has_media_files,  # Добавляем проверку на media_* файлы
                location_latitude,
                shared_post,
                shared_anime,
                shared_playlist,
                shared_shorts,
                has_attachments,
            ]
        ):
            raise serializers.ValidationError(
                "Сообщение должно содержать текст, медиафайл, геолокацию, пост, аниме, плейлист или шортс"
            )

        return data


class ContestSerializer(serializers.ModelSerializer):
    organizer_username = serializers.CharField(
        source="organizer.username", read_only=True
    )
    anime_title = serializers.CharField(source="anime.title_ru", read_only=True)

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "description",
            "type",
            "format",
            "status",
            "theme",
            "rules",
            "prize_1st",
            "prize_2nd",
            "prize_3rd",
            "announced_at",
            "started_at",
            "voting_started_at",
            "ended_at",
            "organizer",
            "organizer_username",
            "anime",
            "anime_title",
            "entries_count",
            "votes_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organizer",
            "entries_count",
            "votes_count",
            "created_at",
            "updated_at",
        ]


class ContestEntrySerializer(serializers.ModelSerializer):
    participant_username = serializers.CharField(
        source="participant.username", read_only=True
    )
    participant_avatar = serializers.ImageField(
        source="participant.avatar", read_only=True
    )
    contest_title = serializers.CharField(source="contest.title", read_only=True)

    class Meta:
        model = ContestEntry
        fields = [
            "id",
            "contest",
            "contest_title",
            "participant",
            "participant_username",
            "participant_avatar",
            "title",
            "description",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "votes_count",
            "is_winner",
            "winner_place",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "participant",
            "votes_count",
            "is_winner",
            "winner_place",
            "submitted_at",
            "updated_at",
        ]


class ContestVoteSerializer(serializers.ModelSerializer):
    voter_username = serializers.CharField(source="voter.username", read_only=True)

    class Meta:
        model = ContestVote
        fields = [
            "id",
            "contest",
            "entry",
            "voter",
            "voter_username",
            "vote_type",
            "value",
            "created_at",
        ]
        read_only_fields = ["id", "voter", "created_at"]


class ChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSettings
        fields = [
            "id",
            "user",
            "chat",
            "notifications_enabled",
            "sound_enabled",
            "auto_repeat_enabled",
            "repeat_interval",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "chat", "created_at", "updated_at"]


# Group Chat Serializers
class UserSimpleSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar_url",
            "is_online",
            "last_seen",
        ]

    def get_avatar_url(self, obj):
        """Получаем avatar_url с фоллбэком на дефолтную аватарку"""
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        
        # Возвращаем путь к дефолтной аватарке из папки def_avatars
        from django.conf import settings
        from pathlib import Path
        
        def_ava_dir = settings.MEDIA_ROOT / "def_avatars"
        if def_ava_dir.exists():
            jpg_files = list(def_ava_dir.glob("*.jpg")) + list(def_ava_dir.glob("*.jpeg"))
            if jpg_files:
                # Используем deterministic выбор на основе user.id
                selected_avatar = jpg_files[obj.id % len(jpg_files)]
                return f"/media/def_avatars/{selected_avatar.name}"
        
        return None

    def get_is_online(self, obj):
        """Проверяем онлайн статус через Redis"""
        from core.online_status import online_status

        return online_status.is_online(obj.id)

    def get_last_seen(self, obj):
        """Получаем время последнего seen из Redis"""
        from core.online_status import online_status

        user_data = online_status.get_user_data(obj.id)
        if user_data:
            return user_data.get("last_seen")
        return None


class ChatRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRole
        fields = "__all__"
        read_only_fields = ["created_at", "created_by"]


class ChatMemberSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    role = ChatRoleSerializer(read_only=True)
    effective_permissions = serializers.JSONField(read_only=True)

    class Meta:
        model = ChatMember
        fields = "__all__"
        read_only_fields = ["joined_at"]


class GroupChatCreateSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )
    avatar = serializers.ImageField(required=False, allow_null=True)
    anime = serializers.PrimaryKeyRelatedField(
        queryset=None, required=False, allow_null=True, read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set anime queryset to avoid circular import
        if 'anime' in self.fields:
            from anime.models import Anime
            self.fields['anime'].queryset = Anime.objects.all()

    class Meta:
        model = GroupChat
        fields = ["name", "description", "avatar", "participants", "anime", "is_public"]

    def validate_participants(self, value):
        return value

    def update(self, instance, validated_data):
        """Обновление чата (включая аватар)"""
        participants = validated_data.pop("participants", None)
        avatar = validated_data.pop("avatar", None)

        # Обновляем обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Обновляем аватар
        if avatar is not None:
            instance.avatar.save(avatar.name, avatar, save=True)
        elif "avatar" in validated_data and validated_data["avatar"] is None:
            # Если передали null - удаляем аватар
            instance.avatar.delete(save=True)

        instance.save()

        # Логируем изменение
        ChatAdminLog.objects.create(
            chat=instance,
            user=self.context["request"].user,
            action="chat_updated",
            details={"updated_fields": list(validated_data.keys())},
        )

        return instance

    def create(self, validated_data):
        participants = validated_data.pop("participants", [])
        avatar = validated_data.pop("avatar", None)

        chat = GroupChat.objects.create(**validated_data)

        if avatar:
            chat.avatar = avatar
            chat.save(update_fields=["avatar"])
        else:
            try:
                self._generate_default_avatar(chat)
            except Exception as e:
                print(f"DEBUG: Ошибка генерации аватарки: {e}")

        # Add creator as admin
        ChatMember.objects.create(
            user=self.context["request"].user, chat=chat, is_admin=True
        )

        # Add other participants (можно 0)
        for user_id in participants:
            try:
                user = User.objects.get(id=user_id)
                ChatMember.objects.create(
                    user=user,
                    chat=chat,
                    can_send_messages=True,
                    can_send_media=chat.can_send_media,
                )
            except User.DoesNotExist:
                continue

        # Create admin log
        ChatAdminLog.objects.create(
            chat=chat,
            user=self.context["request"].user,
            action="chat_created",
            details={
                "chat_name": chat.name,
                "participants_count": len(participants) + 1,
            },
        )

        return chat

    def _generate_default_avatar(self, chat):
        """Генерирует дефолтную аватарку с цветом и буквами из названия"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        import random

        # Получаем первые буквы слов (слова длиннее 2 символов)
        words = chat.name.split()
        initials = []
        for word in words:
            if len(word) > 2:
                # Берем первую букву, приводим к верхнему регистру
                first_letter = word[0].upper()
                # Проверяем что это кириллица или латиница
                if first_letter.isalpha():
                    initials.append(first_letter)
                    if len(initials) == 2:
                        break

        if not initials:
            initials = ["?"]

        # Генерируем цвет от красного до фиолетового (HSV)
        # Красный: H=0, фиолетовый: H=270
        hue = random.randint(0, 270)
        saturation = random.randint(60, 100)
        value = random.randint(50, 80)

        # Конвертируем HSV в RGB
        import colorsys

        r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation / 100, value / 100)
        bg_color = (int(r * 255), int(g * 255), int(b * 255))

        # Создаем изображение 200x200
        img = Image.new("RGB", (200, 200), bg_color)
        draw = ImageDraw.Draw(img)

        # Рисуем текст
        text = "".join(initials)[:2]  # Максимум 2 буквы

        try:
            # Пытаемся использовать крупный шрифт
            font = ImageFont.truetype("arial.ttf", 80)
        except Exception:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 80
                )
            except Exception:
                font = ImageFont.load_default()

        # Центрируем текст
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (200 - text_width) // 2
        y = (200 - text_height) // 2

        # Рисуем текст белым цветом
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        # Сохраняем в BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Сохраняем как аватарку
        from django.core.files.uploadedfile import InMemoryUploadedFile

        avatar_file = InMemoryUploadedFile(
            buffer,
            None,
            f"{chat.id}_avatar.png",
            "image/png",
            buffer.getbuffer().nbytes,
            None,
        )
        chat.avatar.save(f"{chat.id}_avatar.png", avatar_file)
        chat.save(update_fields=["avatar"])


class GroupChatSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    members_count = serializers.IntegerField(source="members.count", read_only=True)
    online_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    participants_usernames = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    # Поля для аниме (для групп обсуждений)
    anime_id = serializers.SerializerMethodField()
    anime_title = serializers.SerializerMethodField()
    anime_poster = serializers.SerializerMethodField()
    anime_slug = serializers.SerializerMethodField()  # slug для URL
    # Поля для franchise discussion
    franchise_id = serializers.SerializerMethodField()
    franchise_slug = serializers.SerializerMethodField()  # slug для URL
    discussion_type = (
        serializers.SerializerMethodField()
    )  # тип обсуждения: anime/franchise

    class Meta:
        model = GroupChat
        fields = "__all__"
        read_only_fields = ["created_at", "created_by", "invite_link"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_anime_id(self, obj):
        """Получить ID аниме, связанного с чатом"""
        try:
            if hasattr(obj, "anime_id") and obj.anime_id:
                return obj.anime_id
            if obj.anime:
                return obj.anime.id
        except Exception:
            pass
        return None

    def get_anime_title(self, obj):
        """Получить название аниме, связанного с чатом"""
        try:
            if obj.anime:
                return obj.anime.title_ru or obj.anime.title_en
        except Exception:
            pass
        return None

    def get_anime_poster(self, obj):
        """Получить постер: из anime → из первого аниме франшизы → None"""
        request = self.context.get("request")

        def _abs(url):
            if url and request and not url.startswith("http"):
                return request.build_absolute_uri(url)
            return url

        try:
            if obj.anime:
                if obj.anime.poster:
                    return _abs(obj.anime.poster.url)
                if obj.anime.poster_url:
                    return obj.anime.poster_url
        except Exception:
            pass

        # Franchise-чат без anime - берём постер первого аниме франшизы
        try:
            if getattr(obj, "franchise_id", None):
                from anime.models import Anime as AnimeModel

                first = (
                    AnimeModel.objects.filter(franchise_id=obj.franchise_id)
                    .exclude(poster="")
                    .order_by("franchise_order", "id")
                    .first()
                )
                if first and first.poster:
                    return _abs(first.poster.url)
                if first and first.poster_url:
                    return first.poster_url
        except Exception:
            pass

        return None

    def get_anime_slug(self, obj):
        """Получить slug аниме для URL"""
        try:
            if obj.anime:
                # Используем title_ru или title_en для создания slug
                title = obj.anime.title_ru or obj.anime.title_en
                if title:
                    from django.utils.text import slugify

                    return slugify(title)
        except Exception:
            pass
        return None

    def get_franchise_id(self, obj):
        """Получить ID франшизы"""
        try:
            return getattr(obj, "franchise_id", None)
        except Exception:
            return None

    def get_franchise_slug(self, obj):
        """Получить slug франшизы для URL"""
        try:
            franchise_id = getattr(obj, "franchise_id", None)
            if franchise_id:
                from anime.models import Franchise

                try:
                    franchise = Franchise.objects.get(id=franchise_id)
                    if franchise.name:
                        from django.utils.text import slugify

                        return slugify(franchise.name)
                except Franchise.DoesNotExist:
                    pass
        except Exception:
            pass
        return None

    def get_discussion_type(self, obj):
        """Получить тип обсуждения: anime/franchise/обычный"""
        try:
            return getattr(obj, "discussion_type", "") or ""
        except Exception:
            return ""

    def get_participants_usernames(self, obj):
        """Получить список имен участников"""
        return list(obj.members.values_list("user__username", flat=True))

    def get_online_count(self, obj):
        # Количество онлайн участников
        online_members = obj.members.filter(user__is_online=True).count()
        return online_members

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return {
                    "is_owner": member.is_owner,
                    "role": ChatRoleSerializer(member.role).data
                    if member.role
                    else None,
                    "custom_title": member.custom_title,
                    "is_admin": member.is_admin,
                }
            except ChatMember.DoesNotExist:
                return None
        return None

    def get_user_permissions(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return member.effective_permissions
            except ChatMember.DoesNotExist:
                return {}
        return {}

    def get_last_message(self, obj):
        last_message = Message.objects.filter(chat=obj).order_by("-created_at").first()
        if last_message:
            try:
                sender_data = UserSimpleSerializer(last_message.sender).data
            except Exception:
                sender_data = {
                    "id": None,
                    "username": "[удалён]",
                    "display_name": None,
                    "avatar": None,
                }
            return {
                "id": last_message.id,
                "text": last_message.text,
                "sender": sender_data,
                "created_at": last_message.created_at,
                "is_edited": last_message.is_edited,
                "media_type": last_message.media_type,
            }
        return None


class ChatAdminLogSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    target_user = UserSimpleSerializer(read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = ChatAdminLog
        fields = "__all__"
        read_only_fields = ["created_at"]


# Private Chat Serializers
class PrivateChatSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    user_settings = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChat
        fields = [
            "id",
            "user1",
            "user2",
            "created_at",
            "last_message_at",
            "user1_notifications",
            "user2_notifications",
            "user1_muted_until",
            "user2_muted_until",
            "user1_archived",
            "user2_archived",
            "user1_pinned",
            "user2_pinned",
            "user1_blocked",
            "user2_blocked",
            "other_user",
            "user_settings",
            "unread_count",
            "last_message",
            "name",
        ]
        read_only_fields = ["created_at", "last_message_at"]

    def get_name(self, obj):
        """Получаем имя чата - display_name пользователя"""
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                other = obj.other_user(request.user)
                if other:
                    return other.display_name or other.username
        except Exception as e:
            print(f"Error in get_name: {e}")
        return "Чат"

    def get_other_user(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                other = obj.other_user(request.user)
                if other:
                    return UserSimpleSerializer(other).data
        except Exception as e:
            print(f"Error in get_other_user: {e}")
        return None

    def get_user_settings(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                return obj.get_user_settings(request.user)
        except Exception as e:
            print(f"Error in get_user_settings: {e}")
        return {}

    def get_unread_count(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                # Получаем количество непрочитанных сообщений
                last_read = (
                    MessageReadStatus.objects.filter(
                        user=request.user, message__private_chat=obj
                    )
                    .order_by("-read_at")
                    .first()
                )

                if last_read:
                    unread_count = (
                        Message.objects.filter(
                            private_chat=obj, created_at__gt=last_read.read_at
                        )
                        .exclude(sender=request.user)
                        .count()
                    )
                else:
                    unread_count = (
                        Message.objects.filter(private_chat=obj)
                        .exclude(sender=request.user)
                        .count()
                    )

                return unread_count
        except Exception as e:
            print(f"Error in get_unread_count: {e}")
        return 0

    def get_last_message(self, obj):
        try:
            last_message = (
                Message.objects.filter(private_chat=obj).order_by("-created_at").first()
            )
            if last_message:
                return {
                    "id": last_message.id,
                    "text": last_message.text,
                    "sender": UserSimpleSerializer(last_message.sender).data,
                    "created_at": last_message.created_at,
                    "is_edited": last_message.is_edited,
                    "media_type": last_message.media_type,
                }
        except Exception as e:
            print(f"Error in get_last_message: {e}")
        return None


class PrivateChatCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания личного чата"""

    class Meta:
        model = PrivateChat
        fields = ["user2"]  # user1 берется из request.user

    def validate_user2(self, value):
        """Проверяем что user2 существует и это не текущий пользователь"""
        request = self.context.get("request")
        if request and request.user == value:
            raise serializers.ValidationError("Нельзя создать чат с самим собой")
        return value

    def create(self, validated_data):
        """Создаем личный чат"""
        request = self.context.get("request")
        user1 = request.user
        user2 = validated_data["user2"]

        # Проверяем не существует ли уже чат
        existing_chat = PrivateChat.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).first()

        if existing_chat:
            # Возвращаем существующий чат
            return existing_chat

        # Создаем новый чат
        return PrivateChat.objects.create(user1=user1, user2=user2)


class PrivateChatUserSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор персональных настроек личного чата"""

    custom_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChatUserSettings
        fields = [
            "id",
            "chat",
            "custom_name",
            "custom_avatar",
            "custom_avatar_url",
            "notifications_enabled",
            "updated_at",
        ]
        read_only_fields = ["id", "chat", "updated_at"]

    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.custom_avatar.url)
            return obj.custom_avatar.url
        return None

    def create(self, validated_data):
        # Проверяем, что чат существует и пользователь в нем
        chat = validated_data.get("chat")
        user = validated_data.get("user")

        if not chat.members.filter(id=user.id).exists():
            if user != chat.user1 and user != chat.user2:
                raise serializers.ValidationError("Вы не участник этого чата")

        # Создаем или обновляем настройки
        settings, created = PrivateChatUserSettings.objects.update_or_create(
            chat=chat, user=user, defaults=validated_data
        )
        return settings


class GroupChatSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор настроек группового чата (общие для всех)"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = ["id", "name", "description", "avatar", "avatar_url"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def update(self, instance, validated_data):
        avatar = validated_data.pop("avatar", None)

        # Обновляем поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Сохраняем аватарку отдельно если она есть
        if avatar:
            instance.avatar.save(avatar.name, avatar, save=True)

        instance.save()

        # Логируем изменение
        ChatAdminLog.objects.create(
            chat=instance,
            user=self.context["request"].user,
            action="chat_updated",
            details={"updated_fields": list(validated_data.keys())},
        )

        return instance


# Follow, Like, Dislike Serializers
class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(
        source="follower.username", read_only=True
    )
    following_username = serializers.CharField(
        source="following.username", read_only=True
    )
    follower_avatar = serializers.ImageField(source="follower.avatar", read_only=True)
    following_avatar = serializers.ImageField(source="following.avatar", read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "follower_username",
            "follower_avatar",
            "following",
            "following_username",
            "following_avatar",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PostLikeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = PostLike
        fields = ["id", "user", "username", "avatar", "created_at"]
        read_only_fields = ["id", "created_at"]


class PostDislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostDislike
        fields = ["id", "user", "post", "created_at"]
        read_only_fields = ["id", "created_at"]


class RepostSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_avatar = serializers.ImageField(source="user.avatar", read_only=True)
    original_post_data = PostSerializer(source="original_post", read_only=True)

    class Meta:
        model = Repost
        fields = [
            "id",
            "user",
            "user_username",
            "user_avatar",
            "original_post",
            "original_post_data",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# Achievement Serializers
class AchievementSerializer(serializers.ModelSerializer):
    icon_url = serializers.ImageField(source="icon", read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Achievement
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "icon_url",
            "category",
            "category_display",
            "level",
            "level_display",
            "condition_type",
            "condition_value",
            "unlocked_count",
            "created_at",
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = [
            "id",
            "user",
            "achievement",
            "progress",
            "progress_percentage",
            "is_unlocked",
            "unlocked_at",
        ]

    def get_progress_percentage(self, obj):
        if obj.achievement.condition_value > 0:
            return min(100, (obj.progress / obj.achievement.condition_value) * 100)
        return 100 if obj.is_unlocked else 0


# Uploaded File Serializer
class UploadedFileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    file_url = serializers.ImageField(source="file", read_only=True)
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)

    class Meta:
        model = UploadedFile
        fields = [
            "id",
            "user",
            "username",
            "file",
            "file_url",
            "file_type",
            "file_name",
            "file_size",
            "mime_type",
            "thumbnail",
            "thumbnail_url",
            "width",
            "height",
            "duration",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


# Favorite Serializer
class FavoriteSerializer(serializers.ModelSerializer):
    content_type_display = serializers.CharField(
        source="get_content_type_display", read_only=True
    )

    class Meta:
        model = Favorite
        fields = [
            "id",
            "user",
            "content_type",
            "content_type_display",
            "anime",
            "playlist",
            "post",
            "target_user",
            "group",
            "reactor_post",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# Chat Invite Serializer
class ChatInviteSerializer(serializers.ModelSerializer):
    chat = GroupChatSerializer(read_only=True)
    created_by = UserSimpleSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    uses_remaining = serializers.SerializerMethodField()

    class Meta:
        model = ChatInvite
        fields = [
            "id",
            "chat",
            "token",
            "created_by",
            "expires_at",
            "max_uses",
            "uses_count",
            "is_active",
            "is_valid",
            "uses_remaining",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "token", "uses_count", "created_at", "updated_at"]

    def get_uses_remaining(self, obj):
        """Получить оставшееся количество использований"""
        if obj.max_uses is None:
            return None
        return max(0, obj.max_uses - obj.uses_count)


class ChatInviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInvite
        fields = ["chat", "expires_at", "max_uses"]

    def validate_chat(self, value):
        """Проверяем, что пользователь имеет право создавать приглашения"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if not value.can_invite_users:
                raise serializers.ValidationError(
                    "В этом чате нельзя создавать приглашения"
                )

            # Проверяем, что пользователь является участником с правами
            member = value.members.filter(user=request.user).first()
            if not member:
                raise serializers.ValidationError(
                    "Вы не являетесь участником этого чата"
                )

        return value

    def create(self, validated_data):
        """Создаем приглашение с уникальным токеном"""
        import secrets
        from .models import ChatInvite

        validated_data["created_by"] = self.context["request"].user

        # Генерируем уникальный токен
        while True:
            token = secrets.token_urlsafe(16)
            if not ChatInvite.objects.filter(token=token).exists():
                validated_data["token"] = token
                break

        return super().create(validated_data)


# Reaction Serializer
class ReactionSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "message", "user", "emoji", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class ReactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ["message", "emoji"]

    def validate_emoji(self, value):
        """Проверяем, что это валидный эмодзи"""
        import emoji

        if not emoji.is_emoji(value):
            raise serializers.ValidationError("Неверный формат эмодзи")
        return value

    def validate_message(self, value):
        """Проверяем, что сообщение существует и не удалено"""
        if value.is_deleted:
            raise serializers.ValidationError(
                "Нельзя реагировать на удаленное сообщение"
            )
        return value

    def create(self, validated_data):
        """Создаем реакцию или удаляем существующую"""
        user = self.context["request"].user
        message = validated_data["message"]
        emoji = validated_data["emoji"]

        # Проверяем, существует ли уже такая реакция
        existing = Reaction.objects.filter(
            message=message, user=user, emoji=emoji
        ).first()

        if existing:
            # Если существует - удаляем (toggle)
            existing.delete()
            # Обновляем реакции в сообщении
            self._update_message_reactions(message)
            return None

        # Создаем новую реакцию
        reaction = Reaction.objects.create(message=message, user=user, emoji=emoji)

        # Обновляем реакции в сообщении
        self._update_message_reactions(message)

        return reaction

    def _update_message_reactions(self, message):
        """Обновляем JSON поле reactions в сообщении"""
        reactions = Reaction.objects.filter(message=message)

        reactions_dict = {}
        for reaction in reactions:
            if reaction.emoji not in reactions_dict:
                reactions_dict[reaction.emoji] = []
            reactions_dict[reaction.emoji].append(reaction.user_id)

        message.reactions = reactions_dict
        message.save(update_fields=["reactions"])


# Attachment Serializer
class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.ImageField(source="file", read_only=True)
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Attachment
        fields = [
            "id",
            "message",
            "type",
            "type_display",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "mime_type",
            "thumbnail",
            "thumbnail_url",
            "width",
            "height",
            "duration",
            "uploaded_at",
        ]
        read_only_fields = ["id", "file_size", "mime_type", "uploaded_at"]


class AttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["message", "type", "file", "file_name", "width", "height", "duration"]

    def validate_file(self, value):
        """Проверяем размер файла"""
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Максимальный размер файла - 10 MB")
        return value

    def validate_message(self, value):
        """Проверяем, что пользователь имеет право добавлять вложения"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if value.sender != request.user:
                raise serializers.ValidationError(
                    "Вы можете добавлять вложения только к своим сообщениям"
                )

            # Проверяем, что чат разрешает отправку медиа
            if value.chat and not value.chat.can_send_media:
                raise serializers.ValidationError(
                    "В этом чате нельзя отправлять медиафайлы"
                )

        return value

    def create(self, validated_data):
        """Создаем вложение с автоматическим определением размера и MIME типа"""
        file = validated_data["file"]
        validated_data["file_size"] = file.size
        validated_data["mime_type"] = file.content_type

        attachment = super().create(validated_data)

        # Если это изображение - создаем миниатюру
        if attachment.type == "image":
            self._create_thumbnail(attachment)

        return attachment

    def _create_thumbnail(self, attachment):
        """Создаем миниатюру для изображения"""
        from PIL import Image
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile

        try:
            img = Image.open(attachment.file)

            # Создаем миниатюру 200x200
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)

            # Сохраняем в BytesIO
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            # Сохраняем как миниатюру
            thumbnail_file = InMemoryUploadedFile(
                buffer,
                None,
                f"{attachment.id}_thumb.jpg",
                "image/jpeg",
                buffer.getbuffer().nbytes,
                None,
            )
            attachment.thumbnail.save(f"{attachment.id}_thumb.jpg", thumbnail_file)
            attachment.save(update_fields=["thumbnail"])
        except Exception as e:
            print(f"Ошибка создания миниатюры: {e}")


# Email Log Serializer
class EmailLogSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    email_type_display = serializers.CharField(
        source="get_email_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EmailLog
        fields = [
            "id",
            "user",
            "email_type",
            "email_type_display",
            "subject",
            "to_email",
            "content",
            "status",
            "status_display",
            "sent_at",
            "error_message",
            "chat_id",
            "message_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EmailLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            "user",
            "email_type",
            "subject",
            "to_email",
            "content",
            "chat_id",
            "message_id",
            "metadata",
        ]

    def create(self, validated_data):
        """Создаем запись лога email"""
        email_log = EmailLog.objects.create(**validated_data)

        # Здесь можно добавить отправку email через Celery
        # send_email_task.delay(email_log.id)

        return email_log


# Chat Folder Serializers
class ChatFolderChatSerializer(serializers.ModelSerializer):
    """Сериализатор для чатов в папке"""

    chat_name = serializers.SerializerMethodField()
    chat_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolderChat
        fields = ["id", "chat_id", "chat_type", "chat_name", "chat_avatar", "added_at"]

    def get_chat_name(self, obj):
        """Получаем имя чата"""
        if obj.chat_type == "group":
            from .models import GroupChat

            chat = GroupChat.objects.filter(id=obj.chat_id).first()
            return chat.name if chat else "Чат"
        else:
            from .models import PrivateChat

            chat = PrivateChat.objects.filter(id=obj.chat_id).first()
            if chat:
                request = self.context.get("request")
                if request and request.user.is_authenticated:
                    other = chat.other_user(request.user)
                    return other.display_name or other.username if other else "Чат"
            return "Чат"

    def get_chat_avatar(self, obj):
        """Получаем аватар чата"""
        if obj.chat_type == "group":
            from .models import GroupChat

            chat = GroupChat.objects.filter(id=obj.chat_id).first()
            if chat and chat.avatar:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(chat.avatar.url)
                return chat.avatar.url
        else:
            from .models import PrivateChat

            chat = PrivateChat.objects.filter(id=obj.chat_id).first()
            if chat:
                request = self.context.get("request")
                if request and request.user.is_authenticated:
                    other = chat.other_user(request.user)
                    if other and other.avatar:
                        if request:
                            return request.build_absolute_uri(other.avatar.url)
                        return other.avatar.url
        return None


class ChatFolderSerializer(serializers.ModelSerializer):
    """Сериализатор для папок чатов"""

    chats = ChatFolderChatSerializer(many=True, read_only=True)
    chats_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolder
        fields = [
            "id",
            "name",
            "icon",
            "color",
            "position",
            "include_private",
            "include_groups",
            "include_archived",
            "include_pinned",
            "is_system",
            "chats",
            "chats_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_chats_count(self, obj):
        return obj.chats.count()


class ChatFolderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания папки"""

    class Meta:
        model = ChatFolder
        fields = [
            "name",
            "icon",
            "color",
            "position",
            "include_private",
            "include_groups",
            "include_archived",
            "include_pinned",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ChatFolderPreviewSerializer(serializers.ModelSerializer):
    """Сериализатор для превью папки (краткий)"""

    chats_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolder
        fields = ["id", "name", "icon", "color", "position", "is_system", "chats_count"]

    def get_chats_count(self, obj):
        return obj.chats.count()


# ==================== FEED SERIALIZERS ====================


class PostMediaSerializer(serializers.ModelSerializer):
    """Сериализатор медиафайлов поста"""

    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "post",
            "media_type",
            "file",
            "file_url",
            "url",
            "thumbnail",
            "thumbnail_url",
            "caption",
            "order",
            "width",
            "height",
            "duration",
            "file_size",
            "mime_type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return obj.url

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None


class PostCommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментариев к посту"""

    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source="parent.id", read_only=True)
    parent_username = serializers.CharField(
        source="parent.author.username", read_only=True
    )
    reply_to = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = [
            "id",
            "post",
            "author",
            "author_username",
            "author_avatar",
            "parent",
            "parent_id",
            "parent_username",
            "content",
            "is_edited",
            "is_deleted",
            "deleted_at",
            "likes_count",
            "dislikes_count",
            "replies_count",
            "path",
            "level",
            "created_at",
            "updated_at",
            "is_liked",
            "is_disliked",
            "reply_to",
            "is_reply",
        ]
        read_only_fields = [
            "id",
            "post",
            "author",
            "created_at",
            "updated_at",
            "is_edited",
        ]

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from .models import PostCommentLike

            return PostCommentLike.objects.filter(
                user=request.user, comment=obj
            ).exists()
        return False

    def get_is_disliked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from .models import PostCommentDislike

            return PostCommentDislike.objects.filter(
                user=request.user, comment=obj
            ).exists()
        return False

    def get_replies_count(self, obj):
        return obj.replies.filter(is_deleted=False).count()

    def get_reply_to(self, obj):
        if obj.parent:
            return {
                "id": obj.parent.id,
                "author_id": obj.parent.author.id,
                "author_username": obj.parent.author.username,
                "author_avatar": obj.parent.author.avatar.url
                if obj.parent.author.avatar
                else None,
                "text": obj.parent.content,
                "created_at": obj.parent.created_at.isoformat(),
            }
        return None

    def get_is_reply(self, obj):
        return obj.parent is not None


class PostCommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания комментария"""

    class Meta:
        model = PostComment
        fields = ["parent", "content"]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Комментарий не может быть пустым")
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Максимальная длина комментария - 2000 символов"
            )
        return value.strip()

    def validate(self, data):
        parent = data.get("parent")

        # Проверяем родительский комментарий (пост будет доступен через perform_create)
        if parent:
            if parent.is_deleted:
                raise serializers.ValidationError(
                    "Нельзя отвечать на удалённый комментарий"
                )

        return data

    def create(self, validated_data):
        author = self.context["request"].user
        parent = validated_data.get("parent")
        post = validated_data.get("post")

        # Строим path и level
        if parent:
            path = f"{parent.path}{parent.id}/"
            level = parent.level + 1
        else:
            path = ""
            level = 0

        comment = PostComment.objects.create(
            author=author,
            post=post,
            parent=parent,
            content=validated_data["content"],
            path=path,
            level=level,
        )

        # Обновляем счётчик комментариев поста
        post.comments_count = PostComment.objects.filter(
            post=post, is_deleted=False
        ).count()
        post.save(update_fields=["comments_count"])

        # Обновляем replies_count родителя
        if parent:
            parent.replies_count = parent.replies.filter(is_deleted=False).count()
            parent.save(update_fields=["replies_count"])

        return comment


class BookmarkSerializer(serializers.ModelSerializer):
    """Сериализатор закладок"""

    post_data = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ["id", "post", "post_data", "folder", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_post_data(self, obj):
        return PostSerializer(obj.post, context=self.context).data


class BookmarkCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания закладки"""

    class Meta:
        model = Bookmark
        fields = ["post", "folder"]


class ReportSerializer(serializers.ModelSerializer):
    """Сериализатор жалоб"""

    reporter_username = serializers.CharField(
        source="reporter.username", read_only=True
    )
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    resolved_by_username = serializers.CharField(
        source="resolved_by.username", read_only=True
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "content_type",
            "content_id",
            "reason",
            "reason_display",
            "comment",
            "status",
            "status_display",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "status",
            "resolved_by",
            "resolved_at",
            "created_at",
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания жалобы"""

    class Meta:
        model = Report
        fields = ["content_type", "content_id", "reason", "comment"]

    def validate_content_type(self, value):
        if value not in ["post", "comment"]:
            raise serializers.ValidationError("Недопустимый тип контента")
        return value

    def validate_reason(self, value):
        valid_reasons = ["spam", "copyright", "harassment", "inappropriate", "other"]
        if value not in valid_reasons:
            raise serializers.ValidationError("Недопустимая причина жалобы")
        return value

    def validate(self, data):
        content_type = data.get("content_type")
        content_id = data.get("content_id")

        # Проверяем, что контент существует
        if content_type == "post":
            from .models import Post

            if not Post.objects.filter(id=content_id).exists():
                raise serializers.ValidationError("Пост не найден")
        elif content_type == "comment":
            from .models import PostComment

            if not PostComment.objects.filter(id=content_id).exists():
                raise serializers.ValidationError("Комментарий не найден")

        # Проверяем, что пользователь ещё не жаловался на этот контент
        reporter = self.context["request"].user
        if Report.objects.filter(
            reporter=reporter,
            content_type=content_type,
            content_id=content_id,
            status="pending",
        ).exists():
            raise serializers.ValidationError("Вы уже отправили жалобу на этот контент")

        return data

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)


class HashtagSerializer(serializers.ModelSerializer):
    """Сериализатор хэштегов"""

    class Meta:
        model = Hashtag
        fields = ["id", "name", "posts_count", "created_at"]
        read_only_fields = ["id", "posts_count", "created_at"]


# Расширенный сериализатор поста для ленты
class FeedPostSerializer(serializers.ModelSerializer):
    """Расширенный сериализатор поста для ленты"""

    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_display_name = serializers.CharField(
        source="author.display_name", read_only=True
    )
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)

    anime = serializers.SerializerMethodField()
    playlist = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    original_post_data = serializers.SerializerMethodField()

    media_files = PostMediaSerializer(many=True, read_only=True)
    attachments_data = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "author_username",
            "author_avatar",
            "author_display_name",
            "author_is_premium",
            "title",
            "post_type",
            "status",
            "visibility",
            "text",
            "content_preview",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "anime",
            "anime_rating",
            "playlist",
            "reactor_post",
            "group",
            "original_post",
            "original_post_data",
            "repost_comment",
            "system_type",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "is_pinned",
            "pinned_at",
            "is_deleted",
            "is_spoiler",
            "allow_comments",
            "edited_at",
            "published_at",
            "created_at",
            "updated_at",
            "media_files",
            "attachments_data",
            "hashtags",
            "is_liked",
            "is_disliked",
            "is_bookmarked",
            "is_following",
            "can_edit",
            "can_delete",
        ]
        read_only_fields = [
            "id",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "is_pinned",
            "pinned_at",
            "edited_at",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_anime(self, obj):
        if obj.anime:
            poster_url = None
            if obj.anime.poster:
                poster_url = obj.anime.poster.url
                request = self.context.get("request")
                if request and poster_url and not poster_url.startswith("http"):
                    poster_url = request.build_absolute_uri(poster_url)
            # Fallback to external CDN URL
            if not poster_url:
                poster_url = obj.anime.poster_url or None
            return {
                "id": obj.anime.id,
                "title_ru": obj.anime.title_ru,
                "title_en": obj.anime.title_en,
                "year": obj.anime.year,
                "description": obj.anime.description,
                "poster_url": poster_url,
                "rating": obj.anime_rating,
            }
        return None

    def get_playlist(self, obj):
        if obj.playlist:
            return {
                "id": obj.playlist.id,
                "title": obj.playlist.title,
                "anime_count": obj.playlist.items_count
                if hasattr(obj.playlist, "items_count")
                else 0,
                "poster_url": obj.playlist.cover_image.url
                if obj.playlist.cover_image
                else None,
            }
        return None

    def get_group(self, obj):
        if obj.group:
            return {
                "id": obj.group.id,
                "name": obj.group.name,
                "slug": obj.group.slug,
                "avatar_url": obj.group.avatar.url if obj.group.avatar else None,
            }
        return None

    def get_original_post_data(self, obj):
        if obj.original_post:
            return FeedPostSerializer(obj.original_post, context=self.context).data
        return None

    def get_hashtags(self, obj):
        return [link.hashtag.name for link in obj.hashtag_links.all()]

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_disliked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PostDislike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Bookmark.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user, following=obj.author
            ).exists()
        return False

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False

    def get_can_delete(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.can_delete(request.user)
        return False

    def get_content_preview(self, obj):
        return obj.get_content_preview(500)

    def get_attachments_data(self, obj):
        attachments = obj.attachments.all() if hasattr(obj, "attachments") else []
        return PostAttachmentSerializer(
            attachments, many=True, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного"""

    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )

    class Meta:
        model = Favorite
        fields = [
            "id",
            "user",
            "content_type",
            "content_type_name",
            "object_id",
            "folder",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]
