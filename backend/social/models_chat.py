"""
Дополнительные модели для системы чатов согласно документации CHAT_SETTINGS.md
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import secrets
import string

User = get_user_model()


class ChatInviteLink(models.Model):
    """Ссылки-приглашения в групповые чаты"""
    
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
    
    # Ссылка
    name = models.CharField(max_length=100, blank=True, verbose_name='Название ссылки')
    invite_link = models.CharField(max_length=100, unique=True, verbose_name='Код приглашения')
    
    # Настройки
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    usage_limit = models.IntegerField(null=True, blank=True, verbose_name='Лимит использований')
    usage_count = models.IntegerField(default=0, verbose_name='Количество использований')
    
    # Статус
    is_revoked = models.BooleanField(default=False, verbose_name='Отозвана')
    is_primary = models.BooleanField(default=False, verbose_name='Основная ссылка')
    
    # Автоматическое назначение роли
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
        """Генерирует уникальную ссылку-приглашение"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @property
    def is_valid(self):
        """Проверяет, действительна ли ссылка"""
        if self.is_revoked:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True
    
    def increment_usage(self):
        """Увеличивает счётчик использований"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class ChatWallpaper(models.Model):
    """Обои для чатов"""
    
    WALLPAPER_TYPES = [
        ('solid', 'Сплошной цвет'),
        ('gradient', 'Градиент'),
        ('pattern', 'Паттерн'),
        ('image', 'Изображение'),
    ]
    
    # Владелец (пользователь или чат)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_wallpapers',
        verbose_name='Пользователь'
    )
    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wallpapers',
        verbose_name='Групповой чат'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wallpapers',
        verbose_name='Личный чат'
    )
    
    # Тип обоев
    wallpaper_type = models.CharField(
        max_length=20, 
        choices=WALLPAPER_TYPES, 
        default='solid',
        verbose_name='Тип обоев'
    )
    
    # Цвета
    wallpaper_color = models.CharField(
        max_length=7, 
        default='#1a1a1a',
        verbose_name='Основной цвет'
    )
    wallpaper_color2 = models.CharField(
        max_length=7, 
        blank=True,
        default='',
        verbose_name='Второй цвет (для градиента)'
    )
    
    # Настройки
    wallpaper_intensity = models.IntegerField(default=100, verbose_name='Интенсивность (0-100)')
    wallpaper_blur = models.IntegerField(default=0, verbose_name='Размытие (0-100)')
    wallpaper_motion = models.CharField(
        max_length=20, 
        default='none',
        verbose_name='Анимация'
    )
    
    # Изображение
    wallpaper_image = models.ImageField(
        upload_to='chat_wallpapers/', 
        null=True, 
        blank=True, 
        verbose_name='Изображение обоев'
    )
    
    # Предустановленные обои
    is_preset = models.BooleanField(default=False, verbose_name='Предустановленные')
    preset_name = models.CharField(max_length=100, blank=True, verbose_name='Название пресета')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Обои чата'
        verbose_name_plural = 'Обои чатов'
        indexes = [
            models.Index(fields=['user', 'chat']),
            models.Index(fields=['user', 'private_chat']),
        ]
    
    def __str__(self):
        if self.chat:
            return f"Обои для чата {self.chat.name}"
        if self.private_chat:
            return f"Обои для личного чата {self.private_chat.id}"
        return f"Обои пользователя {self.user.username if self.user else 'N/A'}"


class ChatTheme(models.Model):
    """Тема оформления чата"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_themes'
    )
    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='themes'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='themes'
    )
    
    # Основные цвета
    theme = models.CharField(max_length=50, default='default', verbose_name='Тема')
    message_color = models.CharField(max_length=7, default='#3b82f6', verbose_name='Цвет своих сообщений')
    message_color_other = models.CharField(max_length=7, default='#2a2a2a', verbose_name='Цвет чужих сообщений')
    
    # Стили пузырей
    bubble_style = models.CharField(
        max_length=20, 
        default='modern',
        verbose_name='Стиль пузырей'
    )  # modern, classic, rounded
    
    # Размеры
    font_size = models.CharField(
        max_length=10, 
        default='medium',
        verbose_name='Размер шрифта'
    )  # small, medium, large
    time_format = models.CharField(
        max_length=5, 
        default='24h',
        verbose_name='Формат времени'
    )  # 12h, 24h
    
    # Анимации
    message_animation = models.CharField(
        max_length=20, 
        default='slide',
        verbose_name='Анимация сообщений'
    )  # slide, fade, pop, none
    reaction_animation = models.CharField(
        max_length=20, 
        default='bounce',
        verbose_name='Анимация реакций'
    )  # bounce, scale, none
    typing_animation = models.CharField(
        max_length=20, 
        default='dots',
        verbose_name='Индикатор печати'
    )  # dots, wave, pulse
    
    # Эмодзи
    emoji_set = models.CharField(
        max_length=20, 
        default='default',
        verbose_name='Набор эмодзи'
    )  # default, twitter, google, samsung, anime
    emoji_size = models.CharField(
        max_length=10, 
        default='medium',
        verbose_name='Размер эмодзи'
    )  # small, medium, large
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Тема чата'
        verbose_name_plural = 'Темы чатов'
        unique_together = [['user', 'chat'], ['user', 'private_chat']]
    
    def __str__(self):
        if self.chat:
            return f"Тема для чата {self.chat.name}"
        if self.private_chat:
            return f"Тема для личного чата {self.private_chat.id}"
        return f"Глобальная тема {self.user.username}"


