"""
Полный импорт всех аниме из Kodik API.

Обновляет существующие аниме (по shikimori_id) или создаёт новые.

Запуск: python backend/full_import_from_kodik.py
"""

import os
import sys
import requests
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime, Genre, Studio
from django.db import transaction

KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'
KODIK_API_BASE = 'https://kodik-api.com'


def fetch_all_anime_from_kodik():
    """Загружает ВСЕ аниме из Kodik API через /list endpoint."""
    all_anime = []
    
    print("📥 Загрузка аниме из Kodik API (endpoint /list)...")
    
    # Первый запрос
    url = f'{KODIK_API_BASE}/list'
    params = {
        'token': KODIK_TOKEN,
        'limit': 100,
        'types': 'anime,anime-serial',
        'with_material_data': 'true',
    }
    
    page = 1
    while True:
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break
            
            all_anime.extend(results)
            total = data.get('total', 0)
            
            print(f"  Страница {page}: загружено {len(all_anime)}/{total} аниме")
            
            # Проверяем есть ли следующая страница
            next_page = data.get('next_page')
            if not next_page:
                break
            
            # Используем next_page URL для следующего запроса
            url = next_page
            params = {}  # Параметры уже в URL
            page += 1
            time.sleep(0.2)  # Rate limiting
            
        except requests.exceptions.HTTPError as e:
            print(f"  ❌ HTTP ошибка на странице {page}: {e}")
            print(f"  Response: {e.response.text[:500] if e.response.text else 'No content'}")
            break
        except Exception as e:
            print(f"  ❌ Ошибка на странице {page}: {e}")
            break
    
    print(f"✅ Всего загружено {len(all_anime)} аниме")
    return all_anime


def map_status(kodik_status):
    """Маппинг статусов Kodik в нашу систему."""
    status_map = {
        'ongoing': 'ongoing',
        'released': 'finished',
        'anons': 'announced',
        'canceled': 'canceled',
    }
    return status_map.get(kodik_status, 'finished')


def map_kind(kodik_kind):
    """Маппинг типов Kodik."""
    kind_map = {
        'tv': 'tv',
        'tv_13': 'tv',
        'tv_24': 'tv',
        'tv_48': 'tv',
        'movie': 'movie',
        'ova': 'ova',
        'ona': 'ona',
        'special': 'special',
        'music': 'music',
    }
    return kind_map.get(kodik_kind, 'tv')


def get_or_create_genre(name):
    """Получает или создаёт жанр."""
    genre, _ = Genre.objects.get_or_create(
        name=name,
        defaults={'slug': name.lower().replace(' ', '-')}
    )
    return genre


def get_or_create_studio(name):
    """Получает или создаёт студию."""
    studio, _ = Studio.objects.get_or_create(
        name=name,
        defaults={'slug': name.lower().replace(' ', '-')}
    )
    return studio


