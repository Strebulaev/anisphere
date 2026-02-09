#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный импортёр аниме с использованием нескольких источников
Использует Jikan API (MyAnimeList) и AniList GraphQL API
Работает без VPN в РФ
"""
import os
import sys
import django
import requests
import time
import re
import argparse
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        logging.FileHandler('universal_anime_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UniversalAnimeImporter:
    """Универсальный импортёр с несколькими источниками данных"""
    
    JIKAN_API = "https://api.jikan.moe/v4"
    ANILIST_API = "https://graphql.anilist.co"
    
    def __init__(self, max_anime=10000, skip_images=False, fast_mode=False, max_workers=5):
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        self.max_workers = max_workers
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        })
        
        self.total_saved = 0
        self.total_updated = 0
        self.total_failed = 0
        self.processed_ids = set()
        
        # Создаем директорию для постеров
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        logger.info(f"Initialized UniversalAnimeImporter: max_anime={max_anime}")
    
    def make_jikan_request(self, endpoint, params=None, max_retries=3):
        """Выполняет запрос к Jikan API"""
        url = f"{self.JIKAN_API}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"Jikan rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                if not self.fast_mode:
                    time.sleep(0.4)
                else:
                    time.sleep(0.2)
                
                return response.json()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        return None
    
    def make_anilist_request(self, query, variables=None, max_retries=3):
        """Выполняет GraphQL запрос к AniList"""
        url = self.ANILIST_API
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        data = {
            'query': query,
            'variables': variables or {}
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=data, headers=headers, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 5 * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                if not self.fast_mode:
                    time.sleep(0.3)
                else:
                    time.sleep(0.15)
                
                return response.json()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None
    
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
            logger.warning(f"Failed to download image {url}: {e}")
            return None
    
    def clean_filename(self, title):
        """Очищает название для файла"""
        if not title:
            return 'unknown'
        
        filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
    def normalize_jikan_anime(self, anime_data):
        """Нормализует данные из Jikan API"""
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
            logger.error(f"Error normalizing Jikan anime: {e}")
            return None
    
    def normalize_anilist_anime(self, anime_data):
        """Нормализует данные из AniList API"""
        try:
            anilist_id = anime_data.get('id')
            if not anilist_id:
                return None
            
            # Названия
            title = anime_data.get('title', {})
            title_en = title.get('english') or title.get('romaji') or ''
            title_jp = title.get('native') or ''
            title_ru = title_en  # AniList не всегда имеет русский
            
            # Описание
            description = anime_data.get('description', '') or ''
            
            # Год
            year = anime_data.get('startDate', {}).get('year')
            
            # Статус
            status_str = anime_data.get('status', '')
            status_map = {
                'FINISHED': 'finished',
                'RELEASING': 'ongoing',
                'NOT_YET_RELEASED': 'announced',
                'CANCELLED': 'finished'
            }
            status = status_map.get(status_str, 'finished')
            
            # Тип
            media_type = anime_data.get('format', '')
            type_map = {
                'TV': 'tv',
                'TV_SHORT': 'tv',
                'MOVIE': 'movie',
                'OVA': 'ova',
                'ONA': 'ona',
                'SPECIAL': 'special',
                'MUSIC': 'music'
            }
            kind = type_map.get(media_type, 'tv')
            
            # Эпизоды
            episodes = anime_data.get('episodes')
            
            # Рейтинг
            score = anime_data.get('meanScore')
            if score is not None:
                score = score / 10.0  # AniList использует 100-балльную шкалу
            
            # Постер
            cover = anime_data.get('coverImage', {})
            poster_url = cover.get('large') or cover.get('medium') or ''
            
            # Жанры
            genres = anime_data.get('genres', [])
            
            # Студии
            studios = []
            for studio in anime_data.get('studios', {}).get('nodes', []):
                name = studio.get('name')
                if name:
                    studios.append(name)
            
            return {
                'anilist_id': anilist_id,
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
                'data_source': 'anilist'
            }
            
        except Exception as e:
            logger.error(f"Error normalizing AniList anime: {e}")
            return None
    
    def save_anime(self, anime_data):
        """Сохраняет или обновляет аниме"""
        try:
            title_ru = anime_data.get('title_ru')
            if not title_ru:
                return False
            
            # Проверяем существующую запись по названию
            existing = Anime.objects.filter(title_ru=title_ru).first()
            
            # Скачиваем постер
            poster_file = None
            poster_url = anime_data.get('poster_url')
            
            if not self.skip_images and poster_url:
                unique_id = anime_data.get('mal_id') or anime_data.get('anilist_id') or ''
                filename = self.clean_filename(title_ru)
                filename = f"{filename}_{unique_id}.jpg"
                poster_file = self.download_image(poster_url, filename)
            
            action = None
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
                    action = 'UPDATED'
                    self.log_anime_details(anime_data, action, existing.id)
                else:
                    action = 'SKIPPED'
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
                action = 'NEW'
                self.log_anime_details(anime_data, action, anime.id)
            
            return action in ['NEW', 'UPDATED']
                
        except Exception as e:
            logger.error(f"Error saving anime: {e}")
            self.total_failed += 1
            return False
    
    def log_anime_details(self, anime_data, action, anime_id):
        """Выводит подробную информацию об аниме"""
        title = anime_data['title_ru']
        title_en = anime_data['title_en']
        year = anime_data['year']
        status = anime_data['status']
        kind = anime_data['kind']
        episodes = anime_data['episodes']
        score = anime_data['score']
        genres = anime_data['genres']
        studios = anime_data['studios']
        source = anime_data['data_source']
        
        # Форматируем вывод
        logger.info(f"\n{'='*60}")
        logger.info(f"[{action}] ID: {anime_id} | Source: {source.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"📺 Title (RU): {title}")
        logger.info(f"📺 Title (EN): {title_en or 'N/A'}")
        logger.info(f"📅 Year: {year or 'N/A'}")
        logger.info(f"📊 Status: {status}")
        logger.info(f"🎬 Type: {kind}")
        logger.info(f"📼 Episodes: {episodes or 'N/A'}")
        logger.info(f"⭐ Score: {score or 'N/A'}")
        logger.info(f"🎭 Genres: {', '.join(genres) if genres else 'N/A'}")
        logger.info(f"🏢 Studios: {', '.join(studios) if studios else 'N/A'}")
        logger.info(f"{'='*60}\n")
    
    def log_consolidated_summary(self):
        """Выводит консолидированную сводку всех аниме"""
        logger.info("\n" + "="*100)
        logger.info("📊 CONSOLIDATED ANIME DATABASE SUMMARY")
        logger.info("="*100)
        
        # Общая статистика
        total = Anime.objects.count()
        with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
        with_descriptions = Anime.objects.exclude(description__isnull=True).exclude(description='').count()
        with_genres = Anime.objects.exclude(genres__isnull=True).exclude(genres='').count()
        with_studios = Anime.objects.exclude(studios__isnull=True).exclude(studios='').count()
        with_score = Anime.objects.exclude(score__isnull=True).count()
        
        logger.info(f"\n📈 OVERALL STATISTICS:")
        logger.info(f"  Total Anime: {total:,}")
        logger.info(f"  With Posters: {with_posters:,} ({with_posters/total*100:.1f}%)")
        logger.info(f"  With Descriptions: {with_descriptions:,} ({with_descriptions/total*100:.1f}%)")
        logger.info(f"  With Genres: {with_genres:,} ({with_genres/total*100:.1f}%)")
        logger.info(f"  With Studios: {with_studios:,} ({with_studios/total*100:.1f}%)")
        logger.info(f"  With Score: {with_score:,} ({with_score/total*100:.1f}%)")
        
        # По статусам
        logger.info(f"\n📊 BY STATUS:")
        status_data = {}
        for status in ['ongoing', 'finished', 'announced', 'unknown']:
            count = Anime.objects.filter(status=status).count()
            if count > 0:
                status_data[status] = count
                logger.info(f"  {status.upper()}: {count:,} ({count/total*100:.1f}%)")
        
        # По типам
        logger.info(f"\n🎬 BY TYPE:")
        type_data = {}
        for kind in ['tv', 'movie', 'ova', 'ona', 'special', 'music']:
            count = Anime.objects.filter(kind=kind).count()
            if count > 0:
                type_data[kind] = count
                logger.info(f"  {kind.upper()}: {count:,} ({count/total*100:.1f}%)")
        
        # По источникам
        logger.info(f"\n🌐 BY DATA SOURCE:")
        for source in ['jikan', 'anilist', 'shikimori', 'manual']:
            count = Anime.objects.filter(data_source=source).count()
            if count > 0:
                logger.info(f"  {source.upper()}: {count:,} ({count/total*100:.1f}%)")
        
        # По годам (топ-10)
        logger.info(f"\n📅 BY YEAR (Top 10):")
        year_data = {}
        for anime in Anime.objects.exclude(year__isnull=True):
            year = anime.year
            year_data[year] = year_data.get(year, 0) + 1
        
        sorted_years = sorted(year_data.items(), key=lambda x: x[1], reverse=True)[:10]
        for year, count in sorted_years:
            logger.info(f"  {year}: {count:,}")
        
        # Топ-20 по рейтингу
        logger.info(f"\n⭐ TOP 20 BY SCORE:")
        top_scored = Anime.objects.exclude(score__isnull=True).order_by('-score')[:20]
        for i, anime in enumerate(top_scored, 1):
            poster = "✓" if anime.poster else "✗"
            logger.info(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40s} | ⭐ {anime.score:.2f}")
        
        # Последние добавленные
        logger.info(f"\n🆕 LATEST 20 ADDED:")
        latest = Anime.objects.order_by('-id')[:20]
        for i, anime in enumerate(latest, 1):
            poster = "✓" if anime.poster else "✗"
            logger.info(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40s} | 📅 {anime.year or 'N/A'} | 📊 {anime.status}")
        
        # Оngoing аниме
        logger.info(f"\n🔄 ONGOING ANIME:")
        ongoing = Anime.objects.filter(status='ongoing').order_by('-score')
        for i, anime in enumerate(ongoing[:20], 1):
            poster = "✓" if anime.poster else "✗"
            logger.info(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40s} | ⭐ {anime.score or 'N/A':5s} | 📼 {anime.episodes or '?'}")
        
        # Популярные жанры
        logger.info(f"\n🎭 POPULAR GENRES:")
        genre_counts = {}
        for anime in Anime.objects.exclude(genres__isnull=True):
            for genre in anime.genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        for genre, count in sorted_genres:
            logger.info(f"  {genre}: {count:,}")
        
        # Популярные студии
        logger.info(f"\n🏢 POPULAR STUDIOS:")
        studio_counts = {}
        for anime in Anime.objects.exclude(studios__isnull=True):
            for studio in anime.studios:
                studio_counts[studio] = studio_counts.get(studio, 0) + 1
        
        sorted_studios = sorted(studio_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        for studio, count in sorted_studios:
            logger.info(f"  {studio}: {count:,}")
        
        logger.info("="*100 + "\n")
    
    def import_from_jikan_top(self, max_items=500):
        """Импортирует топ аниме из Jikan API"""
        logger.info(f"\n=== Importing from Jikan (Top Anime) ===")
        
        count = 0
        page = 1
        limit = 25
        
        while count < max_items:
            logger.info(f"Page {page}...")
            
            data = self.make_jikan_request('top/anime', {'page': page, 'limit': limit})
            
            if not data or 'data' not in data:
                logger.warning("No data from Jikan, stopping")
                break
            
            items = data['data']
            logger.info(f"Found {len(items)} anime")
            
            for item in items:
                if count >= max_items:
                    break
                
                mal_id = item.get('mal_id')
                if mal_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(mal_id)
                
                # Получаем детали
                details = self.make_jikan_request(f'anime/{mal_id}')
                if details and 'data' in details:
                    normalized = self.normalize_jikan_anime(details['data'])
                    if normalized:
                        self.save_anime(normalized)
                        count += 1
                        
                        if count % 50 == 0:
                            logger.info(f"  Progress: {count}/{max_items}")
            
            # Проверяем следующую страницу
            pagination = data.get('pagination', {})
            has_next = pagination.get('has_next_page', False)
            
            if not has_next or count >= max_items:
                break
            
            page += 1
        
        logger.info(f"✅ Jikan: Imported {count} anime")
        return count
    
    def import_from_jikan_seasonal(self, years, seasons):
        """Импортирует сезонные аниме из Jikan API"""
        logger.info(f"\n=== Importing from Jikan (Seasonal) ===")
        
        count = 0
        
        for year in years:
            if count >= self.max_anime:
                break
            
            for season in seasons:
                if count >= self.max_anime:
                    break
                
                logger.info(f"  {season} {year}...")
                
                page = 1
                while count < self.max_anime:
                    data = self.make_jikan_request(f'seasons/{year}/{season}', {'page': page})
                    
                    if not data or 'data' not in data:
                        break
                    
                    items = data['data']
                    
                    for item in items:
                        if count >= self.max_anime:
                            break
                        
                        mal_id = item.get('mal_id')
                        if mal_id in self.processed_ids:
                            continue
                        
                        self.processed_ids.add(mal_id)
                        
                        # Получаем детали
                        details = self.make_jikan_request(f'anime/{mal_id}')
                        if details and 'data' in details:
                            normalized = self.normalize_jikan_anime(details['data'])
                            if normalized:
                                self.save_anime(normalized)
                                count += 1
                    
                    if len(items) < 25:
                        break
                    
                    page += 1
        
        logger.info(f"✅ Jikan Seasonal: Imported {count} anime")
        return count
    
    def import_from_anilist_trending(self, max_items=500):
        """Импортирует трендовые аниме из AniList"""
        logger.info(f"\n=== Importing from AniList (Trending) ===")
        
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                }
                media(type: ANIME, sort: TRENDING_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description
                    startDate {
                        year
                    }
                    status
                    format
                    episodes
                    meanScore
                    coverImage {
                        large
                        medium
                    }
                    genres
                    studios {
                        nodes {
                            name
                        }
                    }
                }
            }
        }
        '''
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            logger.info(f"Page {page}...")
            
            variables = {'page': page, 'perPage': per_page}
            data = self.make_anilist_request(query, variables)
            
            if not data or 'data' not in data:
                logger.warning("No data from AniList, stopping")
                break
            
            media_list = data['data']['Page']['media']
            logger.info(f"Found {len(media_list)} anime")
            
            for media in media_list:
                if count >= max_items:
                    break
                
                anilist_id = media.get('id')
                if anilist_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(anilist_id)
                
                normalized = self.normalize_anilist_anime(media)
                if normalized:
                    self.save_anime(normalized)
                    count += 1
                    
                    if count % 50 == 0:
                        logger.info(f"  Progress: {count}/{max_items}")
            
            # Проверяем следующую страницу
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            
            if not has_next or count >= max_items:
                break
            
            page += 1
        
        logger.info(f"✅ AniList: Imported {count} anime")
        return count
    
    def import_from_anilist_popular(self, max_items=500):
        """Импортирует популярные аниме из AniList"""
        logger.info(f"\n=== Importing from AniList (Popular) ===")
        
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                }
                media(type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description
                    startDate {
                        year
                    }
                    status
                    format
                    episodes
                    meanScore
                    coverImage {
                        large
                        medium
                    }
                    genres
                    studios {
                        nodes {
                            name
                        }
                    }
                }
            }
        }
        '''
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            logger.info(f"Page {page}...")
            
            variables = {'page': page, 'perPage': per_page}
            data = self.make_anilist_request(query, variables)
            
            if not data or 'data' not in data:
                break
            
            media_list = data['data']['Page']['media']
            
            for media in media_list:
                if count >= max_items:
                    break
                
                anilist_id = media.get('id')
                if anilist_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(anilist_id)
                
                normalized = self.normalize_anilist_anime(media)
                if normalized:
                    self.save_anime(normalized)
                    count += 1
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            
            if not has_next or count >= max_items:
                break
            
            page += 1
        
        logger.info(f"✅ AniList Popular: Imported {count} anime")
        return count
    
    def import_from_jikan_search(self, queries):
        """Импортирует аниме через поиск в Jikan"""
        logger.info(f"\n=== Importing from Jikan (Search) ===")
        
        count = 0
        
        for query in queries:
            if count >= self.max_anime:
                break
            
            logger.info(f"  Searching: {query}...")
            
            data = self.make_jikan_request('anime', {'q': query, 'limit': 10})
            
            if not data or 'data' not in data:
                continue
            
            items = data['data']
            
            for item in items:
                if count >= self.max_anime:
                    break
                
                mal_id = item.get('mal_id')
                if mal_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(mal_id)
                
                # Получаем детали
                details = self.make_jikan_request(f'anime/{mal_id}')
                if details and 'data' in details:
                    normalized = self.normalize_jikan_anime(details['data'])
                    if normalized:
                        self.save_anime(normalized)
                        count += 1
        
        logger.info(f"✅ Jikan Search: Imported {count} anime")
        return count
    
    def run_import(self):
        """Запускает полный импорт"""
        logger.info("=" * 100)
        logger.info("🚀 UNIVERSAL ANIME IMPORT - STARTING")
        logger.info("=" * 100)
        logger.info(f"🎯 Target: {self.max_anime} anime")
        logger.info(f"🖼️  Images: {'Yes' if not self.skip_images else 'No'}")
        logger.info(f"⚡ Mode: {'Fast' if self.fast_mode else 'Normal'}")
        logger.info("=" * 100)
        
        start_time = time.time()
        total_imported = 0
        
        # Этап 1: Jikan Top Anime
        logger.info(f"\n{'='*100}")
        logger.info("📡 STAGE 1: JIKAN TOP ANIME")
        logger.info(f"{'='*100}")
        imported = self.import_from_jikan_top(max_items=500)
        total_imported += imported
        logger.info(f"✅ Stage 1 completed: {imported} anime imported")
        
        # Этап 2: AniList Trending
        logger.info(f"\n{'='*100}")
        logger.info("📡 STAGE 2: ANILIST TRENDING")
        logger.info(f"{'='*100}")
        imported = self.import_from_anilist_trending(max_items=500)
        total_imported += imported
        logger.info(f"✅ Stage 2 completed: {imported} anime imported")
        
        # Этап 3: Jikan Seasonal (последние 3 года)
        logger.info(f"\n{'='*100}")
        logger.info("📡 STAGE 3: JIKAN SEASONAL (2024-2026)")
        logger.info(f"{'='*100}")
        years = [2026, 2025, 2024]
        seasons = ['winter', 'spring', 'summer', 'fall']
        imported = self.import_from_jikan_seasonal(years, seasons)
        total_imported += imported
        logger.info(f"✅ Stage 3 completed: {imported} anime imported")
        
        # Этап 4: AniList Popular
        if total_imported < self.max_anime:
            logger.info(f"\n{'='*100}")
            logger.info("📡 STAGE 4: ANILIST POPULAR")
            logger.info(f"{'='*100}")
            remaining = self.max_anime - total_imported
            imported = self.import_from_anilist_popular(max_items=remaining)
            total_imported += imported
            logger.info(f"✅ Stage 4 completed: {imported} anime imported")
        
        # Этап 5: Популярные поиски
        if total_imported < self.max_anime:
            logger.info(f"\n{'='*100}")
            logger.info("📡 STAGE 5: POPULAR SEARCHES")
            logger.info(f"{'='*100}")
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
                "Konosuba", "Reincarnated as a Slime", "That Time I Got Reincarnated as a Slime",
                "Bocchi the Rock", "Cyberpunk Edgerunners", "Arcane", "Castlevania", "Blue Eye Samurai"
            ]
            imported = self.import_from_jikan_search(queries)
            total_imported += imported
            logger.info(f"✅ Stage 5 completed: {imported} anime imported")
        
        # Статистика выполнения
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        logger.info("\n" + "="*100)
        logger.info("🎉 IMPORT COMPLETED!")
        logger.info("="*100)
        logger.info(f"\n📊 EXECUTION STATISTICS:")
        logger.info(f"  Total Processed: {total_imported:,}")
        logger.info(f"  Newly Saved: {self.total_saved:,}")
        logger.info(f"  Updated: {self.total_updated:,}")
        logger.info(f"  Failed: {self.total_failed:,}")
        logger.info(f"  Execution Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Вывод консолидированной сводки
        self.log_consolidated_summary()
        
        logger.info("\n" + "="*100)
        logger.info("✅ ALL DONE! Check your database for all imported anime.")
        logger.info("="*100 + "\n")
    
    def main():
        parser = argparse.ArgumentParser(description='Universal anime importer')
        parser.add_argument('--max', type=int, default=10000,
                       help='Maximum number of anime to import (default: 10000)')
        parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
        parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
        parser.add_argument('--workers', type=int, default=5,
                       help='Number of worker threads (default: 5)')
    
        args = parser.parse_args()
        
        try:
            importer = UniversalAnimeImporter(
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