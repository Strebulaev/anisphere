#!/usr/bin/env python3
"""
Скрипт очистки каталога от анонсов.
1. Анонсы которые уже вышли (есть episodes или kodik_link) -> finished
2. Оставшиеся анонсы остаются анонсами
3. Запускает импорт из Kodik для обновления каталога
"""

import os
import sys
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from django.db import models
from django.utils import timezone
from datetime import datetime

KODIK_API_TOKEN = "74ecb013335271e4344ebc994956dd75"
KODIK_API_BASE    = 'https://kodik-api.com'     # API
KODIK_PLAYER_BASE = 'https://kodikplayer.com'   # Плеер (было: kodik.cc / kodik.info)
KODIK_DB_BASE     = 'https://bd.kodikres.com'   # База данных
KODIK_SOCIAL_BASE = 'https://kodikonline.com'   # Плеер для соцсетей
KODIK_VIDEO_BASE     = 'https://kodikres.com'      # video-links API
KODIK_SCREENSHOTS_BASE = 'https://i.kodikres.com' 

def clean_catalog():
    """Очищает каталог от анонсов"""
    
    print("=" * 60)
    print("ОЧИСТКА КАТАЛОГА ОТ АНОНСОВ")
    print("=" * 60)
    
    # 1. Анонсы которые уже вышли - переводим в finished
    # Критерии: есть episodes > 0 ИЛИ есть kodik_link
    released_announcements = Anime.objects.filter(status='announced').filter(
        models.Q(episodes__gt=0) | models.Q(kodik_link__isnull=False, kodik_link__gt='')
    )
    
    count_released = released_announcements.count()
    print(f"\n📊 Анонсы которые уже вышли (переводим в finished): {count_released}")
    
    if count_released > 0:
        print("Первые 10:")
        for anime in released_announcements[:10]:
            print(f"  [{anime.id}] {anime.title_ru[:40]} | episodes: {anime.episodes}, kodik: {bool(anime.kodik_link)}")
        
        confirm = input(f"\nПеревести {count_released} в finished? (y/n): ").strip().lower()
        if confirm == 'y':
            updated = released_announcements.update(status='finished', updated_at=timezone.now())
            print(f"  ✅ Обновлено: {updated}")
        else:
            print("  ❌ Отменено")
    
    # 2. Анонсы с годом в прошлом или текущем году - тоже в finished
    from datetime import date
    current_year = date.today().year
    
    past_announcements = Anime.objects.filter(status='announced').filter(
        models.Q(year__lt=current_year) | models.Q(year=current_year)
    )
    
    count_past = past_announcements.count()
    print(f"\n📊 Анонсы с годом <= {current_year}: {count_past}")
    
    if count_past > 0:
        print("Первые 10:")
        for anime in past_announcements[:10]:
            print(f"  [{anime.id}] {anime.title_ru[:40]} | year: {anime.year}")
        
        confirm = input(f"\nПеревести {count_past} в finished? (y/n): ").strip().lower()
        if confirm == 'y':
            updated = past_announcements.update(status='finished', updated_at=timezone.now())
            print(f"  ✅ Обновлено: {updated}")
        else:
            print("  ❌ Отменено")
    
    # 3. Показываем итоговую статистику
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    
    stats = {
        'announced': Anime.objects.filter(status='announced').count(),
        'ongoing': Anime.objects.filter(status='ongoing').count(),
        'finished': Anime.objects.filter(status='finished').count(),
        'released': Anime.objects.filter(status='released').count(),
    }
    
    print(f"  announced (анонсы): {stats['announced']}")
    print(f"  ongoing (онгоинг):  {stats['ongoing']}")
    print(f"  finished (вышедшие): {stats['finished']}")
    print(f"  released:           {stats['released']}")
    print(f"  ВСЕГО:              {sum(stats.values())}")
    
    # Спрашиваем про импорт из Kodik
    print("\n" + "=" * 60)
    confirm_import = input("Запустить импорт из Kodik для обновления каталога? (y/n): ").strip().lower()
    
    if confirm_import == 'y':
        print("\n🚀 Запускаю импорт из Kodik...")
        import_from_kodik()


