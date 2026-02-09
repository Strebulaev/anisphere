from django.http import HttpResponseBadRequest, HttpResponseServerError, StreamingHttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any
from .models import Anime, Genre, Episode, Translation, WatchProgress
from .serializers import AnimeSerializer, GenreSerializer
from .services.anime_parser_service import (
    AnimeParserService, VideoStreamingService, CacheService, AnimeUpdateService
)

# Инициализация сервисов
anime_parser_service = AnimeParserService()
video_streaming_service = VideoStreamingService()
cache_service = CacheService()
anime_update_service = AnimeUpdateService()

# Функция для нормализации строки поиска
def normalize_search_string(text: str) -> str:
    """
    Нормализует строку для поиска:
    - Приводит к нижнему регистру
    - Удаляет лишние пробелы
    - Удаляет специальные символы
    """
    if not text:
        return ''
    # Приводим к нижнему регистру
    text = text.lower()
    # Заменяем ё на е
    text = text.replace('ё', 'е')
    # Удаляем все кроме букв, цифр и пробелов
    text = re.sub(r'[^а-яa-z0-9\s]', '', text)
    # Удаляем лишние пробелы
    text = ' '.join(text.split())
    return text

# Функция для нечеткого сравнения строк
def fuzzy_match(query: str, text: str, threshold: float = 0.6) -> float:
    """
    Сравнивает две строки с использованием SequenceMatcher
    Возвращает коэффициент похожести от 0 до 1
    """
    if not query or not text:
        return 0.0
    
    query_norm = normalize_search_string(query)
    text_norm = normalize_search_string(text)
    
    if not query_norm or not text_norm:
        return 0.0
    
    # Точное совпадение
    if query_norm == text_norm:
        return 1.0
    
    # Проверка вхождения
    if query_norm in text_norm or text_norm in query_norm:
        return 0.9
    
    # Нечеткое сравнение
    return SequenceMatcher(None, query_norm, text_norm).ratio()

# Функция для гибкого поиска аниме в БД
def fuzzy_search_anime(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Выполняет гибкий поиск аниме в базе данных
    Ищет по title_ru, title_en, title_jp
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        query = query.strip()
        print(f"  🔍 fuzzy_search_anime: query='{query}'")
        
        # Простой поиск по всем полям
        results = []
        seen_ids = set()
        
        # Ищем по каждому полю отдельно
        for field_name in ['title_ru', 'title_en', 'title_jp']:
            filter_kwargs = {f'{field_name}__icontains': query}
            queryset = Anime.objects.filter(**filter_kwargs)
            
            for anime in queryset:
                if anime.id not in seen_ids:
                    # Вычисляем рейтинг релевантности
                    score = 0.0
                    field_value = getattr(anime, field_name, '')
                    if field_value and query.lower() in field_value.lower():
                        score = 1.0
                        # Точное совпадение - выше рейтинг
                        if field_value.lower() == query.lower():
                            score = 1.2
                    
                    results.append({
                        'anime': anime,
                        'score': score,
                        'field': field_name
                    })
                    seen_ids.add(anime.id)
        
        # Сортируем по убыванию релевантности
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Ограничиваем количество результатов
        results = results[:limit]
        
        # Форматируем результат
        formatted_results = []
        for item in results:
            anime = item['anime']
            formatted_results.append({
                'id': anime.id,
                'title_ru': anime.title_ru or '',
                'title_en': anime.title_en or '',
                'title_jp': anime.title_jp or '',
                'year': anime.year,
                'status': anime.status,
                'episodes': anime.episodes,
                'score': anime.score,
                'poster_url': anime.poster_url,
                'description': anime.description,
                'match_score': item['score'],
                'source': 'database'
            })
            
        print(f"  ✅ fuzzy_search_anime: {len(formatted_results)} результатов")
        return formatted_results
        
    except Exception as e:
        print(f"❌ Ошибка в fuzzy_search_anime: {e}")
        import traceback
        traceback.print_exc()
        return []


# Глобальный сервис для видео (для обратной совместимости)
class VideoService:
    def get_direct_video(self, shikimori_id, episode, translation_id, quality):
        """Получение прямого видео из Kodik"""
        try:
            from anime_parsers_ru import KodikParser
            parser = KodikParser()
            video_url, q = parser.get_link(
                id=str(shikimori_id),
                id_type='shikimori',
                seria_num=episode,
                translation_id=translation_id
            )
            return f"http:{video_url}{quality}.mp4"
        except Exception as e:
            print(f"Ошибка получения видео из Kodik: {e}")
            return None
    
    def get_anilibria_video(self, title, episode):
        """Получение видео из Anilibria"""
        # Заглушка для Anilibria
        return None

video_service = VideoService()


@csrf_exempt
def proxy_video(request):
    """Прокси для видео"""
    video_url = request.GET.get('url')
    
    if not video_url:
        return HttpResponseBadRequest('No URL provided')
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://kodik.cc/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        
        return StreamingHttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('Content-Type', 'video/mp4'),
            status=response.status_code
        )
        
    except Exception as e:
        print(f"Proxy error: {e}")
        return HttpResponseServerError(str(e))


class AnimeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с аниме"""
    
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Настройка queryset с оптимизацией"""
        return Anime.objects.select_related()
    
    def list(self, request, *args, **kwargs):
        """Список аниме с пагинацией и фильтрацией"""
        print(f"\n=== AnimeViewSet.list called ===")
        print(f"Query params: {dict(request.query_params)}")
        
        queryset = self.get_queryset()
        print(f"Initial queryset count: {queryset.count()}")
        
        # Поиск по названию
        search = request.query_params.get('search')
        if search:
            print(f"Search filter: {search}")
            queryset = queryset.filter(
                title_ru__icontains=search
            ) | queryset.filter(
                title_en__icontains=search
            ) | queryset.filter(
                title_jp__icontains=search
            )
            print(f"After search filter count: {queryset.count()}")
            
        # Фильтр по статусу
        status = request.query_params.get('status')
        if status:
            print(f"Status filter: {status}")
            queryset = queryset.filter(status=status)
            print(f"After status filter count: {queryset.count()}")
        
        # Фильтр по жанрам - для JSONField используем contains
        genres = request.query_params.get('genres')
        if genres:
            print(f"Genres filter: {genres}")
            genre_ids = [int(g) for g in genres.split(',') if g.strip().isdigit()]
            print(f"Genre IDs: {genre_ids}")
            # Получаем названия жанров по ID
            genre_names = list(Genre.objects.filter(id__in=genre_ids).values_list('name', flat=True))
            print(f"Genre names: {genre_names}")
            
            # Для JSONField используем contains для поиска элементов в массиве
            if genre_names:
                # Ищем аниме, у которых есть хотя бы один из выбранных жанров
                for genre_name in genre_names:
                    queryset = queryset.filter(genres__contains=genre_name)
                # Убираем дубликаты после OR
                queryset = queryset.distinct()
                print(f"After genres filter count: {queryset.count()}")
        
        # Фильтр по году
        year_from = request.query_params.get('year_from')
        year_to = request.query_params.get('year_to')
        if year_from:
            print(f"Year from filter: {year_from}")
            queryset = queryset.filter(year__gte=int(year_from))
        if year_to:
            print(f"Year to filter: {year_to}")
            queryset = queryset.filter(year__lte=int(year_to))
        
        # Сортировка
        ordering = request.query_params.get('ordering', '-score')
        print(f"Ordering: {ordering}")
        queryset = queryset.order_by(ordering)
        
        # Пагинация
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        serializer = AnimeSerializer(queryset[start:end], many=True)
        
        print(f"Final count: {total_count}, page: {page}, page_size: {page_size}")
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Получение детальной информации об аниме"""
        try:
            anime = self.get_object()
            serializer = AnimeSerializer(anime)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'error': f'Ошибка получения аниме: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def episodes(self, request, pk=None):
        """Получение списка эпизодов для аниме"""
        try:
            anime = self.get_object()
            episodes = Episode.objects.filter(anime=anime).order_by('number')
            
            episodes_data = []
            for episode in episodes:
                episodes_data.append({
                    'id': episode.id,
                    'number': episode.number,
                    'title': episode.title,
                    'title_en': episode.title_en,
                    'description': episode.description,
                    'air_date': episode.air_date,
                })
            
            return Response({
                'anime_id': anime.id,
                'anime_title': anime.title_ru,
                'episodes': episodes_data,
                'total_episodes': len(episodes_data)
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения эпизодов: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def translations(self, request, pk=None):
        """Получение доступных переводов для аниме"""
        try:
            anime = self.get_object()
            translations = Translation.objects.filter(anime=anime, status='active')
            
            translations_data = []
            for translation in translations:
                translations_data.append({
                    'id': translation.id,
                    'name': translation.name,
                    'type': translation.get_translation_type_display(),
                    'studio_name': translation.studio_name,
                    'is_complete': translation.is_complete,
                    'episodes_count': translation.episodes_count,
                })
            
            return Response({
                'anime_id': anime.id,
                'anime_title': anime.title_ru,
                'translations': translations_data,
                'total_translations': len(translations_data)
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения переводов: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def get_video_link(self, request, pk=None):
        """Получение ссылки на видео для проигрывания"""
        print(f"\n=== GET_VIDEO_LINK для аниме ID: {pk} ===")
        
        try:
            anime = self.get_object()
            print(f"Аниме: {anime.title_ru or anime.title_en}")
            print(f"Shikimori ID: {anime.shikimori_id}")
            
            episode = int(request.query_params.get('episode', 1))
            translation_id = request.query_params.get('translation_id', '0')
            quality = request.query_params.get('quality', '720')
            
            print(f"Параметры: эпизод={episode}, перевод={translation_id}, качество={quality}")
            
            # Используем новый сервис для получения видео
            video_sources = video_streaming_service.get_video_sources(
                str(anime.shikimori_id), episode, translation_id
            )
            
            if not video_sources:
                return Response({
                    'error': 'Видео источники не найдены',
                    'anime_id': pk,
                    'video_url': None
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Выбираем подходящий источник
            for source_name, source_data in video_sources.items():
                if source_name == 'kodik' and source_data.get('video_url'):
                    video_url = source_data['video_url']
                    
                    # Для видео с Kodik используем прокси
                    proxy_url = f"http://localhost:8000/api/anime/proxy/video/?url={video_url}"
                    return Response({
                        'video_url': proxy_url,
                        'quality': quality,
                        'episode': episode,
                        'translation_id': translation_id,
                        'source': source_name,
                        'm3u8_url': source_data.get('m3u8_url'),
                        'note': 'Видео через прокси'
                    })
                elif source_name == 'aniboom' and source_data.get('mpd_content'):
                    return Response({
                        'video_url': None,  # MPD требует специальной обработки
                        'mpd_content': source_data['mpd_content'],
                        'quality': quality,
                        'episode': episode,
                        'translation_id': translation_id,
                        'source': source_name,
                        'format': 'mpd',
                        'note': 'MPD формат требует специального плеера'
                    })
            
            return Response({
                'error': 'Подходящий видео источник не найден',
                'available_sources': list(video_sources.keys())
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"❌ Ошибка в get_video_link: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Ошибка получения видео: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def update_from_parser(self, request, pk=None):
        """Обновление данных аниме из парсера"""
        try:
            anime = self.get_object()
            
            if not anime.shikimori_id:
                return Response({
                    'error': 'У аниме нет Shikimori ID для обновления'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем свежие данные из парсера
            fresh_data = anime_parser_service.get_anime_by_id(anime.shikimori_id, 'shikimori')
            
            if not fresh_data:
                return Response({
                    'error': 'Не удалось получить данные из парсера'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Импортируем обновленные данные
            updated_anime = anime_parser_service.import_anime_to_db(fresh_data, 'shikimori')
            
            return Response({
                'message': 'Данные аниме успешно обновлены',
                'anime_id': updated_anime.id,
                'title': updated_anime.title_ru,
                'episodes': updated_anime.episodes,
                'status': updated_anime.status
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка обновления аниме: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def watch_progress(self, request, pk=None):
        """Получение прогресса просмотра для аниме"""
        if not request.user.is_authenticated:
            return Response({
                'error': 'Требуется аутентификация'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            anime = self.get_object()
            progress = video_streaming_service.get_watch_progress(request.user, anime.id)
            
            return Response({
                'anime_id': anime.id,
                'anime_title': anime.title_ru,
                'progress': progress
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения прогресса: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def save_watch_progress(self, request, pk=None):
        """Сохранение прогресса просмотра"""
        if not request.user.is_authenticated:
            return Response({
                'error': 'Требуется аутентификация'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            anime = self.get_object()
            episode_id = request.data.get('episode_id')
            current_time = request.data.get('current_time', 0)
            duration = request.data.get('duration')
            
            if not episode_id:
                return Response({
                    'error': 'Требуется episode_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            progress = video_streaming_service.save_watch_progress(
                request.user, anime.id, episode_id, current_time, duration
            )
            
            if progress:
                return Response({
                    'message': 'Прогресс сохранен',
                    'progress': {
                        'episode_id': progress.episode.id,
                        'current_time': progress.current_time,
                        'is_completed': progress.is_completed
                    }
                })
            else:
                return Response({
                    'error': 'Не удалось сохранить прогресс'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Ошибка сохранения прогресса: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchAPIView(APIView):
    """API для поиска аниме с гибким поиском"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Поиск аниме с нечетким сопоставлением"""
        # Получаем query параметр
        raw_query = request.query_params.get('q', '')
        query = raw_query.strip()
        limit = int(request.query_params.get('limit', 20))
        
        print(f"\n{'='*60}")
        print(f"🔍 SearchAPIView вызван")
        print(f"   Raw query: '{raw_query}' (repr: {repr(raw_query)})")
        print(f"   Stripped query: '{query}' (repr: {repr(query)})")
        print(f"   Query params: {dict(request.query_params)}")
        print(f"   Limit: {limit}")
        print(f"{'='*60}\n")
        
        if not query:
            return Response({
                'error': 'Требуется параметр поиска q'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Ищем в локальной БД
            db_results = fuzzy_search_anime(query, limit)
            
            # Удаляем поле match_score перед отправкой
            for result in db_results:
                result.pop('match_score', None)
            
            print(f"\n✅ Поиск завершен: {len(db_results)} результатов\n")
            
            return Response({
                'query': query,
                'results': db_results,
                'total': len(db_results),
                'source': 'database'
            })
            
        except Exception as e:
            print(f"\n❌ Ошибка в SearchAPIView: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Ошибка поиска: {str(e)}',
                'query': query,
                'results': [],
                'total': 0,
                'source': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParserStatusAPIView(APIView):
    """API для проверки статуса парсеров"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Проверка состояния парсеров"""
        try:
            health_status = anime_parser_service.parser.health_check()
            
            return Response({
                'parsers': health_status,
                'total_parsers': len(health_status),
                'active_parsers': sum(1 for status in health_status.values() if status),
                'status': 'healthy' if any(health_status.values()) else 'unhealthy'
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка проверки статуса: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatesAPIView(APIView):
    """API для получения обновлений аниме"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Получение последних обновлений"""
        limit = int(request.query_params.get('limit', 50))
        
        try:
            updates = anime_update_service.get_recent_updates(limit)
            
            return Response({
                'updates': updates,
                'total': len(updates)
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения обновлений: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenresViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для получения списка всех жанров"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        try:
            genres = Genre.objects.all()
            serializer = GenreSerializer(genres, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения жанров: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )