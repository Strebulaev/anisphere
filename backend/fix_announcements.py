#!/usr/bin/env python3
"""
Скрипт исправления анонсов.
- Очищает поля Kodik (kodik_link, kodik_id, translations и т.д.)
- Исправляет названия: title_ru берется из title_en/title_jp (оригинальное с Jikan)
- Убирает ссылки на просмотр для анонсов
"""

import os
import sys
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def fix_announcements():
    """Исправляет анонсы."""
    from anime.models import Anime
    
    logger.info("=" * 60)
    logger.info("ИСПРАВЛЕНИЕ АНОНСОВ")
    logger.info("=" * 60)
    
    # Находим все анонсы
    announcements = Anime.objects.filter(
        status__in=['announced', 'released']
    )
    
    total = announcements.count()
    logger.info(f"Найдено анонсов: {total}")
    
    if total == 0:
        logger.info("Нет анонсов для исправления!")
        return
    
    fixed_count = 0
    title_fixed_count = 0
    kodik_cleared_count = 0
    
    for anime in announcements:
        changes = []
        
        # 1. Очищаем поля Kodik (у анонсов не должно быть ссылок на просмотр)
        if anime.kodik_link or anime.kodik_id or anime.translations:
            anime.kodik_link = ''
            anime.kodik_id = ''
            anime.translations = []
            anime.seasons = {}
            anime.last_season = None
            anime.last_episode = None
            anime.screenshots = []
            changes.append('kodik')
            kodik_cleared_count += 1
        
        # 2. Исправляем названия - ставим английское название в title_ru
        original_title_ru = anime.title_ru
        
        # Берем title_en (английское) -> title_jp (японское)
        new_title = anime.title_en or anime.title_jp
        
        if new_title and anime.title_ru != new_title:
            anime.title_ru = new_title
            changes.append('title')
            title_fixed_count += 1
        
        # 3. Также очищаем quality если есть
        if anime.quality:
            anime.quality = ''
        
        if changes:
            anime.save(update_fields=[
                'title_ru',
                'kodik_link', 
                'kodik_id',
                'translations',
                'seasons',
                'last_season',
                'last_episode',
                'screenshots',
                'quality',
                'updated_at'
            ])
            
            logger.info(f"[{anime.id}] {original_title_ru[:40]}...")
            logger.info(f"   Исправлено: {', '.join(changes)}")
            logger.info(f"   title_ru: '{original_title_ru[:30]}' -> '{anime.title_ru[:30]}'")
            fixed_count += 1
    
    # Итоги
    logger.info("=" * 60)
    logger.info("ИТОГИ")
    logger.info("=" * 60)
    logger.info(f"  Всего анонсов:     {total}")
    logger.info(f"  Исправлено:        {fixed_count}")
    logger.info(f"  Названий исправлено: {title_fixed_count}")
    logger.info(f"  Kodik полей очищено: {kodik_cleared_count}")
    logger.info("=" * 60)


def show_problem_examples():
    """Показывает примеры проблем."""
    from anime.models import Anime
    
    logger.info("\n" + "=" * 60)
    logger.info("ПРИМЕРЫ ПРОБЛЕМ")
    logger.info("=" * 60)
    
    announcements = Anime.objects.filter(
        status__in=['announced', 'released']
    )[:10]
    
    for anime in announcements:
        logger.info(f"\n[{anime.id}] {anime.title_ru[:40]}")
        logger.info(f"  title_en: '{anime.title_en[:30] if anime.title_en else 'N/A'}'")
        logger.info(f"  title_jp: '{anime.title_jp[:30] if anime.title_jp else 'N/A'}'")
        logger.info(f"  kodik_link: '{anime.kodik_link[:40] if anime.kodik_link else 'N/A'}'")
        logger.info(f"  kodik_id: '{anime.kodik_id[:20] if anime.kodik_id else 'N/A'}'")


if __name__ == "__main__":
    # Сначала покажем примеры проблем
    show_problem_examples()
    
    # Спросим подтверждение
    print("\n" + "=" * 60)
    confirm = input("Исправить все анонсы? (y/n): ").strip().lower()
    
    if confirm == 'y':
        fix_announcements()
    else:
        logger.info("Отменено пользователем")
