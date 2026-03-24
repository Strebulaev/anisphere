from rest_framework import serializers
from .models import Anime, Franchise, Genre, Studio

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']

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
            if f.poster and hasattr(f.poster, 'url'):
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
            entries = obj.franchise.entries.all().order_by('franchise_order')
            posters = []
            for entry in entries:
                if entry.poster and hasattr(entry.poster, 'url'):
                    posters.append(entry.poster.url)
                elif entry.poster_url:
                    posters.append(entry.poster_url)
            return posters
        except Exception:
            return []
    
    def get_genres(self, obj):
        """Получение жанров из JSON поля"""
        genres_data = getattr(obj, 'genres', []) or []
        # Если жанры - это массив строк, преобразуем в формат {id, name}
        if isinstance(genres_data, list):
            return [
                {
                    'id': idx,
                    'name': genre,
                    'slug': genre.lower().replace(' ', '-')
                }
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data
    
    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        studios_data = getattr(obj, 'studios', []) or []
        # Если студии - это массив строк, преобразуем в формат {id, name}
        if isinstance(studios_data, list):
            return [
                {
                    'id': idx,
                    'name': studio,
                    'slug': studio.lower().replace(' ', '-')
                }
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data
    
    def get_poster_image_url(self, obj):
        """Получение URL изображения постера"""
        # Сначала проверяем локальное изображение
        if obj.poster:
            return obj.poster.url
        # Затем используем внешний URL
        return obj.poster_url or ''
    
    class Meta:
        model = Anime
        fields = [
            'id', 'title_ru', 'title_en', 'title_jp',
            'description', 'year', 'status', 'kind', 'episodes',
            'score', 'poster_url', 'poster', 'poster_image_url', 'genres', 'studios',
            'movies', 'ovas', 'movie_count', 'ova_count', 'total_items',
            'created_at', 'updated_at', 'shikimori_id', 'data_source',
            'franchise_id', 'is_franchise', 'franchise_order',
            'franchise_name', 'franchise_poster_image_url',
            'franchise_parts_count', 'franchise_year_start', 'franchise_year_end',
            'franchise_avg_score', 'franchise_all_genres', 'franchise_all_posters',
        ]
        read_only_fields = ['created_at', 'updated_at']


class StudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ['id', 'name', 'slug']

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
    kodik_link = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
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
        genres_data = getattr(obj, 'genres', []) or []
        # Если жанры - это массив строк, преобразуем в формат {id, name}
        if isinstance(genres_data, list):
            return [
                {
                    'id': idx,
                    'name': genre,
                    'slug': genre.lower().replace(' ', '-')
                }
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data
    
    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        studios_data = getattr(obj, 'studios', []) or []
        # Если студии - это массив строк, преобразуем в формат {id, name}
        if isinstance(studios_data, list):
            return [
                {
                    'id': idx,
                    'name': studio,
                    'slug': studio.lower().replace(' ', '-')
                }
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        """Получение URL изображения постера"""
        # Сначала проверяем локальное изображение
        if obj.poster:
            return obj.poster.url
        # Затем используем внешний URL
        return obj.poster_url or ''

    def get_seasons_count(self, obj):
        """Получение количества сезонов"""
        seasons_data = getattr(obj, 'seasons', {}) or {}
        return len(seasons_data) if seasons_data else 1
    
    def get_translations(self, obj):
        """Получение переводов"""
        # Если у аниме есть переводы из Kodik, возвращаем их
        translations_data = getattr(obj, 'translations', []) or []
        return translations_data

    def get_screenshots(self, obj):
        """Получение скриншотов в формате {url: string}"""
        screenshots = getattr(obj, 'screenshots', []) or []
        if not screenshots:
            return []
        
        # Если скриншоты - массив строк, преобразуем в массив объектов
        if isinstance(screenshots, list) and screenshots:
            first = screenshots[0]
            if isinstance(first, str):
                return [{'url': url} for url in screenshots]
        
        # Если уже массив объектов, возвращаем как есть
        return screenshots

    class Meta:
        model = Anime
        fields = [
            'id', 'title_ru', 'title_en', 'title_jp',
            'description', 'year', 'status', 'kind', 'episodes',
            'score', 'poster_url', 'poster', 'poster_image_url', 'genres', 'studios',
            'movies', 'ovas', 'movie_count', 'ova_count', 'total_items',
            'created_at', 'updated_at', 'data_source', 'shikimori_id',
            # Kodik поля
            'kodik_link', 'kodik_id', 'quality', 'screenshots',
            'seasons', 'last_season', 'last_episode', 'seasons_count',
            'translations',
            'franchise_id', 'is_franchise', 'franchise_order',
        ]
        read_only_fields = ['created_at', 'updated_at']


class FranchiseEntrySerializer(serializers.ModelSerializer):
    """Mini-сериалайзер элемента франшизы"""
    poster_image_url = serializers.SerializerMethodField()
    anime_slug = serializers.SerializerMethodField()

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, 'url'):
            return obj.poster.url
        return obj.poster_url or ''

    def get_anime_slug(self, obj):
        """Генерирует slug из названия аниме для URL"""
        if not obj.title_ru:
            return ''
        # Транслитерация: заменяем русские буквы на латинские
        slug = obj.title_ru.lower()
        replacements = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
            'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        # Заменяем не буквы и не цифры на дефисы
        import re
        slug = re.sub(r'[^a-z0-9]', '-', slug)
        # Удаляем повторяющиеся дефисы
        slug = re.sub(r'-+', '-', slug)
        # Удаляем дефисы в начале и конце
        slug = slug.strip('-')
        return slug

    class Meta:
        model = Anime
        fields = [
            'id', 'title_ru', 'title_en', 'title_jp',
            'kind', 'episodes', 'year', 'score', 'status',
            'poster_url', 'poster_image_url', 'anime_slug',
            'franchise_order', 'kodik_link',
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
        if obj.poster and hasattr(obj.poster, 'url'):
            return obj.poster.url
        return obj.poster_url or ''

    def get_parts_count(self, obj):
        """Количество частей во франшизе"""
        return obj.entries.count()

    def get_year_range(self, obj):
        """Период выхода (строка)"""
        entries = obj.entries.all()
        years = [e.year for e in entries if e.year]
        if not years:
            return "—"
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
        entries = obj.entries.all().order_by('franchise_order')
        posters = []
        for entry in entries:
            if entry.poster and hasattr(entry.poster, 'url'):
                posters.append(entry.poster.url)
            elif entry.poster_url:
                posters.append(entry.poster_url)
        return posters

    class Meta:
        model = Franchise
        fields = [
            'id', 'name', 'slug', 'description',
            'poster_url', 'poster_image_url',
            'score', 'year_start', 'year_end',
            'parts_count', 'year_range', 'avg_score', 'all_genres', 'all_posters',
            'created_at', 'updated_at',
        ]


class FranchiseDetailSerializer(serializers.ModelSerializer):
    """Детальная страница франшизы со всеми энтриями"""
    poster_image_url = serializers.SerializerMethodField()
    entries = FranchiseEntrySerializer(many=True, read_only=True)
    parts_count = serializers.SerializerMethodField()
    year_range = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()
    all_genres = serializers.SerializerMethodField()
    all_posters = serializers.SerializerMethodField()

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, 'url'):
            return obj.poster.url
        return obj.poster_url or ''

    def get_parts_count(self, obj):
        return obj.entries.count()

    def get_year_range(self, obj):
        entries = obj.entries.all()
        years = [e.year for e in entries if e.year]
        if not years:
            return "—"
        year_start = min(years)
        year_end = max(years)
        if year_start == year_end:
            return str(year_start)
        return f"{year_start} – {year_end}"

    def get_avg_score(self, obj):
        if obj.score:
            return round(obj.score, 1)
        entries = obj.entries.all()
        scores = [e.score for e in entries if e.score]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    def get_all_genres(self, obj):
        if obj.genres:
            return obj.genres
        entries = obj.entries.all()
        genres = set()
        for entry in entries:
            if entry.genres:
                genres.update(entry.genres)
        return list(genres)

    def get_all_posters(self, obj):
        entries = obj.entries.all().order_by('franchise_order')
        posters = []
        for entry in entries:
            if entry.poster and hasattr(entry.poster, 'url'):
                posters.append(entry.poster.url)
            elif entry.poster_url:
                posters.append(entry.poster_url)
        return posters

    class Meta:
        model = Franchise
        fields = [
            'id', 'name', 'slug', 'description',
            'poster_url', 'poster_image_url',
            'score', 'year_start', 'year_end',
            'entries', 'parts_count', 'year_range', 'avg_score', 'all_genres', 'all_posters',
            'created_at', 'updated_at',
        ]