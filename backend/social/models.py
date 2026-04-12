from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
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

    # Ответ на конкретный комментарий (для цепочек ответов в стиле Telegram)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='answer_to')

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
            models.Index(fields=['reply_to', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.content_object}"

    @property
    def is_reply(self):
        return self.parent is not None

    def can_edit(self, user):
        """Проверить, может ли пользователь редактировать комментарий"""
        if not user.is_authenticated:
            return False
        if self.author != user:
            return False
        # Ограничение по времени: 10 минут
        if (timezone.now() - self.created_at).total_seconds() > 600:
            return False
        return True

    def can_delete(self, user):
        """Проверить, может ли пользователь удалить комментарий"""
        if not user.is_authenticated:
            return False
        if self.author == user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        return False


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

    TYPE_CHOICES = [
        ('text', 'Текстовый'),
        ('image', 'С изображением'),
        ('video', 'С видео'),
        ('playlist', 'С плейлистом'),
        ('anime', 'Об аниме'),
        ('repost', 'Репост'),
        ('system', 'Системный'),
    ]

    STATUS_CHOICES = [
        ('published', 'Опубликован'),
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('moderated', 'На модерации'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Публично'),
        ('followers', 'Только подписчики'),
        ('friends', 'Только друзья'),
        ('private', 'Только я'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    # Заголовок
    title = models.CharField(max_length=200, blank=True)

    # Тип поста
    post_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')

    # Статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')

    # Видимость
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')

    # Контент
    text = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='posts/videos/', null=True, blank=True)

    # Привязка к аниме (опционально)
    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    anime_rating = models.IntegerField(null=True, blank=True)  # Оценка автора (1-10)

    # Привязка к плейлисту
    playlist = models.ForeignKey('playlists.Playlist', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    # Привязка к Shorts (Reactor)
    reactor_post = models.ForeignKey('reactor.ReactorPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='feed_posts')

    # Группа (если пост в группе)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    # Репост
    original_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reposts_of')
    repost_comment = models.TextField(blank=True)  # Комментарий при репосте

    # Системный тип поста
    system_type = models.CharField(max_length=50, blank=True)  # level_up, contest_win, etc.

    # Статистика
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    reposts_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)

    # Статус
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_spoiler = models.BooleanField(default=False)
    spoiler_description = models.CharField(max_length=255, blank=True)  # Текстовое описание спойлера
    spoiler_for = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='spoiler_posts')

    # Настройки
    allow_comments = models.BooleanField(default=True)

    # Редактирование
    edited_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Избранное
    favorites = GenericRelation('social.Favorite', related_query_name='posts')

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
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['visibility', 'created_at']),
            models.Index(fields=['post_type', 'created_at']),
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

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать пост"""
        if self.author != user:
            return False
        # Редактирование доступно только первые 5 минут
        time_limit = timezone.now() - timezone.timedelta(minutes=5)
        return self.created_at > time_limit

    def can_delete(self, user):
        """Проверяет, может ли пользователь удалить пост"""
        return self.author == user

    def can_like(self, user):
        """Проверяет, может ли пользователь лайкнуть пост"""
        if self.post_type == 'system':
            return False
        return True

    def can_dislike(self, user):
        """Проверяет, может ли пользователь дизлайкнуть пост"""
        return self.can_like(user)

    def is_liked_by(self, user):
        """Проверяет, лайкнул ли пользователь пост"""
        if not user.is_authenticated:
            return False
        return PostLike.objects.filter(user=user, post=self).exists()

    def is_disliked_by(self, user):
        """Проверяет, дизлайкнул ли пользователь пост"""
        if not user.is_authenticated:
            return False
        return PostDislike.objects.filter(user=user, post=self).exists()

    def is_reposted_by(self, user):
        """Проверяет, зарепостил ли пользователь пост"""
        if not user.is_authenticated:
            return False
        return Repost.objects.filter(user=user, original_post=self).exists()

    def is_bookmarked_by(self, user):
        """Проверяет, добавил ли пользователь пост в закладки"""
        if not user.is_authenticated:
            return False
        return Bookmark.objects.filter(user=user, post=self).exists()

    def get_content_preview(self, length=500):
        """Получить превью текста поста"""
        if len(self.text) <= length:
            return self.text
        return self.text[:length] + '...'

    def extract_hashtags(self):
        """Извлечь хэштеги из текста"""
        import re
        return re.findall(r'#(\w+)', self.text)

    def extract_mentions(self):
        """Извлечь упоминания из текста"""
        import re
        return re.findall(r'@(\w+)', self.text)


class GroupChat(models.Model):
    """Групповой чат с системой ролей"""

    # Основная информация
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='chat_avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_chats')
    is_public = models.BooleanField(default=False)
    invite_link = models.CharField(max_length=100, unique=True, null=True, blank=True)
    max_members = models.IntegerField(default=200)

    # Связь с аниме (опционально)
    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')

    # Франшиза (franchise discussion)
    franchise_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name='ИД франшизы')
    discussion_type = models.CharField(
        max_length=30, blank=True, default='',
        choices=[('', 'Обычный'), ('anime', 'Обсуждение аниме'), ('franchise', 'Обсуждение франшизы')],
        verbose_name='Тип обсуждения'
    )
    folder_type = models.CharField(
        max_length=30, blank=True, default='groups',
        choices=[('groups', 'Группы'), ('discussions', 'Обсуждения')],
        verbose_name='Папка чатов'
    )

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

    # Статистика
    members_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public']),
            models.Index(fields=['anime']),
        ]

    def __str__(self):
        return f"Группа: {self.name}"

    def update_members_count(self):
        """Обновить счётчик участников"""
        self.members_count = self.members.count()
        self.save(update_fields=['members_count'])


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
        return self.chat.created_by_id == self.user_id if self.chat.created_by_id else False

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
        ordering = ['-last_message_at', '-created_at']
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
    text = models.TextField(blank=True)
    
    # Связь с топиком для franchise discussion (anime_id топика)
    topic_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    media = models.FileField(upload_to='message_media/', null=True, blank=True)
    media_type = models.CharField(max_length=20, blank=True)  # image, video, audio, document, location, post, anime

    # Геолокация
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)

    # Поделиться контентом
    shared_post = models.ForeignKey('Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_playlist = models.ForeignKey('playlists.Playlist', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_shorts = models.ForeignKey('reactor.ReactorPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')

    # Статус сообщения
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')

    # Закрепление сообщения
    is_pinned = models.BooleanField(default=False)
    pinned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pinned_messages')
    pinned_at = models.DateTimeField(null=True, blank=True)

    # Ответ на другое сообщение
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    # Пересылка сообщения
    forwarded_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='forwarded_to')

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
            models.Index(fields=['chat', 'topic_id', 'created_at']),
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


class Follow(models.Model):
    """Подписка пользователя на другого пользователя"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class PostLike(models.Model):
    """Лайк поста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class PostDislike(models.Model):
    """Дизлайк поста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_dislikes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='dislikes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} dislikes post {self.post.id}"


class Repost(models.Model):
    """Репост поста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reposts')
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reposts')
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'original_post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['original_post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reposted {self.original_post.id}"


class Achievement(models.Model):
    """Достижение"""

    CATEGORY_CHOICES = [
        ('basic', 'Основные'),
        ('social', 'Социальные'),
        ('collection', 'Коллекционные'),
        ('contest', 'Конкурсные'),
        ('special', 'Специальные'),
    ]

    LEVEL_CHOICES = [
        ('bronze', 'Бронзовый'),
        ('silver', 'Серебряный'),
        ('gold', 'Золотой'),
        ('legendary', 'Легендарный'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievements/icons/', null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basic')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='bronze')

    # Условия получения
    condition_type = models.CharField(max_length=50)  # posts_count, followers_count, etc.
    condition_value = models.IntegerField(default=0)

    # Статистика
    unlocked_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'level', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class UserAchievement(models.Model):
    """Полученное достижение"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='unlocked_by')

    progress = models.IntegerField(default=0)  # Прогресс для незавершённых
    is_unlocked = models.BooleanField(default=False)

    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at', '-progress']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UploadedFile(models.Model):
    """Загруженные файлы для чатов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')

    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=20)  # image, video, document
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # в байтах
    mime_type = models.CharField(max_length=100)

    # Для изображений
    thumbnail = models.ImageField(upload_to='uploads/thumbnails/', null=True, blank=True)

    # Метаданные
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # для видео в секундах

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
        ]

    def __str__(self):
        return f"{self.file_name} by {self.user.username}"


class ChatInvite(models.Model):
    """Приглашение в групповой чат по ссылке"""

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='invites')
    token = models.CharField(max_length=100, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invites')

    # Ограничения
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(default=None, null=True, blank=True)  # None = безлимит
    uses_count = models.IntegerField(default=0)

    # Статус
    is_active = models.BooleanField(default=True)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['chat', 'is_active']),
        ]

    def __str__(self):
        return f"Invite for {self.chat.name} ({self.token})"

    def is_valid(self):
        """Проверка валидности приглашения"""
        if not self.is_active:
            return False

        if self.expires_at and timezone.now() > self.expires_at:
            return False

        if self.max_uses and self.uses_count >= self.max_uses:
            return False

        return True

    def use(self):
        """Использовать приглашение"""
        if not self.is_valid():
            raise ValueError("Invite is not valid")

        self.uses_count += 1
        self.save(update_fields=['uses_count', 'updated_at'])


class Reaction(models.Model):
    """Реакция на сообщение (эмодзи)"""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    emoji = models.CharField(max_length=50)  # Эмодзи реакции

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"


class Attachment(models.Model):
    """Вложение к сообщению"""

    ATTACHMENT_TYPES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('audio', 'Аудио'),
        ('file', 'Файл'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)

    # Файл
    file = models.FileField(upload_to='attachments/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # в байтах
    mime_type = models.CharField(max_length=100)

    # Миниатюра (для изображений и видео)
    thumbnail = models.ImageField(upload_to='attachments/thumbnails/', null=True, blank=True)

    # Метаданные для изображений/видео
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # для аудио/видео в секундах

    # Время загрузки
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['message', 'uploaded_at']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.file_name}"


class EmailLog(models.Model):
    """Лог email-уведомлений"""

    EMAIL_TYPES = [
        ('daily_digest', 'Ежедневный дайджест'),
        ('weekly_digest', 'Еженедельный дайджест'),
        ('mention', 'Упоминание'),
        ('message', 'Новое сообщение'),
        ('system', 'Системное уведомление'),
        ('chat_invite', 'Приглашение в чат'),
    ]

    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)

    # Данные письма
    subject = models.CharField(max_length=255)
    to_email = models.EmailField()
    content = models.TextField(blank=True)  # HTML-контент письма

    # Статус отправки
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Связанные данные (опционально)
    chat_id = models.IntegerField(null=True, blank=True)
    message_id = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_email_type_display()} to {self.to_email} ({self.get_status_display()})"


class Favorite(models.Model):
    """Универсальное избранное"""

    CONTENT_TYPE_CHOICES = [
        ('anime', 'Аниме'),
        ('playlist', 'Плейлист'),
        ('post', 'Пост'),
        ('user', 'Пользователь'),
        ('group', 'Группа'),
        ('reactor_post', 'Reactor пост'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_favorites')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)

    # Полиморфная связь
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_items')
    playlist = models.ForeignKey('playlists.Playlist', on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_items')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_items')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_by_users')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_items')
    reactor_post = models.ForeignKey('reactor.ReactorPost', on_delete=models.CASCADE, null=True, blank=True, related_name='favorited_items')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'content_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} favorited {self.content_type}"


class ChatFolder(models.Model):
    """Папка для чатов пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_folders')

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='📁')  # Эмодзи иконка
    color = models.CharField(max_length=7, default='#7c4dff')  # HEX цвет
    position = models.IntegerField(default=0)

    # Правила автоматического добавления чатов
    include_private = models.BooleanField(default=False)
    include_groups = models.BooleanField(default=False)
    include_archived = models.BooleanField(default=False)
    include_pinned = models.BooleanField(default=False)

    # Системная папка (нельзя удалить)
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"Папка {self.name} пользователя {self.user.username}"


class ChatFolderChat(models.Model):
    """Связь чата с папкой"""

    folder = models.ForeignKey(ChatFolder, on_delete=models.CASCADE, related_name='chats')
    chat_id = models.IntegerField()  # ID чата (группового или личного)
    chat_type = models.CharField(max_length=20)  # 'group' или 'private'

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['folder', 'chat_id']
        ordering = ['-added_at']

    def __str__(self):
        return f"Чат {self.chat_id} в папке {self.folder.name}"


# ==================== FEED MODELS ====================

class PostMedia(models.Model):
    """Медиафайлы поста (галерея изображений)"""

    TYPE_CHOICES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='image')

    # Файл
    file = models.FileField(upload_to='posts/media/')
    url = models.URLField(blank=True)  # Внешний URL

    # Миниатюра (для видео)
    thumbnail = models.ImageField(upload_to='posts/media/thumbnails/', null=True, blank=True)

    # Подпись
    caption = models.CharField(max_length=500, blank=True)

    # Порядок в галерее
    order = models.IntegerField(default=0)

    # Метаданные
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # для видео в секундах
    file_size = models.BigIntegerField(null=True, blank=True)  # в байтах
    mime_type = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['post', 'order']),
        ]

    def __str__(self):
        return f"Media for post {self.post.id} (#{self.order})"


