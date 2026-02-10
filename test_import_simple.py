#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
import requests

print("Testing simple import...")
print("="*80)

# Test AniList
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

try:
    print("\nMaking AniList request...")
    response = requests.post(
        'https://graphql.anilist.co',
        json={'query': query, 'variables': {'page': 1, 'perPage': 5}},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] AniList response received")
        
        if 'data' in data:
            page_data = data['data']['Page']
            media_list = page_data['media']
            
            print(f"[OK] Found {len(media_list)} anime")
            
            for i, media in enumerate(media_list, 1):
                title = media['title']['english'] or media['title']['romaji']
                year = media.get('startDate', {}).get('year')
                episodes = media.get('episodes')
                score = media.get('meanScore')
                genres = media.get('genres', [])
                
                print(f"\n{i}. {title}")
                print(f"   Year: {year}, Episodes: {episodes}, Score: {score}")
                print(f"   Genres: {', '.join(genres[:3])}")
                
                # Save to DB
                title_en = media['title']['english'] or media['title']['romaji']
                title_jp = media['title']['native'] or ''
                description = media.get('description', '') or ''
                status = media.get('status', '').lower()
                status_map = {
                    'finished': 'finished',
                    'releasing': 'ongoing',
                    'not_yet_released': 'announced'
                }
                status = status_map.get(status, 'finished')
                
                media_type = media.get('format', '')
                type_map = {
                    'TV': 'tv',
                    'MOVIE': 'movie',
                    'OVA': 'ova',
                    'ONA': 'ona',
                    'SPECIAL': 'special',
                    'MUSIC': 'music'
                }
                kind = type_map.get(media_type, 'tv')
                
                poster_url = media.get('coverImage', {}).get('large') or media.get('coverImage', {}).get('medium') or ''
                
                studios = []
                for studio in media.get('studios', {}).get('nodes', []):
                    name = studio.get('name')
                    if name:
                        studios.append(name)
                
                anime, created = Anime.objects.get_or_create(
                    title_ru=title_en,
                    defaults={
                        'title_en': title_en,
                        'title_jp': title_jp,
                        'description': description[:5000] if description else '',
                        'year': year,
                        'status': status,
                        'kind': kind,
                        'episodes': episodes,
                        'score': score / 10.0 if score else None,
                        'poster_url': poster_url,
                        'genres': genres[:10],
                        'studios': studios[:5],
                        'data_source': 'anilist'
                    }
                )
                
                if created:
                    print(f"   [OK] Saved to DB")
                else:
                    print(f"   [SKIP] Already in DB")
        else:
            print("[ERROR] No 'data' in response")
            print(f"Response: {data}")
    else:
        print(f"[ERROR] AniList error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print(f"Total anime in DB: {Anime.objects.count()}")
print("="*80)
