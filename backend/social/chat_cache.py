"""
Сервис для кэширования данных чатов в Redis
"""
import json
from typing import List, Dict, Optional, Any
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class ChatCacheService:
    """Сервис для работы с кэшем чатов"""

    # TTL для разных типов данных
    TTL_LAST_MESSAGES = 86400  # 24 часа
    TTL_CHAT_INFO = 3600  # 1 час
    TTL_USER_INFO = 3600  # 1 час
    TTL_TYPING = 5  # 5 секунд

    @staticmethod
    def _get_chat_last_messages_key(chat_id: int) -> str:
        """Ключ для списка последних сообщений чата"""
        return f"chat:{chat_id}:last_messages"

    @staticmethod
    def _get_chat_last_message_key(chat_id: int) -> str:
        """Ключ для последнего сообщения чата"""
        return f"chat:{chat_id}:last_message"

    @staticmethod
    def _get_chat_info_key(chat_id: int) -> str:
        """Ключ для информации о чате"""
        return f"chat:{chat_id}:info"

    @staticmethod
    def _get_user_info_key(user_id: int) -> str:
        """Ключ для информации о пользователе"""
        return f"user:{user_id}:info"

    @staticmethod
    def _get_user_unread_chat_key(user_id: int, chat_id: int) -> str:
        """Ключ для счётчика непрочитанных сообщений в конкретном чате"""
        return f"user:{user_id}:unread:{chat_id}"

    @staticmethod
    def _get_user_unread_total_key(user_id: int) -> str:
        """Ключ для общего счётчика непрочитанных сообщений"""
        return f"user:{user_id}:unread:total"

    @staticmethod
    def _get_user_unread_chats_key(user_id: int) -> str:
        """Ключ для множества чатов с непрочитанными сообщениями"""
        return f"user:{user_id}:unread_chats"

    @staticmethod
    def _get_typing_key(chat_id: int, user_id: int) -> str:
        """Ключ для статуса печати"""
        return f"typing:{chat_id}:{user_id}"

    @staticmethod
    def _serialize_message(message: Any) -> Dict:
        """Сериализация сообщения для хранения в кэше"""
        return {
            'id': message.id,
            'sender_id': message.sender_id,
            'text': message.text,
            'media_type': message.media_type,
            'media_url': message.media.url if message.media else None,
            'created_at': message.created_at.isoformat(),
            'is_edited': message.is_edited,
            'is_deleted': message.is_deleted,
            'is_pinned': message.is_pinned,
            'reply_to_id': message.reply_to_id,
            'forwarded_from_id': message.forwarded_from_id,
            'reactions': message.reactions,
        }

    @staticmethod
    def get_last_messages(chat_id: int, limit: int = 50) -> List[Dict]:
        """Получить последние сообщения чата из кэша"""
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        cached = cache.get(key)

        if cached:
            return cached[:limit]

        return []

    @staticmethod
    def add_message_to_cache(chat_id: int, message: Any, max_cached: int = 50) -> None:
        """Добавить сообщение в кэш последних сообщений"""
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id, max_cached)

        serialized = ChatCacheService._serialize_message(message)
        messages.append(serialized)

        # Ограничиваем количество сообщений
        if len(messages) > max_cached:
            messages = messages[-max_cached:]

        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

        # Обновляем последнее сообщение
        ChatCacheService.set_last_message(chat_id, serialized)

    @staticmethod
    def update_message_in_cache(chat_id: int, message_id: int, updates: Dict) -> None:
        """Обновить сообщение в кэше"""
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id)

        for msg in messages:
            if msg['id'] == message_id:
                msg.update(updates)
                break

        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def remove_message_from_cache(chat_id: int, message_id: int) -> None:
        """Удалить сообщение из кэша"""
        key = ChatCacheService._get_chat_last_messages_key(chat_id)
        messages = ChatCacheService.get_last_messages(chat_id)

        messages = [msg for msg in messages if msg['id'] != message_id]
        cache.set(key, messages, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def set_last_message(chat_id: int, message: Dict) -> None:
        """Установить последнее сообщение чата"""
        key = ChatCacheService._get_chat_last_message_key(chat_id)
        cache.set(key, message, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def get_last_message(chat_id: int) -> Optional[Dict]:
        """Получить последнее сообщение чата"""
        key = ChatCacheService._get_chat_last_message_key(chat_id)
        return cache.get(key)

    @staticmethod
    def set_chat_info(chat_id: int, info: Dict) -> None:
        """Сохранить информацию о чате в кэш"""
        key = ChatCacheService._get_chat_info_key(chat_id)
        cache.set(key, info, ChatCacheService.TTL_CHAT_INFO)

    @staticmethod
    def get_chat_info(chat_id: int) -> Optional[Dict]:
        """Получить информацию о чате из кэша"""
        key = ChatCacheService._get_chat_info_key(chat_id)
        return cache.get(key)

    @staticmethod
    def invalidate_chat_info(chat_id: int) -> None:
        """Инвалидировать кэш информации о чате"""
        key = ChatCacheService._get_chat_info_key(chat_id)
        cache.delete(key)

    @staticmethod
    def set_user_info(user_id: int, info: Dict) -> None:
        """Сохранить информацию о пользователе в кэш"""
        key = ChatCacheService._get_user_info_key(user_id)
        cache.set(key, info, ChatCacheService.TTL_USER_INFO)

    @staticmethod
    def get_user_info(user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе из кэша"""
        key = ChatCacheService._get_user_info_key(user_id)
        return cache.get(key)

    @staticmethod
    def invalidate_user_info(user_id: int) -> None:
        """Инвалидировать кэш информации о пользователе"""
        key = ChatCacheService._get_user_info_key(user_id)
        cache.delete(key)

    @staticmethod
    def increment_unread(user_id: int, chat_id: int, count: int = 1) -> int:
        """Увеличить счётчик непрочитанных сообщений"""
        # Увеличиваем счётчик по конкретному чату
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = cache.get(chat_key, 0) + count
        cache.set(chat_key, unread_count, ChatCacheService.TTL_LAST_MESSAGES)

        # Увеличиваем общий счётчик
        total_key = ChatCacheService._get_user_unread_total_key(user_id)
        total_unread = cache.get(total_key, 0) + count
        cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

        # Добавляем чат в множество непрочитанных
        chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
        unread_chats = cache.get(chats_key, set())
        unread_chats.add(chat_id)
        cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

        return unread_count

    @staticmethod
    def decrement_unread(user_id: int, chat_id: int, count: int = 1) -> int:
        """Уменьшить счётчик непрочитанных сообщений"""
        # Уменьшаем счётчик по конкретному чату
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = max(0, cache.get(chat_key, 0) - count)
        cache.set(chat_key, unread_count, ChatCacheService.TTL_LAST_MESSAGES)

        # Уменьшаем общий счётчик
        total_key = ChatCacheService._get_user_unread_total_key(user_id)
        total_unread = max(0, cache.get(total_key, 0) - count)
        cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

        # Если счётчик по чату стал 0, удаляем из множества
        if unread_count == 0:
            chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
            unread_chats = cache.get(chats_key, set())
            unread_chats.discard(chat_id)
            cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

        return unread_count

    @staticmethod
    def get_unread_count(user_id: int, chat_id: Optional[int] = None) -> int:
        """Получить количество непрочитанных сообщений"""
        if chat_id:
            key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        else:
            key = ChatCacheService._get_user_unread_total_key(user_id)

        return cache.get(key, 0)

    @staticmethod
    def get_unread_chats(user_id: int) -> List[int]:
        """Получить список чатов с непрочитанными сообщениями"""
        key = ChatCacheService._get_user_unread_chats_key(user_id)
        return list(cache.get(key, set()))

    @staticmethod
    def mark_chat_read(user_id: int, chat_id: int) -> None:
        """Отметить весь чат как прочитанный"""
        chat_key = ChatCacheService._get_user_unread_chat_key(user_id, chat_id)
        unread_count = cache.get(chat_key, 0)

        if unread_count > 0:
            # Уменьшаем общий счётчик
            total_key = ChatCacheService._get_user_unread_total_key(user_id)
            total_unread = max(0, cache.get(total_key, 0) - unread_count)
            cache.set(total_key, total_unread, ChatCacheService.TTL_LAST_MESSAGES)

            # Обнуляем счётчик по чату
            cache.set(chat_key, 0, ChatCacheService.TTL_LAST_MESSAGES)

            # Удаляем из множества
            chats_key = ChatCacheService._get_user_unread_chats_key(user_id)
            unread_chats = cache.get(chats_key, set())
            unread_chats.discard(chat_id)
            cache.set(chats_key, unread_chats, ChatCacheService.TTL_LAST_MESSAGES)

    @staticmethod
    def set_typing(chat_id: int, user_id: int) -> None:
        """Установить статус 'печатает'"""
        key = ChatCacheService._get_typing_key(chat_id, user_id)
        cache.set(key, timezone.now().isoformat(), ChatCacheService.TTL_TYPING)

    @staticmethod
    def remove_typing(chat_id: int, user_id: int) -> None:
        """Удалить статус "печатает\""""
        key = ChatCacheService._get_typing_key(chat_id, user_id)
        cache.delete(key)

    @staticmethod
    def get_typing_users(chat_id: int, user_ids: List[int]) -> List[int]:
        """Получить список пользователей, которые печатают в чате"""
        typing_users = []
        for user_id in user_ids:
            key = ChatCacheService._get_typing_key(chat_id, user_id)
            if cache.get(key):
                typing_users.append(user_id)
        return typing_users

    @staticmethod
    def clear_chat_cache(chat_id: int) -> None:
        """Очистить весь кэш чата"""
        keys = [
            ChatCacheService._get_chat_last_messages_key(chat_id),
            ChatCacheService._get_chat_last_message_key(chat_id),
            ChatCacheService._get_chat_info_key(chat_id),
        ]
        cache.delete_many(keys)

    @staticmethod
    def clear_user_cache(user_id: int) -> None:
        """Очистить весь кэш пользователя"""
        keys = [
            ChatCacheService._get_user_info_key(user_id),
            ChatCacheService._get_user_unread_total_key(user_id),
            ChatCacheService._get_user_unread_chats_key(user_id),
        ]
        cache.delete_many(keys)
