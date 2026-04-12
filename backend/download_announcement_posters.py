#!/usr/bin/env python3
"""
Скрипт скачивания постеров для анонсов.
Использует тот же метод что и download_all_posters.py (прямой запрос с VPN).
Сохраняет в папку anime_posters как обычные аниме.
"""

import os
import sys
import logging
import hashlib
import requests
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import models

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================
MEDIA_ROOT = Path("media")
POSTERS_DIR = MEDIA_ROOT / "anime_posters"
TIMEOUT = 30


def generate_filename(url: str, anime_id: int) -> str:
    """Генерирует уникальное имя файла."""
    ext = ".jpg"
    if url.endswith(".png"):
        ext = ".png"
    elif url.endswith(".webp"):
        ext = ".webp"
    
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{anime_id}_{url_hash}{ext}"


def download_poster(session: requests.Session, url: str, save_path: Path) -> bool:
    """Скачивает один постер."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/*,*/*;q=0.8',
        }
        
        response = session.get(url, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            logger.warning(f"  Код {response.status_code}: {url[:50]}...")
            return False
            
    except requests.exceptions.Timeout:
        logger.warning(f"  Таймаут: {url[:50]}...")
        return False
    except Exception as e:
        logger.warning(f"  Ошибка: {type(e).__name__} - {url[:50]}...")
        return False


def main():
    """Главная функция."""
    from anime.models import Anime
    
    logger.info("=" * 60)
    logger.info("СКАЧИВАНИЕ ПОСТЕРОВ ДЛЯ АНОНСОВ")
    logger.info("=" * 60)
    logger.info(f"Папка для сохранения: {POSTERS_DIR}")
    
    # Создаём директории
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Создаём сессию
    session = requests.Session()
    
    # Находим анонсы с poster_url но без local poster
    # Ищем где poster пустой или NULL
    announcements = Anime.objects.filter(
        status__in=['announced', 'released'],
        poster_url__isnull=False
    ).exclude(
        poster_url=""
    ).filter(
        models.Q(poster="") | models.Q(poster__isnull=True)
    )
    
    total = announcements.count()
    logger.info(f"Найдено анонсов для обработки: {total}")
    
    if total == 0:
        logger.info("Нет анонсов для обработки!")
        return
    
    success_count = 0
    fail_count = 0
    
    for anime in announcements:
        url = anime.poster_url
        if not url:
            continue
            
        filename = generate_filename(url, anime.id)
        save_path = POSTERS_DIR / filename
        
        logger.info(f"[{anime.id}] {anime.title_ru or anime.title_en or 'N/A'[:40]}...")
        logger.info(f"  URL: {url[:60]}...")
        
        if download_poster(session, url, save_path):
            # Обновляем запись в БД - в ту же папку что и обычные аниме
            anime.poster = f"anime_posters/{filename}"
            anime.save(update_fields=['poster'])
            logger.info(f"  ✓ Сохранён: {filename}")
            success_count += 1
        else:
            fail_count += 1
        
        # Пауза чтобы не спамить сервер
        import time
        time.sleep(0.3)
    
    # Итоги
    logger.info("=" * 60)
    logger.info("ИТОГИ")
    logger.info("=" * 60)
    logger.info(f"  Успешно: {success_count}")
    logger.info(f"  Ошибки:  {fail_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
