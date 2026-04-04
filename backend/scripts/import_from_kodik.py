#!/usr/bin/env python
"""
Скрипт для импорта всех аниме из Kodik API
"""

import os
import sys
import django
import requests
import time
from typing import Dict, List, Any, Optional

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime, Genre, Studio

# Импортируем актуальные домены из единого конфига
from anime.kodik_config import KODIK_API_TOKEN, KODIK_API_BASE, normalize_kodik_player_link


def map_status(status: str) -> str:
    """Маппинг статусов из Kodik в нашу модель"""
    status_map = {
        'anons': 'announced',
        'ongoing': 'ongoing',
        'released': 'finished',
        'discontinued': 'canceled'
    }
    return status_map.get(status, 'finished')


def map_kind(kind: str) -> str:
    """Маппинг типов из Kodik в нашу модель"""
    kind_map = {
        'tv': 'tv',
        'tv_13': 'tv',
        'tv_24': 'tv',
        'tv_48': 'tv',
        'movie': 'movie',
        'ova': 'ova',
        'ona': 'ona',
        'special': 'special',
        'music': 'music'
    }
    return kind_map.get(kind, 'tv')


def get_genres(genre_names: List[str]) -> List[Genre]:
    """Получение или создание жанров"""
    genres = []
    for name in genre_names:
        genre, _ = Genre.objects.get_or_create(
            name=name,
            defaults={'slug': name.lower().replace(' ', '-')}
        )
        genres.append(genre)
    return genres


def get_studios(studio_names: List[str]) -> List[Studio]:
    """Получение или создание студий"""
    studios = []
    for name in studio_names:
        studio, _ = Studio.objects.get_or_create(
            name=name,
            defaults={'slug': name.lower().replace(' ', '-')}
        )
        studios.append(studio)
    return studios


def fetch_all_anime() -> List[Dict[str, Any]]:
    """Получение всех аниме из Kodik API"""
    all_anime = []
    next_page = None
    page = 0
    
    print("📥 Загрузка аниме из Kodik API...")
    
    while True:
        try:
            params = {
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'with_material_data': True,
                'with_seasons': True,
                'with_episodes': True,
                'limit': 100,
                'sort': 'updated_at',
                'order': 'desc'
            }
            
            if next_page:
                # next_page уже содержит полный URL с параметрами
                url = next_page
                # Убираем базовый URL для requests
                if url.startswith(KODIK_API_BASE):
                    url = url.replace(KODIK_API_BASE, '')
            else:
                url = '/list'
            
            response = requests.get(f"{KODIK_API_BASE}{url}", params=not next_page and params or None)
            response.raise_for_status()
            
            data = response.json()
            all_anime.extend(data.get('results', []))
            
            page += 1
            total = data.get('total', 0)
            loaded = len(all_anime)
            
            print(f"  📄 Страница {page}: загружено {loaded}/{total} аниме")
            
            next_page = data.get('next_page')
            
            if not next_page:
                break
            
            # Небольшая пауза чтобы не перегрузить API
            time.sleep(0.1)
            
        except requests.RequestException as e:
            print(f"❌ Ошибка при загрузке страницы {page}: {e}")
            break
    
    print(f"✅ Всего загружено {len(all_anime)} аниме")
    return all_anime


