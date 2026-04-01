from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    FavoriteEpisode, FavoriteTheme, User, UserFavorite, UserSession, UserSettings, UserProfileSettings, TwoFactorAuth,
    ActiveSession, NotificationSettings, PrivacySettings, UserTheme,
    ChatBackground, EmailLog, MessageNotification, UserAnalytics, UserLibrary
)


class UserSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор пользователя для списков"""
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'display_name', 'avatar_url', 'is_online', 'last_login', 'level', 'bio']

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_display_name(self, obj):
        return obj.display_name or obj.nickname or obj.username


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    avatar_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    display_name_computed = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'unique_id', 'username', 'email', 'first_name', 'last_name', 'display_name',
            'display_name_computed', 'nickname', 'phone_number', 'avatar', 'avatar_url',
            'cover_image', 'cover_image_url', 'bio', 'favorite_genres',
            'website', 'vk_profile', 'telegram', 'email_verified',
            'phone_verified', 'two_factor_enabled', 'is_online', 'last_login',
            'created_at', 'updated_at', 'level', 'experience', 'mana', 'badges',
            'posts_count', 'comments_count', 'likes_received', 'playlists_count',
            'is_staff', 'is_admin',
        ]
        read_only_fields = ['id', 'unique_id', 'created_at', 'updated_at', 'level', 'experience', 'mana', 'badges', 'posts_count', 'comments_count', 'likes_received', 'playlists_count', 'is_staff']

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_display_name_computed(self, obj):
        return obj.display_name or obj.nickname or obj.username

    def get_is_admin(self, obj):
        return obj.is_staff or obj.is_superuser or obj.username == 'kaiden812'


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone_number', 'first_name', 'last_name',
            'password', 'password_confirm'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")

        # Проверяем, что указан либо email, либо телефон
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Необходимо указать email или телефон")

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        # При регистрации сразу устанавливаем nickname = username,
        # чтобы не было двойного никнейма при первом входе через Google/емайл
        if not user.nickname:
            user.nickname = user.username
        if not user.display_name:
            user.display_name = user.username
        user.save(update_fields=['nickname', 'display_name'])
        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор входа"""

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        data['user'] = user
        return data


class GoogleAuthSerializer(serializers.Serializer):
    """Сериализатор Google аутентификации"""

    id_token = serializers.CharField()


class PhoneVerificationSerializer(serializers.Serializer):
    """Сериализатор верификации телефона"""

    phone_number = serializers.CharField()
    action = serializers.ChoiceField(choices=['send', 'verify'])
    code = serializers.CharField(required=False, min_length=6, max_length=6)


class EmailVerificationSerializer(serializers.Serializer):
    """Сериализатор верификации email"""

    email = serializers.EmailField()
    action = serializers.ChoiceField(choices=['send', 'verify'])
    code = serializers.CharField(required=False, min_length=8, max_length=8)


class PasswordResetSerializer(serializers.Serializer):
    """Сериализатор сброса пароля"""

    email = serializers.EmailField()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор обновления профиля пользователя"""

    class Meta:
        model = User
        fields = [
            'display_name', 'nickname', 'avatar', 'cover_image', 'bio', 'favorite_genres',
            'website', 'vk_profile', 'telegram'
        ]

    def validate_nickname(self, value):
        """Проверка уникальности nickname"""
        if value and User.objects.filter(nickname=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Этот nickname уже занят")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессий пользователя"""

    is_current = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id', 'session_key', 'device_info', 'ip_address', 'location',
            'last_activity', 'created_at', 'is_current'
        ]
        read_only_fields = ['id', 'session_key', 'created_at']

    def get_is_current(self, obj):
        # Упрощенная версия - определяем по времени последней активности
        # В реальном приложении нужно сравнивать с текущей сессией
        from django.utils import timezone
        # Считаем сессию текущей, если активность была в последние 5 минут
        return (timezone.now() - obj.last_activity).seconds < 300


class UserSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор настроек пользователя"""

    def validate_theme(self, value):
        """Валидация темы"""
        valid_themes = ['light', 'dark', 'auto']
        if value not in valid_themes:
            raise serializers.ValidationError(f"Недопустимая тема. Допустимые значения: {', '.join(valid_themes)}")
        return value

    def validate_ui_style(self, value):
        """Валидация стиля интерфейса"""
        valid_styles = ['modern', 'classic', 'minimal', 'dark']
        if value not in valid_styles:
            raise serializers.ValidationError(f"Недопустимый стиль интерфейса. Допустимые значения: {', '.join(valid_styles)}")
        return value

    def validate_text_size(self, value):
        """Валидация размера текста"""
        valid_sizes = ['small', 'medium', 'large']
        if value not in valid_sizes:
            raise serializers.ValidationError(f"Недопустимый размер текста. Допустимые значения: {', '.join(valid_sizes)}")
        return value

    def validate_selected_interests(self, value):
        """Валидация выбранных интересов"""
        if not isinstance(value, list):
            raise serializers.ValidationError("selected_interests должен быть списком")

        # Ограничиваем количество интересов
        if len(value) > 20:
            raise serializers.ValidationError("Максимум 20 интересов")

        # Проверяем что все значения - строки
        if not all(isinstance(interest, str) for interest in value):
            raise serializers.ValidationError("Все интересы должны быть строками")

        # Ограничиваем длину каждого интереса
        for interest in value:
            if len(interest) > 50:
                raise serializers.ValidationError("Длина каждого интереса не должна превышать 50 символов")

        return value

    class Meta:
        model = UserSettings
        fields = [
            'theme', 'ui_style', 'text_size', 'push_notifications',
            'email_notifications', 'message_notifications', 'contest_notifications',
            'show_in_search', 'show_online_status', 'show_stats',
            'personalized_recommendations', 'selected_interests',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NicknameCheckSerializer(serializers.Serializer):
    """Сериализатор проверки доступности nickname"""

    nickname = serializers.CharField(max_length=30)

    def validate_nickname(self, value):
        """Проверка nickname на корректность"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Nickname может содержать только буквы, цифры, подчеркивания и дефисы")

        # Проверяем доступность
        available = not User.objects.filter(nickname=value).exists()
        if not available:
            raise serializers.ValidationError("Этот nickname уже занят")

        return value


class TwoFactorSetupSerializer(serializers.Serializer):
    """Сериализатор настройки 2FA"""

    action = serializers.ChoiceField(choices=['enable', 'disable', 'verify'])
    code = serializers.CharField(required=False, min_length=6, max_length=6)


