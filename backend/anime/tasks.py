"""
Celery задачи для импорта аниме из Kodik
"""
import logging
from celery import shared_task
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_new_anime_task(self, limit: int = 100):
    """
    Импорт новых аниме из Kodik API
    Запускается по расписанию через Celery Beat
    """
    from django.core.management import call_command
    import io
    import sys

    logger.info('📥 Запуск импорта новых аниме...')

    # Перехватываем вывод
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        call_command('import_new_anime', limit=limit)
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        logger.info(f'✅ Импорт завершен: {output}')
        return {'status': 'success', 'output': output}
        
    except Exception as e:
        sys.stdout = old_stdout
        logger.error(f'❌ Ошибка импорта: {e}')
        raise self.retry(exc=e, countdown=300)  # Повтор через 5 минут


@shared_task
def update_episode_durations_task(limit: int = 100):
    """
    Обновление длительностей и количества эпизодов
    """
    from scripts.update_episode_durations_from_kodik import process_anime_batch, get_anime_to_process
    
    logger.info('📺 Запуск обновления длительностей...')
    
    anime_list = get_anime_to_process(limit=limit)
    process_anime_batch(anime_list, batch_size=50)
    
    logger.info('✅ Обновление завершено')
    return {'status': 'success'}


@shared_task
def fix_episodes_count_task(limit: int = 1000):
    """
    Исправление количества эпизодов
    """
    from scripts.fix_episodes_count import get_episodes_count
    from anime.models import Anime
    
    logger.info('🔧 Запуск исправления количества эпизодов...')
    
    anime_list = Anime.objects.filter(
        shikimori_id__isnull=False
    ).exclude(shikimori_id=0)[:limit]
    
    updated = 0
    for anime in anime_list:
        try:
            new_episodes = get_episodes_count(anime.shikimori_id)
            if new_episodes and new_episodes != anime.episodes:
                anime.episodes = new_episodes
                anime.save(update_fields=['episodes', 'updated_at'])
                updated += 1
        except Exception:
            pass
    
    logger.info(f'✅ Исправлено эпизодов: {updated}')
    return {'status': 'success', 'updated': updated}