class MessageReaction(models.Model):
    """Реакции на сообщения (вынесено из JSON для производительности)"""
    
    message = models.ForeignKey(
        'social.Message', 
        on_delete=models.CASCADE, 
        related_name='chat_reactions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_message_reactions'
    )
    emoji = models.CharField(max_length=10, verbose_name='Эмодзи реакции')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Реакция на сообщение'
        verbose_name_plural = 'Реакции на сообщения'
        unique_together = [['message', 'user', 'emoji']]
        indexes = [
            models.Index(fields=['message', 'emoji']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.emoji}"


class ChatBan(models.Model):
    """Блокировка пользователя в групповом чате"""
    
    chat = models.ForeignKey(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='bans'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_bans'
    )
    banned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='issued_bans'
    )
    
    reason = models.TextField(verbose_name='Причина блокировки')
    until_date = models.DateTimeField(null=True, blank=True, verbose_name='До какой даты')
    
    # Удаление сообщений при блокировке
    delete_messages = models.BooleanField(default=False, verbose_name='Удалить все сообщения')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Блокировка в чате'
        verbose_name_plural = 'Блокировки в чатах'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', 'user']),
            models.Index(fields=['until_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} заблокирован в {self.chat.name}"
    
    @property
    def is_active(self):
        """Проверяет, активна ли блокировка"""
        if self.until_date is None:
            return True  # Вечная блокировка
        return self.until_date > timezone.now()


class ChatRestriction(models.Model):
    """Ограничения пользователя в групповом чате"""
    
    RESTRICTION_TYPES = [
        ('read_only', 'Только чтение'),
        ('no_media', 'Без медиа'),
        ('no_stickers', 'Без стикеров'),
        ('no_links', 'Без ссылок'),
        ('no_voice', 'Без голосовых'),
        ('slow_mode', 'Медленный режим'),
        ('custom', 'Кастомное'),
    ]
    
    chat = models.ForeignKey(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='restrictions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_restrictions'
    )
    restricted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='issued_restrictions'
    )
    
    # Тип ограничения
    restriction_type = models.CharField(
        max_length=20, 
        choices=RESTRICTION_TYPES,
        verbose_name='Тип ограничения'
    )
    
    # Параметры
    reason = models.TextField(blank=True, verbose_name='Причина')
    until_date = models.DateTimeField(null=True, blank=True, verbose_name='До какой даты')
    slow_mode_delay = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Задержка (для медленного режима)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ограничение в чате'
        verbose_name_plural = 'Ограничения в чатах'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', 'user']),
            models.Index(fields=['until_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.get_restriction_type_display()} в {self.chat.name}"
    
    @property
    def is_active(self):
        """Проверяет, активно ли ограничение"""
        if self.until_date is None:
            return True
        return self.until_date > timezone.now()


class ChatSlowMode(models.Model):
    """Настройки медленного режима для чата"""
    
    chat = models.OneToOneField(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='slow_mode_settings'
    )
    
    enabled = models.BooleanField(default=False, verbose_name='Включён')
    delay = models.IntegerField(default=30, verbose_name='Задержка в секундах')
    
    # Исключения
    exempt_admins = models.BooleanField(default=True, verbose_name='Админы без ограничений')
    exempt_moderators = models.BooleanField(default=True, verbose_name='Модераторы без ограничений')
    
    # Персональные задержки
    custom_delays = models.JSONField(
        default=dict, 
        verbose_name='Персональные задержки'
    )  # {user_id: delay_seconds}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Медленный режим'
        verbose_name_plural = 'Медленные режимы'
    
    def __str__(self):
        return f"Медленный режим для {self.chat.name}: {self.delay}с"


class ChatJoinRequest(models.Model):
    """Запрос на вступление в приватную группу"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    chat = models.ForeignKey(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='join_requests'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='join_requests'
    )
    
    # Анкета
    message = models.TextField(blank=True, verbose_name='Сообщение пользователю')
    answers = models.JSONField(default=dict, verbose_name='Ответы на вопросы')
    
    # Статус
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_join_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запрос на вступление'
        verbose_name_plural = 'Запросы на вступление'
        ordering = ['-created_at']
        unique_together = [['chat', 'user']]
        indexes = [
            models.Index(fields=['chat', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} → {self.chat.name} ({self.status})"


class ChatTag(models.Model):
    """Теги для чатов (для организации)"""
    
    TAG_COLORS = [
        ('#ef4444', 'Красный'),
        ('#f97316', 'Оранжевый'),
        ('#eab308', 'Жёлтый'),
        ('#22c55e', 'Зелёный'),
        ('#3b82f6', 'Синий'),
        ('#8b5cf6', 'Фиолетовый'),
        ('#ec4899', 'Розовый'),
        ('#6b7280', 'Серый'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_tags'
    )
    
    name = models.CharField(max_length=50, verbose_name='Название тега')
    color = models.CharField(
        max_length=7, 
        choices=TAG_COLORS, 
        default='#3b82f6',
        verbose_name='Цвет'
    )
    emoji = models.CharField(max_length=10, blank=True, verbose_name='Эмодзи')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Тег чата'
        verbose_name_plural = 'Теги чатов'
        ordering = ['name']
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return f"{self.emoji} {self.name}"


class ChatTagAssignment(models.Model):
    """Привязка тегов к чатам"""
    
    tag = models.ForeignKey(
        ChatTag, 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    
    # Может быть привязан к групповому или личному чату
    group_chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tag_assignments'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tag_assignments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Привязка тега'
        verbose_name_plural = 'Привязки тегов'
        unique_together = [
            ['tag', 'group_chat'],
            ['tag', 'private_chat'],
        ]


class AntiSpamRule(models.Model):
    """Правила анти-спама для группового чата"""
    
    RULE_TYPES = [
        ('flood', 'Флуд (много сообщений)'),
        ('links', 'Ссылки в сообщениях'),
        ('spam_keywords', 'Стоп-слова'),
        ('caps_lock', 'Caps Lock'),
        ('new_members', 'Ограничение новых участников'),
        ('media_flood', 'Медиа-флуд'),
    ]
    
    ACTION_TYPES = [
        ('delete', 'Удалить сообщение'),
        ('mute', 'Заглушить'),
        ('ban', 'Забанить'),
        ('warn', 'Предупреждение'),
    ]
    
    chat = models.ForeignKey(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='anti_spam_rules'
    )
    
    rule_type = models.CharField(
        max_length=20, 
        choices=RULE_TYPES,
        verbose_name='Тип правила'
    )
    
    # Параметры правила
    threshold = models.IntegerField(default=5, verbose_name='Порог срабатывания')
    time_window = models.IntegerField(default=60, verbose_name='Временное окно (секунды)')
    keywords = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='Ключевые слова'
    )
    
    # Действие
    action = models.CharField(
        max_length=20, 
        choices=ACTION_TYPES, 
        default='delete',
        verbose_name='Действие'
    )
    action_duration = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Длительность действия (минуты)'
    )
    
    enabled = models.BooleanField(default=True, verbose_name='Включено')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Правило анти-спама'
        verbose_name_plural = 'Правила анти-спама'
        ordering = ['rule_type']
    
    def __str__(self):
        return f"{self.get_rule_type_display()} в {self.chat.name}"


class ChatBackup(models.Model):
    """Резервная копия чата"""
    
    STATUS_CHOICES = [
        ('creating', 'Создание'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    
    chat = models.ForeignKey(
        'social.GroupChat', 
        on_delete=models.CASCADE, 
        related_name='backups'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_backups'
    )
    
    # Файл бэкапа
    backup_file = models.FileField(
        upload_to='chat_backups/', 
        null=True, 
        blank=True,
        verbose_name='Файл бэкапа'
    )
    
    # Статистика
    messages_count = models.IntegerField(default=0, verbose_name='Количество сообщений')
    members_count = models.IntegerField(default=0, verbose_name='Количество участников')
    file_size = models.BigIntegerField(default=0, verbose_name='Размер файла')
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='creating',
        verbose_name='Статус'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Резервная копия чата'
        verbose_name_plural = 'Резервные копии чатов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Бэкап {self.chat.name} от {self.created_at.strftime('%d.%m.%Y')}"


class ScheduledMessage(models.Model):
    """Запланированные сообщения"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('sent', 'Отправлено'),
        ('cancelled', 'Отменено'),
        ('failed', 'Ошибка'),
    ]
    
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='scheduled_messages'
    )
    
    # Может быть в групповом или личном чате
    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scheduled_messages'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scheduled_messages'
    )
    
    # Контент
    text = models.TextField(blank=True, verbose_name='Текст сообщения')
    media = models.FileField(
        upload_to='scheduled_messages/', 
        null=True, 
        blank=True,
        verbose_name='Медиафайл'
    )
    media_type = models.CharField(max_length=20, blank=True, verbose_name='Тип медиа')
    
    # Расписание
    scheduled_at = models.DateTimeField(verbose_name='Время отправки')
    
    # Повторение
    is_recurring = models.BooleanField(default=False, verbose_name='Повторяющееся')
    recurring_interval = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Интервал повтора (дни)'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='scheduled',
        verbose_name='Статус'
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Время фактической отправки')
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Запланированное сообщение'
        verbose_name_plural = 'Запланированные сообщения'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
        ]
    
    def __str__(self):
        return f"Запланировано на {self.scheduled_at.strftime('%d.%m.%Y %H:%M')}"


