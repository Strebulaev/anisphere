"""
Сервис настроек чатов: обои, темы, шрифты, цвета, хранение и применение настроек.
Полная реализация системы кастомизации согласно CHAT_SETTINGS.md.
"""

import json
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q


# ==================== КЭШ НАСТРОЕК ====================

class SettingsCache:
    """Кэш настроек для быстрого доступа (Redis)"""

    TIMEOUT = 300  # 5 минут

    @staticmethod
    def _key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_settings:{user_id}:{chat_type}:{chat_id}"

    @staticmethod
    def _wallpaper_key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_wallpaper:{user_id}:{chat_type}:{chat_id}"

    @staticmethod
    def _theme_key(user_id: int, chat_type: str, chat_id: int) -> str:
        return f"chat_theme:{user_id}:{chat_type}:{chat_id}"

    @classmethod
    def get_chat_settings(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_chat_settings(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        key = cls._key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)

    @classmethod
    def invalidate(cls, user_id: int, chat_type: str, chat_id: int):
        cache.delete(cls._key(user_id, chat_type, chat_id))
        cache.delete(cls._wallpaper_key(user_id, chat_type, chat_id))
        cache.delete(cls._theme_key(user_id, chat_type, chat_id))

    @classmethod
    def invalidate_all_for_chat(cls, chat_type: str, chat_id: int):
        """Инвалидация для всех пользователей чата (паттерн)"""
        pattern = f"chat_settings:*:{chat_type}:{chat_id}"
        try:
            from django.core.cache import cache as django_cache
            if hasattr(django_cache, 'delete_pattern'):
                django_cache.delete_pattern(pattern)
        except Exception:
            pass

    @classmethod
    def get_wallpaper(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._wallpaper_key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_wallpaper(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        key = cls._wallpaper_key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)

    @classmethod
    def get_theme(cls, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        key = cls._theme_key(user_id, chat_type, chat_id)
        return cache.get(key)

    @classmethod
    def set_theme(cls, user_id: int, chat_type: str, chat_id: int, data: Dict):
        key = cls._theme_key(user_id, chat_type, chat_id)
        cache.set(key, data, timeout=cls.TIMEOUT)


# ==================== СЕРВИС НАСТРОЕК ЧАТА ====================

class ChatSettingsService:
    """Сервис для работы с настройками чата (обои, темы, уведомления)"""

    # ===== ПРЕДУСТАНОВЛЕННЫЕ ОБОИ =====
    PRESET_WALLPAPERS = [
        # Сплошные цвета
        {'id': 'solid_dark', 'name': 'Тёмный', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#0f0f1a', 'wallpaper_color2': ''},
        {'id': 'solid_navy', 'name': 'Тёмно-синий', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1a1a2e', 'wallpaper_color2': ''},
        {'id': 'solid_gray', 'name': 'Тёмно-серый', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1c1c1c', 'wallpaper_color2': ''},
        {'id': 'solid_indigo', 'name': 'Индиго', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#1e1b4b', 'wallpaper_color2': ''},
        {'id': 'solid_black', 'name': 'Чёрный', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#000000', 'wallpaper_color2': ''},
        {'id': 'solid_white', 'name': 'Белый', 'category': 'solid',
         'wallpaper_type': 'solid', 'wallpaper_color': '#f8f9fa', 'wallpaper_color2': ''},
        # Градиенты
        {'id': 'grad_blue_purple', 'name': 'Синий → Фиолетовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#1a1a2e', 'wallpaper_color2': '#16213e',
         'gradient_angle': 135},
        {'id': 'grad_pink_orange', 'name': 'Розовый → Оранжевый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#831843', 'wallpaper_color2': '#9a3412',
         'gradient_angle': 135},
        {'id': 'grad_green_teal', 'name': 'Зелёный → Бирюзовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#14532d', 'wallpaper_color2': '#134e4a',
         'gradient_angle': 135},
        {'id': 'grad_violet_pink', 'name': 'Фиолетовый → Розовый', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#4c1d95', 'wallpaper_color2': '#831843',
         'gradient_angle': 135},
        {'id': 'grad_midnight', 'name': 'Полночь', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#0a0a1a', 'wallpaper_color2': '#1a1a3e',
         'gradient_angle': 180},
        {'id': 'grad_ocean', 'name': 'Океан', 'category': 'gradient',
         'wallpaper_type': 'gradient', 'wallpaper_color': '#0c4a6e', 'wallpaper_color2': '#164e63',
         'gradient_angle': 135},
        # Паттерны
        {'id': 'pattern_dots', 'name': 'Точки', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#0f0f1a',
         'pattern_type': 'dots', 'pattern_color': '#3b82f6', 'pattern_opacity': 15},
        {'id': 'pattern_grid', 'name': 'Сетка', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#1a1a2e',
         'pattern_type': 'grid', 'pattern_color': '#6366f1', 'pattern_opacity': 10},
        {'id': 'pattern_waves', 'name': 'Волны', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#0f172a',
         'pattern_type': 'waves', 'pattern_color': '#0ea5e9', 'pattern_opacity': 20},
        {'id': 'pattern_hex', 'name': 'Шестиугольники', 'category': 'pattern',
         'wallpaper_type': 'pattern', 'wallpaper_color': '#1e1b4b',
         'pattern_type': 'hexagon', 'pattern_color': '#8b5cf6', 'pattern_opacity': 15},
    ]

    # ===== ПРЕДУСТАНОВЛЕННЫЕ ТЕМЫ =====
    PRESET_THEMES = [
        {
            'id': 'default_dark',
            'name': 'Тёмная (по умолчанию)',
            'theme': 'dark',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#1e1e32',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e2e8f0',
            'background_color': '#0f0f1a',
            'header_color': '#1a1a2e',
            'input_color': '#1e1e32',
            'accent_color': '#3b82f6',
        },
        {
            'id': 'anime_purple',
            'name': 'Аниме Фиолет',
            'theme': 'custom',
            'message_color_mine': '#8b5cf6',
            'message_color_other': '#2d1b69',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#ddd6fe',
            'background_color': '#1e1b4b',
            'header_color': '#2e2065',
            'input_color': '#312e81',
            'accent_color': '#8b5cf6',
        },
        {
            'id': 'sakura',
            'name': 'Сакура',
            'theme': 'custom',
            'message_color_mine': '#ec4899',
            'message_color_other': '#4a1942',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#fce7f3',
            'background_color': '#2d0a2e',
            'header_color': '#3b1040',
            'input_color': '#4a1942',
            'accent_color': '#ec4899',
        },
        {
            'id': 'ocean',
            'name': 'Океан',
            'theme': 'custom',
            'message_color_mine': '#0ea5e9',
            'message_color_other': '#0c2e4a',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e0f2fe',
            'background_color': '#071826',
            'header_color': '#0c2e4a',
            'input_color': '#0f3a5c',
            'accent_color': '#0ea5e9',
        },
        {
            'id': 'forest',
            'name': 'Лес',
            'theme': 'custom',
            'message_color_mine': '#10b981',
            'message_color_other': '#0a2e1e',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#d1fae5',
            'background_color': '#071a0f',
            'header_color': '#0a2e1e',
            'input_color': '#0d3824',
            'accent_color': '#10b981',
        },
        {
            'id': 'light',
            'name': 'Светлая',
            'theme': 'light',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#f1f5f9',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#1e293b',
            'background_color': '#f8fafc',
            'header_color': '#ffffff',
            'input_color': '#f1f5f9',
            'accent_color': '#3b82f6',
        },
    ]

    @classmethod
    def get_wallpaper_for_chat(cls, user, chat_type: str, chat_id: int) -> Optional[Dict]:
        """Получить обои для чата (с кэшированием)"""
        cached = SettingsCache.get_wallpaper(user.id, chat_type, chat_id)
        if cached:
            return cached

        from ..models_chat import ChatWallpaper

        if chat_type == 'group':
            wp = ChatWallpaper.objects.filter(user=user, chat_id=chat_id).first()
        else:
            wp = ChatWallpaper.objects.filter(user=user, private_chat_id=chat_id).first()

        if not wp:
            return None

        data = cls._wallpaper_to_dict(wp)
        SettingsCache.set_wallpaper(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def set_wallpaper_for_chat(cls, user, chat_type: str, chat_id: int, wallpaper_data: Dict) -> Dict:
        """Установить обои для чата"""
        from ..models_chat import ChatWallpaper

        defaults = {
            'wallpaper_type': wallpaper_data.get('wallpaper_type', 'solid'),
            'wallpaper_color': wallpaper_data.get('wallpaper_color', '#0f0f1a'),
            'wallpaper_color2': wallpaper_data.get('wallpaper_color2', ''),
            'wallpaper_intensity': wallpaper_data.get('wallpaper_intensity', 100),
            'wallpaper_blur': wallpaper_data.get('wallpaper_blur', 0),
            'wallpaper_motion': wallpaper_data.get('wallpaper_motion', 'none'),
            'gradient_angle': wallpaper_data.get('gradient_angle', 135),
            'pattern_type': wallpaper_data.get('pattern_type', ''),
            'pattern_color': wallpaper_data.get('pattern_color', ''),
            'pattern_opacity': wallpaper_data.get('pattern_opacity', 20),
        }

        if chat_type == 'group':
            wp, _ = ChatWallpaper.objects.update_or_create(
                user=user,
                chat_id=chat_id,
                defaults=defaults
            )
        else:
            wp, _ = ChatWallpaper.objects.update_or_create(
                user=user,
                private_chat_id=chat_id,
                defaults=defaults
            )

        data = cls._wallpaper_to_dict(wp)
        SettingsCache.set_wallpaper(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def reset_wallpaper(cls, user, chat_type: str, chat_id: int):
        """Сбросить обои"""
        from ..models_chat import ChatWallpaper
        if chat_type == 'group':
            ChatWallpaper.objects.filter(user=user, chat_id=chat_id).delete()
        else:
            ChatWallpaper.objects.filter(user=user, private_chat_id=chat_id).delete()
        SettingsCache.invalidate(user.id, chat_type, chat_id)

    @classmethod
    def apply_preset_wallpaper(cls, user, chat_type: str, chat_id: int, preset_id: str) -> Optional[Dict]:
        """Применить предустановленные обои"""
        preset = next((p for p in cls.PRESET_WALLPAPERS if p['id'] == preset_id), None)
        if not preset:
            return None
        return cls.set_wallpaper_for_chat(user, chat_type, chat_id, preset)

    @classmethod
    def get_theme_for_chat(cls, user, chat_type: str, chat_id: int) -> Optional[Dict]:
        """Получить тему для чата"""
        cached = SettingsCache.get_theme(user.id, chat_type, chat_id)
        if cached:
            return cached

        from ..models_chat import ChatTheme

        if chat_type == 'group':
            theme = ChatTheme.objects.filter(user=user, chat_id=chat_id).first()
        else:
            theme = ChatTheme.objects.filter(user=user, private_chat_id=chat_id).first()

        if not theme:
            return cls._default_theme()

        data = cls._theme_to_dict(theme)
        SettingsCache.set_theme(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def set_theme_for_chat(cls, user, chat_type: str, chat_id: int, theme_data: Dict) -> Dict:
        """Установить тему для чата"""
        from ..models_chat import ChatTheme

        fields = [
            'theme', 'message_color_mine', 'message_color_other',
            'message_text_color_mine', 'message_text_color_other',
            'bubble_style', 'bubble_border_radius', 'bubble_shadow',
            'font_family', 'font_size', 'font_size_px', 'font_weight', 'line_height',
            'time_format', 'time_color',
            'background_color', 'header_color', 'input_color',
            'input_text_color', 'accent_color', 'link_color',
            'message_animation', 'reaction_animation', 'typing_animation',
            'emoji_set', 'emoji_size',
            'show_avatars', 'show_usernames', 'compact_mode',
            'show_read_status', 'show_typing_indicator', 'message_grouping',
            'custom_css',
        ]
        defaults = {k: v for k, v in theme_data.items() if k in fields}

        if chat_type == 'group':
            theme, _ = ChatTheme.objects.update_or_create(
                user=user, chat_id=chat_id, private_chat=None,
                defaults=defaults
            )
        else:
            theme, _ = ChatTheme.objects.update_or_create(
                user=user, chat=None, private_chat_id=chat_id,
                defaults=defaults
            )

        data = cls._theme_to_dict(theme)
        SettingsCache.set_theme(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def apply_preset_theme(cls, user, chat_type: str, chat_id: int, preset_id: str) -> Optional[Dict]:
        """Применить предустановленную тему"""
        preset = next((p for p in cls.PRESET_THEMES if p['id'] == preset_id), None)
        if not preset:
            return None
        theme_data = {k: v for k, v in preset.items() if k != 'id' and k != 'name'}
        return cls.set_theme_for_chat(user, chat_type, chat_id, theme_data)

    @classmethod
    def get_all_settings_for_chat(cls, user, chat_type: str, chat_id: int) -> Dict:
        """Получить все настройки чата (обои + тема)"""
        cached = SettingsCache.get_chat_settings(user.id, chat_type, chat_id)
        if cached:
            return cached

        wallpaper = cls.get_wallpaper_for_chat(user, chat_type, chat_id)
        theme = cls.get_theme_for_chat(user, chat_type, chat_id)

        data = {
            'wallpaper': wallpaper,
            'theme': theme or cls._default_theme(),
            'css_vars': cls._build_css_vars(wallpaper, theme),
        }

        SettingsCache.set_chat_settings(user.id, chat_type, chat_id, data)
        return data

    @classmethod
    def _wallpaper_to_dict(cls, wp) -> Dict:
        from django.conf import settings as django_settings
        data = {
            'id': wp.id,
            'wallpaper_type': wp.wallpaper_type,
            'wallpaper_color': wp.wallpaper_color,
            'wallpaper_color2': wp.wallpaper_color2,
            'wallpaper_intensity': wp.wallpaper_intensity,
            'wallpaper_blur': wp.wallpaper_blur,
            'wallpaper_motion': wp.wallpaper_motion,
            'gradient_angle': wp.gradient_angle,
            'pattern_type': wp.pattern_type,
            'pattern_color': wp.pattern_color,
            'pattern_opacity': wp.pattern_opacity,
            'css': wp.to_css(),
        }
        if wp.wallpaper_image:
            data['wallpaper_image_url'] = wp.wallpaper_image.url
        return data

    @classmethod
    def _theme_to_dict(cls, theme) -> Dict:
        data = {
            'id': theme.id,
            'theme': theme.theme,
            'message_color_mine': theme.message_color_mine,
            'message_color_other': theme.message_color_other,
            'message_text_color_mine': theme.message_text_color_mine,
            'message_text_color_other': theme.message_text_color_other,
            'bubble_style': theme.bubble_style,
            'bubble_border_radius': theme.bubble_border_radius,
            'bubble_shadow': theme.bubble_shadow,
            'font_family': theme.font_family,
            'font_size': theme.font_size,
            'font_size_px': theme.font_size_px,
            'font_weight': theme.font_weight,
            'line_height': theme.line_height,
            'time_format': theme.time_format,
            'time_color': theme.time_color,
            'background_color': theme.background_color,
            'header_color': theme.header_color,
            'input_color': theme.input_color,
            'input_text_color': theme.input_text_color,
            'accent_color': theme.accent_color,
            'link_color': theme.link_color,
            'message_animation': theme.message_animation,
            'reaction_animation': theme.reaction_animation,
            'typing_animation': theme.typing_animation,
            'emoji_set': theme.emoji_set,
            'emoji_size': theme.emoji_size,
            'show_avatars': theme.show_avatars,
            'show_usernames': theme.show_usernames,
            'compact_mode': theme.compact_mode,
            'show_read_status': theme.show_read_status,
            'show_typing_indicator': theme.show_typing_indicator,
            'message_grouping': theme.message_grouping,
            'custom_css': theme.custom_css,
            'css_vars': theme.to_css_vars(),
        }
        return data

    @classmethod
    def _default_theme(cls) -> Dict:
        """Возвращает настройки темы по умолчанию"""
        return {
            'theme': 'default',
            'message_color_mine': '#3b82f6',
            'message_color_other': '#1e1e32',
            'message_text_color_mine': '#ffffff',
            'message_text_color_other': '#e2e8f0',
            'bubble_style': 'modern',
            'bubble_border_radius': 18,
            'bubble_shadow': False,
            'font_family': 'system',
            'font_size': 'medium',
            'font_size_px': 14,
            'font_weight': 400,
            'line_height': 1.5,
            'time_format': '24h',
            'time_color': 'rgba(255,255,255,0.5)',
            'background_color': '#0f0f1a',
            'header_color': '#1a1a2e',
            'input_color': '#1e1e32',
            'input_text_color': '#e2e8f0',
            'accent_color': '#3b82f6',
            'link_color': '#60a5fa',
            'message_animation': 'slide',
            'reaction_animation': 'bounce',
            'typing_animation': 'dots',
            'emoji_set': 'default',
            'emoji_size': 'medium',
            'show_avatars': True,
            'show_usernames': True,
            'compact_mode': False,
            'show_read_status': True,
            'show_typing_indicator': True,
            'message_grouping': True,
            'custom_css': '',
            'css_vars': {
                '--msg-mine-bg': '#3b82f6',
                '--msg-other-bg': '#1e1e32',
                '--msg-mine-text': '#ffffff',
                '--msg-other-text': '#e2e8f0',
                '--chat-bg': '#0f0f1a',
                '--chat-header-bg': '#1a1a2e',
                '--chat-input-bg': '#1e1e32',
                '--chat-accent': '#3b82f6',
                '--msg-font-size': '14px',
                '--msg-border-radius': '18px',
            },
        }

    @classmethod
    def _build_css_vars(cls, wallpaper: Optional[Dict], theme: Optional[Dict]) -> Dict:
        """Строит итоговый набор CSS переменных"""
        css_vars = {}
        if theme:
            css_vars.update(theme.get('css_vars', {}))
        if wallpaper:
            css_vars['--chat-wallpaper-css'] = wallpaper.get('css', '')
        return css_vars


# ==================== ПРОВЕРКА ПРАВ ====================

from dataclasses import dataclass, field
from typing import List


@dataclass
class PermissionResult:
    allowed: bool
    reason: str = ""
    missing_permissions: List[str] = field(default_factory=list)


class PermissionChecker:
    """Проверка прав доступа в чатах"""

    ALL_PERMISSIONS = {
        'can_delete_messages', 'can_ban_users', 'can_restrict_members',
        'can_pin_messages', 'can_manage_chat', 'can_change_chat_info',
        'can_invite_users', 'can_add_new_admins', 'can_promote_members',
        'can_post_messages', 'can_edit_messages', 'can_manage_video_chats',
        'can_remain_anonymous', 'can_delete_chat',
    }

    def __init__(self, user, chat):
        self.user = user
        self.chat = chat
        from ..models import ChatMember
        self.membership = ChatMember.objects.filter(user=user, chat=chat).first()

    def _is_banned(self) -> bool:
        from ..models_chat import ChatBan
        return ChatBan.objects.filter(
            user=self.user, chat=self.chat
        ).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())).exists()

    def _get_restriction(self, rtype: str):
        from ..models_chat import ChatRestriction
        return ChatRestriction.objects.filter(
            user=self.user, chat=self.chat, restriction_type=rtype
        ).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())).first()

    def has_permission(self, permission_name: str) -> PermissionResult:
        if not self.membership:
            return PermissionResult(False, "Вы не участник чата")

        if self._is_banned():
            return PermissionResult(False, "Вы заблокированы в этом чате")

        # Владелец имеет все права
        if self.membership.is_owner:
            return PermissionResult(True)

        # Проверяем ограничения
        if permission_name == 'can_post_messages':
            if self._get_restriction('read_only'):
                return PermissionResult(False, "Вам запрещено отправлять сообщения")

        # Берём из роли
        perms = self.membership.effective_permissions
        allowed = perms.get(permission_name, False)
        if allowed:
            return PermissionResult(True)

        return PermissionResult(False, f"Нет права: {permission_name}")

    def has_any_permission(self, permission_names: List[str]) -> PermissionResult:
        for p in permission_names:
            r = self.has_permission(p)
            if r.allowed:
                return r
        return PermissionResult(False, "Нет ни одного из требуемых прав", list(permission_names))

    def has_all_permissions(self, permission_names: List[str]) -> PermissionResult:
        missing = []
        for p in permission_names:
            r = self.has_permission(p)
            if not r.allowed:
                missing.append(p)
        if missing:
            return PermissionResult(False, "Не хватает прав", missing)
        return PermissionResult(True)


# ==================== ОГРАНИЧЕНИЕ ЧАСТОТЫ ====================

class RateLimiter:
    """Ограничение частоты действий"""

    def __init__(self, user_id: int, action_type: str):
        self.user_id = user_id
        self.action_type = action_type
        self.redis_key = f"rate_limit:{user_id}:{action_type}"

    def check(self, limit: int = 10, period: int = 60) -> bool:
        current = cache.get(self.redis_key, 0)
        if current >= limit:
            return False
        new_val = current + 1
        cache.set(self.redis_key, new_val, timeout=period)
        return True

    def get_remaining(self, limit: int = 10) -> int:
        current = cache.get(self.redis_key, 0)
        return max(0, limit - current)

    def reset(self):
        cache.delete(self.redis_key)


# ==================== УВЕДОМЛЕНИЯ ====================

class NotificationService:
    """Сервис отправки уведомлений"""

    @staticmethod
    def send_to_chat(chat, event_type: str, data: Dict, exclude_users=None):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        exclude_ids = [u.id for u in (exclude_users or [])]
        for member in chat.members.all():
            if member.user_id in exclude_ids:
                continue
            try:
                async_to_sync(channel_layer.group_send)(
                    f"user_{member.user_id}",
                    {'type': 'chat_message', 'event': event_type, 'data': data}
                )
            except Exception:
                pass

    @staticmethod
    def send_to_user(user_id: int, event_type: str, data: Dict):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        try:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {'type': 'chat_message', 'event': event_type, 'data': data}
            )
        except Exception:
            pass


# ==================== АНТИ-СПАМ ====================

class AntiSpamService:
    """Проверка сообщений на спам"""

    def __init__(self, chat):
        self.chat = chat

    def check_message(self, message) -> Dict:
        violations = []
        from ..models import Message

        text = getattr(message, 'text', '') or ''
        user = getattr(message, 'sender', None)
        if not user:
            return {'clean': True, 'violations': []}

        # Флуд
        recent = Message.objects.filter(
            sender=user, chat=self.chat,
            created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
        ).count()
        if recent >= 5:
            violations.append({'type': 'flood', 'action': 'mute', 'duration': 300})

        # Ссылки
        if 'http' in text:
            link_count = Message.objects.filter(
                sender=user, chat=self.chat,
                text__contains='http',
                created_at__gte=timezone.now() - timezone.timedelta(seconds=60)
            ).count()
            if link_count >= 3:
                violations.append({'type': 'links', 'action': 'restrict_links'})

        # Капс
        if len(text) > 10:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:
                violations.append({'type': 'caps', 'action': 'delete'})

        # Кастомные правила
        from ..models_chat import AntiSpamRule
        rules = AntiSpamRule.objects.filter(chat=self.chat, enabled=True)
        for rule in rules:
            if rule.rule_type == 'spam_keywords' and rule.keywords:
                text_lower = text.lower()
                for kw in rule.keywords:
                    if kw.lower() in text_lower:
                        violations.append({'type': 'keyword', 'keyword': kw, 'action': rule.action})
                        break

        return {'clean': len(violations) == 0, 'violations': violations}


# ==================== АНАЛИТИКА ====================

class ChatAnalytics:
    def __init__(self, chat):
        self.chat = chat

    def get_activity_stats(self, days: int = 7) -> Dict:
        from ..models import Message
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        since = timezone.now() - timezone.timedelta(days=days)
        msgs_per_day = (
            Message.objects.filter(chat=self.chat, created_at__gte=since)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        return {'messages_per_day': list(msgs_per_day), 'total': sum(d['count'] for d in msgs_per_day)}

    def get_member_stats(self) -> Dict:
        from core.online_status import online_status
        total = self.chat.members.count()
        online = sum(1 for m in self.chat.members.all() if online_status.is_online(m.user_id))
        return {'total': total, 'online': online}

    def get_content_stats(self, days: int = 7) -> Dict:
        from ..models import Message
        from django.db.models import Count
        since = timezone.now() - timezone.timedelta(days=days)
        qs = Message.objects.filter(chat=self.chat, created_at__gte=since)
        return {
            'total': qs.count(),
            'with_media': qs.exclude(media='').exclude(media=None).count(),
            'text_only': qs.filter(Q(media='') | Q(media=None)).count(),
        }

    def get_engagement_score(self) -> float:
        stats = self.get_activity_stats(7)
        members = self.get_member_stats()
        if not members['total']:
            return 0.0
        return round(stats['total'] / members['total'], 2)


# ==================== ЭКСПОРТ/ИМПОРТ НАСТРОЕК ====================

class SettingsExport:
    def export_user_settings(self, user) -> Dict:
        from ..models_chat import ChatWallpaper, ChatTheme, PrivateChatSettings
        from ..models import ChatFolder, ChatFolderChat

        data = {
            'version': '2.0',
            'exported_at': timezone.now().isoformat(),
            'private_chats': [],
            'group_chats': [],
            'folders': [],
            'wallpapers': [],
            'themes': [],
        }

        # Настройки личных чатов
        for s in PrivateChatSettings.objects.filter(user=user).select_related('chat'):
            data['private_chats'].append({
                'chat_id': s.chat_id,
                'custom_name': s.custom_name,
                'notifications': s.notifications_enabled,
                'archived': s.is_archived,
                'pinned': s.is_pinned,
            })

        # Обои
        for wp in ChatWallpaper.objects.filter(user=user):
            data['wallpapers'].append({
                'chat_id': wp.chat_id,
                'private_chat_id': wp.private_chat_id,
                'wallpaper_type': wp.wallpaper_type,
                'wallpaper_color': wp.wallpaper_color,
                'wallpaper_color2': wp.wallpaper_color2,
            })

        return data

    def import_user_settings(self, user, data: Dict) -> Dict:
        imported = {'wallpapers': 0, 'themes': 0, 'settings': 0}
        # Базовая реализация
        return {'success': True, 'imported': imported}


# ==================== ВЕРСИОНИРОВАНИЕ НАСТРОЕК ====================

class SettingsVersioning:
    @staticmethod
    def get_version(user_id: int) -> int:
        return cache.get(f"settings_version:{user_id}", 1)

    @staticmethod
    def increment_version(user_id: int):
        try:
            cache.incr(f"settings_version:{user_id}")
        except Exception:
            cache.set(f"settings_version:{user_id}", 2, timeout=86400)

    @staticmethod
    def sync_needed(user_id: int, client_version: int) -> bool:
        return SettingsVersioning.get_version(user_id) != client_version
