from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseServerError,
    StreamingHttpResponse,
)
import tempfile
import os
from django.db.models import Q
from django.utils import timezone
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
from .models import (
    Anime,
    AnimeEpisodeNotification,
    Franchise,
    Genre,
    Episode,
    Translation,
    WatchProgress,
    CustomDub,
    UserEpisodeProgress,
    AnimeAnnouncement,
)
from .serializers import (
    AnimeSerializer,
    AnimeDetailSerializer,
    GenreSerializer,
    FranchiseSerializer,
    FranchiseSerializer,
    AnnouncementSerializer,
)
from .services.anime_parser_service import (
    AnimeParserService,
    VideoStreamingService,
    CacheService,
    AnimeUpdateService,
)
from .kodik_config import (
    KODIK_API_TOKEN,
    KODIK_PRIVATE_KEY,
    KODIK_API_BASE,
    KODIK_PLAYER_BASE,
    KODIK_VIDEO_BASE,
    normalize_kodik_player_link,
)

# Инициализация сервисов (в try/except чтобы ошибки парсера не ломали весь модуль)
try:
    anime_parser_service = AnimeParserService()
    video_streaming_service = VideoStreamingService()
    cache_service = CacheService()
    anime_update_service = AnimeUpdateService()
except Exception as _svc_init_err:
    import logging

    logging.getLogger(__name__).warning(
        f"Anime parser services failed to initialize: {_svc_init_err}"
    )
    anime_parser_service = None
    video_streaming_service = None
    cache_service = None
    anime_update_service = None


