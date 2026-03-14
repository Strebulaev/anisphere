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
from PIL import Image as PILImage
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
        """Возвращает URL постеров первых аниме для составной обложки"""
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
        """Генерирует вертикальную обложку из постеров аниме"""
        items = self.items.select_related('anime').order_by('position', 'added_at')[:3]
        if not items:
            return None
        
        # Собираем пути и URL постеров
        poster_data = []
        for item in items:
            if item.anime.poster and hasattr(item.anime.poster, 'path'):
                poster_data.append(('local', item.anime.poster.path))
            elif item.anime.poster_url:
                poster_data.append(('url', item.anime.poster_url))
        
        if not poster_data:
            return None

        return self._generate_cover(poster_data)

    def _generate_cover(self, poster_data):
        """
        Генерирует квадратную обложку с горизонтальным расположением постеров
        poster_data: список кортежей ('local'|'url', path_or_url)
        """
        import requests
        from io import BytesIO
        
        # Размеры обложки (квадратная)
        target_width = 300
        target_height = 300
        
        n = len(poster_data)
        # Ширина каждого изображения с учётом разделителей
        separator_width = 2
        total_separator = separator_width * (n - 1) if n > 1 else 0
        item_width = (target_width - total_separator) // n
        
        try:
            cover = PILImage.new('RGB', (target_width, target_height), color=(25, 25, 30))
            
            for i, (source_type, source) in enumerate(poster_data):
                try:
                    # Загружаем изображение
                    if source_type == 'local':
                        img = PILImage.open(source).convert('RGB')
                    else:
                        response = requests.get(source, timeout=10)
                        response.raise_for_status()
                        img = PILImage.open(BytesIO(response.content)).convert('RGB')
                    
                    # Обрезаем по центру и масштабируем
                    img = self._resize_and_crop(img, item_width, target_height)
                    
                    # Позиция по горизонтали
                    x_pos = i * (item_width + separator_width)
                    
                    # Вставляем изображение
                    cover.paste(img, (x_pos, 0))
                    
                    # Добавляем разделитель (кроме последнего)
                    if i < n - 1:
                        for x in range(x_pos + item_width, x_pos + item_width + separator_width):
                            for y in range(target_height):
                                cover.putpixel((x, y), (255, 255, 255))
                
                except Exception as e:
                    print(f"Error processing poster {i}: {e}")
                    # Заполняем место плейсхолдером
                    x_pos = i * (item_width + separator_width)
                    placeholder = PILImage.new('RGB', (item_width, target_height), color=(40, 40, 45))
                    cover.paste(placeholder, (x_pos, 0))
                    continue

            # Сохраняем
            filename = f"playlist_{self.id}_{int(self.updated_at.timestamp())}.jpg"
            filepath = f'playlist_covers/{filename}'
            full_path = default_storage.path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            cover.save(full_path, 'JPEG', quality=90)
            
            self.cover_image = filepath
            self.save(update_fields=['cover_image'])
            return self.cover_image.url
            
        except Exception as e:
            print(f"Error generating cover: {e}")
            return None

    def _resize_and_crop(self, img, target_width, target_height):
        """Масштабирует и обрезает изображение по центру до нужных размеров"""
        # Текущие размеры
        w, h = img.size
        
        # Вычисляем коэффициенты масштабирования
        width_ratio = target_width / w
        height_ratio = target_height / h
        
        # Берём больший коэффициент, чтобы изображение точно покрыло целевую область
        ratio = max(width_ratio, height_ratio)
        
        # Масштабируем
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
        
        # Обрезаем по центру
        left = (new_w - target_width) // 2
        top = (new_h - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img.crop((left, top, right, bottom))

    def update_cover(self):
        """Обновляет обложку плейлиста"""
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
