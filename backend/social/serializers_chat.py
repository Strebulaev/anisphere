"""
Сериализаторы для системы чатов согласно документации CHAT_SETTINGS.md
"""

from rest_framework import serializers
from django.utils import timezone
from django.db.models import Count, Q
from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    SecurityLog, GroupChatSettings, PrivateChatSettings, MessagePin
)
from .models import GroupChat, PrivateChat, Message, ChatRole, ChatMember, ChatFolder, ChatFolderChat
from .serializers import ChatRoleSerializer

# Импортируем MessageSerializer если он есть, иначе создаём простой вариант
try:
    from .serializers import MessageSerializer
except ImportError:
    class MessageSerializer(serializers.ModelSerializer):
        class Meta:
            model = Message
            fields = ['id', 'text', 'sender', 'created_at', 'media_type', 'is_pinned']

from users.models import User


class UserSimpleSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор пользователя"""
    avatar_url = serializers.ImageField(source='avatar', read_only=True)
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'is_online']
    
    def get_is_online(self, obj):
        from core.online_status import online_status
        return online_status.is_online(obj.id)


# ==================== ССЫЛКИ-ПРИГЛАШЕНИЯ ====================

class ChatInviteLinkSerializer(serializers.ModelSerializer):
    """Сериализатор ссылки-приглашения"""
    creator = UserSimpleSerializer(read_only=True)
    chat_name = serializers.CharField(source='chat.name', read_only=True)
    is_valid = serializers.ReadOnlyField()
    remaining_uses = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatInviteLink
        fields = [
            'id', 'chat', 'chat_name', 'creator', 'name', 'invite_link',
            'expires_at', 'usage_limit', 'usage_count', 'remaining_uses',
            'is_revoked', 'is_primary', 'auto_assign_role',
            'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invite_link', 'usage_count', 'created_at', 'updated_at']
    
    def get_remaining_uses(self, obj):
        if obj.usage_limit is None:
            return None  # Безлимитно
        return max(0, obj.usage_limit - obj.usage_count)


class ChatInviteLinkCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания ссылки-приглашения"""
    
    class Meta:
        model = ChatInviteLink
        fields = [
            'chat', 'name', 'expires_at', 'usage_limit',
            'is_primary', 'auto_assign_role'
        ]
    
    def validate(self, data):
        # Проверяем права пользователя
        request = self.context.get('request')
        if request:
            chat = data.get('chat')
            try:
                member = ChatMember.objects.get(chat=chat, user=request.user)
                if not member.is_owner and not member.is_admin:
                    if not member.effective_permissions.get('can_invite_users', False):
                        raise serializers.ValidationError('У вас нет прав на создание приглашений')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник этого чата')
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['creator'] = request.user
        return super().create(validated_data)


# ==================== ОБОИ ЧАТОВ ====================

class ChatWallpaperSerializer(serializers.ModelSerializer):
    """Сериализатор обоев чата"""
    wallpaper_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatWallpaper
        fields = [
            'id', 'user', 'chat', 'private_chat', 'wallpaper_type',
            'wallpaper_color', 'wallpaper_color2',
            'wallpaper_intensity', 'wallpaper_blur', 'wallpaper_motion',
            'wallpaper_image', 'wallpaper_image_url',
            'is_preset', 'preset_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_wallpaper_image_url(self, obj):
        if obj.wallpaper_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.wallpaper_image.url)
            return obj.wallpaper_image.url
        return None


class ChatWallpaperPresetSerializer(serializers.Serializer):
    """Сериализатор для предустановленных обоев"""
    id = serializers.CharField()
    name = serializers.CharField()
    wallpaper_type = serializers.CharField()
    wallpaper_color = serializers.CharField()
    wallpaper_color2 = serializers.CharField()
    preview_url = serializers.URLField(allow_null=True)


# ==================== ТЕМЫ ОФОРМЛЕНИЯ ====================

