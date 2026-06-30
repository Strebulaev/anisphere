from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session
from django.utils import timezone
import pyotp
import qrcode
from io import BytesIO
from django.core.files import File



class User(AbstractUser):
    
    unique_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name=_("Unique ID")
    )

    
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    cover_image = models.ImageField(
        upload_to="covers/", null=True, blank=True, verbose_name=_("Profile cover")
    )
    cover_position_x = models.FloatField(default=50, verbose_name=_("Cover position X"))
    cover_position_y = models.FloatField(default=50, verbose_name=_("Cover position Y"))
    bio = models.TextField(max_length=500, blank=True)

    
    nickname = models.CharField(
        max_length=30, blank=True, null=True, unique=True, verbose_name=_("Nickname")
    )
    display_name = models.CharField(
        max_length=50, blank=True, verbose_name=_("Display name")
    )

    
    favorite_genres = models.JSONField(default=list, verbose_name=_("Favorite genres"))

    
    website = models.URLField(blank=True, verbose_name=_("Website"))
    vk_profile = models.CharField(
        max_length=100, blank=True, verbose_name=_("VK profile")
    )
    telegram = models.CharField(max_length=100, blank=True, verbose_name=_("Telegram"))
    github = models.CharField(max_length=100, blank=True, verbose_name=_("GitHub"))
    discord = models.CharField(max_length=100, blank=True, verbose_name=_("Discord"))
    twitter = models.CharField(max_length=100, blank=True, verbose_name=_("Twitter"))

    
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Phone number")
    )
    email_verified = models.BooleanField(
        default=False, verbose_name=_("Email verified")
    )
    phone_verified = models.BooleanField(
        default=False, verbose_name=_("Phone verified")
    )

    
    google_id = models.CharField(
        max_length=50, blank=True, null=True, unique=True, verbose_name=_("Google ID")
    )

    
    is_online = models.BooleanField(default=False, verbose_name=_("Is online"))
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name=_("Last seen"))

    
    sms_code = models.CharField(
        max_length=6, blank=True, null=True, verbose_name=_("SMS verification code")
    )
    sms_code_expires = models.DateTimeField(
        blank=True, null=True, verbose_name=_("SMS code expiration")
    )

    
    two_factor_enabled = models.BooleanField(
        default=False, verbose_name=_("Two factor enabled")
    )
    two_factor_secret = models.CharField(
        max_length=32, blank=True, null=True, verbose_name=_("Two factor secret")
    )

    
    level = models.IntegerField(default=1, verbose_name=_("Level"))
    experience = models.IntegerField(default=0, verbose_name=_("Experience points"))
    mana = models.IntegerField(default=0, verbose_name=_("Mana currency"))

    
    badges = models.JSONField(default=list, verbose_name=_("Badges list"))

    
    posts_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    playlists_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    
    notify_likes = models.BooleanField(
        default=True, verbose_name=_("Уведомления о лайках")
    )
    
    notify_comments = models.BooleanField(
        default=True, verbose_name=_("Уведомления о комментариях")
    )
    
    notify_mentions = models.BooleanField(
        default=True, verbose_name=_("Уведомления об упоминаниях")
    )
    
    email_digest = models.CharField(
        max_length=20,
        choices=[
            ("never", "Никогда"),
            ("daily", "Раз в день"),
            ("weekly", "Раз в неделю"),
        ],
        default="never",
        verbose_name=_("Email дайджест"),
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return (
            self.username or self.email or str(self.phone_number) or f"User {self.id}"
        )

    def generate_unique_id(self):
        """Генерирует уникальный ID для пользователя"""
        import random
        import string

        if self.unique_id:
            return self.unique_id

        
        while True:
            
            unique_id = "".join(random.choices(string.digits, k=12))

            
            if not User.objects.filter(unique_id=unique_id).exists():
                self.unique_id = unique_id
                self.save(update_fields=["unique_id"])
                return unique_id

    def ensure_unique_id(self):
        """Убеждается, что у пользователя есть уникальный ID"""
        if not self.unique_id:
            return self.generate_unique_id()
        return self.unique_id


class UserSession(models.Model):
    """Модель для отслеживания активных сессий пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="active_sessions"
    )
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.CharField(
        max_length=200, blank=True, verbose_name=_("Device info")
    )
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, verbose_name=_("IP address")
    )
    user_agent = models.TextField(blank=True, verbose_name=_("User agent"))
    location = models.CharField(max_length=100, blank=True, verbose_name=_("Location"))
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User session")
        verbose_name_plural = _("User sessions")
        ordering = ["-last_activity"]

    def __str__(self):
        return f"{self.user.username} - {self.device_info or 'Unknown device'}"

    @property
    def is_current_session(self):
        """Проверяет, является ли эта сессия текущей для пользователя"""
        from django.contrib.sessions.middleware import get_current_session_key

        return self.session_key == get_current_session_key()


class UserSettings(models.Model):
    """Модель для хранения настроек пользователя"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")

    
    theme = models.CharField(
        max_length=20,
        default="light",
        choices=[("light", "Светлая"), ("dark", "Тёмная"), ("auto", "Автоматическая")],
        verbose_name=_("Theme"),
    )

    ui_style = models.CharField(
        max_length=20,
        default="modern",
        choices=[
            ("modern", "Современный"),
            ("classic", "Классический"),
            ("minimal", "Минималистичный"),
            ("dark", "Тёмный"),
        ],
        verbose_name=_("UI Style"),
    )

    text_size = models.CharField(
        max_length=20,
        default="medium",
        choices=[("small", "Маленький"), ("medium", "Средний"), ("large", "Большой")],
        verbose_name=_("Text Size"),
    )

    
    push_notifications = models.BooleanField(
        default=True, verbose_name=_("Push notifications")
    )
    email_notifications = models.BooleanField(
        default=True, verbose_name=_("Email notifications")
    )
    message_notifications = models.BooleanField(
        default=True, verbose_name=_("Message notifications")
    )
    contest_notifications = models.BooleanField(
        default=False, verbose_name=_("Contest notifications")
    )

    
    show_in_search = models.BooleanField(default=True, verbose_name=_("Show in search"))
    show_online_status = models.BooleanField(
        default=True, verbose_name=_("Show online status")
    )
    show_stats = models.BooleanField(default=True, verbose_name=_("Show statistics"))

    
    personalized_recommendations = models.BooleanField(
        default=True, verbose_name=_("Personalized recommendations")
    )
    selected_interests = models.JSONField(
        default=list, verbose_name=_("Selected interests")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User settings")
        verbose_name_plural = _("User settings")

    def __str__(self):
        return f"{self.user.username} settings"


class UserProfileSettings(models.Model):
    """Основные настройки профиля пользователя"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile_settings"
    )

    
    show_online_status = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_typing_status = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_group_invites = models.BooleanField(default=True)
    who_can_add_to_groups = models.CharField(
        max_length=20,
        choices=[
            ("everyone", "Все"),
            ("contacts", "Только контакты"),
            ("nobody", "Никто"),
        ],
        default="everyone",
    )

    
    sync_contacts = models.BooleanField(default=True)
    suggest_frequent_contacts = models.BooleanField(default=True)

    
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    theme = models.CharField(
        max_length=20,
        choices=[
            ("light", "Светлая"),
            ("dark", "Темная"),
            ("system", "Как в системе"),
            ("blue", "Синяя"),
            ("green", "Зеленая"),
        ],
        default="dark",
    )
    accent_color = models.CharField(max_length=7, default="#6366f1")

    
    use_shared_background = models.BooleanField(default=True)
    custom_background = models.URLField(blank=True)
    background_type = models.CharField(
        max_length=20,
        choices=[
            ("default", "По умолчанию"),
            ("solid", "Сплошной цвет"),
            ("gradient", "Градиент"),
            ("image", "Изображение"),
        ],
        default="default",
    )
    solid_color = models.CharField(max_length=7, default="#000000")
    gradient_colors = models.JSONField(default=dict)
    custom_image = models.URLField(blank=True)
    background_effects = models.JSONField(default=dict)

    
    smooth_animations = models.BooleanField(default=True)
    scroll_effects = models.BooleanField(default=True)
    parallax_effect = models.BooleanField(default=False)
    truncate_names = models.BooleanField(default=True)
    compact_lists = models.BooleanField(default=True)
    hide_avatars = models.BooleanField(default=False)
    show_time_everywhere = models.BooleanField(default=False)
    small_emojis = models.BooleanField(default=True)
    high_contrast = models.BooleanField(default=False)

    
    is_premium = models.BooleanField(default=False)

    
    nickname_color = models.CharField(max_length=7, default="#6366f1")
    nickname_gradient_start = models.CharField(max_length=7, blank=True, null=True)
    nickname_gradient_end = models.CharField(max_length=7, blank=True, null=True)
    nickname_glow_enabled = models.BooleanField(default=False)
    nickname_glow_color = models.CharField(max_length=7, default="#6366f1")
    nickname_glow_intensity = models.IntegerField(default=1, choices=[(i, str(i)) for i in range(1, 6)])

    
    language = models.CharField(max_length=10, default="ru")
    timezone = models.CharField(max_length=50, default="Europe/Moscow")
    date_format = models.CharField(
        max_length=20,
        choices=[
            ("dd.mm.yyyy", "ДД.ММ.ГГГГ"),
            ("mm/dd/yyyy", "ММ/ДД/ГГГГ"),
            ("yyyy-mm-dd", "ГГГГ-ММ-ДД"),
        ],
        default="dd.mm.yyyy",
    )
    time_format = models.CharField(
        max_length=10, choices=[("24", "24 часа"), ("12", "12 часов")], default="24"
    )

    
    notification_sound = models.CharField(max_length=100, default="default")
    vibration = models.BooleanField(default=True)
    preview_content = models.BooleanField(default=True)

    
    login_notifications = models.BooleanField(default=True)
    password_changed_notification = models.BooleanField(default=True)

    
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    social_links = models.JSONField(
        default=list, blank=True, verbose_name="Ссылки на соцсети"
    )
    status = models.CharField(
        max_length=20,
        choices=[("online", "Онлайн"), ("away", "Отошёл"), ("invisible", "Невидимка")],
        default="online",
        blank=True,
        verbose_name="Статус",
    )

    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки профиля"
        verbose_name_plural = "Настройки профилей"


class TwoFactorAuth(models.Model):
    """Настройки двухфакторной аутентификации"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="two_factor"
    )
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)

    
    backup_codes = models.JSONField(default=list)  
    phone_number = models.CharField(max_length=20, blank=True)  
    email_enabled = models.BooleanField(default=True)  

    
    require_on_new_device = models.BooleanField(default=True)
    remember_device_days = models.IntegerField(
        default=30
    )  

    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def generate_secret(self):
        """Генерация нового секретного ключа"""
        self.secret_key = pyotp.random_base32()

    def generate_backup_codes(self, count=10):
        """Генерация резервных кодов"""
        import secrets

        self.backup_codes = [
            "-".join([secrets.token_hex(2).upper() for _ in range(2)])
            for _ in range(count)
        ]

    def generate_qr_code(self):
        """Генерация QR-кода для приложения аутентификатора"""
        if not self.secret_key:
            self.generate_secret()

        totp = pyotp.TOTP(self.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.email, issuer_name="Messenger App"
        )

        
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        return File(buffer, name=f"2fa_qr_{self.user.id}.png")

    def verify_code(self, code):
        """Проверка кода аутентификатора"""
        if not self.is_enabled or not self.secret_key:
            return False

        totp = pyotp.TOTP(self.secret_key)

        
        if totp.verify(code):
            self.last_used = timezone.now()
            self.save()
            return True

        
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True

        return False


