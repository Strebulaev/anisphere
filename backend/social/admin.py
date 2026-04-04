from django.contrib import admin
from .models import (
    Group, GroupMembership, Post, Comment, GroupChat, ChatRole, ChatMember,
    PrivateChat, Message, MessageReadStatus, ChatAdminLog, ChatTypingStatus,
    ChatSettings, PrivateChatUserSettings, Contest, ContestEntry, ContestVote
)

# Импорт новых моделей чатов
from .admin_chat import (
    ChatInviteLinkAdmin, ChatWallpaperAdmin, ChatThemeAdmin, MessageReactionAdmin,
    ChatBanAdmin, ChatRestrictionAdmin, ChatSlowModeAdmin, ChatJoinRequestAdmin,
    ChatTagAdmin, ChatTagAssignmentAdmin, AntiSpamRuleAdmin, ChatBackupAdmin, ScheduledMessageAdmin
)


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    readonly_fields = ('joined_at',)
    fields = ('user', 'role', 'joined_at')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'creator', 'is_private', 'members_count', 'posts_count', 'created_at')
    search_fields = ('name', 'slug', 'description', 'creator__username')
    list_filter = ('is_private', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'members_count', 'posts_count')
    filter_horizontal = ('moderators',)
    inlines = [GroupMembershipInline]


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    search_fields = ('user__username', 'group__name')
    list_filter = ('role', 'joined_at')
    readonly_fields = ('joined_at',)
    raw_id_fields = ('user', 'group')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'text_preview', 'anime', 'group', 'likes_count', 'comments_count', 'is_pinned', 'created_at')
    search_fields = ('author__username', 'text', 'anime__title_ru')
    list_filter = ('is_pinned', 'is_deleted', 'created_at', 'group')
    readonly_fields = ('created_at', 'updated_at', 'likes_count', 'comments_count', 'reposts_count')
    raw_id_fields = ('author', 'anime', 'group')
    
    def text_preview(self, obj):
        return obj.text[:100] if obj.text else ''
    text_preview.short_description = 'Текст'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'text_preview', 'content_object', 'parent', 'created_at')
    search_fields = ('author__username', 'text')
    list_filter = ('is_deleted', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('author', 'parent')
    
    def text_preview(self, obj):
        return obj.text[:100] if obj.text else ''
    text_preview.short_description = 'Текст'


class ChatMemberInline(admin.TabularInline):
    model = ChatMember
    extra = 0
    readonly_fields = ('joined_at',)
    fields = ('user', 'role', 'is_admin', 'joined_at')


@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_public', 'max_members', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    list_filter = ('is_public', 'created_at')
    readonly_fields = ('created_at', 'invite_link')
    inlines = [ChatMemberInline]


@admin.register(ChatRole)
class ChatRoleAdmin(admin.ModelAdmin):
    list_display = ('chat', 'name', 'level', 'color', 'can_delete_messages', 'can_ban_users')
    search_fields = ('chat__name', 'name')
    list_filter = ('can_delete_messages', 'can_ban_users', 'can_manage_chat')
    readonly_fields = ('created_at',)
    raw_id_fields = ('chat', 'created_by')


@admin.register(ChatMember)
class ChatMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'role', 'is_admin', 'is_banned', 'joined_at')
    search_fields = ('user__username', 'chat__name')
    list_filter = ('is_admin', 'is_banned', 'is_muted', 'is_pinned', 'is_archived')
    readonly_fields = ('joined_at',)
    raw_id_fields = ('user', 'chat', 'role', 'banned_by')


@admin.register(PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'last_message_at', 'user1_blocked', 'user2_blocked')
    search_fields = ('user1__username', 'user2__username')
    list_filter = ('user1_blocked', 'user2_blocked', 'user1_pinned', 'user2_pinned', 'user1_archived', 'user2_archived')
    readonly_fields = ('created_at', 'last_message_at')
    raw_id_fields = ('user1', 'user2')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'text_preview', 'chat', 'private_chat', 'is_edited', 'is_deleted', 'created_at')
    search_fields = ('sender__username', 'text')
    list_filter = ('is_edited', 'is_deleted', 'media_type', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'edited_at', 'deleted_at')
    raw_id_fields = ('chat', 'private_chat', 'sender', 'deleted_by', 'reply_to')
    
    def text_preview(self, obj):
        return obj.text[:100] if obj.text else ''
    text_preview.short_description = 'Текст'


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'read_at')
    search_fields = ('message__text', 'user__username')
    list_filter = ('read_at',)
    readonly_fields = ('read_at',)
    raw_id_fields = ('message', 'user')


@admin.register(ChatAdminLog)
class ChatAdminLogAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'action', 'target_user', 'created_at')
    search_fields = ('chat__name', 'user__username', 'action')
    list_filter = ('action', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('chat', 'user', 'target_user', 'message')


@admin.register(ChatTypingStatus)
class ChatTypingStatusAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'typed_at')
    search_fields = ('chat__name', 'user__username')
    list_filter = ('typed_at',)
    readonly_fields = ('typed_at',)
    raw_id_fields = ('chat', 'user')


@admin.register(ChatSettings)
class ChatSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'notifications_enabled', 'sound_enabled', 'auto_repeat_enabled')
    search_fields = ('user__username', 'chat__name')
    list_filter = ('notifications_enabled', 'sound_enabled', 'auto_repeat_enabled', 'is_blocked')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'chat')


@admin.register(PrivateChatUserSettings)
class PrivateChatUserSettingsAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'notifications_enabled', 'updated_at')
    search_fields = ('chat__user1__username', 'chat__user2__username', 'user__username')
    list_filter = ('notifications_enabled',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('chat', 'user')


class ContestEntryInline(admin.TabularInline):
    model = ContestEntry
    extra = 0
    readonly_fields = ('submitted_at', 'votes_count')
    fields = ('participant', 'title', 'votes_count', 'is_winner', 'winner_place', 'submitted_at')


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'format', 'status', 'organizer', 'entries_count', 'votes_count', 'created_at')
    search_fields = ('title', 'description', 'theme', 'organizer__username')
    list_filter = ('type', 'format', 'status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'entries_count', 'votes_count')
    raw_id_fields = ('organizer', 'anime')
    inlines = [ContestEntryInline]


@admin.register(ContestEntry)
class ContestEntryAdmin(admin.ModelAdmin):
    list_display = ('contest', 'participant', 'title', 'votes_count', 'is_winner', 'winner_place', 'submitted_at')
    search_fields = ('contest__title', 'participant__username', 'title', 'description')
    list_filter = ('is_winner', 'winner_place', 'submitted_at')
    readonly_fields = ('submitted_at', 'updated_at', 'votes_count')
    raw_id_fields = ('contest', 'participant')


@admin.register(ContestVote)
class ContestVoteAdmin(admin.ModelAdmin):
    list_display = ('contest', 'entry', 'voter', 'vote_type', 'value', 'created_at')
    search_fields = ('contest__title', 'entry__title', 'voter__username')
    list_filter = ('vote_type', 'value', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('contest', 'entry', 'voter')


# Модели мини-чата поддержки
from .models_support import SupportTicket, SupportMessage


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'subject')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    raw_id_fields = ('user',)


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'sender', 'text_preview', 'is_read', 'created_at')
    search_fields = ('sender__username', 'text', 'ticket__id')
    list_filter = ('is_read', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('ticket', 'sender')
    
    def text_preview(self, obj):
        return obj.text[:100] if obj.text else ''
    text_preview.short_description = 'Текст'