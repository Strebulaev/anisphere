 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправленный импортёр аниме - без эмодзи для Windows PowerShell
"""
import os
import sys
import django
import requests
import time
import re
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime


class AnimeImporter:
    """Импортёр без эмодзи"""
    
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
    
    def __init__(self, max_anime=100000, skip_images=False, fast_mode=False, max_workers=5):
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
        print(f"Initialized AnimeImporter: max_anime={max_anime}")
        print("="*80)
    
    def make_anilist_request(self, query, variables=None, max_retries=5):
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
                # Увеличиваем timeout и отключаем stream
                response = self.session.post(url, json=data, headers=headers, timeout=60, stream=False)
                
                if response.status_code == 429:
                    wait_time = 5 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # Сразу читаем ответ
                result = response.json()
                
                if not self.fast_mode:
                    time.sleep(0.3)
                else:
                    time.sleep(0.15)
                
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        print(f"Failed to get data from AniList")
        return None
    
    def download_image(self, url, filename):
        """Скачивает изображение"""
        if self.skip_images or not url:
            return None
        
        # Пропускаем MyAnimeList в России
        if 'myanimelist.net' in url:
            return None
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    return None
                
                filepath = f'backend/media/anime_posters/{filename}'
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return f'anime_posters/{filename}'
        except:
            pass
        
        return None
    
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
            
            # Очищаем описание от HTML тегов
            import re
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
                    poster_file = self.download_image(poster_url, filename)
            
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
    
    def import_from_anilist_trending(self, max_items=1000):
        """Импорт из AniList Trending"""
        print("="*80)
        print(f"AniList Trending - {max_items} anime")
        print("="*80)
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            print(f"Fetching page {page}...")
            
            variables = {'page': page, 'perPage': per_page}
            data = self.make_anilist_request(self.ANILIST_TRENDING_QUERY, variables)
            
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
                
                if count % 10 == 0:
                    print(f"Progress: {count}/{max_items} anime imported")
            
            if count >= max_items:
                break
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next:
                break
            
            page += 1
        
        print(f"AniList Trending: {count} anime imported\n")
        return count
    
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
        
        print("="*80)
        print(f"AniList Popular - {max_items} anime")
        print("="*80)
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            print(f"Fetching page {page}...")
            
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
                
                if count % 10 == 0:
                    print(f"Progress: {count}/{max_items} anime imported")
            
            if count >= max_items:
                break
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next:
                break
            
            page += 1
        
        print(f"AniList Popular: {count} anime imported\n")
        return count

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
        
        print("="*80)
        print(f"AniList High Score - {max_items} anime")
        print("="*80)
        
        count = 0
        page = 1
        per_page = 50
        
        while count < max_items:
            print(f"Fetching page {page}...")
            
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
                
                if count % 10 == 0:
                    print(f"Progress: {count}/{max_items} anime imported")
            
            if count >= max_items:
                break
            
            has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
            if not has_next:
                break
            
            page += 1
        
        print(f"AniList High Score: {count} anime imported\n")
        return count
    
    def run_import(self):
        """Полный импорт"""
        print("="*80)
        print("MASS ANIME IMPORT - STARTING")
        print("="*80)
        print(f"Target: {self.max_anime:,} anime")
        print(f"Images: {'Yes' if not self.skip_images else 'No'}")
        print(f"Mode: {'Fast' if self.fast_mode else 'Normal'}")
        print("")
        
        start_time = time.time()
        total_imported = 0
        
        # 1. AniList Trending
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(1000, remaining)
            print(f"Phase 1: AniList Trending ({to_import} anime)")
            imported = self.import_from_anilist_trending(max_items=to_import)
            total_imported += imported
        
        # 2. AniList Popular
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(500, remaining)
            print(f"Phase 2: AniList Popular ({to_import} anime)")
            imported = self.import_from_anilist_popular(max_items=to_import)
            total_imported += imported
        
        # 3. AniList High Score
        if total_imported < self.max_anime:
            remaining = self.max_anime - total_imported
            to_import = min(500, remaining)
            print(f"Phase 3: AniList High Score ({to_import} anime)")
            imported = self.import_from_anilist_score(max_items=to_import)
            total_imported += imported
        
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
        
        print("")
        print("="*80)
        print("DATABASE SUMMARY")
        print("="*80)
        print(f"Total Anime: {total:,}")
        if total > 0:
            print(f"With Posters: {with_posters:,} ({with_posters/total*100:.1f}%)")
        else:
            print(f"With Posters: {with_posters:,}")
        
        print("")
        print("="*80)
        print(f"SUCCESS! Imported {total_imported:,} anime in {hours}h {minutes}m {seconds}s")
        print("="*80)
        print("")
        
def main():
    parser = argparse.ArgumentParser(description='Anime importer')
    parser.add_argument('--max', type=int, default=100000,
                       help='Maximum number of anime to import (default: 100000)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of worker threads (default: 5)')
    
    args = parser.parse_args()
    
    try:
        importer = AnimeImporter(
            max_anime=args.max,
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
