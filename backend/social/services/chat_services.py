"""
Сервисы для системы чатов согласно документации CHAT_SETTINGS.md
Включает: PermissionChecker, SettingsCache, AntiSpamService, RateLimiter,
SmartNotifications, ChatAnalytics, ChatBackupService, SettingsExport, SettingsVersioning
"""

import json
import hashlib
import re
import uuid
from datetime import timedelta, datetime
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from pathlib import Path

from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

import redis

# Для аннотаций типов
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..models import GroupChat, PrivateChat, Message, ChatMember
    from ..models_chat import ChatRestriction, ChatBan, AntiSpamRule, ChatBackup
    from django.contrib.auth.models import User

User = get_user_model()


# ==================== PERMISSION CHECKER ====================

@dataclass
class PermissionResult:
    """Результат проверки прав"""
    allowed: bool
    reason: str = ""
    missing_permissions: List[str] = field(default_factory=list)


class PermissionChecker:
    """
    Проверка прав доступа в чатах.
    Учитывает роли, настройки группы, ограничения и блокировки.
    """
    
    # Все возможные права
    ALL_PERMISSIONS = {
        # Права модерации
        'can_delete_messages',
        'can_ban_users',
        'can_restrict_members',
        'can_pin_messages',
        
        # Права управления
        'can_manage_chat',
        'can_change_chat_info',
        'can_invite_users',
        'can_add_new_admins',
        'can_promote_members',
        
        # Права контента
        'can_post_messages',
        'can_edit_messages',
        'can_manage_video_chats',
        
        # Специальные права
        'can_remain_anonymous',
        'can_delete_chat',
    }
    
    # Права по ролям по умолчанию
    DEFAULT_ROLE_PERMISSIONS = {
        'owner': ALL_PERMISSIONS,  # Владелец имеет все права
        'admin': {
            'can_manage_chat', 'can_change_chat_info', 'can_delete_messages',
            'can_ban_users', 'can_invite_users', 'can_pin_messages',
            'can_promote_members', 'can_manage_video_chats', 'can_post_messages',
            'can_edit_messages',
        },
        'moderator': {
            'can_delete_messages', 'can_restrict_members', 'can_pin_messages',
            'can_invite_users', 'can_post_messages',
        },
        'member': {
            'can_post_messages',
        },
    }
    
    def __init__(self, user, chat):
        """
        Инициализация проверки прав.
        
        Args:
            user: Пользователь для проверки
            chat: GroupChat или PrivateChat
        """
        self.user = user
        self.chat = chat
        self._membership = None
        self._restrictions = None
        self._ban = None
    
    @property
    def membership(self):
        """Ленивая загрузка участия в группе"""
        if self._membership is None and hasattr(self.chat, 'members'):
            from ..models import ChatMember
            try:
                self._membership = self.chat.members.get(user=self.user)
            except ChatMember.DoesNotExist:
                self._membership = False
        return self._membership if self._membership else None
    
    @property
    def restrictions(self):
        """Ленивая загрузка ограничений"""
        if self._restrictions is None and hasattr(self.chat, 'restrictions'):
            from ..models_chat import ChatRestriction
            self._restrictions = ChatRestriction.objects.filter(
                chat=self.chat,
                user=self.user
            ).filter(
                Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
            )
        return self._restrictions or []
    
    @property
    def is_banned(self) -> bool:
        """Проверка на блокировку"""
        if self._ban is None and hasattr(self.chat, 'bans'):
            from ..models_chat import ChatBan
            self._ban = ChatBan.objects.filter(
                chat=self.chat,
                user=self.user
            ).filter(
                Q(until_date__isnull=True) | Q(until_date__gt=timezone.now())
            ).exists()
        return self._ban or False
    
    def has_permission(self, permission_name: str) -> PermissionResult:
        """
        Проверить наличие конкретного права.
        
        Args:
            permission_name: Название права
            
        Returns:
            PermissionResult с результатом проверки
        """
        # Проверяем, что право существует
        if permission_name not in self.ALL_PERMISSIONS:
            return PermissionResult(
                allowed=False,
                reason=f"Неизвестное право: {permission_name}"
            )
        
        # Для личных чатов правила проще
        if not hasattr(self.chat, 'members'):
            return self._check_private_chat_permission(permission_name)
        
        # Проверяем блокировку
        if self.is_banned:
            return PermissionResult(
                allowed=False,
                reason="Пользователь заблокирован в этом чате"
            )
        
        # Проверяем участие
        if not self.membership:
            return PermissionResult(
                allowed=False,
                reason="Пользователь не является участником чата"
            )
        
        # Владелец имеет все права
        if self._is_owner():
            return PermissionResult(allowed=True)
        
        # Получаем эффективные права
        effective_permissions = self._get_effective_permissions()
        
        # Проверяем ограничения
        restricted_perms = self._get_restricted_permissions()
        
        # Если право ограничено
        if permission_name in restricted_perms:
            return PermissionResult(
                allowed=False,
                reason=f"Право '{permission_name}' ограничено",
                missing_permissions=[permission_name]
            )
        
        # Проверяем наличие права
        has_perm = effective_permissions.get(permission_name, False)
        
        return PermissionResult(
            allowed=has_perm,
            reason="" if has_perm else f"Нет права '{permission_name}'",
            missing_permissions=[] if has_perm else [permission_name]
        )
    
    def has_any_permission(self, permission_names: List[str]) -> PermissionResult:
        """Проверить наличие хотя бы одного из прав"""
        for perm in permission_names:
            result = self.has_permission(perm)
            if result.allowed:
                return result
        
        return PermissionResult(
            allowed=False,
            reason=f"Нет ни одного из прав: {', '.join(permission_names)}",
            missing_permissions=permission_names
        )
    
    def has_all_permissions(self, permission_names: List[str]) -> PermissionResult:
        """Проверить наличие всех прав"""
        missing = []
        for perm in permission_names:
            result = self.has_permission(perm)
            if not result.allowed:
                missing.append(perm)
        
        if missing:
            return PermissionResult(
                allowed=False,
                reason=f"Отсутствуют права: {', '.join(missing)}",
                missing_permissions=missing
            )
        
        return PermissionResult(allowed=True)
    
    def can_perform_action(self, action: str, target_user=None) -> PermissionResult:
        """
        Проверить возможность выполнения действия над пользователем.
        Учитывает иерархию ролей.
        """
        if not hasattr(self.chat, 'members'):
            return PermissionResult(allowed=False, reason="Не групповой чат")
        
        # Владелец может всё
        if self._is_owner():
            # Кроме действий над собой
            if target_user == self.user and action in ['ban', 'demote', 'remove']:
                return PermissionResult(allowed=False, reason="Нельзя выполнить это действие над собой")
            return PermissionResult(allowed=True)
        
        # Проверяем право на действие
        action_permissions = {
            'ban': 'can_ban_users',
            'restrict': 'can_restrict_members',
            'promote': 'can_promote_members',
            'demote': 'can_promote_members',
            'remove': 'can_manage_chat',
            'edit_info': 'can_change_chat_info',
            'pin': 'can_pin_messages',
            'delete_message': 'can_delete_messages',
            'invite': 'can_invite_users',
        }
        
        required_perm = action_permissions.get(action)
        if not required_perm:
            return PermissionResult(allowed=False, reason=f"Неизвестное действие: {action}")
        
        result = self.has_permission(required_perm)
        if not result.allowed:
            return result
        
        # Если есть целевой пользователь, проверяем иерархию
        if target_user:
            target_membership = self.chat.members.filter(user=target_user).first()
            if target_membership:
                # Нельзя действовать на пользователя с уровнем выше или равным
                if self.membership:
                    my_level = self._get_role_level()
                    target_level = self._get_role_level_for_member(target_membership)
                    
                    if target_level >= my_level:
                        return PermissionResult(
                            allowed=False,
                            reason="Нельзя выполнить действие над пользователем с равным или более высоким уровнем"
                        )
        
        return PermissionResult(allowed=True)
    
    def _is_owner(self) -> bool:
        """Проверка, является ли пользователь владельцем"""
        return hasattr(self.chat, 'created_by') and self.chat.created_by == self.user
    
    def _get_role_level(self) -> int:
        """Получить уровень роли текущего пользователя"""
        if self._is_owner():
            return 5  # Владелец
        
        if not self.membership:
            return 0
        
        if self.membership.role:
            return self.membership.role.level
        
        if self.membership.is_admin:
            return 4  # Администратор
        
        return 0  # Участник
    
    def _get_role_level_for_member(self, membership) -> int:
        """Получить уровень роли участника"""
        if membership.chat.created_by == membership.user:
            return 5
        if membership.role:
            return membership.role.level
        if membership.is_admin:
            return 4
        return 0
    
    def _get_effective_permissions(self) -> Dict[str, bool]:
        """Получить эффективные права пользователя"""
        permissions = {}
        
        # Базовые права участника
        permissions.update({p: False for p in self.ALL_PERMISSIONS})
        permissions['can_post_messages'] = True  # Базовое право
        
        # Если есть роль, берём права из неё
        if self.membership and self.membership.role:
            for field in self.membership.role._meta.fields:
                if field.name.startswith('can_'):
                    permissions[field.name] = getattr(self.membership.role, field.name)
        
        # Переопределяем индивидуальными настройками участника
        if self.membership:
            for field in self.membership._meta.fields:
                if field.name.startswith('can_'):
                    permissions[field.name] = getattr(self.membership, field.name)
        
        return permissions
    
    def _get_restricted_permissions(self) -> Set[str]:
        """Получить права, ограниченные для пользователя"""
        restricted = set()
        
        for restriction in self.restrictions:
            restriction_type = restriction.restriction_type
            
            if restriction_type == 'read_only':
                restricted.add('can_post_messages')
            elif restriction_type == 'no_media':
                restricted.update(['can_send_media'])
            elif restriction_type == 'no_stickers':
                restricted.update(['can_send_stickers'])
            elif restriction_type == 'no_links':
                restricted.update(['can_send_links'])
            elif restriction_type == 'no_voice':
                restricted.update(['can_send_voice'])
        
        return restricted
    
    def _check_private_chat_permission(self, permission_name: str) -> PermissionResult:
        """Проверка прав для личного чата"""
        from ..models import PrivateChat
        
        if not isinstance(self.chat, PrivateChat):
            return PermissionResult(allowed=False, reason="Не личный чат")
        
        # Проверяем, что пользователь участник чата
        if self.user not in [self.chat.user1, self.chat.user2]:
            return PermissionResult(allowed=False, reason="Не участник чата")
        
        # Проверяем блокировку
        if self.user == self.chat.user1 and self.chat.user2_blocked:
            return PermissionResult(allowed=False, reason="Вы заблокированы")
        if self.user == self.chat.user2 and self.chat.user1_blocked:
            return PermissionResult(allowed=False, reason="Вы заблокированы")
        
        # В личных чатах базовые права есть у обоих участников
        basic_permissions = {
            'can_post_messages', 'can_send_media', 'can_send_stickers',
            'can_send_links', 'can_send_voice'
        }
        
        if permission_name in basic_permissions:
            return PermissionResult(allowed=True)
        
        return PermissionResult(allowed=False, reason="Недоступно в личном чате")


