from rest_framework import serializers
from .models import (
    Anime,
    Franchise,
    Genre,
    Studio,
    Playlist,
    PlaylistItem,
    VoiceActor,
    DubStudio,
    Dub,
    DubRole,
    UserDubRating,
    VideoSource,
    Episode,
    Translation,
    WatchProgress,
    VideoQuality,
    AnimeUpdate,
    UserEpisodeProgress,
    UserActiveTab,
    CustomDub,
    ClipTask,
    AnimeSchedule,
    AnimeAnnouncement,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "slug"]


class AnimeSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    franchise_id = serializers.SerializerMethodField()
    is_franchise = serializers.SerializerMethodField()
    franchise_name = serializers.SerializerMethodField()
    franchise_poster_image_url = serializers.SerializerMethodField()
    franchise_parts_count = serializers.SerializerMethodField()
    franchise_year_start = serializers.SerializerMethodField()
    franchise_year_end = serializers.SerializerMethodField()
    franchise_avg_score = serializers.SerializerMethodField()
    franchise_all_genres = serializers.SerializerMethodField()
    franchise_all_posters = serializers.SerializerMethodField()

    def get_franchise_id(self, obj):
        try:
            return obj.franchise_id
        except Exception:
            return None

    def get_is_franchise(self, obj):
        try:
            return obj.franchise_id is not None
        except Exception:
            return False

    def get_franchise_name(self, obj):
        try:
            if not obj.franchise_id:
                return None
            return obj.franchise.name if obj.franchise else None
        except Exception:
            return None

    def get_franchise_poster_image_url(self, obj):
        try:
            if not obj.franchise_id:
                return None
            f = obj.franchise
            if not f:
                return None
            if f.poster and hasattr(f.poster, "url"):
                return f.poster.url
            return f.poster_url or None
        except Exception:
            return None

    def get_franchise_parts_count(self, obj):
        """Количество частей во франшизе"""
        try:
            if not obj.franchise_id:
                return None
            # Используем кэшированное значение или считаем
            if obj.franchise.parts_count:
                return obj.franchise.parts_count
            return obj.franchise.entries.count()
        except Exception:
            return None

    def get_franchise_year_start(self, obj):
        """Год начала франшизы"""
        try:
            if not obj.franchise_id:
                return None
            return obj.franchise.year_start
        except Exception:
            return None

    def get_franchise_year_end(self, obj):
        """Год конца франшизы"""
        try:
            if not obj.franchise_id:
                return None
            return obj.franchise.year_end
        except Exception:
            return None

    def get_franchise_avg_score(self, obj):
        """Средняя оценка франшизы"""
        try:
            if not obj.franchise_id:
                return None
            if obj.franchise.score:
                return round(obj.franchise.score, 1)
            # Вычисляем если нет кэша
            entries = obj.franchise.entries.all()
            scores = [e.score for e in entries if e.score]
            if not scores:
                return None
            return round(sum(scores) / len(scores), 1)
        except Exception:
            return None

    def get_franchise_all_genres(self, obj):
        """Все жанры франшизы"""
        try:
            if not obj.franchise_id:
                return []
            if obj.franchise.genres:
                return obj.franchise.genres
            # Вычисляем если нет кэша
            entries = obj.franchise.entries.all()
            genres = set()
            for entry in entries:
                if entry.genres:
                    genres.update(entry.genres)
            return list(genres)
        except Exception:
            return []

    def get_franchise_all_posters(self, obj):
        """Все постеры франшизы"""
        try:
            if not obj.franchise_id:
                return []
            entries = obj.franchise.entries.all().order_by("franchise_order")
            posters = []
            for entry in entries:
                if entry.poster and hasattr(entry.poster, "url"):
                    posters.append(entry.poster.url)
                elif entry.poster_url:
                    posters.append(entry.poster_url)
            return posters
        except Exception:
            return []

    def get_genres(self, obj):
        """Получение жанров из JSON поля"""
        genres_data = getattr(obj, "genres", []) or []
        # Если жанры - это массив строк, преобразуем в формат {id, name}
        if isinstance(genres_data, list):
            return [
                {"id": idx, "name": genre, "slug": genre.lower().replace(" ", "-")}
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data

    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        studios_data = getattr(obj, "studios", []) or []
        # Если студии - это массив строк, преобразуем в формат {id, name}
        if isinstance(studios_data, list):
            return [
                {"id": idx, "name": studio, "slug": studio.lower().replace(" ", "-")}
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        """Получение URL изображения постера - ПРИОРИТЕТ ЛОКАЛЬНОГО POSTER"""
        # Сначала проверяем локальное изображение (WebP)
        if obj.poster and hasattr(obj.poster, 'url'):
            return obj.poster.url
        # Затем используем внешний URL
        return obj.poster_url or ""

    class Meta:
        model = Anime
        fields = [
            "id",
            "slug",
            "title_ru",
            "title_en",
            "title_jp",
            "description",
            "year",
            "release_date",
            "release_date_string",
            "status",
            "kind",
            "episodes",
            "score",
            "poster_url",
            "poster",
            "poster_image_url",  # ← ФРОНТЕНД ДОЛЖЕН ИСПОЛЬЗОВАТЬ ЭТО
            "genres",
            "studios",
            "movies",
            "ovas",
            "movie_count",
            "ova_count",
            "total_items",
            "created_at",
            "updated_at",
            "shikimori_id",
            "data_source",
            "franchise_id",
            "is_franchise",
            "franchise_order",
            "franchise_name",
            "franchise_poster_image_url",
            "franchise_parts_count",
            "franchise_year_start",
            "franchise_year_end",
            "franchise_avg_score",
            "franchise_all_genres",
            "franchise_all_posters",
            "download_links",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ["id", "name", "slug"]


class AnimeDetailSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    franchise_id = serializers.SerializerMethodField()
    is_franchise = serializers.SerializerMethodField()

    def get_franchise_id(self, obj):
        try:
            return obj.franchise_id
        except Exception:
            return None

    def get_is_franchise(self, obj):
        try:
            return obj.franchise_id is not None
        except Exception:
            return False

    # Дополнительные поля для Kodik
    kodik_link = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True
    )
    kodik_id = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    quality = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    screenshots = serializers.SerializerMethodField()
    seasons = serializers.JSONField(read_only=True, allow_null=True)
    last_season = serializers.IntegerField(read_only=True, allow_null=True)
    last_episode = serializers.IntegerField(read_only=True, allow_null=True)
    seasons_count = serializers.SerializerMethodField()
    translations = serializers.JSONField(read_only=True, allow_null=True)

    def get_genres(self, obj):
        """Получение жанров из JSON поля"""
        genres_data = getattr(obj, "genres", []) or []
        # Если жанры - это массив строк, преобразуем в формат {id, name}
        if isinstance(genres_data, list):
            return [
                {"id": idx, "name": genre, "slug": genre.lower().replace(" ", "-")}
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data

    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        studios_data = getattr(obj, "studios", []) or []
        # Если студии - это массив строк, преобразуем в формат {id, name}
        if isinstance(studios_data, list):
            return [
                {"id": idx, "name": studio, "slug": studio.lower().replace(" ", "-")}
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        """Получение URL изображения постера"""
        # Сначала проверяем локальное изображение
        if obj.poster:
            return obj.poster.url
        # Затем используем внешний URL
        return obj.poster_url or ""

    def get_seasons_count(self, obj):
        """Получение количества сезонов"""
        seasons_data = getattr(obj, "seasons", {}) or {}
        return len(seasons_data) if seasons_data else 1

    def get_translations(self, obj):
        """Получение переводов"""
        # Если у аниме есть переводы из Kodik, возвращаем их
        translations_data = getattr(obj, "translations", []) or []
        return translations_data

    def get_screenshots(self, obj):
        """Получение скриншотов в формате {url: string}"""
        from .kodik_config import KODIK_SCREENSHOTS_BASE, KODIK_OLD_DOMAINS

        screenshots = getattr(obj, "screenshots", []) or []
        if not screenshots:
            return []

        def normalize_screenshot_url(url: str) -> str:
            """Нормализует URL скриншота - заменяет старые домены на KODIK_SCREENSHOTS_BASE"""
            if not url:
                return url
            # Если URL уже абсолютный с новым доменом - возвращаем как есть
            if KODIK_SCREENSHOTS_BASE in url:
                return url
            # Заменяем старые домены на KODIK_SCREENSHOTS_BASE
            for old_domain in KODIK_OLD_DOMAINS:
                if old_domain in url:
                    # Извлекаем путь после старого домена
                    path = url.split(old_domain)[-1]
                    return f"{KODIK_SCREENSHOTS_BASE}{path}"
            return url

        # Если скриншоты - массив строк, преобразуем в массив объектов
        if isinstance(screenshots, list) and screenshots:
            first = screenshots[0]
            if isinstance(first, str):
                return [{"url": normalize_screenshot_url(url)} for url in screenshots]
            elif isinstance(first, dict):
                # Если уже массив объектов - нормализуем URL в каждом
                return [
                    {"url": normalize_screenshot_url(s.get("url", ""))}
                    for s in screenshots
                ]
        return []
    
    class Meta:
        model = Anime
        fields = [
            "id",
            "slug",
            "title_ru",
            "title_en",
            "title_jp",
            "description",
            "year",
            "release_date",
            "release_date_string",
            "status",
            "kind",
            "episodes",
            "score",
            "poster_url",
            "poster",
            "poster_image_url",
            "genres",
            "studios",
            "movies",
            "ovas",
            "movie_count",
            "ova_count",
            "total_items",
            "created_at",
            "updated_at",
            "data_source",
            "shikimori_id",
            # Kodik поля
            "kodik_link",
            "kodik_id",
            "quality",
            "screenshots",
            "seasons",
            "last_season",
            "last_episode",
            "seasons_count",
            "translations",
            "franchise_id",
            "is_franchise",
            "franchise_order",
            "download_links",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    """Сериалайзер для анонсов аниме"""
    poster_image_url = serializers.SerializerMethodField()
    genres_display = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    slug = serializers.SlugField(read_only=True)
    slug_en = serializers.SerializerMethodField()
    
    def get_poster_image_url(self, obj):
        """Возвращает полный URL постера"""
        if not obj.poster_url:
            return "/placeholder-anime.jpg"
        # Если это относительный путь, добавляем домен
        if obj.poster_url.startswith("/media"):
            return f"https://anisphere.org{obj.poster_url}"
        return obj.poster_url
    
    def get_genres(self, obj):
        """Возвращает массив жанров"""
        if not obj.genres:
            return []
        if isinstance(obj.genres, list):
            return obj.genres
        return []
    
    def get_genres_display(self, obj):
        """Возвращает строку жанров"""
        genres = self.get_genres(obj)
        if not genres:
            return ""
        return ", ".join(genres)
    
    def get_slug_en(self, obj):
        """Генерирует slug из названия для URL (транслитерация)"""
        import re

        title = obj.title_en or obj.title_ru
        if not title:
            return obj.slug or ""
        
        # Транслитерация русских букв
        slug = title.lower()
        replacements = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
            "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
            "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        
        # Заменяем не буквы и не цифры на дефисы
        slug = re.sub(r"[^a-z0-9\s-]", "-", slug)
        # Удаляем повторяющиеся дефисы
        slug = re.sub(r"-+", "-", slug)
        # Удаляем дефисы в начале и конце
        slug = slug.strip("-")
        # Заменяем пробелы на дефисы
        slug = slug.replace(" ", "-")
        
        return slug

    class Meta:
        model = AnimeAnnouncement
        fields = [
            "id",
            "slug",
            "slug_en",
            "title_ru",
            "title_en",
            "release_date",
            "status",
            "description",
            "score",
            "rating",
            "type",
            "episodes",
            "studio",
            "genres",
            "genres_display",
            "poster_url",
            "poster_image_url",
            "next_episode_date",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class FranchiseEntrySerializer(serializers.ModelSerializer):
    """Mini-сериалайзер элемента франшизы"""

    poster_image_url = serializers.SerializerMethodField()
    anime_slug = serializers.SerializerMethodField()

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        return obj.poster_url or ""

    def get_anime_slug(self, obj):
        """Генерирует slug из названия аниме для URL"""
        if not obj.title_ru:
            return ""
        # Транслитерация: заменяем русские буквы на латинские
        slug = obj.title_ru.lower()
        replacements = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "yo",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        # Заменяем не буквы и не цифры на дефисы
        import re

        slug = re.sub(r"[^a-z0-9]", "-", slug)
        # Удаляем повторяющиеся дефисы
        slug = re.sub(r"-+", "-", slug)
        # Удаляем дефисы в начале и конце
        slug = slug.strip("-")
        return slug

    class Meta:
        model = Anime
        fields = [
            "id",
            "title_ru",
            "title_en",
            "title_jp",
            "kind",
            "episodes",
            "year",
            "score",
            "status",
            "poster_url",
            "poster_image_url",
            "anime_slug",
            "franchise_order",
            "kodik_link",
        ]


class FranchiseSerializer(serializers.ModelSerializer):
    """Список франшиз для каталога"""

    poster_image_url = serializers.SerializerMethodField()
    parts_count = serializers.SerializerMethodField()
    year_range = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()
    all_genres = serializers.SerializerMethodField()
    all_posters = serializers.SerializerMethodField()

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        if obj.poster_url:
            return obj.poster_url
        # Если нет постера франшизы, берём постер первого аниме
        first_entry = (
            obj.entries.filter(poster_url__isnull=False).exclude(poster_url="").first()
        )
        if first_entry:
            if first_entry.poster and hasattr(first_entry.poster, "url"):
                return first_entry.poster.url
            return first_entry.poster_url
        return ""

    def get_parts_count(self, obj):
        """Количество частей во франшизе"""
        return obj.entries.count()

    def get_year_range(self, obj):
        """Период выхода (строка)"""
        entries = obj.entries.all()
        years = [e.year for e in entries if e.year]
        if not years:
            return "-"
        year_start = min(years)
        year_end = max(years)
        if year_start == year_end:
            return str(year_start)
        return f"{year_start} – {year_end}"

    def get_avg_score(self, obj):
        """Средняя оценка по всем частям"""
        if obj.score:
            return round(obj.score, 1)
        entries = obj.entries.all()
        scores = [e.score for e in entries if e.score]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    def get_all_genres(self, obj):
        """Все жанры всех частей"""
        if obj.genres:
            return obj.genres
        entries = obj.entries.all()
        genres = set()
        for entry in entries:
            if entry.genres:
                genres.update(entry.genres)
        return list(genres)

    def get_all_posters(self, obj):
        """Список постеров всех частей для прокрутки"""
        entries = obj.entries.all().order_by("franchise_order")
        posters = []
        for entry in entries:
            if entry.poster and hasattr(entry.poster, "url"):
                posters.append(entry.poster.url)
            elif entry.poster_url:
                posters.append(entry.poster_url)
        return posters

    class Meta:
        model = Franchise
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "poster_url",
            "poster_image_url",
            "score",
            "year_start",
            "year_end",
            "entries",
            "parts_count",
            "year_range",
            "avg_score",
            "all_genres",
            "all_posters",
            "created_at",
            "updated_at",
        ]


class ClipTaskSerializer(serializers.ModelSerializer):
    """Сериалайзер для задач на вырезку видео/скриншотов"""
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    download_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_download_url(self, obj):
        return obj.download_url or ""
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            return obj.thumbnail.url
        return None

    class Meta:
        model = ClipTask
        fields = [
            'id',
            'task_type',
            'anime',
            'anime_title',
            'episode',
            'season',
            'start_time',
            'end_time',
            'timestamp',
            'label',
            'quality',
            'status',
            'result_file',
            'download_url',
            'thumbnail_url',
            'duration',
            'file_size',
            'error_message',
            'created_at',
            'started_at',
            'completed_at',
        ]
        read_only_fields = ['status', 'result_file', 'error_message', 'created_at', 'started_at', 'completed_at']


class ClipTaskCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер для создания задачи"""
    
    class Meta:
        model = ClipTask
        fields = [
            'anime',
            'episode',
            'season',
            'start_time',
            'end_time',
            'timestamp',
            'label',
            'quality',
            'task_type',
            'format',
        ]
    
    def validate(self, data):
        # Проверка для клипов
        if data.get('task_type') == 'clip':
            # Проверяем наличие start_time и end_time (0 - валидное значение)
            if 'start_time' not in data or 'end_time' not in data:
                raise serializers.ValidationError({
                    'start_time': 'Требуется для видео фрагмента',
                    'end_time': 'Требуется для видео фрагмента'
                })
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'Время конца должно быть больше времени начала'
                })
        
        # Проверка для скриншотов
        elif data.get('task_type') == 'screenshot':
            if 'timestamp' not in data:
                raise serializers.ValidationError({
                    'timestamp': 'Требуется для скриншота'
                })
            if data['timestamp'] < 0:
                raise serializers.ValidationError({
                    'timestamp': 'Время не может быть отрицательным'
                })
        
        return data


class AnimeScheduleSerializer(serializers.ModelSerializer):
    """Сериалайзер для анонсов из таблицы anime_schedule
    
    Возвращает данные в формате, совместимом с AnimeSerializer для фронтенда.
    """
    poster_image_url = serializers.SerializerMethodField()
    # Для совместимости с фронтендом
    title_en = serializers.CharField(source='title', read_only=True)
    title_jp = serializers.CharField(source='title', read_only=True)
    kind = serializers.CharField(default='tv', read_only=True)
    genres = serializers.ListField(default=list, read_only=True)
    studios = serializers.ListField(default=list, read_only=True)
    description = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()
    release_date_string = serializers.SerializerMethodField()
    # status всегда 'announced' для фронтенда
    status = serializers.SerializerMethodField()
    # id возвращаем как mal_id для совместимости переходов
    id = serializers.SerializerMethodField()
    shikimori_id = serializers.SerializerMethodField()

    def get_id(self, obj):
        # Приоритет: mal_id, иначе оригинальный id
        return obj.mal_id or obj.id

    def get_shikimori_id(self, obj):
        return obj.mal_id

    def get_status(self, obj):
        return 'announced'

    def get_description(self, obj):
        return ''

    def get_release_date(self, obj):
        return None

    def get_release_date_string(self, obj):
        return ''

    def get_poster_image_url(self, obj):
        return obj.poster_url or ""

    def get_anime_slug(self, obj):
        """Генерирует slug из названия для URL (транслитерация русского названия)"""
        import re
        
        title = obj.title_ru or obj.title
        if not title:
            return ""
        
        # Транслитерация: заменяем русские буквы на латинские
        slug = title.lower()
        replacements = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
            "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
            "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        
        # Заменяем не буквы и не цифры на дефисы
        slug = re.sub(r"[^a-z0-9]", "-", slug)
        # Удаляем повторяющиеся дефисы
        slug = re.sub(r"-+", "-", slug)
        # Удаляем дефисы в начале и конце
        slug = slug.strip("-")
        
        return slug

    class Meta:
        model = AnimeSchedule
        fields = [
            "id",
            "mal_id",
            "shikimori_id",
            "title_ru",
            "title",
            "title_en",
            "title_jp",
            "status",
            "airing",
            "broadcast_day",
            "episodes",
            "score",
            "year",
            "poster_url",
            "poster_image_url",
            "kind",
            "genres",
            "studios",
            "description",
            "release_date",
            "release_date_string",
            "created_at",
            "updated_at",
            "anime_slug",  # Добавлено поле
        ]
