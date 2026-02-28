from django.contrib import admin
from .models import (
    User, UserSettings, UserProfileSettings, TwoFactorAuth, 
    ActiveSession, NotificationSettings, PrivacySettings, 
    UserTheme, ChatBackground, SecurityLog, EmailLog, 
    MessageNotification, UserAnalytics
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active', 'is_online', 'level')
    search_fields = ('username', 'email', 'nickname', 'display_name')
    list_filter = ('is_staff', 'is_active', 'is_online', 'email_verified', 'phone_verified', 'two_factor_enabled')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at', 'unique_id')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'email', 'password', 'nickname', 'display_name')
        }),
        ('Аватар и био', {
            'fields': ('avatar', 'bio')
        }),
        ('Статистика', {
            'fields': ('level', 'experience', 'mana', 'posts_count', 'comments_count', 'likes_received', 'playlists_count')
        }),
        ('Верификация', {
            'fields': ('email_verified', 'phone_verified', 'google_id', 'unique_id')
        }),
        ('Онлайн статус', {
            'fields': ('is_online', 'last_seen')
        }),
        ('Двухфакторная аутентификация', {
            'fields': ('two_factor_enabled', 'two_factor_secret', 'sms_code', 'sms_code_expires')
        }),
        ('Контакты', {
            'fields': ('website', 'vk_profile', 'telegram', 'phone_number')
        }),
        ('Бейджи', {
            'fields': ('badges',)
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'ui_style', 'text_size', 'push_notifications')
    search_fields = ('user__username', 'user__email')
    list_filter = ('theme', 'ui_style', 'text_size', 'push_notifications', 'email_notifications', 'show_in_search')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProfileSettings)
class UserProfileSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'language', 'timezone', 'show_online_status')
    search_fields = ('user__username', 'user__email')
    list_filter = ('theme', 'language', 'timezone', 'show_online_status', 'allow_calls', 'allow_group_invites')
    readonly_fields = ('updated_at',)


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'email_enabled', 'require_on_new_device', 'last_used')
    search_fields = ('user__username', 'user__email')
    list_filter = ('is_enabled', 'email_enabled', 'require_on_new_device')
    readonly_fields = ('created_at', 'last_used')


@admin.register(ActiveSession)
class ActiveSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'ip_address', 'country', 'city', 'is_current', 'last_activity')
    search_fields = ('user__username', 'session_key', 'ip_address')
    list_filter = ('is_current', 'country', 'city')
    readonly_fields = ('created_at', 'last_activity')


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_notifications', 'group_notifications', 'call_notifications', 'push_enabled')
    search_fields = ('user__username', 'user__email')
    list_filter = ('message_notifications', 'group_notifications', 'call_notifications', 'push_enabled', 'push_sound', 'email_enabled')
    readonly_fields = ('updated_at',)


@admin.register(PrivacySettings)
class PrivacySettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'who_can_see_phone', 'who_can_see_email', 'who_can_see_last_seen', 'who_can_call')
    search_fields = ('user__username', 'user__email')
    list_filter = ('who_can_see_phone', 'who_can_see_email', 'who_can_see_last_seen', 'who_can_call', 'who_can_add_to_groups')


@admin.register(UserTheme)
class UserThemeAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_active', 'primary_color', 'secondary_color')
    search_fields = ('user__username', 'name')
    list_filter = ('is_active', 'compact_mode', 'show_message_time')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatBackground)
class ChatBackgroundAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_default', 'opacity', 'created_at')
    search_fields = ('user__username', 'name')
    list_filter = ('is_default',)


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'location', 'created_at')
    search_fields = ('user__username', 'action', 'ip_address')
    list_filter = ('action', 'location', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'sent_at')
    search_fields = ('user__username', 'user__email', 'subject')
    list_filter = ('sent_at',)
    readonly_fields = ('sent_at',)


@admin.register(MessageNotification)
class MessageNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_id', 'notified_via', 'notified_at')
    search_fields = ('user__username', 'message_id')
    list_filter = ('notified_via', 'notified_at')
    readonly_fields = ('notified_at',)


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'messages_sent', 'messages_received', 'time_spent', 'primary_device')
    search_fields = ('user__username', 'primary_device', 'last_used_device')
    list_filter = ('favorite_chat_type', 'primary_device', 'last_used_device')
    readonly_fields = ('last_updated', 'collected_since')