class ChatThemeSerializer(serializers.ModelSerializer):
    """Сериализатор темы оформления чата"""
    
    class Meta:
        model = ChatTheme
        fields = [
            'id', 'user', 'chat', 'private_chat',
            'theme', 'message_color', 'message_color_other',
            'bubble_style', 'font_size', 'time_format',
            'message_animation', 'reaction_animation', 'typing_animation',
            'emoji_set', 'emoji_size',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ==================== РЕАКЦИИ НА СООБЩЕНИЯ ====================

class MessageReactionSerializer(serializers.ModelSerializer):
    """Сериализатор реакции на сообщение"""
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'message', 'user', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class MessageReactionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления реакции"""
    
    class Meta:
        model = MessageReaction
        fields = ['message', 'emoji']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # Проверяем, не существует ли уже такая реакция
        reaction, created = MessageReaction.objects.get_or_create(
            message=validated_data['message'],
            user=validated_data['user'],
            emoji=validated_data['emoji']
        )
        
        if not created:
            # Если реакция уже есть - удаляем её (toggle)
            reaction.delete()
            return None
        
        return reaction


class GroupedReactionsSerializer(serializers.Serializer):
    """Сериализатор для сгруппированных реакций"""
    emoji = serializers.CharField()
    count = serializers.IntegerField()
    users = UserSimpleSerializer(many=True)
    is_mine = serializers.BooleanField()


# ==================== БЛОКИРОВКИ И ОГРАНИЧЕНИЯ ====================

class ChatBanSerializer(serializers.ModelSerializer):
    """Сериализатор блокировки"""
    user = UserSimpleSerializer(read_only=True)
    banned_by = UserSimpleSerializer(read_only=True)
    chat_name = serializers.CharField(source='chat.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatBan
        fields = [
            'id', 'chat', 'chat_name', 'user', 'banned_by',
            'reason', 'until_date', 'delete_messages',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'banned_by', 'created_at']


class ChatBanCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания блокировки"""
    
    class Meta:
        model = ChatBan
        fields = ['chat', 'user', 'reason', 'until_date', 'delete_messages']
    
    def validate(self, data):
        # Нельзя забанить владельца
        chat = data.get('chat')
        user = data.get('user')
        if chat.created_by == user:
            raise serializers.ValidationError('Нельзя заблокировать владельца чата')
        
        # Проверяем права
        request = self.context.get('request')
        if request:
            try:
                member = ChatMember.objects.get(chat=chat, user=request.user)
                if not member.is_owner and not member.effective_permissions.get('can_ban_users', False):
                    raise serializers.ValidationError('У вас нет прав на блокировку')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник этого чата')
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['banned_by'] = request.user
        
        # Удаляем участника из чата
        ChatMember.objects.filter(
            chat=validated_data['chat'],
            user=validated_data['user']
        ).delete()
        
        # Если нужно удалить сообщения
        if validated_data.get('delete_messages'):
            Message.objects.filter(
                chat=validated_data['chat'],
                sender=validated_data['user']
            ).delete()
        
        return super().create(validated_data)


class ChatRestrictionSerializer(serializers.ModelSerializer):
    """Сериализатор ограничения"""
    user = UserSimpleSerializer(read_only=True)
    restricted_by = UserSimpleSerializer(read_only=True)
    restriction_type_display = serializers.CharField(source='get_restriction_type_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatRestriction
        fields = [
            'id', 'chat', 'user', 'restricted_by',
            'restriction_type', 'restriction_type_display',
            'reason', 'until_date', 'slow_mode_delay',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'restricted_by', 'created_at']


class ChatRestrictionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания ограничения"""
    
    class Meta:
        model = ChatRestriction
        fields = ['chat', 'user', 'restriction_type', 'reason', 'until_date', 'slow_mode_delay']
    
    def validate(self, data):
        request = self.context.get('request')
        if request:
            try:
                member = ChatMember.objects.get(chat=data.get('chat'), user=request.user)
                if not member.is_owner and not member.effective_permissions.get('can_restrict_members', False):
                    raise serializers.ValidationError('У вас нет прав на ограничение участников')
            except ChatMember.DoesNotExist:
                raise serializers.ValidationError('Вы не участник этого чата')
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['restricted_by'] = request.user
        return super().create(validated_data)


# ==================== МЕДЛЕННЫЙ РЕЖИМ ====================

class ChatSlowModeSerializer(serializers.ModelSerializer):
    """Сериализатор медленного режима"""
    
    class Meta:
        model = ChatSlowMode
        fields = [
            'id', 'chat', 'enabled', 'delay',
            'exempt_admins', 'exempt_moderators',
            'custom_delays', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ==================== ЗАПРОСЫ НА ВСТУПЛЕНИЕ ====================

class ChatJoinRequestSerializer(serializers.ModelSerializer):
    """Сериализатор запроса на вступление"""
    user = UserSimpleSerializer(read_only=True)
    chat_name = serializers.CharField(source='chat.name', read_only=True)
    reviewed_by = UserSimpleSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ChatJoinRequest
        fields = [
            'id', 'chat', 'chat_name', 'user',
            'message', 'answers', 'status', 'status_display',
            'reviewed_by', 'reviewed_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']


class ChatJoinRequestCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания запроса на вступление"""
    
    class Meta:
        model = ChatJoinRequest
        fields = ['chat', 'message', 'answers']
    
    def validate(self, data):
        chat = data.get('chat')
        request = self.context.get('request')
        
        # Проверяем, не является ли пользователь уже участником
        if ChatMember.objects.filter(chat=chat, user=request.user).exists():
            raise serializers.ValidationError('Вы уже участник этого чата')
        
        # Проверяем, нет ли уже pending запроса
        if ChatJoinRequest.objects.filter(chat=chat, user=request.user, status='pending').exists():
            raise serializers.ValidationError('У вас уже есть pending запрос на вступление')
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


# ==================== ТЕГИ ЧАТОВ ====================

class ChatTagSerializer(serializers.ModelSerializer):
    """Сериализатор тега чата"""
    
    class Meta:
        model = ChatTag
        fields = ['id', 'user', 'name', 'color', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatTagAssignmentSerializer(serializers.ModelSerializer):
    """Сериализатор привязки тега"""
    tag = ChatTagSerializer(read_only=True)
    
    class Meta:
        model = ChatTagAssignment
        fields = ['id', 'tag', 'group_chat', 'private_chat', 'created_at']
        read_only_fields = ['id', 'created_at']


# ==================== АНТИ-СПАМ ====================

class AntiSpamRuleSerializer(serializers.ModelSerializer):
    """Сериализатор правила анти-спама"""
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AntiSpamRule
        fields = [
            'id', 'chat', 'rule_type', 'rule_type_display',
            'threshold', 'time_window', 'keywords',
            'action', 'action_display', 'action_duration',
            'enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ==================== РЕЗЕРВНЫЕ КОПИИ ====================

class ChatBackupSerializer(serializers.ModelSerializer):
    """Сериализатор резервной копии"""
    created_by = UserSimpleSerializer(read_only=True)
    chat_name = serializers.CharField(source='chat.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatBackup
        fields = [
            'id', 'chat', 'chat_name', 'created_by',
            'backup_file', 'messages_count', 'members_count',
            'file_size', 'file_size_mb', 'status', 'status_display',
            'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


# ==================== ЗАПЛАНИРОВАННЫЕ СООБЩЕНИЯ ====================

class ScheduledMessageSerializer(serializers.ModelSerializer):
    """Сериализатор запланированного сообщения"""
    sender = UserSimpleSerializer(read_only=True)
    chat_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    media_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledMessage
        fields = [
            'id', 'sender', 'chat', 'private_chat', 'chat_name',
            'text', 'media', 'media_url', 'media_type',
            'scheduled_at', 'is_recurring', 'recurring_interval',
            'status', 'status_display', 'sent_at', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'status', 'sent_at', 'error_message', 'created_at', 'updated_at']
    
    def get_chat_name(self, obj):
        if obj.chat:
            return obj.chat.name
        if obj.private_chat:
            other = obj.private_chat.other_user(obj.sender)
            return other.display_name or other.username
        return None
    
    def get_media_url(self, obj):
        if obj.media:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media.url)
            return obj.media.url
        return None


class ScheduledMessageCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания запланированного сообщения"""
    
    class Meta:
        model = ScheduledMessage
        fields = [
            'chat', 'private_chat', 'text', 'media', 'media_type',
            'scheduled_at', 'is_recurring', 'recurring_interval'
        ]
    
    def validate(self, data):
        # Должен быть указан либо chat, либо private_chat
        if not data.get('chat') and not data.get('private_chat'):
            raise serializers.ValidationError('Укажите чат или личный чат')
        
        if data.get('chat') and data.get('private_chat'):
            raise serializers.ValidationError('Укажите только один тип чата')
        
        # Проверяем, что scheduled_at в будущем
        if data.get('scheduled_at') and data['scheduled_at'] <= timezone.now():
            raise serializers.ValidationError('Время отправки должно быть в будущем')
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)


# ==================== РАСШИРЕННЫЕ СЕРИАЛИЗАТОРЫ ЧАТОВ ====================

class GroupChatExtendedSerializer(serializers.ModelSerializer):
    """Расширенный сериализатор группового чата с дополнительными полями"""
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    online_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    wallpaper = ChatWallpaperSerializer(read_only=True)
    theme = ChatThemeSerializer(read_only=True)
    slow_mode = ChatSlowModeSerializer(read_only=True)
    active_restrictions = serializers.SerializerMethodField()
    pending_join_requests = serializers.SerializerMethodField()
    invite_links_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupChat
        fields = '__all__'
    
    def get_online_count(self, obj):
        from core.online_status import online_status
        online = 0
        for member in obj.members.all():
            if online_status.is_online(member.user_id):
                online += 1
        return online
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return {
                    'is_owner': member.is_owner,
                    'is_admin': member.is_admin,
                    'role': ChatRoleSerializer(member.role).data if member.role else None,
                    'custom_title': member.custom_title
                }
            except ChatMember.DoesNotExist:
                pass
        return None
    
    def get_user_permissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return member.effective_permissions
            except ChatMember.DoesNotExist:
                pass
        return {}
    
    def get_last_message(self, obj):
        last_message = Message.objects.filter(chat=obj).order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'text': last_message.text[:100] if last_message.text else None,
                'sender': UserSimpleSerializer(last_message.sender).data,
                'created_at': last_message.created_at,
                'media_type': last_message.media_type
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import MessageReadStatus
            read_ids = MessageReadStatus.objects.filter(
                user=request.user,
                message__chat=obj
            ).values_list('message_id', flat=True)
            
            return Message.objects.filter(
                chat=obj
            ).exclude(
                sender=request.user
            ).exclude(
                id__in=read_ids
            ).count()
        return 0
    
    def get_active_restrictions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ChatRestriction.objects.filter(
                chat=obj,
                user=request.user
            ).filter(
                Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
            ).count()
        return 0
    
    def get_pending_join_requests(self, obj):
        if obj.is_public:
            return 0
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                if member.is_admin or member.is_owner:
                    return ChatJoinRequest.objects.filter(chat=obj, status='pending').count()
            except ChatMember.DoesNotExist:
                pass
        return 0
    
    def get_invite_links_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                if member.is_admin or member.is_owner or member.effective_permissions.get('can_invite_users'):
                    return obj.invite_links.filter(is_revoked=False).count()
            except ChatMember.DoesNotExist:
                pass
        return 0


class PrivateChatExtendedSerializer(serializers.ModelSerializer):
    """Расширенный сериализатор личного чата"""
    other_user = serializers.SerializerMethodField()
    user_settings = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    wallpaper = ChatWallpaperSerializer(read_only=True)
    theme = ChatThemeSerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = PrivateChat
        fields = [
            'id', 'user1', 'user2', 'created_at', 'last_message_at',
            'user1_notifications', 'user2_notifications',
            'user1_muted_until', 'user2_muted_until',
            'user1_archived', 'user2_archived',
            'user1_pinned', 'user2_pinned',
            'user1_blocked', 'user2_blocked',
            'other_user', 'user_settings', 'unread_count', 'last_message',
            'wallpaper', 'theme', 'tags'
        ]
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.other_user(request.user)
            return UserSimpleSerializer(other).data
        return None
    
    def get_user_settings(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_settings(request.user)
        return {}
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import MessageReadStatus
            read_ids = MessageReadStatus.objects.filter(
                user=request.user,
                message__private_chat=obj
            ).values_list('message_id', flat=True)
            
            return Message.objects.filter(
                private_chat=obj
            ).exclude(
                sender=request.user
            ).exclude(
                id__in=read_ids
            ).count()
        return 0
    
    def get_last_message(self, obj):
        last_message = Message.objects.filter(private_chat=obj).order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'text': last_message.text[:100] if last_message.text else None,
                'sender': UserSimpleSerializer(last_message.sender).data,
                'created_at': last_message.created_at,
                'media_type': last_message.media_type
            }
        return None
    
    def get_tags(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            assignments = ChatTagAssignment.objects.filter(
                private_chat=obj,
                tag__user=request.user
            ).select_related('tag')
            return ChatTagSerializer([a.tag for a in assignments], many=True).data
        return []


# ==================== ПАПКИ ЧАТОВ ====================

class ChatFolderSerializer(serializers.ModelSerializer):
    """Сериализатор папки чатов"""
    chats_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatFolder
        fields = [
            'id', 'name', 'icon', 'color', 'order',
            'include_private', 'include_groups', 'include_channels',
            'include_archived', 'include_muted', 'match_all',
            'created_at', 'updated_at', 'chats_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_chats_count(self, obj):
        return obj.chats.count()


class ChatFolderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания папки"""
    chat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ChatFolder
        fields = [
            'name', 'icon', 'color', 'order',
            'include_private', 'include_groups', 'include_channels',
            'include_archived', 'include_muted', 'match_all',
            'chat_ids'
        ]
    
    def create(self, validated_data):
        chat_ids = validated_data.pop('chat_ids', [])
        folder = ChatFolder.objects.create(**validated_data)
        
        # Добавляем чаты в папку
        for chat_id in chat_ids:
            # Определяем тип чата и добавляем
            if GroupChat.objects.filter(id=chat_id).exists():
                ChatFolderChat.objects.create(
                    folder=folder,
                    group_chat_id=chat_id
                )
            elif PrivateChat.objects.filter(id=chat_id).exists():
                ChatFolderChat.objects.create(
                    folder=folder,
                    private_chat_id=chat_id
                )
        
        return folder


class ChatFolderReorderSerializer(serializers.Serializer):
    """Сериализатор для изменения порядка папок"""
    folder_ids = serializers.ListField(
        child=serializers.IntegerField()
    )


# ==================== ЖУРНАЛ БЕЗОПАСНОСТИ ====================

class SecurityLogSerializer(serializers.ModelSerializer):
    """Сериализатор журнала безопасности"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SecurityLog
        fields = [
            'id', 'user', 'user_username', 'action', 'action_display',
            'ip_address', 'user_agent', 'device_info', 'location',
            'details', 'is_suspicious', 'was_notified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ==================== НАСТРОЙКИ ГРУППЫ ====================

class GroupChatSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор кэшированных настроек группы"""
    
    class Meta:
        model = GroupChatSettings
        fields = [
            'id', 'chat', 'members_count', 'online_count', 'messages_count',
            'last_activity_at', 'last_message_at', 'permissions_cache',
            'daily_messages', 'weekly_active', 'cache_updated_at'
        ]
        read_only_fields = ['id', 'cache_updated_at']


# ==================== НАСТРОЙКИ ЛИЧНОГО ЧАТА ====================

class PrivateChatSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор персональных настроек личного чата"""
    custom_avatar_url = serializers.SerializerMethodField()
    is_muted = serializers.ReadOnlyField()
    
    class Meta:
        model = PrivateChatSettings
        fields = [
            'id', 'chat', 'user',
            'custom_name', 'custom_avatar', 'custom_avatar_url',
            'notifications_enabled', 'sound_enabled', 'vibration_enabled',
            'show_preview', 'show_popup',
            'muted_until', 'is_muted',
            'is_archived', 'is_pinned', 'is_hidden', 'is_blocked',
            'auto_delete_after', 'folder',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.custom_avatar.url)
            return obj.custom_avatar.url
        return None


# ==================== ЗАКРЕПЛЁННЫЕ СООБЩЕНИЯ ====================

class MessagePinSerializer(serializers.ModelSerializer):
    """Сериализатор закреплённого сообщения"""
    message = MessageSerializer(read_only=True)
    pinned_by_username = serializers.CharField(source='pinned_by.username', read_only=True)
    
    class Meta:
        model = MessagePin
        fields = [
            'id', 'message', 'pinned_by', 'pinned_by_username',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ==================== АНАЛИТИКА ЧАТА ====================

class ChatAnalyticsSerializer(serializers.Serializer):
    """Сериализатор аналитики чата"""
    activity = serializers.DictField()
    members = serializers.DictField()
    content = serializers.DictField()
    engagement_score = serializers.FloatField()


# ==================== ЭКСПОРТ/ИМПОРТ НАСТРОЕК ====================

class SettingsExportSerializer(serializers.Serializer):
    """Сериализатор экспорта настроек"""
    version = serializers.CharField()
    exported_at = serializers.DateTimeField()
    private_chats = serializers.ListField()
    group_chats = serializers.ListField()
    folders = serializers.ListField()
    themes = serializers.ListField()
    wallpapers = serializers.ListField()


class SettingsImportSerializer(serializers.Serializer):
    """Сериализатор импорта настроек"""
    data = SettingsExportSerializer()


# ==================== МАССОВЫЕ ОПЕРАЦИИ ====================

class BulkMessageDeleteSerializer(serializers.Serializer):
    """Сериализатор массового удаления сообщений"""
    message_ids = serializers.ListField(
        child=serializers.IntegerField()
    )


class BulkMembersAddSerializer(serializers.Serializer):
    """Сериализатор массового добавления участников"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField()
    )


class BulkMembersRemoveSerializer(serializers.Serializer):
    """Сериализатор массового удаления участников"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