def import_anime_from_kodik_data(kodik_data):
    """Импортирует одно аниме из Kodik данных."""
    try:
        material_data = kodik_data.get('material_data', {})
        
        if not material_data:
            return None
        
        # Получаем shikimori_id
        shikimori_id = kodik_data.get('shikimori_id')
        if not shikimori_id:
            return None
        
        shikimori_id = int(shikimori_id)
        
        # Основные данные
        title_ru = material_data.get('anime_title') or material_data.get('title') or ''
        title_en = material_data.get('title_en') or ''
        title_jp = material_data.get('other_titles', [''])[0] if isinstance(material_data.get('other_titles'), list) else ''
        
        year = None
        if material_data.get('year'):
            try:
                year = int(material_data.get('year'))
            except (ValueError, TypeError):
                pass
        
        status = map_status(material_data.get('anime_status') or material_data.get('all_status'))
        kind = map_kind(material_data.get('anime_kind'))
        
        episodes = material_data.get('episodes_total') or material_data.get('episodes_aired')
        if episodes:
            try:
                episodes = int(episodes)
            except (ValueError, TypeError):
                episodes = None
        
        score = None
        if material_data.get('shikimori_rating'):
            try:
                score = float(material_data.get('shikimori_rating'))
            except (ValueError, TypeError):
                pass
        
        poster_url = material_data.get('anime_poster_url') or material_data.get('poster_url') or ''
        description = material_data.get('anime_description') or material_data.get('description') or ''
        
        genres = material_data.get('anime_genres') or material_data.get('all_genres') or []
        studios = material_data.get('anime_studios') or []
        
        mal_id = None
        if material_data.get('mal_id'):
            try:
                mal_id = int(material_data.get('mal_id'))
            except (ValueError, TypeError):
                pass
        
        # Получаем или создаём аниме
        with transaction.atomic():
            anime, created = Anime.objects.update_or_create(
                shikimori_id=shikimori_id,
                defaults={
                    'title_ru': title_ru,
                    'title_en': title_en,
                    'title_jp': title_jp,
                    'description': description,
                    'year': year,
                    'status': status,
                    'kind': kind,
                    'episodes': episodes,
                    'score': score,
                    'poster_url': poster_url,
                    'genres': genres if isinstance(genres, list) else [],
                    'studios': studios if isinstance(studios, list) else [],
                    'mal_id': mal_id,
                    'data_source': 'kodik',
                }
            )
            
            # Обновляем kodik_id и kodik_link если есть
            if kodik_data.get('id'):
                anime.kodik_id = kodik_data.get('id')
            if kodik_data.get('link'):
                anime.kodik_link = kodik_data.get('link')
            anime.save(update_fields=['kodik_id', 'kodik_link'])
        
        return {
            'shikimori_id': shikimori_id,
            'title': title_ru or title_en,
            'created': created,
        }
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Error importing anime {kodik_data.get("shikimori_id")}: {e}')
        return None


def main():
    print("=" * 60)
    print("ПОЛНЫЙ ИМПОРТ АНИМЕ ИЗ KODIK")
    print("=" * 60)
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Загружаем все аниме из Kodik
    all_kodik_anime = fetch_all_anime_from_kodik()
    
    if not all_kodik_anime:
        print("❌ Не удалось загрузить данные из Kodik")
        return
    
    print()
    print("🔄 Импорт в базу данных...")
    print()
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    for i, kodik_data in enumerate(all_kodik_anime, 1):
        result = import_anime_from_kodik_data(kodik_data)
        
        if result is None:
            error_count += 1
        elif result['created']:
            created_count += 1
        else:
            updated_count += 1
        
        # Прогресс каждые 1000
        if i % 1000 == 0:
            print(f"  Обработано {i}/{len(all_kodik_anime)} (создано: {created_count}, обновлено: {updated_count}, ошибок: {error_count})")
        
        # Rate limiting
        if i % 100 == 0:
            time.sleep(0.1)
    
    print()
    print("=" * 60)
    print("✅ ИМПОРТ ЗАВЕРШЁН")
    print("=" * 60)
    print(f"Всего обработано: {len(all_kodik_anime)}")
    print(f"  Создано: {created_count}")
    print(f"  Обновлено: {updated_count}")
    print(f"  Ошибок: {error_count}")
    print()
    print(f"Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверка Frieren
    print()
    print("🔍 Проверка Frieren (shikimori_id=59978)...")
    try:
        frieren = Anime.objects.get(shikimori_id=59978)
        print(f"✅ Frieren найден!")
        print(f"  title_ru: {frieren.title_ru}")
        print(f"  year: {frieren.year}")
        print(f"  status: {frieren.status}")
        print(f"  poster_url: {frieren.poster_url[:50]}...")
    except Anime.DoesNotExist:
        print(f"❌ Frieren НЕ найден в Kodik API (возможно ещё не добавлен)")


if __name__ == '__main__':
    main()