def import_from_kodik():
    """Импорт аниме из Kodik - только вышедшие"""
    
    print("📥 Импорт из Kodik (только finished/released)...")
    
    page_size = 100
    page = 1
    imported = 0
    updated = 0
    skipped = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    while page <= 10:  # Ограничим 10 страницами
        try:
            params = {
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'with_material_data': True,
                'with_seasons': True,
                'with_episodes': True,
                'limit': page_size,
                'page': page,
                'sort': 'updated_at',
                'order': 'desc'
            }
            
            response = requests.get(f'{KODIK_API_BASE}/list', params=params, timeout=60, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                break
            
            print(f"  Страница {page}: {len(results)} аниме")
            
            for item in results:
                shikimori_id = item.get('shikimori_id')
                if not shikimori_id:
                    skipped += 1
                    continue
                
                material_data = item.get('material_data', {})
                anime_status = material_data.get('anime_status', '')
                
                # Пропускаем анонсы (anons)
                if anime_status == 'anons':
                    skipped += 1
                    continue
                
                # Маппим статус
                status_map = {
                    'anons': 'announced',
                    'ongoing': 'ongoing',
                    'released': 'finished',
                    'discontinued': 'canceled'
                }
                new_status = status_map.get(anime_status, 'finished')
                
                # Пропускаем анонсы
                if new_status == 'announced':
                    skipped += 1
                    continue
                
                # Находим существующее
                anime = Anime.objects.filter(shikimori_id=shikimori_id).first()
                
                if anime:
                    # Обновляем
                    material_data = item.get('material_data', {})
                    
                    # Обновляем эпизоды
                    episodes_count = item.get('episodes_count') or item.get('last_episode') or 0
                    if episodes_count and anime.episodes != episodes_count:
                        anime.episodes = episodes_count
                    
                    # Обновляем статус
                    if anime.status != new_status:
                        anime.status = new_status
                    
                    # Обновляем год
                    year = item.get('year')
                    if year and anime.year != year:
                        anime.year = year
                    
                    anime.updated_at = timezone.now()
                    anime.save()
                    updated += 1
                else:
                    # Создаём новое
                    kind_map = {
                        'tv': 'tv', 'tv_13': 'tv', 'tv_24': 'tv', 'tv_48': 'tv',
                        'movie': 'movie', 'ova': 'ova', 'ona': 'ona',
                        'special': 'special', 'music': 'music'
                    }
                    
                    kind = kind_map.get(material_data.get('anime_kind') or item.get('type', 'tv'), 'tv')
                    
                    try:
                        Anime.objects.create(
                            title_ru=item.get('title', ''),
                            title_en=item.get('title_orig', ''),
                            title_jp=item.get('other_title', ''),
                            description=material_data.get('anime_description') or '',
                            year=item.get('year'),
                            status=new_status,
                            kind=kind,
                            episodes=episodes_count,
                            episode_duration=material_data.get('duration', 24),
                            score=material_data.get('shikimori_rating') or 0.0,
                            poster_url=material_data.get('anime_poster_url') or '',
                            genres=material_data.get('anime_genres') or [],
                            studios=material_data.get('anime_studios') or [],
                            data_source='kodik',
                            shikimori_id=shikimori_id,
                            screenshots=material_data.get('screenshots') or [],
                            kodik_link=item.get('link', ''),
                            kodik_id=item.get('id', ''),
                            quality=item.get('quality', ''),
                        )
                        imported += 1
                    except Exception as e:
                        print(f"    Ошибка создания {item.get('title')}: {e}")
                
                time.sleep(0.05)
            
            # Проверяем есть ли следующая страница
            if not data.get('next_page'):
                break
            
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            break
    
    print(f"\n✅ Импорт завершён!")
    print(f"  Создано: {imported}")
    print(f"  Обновлено: {updated}")
    print(f"  Пропущено (анонсы): {skipped}")
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    
    stats = {
        'announced': Anime.objects.filter(status='announced').count(),
        'ongoing': Anime.objects.filter(status='ongoing').count(),
        'finished': Anime.objects.filter(status='finished').count(),
        'released': Anime.objects.filter(status='released').count(),
    }
    
    print(f"  announced (анонсы): {stats['announced']}")
    print(f"  ongoing (онгоинг):  {stats['ongoing']}")
    print(f"  finished (вышедшие): {stats['finished']}")
    print(f"  released:           {stats['released']}")
    print(f"  ВСЕГО:              {sum(stats.values())}")


if __name__ == '__main__':
    clean_catalog()
