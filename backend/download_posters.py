#!/usr/bin/env python3
"""
Скрипт для скачивания постеров аниме с shikimori.one через прокси.
Использует images.weserv.nl как прокси-сервис для обхода блокировок.
"""

import os
import sys
import django
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from anime.models import Anime


def download_poster(anime_id: int, poster_url: str, save_dir: Path) -> str | None:
    """
    Скачивает постер через прокси-сервис.
    Возвращает путь к сохраненному файлу или None при ошибке.
    """
    if not poster_url or not poster_url.startswith('http'):
        return None
    
    try:
        # Используем images.weserv.nl как прокси
        from urllib.parse import quote, urlparse
        
        # Кодируем оригинальный URL - PNG без потерь
        encoded_url = quote(poster_url, safe='')
        proxy_url = f'https://images.weserv.nl/?url={encoded_url}&w=1200&output=png'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/*,*/*;q=0.8',
        }
        
        response = requests.get(proxy_url, headers=headers, timeout=30, stream=True)
        
        if response.status_code != 200:
            # Пробуем напрямую если прокси не работает
            response = requests.get(poster_url, headers=headers, timeout=30, stream=True)
        
        if response.status_code != 200:
            print(f'  [ERROR] HTTP {response.status_code} for {anime_id}')
            return None
        
        # Расширение - PNG
        ext = 'png'
        
        # Сохраняем файл
        filename = f'poster_{anime_id}.{ext}'
        filepath = save_dir / filename
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return str(filepath.relative_to(save_dir.parent))
        
    except requests.exceptions.Timeout:
        print(f'  [TIMEOUT] {anime_id}')
        return None
    except Exception as e:
        print(f'  [ERROR] {anime_id}: {str(e)[:50]}')
        return None


def process_anime(anime: Anime, save_dir: Path) -> tuple:
    """Обрабатывает одно аниме."""
    if not anime.poster_url:
        return anime.id, None, 'no_url'
    
    # Пропускаем если уже есть локальный постер
    if anime.poster:
        return anime.id, anime.poster, 'already_exists'
    
    filepath = download_poster(anime.id, anime.poster_url, save_dir)
    
    if filepath:
        return anime.id, filepath, 'success'
    else:
        return anime.id, None, 'failed'


def main():
    print('=' * 60)
    print('Скрипт загрузки постеров аниме')
    print('=' * 60)
    
    # Папка для сохранения
    media_root = Path(__file__).parent / 'media'
    posters_dir = media_root / 'posters'
    posters_dir.mkdir(parents=True, exist_ok=True)
    
    print(f'\nПапка для постеров: {posters_dir}')
    
    # Получаем аниме без локальных постеров (poster='')
    anime_list = Anime.objects.filter(
        poster_url__isnull=False
    ).exclude(
        poster_url=''
    ).filter(
        poster=''
    )  # Без лимита - всё аниме
    
    total = anime_list.count()
    print(f'Аниме для загрузки: {total}')
    
    if total == 0:
        print('Все постеры уже загружены!')
        return
    
    # Загружаем с прогресс-баром
    print('\nЗагрузка постеров...')
    
    success = 0
    failed = 0
    already = 0
    
    for anime in tqdm(anime_list, desc='Загрузка'):
        anime_id, filepath, status = process_anime(anime, posters_dir)
        
        if status == 'success':
            # Обновляем запись в базе
            Anime.objects.filter(id=anime_id).update(poster=filepath)
            success += 1
        elif status == 'already_exists':
            already += 1
        else:
            failed += 1
        
        # Небольшая задержка чтобы не спамить сервер
        time.sleep(0.2)
    
    print(f'\n{'=' * 60}')
    print(f'Результат:')
    print(f'  Успешно: {success}')
    print(f'  Уже есть: {already}')
    print(f'  Ошибки: {failed}')
    print(f'{'=' * 60}')


if __name__ == '__main__':
    main()
