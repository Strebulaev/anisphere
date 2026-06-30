"""
Сервис для получения прямых ссылок на видео из MySQL базы Anilibria
"""

import json
import pymysql
from typing import Optional, Dict, Any
from django.conf import settings


# Конфигурация подключения к MySQL базе Anilibria
ANILIBRIA_DB_CONFIG = getattr(settings, 'ANILIBRIA_DB_CONFIG', {
    'host': '85.121.4.196',
    'database': 'anisphere.org_db',
    'user': 'u333333',
    'password': 'iQ8zH0uM9k',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
})


def get_anime_video_links(anime_title: str, use_russian: bool = True) -> Optional[Dict[str, str]]:
    """
    Получает прямые ссылки на видео из БД Anilibria
    
    Args:
        anime_title: Название аниме (русское или английское)
        use_russian: Если True, сначала ищем по title_ru, иначе по title_en
    
    Returns:
        Dict с ссылками по качествам {'480': url, '720': url, '1080': url} или None
    """
    try:
        conn = pymysql.connect(**ANILIBRIA_DB_CONFIG)
        cursor = conn.cursor()
        
        # Ищем аниме по названию
        if use_russian:
            cursor.execute("""
                SELECT download_links, title_ru, title_en 
                FROM anime_anime 
                WHERE title_ru = %s OR title_en = %s OR title_jp = %s
                LIMIT 1
            """, (anime_title, anime_title, anime_title))
        else:
            cursor.execute("""
                SELECT download_links, title_ru, title_en 
                FROM anime_anime 
                WHERE title_en = %s OR title_ru = %s
                LIMIT 1
            """, (anime_title, anime_title))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return None
        
        if not result.get('download_links'):
            return None
        
        # Парсим JSON
        links = json.loads(result['download_links'])
        
        return {
            '480': links.get('480'),
            '720': links.get('720'),
            '1080': links.get('1080'),
            'title_ru': result.get('title_ru'),
            'title_en': result.get('title_en'),
        }
    
    except Exception as e:
        print(f"[DB_VIDEO_EXTRACTOR] Error: {e}")
        return None


def get_anime_video_links_by_id(anime_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает прямые ссылки на видео по ID аниме в нашей БД
    
    Args:
        anime_id: ID аниме в локальной PostgreSQL базе
    
    Returns:
        Dict с информацией о видео или None
    """
    from anime.models import Anime
    
    try:
        anime = Anime.objects.get(id=anime_id)
        
        if not anime.title_ru and not anime.title_en:
            return None
        
        # Пробуем найти по русскому названию
        if anime.title_ru:
            links = get_anime_video_links(anime.title_ru, use_russian=True)
            if links:
                return {
                    **links,
                    'anime_id': anime_id,
                    'shikimori_id': anime.shikimori_id,
                }
        
        # Пробуем по английскому
        if anime.title_en:
            links = get_anime_video_links(anime.title_en, use_russian=False)
            if links:
                return {
                    **links,
                    'anime_id': anime_id,
                    'shikimori_id': anime.shikimori_id,
                }
        
        return None
    
    except Anime.DoesNotExist:
        return None
    except Exception as e:
        print(f"[DB_VIDEO_EXTRACTOR] Error by ID: {e}")
        return None


def get_best_quality_url(links: Dict[str, Optional[str]], preferred: str = '1080') -> Optional[str]:
    """
    Возвращает ссылку наилучшего доступного качества
    
    Args:
        links: Dict с ссылками по качествам
        preferred: Предпочтительное качество
    
    Returns:
        URL видео или None
    """
    quality_order = ['1080', '720', '480']
    
    # Начинаем с предпочтительного
    if preferred in quality_order:
        quality_order.remove(preferred)
        quality_order.insert(0, preferred)
    
    for quality in quality_order:
        url = links.get(quality)
        if url:
            return url
    
    return None
