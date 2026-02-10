#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный импортёр аниме с обходом блокировок
Использует Jikan API, AniList GraphQL API и Shikimori API
Работает с обходом блокировок в РФ
"""
import os
import sys
import django
import requests
import time
import re
import argparse
import socket
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime


class AnimeImporterWithBypass:
    """Импортёр с обходом блокировок"""
    
    JIKAN_API = "https://api.jikan.moe/v4"
    ANILIST_API = "https://graphql.anilist.co"
    SHIKIMORI_API = "https://shikimori.one/api"
    
    # DNS серверы для обхода
    DNS_SERVERS = [
        ('8.8.8.8', 53),    # Google DNS
        ('1.1.1.1', 53),    # Cloudflare DNS
        ('77.88.8.8', 53),  # Yandex DNS
    ]
    
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
    
    def __init__(self, max_anime=20000, skip_images=False, fast_mode=False, max_workers=5):
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
        
        os.makedirs('backend/media/anime_posters', exist_ok=True)
        
        print("="*80)
        print(f"Initialized AnimeImporterWithBypass: max_anime={max_anime}")
        print("="*80)
    
    def resolve_hostname(self, hostname):
        """Разрешает hostname через альтернативные DNS"""
        for dns_ip, dns_port in self.DNS_SERVERS:
            try:
                result = socket.getaddrinfo(hostname, 443, family=socket.AF_INET)
                if result:
                    ip = result[0][4][0]
                    return ip
            except:
                continue
        return None
    
    def make_request_with_bypass(self, url, method='GET', json_data=None, timeout=30):
        """Выполняет запрос с обходом блокировок"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        if method == 'POST':
            headers['Content-Type'] = 'application/json'
        
        # Метод 1: Прямой запрос
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=timeout)
            else:
                response = self.session.post(url, json=json_data, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
        
        # Метод 2: С другим User-Agent
        try:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=timeout)
            else:
                response = self.session.post(url, json=json_data, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
        
        return None
    
    def download_image_with_bypass(self, url, filename):
        """Скачивает изображение с обходом блокировок"""
        if self.skip_images or not url:
            return None
        
        # Пропускаем MyAnimeList
        if 'myanimelist.net' in url:
            return None
        
        # Методы для скачивания
        methods = [
            {'name': 'Direct', 'timeout': 10},
            {'name': 'Long timeout', 'timeout': 30},
            {'name': 'With headers', 'timeout': 15, 'headers': {'Referer': 'https://anilist.co/'}},
        ]
        
        for method in methods:
            try:
                headers = method.get('headers', {})
                headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                })
                
                response = self.session.get(url, headers=headers, timeout=method['timeout'])
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type:
                        continue
                    
                    filepath = f'backend/media/anime_posters/{filename}'
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"    Downloaded via {method['name']}: {filename}")
                    return f'anime_posters/{filename}'
                    
            except Exception as e:
                continue
        
        return None
    
    def make_anilist_request(self, query, variables=None):
        """Выполняет GraphQL запрос к AniList"""
        return self.make_request_with_bypass(
            self.ANILIST_API,
            method='POST',
            json_data={'query': query, 'variables': variables or {}},
            timeout=60
        )
    
    def clean_filename(self, title):
        """Очищает название для файла"""
        if not title:
            return 'unknown'
        filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename[:50] or 'unknown'
    
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
            description = re.sub(r'<[^>]+>', '', description)
            description = description.replace('\\n', ' ').replace('\\r', ' ')
            description = re.sub(r'\s+', ' ', description).strip()
            
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
                
                if os.path.exists(filepath):
                    poster_file = f'anime_posters/{filename}'
                else:
                    poster_file = self.download_image_with_bypass(poster_url, filename)
            
            if existing:
                updated = False
                
                if poster_file and not existing.poster:
                    existing.poster = poster_file
                    updated = True
                
                if existing.poster_url != poster_url and poster_url:
                    existing.poster_url = poster_url
                    updated = True
                
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
                else:
                    self.total_skipped += 1
            else:
                Anime.objects.create(
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
    
    def import_from_anilist(self, sort_by, max_items):
        """Импорт из AniList с заданной сортировкой"""
        print("="*80)
        print(f"AniList {sort_by} - {max_items} anime")
        print("="*80)
        
        query = f'''
        query ($page: Int, $perPage: Int) {{
            Page(page: $page, perPage: $perPage) {{
                pageInfo {{
                    hasNextPage
                }}
                media(type: ANIME, sort: {sort_by}) {{
                    id
                    title {{
                        romaji
                        english
                        native
                    }}
                    description
                    startDate {{
                        year
                    }}
                    status
                    format
                    episodes
                    meanScore
                    coverImage {{
                        large
                        medium
                    }}
                    genres
                    studios {{
                        nodes {{
                            name
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            print(f"Fetching page {page}...")
            
            data = self.make_anilist_request(query, {'page': page, 'perPage': per_page})
            
            if not data or 'data' not in data or not data['data']['Page']['media']:
                print("No more data from AniList")
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
                
                if count % 20 == 0:
                    print(f"Progress: {count}/{max_items} anime imported")
            
            if count >= max_items:
                break
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next:
                break
            
            page += 1
            
            # Пауза для rate limit
            time.sleep(0.5)
        
        print(f"AniList {sort_by}: {count} anime imported\n")
        return count
    
    def import_from_anilist_unlimited(self, sort_by):
        """Импорт ВСЕХ доступных аниме из AniList с заданной сортировкой"""
        print("="*80)
        print(f"AniList {sort_by} - UNLIMITED import")
        print("="*80)
        
        query = f'''
        query ($page: Int, $perPage: Int) {{
            Page(page: $page, perPage: $perPage) {{
                pageInfo {{
                    hasNextPage
                    currentPage
                    lastPage
                }}
                media(type: ANIME, sort: {sort_by}) {{
                    id
                    title {{
                        romaji
                        english
                        native
                    }}
                    description
                    startDate {{
                        year
                    }}
                    status
                    format
                    episodes
                    meanScore
                    coverImage {{
                        large
                        medium
                    }}
                    genres
                    studios {{
                        nodes {{
                            name
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        count = 0
        page = 1
        per_page = 50
        total_pages = None
        last_report = 0
        
        while True:
            print(f"Fetching page {page}...", end='\r')
            
            data = self.make_anilist_request(query, {'page': page, 'perPage': per_page})
            
            if not data or 'data' not in data:
                print("\nNo more data from AniList")
                break
            
            page_info = data['data']['Page']['pageInfo']
            media_list = data['data']['Page']['media']
            
            if not media_list:
                print("\nNo anime on this page, stopping")
                break
            
            # Получаем информацию о страницах
            has_next = page_info.get('hasNextPage', False)
            current_page = page_info.get('currentPage', page)
            last_page = page_info.get('lastPage', None)
            
            if last_page and not total_pages:
                total_pages = last_page
                print(f"\nTotal pages available: {total_pages}")
            
            # Обрабатываем аниме
            page_new_count = 0
            for media in media_list:
                anilist_id = media.get('id')
                if anilist_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(anilist_id)
                
                normalized = self.normalize_anilist_anime(media)
                if normalized:
                    self.save_anime(normalized)
                    count += 1
                    page_new_count += 1
            
            # Отчёты каждые 100 аниме
            if count - last_report >= 100 or not has_next:
                print(f"Page {current_page}/{last_page or '?'}: +{page_new_count} new (total: {count} processed)")
                last_report = count
            
            # Проверяем следующую страницу
            if not has_next:
                print(f"\nReached last page for {sort_by}")
                break
            
            page += 1
            
            # Пауза для rate limit
            time.sleep(0.3)
        
        print(f"\nAniList {sort_by}: {count} anime imported\n")
        return count
    
    def import_from_anilist_by_year(self, year, sort_by='SCORE_DESC'):
        """Импорт аниме за определённый год"""
        print("="*80)
        print(f"AniList {year} - {sort_by}")
        print("="*80)
        
        query = f'''
        query ($page: Int, $perPage: Int, $year: Int) {{
            Page(page: $page, perPage: $perPage) {{
                pageInfo {{
                    hasNextPage
                }}
                media(type: ANIME, sort: {sort_by}, startDate: {{year: $year}}) {{
                    id
                    title {{
                        romaji
                        english
                        native
                    }}
                    description
                    startDate {{
                        year
                    }}
                    status
                    format
                    episodes
                    meanScore
                    coverImage {{
                        large
                        medium
                    }}
                    genres
                    studios {{
                        nodes {{
                            name
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        count = 0
        page = 1
        per_page = 50
        
        while True:
            print(f"  Year {year} - Page {page}...", end='\r')
            
            data = self.make_anilist_request(query, {'page': page, 'perPage': per_page, 'year': year})
            
            if not data or 'data' not in data:
                break
            
            media_list = data['data']['Page']['media']
            
            if not media_list:
                break
            
            for media in media_list:
                anilist_id = media.get('id')
                if anilist_id in self.processed_ids:
                    continue
                
                self.processed_ids.add(anilist_id)
                
                normalized = self.normalize_anilist_anime(media)
                if normalized:
                    self.save_anime(normalized)
                    count += 1
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            
            if not has_next:
                break
            
            page += 1
            time.sleep(0.3)
        
        print(f"\n  Year {year}: {count} anime")
        return count
    
    def run_import(self):
        start_time = time.time()
        total_imported = 0

        # Фаза 1: Основные сортировки (без ограничений)
        print("\n" + "="*80)
        print("PHASE 1: MAIN SORTS (UNLIMITED)")
        print("="*80 + "\n")
        
        sorts = [
            'TRENDING_DESC',
            'POPULARITY_DESC', 
            'SCORE_DESC',
            'FAVOURITES_DESC',
        ]
        
        for sort_by in sorts:
            imported = self.import_from_anilist_unlimited(sort_by)
            total_imported += imported
            print(f"Running total: {total_imported} anime\n")
        
        # Фаза 2: По годам (последние 10 лет)
        print("\n" + "="*80)
        print("PHASE 2: BY YEAR (LAST 10 YEARS)")
        print("="*80 + "\n")
        
        current_year = 2024
        for year in range(current_year, current_year - 10, -1):
            imported = self.import_from_anilist_by_year(year, 'SCORE_DESC')
            total_imported += imported
            print(f"Running total: {total_imported} anime\n")
        
        # Фаза 3: По типам
        print("\n" + "="*80)
        print("PHASE 3: BY TYPE")
        print("="*80 + "\n")
        
        types_and_sorts = [
            ('TV', 'SCORE_DESC'),
            ('MOVIE', 'SCORE_DESC'),
            ('OVA', 'SCORE_DESC'),
            ('ONA', 'SCORE_DESC'),
        ]
        
        for media_type, sort_by in types_and_sorts:
            print(f"Importing {media_type} anime sorted by {sort_by}...")
            
            query = f'''
            query ($page: Int, $perPage: Int) {{
                Page(page: $page, perPage: $perPage) {{
                    pageInfo {{
                        hasNextPage
                    }}
                    media(type: ANIME, sort: {sort_by}, format: {media_type}) {{
                        id
                        title {{
                            romaji
                            english
                            native
                        }}
                        description
                        startDate {{
                            year
                        }}
                        status
                        format
                        episodes
                        meanScore
                        coverImage {{
                            large
                            medium
                        }}
                        genres
                        studios {{
                            nodes {{
                                name
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
            count = 0
            page = 1
            per_page = 50
            
            while True:
                print(f"  {media_type} - Page {page}...", end='\r')
                
                data = self.make_anilist_request(query, {'page': page, 'perPage': per_page})
                
                if not data or 'data' not in data:
                    break
                
                media_list = data['data']['Page']['media']
                
                if not media_list:
                    break
                
                for media in media_list:
                    anilist_id = media.get('id')
                    if anilist_id in self.processed_ids:
                        continue
                    
                    self.processed_ids.add(anilist_id)
                    
                    normalized = self.normalize_anilist_anime(media)
                    if normalized:
                        self.save_anime(normalized)
                        count += 1
                
                has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
                
                if not has_next:
                    break
                
                page += 1
                time.sleep(0.3)
            
            print(f"\n  {media_type}: {count} anime")
            total_imported += count
            print(f"Running total: {total_imported} anime\n")
        
        # Статистика
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        print("="*80)
        print("IMPORT COMPLETED!")
        print("="*80)
        print(f"Total Imported: {total_imported:,}")
        print(f"Newly Saved: {self.total_saved:,}")
        print(f"Updated: {self.total_updated:,}")
        print(f"Skipped: {self.total_skipped:,}")
        print(f"Failed: {self.total_failed:,}")
        print(f"Execution Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"Average time per anime: {elapsed_time/max(1, total_imported):.1f}s")
        
        # Финальная статистика
        total = Anime.objects.count()
        with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()
        
        print()
        print("="*80)
        print("DATABASE SUMMARY")
        print("="*80)
        print(f"Total Anime: {total:,}")
        if total > 0:
            print(f"With Posters: {with_posters:,} ({with_posters/total*100:.1f}%)")
        else:
            print(f"With Posters: {with_posters:,}")
        
        print()
        print("="*80)
        print(f"SUCCESS! Imported {total_imported:,} anime in {hours}h {minutes}m {seconds}s")
        print("="*80)
        print()
    
def main():
    parser = argparse.ArgumentParser(description='Anime importer with bypass - UNLIMITED mode')
    parser.add_argument('--max', type=int, default=None,
                       help='Maximum number of anime to import (default: unlimited)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of worker threads (default: 5)')
    
    args = parser.parse_args()
    
    try:
        # Если max не указан или 0, используем None для безлимитного режима
        max_anime = args.max if args.max and args.max > 0 else None
        
        importer = AnimeImporterWithBypass(
            max_anime=max_anime,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            max_workers=args.workers
        )
        importer.run_import()
    except KeyboardInterrupt:
        print("\n\nImport interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