class ActiveSession(models.Model):
    """Активные сессии пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.JSONField(default=dict)  
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    
    is_current = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "last_activity"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.device_info.get('device', 'Unknown')}"


class NotificationSettings(models.Model):
    """Детальные настройки уведомлений"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_settings"
    )

    
    message_notifications = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    call_notifications = models.BooleanField(default=True)
    mention_notifications = models.BooleanField(default=True)
    reaction_notifications = models.BooleanField(default=True)

    
    push_enabled = models.BooleanField(default=True)
    push_sound = models.BooleanField(default=True)
    push_vibration = models.BooleanField(default=True)
    push_preview = models.BooleanField(default=True)  

    
    email_enabled = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ("immediately", "Немедленно"),
            ("hourly", "Каждый час"),
            ("daily", "Ежедневно"),
            ("weekly", "Еженедельно"),
        ],
        default="immediately",
    )

    
    mute_until = models.DateTimeField(null=True, blank=True)
    do_not_disturb_start = models.TimeField(
        null=True, blank=True
    )  
    do_not_disturb_end = models.TimeField(null=True, blank=True)  

    
    override_chat_settings = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)


class PrivacySettings(models.Model):
    """Настройки приватности"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="privacy_settings"
    )

    
    who_can_see_phone = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="contacts",
    )

    who_can_see_email = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="contacts",
    )

    who_can_see_last_seen = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="everyone",
    )

    who_can_see_profile_photo = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="everyone",
    )

    
    blocked_users = models.ManyToManyField(User, related_name="blocked_by", blank=True)

    
    allow_message_forwarding = models.BooleanField(default=True)

    
    who_can_call = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="everyone",
    )

    
    who_can_add_to_groups = models.CharField(
        max_length=20,
        choices=[("everyone", "Все"), ("contacts", "Контакты"), ("nobody", "Никто")],
        default="everyone",
    )


class UserTheme(models.Model):
    """Пользовательские темы"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="themes")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    
    primary_color = models.CharField(max_length=7, default="#6366f1")
    secondary_color = models.CharField(max_length=7, default="#4a4d65")
    background_color = models.CharField(max_length=7, default="#1a1b26")
    card_background = models.CharField(max_length=7, default="#24283b")
    hover_background = models.CharField(max_length=7, default="#363b52")
    text_color = models.CharField(max_length=7, default="#a9b1d6")
    secondary_text_color = models.CharField(max_length=7, default="#7aa2f7")
    border_color = models.CharField(max_length=7, default="#414868")

    
    message_bubble_radius = models.IntegerField(default=12)  
    show_message_time = models.BooleanField(default=True)
    compact_mode = models.BooleanField(default=False)

    
    chat_background = models.ImageField(
        upload_to="chat_backgrounds/", null=True, blank=True
    )
    chat_background_opacity = models.FloatField(default=0.1)  

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "name"]

    def apply_to_user(self):
        """Применить тему к пользователю"""
        
        profile_settings = self.user.profile_settings
        profile_settings.theme = "custom"
        profile_settings.accent_color = self.primary_color
        profile_settings.save()

        
        UserTheme.objects.filter(user=self.user).exclude(id=self.id).update(
            is_active=False
        )

        self.is_active = True
        self.save()

    def to_css_variables(self):
        """Преобразовать в CSS переменные"""
        return {
            "--primary-color": self.primary_color,
            "--secondary-color": self.secondary_color,
            "--background-color": self.background_color,
            "--card-bg": self.card_background,
            "--hover-bg": self.hover_background,
            "--text-color": self.text_color,
            "--secondary-text": self.secondary_text_color,
            "--border-color": self.border_color,
            "--message-bubble-radius": f"{self.message_bubble_radius}px",
            "--chat-background-opacity": self.chat_background_opacity,
        }


