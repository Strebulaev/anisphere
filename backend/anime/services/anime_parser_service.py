"""Сервис для парсинга аниме и работы с базой данных"""
import logging
import time
from typing import List, Dict, Optional
from django.core.cache import cache
from django.db import transaction
from ..models import Anime, Genre, Studio, Episode, VideoSource, Translation, WatchProgress
from .animeparsers_ru import AnimeParsersRuParser
from .image_service import ImageService

logger = logging.getLogger(__name__)

class AnimeParserService:
    """Сервис для парсинга данных об аниме"""
    
    def __init__(self):
        self.parser = AnimeParsersRuParser()
        self.cache_timeout = 3600  # 1 час кэширования
    
    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск аниме с кэшированием"""
        cache_key = f"search_{query}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Возвращаем кэшированный результат поиска для: {query}")
            return cached_result
        
        try:
            results = self.parser.search_anime(query, limit)
            cache.set(cache_key, results, self.cache_timeout)
            logger.info(f"Найдено {len(results)} результатов для запроса: {query}")
            return results
        except Exception as e:
            logger.error(f"Ошибка поиска аниме: {e}")
            return []
    
    def get_anime_by_id(self, external_id: int, source: str = 'shikimori') -> Optional[Dict]:
        """Получение аниме по внешнему ID"""
        cache_key = f"anime_{source}_{external_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            result = self.parser.get_anime_by_id(external_id, source)
            if result:
                cache.set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Ошибка получения аниме по ID {external_id}: {e}")
            return None
    
    def import_anime_to_db(self, anime_data: Dict, source: str = 'kodik') -> Anime:
        """Импорт аниме в базу данных"""
        try:
            with transaction.atomic():
                # Обрабатываем случаи с пустыми значениями
                title_en = anime_data.get('title_en')
                if title_en is None:
                    title_en = ''
                
                # Создаем или обновляем аниме
                anime, created = Anime.objects.update_or_create(
                    shikimori_id=anime_data.get('shikimori_id') or anime_data.get('id'),
                    defaults={
                        'title_ru': anime_data.get('title_ru', '') or 'Без названия',
                        'title_en': title_en,
                        'title_jp': anime_data.get('title_jp', '') or '',
                        'description': anime_data.get('description', ''),
                        'year': anime_data.get('year'),
                        'status': anime_data.get('status', 'finished'),
                        'kind': anime_data.get('kind', 'tv'),
                        'episodes': anime_data.get('episodes'),
                        'score': anime_data.get('score'),
                        'poster_url': anime_data.get('poster_url', ''),
                        
                        # Поля для франшиз
                        'movies': anime_data.get('movies', []),
                        'ovas': anime_data.get('ovas', []),
                        'movie_count': anime_data.get('movie_count', 0),
                        'ova_count': anime_data.get('ova_count', 0),
                        'total_items': anime_data.get('total_items', 1),
                        
                        'data_source': source,
                    }
                )
                
                # Загружаем постер если есть URL и нет локального постера
                if anime_data.get('poster_url') and not anime.poster:
                    self._download_anime_poster(anime, anime_data['poster_url'])
                
                # Обновляем жанры
                self._update_genres(anime, anime_data.get('genres', []))
                
                # Обновляем студии
                self._update_studios(anime, anime_data.get('studios', []))
                
                # Обновляем источники видео
                self._update_video_sources(anime, anime_data, source)
                
                logger.info(f"{'Создано' if created else 'Обновлено'} аниме: {anime.title_ru}")
                return anime
                
        except Exception as e:
            logger.error(f"Ошибка импорта аниме {anime_data.get('title_ru', 'Unknown')}: {e}")
            raise
    
    def _download_anime_poster(self, anime: Anime, poster_url: str):
        """Загрузка постера аниме"""
        try:
            image_service = ImageService()
            poster_path = image_service.download_poster_safe(poster_url, anime.id, anime.title_ru)
            
            if poster_path:
                # Удаляем старый постер если есть
                if anime.poster:
                    image_service.cleanup_old_poster(anime.poster.name)
                
                # Обновляем аниме с новым постером
                anime.poster.name = poster_path
                anime.save(update_fields=['poster'])
                logger.info(f"Постер загружен для {anime.title_ru}")
            else:
                logger.warning(f"Не удалось загрузить постер для {anime.title_ru}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки постера для {anime.title_ru}: {e}")
    
    def _update_genres(self, anime: Anime, genres_data: List[Dict]):
        """Обновление жанров аниме (JSON поле)"""
        try:
            # Извлекаем названия жанров из разных форматов данных
            genre_names = []
            
            if isinstance(genres_data, list):
                for genre in genres_data:
                    if isinstance(genre, dict):
                        name = genre.get('name') or genre.get('title') or genre.get('russian')
                        if name:
                            genre_names.append(name)
                    elif isinstance(genre, str):
                        genre_names.append(genre)
            
            # Убираем дубликаты и сохраняем в JSON поле
            unique_genres = list(set(genre_names))
            anime.genres = unique_genres
            anime.save(update_fields=['genres'])
            
            logger.debug(f"Обновлены жанры для {anime.title_ru}: {unique_genres}")
            
        except Exception as e:
            logger.warning(f"Ошибка обновления жанров для {anime.title_ru}: {e}")
    
    def _update_studios(self, anime: Anime, studios_data: List[Dict]):
        """Обновление студий аниме (JSON поле)"""
        try:
            # Извлекаем названия студий из разных форматов данных
            studio_names = []
            
            if isinstance(studios_data, list):
                for studio in studios_data:
                    if isinstance(studio, dict):
                        name = studio.get('name') or studio.get('title') or studio.get('russian')
                        if name:
                            studio_names.append(name)
                    elif isinstance(studio, str):
                        studio_names.append(studio)
            
            # Убираем дубликаты и сохраняем в JSON поле
            unique_studios = list(set(studio_names))
            anime.studios = unique_studios
            anime.save(update_fields=['studios'])
            
            logger.debug(f"Обновлены студии для {anime.title_ru}: {unique_studios}")
            
        except Exception as e:
            logger.warning(f"Ошибка обновления студий для {anime.title_ru}: {e}")
    
    def _update_video_sources(self, anime: Anime, anime_data: Dict, source: str):
        """Обновление источников видео"""
        try:
            # Получаем shikimori_id для получения эпизодов
            shikimori_id = anime_data.get('shikimori_id')
            
            # Обновляем информацию об эпизодах только если есть shikimori_id и источник не kodik
            if shikimori_id and source != 'kodik':
                self._update_episodes(anime, shikimori_id, source)
            
            # Обновляем источники видео
            if anime_data.get('video_sources'):
                self._save_video_sources(anime, anime_data['video_sources'])
                
        except Exception as e:
            logger.warning(f"Ошибка обновления источников видео для {anime.title_ru}: {e}")
    
    def _update_episodes(self, anime: Anime, shikimori_id: str, source: str):
        """Обновление информации об эпизодах"""
        try:
            # Для источника 'kodik' пропускаем обновление эпизодов
            if source == 'kodik':
                logger.debug(f"Пропускаем обновление эпизодов для {anime.title_ru} (источник: kodik)")
                return
                
            episodes_data = self.parser.get_episodes_info(str(shikimori_id), 'aniboom')
            
            for ep_data in episodes_data:
                Episode.objects.update_or_create(
                    anime=anime,
                    number=int(ep_data['num']),
                    defaults={
                        'title': ep_data.get('title', ''),
                        'air_date': self._parse_date(ep_data.get('date')),
                    }
                )
                
        except Exception as e:
            logger.debug(f"Не удалось обновить эпизоды для {anime.title_ru}: {e}")
    
    def _parse_date(self, date_str: str) -> Optional[object]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
        
        try:
            # Простой парсинг даты в формате "2026-01-15"
            from datetime import datetime
            return datetime.strptime(date_str.split()[0], '%Y-%m-%d').date()
        except (ValueError, IndexError):
            return None

    def get_all_anime(self, source: str = 'kodik', page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение всех аниме с пагинацией"""
        cache_key = f"all_anime_{source}_{page}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Возвращаем кэшированный результат для всех аниме: {source}")
            return cached_result
        
        try:
            results = self.parser.get_all_anime(source, page, limit)
            cache.set(cache_key, results, self.cache_timeout)
            logger.info(f"Получено {len(results)} аниме из {source}")
            return results
        except Exception as e:
            logger.error(f"Ошибка получения всех аниме: {e}")
            return []
    
