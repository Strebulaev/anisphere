# backend/social/feed_cache.py
"""
Redis кэш для ленты постов
"""
import json
import redis
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta


class FeedCache:
    """Класс для работы с кэшем ленты в Redis"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    # ==================== FEED CACHE ====================

    def add_post_to_feed(self, user_id: int, post_id: int, timestamp: float = None):
        """Добавить пост в ленту пользователя"""
        if timestamp is None:
            timestamp = timezone.now().timestamp()

        key = f"feed:user:{user_id}"
        # Sorted set сортируем по времени публикации
        self.redis_client.zadd(key, {str(post_id): timestamp})

        # Ограничиваем размер ленты до 200 постов
        self.redis_client.zremrangebyrank(key, 0, -201)

        # Устанавливаем TTL 7 дней
        self.redis_client.expire(key, 7 * 24 * 60 * 60)

    def remove_post_from_feed(self, user_id: int, post_id: int):
        """Удалить пост из ленты пользователя"""
        key = f"feed:user:{user_id}"
        self.redis_client.zrem(key, str(post_id))

    def get_user_feed(self, user_id: int, offset: int = 0, limit: int = 20) -> list:
        """Получить ленту пользователя"""
        key = f"feed:user:{user_id}"
        # Получаем посты от newest к oldest
        post_ids = self.redis_client.zrevrange(key, offset, offset + limit - 1)
        return [int(pid) for pid in post_ids]

    def get_feed_count(self, user_id: int) -> int:
        """Получить количество постов в ленте"""
        key = f"feed:user:{user_id}"
        return self.redis_client.zcard(key)

    def update_last_read(self, user_id: int):
        """Обновить время последнего прочитанного поста"""
        key = f"feed:user:{user_id}:last_read"
        self.redis_client.set(key, timezone.now().isoformat())
        self.redis_client.expire(key, 30 * 24 * 60 * 60)  # 30 дней

    def get_last_read_time(self, user_id: int) -> datetime:
        """Получить время последнего прочитанного поста"""
        key = f"feed:user:{user_id}:last_read"
        last_read = self.redis_client.get(key)
        if last_read:
            return datetime.fromisoformat(last_read)
        return None

    def get_new_posts_count(self, user_id: int) -> int:
        """Получить количество новых постов"""
        last_read = self.get_last_read_time(user_id)
        if not last_read:
            return self.get_feed_count(user_id)

        # Считаем посты, опубликованные после last_read
        timestamp = last_read.timestamp()
        key = f"feed:user:{user_id}"
        return self.redis_client.zcount(key, timestamp, '+inf')

    # ==================== POST CACHE ====================

    def set_post_data(self, post_id: int, data: dict):
        """Кэшировать данные поста"""
        key = f"post:{post_id}:data"
        self.redis_client.setex(key, 3600, json.dumps(data))  # 1 час

    def get_post_data(self, post_id: int) -> dict:
        """Получить кэшированные данные поста"""
        key = f"post:{post_id}:data"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def update_post_count(self, post_id: int, field: str, delta: int):
        """Обновить счётчик поста (лайки, дизлайки, комментарии и т.д.)"""
        key = f"post:{post_id}:counts"
        field_key = f"{field}_count"

        # Используем hash для хранения всех счётчиков
        self.redis_client.hincrby(key, field_key, delta)
        self.redis_client.expire(key, 3600)  # 1 час

    def get_post_counts(self, post_id: int) -> dict:
        """Получить все счётчики поста"""
        key = f"post:{post_id}:counts"
        counts = self.redis_client.hgetall(key)
        return {k: int(v) for k, v in counts.items()}

    def set_user_reaction(self, user_id: int, post_id: int, reaction: str):
        """Сохранить реакцию пользователя на пост"""
        key = f"post:{post_id}:user:{user_id}:reaction"
        if reaction == 'none':
            self.redis_client.delete(key)
        else:
            self.redis_client.setex(key, 7 * 24 * 60 * 60, reaction)  # 7 дней

    def get_user_reaction(self, user_id: int, post_id: int) -> str:
        """Получить реакцию пользователя на пост"""
        key = f"post:{post_id}:user:{user_id}:reaction"
        return self.redis_client.get(key) or 'none'

    # ==================== COMMENTS CACHE ====================

    def add_comment_to_post(self, post_id: int, comment_id: int):
        """Добавить комментарий в кэш поста"""
        # Recent comments
        key = f"post:{post_id}:comments:recent"
        self.redis_client.lpush(key, str(comment_id))
        self.redis_client.ltrim(key, 0, 49)  # Ограничиваем 50 комментариями
        self.redis_client.expire(key, 3600)

    def get_recent_comments(self, post_id: int, limit: int = 10) -> list:
        """Получить последние комментарии поста"""
        key = f"post:{post_id}:comments:recent"
        comment_ids = self.redis_client.lrange(key, 0, limit - 1)
        return [int(cid) for cid in comment_ids]

    def add_top_comment(self, post_id: int, comment_id: int, likes: int):
        """Добавить комментарий в топ"""
        key = f"post:{post_id}:comments:top"
        self.redis_client.zadd(key, {str(comment_id): likes})
        self.redis_client.zremrangebyrank(key, 0, -21)  # Оставляем топ-20
        self.redis_client.expire(key, 3600)

    def get_top_comments(self, post_id: int, limit: int = 10) -> list:
        """Получить топ комментариев по лайкам"""
        key = f"post:{post_id}:comments:top"
        comment_ids = self.redis_client.zrevrange(key, 0, limit - 1)
        return [int(cid) for cid in comment_ids]

    def set_comment_data(self, comment_id: int, data: dict):
        """Кэшировать данные комментария"""
        key = f"comment:{comment_id}:data"
        self.redis_client.setex(key, 3600, json.dumps(data))

    def get_comment_data(self, comment_id: int) -> dict:
        """Получить кэшированные данные комментария"""
        key = f"comment:{comment_id}:data"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_comment_reaction(self, user_id: int, comment_id: int, reaction: str):
        """Сохранить реакцию пользователя на комментарий"""
        key = f"comment:{comment_id}:user:{user_id}:reaction"
        if reaction == 'none':
            self.redis_client.delete(key)
        else:
            self.redis_client.setex(key, 7 * 24 * 60 * 60, reaction)

    def get_comment_reaction(self, user_id: int, comment_id: int) -> str:
        """Получить реакцию пользователя на комментарий"""
        key = f"comment:{comment_id}:user:{user_id}:reaction"
        return self.redis_client.get(key) or 'none'

    # ==================== INVALIDATION ====================

    def invalidate_post(self, post_id: int):
        """Инвалидировать кэш поста"""
        keys = self.redis_client.keys(f"post:{post_id}:*")
        if keys:
            self.redis_client.delete(*keys)

    def set_post_popularity(self, post_id: int, score: float):
        """Установить популярность поста для сортировки"""
        key = f"post:{post_id}:popularity"
        self.redis_client.set(key, score, ex=86400 * 7)  # 7 дней

    def get_post_popularity(self, post_id: int) -> float:
        """Получить популярность поста"""
        key = f"post:{post_id}:popularity"
        score = self.redis_client.get(key)
        return float(score) if score else 0.0

    def invalidate_user_feed(self, user_id: int):
        """Инвалидировать ленту пользователя"""
        key = f"feed:user:{user_id}"
        self.redis_client.delete(key)

    def invalidate_all_feeds(self):
        """Инвалидировать все ленты (вызывается при очистке)"""
        keys = self.redis_client.keys("feed:user:*")
        if keys:
            self.redis_client.delete(*keys)

    # ==================== FEED UPDATE ====================

    def update_followers_feeds(self, author_id: int, post_id: int):
        """Обновить ленты всех подписчиков автора"""
        from .models import Follow

        # Получаем всех подписчиков
        follower_ids = Follow.objects.filter(following_id=author_id).values_list('follower_id', flat=True)

        timestamp = timezone.now().timestamp()
        for follower_id in follower_ids:
            self.add_post_to_feed(follower_id, post_id, timestamp)

    # ==================== VIEWS CACHE ====================

    def increment_views(self, post_id: int):
        """Увеличить счётчик просмотров"""
        key = f"post:{post_id}:views"
        self.redis_client.incr(key)

    def get_views_count(self, post_id: int) -> int:
        """Получить количество просмотров из кэша"""
        key = f"post:{post_id}:views"
        count = self.redis_client.get(key)
        return int(count) if count else 0

    # ==================== BOOKMARKS CACHE ====================

    def add_bookmark(self, user_id: int, post_id: int, folder: str = ''):
        """Добавить пост в закладки"""
        key = f"bookmarks:user:{user_id}"
        data = json.dumps({'post_id': post_id, 'folder': folder})
        self.redis_client.zadd(key, {str(post_id): timezone.now().timestamp()})
        self.redis_client.expire(key, 30 * 24 * 60 * 60)  # 30 дней

    def remove_bookmark(self, user_id: int, post_id: int):
        """Удалить пост из закладок"""
        key = f"bookmarks:user:{user_id}"
        self.redis_client.zrem(key, str(post_id))

    def get_user_bookmarks(self, user_id: int, folder: str = None, offset: int = 0, limit: int = 20) -> list:
        """Получить закладки пользователя"""
        key = f"bookmarks:user:{user_id}"
        
        if folder:
            # Фильтрация по папке (не поддерживается напрямую в Redis, используем хэш)
            folder_key = f"bookmarks:user:{user_id}:folder:{folder}"
            bookmark_ids = self.redis_client.zrevrange(folder_key, offset, offset + limit - 1)
        else:
            bookmark_ids = self.redis_client.zrevrange(key, offset, offset + limit - 1)
        
        return [int(bid) for bid in bookmark_ids]

    def get_bookmarks_count(self, user_id: int) -> int:
        """Получить количество закладок"""
        key = f"bookmarks:user:{user_id}"
        return self.redis_client.zcard(key)

    # ==================== REPOSTS CACHE ====================

    def increment_reposts(self, post_id: int):
        """Увеличить счётчик репостов"""
        key = f"post:{post_id}:reposts"
        self.redis_client.incr(key)

    def get_reposts_count(self, post_id: int) -> int:
        """Получить количество репостов из кэша"""
        key = f"post:{post_id}:reposts"
        count = self.redis_client.get(key)
        return int(count) if count else 0

    # ==================== POPULAR POSTS ====================

    def add_to_popular(self, post_id: int, score: float):
        """Добавить пост в популярные"""
        key = "feed:popular"
        self.redis_client.zadd(key, {str(post_id): score})
        self.redis_client.zremrangebyrank(key, 0, -101)  # Оставляем топ-100
        self.redis_client.expire(key, 3600)  # 1 час

    def get_popular_posts(self, limit: int = 50) -> list:
        """Получить популярные посты"""
        key = "feed:popular"
        post_ids = self.redis_client.zrevrange(key, 0, limit - 1)
        return [int(pid) for pid in post_ids]

    # ==================== HASHTAG FEED ====================

    def add_to_hashtag_feed(self, hashtag: str, post_id: int):
        """Добавить пост в ленту хэштега"""
        key = f"feed:hashtag:{hashtag.lower()}"
        self.redis_client.zadd(key, {str(post_id): timezone.now().timestamp()})
        self.redis_client.zremrangebyrank(key, 0, -201)  # Ограничиваем 200 постами
        self.redis_client.expire(key, 30 * 24 * 60 * 60)  # 30 дней

    def get_hashtag_posts(self, hashtag: str, offset: int = 0, limit: int = 20) -> list:
        """Получить посты по хэштегу"""
        key = f"feed:hashtag:{hashtag.lower()}"
        post_ids = self.redis_client.zrevrange(key, offset, offset + limit - 1)
        return [int(pid) for pid in post_ids]

    # ==================== USER ACTIVITY ====================

    def set_user_last_activity(self, user_id: int):
        """Установить время последней активности пользователя"""
        key = f"user:{user_id}:last_activity"
        self.redis_client.set(key, timezone.now().isoformat())
        self.redis_client.expire(key, 24 * 60 * 60)  # 24 часа

    def get_user_last_activity(self, user_id: int) -> datetime:
        """Получить время последней активности"""
        key = f"user:{user_id}:last_activity"
        last_activity = self.redis_client.get(key)
        if last_activity:
            return datetime.fromisoformat(last_activity)
        return None


# Глобальный экземпляр
feed_cache = FeedCache()
