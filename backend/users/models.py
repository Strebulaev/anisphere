from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session
from django.utils import timezone
import pyotp
import qrcode
from io import BytesIO
from django.core.files import File
# from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    # Дополнительные поля профиля
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    # Никнейм и отображаемое имя
    nickname = models.CharField(max_length=30, blank=True, null=True, unique=True, verbose_name=_('Nickname'))
    display_name = models.CharField(max_length=50, blank=True, verbose_name=_('Display name'))

    # Любимые жанры
    favorite_genres = models.JSONField(default=list, verbose_name=_('Favorite genres'))

    # Социальные ссылки
    website = models.URLField(blank=True, verbose_name=_('Website'))
    vk_profile = models.CharField(max_length=100, blank=True, verbose_name=_('VK profile'))
    telegram = models.CharField(max_length=100, blank=True, verbose_name=_('Telegram'))

    # Поля для аутентификации
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Phone number'))
    email_verified = models.BooleanField(default=False, verbose_name=_('Email verified'))
    phone_verified = models.BooleanField(default=False, verbose_name=_('Phone verified'))

    # OAuth поля
    google_id = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name=_('Google ID'))

    # Статус онлайн
    is_online = models.BooleanField(default=False, verbose_name=_('Is online'))
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name=_('Last seen'))

    # Для SMS верификации
    sms_code = models.CharField(max_length=6, blank=True, null=True, verbose_name=_('SMS verification code'))
    sms_code_expires = models.DateTimeField(blank=True, null=True, verbose_name=_('SMS code expiration'))

    # Двухфакторная аутентификация
    two_factor_enabled = models.BooleanField(default=False, verbose_name=_('Two factor enabled'))
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Two factor secret'))

    # Система репутации
    level = models.IntegerField(default=1, verbose_name=_('Level'))
    experience = models.IntegerField(default=0, verbose_name=_('Experience points'))
    mana = models.IntegerField(default=0, verbose_name=_('Mana currency'))

    # Значки и достижения
    badges = models.JSONField(default=list, verbose_name=_('Badges list'))

    # Статистика активности
    posts_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    playlists_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username or self.email or str(self.phone_number) or f'User {self.id}'


