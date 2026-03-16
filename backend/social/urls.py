# social/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .views_feed import FeedViewSet
from .views import (
    CommentListCreateView, CommentDetailView, GroupViewSet, PostCommentViewSet,
    PostViewSet, CombinedChatsView,
    GroupChatViewSet, ChatRoleViewSet, PrivateChatViewSet,
    get_chat_detail,
    PrivateChatSettingsView, GroupChatSettingsView,
    FollowViewSet, get_post_likers,
    get_anime_discussion_group, create_anime_discussion_group, join_anime_discussion_group,
    get_unread_count, get_unread_chats, mark_chat_read, mark_private_chat_read, mark_group_chat_read,
)
from .views_all_actions import (
    BookmarkViewSet,
    PostMediaViewSet,
    PostAttachmentViewSet,
    ReportViewSet,
    SubscriptionViewSet,
    NotInterestedViewSet,
    ModerationReportViewSet,
    toggle_follow,
    toggle_post_like, toggle_post_dislike, get_post_likes, get_post_dislikers,
    toggle_comment_like, toggle_comment_dislike,
    pin_post, unpin_post, report_post, add_bookmark, remove_bookmark, toggle_bookmark_view,
    get_bookmarks_folders, repost_post, unrepost_post, create_repost, delete_repost,
    track_post_view, get_post_viewers,
    get_comment_replies, report_comment,
    edit_post, edit_comment,
    hide_post_from_feed, mark_post_not_interested, hide_author_from_feed,
    get_hidden_posts, restore_hidden_post,
    get_feed_statistics, get_popular_posts, get_user_posts, get_group_posts,
    get_hashtag_posts, search_hashtags,
    get_user_notification_settings, update_user_notification_settings,
    AchievementViewSet, UserAchievementViewSet,
    UploadedFileViewSet, upload_file,
    FavoriteViewSet,
    get_online_users, GroupSearchView,
    ChatInviteViewSet, join_chat_by_invite,
    ReactionViewSet, toggle_reaction,
    AttachmentViewSet, upload_attachment,
    pin_message, unpin_message, forward_message, get_pinned_messages,
    EmailLogViewSet,
    search_messages, reindex_messages,
    ChatFolderViewSet, get_folder_chats,
    RepostViewSet,
    get_chats_for_forward, forward_post_to_chat,
    get_extended_feed,
)
# Новые views для системы чатов
from .views_chat import (
    ChatInviteLinkViewSet, join_chat_by_invite as join_chat_by_invite_new,
    ChatWallpaperViewSet, set_chat_wallpaper,
    ChatThemeViewSet,
    MessageReactionViewSet, toggle_reaction as toggle_reaction_new,
    ChatBanViewSet, ChatRestrictionViewSet,
    ChatSlowModeViewSet,
    ChatJoinRequestViewSet,
    ChatTagViewSet, ChatTagAssignmentViewSet,
    AntiSpamRuleViewSet,
    ChatBackupViewSet,
    ScheduledMessageViewSet,
    set_member_role, transfer_ownership,
    get_banned_users, get_restricted_users,
    ChatFolderViewSet, get_folder_chats,
    SecurityLogViewSet,
    get_chat_analytics,
    export_settings, import_settings,
    bulk_delete_messages, bulk_add_members, bulk_remove_members,
    pin_message_new, unpin_message_new, get_pinned_messages_new,
    check_message_spam,
    clear_chat_history,
)