# ==================== ЖУРНАЛ БЕЗОПАСНОСТИ ====================

class SecurityLog(models.Model):
    """Журнал безопасности для критических действий"""
    
    ACTION_CHOICES = [
        ('login', 'Вход в аккаунт'),
        ('logout', 'Выход из аккаунта'),
        ('password_change', 'Изменение пароля'),
        ('new_device', 'Новая авторизация'),
        ('suspicious_activity', 'Подозрительная активность'),
        ('ownership_transfer', 'Передача владения группой'),
        ('chat_delete', 'Удаление группы'),
        ('admin_ban', 'Блокировка администратора'),
        ('settings_change', 'Изменение критических настроек'),
        ('2fa_enable', 'Включение 2FA'),
        ('2fa_disable', 'Отключение 2FA'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='security_logs'
    )
    
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES,
        verbose_name='Тип действия'
    )
    
    # Данные об устройстве и местоположении
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP-адрес')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    device_info = models.JSONField(default=dict, verbose_name='Информация об устройстве')
    location = models.JSONField(default=dict, verbose_name='Местоположение')
    
    # Дополнительные данные
    details = models.JSONField(default=dict, verbose_name='Детали действия')
    
    # Статус
    is_suspicious = models.BooleanField(default=False, verbose_name='Подозрительная активность')
    was_notified = models.BooleanField(default=False, verbose_name='Пользователь уведомлён')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запись безопасности'
        verbose_name_plural = 'Журнал безопасности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.user.username} - {self.created_at}"


