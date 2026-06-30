"""
Асинхронная нарезка клипов - новый модуль, не изменяет существующий код
"""
import subprocess
import tempfile
import os
import hashlib
from celery import shared_task
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Импортируем существующие функции из твоего views.py
# (они уже есть в твоём коде, просто импортируем их)
from anime.views import KodikClipDownloadView


def get_m3u8_url(anime, episode, season, translation_id, user_ip):
    """
    Использует существующие методы KodikClipDownloadView
    для получения m3u8 URL
    """
    # Создаём временный экземпляр класса
    clip_view = KodikClipDownloadView()
    
    # Используем существующие методы
    episode_url = clip_view._get_episode_player_url(
        anime, episode, season, translation_id
    )
    if not episode_url:
        return None
    
    m3u8_url = clip_view._get_m3u8_via_api(episode_url, user_ip)
    return m3u8_url


@shared_task(bind=True, max_retries=2)
def create_clip_async(self, anime_id, episode, season, translation_id, 
                      start_sec, end_sec, user_ip="1.1.1.1"):
    """
    Асинхронная нарезка клипа - работает в фоне
    """
    from anime.models import Anime
    
    duration = end_sec - start_sec
    if duration <= 0:
        raise ValueError("end должен быть больше start")
    
    # Уникальный ключ для кэша
    cache_key = f"clip:{anime_id}:{episode}:{season}:{translation_id}:{start_sec}:{end_sec}"
    
    # Проверяем, может уже есть в кэше?
    cached = cache.get(cache_key)
    if cached:
        return {"url": cached, "cached": True}
    
    try:
        anime = Anime.objects.get(pk=anime_id)
        
        # Получаем m3u8 URL используя существующую логику
        m3u8_url = get_m3u8_url(anime, episode, season, translation_id, user_ip)
        if not m3u8_url:
            raise Exception("Не удалось получить m3u8 URL")
        
        # Нарезаем видео во временный файл
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        cmd = [
            "/usr/bin/ffmpeg",
            "-y",
            "-ss", str(start_sec),
            "-i", m3u8_url,
            "-t", str(duration),
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_path
        ]
        
        logger.info(f"FFmpeg команда: {' '.join(cmd[:6])}...")
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {process.stderr[:200]}")
        
        # Сохраняем в медиа (можно в S3, но пока локально)
        filename = f"clips/{anime_id}/ep{episode}_{start_sec}_{end_sec}_{hashlib.md5(str(cache_key).encode()).hexdigest()[:8]}.mp4"
        
        # Создаём директорию если нужно
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'clips', str(anime_id)), exist_ok=True)
        
        # Перемещаем файл
        final_path = os.path.join(settings.MEDIA_ROOT, filename)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        os.rename(tmp_path, final_path)
        
        # URL для доступа
        url = f"{settings.MEDIA_URL}{filename}"
        
        # Кэшируем на 24 часа
        cache.set(cache_key, url, 86400)
        
        return {
            "url": url,
            "duration": duration,
            "anime_id": anime_id,
            "episode": episode,
            "cached": False
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timeout для anime {anime_id}")
        raise Exception("Нарезка видео заняла слишком много времени")
    except Exception as e:
        logger.exception(f"Clip task failed: {e}")
        raise self.retry(exc=e, countdown=60)