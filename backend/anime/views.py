from django.http import HttpResponseBadRequest, HttpResponseServerError, StreamingHttpResponse
from django.db.models import Q
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
import logging

from users.models import UserLibrary
from .models import Anime, Franchise, Genre, Episode, Translation, WatchProgress, CustomDub, UserEpisodeProgress
from .serializers import (
    AnimeSerializer, AnimeDetailSerializer, GenreSerializer,
    FranchiseSerializer, FranchiseDetailSerializer,
)
from .services.anime_parser_service import (
    AnimeParserService, VideoStreamingService, CacheService, AnimeUpdateService
)

# Инициализация сервисов (в try/except чтобы ошибки парсера не ломали весь модуль)
try:
    anime_parser_service = AnimeParserService()
    video_streaming_service = VideoStreamingService()
    cache_service = CacheService()
    anime_update_service = AnimeUpdateService()
except Exception as _svc_init_err:
    import logging
    logging.getLogger(__name__).warning(f'Anime parser services failed to initialize: {_svc_init_err}')
    anime_parser_service = None
    video_streaming_service = None
    cache_service = None
    anime_update_service = None

# Функция для нормализации строки поиска
def normalize_search_string(text: str) -> str:
    if not text:
        return ''
    text = text.lower()
    text = text.replace('ё', 'е')
    text = re.sub(r'[^а-яa-z0-9\s]', '', text)
    text = ' '.join(text.split())
    return text

def fuzzy_match(query: str, text: str, threshold: float = 0.6) -> float:
    if not query or not text:
        return 0.0
    query_norm = normalize_search_string(query)
    text_norm = normalize_search_string(text)
    if not query_norm or not text_norm:
        return 0.0
    if query_norm == text_norm:
        return 1.0
    if query_norm in text_norm or text_norm in query_norm:
        return 0.9
    return SequenceMatcher(None, query_norm, text_norm).ratio()

