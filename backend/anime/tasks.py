"""
Celery задачи для импорта аниме из Kodik и обработки видео
"""
import logging
import os
import tempfile
from pathlib import Path
from celery import shared_task
from datetime import datetime

from anime.models import ClipTask

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


@shared_task(bind=True, max_retries=2)
def process_clip_task(self, task_id: str):
    """
    Обработка задачи на вырезку фрагмента или создание скриншота
    
    Args:
        task_id: UUID задачи ClipTask
    """
    from .models import ClipTask
    from .services.video_processor import (
        take_screenshot,
        download_clip,
        screenshot_to_base64,
        get_clip_duration,
        check_requirements,
    )
    from .services.db_video_extractor import get_anime_video_links_by_id, get_best_quality_url
    from django.core.files.base import ContentFile
    from django.utils import timezone
    import os
    import tempfile
    from pathlib import Path
    
    try:
        task = ClipTask.objects.get(id=task_id)
    except ClipTask.DoesNotExist:
        print(f"[TASK] ClipTask {task_id} not found")
        return
    yt_dlp_ok, ffmpeg_ok = True, True
    # Проверяем требования
    # yt_dlp_ok, ffmpeg_ok = check_requirements()
    # if not yt_dlp_ok or not ffmpeg_ok:
    #     task.status = 'failed'
    #     task.error_message = f"Требования не выполнены: yt-dlp={yt_dlp_ok}, ffmpeg={ffmpeg_ok}"
    #     task.completed_at = timezone.now()
    #     task.save()
    #     print(f"[TASK] Requirements check failed: yt-dlp={yt_dlp_ok}, ffmpeg={ffmpeg_ok}")
    #     return
    
    # Обновляем статус
    task.status = 'processing'
    task.started_at = timezone.now()
    task.save()
    
    # Получаем данные о видео
    if not task.video_url:
        video_info = get_anime_video_links_by_id(task.anime_id)
        if video_info and video_info.get(task.quality):
            task.video_url = video_info[task.quality]
            task.save()
    
    if not task.video_url:
        task.status = 'failed'
        task.error_message = "Не удалось получить ссылку на видео"
        task.completed_at = timezone.now()
        task.save()
        return
    
    # Создаём временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        if task.task_type == 'screenshot':
            result = _process_screenshot(task, tmpdir_path)
        else:
            result = _process_video_clip(task, tmpdir_path)
        
        # Обработка результата
        if result['success']:
            task.status = 'ready'
            task.result_file = result['file']
            task.thumbnail = result.get('thumbnail')
            task.duration = result.get('duration')
            task.file_size = result.get('file_size')
            task.error_message = ''
            print(f"[TASK] Task {task_id} completed successfully")
        else:
            task.status = 'failed'
            task.error_message = result.get('error', 'Неизвестная ошибка')
            print(f"[TASK] Task {task_id} failed: {task.error_message}")
        
        task.completed_at = timezone.now()
        task.save()


