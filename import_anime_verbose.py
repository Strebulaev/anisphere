#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный импортёр аниме с подробным выводом всех данных
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
    format='%(message)s',
    handlers=[
        logging.FileHandler('verbose_anime_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class VerboseAnimeImporter:
    """Импортёр с подробным выводом всех данных"""
    
    JIKAN_API = "https://api.jikan.moe/v4"
    ANILIST_API = "https://graphql.anilist.co"
    ANILIST_TRENDING_QUERY = '''
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
        self.total_skipped = 0
        self.processed_ids = set()
        self.all_anime_data = []  # Храним все данные для консолидации
        
        # Создаем директорию для постеров
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        self.log_header(f"Initialized VerboseAnimeImporter: max_anime={max_anime}")
    
    def log_header(self, message):
        """Выводит заголовок"""
        logger.info("\n" + "="*100)
        logger.info(f"  {message}")
        logger.info("="*100 + "\n")
    
    def log_section(self, message):
        """Выводит секцию"""
        logger.info(f"\n{'─'*100}")
        logger.info(f"  {message}")
        logger.info(f"{'─'*100}\n")
    
    def make_jikan_request(self, endpoint, params=None, max_retries=3):
        """Выполняет запрос к Jikan API"""
        url = f"{self.JIKAN_API}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 30 * (attempt + 1)
                    logger.warning(f"⏳ Jikan rate limited. Waiting {wait_time}s...")
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
        """Скачивает изображение с несколькими методами обхода блокировки"""
        if self.skip_images or not url:
            return None
        
        methods_to_try = [
            # Метод 1: Прямой запрос (самый быстрый)
            {
                'name': 'Direct',
                'func': lambda u: self.session.get(u, timeout=10),
                'proxies': None
            },
            # Метод 2: С HTTPS если HTTP
            {
                'name': 'HTTPS',
                'func': lambda u: self.session.get(
                    u.replace('http://', 'https://') if u.startswith('http://') else u,
                    timeout=10
                ),
                'proxies': None
            },
            # Метод 3: Без реферера
            {
                'name': 'No Referer',
                'func': lambda u: self.session.get(u, timeout=10, 
                    headers={'Referer': 'https://myanimelist.net/'}
                ),
                'proxies': None
            },
            # Метод 4: Tor (если запущен)
            {
                'name': 'Tor',
                'func': lambda u: self.session.get(u, timeout=15, 
                    proxies={'http': 'socks5h://127.0.0.1:9150',
                            'https': 'socks5h://127.0.0.1:9150'}
                ),
                'proxies': 'socks5h://127.0.0.1:9150'
            },
            # Метод 5: Tor альтернативный порт
            {
                'name': 'Tor (9050)',
                'func': lambda u: self.session.get(u, timeout=15,
                    proxies={'http': 'socks5h://127.0.0.1:9050',
                            'https': 'socks5h://127.0.0.1:9050'}
                ),
                'proxies': 'socks5h://127.0.0.1:9050'
            },
        ]
        
        for method in methods_to_try:
            try:
                logger.debug(f"  Trying {method['name']} method...")
                
                response = method['func'](url)
                
                if response.status_code == 200:
                    # Проверяем что это изображение
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type:
                        logger.warning(f"  ⚠️  Not an image ({content_type})")
                        continue
                    
                    filepath = f'backend/media/anime_posters/{filename}'
                    
                    # Создаем директорию если нужно
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"  ✅ Downloaded via {method['name']}: {filename}")
                    return f'anime_posters/{filename}'
                    
                elif response.status_code == 403 or response.status_code == 429:
                    logger.warning(f"  ⏳ Blocked by {method['name']} (HTTP {response.status_code})")
                    time.sleep(2)
                    
            except requests.exceptions.ConnectionError as e:
                if '9050' in str(method.get('proxies', '')) or '9150' in str(method.get('proxies', '')):
                    logger.debug(f"  Tor not running on port {method['name'].split('(')[-1].replace(')', '')}")
                else:
                    logger.debug(f"  Connection failed for {method['name']}: {e}")
                continue
            except Exception as e:
                logger.debug(f"  Method {method['name']} failed: {e}")
                continue
        
        logger.warning(f"  ❌ All methods failed for: {url[:60]}...")
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
            
            description = anime_data.get('synopsis', '') or ''
            
            year = None
            aired = anime_data.get('aired', {})
            from_date = aired.get('from')
            if from_date:
                try:
                    year = int(str(from_date).split('-')[0])
                except:
                    pass
            
            status_str = anime_data.get('status', '').lower()
            status_map = {
                'finished airing': 'finished',
                'currently airing': 'ongoing',
                'not yet aired': 'announced'
            }
            status = status_map.get(status_str, 'finished')
            
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
            images = anime_data.get('images', {})
            jpg = images.get('jpg', {})
            poster_url = jpg.get('large_image_url') or jpg.get('image_url') or ''
            
            genres = []
            for genre in anime_data.get('genres', []):
                name = genre.get('name')
                if name:
                    genres.append(name)
            
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
            return None
    
    def normalize_anilist_anime(self, anime_data):
        """Нормализует данные из AniList API"""
        try:
            anilist_id = anime_data.get('id')
            if not anilist_id:
                return None
            
            title = anime_data.get('title', {})
            title_en = title.get('english') or title.get('romaji') or ''
            title_jp = title.get('native') or ''
            title_ru = title_en
            
            description = anime_data.get('description', '') or ''
            
            year = anime_data.get('startDate', {}).get('year')
            
            status_str = anime_data.get('status', '')
            status_map = {
                'FINISHED': 'finished',
                'RELEASING': 'ongoing',
                'NOT_YET_RELEASED': 'announced',
                'CANCELLED': 'finished'
            }
            status = status_map.get(status_str, 'finished')
            
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
            
            episodes = anime_data.get('episodes')
            
            score = anime_data.get('meanScore')
            if score is not None:
                score = score / 10.0
            
            cover = anime_data.get('coverImage', {})
            poster_url = cover.get('large') or cover.get('medium') or ''
            
            genres = anime_data.get('genres', [])
            
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
            return None
        
    def save_anime(self, anime_data):
        """Сохраняет или обновляет аниме"""
        try:
            title_ru = anime_data.get('title_ru')
            if not title_ru:
                return False
            
            existing = Anime.objects.filter(title_ru=title_ru).first()
            
            poster_file = None
            poster_url = anime_data.get('poster_url')
            
            if not self.skip_images and poster_url:
                unique_id = anime_data.get('mal_id') or anime_data.get('anilist_id') or ''
                filename = self.clean_filename(title_ru)
                filename = f"{filename}_{unique_id}.jpg"
                
                filepath = f'backend/media/anime_posters/{filename}'
                
                # Если файл уже существует
                if os.path.exists(filepath):
                    poster_file = f'anime_posters/{filename}'
                    logger.info(f"  📁 Poster already exists: {filename}")
                else:
                    # Пробуем скачать
                    poster_file = self.download_image(poster_url, filename)
                    
                    # Если MyAnimeList заблокирован, пробуем получить постер из AniList
                    if not poster_file and 'myanimelist.net' in poster_url:
                        logger.info(f"  🔄 MyAnimeList blocked, trying AniList...")
                        
                        # Получаем аналог с AniList
                        anime_title = anime_data.get('title_en') or title_ru
                        anilist_poster = self.get_anilist_poster(anime_title, unique_id)
                        
                        if anilist_poster:
                            poster_file = anilist_poster
                            poster_url = ''  # Очищаем MyAnimeList URL
                            anime_data['poster_url'] = ''  # Обновляем в данных
            
            action = None
            anime_id = None
            
            if existing:
                updated = False
                
                # Проверяем и обновляем постер в любом случае
                if poster_file and not existing.poster:
                    existing.poster = poster_file
                    updated = True
                    logger.info(f"  🖼️  Added missing poster to existing anime")
                
                if existing.poster_url != poster_url and poster_url:
                    existing.poster_url = poster_url
                    updated = True
                
                # Остальные поля проверяем только если они пустые
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
                
                if updated:
                    existing.save()
                    self.total_updated += 1
                    action = 'UPDATED'
                    anime_id = existing.id
                else:
                    action = 'SKIPPED'
                    anime_id = existing.id
                    self.total_skipped += 1
                    
                    # Но даже для SKIPPED обновляем постер если нужно
                    if poster_file and existing.poster != poster_file:
                        existing.poster = poster_file
                        existing.poster_url = poster_url
                        existing.save()
                        logger.info(f"  🖼️  Updated poster for SKIPPED entry")
            else:
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
                anime_id = anime.id
            
            # Сохраняем данные для консолидации
            anime_data['action'] = action
            anime_data['db_id'] = anime_id
            self.all_anime_data.append(anime_data)
            
            # Выводим детали
            self.log_anime_details(anime_data, action, anime_id)
            
            return action in ['NEW', 'UPDATED', 'SKIPPED']
                    
        except Exception as e:
            logger.error(f"❌ Error saving anime: {e}")
            self.total_failed += 1
            return False
    
    def get_anilist_poster(self, title, mal_id=None):
        """Получает постер из AniList по названию"""
        query = '''
        query ($search: String, $malId: Int) {
            Page(page: 1, perPage: 1) {
                media(type: ANIME, search: $search, idMal: $malId) {
                    coverImage {
                        large
                        medium
                    }
                }
            }
        }
        '''
        
        variables = {'search': title}
        if mal_id:
            variables['malId'] = int(mal_id)
        
        try:
            data = self.make_anilist_request(query, variables)
            
            if data and 'data' in data:
                media_list = data['data']['Page']['media']
                if media_list and media_list[0]:
                    cover = media_list[0]['coverImage']
                    poster_url = cover.get('large') or cover.get('medium')
                    
                    if poster_url:
                        # Скачиваем этот постер
                        filename = f"anilist_{self.clean_filename(title)}_{mal_id or 'search'}.jpg"
                        return self.download_image(poster_url, filename)
        except Exception as e:
            logger.debug(f"  Failed to get AniList poster: {e}")
        
        return None

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
        poster_url = anime_data.get('poster_url', '')
        
        # Иконки
        action_icons = {
            'NEW': '🆕',
            'UPDATED': '🔄',
            'SKIPPED': '📥'  # ⬅️ Изменено на иконку загрузки
        }
        
        icon = action_icons.get(action, '❓')
        
        # Проверяем наличие постера в БД
        poster_status = '❌ No poster'
        poster_file_path = None
        
        if anime_id:
            try:
                anime_obj = Anime.objects.get(id=anime_id)
                if anime_obj.poster:
                    poster_file_path = anime_obj.poster.name
                    
                    # Проверяем физическое существование файла
                    full_path = f'backend/media/{poster_file_path}'
                    if os.path.exists(full_path):
                        poster_status = f'✅ {poster_file_path}'
                    else:
                        poster_status = f'⚠️  File missing: {poster_file_path}'
                elif poster_url:
                    poster_status = f'⏳ URL only: {poster_url[:60]}...'
            except:
                if poster_url:
                    poster_status = f'⏳ URL only: {poster_url[:60]}...'
        
        # Форматируем вывод
        logger.info(f"{icon} [{action}] ID: {anime_id} | Source: {source.upper()}")
        logger.info(f"  📺 Title (RU): {title}")
        if title_en:
            logger.info(f"  📺 Title (EN): {title_en}")
        logger.info(f"  📅 Year: {year or 'N/A'} | 📊 Status: {status} | 🎬 Type: {kind}")
        logger.info(f"  📼 Episodes: {episodes or 'N/A'} | ⭐ Score: {score or 'N/A'}")
        
        # Постер
        logger.info(f"  🖼️  Poster: {poster_status}")
        
        if genres:
            logger.info(f"  🎭 Genres: {', '.join(genres)}")
        if studios:
            logger.info(f"  🏢 Studios: {', '.join(studios)}")
        
        logger.info("")
    
    def log_consolidated_summary(self):
        """Выводит консолидированную сводку всех аниме"""
        self.log_header("📊 CONSOLIDATED ANIME DATABASE SUMMARY")
        
        # Общая статистика
        total = Anime.objects.count()
        with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
        with_descriptions = Anime.objects.exclude(description__isnull=True).exclude(description='').count()
        with_genres = Anime.objects.exclude(genres__isnull=True).exclude(genres='').count()
        with_studios = Anime.objects.exclude(studios__isnull=True).exclude(studios='').count()
        with_score = Anime.objects.exclude(score__isnull=True).count()
        with_poster_urls = Anime.objects.exclude(poster_url__isnull=True).exclude(poster_url='').count()
        
        logger.info("📈 OVERALL STATISTICS:")
        logger.info(f"  Total Anime: {total:,}")
        logger.info(f"  With Posters (local): {with_posters:,} ({with_posters/total*100:.1f}%)")
        logger.info(f"  With Poster URLs: {with_poster_urls:,} ({with_poster_urls/total*100:.1f}%)")
        logger.info(f"  With Descriptions: {with_descriptions:,} ({with_descriptions/total*100:.1f}%)")
        logger.info(f"  With Genres: {with_genres:,} ({with_genres/total*100:.1f}%)")
        logger.info(f"  With Studios: {with_studios:,} ({with_studios/total*100:.1f}%)")
        logger.info(f"  With Score: {with_score:,} ({with_score/total*100:.1f}%)")
        
        # Популярные студии
        logger.info(f"\n🏢 POPULAR STUDIOS:")
        studio_counts = {}
        for anime in Anime.objects.exclude(studios__isnull=True):
            for studio in anime.studios:
                studio_counts[studio] = studio_counts.get(studio, 0) + 1
        
        sorted_studios = sorted(studio_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        for studio, count in sorted_studios:
            logger.info(f"  {studio}: {count:,}")
        
        # Примеры постеров
        logger.info(f"\n🖼️  POSTER PATHS EXAMPLES:")
        anime_with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='')[:10]
        if anime_with_posters:
            for i, anime in enumerate(anime_with_posters, 1):
                logger.info(f"  {i}. {anime.title_ru[:40]:40s}")
                logger.info(f"     Path: {anime.poster.name}")
                logger.info(f"     URL:  {anime.poster_url[:60] if anime.poster_url else 'N/A'}...")
        else:
            logger.info(f"  ⚠️  No local posters found yet (run with images to download)")
        
        # По статусам
        logger.info(f"\n📊 BY STATUS:")
        for status in ['ongoing', 'finished', 'announced']:
            count = Anime.objects.filter(status=status).count()
            if count > 0:
                logger.info(f"  {status.upper()}: {count:,} ({count/total*100:.1f}%)")
        
        # По типам
        logger.info(f"\n🎬 BY TYPE:")
        for kind in ['tv', 'movie', 'ova', 'ona', 'special', 'music']:
            count = Anime.objects.filter(kind=kind).count()
            if count > 0:
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
        
        # Ongoing аниме
        logger.info(f"\n🔄 ONGOING ANIME:")
        ongoing = Anime.objects.filter(status='ongoing').order_by('-score')
        for i, anime in enumerate(ongoing[:20], 1):
            poster = "✓" if anime.poster else "✗"
            logger.info(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40s} | ⭐ {anime.score or 'N/A':5} | 📼 {anime.episodes or '?'}")
        
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
        
        # Все импортированные аниме в текущем запуске
        logger.info(f"\n📋 ALL ANIME PROCESSED IN THIS RUN:")
        logger.info(f"  Total processed: {len(self.all_anime_data)}")
        logger.info(f"  New: {self.total_saved}")
        logger.info(f"  Updated: {self.total_updated}")
        logger.info(f"  Skipped: {self.total_skipped}")
        logger.info(f"  Failed: {self.total_failed}")
        
        if self.all_anime_data:
            logger.info(f"\n📝 DETAILED LIST:")
            for i, anime in enumerate(self.all_anime_data, 1):
                action = anime['action']
                icon = {'NEW': '🆕', 'UPDATED': '🔄', 'SKIPPED': '⏭️ '}.get(action, '❓')
                logger.info(f"  {i:3d}. {icon} [{action}] {anime['title_ru'][:50]:50s} | {anime['data_source'].upper()}")
    
    def import_from_jikan_top(self, max_items=500):
        """Оптимизированный импорт из Jikan"""
        self.log_section("STAGE 1: JIKAN TOP ANIME (OPTIMIZED)")
        
        count = 0
        page = 1
        limit = 50
        
        while count < max_items:
            logger.info(f"📄 Page {page}...")
            
            # Получаем список топ аниме
            data = self.make_jikan_request_smart('top/anime', {'page': page, 'limit': limit})
            
            if not data or 'data' not in data:
                logger.warning(f"⚠️  No data from Jikan page {page}, stopping")
                break
            
            items = data['data']
            logger.info(f"✅ Found {len(items)} anime on page {page}")
            
            # Обрабатываем каждое аниме
            for item in items:
                if count >= max_items:
                    break
                
                mal_id = item.get('mal_id')
                if not mal_id:
                    continue
                    
                if mal_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(mal_id)
                
                # Получаем детали с задержкой
                time.sleep(1.0)  # 1 запрос в секунду
                details = self.make_jikan_request_smart(f'anime/{mal_id}')
                
                if details and 'data' in details:
                    normalized = self.normalize_jikan_anime(details['data'])
                    if normalized:
                        if self.save_anime(normalized):
                            count += 1
                
                if count % 10 == 0:
                    logger.info(f"📊 Progress: {count}/{max_items} anime imported")
            
            # Проверяем следующую страницу
            has_next = data.get('pagination', {}).get('has_next_page', False)
            if not has_next or count >= max_items:
                break
            
            page += 1
        
        logger.info(f"✅ Jikan Top: {count} anime imported\n")
        return count

    def use_minimal_data(self, item):
        """Проверяет, достаточно ли данных из списка"""
        # Можно использовать минимум данных для ускорения
        # Возвращает True если можно обойтись без детального запроса
        return False  # Пока всегда запрашиваем детали
    
    def normalize_jikan_anime_fast(self, anime_data):
        """Быстрая нормализация данных из Jikan API"""
        try:
            # Используем упрощенную версию normalize_jikan_anime
            return self.normalize_jikan_anime(anime_data)
        except:
            return None
    
    def log_quick_summary(self):
        """Быстрая сводка (без ошибки форматирования)"""
        self.log_header("📊 QUICK DATABASE SUMMARY")
        
        total = Anime.objects.count()
        with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
        
        logger.info("📈 OVERALL STATISTICS:")
        logger.info(f"  Total Anime: {total:,}")
        logger.info(f"  With Posters: {with_posters:,} ({with_posters/total*100:.1f}%)")
        logger.info(f"  New in this run: {self.total_saved:,}")
        logger.info(f"  Updated: {self.total_updated:,}")
        
        # Топ-10 по рейтингу
        logger.info(f"\n⭐ TOP 10 BY SCORE:")
        top_scored = Anime.objects.exclude(score__isnull=True).order_by('-score')[:10]
        for i, anime in enumerate(top_scored, 1):
            poster = "✓" if anime.poster else "✗"
            score = f"{anime.score:.2f}" if anime.score else "N/A"
            logger.info(f"  {i:2d}. [{poster}] {anime.title_ru[:40]:40s} | ⭐ {score}")

    def make_jikan_request_smart(self, endpoint, params=None):
        """Умный запрос к Jikan с обработкой rate limiting"""
        url = f"{self.JIKAN_API}/{endpoint}"
        
        logger.debug(f"  Jikan request: {endpoint}")
        
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 429:
                    wait_time = min(10 * (attempt + 1), 30)
                    logger.warning(f"⏳ Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                if response.status_code != 200:
                    logger.warning(f"⚠️  HTTP {response.status_code} for {endpoint}")
                    time.sleep(3)
                    continue
                    
                # Соблюдаем rate limit: 1 запрос в секунду
                time.sleep(1.0)
                
                return response.json()
                
            except Exception as e:
                logger.warning(f"  Attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(3)
        
        logger.error(f"❌ Failed to get data from {endpoint}")
        return None
            
    def import_from_anilist_popular(self, max_items=500):
        """Импорт популярных аниме из AniList"""
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
        
        return self.import_from_anilist_query(query, max_items, "POPULAR")

    def import_from_anilist_score(self, max_items=500):
        """Импорт аниме с высоким рейтингом из AniList"""
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                }
                media(type: ANIME, sort: SCORE_DESC) {
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
        
        return self.import_from_anilist_query(query, max_items, "HIGH SCORE")

    def import_from_anilist_query(self, query, max_items, source_name):
        """Общий метод для импорта из AniList по запросу"""
        self.log_section(f"ANILIST {source_name} - {max_items} anime")
        
        count = 0
        page = 1
        per_page = 50
        batch_size = self.max_workers * 2
        
        while count < max_items:
            variables = {'page': page, 'perPage': per_page}
            data = self.make_anilist_request(query, variables)
            
            if not data or 'data' not in data:
                break
            
            media_list = data['data']['Page']['media']
            
            # Обрабатываем батчами
            for i in range(0, len(media_list), batch_size):
                batch = media_list[i:i+batch_size]
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    
                    for media in batch:
                        if count >= max_items:
                            break
                        
                        anilist_id = media.get('id')
                        if anilist_id in self.processed_ids:
                            continue
                        
                        self.processed_ids.add(anilist_id)
                        future = executor.submit(self.process_anilist_media, media)
                        futures.append(future)
                    
                    for future in as_completed(futures):
                        try:
                            if future.result(timeout=30):
                                count += 1
                                
                                if count % 20 == 0:
                                    logger.info(f"📊 {source_name}: {count}/{max_items}")
                        except Exception as e:
                            logger.error(f"Error: {e}")
            
            if count >= max_items:
                break
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next:
                break
            
            page += 1
        
        logger.info(f"✅ AniList {source_name}: {count} anime imported\n")
        return count

    def import_from_anilist_trending(self, max_items=1000):
        """Параллельный импорт из AniList"""
        self.log_section(f"STAGE 1: ANILIST TRENDING (PARALLEL) - {max_items} anime")
        
        count = 0
        page = 1
        per_page = 50  # Максимум 50 на страницу
        batch_size = min(self.max_workers * 3, 30)  # Больше потоков
        
        logger.info(f"⚡ Using {batch_size} parallel threads")
        
        all_media = []  # Собираем все аниме сначала
        
        # Сначала собираем все данные
        while len(all_media) < max_items:
            logger.info(f"📥 Fetching page {page}...")
            
            variables = {'page': page, 'perPage': per_page}
            data = self.make_anilist_request(self.ANILIST_TRENDING_QUERY, variables)
            
            if not data or 'data' not in data or not data['data']['Page']['media']:
                logger.warning(f"⚠️  No more data from AniList")
                break
            
            media_list = data['data']['Page']['media']
            all_media.extend(media_list)
            
            logger.info(f"📊 Collected: {len(all_media)}/{max_items} anime")
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next or len(all_media) >= max_items:
                break
            
            page += 1
        
        # Обрезаем до нужного количества
        all_media = all_media[:max_items]
        logger.info(f"✅ Total collected: {len(all_media)} anime for processing")
        
        # Параллельная обработка
        processed_count = 0
        
        for i in range(0, len(all_media), batch_size):
            batch = all_media[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_media) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} anime)")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for media in batch:
                    anilist_id = media.get('id')
                    if anilist_id in self.processed_ids:
                        continue
                    
                    self.processed_ids.add(anilist_id)
                    
                    future = executor.submit(self.process_anilist_media, media)
                    futures.append(future)
                
                # Собираем результаты
                for future in as_completed(futures):
                    try:
                        if future.result(timeout=45):
                            processed_count += 1
                            count += 1
                            
                            if count % 50 == 0:
                                logger.info(f"📊 Progress: {count}/{len(all_media)} anime processed")
                    except Exception as e:
                        logger.error(f"❌ Error in thread: {e}")
        
        logger.info(f"✅ AniList Trending: {count} anime imported\n")
        return count

    def process_anilist_media(self, media):
        """Обрабатывает одно аниме из AniList (вызывается в потоке)"""
        try:
            normalized = self.normalize_anilist_anime(media)
            if normalized:
                return self.save_anime_fast(normalized)
        except Exception as e:
            logger.debug(f"Error processing anime: {e}")
        return False
        
    def run_import(self):
        """Полный импорт большого объема"""
        self.log_header("🚀 MASS ANIME IMPORT - STARTING")
        
        logger.info(f"🎯 Target: {self.max_anime:,} anime")
        logger.info(f"🖼️  Images: {'Yes' if not self.skip_images else 'No'}")
        logger.info(f"⚡ Mode: {'Fast' if self.fast_mode else 'Normal'}")
        logger.info(f"🧵 Workers: {self.max_workers}")
        logger.info("")
        
        start_time = time.time()
        total_imported = 0
        
        # Стратегия: сначала AniList (быстро и много), потом Jikan
        
        # 1. AniList Trending - 1000 аниме
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(1000, remaining)
            logger.info(f"📥 Phase 1: AniList Trending ({to_import} anime)")
            imported = self.import_from_anilist_trending(max_items=to_import)
            total_imported += imported
        
        # 2. AniList Popular - 500 аниме
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(500, remaining)
            logger.info(f"📥 Phase 2: AniList Popular ({to_import} anime)")
            imported = self.import_from_anilist_popular(max_items=to_import)
            total_imported += imported
        
        # 3. AniList High Score - 500 аниме
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(500, remaining)
            logger.info(f"📥 Phase 3: AniList High Score ({to_import} anime)")
            imported = self.import_from_anilist_score(max_items=to_import)
            total_imported += imported
        
        # 4. Jikan - оставшиеся (медленно)
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(500, remaining)
            logger.info(f"📥 Phase 4: Jikan Top ({to_import} anime - slow)")
            imported = self.import_from_jikan_top(max_items=to_import)
            total_imported += imported
        
        # Статистика
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        self.log_header("🎉 IMPORT COMPLETED!")
        
        logger.info("📊 EXECUTION STATISTICS:")
        logger.info(f"  Total Imported: {total_imported:,}")
        logger.info(f"  Newly Saved: {self.total_saved:,}")
        logger.info(f"  Updated: {self.total_updated:,}")
        logger.info(f"  Skipped: {self.total_skipped:,}")
        logger.info(f"  Failed: {self.total_failed:,}")
        logger.info(f"  Execution Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        logger.info(f"  Average time per anime: {elapsed_time/max(1, total_imported):.1f}s")
        
        # Детальная статистика
        self.log_consolidated_summary()
        
        logger.info("\n" + "="*100)
        logger.info(f"✅ SUCCESS! Imported {total_imported:,} anime in {hours}h {minutes}m {seconds}s")
        logger.info("="*100 + "\n")

    def save_anime_fast(self, anime_data):
        """Быстрое сохранение аниме (оптимизированное)"""
        try:
            title_ru = anime_data.get('title_ru')
            if not title_ru:
                return False
            
            # Быстрая проверка существования
            existing = Anime.objects.filter(title_ru=title_ru).only('id', 'poster', 'poster_url').first()
            
            # Быстрое скачивание постера
            poster_file = None
            poster_url = anime_data.get('poster_url')
            
            if not self.skip_images and poster_url:
                unique_id = anime_data.get('mal_id') or anime_data.get('anilist_id') or ''
                filename = self.clean_filename(title_ru)
                filename = f"{filename}_{unique_id}.jpg"
                
                filepath = f'backend/media/anime_posters/{filename}'
                
                if not os.path.exists(filepath):
                    # Быстрое скачивание (только прямой метод)
                    poster_file = self.download_image_fast(poster_url, filename)
                else:
                    poster_file = f'anime_posters/{filename}'
            
            if existing:
                updated = False
                
                # Только самые важные обновления
                if poster_file and not existing.poster:
                    existing.poster = poster_file
                    updated = True
                
                if poster_url and existing.poster_url != poster_url:
                    existing.poster_url = poster_url
                    updated = True
                
                if updated:
                    existing.save()
                    self.total_updated += 1
                else:
                    self.total_skipped += 1
                    
                return updated
            else:
                Anime.objects.create(
                    title_ru=anime_data['title_ru'],
                    title_en=anime_data['title_en'],
                    title_jp=anime_data['title_jp'],
                    description=anime_data['description'][:2000] if anime_data['description'] else '',
                    year=anime_data['year'],
                    status=anime_data['status'],
                    kind=anime_data['kind'],
                    episodes=anime_data['episodes'],
                    score=anime_data['score'],
                    poster_url=anime_data['poster_url'],
                    poster=poster_file,
                    genres=anime_data['genres'][:5],
                    studios=anime_data['studios'][:3],
                    data_source=anime_data['data_source']
                )
                self.total_saved += 1
                return True
                
        except Exception as e:
            self.total_failed += 1
            logger.debug(f"Fast save error: {e}")
            return False

    def download_image_fast(self, url, filename):
        """Быстрое скачивание (без сложных проверок)"""
        if not url or 'myanimelist.net' in url:
            return None  # Пропускаем MyAnimeList в России
        
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                filepath = f'backend/media/anime_posters/{filename}'
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return f'anime_posters/{filename}'
        except:
            pass
        return None

def main():
    parser = argparse.ArgumentParser(description='Verbose anime importer with detailed output')
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
        importer = VerboseAnimeImporter(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            max_workers=args.workers
        )
        importer.run_import()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Import interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