# Функция для нормализации строки поиска
# Знаки -, :, и пробел считаются за один разделитель
def normalize_search_string(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    # Заменяем дефисы, двоеточия и множественные пробелы на одиночные пробелы
    text = re.sub(r"[-:\s]+", " ", text)
    # Убираем все кроме букв, цифр и пробелов
    text = re.sub(r"[^а-яa-z0-9\s]", "", text)
    # Убираем лишние пробелы
    text = " ".join(text.split())
    return text


def normalize_search_stringFlexible(text: str) -> str:
    """
    Гибкая нормализация: сохраняет возможность поиска и слитно, и раздельно.
    "ван-пис" → "ванпис" (слитно)
    "ван пис" → "ван пис" (раздельно)
    """
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    # Убираем дефисы и двоеточия ВООБЩЕ (не заменяем на пробел)
    text = text.replace("-", "").replace(":", "")
    # Убираем все кроме букв и цифр
    text = re.sub(r"[^а-яa-z0-9]", "", text)
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
    """
    Нечеткий поиск аниме.
    Поддерживает поиск "ван-пис", "ван пис", "ванпис" - все варианты находят одно и то же.
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        query = query.strip()
        logging.getLogger(__name__).debug("fuzzy_search_anime query=%r", query)
        
        # Создаем два варианта нормализации:
        # 1. Слитный: "ван-пис" → "ванпис", "ван пис" → "ванпис"
        query_compact = normalize_search_stringFlexible(query)
        # 2. Раздельный: "ван-пис" → "ван пис", "ван пис" → "ван пис"
        query_normalized = normalize_search_string(query)
        search_words = query_normalized.split()
        
        logging.getLogger(__name__).debug(f"Compact: {query_compact!r}, Normalized: {query_normalized!r}, Words: {search_words}")
        
        # Получаем аниме с русскими буквами в названии, сортируем по рейтингу
        queryset = Anime.objects.filter(
            title_ru__regex=r"[а-яёА-ЯЁ]"
        ).order_by("-score")[:limit * 5]  # Берем с запасом
        
        # Фильтруем в Python
        results = []
        seen_ids = set()  # Для удаления дубликатов
        
        for anime in queryset:
            if len(results) >= limit:
                break

            # Пропускаем дубликаты
            if anime.id in seen_ids:
                continue
            
            # Собираем все текстовые поля для поиска (оба варианта нормализации)
            searchable_compact = [
                normalize_search_stringFlexible(anime.title_ru or ""),
                normalize_search_stringFlexible(anime.title_en or ""),
                normalize_search_stringFlexible(anime.title_jp or ""),
                normalize_search_stringFlexible(anime.slug or ""),
            ]
            
            searchable_split = [
                normalize_search_string(anime.title_ru or ""),
                normalize_search_string(anime.title_en or ""),
                normalize_search_string(anime.title_jp or ""),
                normalize_search_string(anime.slug or ""),
            ]
            
            # Проверяем совпадение
            found = False
            
            # Вариант 1: Ищем слитный запрос (для "ван-пис", "ванпис")
            if len(query_compact) >= 2:
                for text in searchable_compact:
                    if query_compact in text:
                        found = True
                        break
                
            # Вариант 2: Если не нашли слитно, ищем по словам (AND логика)
            if not found and search_words:
                for text in searchable_split:
                    if all(word in text for word in search_words if len(word) >= 2):
                        found = True
                        break
            
            # Если нашли - добавляем результат
            if found:
                seen_ids.add(anime.id)
                poster_url = (
                    anime.poster_image_url
                    if hasattr(anime, "poster_image_url")
                    else anime.poster_url
                )
                results.append({
                    "id": anime.id,
                    "title_ru": anime.title_ru or "",
                    "title_en": anime.title_en or "",
                    "title_jp": anime.title_jp or "",
                    "year": anime.year,
                    "status": anime.status,
                    "kind": anime.kind,
                    "episodes": anime.episodes,
                    "score": anime.score,
                    "poster_url": poster_url,
                    "description": anime.description,
                    "match_score": 1.0,
                    "source": "database",
                })
        
        logging.getLogger(__name__).debug(f"fuzzy_search_anime returned {len(results)} results")
        return results
        
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
                id_type="shikimori",
                seria_num=episode,
                translation_id=translation_id,
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
    video_url = request.GET.get("url")
    if not video_url:
        return HttpResponseBadRequest("No URL provided")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://kodikplayer.com/",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        return StreamingHttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get("Content-Type", "video/mp4"),
            status=response.status_code,
        )
    except Exception as e:
        print(f"Proxy error: {e}")
        return HttpResponseServerError(str(e))


def _split_param(value):
    """Разбивает строку 'a,b,c' в список ['a','b','c'], убирая пустые."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


class AnimeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с аниме.
    Поддерживает получение по ID или slug.
    """
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer
    permission_classes = [permissions.AllowAny]

    # Поддерживаем поиск по pk (id) и slug
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    
    def get_object(self):
        """
        Переопределенный метод для поддержки поиска по slug.
        Ищет по точному slug, частичному совпадению, или mal_id.
        """
        lookup = self.kwargs.get('pk')
        obj = None
        
        # Пробуем найти по slug если lookup не число
        try:
            int(lookup)
            # Это число - ищем по id
            obj = self.queryset.select_related("franchise").get(pk=lookup)
        except (ValueError, TypeError):
            # Это slug - ищем по точному совпадению
            obj = self.queryset.select_related("franchise").filter(slug=lookup).first()
        
            # Если не нашли по точному slug, пробуем частичное совпадение
            if obj is None:
                obj = self.queryset.select_related("franchise").filter(slug__icontains=lookup).first()
            
            # Если все еще не нашли, пробуем mal_id
            if obj is None:
                try:
                    obj = self.queryset.select_related("franchise").filter(mal_id=lookup).first()
                except Exception:
                    pass
        
            # Если все еще не нашли, пробуем title_en (для английских названий в URL)
            if obj is None:
                try:
                    from django.db.models import Q
                    obj = self.queryset.select_related("franchise").filter(
                        Q(title_en__icontains=lookup) | Q(title_jp__icontains=lookup)
                    ).first()
                except Exception:
                    pass

        if obj is None:
            raise Http404()
            
        # Проверка: title_ru должен содержать русские буквы
        import re
        if not re.search(r"[а-яёА-ЯЁ]", obj.title_ru or ""):
            raise Http404()
            
        return obj

    def get_queryset(self):
        return Anime.objects.all()

    def list(self, request, *args, **kwargs):
        """Список аниме с пагинацией и полноценной фильтрацией

        Важно: анонсы (status='announced') НЕ показываются в общем каталоге.
        Для получения анонсов нужно явно указать status=announced в параметрах.
        """
        queryset = self.get_queryset()

        # Всегда исключаем анонсы по году и названию
        current_year = timezone.now().year
        queryset = queryset.exclude(
            Q(year__gt=current_year) | Q(title_ru__isnull=True) | Q(title_ru="")
        )

        # Исключаем анонсы по статусу, если статус явно не запрошен
        status_param = request.query_params.get("status")
        if not status_param:
            queryset = queryset.exclude(status="announced")

        # Исключаем недоступные аниме, кроме анонсов
        if status_param != "announced":
            queryset = queryset.filter(is_available=True)

        # Исключаем аниме без русских букв в названии ВСЕГДА
        queryset = queryset.filter(title_ru__regex=r"[а-яёА-ЯЁ]")

        # ── Поиск по slug (транслитерированное название) ───────────
        slug = request.query_params.get("slug")
        if slug:
            # Нормализуем slug и разбиваем на слова
            slug_normalized = normalize_search_string(slug)
            slug_words = slug_normalized.split()
            logging.getLogger(__name__).debug(f"Slug param: {slug!r} -> normalized: {slug_normalized!r} -> words: {slug_words}")
            
            if slug_words:
                # Ищем каждое слово в title_ru, title_en, slug - ВСЕ слова должны присутствовать (AND)
                slug_q = Q()
                for word in slug_words:
                    if len(word) < 2:
                        continue
                    word_q = (
                        Q(title_ru__icontains=word) |
                        Q(title_en__icontains=word) |
                        Q(slug__icontains=word)
                    )
                    # Если это первое слово - присваиваем, иначе добавляем через AND
                    if not slug_q:
                        slug_q = word_q
                    else:
                        slug_q &= word_q  # Все слова должны присутствовать
                
                if slug_q:
                    queryset = queryset.filter(slug_q)
            
        # ── Поиск по названию ────────────────────────────────────
        search = request.query_params.get("search")
        if search:
            # Нормализуем поисковый запрос и разбиваем на слова
            search_normalized = normalize_search_string(search)
            search_words = search_normalized.split()
            logging.getLogger(__name__).debug(f"Search param: {search!r} -> normalized: {search_normalized!r} -> words: {search_words}")
            
            if search_words:
                # Строим Q-объект: ВСЕ слова должны присутствовать (AND для слов)
                search_q = Q()
                for word in search_words:
                    if len(word) < 2:  # Игнорируем очень короткие слова
                        continue
                    # Ищем слово в title_ru, title_en, title_jp, slug
                    word_q = (
                        Q(title_ru__icontains=word) |
                        Q(title_en__icontains=word) |
                        Q(title_jp__icontains=word) |
                        Q(slug__icontains=word)
                    )
                    # Если это первое слово - присваиваем, иначе добавляем через AND
                    if not search_q:
                        search_q = word_q
                    else:
                        search_q &= word_q  # ВСЕ слова должны присутствовать (AND)
                
                if search_q:
                    queryset = queryset.filter(search_q)

        # ── Статус (multi-value: ongoing,finished,...) ───────────
        status_param = request.query_params.get("status")
        if status_param:
            statuses = _split_param(status_param)
            if statuses:
                queryset = queryset.filter(status__in=statuses)

        # ── Тип/kind (multi-value: tv,movie,ova,...) ─────────────
        # Поддерживаем оба формата: ?type=tv,movie (через запятую) и ?type=tv&type=movie (multiple)
        type_params = request.query_params.getlist("type")
        if not type_params:
            # Fallback: если getlist не вернул (может быть в виде comma-separated строки)
            type_param = request.query_params.get("type")
            if type_param:
                type_params = _split_param(type_param)

        if type_params:
            kinds = [k.strip() for k in type_params if k.strip()]
            if kinds:
                queryset = queryset.filter(kind__in=kinds)

        # ── Жанры (genres - JSON array field, icontains по строкам) ─
        genres_param = request.query_params.get("genres")
        genre_logic = request.query_params.get("genre_logic", "OR").upper()  # OR | AND
        if genres_param:
            genre_values = _split_param(genres_param)
            # Разрешаем передачу числовых ID жанров → конвертируем в названия
            genre_names = []
            for val in genre_values:
                if val.isdigit():
                    name = (
                        Genre.objects.filter(id=int(val))
                        .values_list("name", flat=True)
                        .first()
                    )
                    if name:
                        genre_names.append(name)
                else:
                    genre_names.append(val)

            if genre_names:
                if genre_logic == "AND":
                    # Должны присутствовать ВСЕ жанры
                    for gn in genre_names:
                        queryset = queryset.filter(genres__icontains=gn)
                    queryset = queryset.distinct()
                else:
                    # OR - хотя бы один жанр
                    genre_q = Q()
                    for gn in genre_names:
                        genre_q |= Q(genres__icontains=gn)
                    queryset = queryset.filter(genre_q).distinct()

        # ── Студия (studios - JSON array field) ─────────────────
        # Поддерживаем оба формата: ?studio=Madhouse,Sunrise (через запятую) и ?studio=Madhouse&studio=Sunrise (multiple)
        studio_params = request.query_params.getlist("studio")
        if not studio_params:
            # Fallback: если getlist не вернул (может быть в виде comma-separated строки)
            studio_param = request.query_params.get("studio")
            if studio_param:
                studio_params = _split_param(studio_param)

        if studio_params:
            studios = [s.strip() for s in studio_params if s.strip()]
            if studios:
                # Для PostgreSQL JSONField используем contains для проверки вхождения в массив
                # Пробуем несколько вариантов для надежности
                studio_q = Q()
                for s in studios:
                    # icontains работает для JSONField как проверка подстроки в JSON представлении
                    studio_q |= Q(studios__icontains=s)
                queryset = queryset.filter(studio_q).distinct()

        # ── Год ─────────────────────────────────────────────────
        year_from = request.query_params.get("year_from")
        year_to = request.query_params.get("year_to")
        if year_from is not None and year_from != '':
            try:
                queryset = queryset.filter(year__gte=int(year_from))
            except ValueError:
                pass
        if year_to is not None and year_to != '':
            try:
                queryset = queryset.filter(year__lte=int(year_to))
            except ValueError:
                pass

        # ── Рейтинг ──────────────────────────────────────────────
        score_from = request.query_params.get("score_from")
        score_to = request.query_params.get("score_to")
        if score_from is not None and score_from != '':
            try:
                queryset = queryset.filter(score__gte=float(score_from))
            except ValueError:
                pass
        if score_to is not None and score_to != '':
            try:
                queryset = queryset.filter(score__lte=float(score_to))
            except ValueError:
                pass

        # ── Эпизоды ──────────────────────────────────────────────
        episodes_from = request.query_params.get("episodes_from")
        episodes_to = request.query_params.get("episodes_to")
        if episodes_from is not None and episodes_from != '':
            try:
                queryset = queryset.filter(episodes__gte=int(episodes_from))
            except ValueError:
                pass
        if episodes_to is not None and episodes_to != '':
            try:
                # Если episodes_to = 0, пропускаем этот фильтр (бессмысленно)
                ep_to_val = int(episodes_to)
                if ep_to_val > 0:
                    queryset = queryset.filter(
                        episodes__lte=ep_to_val, episodes__isnull=False
                    )
            except ValueError:
                pass

        # ── Исключить из коллекции пользователя ──────────────────
        excluded_library_statuses = request.query_params.get(
            "excluded_library_statuses"
        )
        if excluded_library_statuses and request.user.is_authenticated:
            excluded_statuses = _split_param(excluded_library_statuses)
            if excluded_statuses:
                # Базовый фильтр: исключаем по статусам
                q = Q(user=request.user, status__in=excluded_statuses)

                # Если среди исключаемых есть 'favorite' - также исключаем по is_favorite=True
                # (т.к. избранное хранится как is_favorite=True, а не status='favorite')
                if 'favorite' in excluded_statuses:
                    q |= Q(user=request.user, is_favorite=True)

                user_library_anime_ids = UserLibrary.objects.filter(q).values_list("anime_id", flat=True)
                queryset = queryset.exclude(id__in=user_library_anime_ids)
                print(f"[FILTER] excluded_library_statuses={excluded_statuses}, excluded {len(set(user_library_anime_ids))} anime IDs")
        elif excluded_library_statuses and not request.user.is_authenticated:
            print(f"[FILTER] excluded_library_statuses={excluded_library_statuses} but user not authenticated")

        # ── Сезон (season + season_year) ─────────────────────────
        season_year = request.query_params.get("season_year")
        if season_year:
            try:
                queryset = queryset.filter(year=int(season_year))
            except ValueError:
                pass

        # ── Сортировка ───────────────────────────────────────────
        ordering = request.query_params.get("ordering", "-score")
        shuffle = request.query_params.get("shuffle", "").lower() in (
            "true",
            "1",
            "yes",
        )

        VALID_ORDER_FIELDS = {
            "score",
            "-score",
            "year",
            "-year",
            "title_ru",
            "-title_ru",
            "episodes",
            "-episodes",
            "created_at",
            "-created_at",
        }
        if ordering not in VALID_ORDER_FIELDS:
            ordering = "-score"

        if shuffle:
            # Перемешивание - используем random() для PostgreSQL
            queryset = queryset.order_by("?")
        else:
            # Для сортировки по эпизодам используем Coalesce чтобы NULL были в конце
            from django.db.models import Value
            from django.db.models.functions import Coalesce
            
            if ordering == "episodes":
                queryset = queryset.order_by(Coalesce("episodes", Value(0)))
            elif ordering == "-episodes":
                queryset = queryset.order_by(Coalesce("episodes", Value(0)).desc())
            else:
                queryset = queryset.order_by(ordering)

        # ── Пагинация ────────────────────────────────────────────
        try:
            page_size = min(int(request.query_params.get("page_size", 20)), 500)
        except ValueError:
            page_size = 20
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        total_pages = max((total_count + page_size - 1) // page_size, 1)

        serializer = AnimeSerializer(queryset[start:end], many=True)

        print(f"Final count: {total_count}, page: {page}, page_size: {page_size}")

        return Response(
            {
                "results": serializer.data,
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            anime = self.get_object()
            
            if not anime.screenshots and anime.shikimori_id:
                try:
                    search_params = {
                        "token": KODIK_API_TOKEN,
                        "shikimori_id": anime.shikimori_id,
                        "with_material_data": True,
                        "limit": 1,
                    }
                    response = requests.get(
                        f"{KODIK_API_BASE}/search", params=search_params, timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        if results:
                            result = results[0]
                            kodik_screenshots = result.get("screenshots", [])
                            if kodik_screenshots:
                                anime.screenshots = kodik_screenshots
                                anime.save(update_fields=["screenshots", "updated_at"])
                except Exception as e:
                    print(f"Не удалось загрузить скриншоты из Kodik: {e}")
                    
            serializer = AnimeDetailSerializer(anime)
            return Response(serializer.data)
            
        except Http404:
            return Response(
                {"error": "Аниме не найдено"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"Error in AnimeViewSet.retrieve: {e}")
            print(traceback.format_exc())
            return Response(
                {
                    "error": f"Ошибка получения аниме: {str(e)}",
                    "detail": traceback.format_exc(),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def episodes(self, request, pk=None):
        try:
            anime = self.get_object()
            episodes = Episode.objects.filter(anime=anime).order_by("number")
            episodes_data = []
            for episode in episodes:
                episodes_data.append(
                    {
                        "id": episode.id,
                        "number": episode.number,
                        "title": episode.title,
                        "title_en": episode.title_en,
                        "description": episode.description,
                        "air_date": episode.air_date,
                    }
                )
            return Response(
                {
                    "anime_id": anime.id,
                    "anime_title": anime.title_ru,
                    "episodes": episodes_data,
                    "total_episodes": len(episodes_data),
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения эпизодов: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def translations(self, request, pk=None):
        try:
            anime = self.get_object()
            translations = Translation.objects.filter(anime=anime, status="active")
            translations_data = []
            for translation in translations:
                translations_data.append(
                    {
                        "id": translation.id,
                        "name": translation.name,
                        "type": translation.get_translation_type_display(),
                        "studio_name": translation.studio_name,
                        "is_complete": translation.is_complete,
                        "episodes_count": translation.episodes_count,
                    }
                )
            return Response(
                {
                    "anime_id": anime.id,
                    "anime_title": anime.title_ru,
                    "translations": translations_data,
                    "total_translations": len(translations_data),
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения переводов: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def kodik_player(self, request, pk=None):
        print(f"\n=== KODIK_PLAYER для аниме ID: {pk} ===")
        try:
            anime = self.get_object()
            if anime.kodik_link:
                return Response({"kodik_link": anime.kodik_link, "source": "database"})
            if not anime.shikimori_id:
                return Response(
                    {"error": "У аниме нет Shikimori ID для поиска в Kodik"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            search_params = {
                "token": KODIK_API_TOKEN,
                "shikimori_id": anime.shikimori_id,
                "with_material_data": True,
                "limit": 1,
            }
            response = requests.get(
                f"{KODIK_API_BASE}/search", params=search_params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                anime.is_available = False
                anime.save(update_fields=["is_available", "updated_at"])
                return Response(
                    {
                        "error": "Аниме не найдено в Kodik API",
                        "shikimori_id": anime.shikimori_id,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            result = results[0]
            kodik_link = result.get("link")
            if not kodik_link:
                anime.is_available = False
                anime.save(update_fields=["is_available", "updated_at"])
                return Response(
                    {
                        "error": "Ссылка на плеер не найдена в ответе Kodik",
                        "result": result,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            anime.kodik_link = normalize_kodik_player_link(kodik_link)
            anime.kodik_id = result.get("id", "")
            anime.quality = result.get("quality", "")
            anime.screenshots = result.get("screenshots", [])
            anime.seasons = result.get("seasons", {})
            anime.last_season = result.get("last_season")
            anime.last_episode = result.get("last_episode")
            anime.is_available = True
            anime.save()
            return Response(
                {
                    "kodik_link": kodik_link,
                    "source": "kodik_api",
                    "quality": anime.quality,
                    "last_episode": anime.last_episode,
                    "seasons": anime.seasons,
                }
            )
        except requests.RequestException as e:
            return Response(
                {"error": f"Ошибка запроса к Kodik API: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response(
                {"error": f"Ошибка получения плеера: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def get_video_link(self, request, pk=None):
        print(f"\n=== GET_VIDEO_LINK для аниме ID: {pk} ===")
        try:
            anime = self.get_object()
            episode = int(request.query_params.get("episode", 1))
            translation_id = request.query_params.get("translation_id", "0")
            quality = request.query_params.get("quality", "720")
            if not video_streaming_service:
                return Response(
                    {"error": "Сервис видео недоступен"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            video_sources = video_streaming_service.get_video_sources(
                str(anime.shikimori_id), episode, translation_id
            )
            if not video_sources:
                return Response(
                    {
                        "error": "Видео источники не найдены",
                        "anime_id": pk,
                        "video_url": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            for source_name, source_data in video_sources.items():
                if source_name == "kodik" and source_data.get("video_url"):
                    video_url = source_data["video_url"]
                    proxy_url = (
                        f"https://anisphere.org/api/anime/proxy/video/?url={video_url}"
                    )
                    return Response(
                        {
                            "video_url": proxy_url,
                            "quality": quality,
                            "episode": episode,
                            "translation_id": translation_id,
                            "source": source_name,
                            "m3u8_url": source_data.get("m3u8_url"),
                            "note": "Видео через прокси",
                        }
                    )
                elif source_name == "aniboom" and source_data.get("mpd_content"):
                    return Response(
                        {
                            "video_url": None,
                            "mpd_content": source_data["mpd_content"],
                            "quality": quality,
                            "episode": episode,
                            "translation_id": translation_id,
                            "source": source_name,
                            "format": "mpd",
                            "note": "MPD формат требует специального плеера",
                        }
                    )
            return Response(
                {
                    "error": "Подходящий видео источник не найден",
                    "available_sources": list(video_sources.keys()),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response(
                {"error": f"Ошибка получения видео: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def update_from_parser(self, request, pk=None):
        try:
            anime = self.get_object()
            if not anime.shikimori_id:
                return Response(
                    {"error": "У аниме нет Shikimori ID для обновления"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not anime_parser_service:
                return Response(
                    {"error": "Сервис парсера недоступен"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            fresh_data = anime_parser_service.get_anime_by_id(
                anime.shikimori_id, "shikimori"
            )
            if not fresh_data:
                return Response(
                    {"error": "Не удалось получить данные из парсера"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            updated_anime = anime_parser_service.import_anime_to_db(
                fresh_data, "shikimori"
            )
            return Response(
                {
                    "message": "Данные аниме успешно обновлены",
                    "anime_id": updated_anime.id,
                    "title": updated_anime.title_ru,
                    "episodes": updated_anime.episodes,
                    "status": updated_anime.status,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка обновления аниме: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def watch_progress(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Требуется аутентификация"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            anime = self.get_object()
            if not video_streaming_service:
                return Response(
                    {"error": "Сервис видео недоступен"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            progress = video_streaming_service.get_watch_progress(
                request.user, anime.id
            )
            return Response(
                {
                    "anime_id": anime.id,
                    "anime_title": anime.title_ru,
                    "progress": progress,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения прогресса: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def save_watch_progress(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Требуется аутентификация"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            anime = self.get_object()
            episode_id = request.data.get("episode_id")
            current_time = request.data.get("current_time", 0)
            duration = request.data.get("duration")
            if not episode_id:
                return Response(
                    {"error": "Требуется episode_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not video_streaming_service:
                return Response(
                    {"error": "Сервис видео недоступен"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            progress = video_streaming_service.save_watch_progress(
                request.user, anime.id, episode_id, current_time, duration
            )
            if progress:
                return Response(
                    {
                        "message": "Прогресс сохранен",
                        "progress": {
                            "episode_id": progress.episode.id,
                            "current_time": progress.current_time,
                            "is_completed": progress.is_completed,
                        },
                    }
                )
            else:
                return Response(
                    {"error": "Не удалось сохранить прогресс"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"error": f"Ошибка сохранения прогресса: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для анонсов аниме из таблицы anime_announcements"""
    queryset = AnimeAnnouncement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = AnimeAnnouncement.objects.all()
        
        # Фильтрация по статусу
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Фильтрация по типу
        type_param = self.request.query_params.get('type')
        if type_param:
            queryset = queryset.filter(type=type_param)
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title_ru__icontains=search) | Q(title_en__icontains=search)
            )

        # Сортировка - только допустимые поля (release_date это строка, поэтому используем created_at)
        ordering = self.request.query_params.get('ordering', '-created_at')
        valid_orderings = {
            '-created_at', 'created_at',
            '-score', 'score',
            'title_ru', '-title_ru'
        }
        if ordering not in valid_orderings:
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)

        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Поддержка получения по id, английскому slug или русскому slug"""
        lookup = kwargs.get('pk')
        instance = None
        
        # Пробуем найти по id если lookup число
        try:
            int(lookup)
            # Это число - ищем по id
            instance = self.queryset.filter(id=lookup).first()
        except (ValueError, TypeError):
            # Это slug - пробуем найти в приоритете:
            # 1. По точному slug (русский слаг из БД)
            # 2. По title_en (английское название)
            # 3. По title_ru (русское название)
            
            # 1. Пробуем по точному slug
            instance = self.queryset.filter(slug=lookup).first()
            
            # 2. Если не нашли, пробуем по title_en
            if not instance:
                instance = self.queryset.filter(
                    title_en__isnull=False,
                    title_en__icontains=lookup.replace('-', ' ')
                ).first()
                
                # Пробуем по отдельным словам из slug
                if not instance:
                    words = lookup.split('-')
                    if len(words) > 1:
                        query = Q()
                        for word in words:
                            if len(word) > 2:  # Игнорируем короткие слова
                                query |= Q(title_en__icontains=word)
                        instance = self.queryset.filter(query).first()
            
            # 3. Если не нашли, пробуем по title_ru
            if not instance:
                instance = self.queryset.filter(
                    title_ru__icontains=lookup.replace('-', ' ')
                ).first()
                
                # Пробуем по отдельным словам из slug
                if not instance:
                    words = lookup.split('-')
                    if len(words) > 1:
                        query = Q()
                        for word in words:
                            if len(word) > 2:  # Игнорируем короткие слова
                                query |= Q(title_ru__icontains=word)
                        instance = self.queryset.filter(query).first()
            
        # Если всё ещё не нашли - 404
        if not instance:
            return Response(
                {"detail": "Анонс не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Пагинация
        try:
            page_size = min(int(request.query_params.get("page_size", 20)), 100)
        except ValueError:
            page_size = 20
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        total_pages = max((total_count + page_size - 1) // page_size, 1)

        serializer = self.get_serializer(queryset[start:end], many=True)

        return Response(
            {
                "results": serializer.data,
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )


class FranchiseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Franchise.objects.prefetch_related("entries").all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FranchiseSerializer
        return FranchiseSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        slug = request.query_params.get("slug")

        # Поиск по slug (транслитерированное название)
        if slug:
            # Транслитерируем slug обратно для поиска или ищем по транслитерированному названию
            qs = qs.filter(name__icontains=slug.replace("-", " "))

        if search:
            qs = qs.filter(name__icontains=search)
        page_size = min(int(request.query_params.get("page_size", 20)), 200)
        page = int(request.query_params.get("page", 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        serializer = FranchiseSerializer(qs[start:end], many=True)
        return Response(
            {
                "results": serializer.data,
                "count": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        )

    def retrieve(self, request, *args, **kwargs):
        franchise = self.get_object()
        serializer = FranchiseSerializer(franchise)
        data = serializer.data
        from .serializers import FranchiseEntrySerializer

        # Фильтруем entries: только с русским названием
        entries = franchise.entries.filter(
            title_ru__regex=r"[а-яёА-ЯЁ]"
        ).order_by("franchise_order", "year")
        data["entries"] = FranchiseEntrySerializer(entries, many=True).data
        return Response(data)

    @action(detail=True, methods=["get"])
    def parts(self, request, pk=None):
        """Получить список аниме во франшизе"""
        try:
            franchise = self.get_object()

            # Только аниме с русским названием
            animes = Anime.objects.filter(
                franchise=franchise,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).order_by("franchise_order", "year", "id")

            parts_data = []

            for anime in animes:
                poster_url = anime.poster.url if anime.poster else anime.poster_url
                parts_data.append(
                    {
                        "id": anime.id,
                        "title_ru": anime.title_ru,
                        "title_en": anime.title_en,
                        "title_jp": anime.title_jp,
                        "year": anime.year,
                        "kind": anime.kind,
                        "episodes": anime.episodes,
                        "status": anime.status,
                        "score": anime.score,
                        "poster_url": poster_url,
                        "franchise_order": anime.franchise_order,
                    }
                )

            return Response(
                {
                    "franchise_id": franchise.id,
                    "franchise_name": franchise.name,
                    "parts": parts_data,
                    "total": len(parts_data),
                }
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


class SearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_query = request.query_params.get("q", "")
        query = raw_query.strip()
        try:
            # Увеличиваем лимит до 500 для полноценного поиска
            limit = int(request.query_params.get("limit", 500))
            if limit <= 0:
                limit = 500
            # Ограничиваем максимум 500
            limit = min(limit, 500)
        except Exception:
            limit = 500
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            "SearchAPIView called; raw_query=%r stripped_query=%r params=%r limit=%d",
            raw_query,
            query,
            dict(request.query_params),
            limit,
        )
        if not query:
            return Response(
                {"error": "Требуется параметр поиска q"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            db_results = fuzzy_search_anime(query, limit)
            try:
                for result in db_results:
                    result.pop("match_score", None)
            except Exception:
                logging.getLogger(__name__).exception("Failed to sanitize db_results")
            return Response(
                {
                    "query": query,
                    "results": db_results,
                    "total": len(db_results),
                    "source": "database",
                }
            )
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            logging.getLogger(__name__).exception("Error in SearchAPIView: %s", tb)
            return Response(
                {
                    "error": f"Ошибка поиска: {str(e)}",
                    "query": query,
                    "results": [],
                    "total": 0,
                    "source": "error",
                    "debug": repr(e),
                    "debug_traceback": tb,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParserStatusAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            if not anime_parser_service:
                return Response(
                    {"error": "Сервис парсера недоступен", "status": "unhealthy"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            health_status = anime_parser_service.parser.health_check()
            return Response(
                {
                    "parsers": health_status,
                    "total_parsers": len(health_status),
                    "active_parsers": sum(
                        1 for status in health_status.values() if status
                    ),
                    "status": "healthy" if any(health_status.values()) else "unhealthy",
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка проверки статуса: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdatesAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))
        try:
            if not anime_update_service:
                return Response(
                    {
                        "error": "Сервис обновлений недоступен",
                        "updates": [],
                        "total": 0,
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            updates = anime_update_service.get_recent_updates(limit)
            return Response({"updates": updates, "total": len(updates)})
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения обновлений: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
            return Response(
                {"error": f"Ошибка получения жанров: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KodikImportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from anime.models import Anime

        data = request.data
        if "shikimori_id" in data:
            return self._import_single_anime(data)
        else:
            return self._import_all_anime(data)

    def _import_single_anime(self, data):
        try:
            shikimori_id = data.get("shikimori_id")
            kodik_data = data.get("kodik_data")
            if not shikimori_id:
                return Response(
                    {"error": "Требуется shikimori_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if kodik_data:
                anime = self._create_anime_from_kodik(kodik_data)
                return Response(
                    {
                        "message": "Аниме успешно импортировано",
                        "anime_id": anime.id,
                        "title": anime.title_ru,
                    }
                )
            return Response(
                {"error": "Требуются данные Kodik"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка импорта: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _import_all_anime(self, data):
        from backend.kodik_import import fetch_all_results, process_results

        try:
            limit = data.get("limit", 0)
            debug = data.get("debug", False)
            replace = data.get("replace", False)

            all_anime = fetch_all_results(limit=limit if limit > 0 else None, debug=debug)

            from anime.models import Anime
            existing = Anime.objects.all().values_list("shikimori_id", "kodik_id")
            existing_shikimori = {sid for sid, _ in existing if sid}
            existing_kodik = {kid for _, kid in existing if kid}

            created, skipped, invalid, error_count = process_results(
                all_anime,
                existing_shikimori,
                existing_kodik,
                debug=debug,
                replace=replace,
            )
            return Response(
                {
                    "message": "Импорт завершен",
                    "total_processed": len(all_anime),
                    "imported": created,
                    "skipped": skipped,
                    "invalid": invalid,
                    "errors": error_count,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка массового импорта: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _create_anime_from_kodik(self, kodik_data):
        from anime.models import Anime

        material_data = kodik_data.get("material_data", {})
        episodes_count = (
            material_data.get("episodes_total") or kodik_data.get("episodes_count") or 1
        )
        genre_names = (
            material_data.get("anime_genres") or material_data.get("genres") or []
        )
        studio_names = material_data.get("anime_studios") or []
        poster_url = (
            material_data.get("anime_poster_url")
            or material_data.get("poster_url")
            or ""
        )
        score = (
            material_data.get("shikimori_rating")
            or material_data.get("kinopoisk_rating")
            or 0.0
        )
        description = (
            material_data.get("anime_description")
            or material_data.get("description")
            or ""
        )
        status_map = {
            "anons": "announced",
            "ongoing": "ongoing",
            "released": "finished",
            "discontinued": "canceled",
        }
        status = status_map.get(
            material_data.get("anime_status", "released"), "finished"
        )
        kind_map = {
            "tv": "tv",
            "tv_13": "tv",
            "tv_24": "tv",
            "tv_48": "tv",
            "movie": "movie",
            "ova": "ova",
            "ona": "ona",
            "special": "special",
            "music": "music",
        }
        kind = kind_map.get(
            material_data.get("anime_kind") or kodik_data.get("type", "tv"), "tv"
        )
        anime, created = Anime.objects.update_or_create(
            shikimori_id=kodik_data.get("shikimori_id"),
            defaults={
                "title_ru": kodik_data.get("title", ""),
                "title_en": kodik_data.get("title_orig", ""),
                "title_jp": kodik_data.get("other_title", ""),
                "description": description,
                "year": kodik_data.get("year"),
                "status": status,
                "kind": kind,
                "episodes": episodes_count,
                "score": score,
                "poster_url": poster_url,
                "genres": genre_names,
                "studios": studio_names,
                "data_source": "kodik",
                "movies": [],
                "ovas": [],
                "movie_count": 0,
                "ova_count": 0,
                "total_items": 1,
            },
        )
        return anime


class KodikFiltersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import requests

        try:
            genres_response = requests.get(
                f"{KODIK_API_BASE}/genres",
                params={
                    "token": KODIK_API_TOKEN,
                    "types": "anime-serial,anime",
                    "genres_type": "shikimori",
                    "sort": "title",
                },
            )
            years_response = requests.get(
                f"{KODIK_API_BASE}/years",
                params={
                    "token": KODIK_API_TOKEN,
                    "types": "anime-serial,anime",
                    "sort": "year",
                    "order": "desc",
                },
            )
            studios_response = requests.get(
                f"{KODIK_API_BASE}/anime_studios",
                params={
                    "token": KODIK_API_TOKEN,
                    "types": "anime-serial,anime",
                    "sort": "title",
                },
            )
            translations_response = requests.get(
                f"{KODIK_API_BASE}/translations/v2",
                params={
                    "token": KODIK_API_TOKEN,
                    "types": "anime-serial,anime",
                    "sort": "title",
                },
            )
            return Response(
                {
                    "genres": genres_response.json().get("results", []),
                    "years": years_response.json().get("results", []),
                    "studios": studios_response.json().get("results", []),
                    "translations": translations_response.json().get("results", []),
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения фильтров: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KodikTranslationsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
            if not anime.shikimori_id:
                return Response(
                    {"error": "У аниме нет Shikimori ID"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            search_params = {
                "token": KODIK_API_TOKEN,
                "shikimori_id": anime.shikimori_id,
                "with_episodes_data": False,
                "limit": 100,
            }
            response = requests.get(
                f"{KODIK_API_BASE}/search", params=search_params, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                return Response({"translations": [], "total": 0})
            translations_map = {}
            for result in results:
                translation = result.get("translation", {})
                if not translation:
                    continue
                translation_id = translation.get("id")
                translation_name = translation.get("title", "Неизвестно")
                translation_type = translation.get("type", "voice")
                if translation_id not in translations_map:
                    translations_map[translation_id] = {
                        "id": translation_id,
                        "name": translation_name,
                        "type": translation_type,
                        "quality": result.get("quality", ""),
                        "episodes_done": 0,
                        "total_episodes": result.get("episodes_count")
                        or anime.episodes,
                        "is_complete": False,
                        "kodik_link": result.get("link", ""),
                        "logo": None,
                    }
                t = translations_map[translation_id]
                episodes = result.get("episodes_count") or 0
                if episodes > t["episodes_done"]:
                    t["episodes_done"] = episodes
            translations = list(translations_map.values())
            translations.sort(key=lambda x: x["episodes_done"], reverse=True)
            return Response({"translations": translations, "total": len(translations)})
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except requests.RequestException as e:
            return Response(
                {"error": f"Ошибка запроса к Kodik API: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения озвучек: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnimeAnnouncementsView(APIView):
    """Получение анонсов из таблицы anime_schedule (Jikan API)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .models import AnimeSchedule
        from .serializers import AnimeScheduleSerializer

        # Фильтр: анонсы (Not yet aired) или не идущие в эфире
        queryset = AnimeSchedule.objects.filter(
            Q(status="Not yet aired") | Q(airing=False)
        )

        # Поиск по названию
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title_ru__icontains=search) | Q(title__icontains=search)
            )

        # Сортировка
        ordering = request.query_params.get("ordering", "-year")
        valid_orderings = {"year", "-year", "score", "-score", "title_ru", "-title_ru", "mal_id", "-mal_id"}
        if ordering not in valid_orderings:
            ordering = "-year"
        queryset = queryset.order_by(ordering)

        # Пагинация
        try:
            page_size = min(int(request.query_params.get("page_size", 200)), 500)
        except ValueError:
            page_size = 200
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        total_pages = max((total_count + page_size - 1) // page_size, 1)

        serializer = AnimeScheduleSerializer(queryset[start:end], many=True)

        return Response(
            {
                "results": serializer.data,
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )


class CustomDubListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
            custom_dubs = CustomDub.objects.filter(
                anime=anime, status="approved"
            ).order_by("-rating", "-created_at")
            dubs_data = []
            for dub in custom_dubs:
                dubs_data.append(
                    {
                        "id": dub.id,
                        "name": dub.name,
                        "studio": dub.studio,
                        "description": dub.description,
                        "quality": dub.quality,
                        "logo": dub.logo_url,
                        "episodes_done": dub.episodes_done,
                        "total_episodes": dub.total_episodes or anime.episodes,
                        "is_complete": dub.is_complete,
                        "is_custom": True,
                        "rating": dub.rating,
                        "views_count": dub.views_count,
                    }
                )
            return Response({"dubs": dubs_data, "total": len(dubs_data)})
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, anime_id):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Требуется авторизация"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            anime = Anime.objects.get(pk=anime_id)
            name = request.data.get("name")
            studio = request.data.get("studio", "")
            quality = request.data.get("quality")
            video_url = request.data.get("video_url")
            logo_url = request.data.get("logo_url", "")
            description = request.data.get("description", "")
            episodes_done = request.data.get("episodes_done", 0)
            is_complete = request.data.get("is_complete", False)
            if not name or not quality or not video_url:
                return Response(
                    {
                        "error": "Необходимо указать название, качество и ссылку на видео"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            existing_dub = CustomDub.objects.filter(
                anime=anime, created_by=request.user, name=name
            ).first()
            if existing_dub:
                return Response(
                    {"error": "Вы уже добавляли озвучку с таким названием"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
                status="pending",
            )
            return Response(
                {
                    "message": "Озвучка отправлена на модерацию",
                    "dub_id": dub.id,
                    "status": dub.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка добавления озвучки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomDubDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, anime_id, dub_id):
        try:
            dub = CustomDub.objects.get(id=dub_id, anime_id=anime_id, status="approved")
            dub.views_count += 1
            dub.save(update_fields=["views_count"])
            return Response(
                {
                    "video_url": dub.video_url,
                    "quality": dub.quality,
                    "name": dub.name,
                    "studio": dub.studio,
                    "logo": dub.logo_url,
                }
            )
        except CustomDub.DoesNotExist:
            return Response(
                {"error": "Озвучка не найдена или не одобрена"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения видео: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserLibraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            library_items = UserLibrary.objects.filter(
                user=request.user
            ).select_related("anime")
            library_data = []
            for item in library_items:
                library_data.append(
                    {
                        "id": item.id,
                        "anime": {
                            "id": item.anime.id,
                            "title_ru": item.anime.title_ru,
                            "title_en": item.anime.title_en,
                            "poster_url": item.anime.poster_url,
                            "year": item.anime.year,
                            "episodes": item.anime.episodes,
                            "score": item.anime.score,
                            "kind": item.anime.kind,
                            "status": item.anime.status,
                        },
                        "status": item.status,
                        "last_episode": item.last_episode,
                        "watched_episodes": item.watched_episodes,
                        "total_progress": item.total_progress,
                        "user_score": item.user_score,
                        "last_watched_at": item.last_watched_at.isoformat(),
                        "completed_at": item.completed_at.isoformat()
                        if item.completed_at
                        else None,
                        "created_at": item.created_at.isoformat(),
                    }
                )
            return Response({"library": library_data, "total": len(library_data)})
        except Exception as e:
            return Response(
                {"error": f"Ошибка получения библиотеки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            anime_id = request.data.get("anime")
            status_val = request.data.get("status", "want_to_watch")
            if not anime_id:
                return Response(
                    {"error": "Не указан ID аниме"}, status=status.HTTP_400_BAD_REQUEST
                )
            anime = Anime.objects.get(pk=anime_id)
            existing = UserLibrary.objects.filter(
                user=request.user, anime=anime
            ).first()
            if existing:
                return Response(
                    {"error": "Аниме уже добавлено в библиотеку"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            library_item = UserLibrary.objects.create(
                user=request.user, anime=anime, status=status_val
            )
            return Response(
                {"message": "Аниме добавлено в библиотеку", "id": library_item.id},
                status=status.HTTP_201_CREATED,
            )
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка добавления: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserLibraryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            return Response(
                {
                    "id": item.id,
                    "anime": {
                        "id": item.anime.id,
                        "title_ru": item.anime.title_ru,
                        "title_en": item.anime.title_en,
                        "poster_url": item.anime.poster_url,
                        "year": item.anime.year,
                        "episodes": item.anime.episodes,
                        "score": item.anime.score,
                    },
                    "status": item.status,
                    "last_episode": item.last_episode,
                    "watched_episodes": item.watched_episodes,
                    "total_progress": item.total_progress,
                    "user_score": item.user_score,
                }
            )
        except UserLibrary.DoesNotExist:
            return Response(
                {"error": "Запись не найдена"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            status_val = request.data.get("status")
            last_episode = request.data.get("last_episode")
            watched_episodes = request.data.get("watched_episodes")
            total_progress = request.data.get("total_progress")
            user_score = request.data.get("user_score")
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
            return Response({"message": "Запись обновлена"})
        except UserLibrary.DoesNotExist:
            return Response(
                {"error": "Запись не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка обновления: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            item = UserLibrary.objects.get(pk=pk, user=request.user)
            item.delete()
            return Response({"message": "Аниме удалено из библиотеки"})
        except UserLibrary.DoesNotExist:
            return Response(
                {"error": "Запись не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка удаления: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RandomAnimeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import random

        try:
            ids = list(Anime.objects.filter(title_ru__regex=r"[а-яёА-ЯЁ]").values_list("id", flat=True))
            if not ids:
                return Response(
                    {"error": "Нет аниме"}, status=status.HTTP_404_NOT_FOUND
                )
            random_id = random.choice(ids)
            anime = Anime.objects.get(id=random_id)
            serializer = AnimeSerializer(anime)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentlyWatchingView(APIView):
    """
    «Сейчас смотрят» учитывает три случая:

    1. Плеер активен сейчас (воспроизведение идёт, не зависит от видимости вкладки):
       UserActiveTab.activity_type='player' И last_ping <= 2 минуты назад.

    2. Вкладка активна (прямо сейчас, но не обязательно воспроизводится):
       UserActiveTab.activity_type='watching' И last_ping <= 10 минут назад.

    3. Свежие данные из UserEpisodeProgress как дополнение к (1):
       last_watched <= 2 минуты назад (плеер зафиксировал прогресс).

    viewers_count = количество уникальных пользователей, попадающих хоть в один из случаев.
    """

    permission_classes = [permissions.AllowAny]

    # Временные окна (секунды)
    PLAYER_WINDOW = 2 * 60  # плеер активен - 2 мин
    TAB_WINDOW = 10 * 60  # вкладка открыта - 10 мин
    PROGRESS_WINDOW = 2 * 60  # прогресс зафиксирован - 2 мин

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from anime.models import UserActiveTab

        try:
            now = timezone.now()

            # ── 1. Плеер активен ──────────────────────────────────────
            player_cutoff = now - timedelta(seconds=self.PLAYER_WINDOW)

            # Из UserActiveTab с activity_type='player'
            player_tab = (
                UserActiveTab.objects.filter(
                    activity_type="player", last_ping__gte=player_cutoff
                )
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            player_tab_map = {r["anime_id"]: r["n"] for r in player_tab}

            # Из UserEpisodeProgress (last_watched) - подтверждает факт воспроизведения
            progress_cutoff = now - timedelta(seconds=self.PROGRESS_WINDOW)
            progress_rows = (
                UserEpisodeProgress.objects.filter(last_watched__gte=progress_cutoff)
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            progress_map = {r["anime_id"]: r["n"] for r in progress_rows}

            # ── 2. Вкладка открыта (не плеер) ───────────────────────
            tab_cutoff = now - timedelta(seconds=self.TAB_WINDOW)
            watching_tab = (
                UserActiveTab.objects.filter(
                    activity_type="watching", last_ping__gte=tab_cutoff
                )
                .values("anime_id")
                .annotate(n=Count("user", distinct=True))
            )
            watching_tab_map = {r["anime_id"]: r["n"] for r in watching_tab}

            # ── Объединяем уникальные ID аниме ─────────────────────
            all_ids = set(player_tab_map) | set(progress_map) | set(watching_tab_map)

            if not all_ids:
                return Response({"results": [], "count": 0})

            animes = {a.id: a for a in Anime.objects.filter(id__in=all_ids, title_ru__regex=r"[а-яёА-ЯЁ]")}
            results = []

            for aid in all_ids:
                a = animes.get(aid)
                if not a:
                    continue

                # Уникальные зрители = жесткое объединение пользователей из всех трёх источников.
                # Чтобы не считать одного человека дважды, берём максимум.
                # Сравнение player_tab и progress: возьмём максимум (player_tab записывается в тот же момент)
                player_count = max(player_tab_map.get(aid, 0), progress_map.get(aid, 0))
                watching_count = watching_tab_map.get(aid, 0)
                total = max(
                    player_count, watching_count
                )  # макс: один человек может попасть в несколько срезов

                data = AnimeSerializer(a).data
                data["viewers_count"] = total
                data["has_active_player"] = aid in player_tab_map or aid in progress_map
                data["has_active_tab"] = aid in watching_tab_map
                results.append(data)

            results.sort(key=lambda x: x["viewers_count"], reverse=True)
            return Response({"results": results, "count": len(results)})

        except Exception as e:
            import traceback

            return Response(
                {"error": str(e), "detail": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserActiveTabView(APIView):
    """
    API для управления активными вкладками пользователя.
    Позволяет отмечать, что пользователь находится на странице аниме.

    POST /anime/active-tab/
    {
        "anime_id": 123,
        "activity_type": "watching" | "player",  // optional, default: "watching"
        "current_episode": 5  // optional
    }

    DELETE /anime/active-tab/?anime_id=123 - удалить вкладку
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from anime.models import UserActiveTab

        anime_id = request.data.get("anime_id")
        activity_type = request.data.get("activity_type", "watching")
        current_episode = request.data.get("current_episode")

        if not anime_id:
            return Response(
                {"error": "Требуется anime_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

        # Обновляем или создаём запись
        tab, created = UserActiveTab.objects.update_or_create(
            user=request.user,
            anime=anime,
            defaults={
                "activity_type": activity_type,
                "current_episode": current_episode,
            },
        )

        return Response(
            {
                "anime_id": anime.id,
                "activity_type": tab.activity_type,
                "current_episode": tab.current_episode,
                "last_ping": tab.last_ping.isoformat(),
                "created": created,
            }
        )

    def delete(self, request):
        from anime.models import UserActiveTab

        anime_id = request.query_params.get("anime_id")
        if not anime_id:
            return Response(
                {"error": "Требуется anime_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND
            )

        deleted, _ = UserActiveTab.objects.filter(
            user=request.user, anime=anime
        ).delete()

        return Response(
            {
                "deleted": deleted > 0,
                "anime_id": anime_id,
            }
        )


class HomeAPIView(APIView):
    """Общий endpoint для home страницы с базовыми рекомендациями"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        continue_watching = self._get_continue_watching(user) if user else []
        rewatch = self._get_rewatch(user) if user else []
        recommendations = self._get_recommendations(user)
        trending = self._get_trending(user)
        
        # Финальная фильтрация: убираем аниме без русских букв в названии
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        
        def has_cyrillic(text):
            return bool(CYRILLIC_RE.search(text or ''))
        
        def filter_items(items):
            return [item for item in items if has_cyrillic(item.get("title", ""))]
        
        return Response(
            {
                "continue_watching": filter_items(continue_watching),
                "rewatch": filter_items(rewatch),
                "recommendations": filter_items(recommendations),
                "trending": filter_items(trending),
            }
        )

    # Методы для personalized_recommendations
    def personalized_recommendations(self, request):
        """
        Расширенные персонализированные рекомендации для страницы 'Для вас'
        
        Возвращает 9 категорий рекомендаций согласно требованиям:
        1. based_on_watched - на основе ПРОСМОТРЕННОГО (started/completed) пользователем, если ничего не смотрел - 20 популярных рандомно
        2. similar_style - аниме НЕ из коллекции пользователя, похожие между собой по жанрам, рандомно, жанр меняется при перезаходе
        3. top_rated_in_genres - ТОП в жанрах пользователя (с наивысшим рейтингом), рандомно
        4. new_in_genres - ОНГОИНГИ в жанрах пользователя, рандомно
        5. classics - рейтинг > 8, год <= 2010, рандомно
        6. top_anime - ЗА ПОСЛЕДНИЙ ГОД, с наивысшим рейтингом, рандомно
        7. new_releases - в жанрах которые пользователь смотрел РЕЖЕ ВСЕГО, рейтинг > 8, за последние 2 года, рандомно
        8. short - до 13 серий, рейтинг > 8, НЕ онгоинги
        9. movies - type=movie или ova, рейтинг > 8.5
        """
        from django.utils import timezone
        from datetime import timedelta
        import random
        
        user = request.user if request.user.is_authenticated else None
        
        # Получаем данные пользователя
        user_genres, user_genre_counts, watched_ids = self._get_user_genre_preferences_detailed(user)
        
        # Определяем редкие жанры (для раздела 7)
        rare_genres = self._get_rare_genres(user_genre_counts)
        
        # Для "похожий стиль" выбираем случайный жанр при каждом запросе
        random_genre = random.choice(user_genres) if user_genres else None
        
        return Response({
            "based_on_watched": self._get_based_on_watched(user, watched_ids, 20),
            "similar_style": self._get_similar_style(user, watched_ids, 20, random_genre),
            "top_rated_in_genres": self._get_top_rated_in_genres_new(user_genres, watched_ids, 20),
            "new_in_genres": self._get_new_in_genres_ongoing(user_genres, watched_ids, 20),
            "classics": self._get_classics_high_rated(20),
            "top_anime": self._get_top_anime_last_year(20),
            "new_releases": self._get_new_in_rare_genres(rare_genres, watched_ids, 20),
            "short": self._get_short_anime(20),
            "movies": self._get_movies_high_rated(20),
            "user_genres": user_genres,
            "has_personalization": user is not None and len(watched_ids) > 0,
        })

    # Прокси-методы к PersonalizedRecommendationsView (избегаем дублирования кода)
    def _get_continue_watching(self, user):
        return PersonalizedRecommendationsView()._get_continue_watching(user)

    def _get_rewatch(self, user):
        return PersonalizedRecommendationsView()._get_rewatch(user)

    def _get_recommendations(self, user):
        return PersonalizedRecommendationsView()._get_recommendations(user)

    def _get_trending(self, user=None):
        return PersonalizedRecommendationsView()._get_trending(user)


class PersonalizedRecommendationsView(APIView):
    """
    GET /anime/home/personalized/
    
    Возвращает 9 категорий рекомендаций для страницы 'Для вас'
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Расширенные персонализированные рекомендации для страницы 'Для вас'
        
        Возвращает 9 категорий рекомендаций согласно требованиям:
        1. based_on_watched - на основе ПРОСМОТРЕННОГО (started/completed) пользователем
        2. similar_style - похожий стиль, жанр меняется при перезаходе
        3. top_rated_in_genres - ТОП в жанрах пользователя
        4. new_in_genres - ОНГОИНГИ в жанрах пользователя
        5. classics - рейтинг > 8, год <= 2010
        6. top_anime - ЗА ПОСЛЕДНИЙ ГОД
        7. new_releases - в редких жанрах пользователя
        8. short - до 13 серий, рейтинг > 8
        9. movies - type=movie или ova, рейтинг > 8.5
        """
        from django.utils import timezone
        from datetime import timedelta
        import random
        user = request.user if request.user.is_authenticated else None

        # Финальная фильтрация: убираем аниме без русских букв в названии
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        
        def has_cyrillic(text):
            return bool(CYRILLIC_RE.search(text or ''))
        
        for key in ["based_on_watched", "similar_style", "top_rated_in_genres", 
                    "new_in_genres", "classics", "top_anime", "new_releases", 
                    "short", "movies"]:
            if key in result:
                result[key] = [
                    item for item in result[key]
                    if has_cyrillic(item.get("title", ""))
                ]
        
        user = request.user if request.user.is_authenticated else None
        
        # Получаем данные пользователя
        user_genres, user_genre_counts, watched_ids = self._get_user_genre_preferences_detailed(user)
        
        # Определяем редкие жанры (для раздела 7)
        rare_genres = self._get_rare_genres(user_genre_counts)
        
        # Для "похожий стиль" выбираем случайный жанр при каждом запросе
        random_genre = random.choice(user_genres) if user_genres else None
        
        # Получаем сырые данные
        result = {
            "based_on_watched": self._get_based_on_watched(user, watched_ids, 20),
            "similar_style": self._get_similar_style(user, watched_ids, 20, random_genre),
            "top_rated_in_genres": self._get_top_rated_in_genres_new(user_genres, watched_ids, 20),
            "new_in_genres": self._get_new_in_genres_ongoing(user_genres, watched_ids, 20),
            "classics": self._get_classics_high_rated(20),
            "top_anime": self._get_top_anime_last_year(20),
            "new_releases": self._get_new_in_rare_genres(rare_genres, watched_ids, 20),
            "short": self._get_short_anime(20),
            "movies": self._get_movies_high_rated(20),
            "user_genres": user_genres,
            "has_personalization": user is not None and len(watched_ids) > 0,
        }
        
        # Финальная фильтрация: убираем аниме без русских букв в названии
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        
        def has_cyrillic(text):
            return bool(CYRILLIC_RE.search(text or ''))
        
        for key in ["based_on_watched", "similar_style", "top_rated_in_genres", 
                    "new_in_genres", "classics", "top_anime", "new_releases", 
                    "short", "movies"]:
            if key in result:
                result[key] = [
                    item for item in result[key]
                    if has_cyrillic(item.get("title", ""))
                ]
        
        return Response(result)

    def _get_user_genre_preferences_detailed(self, user):
        """Получает детальные жанровые предпочтения пользователя"""
        from users.models import UserLibrary
        from collections import Counter
        
        if not user:
            return [], {}, set()
        
        library_items = UserLibrary.objects.filter(
            user=user,
            status__in=("started", "completed")
        ).select_related("anime").only("anime_id", "anime__genres")
        
        watched_ids = set()
        genre_counter = Counter()
        
        for item in library_items:
            watched_ids.add(item.anime_id)
            anime_genres = item.anime.genres or []
            for genre in anime_genres:
                genre_counter[genre] += 1
        
        top_genres = [g for g, _ in genre_counter.most_common(15)]
        return top_genres, dict(genre_counter), watched_ids
    
    def _get_rare_genres(self, genre_counts: dict):
        """Получает редкие жанры"""
        if not genre_counts:
            return []
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1])
        rare_genres = [g for g, _ in sorted_genres[:5]]
        return rare_genres

    def _dedupe_franchises(self, animes):
        """Дедуплицирует список аниме по франшизам, пропуская аниме без русских букв в названии"""
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        seen_franchises = set()
        result = []

        for anime in animes:
            # Проверка: у аниме должно быть русское название
            title = anime.title_ru or ""
            if not CYRILLIC_RE.search(title):
                continue
            
            data = self._anime_to_dict(anime)
            if data is None:
                continue
                
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    result.append(data)
            else:
                result.append(data)

        return result

    @staticmethod
    def _anime_to_dict(anime):
        """Преобразует аниме в словарь. Возвращает None если нет русских букв в названии."""
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')
        
        # Проверка: у аниме должно быть русское название
        title = anime.title_ru or ""
        if not CYRILLIC_RE.search(title):
            return None
        
        poster_url = anime.poster.url if anime.poster else anime.poster_url

        if anime.franchise:
            franchise = anime.franchise
            return {
                "anime_id": anime.id,
                "title": anime.title_ru or anime.title_en or "",
                "title_en": anime.title_en or "",
                "poster": poster_url,
                "genres": anime.genres or [],
                "rating": anime.score,
                "rating_count": 0,
                "year": anime.year,
                "status": anime.status,
                "is_franchise": True,
                "franchise_id": franchise.id,
                "franchise_name": franchise.name,
                "franchise_parts_count": franchise.entries.count(),
                "franchise_year_start": franchise.year_start,
                "franchise_year_end": franchise.year_end,
                "franchise_score": franchise.score,
            }

        return {
            "anime_id": anime.id,
            "title": anime.title_ru or anime.title_en or "",
            "title_en": anime.title_en or "",
            "poster": poster_url,
            "genres": anime.genres or [],
            "rating": anime.score,
            "rating_count": 0,
            "year": anime.year,
            "status": anime.status,
            "is_franchise": False,
        }

    def _get_based_on_watched(self, user, exclude_ids, limit=20):
        """Раздел 1: На основе ПРОСМОТРЕННОГО пользователем"""
        from anime.models import Anime
        import random
        
        if not exclude_ids or len(exclude_ids) == 0:
            candidates = list(
                Anime.objects.filter(
                    score__gte=7.0,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .select_related("franchise")
                .order_by("-score")[:100]
            )
            random.shuffle(candidates)
            result = self._dedupe_franchises(candidates)
            return result[:limit]

        user_genres, _, _ = self._get_user_genre_preferences_detailed(user)
        
        if not user_genres:
            candidates = list(
                Anime.objects.filter(
                    score__gte=7.0,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .exclude(id__in=exclude_ids)
                .select_related("franchise")
                .order_by("-score")[:100]
            )
            random.shuffle(candidates)
            result = self._dedupe_franchises(candidates)
            return result[:limit]

        genre_q = Q()
        for genre in user_genres[:10]:
            genre_q |= Q(genres__icontains=genre)
        
        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=6.5,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .exclude(id__in=exclude_ids)
            .select_related("franchise")
            .order_by("-score")[:150]
        )

        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_similar_style(self, user, exclude_ids, limit=20, random_genre=None):
        """Раздел 2: Похожий стиль"""
        from anime.models import Anime
        import random
        
        if not random_genre:
            user_genres, _, _ = self._get_user_genre_preferences_detailed(user)
            if user_genres:
                random_genre = random.choice(user_genres)
        
        if random_genre:
            candidates = list(
                Anime.objects.filter(
                    genres__icontains=random_genre,
                    score__gte=6.5,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .exclude(id__in=exclude_ids)
                .select_related("franchise")
                .order_by("-score")[:100]
            )
        else:
            candidates = list(
                Anime.objects.filter(
                    score__gte=7.0,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .exclude(id__in=exclude_ids)
                .select_related("franchise")
                .order_by("-score")[:100]
            )

        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_top_rated_in_genres_new(self, genres, exclude_ids, limit=20):
        """Раздел 3: Лучшее в жанрах"""
        from anime.models import Anime
        import random
        
        if not genres:
            candidates = list(
                Anime.objects.filter(
                    score__gte=8.0,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .select_related("franchise")
                .order_by("-score")[:100]
            )
            random.shuffle(candidates)
            result = self._dedupe_franchises(candidates)
            return result[:limit]

        genre_q = Q()
        for genre in genres[:10]:
            genre_q |= Q(genres__icontains=genre)
        
        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=7.5,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .exclude(id__in=exclude_ids)
            .select_related("franchise")
            .order_by("-score")[:100]
        )

        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_new_in_genres_ongoing(self, genres, exclude_ids, limit=20):
        """Раздел 4: Новинки в жанрах"""
        from anime.models import Anime
        import random
        
        if not genres:
            candidates = list(
                Anime.objects.filter(
                    status="ongoing",
                    score__gte=6.5,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .select_related("franchise")
                .order_by("-score")[:100]
            )
            random.shuffle(candidates)
            result = self._dedupe_franchises(candidates)
            return result[:limit]

        genre_q = Q()
        for genre in genres[:10]:
            genre_q |= Q(genres__icontains=genre)
        
        candidates = list(
            Anime.objects.filter(
                genre_q,
                status="ongoing",
                score__gte=6.5,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .exclude(id__in=exclude_ids)
            .select_related("franchise")
            .order_by("-score")[:100]
        )

        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_classics_high_rated(self, limit=20):
        """Раздел 5: Классик"""
        from anime.models import Anime
        import random
        
        candidates = list(
            Anime.objects.filter(
                score__gt=8.0,
                year__lte=2010,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("franchise")
            .order_by("-score")[:100]
        )

        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_top_anime_last_year(self, limit=20):
        """Раздел 6: Топ аниме за последний год"""
        from anime.models import Anime
        from django.utils import timezone
        import random
        
        current_year = timezone.now().year
        min_year = current_year - 1
        
        candidates = list(
            Anime.objects.filter(
                year__gte=min_year,
                score__gte=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("franchise")
            .order_by("-score")[:100]
        )
        
        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_new_in_rare_genres(self, rare_genres, exclude_ids, limit=20):
        """Раздел 7: Новинки в редких жанрах"""
        from anime.models import Anime
        from django.utils import timezone
        import random
        
        current_year = timezone.now().year
        min_year = current_year - 2
        
        if not rare_genres:
            candidates = list(
                Anime.objects.filter(
                    year__gte=min_year,
                    score__gt=8.0,
                    title_ru__regex=r"[а-яёА-ЯЁ]"
                )
                .select_related("franchise")
                .order_by("-score")[:100]
            )
            random.shuffle(candidates)
            result = self._dedupe_franchises(candidates)
            return result[:limit]
        
        genre_q = Q()
        for genre in rare_genres:
            genre_q |= Q(genres__icontains=genre)
        
        candidates = list(
            Anime.objects.filter(
                genre_q,
                year__gte=min_year,
                score__gt=8.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .exclude(id__in=exclude_ids)
            .select_related("franchise")
            .order_by("-score")[:100]
        )
        
        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_short_anime(self, limit=20):
        """Раздел 8: Короткие"""
        from anime.models import Anime
        import random
        
        candidates = list(
            Anime.objects.filter(
                episodes__lte=13,
                score__gt=8.0,
                status__in=["finished", "canceled"],
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("franchise")
            .order_by("-score")[:100]
        )
        
        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_movies_high_rated(self, limit=20):
        """Раздел 9: Полнометражные"""
        from anime.models import Anime
        import random
        
        candidates = list(
            Anime.objects.filter(
                kind__in=["movie", "ova"],
                score__gt=8.5,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("franchise")
            .order_by("-score")[:100]
        )
        
        random.shuffle(candidates)
        result = self._dedupe_franchises(candidates)
        return result[:limit]

    def _get_continue_watching(self, user):
        from users.models import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="started", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:15]
        )
        result = []
        for item in library_items:
            anime = item.anime
            # Двойная проверка: название должно содержать русские буквы
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            total_episodes = anime.episodes or 1
            progress_percent = (
                min(100, int((item.current_episode / total_episodes) * 100))
                if total_episodes
                else 0
            )
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "current_episode": item.current_episode,
                    "total_episodes": anime.episodes,
                    "progress_percent": progress_percent,
                    "status": anime.status,
                    "last_watched": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                }
            )
        return result

    def _get_rewatch(self, user):
        from users.models import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="completed", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:10]
        )
        result = []
        for item in library_items:
            anime = item.anime
            # Двойная проверка: название должно содержать русские буквы
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "completed_date": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                    "user_rating": item.rating,
                }
            )
        return result

    def _get_recommendations(self, user):
        """
        Персонализированные рекомендации - строго из БД, без фоллбэков
        """
        from anime.models import Anime
        from collections import Counter

        if not user or not user.is_authenticated:
            return []

        from users.models import UserLibrary
        from studios.models import StudioSubscription

        watched_ids = set(
            UserLibrary.objects.filter(
                user=user, status__in=("started", "completed", "on_hold", "planned")
            ).values_list("anime_id", flat=True)
        )

        watched_anime = Anime.objects.filter(
            id__in=UserLibrary.objects.filter(
                user=user, status__in=("started", "completed")
            ).values_list("anime_id", flat=True),
            title_ru__regex=r"[а-яёА-ЯЁ]",
        )
        genre_counter = Counter()
        for anime in watched_anime:
            for g in anime.genres or []:
                genre_counter[g] += 1

        if not genre_counter:
            return []

        subscribed_studios = list(
            StudioSubscription.objects.filter(user=user)
            .select_related("studio")
            .values_list("studio__name", flat=True)
        )
        if subscribed_studios:
            for studio_obj in StudioSubscription.objects.filter(
                user=user
            ).select_related("studio"):
                for g, cnt in (studio_obj.studio.genre_stats or {}).items():
                    genre_counter[g] += max(1, cnt // 10)

        top_genres = [g for g, _ in genre_counter.most_common(10)]

        if top_genres:
            genre_q = Q()
            for g in top_genres:
                genre_q |= Q(genres__icontains=g)
            qs = Anime.objects.filter(
                genre_q, score__gte=6.5, title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise")
        else:
            return []

        studio_bonus_ids = set()
        if subscribed_studios:
            sq = Q()
            for s in subscribed_studios:
                sq |= Q(studios__icontains=s)
            studio_bonus_ids = set(
                Anime.objects.filter(sq, title_ru__regex=r"[а-яёА-ЯЁ]").values_list("id", flat=True)
            )

        candidates = list(qs.exclude(id__in=watched_ids).order_by("-score")[:60])

        def sort_key(anime):
            base = anime.score or 0
            bonus = 2.0 if anime.id in studio_bonus_ids else 0
            overlap = sum(1 for g in (anime.genres or []) if g in genre_counter)
            return base + bonus + overlap * 0.3

        candidates.sort(key=sort_key, reverse=True)
        return self._dedupe_franchises(candidates)[:20]

    def _dedupe_franchises(self, animes):
        """Дедуплицирует список аниме по франшизам, оставляя только одну карточку на франшизу"""
        seen_franchises = set()
        result = []

        for anime in animes:
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    result.append(self._anime_to_dict(anime))
            else:
                result.append(self._anime_to_dict(anime))

        return result

    def _get_trending(self, user=None):
        """
        Популярное на этой неделе:
          - Определяем по количеству записей UserEpisodeProgress за последние 7 дней
          - Исключаем аниме которое текущий пользователь уже смотрит или смотрел
          - Группируем по франшизам
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
                    user=user, status__in=("started", "completed", "on_hold", "dropped")
                ).values_list("anime_id", flat=True)
            )

        # Топ аниме по активности UserEpisodeProgress
        trending_qs = (
            UserEpisodeProgress.objects.filter(last_watched__gte=week_ago)
            .values("anime_id")
            .annotate(views=Count("user", distinct=True))
            .order_by("-views")[:60]
        )
        trending_ids = [row["anime_id"] for row in trending_qs]

        # Загружаем аниме в порядке идентификаторов
        anime_map = {
            a.id: a
            for a in Anime.objects.filter(
                id__in=trending_ids, title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise")
        }

        candidates = []
        for row in trending_qs:
            aid = row["anime_id"]
            if aid in excluded_ids:
                continue
            anime = anime_map.get(aid)
            if not anime:
                continue
            candidates.append((anime, row["views"]))

        # Дедуплицируем по франшизам
        seen_franchises = set()
        result = []
        for anime, views in candidates:
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    d = self._anime_to_dict(anime)
                    d["views_this_week"] = views
                    result.append(d)
            else:
                d = self._anime_to_dict(anime)
                d["views_this_week"] = views
                result.append(d)

            if len(result) >= 20:
                break

        return result

    @staticmethod
    def _anime_to_dict(anime):
        """Преобразует аниме в словарь, добавляя данные о франшизе если есть"""
        poster_url = anime.poster.url if anime.poster else anime.poster_url

        # Если аниме входит во франшизу, возвращаем данные франшизы
        if anime.franchise:
            franchise = anime.franchise
            return {
                "anime_id": anime.id,
                "title": anime.title_ru or anime.title_en or "",
                "title_en": anime.title_en or "",
                "poster": poster_url,
                "genres": anime.genres or [],
                "rating": anime.score,
                "rating_count": 0,
                "year": anime.year,
                "status": anime.status,
                # Данные франшизы
                "is_franchise": True,
                "franchise_id": franchise.id,
                "franchise_name": franchise.name,
                "franchise_parts_count": franchise.entries.count(),
                "franchise_year_start": franchise.year_start,
                "franchise_year_end": franchise.year_end,
                "franchise_score": franchise.score,
            }

        return {
            "anime_id": anime.id,
            "title": anime.title_ru or anime.title_en or "",
            "title_en": anime.title_en or "",
            "poster": poster_url,
            "genres": anime.genres or [],
            "rating": anime.score,
            "rating_count": 0,
            "year": anime.year,
            "status": anime.status,
            "is_franchise": False,
        }

    def _get_user_genre_preferences_detailed(self, user):
        """
        Получает детальные жанровые предпочтения пользователя на основе библиотеки
        
        Returns:
            tuple: (top_genres: List[str], genre_counts: dict, watched_ids: Set[int])
        """
        from users.models import UserLibrary
        from collections import Counter
        
        if not user:
            return [], {}, set()
        
        # Получаем все аниме которые пользователь смотрел (started + completed)
        library_items = UserLibrary.objects.filter(
            user=user,
            status__in=("started", "completed")
        ).select_related("anime").only("anime_id", "anime__genres")
        
        watched_ids = set()
        genre_counter = Counter()
        
        for item in library_items:
            watched_ids.add(item.anime_id)
            anime_genres = item.anime.genres or []
            for genre in anime_genres:
                genre_counter[genre] += 1
        
        # Топ 15 жанров
        top_genres = [g for g, _ in genre_counter.most_common(15)]
        
        return top_genres, dict(genre_counter), watched_ids
    
    def _get_rare_genres(self, genre_counts: dict):
        """Получает редкие жанры (которые пользователь смотрел меньше всего)"""
        if not genre_counts:
            return []
        
        # Сортируем по количеству и берем последние 5 (самые редкие)
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1])
        rare_genres = [g for g, _ in sorted_genres[:5]]
        return rare_genres

    # ── Вспомогательные методы для персонализации ─────────────────

    def _get_user_watched_profiles(self, user):
        """Возвращает жанровые профили просмотренных аниме: список (anime_id, set(genres), kind, studios)"""
        from users.models import UserLibrary
        from anime.models import Anime

        if not user:
            return []

        watched = UserLibrary.objects.filter(
            user=user, status__in=("started", "completed")
        ).select_related("anime").only("anime__id", "anime__genres", "anime__kind", "anime__studios")

        profiles = []
        for item in watched:
            a = item.anime
            profiles.append({
                "id": a.id,
                "genres": set(a.genres or []),
                "kind": a.kind,
                "studios": set(a.studios or []),
            })
        return profiles

    @staticmethod
    def _genre_similarity_score(genres_a, genres_b):
        """Jaccard similarity между двумя наборами жанров"""
        if not genres_a or not genres_b:
            return 0.0
        intersection = len(genres_a & genres_b)
        union = len(genres_a | genres_b)
        return intersection / union if union else 0.0

    def _pick_diverse_by_genre(self, candidates, genres_pool, limit, exclude_ids):
        """Равномерно распределяет аниме по жанрам из genres_pool"""
        import random
        from collections import defaultdict
        
        if not genres_pool:
            random.shuffle(candidates)
            return self._dedupe_franchises(candidates)[:limit]

        # Группируем кандидатов по жанрам
        genre_buckets = defaultdict(list)
        for anime in candidates:
            if anime.id in exclude_ids:
                continue
            ag = set(anime.genres or [])
            for g in genres_pool:
                if g in ag:
                    genre_buckets[g].append(anime)

        # Берём по round-robin из каждого жанра
        result = []
        seen_ids = set()
        pointers = {g: 0 for g in genres_pool}
        sorted_genres = sorted(genres_pool, key=lambda g: len(genre_buckets.get(g, [])), reverse=True)

        while len(result) < limit:
            added_any = False
            for g in sorted_genres:
                bucket = genre_buckets.get(g, [])
                while pointers[g] < len(bucket):
                    anime = bucket[pointers[g]]
                    pointers[g] += 1
                    if anime.id not in seen_ids:
                        seen_ids.add(anime.id)
                        result.append(anime)
                        added_any = True
                        break
                if len(result) >= limit:
                    break
            if not added_any:
                break

        # Добиваем случайными оставшимися
        if len(result) < limit:
            remaining = [a for a in candidates if a.id not in seen_ids and a.id not in exclude_ids]
            random.shuffle(remaining)
            result.extend(remaining[:limit - len(result)])

        return self._dedupe_franchises(result)[:limit]

    def _get_rare_genres_from_db(self, exclude_ids, min_year):
        """Находит реально редкие жанры из БД (с наименьшим количеством аниме за последние 2 года)"""
        from anime.models import Anime
        from collections import Counter

        # Берём аниме за последние 2 года
        recent = Anime.objects.filter(
            year__gte=min_year,
            score__gte=6.0,
            title_ru__regex=r"[а-яёА-ЯЁ]"
        ).exclude(id__in=exclude_ids).only("genres")

        genre_counter = Counter()
        for anime in recent:
            for g in anime.genres or []:
                genre_counter[g] += 1

        if not genre_counter:
            return []
        # Самые редкие жанры (но не совсем уникальные - минимум 3 аниме)
        rare = [g for g, c in genre_counter.most_common() if 3 <= c <= 15]
        if not rare:
            rare = [g for g, c in genre_counter.most_common()[-20:]]
        return rare[:8]

    # ── Основные методы разделов ──────────────────────────────────

    def _get_based_on_watched(self, user, exclude_ids, limit=20):
        """
        Раздел 1: На основе ПРОСМОТРЕННОГО
        - Ищем аниме с максимальным жанровым пересечением с просмотренными
        - Исключаем всё просмотренное
        - Перемешиваем результат
        """
        from anime.models import Anime
        import random

        if not exclude_ids:
            return []

        profiles = self._get_user_watched_profiles(user)
        if not profiles:
            return []

        # Собираем "средний" жанровый профиль пользователя
        all_watched_genres = set()
        for p in profiles:
            all_watched_genres |= p["genres"]

        # Берём кандидатов из похожих жанров
        genre_q = Q()
        for g in list(all_watched_genres)[:15]:
            genre_q |= Q(genres__icontains=g)

        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:250]
        )

        # Сортируем по схожести жанров (Jaccard)
        scored = []
        for anime in candidates:
            ag = set(anime.genres or [])
            # Максимальная схожесть с любым просмотренным
            max_sim = max(
                (self._genre_similarity_score(ag, p["genres"]) for p in profiles),
                default=0
            )
            # Бонус за совпадение типа (TV/TV)
            type_bonus = 0.05 if any(p["kind"] == anime.kind for p in profiles) else 0
            scored.append((anime, max_sim + type_bonus + (anime.score or 0) * 0.01))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scored[:limit * 3]]
        random.shuffle(top)
        return self._dedupe_franchises(top)[:limit]

    def _get_similar_style(self, user, exclude_ids, limit=20, random_genre=None):
        """
        Раздел 2: Похожий стиль
        - Берём жанровый профиль случайного просмотренного аниме
        - Ищем аниме с похожим КОМБИНИРОВАННЫМ набором жанров
        - Перемешиваем
        """
        from anime.models import Anime
        import random

        profiles = self._get_user_watched_profiles(user)
        if not profiles:
            return []

        # Выбираем случайное просмотренное аниме как "эталон стиля"
        base_profile = random.choice(profiles)
        base_genres = base_profile["genres"]
        base_kind = base_profile["kind"]

        if not base_genres:
            return []

        # Ищем аниме, у которых есть ХОТЯ БЫ 2 жанра из базового набора
        genre_q = Q()
        for g in base_genres:
            genre_q |= Q(genres__icontains=g)

        candidates = list(
            Anime.objects.filter(
                genre_q,
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:200]
        )

        # Сортируем по схожести с базовым профилем
        scored = []
        for anime in candidates:
            ag = set(anime.genres or [])
            sim = self._genre_similarity_score(ag, base_genres)
            # Бонус за тот же тип
            if base_kind and anime.kind == base_kind:
                sim += 0.1
            scored.append((anime, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [s[0] for s in scored[:limit * 3]]
        random.shuffle(top)
        return self._dedupe_franchises(top)[:limit]

    def _get_top_rated_in_genres_new(self, genres, exclude_ids, limit=20):
        """
        Раздел 3: Лучшее в жанрах
        - Равномерно распределяем по жанрам пользователя
        - Берём лучшее в каждом жанре
        - Перемешиваем итог
        """
        from anime.models import Anime
        import random

        if not genres:
            return []

        # Для каждого жанра берём топ-10, затем объединяем
        all_picks = []
        seen = set()
        for genre in genres[:6]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                score__gte=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:10]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_new_in_genres_ongoing(self, genres, exclude_ids, limit=20):
        """
        Раздел 4: Новинки в жанрах
        - Онгоинги в жанрах пользователя
        - Равномерное распределение по жанрам
        - Перемешиваем
        """
        from anime.models import Anime
        import random

        if not genres:
            return []

        # Round-robin по жанрам
        all_picks = []
        seen = set()
        for genre in genres[:6]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                status="ongoing",
                score__gte=6.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:8]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_classics_high_rated(self, limit=20):
        """
        Раздел 5: Классика
        - Рейтинг > 7.0, год <= 2010, только завершённые
        - Перемешиваем для разнообразия
        """
        from anime.models import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                score__gt=7.0,
                year__lte=2010,
                status="finished",
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_top_anime_last_year(self, limit=20):
        """
        Раздел 6: Топ аниме
        - За последний год, с наивысшим рейтингом
        - БЕЗ перемешивания - чёткий топ
        """
        from anime.models import Anime
        from django.utils import timezone

        current_year = timezone.now().year
        min_year = current_year - 1

        candidates = list(
            Anime.objects.filter(
                year__gte=min_year,
                score__gte=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:40]
        )

        return self._dedupe_franchises(candidates)[:limit]

    def _get_new_in_rare_genres(self, rare_genres, exclude_ids, limit=20):
        """
        Раздел 7: Новинки (редкие жанры)
        - Реально редкие жанры из БД
        - За последние 2 года, рейтинг > 7.0
        - Перемешиваем
        """
        from anime.models import Anime
        from django.utils import timezone
        import random

        current_year = timezone.now().year
        min_year = current_year - 2

        # Если редкие жанры не переданы - берём из БД
        if not rare_genres:
            rare_genres = self._get_rare_genres_from_db(exclude_ids, min_year)

        if not rare_genres:
            return []

        # Round-robin по редким жанрам
        all_picks = []
        seen = set()
        for genre in rare_genres[:8]:
            qs = Anime.objects.filter(
                genres__icontains=genre,
                year__gte=min_year,
                score__gt=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).exclude(id__in=exclude_ids).select_related("franchise").order_by("-score")[:6]
            for anime in qs:
                if anime.id not in seen:
                    seen.add(anime.id)
                    all_picks.append(anime)

        random.shuffle(all_picks)
        return self._dedupe_franchises(all_picks)[:limit]

    def _get_short_anime(self, limit=20):
        """
        Раздел 8: Короткие
        - До 13 серий, рейтинг > 7.0, ТОЛЬКО завершённые
        - Перемешиваем
        """
        from anime.models import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                episodes__lte=13,
                episodes__isnull=False,
                score__gt=7.0,
                status="finished",
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_movies_high_rated(self, limit=20):
        """
        Раздел 9: Полнометражные
        - Фильмы и OVA, рейтинг > 7.0
        - Перемешиваем
        """
        from anime.models import Anime
        import random

        candidates = list(
            Anime.objects.filter(
                kind__in=["movie", "ova"],
                score__gt=7.0,
                title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise").order_by("-score")[:150]
        )

        random.shuffle(candidates)
        return self._dedupe_franchises(candidates)[:limit]

    def _get_continue_watching(self, user):
        from users.models import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="started", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:15]
        )
        result = []
        for item in library_items:
            anime = item.anime
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            total_episodes = anime.episodes or 1
            progress_percent = (
                min(100, int((item.current_episode / total_episodes) * 100))
                if total_episodes
                else 0
            )
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "current_episode": item.current_episode,
                    "total_episodes": anime.episodes,
                    "progress_percent": progress_percent,
                    "status": anime.status,
                    "last_watched": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                }
            )
        return result

    def _get_rewatch(self, user):
        from users.models import UserLibrary
        import re
        CYRILLIC_RE = re.compile(r'[а-яёА-ЯЁ]')

        library_items = (
            UserLibrary.objects.filter(
                user=user, status="completed", anime__title_ru__regex=r"[а-яёА-ЯЁ]"
            )
            .select_related("anime")
            .order_by("-updated_at")[:10]
        )
        result = []
        for item in library_items:
            anime = item.anime
            if not CYRILLIC_RE.search(anime.title_ru or ""):
                continue
            poster_url = anime.poster.url if anime.poster else anime.poster_url
            result.append(
                {
                    "anime_id": anime.id,
                    "title": anime.title_ru or anime.title_en or "",
                    "title_en": anime.title_en or "",
                    "poster": poster_url,
                    "completed_date": item.updated_at.isoformat()
                    if item.updated_at
                    else None,
                    "user_rating": item.rating,
                }
            )
        return result

    def _get_recommendations(self, user):
        from anime.models import Anime
        from collections import Counter

        if not user or not user.is_authenticated:
            animes = list(
                Anime.objects.filter(score__gte=7.0, title_ru__regex=r"[а-яёА-ЯЁ]")
                .select_related("franchise")
                .order_by("-score")[:60]
            )
            return self._dedupe_franchises(animes)[:20]

        from users.models import UserLibrary
        from studios.models import StudioSubscription

        watched_ids = set(
            UserLibrary.objects.filter(
                user=user, status__in=("started", "completed", "on_hold", "planned")
            ).values_list("anime_id", flat=True)
        )

        watched_anime = Anime.objects.filter(
            id__in=UserLibrary.objects.filter(
                user=user, status__in=("started", "completed")
            ).values_list("anime_id", flat=True),
            title_ru__regex=r"[а-яёА-ЯЁ]",
        )
        genre_counter = Counter()
        for anime in watched_anime:
            for g in anime.genres or []:
                genre_counter[g] += 1

        subscribed_studios = list(
            StudioSubscription.objects.filter(user=user)
            .select_related("studio")
            .values_list("studio__name", flat=True)
        )
        if subscribed_studios:
            for studio_obj in StudioSubscription.objects.filter(
                user=user
            ).select_related("studio"):
                for g, cnt in (studio_obj.studio.genre_stats or {}).items():
                    genre_counter[g] += max(1, cnt // 10)

        top_genres = [g for g, _ in genre_counter.most_common(10)]

        if top_genres:
            genre_q = Q()
            for g in top_genres:
                genre_q |= Q(genres__icontains=g)
            qs = Anime.objects.filter(
                genre_q, score__gte=6.5, title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise")
        else:
            qs = Anime.objects.filter(
                score__gte=7.5, title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise")

        studio_bonus_ids = set()
        if subscribed_studios:
            sq = Q()
            for s in subscribed_studios:
                sq |= Q(studios__icontains=s)
            studio_bonus_ids = set(
                Anime.objects.filter(sq, title_ru__regex=r"[а-яёА-ЯЁ]").values_list("id", flat=True)
            )

        candidates = list(qs.exclude(id__in=watched_ids).order_by("-score")[:60])

        def sort_key(anime):
            base = anime.score or 0
            bonus = 2.0 if anime.id in studio_bonus_ids else 0
            overlap = sum(1 for g in (anime.genres or []) if g in genre_counter)
            return base + bonus + overlap * 0.3

        candidates.sort(key=sort_key, reverse=True)
        return self._dedupe_franchises(candidates)[:20]

    def _get_trending(self, user=None):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from users.models import UserLibrary
        from anime.models import Anime

        week_ago = timezone.now() - timedelta(days=7)

        excluded_ids: set = set()
        if user and user.is_authenticated:
            excluded_ids = set(
                UserLibrary.objects.filter(
                    user=user, status__in=("started", "completed", "on_hold", "dropped")
                ).values_list("anime_id", flat=True)
            )

        trending_qs = (
            UserEpisodeProgress.objects.filter(last_watched__gte=week_ago)
            .values("anime_id")
            .annotate(views=Count("user", distinct=True))
            .order_by("-views")[:60]
        )
        trending_ids = [row["anime_id"] for row in trending_qs]

        anime_map = {
            a.id: a
            for a in Anime.objects.filter(
                id__in=trending_ids, title_ru__regex=r"[а-яёА-ЯЁ]"
            ).select_related("franchise")
        }

        candidates = []
        for row in trending_qs:
            aid = row["anime_id"]
            if aid in excluded_ids:
                continue
            anime = anime_map.get(aid)
            if not anime:
                continue
            candidates.append((anime, row["views"]))

        seen_franchises = set()
        result = []
        for anime, views in candidates:
            if anime.franchise:
                fid = anime.franchise_id
                if fid not in seen_franchises:
                    seen_franchises.add(fid)
                    d = self._anime_to_dict(anime)
                    d["views_this_week"] = views
                    result.append(d)
            else:
                d = self._anime_to_dict(anime)
                d["views_this_week"] = views
                result.append(d)

            if len(result) >= 20:
                break

        if len(result) < 10:
            existing_ids = {r["anime_id"] for r in result}
            existing_franchises = {
                r.get("franchise_id") for r in result if r.get("franchise_id")
            }
            fallback = list(
                Anime.objects.filter(score__isnull=False, title_ru__regex=r"[а-яёА-ЯЁ]")
                .exclude(id__in=excluded_ids | existing_ids)
                .select_related("franchise")
                .order_by("-score")[:60]
            )

            for anime in fallback:
                if anime.franchise:
                    fid = anime.franchise_id
                    if fid in existing_franchises:
                        continue
                    existing_franchises.add(fid)
                if anime.id in existing_ids:
                    continue
                existing_ids.add(anime.id)
                result.append(self._anime_to_dict(anime))
                if len(result) >= 20:
                    break

        return result


# ═══════════════════════════════════════════════════════════════
# EPISODE PROGRESS SYSTEM
# ═══════════════════════════════════════════════════════════════


class EpisodeProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, anime_id):
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        try:
            rows = list(
                UserEpisodeProgress.objects.filter(user=request.user, anime=anime)
            )
            data = []
            for r in rows:
                try:
                    pct = r.progress_percent
                except Exception:
                    pct = (
                        round(r.last_position / r.duration * 100)
                        if (r.duration and r.duration > 0)
                        else 0
                    )
                data.append(
                    {
                        "episode_number": r.episode_number,
                        "status": r.status,
                        "last_position": r.last_position,
                        "duration": r.duration,
                        "progress_percent": pct,
                        "is_manually_marked": r.is_manually_marked,
                        "watched_at": r.watched_at.isoformat()
                        if r.watched_at
                        else None,
                    }
                )
            watched_count = sum(1 for r in rows if r.status in ("watched", "skipped"))
            total = anime.episodes or 0
            return Response(
                {
                    "anime_id": anime_id,
                    "total": total,
                    "watched_count": watched_count,
                    "percent": round(watched_count / total * 100) if total else 0,
                    "episodes": data,
                }
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            # Возвращаем пустой прогресс вместо 500
            return Response(
                {
                    "anime_id": anime_id,
                    "total": anime.episodes or 0,
                    "watched_count": 0,
                    "percent": 0,
                    "episodes": [],
                    "warning": str(e),
                }
            )

    def post(self, request, anime_id):
        episode_number = request.data.get("episode_number")
        last_position = request.data.get("last_position", 0)
        duration = request.data.get("duration")
        action_type = request.data.get("action", "progress")
        if action_type == "bulk":
            return self._bulk_sync(request, anime_id)
        if action_type == "mark":
            return self._mark_watched(request, anime_id, episode_number, manual=True)
        if action_type == "skip":
            return self._skip_episode(request, anime_id, episode_number)
        if episode_number is None:
            return Response({"error": "Требуется episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        ep, _ = UserEpisodeProgress.objects.get_or_create(
            user=request.user,
            anime=anime,
            episode_number=episode_number,
            defaults={"status": "in_progress"},
        )
        if ep.status not in ("watched", "skipped"):
            ep.last_position = int(last_position)
            if duration:
                ep.duration = int(duration)
            if ep.duration and ep.duration > 0:
                pct = ep.last_position / ep.duration * 100
                if pct >= 85:
                    return self._mark_watched(
                        request, anime_id, episode_number, instance=ep
                    )
            ep.status = "in_progress"
            ep.save(update_fields=["last_position", "duration", "status"])
        return Response(
            {
                "episode_number": ep.episode_number,
                "status": ep.status,
                "last_position": ep.last_position,
                "progress_percent": ep.progress_percent,
            }
        )

    def _mark_watched(
        self, request, anime_id, episode_number, manual=False, instance=None
    ):
        from django.utils import timezone

        if episode_number is None:
            return Response({"error": "Требуется episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        if instance is None:
            instance, _ = UserEpisodeProgress.objects.get_or_create(
                user=request.user, anime=anime, episode_number=episode_number
            )
        instance.status = "watched"
        instance.is_manually_marked = manual
        instance.watched_at = timezone.now()
        if instance.duration and not instance.last_position:
            instance.last_position = instance.duration
        instance.save()
        self._sync_library(request.user, anime)
        return Response(
            {
                "episode_number": instance.episode_number,
                "status": "watched",
                "is_manually_marked": manual,
                "auto_marked": not manual,
            }
        )

    def _skip_episode(self, request, anime_id, episode_number):
        if episode_number is None:
            return Response({"error": "Требуется episode_number"}, status=400)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        ep, _ = UserEpisodeProgress.objects.get_or_create(
            user=request.user, anime=anime, episode_number=episode_number
        )
        ep.status = "skipped"
        ep.is_manually_marked = True
        ep.save(update_fields=["status", "is_manually_marked"])
        self._sync_library(request.user, anime)
        return Response({"episode_number": episode_number, "status": "skipped"})

    def _bulk_sync(self, request, anime_id):
        from django.utils import timezone

        watched_up_to = request.data.get("watched_up_to")
        reset = request.data.get("reset", False)
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)
        if reset:
            UserEpisodeProgress.objects.filter(user=request.user, anime=anime).delete()
            self._sync_library(request.user, anime)
            return Response({"reset": True, "watched_count": 0})
        if watched_up_to is None:
            return Response({"error": "Требуется watched_up_to"}, status=400)
        total = int(watched_up_to)
        now = timezone.now()
        marked = 0
        for ep_num in range(1, total + 1):
            UserEpisodeProgress.objects.update_or_create(
                user=request.user,
                anime=anime,
                episode_number=ep_num,
                defaults={
                    "status": "watched",
                    "is_manually_marked": True,
                    "watched_at": now,
                },
            )
            marked += 1
        self._sync_library(request.user, anime)
        return Response({"watched_count": marked, "watched_up_to": total})

    def _sync_library(self, user, anime):
        try:
            watched = UserEpisodeProgress.objects.filter(
                user=user, anime=anime, status__in=["watched", "skipped"]
            ).count()
            total = anime.episodes or 0
            lib, _ = UserLibrary.objects.get_or_create(
                user=user, anime=anime, defaults={"status": "started"}
            )
            if total and watched >= total:
                lib.status = "completed"
            elif watched > 0:
                lib.status = "started"
            lib.current_episode = (
                UserEpisodeProgress.objects.filter(
                    user=user, anime=anime, status__in=["watched", "skipped"]
                )
                .order_by("-episode_number")
                .values_list("episode_number", flat=True)
                .first()
                or 0
            )
            lib.save(update_fields=["status", "current_episode", "updated_at"])
        except Exception as e:
            logging.getLogger(__name__).warning("_sync_library error: %s", e)


class EpisodeProgressUndoView(APIView):
    """
    Отмена последней отметки о просмотре серии.

    POST /anime/<anime_id>/episode-progress/<episode_number>/undo/

    Возвращает предыдущую серию к которой нужно вернуться.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, anime_id, episode_number):
        from django.utils import timezone

        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        try:
            # Находим запись о просмотре этой серии
            progress = UserEpisodeProgress.objects.get(
                user=request.user, anime=anime, episode_number=episode_number
            )

            # Если серия была отмечена как просмотренная - сбрасываем
            if progress.status == "watched":
                progress.status = "not_started"
                progress.is_manually_marked = False
                progress.watched_at = None
                progress.last_position = 0
                progress.save(
                    update_fields=[
                        "status",
                        "is_manually_marked",
                        "watched_at",
                        "last_position",
                    ]
                )

                # Синхронизируем с библиотекой
                self._sync_library(request.user, anime)

                # Находим предыдущую просмотренную серию
                prev_watched = (
                    UserEpisodeProgress.objects.filter(
                        user=request.user,
                        anime=anime,
                        status__in=["watched", "skipped"],
                        episode_number__lt=episode_number,
                    )
                    .order_by("-episode_number")
                    .first()
                )

                return Response(
                    {
                        "success": True,
                        "episode_number": episode_number,
                        "previous_episode": prev_watched.episode_number
                        if prev_watched
                        else None,
                        "message": f"Отменён просмотр серии {episode_number}",
                    }
                )
            else:
                return Response(
                    {
                        "success": False,
                        "message": "Серия не была отмечена как просмотренная",
                    },
                    status=400,
                )

        except UserEpisodeProgress.DoesNotExist:
            return Response(
                {"success": False, "message": "Запись о просмотре не найдена"},
                status=404,
            )
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"EpisodeProgressUndo error: {e}")
            return Response({"error": str(e)}, status=500)

    def _sync_library(self, user, anime):
        """Синхронизирует прогресс с UserLibrary."""
        try:
            watched = UserEpisodeProgress.objects.filter(
                user=user, anime=anime, status__in=["watched", "skipped"]
            ).count()

            total = anime.episodes or 0
            lib, _ = UserLibrary.objects.get_or_create(
                user=user, anime=anime, defaults={"status": "started"}
            )

            if total and watched >= total:
                lib.status = "completed"
            elif watched > 0:
                lib.status = "started"
            else:
                lib.status = "planned"

            lib.current_episode = (
                UserEpisodeProgress.objects.filter(
                    user=user, anime=anime, status__in=["watched", "skipped"]
                )
                .order_by("-episode_number")
                .values_list("episode_number", flat=True)
                .first()
                or 0
            )

            lib.save(update_fields=["status", "current_episode", "updated_at"])

        except Exception as e:
            logging.getLogger(__name__).warning("_sync_library error: %s", e)


class AnimeThemesView(APIView):
    """
    GET /anime/<id>/themes/?episode=1&season=1&translation_id=610

    Получает тайминги опенинга/эндинга через официальный Kodik API:
      1. kodikapi.com/search с with_episodes=True → URL страницы плеера серии
      2. kodik.biz/api/video-links?skip_segments=true → поле segments.skip[]
         skip-сегменты: первый = опенинг (начало серии), последний = эндинг (конец серии)

    Возвращает:
      { opening: {start, stop, kind} | null, ending: {start, stop, kind} | null }
    
    Кэширование: тайминги кэшируются на 24 часа в Redis
    """

    permission_classes = [permissions.AllowAny]
    KODIK_API_TOKEN = KODIK_API_TOKEN
    KODIK_PRIVATE_KEY = ""
    KODIK_PUBLIC_KEY = KODIK_API_TOKEN

    def _get_cache_key(self, anime_id, episode, season, translation_id):
        """Генерирует ключ кэша для таймингов"""
        tid = translation_id or 'all'
        return f'anime_themes:{anime_id}:{season}:{episode}:{tid}'

    def _get_episode_url(self, anime, episode, season, translation_id):
        """Возвращает URL вида //kodik.info/seria/... для конкретной серии."""
        params = {
            "token": self.KODIK_API_TOKEN,
            "with_material_data": False,
            "with_episodes": True,
            "limit": 100,
        }
        if anime.shikimori_id:
            params["shikimori_id"] = anime.shikimori_id
        elif anime.kodik_id:
            params["id"] = anime.kodik_id
        else:
            return None
        if translation_id:
            params["translation_id"] = translation_id

        r = requests.get(f"{KODIK_API_BASE}/search", params=params, timeout=10)
        r.raise_for_status()
        season_key = str(season)
        ep_key = str(episode)
        for res in r.json().get("results", []):
            if translation_id:
                tid = (res.get("translation") or {}).get("id")
                if str(tid) != str(translation_id):
                    continue
            s_data = ((res.get("seasons") or {}).get(season_key)) or {}
            ep_data = s_data.get("episodes") or {}
            ep_url = ep_data.get(ep_key) or ep_data.get(
                int(ep_key) if ep_key.isdigit() else ep_key
            )
            if ep_url:
                return ep_url.strip()
        return None

    def _get_segments(self, episode_url, user_ip="1.1.1.1"):
        """
        Запрашивает kodik.biz/api/video-links?skip_segments=true.
        Возвращает (opening|None, ending|None).

        skip[] - список сегментов для пропуска (опенинг, эндинг, заставка).
        Определяем роль по позиции в серии:
          • сегмент заканчивается до середины серии → опенинг
          • сегмент начинается после середины серии → эндинг
        """
        import hmac, hashlib
        from datetime import datetime, timezone, timedelta

        link = episode_url.strip()
        if link.startswith("https:"):
            link = link[6:]
        elif link.startswith("http:"):
            link = link[5:]

        deadline = (datetime.now(timezone.utc) + timedelta(hours=6)).strftime(
            "%Y%m%d%H"
        )
        sign_str = f"{link}:{user_ip}:{deadline}"
        signature = hmac.new(
            self.KODIK_PRIVATE_KEY.encode(),
            sign_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        params = {
            "link": link,
            "p": self.KODIK_PUBLIC_KEY,
            "ip": user_ip,
            "d": deadline,
            "s": signature,
            "skip_segments": "true",
        }
        r = requests.get(
            f"{KODIK_VIDEO_BASE}/api/video-links", params=params, timeout=15
        )
        r.raise_for_status()
        data = r.json()

        segments = data.get("segments") or {}
        skip_list = segments.get("skip") or []

        if not skip_list:
            return None, None

        # Оцениваем общую длину серии по крайнему концу всех сегментов
        # (или берём максимальный end из skip+ad)
        all_segs = (segments.get("ad") or []) + skip_list
        max_end = max((s.get("end", 0) for s in all_segs), default=0)
        # Если данных мало - ориентируемся на 1200 с (20 мин) как типичная серия
        total_est = max(max_end * 1.1, 1200)
        midpoint = total_est / 2

        opening = None
        ending = None
        for seg in skip_list:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            if end <= midpoint and opening is None:
                opening = {"start": start, "stop": end, "kind": "opening"}
            elif start >= midpoint and ending is None:
                ending = {"start": start, "stop": end, "kind": "ending"}

        return opening, ending

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
            0
        ].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        try:
            episode_url = self._get_episode_url(anime, episode, season, translation_id)
            if not episode_url:
                return Response(
                    {
                        "opening": None,
                        "ending": None,
                        "error": "Серия не найдена в Kodik",
                    },
                    status=404,
                )

            opening, ending = self._get_segments(episode_url, user_ip=user_ip)

            return Response(
                {
                    "opening": opening,
                    "ending": ending,
                    "source": "kodik_video_links",
                }
            )

        except requests.RequestException as e:
            return Response(
                {
                    "opening": None,
                    "ending": None,
                    "error": f"Ошибка запроса к Kodik: {e}",
                },
                status=503,
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response(
                {"opening": None, "ending": None, "error": str(e)}, status=500
            )


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
    KODIK_API_TOKEN = KODIK_API_TOKEN

    def get(self, request, pk):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")

        try:
            # 1. Kodik API: ищем прямую ссылку на серию через with_episodes=True
            if anime.shikimori_id or anime.kodik_id:
                params = {
                    "token": self.KODIK_API_TOKEN,
                    "with_material_data": False,
                    "with_episodes": True,
                    "limit": 100,
                }
                if anime.shikimori_id:
                    params["shikimori_id"] = anime.shikimori_id
                else:
                    params["id"] = anime.kodik_id
                if translation_id:
                    params["translation_id"] = translation_id

                r = requests.get(f"{KODIK_API_BASE}/search", params=params, timeout=10)
                r.raise_for_status()
                results = r.json().get("results", [])

                for res in results:
                    seasons_data = res.get("seasons", {}) or {}
                    s_data = (
                        seasons_data.get(str(season)) or seasons_data.get(season) or {}
                    )
                    ep_data = s_data.get("episodes", {}) if s_data else {}
                    ep_url = ep_data.get(str(episode)) or ep_data.get(episode)
                    if ep_url:
                        if ep_url.startswith("//"):
                            ep_url = "https:" + ep_url
                        elif not ep_url.startswith("http"):
                            ep_url = "https://" + ep_url
                        return Response(
                            {
                                "m3u8_url": ep_url,
                                "episode": episode,
                                "season": season,
                                "source": "kodik_api",
                            }
                        )

            # 2. Fallback: парсим страницу плеера
            kodik_link = anime.kodik_link
            if not kodik_link:
                return Response(
                    {"error": "Нет kodik_link и не удалось найти через API"}, status=404
                )

            if kodik_link.startswith("//"):
                kodik_link = "https:" + kodik_link
            elif not kodik_link.startswith("http"):
                kodik_link = "https://" + kodik_link

            from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

            parsed = urlparse(kodik_link)
            qs = parse_qs(parsed.query)
            qs["season"] = [str(season)]
            qs["episode"] = [str(episode)]
            if translation_id:
                qs["only_translations"] = [str(translation_id)]
            player_url = urlunparse(
                parsed._replace(query=urlencode({k: v[0] for k, v in qs.items()}))
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://anisphere.org/",
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
                return Response(
                    {
                        "error": "Не удалось извлечь m3u8 из страницы плеера",
                        "player_url": player_url,
                    },
                    status=404,
                )

            if m3u8_url.startswith("//"):
                m3u8_url = "https:" + m3u8_url

            return Response(
                {
                    "m3u8_url": m3u8_url,
                    "player_url": player_url,
                    "episode": episode,
                    "season": season,
                    "source": "kodik_player_html",
                }
            )

        except requests.RequestException as e:
            return Response({"error": f"Ошибка запроса: {e}"}, status=503)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


class KodikClipDownloadView(APIView):
    """
    GET /anime/<pk>/clip/?episode=1&season=1&translation_id=610&start=60&end=150&label=clip

    Нарезает MP4-фрагмент серии через ffmpeg на сервере.

    Доступно ТОЛЬКО премиум пользователям.

    Алгоритм получения m3u8:
      1. Kodik API (kodikapi.com/search) → URL страницы плеера серии (//kodik.info/seria/...)
      2. kodik.biz/api/video-links с HMAC-подписью → JSON с прямыми ссылками на m3u8
      3. ffmpeg нарезает фрагмент из m3u8 и отдаёт готовый MP4
    """

    permission_classes = [permissions.IsAuthenticated]

    # Импортируем из kodik_config
    KODIK_API_TOKEN = KODIK_API_TOKEN
    KODIK_PRIVATE_KEY = KODIK_PRIVATE_KEY
    KODIK_PUBLIC_KEY = KODIK_API_TOKEN

    # ------------------------------------------------------------------ #
    #  Шаг 1: URL страницы плеера конкретной серии                        #
    # ------------------------------------------------------------------ #
    def _get_episode_player_url(self, anime, episode, season, translation_id):
        """
        Возвращает URL вида //kodik.info/seria/461359/hash/720p
        для конкретной серии через kodikapi.com/search с with_episodes=True.
        """
        season_key = str(season)
        ep_key = str(episode)

        try:
            params = {
                "token": self.KODIK_API_TOKEN,
                "with_material_data": False,
                "with_episodes": True,
                "limit": 100,
            }
            if anime.shikimori_id:
                params["shikimori_id"] = anime.shikimori_id
            elif anime.kodik_id:
                params["id"] = anime.kodik_id
            else:
                return None

            if translation_id:
                params["translation_id"] = translation_id

            resp = requests.get(f"{KODIK_API_BASE}/search", params=params, timeout=10)
            resp.raise_for_status()

            for res in resp.json().get("results", []):
                # Если translation_id указан - берём только нужный
                if translation_id:
                    tid = (res.get("translation") or {}).get("id")
                    if str(tid) != str(translation_id):
                        continue

                s_data = ((res.get("seasons") or {}).get(season_key)) or {}
                ep_data = s_data.get("episodes") or {}
                ep_url = ep_data.get(ep_key) or ep_data.get(
                    int(ep_key) if ep_key.isdigit() else ep_key
                )

                if ep_url:
                    # Kodik возвращает //kodik.info/seria/... - оставляем как есть,
                    # потому что video-links API принимает именно //... формат
                    return ep_url.strip()

        except Exception as e:
            import logging

            logging.getLogger(__name__).warning("_get_episode_player_url error: %s", e)

        return None

    # ------------------------------------------------------------------ #
    #  Шаг 2: прямой m3u8 через kodik.biz/api/video-links                 #
    # ------------------------------------------------------------------ #
    def _get_m3u8_via_api(self, episode_url, user_ip="1.1.1.1"):
        """
        Запрашивает kodik.biz/api/video-links и возвращает прямой m3u8 URL.

        Подпись: HMAC-SHA256(private_key, "{link}:{ip}:{deadline}")
        Deadline: текущее UTC + 6 часов, формат YYYYMMDDHH
        """
        import hmac, hashlib
        from datetime import datetime, timezone, timedelta

        # Нормализуем ссылку: убираем https: если есть, оставляем //...
        link = episode_url.strip()
        if link.startswith("https:"):
            link = link[6:]
        elif link.startswith("http:"):
            link = link[5:]
        # Теперь link вида //kodik.info/seria/...

        # Deadline: UTC now + 6 часов, формат YYYYMMDDHH
        deadline_dt = datetime.now(timezone.utc) + timedelta(hours=6)
        deadline = deadline_dt.strftime("%Y%m%d%H")

        # HMAC-SHA256 подпись
        sign_string = f"{link}:{user_ip}:{deadline}"
        signature = hmac.new(
            self.KODIK_PRIVATE_KEY.encode("utf-8"),
            sign_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        params = {
            "link": link,
            "p": self.KODIK_PUBLIC_KEY,
            "ip": user_ip,
            "d": deadline,
            "s": signature,
        }

        try:
            resp = requests.get(
                f"{KODIK_VIDEO_BASE}/api/video-links", params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            # Формат ответа Kodik: {"links": {"720": {"Src": "https://...", "Type": "..."}, ...}}
            # Внимание: ключи с заглавной буквы (Src, Type), значение - dict, не list
            links = data.get("links") or {}
            for quality in ["720", "1080", "480", "360", "240"]:
                ql = links.get(quality)
                if not ql:
                    continue
                # Может быть dict {"Src": "..."} или list [{"src": "..."}]
                items = ql if isinstance(ql, list) else [ql]
                for item in items:
                    # Пробуем оба варианта регистра
                    src = (
                        item.get("Src")
                        or item.get("src")
                        or item.get("File")
                        or item.get("file")
                        or ""
                    )
                    if src:
                        if src.startswith("//"):
                            src = "https:" + src
                        return src

        except Exception as e:
            import logging

            logging.getLogger(__name__).warning("_get_m3u8_via_api error: %s", e)

        return None

    # ------------------------------------------------------------------ #
    #  Основной handler                                                    #
    # ------------------------------------------------------------------ #
    def get(self, request, pk):
        """
        Нарезает клип из аниме.
        """
        # Проверка премиум статуса
        is_premium = False
        if hasattr(request.user, 'profile_settings'):
            is_premium = request.user.profile_settings.is_premium
        
        if not is_premium:
            print(f"[CLIP] Non-premium user {request.user.id if request.user.is_authenticated else 'anon'}")
            return Response(
                {"error": "Доступно только премиум пользователям"}, status=403
            )

        print(f"[CLIP] Premium user {request.user.id}, anime={pk}")

        try:
            anime = Anime.objects.get(pk=pk)
            print(f"[CLIP] Anime found: {anime.title_ru}, shikimori_id={anime.shikimori_id}, kodik_id={anime.kodik_id}")
        except Anime.DoesNotExist:
            print(f"[CLIP] Anime {pk} NOT FOUND")
            return Response({"error": "Аниме не найдено"}, status=404)

        episode = int(request.query_params.get("episode", 1))
        season = int(request.query_params.get("season", 1))
        translation_id = request.query_params.get("translation_id")
        start_sec = int(request.query_params.get("start", 0))
        end_sec = int(request.query_params.get("end", 120))
        label = request.query_params.get("label", "clip")
        format_type = request.query_params.get("format", "video")  # video или audio
        user_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
            0
        ].strip() or request.META.get("REMOTE_ADDR", "1.1.1.1")

        # 1. Получаем URL страницы плеера серии
        episode_url = self._get_episode_player_url(
            anime, episode, season, translation_id
        )
        if not episode_url:
            return Response({"error": "Не удалось найти серию в Kodik"}, status=404)

        # 2. Получаем прямой m3u8 через video-links API
        m3u8_url = self._get_m3u8_via_api(episode_url, user_ip=user_ip)
        if not m3u8_url:
            return Response({"error": "Не удалось получить m3u8"}, status=404)

        # 3. Нарезаем клип через ffmpeg
        import subprocess
        import tempfile
        import os
        from django.http import HttpResponse
        import logging

        logger = logging.getLogger(__name__)
        duration = end_sec - start_sec
        if duration <= 0:
            return Response({"error": "end должен быть больше start"}, status=400)

        logger.info(f"Нарезка клипа: anime={pk}, episode={episode}, start={start_sec}s, end={end_sec}s, duration={duration}s")
        logger.info(f"M3U8 URL: {m3u8_url[:100]}...")

        # Создаём временный файл
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Проверяем что ffmpeg существует
            if not os.path.exists("/usr/bin/ffmpeg"):
                logger.error("ffmpeg не найден по пути /usr/bin/ffmpeg")
                return Response({"error": "Сервис ffmpeg недоступен"}, status=503)

            if format_type == "audio":
                # Только аудио (MP3)
                cmd = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-ss", str(start_sec),
                    "-i", m3u8_url,
                    "-t", str(duration),
                    "-vn",  # Без видео
                    "-acodec", "libmp3lame",
                    "-b:a", "192k",
                    "-f", "mp3",
                    "pipe:1",
                ]
                content_type = "audio/mpeg"
                extension = "mp3"
            else:
                # Видео (MP4) - твой существующий код
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp_path = tmp.name
                
                cmd = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-ss", str(start_sec),
                    "-i", m3u8_url,
                    "-t", str(duration),
                    "-c", "copy",
                    "-movflags", "+faststart",
                    tmp_path
                ]
                content_type = "video/mp4"
                extension = "mp4"
            
            logger.info(f"FFmpeg команда: {' '.join(cmd)}")
            
            # Запускаем с таймаутом
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if process.returncode != 0:
                logger.error(f"FFmpeg stderr: {process.stderr}")
                return Response(
                    {"error": f"Ошибка ffmpeg: {process.stderr[:200]}"},
                    status=500
                )
            
            # Читаем файл и отдаём
            with open(tmp_path, 'rb') as f:
                output = f.read()
            
            response = HttpResponse(output, content_type=content_type)
            from django.utils.encoding import escape_uri_path
            filename = f"{label.replace(' ', '_')}_{pk}_{episode}.{extension}"
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{escape_uri_path(filename)}"
            response["Content-Length"] = len(output)
            return response

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout после 120 секунд")
            return Response({"error": "Нарезка видео заняла слишком много времени"}, status=504)
        except Exception as e:
            logger.exception(f"Clip download error: {e}")
            return Response({"error": f"Внутренняя ошибка сервера: {str(e)}"}, status=500)
        finally:
            # Удаляем временный файл в любом случае
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class AdminTodayAddedAnimeView(APIView):
    """
    Админка: аниме добавленные сегодня.

    GET /anime/admin/today-added/

    Возвращает список аниме которые были добавлены в базу сегодня.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from datetime import datetime

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        animes = Anime.objects.filter(created_at__gte=today_start, title_ru__regex=r"[а-яёА-ЯЁ]").order_by(
            "-created_at"
        )

        data = []
        for anime in animes[:100]:  # Максимум 100
            data.append(
                {
                    "id": anime.id,
                    "title_ru": anime.title_ru or anime.title_en or "",
                    "shikimori_id": anime.shikimori_id,
                    "mal_id": anime.mal_id,
                    "year": anime.year,
                    "status": anime.status,
                    "kind": anime.kind,
                    "episodes": anime.episodes,
                    "score": anime.score,
                    "poster_url": anime.poster_url,
                    "created_at": anime.created_at.isoformat(),
                    "data_source": anime.data_source,
                }
            )

        return Response(
            {
                "count": len(data),
                "today_start": today_start.isoformat(),
                "results": data,
            }
        )


class AnimeEpisodeNotificationView(APIView):
    """Подписка/отписка на уведомления о новых сериях аниме"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """Переключить подписку"""
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        subscription, created = AnimeEpisodeNotification.objects.get_or_create(
            user=request.user, anime=anime
        )

        if not created:
            # Если подписка уже есть, удалить (отписка)
            subscription.delete()
            return Response({"subscribed": False})

        return Response({"subscribed": True})

    def get(self, request, pk):
        """Проверить статус подписки"""
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=404)

        subscribed = AnimeEpisodeNotification.objects.filter(
            user=request.user, anime=anime
        ).exists()

        return Response({"subscribed": subscribed})