class GroupChatSettings(models.Model):
    """Кэшированные настройки группы"""
    
    chat = models.OneToOneField(
        'social.GroupChat',
        on_delete=models.CASCADE,
        related_name='cached_settings'
    )
    
    # Кэшированные данные
    members_count = models.IntegerField(default=0, verbose_name='Количество участников')
    online_count = models.IntegerField(default=0, verbose_name='Количество онлайн')
    messages_count = models.IntegerField(default=0, verbose_name='Количество сообщений')
    
    # Время последней активности
    last_activity_at = models.DateTimeField(null=True, blank=True, verbose_name='Последняя активность')
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name='Последнее сообщение')
    
    # Кэш разрешений
    permissions_cache = models.JSONField(default=dict, verbose_name='Кэш разрешений')
    
    # Статистика
    daily_messages = models.IntegerField(default=0, verbose_name='Сообщений за день')
    weekly_active = models.IntegerField(default=0, verbose_name='Активных за неделю')
    
    # Время обновления кэша
    cache_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Настройки группы (кэш)'
        verbose_name_plural = 'Настройки групп (кэш)'
    
    def __str__(self):
        return f"Настройки {self.chat.name}"
    
    def invalidate_cache(self):
        """Инвалидация кэша"""
        from django.utils import timezone
        self.cache_updated_at = None
        self.save(update_fields=['cache_updated_at'])
    
    def refresh_cache(self):
        """Обновление кэша"""
        from django.utils import timezone
        from .models import ChatMember, Message
        
        self.members_count = self.chat.members.count()
        self.messages_count = Message.objects.filter(chat=self.chat).count()
        self.last_message_at = Message.objects.filter(chat=self.chat).order_by('-created_at').values_list('created_at', flat=True).first()
        self.cache_updated_at = timezone.now()
        self.save()