def _process_screenshot(task: 'ClipTask', tmpdir: Path) -> dict:
    """Обработка задачи на создание скриншота"""
    from .services.video_processor import take_screenshot, screenshot_to_base64
    from django.core.files.base import ContentFile
    
    try:
        timestamp_str = f"{task.timestamp:.3f}".replace('.', '_')
        filename = f"screenshot_{task.anime.id}_{timestamp_str}.jpg"
        filepath = tmpdir / filename
        
        print(f"[SCREENSHOT] Creating screenshot at {task.timestamp}s")
        
        result_path = take_screenshot(
            video_url=task.video_url,
            timestamp=task.timestamp,
            output_path=str(filepath),
            quality=2
        )
        
        if not result_path:
            return {'success': False, 'error': 'Не удалось создать скриншот'}
        
        # Сохраняем в Django storage (upload_to сам добавит путь)
        with open(result_path, 'rb') as f:
            content = ContentFile(f.read())
            task.result_file.save(filename, content, save=False)
        
        file_size = os.path.getsize(result_path)
        
        # Thumbnail (миниатюра) - для скриншота используем тот же файл
        thumb_filename = f"thumb_{filename.replace('.jpg', '.png')}"
        with open(result_path, 'rb') as f:
            thumb_content = ContentFile(f.read())
            task.thumbnail.save(thumb_filename, thumb_content, save=False)
        
        return {
            'success': True,
            'file': task.result_file,
            'thumbnail': task.thumbnail,
            'file_size': file_size,
        }
    
    except Exception as e:
        print(f"[SCREENSHOT] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def _process_video_clip(task: 'ClipTask', tmpdir: Path) -> dict:
    """Обработка задачи на вырезку видео фрагмента"""
    from .services.video_processor import download_clip, take_screenshot, get_clip_duration
    from django.core.files.base import ContentFile
    import subprocess
    import shutil
    
    FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    
    try:
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
            return f"{minutes:02d}:{secs:05.2f}"
        
        start_str = format_time(task.start_time)
        end_str = format_time(task.end_time)
        
        safe_label = task.label.replace(' ', '_').replace('/', '_') if task.label else 'clip'
        is_mp3 = task.format == 'mp3'
        ext = 'mp3' if is_mp3 else 'mp4'
        filename = f"{safe_label}_{task.anime.id}_ep{task.episode}_{start_str.replace(':', '-')}-{end_str.replace(':', '-')}.{ext}"
        filepath = tmpdir / filename
        
        print(f"[CLIP] Downloading clip from {start_str} to {end_str} (format={task.format})")
        
        if is_mp3:
            # Для MP3 используем ffmpeg напрямую для извлечения аудио
            cmd = [
                "/usr/bin/ffmpeg",
                '-y',
                '-ss', start_str,
                '-i', task.video_url,
                '-to', end_str,
                '-vn',
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                '-threads', '2',
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"[CLIP] ffmpeg mp3 error: {result.stderr}")
                return {'success': False, 'error': f"Ошибка ffmpeg: {result.stderr[:200]}"}
            result_path = str(filepath)
        else:
            result_path = download_clip(
                video_url=task.video_url,
                start_time=start_str,
                end_time=end_str,
                output_path=str(filepath),
                use_keyframes=True
            )
        
        if not result_path or not os.path.exists(result_path) or os.path.getsize(result_path) == 0:
            return {'success': False, 'error': 'Не удалось скачать фрагмент'}
        
        # Сохраняем (upload_to сам добавит путь)
        with open(result_path, 'rb') as f:
            content = ContentFile(f.read())
            task.result_file.save(filename, content, save=False)
        
        file_size = os.path.getsize(result_path)
        duration = get_clip_duration(result_path) if not is_mp3 else (task.end_time - task.start_time)
        
        # Thumbnail - только для MP4
        if not is_mp3:
            thumbnail_path = tmpdir / f"thumb_{filename.replace('.mp4', '.jpg')}"
            
            thumb_result = take_screenshot(
                video_url=result_path,
                timestamp=0,
                output_path=str(thumbnail_path),
                quality=5
            )
            
            if thumb_result:
                with open(thumb_result, 'rb') as f:
                    thumb_content = ContentFile(f.read())
                    thumb_filename = f"thumb_{filename.replace('.mp4', '.jpg')}"
                    task.thumbnail.save(thumb_filename, thumb_content, save=False)
        
        return {
            'success': True,
            'file': task.result_file,
            'thumbnail': task.thumbnail,
            'duration': duration,
            'file_size': file_size,
        }
    
    except Exception as e:
        print(f"[CLIP] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_clips(max_age_hours: int = 168):  # 7 дней по умолчанию
    """Очистка старых клипов и скриншотов"""
    from .models import ClipTask
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    old_tasks = ClipTask.objects.filter(created_at__lt=cutoff, status__in=['ready', 'failed'])
    
    deleted_count = 0
    for task in old_tasks:
        if task.result_file:
            task.result_file.delete()
        if task.thumbnail:
            task.thumbnail.delete()
        task.delete()
        deleted_count += 1
    
    print(f"[CLEANUP] Deleted {deleted_count} old clip tasks")
    return deleted_count

