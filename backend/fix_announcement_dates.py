#!/usr/bin/env python3
"""
Скрипт исправления даты выхода анонсов.
Загружает все анонсы из Jikan /seasons/upcoming и обновляет данные в базе.
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
from datetime import datetime, date

JIKAN_BASE = 'https://api.jikan.moe/v4'


def fetch_jikan_upcoming() -> list:
    """Загружает все анонсы из Jikan seasons/upcoming"""
    print("📥 Загружаю анонсы из Jikan...")
    
    all_announcements = []
    
    # Headers как в работающем скрипте
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # seasons/upcoming с пагинацией и retry при 429
    print("  Загружаю /seasons/upcoming (все страницы)...")
    page = 1
    retries = 0
    max_retries = 5
    
    while page <= 30:  # max pages
        try:
            response = requests.get(
                f'{JIKAN_BASE}/seasons/upcoming',
                params={'page': page, 'limit': 25},
                timeout=30,
                headers=headers
            )
            
            if response.status_code == 429:
                retries += 1
                if retries <= max_retries:
                    wait_time = retries * 3  # 3, 6, 9, 12, 15 сек
                    print(f"    429 Rate limit, жду {wait_time} сек... (retry {retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"    Превышено количество retry, останавливаюсь на странице {page}")
                    break
            elif response.status_code != 200:
                print(f"    Страница {page}: статус {response.status_code}")
                break
                
            retries = 0  # Сброс retry при успехе
            data = response.json()
            items = data.get('data', [])
            
            if not items:
                break
            
            all_announcements.extend(items)
            print(f"    Страница {page}: {len(items)} аниме")
            
            # Проверяем есть ли следующая страница
            pagination = data.get('pagination', {})
            if not pagination.get('has_next_page'):
                print(f"    Последняя страница: {page}")
                break
            
            page += 1
            time.sleep(1)  # Rate limit - 1 сек между запросами
            
        except Exception as e:
            print(f"    Ошибка на странице {page}: {e}")
            break
    
    print(f"  📊 Всего загружено: {len(all_announcements)}")
    
    # Если мало, добираем из сезонов
    if len(all_announcements) < 200:
        print("  Добираю из сезонов...")
        for year in [2026, 2027]:
            for season in ['winter', 'spring', 'summer', 'fall']:
                if len(all_announcements) >= 500:
                    break
                try:
                    response = requests.get(
                        f'{JIKAN_BASE}/seasons/{year}/{season}',
                        params={'limit': 25},
                        timeout=30,
                        headers=headers
                    )
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('data', [])
                        for item in items:
                            # Добавляем только Not yet aired
                            if item.get('status') == 'Not yet aired':
                                if item not in all_announcements:
                                    all_announcements.append(item)
                    time.sleep(0.5)
                except:
                    pass
        print(f"  📊 После сезонов: {len(all_announcements)}")
    
    return all_announcements


        
    print(f"  📊 Всего загружено из Jikan: {len(all_announcements)}")
    
    # Если мало, добираем из сезонов
    if len(all_announcements) < 100:
        print("  Добираю из сезонов...")
        for year in [2026, 2027]:
            for season in ['winter', 'spring', 'summer', 'fall']:
                if len(all_announcements) >= 300:
                    break
                try:
                    response = requests.get(
                        f'{JIKAN_BASE}/seasons/{year}/{season}',
                        params={'limit': 25},
                        timeout=30,
                        headers=headers
                    )
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('data', [])
                        for item in items:
                            # Добавляем только Not yet aired
                            if item.get('status') == 'Not yet aired':
                                if item not in all_announcements:
                                    all_announcements.append(item)
                    time.sleep(0.3)
                except:
                    pass
        print(f"  📊 После сезонов: {len(all_announcements)}")
    
    return all_announcements


def parse_jikan_anime(jikan_item: dict) -> dict:
    """Парсит данные аниме из Jikan"""
    mal_id = jikan_item.get('mal_id')
    
    # Собираем все названия
    titles = jikan_item.get('titles', [])
    title_ru = None
    title_en = None
    title_jp = None
    
    for t in titles:
        t_type = t.get('type', '')
        t_title = t.get('title', '')
        if t_type == 'Default':
            title_en = t_title
        elif t_type == 'English':
            title_en = t_title
        elif t_type == 'Japanese':
            title_jp = t_title
    
    # Fallback
    if not title_en:
        title_en = jikan_item.get('title_english') or jikan_item.get('title', '')
    if not title_en:
        title_en = jikan_item.get('title', '')
    
    # Дата выхода
    aired = jikan_item.get('aired', {})
    release_date = None
    year = None
    season = jikan_item.get('season')  # winter, spring, summer, fall
    
    from_iso = aired.get('from')
    if from_iso:
        try:
            dt = datetime.fromisoformat(from_iso.replace('Z', '+00:00'))
            release_date = dt.date()
            year = dt.year
        except:
            pass
    
    if not year:
        year = jikan_item.get('year')
    
    # Статус
    status = jikan_item.get('status', '')
    is_ongoing = status == 'Currently Airing'
    
    # Постер
    images = jikan_item.get('images', {})
    jpg = images.get('jpg', {})
    poster_url = jpg.get('large_image_url') or jpg.get('image_url')
    
    # Тип
    anime_type = jikan_item.get('type')  # TV, Movie, OVA, etc.
    
    return {
        'mal_id': mal_id,
        'title_en': title_en,
        'title_jp': title_jp,
        'release_date': release_date,
        'year': year,
        'season': season,
        'is_ongoing': is_ongoing,
        'poster_url': poster_url,
        'type': anime_type,
        'status_raw': status,
    }


def fix_announcement_dates():
    """Исправляет даты анонсов"""
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ ДАТ АНОНСОВ")
    print("=" * 60)
    
    # Загружаем анонсы из Jikan
    jikan_announcements = fetch_jikan_upcoming()
    
    if not jikan_announcements:
        print("❌ Не удалось загрузить анонсы из Jikan")
        return
    
    # Парсим данные из Jikan
    jikan_data = {}
    for item in jikan_announcements:
        parsed = parse_jikan_anime(item)
        mal_id = parsed['mal_id']
        
        # Индексируем по mal_id и по названию
        jikan_data[mal_id] = parsed
        
        # Также по названию (для поиска без mal_id)
        if parsed['title_en']:
            jikan_data[parsed['title_en'].lower()] = parsed
        if parsed['title_jp']:
            jikan_data[parsed['title_jp'].lower()] = parsed
    
    print(f"📊 Индексировано: {len(jikan_data)} записей")
    
    # Берём все анонсы из базы
    announcements = Anime.objects.filter(status='announced')
    total = announcements.count()
    
    print(f"\n📊 Анонсов в базе: {total}")
    
    # Сопоставляем - проходим по ВСЕМ анонсам
    updated = 0
    matched = 0
    skipped = 0
    
    print("\nОбрабатываю анонсы...")
    for i, anime in enumerate(announcements):
        if i % 50 == 0:
            print(f"  Прогресс: {i}/{total}")
        
        found = None
        
        # 1. Ищем по shikimori_id (mal_id)
        if anime.shikimori_id:
            found = jikan_data.get(anime.shikimori_id)
        
        # 2. Ищем по точному названию (английское)
        if not found and anime.title_en:
            key = anime.title_en.lower()
            found = jikan_data.get(key)
        
        # 3. Ищем по японскому названию
        if not found and anime.title_jp:
            key = anime.title_jp.lower()
            found = jikan_data.get(key)
        
        # 4. Частичное совпадение по английскому названию
        if not found and anime.title_en:
            search_title = anime.title_en.lower().strip()
            # Убираем всякие (TV), (Movie), 2nd Season и т.д.
            search_base = search_title.replace('(tv)', '').replace('(movie)', '').replace('(ona)', '').replace('(ova)', '').replace(' 2nd season', '').replace(' season', '').strip()
            
            for key, data in jikan_data.items():
                if isinstance(key, str) and key in jikan_data:
                    jikan_title = key.lower()
                    # Проверяем содержится ли одно в другом
                    if search_base and len(search_base) > 3:
                        if search_base in jikan_title or jikan_title in search_base:
                            found = data
                            break
                        # Проверяем первые слова
                        search_words = search_base.split()[:3]
                        jikan_words = jikan_title.split()[:3]
                        if len(search_words) >= 2 and len(jikan_words) >= 2:
                            if search_words[0] == jikan_words[0] and search_words[1] == jikan_words[1]:
                                found = data
                                break
        found = None
        
        # 1. Ищем по shikimori_id (mal_id)
        if anime.shikimori_id:
            found = jikan_data.get(anime.shikimori_id)
        
        # 2. Ищем по названию
        if not found and anime.title_en:
            found = jikan_data.get(anime.title_en.lower())
        
        if not found and anime.title_jp:
            found = jikan_data.get(anime.title_jp.lower())
        
        # 3. Частичное совпадение по названию
        if not found:
            search_title = (anime.title_en or anime.title_ru or '').lower()
            for key, data in jikan_data.items():
                if isinstance(key, str) and search_title and search_title in key:
                    found = data
                    break
                if isinstance(key, str) and data.get('title_en'):
                    if search_title and search_title in data['title_en'].lower():
                        found = data
                        break
        
        if not found:
            skipped += 1
            continue
        
        matched += 1
        changes = []
        
        # Обновляем год (всегда)
        if found['year']:
            if anime.year != found['year']:
                changes.append(f"year: {anime.year} -> {found['year']}")
                anime.year = found['year']
        
        # Обновляем дату выхода
        if found['release_date']:
            if anime.release_date != found['release_date']:
                changes.append(f"release_date: {anime.release_date} -> {found['release_date']}")
                anime.release_date = found['release_date']
        
        # Обновляем статус если ongoing
        if found['is_ongoing'] and anime.status != 'ongoing':
            changes.append(f"status: {anime.status} -> ongoing")
            anime.status = 'ongoing'
        
        # Обновляем постер если есть
        if found['poster_url'] and not anime.poster_url:
            anime.poster_url = found['poster_url']
            changes.append("poster_url добавлен")
        
        # Обновляем title_en если в Jikan есть а английское
        if found['title_en'] and not anime.title_en:
            anime.title_en = found['title_en']
            changes.append(f"title_en: добавлен '{found['title_en'][:30]}'")
        
        # Обновляем title_jp если в Jikan есть
        if found['title_jp'] and not anime.title_jp:
            anime.title_jp = found['title_jp']
            changes.append(f"title_jp: добавлен")
        
        if changes:
            anime.updated_at = timezone.now()
            anime.save()
            updated += 1
            title = (anime.title_en or anime.title_ru or 'N/A')[:40]
            print(f"  ✅ [{anime.id}] {title}")
            for c in changes[:4]:  # Показываем первые 4 изменения
                print(f"      {c}")
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    print(f"  Сопоставлено: {matched}")
    print(f"  Обновлено: {updated}")
    print(f"  Не найдены: {skipped}")
    
    # Статистика по статусам
    print("\n📊 Статистика:")
    print(f"  announced: {Anime.objects.filter(status='announced').count()}")
    print(f"  ongoing:   {Anime.objects.filter(status='ongoing').count()}")
    print(f"  finished:  {Anime.objects.filter(status='finished').count()}")


if __name__ == '__main__':
    fix_announcement_dates()