# Endpoint для получения текущего пользователя
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Получить информацию о текущем пользователе"""
    from users.serializers import UserSerializer
    # Добавляем avatar_url
    data = UserSerializer(request.user, context={'request': request}).data
    data['avatar_url'] = request.user.avatar.url if request.user.avatar else None
    return Response(data)

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'posts', PostViewSet)
router.register(r'feed', FeedViewSet, basename='feed')
router.register(r'post-media', PostMediaViewSet, basename='post-media')
router.register(r'post-attachments', PostAttachmentViewSet, basename='post-attachment')
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

# Новые ViewSet'ы для системы чатов
router.register(r'chat-invite-links', ChatInviteLinkViewSet, basename='chat-invite-link')
router.register(r'chat-wallpapers', ChatWallpaperViewSet, basename='chat-wallpaper')
router.register(r'chat-themes', ChatThemeViewSet, basename='chat-theme')
router.register(r'message-reactions', MessageReactionViewSet, basename='message-reaction')
router.register(r'chat-bans', ChatBanViewSet, basename='chat-ban')
router.register(r'chat-restrictions', ChatRestrictionViewSet, basename='chat-restriction')
router.register(r'chat-slow-modes', ChatSlowModeViewSet, basename='chat-slow-mode')
router.register(r'chat-join-requests', ChatJoinRequestViewSet, basename='chat-join-request')
router.register(r'chat-tags', ChatTagViewSet, basename='chat-tag')
router.register(r'chat-tag-assignments', ChatTagAssignmentViewSet, basename='chat-tag-assignment')
router.register(r'anti-spam-rules', AntiSpamRuleViewSet, basename='anti-spam-rule')
router.register(r'chat-backups', ChatBackupViewSet, basename='chat-backup')
router.register(r'scheduled-messages', ScheduledMessageViewSet, basename='scheduled-message')

urlpatterns = [
    # ВАЖНО: эти маршруты должны быть ПЕРЕД router.urls
    # Users - текущий пользователь
    path('users/me/', get_current_user, name='current-user'),
    path('users/me/feed/', FeedViewSet.as_view({'get': 'list'}), name='user-feed'),
    
    # Feed - основная лента (дополнительные endpoints)
    path('feed/trending/', FeedViewSet.as_view({'get': 'trending'}), name='feed-trending'),
    path('feed/followers/', FeedViewSet.as_view({'get': 'followers'}), name='feed-followers'),
    path('feed/weighted/', FeedViewSet.as_view({'get': 'weighted'}), name='feed-weighted'),
    path('feed/hot/', FeedViewSet.as_view({'get': 'hot'}), name='feed-hot'),
    path('feed/top/', FeedViewSet.as_view({'get': 'top'}), name='feed-top'),
    
    # Chats
    path('chats/', CombinedChatsView.as_view(), name='combined-chats'),
    path('chats/<int:pk>/', get_chat_detail, name='chat-detail'),
    path('chats/<int:pk>/settings/', get_chat_detail, name='chat-settings'),
    path('private-chats/<int:chat_id>/settings/', PrivateChatSettingsView.as_view(), name='private-chat-settings'),
    path('group-chats/<int:chat_id>/settings/', GroupChatSettingsView.as_view(), name='group-chat-settings'),

    # Comments
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # Post Comments
    path('posts/<int:post_pk>/comments/', PostCommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='post-comments'),
    path('posts/<int:post_pk>/comments/<int:pk>/', PostCommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='post-comment-detail'),
    path('comments/<int:comment_id>/like/', toggle_comment_like, name='toggle-comment-like'),

    # Follow system
    path('follow/toggle/<int:user_id>/', toggle_follow, name='toggle-follow'),

    # Like/Dislike system
    path('posts/<int:post_id>/like/', toggle_post_like, name='toggle-post-like'),
    path('posts/<int:post_id>/dislike/', toggle_post_dislike, name='toggle-post-dislike'),
    path('posts/<int:post_id>/likes/', get_post_likes, name='get-post-likes'),

    # Repost system
    path('posts/<int:post_id>/repost/', create_repost, name='create-repost'),
    path('posts/<int:post_id>/repost/delete/', delete_repost, name='delete-repost'),

    # Post Views
    path('posts/<int:post_id>/view/', track_post_view, name='track-post-view'),
    path('posts/<int:post_id>/viewers/', get_post_viewers, name='get-post-viewers'),

    # Files
    path('files/upload/', upload_file, name='upload-file'),

    # Online users
    path('users/online/', get_online_users, name='get-online-users'),

    # Search
    path('groups/search/', GroupSearchView.as_view({'get': 'list'}), name='group-search'),

    # Hashtags
    path('hashtags/<str:tag_name>/', get_hashtag_posts, name='get-hashtag-posts'),
    path('hashtags/search/', search_hashtags, name='search-hashtags'),

    # Chat Invites
    path('chat-invites/join/<str:token>/', join_chat_by_invite, name='join-chat-by-invite'),

    # Reactions
    path('messages/<int:message_id>/reaction/toggle/', toggle_reaction, name='toggle-reaction'),
    path('messages/<int:message_id>/reactions/', ReactionViewSet.as_view({'get': 'for_message'}), name='message-reactions'),

    # Attachments
    path('messages/<int:message_id>/attachments/upload/', upload_attachment, name='upload-attachment'),

    # Message Actions
    path('messages/<int:message_id>/pin/', pin_message, name='pin-message'),
    path('messages/<int:message_id>/unpin/', unpin_message, name='unpin-message'),
    path('messages/<int:message_id>/forward/', forward_message, name='forward-message'),
    path('chats/<int:chat_id>/pinned-messages/', get_pinned_messages, name='get-pinned-messages'),

    # Unread Messages
    path('chats/unread-count/', get_unread_count, name='get-unread-count'),
    path('chats/unread/', get_unread_chats, name='get-unread-chats'),
    path('chats/<int:chat_id>/mark-read/', mark_chat_read, name='mark-chat-read'),
    path('private-chats/<int:chat_id>/mark_as_read/', mark_private_chat_read, name='mark-private-chat-read'),
    path('group-chats/<int:chat_id>/mark_as_read/', mark_group_chat_read, name='mark-group-chat-read'),

    # Search
    path('messages/search/', search_messages, name='search-messages'),
    path('messages/reindex/', reindex_messages, name='reindex-messages'),

    # Chat Folders
    path('chat-folders/<int:folder_id>/chats/', get_folder_chats, name='folder-chats'),

    # Post Actions
    path('posts/<int:post_id>/pin/', pin_post, name='pin-post'),
    path('posts/<int:post_id>/unpin/', unpin_post, name='unpin-post'),
    path('posts/<int:post_id>/report/', report_post, name='report-post'),
    path('posts/<int:post_id>/bookmark/', add_bookmark, name='add-bookmark'),
    path('posts/<int:post_id>/bookmark/remove/', remove_bookmark, name='remove-bookmark'),
    path('bookmarks/toggle/', toggle_bookmark_view, name='toggle-bookmark'),
    path('bookmarks/folders/', get_bookmarks_folders, name='bookmarks-folders'),
    path('posts/<int:post_id>/likers/', get_post_likers, name='get-post-likers'),
    path('posts/<int:post_id>/dislikers/', get_post_dislikers, name='get-post-dislikers'),
    path('posts/<int:post_id>/repost/action/', repost_post, name='repost-post'),
    path('posts/<int:post_id>/repost/remove/', unrepost_post, name='unrepost-post'),

    # Comment Actions
    path('comments/<int:comment_id>/replies/', get_comment_replies, name='get-comment-replies'),
    path('comments/<int:comment_id>/dislike/', toggle_comment_dislike, name='toggle-comment-dislike'),
    path('comments/<int:comment_id>/report/', report_comment, name='report-comment'),

    # Feed Statistics
    path('feed/statistics/', get_feed_statistics, name='feed-statistics'),
    path('feed/popular/', get_popular_posts, name='popular-posts'),
    path('users/<int:user_id>/posts/', get_user_posts, name='user-posts'),
    path('groups/<int:group_id>/posts/', get_group_posts, name='group-posts'),

    # Content Moderation
    path('posts/<int:post_id>/hide/', hide_post_from_feed, name='hide-post'),
    path('posts/<int:post_id>/not-interested/', mark_post_not_interested, name='not-interested'),

    # Post Editing
    path('posts/<int:post_id>/edit/', edit_post, name='edit-post'),
    path('comments/<int:comment_id>/edit/', edit_comment, name='edit-comment'),

    # Notification Settings
    path('notifications/settings/', get_user_notification_settings, name='notification-settings'),
    path('notifications/settings/update/', update_user_notification_settings, name='update-notification-settings'),

    # Subscriptions (подписки)
    path('subscriptions/toggle/<int:user_id>/', toggle_follow, name='toggle-subscription'),

    # Not Interested (скрытые профили)
    path('not-interested/user/<int:user_id>/', mark_post_not_interested, name='not-interested-user'),
    path('users/<int:user_id>/hide/', hide_author_from_feed, name='hide-author'),

    # Hidden posts
    path('hidden-posts/', get_hidden_posts, name='hidden-posts'),
    path('hidden-posts/<int:post_id>/restore/', restore_hidden_post, name='restore-hidden-post'),

    # Extended Feed
    path('feed/extended/', get_extended_feed, name='feed-extended'),
    path('feed/', get_extended_feed, name='feed'),

    # Forward Post (пересылка)
    path('chats/for-forward/', get_chats_for_forward, name='chats-for-forward'),
    path('chats/<int:chat_id>/forward/', forward_post_to_chat, name='forward-post'),

    # Extended Feed
    path('feed/extended/', get_extended_feed, name='feed-extended'),
    path('feed/', get_extended_feed, name='feed'),

    # Anime Discussion Groups
    path('anime/<int:anime_id>/discussion-group/', get_anime_discussion_group, name='anime-discussion-group'),
    path('anime/<int:anime_id>/discussion-group/create/', create_anime_discussion_group, name='anime-discussion-group-create'),
    path('anime/<int:anime_id>/discussion-group/join/', join_anime_discussion_group, name='anime-discussion-group-join'),
    
    # ==================== НОВЫЕ МАРШРУТЫ ДЛЯ СИСТЕМЫ ЧАТОВ ====================
    
    # Ссылки-приглашения
    path('invite-links/join/<str:token>/', join_chat_by_invite_new, name='join-chat-by-invite-new'),
    path('group-chats/<int:chat_id>/invite-links/', ChatInviteLinkViewSet.as_view({'get': 'list', 'post': 'create'}), name='chat-invite-links'),
    
    # Обои чатов
    path('chats/<int:chat_id>/wallpaper/', set_chat_wallpaper, name='set-chat-wallpaper'),
    path('wallpapers/presets/', ChatWallpaperViewSet.as_view({'get': 'presets'}), name='wallpaper-presets'),
    
    # Роли и модерация
    path('group-chats/<int:chat_id>/members/<int:user_id>/role/', set_member_role, name='set-member-role'),
    path('group-chats/<int:chat_id>/transfer-ownership/', transfer_ownership, name='transfer-ownership'),
    path('group-chats/<int:chat_id>/banned-users/', get_banned_users, name='get-banned-users'),
    path('group-chats/<int:chat_id>/restricted-users/', get_restricted_users, name='get-restricted-users'),
    
    # Запросы на вступление
    path('group-chats/<int:chat_id>/join-requests/', ChatJoinRequestViewSet.as_view({'get': 'list', 'post': 'create'}), name='chat-join-requests'),
    path('group-chats/<int:chat_id>/join-requests/<int:pk>/approve/', ChatJoinRequestViewSet.as_view({'post': 'approve'}), name='approve-join-request'),
    path('group-chats/<int:chat_id>/join-requests/<int:pk>/reject/', ChatJoinRequestViewSet.as_view({'post': 'reject'}), name='reject-join-request'),
    
    # Анти-спам
    path('group-chats/<int:chat_id>/anti-spam-rules/', AntiSpamRuleViewSet.as_view({'get': 'list', 'post': 'create'}), name='anti-spam-rules'),
    
    # Резервные копии
    path('group-chats/<int:chat_id>/backups/', ChatBackupViewSet.as_view({'get': 'list', 'post': 'create'}), name='chat-backups'),
    path('group-chats/<int:chat_id>/backups/<int:pk>/restore/', ChatBackupViewSet.as_view({'post': 'restore'}), name='restore-backup'),
    
    # Запланированные сообщения
    path('chats/<int:chat_id>/scheduled-messages/', ScheduledMessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='scheduled-messages'),
    path('scheduled-messages/<int:pk>/cancel/', ScheduledMessageViewSet.as_view({'post': 'cancel'}), name='cancel-scheduled-message'),
    path('scheduled-messages/<int:pk>/send-now/', ScheduledMessageViewSet.as_view({'post': 'send_now'}), name='send-scheduled-message-now'),
    
    # Теги чатов
    path('chat-tags/<int:pk>/assign/', ChatTagAssignmentViewSet.as_view({'post': 'create'}), name='assign-chat-tag'),
    path('chat-tags/<int:pk>/unassign/', ChatTagAssignmentViewSet.as_view({'delete': 'destroy'}), name='unassign-chat-tag'),
    
    # Папки чатов
    path('chat-folders/<int:folder_id>/chats/', get_folder_chats, name='folder-chats'),
    path('chat-folders/reorder/', ChatFolderViewSet.as_view({'post': 'reorder'}), name='reorder-folders'),
    path('chat-folders/<int:pk>/add-chat/', ChatFolderViewSet.as_view({'post': 'add_chat'}), name='add-chat-to-folder'),
    path('chat-folders/<int:pk>/remove-chat/', ChatFolderViewSet.as_view({'post': 'remove_chat'}), name='remove-chat-from-folder'),
    
    # Журнал безопасности
    path('security-logs/', SecurityLogViewSet.as_view({'get': 'list'}), name='security-logs'),
    
    # Аналитика
    path('group-chats/<int:chat_id>/analytics/', get_chat_analytics, name='chat-analytics'),
    
    # Экспорт/импорт настроек
    path('chat-settings/export/', export_settings, name='export-settings'),
    path('chat-settings/import/', import_settings, name='import-settings'),
    
    # Массовые операции
    path('group-chats/<int:chat_id>/messages/bulk-delete/', bulk_delete_messages, name='bulk-delete-messages'),
    path('group-chats/<int:chat_id>/members/bulk-add/', bulk_add_members, name='bulk-add-members'),
    path('group-chats/<int:chat_id>/members/bulk-remove/', bulk_remove_members, name='bulk-remove-members'),
    
    # Закреплённые сообщения (новая реализация)
    path('messages/<int:message_id>/pin-new/', pin_message_new, name='pin-message-new'),
    path('messages/<int:message_id>/unpin-new/', unpin_message_new, name='unpin-message-new'),
    path('chats/<int:chat_id>/pinned-messages-new/', get_pinned_messages_new, name='get-pinned-messages-new'),
    
    # Анти-спам
    path('group-chats/<int:chat_id>/check-spam/', check_message_spam, name='check-message-spam'),
    
    # Очистка чата
    path('chats/<int:chat_id>/clear-history/', clear_chat_history, name='clear-chat-history'),
    
] + router.urls