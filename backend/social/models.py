from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone
from users.models import User

class Comment(models.Model):
    """Универсальный комментарий для разных типов контента"""

    # Полиморфная связь
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Автор и контент
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.content_object}"

    @property
    def is_reply(self):
        return self.parent is not None


class Group(models.Model):
    """Сообщество/группа"""

    # Основная информация
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    # Фото
    avatar_url = models.URLField(blank=True)
    avatar_file = models.ImageField(upload_to='groups/avatars/', null=True, blank=True)
    banner_url = models.URLField(blank=True)
    banner_file = models.ImageField(upload_to='groups/banners/', null=True, blank=True)

    # Настройки
    is_private = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')

    # Модераторы
    moderators = models.ManyToManyField(User, related_name='moderated_groups', blank=True)

    # Статистика
    members_count = models.IntegerField(default=1)  # + создатель
    posts_count = models.IntegerField(default=0)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Убеждаемся в уникальности slug
            original_slug = self.slug
            counter = 1
            while Group.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def update_members_count(self):
        self.members_count = self.memberships.filter(role='member').count() + 1  # + создатель
        self.save()


class GroupMembership(models.Model):
    """Членство в группе"""

    ROLE_CHOICES = [
        ('member', 'Участник'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class Post(models.Model):
    """Пост в ленте"""

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    # Контент
    text = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='posts/videos/', null=True, blank=True)

    # Привязка к аниме (опционально)
    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    # Группа (если пост в группе)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    # Статистика
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    reposts_count = models.IntegerField(default=0)

    # Статус
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['anime', 'created_at']),
            models.Index(fields=['is_pinned', 'created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author.username}: {self.text[:50]}"

    @property
    def media_url(self):
        """URL для медиа контента"""
        if self.video_file:
            return self.video_file.url
        elif self.image_file:
            return self.image_file.url
        elif self.video_url:
            return self.video_url
        elif self.image_url:
            return self.image_url
        return None


class GroupChat(models.Model):
    """Групповой чат с системой ролей"""

    # Основная информация
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='chat_avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_chats')
    is_public = models.BooleanField(default=False)
    invite_link = models.CharField(max_length=100, unique=True, null=True, blank=True)
    max_members = models.IntegerField(default=200)

    # Настройки чата
    slow_mode_delay = models.IntegerField(default=0)  # в секундах, 0 = отключен
    history_visible = models.BooleanField(default=True)
    can_send_media = models.BooleanField(default=True)
    can_send_stickers = models.BooleanField(default=True)
    can_send_polls = models.BooleanField(default=True)
    can_add_web_page_previews = models.BooleanField(default=True)
    can_change_info = models.BooleanField(default=True)
    can_pin_messages = models.BooleanField(default=True)
    can_invite_users = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"Группа: {self.name}"

    @property
    def members_count(self):
        return self.members.count()


class ChatRole(models.Model):
    """Роли в чате"""

    ROLE_LEVELS = (
        (0, 'Участник'),
        (1, 'Модератор'),
        (2, 'Администратор'),
        (3, 'Владелец'),
    )

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=50)
    level = models.IntegerField(choices=ROLE_LEVELS, default=0)
    color = models.CharField(max_length=7, default='#808080')  # HEX цвет роли

    # Разрешения роли
    can_delete_messages = models.BooleanField(default=False)
    can_ban_users = models.BooleanField(default=False)
    can_pin_messages = models.BooleanField(default=False)
    can_add_new_admins = models.BooleanField(default=False)
    can_remain_anonymous = models.BooleanField(default=False)
    can_manage_chat = models.BooleanField(default=False)
    can_manage_video_chats = models.BooleanField(default=False)
    can_restrict_members = models.BooleanField(default=False)
    can_promote_members = models.BooleanField(default=False)
    can_change_chat_info = models.BooleanField(default=False)
    can_invite_users = models.BooleanField(default=False)
    can_post_messages = models.BooleanField(default=True)
    can_edit_messages = models.BooleanField(default=False)
    can_delete_chat = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['chat', 'name']
        ordering = ['-level', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class ChatMember(models.Model):
    """Участник группового чата с ролью"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_chat_memberships')
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='members')

    role = models.ForeignKey(ChatRole, on_delete=models.SET_NULL, null=True, blank=True)

    # Дополнительные настройки для участника
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    until_date = models.DateTimeField(null=True, blank=True)  # До какого числа участник
    custom_title = models.CharField(max_length=32, blank=True)  # Кастомный заголовок

    # Ограничения для участника
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    can_send_messages = models.BooleanField(default=True)
    can_send_media = models.BooleanField(default=True)
    can_add_reactions = models.BooleanField(default=True)
    can_send_polls = models.BooleanField(default=True)
    can_change_info = models.BooleanField(default=False)
    can_invite_users = models.BooleanField(default=False)
    can_pin_messages = models.BooleanField(default=False)

    # Статус участника
    is_banned = models.BooleanField(default=False)
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banned_users')
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_reason = models.TextField(blank=True)

    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'chat']
        indexes = [
            models.Index(fields=['user', 'chat']),
            models.Index(fields=['is_admin']),
            models.Index(fields=['is_banned']),
        ]

    def __str__(self):
        return f"{self.user.username} в {self.chat.name}"

    @property
    def is_owner(self):
        """Проверка, является ли пользователь владельцем"""
        return self.chat.created_by == self.user

    @property
    def effective_permissions(self):
        """Эффективные разрешения с учетом роли и индивидуальных настроек"""
        permissions = {}

        # Если владелец - все разрешения
        if self.is_owner:
            return {field.name: True for field in ChatRole._meta.fields if field.name.startswith('can_')}

        # Берем разрешения из роли
        if self.role:
            for field in ChatRole._meta.fields:
                if field.name.startswith('can_'):
                    permissions[field.name] = getattr(self.role, field.name, False)

        # Переопределяем индивидуальными настройками
        for field in self._meta.fields:
            if field.name.startswith('can_'):
                permissions[field.name] = getattr(self, field.name, False)

        return permissions


class ChatAdminLog(models.Model):
    """Лог действий администраторов"""

    ACTION_CHOICES = (
        ('chat_created', 'Чат создан'),
        ('chat_updated', 'Настройки чата изменены'),
        ('member_joined', 'Участник присоединился'),
        ('member_left', 'Участник вышел'),
        ('member_banned', 'Участник забанен'),
        ('member_unbanned', 'Участник разбанен'),
        ('member_promoted', 'Участник повышен'),
        ('member_demoted', 'Участник понижен'),
        ('message_deleted', 'Сообщение удалено'),
        ('message_pinned', 'Сообщение закреплено'),
        ('message_unpinned', 'Сообщение откреплено'),
        ('invite_link_created', 'Пригласительная ссылка создана'),
        ('invite_link_revoked', 'Пригласительная ссылка отозвана'),
        ('slow_mode_changed', 'Режим медленной отправки изменен'),
    )

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='admin_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_actions')
    message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict)  # Детали действия
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} в {self.chat.name}"


class PrivateChat(models.Model):
    """Личный чат между двумя пользователями"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    # Настройки для каждого пользователя
    user1_notifications = models.BooleanField(default=True)
    user2_notifications = models.BooleanField(default=True)
    user1_muted_until = models.DateTimeField(null=True, blank=True)
    user2_muted_until = models.DateTimeField(null=True, blank=True)
    user1_archived = models.BooleanField(default=False)
    user2_archived = models.BooleanField(default=False)
    user1_pinned = models.BooleanField(default=False)
    user2_pinned = models.BooleanField(default=False)
    user1_blocked = models.BooleanField(default=False)
    user2_blocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user1', 'user2']
        indexes = [
            models.Index(fields=['user1', 'last_message_at']),
            models.Index(fields=['user2', 'last_message_at']),
            models.Index(fields=['user1', 'user1_pinned']),
            models.Index(fields=['user2', 'user2_pinned']),
        ]

    def __str__(self):
        return f"Личный чат: {self.user1.username} ↔ {self.user2.username}"

    def other_user(self, current_user):
        """Получить другого пользователя в чате"""
        if current_user == self.user1:
            return self.user2
        return self.user1

    def get_user_settings(self, user):
        """Получить настройки для конкретного пользователя"""
        if user == self.user1:
            return {
                'notifications': self.user1_notifications,
                'muted_until': self.user1_muted_until,
                'archived': self.user1_archived,
                'pinned': self.user1_pinned,
                'blocked': self.user1_blocked,
            }
        else:
            return {
                'notifications': self.user2_notifications,
                'muted_until': self.user2_muted_until,
                'archived': self.user2_archived,
                'pinned': self.user2_pinned,
                'blocked': self.user2_blocked,
            }

    def update_user_settings(self, user, **kwargs):
        """Обновить настройки для пользователя"""
        if user == self.user1:
            for key, value in kwargs.items():
                setattr(self, f'user1_{key}', value)
        else:
            for key, value in kwargs.items():
                setattr(self, f'user2_{key}', value)
        self.save()


class Message(models.Model):
    """Общая модель сообщения для всех типов чатов"""
    chat = models.ForeignKey('GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='group_messages')
    private_chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='private_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    media = models.FileField(upload_to='message_media/', null=True, blank=True)
    media_type = models.CharField(max_length=20, blank=True)  # image, video, audio, document

    # Статус сообщения
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')

    # Ответ на другое сообщение
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    # Реакции
    reactions = models.JSONField(default=dict)  # { '❤️': [user_ids], '😂': [user_ids] }

    # Системная информация
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]

    def __str__(self):
        return f"Сообщение от {self.sender.username}"

    @property
    def parent_chat(self):
        """Получить родительский чат (групповой или личный)"""
        return self.chat or self.private_chat

    def can_edit(self, user):
        """Может ли пользователь редактировать сообщение"""
        if self.is_deleted:
            return False

        # Только отправитель может редактировать
        if self.sender != user:
            return False

        # Проверка времени (например, можно редактировать только 48 часов)
        time_limit = timezone.now() - timezone.timedelta(hours=48)
        return self.created_at > time_limit

    def can_delete(self, user):
        """Может ли пользователь удалить сообщение"""
        if self.is_deleted:
            return False

        # Отправитель может удалить всегда
        if self.sender == user:
            return True

        # В групповых чатах проверяем разрешения
        if self.chat:
            try:
                member = self.chat.members.get(user=user)
                return member.effective_permissions.get('can_delete_messages', False)
            except ChatMember.DoesNotExist:
                return False

        return False


class MessageReadStatus(models.Model):
    """Статус прочтения сообщений"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user.username} прочел сообщение {self.message.id}"


class ChatTypingStatus(models.Model):
    """Статус печатания в чате"""
    chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, related_name='typing_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='typing_statuses')
    typed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['chat', 'user']
        indexes = [
            models.Index(fields=['chat', 'typed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} печатает в чате {self.chat.id}"


class ChatSettings(models.Model):
    """Настройки чата для пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_settings')
    chat = models.ForeignKey('GroupChat', on_delete=models.CASCADE, related_name='user_settings')

    # Настройки уведомлений
    notifications_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    # Настройки авто-повторов
    auto_repeat_enabled = models.BooleanField(default=False)
    repeat_interval = models.IntegerField(default=1000)  # в миллисекундах

    # Блокировка чата
    is_blocked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'chat']

    def __str__(self):
        return f"Settings for {self.user.username} in {self.chat}"