class PrivateChatSettings(models.Model):
    """Персональные настройки пользователя для личного чата"""
    
    chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        related_name='settings'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='private_chat_settings_new'
    )
    
    # Кастомизация
    custom_name = models.CharField(max_length=255, blank=True, verbose_name='Кастомное название')
    custom_avatar = models.ImageField(
        upload_to='private_chat_avatars/', 
        null=True, 
        blank=True,
        verbose_name='Кастомная аватарка'
    )
    
    # Уведомления
    notifications_enabled = models.BooleanField(default=True, verbose_name='Уведомления включены')
    sound_enabled = models.BooleanField(default=True, verbose_name='Звук включён')
    vibration_enabled = models.BooleanField(default=True, verbose_name='Вибрация включена')
    show_preview = models.BooleanField(default=True, verbose_name='Показывать превью сообщения')
    show_popup = models.BooleanField(default=True, verbose_name='Показывать всплывающие')
    
    # Заглушивание
    muted_until = models.DateTimeField(null=True, blank=True, verbose_name='Заглушен до')
    
    # Статус
    is_archived = models.BooleanField(default=False, verbose_name='Архивирован')
    is_pinned = models.BooleanField(default=False, verbose_name='Закреплён')
    is_hidden = models.BooleanField(default=False, verbose_name='Скрыт')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')
    
    # Автоудаление
    auto_delete_after = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Автоудаление через (дней)'
    )
    
    # Папка (ID папки из models.py)
    folder_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID папки'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Настройки личного чата'
        verbose_name_plural = 'Настройки личных чатов'
        unique_together = [['chat', 'user']]
        indexes = [
            models.Index(fields=['user', 'is_pinned']),
            models.Index(fields=['user', 'is_archived']),
        ]
    
    def __str__(self):
        return f"Настройки {self.user.username} для чата {self.chat.id}"
    
    @property
    def is_muted(self):
        """Проверяет, заглушен ли чат"""
        if not self.muted_until:
            return False
        from django.utils import timezone
        return self.muted_until > timezone.now()


class MessagePin(models.Model):
    """Закреплённые сообщения в чатах"""
    
    chat = models.ForeignKey(
        'social.GroupChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pinned_messages_new'
    )
    private_chat = models.ForeignKey(
        'social.PrivateChat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pinned_messages_new'
    )
    message = models.OneToOneField(
        'social.Message',
        on_delete=models.CASCADE,
        related_name='pin_info'
    )
    pinned_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pinned_messages_new'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Закреплённое сообщение'
        verbose_name_plural = 'Закреплённые сообщения'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['private_chat', 'created_at']),
        ]
    
    def __str__(self):
        return f"Закреплено: {self.message.id}"