def fuzzy_search_anime(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return []
    try:
        query = query.strip()
        logging.getLogger(__name__).debug("fuzzy_search_anime query=%r", query)
        queryset = Anime.objects.filter(
            Q(title_ru__icontains=query) |
            Q(title_en__icontains=query) |
            Q(title_jp__icontains=query)
        ).order_by('-score')[:limit]
        formatted_results = []
        for anime in queryset:
            poster_url = anime.poster_image_url if hasattr(anime, 'poster_image_url') else anime.poster_url
            formatted_results.append({
                'id': anime.id,
                'title_ru': anime.title_ru or '',
                'title_en': anime.title_en or '',
                'title_jp': anime.title_jp or '',
                'year': anime.year,
                'status': anime.status,
                'episodes': anime.episodes,
                'score': anime.score,
                'poster_url': poster_url,
                'description': anime.description,
                'match_score': 1.0,
                'source': 'database'
            })
        logging.getLogger(__name__).debug("fuzzy_search_anime returned %d results", len(formatted_results))
        return formatted_results
    except Exception as e:
        logging.getLogger(__name__).exception("Ошибка в fuzzy_search_anime")
        import traceback
        traceback.print_exc()
        return []

class VideoService:
    def get_direct_video(self, shikimori_id, episode, translation_id, quality):
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
        return None

video_service = VideoService()

@csrf_exempt
def proxy_video(request):
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


def _split_param(value):
    """Разбивает строку 'a,b,c' в список ['a','b','c'], убирая пустые."""
    if not value:
        return []
    return [v.strip() for v in value.split(',') if v.strip()]


class AnimeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с аниме"""
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Anime.objects.select_related('franchise')

    def list(self, request, *args, **kwargs):
        """Список аниме с пагинацией и полноценной фильтрацией"""
        print(f"\n=== AnimeViewSet.list called ===")
        print(f"Query params: {dict(request.query_params)}")

        queryset = self.get_queryset()

        # ── Поиск по названию ────────────────────────────────────
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title_ru__icontains=search) |
                Q(title_en__icontains=search) |
                Q(title_jp__icontains=search)
            )

        # ── Статус (multi-value: ongoing,finished,...) ───────────
        status_param = request.query_params.get('status')
        if status_param:
            statuses = _split_param(status_param)
            if statuses:
                queryset = queryset.filter(status__in=statuses)

        # ── Тип/kind (multi-value: tv,movie,ova,...) ─────────────
        type_param = request.query_params.get('type')
        if type_param:
            kinds = _split_param(type_param)
            if kinds:
                queryset = queryset.filter(kind__in=kinds)

        # ── Жанры (genres — JSON array field, icontains по строкам) ─
        genres_param = request.query_params.get('genres')
        genre_logic = request.query_params.get('genre_logic', 'OR').upper()  # OR | AND
        if genres_param:
            genre_values = _split_param(genres_param)
            # Разрешаем передачу числовых ID жанров → конвертируем в названия
            genre_names = []
            for val in genre_values:
                if val.isdigit():
                    name = Genre.objects.filter(id=int(val)).values_list('name', flat=True).first()
                    if name:
                        genre_names.append(name)
                else:
                    genre_names.append(val)

            if genre_names:
                if genre_logic == 'AND':
                    # Должны присутствовать ВСЕ жанры
                    for gn in genre_names:
                        queryset = queryset.filter(genres__icontains=gn)
                    queryset = queryset.distinct()
                else:
                    # OR — хотя бы один жанр
                    genre_q = Q()
                    for gn in genre_names:
                        genre_q |= Q(genres__icontains=gn)
                    queryset = queryset.filter(genre_q).distinct()

        # ── Студия (studios — JSON array field) ─────────────────
        studio_param = request.query_params.get('studio')
        if studio_param:
            studios = _split_param(studio_param)
            if studios:
                studio_q = Q()
                for s in studios:
                    studio_q |= Q(studios__icontains=s)
                queryset = queryset.filter(studio_q).distinct()

        # ── Год ─────────────────────────────────────────────────
        year_from = request.query_params.get('year_from')
        year_to   = request.query_params.get('year_to')
        if year_from:
            try:
                queryset = queryset.filter(year__gte=int(year_from))
            except ValueError:
                pass
        if year_to:
            try:
                queryset = queryset.filter(year__lte=int(year_to))
            except ValueError:
                pass

        # ── Рейтинг ──────────────────────────────────────────────
        score_from = request.query_params.get('score_from')
        score_to   = request.query_params.get('score_to')
        if score_from:
            try:
                queryset = queryset.filter(score__gte=float(score_from))
            except ValueError:
                pass
        if score_to:
            try:
                queryset = queryset.filter(score__lte=float(score_to))
            except ValueError:
                pass

        # ── Эпизоды ──────────────────────────────────────────────
        episodes_from = request.query_params.get('episodes_from')
        episodes_to   = request.query_params.get('episodes_to')
        if episodes_from:
            try:
                queryset = queryset.filter(episodes__gte=int(episodes_from))
            except ValueError:
                pass
        if episodes_to:
            try:
                queryset = queryset.filter(episodes__lte=int(episodes_to), episodes__isnull=False)
            except ValueError:
                pass

        # ── Сезон (season + season_year) ─────────────────────────
        season_year = request.query_params.get('season_year')
        if season_year:
            try:
                queryset = queryset.filter(year=int(season_year))
            except ValueError:
                pass

        # ── Сортировка ───────────────────────────────────────────
        ordering = request.query_params.get('ordering', '-score')
        VALID_ORDER_FIELDS = {
            'score', '-score',
            'year', '-year',
            'title_ru', '-title_ru',
            'episodes', '-episodes',
            'created_at', '-created_at',
        }
        if ordering not in VALID_ORDER_FIELDS:
            ordering = '-score'
        queryset = queryset.order_by(ordering)

        # ── Пагинация ────────────────────────────────────────────
        try:
            page_size = min(int(request.query_params.get('page_size', 20)), 500)
        except ValueError:
            page_size = 20
        try:
            page = max(int(request.query_params.get('page', 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end   = start + page_size

        total_count = queryset.count()
        total_pages = max((total_count + page_size - 1) // page_size, 1)

        serializer = AnimeSerializer(queryset[start:end], many=True)

        print(f"Final count: {total_count}, page: {page}, page_size: {page_size}")

        return Response({
            'results':     serializer.data,
            'count':       total_count,
            'page':        page,
            'page_size':   page_size,
            'total_pages': total_pages,
        })

    def retrieve(self, request, *args, **kwargs):
        try:
            anime = Anime.objects.select_related('franchise').get(pk=kwargs['pk'])
            if not anime.screenshots and anime.shikimori_id:
                try:
                    KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
                    KODIK_API_BASE = 'https://kodikapi.com'
                    search_params = {
                        'token': KODIK_API_TOKEN,
                        'shikimori_id': anime.shikimori_id,
                        'with_material_data': True,
                        'limit': 1
                    }
                    response = requests.get(f'{KODIK_API_BASE}/search', params=search_params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        if results:
                            result = results[0]
                            kodik_screenshots = result.get('screenshots', [])
                            if kodik_screenshots:
                                anime.screenshots = kodik_screenshots
                                anime.save(update_fields=['screenshots', 'updated_at'])
                except Exception as e:
                    print(f"Не удалось загрузить скриншоты из Kodik: {e}")
            serializer = AnimeDetailSerializer(anime)
            return Response(serializer.data)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            return Response({
                'error': f'Ошибка получения аниме: {str(e)}',
                'detail': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def episodes(self, request, pk=None):
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
            return Response({'error': f'Ошибка получения эпизодов: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def translations(self, request, pk=None):
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
            return Response({'error': f'Ошибка получения переводов: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def kodik_player(self, request, pk=None):
        print(f"\n=== KODIK_PLAYER для аниме ID: {pk} ===")
        try:
            anime = self.get_object()
            if anime.kodik_link:
                return Response({'kodik_link': anime.kodik_link, 'source': 'database'})
            if not anime.shikimori_id:
                return Response({'error': 'У аниме нет Shikimori ID для поиска в Kodik'}, status=status.HTTP_400_BAD_REQUEST)
            KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
            KODIK_API_BASE = 'https://kodikapi.com'
            search_params = {'token': KODIK_API_TOKEN, 'shikimori_id': anime.shikimori_id, 'with_material_data': True, 'limit': 1}
            response = requests.get(f'{KODIK_API_BASE}/search', params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            if not results:
                return Response({'error': 'Аниме не найдено в Kodik API', 'shikimori_id': anime.shikimori_id}, status=status.HTTP_404_NOT_FOUND)
            result = results[0]
            kodik_link = result.get('link')
            if not kodik_link:
                return Response({'error': 'Ссылка на плеер не найдена в ответе Kodik', 'result': result}, status=status.HTTP_404_NOT_FOUND)
            anime.kodik_link = kodik_link
            anime.kodik_id = result.get('id', '')
            anime.quality = result.get('quality', '')
            anime.screenshots = result.get('screenshots', [])
            anime.seasons = result.get('seasons', {})
            anime.last_season = result.get('last_season')
            anime.last_episode = result.get('last_episode')
            anime.save()
            return Response({'kodik_link': kodik_link, 'source': 'kodik_api', 'quality': anime.quality, 'last_episode': anime.last_episode, 'seasons': anime.seasons})
        except requests.RequestException as e:
            return Response({'error': f'Ошибка запроса к Kodik API: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': f'Ошибка получения плеера: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def get_video_link(self, request, pk=None):
        print(f"\n=== GET_VIDEO_LINK для аниме ID: {pk} ===")
        try:
            anime = self.get_object()
            episode = int(request.query_params.get('episode', 1))
            translation_id = request.query_params.get('translation_id', '0')
            quality = request.query_params.get('quality', '720')
            if not video_streaming_service:
                return Response({'error': 'Сервис видео недоступен'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            video_sources = video_streaming_service.get_video_sources(str(anime.shikimori_id), episode, translation_id)
            if not video_sources:
                return Response({'error': 'Видео источники не найдены', 'anime_id': pk, 'video_url': None}, status=status.HTTP_404_NOT_FOUND)
            for source_name, source_data in video_sources.items():
                if source_name == 'kodik' and source_data.get('video_url'):
                    video_url = source_data['video_url']
                    proxy_url = f"https://anisphere.ru/api/anime/proxy/video/?url={video_url}"
                    return Response({'video_url': proxy_url, 'quality': quality, 'episode': episode, 'translation_id': translation_id, 'source': source_name, 'm3u8_url': source_data.get('m3u8_url'), 'note': 'Видео через прокси'})
                elif source_name == 'aniboom' and source_data.get('mpd_content'):
                    return Response({'video_url': None, 'mpd_content': source_data['mpd_content'], 'quality': quality, 'episode': episode, 'translation_id': translation_id, 'source': source_name, 'format': 'mpd', 'note': 'MPD формат требует специального плеера'})
            return Response({'error': 'Подходящий видео источник не найден', 'available_sources': list(video_sources.keys())}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': f'Ошибка получения видео: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_from_parser(self, request, pk=None):
        try:
            anime = self.get_object()
            if not anime.shikimori_id:
                return Response({'error': 'У аниме нет Shikimori ID для обновления'}, status=status.HTTP_400_BAD_REQUEST)
            if not anime_parser_service:
                return Response({'error': 'Сервис парсера недоступен'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            fresh_data = anime_parser_service.get_anime_by_id(anime.shikimori_id, 'shikimori')
            if not fresh_data:
                return Response({'error': 'Не удалось получить данные из парсера'}, status=status.HTTP_404_NOT_FOUND)
            updated_anime = anime_parser_service.import_anime_to_db(fresh_data, 'shikimori')
            return Response({'message': 'Данные аниме успешно обновлены', 'anime_id': updated_anime.id, 'title': updated_anime.title_ru, 'episodes': updated_anime.episodes, 'status': updated_anime.status})
        except Exception as e:
            return Response({'error': f'Ошибка обновления аниме: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def watch_progress(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется аутентификация'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            anime = self.get_object()
            if not video_streaming_service:
                return Response({'error': 'Сервис видео недоступен'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            progress = video_streaming_service.get_watch_progress(request.user, anime.id)
            return Response({'anime_id': anime.id, 'anime_title': anime.title_ru, 'progress': progress})
        except Exception as e:
            return Response({'error': f'Ошибка получения прогресса: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def save_watch_progress(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется аутентификация'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            anime = self.get_object()
            episode_id = request.data.get('episode_id')
            current_time = request.data.get('current_time', 0)
            duration = request.data.get('duration')
            if not episode_id:
                return Response({'error': 'Требуется episode_id'}, status=status.HTTP_400_BAD_REQUEST)
            if not video_streaming_service:
                return Response({'error': 'Сервис видео недоступен'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            progress = video_streaming_service.save_watch_progress(request.user, anime.id, episode_id, current_time, duration)
            if progress:
                return Response({'message': 'Прогресс сохранен', 'progress': {'episode_id': progress.episode.id, 'current_time': progress.current_time, 'is_completed': progress.is_completed}})
            else:
                return Response({'error': 'Не удалось сохранить прогресс'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Ошибка сохранения прогресса: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FranchiseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Franchise.objects.prefetch_related('entries').all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FranchiseDetailSerializer
        return FranchiseSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        page_size = min(int(request.query_params.get('page_size', 20)), 200)
        page      = int(request.query_params.get('page', 1))
        start     = (page - 1) * page_size
        end       = start + page_size
        total     = qs.count()
        serializer = FranchiseSerializer(qs[start:end], many=True)
        return Response({'results': serializer.data, 'count': total, 'page': page, 'page_size': page_size, 'total_pages': (total + page_size - 1) // page_size})

    def retrieve(self, request, *args, **kwargs):
        franchise = self.get_object()
        franchise._prefetched_objects_cache = {}
        franchise.entries_sorted = franchise.entries.order_by('franchise_order', 'year')
        serializer = FranchiseDetailSerializer(franchise)
        data = serializer.data
        from .serializers import FranchiseEntrySerializer
        data['entries'] = FranchiseEntrySerializer(franchise.entries.order_by('franchise_order', 'year'), many=True).data
        return Response(data)


class SearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_query = request.query_params.get('q', '')
        query = raw_query.strip()
        try:
            limit = int(request.query_params.get('limit', 20))
            if limit <= 0:
                limit = 20
        except Exception:
            limit = 20
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("SearchAPIView called; raw_query=%r stripped_query=%r params=%r limit=%d", raw_query, query, dict(request.query_params), limit)
        if not query:
            return Response({'error': 'Требуется параметр поиска q'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            db_results = fuzzy_search_anime(query, limit)
            try:
                for result in db_results:
                    result.pop('match_score', None)
            except Exception:
                logging.getLogger(__name__).exception('Failed to sanitize db_results')
            return Response({'query': query, 'results': db_results, 'total': len(db_results), 'source': 'database'})
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logging.getLogger(__name__).exception("Error in SearchAPIView: %s", tb)
            return Response({'error': f'Ошибка поиска: {str(e)}', 'query': query, 'results': [], 'total': 0, 'source': 'error', 'debug': repr(e), 'debug_traceback': tb}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParserStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            if not anime_parser_service:
                return Response({'error': 'Сервис парсера недоступен', 'status': 'unhealthy'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            health_status = anime_parser_service.parser.health_check()
            return Response({'parsers': health_status, 'total_parsers': len(health_status), 'active_parsers': sum(1 for status in health_status.values() if status), 'status': 'healthy' if any(health_status.values()) else 'unhealthy'})
        except Exception as e:
            return Response({'error': f'Ошибка проверки статуса: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatesAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        try:
            if not anime_update_service:
                return Response({'error': 'Сервис обновлений недоступен', 'updates': [], 'total': 0}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            updates = anime_update_service.get_recent_updates(limit)
            return Response({'updates': updates, 'total': len(updates)})
        except Exception as e:
            return Response({'error': f'Ошибка получения обновлений: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenresViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        try:
            genres = Genre.objects.all()
            serializer = GenreSerializer(genres, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': f'Ошибка получения жанров: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KodikImportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from anime.models import Anime
        data = request.data
        if 'shikimori_id' in data:
            return self._import_single_anime(data)
        else:
            return self._import_all_anime(data)

    def _import_single_anime(self, data):
        try:
            shikimori_id = data.get('shikimori_id')
            kodik_data = data.get('kodik_data')
            if not shikimori_id:
                return Response({'error': 'Требуется shikimori_id'}, status=status.HTTP_400_BAD_REQUEST)
            if kodik_data:
                anime = self._create_anime_from_kodik(kodik_data)
                return Response({'message': 'Аниме успешно импортировано', 'anime_id': anime.id, 'title': anime.title_ru})
            return Response({'error': 'Требуются данные Kodik'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Ошибка импорта: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _import_all_anime(self, data):
        from backend.scripts.import_from_kodik import fetch_all_anime, import_anime
        try:
            limit = data.get('limit', 0)
            all_anime = fetch_all_anime()
            if limit > 0:
                all_anime = all_anime[:limit]
            imported = 0
            errors = []
            for kodik_anime in all_anime:
                try:
                    anime = import_anime(kodik_anime)
                    imported += 1
                except Exception as e:
                    errors.append({'title': kodik_anime.get('title', 'Unknown'), 'error': str(e)})
            return Response({'message': 'Импорт завершен', 'total_processed': len(all_anime), 'imported': imported, 'errors': errors[:10]})
        except Exception as e:
            return Response({'error': f'Ошибка массового импорта: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_anime_from_kodik(self, kodik_data):
        from anime.models import Anime
        material_data = kodik_data.get('material_data', {})
        episodes_count = material_data.get('episodes_total') or kodik_data.get('episodes_count') or 1
        genre_names = material_data.get('anime_genres') or material_data.get('genres') or []
        studio_names = material_data.get('anime_studios') or []
        poster_url = material_data.get('anime_poster_url') or material_data.get('poster_url') or ''
        score = material_data.get('shikimori_rating') or material_data.get('kinopoisk_rating') or 0.0
        description = material_data.get('anime_description') or material_data.get('description') or ''
        status_map = {'anons': 'announced', 'ongoing': 'ongoing', 'released': 'finished', 'discontinued': 'canceled'}
        status = status_map.get(material_data.get('anime_status', 'released'), 'finished')
        kind_map = {'tv': 'tv', 'tv_13': 'tv', 'tv_24': 'tv', 'tv_48': 'tv', 'movie': 'movie', 'ova': 'ova', 'ona': 'ona', 'special': 'special', 'music': 'music'}
        kind = kind_map.get(material_data.get('anime_kind') or kodik_data.get('type', 'tv'), 'tv')
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
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import requests
        KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
        KODIK_API_BASE = 'https://kodikapi.com'
        try:
            genres_response = requests.get(f'{KODIK_API_BASE}/genres', params={'token': KODIK_API_TOKEN, 'types': 'anime-serial,anime', 'genres_type': 'shikimori', 'sort': 'title'})
            years_response = requests.get(f'{KODIK_API_BASE}/years', params={'token': KODIK_API_TOKEN, 'types': 'anime-serial,anime', 'sort': 'year', 'order': 'desc'})
            studios_response = requests.get(f'{KODIK_API_BASE}/anime_studios', params={'token': KODIK_API_TOKEN, 'types': 'anime-serial,anime', 'sort': 'title'})
            translations_response = requests.get(f'{KODIK_API_BASE}/translations/v2', params={'token': KODIK_API_TOKEN, 'types': 'anime-serial,anime', 'sort': 'title'})
            return Response({'genres': genres_response.json().get('results', []), 'years': years_response.json().get('results', []), 'studios': studios_response.json().get('results', []), 'translations': translations_response.json().get('results', [])})
        except Exception as e:
            return Response({'error': f'Ошибка получения фильтров: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KodikTranslationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
            if not anime.shikimori_id:
                return Response({'error': 'У аниме нет Shikimori ID'}, status=status.HTTP_400_BAD_REQUEST)
            KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
            KODIK_API_BASE = 'https://kodikapi.com'
            search_params = {'token': KODIK_API_TOKEN, 'shikimori_id': anime.shikimori_id, 'with_episodes_data': False, 'limit': 100}
            response = requests.get(f'{KODIK_API_BASE}/search', params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            if not results:
                return Response({'translations': [], 'total': 0})
            translations_map = {}
            for result in results:
                translation = result.get('translation', {})
                if not translation:
                    continue
                translation_id = translation.get('id')
                translation_name = translation.get('title', 'Неизвестно')
                translation_type = translation.get('type', 'voice')
                if translation_id not in translations_map:
                    translations_map[translation_id] = {'id': translation_id, 'name': translation_name, 'type': translation_type, 'quality': result.get('quality', ''), 'episodes_done': 0, 'total_episodes': result.get('episodes_count') or anime.episodes, 'is_complete': False, 'kodik_link': result.get('link', ''), 'logo': None}
                t = translations_map[translation_id]
                episodes = result.get('episodes_count') or 0
                if episodes > t['episodes_done']:
                    t['episodes_done'] = episodes
            translations = list(translations_map.values())
            translations.sort(key=lambda x: x['episodes_done'], reverse=True)
            return Response({'translations': translations, 'total': len(translations)})
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)
        except requests.RequestException as e:
            return Response({'error': f'Ошибка запроса к Kodik API: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': f'Ошибка получения озвучек: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDubListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
            custom_dubs = CustomDub.objects.filter(anime=anime, status='approved').order_by('-rating', '-created_at')
            dubs_data = []
            for dub in custom_dubs:
                dubs_data.append({'id': dub.id, 'name': dub.name, 'studio': dub.studio, 'description': dub.description, 'quality': dub.quality, 'logo': dub.logo_url, 'episodes_done': dub.episodes_done, 'total_episodes': dub.total_episodes or anime.episodes, 'is_complete': dub.is_complete, 'is_custom': True, 'rating': dub.rating, 'views_count': dub.views_count})
            return Response({'dubs': dubs_data, 'total': len(dubs_data)})
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, anime_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=status.HTTP_401_UNAUTHORIZED)
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
                return Response({'error': 'Необходимо указать название, качество и ссылку на видео'}, status=status.HTTP_400_BAD_REQUEST)
            existing_dub = CustomDub.objects.filter(anime=anime, created_by=request.user, name=name).first()
            if existing_dub:
                return Response({'error': 'Вы уже добавляли озвучку с таким названием'}, status=status.HTTP_400_BAD_REQUEST)
            dub = CustomDub.objects.create(anime=anime, created_by=request.user, name=name, studio=studio or name, description=description, quality=quality, video_url=video_url, logo_url=logo_url, episodes_done=episodes_done or 0, total_episodes=anime.episodes, is_complete=is_complete, status='pending')
            return Response({'message': 'Озвучка отправлена на модерацию', 'dub_id': dub.id, 'status': dub.status}, status=status.HTTP_201_CREATED)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка добавления озвучки: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomDubDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id, dub_id):
        try:
            dub = CustomDub.objects.get(id=dub_id, anime_id=anime_id, status='approved')
            dub.views_count += 1
            dub.save(update_fields=['views_count'])
            return Response({'video_url': dub.video_url, 'quality': dub.quality, 'name': dub.name, 'studio': dub.studio, 'logo': dub.logo_url})
        except CustomDub.DoesNotExist:
            return Response({'error': 'Озвучка не найдена или не одобрена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка получения видео: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLibraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            library_items = UserLibrary.objects.filter(user=request.user).select_related('anime')
            library_data = []
            for item in library_items:
                library_data.append({'id': item.id, 'anime': {'id': item.anime.id, 'title_ru': item.anime.title_ru, 'title_en': item.anime.title_en, 'poster_url': item.anime.poster_url, 'year': item.anime.year, 'episodes': item.anime.episodes, 'score': item.anime.score, 'kind': item.anime.kind, 'status': item.anime.status}, 'status': item.status, 'last_episode': item.last_episode, 'watched_episodes': item.watched_episodes, 'total_progress': item.total_progress, 'user_score': item.user_score, 'last_watched_at': item.last_watched_at.isoformat(), 'completed_at': item.completed_at.isoformat() if item.completed_at else None, 'created_at': item.created_at.isoformat()})
            return Response({'library': library_data, 'total': len(library_data)})
        except Exception as e:
            return Response({'error': f'Ошибка получения библиотеки: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            anime_id = request.data.get('anime')
            status_val = request.data.get('status', 'want_to_watch')
            if not anime_id:
                return Response({'error': 'Не указан ID аниме'}, status=status.HTTP_400_BAD_REQUEST)
            anime = Anime.objects.get(pk=anime_id)
            existing = UserLibrary.objects.filter(user=request.user, anime=anime).first()
            if existing:
                return Response({'error': 'Аниме уже добавлено в библиотеку'}, status=status.HTTP_400_BAD_REQUEST)
            library_item = UserLibrary.objects.create(user=request.user, anime=anime, status=status_val)
            return Response({'message': 'Аниме добавлено в библиотеку', 'id': library_item.id}, status=status.HTTP_201_CREATED)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка добавления: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLibraryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            return Response({'id': item.id, 'anime': {'id': item.anime.id, 'title_ru': item.anime.title_ru, 'title_en': item.anime.title_en, 'poster_url': item.anime.poster_url, 'year': item.anime.year, 'episodes': item.anime.episodes, 'score': item.anime.score}, 'status': item.status, 'last_episode': item.last_episode, 'watched_episodes': item.watched_episodes, 'total_progress': item.total_progress, 'user_score': item.user_score})
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            status_val = request.data.get('status')
            last_episode = request.data.get('last_episode')
            watched_episodes = request.data.get('watched_episodes')
            total_progress = request.data.get('total_progress')
            user_score = request.data.get('user_score')
            if status_val:
                item.status = status_val
            if last_episode is not None:
                item.last_episode = last_episode
            if watched_episodes is not None:
                item.watched_episodes = watched_episodes
            if total_progress is not None:
                item.total_progress = total_progress
            if user_score is not None:
                item.user_score = user_score
            item.save()
            return Response({'message': 'Запись обновлена'})
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка обновления: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            item.delete()
            return Response({'message': 'Аниме удалено из библиотеки'})
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Ошибка удаления: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RandomAnimeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import random
        try:
            ids = list(Anime.objects.values_list('id', flat=True))
            if not ids:
                return Response({'error': 'Нет аниме'}, status=status.HTTP_404_NOT_FOUND)
            random_id = random.choice(ids)
            anime = Anime.objects.get(id=random_id)
            serializer = AnimeSerializer(anime)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrentlyWatchingView(APIView):
    permission_classes = [permissions.AllowAny]

    # «Сейчас смотрит» = last_watched обновлялся не позже 2 часов назад.
    # UserEpisodeProgress.last_watched (auto_now=True) пишется каждые ~30с из AnimeWatchView.
    ACTIVE_WINDOW_HOURS = 2

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        try:
            cutoff = timezone.now() - timedelta(hours=self.ACTIVE_WINDOW_HOURS)
            active = (
                UserEpisodeProgress.objects
                .filter(last_watched__gte=cutoff)
                .values('anime_id')
                .annotate(viewers=Count('user', distinct=True))
                .order_by('-viewers')
            )
            anime_ids   = [r['anime_id'] for r in active]
            viewers_map = {r['anime_id']: r['viewers'] for r in active}

            if not anime_ids:
                return Response({'results': [], 'count': 0})

            animes = Anime.objects.filter(id__in=anime_ids)
            animes_dict = {a.id: a for a in animes}
            results = []
            for aid in anime_ids:
                a = animes_dict.get(aid)
                if not a:
                    continue
                data = AnimeSerializer(a).data
                data['viewers_count'] = viewers_map[aid]
                results.append(data)
            return Response({'results': results, 'count': len(results)})
        except Exception as e:
            import traceback
            return Response({'error': str(e), 'detail': traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HomeAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        continue_watching = self._get_continue_watching(user) if user else []
        rewatch           = self._get_rewatch(user) if user else []
        recommendations   = self._get_recommendations(user)
        trending          = self._get_trending(user)
        return Response({
            'continue_watching': continue_watching,
            'rewatch':           rewatch,
            'recommendations':   recommendations,
            'trending':          trending,
        })

    def _get_continue_watching(self, user):
        from users.models import UserLibrary
        library_items = UserLibrary.objects.filter(
            user=user, status='started'
        ).select_related('anime').order_by('-updated_at')[:15]
        result = []
        for item in library_items:
            anime = item.anime
            total_episodes   = anime.episodes or 1
            progress_percent = min(100, int((item.current_episode / total_episodes) * 100)) if total_episodes else 0
            poster_url       = anime.poster.url if anime.poster else anime.poster_url
            result.append({
                'anime_id':        anime.id,
                'title':           anime.title_ru or anime.title_en or '',
                'title_en':        anime.title_en or '',
                'poster':          poster_url,
                'current_episode': item.current_episode,
                'total_episodes':  anime.episodes,
                'progress_percent': progress_percent,
                'last_watched':    item.updated_at.isoformat() if item.updated_at else None,
            })
        return result

    def _get_rewatch(self, user):
        from users.models import UserLibrary
        library_items = UserLibrary.objects.filter(
            user=user, status='completed'
        ).select_related('anime').order_by('-updated_at')[:10]
        result = []
        for item in library_items:
            anime      = item.anime
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append({
                'anime_id':       anime.id,
                'title':          anime.title_ru or anime.title_en or '',
                'title_en':       anime.title_en or '',
                'poster':         poster_url,
                'completed_date': item.updated_at.isoformat() if item.updated_at else None,
                'user_rating':    item.rating,
            })
        return result

    def _get_recommendations(self, user):
        """
        Персонализированные рекомендации:
          - Основа: жанры аниме которое пользователь уже смотрел (статус started/completed)
          - Бонус: жанры студий, на которые подписан (если есть подписки)
          - Исключаем аниме которое пользователь уже смотрит или планирует
          - Для неавторизованных: лучшее по рейтингу
        """
        from anime.models import Anime
        from collections import Counter

        if not user or not user.is_authenticated:
            # Без авторизации — просто топ 20 по рейтингу
            animes = Anime.objects.filter(score__gte=7.0).order_by('-score')[:20]
            return [self._anime_to_dict(a) for a in animes]

        from users.models import UserLibrary
        from studios.models import StudioSubscription

        # 1. Аниме которое пользователь уже смотрел или смотрит (или планирует)
        watched_ids = set(
            UserLibrary.objects.filter(
                user=user,
                status__in=('started', 'completed', 'on_hold', 'planned')
            ).values_list('anime_id', flat=True)
        )

        # 2. Жанры из просмотренного (started + completed)
        watched_anime = Anime.objects.filter(
            id__in=UserLibrary.objects.filter(
                user=user, status__in=('started', 'completed')
            ).values_list('anime_id', flat=True)
        )
        genre_counter = Counter()
        for anime in watched_anime:
            for g in (anime.genres or []):
                genre_counter[g] += 1

        # 3. Жанры подписанных студий (если есть подписки)
        subscribed_studios = list(
            StudioSubscription.objects.filter(user=user)
            .select_related('studio')
            .values_list('studio__name', flat=True)
        )
        if subscribed_studios:
            for studio_obj in StudioSubscription.objects.filter(user=user).select_related('studio'):
                for g, cnt in (studio_obj.studio.genre_stats or {}).items():
                    genre_counter[g] += max(1, cnt // 10)  # лёгкий вес

        # 4. Строим фильтр по жанрам
        top_genres = [g for g, _ in genre_counter.most_common(10)]

        if top_genres:
            genre_q = Q()
            for g in top_genres:
                genre_q |= Q(genres__icontains=g)
            qs = Anime.objects.filter(genre_q, score__gte=6.5)
        else:
            qs = Anime.objects.filter(score__gte=7.5)

        # 5. Бонус: аниме подписанных студий (JSON поле studios)
        studio_bonus_ids = set()
        if subscribed_studios:
            sq = Q()
            for s in subscribed_studios:
                sq |= Q(studios__icontains=s)
            studio_bonus_ids = set(
                Anime.objects.filter(sq).values_list('id', flat=True)
            )

        # 6. Исключаем уже в библиотеке
        candidates = list(
            qs.exclude(id__in=watched_ids)
            .order_by('-score')
            [:60]
        )

        # 7. Сортируем: студийные вверх
        def sort_key(anime):
            base    = anime.score or 0
            bonus   = 2.0 if anime.id in studio_bonus_ids else 0
            # Жанровый матч
            overlap = sum(1 for g in (anime.genres or []) if g in genre_counter)
            return base + bonus + overlap * 0.3

        candidates.sort(key=sort_key, reverse=True)
        return [self._anime_to_dict(a) for a in candidates[:20]]

    def _get_trending(self, user=None):
        """
        Популярное на этой неделе:
          - Определяем по количеству записей UserEpisodeProgress за последние 7 дней
          - Исключаем аниме которое текущий пользователь уже смотрит или смотрел
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from users.models import UserLibrary

        week_ago = timezone.now() - timedelta(days=7)

        # Смотрели / смотрят пользователь
        excluded_ids: set = set()
        if user and user.is_authenticated:
            excluded_ids = set(
                UserLibrary.objects.filter(
                    user=user,
                    status__in=('started', 'completed', 'on_hold', 'dropped')
                ).values_list('anime_id', flat=True)
            )

        # Топ аниме по активности UserEpisodeProgress
        trending_qs = (
            UserEpisodeProgress.objects
            .filter(last_watched__gte=week_ago)
            .values('anime_id')
            .annotate(views=Count('user', distinct=True))
            .order_by('-views')
            [:60]
        )
        trending_ids = [row['anime_id'] for row in trending_qs]

        # Загружаем аниме в порядке идентификаторов
        anime_map = {
            a.id: a
            for a in Anime.objects.filter(id__in=trending_ids)
        }

        result = []
        for row in trending_qs:
            aid = row['anime_id']
            if aid in excluded_ids:
                continue
            anime = anime_map.get(aid)
            if not anime:
                continue
            d = self._anime_to_dict(anime)
            d['views_this_week'] = row['views']
            result.append(d)
            if len(result) >= 20:
                break

        # Фоллбэк: если активность недельная недостаточна — дополняем топом по рейтингу
        if len(result) < 10:
            existing = {r['anime_id'] for r in result}
            fallback = (
                Anime.objects.filter(score__isnull=False)
                .exclude(id__in=excluded_ids | existing)
                .order_by('-score')
                [:20 - len(result)]
            )
            for anime in fallback:
                result.append(self._anime_to_dict(anime))

        return result

    @staticmethod
    def _anime_to_dict(anime):
        poster_url = anime.poster.url if anime.poster else anime.poster_url
        return {
            'anime_id':     anime.id,
            'title':        anime.title_ru or anime.title_en or '',
            'title_en':     anime.title_en or '',
            'poster':       poster_url,
            'genres':       anime.genres or [],
            'rating':       anime.score,
            'rating_count': 0,
            'year':         anime.year,
            'status':       anime.status,
        }


# ═══════════════════════════════════════════════════════════════
# EPISODE PROGRESS SYSTEM
# ═══════════════════════════════════════════════════════════════

class EpisodeProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        try:
            rows = list(UserEpisodeProgress.objects.filter(user=request.user, anime=anime))
            data = []
            for r in rows:
                try:
                    pct = r.progress_percent
                except Exception:
                    pct = round(r.last_position / r.duration * 100) if (r.duration and r.duration > 0) else 0
                data.append({
                    'episode_number': r.episode_number,
                    'status': r.status,
                    'last_position': r.last_position,
                    'duration': r.duration,
                    'progress_percent': pct,
                    'is_manually_marked': r.is_manually_marked,
                    'watched_at': r.watched_at.isoformat() if r.watched_at else None,
                })
            watched_count = sum(1 for r in rows if r.status in ('watched', 'skipped'))
            total = anime.episodes or 0
            return Response({'anime_id': anime_id, 'total': total, 'watched_count': watched_count, 'percent': round(watched_count / total * 100) if total else 0, 'episodes': data})
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Возвращаем пустой прогресс вместо 500
            return Response({'anime_id': anime_id, 'total': anime.episodes or 0, 'watched_count': 0, 'percent': 0, 'episodes': [], 'warning': str(e)})

    def post(self, request, anime_id):
        episode_number = request.data.get('episode_number')
        last_position  = request.data.get('last_position', 0)
        duration       = request.data.get('duration')
        action_type    = request.data.get('action', 'progress')
        if action_type == 'bulk':
            return self._bulk_sync(request, anime_id)
        if action_type == 'mark':
            return self._mark_watched(request, anime_id, episode_number, manual=True)
        if action_type == 'skip':
            return self._skip_episode(request, anime_id, episode_number)
        if episode_number is None:
            return Response({'error': 'Требуется episode_number'}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        ep, _ = UserEpisodeProgress.objects.get_or_create(user=request.user, anime=anime, episode_number=episode_number, defaults={'status': 'in_progress'})
        if ep.status not in ('watched', 'skipped'):
            ep.last_position = int(last_position)
            if duration:
                ep.duration = int(duration)
            if ep.duration and ep.duration > 0:
                pct = ep.last_position / ep.duration * 100
                if pct >= 85:
                    return self._mark_watched(request, anime_id, episode_number, instance=ep)
            ep.status = 'in_progress'
            ep.save(update_fields=['last_position', 'duration', 'status'])
        return Response({'episode_number': ep.episode_number, 'status': ep.status, 'last_position': ep.last_position, 'progress_percent': ep.progress_percent})

    def _mark_watched(self, request, anime_id, episode_number, manual=False, instance=None):
        from django.utils import timezone
        if episode_number is None:
            return Response({'error': 'Требуется episode_number'}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        if instance is None:
            instance, _ = UserEpisodeProgress.objects.get_or_create(user=request.user, anime=anime, episode_number=episode_number)
        instance.status = 'watched'
        instance.is_manually_marked = manual
        instance.watched_at = timezone.now()
        if instance.duration and not instance.last_position:
            instance.last_position = instance.duration
        instance.save()
        self._sync_library(request.user, anime)
        return Response({'episode_number': instance.episode_number, 'status': 'watched', 'is_manually_marked': manual, 'auto_marked': not manual})

    def _skip_episode(self, request, anime_id, episode_number):
        if episode_number is None:
            return Response({'error': 'Требуется episode_number'}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        ep, _ = UserEpisodeProgress.objects.get_or_create(user=request.user, anime=anime, episode_number=episode_number)
        ep.status = 'skipped'
        ep.is_manually_marked = True
        ep.save(update_fields=['status', 'is_manually_marked'])
        self._sync_library(request.user, anime)
        return Response({'episode_number': episode_number, 'status': 'skipped'})

    def _bulk_sync(self, request, anime_id):
        from django.utils import timezone
        watched_up_to = request.data.get('watched_up_to')
        reset         = request.data.get('reset', False)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        if reset:
            UserEpisodeProgress.objects.filter(user=request.user, anime=anime).delete()
            self._sync_library(request.user, anime)
            return Response({'reset': True, 'watched_count': 0})
        if watched_up_to is None:
            return Response({'error': 'Требуется watched_up_to'}, status=400)
        total = int(watched_up_to)
        now = timezone.now()
        marked = 0
        for ep_num in range(1, total + 1):
            UserEpisodeProgress.objects.update_or_create(user=request.user, anime=anime, episode_number=ep_num, defaults={'status': 'watched', 'is_manually_marked': True, 'watched_at': now})
            marked += 1
        self._sync_library(request.user, anime)
        return Response({'watched_count': marked, 'watched_up_to': total})

    def _sync_library(self, user, anime):
        try:
            watched = UserEpisodeProgress.objects.filter(user=user, anime=anime, status__in=['watched', 'skipped']).count()
            total = anime.episodes or 0
            lib, _ = UserLibrary.objects.get_or_create(user=user, anime=anime, defaults={'status': 'started'})
            if total and watched >= total:
                lib.status = 'completed'
            elif watched > 0:
                lib.status = 'started'
            lib.current_episode = UserEpisodeProgress.objects.filter(user=user, anime=anime, status__in=['watched', 'skipped']).order_by('-episode_number').values_list('episode_number', flat=True).first() or 0
            lib.save(update_fields=['status', 'current_episode', 'updated_at'])
        except Exception as e:
            logging.getLogger(__name__).warning('_sync_library error: %s', e)


class AnimeThemesView(APIView):
    """
    GET /anime/<id>/themes/?episode=1&season=1&translation_id=610

    Получает тайминги опенинга/эндинга через официальный Kodik API:
      1. kodikapi.com/search с with_episodes=True → URL страницы плеера серии
      2. kodik.biz/api/video-links?skip_segments=true → поле segments.skip[]
         skip-сегменты: первый = опенинг (начало серии), последний = эндинг (конец серии)

    Возвращает:
      { opening: {start, stop, kind} | null, ending: {start, stop, kind} | null }
    """
    permission_classes  = [permissions.AllowAny]
    KODIK_API_TOKEN     = '74ecb013335271e4344ebc994956dd75'
    KODIK_PRIVATE_KEY   = '692e74fa70fed3493e922cfcb6b0eab7'
    KODIK_PUBLIC_KEY    = '74ecb013335271e4344ebc994956dd75'

    def _get_episode_url(self, anime, episode, season, translation_id):
        """Возвращает URL вида //kodik.info/seria/... для конкретной серии."""
        params = {
            'token':             self.KODIK_API_TOKEN,
            'with_material_data': False,
            'with_episodes':     True,
            'limit':             100,
        }
        if anime.shikimori_id:
            params['shikimori_id'] = anime.shikimori_id
        elif anime.kodik_id:
            params['id'] = anime.kodik_id
        else:
            return None
        if translation_id:
            params['translation_id'] = translation_id

        r = requests.get('https://kodikapi.com/search', params=params, timeout=10)
        r.raise_for_status()
        season_key = str(season)
        ep_key     = str(episode)
        for res in r.json().get('results', []):
            if translation_id:
                tid = (res.get('translation') or {}).get('id')
                if str(tid) != str(translation_id):
                    continue
            s_data  = ((res.get('seasons') or {}).get(season_key)) or {}
            ep_data = s_data.get('episodes') or {}
            ep_url  = ep_data.get(ep_key) or ep_data.get(int(ep_key) if ep_key.isdigit() else ep_key)
            if ep_url:
                return ep_url.strip()
        return None

    def _get_segments(self, episode_url, user_ip='1.1.1.1'):
        """
        Запрашивает kodik.biz/api/video-links?skip_segments=true.
        Возвращает (opening|None, ending|None).

        skip[] — список сегментов для пропуска (опенинг, эндинг, заставка).
        Определяем роль по позиции в серии:
          • сегмент заканчивается до середины серии → опенинг
          • сегмент начинается после середины серии → эндинг
        """
        import hmac, hashlib
        from datetime import datetime, timezone, timedelta

        link = episode_url.strip()
        if link.startswith('https:'):
            link = link[6:]
        elif link.startswith('http:'):
            link = link[5:]

        deadline = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime('%Y%m%d%H')
        sign_str  = f'{link}:{user_ip}:{deadline}'
        signature = hmac.new(
            self.KODIK_PRIVATE_KEY.encode(),
            sign_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        params = {
            'link':          link,
            'p':             self.KODIK_PUBLIC_KEY,
            'ip':            user_ip,
            'd':             deadline,
            's':             signature,
            'skip_segments': 'true',
        }
        r = requests.get('https://kodik.biz/api/video-links', params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        segments = data.get('segments') or {}
        skip_list = segments.get('skip') or []

        if not skip_list:
            return None, None

        # Оцениваем общую длину серии по крайнему концу всех сегментов
        # (или берём максимальный end из skip+ad)
        all_segs = (segments.get('ad') or []) + skip_list
        max_end  = max((s.get('end', 0) for s in all_segs), default=0)
        # Если данных мало — ориентируемся на 1200 с (20 мин) как типичная серия
        total_est = max(max_end * 1.1, 1200)
        midpoint  = total_est / 2

        opening = None
        ending  = None
        for seg in skip_list:
            start = seg.get('start', 0)
            end   = seg.get('end', 0)
            if end <= midpoint and opening is None:
                opening = {'start': start, 'stop': end, 'kind': 'opening'}
            elif start >= midpoint and ending is None:
                ending = {'start': start, 'stop': end, 'kind': 'ending'}

        return opening, ending

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)

        episode        = int(request.query_params.get('episode', 1))
        season         = int(request.query_params.get('season', 1))
        translation_id = request.query_params.get('translation_id')
        user_ip        = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
                         or request.META.get('REMOTE_ADDR', '1.1.1.1')

        try:
            episode_url = self._get_episode_url(anime, episode, season, translation_id)
            if not episode_url:
                return Response({
                    'opening': None, 'ending': None,
                    'error': 'Серия не найдена в Kodik'
                }, status=404)

            opening, ending = self._get_segments(episode_url, user_ip=user_ip)

            return Response({
                'opening': opening,
                'ending':  ending,
                'source':  'kodik_video_links',
            })

        except requests.RequestException as e:
            return Response({'opening': None, 'ending': None,
                             'error': f'Ошибка запроса к Kodik: {e}'}, status=503)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'opening': None, 'ending': None,
                             'error': str(e)}, status=500)


class KodikVideoUrlView(APIView):
    """
    GET /anime/<id>/kodik_video_url/?episode=1&season=1&translation_id=610

    Возвращает прямой URL конкретной серии из Kodik для скачивания.

    Алгоритм:
      1. Kodik API search с with_episodes=True
         → seasons.{season}.episodes.{episode} → прямая ссылка на плеер серии
      2. Fallback: загружаем HTML страницы плеера и ищем .m3u8 в JS
    """
    permission_classes = [permissions.AllowAny]
    KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)

        episode        = int(request.query_params.get('episode', 1))
        season         = int(request.query_params.get('season', 1))
        translation_id = request.query_params.get('translation_id')

        try:
            # 1. Kodik API: ищем прямую ссылку на серию через with_episodes=True
            if anime.shikimori_id or anime.kodik_id:
                params = {
                    'token': self.KODIK_API_TOKEN,
                    'with_material_data': False,
                    'with_episodes': True,
                    'limit': 100,
                }
                if anime.shikimori_id:
                    params['shikimori_id'] = anime.shikimori_id
                else:
                    params['id'] = anime.kodik_id
                if translation_id:
                    params['translation_id'] = translation_id

                r = requests.get('https://kodikapi.com/search', params=params, timeout=10)
                r.raise_for_status()
                results = r.json().get('results', [])

                for res in results:
                    seasons_data = res.get('seasons', {}) or {}
                    s_data = seasons_data.get(str(season)) or seasons_data.get(season) or {}
                    ep_data = s_data.get('episodes', {}) if s_data else {}
                    ep_url = ep_data.get(str(episode)) or ep_data.get(episode)
                    if ep_url:
                        if ep_url.startswith('//'):
                            ep_url = 'https:' + ep_url
                        elif not ep_url.startswith('http'):
                            ep_url = 'https://' + ep_url
                        return Response({
                            'm3u8_url': ep_url,
                            'episode':  episode,
                            'season':   season,
                            'source':   'kodik_api',
                        })

            # 2. Fallback: парсим страницу плеера
            kodik_link = anime.kodik_link
            if not kodik_link:
                return Response({'error': 'Нет kodik_link и не удалось найти через API'}, status=404)

            if kodik_link.startswith('//'):
                kodik_link = 'https:' + kodik_link
            elif not kodik_link.startswith('http'):
                kodik_link = 'https://' + kodik_link

            from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
            parsed = urlparse(kodik_link)
            qs = parse_qs(parsed.query)
            qs['season']  = [str(season)]
            qs['episode'] = [str(episode)]
            if translation_id:
                qs['only_translations'] = [str(translation_id)]
            player_url = urlunparse(parsed._replace(query=urlencode({k: v[0] for k, v in qs.items()})))

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://anisphere.ru/',
            }
            page_resp = requests.get(player_url, headers=headers, timeout=15)
            page_resp.raise_for_status()
            page_html = page_resp.text

            m3u8_url = None
            for pat in [
                r'"src":\s*"(//[^"]+\.m3u8[^"]*)"',
                r"'src':\s*'(//[^']+\.m3u8[^']*)'",
                r'"([^"]*\.m3u8)"',
                r"'([^']*\.m3u8)'",
            ]:
                m = re.search(pat, page_html)
                if m:
                    m3u8_url = m.group(1)
                    break

            if not m3u8_url:
                return Response({'error': 'Не удалось извлечь m3u8 из страницы плеера',
                                 'player_url': player_url}, status=404)

            if m3u8_url.startswith('//'):
                m3u8_url = 'https:' + m3u8_url

            return Response({
                'm3u8_url':   m3u8_url,
                'player_url': player_url,
                'episode':    episode,
                'season':     season,
                'source':     'kodik_player_html',
            })

        except requests.RequestException as e:
            return Response({'error': f'Ошибка запроса: {e}'}, status=503)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class KodikClipDownloadView(APIView):
    """
    GET /anime/<pk>/clip/?episode=1&season=1&translation_id=610&start=60&end=150&label=clip

    Нарезает MP4-фрагмент серии через ffmpeg на сервере.

    Алгоритм получения m3u8:
      1. Kodik API (kodikapi.com/search) → URL страницы плеера серии (//kodik.info/seria/...)
      2. kodik.biz/api/video-links с HMAC-подписью → JSON с прямыми ссылками на m3u8
      3. ffmpeg нарезает фрагмент из m3u8 и отдаёт готовый MP4
    """
    permission_classes = [permissions.AllowAny]

    KODIK_API_TOKEN   = '74ecb013335271e4344ebc994956dd75'   # публичный
    KODIK_PRIVATE_KEY = '692e74fa70fed3493e922cfcb6b0eab7'   # приватный (для HMAC)
    KODIK_PUBLIC_KEY  = '74ecb013335271e4344ebc994956dd75'   # p= в video-links

    # ------------------------------------------------------------------ #
    #  Шаг 1: URL страницы плеера конкретной серии                        #
    # ------------------------------------------------------------------ #
    def _get_episode_player_url(self, anime, episode, season, translation_id):
        """
        Возвращает URL вида //kodik.info/seria/461359/hash/720p
        для конкретной серии через kodikapi.com/search с with_episodes=True.
        """
        season_key = str(season)
        ep_key     = str(episode)

        try:
            params = {
                'token': self.KODIK_API_TOKEN,
                'with_material_data': False,
                'with_episodes': True,
                'limit': 100,
            }
            if anime.shikimori_id:
                params['shikimori_id'] = anime.shikimori_id
            elif anime.kodik_id:
                params['id'] = anime.kodik_id
            else:
                return None

            if translation_id:
                params['translation_id'] = translation_id

            resp = requests.get('https://kodikapi.com/search', params=params, timeout=10)
            resp.raise_for_status()

            for res in resp.json().get('results', []):
                # Если translation_id указан — берём только нужный
                if translation_id:
                    tid = (res.get('translation') or {}).get('id')
                    if str(tid) != str(translation_id):
                        continue

                s_data  = ((res.get('seasons') or {}).get(season_key)) or {}
                ep_data = s_data.get('episodes') or {}
                ep_url  = ep_data.get(ep_key) or ep_data.get(int(ep_key) if ep_key.isdigit() else ep_key)

                if ep_url:
                    # Kodik возвращает //kodik.info/seria/... — оставляем как есть,
                    # потому что video-links API принимает именно //... формат
                    return ep_url.strip()

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('_get_episode_player_url error: %s', e)

        return None

    # ------------------------------------------------------------------ #
    #  Шаг 2: прямой m3u8 через kodik.biz/api/video-links                 #
    # ------------------------------------------------------------------ #
    def _get_m3u8_via_api(self, episode_url, user_ip='1.1.1.1'):
        """
        Запрашивает kodik.biz/api/video-links и возвращает прямой m3u8 URL.

        Подпись: HMAC-SHA256(private_key, "{link}:{ip}:{deadline}")
        Deadline: текущее UTC + 6 часов, формат YYYYMMDDHH
        """
        import hmac, hashlib
        from datetime import datetime, timezone, timedelta

        # Нормализуем ссылку: убираем https: если есть, оставляем //...
        link = episode_url.strip()
        if link.startswith('https:'):
            link = link[6:]
        elif link.startswith('http:'):
            link = link[5:]
        # Теперь link вида //kodik.info/seria/...

        # Deadline: UTC now + 6 часов, формат YYYYMMDDHH
        deadline_dt = datetime.now(timezone.utc) + timedelta(hours=6)
        deadline = deadline_dt.strftime('%Y%m%d%H')

        # HMAC-SHA256 подпись
        sign_string = f'{link}:{user_ip}:{deadline}'
        signature = hmac.new(
            self.KODIK_PRIVATE_KEY.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        params = {
            'link': link,
            'p':    self.KODIK_PUBLIC_KEY,
            'ip':   user_ip,
            'd':    deadline,
            's':    signature,
        }

        try:
            resp = requests.get('https://kodik.biz/api/video-links', params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Формат ответа Kodik: {"links": {"720": {"Src": "https://...", "Type": "..."}, ...}}
            # Внимание: ключи с заглавной буквы (Src, Type), значение — dict, не list
            links = data.get('links') or {}
            for quality in ['720', '1080', '480', '360', '240']:
                ql = links.get(quality)
                if not ql:
                    continue
                # Может быть dict {"Src": "..."} или list [{"src": "..."}]
                items = ql if isinstance(ql, list) else [ql]
                for item in items:
                    # Пробуем оба варианта регистра
                    src = (item.get('Src') or item.get('src')
                           or item.get('File') or item.get('file') or '')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        return src

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('_get_m3u8_via_api error: %s', e)

        return None

    # ------------------------------------------------------------------ #
    #  Основной handler                                                    #
    # ------------------------------------------------------------------ #
    def get(self, request, pk):
        import subprocess, tempfile, os, shutil, re, urllib.parse, threading
        from django.http import FileResponse

        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)

        # Параметры запроса
        try:
            start          = float(request.query_params.get('start', 0))
            end            = float(request.query_params.get('end', 0))
            episode        = int(request.query_params.get('episode', 1))
            season         = int(request.query_params.get('season', 1))
            translation_id = request.query_params.get('translation_id')
            label          = request.query_params.get('label', 'clip')[:40]
        except (ValueError, TypeError):
            return Response({'error': 'Некорректные параметры'}, status=400)

        # end=99999 — специальное значение «скачать целиком»
        full_episode = (end >= 99990)
        duration = end - start
        if not full_episode and duration <= 0:
            return Response({'error': 'Конец должен быть позже начала'}, status=400)

        # Шаг 1: URL плеера серии
        episode_url = self._get_episode_player_url(anime, episode, season, translation_id)
        if not episode_url:
            return Response({'error': 'Не удалось найти серию в Kodik'}, status=503)

        # Шаг 2: прямой m3u8
        user_ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '1.1.1.1')
        )
        m3u8_url = self._get_m3u8_via_api(episode_url, user_ip=user_ip)
        if not m3u8_url:
            return Response({'error': 'Не удалось получить ссылку на видео от Kodik'}, status=503)

        # Шаг 3: нарезка через ffmpeg
        ffmpeg_bin = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
        if not ffmpeg_bin or not os.path.isfile(ffmpeg_bin):
            return Response({'error': 'ffmpeg не установлен. Выполните: apt-get install -y ffmpeg'}, status=503)

        safe_title = re.sub(r'[^\w\s\-]', '', anime.title_ru or anime.title_en or f'anime_{pk}').strip()[:50]
        safe_label = re.sub(r'[^\w\s\-]', '', label).strip()
        filename   = f'{safe_title} - Ep{episode} - {safe_label}.mp4'

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name

        # Таймаут: целая серия может идти долго; даём 90 минут на целиком, 15 мин на фрагмент
        ffmpeg_timeout = 5400 if full_episode else 900

        try:
            # Общие флаги для HLS/m3u8
            hls_flags = [
                '-headers', 'Referer: https://kodik.info/\r\nOrigin: https://kodik.info\r\n',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_delay_max', '10',
            ]

            if full_episode:
                # Скачиваем всю серию — без -ss и -t
                cmd = [
                    ffmpeg_bin, '-y',
                    *hls_flags,
                    '-i', m3u8_url,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-movflags', '+faststart',
                    tmp_path,
                ]
            else:
                # Нарезаем фрагмент: -ss после -i (точный seek для HLS)
                cmd = [
                    ffmpeg_bin, '-y',
                    *hls_flags,
                    '-i', m3u8_url,
                    '-ss', str(start),
                    '-t', str(duration),
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-movflags', '+faststart',
                    tmp_path,
                ]

            result = subprocess.run(cmd, capture_output=True, timeout=ffmpeg_timeout)

            if result.returncode != 0:
                err = result.stderr.decode('utf-8', errors='replace')[-800:]
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                return Response({'error': f'ffmpeg ошибка: {err}'}, status=500)

            # Проверяем что файл не пустой
            if os.path.getsize(tmp_path) < 1000:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                return Response({'error': 'ffmpeg создал пустой файл — возможно ссылка уже истекла'}, status=500)

            # Отдаём файл
            encoded_name = urllib.parse.quote(filename)
            response = FileResponse(
                open(tmp_path, 'rb'),
                content_type='video/mp4',
                as_attachment=True,
                filename=filename,
            )
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_name}"
            response['X-Accel-Buffering']   = 'no'

            def _cleanup():
                import time as _t
                _t.sleep(60)
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            threading.Thread(target=_cleanup, daemon=True).start()
            return response

        except subprocess.TimeoutExpired:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            return Response({'error': 'Таймаут: обработка заняла слишком долго'}, status=504)
        except Exception as e:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class EpisodeProgressUndoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, anime_id, episode_number):
        try:
            ep = UserEpisodeProgress.objects.get(user=request.user, anime_id=anime_id, episode_number=episode_number)
            ep.status = 'in_progress'
            ep.is_manually_marked = False
            ep.watched_at = None
            ep.save(update_fields=['status', 'is_manually_marked', 'watched_at'])
            return Response({'episode_number': episode_number, 'status': 'in_progress', 'undone': True})
        except UserEpisodeProgress.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)
