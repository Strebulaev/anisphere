from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
import os

User = get_user_model()


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
    
    # Настройки приватности
    is_public = models.BooleanField(default=True, verbose_name='Публичный')
    
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
        """Количество аниме в плейлисте"""
        return self.items.count()

    @property
    def favorites_count(self):
        """Количество пользователей, добавивших плейлист в избранное"""
        return self.favorited_by.count()

    @property
    def is_favorited_by_user(self, user):
        """Добавлен ли плейлист в избранное пользователем"""
        if user.is_authenticated:
            return self.favorited_by.filter(user=user).exists()
        return False

    def get_cover_urls(self):
        """Возвращает URL постеров первых 3 аниме для составной обложки"""
        items = self.items.select_related('anime').order_by('position', 'added_at')[:3]
        urls = []
        for item in items:
            if item.anime.poster and hasattr(item.anime.poster, 'url'):
                poster_url = item.anime.poster.url
                # Убираем дублирование /media/
                if poster_url.startswith('/media/media/'):
                    poster_url = poster_url.replace('/media/media/', '/media/')
                urls.append(poster_url)
            elif item.anime.poster_url:
                urls.append(item.anime.poster_url)
        return urls

    def generate_cover_image(self):
        """Генерирует составную обложку из постеров первых 3 аниме"""
        items = self.items.select_related('anime').order_by('position', 'added_at')[:3]

        if not items:
            return None

        # Получаем пути к постерам или URL
        poster_paths = []
        poster_urls = []
        for item in items:
            if item.anime.poster and hasattr(item.anime.poster, 'path'):
                poster_paths.append(item.anime.poster.path)
            elif item.anime.poster_url:
                poster_urls.append(item.anime.poster_url)

        # Если есть локальные файлы, используем их
        if poster_paths:
            return self._generate_from_local_files(poster_paths)
        # Если есть URL, скачиваем и используем их
        elif poster_urls:
            return self._generate_from_urls(poster_urls)

        return None

    def _generate_from_local_files(self, poster_paths):
        """Генерирует обложку из локальных файлов"""
        from PIL import Image as PILImage

        # Размеры
        target_width = 600
        target_height = 400
        item_width = target_width // len(poster_paths)

        try:
            # Создаем составное изображение
            cover = PILImage.new('RGB', (target_width, target_height), color=(30, 30, 30))

            for i, poster_path in enumerate(poster_paths):
                try:
                    # Открываем постер
                    img = PILImage.open(poster_path)

                    # Изменяем размер с сохранением пропорций
                    img_ratio = img.width / img.height
                    new_height = int(item_width / img_ratio)

                    if new_height > target_height:
                        new_height = target_height
                        item_width = int(new_height * img_ratio)

                    img = img.resize((item_width, new_height), PILImage.Resampling.LANCZOS)

                    # Позиционирование (по центру по вертикали)
                    y_pos = (target_height - new_height) // 2
                    x_pos = i * (target_width // len(poster_paths))

                    # Вставляем изображение
                    cover.paste(img, (x_pos, y_pos))

                except Exception as e:
                    print(f"Error processing poster {i}: {e}")
                    continue

            # Сохраняем обложку
            filename = f"playlist_{self.id}_{int(self.updated_at.timestamp())}.jpg"
            filepath = f'playlist_covers/{filename}'

            # Создаем директорию если нужно
            full_path = default_storage.path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            cover.save(full_path, 'JPEG', quality=85)

            # Обновляем модель
            self.cover_image = filepath
            self.save(update_fields=['cover_image'])

            return self.cover_image.url

        except Exception as e:
            print(f"Error generating cover from local files: {e}")
            return None

    def _generate_from_urls(self, poster_urls):
        """Генерирует обложку из URL"""
        from PIL import Image as PILImage
        import requests
        from io import BytesIO

        # Размеры
        target_width = 600
        target_height = 400
        item_width = target_width // len(poster_urls)

        try:
            # Создаем составное изображение
            cover = PILImage.new('RGB', (target_width, target_height), color=(30, 30, 30))

            for i, url in enumerate(poster_urls):
                try:
                    # Скачиваем изображение
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    img = PILImage.open(BytesIO(response.content))

                    # Изменяем размер с сохранением пропорций
                    img_ratio = img.width / img.height
                    new_height = int(item_width / img_ratio)

                    if new_height > target_height:
                        new_height = target_height
                        item_width = int(new_height * img_ratio)

                    img = img.resize((item_width, new_height), PILImage.Resampling.LANCZOS)

                    # Позиционирование (по центру по вертикали)
                    y_pos = (target_height - new_height) // 2
                    x_pos = i * (target_width // len(poster_urls))

                    # Вставляем изображение
                    cover.paste(img, (x_pos, y_pos))

                except Exception as e:
                    print(f"Error processing URL {i}: {e}")
                    continue

            # Сохраняем обложку
            filename = f"playlist_{self.id}_{int(self.updated_at.timestamp())}.jpg"
            filepath = f'playlist_covers/{filename}'

            # Создаем директорию если нужно
            full_path = default_storage.path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            cover.save(full_path, 'JPEG', quality=85)

            # Обновляем модель
            self.cover_image = filepath
            self.save(update_fields=['cover_image'])

            return self.cover_image.url

        except Exception as e:
            print(f"Error generating cover from URLs: {e}")
            return None

    def update_cover(self):
        """Обновляет обложку плейлиста"""
        # Удаляем старую обложку если есть
        if self.cover_image:
            try:
                default_storage.delete(self.cover_image.name)
            except:
                pass

        # Генерируем новую
        return self.generate_cover_image()


class PlaylistItem(models.Model):
    """Элемент плейлиста"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE)
    
    # Позиция для сортировки
    position = models.PositiveIntegerField(default=0, verbose_name='Позиция')
    
    # Дополнительная информация
    notes = models.TextField(blank=True, verbose_name='Заметки')
    
    # Метаданные
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
        # Автоматически назначаем позицию если не задана
        if self.position == 0:
            max_position = PlaylistItem.objects.filter(
                playlist=self.playlist
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        
        super().save(*args, **kwargs)
        
        # Обновляем обложку плейлиста
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