"""
Скрипт для проверки и восстановления аниме из Kodik API.

Запуск: python backend/restore_anime_from_kodik.py
"""

import os
import sys
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from anime.models import Anime

KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'


def check_database():
    """Проверяет что в базе."""
    from django.db.models import Count
    
    print("=" * 60)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    total = Anime.objects.count()
    print(f"Всего аниме: {total}")
    
    stats = Anime.objects.values('status').annotate(count=Count('id'))
    print("\nПо статусам:")
    for s in stats:
        print(f"  {s['status']}: {s['count']}")
    
    # Проверяем конкретное аниме
    try:
        frieren = Anime.objects.get(shikimori_id=59978)
        print(f"\n✅ Frieren найден:")
        print(f"  title_ru: {frieren.title_ru}")
        print(f"  year: {frieren.year}")
        print(f"  status: {frieren.status}")
        print(f"  poster_url: {frieren.poster_url[:50]}...")
    except Anime.DoesNotExist:
        print(f"\n❌ Frieren (shikimori_id=59978) НЕ найден!")
        return False
    
    return True


def restore_from_kodik(shikimori_id):
    """Восстанавливает одно аниме из Kodik."""
    try:
        url = 'https://kodik-api.com/search'
        params = {
            'token': KODIK_TOKEN,
            'shikimori_id': shikimori_id,
            'types': 'anime,anime-serial',
            'with_material_data': 'true',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            print(f"  ❌ Не найдено в Kodik")
            return False
        
        result = results[0]
        material_data = result.get('material_data', {})
        
        if not material_data:
            print(f"  ❌ Нет material_data")
            return False
        
        # Получаем или создаём
        anime, created = Anime.objects.update_or_create(
            shikimori_id=shikimori_id,
            defaults={
                'title_ru': material_data.get('anime_title') or material_data.get('title') or '',
                'title_en': material_data.get('title_en') or '',
                'title_jp': material_data.get('other_titles', [material_data.get('title', '')])[0] if isinstance(material_data.get('other_titles'), list) else '',
                'description': material_data.get('anime_description') or material_data.get('description') or '',
                'year': int(material_data.get('year')) if material_data.get('year') else None,
                'status': map_status(material_data.get('anime_status') or material_data.get('all_status')),
                'kind': map_kind(material_data.get('anime_kind')),
                'episodes': material_data.get('episodes_total') or material_data.get('episodes_aired'),
                'score': float(material_data.get('shikimori_rating')) if material_data.get('shikimori_rating') else None,
                'poster_url': material_data.get('anime_poster_url') or material_data.get('poster_url') or '',
                'genres': material_data.get('anime_genres') or material_data.get('all_genres') or [],
                'studios': material_data.get('anime_studios') or [],
                'mal_id': int(material_data.get('mal_id')) if material_data.get('mal_id') else None,
                'data_source': 'kodik',
            }
        )
        
        if created:
            print(f"  ✅ СОЗДАНО: {anime.title_ru}")
        else:
            print(f"  ✅ ОБНОВЛЕНО: {anime.title_ru}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def map_status(kodik_status):
    """Маппинг статусов Kodik."""
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


def main():
    print("=" * 60)
    print("ВОССТАНОВЛЕНИЕ АНИМЕ ИЗ KODIK")
    print("=" * 60)
    
    # Проверяем базу
    if not check_database():
        print("\n❌ База пуста или аниме не найдены!")
        print("Нужно импортировать из Kodik")
        
        # Спрашиваем какие ID восстановить
        print("\nВведите shikimori_id для восстановления (через запятую):")
        print("Или введите 'all' для массового импорта")
        user_input = input("> ").strip()
        
        if user_input.lower() == 'all':
            print("\n⚠️ Массовый импорт — это займёт время!")
            print("Введите лимит (0 = без лимита):")
            limit = int(input("> ").strip())
            
            # Импорт всех из Kodik
            from scripts.import_from_kodik import fetch_all_anime, import_anime
            
            print("Загрузка списка из Kodik...")
            all_anime = fetch_all_anime()
            
            if limit > 0:
                all_anime = all_anime[:limit]
            
            print(f"Импортируем {len(all_anime)} аниме...")
            
            for i, kodik_data in enumerate(all_anime[:100], 1):  # Первые 100 для теста
                shikimori_id = kodik_data.get('shikimori_id')
                if shikimori_id:
                    print(f"[{i}/{len(all_anime)}] shikimori_id={shikimori_id}")
                    restore_from_kodik(int(shikimori_id))
                    time.sleep(0.3)
        else:
            ids = [int(x.strip()) for x in user_input.split(',') if x.strip().isdigit()]
            
            for sid in ids:
                print(f"\nВосстанавливаем shikimori_id={sid}...")
                restore_from_kodik(sid)
                time.sleep(0.3)
    else:
        print("\n✅ База в порядке!")
        print("Хотите восстановить конкретные аниме? (y/n)")
        confirm = input("> ").strip().lower()
        
        if confirm == 'y':
            print("Введите shikimori_id (через запятую):")
            user_input = input("> ").strip()
            ids = [int(x.strip()) for x in user_input.split(',') if x.strip().isdigit()]
            
            for sid in ids:
                print(f"\nВосстанавливаем shikimori_id={sid}...")
                restore_from_kodik(sid)
                time.sleep(0.3)


if __name__ == '__main__':
    main()
