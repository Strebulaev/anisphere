# social/urls.py — объединённый файл маршрутов
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from social._discussion_views_patch import get_anime_discussion_group

from .views_feed import FeedViewSet
from .views import (
    CommentListCreateView, CommentDetailView, GroupViewSet, PostCommentViewSet,
    PostViewSet, CombinedChatsView,
    GroupChatViewSet, ChatRoleViewSet, PrivateChatViewSet,
    get_chat_detail,
    FollowViewSet, get_post_likers,
    get_unread_count, get_unread_chats, mark_chat_read, mark_private_chat_read, mark_group_chat_read,
    MessageListCreateView,
)
from .views_all_actions import (
    AchievementViewSet,
    AttachmentViewSet,
    ChatInviteViewSet,
    EmailLogViewSet,
    FavoriteViewSet,
    ReportViewSet,
    RepostViewSet,
    UploadedFileViewSet,
    UserAchievementViewSet,
    get_chats_for_forward, forward_post_to_chat,
    get_extended_feed,
    get_post_comment_replies,
    get_franchise_discussions,
    GroupSearchView,
    get_hashtag_posts, search_hashtags, search_messages, reindex_messages,
    pin_post, unpin_post, report_post, add_bookmark, remove_bookmark, toggle_bookmark_view,
    get_bookmarks_folders, hide_post_from_feed, mark_post_not_interested, edit_post,
    get_user_posts, get_group_posts, hide_author_from_feed, get_hidden_posts, restore_hidden_post,
    get_bookmarked_posts, get_feed_statistics, get_popular_posts,
    get_user_notification_settings, update_user_notification_settings,
    toggle_comment_like, toggle_comment_dislike, get_comment_replies, report_comment, edit_comment,
    toggle_follow, toggle_post_like, toggle_post_dislike, get_post_likes,
    get_post_dislikers, create_repost, delete_repost, repost_post, unrepost_post, track_post_view,
    get_post_viewers, upload_file, get_online_users,
    join_chat_by_invite, toggle_reaction, pin_message, unpin_message, forward_message,
    get_pinned_messages, upload_attachment,
    BookmarkViewSet,
    SubscriptionViewSet,
    NotInterestedViewSet,
    ModerationReportViewSet,
    ReactionViewSet,
)

# Импорты из _discussion_views_patch
try:
    from ._discussion_views_patch import (
        get_anime_discussion_group,
        create_anime_discussion_group,
        join_anime_discussion_group,
        get_franchise_discussion_group,
        join_franchise_discussion_group,
    )
except ImportError:
    # Fallback - определяем функции прямо здесь если файл не существует
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def get_anime_discussion_group(request, anime_id):
        """Получить или создать групповой чат для обсуждения аниме."""
        from .models import GroupChat, ChatMember
        from .serializers import GroupChatSerializer
        try:
            from anime.models import Anime
            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        try:
            chat = GroupChat.objects.get(anime_id=anime_id)
            serializer = GroupChatSerializer(chat, context={'request': request})
            return Response(serializer.data)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def create_anime_discussion_group(request, anime_id):
        """Создать групповой чат для обсуждения аниме"""
        from .models import GroupChat, ChatMember
        from .serializers import GroupChatSerializer
        try:
            from anime.models import Anime
            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({'error': 'Аниме не найдено'}, status=404)

        if GroupChat.objects.filter(anime_id=anime_id).exists():
            return Response({'error': 'Чат для этого аниме уже существует'}, status=400)

        chat = GroupChat.objects.create(
            name=anime.title_ru or anime.title_en,
            anime_id=anime_id,
            created_by=request.user,
            is_public=True,
            description=anime.description[:500] if anime.description else '',
            discussion_type='anime',
            folder_type='discussions',
        )
        ChatMember.objects.get_or_create(user=request.user, chat=chat, defaults={'is_admin': True})
        serializer = GroupChatSerializer(chat, context={'request': request})
        return Response(serializer.data, status=201)

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def join_anime_discussion_group(request, anime_id):
        """Присоединиться к групповому чату аниме или создать его"""
        from .models import GroupChat, ChatMember
        from .serializers import GroupChatSerializer
        try:
            from anime.models import Anime
            anime = Anime.objects.get(id=anime_id)
        except Exception:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        # Пробуем найти существующий чат
        try:
            chat = GroupChat.objects.get(anime_id=anime_id)
        except GroupChat.DoesNotExist:
            # Создаем чат если его нет
            chat = GroupChat.objects.create(
                name=anime.title_ru or anime.title_en,
                anime_id=anime_id,
                created_by=request.user,
                is_public=True,
                description=(anime.description or '')[:500],
                discussion_type='anime',
                folder_type='discussions',
            )
            ChatMember.objects.create(user=request.user, chat=chat, is_admin=True)
        
        # Проверяем участника
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            if chat.members.count() >= chat.max_members:
                return Response({'error': 'Чат переполнен'}, status=400)
            ChatMember.objects.create(user=request.user, chat=chat)
        
        return Response({
            'success': True,
            'chat_id': chat.id,
            'chat': GroupChatSerializer(chat, context={'request': request}).data
        })

    @api_view(['GET', 'POST'])
    @permission_classes([IsAuthenticated])
    def get_franchise_discussion_group(request, franchise_id):
        from .models import GroupChat
        from .serializers import GroupChatSerializer
        try:
            chat = GroupChat.objects.get(franchise_id=franchise_id)
            serializer = GroupChatSerializer(chat, context={'request': request})
            return Response(serializer.data)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def join_franchise_discussion_group(request, franchise_id):
        from .models import GroupChat, ChatMember
        try:
            chat = GroupChat.objects.get(franchise_id=franchise_id)
        except GroupChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
        if ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response({'message': 'Вы уже участник', 'chat_id': chat.id})
        ChatMember.objects.create(user=request.user, chat=chat)
        return Response({'success': True, 'chat_id': chat.id})