def calculate_episode_duration(kodik_anime: Dict[str, Any]) -> Optional[int]:
    """Рассчитывает среднюю длительность эпизода в минутах на основе данных Kodik"""
    material_data = kodik_anime.get('material_data', {})
    
    # Сначала пробуем получить из material_data (это точнее)
    duration_from_material = material_data.get('duration')
    if duration_from_material:
        duration_minutes = int(duration_from_material)
        # Проверяем на разумность
        if 1 <= duration_minutes <= 180:
            return duration_minutes
    
    # Если нет в material_data, пробуем из episodes
    episodes_data = kodik_anime.get('episodes', [])
    if not episodes_data:
        return None

    # Собираем длительности эпизодов в секундах
    durations = []
    for episode in episodes_data:
        duration = episode.get('duration')
        if duration and duration > 0:
            durations.append(duration)

    if not durations:
        return None
    
    # Фильтруем выбросы: слишком короткие (менее 30 сек) и слишком длинные (более 2 часов)
    valid_durations = [d for d in durations if 30 <= d <= 7200]
    if not valid_durations:
        return None
    
    # Берем медиану для большей устойчивости к выбросам
    sorted_durations = sorted(valid_durations)
    n = len(sorted_durations)
    
    if n % 2 == 1:
        median_seconds = sorted_durations[n // 2]
    else:
        median_seconds = (sorted_durations[n // 2 - 1] + sorted_durations[n // 2]) / 2
    
    # Конвертируем в минуты и округляем
    average_minutes = int(round(median_seconds / 60))
    
    # Проверяем на разумность результата
    if average_minutes < 5:  # Слишком коротко для аниме
        average_minutes = 24  # Стандартная длительность
    elif average_minutes > 180:  # Слишком длинно
        average_minutes = 60 if kodik_anime.get('type') == 'movie' else 24
    
    return average_minutes


def import_anime(kodik_anime: Dict[str, Any]) -> Anime:
    """Импорт одного аниме (только новые, без обновления)"""
    material_data = kodik_anime.get('material_data', {})
    
    # Проверяем, есть ли уже это аниме
    shikimori_id = kodik_anime.get('shikimori_id')
    if shikimori_id and Anime.objects.filter(shikimori_id=shikimori_id).exists():
        return None  # Пропускаем - уже есть
    
    # Определяем количество эпизодов
    # ВАЖНО: kodik_anime.get('episodes_count') правильнее чем material_data.get('episodes_total')
    episodes_count = (
        kodik_anime.get('episodes_count') or
        kodik_anime.get('last_episode') or
        material_data.get('episodes_total') or
        1
    )
    
    # Определяем длительность эпизода
    episode_duration = calculate_episode_duration(kodik_anime)
    
    # Определяем количество сезонов
    seasons_data = kodik_anime.get('seasons', {})
    seasons_count = len(seasons_data) if seasons_data else 1
    
    # Жанры
    genre_names = material_data.get('anime_genres') or material_data.get('genres') or []
    
    # Студии
    studio_names = material_data.get('anime_studios') or []
    
    # Постер
    poster_url = (
        material_data.get('anime_poster_url') or
        material_data.get('poster_url') or
        ''
    )
    
    # Скриншоты - из материала или из корня
    screenshots = (
        material_data.get('screenshots') or
        kodik_anime.get('screenshots') or
        []
    )
    
    # Рейтинг
    score = (
        material_data.get('shikimori_rating') or
        material_data.get('kinopoisk_rating') or
        0.0
    )
    
    # Описание
    description = (
        material_data.get('anime_description') or
        material_data.get('description') or
        ''
    )
    
    # Создаём только новое аниме (без обновления существующих)
    try:
        anime = Anime.objects.create(
            title_ru=kodik_anime.get('title', ''),
            title_en=kodik_anime.get('title_orig', ''),
            title_jp=kodik_anime.get('other_title', ''),
            description=description,
            year=kodik_anime.get('year'),
            status=map_status(material_data.get('anime_status', 'released')),
            kind=map_kind(material_data.get('anime_kind') or kodik_anime.get('type', 'tv')),
            episodes=episodes_count,
            episode_duration=episode_duration,  # Новая длительность эпизода
            score=score,
            poster_url=poster_url,
            genres=genre_names,
            studios=studio_names,
            data_source='kodik',
            shikimori_id=shikimori_id,
            # Дополнительные поля для хранения данных Kodik
            movies=[],
            ovas=[],
            movie_count=0,
            ova_count=0,
            total_items=seasons_count,
            screenshots=screenshots,
            kodik_link=normalize_kodik_player_link(kodik_anime.get('link', '')),
            kodik_id=kodik_anime.get('id', ''),
            quality=kodik_anime.get('quality', ''),
        )
        print(f"  ✨ Создано: {anime.title_ru} (эпизоды: {episodes_count}, длительность: {episode_duration or '?'} мин)")
        return anime
    except Exception as e:
        # Возможно уже есть (дубликат по другому полю)
        return None


def main():
    print("🚀 Начинаем импорт аниме из Kodik")
    print("=" * 50)
    
    # Загружаем все аниме
    all_anime = fetch_all_anime()
    
    if not all_anime:
        print("❌ Не удалось загрузить аниме из Kodik")
        return
    
    print("\n📥 Импорт в базу данных...")
    print("=" * 50)
    
    imported = 0
    skipped = 0
    errors = 0
    
    for i, kodik_anime in enumerate(all_anime, 1):
        try:
            anime = import_anime(kodik_anime)
            
            if anime:
                imported += 1
            else:
                skipped += 1  # Уже есть
            
            # Прогресс
            if i % 50 == 0:
                print(f"  📊 Прогресс: {i}/{len(all_anime)}")
            
        except Exception as e:
            print(f"  ❌ Ошибка при импорте {kodik_anime.get('title', 'Unknown')}: {e}")
            errors += 1
    
    print("\n" + "=" * 50)
    print("📊 Статистика импорта:")
    print(f"  ✨ Создано: {imported}")
    print(f"  ⏭️  Пропущено (уже есть): {skipped}")
    print(f"  ❌ Ошибок: {errors}")
    print(f"  📦 Всего обработано: {len(all_anime)}")
    print("=" * 50)
    
    # Статистика в базе
    total_anime = Anime.objects.count()
    kodik_anime_count = Anime.objects.filter(data_source='kodik').count()
    
    print(f"\n📊 Статистика в базе данных:")
    print(f"  📦 Всего аниме: {total_anime}")
    print(f"  🎬 Аниме из Kodik: {kodik_anime_count}")
    print("=" * 50)


if __name__ == '__main__':
    main()



