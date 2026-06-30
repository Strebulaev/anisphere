"""
Модели для системы чатов согласно документации CHAT_SETTINGS.md
Полная реализация: обои, темы, шрифты, цвета, роли, модерация, папки и т.д.

ВАЖНО для MySQL: поля с дефолтными значениями содержащими скобки (rgba, etc.)
должны быть null=True или blank=True чтобы избежать ошибки Invalid default value.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import secrets
import string

User = get_user_model()


# ==================== ССЫЛКИ-ПРИГЛАШЕНИЯ ====================

class ChatInviteLink(models.Model):
    """Ссылки-приглашения в групповые чаты"""

    LINK_TYPES = [
        ('primary', 'Основная'),
        ('temporary', 'Временная'),
        ('personal', 'Персональная'),
    ]

    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        related_name='invite_links'
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_invite_links'
    )

    name = models.CharField(max_length=100, blank=True, verbose_name='Название ссылки')
    invite_link = models.CharField(max_length=100, unique=True, verbose_name='Код приглашения')
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default='temporary')

    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    usage_limit = models.IntegerField(null=True, blank=True, verbose_name='Лимит использований')
    usage_count = models.IntegerField(default=0, verbose_name='Количество использований')

    is_revoked = models.BooleanField(default=False, verbose_name='Отозвана')
    is_primary = models.BooleanField(default=False, verbose_name='Основная ссылка')

    # Для персональных ссылок
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='personal_invite_links', verbose_name='Целевой пользователь'
    )
    auto_assign_role = models.ForeignKey(
        'social.ChatRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invite_links',
        verbose_name='Автоматически назначаемая роль'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ссылка-приглашение'
        verbose_name_plural = 'Ссылки-приглашения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invite_link']),
            models.Index(fields=['chat', 'is_revoked']),
        ]

    def __str__(self):
        return f"Приглашение в {self.chat.name}: {self.invite_link}"

    def save(self, *args, **kwargs):
        if not self.invite_link:
            self.invite_link = self.generate_invite_link()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_invite_link(length=22):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @property
    def is_valid(self):
        if self.is_revoked:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


# ==================== ОБОИ ЧАТОВ ====================

class ChatWallpaper(models.Model):
    """Обои для чатов - привязываются к пользователю + чату"""

    WALLPAPER_TYPES = [
        ('solid', 'Сплошной цвет'),
        ('gradient', 'Градиент'),
        ('pattern', 'Паттерн'),
        ('image', 'Изображение'),
    ]

    PATTERN_TYPES = [
        ('dots', 'Точки'),
        ('grid', 'Сетка'),
        ('waves', 'Волны'),
        ('geometry', 'Геометрия'),
        ('hexagon', 'Шестиугольники'),
        ('triangles', 'Треугольники'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_wallpapers'
    )
    chat = models.ForeignKey(
        'social.GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='user_wallpapers'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='user_wallpapers'
    )

    wallpaper_type = models.CharField(max_length=20, choices=WALLPAPER_TYPES, default='solid')
    wallpaper_color = models.CharField(max_length=7, default='#1a1a2e')
    wallpaper_color2 = models.CharField(max_length=7, blank=True, default='')

    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPES, blank=True, default='')
    pattern_color = models.CharField(max_length=7, blank=True, default='')
    pattern_opacity = models.IntegerField(default=20)

    wallpaper_intensity = models.IntegerField(default=100)
    wallpaper_blur = models.IntegerField(default=0)
    wallpaper_motion = models.CharField(
        max_length=20,
        choices=[('none', 'Нет'), ('parallax', 'Параллакс')],
        default='none'
    )
    gradient_angle = models.IntegerField(default=135)
    wallpaper_image = models.ImageField(upload_to='chat_wallpapers/', null=True, blank=True)

    is_preset = models.BooleanField(default=False)
    preset_name = models.CharField(max_length=100, blank=True)
    preset_category = models.CharField(max_length=50, blank=True)

    dark_variant_color = models.CharField(max_length=7, blank=True, default='')
    light_variant_color = models.CharField(max_length=7, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Обои чата'
        verbose_name_plural = 'Обои чатов'
        indexes = [
            models.Index(fields=['user', 'chat']),
            models.Index(fields=['user', 'private_chat']),
            models.Index(fields=['is_preset']),
        ]

    def __str__(self):
        if self.is_preset:
            return f"Пресет: {self.preset_name}"
        if self.chat:
            return f"Обои {self.user.username if self.user else '?'} для {self.chat.name}"
        if self.private_chat:
            return f"Обои личного чата {self.private_chat.id}"
        return f"Обои {self.user.username if self.user else '?'}"

    def to_css(self):
        if self.wallpaper_type == 'solid':
            return f'background-color: {self.wallpaper_color};'
        elif self.wallpaper_type == 'gradient':
            c2 = self.wallpaper_color2 or self.wallpaper_color
            return f'background: linear-gradient({self.gradient_angle}deg, {self.wallpaper_color}, {c2});'
        elif self.wallpaper_type == 'image' and self.wallpaper_image:
            blur = f'filter: blur({self.wallpaper_blur}px);' if self.wallpaper_blur else ''
            return f'background-image: url({self.wallpaper_image.url}); background-size: cover; {blur}'
        return f'background-color: {self.wallpaper_color};'


# ==================== ТЕМЫ ОФОРМЛЕНИЯ ====================

class ChatTheme(models.Model):
    """Полная тема оформления чата.

    MySQL-совместима: поля с non-trivial дефолтами (содержащие скобки)
    объявлены как blank=True и null=True и получают значение в save().
    """

    BUBBLE_STYLES = [
        ('modern', 'Современный'),
        ('classic', 'Классический'),
        ('rounded', 'Округлый'),
        ('flat', 'Плоский'),
        ('minimal', 'Минималистичный'),
    ]
    FONT_SIZES = [
        ('small', 'Маленький'), ('medium', 'Средний'),
        ('large', 'Большой'), ('xlarge', 'Очень большой'),
    ]
    FONT_FAMILIES = [
        ('system', 'Системный'), ('inter', 'Inter'),
        ('roboto', 'Roboto'), ('nunito', 'Nunito'),
        ('montserrat', 'Montserrat'), ('opensans', 'Open Sans'),
    ]
    MESSAGE_ANIMATIONS = [
        ('slide', 'Скольжение'), ('fade', 'Затухание'),
        ('pop', 'Появление'), ('none', 'Без анимации'),
    ]
    REACTION_ANIMATIONS = [
        ('bounce', 'Прыжок'), ('scale', 'Масштаб'), ('none', 'Без анимации'),
    ]
    TYPING_ANIMATIONS = [
        ('dots', 'Точки'), ('wave', 'Волна'), ('pulse', 'Пульс'),
    ]
    TIME_FORMATS = [('12h', '12 часов'), ('24h', '24 часа')]
    EMOJI_SETS = [
        ('default', 'По умолчанию'), ('twitter', 'Twitter'),
        ('google', 'Google'), ('samsung', 'Samsung'), ('anime', 'Аниме'),
    ]
    EMOJI_SIZES = [('small', 'Маленький'), ('medium', 'Средний'), ('large', 'Большой')]
    SCROLL_ANIMATIONS = [
        ('smooth', 'Плавная'), ('instant', 'Мгновенная'), ('auto', 'Автоматическая'),
    ]

    # Привязка
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_themes')
    chat = models.ForeignKey(
        'social.GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='user_themes'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='user_themes'
    )

    theme = models.CharField(max_length=50, default='default')

    # Цвета сообщений - только HEX, MySQL-безопасно
    message_color_mine = models.CharField(max_length=7, default='#3b82f6')
    message_color_other = models.CharField(max_length=7, default='#2a2a3e')
    message_text_color_mine = models.CharField(max_length=7, default='#ffffff')
    message_text_color_other = models.CharField(max_length=7, default='#e2e8f0')

    # Стиль пузырей
    bubble_style = models.CharField(max_length=20, choices=BUBBLE_STYLES, default='modern')
    bubble_border_radius = models.IntegerField(default=18)
    bubble_padding_x = models.IntegerField(default=12)
    bubble_padding_y = models.IntegerField(default=8)
    bubble_shadow = models.BooleanField(default=False)

    # bubble_shadow_color содержит rgba() - НЕ задаём default на уровне БД
    # Используем blank=True + null=True, значение устанавливаем в save()
    bubble_shadow_color = models.CharField(max_length=30, blank=True, null=True)

    # Шрифты
    font_family = models.CharField(max_length=30, choices=FONT_FAMILIES, default='system')
    font_size = models.CharField(max_length=10, choices=FONT_SIZES, default='medium')
    font_size_px = models.IntegerField(default=14)
    font_weight = models.IntegerField(default=400)
    line_height = models.FloatField(default=1.5)

    # Время
    time_format = models.CharField(max_length=5, choices=TIME_FORMATS, default='24h')
    show_seconds = models.BooleanField(default=False)

    # time_color содержит rgba() - НЕ задаём default на уровне БД
    time_color = models.CharField(max_length=30, blank=True, null=True)

    # Цвета интерфейса - только HEX, MySQL-безопасно
    background_color = models.CharField(max_length=7, default='#0f0f1a')
    header_color = models.CharField(max_length=7, default='#1a1a2e')
    input_color = models.CharField(max_length=7, default='#1e1e32')
    input_text_color = models.CharField(max_length=7, default='#e2e8f0')
    accent_color = models.CharField(max_length=7, default='#3b82f6')
    link_color = models.CharField(max_length=7, default='#60a5fa')

    # Анимации
    message_animation = models.CharField(max_length=20, choices=MESSAGE_ANIMATIONS, default='slide')
    reaction_animation = models.CharField(max_length=20, choices=REACTION_ANIMATIONS, default='bounce')
    typing_animation = models.CharField(max_length=20, choices=TYPING_ANIMATIONS, default='dots')
    scroll_animation = models.CharField(max_length=20, choices=SCROLL_ANIMATIONS, default='smooth')

    # Эмодзи
    emoji_set = models.CharField(max_length=20, choices=EMOJI_SETS, default='default')
    emoji_size = models.CharField(max_length=10, choices=EMOJI_SIZES, default='medium')

    # Дополнительные настройки
    show_avatars = models.BooleanField(default=True)
    show_usernames = models.BooleanField(default=True)
    compact_mode = models.BooleanField(default=False)
    show_read_status = models.BooleanField(default=True)
    show_typing_indicator = models.BooleanField(default=True)
    message_grouping = models.BooleanField(default=True)

    custom_css = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тема чата'
        verbose_name_plural = 'Темы чатов'

    def save(self, *args, **kwargs):
        # Устанавливаем дефолты для rgba-полей если пустые
        if not self.time_color:
            self.time_color = 'rgba(255,255,255,0.5)'
        if not self.bubble_shadow_color:
            self.bubble_shadow_color = 'rgba(0,0,0,0.2)'
        super().save(*args, **kwargs)

    def __str__(self):
        if self.chat:
            return f"Тема {self.user.username} для {self.chat.name}"
        if self.private_chat:
            return f"Тема {self.user.username} для личного чата {self.private_chat.id}"
        return f"Глобальная тема {self.user.username}"

    def to_css_vars(self):
        fs_map = {'small': '12px', 'medium': '14px', 'large': '16px', 'xlarge': '18px'}
        br_map = {'modern': '18px', 'classic': '4px', 'rounded': '24px', 'flat': '8px', 'minimal': '2px'}
        return {
            '--msg-mine-bg': self.message_color_mine,
            '--msg-other-bg': self.message_color_other,
            '--msg-mine-text': self.message_text_color_mine,
            '--msg-other-text': self.message_text_color_other,
            '--chat-bg': self.background_color,
            '--chat-header-bg': self.header_color,
            '--chat-input-bg': self.input_color,
            '--chat-input-text': self.input_text_color,
            '--chat-accent': self.accent_color,
            '--chat-link': self.link_color,
            '--msg-time-color': self.time_color or 'rgba(255,255,255,0.5)',
            '--msg-font-size': fs_map.get(self.font_size, '14px'),
            '--msg-border-radius': br_map.get(self.bubble_style, '18px'),
            '--msg-font-family': self.font_family,
        }


# ==================== НАСТРОЙКИ ЛИЧНОГО ЧАТА ====================

class PrivateChatSettings(models.Model):
    """Персональные настройки пользователя для конкретного личного чата"""

    chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, related_name='settings'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='private_chat_settings_v2'
    )

    custom_name = models.CharField(max_length=255, blank=True)
    custom_avatar = models.ImageField(upload_to='private_chat_avatars/', null=True, blank=True)

    notifications_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    notification_sound = models.CharField(max_length=50, default='default')
    vibration_enabled = models.BooleanField(default=True)
    vibration_type = models.CharField(max_length=20, default='default')
    show_preview = models.BooleanField(default=True)
    show_popup = models.BooleanField(default=True)
    muted_until = models.DateTimeField(null=True, blank=True)

    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)

    auto_delete_enabled = models.BooleanField(default=False)
    auto_delete_after = models.IntegerField(null=True, blank=True)

    folder_id = models.IntegerField(null=True, blank=True)
    tags = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки личного чата'
        verbose_name_plural = 'Настройки личных чатов'
        unique_together = [['chat', 'user']]
        indexes = [
            models.Index(fields=['user', 'is_pinned']),
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'is_hidden']),
        ]

    def __str__(self):
        return f"Настройки {self.user.username} для чата {self.chat.id}"

    @property
    def is_muted(self):
        if not self.muted_until:
            return False
        try:
            from django.utils.dateparse import parse_datetime
            muted_until = self.muted_until
            if isinstance(muted_until, str):
                muted_until = parse_datetime(muted_until)
            if muted_until is None:
                return False
            return muted_until > timezone.now()
        except Exception:
            return False


# ==================== НАСТРОЙКИ УЧАСТНИКА ГРУППЫ ====================

class GroupMemberSettings(models.Model):
    """Персональные настройки пользователя для группового чата"""

    membership = models.OneToOneField(
        'social.ChatMember', on_delete=models.CASCADE, related_name='personal_settings'
    )

    notifications_enabled = models.BooleanField(default=True)
    mentions_only = models.BooleanField(default=False)
    sound_enabled = models.BooleanField(default=True)
    show_preview = models.BooleanField(default=True)
    muted_until = models.DateTimeField(null=True, blank=True)

    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    tags = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки участника группы'
        verbose_name_plural = 'Настройки участников групп'

    @property
    def is_muted(self):
        if not self.muted_until:
            return False
        try:
            from django.utils.dateparse import parse_datetime
            muted_until = self.muted_until
            if isinstance(muted_until, str):
                muted_until = parse_datetime(muted_until)
            if muted_until is None:
                return False
            return muted_until > timezone.now()
        except Exception:
            return False


# ==================== БЛОКИРОВКИ И ОГРАНИЧЕНИЯ ====================

class ChatBan(models.Model):
    chat = models.ForeignKey('social.GroupChat', on_delete=models.CASCADE, related_name='bans')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_bans')
    banned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_bans')
    reason = models.TextField()
    until_date = models.DateTimeField(null=True, blank=True)
    delete_messages = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Блокировка в чате'
        verbose_name_plural = 'Блокировки в чатах'
        unique_together = [['chat', 'user']]
        indexes = [
            models.Index(fields=['chat', 'user']),
            models.Index(fields=['until_date']),
        ]

    def __str__(self):
        return f"{self.user.username} заблокирован в {self.chat.name}"

    @property
    def is_active(self):
        if self.until_date is None:
            return True
        return self.until_date > timezone.now()


class ChatRestriction(models.Model):
    RESTRICTION_TYPES = [
        ('read_only', 'Только чтение'), ('no_media', 'Без медиа'),
        ('no_stickers', 'Без стикеров'), ('no_links', 'Без ссылок'),
        ('no_voice', 'Без голосовых'), ('slow_mode', 'Медленный режим'),
        ('custom', 'Кастомное'),
    ]

    chat = models.ForeignKey('social.GroupChat', on_delete=models.CASCADE, related_name='restrictions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_restrictions')
    restricted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issued_restrictions')
    restriction_type = models.CharField(max_length=20, choices=RESTRICTION_TYPES)
    reason = models.TextField(blank=True)
    until_date = models.DateTimeField(null=True, blank=True)
    slow_mode_delay = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ограничение в чате'
        verbose_name_plural = 'Ограничения в чатах'
        indexes = [
            models.Index(fields=['chat', 'user']),
            models.Index(fields=['until_date']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.get_restriction_type_display()} в {self.chat.name}"

    @property
    def is_active(self):
        if self.until_date is None:
            return True
        return self.until_date > timezone.now()


class ChatSlowMode(models.Model):
    chat = models.OneToOneField('social.GroupChat', on_delete=models.CASCADE, related_name='slow_mode_settings')
    enabled = models.BooleanField(default=False)
    delay = models.IntegerField(default=30)
    exempt_admins = models.BooleanField(default=True)
    exempt_moderators = models.BooleanField(default=True)
    custom_delays = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Медленный режим'
        verbose_name_plural = 'Медленные режимы'


# ==================== ЗАПРОСЫ НА ВСТУПЛЕНИЕ ====================

class ChatJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'), ('approved', 'Одобрено'), ('rejected', 'Отклонено'),
    ]

    chat = models.ForeignKey('social.GroupChat', on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_join_requests')
    message = models.TextField(blank=True)
    answers = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_join_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Запрос на вступление'
        verbose_name_plural = 'Запросы на вступление'
        unique_together = [['chat', 'user']]
        indexes = [models.Index(fields=['chat', 'status'])]


# ==================== ТЕГИ ====================

class ChatTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#3b82f6')
    emoji = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тег чата'
        verbose_name_plural = 'Теги чатов'
        unique_together = [['user', 'name']]


class ChatTagAssignment(models.Model):
    tag = models.ForeignKey(ChatTag, on_delete=models.CASCADE, related_name='assignments')
    group_chat = models.ForeignKey(
        'social.GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='tag_assignments'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='tag_assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Привязка тега'
        verbose_name_plural = 'Привязки тегов'


# ==================== АНТИ-СПАМ ====================

class AntiSpamRule(models.Model):
    RULE_TYPES = [
        ('flood', 'Флуд'), ('links', 'Ссылки'), ('spam_keywords', 'Стоп-слова'),
        ('caps_lock', 'Caps Lock'), ('new_members', 'Новые участники'), ('media_flood', 'Медиа-флуд'),
    ]
    ACTION_TYPES = [
        ('delete', 'Удалить'), ('mute', 'Заглушить'), ('ban', 'Забанить'), ('warn', 'Предупреждение'),
    ]

    chat = models.ForeignKey('social.GroupChat', on_delete=models.CASCADE, related_name='anti_spam_rules')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    threshold = models.IntegerField(default=5)
    time_window = models.IntegerField(default=60)
    keywords = models.JSONField(default=list, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES, default='delete')
    action_duration = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Правило анти-спама'
        verbose_name_plural = 'Правила анти-спама'


# ==================== РЕАКЦИИ ====================

class MessageReaction(models.Model):
    message = models.ForeignKey('social.Message', on_delete=models.CASCADE, related_name='emoji_reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_emoji_reactions')
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Реакция'
        verbose_name_plural = 'Реакции'
        unique_together = [['message', 'user', 'emoji']]
        indexes = [models.Index(fields=['message', 'emoji'])]


# ==================== ЗАКРЕПЛЁННЫЕ СООБЩЕНИЯ ====================

class MessagePin(models.Model):
    chat = models.ForeignKey(
        'social.GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='pinned_messages_v2'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='pinned_messages_v2'
    )
    message = models.OneToOneField('social.Message', on_delete=models.CASCADE, related_name='pin_info')
    pinned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_messages_v2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Закреплённое сообщение'
        verbose_name_plural = 'Закреплённые сообщения'


# ==================== РЕЗЕРВНЫЕ КОПИИ ====================

class ChatBackup(models.Model):
    STATUS_CHOICES = [
        ('creating', 'Создание'), ('completed', 'Завершено'), ('failed', 'Ошибка'),
    ]

    chat = models.ForeignKey('social.GroupChat', on_delete=models.CASCADE, related_name='backups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_backups')
    backup_file = models.FileField(upload_to='chat_backups/', null=True, blank=True)
    messages_count = models.IntegerField(default=0)
    members_count = models.IntegerField(default=0)
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='creating')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Резервная копия'
        verbose_name_plural = 'Резервные копии'


# ==================== ЗАПЛАНИРОВАННЫЕ СООБЩЕНИЯ ====================

class ScheduledMessage(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'), ('sent', 'Отправлено'),
        ('cancelled', 'Отменено'), ('failed', 'Ошибка'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_messages')
    chat = models.ForeignKey(
        'social.GroupChat', on_delete=models.CASCADE, null=True, blank=True, related_name='scheduled_messages'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat', on_delete=models.CASCADE, null=True, blank=True, related_name='scheduled_messages'
    )
    text = models.TextField(blank=True)
    media = models.FileField(upload_to='scheduled_messages/', null=True, blank=True)
    media_type = models.CharField(max_length=20, blank=True)
    scheduled_at = models.DateTimeField()
    is_recurring = models.BooleanField(default=False)
    recurring_interval = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Запланированное сообщение'
        verbose_name_plural = 'Запланированные сообщения'
        indexes = [models.Index(fields=['scheduled_at', 'status'])]


# ==================== ЖУРНАЛ БЕЗОПАСНОСТИ ====================

class SecurityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Вход'), ('logout', 'Выход'), ('password_change', 'Изменение пароля'),
        ('new_device', 'Новое устройство'), ('suspicious_activity', 'Подозрительная активность'),
        ('ownership_transfer', 'Передача владения'), ('chat_delete', 'Удаление группы'),
        ('2fa_enable', 'Включение 2FA'), ('2fa_disable', 'Отключение 2FA'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(default=dict)
    location = models.JSONField(default=dict)
    details = models.JSONField(default=dict)
    is_suspicious = models.BooleanField(default=False)
    was_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Запись безопасности'
        verbose_name_plural = 'Журнал безопасности'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_suspicious']),
        ]


# ==================== КЭШИРОВАННЫЕ НАСТРОЙКИ ГРУППЫ ====================

class GroupChatSettings(models.Model):
    chat = models.OneToOneField(
        'social.GroupChat', on_delete=models.CASCADE, related_name='cached_settings'
    )
    members_count = models.IntegerField(default=0)
    online_count = models.IntegerField(default=0)
    messages_count = models.IntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    permissions_cache = models.JSONField(default=dict)
    daily_messages = models.IntegerField(default=0)
    weekly_active = models.IntegerField(default=0)
    cache_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки группы (кэш)'
        verbose_name_plural = 'Настройки групп (кэш)'

    def refresh_cache(self):
        from .models import Message
        self.members_count = self.chat.members.count()
        self.messages_count = Message.objects.filter(chat=self.chat).count()
        last = Message.objects.filter(chat=self.chat).order_by('-created_at').first()
        self.last_message_at = last.created_at if last else None
        self.save()


# ==================== FRANCHISE DISCUSSION TOPICS ====================

class ChatTopic(models.Model):
    """Топик (forum thread) внутри franchise discussion чата.
    anime=None - общая тема «О франшизе».
    """
    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name='Чат'
    )
    anime = models.ForeignKey(
        'anime.Anime',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='discussion_topics',
        verbose_name='Аниме'
    )
    title = models.CharField(max_length=255, verbose_name='Название')
    order = models.IntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тема обсуждения'
        verbose_name_plural = 'Темы обсуждений'
        ordering = ['order']
        unique_together = [('chat', 'anime')]

    def __str__(self):
        return f'{self.chat.name} - {self.title}'


# ==================== GLOBAL CHAT STYLE ====================

class UserGlobalChatStyle(models.Model):
    """Глобальные стилевые настройки чатов пользователя.
    Per-chat настройки имеют приоритет над этими.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='global_chat_style',
        verbose_name='Пользователь'
    )
    wallpaper_type  = models.CharField(max_length=20, default='solid')
    wallpaper_color = models.CharField(max_length=7,  default='#0f0f0f')
    wallpaper_color2 = models.CharField(max_length=7, default='#1a1a2e')
    bubble_style      = models.CharField(max_length=20, default='modern')
    accent_color      = models.CharField(max_length=7,  default='#6C5CE7')
    font_size         = models.CharField(max_length=20, default='medium')
    message_animation = models.CharField(max_length=20, default='slide')
    emoji_set         = models.CharField(max_length=30, default='default')
    time_format       = models.CharField(max_length=4,  default='24h')
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Глобальные настройки чата'
        verbose_name_plural = 'Глобальные настройки чатов'

    def __str__(self):
        return f'GlobalChatStyle for {self.user}'
