#!/usr/bin/env python3
"""
Скрипт импорта анонсов аниме из Jikan API.

Источник:
- Jikan API: https://api.jikan.moe/v4/seasons/upcoming (все анонсы с датами)

Логика:
1. Удалить ВСЕ старые анонсы (status='announced')
2. Получить все анонсы из Jikan (пагинация)
3. Сохранить в БД со статусом 'announced'
4. Постеры - ТОЛЬКО с MyAnimeList (jpg.large_image_url)
5. Дата выхода - полная (год + месяц + число)

Важно:
- Анонсы НЕ должны попадать в общий каталог (фильтр по status != 'announced')
- Постеры берутся ссылкой с MAL, не скачиваются локально

Запуск: python backend/import_announcements.py
"""

import os
import sys
import time
import logging
import requests
from datetime import date
from typing import Optional

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.utils import timezone
from django.db import transaction

from anime.models import Anime


# ==================== КОНСТАНТЫ ====================

# Jikan API (MyAnimeList)
JIKAN_BASE_URL = "https://api.jikan.moe/v4"
JIKAN_RATE_LIMIT = 1.0  # секунд между запросами

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==================== УДАЛЕНИЕ СТАРЫХ АНОНСОВ ====================

def delete_old_announcements():
    """Удаляет ВСЕ старые анонсы перед новым импортом."""
    logger.info("=" * 60)
    logger.info("УДАЛЕНИЕ СТАРЫХ АНОНСОВ")
    logger.info("=" * 60)
    
    count = Anime.objects.filter(status='announced').count()
    logger.info(f"Найдено анонсов для удаления: {count}")
    
    if count > 0:
        confirm = input(f"Удалить {count} анонсов? (y/n): ").strip().lower()
        if confirm == 'y':
            Anime.objects.filter(status='announced').delete()
            logger.info("✅ Все анонсы удалены")
        else:
            logger.info("❌ Удаление отменено пользователем")
            return False
    else:
        logger.info("Анонсов не найдено")
    
    return True


# ==================== JIKAN API ====================

