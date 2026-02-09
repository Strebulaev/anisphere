from django.db import models
from users.models import User

class ReactorPost(models.Model):
    """Shorts видео (Reactor)"""

    # Автор и контент
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactor_posts')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Видео
    video_file = models.FileField(upload_to='reactor/videos/')
    thumbnail_file = models.ImageField(upload_to='reactor/thumbnails/', null=True, blank=True)
    duration = models.IntegerField(default=0)  # в секундах

    # Связанные аниме
    anime_tags = models.ManyToManyField('anime.Anime', related_name='reactor_posts', blank=True)

    # Статистика
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)

    # Статус
    is_processing = models.BooleanField(default=True)  # Обрабатывается ли видео
    is_published = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_published', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    @property
    def video_url(self):
        """URL для доступа к видео"""
        if self.video_file:
            return self.video_file.url
        return None

    @property
    def thumbnail_url(self):
        """URL для доступа к превью"""
        if self.thumbnail_file:
            return self.thumbnail_file.url
        return None


class ReactorLike(models.Model):
    """Лайк на Reactor пост"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactor_likes')
    post = models.ForeignKey(ReactorPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class ReactorComment(models.Model):
    """Комментарий к Reactor посту"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactor_comments')
    post = models.ForeignKey(ReactorPost, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    @property
    def is_reply(self):
        return self.parent is not None