class FontSettings(models.Model):
    """Настройки шрифтов пользователя"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="font_settings"
    )

    
    font_family = models.CharField(max_length=50, default="system")
    font_size = models.IntegerField(default=14)  
    interface_scale = models.IntegerField(default=100)  

    
    line_height = models.FloatField(default=1.5)

    
    density = models.CharField(
        max_length=20,
        choices=[
            ("compact", "Компактный"),
            ("comfortable", "Удобный"),
            ("spacious", "Просторный"),
        ],
        default="comfortable",
    )

    
    bold_headings = models.BooleanField(default=True)
    increase_line_height = models.BooleanField(default=False)
    monospace_code = models.BooleanField(default=True)
    reduce_motion = models.BooleanField(default=False)
    high_contrast_mode = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.font_family} {self.font_size}px"


class SyncSettings(models.Model):
    """Настройки синхронизации пользователя"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="sync_settings"
    )

    
    sync_playlists = models.BooleanField(default=True)
    sync_settings = models.BooleanField(default=True)
    sync_favorites = models.BooleanField(default=True)
    sync_history = models.BooleanField(default=True)
    sync_drafts = models.BooleanField(default=True)
    sync_watchlist = models.BooleanField(default=True)

    
    sync_condition = models.CharField(
        max_length=20,
        choices=[
            ("auto", "Автоматически"),
            ("manual", "Вручную"),
            ("schedule", "По расписанию"),
        ],
        default="auto",
    )
    sync_schedule = models.CharField(
        max_length=20,
        choices=[
            ("hourly", "Каждый час"),
            ("daily", "Каждый день"),
            ("weekly", "Каждую неделю"),
        ],
        default="daily",
    )

    
    wifi_only = models.BooleanField(default=True)
    charging_only = models.BooleanField(default=False)

    
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ("idle", "Ожидает"),
            ("syncing", "Синхронизация"),
            ("synced", "Синхронизировано"),
            ("error", "Ошибка"),
        ],
        default="idle",
    )
    last_sync_time = models.DateTimeField(null=True, blank=True)
    next_sync_time = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.sync_condition}"


