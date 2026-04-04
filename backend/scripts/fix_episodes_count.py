#!/usr/bin/env python
"""
Скрипт для исправления количества эпизодов аниме из Kodik API
"""

import os
import sys
import django
import requests
import time
import logging
from typing import Optional

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime
from anime.kodik_config import KODIK_API_TOKEN, KODIK_API_BASE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('fix_episodes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_episodes_count(shikimori_id: int) -> Optional[int]:
    """Получает количество эпизодов из Kodik API"""
    try:
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
            return None
        
        result = results[0]
        
        # Берем максимальное значение между episodes_count и last_episode
        # last_episode может быть больше для длинных онгоингов (Ван-Пис: 87 vs 1155)
        episodes_count = result.get('episodes_count') or 0
        last_episode = result.get('last_episode') or 0
        
        # Используем большее значение
        if last_episode > episodes_count:
            return int(last_episode)
        elif episodes_count:
            return int(episodes_count)
        
        return None

    except Exception as e:
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Исправление количества эпизодов из Kodik API')
    parser.add_argument('--limit', type=int, help='Ограничение количества аниме')
    parser.add_argument('--id', type=int, help='Конкретный anime ID для обновления')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Исправление количества эпизодов")
    logger.info("=" * 60)
    logger.info(f"{'Название':<45} | {'Было':<6} | {'Стало':<6}")
    logger.info("-" * 60)
    
    # Получаем аниме для обработки
    if args.id:
        anime_list = [Anime.objects.get(id=args.id)]
    else:
        anime_list = list(Anime.objects.filter(
            shikimori_id__isnull=False
        ).exclude(shikimori_id=0)[:args.limit or 10000])
    
    updated = 0
    failed = 0
    
    for anime in anime_list:
        try:
            old_episodes = anime.episodes
            new_episodes = get_episodes_count(anime.shikimori_id)
            
            if new_episodes and new_episodes != old_episodes:
                anime.episodes = new_episodes
                anime.save(update_fields=['episodes', 'updated_at'])
                logger.info(f"{anime.title_ru[:45]:<45} | {old_episodes:<6} | {new_episodes:<6}")
                updated += 1
            else:
                failed += 1
                
            time.sleep(0.3)
            
        except Exception as e:
            failed += 1
            time.sleep(1)
    
    logger.info("-" * 60)
    logger.info(f"Обновлено: {updated}, Пропущено: {failed}")


if __name__ == '__main__':
    main()
