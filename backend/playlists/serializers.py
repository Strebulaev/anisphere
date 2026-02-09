from rest_framework import serializers
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist

class PlaylistItemSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_poster = serializers.CharField(source='anime.poster_url', read_only=True)
    anime = serializers.IntegerField(source='anime.id', read_only=True)

    class Meta:
        model = PlaylistItem
        fields = [
            'id', 'anime', 'anime_title', 'anime_poster',
            'episode_number', 'source_url', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class PlaylistSerializer(serializers.ModelSerializer):
    items = PlaylistItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.CharField(source='user.avatar', read_only=True)
    items_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'user', 'user_username', 'user_avatar', 'title', 'description',
            'is_public', 'is_favorite', 'favorites_count', 'is_favorited',
            'created_at', 'updated_at', 'items', 'items_count', 'genres'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoritePlaylist.objects.filter(
                user=request.user, playlist=obj
            ).exists()
        return False

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()

    def get_genres(self, obj):
        """Получить уникальные жанры из аниме в плейлисте"""
        genres = set()
        for item in obj.items.all():
            for genre in item.anime.genres.all():
                genres.add({
                    'id': genre.id,
                    'name': genre.name,
                    'slug': genre.slug
                })
        return list(genres)[:10]  # Ограничиваем 10 жанрами

class PlaylistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = ['title', 'description', 'is_public']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PlaylistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistItem
        fields = ['anime', 'episode_number', 'source_url', 'notes']

class FavoriteAnimeSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_poster = serializers.CharField(source='anime.poster_url', read_only=True)
    anime_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteAnime
        fields = [
            'id', 'anime', 'anime_title', 'anime_poster', 'anime_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_anime_data(self, obj):
        return {
            'id': obj.anime.id,
            'title_ru': obj.anime.title_ru,
            'title_en': obj.anime.title_en,
            'poster_url': obj.anime.poster_url,
            'year': obj.anime.year,
            'status': obj.anime.status,
            'score': obj.anime.score,
        }

class FavoritePlaylistSerializer(serializers.ModelSerializer):
    playlist_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoritePlaylist
        fields = ['id', 'playlist', 'playlist_data', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_playlist_data(self, obj):
        return {
            'id': obj.playlist.id,
            'title': obj.playlist.title,
            'description': obj.playlist.description,
            'is_public': obj.playlist.is_public,
            'user_username': obj.playlist.user.username,
            'items_count': obj.playlist.items.count(),
            'created_at': obj.playlist.created_at,
        }

class AddToPlaylistSerializer(serializers.Serializer):
    anime_id = serializers.IntegerField()
    playlist_id = serializers.IntegerField(required=False)
    new_playlist_title = serializers.CharField(required=False)
    episode_number = serializers.IntegerField(required=False, allow_null=True)
    source_url = serializers.URLField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')

        if not playlist_id and not new_playlist_title:
            raise serializers.ValidationError(
                "Необходимо указать playlist_id или new_playlist_title"
            )

        if playlist_id and new_playlist_title:
            raise serializers.ValidationError(
                "Укажите либо существующий плейлист, либо создайте новый"
            )

        return data