# Новые views для системы чатов
from .views_chat import (
    init_franchise_discussion,
    global_chat_style,
    ChatCustomizationViewSet,
    ChatInviteLinkViewSet, join_chat_by_invite as join_invite_new,
    ChatBanViewSet, ChatRestrictionViewSet,
    ChatJoinRequestViewSet,
    ChatTagViewSet,
    AntiSpamRuleViewSet,
    ChatBackupViewSet,
    ScheduledMessageViewSet,
    ChatFolderViewSet, get_folder_chats,
    SecurityLogViewSet,
    get_chat_analytics,
    export_settings, import_settings,
    bulk_delete_messages, bulk_add_members, bulk_remove_members,
    pin_message_new, unpin_message_new, get_pinned_messages_new,
    check_message_spam, clear_chat_history,
    set_member_role, transfer_ownership,
    get_banned_users, get_restricted_users,
    toggle_reaction as toggle_reaction_new,
    private_chat_user_settings,
    mute_private_chat, unmute_private_chat,
    block_user_in_private_chat, unblock_user_in_private_chat,
    group_member_settings, mute_group_chat,
    # Новые эндпойнты
    unmute_group_chat,
    archive_group_chat,
    archive_private_chat,
    get_group_notification_settings,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    from users.serializers import UserSerializer
    data = UserSerializer(request.user, context={'request': request}).data
    data['avatar_url'] = request.user.avatar.url if request.user.avatar else None
    return Response(data)


router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'posts', PostViewSet)
router.register(r'feed', FeedViewSet, basename='feed')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'group-chats', GroupChatViewSet)
router.register(r'group-chats/(?P<chat_pk>\d+)/roles', ChatRoleViewSet, basename='chat-roles')
router.register(r'private-chats', PrivateChatViewSet)
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'reposts', RepostViewSet, basename='repost')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-achievements', UserAchievementViewSet, basename='user-achievement')
router.register(r'uploaded-files', UploadedFileViewSet, basename='uploaded-file')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'chat-invites', ChatInviteViewSet, basename='chat-invite')
router.register(r'reactions', ReactionViewSet, basename='reaction')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'email-logs', EmailLogViewSet, basename='email-log')
router.register(r'chat-folders', ChatFolderViewSet, basename='chat-folder')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'not-interested', NotInterestedViewSet, basename='not-interested')
router.register(r'moderation/reports', ModerationReportViewSet, basename='moderation-report')

