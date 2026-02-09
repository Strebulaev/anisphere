#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический импорт аниме через Shikimori Collector
Неинтерактивная версия для массового сбора данных
"""
import os
import sys
import django
import pandas as pd
import json
import time
import logging
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
import requests
from urllib.parse import urlencode

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_shikimori_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AutoShikimoriImporter:
    """Автоматический импортер аниме"""
    
    BASE_URL = "https://shikimori.one/api"
    
    def __init__(self, total_pages=200, skip_images=False):
        self.total_pages = total_pages
        self.skip_images = skip_images
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        })
        
        self.total_saved = 0
        self.total_updated = 0
        
        # Создаем директорию для постеров
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        logger.info(f"Initialized AutoShikimoriImporter: pages={total_pages}")
    
    def get_anime_page(self, page, limit=50):
        """Получает страницу аниме"""
        url = f"{self.BASE_URL}/animes"
        params = {
            'page': page,
            'limit': limit,
            'order': 'popularity',
            'status': 'released,ongoing,anons'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning(f"Rate limited on page {page}, waiting 30s...")
                time.sleep(30)
                return self.get_anime_page(page, limit)
            
            response.raise_for_status()
            time.sleep(0.5)
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return None
    
    def get_anime_details(self, anime_id):
        """Получает детали аниме"""
        try:
            url = f"{self.BASE_URL}/animes/{anime_id}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 429:
                time.sleep(30)
                return self.get_anime_details(anime_id)
            
            response.raise_for_status()
            time.sleep(0.3)
            
            return response.json()
            
        except Exception as e:
            logger.warning(f"Error fetching details for {anime_id}: {e}")
            return None
    
    def download_image(self, url, filename):
        """Скачивает изображение"""
        if self.skip_images or not url:
            return None
        
        try:
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://shikimori.one' + url
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = f'backend/media/anime_posters/{filename}'
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f'anime_posters/{filename}'
        except Exception as e:
            logger.warning(f"Failed to download image: {e}")
            return None
    
    def clean_filename(self, title):
        """Очищает название для файла"""
        import re
        if not title:
            return 'unknown'
        
        filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
    def save_anime_to_db(self, anime_data):
        """Сохраняет аниме в базу данных"""
        try:
            shikimori_id = anime_data.get('id')
            if not shikimori_id:
                return False
            
            # Названия
            title_ru = anime_data.get('russian') or anime_data.get('name')
            title_en = anime_data.get('english') or anime_data.get('name')
            title_jp = anime_data.get('japanese') or anime_data.get('name')
            
            if not title_ru:
                return False
            
            # Описание
            description = anime_data.get('description', '') or ''
            
            # Год
            year = None
            aired_on = anime_data.get('aired_on')
            if aired_on:
                try:
                    year = int(str(aired_on).split('-')[0])
                except:
                    pass
            
            # Статус
            status_map = {
                'released': 'finished',
                'ongoing': 'ongoing',
                'anons': 'announced'
            }
            status = status_map.get(anime_data.get('status'), 'finished')
            
            # Тип
            kind = anime_data.get('kind', 'tv')
            if kind not in ['tv', 'movie', 'ova', 'ona', 'special', 'music']:
                kind = 'tv'
            
            # Эпизоды
            episodes = anime_data.get('episodes')
            if episodes is not None:
                try:
                    episodes = int(episodes)
                except:
                    episodes = None
            
            # Рейтинг
            score = anime_data.get('score')
            if score is not None:
                try:
                    score = float(score)
                except:
                    score = None
            
            # Постер
            poster_url = ''
            image = anime_data.get('image', {})
            if image:
                poster_url = image.get('original') or image.get('preview') or ''
                if poster_url and not poster_url.startswith('http'):
                    poster_url = f"https://shikimori.one{poster_url}"
            
            # Жанры
            genres = []
            for genre in anime_data.get('genres', []):
                name = genre.get('russian') or genre.get('name')
                if name:
                    genres.append(name)
            
            # Студии
            studios = []
            for studio in anime_data.get('studios', []):
                name = studio.get('name')
                if name:
                    studios.append(name)
            
            # Проверяем существующую запись
            existing = Anime.objects.filter(shikimori_id=shikimori_id).first()
            
            # Скачиваем постер
            poster_file = None
            if not self.skip_images and poster_url:
                filename = self.clean_filename(title_ru)
                filename = f"{filename}_{shikimori_id}.jpg"
                poster_file = self.download_image(poster_url, filename)
            
            if existing:
                # Обновляем существующую запись
                updated = False
                
                if not existing.description and description:
                    existing.description = description
                    updated = True
                
                if not existing.year and year:
                    existing.year = year
                    updated = True
                
                if not existing.episodes and episodes:
                    existing.episodes = episodes
                    updated = True
                
                if not existing.score and score:
                    existing.score = score
                    updated = True
                
                if not existing.genres and genres:
                    existing.genres = genres
                    updated = True
                
                if not existing.studios and studios:
                    existing.studios = studios
                    updated = True
                
                if poster_file and not existing.poster:
                    existing.poster = poster_file
                    updated = True
                
                if existing.poster_url != poster_url and poster_url:
                    existing.poster_url = poster_url
                    updated = True
                
                if updated:
                    existing.save()
                    self.total_updated += 1
                    return True
                return False
            else:
                # Создаем новую запись
                anime = Anime.objects.create(
                    shikimori_id=shikimori_id,
                    title_ru=title_ru[:255],
                    title_en=title_en[:255] if title_en else '',
                    title_jp=title_jp[:255] if title_jp else '',
                    description=description[:5000] if description else '',
                    year=year,
                    status=status,
                    kind=kind,
                    episodes=episodes,
                    score=score,
                    poster_url=poster_url,
                    poster=poster_file,
                    genres=genres[:10],
                    studios=studios[:5],
                    data_source='shikimori'
                )
                self.total_saved += 1
                return True
                
        except Exception as e:
            logger.error(f"Error saving anime: {e}")
            return False
    
    def run_import(self):
        """Запускает импорт"""
        logger.info("=" * 80)
        logger.info("AUTO SHIKIMORI ANIME IMPORT")
        logger.info("=" * 80)
        logger.info(f"Pages: {self.total_pages}")
        logger.info(f"Images: {'Yes' if not self.skip_images else 'No'}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        for page in range(1, self.total_pages + 1):
            logger.info(f"\nFetching page {page}/{self.total_pages}...")
            
            # Получаем список аниме
            anime_list = self.get_anime_page(page)
            
            if not anime_list:
                logger.warning(f"No data on page {page}, stopping")
                break
            
            logger.info(f"Found {len(anime_list)} anime")
            
            # Получаем детали и сохраняем
            for i, anime_data in enumerate(anime_list):
                shikimori_id = anime_data.get('id')
                if not shikimori_id:
                    continue
                
                # Получаем детали
                details = self.get_anime_details(shikimori_id)
                if details:
                    self.save_anime_to_db(details)
                
                # Показываем прогресс
                if (i + 1) % 10 == 0:
                    logger.info(f"  Processed {i + 1}/{len(anime_list)} on page {page}")
            
            logger.info(f"Page {page} completed. Total saved: {self.total_saved}, updated: {self.total_updated}")
            
            # Пауза между страницами
            if page < self.total_pages:
                time.sleep(2)
        
        # Статистика
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        logger.info("\n" + "=" * 80)
        logger.info("IMPORT COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"\nStatistics:")
        logger.info(f"  Total in database: {Anime.objects.count():,}")
        logger.info(f"  Newly saved: {self.total_saved:,}")
        logger.info(f"  Updated: {self.total_updated:,}")
        logger.info(f"  Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Статистика по статусам
        logger.info("\nBy status:")
        for status in ['ongoing', 'finished', 'announced']:
            count = Anime.objects.filter(status=status).count()
            logger.info(f"  {status}: {count}")
        
        # Статистика по типам
        logger.info("\nBy kind:")
        for kind in ['tv', 'movie', 'ova', 'ona']:
            count = Anime.objects.filter(kind=kind).count()
            logger.info(f"  {kind}: {count}")
        
        logger.info("\n" + "=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Shikimori anime importer')
    parser.add_argument('--pages', type=int, default=200,
                       help='Number of pages to import (default: 200)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
    
    args = parser.parse_args()
    
    try:
        importer = AutoShikimoriImporter(
            total_pages=args.pages,
            skip_images=args.skip_images
        )
        importer.run_import()
    except KeyboardInterrupt:
        logger.info("\n\nImport interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