class UserProfileSettingsSerializer(serializers.ModelSerializer):
    """Полный сериализатор настроек профиля пользователя"""
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    user_bio = serializers.CharField(source='user.bio', read_only=True)
    user_favorite_genres = serializers.JSONField(source='user.favorite_genres', read_only=True)
    user_website = serializers.URLField(source='user.website', read_only=True)
    user_vk_profile = serializers.CharField(source='user.vk_profile', read_only=True)
    user_telegram = serializers.CharField(source='user.telegram', read_only=True)
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfileSettings
        fields = '__all__'
        read_only_fields = ['user', 'updated_at']

    def to_representation(self, instance):
        """Преобразуем имена полей для API"""
        data = super().to_representation(instance)
        # Добавляем поля для совместимости с frontend
        data['notification_sound'] = instance.notification_sound
        data['vibration'] = instance.vibration
        data['preview_content'] = instance.preview_content
        return data

    def validate_theme(self, value):
        """Валидация темы"""
        valid_themes = ['light', 'dark', 'system', 'blue', 'green']
        if value not in valid_themes:
            raise serializers.ValidationError(f"Недопустимая тема. Допустимые значения: {', '.join(valid_themes)}")
        return value

    def validate_accent_color(self, value):
        """Валидация акцентного цвета"""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError("Недопустимый формат цвета. Используйте формат #RRGGBB")
        return value

    def validate_language(self, value):
        """Валидация языка"""
        valid_languages = ['ru', 'en', 'uk', 'be', 'kk']
        if value not in valid_languages:
            raise serializers.ValidationError(f"Недопустимый язык. Допустимые значения: {', '.join(valid_languages)}")
        return value

    def validate_timezone(self, value):
        """Валидация часового пояса"""
        try:
            import pytz
            pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise serializers.ValidationError(f"Недопустимый часовой пояс: {value}")
        return value


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Полный сериализатор настроек уведомлений"""
    enabled = serializers.BooleanField(required=False)
    sound_enabled = serializers.BooleanField(required=False)
    vibration_enabled = serializers.BooleanField(required=False)
    preview_enabled = serializers.BooleanField(required=False)

    push_sound_enabled = serializers.BooleanField(required=False, source='push_sound')
    push_vibration_enabled = serializers.BooleanField(required=False, source='push_vibration')
    push_preview_enabled = serializers.BooleanField(required=False, source='push_preview')

    class Meta:
        model = NotificationSettings
        fields = '__all__'
        read_only_fields = ['user', 'updated_at']

    def to_representation(self, instance):
        """Преобразуем имена полей для API"""
        data = super().to_representation(instance)
        # Добавляем поля для совместимости с frontend
        data['enabled'] = True  # Всегда включен, если есть настройки
        data['sound_enabled'] = True  # Можно расширить логику
        data['vibration_enabled'] = instance.push_vibration if hasattr(instance, 'push_vibration') else True
        data['preview_enabled'] = instance.push_preview if hasattr(instance, 'push_preview') else True
        data['push_sound_enabled'] = instance.push_sound if hasattr(instance, 'push_sound') else True
        data['push_vibration_enabled'] = instance.push_vibration if hasattr(instance, 'push_vibration') else True
        data['push_preview_enabled'] = instance.push_preview if hasattr(instance, 'push_preview') else True
        data['do_not_disturb_enabled'] = instance.do_not_disturb_start is not None and instance.do_not_disturb_end is not None
        return data

    def validate_email_frequency(self, value):
        """Валидация частоты email"""
        valid_frequencies = ['immediately', 'hourly', 'daily', 'weekly']
        if value not in valid_frequencies:
            raise serializers.ValidationError(f"Недопустимая частота. Допустимые значения: {', '.join(valid_frequencies)}")
        return value

    def validate(self, data):
        """Проверка периода не беспокоить"""
        do_not_disturb_start = data.get('do_not_disturb_start', self.instance.do_not_disturb_start if self.instance else None)
        do_not_disturb_end = data.get('do_not_disturb_end', self.instance.do_not_disturb_end if self.instance else None)

        if do_not_disturb_start and do_not_disturb_end:
            if do_not_disturb_start >= do_not_disturb_end:
                raise serializers.ValidationError("Время начала должно быть раньше времени окончания")

        return data


class PrivacySettingsSerializer(serializers.ModelSerializer):
    """Полный сериализатор настроек приватности"""
    blocked_users_list = serializers.SerializerMethodField()

    show_online_status = serializers.BooleanField(required=False)
    show_last_seen = serializers.BooleanField(required=False)
    show_typing_status = serializers.BooleanField(required=False)
    allow_calls = serializers.BooleanField(required=False)
    allow_group_invites = serializers.BooleanField(required=False)

    class Meta:
        model = PrivacySettings
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        """Преобразуем имена полей для API"""
        data = super().to_representation(instance)
        # Добавляем поля из UserProfileSettings для совместимости
        try:
            profile_settings = instance.user.profile_settings
            data['show_online_status'] = profile_settings.show_online_status
            data['show_last_seen'] = profile_settings.show_last_seen
            data['show_typing_status'] = profile_settings.show_typing_status
            data['allow_calls'] = profile_settings.allow_calls
            data['allow_group_invites'] = profile_settings.allow_group_invites
        except:
            # Если профильные настройки не существуют, используем значения по умолчанию
            data['show_online_status'] = True
            data['show_last_seen'] = True
            data['show_typing_status'] = True
            data['allow_calls'] = True
            data['allow_group_invites'] = True
        return data

    def get_blocked_users_list(self, obj):
        """Получить список заблокированных пользователей"""
        return UserSimpleSerializer(obj.blocked_users.all(), many=True).data

    def validate_who_can_see_phone(self, value):
        """Валидация настройки видимости телефона"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value

    def validate_who_can_see_email(self, value):
        """Валидация настройки видимости email"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value

    def validate_who_can_see_last_seen(self, value):
        """Валидация настройки видимости последнего визита"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value

    def validate_who_can_see_profile_photo(self, value):
        """Валидация настройки видимости фото профиля"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value

    def validate_who_can_call(self, value):
        """Валидация настройки звонков"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value

    def validate_who_can_add_to_groups(self, value):
        """Валидация настройки добавления в группы"""
        valid_values = ['everyone', 'contacts', 'nobody']
        if value not in valid_values:
            raise serializers.ValidationError(f"Недопустимое значение. Допустимые: {', '.join(valid_values)}")
        return value


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    has_backup_codes = serializers.SerializerMethodField()
    backup_codes_count = serializers.SerializerMethodField()

    class Meta:
        model = TwoFactorAuth
        fields = '__all__'
        read_only_fields = ['user', 'secret_key', 'created_at', 'last_used']
        extra_kwargs = {
            'backup_codes': {'write_only': True}
        }

    def get_qr_code_url(self, obj):
        if obj.secret_key:
            return f'/api/auth/2fa/qr/{obj.user.id}/'
        return None

    def get_has_backup_codes(self, obj):
        return len(obj.backup_codes) > 0

    def get_backup_codes_count(self, obj):
        return len(obj.backup_codes)


