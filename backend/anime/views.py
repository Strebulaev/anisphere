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

from users.models import UserLibrary
from .models import Anime, Genre, Episode, Translation, WatchProgress, CustomDub
from .serializers import AnimeSerializer, AnimeDetailSerializer, GenreSerializer
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

# Функция для простого поиска аниме в БД (по строгому содержанию)
def fuzzy_search_anime(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Выполняет простой поиск аниме в базе данных по строгому содержанию
    Ищет по title_ru, title_en, title_jp (case-insensitive)
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        query = query.strip()
        print(f"  🔍 fuzzy_search_anime: query='{query}'")
        
        from django.db.models import Q
        
        # Простой поиск по всем полям (icontains - case-insensitive)
        queryset = Anime.objects.filter(
            Q(title_ru__icontains=query) |
            Q(title_en__icontains=query) |
            Q(title_jp__icontains=query)
        )
        
        # Сортируем по рейтингу
        queryset = queryset.order_by('-score')[:limit]
        
        # Форматируем результат
        formatted_results = []
        for anime in queryset:
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
                'match_score': 1.0,
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
            serializer = AnimeDetailSerializer(anime)
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
    def kodik_player(self, request, pk=None):
        """Получение ссылки на Kodik плеер через официальное API"""
        print(f"\n=== KODIK_PLAYER для аниме ID: {pk} ===")

        try:
            anime = self.get_object()
            print(f"Аниме: {anime.title_ru or anime.title_en}")
            print(f"Shikimori ID: {anime.shikimori_id}")
            
            # Сначала проверяем, есть ли уже kodik_link
            if anime.kodik_link:
                print(f"Используем существующий kodik_link: {anime.kodik_link}")
                return Response({
                    'kodik_link': anime.kodik_link,
                    'source': 'database'
                })

            # Если нет, ищем через официальное API Kodik
            if not anime.shikimori_id:
                return Response({
                    'error': 'У аниме нет Shikimori ID для поиска в Kodik'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
            KODIK_API_BASE = 'https://kodikapi.com'

            # Ищем аниме через /search API
            search_params = {
                'token': KODIK_API_TOKEN,
                'shikimori_id': anime.shikimori_id,
                'with_material_data': True,
                'limit': 1
            }

            print(f"Поиск в Kodik API: {search_params}")

            response = requests.get(f'{KODIK_API_BASE}/search', params=search_params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if not results:
                return Response({
                    'error': 'Аниме не найдено в Kodik API',
                    'shikimori_id': anime.shikimori_id
                }, status=status.HTTP_404_NOT_FOUND)

            # Получаем первый результат
            result = results[0]
            kodik_link = result.get('link')

            if not kodik_link:
                return Response({
                    'error': 'Ссылка на плеер не найдена в ответе Kodik',
                    'result': result
                }, status=status.HTTP_404_NOT_FOUND)

            # Обновляем kodik_link в базе данных
            anime.kodik_link = kodik_link
            anime.kodik_id = result.get('id', '')
            anime.quality = result.get('quality', '')
            anime.screenshots = result.get('screenshots', [])
            anime.seasons = result.get('seasons', {})
            anime.last_season = result.get('last_season')
            anime.last_episode = result.get('last_episode')
            anime.save()

            print(f"Найден kodik_link: {kodik_link}")
            print(f"Сохранены данные: quality={anime.quality}, last_episode={anime.last_episode}")

            return Response({
                'kodik_link': kodik_link,
                'source': 'kodik_api',
                'quality': anime.quality,
                'last_episode': anime.last_episode,
                'seasons': anime.seasons
            })
            
        except requests.RequestException as e:
            print(f"❌ Ошибка запроса к Kodik API: {e}")
            return Response({
                'error': f'Ошибка запроса к Kodik API: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            print(f"❌ Ошибка в kodik_player: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Ошибка получения плеера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def get_video_link(self, request, pk=None):
        """Получение ссылки на видео для проигрывания (legacy)"""
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
                    proxy_url = f"https://anisphere.ru/api/anime/proxy/video/?url={video_url}"
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


class KodikImportView(APIView):
    """API для импорта аниме из Kodik"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        """Импорт аниме из Kodik"""
        from anime.models import Anime
        
        data = request.data
        
        # Проверяем, это одиночный импорт или массовый
        if 'shikimori_id' in data:
            # Одиночный импорт
            return self._import_single_anime(data)
        else:
            # Массовый импорт
            return self._import_all_anime(data)
    
    def _import_single_anime(self, data):
        """Импорт одного аниме"""
        try:
            shikimori_id = data.get('shikimori_id')
            kodik_data = data.get('kodik_data')
            
            if not shikimori_id:
                return Response({
                    'error': 'Требуется shikimori_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Если переданы данные Kodik, импортируем их
            if kodik_data:
                anime = self._create_anime_from_kodik(kodik_data)
                return Response({
                    'message': 'Аниме успешно импортировано',
                    'anime_id': anime.id,
                    'title': anime.title_ru
                })
            
            return Response({
                'error': 'Требуются данные Kodik'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Ошибка импорта: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _import_all_anime(self, data):
        """Массовый импорт всех аниме"""
        from backend.scripts.import_from_kodik import fetch_all_anime, import_anime
        
        try:
            limit = data.get('limit', 0)
            
            # Загружаем все аниме из Kodik
            all_anime = fetch_all_anime()
            
            if limit > 0:
                all_anime = all_anime[:limit]
            
            imported = 0
            updated = 0
            errors = []
            
            for kodik_anime in all_anime:
                try:
                    anime = import_anime(kodik_anime)
                    imported += 1
                except Exception as e:
                    errors.append({
                        'title': kodik_anime.get('title', 'Unknown'),
                        'error': str(e)
                    })
            
            return Response({
                'message': 'Импорт завершен',
                'total_processed': len(all_anime),
                'imported': imported,
                'errors': errors[:10]  # Первые 10 ошибок
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка массового импорта: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_anime_from_kodik(self, kodik_data):
        """Создание аниме из данных Kodik"""
        from anime.models import Anime
        
        material_data = kodik_data.get('material_data', {})
        
        # Определяем количество эпизодов
        episodes_count = (
            material_data.get('episodes_total') or
            kodik_data.get('episodes_count') or
            1
        )
        
        # Жанры
        genre_names = material_data.get('anime_genres') or material_data.get('genres') or []
        
        # Студии
        studio_names = material_data.get('anime_studios') or []
        
        # Постер
        poster_url = (
            material_data.get('anime_poster_url') or
            material_data.get('poster_url') or
            ''
        )
        
        # Рейтинг
        score = (
            material_data.get('shikimori_rating') or
            material_data.get('kinopoisk_rating') or
            0.0
        )
        
        # Описание
        description = (
            material_data.get('anime_description') or
            material_data.get('description') or
            ''
        )
        
        # Маппинг статуса
        status_map = {
            'anons': 'announced',
            'ongoing': 'ongoing',
            'released': 'finished',
            'discontinued': 'canceled'
        }
        status = status_map.get(material_data.get('anime_status', 'released'), 'finished')
        
        # Маппинг типа
        kind_map = {
            'tv': 'tv',
            'tv_13': 'tv',
            'tv_24': 'tv',
            'tv_48': 'tv',
            'movie': 'movie',
            'ova': 'ova',
            'ona': 'ona',
            'special': 'special',
            'music': 'music'
        }
        kind = kind_map.get(material_data.get('anime_kind') or kodik_data.get('type', 'tv'), 'tv')
        
        # Создаем или обновляем аниме
        anime, created = Anime.objects.update_or_create(
            shikimori_id=kodik_data.get('shikimori_id'),
            defaults={
                'title_ru': kodik_data.get('title', ''),
                'title_en': kodik_data.get('title_orig', ''),
                'title_jp': kodik_data.get('other_title', ''),
                'description': description,
                'year': kodik_data.get('year'),
                'status': status,
                'kind': kind,
                'episodes': episodes_count,
                'score': score,
                'poster_url': poster_url,
                'genres': genre_names,
                'studios': studio_names,
                'data_source': 'kodik',
                'movies': [],
                'ovas': [],
                'movie_count': 0,
                'ova_count': 0,
                'total_items': 1,
            }
        )
        
        return anime


class KodikFiltersView(APIView):
    """API для получения фильтров Kodik"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Получение доступных фильтров"""
        import requests
        
        KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
        KODIK_API_BASE = 'https://kodikapi.com'
        
        try:
            # Получаем фильтры параллельно
            genres_response = requests.get(f'{KODIK_API_BASE}/genres', params={
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'genres_type': 'shikimori',
                'sort': 'title'
            })
            
            years_response = requests.get(f'{KODIK_API_BASE}/years', params={
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'sort': 'year',
                'order': 'desc'
            })
            
            studios_response = requests.get(f'{KODIK_API_BASE}/anime_studios', params={
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'sort': 'title'
            })
            
            translations_response = requests.get(f'{KODIK_API_BASE}/translations/v2', params={
                'token': KODIK_API_TOKEN,
                'types': 'anime-serial,anime',
                'sort': 'title'
            })
            
            return Response({
                'genres': genres_response.json().get('results', []),
                'years': years_response.json().get('results', []),
                'studios': studios_response.json().get('results', []),
                'translations': translations_response.json().get('results', [])
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения фильтров: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KodikTranslationsView(APIView):
    """API для получения озвучек из Kodik API"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk):
        """Получение списка озвучек для аниме через Kodik API"""
        try:
            anime = Anime.objects.get(pk=pk)
            
            if not anime.shikimori_id:
                return Response({
                    'error': 'У аниме нет Shikimori ID'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
            KODIK_API_BASE = 'https://kodikapi.com'
            
            # Ищем аниме через Kodik API
            search_params = {
                'token': KODIK_API_TOKEN,
                'shikimori_id': anime.shikimori_id,
                'with_episodes_data': False,
                'limit': 100
            }
            
            response = requests.get(f'{KODIK_API_BASE}/search', params=search_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                return Response({
                    'translations': [],
                    'total': 0
                })
            
            # Группируем по переводам
            translations_map = {}
            
            for result in results:
                translation = result.get('translation', {})
                if not translation:
                    continue
                
                translation_id = translation.get('id')
                translation_name = translation.get('title', 'Неизвестно')
                translation_type = translation.get('type', 'voice')
                
                if translation_id not in translations_map:
                    translations_map[translation_id] = {
                        'id': translation_id,
                        'name': translation_name,
                        'type': translation_type,
                        'quality': result.get('quality', ''),
                        'episodes_done': 0,
                        'total_episodes': result.get('episodes_count') or anime.episodes,
                        'is_complete': False,
                        'kodik_link': result.get('link', ''),
                        'logo': None
                    }
                
                # Обновляем информацию о серии
                t = translations_map[translation_id]
                episodes = result.get('episodes_count') or 0
                if episodes > t['episodes_done']:
                    t['episodes_done'] = episodes
            
            translations = list(translations_map.values())
            
            # Сортируем по количеству серий (сначала самые полные)
            translations.sort(key=lambda x: x['episodes_done'], reverse=True)
            
            return Response({
                'translations': translations,
                'total': len(translations)
            })
            
        except Anime.DoesNotExist:
            return Response({
                'error': 'Аниме не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        except requests.RequestException as e:
            return Response({
                'error': f'Ошибка запроса к Kodik API: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'error': f'Ошибка получения озвучек: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDubListView(APIView):
    """API для списка пользовательских озвучек"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, anime_id):
        """Получение списка пользовательских озвучек для аниме"""
        try:
            anime = Anime.objects.get(pk=anime_id)
            
            # Получаем только одобренные пользовательские озвучки
            custom_dubs = CustomDub.objects.filter(
                anime=anime,
                status='approved'
            ).order_by('-rating', '-created_at')
            
            dubs_data = []
            for dub in custom_dubs:
                dubs_data.append({
                    'id': dub.id,
                    'name': dub.name,
                    'studio': dub.studio,
                    'description': dub.description,
                    'quality': dub.quality,
                    'logo': dub.logo_url,
                    'episodes_done': dub.episodes_done,
                    'total_episodes': dub.total_episodes or anime.episodes,
                    'is_complete': dub.is_complete,
                    'is_custom': True,
                    'rating': dub.rating,
                    'views_count': dub.views_count
                })
            
            return Response({
                'dubs': dubs_data,
                'total': len(dubs_data)
            })
            
        except Anime.DoesNotExist:
            return Response({
                'error': 'Аниме не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, anime_id):
        """Добавление пользовательской озвучки"""
        if not request.user.is_authenticated:
            return Response({
                'error': 'Требуется авторизация'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            anime = Anime.objects.get(pk=anime_id)
            
            name = request.data.get('name')
            studio = request.data.get('studio', '')
            quality = request.data.get('quality')
            video_url = request.data.get('video_url')
            logo_url = request.data.get('logo_url', '')
            description = request.data.get('description', '')
            episodes_done = request.data.get('episodes_done', 0)
            is_complete = request.data.get('is_complete', False)
            
            if not name or not quality or not video_url:
                return Response({
                    'error': 'Необходимо указать название, качество и ссылку на видео'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, существует ли уже такая озвучка
            existing_dub = CustomDub.objects.filter(
                anime=anime,
                created_by=request.user,
                name=name
            ).first()
            
            if existing_dub:
                return Response({
                    'error': 'Вы уже добавляли озвучку с таким названием'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Создаем пользовательскую озвучку
            dub = CustomDub.objects.create(
                anime=anime,
                created_by=request.user,
                name=name,
                studio=studio or name,
                description=description,
                quality=quality,
                video_url=video_url,
                logo_url=logo_url,
                episodes_done=episodes_done or 0,
                total_episodes=anime.episodes,
                is_complete=is_complete,
                status='pending'  # На модерации
            )
            
            return Response({
                'message': 'Озвучка отправлена на модерацию',
                'dub_id': dub.id,
                'status': dub.status
            }, status=status.HTTP_201_CREATED)
            
        except Anime.DoesNotExist:
            return Response({
                'error': 'Аниме не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Ошибка добавления озвучки: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDubDetailView(APIView):
    """API для детальной информации о пользовательской озвучке"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, anime_id, dub_id):
        """Получение ссылки на видео для пользовательской озвучки"""
        try:
            dub = CustomDub.objects.get(
                id=dub_id,
                anime_id=anime_id,
                status='approved'
            )
            
            # Увеличиваем счетчик просмотров
            dub.views_count += 1
            dub.save(update_fields=['views_count'])
            
            return Response({
                'video_url': dub.video_url,
                'quality': dub.quality,
                'name': dub.name,
                'studio': dub.studio,
                'logo': dub.logo_url
            })
            
        except CustomDub.DoesNotExist:
            return Response({
                'error': 'Озвучка не найдена или не одобрена'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Ошибка получения видео: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLibraryView(APIView):
    """API для библиотеки пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Получение библиотеки пользователя"""
        try:
            library_items = UserLibrary.objects.filter(user=request.user).select_related('anime')
            
            library_data = []
            for item in library_items:
                library_data.append({
                    'id': item.id,
                    'anime': {
                        'id': item.anime.id,
                        'title_ru': item.anime.title_ru,
                        'title_en': item.anime.title_en,
                        'poster_url': item.anime.poster_url,
                        'year': item.anime.year,
                        'episodes': item.anime.episodes,
                        'score': item.anime.score,
                        'kind': item.anime.kind,
                        'status': item.anime.status
                    },
                    'status': item.status,
                    'last_episode': item.last_episode,
                    'watched_episodes': item.watched_episodes,
                    'total_progress': item.total_progress,
                    'user_score': item.user_score,
                    'last_watched_at': item.last_watched_at.isoformat(),
                    'completed_at': item.completed_at.isoformat() if item.completed_at else None,
                    'created_at': item.created_at.isoformat()
                })
            
            return Response({
                'library': library_data,
                'total': len(library_data)
            })
            
        except Exception as e:
            return Response({
                'error': f'Ошибка получения библиотеки: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Добавление аниме в библиотеку"""
        try:
            anime_id = request.data.get('anime')
            status = request.data.get('status', 'want_to_watch')
            
            if not anime_id:
                return Response({
                    'error': 'Не указан ID аниме'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            anime = Anime.objects.get(pk=anime_id)
            
            # Проверяем, не добавлено ли уже
            existing = UserLibrary.objects.filter(user=request.user, anime=anime).first()
            if existing:
                return Response({
                    'error': 'Аниме уже добавлено в библиотеку'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Создаем запись
            library_item = UserLibrary.objects.create(
                user=request.user,
                anime=anime,
                status=status
            )
            
            return Response({
                'message': 'Аниме добавлено в библиотеку',
                'id': library_item.id
            }, status=status.HTTP_201_CREATED)
            
        except Anime.DoesNotExist:
            return Response({
                'error': 'Аниме не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Ошибка добавления: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLibraryDetailView(APIView):
    """API для детальной работы с записью библиотеки"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """Получение информации о записи"""
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            
            return Response({
                'id': item.id,
                'anime': {
                    'id': item.anime.id,
                    'title_ru': item.anime.title_ru,
                    'title_en': item.anime.title_en,
                    'poster_url': item.anime.poster_url,
                    'year': item.anime.year,
                    'episodes': item.anime.episodes,
                    'score': item.anime.score
                },
                'status': item.status,
                'last_episode': item.last_episode,
                'watched_episodes': item.watched_episodes,
                'total_progress': item.total_progress,
                'user_score': item.user_score
            })
            
        except UserLibrary.DoesNotExist:
            return Response({
                'error': 'Запись не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """Обновление записи (статус, прогресс)"""
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            
            status = request.data.get('status')
            last_episode = request.data.get('last_episode')
            watched_episodes = request.data.get('watched_episodes')
            total_progress = request.data.get('total_progress')
            user_score = request.data.get('user_score')
            
            if status:
                item.status = status
            if last_episode is not None:
                item.last_episode = last_episode
            if watched_episodes is not None:
                item.watched_episodes = watched_episodes
            if total_progress is not None:
                item.total_progress = total_progress
            if user_score is not None:
                item.user_score = user_score
            
            item.save()
            
            return Response({
                'message': 'Запись обновлена'
            })
            
        except UserLibrary.DoesNotExist:
            return Response({
                'error': 'Запись не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Ошибка обновления: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Удаление записи из библиотеки"""
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            item.delete()
            
            return Response({
                'message': 'Аниме удалено из библиотеки'
            })
            
        except UserLibrary.DoesNotExist:
            return Response({
                'error': 'Запись не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Ошибка удаления: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)