class DataExport(models.Model):
    """Запросы на экспорт данных"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="data_exports"
    )

    items = models.JSONField(default=list)  
    format = models.CharField(
        max_length=10,
        choices=[
            ("json", "JSON"),
            ("csv", "CSV"),
            ("html", "HTML"),
        ],
        default="json",
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("processing", "Обработка"),
            ("ready", "Готов"),
            ("expired", "Истёк"),
            ("failed", "Ошибка"),
        ],
        default="processing",
    )

    size = models.CharField(max_length=20, blank=True)  
    download_url = models.URLField(blank=True)
    file_path = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.format} ({self.status})"


class ChatBackground(models.Model):
    """Фоны для чатов"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_backgrounds"
    )
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="chat_backgrounds/")
    thumbnail = models.ImageField(upload_to="chat_backgrounds/thumbnails/")
    is_default = models.BooleanField(default=False)
    opacity = models.FloatField(default=0.1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "name"]


class SecurityLog(models.Model):
    """Лог событий безопасности"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(
        max_length=100
    )  
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    additional_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action"]),
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
            models.Index(fields=["user", "sent_at"]),
        ]


class MessageNotification(models.Model):
    """Отслеживание отправленных уведомлений о сообщениях"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey("social.Message", on_delete=models.CASCADE)
    notified_via = models.CharField(
        max_length=20,
        choices=[
            ("push", "Push уведомление"),
            ("email", "Email уведомление"),
            ("sms", "SMS уведомление"),
        ],
    )
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "message", "notified_via"]