class PostAttachment(models.Model):
    """Прикреплённый контент к посту"""

    CONTENT_TYPE_CHOICES = [
        ('playlist', 'Плейлист'),
        ('anime', 'Аниме'),
        ('shorts', 'Shorts'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)

    # ID прикреплённого объекта
    object_id = models.PositiveIntegerField()

    # Дополнительные данные (JSON)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'content_type']),
        ]

    def __str__(self):
        return f"{self.content_type} attachment for post {self.post.id}"


class PostComment(models.Model):
    """Комментарий к посту (отдельная модель для ленты)"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')

    # Родительский комментарий (для ответов)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    # Текст комментария
    content = models.TextField()

    # Статус
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Статистика
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)

    # Для быстрых запросов вложенности
    path = models.CharField(max_length=500, blank=True)  # материализованный путь
    level = models.IntegerField(default=0)  # уровень вложенности (0 - корневой)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['post', 'path']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"

    @property
    def is_reply(self):
        return self.parent is not None


class PostCommentLike(models.Model):
    """Лайк комментария к посту"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_likes')
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class PostCommentDislike(models.Model):
    """Дизлайк комментария к посту"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_dislikes')
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='dislikes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} dislikes comment {self.comment.id}"


class FeedView(models.Model):
    """Просмотр поста в ленте"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_views')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed post {self.post.id}"