# Новые ViewSet'ы
router.register(r'chat-customization', ChatCustomizationViewSet, basename='chat-customization')
router.register(r'chat-invite-links', ChatInviteLinkViewSet, basename='chat-invite-link')
router.register(r'chat-bans', ChatBanViewSet, basename='chat-ban')
router.register(r'chat-restrictions', ChatRestrictionViewSet, basename='chat-restriction')
router.register(r'chat-join-requests', ChatJoinRequestViewSet, basename='chat-join-request')
router.register(r'chat-tags', ChatTagViewSet, basename='chat-tag')
router.register(r'anti-spam-rules', AntiSpamRuleViewSet, basename='anti-spam-rule')
router.register(r'chat-backups', ChatBackupViewSet, basename='chat-backup')
router.register(r'scheduled-messages', ScheduledMessageViewSet, basename='scheduled-message')
router.register(r'security-logs', SecurityLogViewSet, basename='security-log')

# Мини-чат поддержки
from .views_support import SupportTicketViewSet
router.register(r'support', SupportTicketViewSet, basename='support')

urlpatterns = [
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    path('users/me/', get_current_user, name='current-user'),
    path('users/me/feed/', FeedViewSet.as_view({'get': 'list'}), name='user-feed'),

    # ==================== ЛЕНТА ====================
    path('feed/trending/', FeedViewSet.as_view({'get': 'trending'}), name='feed-trending'),
    path('feed/followers/', FeedViewSet.as_view({'get': 'followers'}), name='feed-followers'),
    path('feed/weighted/', FeedViewSet.as_view({'get': 'weighted'}), name='feed-weighted'),
    path('feed/hot/', FeedViewSet.as_view({'get': 'hot'}), name='feed-hot'),
    path('feed/top/', FeedViewSet.as_view({'get': 'top'}), name='feed-top'),
    path('feed/extended/', get_extended_feed, name='feed-extended'),
    path('feed/', get_extended_feed, name='feed'),

    # ==================== ЧАТЫ ====================
    path('chats/', CombinedChatsView.as_view(), name='combined-chats'),
    # Алиас для создания чата - ДО маршрута с параметрами!
    path('chats/private/', PrivateChatViewSet.as_view({'post': 'create'}), name='create-private-chat'),
    path('chats/<int:pk>/', get_chat_detail, name='chat-detail'),
    path('chats/<int:pk>/settings/', get_chat_detail, name='chat-settings'),
    # Сообщения (фронтенд использует /api/social/messages/)
    path('chats/<int:chat_id>/messages/', MessageListCreateView.as_view(), name='chat-messages'),
    path('messages/', MessageListCreateView.as_view(), name='messages-list-create'),

    # ==================== НАСТРОЙКИ ЛИЧНОГО ЧАТА ====================
    path('private-chats/<int:chat_id>/settings/', private_chat_user_settings, name='private-chat-settings'),
    path('private-chats/<int:chat_id>/user-settings/', private_chat_user_settings, name='private-chat-user-settings'),
    path('private-chats/<int:chat_id>/mute/', mute_private_chat, name='mute-private-chat'),
    path('private-chats/<int:chat_id>/unmute/', unmute_private_chat, name='unmute-private-chat'),
    path('private-chats/<int:chat_id>/block/', block_user_in_private_chat, name='block-private-chat'),
    path('private-chats/<int:chat_id>/unblock/', unblock_user_in_private_chat, name='unblock-private-chat'),
    path('private-chats/<int:chat_id>/mark_as_read/', mark_private_chat_read, name='mark-private-chat-read'),

    # ==================== НАСТРОЙКИ ГРУППОВОГО ЧАТА ====================
    path('group-chats/<int:chat_id>/settings/', group_member_settings, name='group-chat-settings'),
    path('group-chats/<int:chat_id>/member-settings/', group_member_settings, name='group-member-settings'),
    path('group-chats/<int:chat_id>/mute/', mute_group_chat, name='mute-group-chat'),
    path('group-chats/<int:chat_id>/unmute/', unmute_group_chat, name='unmute-group-chat'),
    path('group-chats/<int:chat_id>/notification-settings/', get_group_notification_settings, name='group-notification-settings'),
    path('group-chats/<int:chat_id>/archive/', archive_group_chat, name='archive-group-chat'),
    path('group-chats/<int:chat_id>/mark_as_read/', mark_group_chat_read, name='mark-group-chat-read'),
    path('private-chats/<int:chat_id>/archive/', archive_private_chat, name='archive-private-chat'),

    # ==================== КАСТОМИЗАЦИЯ ЧАТОВ (ОБОИ + ТЕМЫ) ====================
    # Обои — группа
    path('chat-settings/group/<int:chat_id>/wallpaper/',
         ChatCustomizationViewSet.as_view({'get': 'get_wallpaper'}),
         {'chat_type': 'group'}, name='group-wallpaper'),
    path('chat-settings/group/<int:chat_id>/wallpaper/set/',
         ChatCustomizationViewSet.as_view({'put': 'set_wallpaper', 'post': 'set_wallpaper'}),
         {'chat_type': 'group'}, name='set-group-wallpaper'),
    path('chat-settings/group/<int:chat_id>/wallpaper/reset/',
         ChatCustomizationViewSet.as_view({'delete': 'reset_wallpaper'}),
         {'chat_type': 'group'}, name='reset-group-wallpaper'),
    path('chat-settings/group/<int:chat_id>/wallpaper/preset/',
         ChatCustomizationViewSet.as_view({'post': 'apply_wallpaper_preset'}),
         {'chat_type': 'group'}, name='group-wallpaper-preset'),

    # Обои — личный чат
    path('chat-settings/private/<int:chat_id>/wallpaper/',
         ChatCustomizationViewSet.as_view({'get': 'get_wallpaper'}),
         {'chat_type': 'private'}, name='private-wallpaper'),
    path('chat-settings/private/<int:chat_id>/wallpaper/set/',
         ChatCustomizationViewSet.as_view({'put': 'set_wallpaper', 'post': 'set_wallpaper'}),
         {'chat_type': 'private'}, name='set-private-wallpaper'),
    path('chat-settings/private/<int:chat_id>/wallpaper/reset/',
         ChatCustomizationViewSet.as_view({'delete': 'reset_wallpaper'}),
         {'chat_type': 'private'}, name='reset-private-wallpaper'),
    path('chat-settings/private/<int:chat_id>/wallpaper/preset/',
         ChatCustomizationViewSet.as_view({'post': 'apply_wallpaper_preset'}),
         {'chat_type': 'private'}, name='private-wallpaper-preset'),

    # Тема — группа
    path('chat-settings/group/<int:chat_id>/theme/',
         ChatCustomizationViewSet.as_view({'get': 'get_theme'}),
         {'chat_type': 'group'}, name='group-theme'),
    path('chat-settings/group/<int:chat_id>/theme/set/',
         ChatCustomizationViewSet.as_view({'put': 'set_theme', 'post': 'set_theme'}),
         {'chat_type': 'group'}, name='set-group-theme'),
    path('chat-settings/group/<int:chat_id>/theme/preset/',
         ChatCustomizationViewSet.as_view({'post': 'apply_theme_preset'}),
         {'chat_type': 'group'}, name='group-theme-preset'),
    path('chat-settings/group/<int:chat_id>/theme/reset/',
         ChatCustomizationViewSet.as_view({'delete': 'reset_theme'}),
         {'chat_type': 'group'}, name='reset-group-theme'),

    # Тема — личный чат
    path('chat-settings/private/<int:chat_id>/theme/',
         ChatCustomizationViewSet.as_view({'get': 'get_theme'}),
         {'chat_type': 'private'}, name='private-theme'),
    path('chat-settings/private/<int:chat_id>/theme/set/',
         ChatCustomizationViewSet.as_view({'put': 'set_theme', 'post': 'set_theme'}),
         {'chat_type': 'private'}, name='set-private-theme'),
    path('chat-settings/private/<int:chat_id>/theme/preset/',
         ChatCustomizationViewSet.as_view({'post': 'apply_theme_preset'}),
         {'chat_type': 'private'}, name='private-theme-preset'),
    path('chat-settings/private/<int:chat_id>/theme/reset/',
         ChatCustomizationViewSet.as_view({'delete': 'reset_theme'}),
         {'chat_type': 'private'}, name='reset-private-theme'),

    # Все настройки сразу
    path('chat-settings/group/<int:chat_id>/all/',
         ChatCustomizationViewSet.as_view({'get': 'get_all_settings'}),
         {'chat_type': 'group'}, name='group-all-settings'),
    path('chat-settings/private/<int:chat_id>/all/',
         ChatCustomizationViewSet.as_view({'get': 'get_all_settings'}),
         {'chat_type': 'private'}, name='private-all-settings'),

    # Bulk update
    path('chat-settings/group/<int:chat_id>/bulk-update/',
         ChatCustomizationViewSet.as_view({'post': 'bulk_update_settings'}),
         {'chat_type': 'group'}, name='group-bulk-settings'),
    path('chat-settings/private/<int:chat_id>/bulk-update/',
         ChatCustomizationViewSet.as_view({'post': 'bulk_update_settings'}),
         {'chat_type': 'private'}, name='private-bulk-settings'),

    # CSS переменные
    path('chat-settings/group/<int:chat_id>/css-vars/',
         ChatCustomizationViewSet.as_view({'get': 'get_css_vars'}),
         {'chat_type': 'group'}, name='group-css-vars'),
    path('chat-settings/private/<int:chat_id>/css-vars/',
         ChatCustomizationViewSet.as_view({'get': 'get_css_vars'}),
         {'chat_type': 'private'}, name='private-css-vars'),

    # Пресеты обоев и тем
    path('chat-settings/wallpapers/presets/', ChatCustomizationViewSet.as_view({'get': 'wallpaper_presets'}), name='wallpaper-presets'),
    path('chat-settings/themes/presets/', ChatCustomizationViewSet.as_view({'get': 'theme_presets'}), name='theme-presets'),

    # ==================== КОММЕНТАРИИ ====================
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('posts/<int:post_pk>/comments/', PostCommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='post-comments'),
    path('posts/<int:post_pk>/comments/<int:pk>/', PostCommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='post-comment-detail'),
    path('comments/<int:comment_id>/like/', toggle_comment_like, name='toggle-comment-like'),
    path('comments/<int:comment_id>/dislike/', toggle_comment_dislike, name='toggle-comment-dislike'),
    path('comments/<int:comment_id>/replies/', get_comment_replies, name='get-comment-replies'),
    path('comments/<int:comment_id>/report/', report_comment, name='report-comment'),
    path('comments/<int:comment_id>/edit/', edit_comment, name='edit-comment'),

    # ==================== POST COMMENT REPLIES ====================
    path('posts/comments/<int:comment_id>/replies/', get_post_comment_replies, name='get-post-comment-replies'),

    # ==================== ПОДПИСКИ ====================
    path('follow/toggle/<int:user_id>/', toggle_follow, name='toggle-follow'),
    path('subscriptions/toggle/<int:user_id>/', toggle_follow, name='toggle-subscription'),

    # ==================== ЛАЙКИ ====================
    path('posts/<int:post_id>/like/', toggle_post_like, name='toggle-post-like'),
    path('posts/<int:post_id>/dislike/', toggle_post_dislike, name='toggle-post-dislike'),
    path('posts/<int:post_id>/likes/', get_post_likes, name='get-post-likes'),
    path('posts/<int:post_id>/likers/', get_post_likers, name='get-post-likers'),
    path('posts/<int:post_id>/dislikers/', get_post_dislikers, name='get-post-dislikers'),

    # ==================== РЕПОСТЫ ====================
    path('posts/<int:post_id>/repost/', create_repost, name='create-repost'),
    path('posts/<int:post_id>/repost/delete/', delete_repost, name='delete-repost'),
    path('posts/<int:post_id>/repost/action/', repost_post, name='repost-post'),
    path('posts/<int:post_id>/repost/remove/', unrepost_post, name='unrepost-post'),

    # ==================== ПРОСМОТРЫ ====================
    path('posts/<int:post_id>/view/', track_post_view, name='track-post-view'),
    path('posts/<int:post_id>/viewers/', get_post_viewers, name='get-post-viewers'),

    # ==================== ФАЙЛЫ ====================
    path('files/upload/', upload_file, name='upload-file'),

    # ==================== ОНЛАЙН ====================
    path('users/online/', get_online_users, name='get-online-users'),

    # ==================== ПОИСК ====================
    path('groups/search/', GroupSearchView.as_view({'get': 'list'}), name='group-search'),
    path('hashtags/<str:tag_name>/', get_hashtag_posts, name='get-hashtag-posts'),
    path('hashtags/search/', search_hashtags, name='search-hashtags'),
    path('messages/search/', search_messages, name='search-messages'),
    path('messages/reindex/', reindex_messages, name='reindex-messages'),

    # ==================== ПРИГЛАШЕНИЯ ====================
    path('chat-invites/join/<str:token>/', join_chat_by_invite, name='join-chat-by-invite'),
    path('invite-links/join/<str:token>/', join_invite_new, name='join-chat-by-invite-new'),
    path('group-chats/<int:chat_id>/invite-links/',
         ChatInviteLinkViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='chat-invite-links'),

    # ==================== РЕАКЦИИ ====================
    path('messages/<int:message_id>/reaction/toggle/', toggle_reaction, name='toggle-reaction'),
    path('messages/<int:message_id>/reaction/new/', toggle_reaction_new, name='toggle-reaction-new'),
    path('messages/<int:message_id>/reactions/', ReactionViewSet.as_view({'get': 'for_message'}), name='message-reactions'),

    # ==================== АТТАЧМЕНТЫ ====================
    path('messages/<int:message_id>/attachments/upload/', upload_attachment, name='upload-attachment'),

    # ==================== ЗАКРЕПЛЕНИЕ СООБЩЕНИЙ ====================
    path('messages/<int:message_id>/pin/', pin_message, name='pin-message'),
    path('messages/<int:message_id>/unpin/', unpin_message, name='unpin-message'),
    path('messages/<int:message_id>/forward/', forward_message, name='forward-message'),
    path('chats/<int:chat_id>/pinned-messages/', get_pinned_messages, name='get-pinned-messages'),
    path('messages/<int:message_id>/pin-v2/', pin_message_new, name='pin-message-v2'),
    path('messages/<int:message_id>/unpin-v2/', unpin_message_new, name='unpin-message-v2'),
    path('chats/<int:chat_id>/pinned-messages-v2/', get_pinned_messages_new, name='get-pinned-messages-v2'),

    # ==================== НЕПРОЧИТАННЫЕ ====================
    path('chats/unread-count/', get_unread_count, name='get-unread-count'),
    path('chats/unread/', get_unread_chats, name='get-unread-chats'),
    path('chats/<int:chat_id>/mark-read/', mark_chat_read, name='mark-chat-read'),

    # ==================== ПОСТЫ ====================
    # Публичный просмотр поста (без аутентификации)
    path('posts/<int:post_id>/public/', PostViewSet.as_view({'get': 'public_retrieve'}), name='post-detail-public'),
    path('posts/<int:post_id>/', PostViewSet.as_view({'get': 'retrieve'}), name='post-detail'),
    path('posts/<int:post_id>/pin/', pin_post, name='pin-post'),
    path('posts/<int:post_id>/unpin/', unpin_post, name='unpin-post'),
    path('posts/<int:post_id>/report/', report_post, name='report-post'),
    path('posts/<int:post_id>/bookmark/', add_bookmark, name='add-bookmark'),
    path('posts/<int:post_id>/bookmark/remove/', remove_bookmark, name='remove-bookmark'),
    path('bookmarks/toggle/', toggle_bookmark_view, name='toggle-bookmark'),
    path('bookmarks/folders/', get_bookmarks_folders, name='bookmarks-folders'),
    path('posts/<int:post_id>/hide/', hide_post_from_feed, name='hide-post'),
    path('posts/<int:post_id>/not-interested/', mark_post_not_interested, name='not-interested'),
    path('posts/<int:post_id>/edit/', edit_post, name='edit-post'),
    path('users/<int:user_id>/posts/', get_user_posts, name='user-posts'),
    path('groups/<int:group_id>/posts/', get_group_posts, name='group-posts'),
    path('users/<int:user_id>/hide/', hide_author_from_feed, name='hide-author'),
    path('hidden-posts/', get_hidden_posts, name='hidden-posts'),
    path('hidden-posts/<int:post_id>/restore/', restore_hidden_post, name='restore-hidden-post'),
    path('bookmarks/posts/', get_bookmarked_posts, name='bookmarked-posts'),
    path('feed/statistics/', get_feed_statistics, name='feed-statistics'),
    path('feed/popular/', get_popular_posts, name='popular-posts'),

    # ==================== УВЕДОМЛЕНИЯ ====================
    path('notifications/settings/', get_user_notification_settings, name='notification-settings'),
    path('notifications/settings/update/', update_user_notification_settings, name='update-notification-settings'),
    path('not-interested/user/<int:user_id>/', mark_post_not_interested, name='not-interested-user'),

    # ==================== РОЛИ ====================
    path('group-chats/<int:chat_id>/members/<int:user_id>/role/', set_member_role, name='set-member-role'),
    path('group-chats/<int:chat_id>/transfer-ownership/', transfer_ownership, name='transfer-ownership'),

    # ==================== МОДЕРАЦИЯ ====================
    path('group-chats/<int:chat_id>/banned-users/', get_banned_users, name='get-banned-users'),
    path('group-chats/<int:chat_id>/restricted-users/', get_restricted_users, name='get-restricted-users'),
    path('group-chats/<int:chat_id>/join-requests/',
         ChatJoinRequestViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='chat-join-requests'),
    path('group-chats/<int:chat_id>/join-requests/<int:pk>/approve/',
         ChatJoinRequestViewSet.as_view({'post': 'approve'}),
         name='approve-join-request'),
    path('group-chats/<int:chat_id>/join-requests/<int:pk>/reject/',
         ChatJoinRequestViewSet.as_view({'post': 'reject'}),
         name='reject-join-request'),

    # ==================== АНТИ-СПАМ ====================
    path('group-chats/<int:chat_id>/anti-spam-rules/',
         AntiSpamRuleViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='anti-spam-rules'),
    path('group-chats/<int:chat_id>/check-spam/', check_message_spam, name='check-message-spam'),

    # ==================== РЕЗЕРВНЫЕ КОПИИ ====================
    path('group-chats/<int:chat_id>/backups/',
         ChatBackupViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='chat-backups'),

    # ==================== ПАПКИ ЧАТОВ ====================
    path('chat-folders/<int:folder_id>/chats/', get_folder_chats, name='folder-chats'),
    path('chat-folders/reorder/', ChatFolderViewSet.as_view({'post': 'reorder'}), name='reorder-folders'),
    path('chat-folders/<int:pk>/add-chat/', ChatFolderViewSet.as_view({'post': 'add_chat'}), name='add-chat-to-folder'),
    path('chat-folders/<int:pk>/remove-chat/', ChatFolderViewSet.as_view({'post': 'remove_chat'}), name='remove-chat-from-folder'),

    # ==================== АНАЛИТИКА ====================
    path('group-chats/<int:chat_id>/analytics/', get_chat_analytics, name='chat-analytics'),

    # ==================== ЭКСПОРТ/ИМПОРТ ====================
    path('settings/export/', export_settings, name='export-settings'),
    path('settings/import/', import_settings, name='import-settings'),

    # ==================== МАССОВЫЕ ОПЕРАЦИИ ====================
    path('group-chats/<int:chat_id>/messages/bulk-delete/', bulk_delete_messages, name='bulk-delete-messages'),
    path('group-chats/<int:chat_id>/members/bulk-add/', bulk_add_members, name='bulk-add-members'),
    path('group-chats/<int:chat_id>/members/bulk-remove/', bulk_remove_members, name='bulk-remove-members'),

    # ==================== ОЧИСТКА ИСТОРИИ ====================
    path('chats/<int:chat_id>/clear-history/', clear_chat_history, name='clear-chat-history'),

    # ==================== ПЕРЕСЫЛКА ====================
    path('chats/for-forward/', get_chats_for_forward, name='chats-for-forward'),
    path('chats/<int:chat_id>/forward/', forward_post_to_chat, name='forward-post'),
    path('chats/forward/', forward_post_to_chat, name='forward-post-no-id'),

      # ==================== АНИМЕ ОБСУЖДЕНИЯ ====================
      path('anime/<int:anime_id>/discussion-group/', get_anime_discussion_group, name='anime-discussion-group'),
      path('anime/<int:anime_id>/discussion-group/create/', create_anime_discussion_group, name='anime-discussion-group-create'),
      path('anime/<int:anime_id>/discussion-group/join/', join_anime_discussion_group, name='anime-discussion-group-join'),
      
      # ==================== FRANCHISE DISCUSSION ====================
      path('franchise/<int:franchise_id>/discussion/', get_franchise_discussion_group, name='franchise-discussion'),
      path('franchise/<int:franchise_id>/discussion/join/', join_franchise_discussion_group, name='franchise-discussion-join'),
    path('franchise-discussion/init/', init_franchise_discussion, name='franchise-discussion-init'),
    path('franchise-discussion/list/', get_franchise_discussions, name='franchise-discussion-list'),

    # ==================== GLOBAL CHAT STYLE ====================
    path('chat-settings/global/', global_chat_style, name='global-chat-style'),

] + router.urls
