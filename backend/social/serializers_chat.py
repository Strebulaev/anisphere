"""
Сериализаторы для системы чатов.
"""

from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q

from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme,
    MessageReaction, ChatBan, ChatRestriction, ChatSlowMode,
    ChatJoinRequest, ChatTag, ChatTagAssignment, AntiSpamRule,
    ChatBackup, ScheduledMessage, SecurityLog, GroupChatSettings,
    PrivateChatSettings, MessagePin, GroupMemberSettings,
)
from .models import GroupChat, PrivateChat, Message, ChatRole, ChatMember, ChatFolder, ChatFolderChat
from users.models import User


# ── Util ──

class UserMiniSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'is_online']

    def get_avatar_url(self, obj):
        if obj.avatar:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.avatar.url) if req else obj.avatar.url
        return None

    def get_is_online(self, obj):
        try:
            from core.online_status import online_status
            return online_status.is_online(obj.id)
        except Exception:
            return False


# ── ChatWallpaper ──

class ChatWallpaperSerializer(serializers.ModelSerializer):
    wallpaper_image_url = serializers.SerializerMethodField()
    css = serializers.SerializerMethodField()

    class Meta:
        model = ChatWallpaper
        fields = [
            'id', 'wallpaper_type',
            'wallpaper_color', 'wallpaper_color2',
            'wallpaper_intensity', 'wallpaper_blur', 'wallpaper_motion',
            'gradient_angle',
            'pattern_type', 'pattern_color', 'pattern_opacity',
            'wallpaper_image', 'wallpaper_image_url',
            'is_preset', 'preset_name', 'preset_category',
            'css', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_wallpaper_image_url(self, obj):
        if obj.wallpaper_image:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.wallpaper_image.url) if req else obj.wallpaper_image.url
        return None

    def get_css(self, obj):
        return obj.to_css()


# ── ChatTheme ──