class PrivateChatUserSettings(models.Model):
    """Персональные настройки личного чата для пользователя"""

    chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, related_name='user_settings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chat_settings')

    # Кастомное название чата (только для этого пользователя)
    custom_name = models.CharField(max_length=255, blank=True)

    # Кастомная аватарка (только для этого пользователя)
    custom_avatar = models.ImageField(upload_to='private_chat_avatars/', null=True, blank=True)

    # Настройки уведомлений
    notifications_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['chat', 'user']

    def __str__(self):
        return f"Settings for {self.user.username} in private chat {self.chat.id}"


class Contest(models.Model):
    """Конкурс"""

    TYPE_CHOICES = [
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('seasonal', 'Сезонный'),
        ('special', 'Специальный'),
    ]

    FORMAT_CHOICES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('text', 'Текст'),
        ('mixed', 'Смешанный'),
    ]

    STATUS_CHOICES = [
        ('announce', 'Анонс'),
        ('active', 'Активен'),
        ('voting', 'Голосование'),
        ('finished', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]

    # Основная информация
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='weekly')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='image')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='announce')

    # Тема и правила
    theme = models.CharField(max_length=500, blank=True)
    rules = models.TextField(blank=True)

    # Призы
    prize_1st = models.CharField(max_length=500, blank=True)
    prize_2nd = models.CharField(max_length=500, blank=True)
    prize_3rd = models.CharField(max_length=500, blank=True)

    # Даты
    announced_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    voting_started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Организатор
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_contests')

    # Связанное аниме (опционально)
    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='contests')

    # Статистика
    entries_count = models.IntegerField(default=0)
    votes_count = models.IntegerField(default=0)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ContestEntry(models.Model):
    """Участие в конкурсе"""

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='entries')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_entries')

    # Работа
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    # Контент
    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to='contests/entries/images/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='contests/entries/videos/', null=True, blank=True)

    # Голосование
    votes_count = models.IntegerField(default=0)

    # Статус
    is_winner = models.BooleanField(default=False)
    winner_place = models.IntegerField(null=True, blank=True)  # 1, 2, 3

    # Время
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['contest', 'participant']

    def __str__(self):
        return f"{self.participant.username} in {self.contest.title}"


class ContestVote(models.Model):
    """Голос в конкурсе"""

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='votes')
    entry = models.ForeignKey(ContestEntry, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_votes')

    # Тип голоса
    vote_type = models.CharField(max_length=20, choices=[
        ('like', 'Лайк'),
        ('star', 'Звезда'),
        ('heart', 'Сердце'),
    ], default='like')

    # Значение (для рейтинговых систем)
    value = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['contest', 'entry', 'voter']
        indexes = [
            models.Index(fields=['contest', 'voter']),
        ]

    def __str__(self):
        return f"{self.voter.username} voted for {self.entry}"
