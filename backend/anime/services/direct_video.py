"""
Сервис для получения прямых MP4 ссылок через anicli-api
"""
import asyncio
import aiohttp
from typing import Any


class DirectVideoService:
    """Сервис для извлечения прямых видео ссылок из разных источников"""
    
    @staticmethod
    async def get_anime_episode_url(
        anime_id: int,
        episode: int,
        season: int = 1,
        translation_id: str | None = None,
        quality: str = "720"
    ) -> dict[str, Any] | None:
        """
        Получить прямую MP4 ссылку на эпизод аниме
        
        Возвращает:
            {
                "url": "https://...",  # Прямая MP4 ссылка
                "quality": "720",
                "source": "kodik"
            }
        """
        try:
            # Используем anicli-api для получения ссылки
            from anicli_api.player.kodik import Kodik
            from anicli_api.player.aniboom import AniBoom
            
            # Формируем URL для парсера (это внутренний формат anicli-api)
            # Для Kodik обычно используется формат: https://kodik.cc/video/{video_id}
            # Но нам нужно сначала получить video_id через get_anime_m3u8
            
            # Пока используем упрощённый подход:
            # 1. Получаем m3u8 URL через существующий сервис
            # 2. Извлекаем прямую ссылку
            
            from anime.services.kodik_video import get_anime_m3u8
            
            user_ip = "1.1.1.1"  # Можно передавать из запроса
            m3u8_url = await asyncio.to_thread(
                get_anime_m3u8,
                anime_id=anime_id,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality
            )
            
            if not m3u8_url:
                return None
            
            # Пробуем извлечь прямую MP4 ссылку
            direct_url = await DirectVideoService._extract_direct_url(m3u8_url)
            
            if direct_url:
                return {
                    "url": direct_url,
                    "quality": quality,
                    "source": "kodik"
                }
            
            # Если не удалось извлечь, возвращаем m3u8 как fallback
            return {
                "url": m3u8_url,
                "quality": quality,
                "source": "kodik",
                "is_m3u8": True
            }
            
        except Exception as e:
            print(f"[DirectVideoService] Error: {e}")
            return None
    
    @staticmethod
    async def _extract_direct_url(m3u8_url: str) -> str | None:
        """
        Извлечь прямую MP4 ссылку из HLS плейлиста или Kodik
        
        Кодик иногда отдаёт прямые ссылки в формате:
        https://v.kodik.cc/.../video.mp4
        """
        try:
            # Проверяем, не является ли ссылка уже прямой
            if m3u8_url.endswith('.mp4'):
                return m3u8_url
            
            # Пробуем anicli-api парсер
            from anicli_api.player.kodik import Kodik
            
            # Для Kodik нужно преобразовать m3u8 в формат для парсера
            # Обычно это video_id из URL
            if "kodik.cc" in m3u8_url or "kodikapi" in m3u8_url:
                # Извлекаем video_id из URL
                # Пример: https://v.kodik.cc/.../session=.../index.m3u8
                # Нам нужен original video page URL
                
                # Пока используем простой fallback: заменяем .m3u8 на .mp4
                direct_url = m3u8_url.replace('.m3u8', '.mp4')
                
                # Проверяем доступность
                async with aiohttp.ClientSession() as session:
                    async with session.head(direct_url, allow_redirects=True) as resp:
                        if resp.status == 200:
                            return direct_url
                
                # Если не работает, пробуем через anicli-api
                try:
                    parser = Kodik()
                    # Нужно найти original URL плеера Kodik
                    # Это сложная задача, пока возвращаем None
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"[ExtractDirectURL] Error: {e}")
            return None
    
    @staticmethod
    async def get_screenshot_url(
        anime_id: int,
        episode: int,
        timestamp: float,
        translation_id: str | None = None,
        quality: str = "720"
    ) -> str | None:
        """
        Получить URL для скриншота
        
        Для ускорения можно:
        1. Использовать thumbnail из HLS плейлиста (если доступен)
        2. Генерировать скриншот через ffmpeg (текущий метод)
        """
        # Пока используем текущий метод с оптимизацией
        # В будущем можно добавить кэширование скриншотов
        from anime.services.kodik_video import get_anime_m3u8
        
        user_ip = "1.1.1.1"
        m3u8_url = await asyncio.to_thread(
            get_anime_m3u8,
            anime_id=anime_id,
            episode=episode,
            season=1,
            translation_id=translation_id,
            user_ip=user_ip,
            quality=quality
        )
        
        return m3u8_url  # Возвращаем m3u8 для генерации скриншота


# Синхронные обёртки для использования в Django views
def get_anime_episode_url_sync(*args, **kwargs):
    """Синхронная версия для Django views"""
    return asyncio.run(DirectVideoService.get_anime_episode_url(*args, **kwargs))


def get_screenshot_url_sync(*args, **kwargs):
    """Синхронная версия для Django views"""
    return asyncio.run(DirectVideoService.get_screenshot_url(*args, **kwargs))