class ChatThemeSerializer(serializers.ModelSerializer):
    css_vars = serializers.SerializerMethodField()

    class Meta:
        model = ChatTheme
        fields = [
            'id', 'theme',
            'message_color_mine', 'message_color_other',
            'message_text_color_mine', 'message_text_color_other',
            'bubble_style', 'bubble_border_radius', 'bubble_shadow',
            'font_family', 'font_size', 'font_size_px', 'font_weight', 'line_height',
            'time_format', 'time_color',
            'background_color', 'header_color', 'input_color',
            'input_text_color', 'accent_color', 'link_color',
            'message_animation', 'reaction_animation', 'typing_animation',
            'emoji_set', 'emoji_size',
            'show_avatars', 'show_usernames', 'compact_mode',
            'show_read_status', 'show_typing_indicator', 'message_grouping',
            'custom_css', 'css_vars', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_css_vars(self, obj):
        return obj.to_css_vars()


# ── PrivateChatSettings ──

class PrivateChatSettingsSerializer(serializers.ModelSerializer):
    is_muted = serializers.ReadOnlyField()
    custom_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChatSettings
        fields = [
            'id', 'chat', 'user',
            'custom_name', 'custom_avatar', 'custom_avatar_url',
            'notifications_enabled', 'sound_enabled', 'notification_sound',
            'vibration_enabled', 'show_preview', 'show_popup',
            'muted_until', 'is_muted',
            'is_archived', 'is_pinned', 'is_hidden', 'is_blocked', 'blocked_at',
            'auto_delete_enabled', 'auto_delete_after',
            'folder_id', 'tags',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.custom_avatar.url) if req else obj.custom_avatar.url
        return None


# ── GroupMemberSettings ──

class GroupMemberSettingsSerializer(serializers.ModelSerializer):
    is_muted = serializers.ReadOnlyField()

    class Meta:
        model = GroupMemberSettings
        fields = [
            'id', 'notifications_enabled', 'mentions_only',
            'sound_enabled', 'show_preview', 'muted_until', 'is_muted',
            'is_pinned', 'is_archived', 'tags',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ── ChatInviteLink ──

class ChatInviteLinkSerializer(serializers.ModelSerializer):
    creator = UserMiniSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = ChatInviteLink
        fields = [
            'id', 'chat', 'creator', 'name', 'invite_link', 'link_type',
            'expires_at', 'usage_limit', 'usage_count', 'remaining_uses',
            'is_revoked', 'is_primary', 'auto_assign_role',
            'is_valid', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'invite_link', 'usage_count', 'creator', 'created_at', 'updated_at']

    def get_remaining_uses(self, obj):
        if obj.usage_limit is None:
            return None
        return max(0, obj.usage_limit - obj.usage_count)


class ChatInviteLinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInviteLink
        fields = ['chat', 'name', 'link_type', 'expires_at', 'usage_limit', 'is_primary', 'auto_assign_role']

    def validate(self, data):
        req = self.context.get('request')
        if req:
            chat = data.get('chat')
            try:
                member = ChatMember.objects.get(chat=chat, user=req.user)
                if not member.is_owner and not member.is_admin:
                    if not member.effective_permissions.get('can_invite_users', False):
                        raise serializers.ValidationError('Нет прав на создание приглашений')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник этого чата')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['creator'] = req.user
        return super().create(validated_data)


# ── ChatBan ──

class ChatBanSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    banned_by = UserMiniSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = ChatBan
        fields = [
            'id', 'chat', 'user', 'banned_by', 'reason',
            'until_date', 'delete_messages', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'banned_by', 'created_at']


class ChatBanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBan
        fields = ['chat', 'user', 'reason', 'until_date', 'delete_messages']

    def validate(self, data):
        chat = data.get('chat')
        user = data.get('user')
        if chat.created_by == user:
            raise serializers.ValidationError('Нельзя заблокировать владельца')
        req = self.context.get('request')
        if req:
            try:
                m = ChatMember.objects.get(chat=chat, user=req.user)
                if not m.is_owner and not m.effective_permissions.get('can_ban_users', False):
                    raise serializers.ValidationError('Нет прав на блокировку')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['banned_by'] = req.user
        # Удаляем участника
        ChatMember.objects.filter(chat=validated_data['chat'], user=validated_data['user']).delete()
        if validated_data.get('delete_messages'):
            Message.objects.filter(chat=validated_data['chat'], sender=validated_data['user']).delete()
        return super().create(validated_data)


# ── ChatRestriction ──

class ChatRestrictionSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    restricted_by = UserMiniSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    restriction_type_display = serializers.CharField(source='get_restriction_type_display', read_only=True)

    class Meta:
        model = ChatRestriction
        fields = [
            'id', 'chat', 'user', 'restricted_by',
            'restriction_type', 'restriction_type_display',
            'reason', 'until_date', 'slow_mode_delay',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'restricted_by', 'created_at']


class ChatRestrictionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRestriction
        fields = ['chat', 'user', 'restriction_type', 'reason', 'until_date', 'slow_mode_delay']

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['restricted_by'] = req.user
        return super().create(validated_data)


# ── ChatSlowMode ──

class ChatSlowModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSlowMode
        fields = ['id', 'chat', 'enabled', 'delay', 'exempt_admins', 'exempt_moderators', 'custom_delays']
        read_only_fields = ['id']


# ── ChatJoinRequest ──

class ChatJoinRequestSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    reviewed_by = UserMiniSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChatJoinRequest
        fields = [
            'id', 'chat', 'user', 'message', 'answers',
            'status', 'status_display', 'reviewed_by', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']


class ChatJoinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatJoinRequest
        fields = ['chat', 'message', 'answers']

    def validate(self, data):
        chat = data.get('chat')
        req = self.context.get('request')
        if ChatMember.objects.filter(chat=chat, user=req.user).exists():
            raise serializers.ValidationError('Вы уже участник')
        if ChatJoinRequest.objects.filter(chat=chat, user=req.user, status='pending').exists():
            raise serializers.ValidationError('Запрос уже отправлен')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['user'] = req.user
        return super().create(validated_data)


# ── ChatTag ──

class ChatTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatTag
        fields = ['id', 'user', 'name', 'color', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatTagAssignmentSerializer(serializers.ModelSerializer):
    tag = ChatTagSerializer(read_only=True)

    class Meta:
        model = ChatTagAssignment
        fields = ['id', 'tag', 'group_chat', 'private_chat', 'created_at']
        read_only_fields = ['id', 'created_at']


# ── AntiSpamRule ──

class AntiSpamRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AntiSpamRule
        fields = [
            'id', 'chat', 'rule_type', 'rule_type_display',
            'threshold', 'time_window', 'keywords',
            'action', 'action_display', 'action_duration',
            'enabled', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ── ChatBackup ──

class ChatBackupSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChatBackup
        fields = [
            'id', 'chat', 'created_by',
            'backup_file', 'messages_count', 'members_count',
            'file_size', 'file_size_mb', 'status', 'status_display', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size else 0


# ── ScheduledMessage ──

class ScheduledMessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ScheduledMessage
        fields = [
            'id', 'sender', 'chat', 'private_chat',
            'text', 'media', 'media_type',
            'scheduled_at', 'is_recurring', 'recurring_interval',
            'status', 'status_display', 'sent_at', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sender', 'status', 'sent_at', 'error_message', 'created_at', 'updated_at']


class ScheduledMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledMessage
        fields = ['chat', 'private_chat', 'text', 'media', 'media_type', 'scheduled_at', 'is_recurring', 'recurring_interval']

    def validate(self, data):
        if not data.get('chat') and not data.get('private_chat'):
            raise serializers.ValidationError('Укажите чат')
        if data.get('scheduled_at') and data['scheduled_at'] <= timezone.now():
            raise serializers.ValidationError('Время в прошлом')
        return data

    def create(self, validated_data):
        req = self.context.get('request')
        validated_data['sender'] = req.user
        return super().create(validated_data)


# ── SecurityLog ──

class SecurityLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = SecurityLog
        fields = [
            'id', 'user', 'action', 'action_display',
            'ip_address', 'user_agent', 'device_info', 'location',
            'details', 'is_suspicious', 'was_notified', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ── GroupChatSettings ──

class GroupChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupChatSettings
        fields = [
            'id', 'chat', 'members_count', 'online_count', 'messages_count',
            'last_activity_at', 'last_message_at',
            'daily_messages', 'weekly_active', 'cache_updated_at',
        ]
        read_only_fields = ['id', 'cache_updated_at']


# ── MessagePin ──

class MessagePinSerializer(serializers.ModelSerializer):
    pinned_by_username = serializers.CharField(source='pinned_by.username', read_only=True)

    class Meta:
        model = MessagePin
        fields = ['id', 'message', 'pinned_by', 'pinned_by_username', 'created_at']
        read_only_fields = ['id', 'created_at']


# ── ChatFolder ──

class ChatFolderSerializer(serializers.ModelSerializer):
    chats_count = serializers.SerializerMethodField()

    class Meta:
        from .models import ChatFolder
        model = ChatFolder
        fields = [
            'id', 'name', 'icon', 'color', 'order',
            'include_private', 'include_groups', 'include_channels',
            'include_archived', 'include_muted', 'match_all',
            'created_at', 'updated_at', 'chats_count',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_chats_count(self, obj):
        return obj.chats.count()


class ChatFolderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import ChatFolder
        model = ChatFolder
        fields = ['name', 'icon', 'color', 'order', 'include_private', 'include_groups',
                  'include_channels', 'include_archived', 'include_muted', 'match_all']
