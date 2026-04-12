"""
Скрипт для исправления названий аниме-анонсов через Kodik API.

Проблема: При импорте анонсов некоторые существующие аниме были обновлены
неправильными данными (название на английском вместо русского).

Логика исправления:
- Если poster_url содержит "shikimori" (значит данные из Shikimori)
- И название НЕ на русском
- ТО обновляем данные из Kodik API

НЕ обновляем если:
- poster_url НЕ содержит "shikimori" → пропускаем
- название на русском → пропускаем

Обновляемые поля:
- title_ru, title_en
- year
- status
- description
- genres
- studios
- mal_id
- release_date

НЕ обновляем:
- poster_url, poster (файл)

Запуск: python backend/fix_announcement_titles.py
"""

import os
import sys
import re
import requests
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime

# Kodik API токен
KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'


def is_russian(text):
    """Проверяет, содержит ли текст русские буквы."""
    if not text:
        return False
    return bool(re.search('[а-яА-ЯёЁ]', text))


def is_shikimori_poster(poster_url):
    """Проверяет, является ли постер от Shikimori."""
    if not poster_url:
        return False
    return 'shikimori' in poster_url.lower()


def fetch_kodik_data(shikimori_id):
    """Получает данные из Kodik API по shikimori_id."""
    try:
        url = f'https://kodik-api.com/search'
        params = {
            'token': KODIK_TOKEN,
            'shikimori_id': shikimori_id,
            'types': 'anime,anime-serial',
            'with_material_data': 'true',
            'limit': 1
        }
        
        response = requests.get(url, params=params, headers={'User-Agent': 'Anisphere/1.0'})
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return None
            
            # Берём первый результат
            result = results[0]
            material_data = result.get('material_data', {})
            
            if not material_data:
                return None
            
            # Парсим release_date
            release_date = None
            if material_data.get('aired_at'):
                try:
                    release_date = datetime.strptime(material_data['aired_at'], '%Y-%m-%d').date()
                except:
                    pass
            
            return {
                'title_ru': material_data.get('anime_title') or material_data.get('title') or '',
                'title_en': material_data.get('title_en') or '',
                'year': int(material_data.get('year')) if material_data.get('year') else None,
                'status': map_status(material_data.get('anime_status') or material_data.get('all_status')),
                'description': material_data.get('anime_description') or material_data.get('description') or '',
                'genres': material_data.get('anime_genres') or material_data.get('all_genres') or [],
                'studios': material_data.get('anime_studios') or [],
                'mal_id': int(material_data.get('mal_id')) if material_data.get('mal_id') else None,
                'release_date': release_date,
            }
        else:
            return None
    except Exception as e:
        print(f"  ❌ Ошибка запроса к Kodik: {e}")
        return None


def map_status(kodik_status):
    """Маппинг статусов Kodik в нашу БД."""
    status_map = {
        'ongoing': 'ongoing',
        'released': 'finished',
        'anons': 'announced',
        'canceled': 'canceled',
    }
    return status_map.get(kodik_status, 'finished')


def fix_anime_titles():
    """Исправляет названия аниме с некорректными данными."""
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ НАЗВАНИЙ АНИМЕ-АНОНСОВ (через Kodik API)")
    print("=" * 60)
    
    # Находим ВСЕ аниме (без фильтра по году)
    all_anime = list(Anime.objects.all().order_by('-id'))
    
    print(f"Всего аниме в БД: {len(all_anime)}")
    
    # Фильтруем: poster_url содержит "shikimori" И название НЕ на русском
    to_fix = []
    skipped_russian = 0
    skipped_not_shikimori = 0
    
    for anime in all_anime:
        if not is_shikimori_poster(anime.poster_url):
            skipped_not_shikimori += 1
            continue
        
        if is_russian(anime.title_ru):
            skipped_russian += 1
            continue
        
        to_fix.append(anime)
    
    print(f"Пропущено (не shikimori постер): {skipped_not_shikimori}")
    print(f"Пропущено (название на русском): {skipped_russian}")
    print(f"Требуют исправления: {len(to_fix)}")
    print()
    
    if not to_fix:
        print("✅ Все названия корректны!")
        return
    
    fixed_count = 0
    error_count = 0
    skip_count = 0
    not_found_count = 0
    
    for i, anime in enumerate(to_fix, 1):
        print(f"[{i}/{len(to_fix)}] ID:{anime.id} | Shikimori:{anime.shikimori_id or 'N/A'}")
        print(f"  Было: {anime.title_ru[:60]} ({anime.year})")
        print(f"  Poster: {anime.poster_url[:70]}...")
        
        # Пробуем получить shikimori_id из БД или из poster_url
        shikimori_id = anime.shikimori_id
        
        # Если нет shikimori_id в БД, пробуем извлечь из poster_url
        if not shikimori_id and anime.poster_url:
            match = re.search(r'/animes/(\d+)', anime.poster_url)
            if match:
                shikimori_id = int(match.group(1))
                print(f"  Извлечён shikimori_id из poster_url: {shikimori_id}")
        
        if not shikimori_id:
            print(f"  ⚠️ Пропущено: нет shikimori_id")
            skip_count += 1
            continue
        
        # Получаем данные из Kodik
        data = fetch_kodik_data(shikimori_id)
        
        if data and data['title_ru']:
            # Проверяем, что новое название на русском
            if is_russian(data['title_ru']):
                # Обновляем данные
                anime.title_ru = data['title_ru'][:255]
                anime.title_en = data['title_en'][:255] if data['title_en'] else anime.title_en
                anime.year = data['year']
                anime.status = data['status']
                if data['description']:
                    anime.description = data['description']
                if data['genres']:
                    anime.genres = data['genres']
                if data['studios']:
                    anime.studios = data['studios']
                if data['mal_id']:
                    anime.mal_id = data['mal_id']
                if data['release_date']:
                    anime.release_date = data['release_date']
                
                anime.save(update_fields=[
                    'title_ru', 'title_en', 'year', 'status',
                    'description', 'genres', 'studios', 'mal_id', 'release_date', 'updated_at'
                ])
                
                print(f"  ✅ Исправлено: {data['title_ru'][:60]} ({data['year']})")
                fixed_count += 1
            else:
                print(f"  ⚠️ Пропущено: название из Kodik тоже не на русском: '{data['title_ru']}'")
                skip_count += 1
        else:
            print(f"  ❌ Не найдено в Kodik")
            not_found_count += 1
        
        # Задержка чтобы не спамить API
        if i % 5 == 0:
            time.sleep(0.3)
        
        print()
    
    print("=" * 60)
    print(f"ГОТОВО!")
    print(f"Исправлено: {fixed_count}")
    print(f"Не найдено в Kodik: {not_found_count}")
    print(f"Пропущено (нет shikimori_id): {skip_count}")
    print(f"Ошибок: {error_count}")
    print("=" * 60)
    
    return fixed_count, error_count, skip_count


if __name__ == '__main__':
    fix_anime_titles()
