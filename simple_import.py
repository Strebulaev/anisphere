#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

# GraphQL запрос
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

def clean_description(text):
    import re
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\\n', ' ').replace('\\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_anime(anime_data):
    title = anime_data.get('title', {})
    title_en = title.get('english') or title.get('romaji') or ''
    title_jp = title.get('native') or ''
    title_ru = title_en
    
    description = clean_description(anime_data.get('description', '') or '')
    
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

def download_image(url, filename):
    if not url or 'myanimelist.net' in url:
        return None
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            filepath = f'backend/media/anime_posters/{filename}'
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return f'anime_posters/{filename}'
    except:
        pass
    return None

def clean_filename(title):
    import re
    if not title:
        return 'unknown'
    filename = re.sub(r'[^\w\s-]', '', str(title)).strip()
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename[:50] or 'unknown'

print("="*80)
print("SIMPLE ANIME IMPORTER")
print("="*80)
print("Target: 20 anime")
print("Images: Yes")
print("="*80)
print()

total_imported = 0
page = 1
per_page = 20

os.makedirs('backend/media/anime_posters', exist_ok=True)

while total_imported < 20:
    print(f"Fetching page {page}...")
    
    try:
        response = requests.post(
            'https://graphql.anilist.co',
            json={'query': query, 'variables': {'page': page, 'perPage': per_page}},
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            timeout=60
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  Error: HTTP {response.status_code}")
            break
        
        data = response.json()
        
        if 'data' not in data:
            print("  Error: No 'data' in response")
            break
        
        media_list = data['data']['Page']['media']
        print(f"  Found: {len(media_list)} anime")
        
        for media in media_list:
            if total_imported >= 20:
                break
            
            normalized = normalize_anime(media)
            if not normalized:
                continue
            
            # Download poster
            poster_file = None
            poster_url = normalized['poster_url']
            if poster_url:
                filename = f"{clean_filename(normalized['title_ru'])}_{media['id']}.jpg"
                poster_file = download_image(poster_url, filename)
                if poster_file:
                    print(f"    Downloaded poster: {filename}")
            
            # Save to DB
            anime, created = Anime.objects.get_or_create(
                title_ru=normalized['title_ru'],
                defaults={
                    'title_en': normalized['title_en'],
                    'title_jp': normalized['title_jp'],
                    'description': normalized['description'],
                    'year': normalized['year'],
                    'status': normalized['status'],
                    'kind': normalized['kind'],
                    'episodes': normalized['episodes'],
                    'score': normalized['score'],
                    'poster_url': normalized['poster_url'],
                    'poster': poster_file,
                    'genres': normalized['genres'],
                    'studios': normalized['studios'],
                    'data_source': normalized['data_source']
                }
            )
            
            if created:
                print(f"  [{total_imported+1:2d}] NEW: {normalized['title_ru'][:50]}")
                total_imported += 1
            else:
                print(f"  [SKIP] Already exists: {normalized['title_ru'][:50]}")
        
        if total_imported >= 20:
            break
        
        has_next = data['data']['Page']['pageInfo'].get('hasNextPage', False)
        if not has_next:
            print("  No more pages")
            break
        
        page += 1
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        break

print()
print("="*80)
print(f"IMPORT COMPLETED: {total_imported} anime")
print("="*80)

# Show statistics
total = Anime.objects.count()
with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()

print(f"Total in DB: {total}")
print(f"With posters: {with_posters}")
print()

# Show examples
print("Examples:")
for anime in Anime.objects.all()[:5]:
    poster = "[X]" if anime.poster else "[ ]"
    print(f"  {poster} {anime.title_ru[:40]}")
    print(f"      Year: {anime.year}, Episodes: {anime.episodes}, Score: {anime.score}")
    print()
