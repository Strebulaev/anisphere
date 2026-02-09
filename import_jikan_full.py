#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полноценный импорт аниме через Jikan API (MyAnimeList)
Альтернативный источник, если Shikimori недоступен
"""
import os
import sys
import django
import requests
import time
import re
import argparse
import logging

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
        logging.FileHandler('jikan_full_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class JikanFullImporter:
    """Полноценный импортер через Jikan API"""
    
    BASE_URL = "https://api.jikan.moe/v4"
    
    def __init__(self, max_anime=5000, skip_images=False, fast_mode=False):
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        })
        
        self.total_saved = 0
        self.total_updated = 0
        self.total_failed = 0
        self.processed_mal_ids = set()
        
        # Создаем директорию для постеров
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        logger.info(f"Initialized JikanFullImporter: max_anime={max_anime}")
    
    def make_request(self, endpoint, params=None, max_retries=3):
        """Выполняет запрос к Jikan API"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                # Jikan имеет лимиты
                if response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                if not self.fast_mode:
                    time.sleep(0.4)
                else:
                    time.sleep(0.2)
                
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(3)
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        return None
    
    def get_top_anime(self, page=1, limit=25):
        """Получает топ аниме"""
        params = {'page': page, 'limit': limit}
        return self.make_request('top/anime', params)
    
    def get_seasonal_anime(self, year, season, page=1):
        """Получает сезонные аниме"""
        return self.make_request(f'seasons/{year}/{season}', {'page': page})
    
    def get_anime_search(self, query, page=1, limit=25):
        """Ищет аниме"""
        params = {'q': query, 'page': page, 'limit': limit}
        return self.make_request('anime', params)
    
    def get_anime_by_id(self, mal_id):
        """Получает детали аниме по ID"""
        return self.make_request(f'anime/{mal_id}')
    
    def download_image(self, url, filename):
        """Скачивает изображение"""
        if self.skip_images or not url:
            return None
        
        try:
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
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
        if not title:
            return 'unknown'
        
        filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
    def normalize_anime_data(self, anime_data):
        """Нормализует данные аниме"""
        try:
            mal_id = anime_data.get('mal_id')
            if not mal_id:
                return None
            
            # Названия
            titles = anime_data.get('titles', [])
            title_en = anime_data.get('title', '')
            title_jp = ''
            title_ru = title_en
            
            for t in titles:
                t_type = t.get('type')
                t_title = t.get('title')
                if t_type == 'Japanese':
                    title_jp = t_title
                elif t_type == 'English':
                    title_en = t_title
            
            # Описание
            description = anime_data.get('synopsis', '') or ''
            
            # Год
            year = None
            aired = anime_data.get('aired', {})
            from_date = aired.get('from')
            if from_date:
                try:
                    year = int(str(from_date).split('-')[0])
                except:
                    pass
            
            # Статус
            status_str = anime_data.get('status', '').lower()
            status_map = {
                'finished airing': 'finished',
                'currently airing': 'ongoing',
                'not yet aired': 'announced'
            }
            status = status_map.get(status_str, 'finished')
            
            # Тип
            media_type = anime_data.get('type', '').lower()
            type_map = {
                'tv': 'tv',
                'movie': 'movie',
                'ova': 'ova',
                'ona': 'ona',
                'special': 'special',
                'music': 'music'
            }
            kind = type_map.get(media_type, 'tv')
            
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
            images = anime_data.get('images', {})
            jpg = images.get('jpg', {})
            poster_url = jpg.get('large_image_url') or jpg.get('image_url') or ''
            
            # Жанры
            genres = []
            for genre in anime_data.get('genres', []):
                name = genre.get('name')
                if name:
                    genres.append(name)
            
            # Студии
            studios = []
            for studio in anime_data.get('studios', []):
                name = studio.get('name')
                if name:
                    studios.append(name)
            
            return {
                'mal_id': mal_id,
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
                'data_source': 'jikan'
            }
            
        except Exception as e:
            logger.error(f"Error normalizing anime data: {e}")
            return None
    
    def save_anime(self, anime_data):
        """Сохраняет или обновляет аниме"""
        try:
            mal_id = anime_data.get('mal_id')
            title_ru = anime_data.get('title_ru')
            
            # Проверяем существующую запись по названию
            existing = Anime.objects.filter(title_ru=title_ru).first()
            
            # Скачиваем постер
            poster_file = None
            poster_url = anime_data.get('poster_url')
            
            if not self.skip_images and poster_url:
                filename = self.clean_filename(title_ru)
                filename = f"{filename}_{mal_id}.jpg"
                poster_file = self.download_image(poster_url, filename)
            
            if existing:
                # Обновляем существующую запись
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
                    logger.info(f"Updated: {title_ru[:50]}")
                    return True
                return False
            else:
                # Создаем новую запись
                anime = Anime.objects.create(
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
                logger.info(f"Saved: {title_ru[:50]}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving anime: {e}")
            self.total_failed += 1
            return False
    
    def import_top_anime(self, max_items=500):
        """Импортирует топ аниме"""
        logger.info(f"\nImporting top anime...")
        
        all_anime = []
        page = 1
        limit = 25
        
        while len(all_anime) < max_items:
            logger.info(f"  Page {page}...")
            
            data = self.get_top_anime(page=page, limit=limit)
            
            if not data or 'data' not in data:
                break
            
            items = data['data']
            logger.info(f"  Found {len(items)} anime")
            
            for item in items:
                if len(all_anime) >= max_items:
                    break
                
                mal_id = item.get('mal_id')
                if not mal_id or mal_id in self.processed_mal_ids:
                    continue
                
                self.processed_mal_ids.add(mal_id)
                
                # Получаем детали
                details = self.get_anime_by_id(mal_id)
                if details and 'data' in details:
                    normalized = self.normalize_anime_data(details['data'])
                    if normalized:
                        self.save_anime(normalized)
                        all_anime.append(normalized)
            
            # Проверяем следующую страницу
            pagination = data.get('pagination', {})
            has_next = pagination.get('has_next_page', False)
            
            if not has_next or len(all_anime) >= max_items:
                break
            
            page += 1
        
        logger.info(f"✅ Total processed: {len(all_anime)} anime")
        return all_anime
    
    def import_seasonal_anime(self, years, seasons):
        """Импортирует сезонные аниме"""
        logger.info(f"\nImporting seasonal anime...")
        
        all_anime = []
        
        for year in years:
            if len(all_anime) >= self.max_anime:
                break
            
            for season in seasons:
                if len(all_anime) >= self.max_anime:
                    break
                
                logger.info(f"  {season} {year}...")
                
                page = 1
                while len(all_anime) < self.max_anime:
                    data = self.get_seasonal_anime(year, season, page=page)
                    
                    if not data or 'data' not in data:
                        break
                    
                    items = data['data']
                    
                    for item in items:
                        if len(all_anime) >= self.max_anime:
                            break
                        
                        mal_id = item.get('mal_id')
                        if not mal_id or mal_id in self.processed_mal_ids:
                            continue
                        
                        self.processed_mal_ids.add(mal_id)
                        
                        # Получаем детали
                        details = self.get_anime_by_id(mal_id)
                        if details and 'data' in details:
                            normalized = self.normalize_anime_data(details['data'])
                            if normalized:
                                self.save_anime(normalized)
                                all_anime.append(normalized)
                    
                    if len(items) < 25:
                        break
                    
                    page += 1
        
        logger.info(f"✅ Total processed: {len(all_anime)} anime")
        return all_anime
    
    def import_popular_searches(self, queries):
        """Импортирует популярные аниме через поиск"""
        logger.info(f"\nImporting popular anime via search...")
        
        all_anime = []
        
        for query in queries:
            if len(all_anime) >= self.max_anime:
                break
            
            logger.info(f"  Searching: {query}...")
            
            data = self.get_anime_search(query, page=1, limit=10)
            
            if not data or 'data' not in data:
                continue
            
            items = data['data']
            
            for item in items:
                if len(all_anime) >= self.max_anime:
                    break
                
                mal_id = item.get('mal_id')
                if not mal_id or mal_id in self.processed_mal_ids:
                    continue
                
                self.processed_mal_ids.add(mal_id)
                
                # Получаем детали
                details = self.get_anime_by_id(mal_id)
                if details and 'data' in details:
                    normalized = self.normalize_anime_data(details['data'])
                    if normalized:
                        self.save_anime(normalized)
                        all_anime.append(normalized)
        
        logger.info(f"✅ Total processed: {len(all_anime)} anime")
        return all_anime
    
    def run_import(self):
        """Запускает полный импорт"""
        logger.info("=" * 80)
        logger.info("JIKAN FULL ANIME IMPORT")
        logger.info("=" * 80)
        logger.info(f"Target: {self.max_anime} anime")
        logger.info(f"Images: {'Yes' if not self.skip_images else 'No'}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Этап 1: Топ аниме
        self.import_top_anime(max_items=500)
        
        # Этап 2: Сезонные аниме за последние годы
        years = [2024, 2023, 2022, 2021, 2020]
        seasons = ['winter', 'spring', 'summer', 'fall']
        self.import_seasonal_anime(years, seasons)
        
        # Этап 3: Популярные поиски
        queries = [
            "Naruto", "One Piece", "Attack on Titan", "Demon Slayer", "My Hero Academia",
            "Death Note", "Fullmetal Alchemist", "Hunter x Hunter", "Dragon Ball",
            "Bleach", "One Punch Man", "Tokyo Ghoul", "Jujutsu Kaisen", "Chainsaw Man",
            "Spy x Family", "Vinland Saga", "Steins Gate", "Code Geass", "Neon Genesis",
            "Cowboy Bebop", "Samurai Champloo", "Mob Psycho", "Re Zero", "Konosuba",
            "Sword Art Online", "Fairy Tail", "Black Clover", "Haikyu", "Kuroko no Basket",
            "Your Lie in April", "Clannad", "Anohana", "Violet Evergarden", "March Comes in Like a Lion",
            "Made in Abyss", "Dr. Stone", "Promised Neverland", "Blue Lock", "Solo Leveling",
            "Frieren", "Oshi no Ko", "Hell's Paradise", "Mushoku Tensei", "Overlord",
            "Konosuba", "Reincarnated as a Slime", "That Time I Got Reincarnated as a Slime"
        ]
        self.import_popular_searches(queries)
        
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
    parser = argparse.ArgumentParser(description='Jikan anime importer')
    parser.add_argument('--max', type=int, default=5000,
                       help='Maximum number of anime to import (default: 5000)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
    
    args = parser.parse_args()
    
    try:
        importer = JikanFullImporter(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast
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