# ==================== SETTINGS CACHE ====================

class SettingsCache:
    """
    Кэширование настроек чатов в Redis.
    """
    
    CACHE_PREFIX = 'chat_settings'
    CACHE_TIMEOUT = 3600  # 1 час
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    
    def get_cache_key(self, user_id: int, chat_type: str, chat_id: int) -> str:
        """Сформировать ключ кэша"""
        return f"{self.CACHE_PREFIX}:{user_id}:{chat_type}:{chat_id}"
    
    def get_chat_settings(self, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        """
        Получить настройки чата с кэшированием.
        
        Args:
            user_id: ID пользователя
            chat_type: 'private' или 'group'
            chat_id: ID чата
            
        Returns:
            Словарь с настройками или None
        """
        cache_key = self.get_cache_key(user_id, chat_type, chat_id)
        
        # Пробуем получить из кэша
        cached = self.redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass
        
        # Загружаем из БД
        settings_data = self._load_settings_from_db(user_id, chat_type, chat_id)
        
        if settings_data:
            # Сохраняем в кэш
            self.redis_client.setex(
                cache_key,
                self.CACHE_TIMEOUT,
                json.dumps(settings_data, default=str)
            )
        
        return settings_data
    
    def invalidate(self, user_id: int, chat_type: str, chat_id: int):
        """
        Инвалидировать кэш настроек.
        """
        cache_key = self.get_cache_key(user_id, chat_type, chat_id)
        self.redis_client.delete(cache_key)
    
    def invalidate_all_for_chat(self, chat_type: str, chat_id: int):
        """Инвалидировать кэш для всех пользователей чата"""
        pattern = f"{self.CACHE_PREFIX}:*:{chat_type}:{chat_id}"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def invalidate_all_for_user(self, user_id: int):
        """Инвалидировать весь кэш пользователя"""
        pattern = f"{self.CACHE_PREFIX}:{user_id}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def _load_settings_from_db(self, user_id: int, chat_type: str, chat_id: int) -> Optional[Dict]:
        """Загрузить настройки из БД"""
        try:
            user = User.objects.get(id=user_id)
            
            if chat_type == 'private':
                from ..models import PrivateChat
                from ..models_chat import PrivateChatSettings
                
                chat = PrivateChat.objects.get(id=chat_id)
                if user not in [chat.user1, chat.user2]:
                    return None
                
                settings_obj, _ = PrivateChatSettings.objects.get_or_create(
                    chat=chat, user=user
                )
                
                return {
                    'custom_name': settings_obj.custom_name,
                    'notifications_enabled': settings_obj.notifications_enabled,
                    'sound_enabled': settings_obj.sound_enabled,
                    'muted_until': settings_obj.muted_until.isoformat() if settings_obj.muted_until else None,
                    'is_archived': settings_obj.is_archived,
                    'is_pinned': settings_obj.is_pinned,
                    'is_blocked': settings_obj.is_blocked,
                    'auto_delete_after': settings_obj.auto_delete_after,
                }
            
            elif chat_type == 'group':
                from ..models import GroupChat
                from ..models_chat import ChatSettings
                
                chat = GroupChat.objects.get(id=chat_id)
                if not chat.members.filter(user=user).exists():
                    return None
                
                settings_obj, _ = ChatSettings.objects.get_or_create(
                    user=user, chat=chat
                )
                
                return {
                    'notifications_enabled': settings_obj.notifications_enabled,
                    'sound_enabled': settings_obj.sound_enabled,
                    'is_blocked': settings_obj.is_blocked,
                }
            
        except Exception as e:
            print(f"Error loading settings from DB: {e}")
            return None
        
        return None


# ==================== ANTI-SPAM SERVICE ====================

class AntiSpamService:
    """
    Сервис защиты от спама с настраиваемыми правилами.
    """
    
    def __init__(self, chat):
        self.chat = chat
        self._rules = None
    
    @property
    def rules(self):
        """Ленивая загрузка правил"""
        if self._rules is None and hasattr(self.chat, 'anti_spam_rules'):
            from ..models_chat import AntiSpamRule
            self._rules = list(self.chat.anti_spam_rules.filter(enabled=True))
        return self._rules or []
    
    def check_message(self, message) -> Dict[str, Any]:
        """
        Проверить сообщение на спам.
        
        Args:
            message: Объект Message для проверки
            
        Returns:
            Словарь с результатом проверки:
            {
                'is_spam': bool,
                'violated_rules': list,
                'action': str,
                'action_duration': int
            }
        """
        result = {
            'is_spam': False,
            'violated_rules': [],
            'action': None,
            'action_duration': None
        }
        
        if not self.rules:
            return result
        
        for rule in self.rules:
            violation = self._check_rule(rule, message)
            if violation:
                result['is_spam'] = True
                result['violated_rules'].append(rule.rule_type)
                
                # Берём самое строгое действие
                if not result['action'] or self._action_severity(rule.action) > self._action_severity(result['action']):
                    result['action'] = rule.action
                    result['action_duration'] = rule.action_duration
        
        return result
    
    def _check_rule(self, rule, message) -> bool:
        """Проверить конкретное правило"""
        rule_type = rule.rule_type
        
        if rule_type == 'flood':
            return self._check_flood(rule, message)
        elif rule_type == 'links':
            return self._check_links(rule, message)
        elif rule_type == 'spam_keywords':
            return self._check_keywords(rule, message)
        elif rule_type == 'caps_lock':
            return self._check_caps_lock(rule, message)
        elif rule_type == 'new_members':
            return self._check_new_member(rule, message)
        elif rule_type == 'media_flood':
            return self._check_media_flood(rule, message)
        
        return False
    
    def _check_flood(self, rule, message) -> bool:
        """Проверка на флуд"""
        from ..models import Message
        
        time_window = timezone.now() - timedelta(seconds=rule.time_window)
        recent_count = Message.objects.filter(
            chat=self.chat,
            sender=message.sender,
            created_at__gte=time_window
        ).count()
        
        return recent_count > rule.threshold
    
    def _check_links(self, rule, message) -> bool:
        """Проверка на ссылки"""
        if not message.text:
            return False
        
        # Паттерн для URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message.text)
        
        return len(urls) > 0
    
    def _check_keywords(self, rule, message) -> bool:
        """Проверка на стоп-слова"""
        if not message.text:
            return False
        
        keywords = rule.keywords or []
        text_lower = message.text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _check_caps_lock(self, rule, message) -> bool:
        """Проверка на CAPS LOCK"""
        if not message.text:
            return False
        
        text = message.text
        if len(text) < 5:
            return False
        
        # Считаем процент заглавных букв
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return False
        
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        return caps_ratio > 0.7
    
    def _check_new_member(self, rule, message) -> bool:
        """Проверка ограничений для новых участников"""
        from ..models import ChatMember
        
        try:
            member = ChatMember.objects.get(chat=self.chat, user=message.sender)
            join_time = member.joined_at
            hours_since_join = (timezone.now() - join_time).total_seconds() / 3600
            return hours_since_join < 24  # Первые 24 часа
        except ChatMember.DoesNotExist:
            return True
    
    def _check_media_flood(self, rule, message) -> bool:
        """Проверка на медиа-флуд"""
        from ..models import Message
        
        if not message.media:
            return False
        
        time_window = timezone.now() - timedelta(seconds=rule.time_window)
        recent_media_count = Message.objects.filter(
            chat=self.chat,
            sender=message.sender,
            media__isnull=False,
            created_at__gte=time_window
        ).count()
        
        return recent_media_count > rule.threshold
    
    def _action_severity(self, action: str) -> int:
        """Тяжесть действия"""
        severity = {
            'warn': 1,
            'delete': 2,
            'mute': 3,
            'ban': 4,
        }
        return severity.get(action, 0)
    
    def apply_action(self, message, action: str, duration: int = None):
        """Применить действие к сообщению/пользователю"""
        from ..models_chat import ChatRestriction, ChatBan
        
        if action == 'delete':
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.save(update_fields=['is_deleted', 'deleted_at'])
        
        elif action == 'mute':
            until = timezone.now() + timedelta(minutes=duration or 60)
            ChatRestriction.objects.create(
                chat=self.chat,
                user=message.sender,
                restriction_type='read_only',
                reason='Автоматическое ограничение за спам',
                until_date=until,
                restricted_by=None  # Автоматическое
            )
        
        elif action == 'ban':
            until = timezone.now() + timedelta(hours=duration or 24) if duration else None
            ChatBan.objects.create(
                chat=self.chat,
                user=message.sender,
                reason='Автоматическая блокировка за спам',
                until_date=until,
                banned_by=None
            )


# ==================== RATE LIMITER ====================

class RateLimiter:
    """
    Ограничение частоты действий пользователей.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    
    def is_allowed(self, user_id: int, action_type: str, limit: int, period: int) -> bool:
        """
        Проверить, разрешено ли действие.
        
        Args:
            user_id: ID пользователя
            action_type: Тип действия (message, invite, reaction, etc.)
            limit: Максимум действий за период
            period: Период в секундах
            
        Returns:
            True если действие разрешено
        """
        key = f"rate_limit:{user_id}:{action_type}"
        
        current = self.redis_client.get(key)
        if current is None:
            # Первое действие - создаём счётчик
            self.redis_client.setex(key, period, 1)
            return True
        
        current = int(current)
        if current >= limit:
            return False
        
        self.redis_client.incr(key)
        return True
    
    def get_remaining(self, user_id: int, action_type: str, limit: int) -> int:
        """Получить количество оставшихся действий"""
        key = f"rate_limit:{user_id}:{action_type}"
        current = self.redis_client.get(key)
        
        if current is None:
            return limit
        
        return max(0, limit - int(current))
    
    def reset(self, user_id: int, action_type: str):
        """Сбросить лимит"""
        key = f"rate_limit:{user_id}:{action_type}"
        self.redis_client.delete(key)
    
    def get_retry_after(self, user_id: int, action_type: str) -> int:
        """Получить время до следующего разрешённого действия"""
        key = f"rate_limit:{user_id}:{action_type}"
        ttl = self.redis_client.ttl(key)
        return max(0, ttl)


# ==================== SMART NOTIFICATIONS ====================

class SmartNotifications:
    """
    Интеллектуальная система уведомлений.
    Группирует, приоритизирует и фильтрует уведомления.
    """
    
    PRIORITY_LOW = 1
    PRIORITY_NORMAL = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4
    
    NOTIFICATION_TYPES = {
        'message': PRIORITY_NORMAL,
        'mention': PRIORITY_HIGH,
        'reply': PRIORITY_HIGH,
        'reaction': PRIORITY_LOW,
        'join': PRIORITY_LOW,
        'leave': PRIORITY_LOW,
        'ban': PRIORITY_URGENT,
        'promote': PRIORITY_HIGH,
        'system': PRIORITY_NORMAL,
    }
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    
    def should_notify(self, user, notification_type: str, data: Dict) -> bool:
        """
        Определить, нужно ли отправлять уведомление.
        
        Учитывает:
        - Настройки пользователя
        - Время суток (тихий режим)
        - Частоту уведомлений
        - Статус онлайн
        """
        # Проверяем настройки пользователя
        if not self._check_user_settings(user, notification_type):
            return False
        
        # Проверяем тихий режим
        if self._is_quiet_hours(user):
            # Только срочные уведомления в тихий режим
            if self.NOTIFICATION_TYPES.get(notification_type, 2) < self.PRIORITY_URGENT:
                return False
        
        # Проверяем частоту (не спамим)
        if self._is_too_frequent(user, notification_type):
            # Группируем уведомления
            self._queue_notification(user, notification_type, data)
            return False
        
        # Проверяем онлайн статус
        try:
            from core.online_status import online_status
            if online_status.is_online(user.id):
                # Пользователь онлайн - отправляем через WebSocket
                return True
        except ImportError:
            pass
        
        return True
    
    def send_notification(self, user, notification_type: str, title: str, body: str, data: Dict = None):
        """Отправить уведомление пользователю"""
        try:
            from notifications.services import notification_service
            
            notification_data = {
                'type': notification_type,
                'title': title,
                'body': body,
                'data': data or {},
                'priority': self.NOTIFICATION_TYPES.get(notification_type, 2),
            }
            
            # Отправляем через WebSocket если онлайн
            try:
                from core.online_status import online_status
                if online_status.is_online(user.id):
                    notification_service.send_realtime(user, notification_data)
            except ImportError:
                pass
            
            # Сохраняем в БД
            notification_service.create_notification(user, notification_data)
            
            # Отправляем push/email если нужно
            try:
                from core.online_status import online_status
                if not online_status.is_online(user.id):
                    self._send_push_notification(user, notification_data)
            except ImportError:
                self._send_push_notification(user, notification_data)
                
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def _check_user_settings(self, user, notification_type: str) -> bool:
        """Проверить настройки уведомлений пользователя"""
        # TODO: Реализовать проверку настроек
        return True
    
    def _is_quiet_hours(self, user) -> bool:
        """Проверить, действует ли тихий режим"""
        # Получаем настройки тихого режима пользователя
        quiet_start = getattr(user, 'quiet_hours_start', None)
        quiet_end = getattr(user, 'quiet_hours_end', None)
        
        if not quiet_start or not quiet_end:
            return False
        
        now = datetime.now().time()
        return quiet_start <= now <= quiet_end
    
    def _is_too_frequent(self, user, notification_type: str) -> bool:
        """Проверить частоту уведомлений"""
        key = f"notif_freq:{user.id}:{notification_type}"
        count = self.redis_client.get(key)
        
        if count and int(count) > 5:  # Максимум 5 уведомлений одного типа за минуту
            return True
        
        if count:
            self.redis_client.incr(key)
        else:
            self.redis_client.setex(key, 60, 1)
        
        return False
    
    def _queue_notification(self, user, notification_type: str, data: Dict):
        """Добавить уведомление в очередь для группировки"""
        key = f"notif_queue:{user.id}:{notification_type}"
        self.redis_client.rpush(key, json.dumps(data, default=str))
        self.redis_client.expire(key, 300)  # 5 минут
    
    def _send_push_notification(self, user, data: Dict):
        """Отправить push-уведомление"""
        try:
            from notifications.services import notification_service
            notification_service.send_push(user, data)
        except Exception as e:
            print(f"Error sending push notification: {e}")


# ==================== CHAT ANALYTICS ====================

class ChatAnalytics:
    """
    Сбор и анализ статистики чатов.
    """
    
    def __init__(self, chat):
        self.chat = chat
    
    def get_activity_stats(self, days: int = 7) -> Dict:
        """
        Получить статистику активности за период.
        
        Returns:
            {
                'messages_count': int,
                'active_users': int,
                'avg_messages_per_day': float,
                'peak_hour': int,
                'by_day': [{date, count}],
                'by_hour': [{hour, count}],
            }
        """
        from ..models import Message
        
        start_date = timezone.now() - timedelta(days=days)
        
        messages = Message.objects.filter(
            chat=self.chat,
            created_at__gte=start_date,
            is_deleted=False
        )
        
        # Общее количество сообщений
        messages_count = messages.count()
        
        # Активные пользователи
        active_users = messages.values('sender').distinct().count()
        
        # Среднее в день
        avg_per_day = messages_count / days if days > 0 else 0
        
        # По дням
        by_day = list(messages.extra(
            {'day': "date(created_at)"}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day'))
        
        # По часам
        by_hour = list(messages.extra(
            {'hour': "extract(hour from created_at)"}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour'))
        
        # Пиковый час
        peak_hour = max(by_hour, key=lambda x: x['count'])['hour'] if by_hour else 0
        
        return {
            'messages_count': messages_count,
            'active_users': active_users,
            'avg_messages_per_day': round(avg_per_day, 2),
            'peak_hour': peak_hour,
            'by_day': by_day,
            'by_hour': by_hour,
        }
    
    def get_member_stats(self) -> Dict:
        """
        Получить статистику участников.
        
        Returns:
            {
                'total': int,
                'online': int,
                'admins': int,
                'new_today': int,
                'left_today': int,
                'by_role': [{role, count}],
            }
        """
        from ..models import ChatMember, ChatAdminLog
        
        total = self.chat.members.count()
        
        # Онлайн участники
        online = 0
        try:
            from core.online_status import online_status
            online = sum(
                1 for member in self.chat.members.all()
                if online_status.is_online(member.user_id)
            )
        except ImportError:
            pass
        
        # Администраторы
        admins = self.chat.members.filter(
            Q(is_admin=True) | Q(role__level__gte=3)
        ).count()
        
        # Новые за сегодня
        today = timezone.now().replace(hour=0, minute=0, second=0)
        new_today = ChatAdminLog.objects.filter(
            chat=self.chat,
            action='member_joined',
            created_at__gte=today
        ).count()
        
        # Вышедшие за сегодня
        left_today = ChatAdminLog.objects.filter(
            chat=self.chat,
            action='member_left',
            created_at__gte=today
        ).count()
        
        # По ролям
        by_role = list(self.chat.members.values(
            'role__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count'))
        
        return {
            'total': total,
            'online': online,
            'admins': admins,
            'new_today': new_today,
            'left_today': left_today,
            'by_role': by_role,
        }
    
    def get_content_stats(self, days: int = 7) -> Dict:
        """
        Получить статистику контента.
        
        Returns:
            {
                'media_messages': int,
                'text_messages': int,
                'reactions_count': int,
                'pinned_messages': int,
                'by_media_type': [{type, count}],
            }
        """
        from ..models import Message
        from ..models_chat import MessageReaction
        
        start_date = timezone.now() - timedelta(days=days)
        
        messages = Message.objects.filter(
            chat=self.chat,
            created_at__gte=start_date,
            is_deleted=False
        )
        
        media_messages = messages.filter(media__isnull=False).count()
        text_messages = messages.filter(media__isnull=True).count()
        
        reactions_count = MessageReaction.objects.filter(
            message__chat=self.chat,
            created_at__gte=start_date
        ).count()
        
        pinned_messages = messages.filter(is_pinned=True).count()
        
        # По типу медиа
        by_media_type = list(messages.filter(
            media__isnull=False
        ).values('media_type').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        return {
            'media_messages': media_messages,
            'text_messages': text_messages,
            'reactions_count': reactions_count,
            'pinned_messages': pinned_messages,
            'by_media_type': by_media_type,
        }
    
    def get_engagement_score(self) -> float:
        """
        Рассчитать показатель вовлечённости чата.
        
        Формула: (активные_пользователи / всего_участников) * 
                 (сообщения_за_неделю / активные_пользователи) * 
                 (реакции / сообщения)
        """
        activity = self.get_activity_stats(days=7)
        members = self.get_member_stats()
        
        if members['total'] == 0:
            return 0
        
        active_ratio = activity['active_users'] / members['total'] if members['total'] > 0 else 0
        messages_per_active = activity['messages_count'] / activity['active_users'] if activity['active_users'] > 0 else 0
        content = self.get_content_stats(days=7)
        reaction_ratio = content['reactions_count'] / activity['messages_count'] if activity['messages_count'] > 0 else 0
        
        # Нормализуем и взвешиваем
        score = (active_ratio * 0.4 + 
                min(messages_per_active / 10, 1) * 0.4 + 
                min(reaction_ratio, 1) * 0.2) * 100
        
        return round(score, 2)


# ==================== CHAT BACKUP SERVICE ====================

class ChatBackupService:
    """
    Сервис резервного копирования чатов.
    """
    
    def create_backup(self, chat, user) -> Dict:
        """
        Создать резервную копию чата.
        
        Returns:
            {
                'success': bool,
                'backup_id': int,
                'messages_count': int,
                'members_count': int,
                'file_size': int,
            }
        """
        from ..models import Message, ChatMember
        from ..models_chat import ChatBackup
        
        # Создаём запись о бэкапе
        backup = ChatBackup.objects.create(
            chat=chat,
            created_by=user,
            status='creating'
        )
        
        try:
            # Собираем данные
            backup_data = {
                'chat_info': {
                    'id': chat.id,
                    'name': getattr(chat, 'name', ''),
                    'description': getattr(chat, 'description', ''),
                    'created_at': chat.created_at.isoformat() if hasattr(chat, 'created_at') else None,
                },
                'members': [],
                'messages': [],
                'settings': {},
            }
            
            # Участники
            if hasattr(chat, 'members'):
                for member in chat.members.all():
                    backup_data['members'].append({
                        'user_id': member.user_id,
                        'username': member.user.username if hasattr(member.user, 'username') else '',
                        'joined_at': member.joined_at.isoformat() if hasattr(member, 'joined_at') else None,
                        'role': member.role.name if member.role else None,
                        'is_admin': getattr(member, 'is_admin', False),
                    })
            
            # Сообщения
            messages = Message.objects.filter(chat=chat, is_deleted=False).order_by('created_at')
            for msg in messages:
                backup_data['messages'].append({
                    'id': msg.id,
                    'sender_id': msg.sender_id,
                    'sender_username': msg.sender.username if hasattr(msg.sender, 'username') else '',
                    'text': msg.text,
                    'media_type': msg.media_type,
                    'created_at': msg.created_at.isoformat(),
                    'reactions': getattr(msg, 'reactions', {}),
                })
            
            # Настройки чата
            backup_data['settings'] = {
                'is_public': getattr(chat, 'is_public', True),
                'slow_mode_delay': getattr(chat, 'slow_mode_delay', 0),
                'can_send_media': getattr(chat, 'can_send_media', True),
                'can_send_stickers': getattr(chat, 'can_send_stickers', True),
            }
            
            # Сохраняем в файл
            backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
            backup_file = ContentFile(backup_json.encode('utf-8'))
            
            backup.backup_file.save(
                f'backup_{chat.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json',
                backup_file
            )
            
            # Обновляем статистику
            backup.messages_count = messages.count()
            backup.members_count = chat.members.count() if hasattr(chat, 'members') else 0
            backup.file_size = len(backup_json)
            backup.status = 'completed'
            backup.save()
            
            return {
                'success': True,
                'backup_id': backup.id,
                'messages_count': backup.messages_count,
                'members_count': backup.members_count,
                'file_size': backup.file_size,
            }
            
        except Exception as e:
            backup.status = 'failed'
            backup.save()
            return {
                'success': False,
                'error': str(e),
            }
    
    def restore_backup(self, backup_id: int, user) -> Dict:
        """
        Восстановить чат из резервной копии.
        """
        from ..models_chat import ChatBackup
        
        try:
            backup = ChatBackup.objects.get(id=backup_id, created_by=user)
            
            if backup.status != 'completed':
                return {'success': False, 'error': 'Backup is not ready'}
            
            # Читаем файл бэкапа
            with backup.backup_file.open('r') as f:
                backup_data = json.load(f)
            
            # Восстанавливаем данные
            # TODO: Реализовать логику восстановления
            
            return {
                'success': True,
                'restored_messages': len(backup_data.get('messages', [])),
                'restored_members': len(backup_data.get('members', [])),
            }
            
        except ChatBackup.DoesNotExist:
            return {'success': False, 'error': 'Backup not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ==================== SETTINGS EXPORT/IMPORT ====================

class SettingsExport:
    """
    Экспорт и импорт настроек чатов.
    """
    
    def export_user_settings(self, user) -> Dict:
        """
        Экспортировать все настройки пользователя.
        
        Returns:
            {
                'private_chats': [...],
                'group_chats': [...],
                'folders': [...],
                'themes': [...],
                'wallpapers': [...],
            }
        """
        from ..models import PrivateChat
        from ..models_chat import (
            PrivateChatSettings, ChatFolder, ChatTheme, ChatWallpaper, ChatSettings
        )
        
        export_data = {
            'version': '1.0',
            'exported_at': timezone.now().isoformat(),
            'private_chats': [],
            'group_chats': [],
            'folders': [],
            'themes': [],
            'wallpapers': [],
        }
        
        # Личные чаты
        private_chats = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)
        )
        for chat in private_chats:
            settings = PrivateChatSettings.objects.filter(chat=chat, user=user).first()
            if settings:
                export_data['private_chats'].append({
                    'chat_id': chat.id,
                    'custom_name': settings.custom_name,
                    'notifications_enabled': settings.notifications_enabled,
                    'sound_enabled': settings.sound_enabled,
                    'is_archived': settings.is_archived,
                    'is_pinned': settings.is_pinned,
                })
        
        # Групповые чаты
        from ..models import ChatMember
        memberships = ChatMember.objects.filter(user=user)
        for membership in memberships:
            settings = ChatSettings.objects.filter(
                user=user, chat=membership.chat
            ).first()
            if settings:
                export_data['group_chats'].append({
                    'chat_id': membership.chat.id,
                    'notifications_enabled': settings.notifications_enabled,
                    'sound_enabled': settings.sound_enabled,
                })
        
        # Папки
        folders = ChatFolder.objects.filter(user=user)
        for folder in folders:
            export_data['folders'].append({
                'name': folder.name,
                'icon': folder.icon,
                'color': folder.color,
                'include_private': folder.include_private,
                'include_groups': folder.include_groups,
            })
        
        # Темы
        themes = ChatTheme.objects.filter(user=user)
        for theme in themes:
            export_data['themes'].append({
                'theme': theme.theme,
                'message_color': theme.message_color,
                'message_color_other': theme.message_color_other,
                'bubble_style': theme.bubble_style,
                'font_size': theme.font_size,
            })
        
        return export_data
    
    def import_user_settings(self, user, import_data: Dict) -> Dict:
        """
        Импортировать настройки пользователя.
        """
        from ..models_chat import (
            ChatFolder, ChatTheme
        )
        
        results = {
            'imported': 0,
            'skipped': 0,
            'errors': [],
        }
        
        # Импортируем папки
        for folder_data in import_data.get('folders', []):
            try:
                ChatFolder.objects.get_or_create(
                    user=user,
                    name=folder_data['name'],
                    defaults=folder_data
                )
                results['imported'] += 1
            except Exception as e:
                results['errors'].append(f"Folder {folder_data.get('name')}: {str(e)}")
                results['skipped'] += 1
        
        # Импортируем темы
        for theme_data in import_data.get('themes', []):
            try:
                ChatTheme.objects.update_or_create(
                    user=user,
                    defaults=theme_data
                )
                results['imported'] += 1
            except Exception as e:
                results['errors'].append(f"Theme: {str(e)}")
                results['skipped'] += 1
        
        return results


# ==================== SETTINGS VERSIONING ====================

class SettingsVersioning:
    """
    Версионирование настроек с возможностью отката.
    """
    
    VERSION_PREFIX = 'settings_version'
    MAX_VERSIONS = 10
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
    
    def save_version(self, user_id: int, settings_type: str, settings_id: int, data: Dict) -> str:
        """
        Сохранить версию настроек.
        
        Returns:
            ID версии
        """
        version_id = str(uuid.uuid4())[:8]
        key = f"{self.VERSION_PREFIX}:{user_id}:{settings_type}:{settings_id}"
        
        version_data = {
            'id': version_id,
            'data': data,
            'created_at': timezone.now().isoformat(),
        }
        
        # Добавляем в список версий
        self.redis_client.lpush(key, json.dumps(version_data, default=str))
        
        # Ограничиваем количество версий
        self.redis_client.ltrim(key, 0, self.MAX_VERSIONS - 1)
        
        return version_id
    
    def get_version(self, user_id: int, settings_type: str, settings_id: int, version_id: str) -> Optional[Dict]:
        """Получить конкретную версию"""
        key = f"{self.VERSION_PREFIX}:{user_id}:{settings_type}:{settings_id}"
        
        versions = self.redis_client.lrange(key, 0, -1)
        for version_json in versions:
            version = json.loads(version_json)
            if version['id'] == version_id:
                return version['data']
        
        return None
    
    def get_versions(self, user_id: int, settings_type: str, settings_id: int) -> List[Dict]:
        """Получить все версии"""
        key = f"{self.VERSION_PREFIX}:{user_id}:{settings_type}:{settings_id}"
        
        versions = self.redis_client.lrange(key, 0, -1)
        return [json.loads(v) for v in versions]
    
    def rollback(self, user_id: int, settings_type: str, settings_id: int, version_id: str) -> bool:
        """Откатить настройки к указанной версии"""
        version_data = self.get_version(user_id, settings_type, settings_id, version_id)
        
        if not version_data:
            return False
        
        # TODO: Реализовать применение в зависимости от типа настроек
        # Применяем настройки
        try:
            if settings_type == 'private_chat':
                from ..models_chat import PrivateChatSettings
                settings = PrivateChatSettings.objects.get(chat_id=settings_id, user_id=user_id)
                for key, value in version_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.save()
            elif settings_type == 'group_chat':
                from ..models_chat import ChatSettings
                settings = ChatSettings.objects.get(chat_id=settings_id, user_id=user_id)
                for key, value in version_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.save()
            return True
        except Exception as e:
            print(f"Error rolling back settings: {e}")
            return False


# ==================== NOTIFICATION SERVICE ====================

class NotificationService:
    """
    Сервис отправки уведомлений через WebSocket.
    """
    
    def __init__(self):
        try:
            from channels.layers import get_channel_layer
            self.channel_layer = get_channel_layer()
        except ImportError:
            self.channel_layer = None
    
    async def send_to_chat(self, chat, event_type: str, data: Dict, exclude_users: List[int] = None):
        """Отправить уведомление всем участникам чата"""
        if not self.channel_layer:
            return
        
        chat_id = chat.id if hasattr(chat, 'id') else chat
        
        await self.channel_layer.group_send(
            f'chat_{chat_id}',
            {
                'type': 'chat_message',
                'event_type': event_type,
                'data': data,
                'exclude_users': exclude_users or [],
            }
        )
    
    async def send_to_user(self, user_id: int, event_type: str, data: Dict):
        """Отправить уведомление конкретному пользователю"""
        if not self.channel_layer:
            return
        
        await self.channel_layer.group_send(
            f'user_{user_id}',
            {
                'type': 'notification_event',
                'event_type': event_type,
                'data': data,
            }
        )
    
    async def broadcast_to_chat_members(self, chat, event_type: str, data: Dict):
        """Разослать уведомление всем участникам чата индивидуально"""
        if not self.channel_layer or not hasattr(chat, 'members'):
            return
        
        member_ids = list(chat.members.values_list('user_id', flat=True))
        for user_id in member_ids:
            await self.send_to_user(user_id, event_type, data)


# ==================== DECORATORS ====================

def permission_required(permission_name: str):
    """
    Декоратор для проверки прав доступа.
    
    Usage:
        @permission_required('can_delete_messages')
        def delete_message(request, message_id):
            ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            from ..models import GroupChat, PrivateChat
            
            # Определяем чат
            chat_id = kwargs.get('chat_id') or kwargs.get('pk')
            chat_type = kwargs.get('chat_type', 'group')
            
            if not chat_id:
                return func(request, *args, **kwargs)
            
            try:
                if chat_type == 'private':
                    chat = PrivateChat.objects.get(id=chat_id)
                else:
                    chat = GroupChat.objects.get(id=chat_id)
                
                checker = PermissionChecker(request.user, chat)
                result = checker.has_permission(permission_name)
                
                if not result.allowed:
                    from django.http import JsonResponse
                    return JsonResponse(
                        {'error': result.reason},
                        status=403
                    )
                
            except (GroupChat.DoesNotExist, PrivateChat.DoesNotExist):
                pass
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(action_type: str, limit: int, period: int):
    """
    Декоратор для ограничения частоты действий.
    
    Usage:
        @rate_limit('message', 10, 60)  # 10 сообщений в минуту
        def send_message(request):
            ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            limiter = RateLimiter()
            
            if not limiter.is_allowed(request.user.id, action_type, limit, period):
                from django.http import JsonResponse
                retry_after = limiter.get_retry_after(request.user.id, action_type)
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'retry_after': retry_after,
                    },
                    status=429
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def log_admin_action(func):
    """
    Декоратор для логирования действий администраторов.
    """
    def wrapper(request, *args, **kwargs):
        from ..models import ChatAdminLog
        
        # Выполняем действие
        result = func(request, *args, **kwargs)
        
        # Логируем
        try:
            chat_id = kwargs.get('chat_id') or kwargs.get('pk')
            if chat_id:
                from ..models import GroupChat
                chat = GroupChat.objects.get(id=chat_id)
                
                ChatAdminLog.objects.create(
                    chat=chat,
                    user=request.user,
                    action=func.__name__,
                    details={
                        'args': str(args),
                        'kwargs': str(kwargs),
                    }
                )
        except Exception as e:
            print(f"Error logging admin action: {e}")
        
        return result
    
    return wrapper


# ==================== SINGLETON INSTANCES ====================

settings_cache = SettingsCache()
rate_limiter = RateLimiter()
smart_notifications = SmartNotifications()
settings_export = SettingsExport()
settings_versioning = SettingsVersioning()