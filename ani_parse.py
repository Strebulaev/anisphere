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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

class AnimeImporter:
    def __init__(self, max_anime=None, skip_images=False, fast_mode=False, threads=1, client_id=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        self.threads = threads
        self.total_saved = 0
        self.processed_count = 0
        
        # MyAnimeList API
        self.mal_base_url = "https://api.myanimelist.net/v2"
        self.client_id = client_id or "YOUR_CLIENT_ID_HERE"  # Замените на ваш Client ID
        
        if self.client_id == "YOUR_CLIENT_ID_HERE":
            print("⚠️  Warning: Using default MAL Client ID. Register at https://myanimelist.net/apiconfig")
    
    def download_image(self, url, filename):
        """Скачивает изображение и сохраняет его в файл"""
        if self.skip_images or not url:
            return None
        
        try:
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
            response = requests.get(url, headers=self.headers, timeout=10)
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
        """Парсит год из строки даты MAL"""
        if not date_str:
            return None
        
        try:
            # MAL date formats: "2023", "2023-10", "2023-10-15"
            year_part = date_str.split('-')[0]
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
    
    def mal_request(self, endpoint, params=None):
        """Выполняет запрос к MyAnimeList API"""
        url = f"{self.mal_base_url}/{endpoint}"
        headers = {
            'X-MAL-CLIENT-ID': self.client_id,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)  # Увеличил timeout
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ReadTimeout as e:
            print(f'MAL API ReadTimeout: {e}')
            print('Timeout, waiting 30 seconds...')
            time.sleep(30)
            return None
        except requests.exceptions.ConnectionError as e:
            print(f'MAL API ConnectionError: {e}')
            print('Connection error, waiting 60 seconds...')
            time.sleep(60)
            return None
        except requests.exceptions.HTTPError as e:
            print(f'MAL API HTTPError: {e}')
            if e.response is not None:
                if e.response.status_code == 429:
                    print('Rate limited, waiting 60 seconds...')
                    time.sleep(60)
                elif e.response.status_code == 400:
                    print('Bad request, check parameters')
                elif e.response.status_code == 401:
                    print('Unauthorized, check Client ID')
            return None
        except Exception as e:
            print(f'MAL API Error: {type(e).__name__}: {e}')
            return None
    
    def get_mal_anime_details(self, anime_id):
        """Получает детальную информацию об аниме"""
        fields = [
            'id', 'title', 'main_picture', 'alternative_titles', 'start_date', 'end_date',
            'synopsis', 'mean', 'rank', 'popularity', 'num_list_users', 'num_scoring_users',
            'nsfw', 'media_type', 'status', 'genres', 'num_episodes', 'start_season',
            'broadcast', 'source', 'average_episode_duration', 'rating', 'pictures',
            'background', 'studios', 'statistics'
        ]
        
        params = {
            'fields': ','.join(fields)
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            data = self.mal_request(f'anime/{anime_id}', params)
            if data is not None:
                return data
            elif attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30
                print(f'  Retry {attempt + 1}/{max_retries} in {wait_time} seconds...')
                time.sleep(wait_time)
        
        return None

    def get_mal_anime_ranking(self, ranking_type='all', limit=100, offset=0):
        """Получает рейтинг аниме"""
        params = {
            'ranking_type': ranking_type,
            'limit': min(limit, 500),  # MAL ограничивает 500
            'offset': offset,
            'fields': 'id,title,main_picture,mean,rank,num_episodes,start_date,genres,studios'
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            data = self.mal_request('anime/ranking', params)
            if data is not None:
                if 'data' in data:
                    return data['data'], data.get('paging', {})
                else:
                    print(f'  Unexpected response format')
                    return [], {}
            elif attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30
                print(f'  Retry {attempt + 1}/{max_retries} in {wait_time} seconds...')
                time.sleep(wait_time)
        
        return [], {}

    def import_mal_top_anime(self, ranking_type='all', max_items=1000):
        """Импортирует топ аниме с MyAnimeList"""
        print(f'⭐ Importing MAL {ranking_type} ranking...')
        
        all_anime = []
        limit = 100  # Уменьшил для тестирования
        offset = 0
        batch_count = 0
        
        while len(all_anime) < max_items:
            if self.max_anime and len(all_anime) >= self.max_anime:
                break
            
            batch_count += 1
            print(f'  📊 Batch {batch_count} (offset: {offset})...', end=' ', flush=True)
            
            batch, paging = self.get_mal_anime_ranking(
                ranking_type=ranking_type,
                limit=limit,
                offset=offset
            )
            
            if not batch:
                print('no data or error')
                break
            
            print(f'got {len(batch)} items')
            
            # Получаем детальную информацию для каждого аниме
            detailed_batch = []
            for i, item in enumerate(batch):
                if item.get('node'):
                    anime_id = item['node']['id']
                    title = item['node'].get('title', 'Unknown')[:30]
                    print(f'    → {len(all_anime) + i + 1:4d}. {title}')
                    
                    # Получаем детальную информацию
                    details = self.get_mal_anime_details(anime_id)
                    if details:
                        detailed_batch.append(details)
                    
                    # Задержка чтобы не превысить лимит запросов
                    if not self.fast_mode:
                        time.sleep(1)  # Увеличил задержку
                    elif i % 5 == 0:
                        time.sleep(0.5)
            
            if detailed_batch:
                all_anime.extend(detailed_batch)
                print(f'  ✅ Added {len(detailed_batch)} detailed anime (total: {len(all_anime)})')
            else:
                print(f'  ⚠️ No detailed data in this batch')
            
            if 'next' not in paging or not paging['next']:
                print('  No more pages')
                break
            
            offset += limit
            
            # Большая задержка между батчами
            if not self.fast_mode:
                print(f'  ⏳ Waiting 10 seconds before next batch...')
                time.sleep(10)
            else:
                time.sleep(5)
        
        return all_anime
    
    def get_mal_seasonal_anime(self, year, season, limit=100, offset=0):
        """Получает сезонные аниме"""
        params = {
            'sort': 'anime_score',
            'limit': min(limit, 500),
            'offset': offset,
            'fields': 'id,title,main_picture,mean,num_episodes,start_date,genres,studios'
        }
        
        data = self.mal_request(f'anime/season/{year}/{season}', params)
        if data and 'data' in data:
            return data['data'], data.get('paging', {})
        return [], {}
    
    def get_mal_anime_list(self, query=None, limit=100, offset=0):
        """Ищет аниме по названию"""
        params = {
            'q': query or '',
            'limit': min(limit, 100),
            'offset': offset,
            'fields': 'id,title,main_picture,mean,num_episodes,start_date,genres,studios'
        }
        
        data = self.mal_request('anime', params)
        if data and 'data' in data:
            return data['data'], data.get('paging', {})
        return [], {}
    
    def import_mal_top_anime(self, ranking_type='all', max_items=1000):
        """Импортирует топ аниме с MyAnimeList"""
        print(f'⭐ Importing MAL {ranking_type} ranking...')
        
        all_anime = []
        limit = 500  # Максимум за запрос
        offset = 0
        
        while len(all_anime) < max_items:
            if self.max_anime and len(all_anime) >= self.max_anime:
                break
            
            print(f'  📊 Batch {offset//500 + 1}...', end=' ', flush=True)
            
            batch, paging = self.get_mal_anime_ranking(
                ranking_type=ranking_type,
                limit=limit,
                offset=offset
            )
            
            if not batch:
                print('no data')
                break
            
            # Получаем детальную информацию для каждого аниме
            detailed_batch = []
            for i, item in enumerate(batch):
                if item.get('node'):
                    anime_id = item['node']['id']
                    print(f'    → {len(all_anime) + i + 1:4d}. {item["node"]["title"][:40]}...')
                    
                    # Получаем детальную информацию
                    details = self.get_mal_anime_details(anime_id)
                    if details:
                        detailed_batch.append(details)
                    
                    # Задержка чтобы не превысить лимит запросов
                    if not self.fast_mode and i % 10 == 0:
                        time.sleep(1)
            
            all_anime.extend(detailed_batch)
            print(f'got {len(detailed_batch)} detailed anime (total: {len(all_anime)})')
            
            if 'next' not in paging or not paging['next']:
                break
            
            offset += limit
            
            if not self.fast_mode:
                time.sleep(2)
            else:
                time.sleep(1)
        
        return all_anime
    
    def import_mal_seasonal(self, years_back=10):
        """Импортирует сезонные аниме за несколько лет"""
        print(f'🍂 Importing MAL seasonal anime...')
        
        all_anime = []
        current_year = datetime.now().year
        seasons = ['winter', 'spring', 'summer', 'fall']
        
        for year in range(current_year, current_year - years_back - 1, -1):
            for season in seasons:
                if self.max_anime and len(all_anime) >= self.max_anime:
                    break
                
                print(f'  {season.capitalize()} {year}...', end=' ', flush=True)
                
                batch, paging = self.get_mal_seasonal_anime(year, season, limit=200)
                
                if batch:
                    # Получаем детальную информацию
                    detailed_batch = []
                    for i, item in enumerate(batch):
                        if item.get('node'):
                            anime_id = item['node']['id']
                            
                            # Получаем детальную информацию
                            details = self.get_mal_anime_details(anime_id)
                            if details:
                                detailed_batch.append(details)
                                title = details.get('title', 'Unknown')[:30]
                                print(f'    → {title}')
                            
                            # Задержка
                            if not self.fast_mode and i % 5 == 0:
                                time.sleep(1)
                    
                    all_anime.extend(detailed_batch)
                    print(f'  collected {len(detailed_batch)} anime')
                else:
                    print(f'no data')
                
                if not self.fast_mode:
                    time.sleep(3)
                else:
                    time.sleep(1.5)
        
        return all_anime
    
    def import_mal_by_genres(self):
        """Импортирует аниме по популярным жанрам"""
        print(f'🎭 Importing MAL anime by genres...')
        
        all_anime = []
        seen_ids = set()
        
        # Популярные жанры для поиска
        genre_queries = [
            "action", "adventure", "comedy", "drama", "fantasy", "romance",
            "sci-fi", "slice of life", "sports", "supernatural", "mystery",
            "horror", "psychological", "mecha", "music", "school", "shounen",
            "shoujo", "seinen", "josei", "isekai", "magic", "samurai", "vampire"
        ]
        
        for query in genre_queries:
            if self.max_anime and len(all_anime) >= self.max_anime:
                break
            
            print(f'  {query}...', end=' ', flush=True)
            
            batch, paging = self.get_mal_anime_list(query=query, limit=100)
            
            if batch:
                # Получаем детальную информацию
                detailed_batch = []
                for i, item in enumerate(batch):
                    if item.get('node'):
                        anime_id = item['node']['id']
                        
                        if anime_id in seen_ids:
                            continue
                        
                        seen_ids.add(anime_id)
                        
                        # Получаем детальную информацию
                        details = self.get_mal_anime_details(anime_id)
                        if details:
                            detailed_batch.append(details)
                            title = details.get('title', 'Unknown')[:30]
                            print(f'    → {title}')
                        
                        # Задержка
                        if not self.fast_mode and i % 5 == 0:
                            time.sleep(1)
                
                all_anime.extend(detailed_batch)
                print(f'  collected {len(detailed_batch)} anime')
            else:
                print(f'no data')
            
            if not self.fast_mode:
                time.sleep(3)
            else:
                time.sleep(1.5)
        
        return all_anime
    
    def process_mal_anime_data(self, mal_data):
        """Обрабатывает данные аниме из MAL"""
        if not mal_data:
            return None
        
        try:
            # Основное название (английское или японское)
            title = mal_data.get('title', '')
            if not title:
                return None
            
            # Альтернативные названия
            alt_titles = mal_data.get('alternative_titles', {})
            title_en = alt_titles.get('en') or title
            title_ru = alt_titles.get('ru') or alt_titles.get('synonyms', [title_en])[0]
            
            # Описание
            description = mal_data.get('synopsis', '') or ''
            
            # Даты
            start_date = mal_data.get('start_date')
            end_date = mal_data.get('end_date')
            year = self.parse_year(start_date)
            
            # Эпизоды
            episodes = self.parse_episodes(mal_data.get('num_episodes'))
            
            # Рейтинг
            score = mal_data.get('mean')
            
            # Постер
            poster_url = None
            main_picture = mal_data.get('main_picture', {})
            if main_picture:
                poster_url = main_picture.get('large') or main_picture.get('medium')
            
            # Жанры
            genres = []
            mal_genres = mal_data.get('genres', [])
            for genre in mal_genres:
                if genre.get('name'):
                    genres.append(genre['name'])
            
            # Студии
            studios = []
            mal_studios = mal_data.get('studios', [])
            for studio in mal_studios:
                if studio.get('name'):
                    studios.append(studio['name'])
            
            # Тип
            media_type = mal_data.get('media_type', '').lower()
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
            status_str = mal_data.get('status', '').lower()
            status_map = {
                'finished_airing': 'finished',
                'currently_airing': 'ongoing',
                'not_yet_aired': 'announced'
            }
            status = status_map.get(status_str, 'finished')
            
            # Статистика
            popularity = mal_data.get('popularity')
            rank = mal_data.get('rank')
            
            self.processed_count += 1
            
            return {
                'title_ru': title_ru,
                'title_en': title_en,
                'description': description[:2000] if description else '',  # Ограничиваем длину
                'year': year,
                'episodes': episodes,
                'score': score,
                'poster_url': poster_url,
                'genres': genres[:8],  # Берем первые 8 жанров
                'studios': studios[:3],  # Берем первые 3 студии
                'kind': kind,
                'status': status,
                'source': 'myanimelist',
                'popularity': popularity,
                'rank': rank,
                'mal_id': mal_data.get('id')
            }
        except Exception as e:
            print(f'    ⚠️ Error processing MAL data: {e}')
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
                
                # Используем get_or_create с title_ru как уникальным полем
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
                    
                    # Периодический вывод прогресса
                    if saved_count % 20 == 0:
                        print(f'    📊 Saved {saved_count}/{len(processed_list)} (total: {self.total_saved})')
                
            except Exception as e:
                if not self.fast_mode:
                    print(f'    ⚠️ Error saving {processed_data.get("title_ru", "Unknown")}: {e}')
        
        return saved_count
    
    def run_massive_import(self):
        """Запускает массовый импорт с MyAnimeList"""
        print('=' * 80)
        print('🚀 MASSIVE ANIME DATABASE IMPORTER')
        print('=' * 80)
        print(f'Target: 10,000+ anime')
        print(f'Source: MyAnimeList API')
        print(f'Client ID: {self.client_id[:10]}...')
        print(f'Settings: max_anime={self.max_anime or "unlimited"}, '
              f'skip_images={self.skip_images}, fast_mode={self.fast_mode}, threads={self.threads}')
        print('=' * 80)
        
        start_time = time.time()
        
        # Этап 1: Топ аниме
        print('\n⭐ PHASE 1: Importing top anime from MAL')
        print('   (This will take some time due to API rate limits)')
        
        top_data = self.import_mal_top_anime(ranking_type='all', max_items=2000)
        print(f'✅ Phase 1: Collected {len(top_data)} top anime')
        
        # Этап 2: Сезонные аниме
        print('\n🍂 PHASE 2: Importing seasonal anime')
        
        seasonal_data = self.import_mal_seasonal(years_back=5)
        print(f'✅ Phase 2: Collected {len(seasonal_data)} seasonal anime')
        
        # Этап 3: Аниме по жанрам
        print('\n🎭 PHASE 3: Importing anime by genres')
        
        genre_data = self.import_mal_by_genres()
        print(f'✅ Phase 3: Collected {len(genre_data)} genre-based anime')
        
        # Объединяем все данные
        all_data = top_data + seasonal_data + genre_data
        
        # Убираем дубликаты по mal_id
        print(f'\n🧹 Removing duplicates...')
        unique_data = []
        seen_ids = set()
        
        for anime in all_data:
            if anime is None:
                continue
            
            mal_id = anime.get('id')
            if not mal_id or mal_id in seen_ids:
                continue
            
            seen_ids.add(mal_id)
            unique_data.append(anime)
        
        print(f'✅ Unique anime to process: {len(unique_data):,}')
        
        if not unique_data:
            print('❌ No valid anime data collected')
            return
        
        # Обработка и сохранение
        print('\n💾 PHASE 4: Processing and saving to database...')
        
        batch_size = 50  # Меньше из-за API ограничений
        total_batches = (len(unique_data) + batch_size - 1) // batch_size
        
        print(f'   Batch size: {batch_size}, Total batches: {total_batches}')
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = start_idx + batch_size
            batch = unique_data[start_idx:end_idx]
            
            print(f'\n  Processing batch {batch_num + 1}/{total_batches} '
                  f'({len(batch)} anime)...')
            
            # Обрабатываем батч
            processed_batch = []
            for i, anime_data in enumerate(batch):
                result = self.process_mal_anime_data(anime_data)
                if result:
                    processed_batch.append(result)
                    print(f'    → {start_idx + i + 1:4d}. {result["title_ru"][:40]}')
            
            if processed_batch:
                saved = self.save_anime_bulk(processed_batch)
                success_rate = (saved / len(processed_batch)) * 100 if processed_batch else 0
                print(f'  ✅ Saved {saved}/{len(processed_batch)} '
                      f'({success_rate:.1f}% success rate)')
            else:
                print(f'  ⚠️ No valid anime in this batch')
            
            # Задержка между батчами
            if not self.fast_mode and batch_num + 1 < total_batches:
                print(f'  ⏳ Waiting 2 seconds...')
                time.sleep(2)
        
        # Статистика
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        print('\n' + '=' * 80)
        print('✅ IMPORT COMPLETED!')
        print('=' * 80)
        
        total_in_db = Anime.objects.count()
        print(f'\n📊 DATABASE STATISTICS:')
        print(f'   Total anime in database: {total_in_db:,}')
        print(f'   Processed during import: {self.processed_count:,}')
        print(f'   Newly saved/updated: {self.total_saved:,}')
        print(f'   Time taken: {hours:02d}:{minutes:02d}:{seconds:02d}')
        
        # Подробная статистика
        print(f'\n📈 DETAILED STATS:')
        
        # По жанрам
        anime_with_genres = Anime.objects.exclude(genres=[]).count()
        if total_in_db > 0:
            print(f'   With genres: {anime_with_genres:,} ({anime_with_genres/total_in_db*100:.1f}%)')
        
        # По годам
        years = Anime.objects.exclude(year__isnull=True).values_list('year', flat=True).distinct()
        if years:
            print(f'   Years covered: {len(years)} (from {min(years)} to {max(years)})')
        
        print('\n🎉 MASSIVE IMPORT FINISHED SUCCESSFULLY!')

def main():
    """Точка входа с аргументами командной строки"""
    parser = argparse.ArgumentParser(description='Massive anime import script using MyAnimeList API')
    parser.add_argument('--max', type=int, default=None, 
                       help='Maximum number of anime to import (default: unlimited)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images (faster)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays, may be less reliable)')
    parser.add_argument('--threads', type=int, default=1,
                       help='Number of threads for processing (1-4 recommended)')
    parser.add_argument('--client-id', type=str, default=None,
                       help='MyAnimeList Client ID (get from https://myanimelist.net/apiconfig)')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          MASSIVE ANIME DATABASE IMPORTER                 ║
║          Target: 10,000+ anime                           ║
║          Source: MyAnimeList API                         ║
║          Version: 3.0 (MAL API)                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    if not args.client_id:
        print("⚠️  Warning: No Client ID provided!")
        print("   Get your Client ID from: https://myanimelist.net/apiconfig")
        print("   Or run with: --client-id YOUR_CLIENT_ID")
        args.client_id = input("Enter your MAL Client ID (or press Enter to use default): ").strip()
        if not args.client_id:
            args.client_id = "YOUR_CLIENT_ID_HERE"
    
    try:
        importer = AnimeImporter(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            threads=args.threads,
            client_id=args.client_id
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