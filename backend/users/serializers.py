from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    User, UserSession, UserSettings, UserProfileSettings, TwoFactorAuth,
    ActiveSession, NotificationSettings, PrivacySettings, UserTheme,
    ChatBackground, EmailLog, MessageNotification, UserAnalytics
)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'display_name',
            'nickname', 'phone_number', 'avatar', 'bio', 'favorite_genres',
            'website', 'vk_profile', 'telegram', 'email_verified',
            'phone_verified', 'two_factor_enabled', 'is_online', 'last_login',
            'created_at', 'updated_at', 'level', 'experience', 'mana', 'badges',
            'posts_count', 'comments_count', 'likes_received', 'playlists_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'level', 'experience', 'mana', 'badges', 'posts_count', 'comments_count', 'likes_received', 'playlists_count']


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
            'display_name', 'nickname', 'avatar', 'bio', 'favorite_genres',
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
    class Meta:
        model = UserProfileSettings
        fields = '__all__'
        read_only_fields = ['user', 'updated_at']


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    has_backup_codes = serializers.SerializerMethodField()

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


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = '__all__'
        read_only_fields = ['user', 'updated_at']


class PrivacySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacySettings
        fields = '__all__'
        read_only_fields = ['user']


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


class UserSimpleSerializer(serializers.ModelSerializer):
    """Простой сериализатор для пользователей (для списков)"""

    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar', 'is_online', 'last_seen']

    def get_is_online(self, obj):
        """Определяем онлайн статус через Redis"""
        from core.online_status import online_status
        return online_status.is_online(obj.id)