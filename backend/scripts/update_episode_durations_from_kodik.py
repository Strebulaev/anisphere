#!/usr/bin/env python
"""
Скрипт для обновления реальных длительностей эпизодов аниме из Kodik API
Данные берутся из API с параметром with_episodes_data=True
"""

import os
import sys
import django
import requests
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime, VideoSource, Episode
from anime.kodik_config import KODIK_API_TOKEN, KODIK_API_BASE, KODIK_VIDEO_BASE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('episode_durations_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_kodik_episode_durations(shikimori_id: int, max_episodes: int = 100) -> Dict[int, int]:
    """
    Получает длительности эпизодов из Kodik API для аниме по Shikimori ID
    Использует:
    1. /search с with_material_data=True - продолжительность из базы (в минутах)
    
    Возвращает словарь {номер_эпизода: длительность_в_секундах}
    """
    episode_durations = {}
    
    try:
        # Получаем данные с material_data
        params = {
            'token': KODIK_API_TOKEN,
            'shikimori_id': shikimori_id,
            'with_material_data': True,
            'limit': 10,
        }
        
        response = requests.get(f'{KODIK_API_BASE}/search', params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            return {}
        
        # Берем первый результат
        result = results[0]
        material_data = result.get('material_data', {})
        
        if not material_data:
            return {}
        
        # Получаем duration в минутах
        duration_minutes = material_data.get('duration')
        if not duration_minutes:
            return {}
        
        # Конвертируем в секунды
        duration_seconds = int(duration_minutes) * 60
        
        # Получаем количество эпизодов - используем большее значение
        episodes_count = result.get('episodes_count') or 0
        last_episode = result.get('last_episode') or 0
        
        if last_episode > episodes_count:
            episodes_count = last_episode
        elif not episodes_count:
            episodes_count = 12
        
        # Заполняем все эпизоды
        for ep in range(1, int(episodes_count) + 1):
            episode_durations[ep] = duration_seconds
        
        return episode_durations
            
    except Exception as e:
        return episode_durations


def calculate_average_episode_duration(episode_durations: Dict[int, int]) -> Optional[int]:
    """
    Рассчитывает среднюю длительность эпизода в минутах
    """
    if not episode_durations:
        return None
    
    # Фильтруем слишком короткие эпизоды (менее 30 секунд) и слишком длинные (более 2 часов)
    valid_durations = [
        duration for duration in episode_durations.values()
        if 30 <= duration <= 7200  # 30 сек - 2 часа
    ]
    
    if not valid_durations:
        logger.warning("Нет валидных длительностей эпизодов")
        return None
    
    # Для сериалов берем медиану (чтобы исключить выбросы)
    sorted_durations = sorted(valid_durations)
    n = len(sorted_durations)
    
    if n % 2 == 1:
        median_duration = sorted_durations[n // 2]
    else:
        median_duration = (sorted_durations[n // 2 - 1] + sorted_durations[n // 2]) / 2
    
    # Конвертируем в минуты, округляем
    average_minutes = int(round(median_duration / 60))
    
    # Корректируем для типов аниме
    if average_minutes < 10:  # Слишком коротко для обычного аниме
        average_minutes = 24  # Стандартная длительность
    
    return average_minutes


def update_anime_episode_duration(anime: Anime, episode_durations: Dict[int, int]):
    """
    Обновляет длительность эпизода для аниме
    """
    if not episode_durations:
        return
    
    average_minutes = calculate_average_episode_duration(episode_durations)
    
    if average_minutes is None:
        return
    
    # Обновляем поле в модели
    old_duration = anime.episode_duration
    anime.episode_duration = average_minutes
    anime.updated_at = datetime.now()
    anime.save(update_fields=['episode_duration', 'updated_at'])
    
    # Логируем результат
    status = "✓" if old_duration != average_minutes else "="
    logger.info(f"{status} {anime.title_ru[:50]:<50} | {average_minutes} мин | {len(episode_durations)} эп.")
    
    # Также создаем или обновляем VideoSource с длительностями эпизодов
    update_video_sources(anime, episode_durations)


def update_video_sources(anime: Anime, episode_durations: Dict[int, int]):
    """
    Создает или обновляет VideoSource записи с длительностями эпизодов
    """
    try:
        # Получаем или создаем VideoSource для Kodik
        video_source, created = VideoSource.objects.get_or_create(
            anime=anime,
            source='kodik',
            quality='720',
            defaults={
                'external_id': anime.kodik_id or str(anime.shikimori_id),
                'title': f"Kodik - {anime.title_ru}",
                'description': f"Видео с Kodik для {anime.title_ru}",
                'video_format': 'hls',
                'is_available': True,
                'is_active': True,
            }
        )
        
        # Обновляем общую длительность (если есть эпизоды)
        if episode_durations:
            durations_list = list(episode_durations.values())
            if durations_list:
                avg_duration_seconds = sum(durations_list) // len(durations_list)
                video_source.duration = avg_duration_seconds
                video_source.save(update_fields=['duration', 'updated_at'])
        
    except Exception as e:
        pass


def update_episodes_table(anime: Anime, episode_durations: Dict[int, int]):
    """
    Создает или обновляет записи в таблице Episode с реальными длительностями
    """
    if not episode_durations:
        return
    
    try:
        # Получаем VideoSource для Kodik
        video_source = VideoSource.objects.filter(
            anime=anime,
            source='kodik'
        ).first()
        
        if not video_source:
            return
        
        for episode_num, duration_seconds in episode_durations.items():
            episode, created = Episode.objects.update_or_create(
                anime=anime,
                video_source=video_source,
                number=episode_num,
                defaults={
                    'title': f"Эпизод {episode_num}",
                    'duration': duration_seconds,
                }
            )
            
    except Exception as e:
        pass


def process_anime_batch(anime_list: List[Anime], batch_size: int = 10):
    """
    Обрабатывает батч аниме с задержкой между запросами
    """
    total = len(anime_list)
    logger.info(f"{'='*60}")
    logger.info(f"Обработка {total} аниме...")
    logger.info(f"{'='*60}")
    logger.info(f"{'Название':<50} | {'Время':<10} | {'Эп.'}")
    logger.info(f"{'-'*60}")
    
    success_count = 0
    fail_count = 0
    
    for i, anime in enumerate(anime_list, 1):
        try:
            if not anime.shikimori_id:
                fail_count += 1
                continue
            
            # Получаем длительности эпизодов из Kodik
            episode_durations = get_kodik_episode_durations(anime.shikimori_id)
            
            if episode_durations:
                # Обновляем аниме
                update_anime_episode_duration(anime, episode_durations)
                
                # Обновляем таблицу Episode
                update_episodes_table(anime, episode_durations)
                success_count += 1
            else:
                fail_count += 1
            
            # Задержка между запросами
            if i % batch_size == 0 and i < total:
                time.sleep(3)
            else:
                time.sleep(0.3)
                
        except Exception as e:
            fail_count += 1
            time.sleep(1)
    
    logger.info(f"{'-'*60}")
    logger.info(f"Готово! Обработано: {success_count}, Не удалось: {fail_count}")


def get_anime_to_process(limit: Optional[int] = None, has_shikimori: bool = True):
    """
    Получает список аниме для обработки
    Фильтруем в Python чтобы избежать проблем с некорректными данными в БД
    """
    # Сначала получаем все аниме с ненулевым shikimori_id
    from django.db.models import F
    
    # Получаем только те записи где shikimori_id > 0
    all_anime = list(Anime.objects.filter(
        shikimori_id__isnull=False
    ).exclude(
        shikimori_id=0
    ).order_by(
        # Сортируем: без длительности -> нулевая -> остальные
        F('episode_duration').asc(nulls_first=True),
        'id'
    ))
    
    if limit:
        all_anime = all_anime[:limit]
    
    return all_anime


def main():
    """Основная функция скрипта"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Обновление длительностей эпизодов аниме из Kodik API')
    parser.add_argument('--limit', type=int, help='Ограничение количества аниме для обработки')
    parser.add_argument('--batch-size', type=int, default=10, help='Размер батча между паузами (по умолчанию: 10)')
    parser.add_argument('--shikimori-only', action='store_true', default=True, help='Обрабатывать только аниме с Shikimori ID')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Обновление длительностей эпизодов из Kodik")
    logger.info("=" * 60)

    # Получаем аниме для обработки
    anime_list = get_anime_to_process(
        limit=args.limit,
        has_shikimori=args.shikimori_only
    )

    if not anime_list:
        logger.warning("Нет аниме для обработки!")
        return
    
    # Обрабатываем аниме
    start_time = time.time()
    process_anime_batch(anime_list, args.batch_size)
    end_time = time.time()
    
    # Статистика
    total_time = end_time - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    logger.info("=" * 60)
    logger.info(f"Скрипт завершен!")
    logger.info(f"Общее время выполнения: {minutes} мин {seconds} сек")
    logger.info(f"Обработано аниме: {len(anime_list)}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()