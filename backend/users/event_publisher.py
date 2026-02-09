import redis
import json
from datetime import datetime
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB

class EventPublisher:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    def publish_event(self, event_type, data):
        """Публикация события в Redis"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        }
        # Храним события в списке для последних 1000 событий
        self.redis.lpush('events', json.dumps(event))
        self.redis.ltrim('events', 0, 999)  # Ограничиваем размер списка

        # Также публикуем в канал для real-time подписчиков
        self.redis.publish('realtime_events', json.dumps(event))

    def get_recent_events(self, limit=50):
        """Получить недавние события"""
        events = self.redis.lrange('events', 0, limit - 1)
        return [json.loads(event.decode('utf-8')) for event in events[::-1]]  # Обратный порядок

# Глобальный инстанс
event_publisher = EventPublisher()