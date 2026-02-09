#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный импорт аниме через Shikimori API с множественными фильтрами
Максимально заполняет базу данных реальными аниме
"""
import os
import sys
import django
import requests
import time
import re
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shikimori_extended_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ShikimoriExtendedImporter:
    """Расширенный импортер с множественными фильтрами"""
    
    BASE_URL = "https://shikimori.one/api"
    
    def __init__(self, max_anime=20000, skip_images=False, fast_mode=False, max_workers=5):
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        self.max_workers = max_workers
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        self.total_saved = 0
        self.total_updated = 0
        self.total_failed = 0
        self.processed_ids = set()
        self.seen_urls = set()
        
        # Создаем директорию для постеров
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        logger.info(f"Initialized ShikimoriExtendedImporter: max_anime={max_anime}")
    
    def make_request(self, endpoint, params=None, max_retries=3):
        """Выполняет запрос к API с повторными попытками"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                if not self.fast_mode:
                    time.sleep(0.2)
                else:
                    time.sleep(0.05)
                
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(3)
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
        
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
            return None
    
    def clean_filename(self, title):
        """Очищает название для файла"""
        if not title:
            return 'unknown'
        
        filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
    def normalize_anime_data(self, anime_data):
        """Нормализует данные аниме"""
        try:
            shikimori_id = anime_data.get('id')
            if not shikimori_id:
                return None
            
            title_ru = anime_data.get('russian') or anime_data.get('name')
            title_en = anime_data.get('english') or anime_data.get('name')
            title_jp = anime_data.get('japanese') or anime_data.get('name')
            
            if not title_ru:
                return None
            
            description = anime_data.get('description', '')
            
            year = None
            aired_on = anime_data.get('aired_on')
            if aired_on:
                try:
                    year = int(str(aired_on).split('-')[0])
                except:
                    pass
            
            status_map = {
                'released': 'finished',
                'ongoing': 'ongoing',
                'anons': 'announced'
            }
            status = status_map.get(anime_data.get('status'), 'finished')
            
            kind = anime_data.get('kind', 'tv')
            if kind not in ['tv', 'movie', 'ova', 'ona', 'special', 'music']:
                kind = 'tv'
            
            episodes = anime_data.get('episodes')
            if episodes is not None:
                try:
                    episodes = int(episodes)
                except:
                    episodes = None
            
            score = anime_data.get('score')
            if score is not None:
                try:
                    score = float(score)
                except:
                    score = None
            
            poster_url = ''
            image = anime_data.get('image', {})
            if image:
                poster_url = image.get('original') or image.get('preview') or ''
                if poster_url and not poster_url.startswith('http'):
                    poster_url = f"https://shikimori.one{poster_url}"
            
            genres = []
            for genre in anime_data.get('genres', []):
                name = genre.get('russian') or genre.get('name')
                if name:
                    genres.append(name)
            
            studios = []
            for studio in anime_data.get('studios', []):
                name = studio.get('name')
                if name:
                    studios.append(name)
            
            return {
                'shikimori_id': shikimori_id,
                'title_ru': title_ru[:255],
                'title_en': title_en[:255] if title_en else '',
                'title_jp': title_jp[:255] if title_jp else '',
                'description': description[:5000] if description else '',
                'year': year,
                'status': status,
                'kind': kind,
                'episodes': episodes,
                'score': score,
                'poster_url': poster_url,
                'genres': genres[:10],
                'studios': studios[:5],
                'data_source': 'shikimori'
            }
            
        except Exception as e:
            return None
    
    def save_anime(self, anime_data):
        """Сохраняет или обновляет аниме"""
        try:
            shikimori_id = anime_data.get('shikimori_id')
            
            existing = Anime.objects.filter(shikimori_id=shikimori_id).first()
            
            poster_file = None
            poster_url = anime_data.get('poster_url')
            
            if not self.skip_images and poster_url:
                filename = self.clean_filename(anime_data['title_ru'])
                filename = f"{filename}_{shikimori_id}.jpg"
                poster_file = self.download_image(poster_url, filename)
            
            if existing:
                updated = False
                
                if not existing.description and anime_data['description']:
                    existing.description = anime_data['description']
                    updated = True
                
                if not existing.year and anime_data['year']:
                    existing.year = anime_data['year']
                    updated = True
                
                if not existing.episodes and anime_data['episodes']:
                    existing.episodes = anime_data['episodes']
                    updated = True
                
                if not existing.score and anime_data['score']:
                    existing.score = anime_data['score']
                    updated = True
                
                if not existing.genres and anime_data['genres']:
                    existing.genres = anime_data['genres']
                    updated = True
                
                if not existing.studios and anime_data['studios']:
                    existing.studios = anime_data['studios']
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
                anime = Anime.objects.create(
                    shikimori_id=anime_data['shikimori_id'],
                    title_ru=anime_data['title_ru'],
                    title_en=anime_data['title_en'],
                    title_jp=anime_data['title_jp'],
                    description=anime_data['description'],
                    year=anime_data['year'],
                    status=anime_data['status'],
                    kind=anime_data['kind'],
                    episodes=anime_data['episodes'],
                    score=anime_data['score'],
                    poster_url=anime_data['poster_url'],
                    poster=poster_file,
                    genres=anime_data['genres'],
                    studios=anime_data['studios'],
                    data_source=anime_data['data_source']
                )
                self.total_saved += 1
                return True
                
        except Exception as e:
            self.total_failed += 1
            return False
    
    def get_anime_with_filters(self, filters, page=1, limit=50):
        """Получает аниме с фильтрами"""
        params = {
            'page': page,
            'limit': limit,
            'order': 'popularity'
        }
        params.update(filters)
        
        return self.make_request('animes', params)
    
    def import_by_filters(self, filters_list):
        """Импортирует аниме используя список фильтров"""
        total_imported = 0
        
        for filters in filters_list:
            if total_imported >= self.max_anime:
                break
            
            filter_name = filters.get('name', 'Unknown')
            logger.info(f"\nImporting with filter: {filter_name}")
            
            page = 1
            limit = 50
            
            while total_imported < self.max_anime:
                if page > 10:  # Ограничиваем страницы для каждого фильтра
                    break
                
                logger.info(f"  Page {page}...")
                
                # Удаляем имя фильтра из параметров
                params = {k: v for k, v in filters.items() if k != 'name'}
                anime_list = self.get_anime_with_filters(params, page=page, limit=limit)
                
                if not anime_list:
                    break
                
                new_count = 0
                for anime_data in anime_list:
                    shikimori_id = anime_data.get('id')
                    if not shikimori_id or shikimori_id in self.processed_ids:
                        continue
                    
                    normalized = self.normalize_anime_data(anime_data)
                    if normalized:
                        if self.save_anime(normalized):
                            new_count += 1
                            total_imported += 1
                            self.processed_ids.add(shikimori_id)
                            
                            if total_imported % 50 == 0:
                                logger.info(f"    Progress: {total_imported}/{self.max_anime}")
                
                logger.info(f"  Imported {new_count} anime (total: {total_imported})")
                
                if len(anime_list) < limit:
                    break
                
                page += 1
                
                if not self.fast_mode:
                    time.sleep(1)
        
        return total_imported
    
    def run_import(self):
        """Запускает расширенный импорт"""
        logger.info("=" * 80)
        logger.info("SHIKIMORI EXTENDED ANIME IMPORT")
        logger.info("=" * 80)
        logger.info(f"Target: {self.max_anime} anime")
        logger.info(f"Images: {'Yes' if not self.skip_images else 'No'}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Список фильтров для максимального охвата
        filters_list = [
            # По статусам
            {'name': 'Released anime', 'status': 'released'},
            {'name': 'Ongoing anime', 'status': 'ongoing'},
            {'name': 'Anons anime', 'status': 'anons'},
            
            # По типам
            {'name': 'TV Series', 'kind': 'tv'},
            {'name': 'Movies', 'kind': 'movie'},
            {'name': 'OVA', 'kind': 'ova'},
            {'name': 'ONA', 'kind': 'ona'},
            
            # По рейтингу
            {'name': 'Rated G', 'rating': 'g'},
            {'name': 'Rated PG', 'rating': 'pg'},
            {'name': 'Rated PG-13', 'rating': 'pg_13'},
            {'name': 'Rated R', 'rating': 'r'},
            {'name': 'Rated R+', 'rating': 'r_plus'},
            
            # По жанрам (популярные)
            {'name': 'Action', 'genre': '1'},
            {'name': 'Adventure', 'genre': '2'},
            {'name': 'Comedy', 'genre': '4'},
            {'name': 'Drama', 'genre': '8'},
            {'name': 'Fantasy', 'genre': '10'},
            {'name': 'Magic', 'genre': '11'},
            {'name': 'Sci-Fi', 'genre': '24'},
            {'name': 'Romance', 'genre': '22'},
            {'name': 'Slice of Life', 'genre': '36'},
            {'name': 'Sports', 'genre': '30'},
            {'name': 'Supernatural', 'genre': '37'},
            {'name': 'Thriller', 'genre': '41'},
            
            # По сезонам за последние годы
            {'name': '2024', 'season': '2024_2024', 'order': 'popularity'},
            {'name': '2023', 'season': '2023_2023', 'order': 'popularity'},
            {'name': '2022', 'season': '2022_2022', 'order': 'popularity'},
            {'name': '2021', 'season': '2021_2021', 'order': 'popularity'},
            {'name': '2020', 'season': '2020_2020', 'order': 'popularity'},
            {'name': '2019', 'season': '2019_2019', 'order': 'popularity'},
            {'name': '2018', 'season': '2018_2018', 'order': 'popularity'},
            {'name': '2017', 'season': '2017_2017', 'order': 'popularity'},
            {'name': '2016', 'season': '2016_2016', 'order': 'popularity'},
            {'name': '2015', 'season': '2015_2015', 'order': 'popularity'},
        ]
        
        # Импортируем с фильтрами
        self.import_by_filters(filters_list)
        
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
        logger.info(f"  Failed: {self.total_failed:,}")
        logger.info(f"  Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Показываем статистику по статусам
        logger.info("\nBy status:")
        for status in ['ongoing', 'finished', 'announced']:
            count = Anime.objects.filter(status=status).count()
            logger.info(f"  {status}: {count}")
        
        # Показываем статистику по типам
        logger.info("\nBy kind:")
        for kind in ['tv', 'movie', 'ova', 'ona']:
            count = Anime.objects.filter(kind=kind).count()
            logger.info(f"  {kind}: {count}")
        
        logger.info("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Extended Shikimori anime importer')
    parser.add_argument('--max', type=int, default=20000,
                       help='Maximum number of anime to import (default: 20000)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of worker threads (default: 5)')
    
    args = parser.parse_args()
    
    try:
        importer = ShikimoriExtendedImporter(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            max_workers=args.workers
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
