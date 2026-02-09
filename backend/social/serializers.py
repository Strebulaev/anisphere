from rest_framework import serializers
from django.db.models import Q
from .models import Comment, Group, GroupMembership, Post, ChatSettings, Message, Contest, ContestEntry, ContestVote
from .models import GroupChat, ChatRole, ChatMember, ChatAdminLog, PrivateChat, MessageReadStatus, PrivateChatUserSettings
from users.models import User


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.ImageField(source='author.avatar', read_only=True)
    replies_count = serializers.SerializerMethodField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'author_username', 'author_avatar',
            'text', 'parent', 'is_reply', 'replies_count',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_replies_count(self, obj):
        if hasattr(obj, 'replies'):
            return obj.replies.filter(is_deleted=False).count()
        return 0


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text', 'parent', 'content_type', 'object_id']

    def validate(self, data):
        # Проверяем, что object_id существует для указанного content_type
        content_type = data.get('content_type')
        object_id = data.get('object_id')

        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                model_class.objects.get(pk=object_id)
            except model_class.DoesNotExist:
                raise serializers.ValidationError("Object does not exist.")

        # Проверяем, что родительский комментарий существует и принадлежит тому же объекту
        parent = data.get('parent')
        if parent:
            if parent.content_type != content_type or parent.object_id != object_id:
                raise serializers.ValidationError("Parent comment must be on the same object.")
            if parent.is_reply:
                raise serializers.ValidationError("Cannot reply to a reply.")

        return data


class GroupSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    is_member = serializers.SerializerMethodField()
    is_moderator = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description', 'avatar_url', 'avatar_file',
            'banner_url', 'banner_file', 'is_private', 'creator', 'creator_username',
            'moderators', 'members_count', 'posts_count', 'is_member', 'is_moderator',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'creator', 'members_count', 'posts_count', 'created_at', 'updated_at']

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user).exists()
        return False

    def get_is_moderator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.moderators.filter(pk=request.user.pk).exists() or obj.creator == request.user
        return False


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'description', 'avatar_url', 'banner_url', 'is_private']


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = GroupMembership
        fields = ['id', 'user', 'user_username', 'group', 'group_name', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.ImageField(source='author.avatar', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    media_url = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_avatar', 'text',
            'image_url', 'image_file', 'video_url', 'video_file', 'media_url',
            'anime', 'anime_title', 'group', 'group_name',
            'likes_count', 'comments_count', 'reposts_count', 'is_pinned',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'likes_count', 'comments_count', 'reposts_count', 'created_at', 'updated_at']


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['text', 'image_url', 'image_file', 'video_url', 'video_file', 'anime', 'group']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True)
    reply_text = serializers.CharField(source='reply_to.text', read_only=True)
    is_read = serializers.SerializerMethodField()  # Добавим вычисляемое поле
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'private_chat', 'sender', 'sender_username', 'sender_avatar',
            'text', 'media', 'media_type', 'reply_to', 'reply_text', 'is_read',
            'is_edited', 'edited_at', 'is_deleted', 'deleted_at', 'deleted_by',
            'reactions', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sender', 'is_edited', 'edited_at', 'is_deleted', 
            'deleted_at', 'deleted_by', 'created_at', 'updated_at'
        ]
    
    def get_is_read(self, obj):
        """Проверяем, прочитано ли сообщение текущим пользователем"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return MessageReadStatus.objects.filter(
                message=obj,
                user=request.user
            ).exists()
        return False
    
    def validate(self, data):
        text = data.get('text', '').strip()
        media = data.get('media')
        
        if not text and not media:
            raise serializers.ValidationError(
                "Сообщение должно содержать текст или медиафайл"
            )
        
        return data


class ContestSerializer(serializers.ModelSerializer):
    organizer_username = serializers.CharField(source='organizer.username', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)

    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'description', 'type', 'format', 'status',
            'theme', 'rules', 'prize_1st', 'prize_2nd', 'prize_3rd',
            'announced_at', 'started_at', 'voting_started_at', 'ended_at',
            'organizer', 'organizer_username', 'anime', 'anime_title',
            'entries_count', 'votes_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organizer', 'entries_count', 'votes_count', 'created_at', 'updated_at']


class ContestEntrySerializer(serializers.ModelSerializer):
    participant_username = serializers.CharField(source='participant.username', read_only=True)
    participant_avatar = serializers.ImageField(source='participant.avatar', read_only=True)
    contest_title = serializers.CharField(source='contest.title', read_only=True)

    class Meta:
        model = ContestEntry
        fields = [
            'id', 'contest', 'contest_title', 'participant', 'participant_username', 'participant_avatar',
            'title', 'description', 'image_url', 'image_file', 'video_url', 'video_file',
            'votes_count', 'is_winner', 'winner_place', 'submitted_at', 'updated_at'
        ]
        read_only_fields = ['id', 'participant', 'votes_count', 'is_winner', 'winner_place', 'submitted_at', 'updated_at']


class ContestVoteSerializer(serializers.ModelSerializer):
    voter_username = serializers.CharField(source='voter.username', read_only=True)

    class Meta:
        model = ContestVote
        fields = ['id', 'contest', 'entry', 'voter', 'voter_username', 'vote_type', 'value', 'created_at']
        read_only_fields = ['id', 'voter', 'created_at']


class ChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSettings
        fields = [
            'id', 'user', 'chat', 'notifications_enabled', 'sound_enabled',
            'auto_repeat_enabled', 'repeat_interval', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'chat', 'created_at', 'updated_at']


# Group Chat Serializers
class UserSimpleSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ImageField(source='avatar', read_only=True)
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'avatar_url', 'is_online', 'last_seen']

    def get_is_online(self, obj):
        """Проверяем онлайн статус через Redis"""
        from core.online_status import online_status
        return online_status.is_online(obj.id)

    def get_last_seen(self, obj):
        """Получаем время последнего seen из Redis"""
        from core.online_status import online_status
        user_data = online_status.get_user_data(obj.id)
        if user_data:
            return user_data.get('last_seen')
        return None


class ChatRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRole
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']


class ChatMemberSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    role = ChatRoleSerializer(read_only=True)
    effective_permissions = serializers.JSONField(read_only=True)

    class Meta:
        model = ChatMember
        fields = '__all__'
        read_only_fields = ['joined_at']


class GroupChatCreateSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = GroupChat
        fields = ['name', 'description', 'avatar', 'participants']

    def validate_participants(self, value):
        return value

    def create(self, validated_data):
        participants = validated_data.pop('participants', [])
        avatar = validated_data.pop('avatar', None)

        chat = GroupChat.objects.create(**validated_data)

        if avatar:
            chat.avatar = avatar
            chat.save(update_fields=['avatar'])
        else:
            try:
                self._generate_default_avatar(chat)
            except Exception as e:
                print(f"DEBUG: Ошибка генерации аватарки: {e}")

        # Add creator as admin
        ChatMember.objects.create(
            user=self.context['request'].user,
            chat=chat,
            is_admin=True
        )

        # Add other participants
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

        # Create admin log
        ChatAdminLog.objects.create(
            chat=chat,
            user=self.context['request'].user,
            action='chat_created',
            details={'chat_name': chat.name, 'participants_count': len(participants) + 1}
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
            initials = ['?']

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
        img = Image.new('RGB', (200, 200), bg_color)
        draw = ImageDraw.Draw(img)

        # Рисуем текст
        text = ''.join(initials)[:2]  # Максимум 2 буквы

        try:
            # Пытаемся использовать крупный шрифт
            font = ImageFont.truetype("arial.ttf", 80)
        except Exception:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 80)
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
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Сохраняем как аватарку
        from django.core.files.uploadedfile import InMemoryUploadedFile
        avatar_file = InMemoryUploadedFile(
            buffer,
            None,
            f'{chat.id}_avatar.png',
            'image/png',
            buffer.getbuffer().nbytes,
            None
        )
        chat.avatar.save(f'{chat.id}_avatar.png', avatar_file)
        chat.save(update_fields=['avatar'])


class GroupChatSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    online_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    participants_usernames = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by', 'invite_link']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_participants_usernames(self, obj):
        """Получить список имен участников"""
        return list(obj.members.values_list('user__username', flat=True))

    def get_online_count(self, obj):
        # Количество онлайн участников
        online_members = obj.members.filter(
            user__is_online=True
        ).count()
        return online_members

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return {
                    'is_owner': member.is_owner,
                    'role': ChatRoleSerializer(member.role).data if member.role else None,
                    'custom_title': member.custom_title,
                    'is_admin': member.is_admin
                }
            except ChatMember.DoesNotExist:
                return None
        return None

    def get_user_permissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = obj.members.get(user=request.user)
                return member.effective_permissions
            except ChatMember.DoesNotExist:
                return {}
        return {}

    def get_last_message(self, obj):
        last_message = Message.objects.filter(chat=obj).order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'text': last_message.text,
                'sender': UserSimpleSerializer(last_message.sender).data,
                'created_at': last_message.created_at,
                'is_edited': last_message.is_edited,
                'media_type': last_message.media_type
            }
        return None


class ChatAdminLogSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    target_user = UserSimpleSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ChatAdminLog
        fields = '__all__'
        read_only_fields = ['created_at']


# Private Chat Serializers
class PrivateChatSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    user_settings = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChat
        fields = ['id', 'user1', 'user2', 'created_at', 'last_message_at', 'user1_notifications', 'user2_notifications', 'user1_muted_until', 'user2_muted_until', 'user1_archived', 'user2_archived', 'user1_pinned', 'user2_pinned', 'user1_blocked', 'user2_blocked', 'other_user', 'user_settings', 'unread_count', 'last_message']
        read_only_fields = ['created_at', 'last_message_at']

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
            # Получаем количество непрочитанных сообщений
            last_read = MessageReadStatus.objects.filter(
                user=request.user,
                message__private_chat=obj
            ).order_by('-read_at').first()

            if last_read:
                unread_count = Message.objects.filter(
                    private_chat=obj,
                    created_at__gt=last_read.read_at
                ).exclude(sender=request.user).count()
            else:
                unread_count = Message.objects.filter(
                    private_chat=obj
                ).exclude(sender=request.user).count()

            return unread_count
        return 0

    def get_last_message(self, obj):
        last_message = Message.objects.filter(private_chat=obj).order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'text': last_message.text,
                'sender': UserSimpleSerializer(last_message.sender).data,
                'created_at': last_message.created_at,
                'is_edited': last_message.is_edited,
                'media_type': last_message.media_type
            }
        return None


class PrivateChatUserSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор персональных настроек личного чата"""
    custom_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChatUserSettings
        fields = ['id', 'chat', 'custom_name', 'custom_avatar', 'custom_avatar_url', 'notifications_enabled', 'updated_at']
        read_only_fields = ['id', 'chat', 'updated_at']

    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.custom_avatar.url)
            return obj.custom_avatar.url
        return None

    def create(self, validated_data):
        # Проверяем, что чат существует и пользователь в нем
        chat = validated_data.get('chat')
        user = validated_data.get('user')

        if not chat.members.filter(id=user.id).exists():
            if user != chat.user1 and user != chat.user2:
                raise serializers.ValidationError("Вы не участник этого чата")

        # Создаем или обновляем настройки
        settings, created = PrivateChatUserSettings.objects.update_or_create(
            chat=chat,
            user=user,
            defaults=validated_data
        )
        return settings


class GroupChatSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор настроек группового чата (общие для всех)"""
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = ['id', 'name', 'description', 'avatar', 'avatar_url']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)

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
            user=self.context['request'].user,
            action='chat_updated',
            details={'updated_fields': list(validated_data.keys())}
        )

        return instance