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
        return getattr(obj, 'genres', []) or []
    
    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        return getattr(obj, 'studios', []) or []
    
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
    
    def get_genres(self, obj):
        """Получение жанров из JSON поля"""
        return getattr(obj, 'genres', []) or []
    
    def get_studios(self, obj):
        """Получение студий из JSON поля"""
        return getattr(obj, 'studios', []) or []

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
            'created_at', 'updated_at', 'data_source', 'shikimori_id'
        ]
        read_only_fields = ['created_at', 'updated_at']