class UserAnalytics(models.Model):
    """Статистика использования приложения"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="analytics"
    )

    
    messages_sent = models.IntegerField(default=0)
    messages_received = models.IntegerField(default=0)
    media_sent = models.IntegerField(default=0)
    calls_made = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)  

    
    favorite_chat_type = models.CharField(max_length=20, blank=True)  
    most_active_hour = models.IntegerField(null=True, blank=True)  
    average_response_time = models.IntegerField(default=0)  

    
    primary_device = models.CharField(max_length=100, blank=True)
    last_used_device = models.CharField(max_length=100, blank=True)

    
    last_updated = models.DateTimeField(auto_now=True)
    collected_since = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Analytics"

    def update_activity(self, activity_type, **kwargs):
        """Обновить статистику активности"""
        if activity_type == "message_sent":
            self.messages_sent += 1
        elif activity_type == "message_received":
            self.messages_received += 1
        elif activity_type == "media_sent":
            self.media_sent += 1
        elif activity_type == "call_made":
            self.calls_made += 1
        elif activity_type == "time_spent":
            self.time_spent += kwargs.get("minutes", 0)

        self.save()

    def get_weekly_report(self):
        """Получить недельный отчет"""
        from datetime import datetime, timedelta

        week_ago = timezone.now() - timedelta(days=7)

        return {
            "messages_sent": self.get_messages_since(week_ago, "sent"),
            "time_spent": self.get_time_spent_since(week_ago),
            "most_active_day": self.get_most_active_day(week_ago),
            "top_chats": self.get_top_chats(week_ago, limit=5),
        }

    def get_messages_since(self, since_date, direction="sent"):
        """Получить количество сообщений с указанной даты"""
        from social.models import Message

        if direction == "sent":
            return Message.objects.filter(
                sender=self.user, created_at__gte=since_date
            ).count()
        else:
            return (
                Message.objects.filter(
                    chat__members__user=self.user, created_at__gte=since_date
                )
                .exclude(sender=self.user)
                .count()
            )

    def get_time_spent_since(self, since_date):
        """Получить время, проведенное в приложении с указанной даты"""
        sessions = UserSession.objects.filter(
            user=self.user, start_time__gte=since_date
        )

        total_seconds = sum(
            (s.end_time or timezone.now() - s.start_time).total_seconds()
            for s in sessions
        )

        return int(total_seconds / 60)  

    def get_most_active_day(self, since_date):
        """Получить самый активный день"""
        
        return "нот релизед"  

    def get_top_chats(self, since_date, limit=5):
        """Получить топ чатов по активности"""
        
        return []  


def validate_rating(value):
    """Валидатор для оценки аниме"""
    if value is not None and (value < 1 or value > 10):
        raise ValidationError("Оценка должна быть от 1 до 10")


class UserFavorite(models.Model):
    """Избранное аниме пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    anime = models.ForeignKey(
        "anime.Anime", on_delete=models.CASCADE, related_name="in_favorites"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "anime"]
        indexes = [
            models.Index(fields=["user", "added_at"]),
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru}"