class TwoFactorSettingsSerializer(serializers.Serializer):
    """Сериализатор для обновления настроек 2FA"""
    require_on_new_device = serializers.BooleanField(required=False)
    remember_device_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    email_enabled = serializers.BooleanField(required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def validate_phone_number(self, value):
        """Валидация номера телефона"""
        if value:
            user = self.context['request'].user
            if not user.phone_verified:
                raise serializers.ValidationError(
                    "Необходимо подтвердить номер телефона для использования SMS 2FA"
                )
        return value


class ActiveSessionSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    is_current_device = serializers.BooleanField(source='is_current')

    class Meta:
        model = ActiveSession
        exclude = ['session_key']
        read_only_fields = ['user', 'created_at', 'last_activity']

    def get_device_name(self, obj):
        device = obj.device_info.get('device', 'Неизвестное устройство')
        browser = obj.device_info.get('browser', 'Неизвестный браузер')
        return f"{device} ({browser})"

    def get_location(self, obj):
        if obj.country and obj.city:
            return f"{obj.city}, {obj.country}"
        return "Неизвестно"


class UserThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTheme
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class ChatBackgroundSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBackground
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'
        read_only_fields = ['user', 'sent_at']


class MessageNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageNotification
        fields = '__all__'
        read_only_fields = ['user', 'notified_at']


class UserAnalyticsSerializer(serializers.ModelSerializer):
    weekly_report = serializers.SerializerMethodField()

    class Meta:
        model = UserAnalytics
        fields = '__all__'
        read_only_fields = ['user', 'last_updated', 'collected_since']

    def get_weekly_report(self, obj):
        return obj.get_weekly_report()


class UserFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного аниме"""
    anime_title_ru = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_episodes = serializers.IntegerField(source='anime.episodes', read_only=True)
    anime_kind = serializers.CharField(source='anime.kind', read_only=True)
    anime_year = serializers.IntegerField(source='anime.year', read_only=True)

    class Meta:
        model = UserFavorite
        fields = [
            'id', 'anime', 'anime_title_ru', 'anime_title_en', 'anime_poster',
            'anime_episodes', 'anime_kind', 'anime_year', 'added_at'
        ]
        read_only_fields = ['id', 'user', 'added_at']

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            return obj.anime.poster.url
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None


class FavoriteThemeSerializer(serializers.ModelSerializer):
    """Сериализатор избранных опенингов/эндингов"""
    anime_title_ru = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    theme_type_display = serializers.CharField(source='get_theme_type_display', read_only=True)

    class Meta:
        model = FavoriteTheme
        fields = [
            'id', 'anime', 'anime_title_ru', 'anime_title_en',
            'theme_type', 'theme_type_display', 'episode', 'season',
            'title', 'start_time', 'end_time', 'added_at'
        ]
        read_only_fields = ['id', 'user', 'added_at']


class FavoriteEpisodeSerializer(serializers.ModelSerializer):
    """Сериализатор избранных серий"""
    anime_title_ru = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteEpisode
        fields = [
            'id', 'anime', 'anime_title_ru', 'anime_title_en', 'anime_poster',
            'episode', 'season', 'note', 'added_at'
        ]
        read_only_fields = ['id', 'user', 'added_at']

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            return obj.anime.poster.url
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None


class UserLibrarySerializer(serializers.ModelSerializer):
    """Сериализатор библиотеки аниме пользователя"""
    anime_title_ru = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_episodes_count = serializers.IntegerField(source='anime.episodes', read_only=True)
    anime_status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserLibrary
        fields = [
            'id', 'user', 'anime', 'anime_title_ru', 'anime_title_en', 'anime_poster',
            'anime_episodes_count', 'status', 'anime_status_display',
            'current_episode', 'episodes_watched', 'rating',
            'added_at', 'started_at', 'completed_at', 'updated_at',
            'notes', 'is_favorite', 'rewatch_count', 'progress_percentage'
        ]
        read_only_fields = ['id', 'user', 'added_at', 'updated_at']

    def get_anime_poster(self, obj):
        """Получаем URL постера - сначала локальный, потом внешний"""
        # Сначала пробуем получить локальный постер
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            return obj.anime.poster.url
        # Если нет локального, используем внешний URL
        if obj.anime.poster_url:
            return obj.anime.poster_url
        return None

    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()


class UserLibraryCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления аниме в библиотеку"""

    class Meta:
        model = UserLibrary
        fields = ['anime', 'status', 'rating', 'notes', 'is_favorite', 'current_episode', 'episodes_watched']
        extra_kwargs = {
            'status': {'required': False},
            'current_episode': {'required': False},
            'episodes_watched': {'required': False},
        }

    def create(self, validated_data):
        user = self.context['request'].user
        anime = validated_data['anime']

        # get_or_create — не дублируем
        library_item, created = UserLibrary.objects.get_or_create(
            user=user,
            anime=anime,
            defaults=validated_data
        )

        if not created:
            # Обновляем только переданные поля
            for key, value in validated_data.items():
                if key != 'anime':
                    # Серию обновляем только если новая больше
                    if key == 'current_episode':
                        if value > (library_item.current_episode or 0):
                            setattr(library_item, key, value)
                    elif key == 'episodes_watched':
                        if value > (library_item.episodes_watched or 0):
                            setattr(library_item, key, value)
                    else:
                        setattr(library_item, key, value)
            library_item.save()

        return library_item


class UserLibraryUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления библиотеки"""

    class Meta:
        model = UserLibrary
        fields = ['status', 'current_episode', 'episodes_watched', 'rating', 'notes', 'is_favorite']

    def update(self, instance, validated_data):
        # Обновляем прогресс
        if 'current_episode' in validated_data:
            new_episode = validated_data['current_episode']
            instance.current_episode = new_episode
            instance.episodes_watched = max(instance.episodes_watched, new_episode)

            # Авто-старт: если начали смотреть
            if new_episode > 0 and instance.status == 'planned':
                instance.status = 'started'
                if not instance.started_at:
                    instance.started_at = timezone.now()

            # Авто-завершение: если досмотрели все эпизоды
            total = instance.anime.episodes if instance.anime and instance.anime.episodes else None
            if total and new_episode >= total and instance.status not in ('completed',):
                instance.status = 'completed'
                if not instance.completed_at:
                    instance.completed_at = timezone.now()

        # Обновляем статус если явно указан (перезаписывает авто-логику)
        if 'status' in validated_data:
            instance.status = validated_data['status']
            if instance.status == 'started' and not instance.started_at:
                instance.started_at = timezone.now()
            if instance.status == 'completed' and not instance.completed_at:
                instance.completed_at = timezone.now()

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            if attr not in ['status', 'current_episode']:
                setattr(instance, attr, value)

        instance.save()
        return instance


class UserLibraryProgressSerializer(serializers.Serializer):
    """Сериализатор для обновления прогресса просмотра"""
    episode = serializers.IntegerField(min_value=0)

    def validate_episode(self, value):
        """Проверяем номер эпизода"""
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        """Проверка текущего пароля"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def validate_new_password(self, value):
        """Проверка сложности нового пароля"""
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов")

        # Проверка на наличие букв и цифр
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)

        if not has_letter:
            raise serializers.ValidationError("Пароль должен содержать минимум одну букву")
        if not has_digit:
            raise serializers.ValidationError("Пароль должен содержать минимум одну цифру")

        # Проверка на совпадение с username или email
        user = self.context['request'].user
        if user.username.lower() in value.lower():
            raise serializers.ValidationError("Пароль не должен содержать ваш логин")
        if user.email and user.email.split('@')[0].lower() in value.lower():
            raise serializers.ValidationError("Пароль не должен содержать часть вашего email")

        return value

    def validate(self, attrs):
        """Проверка совпадения паролей"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Пароли не совпадают"
            })

        # Проверка, что новый пароль отличается от старого
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                "new_password": "Новый пароль должен отличаться от текущего"
            })

        return attrs

    def save(self):
        """Смена пароля"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()

        # Логируем смену пароля
        from .models import SecurityLog
        SecurityLog.objects.create(
            user=user,
            action='password_changed',
            ip_address=self.get_client_ip(self.context['request']),
            user_agent=self.context['request'].META.get('HTTP_USER_AGENT', '')
        )

        # Публикуем событие в Redis
        from core.redis_events import publish_password_changed
        publish_password_changed(user.id)

        # Завершаем все другие сессии пользователя
        self.terminate_other_sessions(user)

        return user

    def get_client_ip(self, request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def terminate_other_sessions(self, user):
        """Завершить все сессии кроме текущей"""
        from django.contrib.sessions.models import Session
        from django.contrib.sessions.middleware import get_current_session_key

        current_key = get_current_session_key()

        # Находим все сессии пользователя
        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        sessions_to_delete = []

        for session in user_sessions:
            session_data = session.get_decoded()
            if ('_auth_user_id' in session_data and
                str(user.id) == session_data['_auth_user_id'] and
                session.session_key != current_key):

                sessions_to_delete.append(session.session_key)

        # Удаляем сессии
        Session.objects.filter(session_key__in=sessions_to_delete).delete()

        from .models import ActiveSession
        ActiveSession.objects.filter(session_key__in=sessions_to_delete).delete()