class UserSession(models.Model):
    """Модель для отслеживания активных сессий пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.CharField(max_length=200, blank=True, verbose_name=_('Device info'))
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_('IP address'))
    user_agent = models.TextField(blank=True, verbose_name=_('User agent'))
    location = models.CharField(max_length=100, blank=True, verbose_name=_('Location'))
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('User session')
        verbose_name_plural = _('User sessions')
        ordering = ['-last_activity']

    def __str__(self):
        return f'{self.user.username} - {self.device_info or "Unknown device"}'

    @property
    def is_current_session(self):
        """Проверяет, является ли эта сессия текущей для пользователя"""
        from django.contrib.sessions.middleware import get_current_session_key
        return self.session_key == get_current_session_key()


class UserSettings(models.Model):
    """Модель для хранения настроек пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    # Настройки внешнего вида
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
        ('auto', 'Автоматическая')
    ], verbose_name=_('Theme'))

    ui_style = models.CharField(max_length=20, default='modern', choices=[
        ('modern', 'Современный'),
        ('classic', 'Классический'),
        ('minimal', 'Минималистичный'),
        ('dark', 'Тёмный')
    ], verbose_name=_('UI Style'))

    text_size = models.CharField(max_length=20, default='medium', choices=[
        ('small', 'Маленький'),
        ('medium', 'Средний'),
        ('large', 'Большой')
    ], verbose_name=_('Text Size'))

    # Настройки уведомлений
    push_notifications = models.BooleanField(default=True, verbose_name=_('Push notifications'))
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email notifications'))
    message_notifications = models.BooleanField(default=True, verbose_name=_('Message notifications'))
    contest_notifications = models.BooleanField(default=False, verbose_name=_('Contest notifications'))

    # Настройки приватности
    show_in_search = models.BooleanField(default=True, verbose_name=_('Show in search'))
    show_online_status = models.BooleanField(default=True, verbose_name=_('Show online status'))
    show_stats = models.BooleanField(default=True, verbose_name=_('Show statistics'))

    # Настройки рекомендаций
    personalized_recommendations = models.BooleanField(default=True, verbose_name=_('Personalized recommendations'))
    selected_interests = models.JSONField(default=list, verbose_name=_('Selected interests'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User settings')
        verbose_name_plural = _('User settings')

    def __str__(self):
        return f'{self.user.username} settings'


class UserProfileSettings(models.Model):
    """Основные настройки профиля пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_settings')

    # Конфиденциальность
    show_online_status = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_typing_status = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_group_invites = models.BooleanField(default=True)
    who_can_add_to_groups = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Только контакты'),
            ('nobody', 'Никто')
        ],
        default='everyone'
    )

    # Контакты
    sync_contacts = models.BooleanField(default=True)
    suggest_frequent_contacts = models.BooleanField(default=True)

    # Аватар и тема
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Светлая'),
            ('dark', 'Темная'),
            ('system', 'Как в системе'),
            ('blue', 'Синяя'),
            ('green', 'Зеленая')
        ],
        default='system'
    )
    accent_color = models.CharField(max_length=7, default='#0084FF')

    # Язык и регион
    language = models.CharField(max_length=10, default='ru')
    timezone = models.CharField(max_length=50, default='Europe/Moscow')
    date_format = models.CharField(
        max_length=20,
        choices=[
            ('dd.mm.yyyy', 'ДД.ММ.ГГГГ'),
            ('mm/dd/yyyy', 'ММ/ДД/ГГГГ'),
            ('yyyy-mm-dd', 'ГГГГ-ММ-ДД')
        ],
        default='dd.mm.yyyy'
    )
    time_format = models.CharField(
        max_length=10,
        choices=[('24', '24 часа'), ('12', '12 часов')],
        default='24'
    )

    # Уведомления (общие)
    notification_sound = models.CharField(max_length=100, default='default')
    vibration = models.BooleanField(default=True)
    preview_content = models.BooleanField(default=True)

    # Безопасность
    login_notifications = models.BooleanField(default=True)
    password_changed_notification = models.BooleanField(default=True)

    # Дата обновления
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Настройки профиля'
        verbose_name_plural = 'Настройки профилей'


class TwoFactorAuth(models.Model):
    """Настройки двухфакторной аутентификации"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)

    # Методы восстановления
    backup_codes = models.JSONField(default=list)  # Список кодов
    phone_number = models.CharField(max_length=20, blank=True)  # Для SMS
    email_enabled = models.BooleanField(default=True)  # Резервный email

    # Настройки
    require_on_new_device = models.BooleanField(default=True)
    remember_device_days = models.IntegerField(default=30)  # Запоминать устройство на N дней

    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def generate_secret(self):
        """Генерация нового секретного ключа"""
        self.secret_key = pyotp.random_base32()

    def generate_backup_codes(self, count=10):
        """Генерация резервных кодов"""
        import secrets
        self.backup_codes = [
            '-'.join([secrets.token_hex(2).upper() for _ in range(2)])
            for _ in range(count)
        ]

    def generate_qr_code(self):
        """Генерация QR-кода для приложения аутентификатора"""
        if not self.secret_key:
            self.generate_secret()

        totp = pyotp.TOTP(self.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email,
            issuer_name="Messenger App"
        )

        # Создание QR-кода
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')

        return File(buffer, name=f'2fa_qr_{self.user.id}.png')

    def verify_code(self, code):
        """Проверка кода аутентификатора"""
        if not self.is_enabled or not self.secret_key:
            return False

        totp = pyotp.TOTP(self.secret_key)

        # Проверка текущего кода
        if totp.verify(code):
            self.last_used = timezone.now()
            self.save()
            return True

        # Проверка резервных кодов
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True

        return False


class ActiveSession(models.Model):
    """Активные сессии пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.JSONField(default=dict)  # Информация об устройстве
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    # Локация
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Статус
    is_current = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'last_activity']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.device_info.get('device', 'Unknown')}"


class NotificationSettings(models.Model):
    """Детальные настройки уведомлений"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')

    # Типы уведомлений
    message_notifications = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    call_notifications = models.BooleanField(default=True)
    mention_notifications = models.BooleanField(default=True)
    reaction_notifications = models.BooleanField(default=True)

    # Push-уведомления
    push_enabled = models.BooleanField(default=True)
    push_sound = models.BooleanField(default=True)
    push_vibration = models.BooleanField(default=True)
    push_preview = models.BooleanField(default=True)  # Показывать текст

    # Email уведомления
    email_enabled = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediately', 'Немедленно'),
            ('hourly', 'Каждый час'),
            ('daily', 'Ежедневно'),
            ('weekly', 'Еженедельно')
        ],
        default='immediately'
    )

    # Исключения
    mute_until = models.DateTimeField(null=True, blank=True)
    do_not_disturb_start = models.TimeField(null=True, blank=True)  # Начало периода "Не беспокоить"
    do_not_disturb_end = models.TimeField(null=True, blank=True)    # Конец периода

    # Индивидуальные настройки для чатов
    override_chat_settings = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)


