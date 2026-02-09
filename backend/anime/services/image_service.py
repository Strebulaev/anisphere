"""Сервис для загрузки и управления изображениями аниме"""
import os
import requests
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class ImageService:
    """Сервис для загрузки и обработки изображений"""
    
    def __init__(self):
        self.media_root = settings.MEDIA_ROOT
        self.poster_dir = 'anime_posters'
        self.max_size = (400, 600)  # Максимальный размер постера
        self.quality = 85  # Качество JPEG
        
    def download_poster(self, image_url: str, anime_id: int, title: str) -> str:
        """Загрузка постера аниме"""
        if not image_url:
            logger.warning(f"Пустой URL изображения для аниме {title}")
            return None
            
        try:
            # Загружаем изображение
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Проверяем, что это изображение
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"Неизвестный тип контента: {content_type} для {image_url}")
                return None
            
            # Получаем изображение
            image_content = response.content
            
            # Обрабатываем изображение
            processed_image = self._process_image(image_content)
            
            if not processed_image:
                logger.warning(f"Не удалось обработать изображение для {title}")
                return None
            
            # Создаем имя файла
            filename = self._generate_filename(anime_id, title, response.headers.get('content-type'))
            
            # Сохраняем файл
            file_path = os.path.join(self.poster_dir, filename)
            
            # Используем Django storage для сохранения
            default_storage.save(file_path, ContentFile(processed_image))
            
            logger.info(f"Постер загружен для {title}: {file_path}")
            return file_path
            
        except requests.RequestException as e:
            logger.error(f"Ошибка загрузки изображения {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка загрузки изображения для {title}: {e}")
            return None
    
    def _process_image(self, image_content: bytes) -> bytes:
        """Обработка изображения"""
        try:
            # Открываем изображение
            image = Image.open(BytesIO(image_content))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Изменяем размер с соотношением сторон
            image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем как JPEG
            output = BytesIO()
            image.save(output, format='JPEG', quality=self.quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            return None
    
    def _generate_filename(self, anime_id: int, title: str, content_type: str) -> str:
        """Генерация имени файла"""
        # Очищаем название от недопустимых символов
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Ограничиваем длину
        
        # Определяем расширение
        if 'png' in content_type.lower():
            ext = 'png'
        elif 'webp' in content_type.lower():
            ext = 'webp'
        else:
            ext = 'jpg'
        
        return f"anime_{anime_id}_{safe_title}.{ext}"
    
    def download_poster_safe(self, image_url: str, anime_id: int, title: str) -> str:
        """Безопасная загрузка постера с обработкой ошибок"""
        try:
            if not image_url:
                return None
            
            # Пропускаем локальные файлы
            if image_url.startswith('/media/') or image_url.startswith('/static/'):
                return None
            
            return self.download_poster(image_url, anime_id, title)
            
        except Exception as e:
            logger.error(f"Ошибка безопасной загрузки постера для {title}: {e}")
            return None
    
    def cleanup_old_poster(self, old_poster_path: str):
        """Удаление старого постера"""
        if old_poster_path:
            try:
                if default_storage.exists(old_poster_path):
                    default_storage.delete(old_poster_path)
                    logger.info(f"Удален старый постер: {old_poster_path}")
            except Exception as e:
                logger.error(f"Ошибка удаления постера {old_poster_path}: {e}")
    
    def get_poster_url(self, poster_path: str) -> str:
        """Получение URL постера"""
        if poster_path:
            if poster_path.startswith('/'):
                return poster_path
            return f"/media/{poster_path}"
        return None