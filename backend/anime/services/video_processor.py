"""
Сервис для обработки видео: скриншоты и вырезка фрагментов
Использует yt-dlp и ffmpeg
"""

import os
import shutil
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from django.conf import settings
from django.core.files.base import ContentFile

FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "/usr/bin/ffprobe"


def check_requirements() -> Tuple[bool, bool]:
    """
    Проверка установленных yt-dlp и ffmpeg
    
    Returns:
        (yt_dlp_installed, ffmpeg_installed)
    """
    yt_dlp_ok = False
    ffmpeg_ok = False
    
    # Проверка yt-dlp
    try:
        result = subprocess.run(
            ['/usr/local/bin/yt-dlp', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        yt_dlp_ok = result.returncode == 0
    except Exception:
        pass
    
    # Проверка ffmpeg
    try:
        result = subprocess.run(
            ['/usr/bin/ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        ffmpeg_ok = result.returncode == 0
    except Exception:
        pass
    
    return yt_dlp_ok, ffmpeg_ok


def take_screenshot(
    video_url: str,
    timestamp: float,
    output_path: str,
    quality: int = 2
) -> Optional[str]:
    """
    Делает скриншот из видео на указанный момент
    
    Args:
        video_url: Прямая ссылка на видео
        timestamp: Время в секундах
        output_path: Путь для сохранения скриншота
        quality: Качество JPEG (1-31, где 1 - лучшее, 2-5 - отличное)
    
    Returns:
        Путь к файлу или None если ошибка
    """
    try:
        # Форматируем время в HH:MM:SS.mmm
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = timestamp % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        cmd = [
            "/usr/bin/ffmpeg",
            '-y',                      # Перезаписать если существует
            '-ss', time_str,           # ← input seek: быстрый прыжок до позиции ДО открытия файла
            '-i', video_url,           # Входной файл
            '-frames:v', '1',          # Только 1 кадр
            '-q:v', str(quality),      # Качество JPEG
            '-vf', 'scale=1280:-1',    # Ресайз до 1280px по ширине
            '-an',                     # без аудио
            '-f', 'image2',            # формат - изображение
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"[SCREENSHOT] ffmpeg error: {result.stderr}")
            return None
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            print(f"[SCREENSHOT] File not created or empty")
            return None
        
        return output_path
    
    except subprocess.TimeoutExpired:
        print(f"[SCREENSHOT] Timeout")
        return None
    except Exception as e:
        print(f"[SCREENSHOT] Error: {e}")
        return None


def download_clip(
    video_url: str,
    start_time: str,
    end_time: str,
    output_path: str,
    use_keyframes: bool = True
) -> Optional[str]:
    """
    Вырезает фрагмент видео через yt-dlp
    
    Args:
        video_url: Прямая ссылка на видео
        start_time: Время начала (SS, MM:SS, или HH:MM:SS)
        end_time: Время конца
        output_path: Путь для сохранения
        use_keyframes: Использовать ключевые кадры для точной обрезки
    
    Returns:
        Путь к файлу или None если ошибка
    """
    try:
        cmd = [
            '/usr/local/bin/yt-dlp',
            '--download-sections', f'*{start_time}-{end_time}',
            '--force-keyframes-at-cuts' if use_keyframes else None,
            '-o', output_path,
            '--no-playlist',
            '--no-warnings',
            video_url
        ]
        
        # Удаляем None значения
        cmd = [x for x in cmd if x is not None]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут максимум
        )
        
        if result.returncode != 0:
            print(f"[CLIP] yt-dlp error: {result.stderr}")
            return None
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            print(f"[CLIP] File not created or empty")
            return None
        
        return output_path
    
    except subprocess.TimeoutExpired:
        print(f"[CLIP] Timeout (300s)")
        return None
    except Exception as e:
        print(f"[CLIP] Error: {e}")
        return None


def screenshot_to_base64(file_path: str) -> Optional[str]:
    """
    Конвертирует изображение в base64
    
    Args:
        file_path: Путь к файлу изображения
    
    Returns:
        Base64 строка или None
    """
    import base64
    
    try:
        with open(file_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        print(f"[BASE64] Error: {e}")
        return None


def get_clip_duration(file_path: str) -> Optional[float]:
    """
    Получает длительность видео через ffprobe
    
    Args:
        file_path: Путь к видеофайлу
    
    Returns:
        Длительность в секундах или None
    """
    try:
        cmd = [
            "/usr/bin/ffprobe",
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        return None
    
    except Exception as e:
        print(f"[DURATION] Error: {e}")
        return None


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Удаляет старые файлы из директории
    
    Args:
        directory: Путь к директории
        max_age_hours: Максимальный возраст файлов в часах
    
    Returns:
        Количество удалённых файлов
    """
    import time
    
    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                
                if current_time - file_mtime > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
    
    return deleted_count