class PrivacySettings(models.Model):
    """Настройки приватности"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')

    # Кто может видеть
    who_can_see_phone = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='contacts'
    )

    who_can_see_email = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='contacts'
    )

    who_can_see_last_seen = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='everyone'
    )

    who_can_see_profile_photo = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='everyone'
    )

    # Блокировка
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)

    # Пересылка сообщений
    allow_message_forwarding = models.BooleanField(default=True)

    # Звонки
    who_can_call = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='everyone'
    )

    # Группы
    who_can_add_to_groups = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Все'),
            ('contacts', 'Контакты'),
            ('nobody', 'Никто')
        ],
        default='everyone'
    )


class UserTheme(models.Model):
    """Пользовательские темы"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='themes')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    # Цвета
    primary_color = models.CharField(max_length=7, default='#0084FF')
    secondary_color = models.CharField(max_length=7, default='#00C853')
    background_color = models.CharField(max_length=7, default='#373737')
    text_color = models.CharField(max_length=7, default='#000000')
    secondary_text_color = models.CharField(max_length=7, default='#666666')

    # Дополнительные настройки
    message_bubble_radius = models.IntegerField(default=12)  # px
    show_message_time = models.BooleanField(default=True)
    compact_mode = models.BooleanField(default=False)

    # Фон чата
    chat_background = models.ImageField(upload_to='chat_backgrounds/', null=True, blank=True)
    chat_background_opacity = models.FloatField(default=0.1)  # 0-1

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'name']

    def apply_to_user(self):
        """Применить тему к пользователю"""
        # Сохраняем настройки в профиль пользователя
        profile_settings = self.user.profile_settings
        profile_settings.theme = 'custom'
        profile_settings.accent_color = self.primary_color
        profile_settings.save()

        # Деактивируем другие темы пользователя
        UserTheme.objects.filter(user=self.user).exclude(id=self.id).update(is_active=False)

        self.is_active = True
        self.save()

    def to_css_variables(self):
        """Преобразовать в CSS переменные"""
        return {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--background-color': self.background_color,
            '--text-color': self.text_color,
            '--secondary-text-color': self.secondary_text_color,
            '--message-bubble-radius': f'{self.message_bubble_radius}px',
            '--chat-background-opacity': self.chat_background_opacity,
        }


class ChatBackground(models.Model):
    """Фоны для чатов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_backgrounds')
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='chat_backgrounds/')
    thumbnail = models.ImageField(upload_to='chat_backgrounds/thumbnails/')
    is_default = models.BooleanField(default=False)
    opacity = models.FloatField(default=0.1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'name']


class SecurityLog(models.Model):
    """Лог событий безопасности"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)  # 2fa_enabled, login, password_change, etc.
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    additional_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


class EmailLog(models.Model):
    """Лог отправленных email уведомлений"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'sent_at']),
        ]


class MessageNotification(models.Model):
    """Отслеживание отправленных уведомлений о сообщениях"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey('social.Message', on_delete=models.CASCADE)
    notified_via = models.CharField(max_length=20, choices=[
        ('push', 'Push уведомление'),
        ('email', 'Email уведомление'),
        ('sms', 'SMS уведомление')
    ])
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'message', 'notified_via']


class UserAnalytics(models.Model):
    """Статистика использования приложения"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')

    # Активность
    messages_sent = models.IntegerField(default=0)
    messages_received = models.IntegerField(default=0)
    media_sent = models.IntegerField(default=0)
    calls_made = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)  # в минутах

    # Предпочтения
    favorite_chat_type = models.CharField(max_length=20, blank=True)  # private/group
    most_active_hour = models.IntegerField(null=True, blank=True)  # 0-23
    average_response_time = models.IntegerField(default=0)  # в секундах

    # Устройства
    primary_device = models.CharField(max_length=100, blank=True)
    last_used_device = models.CharField(max_length=100, blank=True)

    # Дата обновления
    last_updated = models.DateTimeField(auto_now=True)
    collected_since = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'User Analytics'

    def update_activity(self, activity_type, **kwargs):
        """Обновить статистику активности"""
        if activity_type == 'message_sent':
            self.messages_sent += 1
        elif activity_type == 'message_received':
            self.messages_received += 1
        elif activity_type == 'media_sent':
            self.media_sent += 1
        elif activity_type == 'call_made':
            self.calls_made += 1
        elif activity_type == 'time_spent':
            self.time_spent += kwargs.get('minutes', 0)

        self.save()

    def get_weekly_report(self):
        """Получить недельный отчет"""
        from datetime import datetime, timedelta
        week_ago = timezone.now() - timedelta(days=7)

        return {
            'messages_sent': self.get_messages_since(week_ago, 'sent'),
            'time_spent': self.get_time_spent_since(week_ago),
            'most_active_day': self.get_most_active_day(week_ago),
            'top_chats': self.get_top_chats(week_ago, limit=5)
        }

    def get_messages_since(self, since_date, direction='sent'):
        """Получить количество сообщений с указанной даты"""
        from social.models import Message
        if direction == 'sent':
            return Message.objects.filter(sender=self.user, created_at__gte=since_date).count()
        else:
            return Message.objects.filter(chat__members__user=self.user, created_at__gte=since_date).exclude(sender=self.user).count()

    def get_time_spent_since(self, since_date):
        """Получить время, проведенное в приложении с указанной даты"""
        sessions = UserSession.objects.filter(
            user=self.user,
            start_time__gte=since_date
        )

        total_seconds = sum(
            (s.end_time or timezone.now() - s.start_time).total_seconds()
            for s in sessions
        )

        return int(total_seconds / 60)  # возвращаем минуты

    def get_most_active_day(self, since_date):
        """Получить самый активный день"""
        # Это можно реализовать более сложной логикой
        return "Понедельник"  # Заглушка

    def get_top_chats(self, since_date, limit=5):
        """Получить топ чатов по активности"""
        # Это можно реализовать более сложной логикой
        return []  # Заглушка