class FavoriteTheme(models.Model):
    """Избранные опенинги/эндинги пользователя"""

    THEME_TYPE_CHOICES = [
        ("opening", "Опенинг"),
        ("ending", "Эндинг"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_themes"
    )
    anime = models.ForeignKey(
        "anime.Anime", on_delete=models.CASCADE, related_name="favorite_themes"
    )
    theme_type = models.CharField(max_length=20, choices=THEME_TYPE_CHOICES)
    episode = models.IntegerField()
    season = models.IntegerField(default=1)
    title = models.CharField(max_length=255, blank=True)  
    start_time = models.IntegerField(default=0)  
    end_time = models.IntegerField(null=True, blank=True)  
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "anime", "theme_type", "episode", "season"]
        indexes = [
            models.Index(fields=["user", "anime", "theme_type"]),
            models.Index(fields=["user", "added_at"]),
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_theme_type_display()} серия {self.episode} ({self.anime.title_ru})"


class FavoriteEpisode(models.Model):
    """Избранные серии пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_episodes"
    )
    anime = models.ForeignKey(
        "anime.Anime", on_delete=models.CASCADE, related_name="favorite_episodes"
    )
    episode = models.IntegerField()
    season = models.IntegerField(default=1)
    note = models.CharField(max_length=255, blank=True)  
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "anime", "episode", "season"]
        indexes = [
            models.Index(fields=["user", "anime", "episode"]),
            models.Index(fields=["user", "added_at"]),
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - Серия {self.episode} ({self.anime.title_ru})"


class UserLibrary(models.Model):
    """Библиотека аниме пользователя (Моя коллекция)"""

    STATUS_CHOICES = [
        ("started", "В процессе"),
        ("completed", "Просмотрено"),
        ("on_hold", "Отложено"),
        ("dropped", "Брошено"),
        ("planned", "В планах"),
        ("favorite", "Любимое"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="library")
    anime = models.ForeignKey(
        "anime.Anime", on_delete=models.CASCADE, related_name="in_libraries"
    )

    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")

    
    current_episode = models.IntegerField(default=0)  
    episodes_watched = models.IntegerField(default=0)  

    
    rating = models.IntegerField(null=True, blank=True, validators=[validate_rating])

    
    added_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)  
    completed_at = models.DateTimeField(
        null=True, blank=True
    )  
    updated_at = models.DateTimeField(auto_now=True)

    
    notes = models.TextField(blank=True)  
    is_favorite = models.BooleanField(
        default=False
    )  

    
    rewatch_count = models.IntegerField(default=0)  

    class Meta:
        unique_together = ["user", "anime"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "added_at"]),
            models.Index(fields=["user", "rating"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru} ({self.get_status_display()})"

    def update_progress(self, episode):
        """Обновить прогресс просмотра"""
        self.current_episode = episode
        self.episodes_watched = max(self.episodes_watched, episode)

        
        if self.status == "planned" and episode > 0:
            self.status = "started"
            if not self.started_at:
                self.started_at = timezone.now()

        
        if self.anime and self.anime.episodes and episode >= self.anime.episodes:
            self.status = "completed"
            if not self.completed_at:
                self.completed_at = timezone.now()

        self.save(
            update_fields=[
                "current_episode",
                "episodes_watched",
                "status",
                "started_at",
                "completed_at",
                "updated_at",
            ]
        )

    def get_progress_percentage(self):
        """Получить прогресс в процентах"""
        if not self.anime or not self.anime.episodes or self.anime.episodes == 0:
            return 0
        return int((self.current_episode / self.anime.episodes) * 100)

    def mark_as_favorite(self):
        """Отметить как любимое"""
        self.is_favorite = True
        self.save(update_fields=["is_favorite", "updated_at"])





class SupportTicket(models.Model):
    """Обращение в поддержку"""

    STATUS_CHOICES = [
        ("open", "Открыто"),
        ("in_progress", "В работе"),
        ("waiting", "Ожидание ответа"),
        ("resolved", "Решено"),
        ("closed", "Закрыто"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
        ("urgent", "Срочный"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_tickets"
    )
    subject = models.CharField(max_length=200, verbose_name="Тема")
    description = models.TextField(verbose_name="Описание")
    category = models.CharField(
        max_length=50,
        choices=[
            ("general", "Общий вопрос"),
            ("account", "Проблема с аккаунтом"),
            ("payment", "Оплата"),
            ("bug", "Баг/ошибка"),
            ("content", "Контент"),
            ("other", "Другое"),
        ],
        default="general",
        verbose_name="Категория",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="Статус"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
        verbose_name="Приоритет",
    )

    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Назначенный админ",
    )

    
    chat_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ID чата"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Решено")

    class Meta:
        verbose_name = "Обращение в поддержку"
        verbose_name_plural = "Обращения в поддержку"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "priority"]),
        ]

    def __str__(self):
        return f"Support Ticket: {self.subject} ({self.status})"


class SupportMessage(models.Model):
    """Сообщение в обращении поддержки"""

    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_messages"
    )
    message = models.TextField(verbose_name="Сообщение")
    is_from_admin = models.BooleanField(default=False, verbose_name="От админа")

    
    attachments = models.JSONField(default=list, verbose_name="Вложения")

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
        ]

    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.sender.username}"


class Subscription(models.Model):
    """Подписка пользователя"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription"
    )
    is_active = models.BooleanField(default=False, verbose_name="Подписка активна")

    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата начала")
    expires_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата окончания"
    )

    
    auto_renew = models.BooleanField(default=True, verbose_name="Автопродление")

    
    payment_method = models.CharField(
        max_length=50, blank=True, verbose_name="Способ оплаты"
    )
    transaction_id = models.CharField(
        max_length=100, blank=True, verbose_name="ID транзакции"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user.username} - {'Активна' if self.is_active else 'Неактивна'}"

    @property
    def is_premium(self) -> bool:
        """Проверяет активна ли подписка"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def activate(self, days: int = 30, payment_method: str = "promo"):
        """Активирует подписку на указанное количество дней"""
        from django.utils import timezone

        now = timezone.now()

        
        if self.is_active and self.expires_at and self.expires_at > now:
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            self.started_at = now
            self.expires_at = now + timedelta(days=days)

        self.is_active = True
        self.payment_method = payment_method
        self.save()

    def deactivate(self):
        """Деактивирует подписку"""
        self.is_active = False
        self.expires_at = None
        self.save()


class PromoCode(models.Model):
    """Промокод для скидки на подписку"""

    code = models.CharField(max_length=50, unique=True, verbose_name="Код")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Скидка %")
    discount_amount = models.PositiveIntegerField(
        default=0, verbose_name="Скидка в рублях"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    max_uses = models.PositiveIntegerField(
        default=1, verbose_name="Максимум использований"
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name="Использовано")
    valid_until = models.DateTimeField(
        null=True, blank=True, verbose_name="Действителен до"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}% или {self.discount_amount}₽)"

    def is_valid(self) -> bool:
        """Проверяет валидность промокода"""
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.valid_until and self.valid_until < timezone.now():
            return False
        return True

    def get_discount(self, base_price: int = 399) -> int:
        """Рассчитывает скидку"""
        if self.discount_percent > 0:
            return int(base_price * self.discount_percent / 100)
        return self.discount_amount


class PromoCodeUsage(models.Model):
    """Использование промокода"""

    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.CASCADE, related_name="usages"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="promo_usages"
    )
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Использование промокода"
        verbose_name_plural = "Использования промокодов"
        unique_together = ["promo_code", "user"]

    def __str__(self):
        return f"{self.user.username} использовал {self.promo_code.code}"



from datetime import timedelta