def fetch_jikan_announcements() -> list:
    """
    Получает все анонсы из Jikan API.
    Пагинация: /seasons/upcoming?page=N&limit=25
    """
    announcements = []
    page = 1
    
    logger.info("=" * 60)
    logger.info("Начинаем загрузку анонсов из Jikan API")
    logger.info("=" * 60)
    
    while True:
        try:
            url = f"{JIKAN_BASE_URL}/seasons/upcoming"
            params = {'page': page, 'limit': 25}
            
            logger.info(f"Запрос страницы {page}...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем структуру ответа
            if 'data' not in data:
                logger.warning(f"Нет данных на странице {page}")
                break
            
            items = data['data']
            if not items:
                logger.info("Данные закончились")
                break
            
            # /seasons/upcoming уже возвращает только предстоящие анонсы
            announcements.extend(items)
            
            logger.info(f"Страница {page}: получено {len(items)} элементов")
            
            # Проверяем пагинацию
            pagination = data.get('pagination', {})
            has_next = pagination.get('has_next_page', False)
            
            if not has_next:
                logger.info("Это последняя страница")
                break
            
            page += 1
            time.sleep(JIKAN_RATE_LIMIT)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Jikan: {e}")
            break
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            break
    
    logger.info(f"Всего получено анонсов из Jikan: {len(announcements)}")
    return announcements


def extract_jikan_data(item: dict) -> dict:
    """Извлекает данные из Jikan API."""
    images = item.get('images', {})
    jpg = images.get('jpg', {})
    
    # Даты
    aired = item.get('aired', {})
    aired_from = aired.get('from')  # ISO строка "2025-07-01T00:00:00+00:00"
    aired_string = aired.get('string', '')  # Человекочитаемая "Jul 2025 to ?"
    
    # Статус
    jikan_status = item.get('status', 'Not yet aired')
    
    # Постер - ТОЛЬКО с MyAnimeList
    poster_url = jpg.get('large_image_url') or jpg.get('image_url', '')
    
    return {
        'mal_id': item.get('mal_id'),
        'title_english': item.get('title_english') or item.get('title', ''),
        'title': item.get('title', ''),
        'title_japanese': item.get('title_japanese', ''),
        'synopsis': item.get('synopsis', '') or '',
        'type': item.get('type', 'TV'),
        'episodes': item.get('episodes'),
        'score': item.get('score'),
        'status': jikan_status,
        'release_date': aired_from,
        'release_date_string': aired_string,
        'poster_url': poster_url,
        'genres': [g.get('name') for g in item.get('genres', [])],
        'studios': [s.get('name') for s in item.get('studios', [])],
    }


# ==================== СОХРАНЕНИЕ В БД ====================

def map_kind(jikan_type: str) -> str:
    """Маппит тип из Jikan в наш формат."""
    mapping = {
        'TV': 'tv',
        'Movie': 'movie',
        'OVA': 'ova',
        'Special': 'special',
        'ONA': 'ona',
        'Music': 'music',
    }
    return mapping.get(jikan_type, 'tv')


def map_status(jikan_status: str) -> str:
    """Маппит статус из Jikan в наш формат."""
    mapping = {
        'Not yet aired': 'announced',
        'Currently Airing': 'ongoing',
        'Finished Airing': 'finished',
        'airing': 'ongoing',
        'completed': 'finished',
        'not_yet_aired': 'announced',
    }
    return mapping.get(jikan_status, 'announced')


def parse_release_date(date_str: str) -> Optional[date]:
    """Парсит ISO дату из Jikan."""
    if not date_str:
        return None
    
    try:
        # Формат: "2025-01-15T00:00:00+00:00"
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


@transaction.atomic
def save_announcement(jikan_data: dict) -> tuple:
    """
    Сохраняет/обновляет анонс в БД.
    Возвращает (created: bool, updated: bool)
    
    Важно:
    - status = 'announced' (НЕ попадает в общий каталог)
    - poster_url = ссылка на MyAnimeList (не скачиваем)
    - release_date = полная дата (год + месяц + число)
    """
    mal_id = jikan_data.get('mal_id')
    
    if not mal_id:
        logger.warning(f"Нет mal_id для {jikan_data.get('title_english')}")
        return False, False
    
    # Приоритет названий
    title_ru = jikan_data.get('title_english') or jikan_data.get('title', '')
    title_en = jikan_data.get('title', '')
    title_original = jikan_data.get('title_japanese') or jikan_data.get('title', '') or 'Unknown'
    
    # Постер - ТОЛЬКО с MyAnimeList
    poster_url = jikan_data.get('poster_url', '')
    
    # Дата выхода - полная (год + месяц + число)
    release_date = parse_release_date(jikan_data.get('release_date', ''))
    release_date_string = jikan_data.get('release_date_string', '')
    
    # Статус - ВСЕГДА 'announced' для анонсов
    status = 'announced'
    
    # Создаем или обновляем по mal_id (он же shikimori_id для Jikan)
    anime, created = Anime.objects.update_or_create(
        mal_id=mal_id,
        defaults={
            'shikimori_id': mal_id,  # Для Jikan mal_id = shikimori_id
            'title_ru': title_ru[:255],
            'title_en': title_en[:255],
            'title_jp': title_original[:255],
            'description': jikan_data.get('synopsis', '')[:5000],
            'year': release_date.year if release_date else None,
            'release_date': release_date,
            'release_date_string': release_date_string,
            'status': status,  # 'announced' - НЕ попадает в общий каталог
            'kind': map_kind(jikan_data.get('type', 'TV')),
            'episodes': jikan_data.get('episodes'),
            'score': jikan_data.get('score'),
            'poster_url': poster_url,  # Ссылка на MAL (не скачиваем)
            'genres': jikan_data.get('genres', []),
            'studios': jikan_data.get('studios', []),
            'data_source': 'jikan',
        }
    )
    
    return created, True


# ==================== MAIN ====================

def main():
    """Главная функция."""
    logger.info("=" * 70)
    logger.info("ИМПОРТ АНОНСОВ АНИМЕ (Jikan API)")
    logger.info("=" * 70)
    
    # Шаг 0: Удаляем ВСЕ старые анонсы
    if not delete_old_announcements():
        logger.error("Импорт отменён")
        return
    
    # Статистика
    stats = {
        'total_jikan': 0,
        'created': 0,
        'updated': 0,
        'errors': 0,
    }
    
    # Шаг 1: Получаем анонсы из Jikan
    jikan_announcements = fetch_jikan_announcements()
    stats['total_jikan'] = len(jikan_announcements)
    
    if not jikan_announcements:
        logger.warning("Не удалось получить анонсы из Jikan")
        return
    
    # Шаг 2: Обрабатываем каждый анонс
    logger.info("=" * 60)
    logger.info("Сохраняем анонсы в БД...")
    logger.info("=" * 60)
    
    for i, item in enumerate(jikan_announcements, 1):
        try:
            # Извлекаем данные из Jikan
            jikan_data = extract_jikan_data(item)
            
            # Сохраняем в БД
            title = jikan_data.get('title_english') or jikan_data.get('title', '')
            try:
                created, updated = save_announcement(jikan_data)
                
                if created:
                    stats['created'] += 1
                    logger.info(f"[СОЗДАНО] {title[:50]} | mal_id={jikan_data.get('mal_id')}")
                elif updated:
                    stats['updated'] += 1
                
            except Exception as e:
                logger.error(f"[ОШИБКА СОХРАНЕНИЯ] {title}: {e}")
                stats['errors'] += 1
            
            # Логируем прогресс каждые 10 элементов
            if i % 10 == 0:
                logger.info(f"Обработано: {i}/{len(jikan_announcements)} (создано: {stats['created']})")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке: {e}")
            stats['errors'] += 1
            continue
    
    # Итоги
    logger.info("=" * 70)
    logger.info("ИТОГИ ИМПОРТА")
    logger.info("=" * 70)
    logger.info(f"  Всего анонсов в Jikan:    {stats['total_jikan']}")
    logger.info(f"  Создано новых:             {stats['created']}")
    logger.info(f"  Обновлено существующих:    {stats['updated']}")
    logger.info(f"  Ошибок:                    {stats['errors']}")
    logger.info("=" * 70)

    # Статистика по БД
    from django.db.models import Count
    stats_qs = Anime.objects.values('status').annotate(count=Count('id'))
    logger.info("\nСтатусы в БД:")
    for s in stats_qs:
        logger.info(f"  {s['status']}: {s['count']}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
