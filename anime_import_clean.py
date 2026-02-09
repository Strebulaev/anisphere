#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
import time
import re
import argparse
import json
from datetime import datetime
from urllib.parse import urlencode
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

class AnimeImporter:
    def __init__(self, max_anime=None, skip_images=False, fast_mode=False, threads=1):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        self.threads = threads
        self.total_saved = 0
        self.processed_count = 0
        
        # Jikan API (неофициальный API для MyAnimeList)
        self.jikan_base_url = "https://api.jikan.moe/v4"
        
        # Создаем сессию с повторными попытками
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        print(f"✅ Using Jikan API (unofficial MyAnimeList API)")
    
    def jikan_request(self, endpoint, params=None):
        """Выполняет запрос к Jikan API"""
        url = f"{self.jikan_base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=15)
            
            # Jikan имеет лимит 60 запросов в минуту, 3 запроса в секунду
            if response.status_code == 429:
                print('⏳ Rate limited by Jikan, waiting 60 seconds...')
                time.sleep(60)
                return self.jikan_request(endpoint, params)
            
            response.raise_for_status()
            
            # Небольшая задержка чтобы не превысить лимит
            if not self.fast_mode:
                time.sleep(1)
            else:
                time.sleep(0.3)
                
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                status_code = e.response.status_code
                if status_code == 404:
                    print(f'⚠️ Not found: {endpoint}')
                elif status_code == 400:
                    print(f'⚠️ Bad request: {endpoint}')
                else:
                    print(f'⚠️ HTTP Error {status_code}: {endpoint}')
            return None
            
        except requests.exceptions.ConnectionError as e:
            print(f'🔌 Connection error: {e}')
            print('⏳ Waiting 5 seconds before retry...')
            time.sleep(5)
            return None
            
        except requests.exceptions.Timeout as e:
            print(f'⏱️ Timeout error: {e}')
            print('⏳ Waiting 5 seconds before retry...')
            time.sleep(5)
            return None
            
        except Exception as e:
            print(f'❌ Unexpected error: {type(e).__name__}: {e}')
            return None
    
    def get_jikan_top_anime(self, page=1, limit=25):
        """Получает топ аниме с Jikan"""
        params = {
            'page': page,
            'limit': limit
        }
        
        return self.jikan_request('top/anime', params)
    
    def get_jikan_anime_by_id(self, mal_id):
        """Получает информацию об аниме по ID"""
        return self.jikan_request(f'anime/{mal_id}')
    
    def get_jikan_anime_search(self, query, page=1, limit=25):
        """Ищет аниме по названию"""
        params = {
            'q': query,
            'page': page,
            'limit': limit
        }
        
        return self.jikan_request('anime', params)
    
    def get_jikan_seasonal_anime(self, year, season, page=1):
        """Получает сезонные аниме"""
        return self.jikan_request(f'seasons/{year}/{season}', {'page': page})
    
    def import_jikan_top_anime(self, max_items=100):
        """Импортирует топ аниме через Jikan"""
        print(f'⭐ Importing top anime via Jikan...')
        
        all_anime = []
        page = 1
        limit = 25
        
        while len(all_anime) < max_items:
            if self.max_anime and len(all_anime) >= self.max_anime:
                break
            
            print(f'  📄 Page {page}...', end=' ', flush=True)
            
            data = self.get_jikan_top_anime(page=page, limit=limit)
            
            if not data or 'data' not in data:
                print('❌ no data')
                break
            
            items = data['data']
            print(f'✅ {len(items)} items')
            
            # Получаем детальную информацию для каждого аниме
            for i, item in enumerate(items):
                if len(all_anime) >= max_items:
                    break
                
                mal_id = item.get('mal_id')
                if not mal_id:
                    continue
                
                title = item.get('title', 'Unknown')[:40]
                print(f'    {len(all_anime) + 1:3d}. {title}')
                
                # Получаем полную информацию
                details = self.get_jikan_anime_by_id(mal_id)
                if details and 'data' in details:
                    all_anime.append(details['data'])
            
            # Проверяем есть ли следующая страница
            pagination = data.get('pagination', {})
            has_next_page = pagination.get('has_next_page', False)
            
            if not has_next_page or len(all_anime) >= max_items:
                break
            
            page += 1
        
        print(f'✅ Total collected: {len(all_anime)} anime')
        return all_anime
    
    def import_jikan_by_popularity(self, max_items=50):
        """Импортирует популярные аниме через поиск"""
        print(f'🔥 Importing popular anime via Jikan...')
        
        all_anime = []
        search_queries = [
            "Naruto", "One Piece", "Attack on Titan", "Demon Slayer", "My Hero Academia",
            "Death Note", "Fullmetal Alchemist", "Hunter x Hunter", "Dragon Ball",
            "Bleach", "One Punch Man", "Tokyo Ghoul", "Jujutsu Kaisen", "Chainsaw Man",
            "Spy x Family", "Vinland Saga", "Steins Gate", "Code Geass", "Neon Genesis",
            "Cowboy Bebop", "Samurai Champloo", "Mob Psycho", "Re Zero", "Konosuba",
            "Sword Art Online", "Fairy Tail", "Black Clover", "Haikyu", "Kuroko no Basket",
            "Your Lie in April", "Clannad", "Anohana", "Violet Evergarden", "March Comes in Like a Lion"
        ]
        
        for query in search_queries:
            if len(all_anime) >= max_items:
                break
            
            print(f'  Searching: {query}...', end=' ', flush=True)
            
            data = self.get_jikan_anime_search(query, page=1, limit=5)
            
            if not data or 'data' not in data:
                print('❌ no results')
                continue
            
            items = data['data']
            print(f'✅ {len(items)} results')
            
            for item in items:
                if len(all_anime) >= max_items:
                    break
                
                mal_id = item.get('mal_id')
                if not mal_id:
                    continue
                
                # Проверяем нет ли уже этого аниме
                if any(a.get('mal_id') == mal_id for a in all_anime):
                    continue
                
                title = item.get('title', 'Unknown')[:40]
                print(f'    → {title}')
                
                # Получаем полную информацию
                details = self.get_jikan_anime_by_id(mal_id)
                if details and 'data' in details:
                    all_anime.append(details['data'])
        
        print(f'✅ Total collected: {len(all_anime)} anime')
        return all_anime
    
    def download_image(self, url, filename):
        """Скачивает изображение и сохраняет его в файл"""
        if self.skip_images or not url:
            return None
        
        try:
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            os.makedirs('backend/media/posters', exist_ok=True)
            filepath = f'backend/media/posters/{filename}'
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f'posters/{filename}'
        except Exception as e:
            if not self.fast_mode:
                print(f'Error downloading image: {e}')
            return None
    
    def clean_filename(self, title):
        """Очищает название для использования в имени файла"""
        if not title:
            return 'unknown'
        
        title = str(title)
        filename = re.sub(r'[^\w\s-]', '', title).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
    def parse_year(self, date_str):
        """Парсит год из строки даты"""
        if not date_str:
            return None
        
        try:
            # Форматы: "2023", "2023-10", "2023-10-15"
            year_part = str(date_str).split('-')[0]
            if year_part.isdigit():
                return int(year_part)
            return None
        except:
            return None
    
    def parse_episodes(self, episodes):
        """Парсит количество эпизодов"""
        if episodes is None:
            return None
        try:
            return int(episodes)
        except:
            return None
    
    def process_jikan_anime_data(self, jikan_data):
        """Обрабатывает данные аниме из Jikan"""
        if not jikan_data:
            return None
        
        try:
            title = jikan_data.get('title', '')
            if not title:
                return None
            
            # Альтернативные названия
            title_english = jikan_data.get('title_english', '') or title
            title_japanese = jikan_data.get('title_japanese', '') or title
            title_ru = title_english  # Используем английское название как русское
            
            # Список синонимов
            titles = jikan_data.get('titles', [])
            for t in titles:
                if t.get('type') == 'English':
                    title_english = t.get('title', title_english)
                elif t.get('type') == 'Japanese':
                    title_japanese = t.get('title', title_japanese)
                elif t.get('type') == 'German':  # Иногда есть русские названия
                    if 'ру' in t.get('title', '').lower():
                        title_ru = t.get('title')
            
            description = jikan_data.get('synopsis', '') or jikan_data.get('background', '') or ''
            
            # Даты
            aired = jikan_data.get('aired', {})
            start_date = aired.get('from')
            year = self.parse_year(start_date)
            
            episodes = self.parse_episodes(jikan_data.get('episodes'))
            score = jikan_data.get('score')
            
            # Постеры
            images = jikan_data.get('images', {})
            jpg = images.get('jpg', {})
            poster_url = jpg.get('large_image_url') or jpg.get('image_url')
            
            # Жанры
            genres = []
            jikan_genres = jikan_data.get('genres', []) + jikan_data.get('explicit_genres', [])
            for genre in jikan_genres:
                name = genre.get('name')
                if name:
                    genres.append(name)
            
            # Студии
            studios = []
            jikan_studios = jikan_data.get('studios', [])
            for studio in jikan_studios:
                name = studio.get('name')
                if name:
                    studios.append(name)
            
            # Тип
            media_type = jikan_data.get('type', '').lower()
            type_map = {
                'tv': 'tv',
                'movie': 'movie',
                'ova': 'ova',
                'ona': 'ona',
                'special': 'special',
                'music': 'music'
            }
            kind = type_map.get(media_type, 'tv')
            
            # Статус
            status_str = jikan_data.get('status', '').lower()
            status_map = {
                'finished airing': 'finished',
                'currently airing': 'ongoing',
                'not yet aired': 'announced'
            }
            status = status_map.get(status_str, 'finished')
            
            self.processed_count += 1
            
            return {
                'title_ru': title_ru,
                'title_en': title_english,
                'description': description if description else '',
                'year': year,
                'episodes': episodes,
                'score': score,
                'poster_url': poster_url,
                'genres': genres[:6],
                'studios': studios[:3],
                'kind': kind,
                'status': status,
                'source': 'jikan',
                'mal_id': jikan_data.get('mal_id')
            }
        except Exception as e:
            print(f'    ⚠️ Error processing data: {e}')
            return None
    
    def save_anime_bulk(self, processed_list):
        """Массовое сохранение аниме"""
        if not processed_list:
            return 0
        
        saved_count = 0
        
        for processed_data in processed_list:
            try:
                title_ru = processed_data['title_ru']
                
                # Скачиваем постер
                poster_file = None
                if not self.skip_images:
                    poster_url = processed_data.get('poster_url')
                    if poster_url:
                        filename = self.clean_filename(title_ru) + '.jpg'
                        poster_file = self.download_image(poster_url, filename)
                
                # Используем get_or_create с проверкой по названию
                anime, created = Anime.objects.get_or_create(
                    title_ru=title_ru,
                    defaults={
                        'title_en': processed_data['title_en'],
                        'description': processed_data['description'],
                        'year': processed_data['year'],
                        'status': processed_data['status'],
                        'kind': processed_data['kind'],
                        'episodes': processed_data['episodes'],
                        'score': processed_data['score'],
                        'poster_url': processed_data.get('poster_url'),
                        'poster': poster_file,
                        'genres': processed_data['genres'],
                        'studios': processed_data['studios'],
                        'data_source': processed_data['source']
                    }
                )
                
                if created:
                    saved_count += 1
                    self.total_saved += 1
                    print(f'    💾 Saved: {title_ru[:50]}')
                else:
                    # Обновляем если нужно
                    needs_update = False
                    if not anime.description and processed_data['description']:
                        anime.description = processed_data['description']
                        needs_update = True
                    if not anime.genres and processed_data['genres']:
                        anime.genres = processed_data['genres']
                        needs_update = True
                    if not anime.score and processed_data['score']:
                        anime.score = processed_data['score']
                        needs_update = True
                    
                    if needs_update:
                        anime.save()
                        saved_count += 1
                        self.total_saved += 1
                        print(f'    🔄 Updated: {title_ru[:50]}')
                
            except Exception as e:
                print(f'    ❌ Error saving {processed_data.get("title_ru", "Unknown")}: {e}')
        
        return saved_count
    
    def run_massive_import(self):
        """Запускает массовый импорт через Jikan"""
        print('=' * 80)
        print('🚀 MASSIVE ANIME DATABASE IMPORTER')
        print('=' * 80)
        print(f'Target: {self.max_anime or 50} anime')
        print(f'Source: Jikan API (MyAnimeList Unofficial)')
        print(f'Settings: skip_images={self.skip_images}, fast_mode={self.fast_mode}')
        print('=' * 80)
        
        start_time = time.time()
        
        # Этап 1: Топ аниме
        print('\n⭐ PHASE 1: Importing top anime')
        
        top_data = self.import_jikan_top_anime(max_items=self.max_anime or 30)
        
        # Этап 2: Популярные аниме
        print('\n🔥 PHASE 2: Importing popular anime')
        
        popular_data = self.import_jikan_by_popularity(max_items=(self.max_anime or 40) - len(top_data))
        
        # Объединяем данные
        all_data = top_data + popular_data
        
        if not all_data:
            print('❌ No data collected, stopping')
            return
        
        print(f'\n✅ Total collected: {len(all_data)} anime')
        
        # Обработка и сохранение
        print('\n💾 Processing and saving...')
        
        processed_batch = []
        for i, anime_data in enumerate(all_data):
            result = self.process_jikan_anime_data(anime_data)
            if result:
                processed_batch.append(result)
        
        if processed_batch:
            saved = self.save_anime_bulk(processed_batch)
            print(f'\n✅ Saved {saved}/{len(processed_batch)} anime to database')
        else:
            print('❌ No valid anime to save')
        
        # Статистика
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print('\n' + '=' * 80)
        print('✅ IMPORT COMPLETED!')
        print('=' * 80)
        
        total_in_db = Anime.objects.count()
        print(f'\n📊 DATABASE STATISTICS:')
        print(f'   Total anime in database: {total_in_db:,}')
        print(f'   Newly saved/updated: {self.total_saved:,}')
        print(f'   Time taken: {minutes:02d}:{seconds:02d}')
        
        # Показываем последние добавленные
        print(f'\n📝 RECENTLY ADDED:')
        recent = Anime.objects.order_by('-id')[:10]
        for anime in recent:
            year_display = f"({anime.year})" if anime.year else ""
            genres_count = len(anime.genres) if anime.genres else 0
            print(f'   - {anime.title_ru[:40]:40} {year_display:8} Genres: {genres_count}')
        
        print('\n🎉 IMPORT FINISHED SUCCESSFULLY!')

def main():
    """Точка входа с аргументами командной строки"""
    parser = argparse.ArgumentParser(description='Massive anime import script using Jikan API')
    parser.add_argument('--max', type=int, default=None, 
                       help='Maximum number of anime to import (default: 50)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images (faster)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          MASSIVE ANIME DATABASE IMPORTER                 ║
║          Source: Jikan API (MyAnimeList Unofficial)      ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        importer = AnimeImporter(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast
        )
        importer.run_massive_import()
    except KeyboardInterrupt:
        print('\n\n⏹️  Import interrupted by user.')
        total = Anime.objects.count()
        print(f'   Imported {total:,} anime before interruption.')
    except Exception as e:
        print(f'\n❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()