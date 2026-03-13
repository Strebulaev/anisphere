from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
from PIL import Image
import os
import uuid
import secrets
from datetime import timedelta

User = get_user_model()


VISIBILITY_PUBLIC = 'public'
VISIBILITY_PRIVATE = 'private'
VISIBILITY_LINK = 'link'

VISIBILITY_CHOICES = [
    (VISIBILITY_PUBLIC, 'Публичный'),
    (VISIBILITY_PRIVATE, 'Приватный'),
    (VISIBILITY_LINK, 'По ссылке'),
]


class Playlist(models.Model):
    """Модель плейлиста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')

    # Основная информация
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Обложка
    cover_image = models.ImageField(
        upload_to='playlist_covers/',
        null=True,
        blank=True,
        verbose_name='Обложка'
    )

    # Видимость: public / private / link
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        verbose_name='Видимость'
    )

    # Обратная совместимость — вычисляемое свойство
    @property
    def is_public(self):
        return self.visibility == VISIBILITY_PUBLIC

    @is_public.setter
    def is_public(self, value):
        if value:
            self.visibility = VISIBILITY_PUBLIC
        else:
            # При записи False переводим в private если не link
            if self.visibility == VISIBILITY_PUBLIC:
                self.visibility = VISIBILITY_PRIVATE

    @property
    def is_private(self):
        return self.visibility == VISIBILITY_PRIVATE

    @property
    def is_link_only(self):
        return self.visibility == VISIBILITY_LINK

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    @property
    def items_count(self):
        return self.items.count()

    @property
    def favorites_count(self):
        return self.favorited_by.count()

    def get_cover_urls(self):
        """Возвращает URL постеров первых 3 аниме для составной обложки"""
        items = self.items.select_related('anime').order_by('position', 'added_at')[:3]
        urls = []
        for item in items:
            if item.anime.poster and hasattr(item.anime.poster, 'url'):
                poster_url = item.anime.poster.url
                if poster_url.startswith('/media/media/'):
                    poster_url = poster_url.replace('/media/media/', '/media/')
                urls.append(poster_url)
            elif item.anime.poster_url:
                urls.append(item.anime.poster_url)
        return urls

    def generate_cover_image(self):
        items = self.items.select_related('anime').order_by('position', 'added_at')[:3]
        if not items:
            return None
        poster_paths = []
        poster_urls = []
        for item in items:
            if item.anime.poster and hasattr(item.anime.poster, 'path'):
                poster_paths.append(item.anime.poster.path)
            elif item.anime.poster_url:
                poster_urls.append(item.anime.poster_url)
        if poster_paths:
            return self._generate_from_local_files(poster_paths)
        elif poster_urls:
            return self._generate_from_urls(poster_urls)
        return None

    def _generate_from_local_files(self, poster_paths):
        from PIL import Image as PILImage
        target_width = 300
        target_height = 420
        n = len(poster_paths)
        item_height = target_height // n
        sep = 1  # тонкий белый разделитель

        try:
            cover = PILImage.new('RGB', (target_width, target_height), color=(30, 30, 30))
            for i, poster_path in enumerate(poster_paths):
                try:
                    img = PILImage.open(poster_path).convert('RGB')
                    img = img.resize((target_width, item_height), PILImage.Resampling.LANCZOS)
                    y_pos = i * item_height
                    cover.paste(img, (0, y_pos))
                    # Белый разделитель между постерами
                    if i < n - 1:
                        for y in range(y_pos + item_height - sep, y_pos + item_height):
                            for x in range(target_width):
                                cover.putpixel((x, y), (255, 255, 255))
                except Exception as e:
                    print(f"Error processing poster {i}: {e}")
                    continue

            filename = f"playlist_{self.id}_{int(self.updated_at.timestamp())}.jpg"
            filepath = f'playlist_covers/{filename}'
            full_path = default_storage.path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            cover.save(full_path, 'JPEG', quality=85)
            self.cover_image = filepath
            self.save(update_fields=['cover_image'])
            return self.cover_image.url
        except Exception as e:
            print(f"Error generating cover from local files: {e}")
            return None

    def _generate_from_urls(self, poster_urls):
        from PIL import Image as PILImage
        import requests
        from io import BytesIO
        target_width = 300
        target_height = 420
        n = len(poster_urls)
        item_height = target_height // n
        sep = 1

        try:
            cover = PILImage.new('RGB', (target_width, target_height), color=(30, 30, 30))
            for i, url in enumerate(poster_urls):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    img = PILImage.open(BytesIO(response.content)).convert('RGB')
                    img = img.resize((target_width, item_height), PILImage.Resampling.LANCZOS)
                    y_pos = i * item_height
                    cover.paste(img, (0, y_pos))
                    if i < n - 1:
                        for y in range(y_pos + item_height - sep, y_pos + item_height):
                            for x in range(target_width):
                                cover.putpixel((x, y), (255, 255, 255))
                except Exception as e:
                    print(f"Error processing URL {i}: {e}")
                    continue

            filename = f"playlist_{self.id}_{int(self.updated_at.timestamp())}.jpg"
            filepath = f'playlist_covers/{filename}'
            full_path = default_storage.path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            cover.save(full_path, 'JPEG', quality=85)
            self.cover_image = filepath
            self.save(update_fields=['cover_image'])
            return self.cover_image.url
        except Exception as e:
            print(f"Error generating cover from URLs: {e}")
            return None

    def update_cover(self):
        if self.cover_image:
            try:
                default_storage.delete(self.cover_image.name)
            except:
                pass
        return self.generate_cover_image()

    def get_active_share_link(self):
        """Возвращает актуальную share-ссылку или None"""
        link = self.share_links.filter(
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).first()
        return link

    def get_or_create_share_link(self, ttl_days=30):
        """Возвращает действующую ссылку или создаёт новую"""
        link = self.get_active_share_link()
        if link:
            return link
        token = secrets.token_urlsafe(32)
        link = PlaylistShareLink.objects.create(
            playlist=self,
            token=token,
            expires_at=timezone.now() + timedelta(days=ttl_days),
        )
        return link

    def invalidate_share_links(self):
        """Деактивирует все share-ссылки плейлиста"""
        self.share_links.update(is_active=False)


class PlaylistShareLink(models.Model):
    """Одноразовая/временная share-ссылка на плейлист по токену"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='share_links')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    is_active = models.BooleanField(default=True)
    # Счётчик переходов по ссылке
    access_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Share-ссылка плейлиста'
        verbose_name_plural = 'Share-ссылки плейлистов'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.playlist.title} / {self.token[:12]}..."

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def touch(self):
        """Фиксирует переход по ссылке"""
        self.access_count += 1
        self.save(update_fields=['access_count'])


class PlaylistItem(models.Model):
    """Элемент плейлиста"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE)

    position = models.PositiveIntegerField(default=0, verbose_name='Позиция')
    notes = models.TextField(blank=True, verbose_name='Заметки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        ordering = ['position', 'added_at']
        verbose_name = 'Элемент плейлиста'
        verbose_name_plural = 'Элементы плейлиста'
        unique_together = ['playlist', 'anime']

    def __str__(self):
        return f"{self.playlist.title}: {self.anime.title_ru}"

    def save(self, *args, **kwargs):
        if self.position == 0:
            max_position = PlaylistItem.objects.filter(
                playlist=self.playlist
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        super().save(*args, **kwargs)
        self.playlist.update_cover()


class FavoritePlaylist(models.Model):
    """Избранные плейлисты"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_playlists')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ['user', 'playlist']
        verbose_name = 'Избранный плейлист'
        verbose_name_plural = 'Избранные плейлисты'

    def __str__(self):
        return f"{self.user.username} - {self.playlist.title}"


class FavoriteAnime(models.Model):
    """Избранные аниме"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_anime')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ['user', 'anime']
        verbose_name = 'Избранное аниме'
        verbose_name_plural = 'Избранные аниме'

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru}"
