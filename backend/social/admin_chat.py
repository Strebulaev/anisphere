"""
Admin для новых моделей системы чатов
"""

from django.contrib import admin
from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage
)


@admin.register(ChatInviteLink)
class ChatInviteLinkAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'creator', 'invite_link', 'is_valid', 'usage_count', 'is_primary', 'created_at']
    list_filter = ['is_revoked', 'is_primary', 'created_at']
    search_fields = ['chat__name', 'creator__username', 'invite_link']
    readonly_fields = ['invite_link', 'usage_count', 'created_at', 'updated_at']
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True


@admin.register(ChatWallpaper)
class ChatWallpaperAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'chat', 'wallpaper_type', 'is_preset', 'created_at']
    list_filter = ['wallpaper_type', 'is_preset', 'created_at']
    search_fields = ['user__username', 'chat__name', 'preset_name']


@admin.register(ChatTheme)
class ChatThemeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'chat', 'private_chat', 'theme', 'bubble_style', 'font_size']
    list_filter = ['theme', 'bubble_style', 'font_size', 'time_format']
    search_fields = ['user__username']


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['user__username', 'message__text']
    raw_id_fields = ['message', 'user']


@admin.register(ChatBan)
class ChatBanAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'user', 'banned_by', 'until_date', 'is_active', 'created_at']
    list_filter = ['created_at', 'until_date']
    search_fields = ['chat__name', 'user__username', 'banned_by__username']
    raw_id_fields = ['chat', 'user', 'banned_by']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True


@admin.register(ChatRestriction)
class ChatRestrictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'user', 'restriction_type', 'until_date', 'is_active', 'created_at']
    list_filter = ['restriction_type', 'created_at', 'until_date']
    search_fields = ['chat__name', 'user__username']
    raw_id_fields = ['chat', 'user', 'restricted_by']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True


@admin.register(ChatSlowMode)
class ChatSlowModeAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'enabled', 'delay', 'exempt_admins', 'exempt_moderators']
    list_filter = ['enabled', 'exempt_admins', 'exempt_moderators']
    raw_id_fields = ['chat']


@admin.register(ChatJoinRequest)
class ChatJoinRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'user', 'status', 'reviewed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['chat__name', 'user__username']
    raw_id_fields = ['chat', 'user', 'reviewed_by']


@admin.register(ChatTag)
class ChatTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'color', 'emoji', 'created_at']
    list_filter = ['color', 'created_at']
    search_fields = ['name', 'user__username']


@admin.register(ChatTagAssignment)
class ChatTagAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'group_chat', 'private_chat', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['tag', 'group_chat', 'private_chat']


@admin.register(AntiSpamRule)
class AntiSpamRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'rule_type', 'threshold', 'action', 'enabled', 'created_at']
    list_filter = ['rule_type', 'action', 'enabled', 'created_at']
    search_fields = ['chat__name']
    raw_id_fields = ['chat']


@admin.register(ChatBackup)
class ChatBackupAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'created_by', 'status', 'messages_count', 'file_size_mb', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['chat__name', 'created_by__username']
    raw_id_fields = ['chat', 'created_by']
    
    def file_size_mb(self, obj):
        return obj.file_size_mb
    file_size_mb.short_description = 'Размер (MB)'


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'chat', 'private_chat', 'scheduled_at', 'status', 'is_recurring', 'created_at']
    list_filter = ['status', 'is_recurring', 'created_at', 'scheduled_at']
    search_fields = ['sender__username', 'text']
    raw_id_fields = ['sender', 'chat', 'private_chat']