class Bookmark(models.Model):
    """Закладка на пост"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')

    # Папка закладок
    folder = models.CharField(max_length=100, blank=True)  # 'watch_later', 'favorite', 'recipes' и т.д.

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'folder']),
        ]

    def __str__(self):
        return f"{self.user.username} bookmarked post {self.post.id}"


class Report(models.Model):
    """Жалоба на контент"""

    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('copyright', 'Нарушение авторских прав'),
        ('harassment', 'Оскорбления / травля'),
        ('inappropriate', 'Неприемлемый контент (18+)'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('resolved', 'Рассмотрено'),
        ('rejected', 'Отклонено'),
    ]

    CONTENT_TYPE_CHOICES = [
        ('post', 'Пост'),
        ('comment', 'Комментарий'),
        ('user', 'Пользователь'),
    ]

    # Кто жалуется
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')

    # Тип контента и ID
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.PositiveIntegerField()

    # Причина
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)

    # Дополнительный комментарий
    comment = models.TextField(blank=True)

    # Статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Модератор
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Report by {self.reporter.username}: {self.reason}"


class Hashtag(models.Model):
    """Хэштег для постов"""

    name = models.CharField(max_length=100, unique=True)
    posts_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posts_count', 'name']

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    """Связь поста с хэштегами"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hashtag_links')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='post_links')

    class Meta:
        unique_together = ['post', 'hashtag']
        indexes = [
            models.Index(fields=['hashtag', 'post']),
        ]


