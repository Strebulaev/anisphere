from rest_framework import serializers
from .models import Anime, Genre, Studio

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']

class AnimeSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    
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
            'created_at', 'updated_at', 'shikimori_id', 'data_source'
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
    
    # Дополнительные поля для Kodik
    kodik_link = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    kodik_id = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    quality = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    screenshots = serializers.JSONField(read_only=True, allow_null=True)
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
            'translations'
        ]
        read_only_fields = ['created_at', 'updated_at']