class VideoStreamingService:
    """Сервис для управления потоковым видео"""
    
    def __init__(self):
        self.parser = AnimeParsersRuParser()
        self.cache_timeout = 1800  # 30 минут кэширования
    
    def get_video_sources(self, anime_id: str, episode_num: int = 1, translation_id: str = "0") -> Dict:
        """Получение источников видео для эпизода"""
        cache_key = f"video_sources_{anime_id}_{episode_num}_{translation_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            video_sources = self.parser.get_video_sources(anime_id, episode_num, translation_id)
            
            # Кэшируем результат
            cache.set(cache_key, video_sources, self.cache_timeout)
            return video_sources
            
        except Exception as e:
            logger.error(f"Ошибка получения видео источников: {e}")
            return {}
    
    def get_streaming_url(self, anime_id: str, episode_num: int = 1, translation_id: str = "0", quality: str = "720") -> Optional[str]:
        """Получение прямой ссылки на стрим"""
        video_sources = self.get_video_sources(anime_id, episode_num, translation_id)
        
        # Ищем подходящий источник
        for source_name, source_data in video_sources.items():
            if source_name == 'kodik':
                # Для Kodik используем M3U8 плейлист
                if source_data.get('m3u8_url'):
                    return source_data['m3u8_url']
                elif source_data.get('video_url'):
                    return source_data['video_url']
            elif source_name == 'aniboom':
                # Для Aniboom возвращаем MPD контент
                if source_data.get('mpd_content'):
                    return source_data['mpd_content']
        
        return None
    
    def save_watch_progress(self, user, anime_id: int, episode_id: int, current_time: int, duration: int = None):
        """Сохранение прогресса просмотра"""
        try:
            anime = Anime.objects.get(id=anime_id)
            episode = Episode.objects.get(id=episode_id)
            
            with transaction.atomic():
                progress, created = WatchProgress.objects.update_or_create(
                    user=user,
                    episode=episode,
                    defaults={
                        'current_time': current_time,
                        'duration': duration,
                        'is_completed': duration and current_time >= duration * 0.9,
                        'watch_count': 1 if created else WatchProgress.objects.get(id=progress.id).watch_count + 1,
                    }
                )
                
                logger.info(f"Сохранен прогресс просмотра для {user.username}: {progress.current_time}s")
                return progress
                
        except (Anime.DoesNotExist, Episode.DoesNotExist) as e:
            logger.error(f"Ошибка сохранения прогресса: {e}")
            return None
    
    def get_watch_progress(self, user, anime_id: int) -> List[Dict]:
        """Получение прогресса просмотра для аниме"""
        try:
            progress_list = WatchProgress.objects.filter(
                user=user,
                anime_id=anime_id
            ).select_related('episode', 'translation').order_by('episode__number')
            
            return [
                {
                    'episode_id': p.episode.id,
                    'episode_number': p.episode.number,
                    'current_time': p.current_time,
                    'duration': p.duration,
                    'is_completed': p.is_completed,
                    'translation_name': p.translation.name if p.translation else None,
                    'last_watched': p.last_watched,
                }
                for p in progress_list
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения прогресса: {e}")
            return []
    
    def get_video_qualities(self, anime_id: str, source: str = 'kodik') -> List[Dict]:
        """Получение доступных качеств видео"""
        try:
            video_sources = VideoSource.objects.filter(
                anime_id=anime_id,
                source=source,
                is_available=True
            ).select_related('video_source').prefetch_related('qualities')
            
            qualities = []
            for vs in video_sources:
                for quality in vs.qualities.filter(is_available=True):
                    qualities.append({
                        'quality': quality.quality,
                        'resolution': quality.resolution,
                        'video_url': quality.video_url,
                        'm3u8_url': quality.m3u8_url,
                    })
            
            return qualities
            
        except Exception as e:
            logger.error(f"Ошибка получения качеств видео: {e}")
            return []

class CacheService:
    """Сервис для управления кэшированием"""
    
    def __init__(self):
        self.default_timeout = 3600  # 1 час
    
    def cache_anime_data(self, anime_id: int, data: Dict, timeout: int = None):
        """Кэширование данных аниме"""
        cache_key = f"anime_{anime_id}"
        cache.set(cache_key, data, timeout or self.default_timeout)
    
    def get_cached_anime_data(self, anime_id: int) -> Optional[Dict]:
        """Получение кэшированных данных аниме"""
        return cache.get(f"anime_{anime_id}")
    
    def cache_search_results(self, query: str, results: List[Dict], timeout: int = None):
        """Кэширование результатов поиска"""
        cache_key = f"search_{hash(query)}"
        cache.set(cache_key, results, timeout or self.default_timeout)
    
    def get_cached_search_results(self, query: str) -> Optional[List[Dict]]:
        """Получение кэшированных результатов поиска"""
        return cache.get(f"search_{hash(query)}")
    
    def invalidate_anime_cache(self, anime_id: int):
        """Инвалидация кэша аниме"""
        cache.delete(f"anime_{anime_id}")
        # Также удаляем связанные кэши
        cache.delete(f"video_sources_{anime_id}")
    
    def clear_all_cache(self):
        """Очистка всего кэша"""
        cache.clear()
        logger.info("Весь кэш очищен")

class AnimeUpdateService:
    """Сервис для отслеживания обновлений аниме"""
    
    def __init__(self):
        self.parser = AnimeParsersRuParser()
    
    def check_for_updates(self, anime: Anime) -> List[Dict]:
        """Проверка обновлений для аниме"""
        updates = []
        
        try:
            if anime.shikimori_id:
                # Получаем свежие данные
                fresh_data = self.parser.get_anime_by_id(anime.shikimori_id, 'shikimori')
                
                if fresh_data:
                    # Проверяем изменения в статусе
                    if fresh_data.get('status') != anime.status:
                        updates.append({
                            'type': 'status_change',
                            'description': f'Статус изменен с {anime.status} на {fresh_data["status"]}',
                            'old_value': anime.status,
                            'new_value': fresh_data['status']
                        })
                    
                    # Проверяем изменения в количестве эпизодов
                    if fresh_data.get('episodes') and fresh_data['episodes'] != anime.episodes:
                        updates.append({
                            'type': 'new_episode',
                            'description': f'Количество эпизодов: {anime.episodes} → {fresh_data["episodes"]}',
                            'old_value': anime.episodes,
                            'new_value': fresh_data['episodes']
                        })
                    
                    # Проверяем изменения в рейтинге
                    if fresh_data.get('score') and fresh_data['score'] != anime.score:
                        updates.append({
                            'type': 'info_update',
                            'description': f'Рейтинг обновлен: {anime.score} → {fresh_data["score"]}',
                            'old_value': anime.score,
                            'new_value': fresh_data['score']
                        })
        
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений для {anime.title_ru}: {e}")
        
        return updates
    
    def save_updates(self, anime: Anime, updates: List[Dict]):
        """Сохранение обновлений в базу данных"""
        from ..models import AnimeUpdate
        
        for update_data in updates:
            AnimeUpdate.objects.create(
                anime=anime,
                update_type=update_data['type'],
                description=update_data['description']
            )
        
        if updates:
            logger.info(f"Сохранено {len(updates)} обновлений для {anime.title_ru}")
    
    def get_recent_updates(self, limit: int = 50) -> List[Dict]:
        """Получение последних обновлений"""
        from ..models import AnimeUpdate
        
        recent_updates = AnimeUpdate.objects.select_related('anime').order_by('-created_at')[:limit]
        
        return [
            {
                'id': update.id,
                'anime_title': update.anime.title_ru,
                'anime_id': update.anime.id,
                'update_type': update.get_update_type_display(),
                'description': update.description,
                'episode_number': update.episode_number,
                'created_at': update.created_at,
            }
            for update in recent_updates
        ]