import redis
import json
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RedisEventPublisher:
    """Публикатор событий в Redis для реального времени обновлений"""

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
                # Проверяем соединение
                self._redis_client.ping()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if not self._connection_error_logged:
                    logger.warning(f"Redis не доступен: {e}. Функционал реального времени отключен.")
                    self._connection_error_logged = True
                self._redis_client = None
        return self._redis_client

    def publish_event(self, event_type: str, data: Dict[str, Any], target_users: Optional[list] = None) -> None:
        """
        Публикует событие в Redis

        Args:
            event_type: Тип события (post_created, user_online, etc.)
            data: Данные события
            target_users: Список ID пользователей для отправки (None = всем)
        """
        if self.redis_client is None:
            return

        try:
            event = {
                'type': event_type,
                'data': data,
                'timestamp': self._get_timestamp(),
                'target_users': target_users
            }

            # Публикуем в канал реального времени
            channel = 'realtime_updates'
            self.redis_client.publish(channel, json.dumps(event))

            # Также сохраняем в очередь для новых подключений
            queue_key = 'realtime_queue'
            self.redis_client.lpush(queue_key, json.dumps(event))

            # Ограничиваем размер очереди (последние 100 событий)
            self.redis_client.ltrim(queue_key, 0, 99)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis publish error (ignored): {e}")
        except Exception as e:
            logger.debug(f"Redis error: {e}")

    def get_recent_events(self, limit: int = 50) -> list:
        """Получить недавние события из очереди"""
        if self.redis_client is None:
            return []

        try:
            queue_key = 'realtime_queue'
            events_data = self.redis_client.lrange(queue_key, 0, limit - 1)
            events = []
            for event_data in events_data:
                try:
                    events.append(json.loads(event_data))
                except json.JSONDecodeError:
                    continue
            return events
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis get events error (ignored): {e}")
            return []
        except Exception as e:
            logger.debug(f"Redis error: {e}")
            return []

    def _get_timestamp(self) -> str:
        """Получить текущий timestamp"""
        from django.utils import timezone
        return timezone.now().isoformat()


# Глобальный экземпляр для использования в приложении
event_publisher = RedisEventPublisher()


# Вспомогательные функции для публикации конкретных событий
def publish_post_created(post_data: Dict[str, Any]) -> None:
    """Публикация события создания поста"""
    event_publisher.publish_event('post_created', post_data)


def publish_post_updated(post_data: Dict[str, Any]) -> None:
    """Публикация события обновления поста"""
    event_publisher.publish_event('post_updated', post_data)


def publish_post_deleted(post_id: int) -> None:
    """Публикация события удаления поста"""
    event_publisher.publish_event('post_deleted', {'post_id': post_id})


def publish_user_online(user_id: int, username: str) -> None:
    """Публикация события пользователь онлайн"""
    event_publisher.publish_event('user_online', {
        'user_id': user_id,
        'username': username
    })


def publish_user_offline(user_id: int, username: str) -> None:
    """Публикация события пользователь оффлайн"""
    event_publisher.publish_event('user_offline', {
        'user_id': user_id,
        'username': username
    })


def publish_chat_created(chat_data: Dict[str, Any]) -> None:
    """Публикация события создания чата"""
    event_publisher.publish_event('chat_created', chat_data)


def publish_message_sent(message_data: Dict[str, Any]) -> None:
    """Публикация события отправки сообщения"""
    event_publisher.publish_event('message_sent', message_data)


def publish_anime_updated(anime_data: Dict[str, Any]) -> None:
    """Публикация события обновления аниме"""
    event_publisher.publish_event('anime_updated', anime_data)