class UserMention(models.Model):
    """Упоминание пользователя в посте"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mentions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_in_posts')
    is_notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['user', 'is_notified']),
        ]

    def __str__(self):
        return f"{self.user.username} mentioned in post {self.post.id}"


class UserPostHidden(models.Model):
    """Скрытый пост из ленты пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hidden_for_users')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} hid post {self.post.id}"


class UserPostNotInterested(models.Model):
    """Посты, отмеченные пользователем как неинтересные (для рекомендаций)"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='not_interested_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='not_interested_for_users')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} not interested in post {self.post.id}"


class UserNotificationSettings(models.Model):
    """Настройки уведомлений для ленты"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_notification_settings')

    # Уведомления о лайках
    notify_likes = models.BooleanField(default=True)

    # Уведомления о комментариях
    notify_comments = models.BooleanField(default=True)

    # Уведомления об упоминаниях (всегда включены, но поле для возможности отключения)
    notify_mentions = models.BooleanField(default=True)

    # Email дайджест
    email_digest = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Никогда'),
            ('daily', 'Раз в день'),
            ('weekly', 'Раз в неделю'),
        ],
        default='never'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User notification settings'

    def __str__(self):
        return f"Notification settings for {self.user.username}"

    @classmethod
    def get_or_create_settings(cls, user):
        """Получить или создать настройки для пользователя"""
        settings, created = cls.objects.get_or_create(user=user)
        return settings


class UserNotInterested(models.Model):
    """Пользователи, отмеченные как неинтересные (скрытые профили)"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='not_interested_users')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_by_users')

    # Причина (опционально)
    reason = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'target_user']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} not interested in {self.target_user.username}"


class Favorite(models.Model):
    """Избранное (универсальное для любого контента)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_favorites')

    # Полиморфная связь
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Папка для организации (опционально)
    folder = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} favorited {self.content_type.model}#{self.object_id}"


# Импорт дополнительных моделей для системы чатов
from .models_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    ChatTopic, UserGlobalChatStyle
)
