"""
Утилиты для отслеживания статуса онлайн пользователей через Redis
"""
import redis
import json
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Ключ в Redis: user_online:{user_id}
ONLINE_KEY_PREFIX = 'user_online:'
# TTL в секундах - 2 минуты (пользователь считается онлайн пока активно использует сайт)
# Если вкладка активна - heartbeat обновляет TTL каждые 30 секунд
ONLINE_TTL = 120
# TTL для неактивных пользователей (отошёл от компа) - 5 минут
AWAY_TTL = 60


class RedisOnlineStatus:
    """Класс для управления статусом онлайн через Redis"""

    def __init__(self):
        self._redis_client = None
        self._connection_error_logged = False

    @property
    def redis_client(self):
        """Ленивое подключение к Redis с обработкой ошибок"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )
                self._redis_client.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if not self._connection_error_logged:
                    logger.warning(f"Redis не доступен для статуса онлайн: {e}")
                    self._connection_error_logged = True
                self._redis_client = None
        return self._redis_client

    def set_online(self, user_id: int, username: str, extra_data: Optional[Dict[str, Any]] = None, is_active: bool = True) -> None:
        """Установить статус онлайн для пользователя.
        
        TTL зависит от активности:
        - is_active=True: 2 минуты (пользователь активно использует сайт)
        - is_active=False: 5 минут (отошёл от компа)
        
        Каждый API-запрос или явный heartbeat сбрасывает таймер.
        """
        if self.redis_client is None:
            return

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            now = timezone.now()
            ttl = ONLINE_TTL if is_active else AWAY_TTL
            data = {
                'user_id': user_id,
                'username': username,
                'last_seen': now.isoformat(),
                'last_seen_ts': now.timestamp(),
                'is_active': is_active,
                **(extra_data or {})
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            
            # Отправляем событие в channel layer для WebSocket
            self._send_online_event(user_id, username, True)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis set_online error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def _send_online_event(self, user_id: int, username: str, is_online: bool) -> None:
        """Отправить событие онлайн статуса в channel layer"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f"user_online_{user_id}"
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "user_online",
                        "user_id": user_id,
                        "username": username,
                        "is_online": is_online,
                    }
                )
        except Exception as e:
            logger.debug(f"Channel layer send error: {e}")

    def set_offline(self, user_id: int) -> None:
        """Установить статус оффлайн для пользователя"""
        if self.redis_client is None:
            return

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            self.redis_client.delete(key)
            
            # Отправляем событие в channel layer для WebSocket
            from django.contrib.auth import get_user_model
            User = get_user_model()
            username = User.objects.filter(id=user_id).values_list('username', flat=True).first() or 'Unknown'
            self._send_online_event(user_id, username, False)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis set_offline error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def is_online(self, user_id: int) -> bool:
        """Проверить, онлайн ли пользователь"""
        if self.redis_client is None:
            return False

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            return self.redis_client.exists(key) > 0
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis is_online error (ignored): {e}")
            return False
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return False

    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя из Redis"""
        if self.redis_client is None:
            return None

        try:
            key = f"{ONLINE_KEY_PREFIX}{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis get_user_data error (ignored): {e}")
            return None
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return None

    def get_online_users(self) -> list:
        """Получить всех онлайн пользователей"""
        if self.redis_client is None:
            return []

        try:
            pattern = f"{ONLINE_KEY_PREFIX}*"
            keys = self.redis_client.keys(pattern)
            users = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        users.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
            return users
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis get_online_users error (ignored): {e}")
            return []
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return []

    def refresh_online(self, user_id: int, username: str) -> None:
        """Обновить время последней активности"""
        self.set_online(user_id, username)


# Ключ в Redis: typing:{chat_id}:{user_id}
TYPING_KEY_PREFIX = 'typing:'
# TTL для статуса печатания (5 секунд)
TYPING_TTL = 5


class RedisTypingStatus:
    """Класс для управления статусом печатания через Redis"""

    def __init__(self):
        self._redis_client = None
        self._connection_error_logged = False

    @property
    def redis_client(self):
        """Ленивое подключение к Redis с обработкой ошибок"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )
                self._redis_client.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if not self._connection_error_logged:
                    logger.warning(f"Redis не доступен для статуса печатания: {e}")
                    self._connection_error_logged = True
                self._redis_client = None
        return self._redis_client

    def set_typing(self, chat_id: int, user_id: int, username: str) -> None:
        """Установить статус печатания"""
        if self.redis_client is None:
            return

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            data = json.dumps({
                'user_id': user_id,
                'username': username,
                'timestamp': timezone.now().isoformat()
            })
            self.redis_client.setex(key, TYPING_TTL, data)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis set_typing error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def stop_typing(self, chat_id: int, user_id: int) -> None:
        """Остановить статус печатания"""
        if self.redis_client is None:
            return

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            self.redis_client.delete(key)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis stop_typing error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def is_typing(self, chat_id: int, user_id: int) -> bool:
        """Проверить, печатает ли пользователь"""
        if self.redis_client is None:
            return False

        try:
            key = f"{TYPING_KEY_PREFIX}{chat_id}:{user_id}"
            return self.redis_client.exists(key) > 0
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis is_typing error (ignored): {e}")
            return False
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return False

    def get_typing_users(self, chat_id: int) -> list:
        """Получить всех печатающих пользователей в чате"""
        if self.redis_client is None:
            return []

        try:
            pattern = f"{TYPING_KEY_PREFIX}{chat_id}:*"
            keys = self.redis_client.keys(pattern)
            typing_users = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        typing_users.append(json.loads(data))
                    except json.JSONDecodeError:
                        continue
            return typing_users
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis get_typing_users error (ignored): {e}")
            return []
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return []

    def stop_all_typing(self, chat_id: int) -> None:
        """Остановить печатание всех пользователей в чате"""
        if self.redis_client is None:
            return

        try:
            pattern = f"{TYPING_KEY_PREFIX}{chat_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis stop_all_typing error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")


# Глобальный экземпляр
online_status = RedisOnlineStatus()
typing_status = RedisTypingStatus()


# Вспомогательные функции
def publish_user_online_event(user_id: int, username: str) -> None:
    """Публикация события пользователь онлайн (для WebSocket)"""
    from core.redis_events import publish_user_online as redis_publish
    try:
        redis_publish(user_id, username)
    except Exception:
        pass  # Игнорируем ошибки Redis events


def publish_user_offline_event(user_id: int, username: str) -> None:
    """Публикация события пользователь оффлайн (для WebSocket)"""
    from core.redis_events import publish_user_offline as redis_publish
    try:
        redis_publish(user_id, username)
    except Exception:
        pass  # Игнорируем ошибки Redis events