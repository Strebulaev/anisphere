from rest_framework import serializers
from django.conf import settings
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist


def get_full_url(url):
    """Преобразует относительный URL в полный"""
    if not url:
        return None
    if url.startswith('https://') or url.startswith('https://'):
        return url
    # Если URL относительный, добавляем базовый URL
    base_url = getattr(settings, 'SITE_URL', 'https://anisphere.ru')
    # Убираем дублирование /media/
    if url.startswith('/media/media/'):
        url = url.replace('/media/media/', '/media/')
    return f"{base_url}{url if url.startswith('/') else '/' + url}"


class PlaylistItemSerializer(serializers.ModelSerializer):
    """Сериализатор элемента плейлиста"""
    anime_id = serializers.IntegerField(source='anime.id', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_poster_url = serializers.CharField(source='anime.poster_url', read_only=True)
    anime_year = serializers.IntegerField(source='anime.year', read_only=True)
    anime_score = serializers.FloatField(source='anime.score', read_only=True)
    anime_status = serializers.CharField(source='anime.status', read_only=True)
    anime_kind = serializers.CharField(source='anime.kind', read_only=True)
    anime_genres = serializers.ListField(source='anime.genres', read_only=True)

    class Meta:
        model = PlaylistItem
        fields = [
            'id', 'anime_id', 'anime_title', 'anime_title_en',
            'anime_poster', 'anime_poster_url', 'anime_year', 'anime_score',
            'anime_status', 'anime_kind', 'anime_genres',
            'position', 'notes', 'added_at', 'created_at'
        ]
        read_only_fields = ['id', 'added_at', 'created_at']

    def get_anime_poster(self, obj):
        """Возвращает URL локального постера или внешний URL"""
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            # Убираем дублирование /media/
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url or None


class PlaylistSerializer(serializers.ModelSerializer):
    """Сериализатор плейлиста"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    
    items = PlaylistItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    # Обложка
    cover_image = serializers.ImageField(read_only=True)
    cover_urls = serializers.SerializerMethodField()
    
    # Избранное
    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    
    # Жанры из аниме в плейлисте
    genres = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'user_id', 'user_username', 'user_avatar',
            'title', 'description', 'cover_image', 'cover_urls',
            'is_public', 'is_favorited', 'favorites_count',
            'created_at', 'updated_at', 'items', 'items_count', 'genres'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_avatar(self, obj):
        """Возвращает URL аватара пользователя"""
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            avatar_url = obj.user.avatar.url
            # Убираем дублирование /media/
            if avatar_url.startswith('/media/media/'):
                avatar_url = avatar_url.replace('/media/media/', '/media/')
            return get_full_url(avatar_url)
        return None

    def get_items_count(self, obj):
        """Количество аниме в плейлисте"""
        return obj.items.count()

    def get_is_favorited(self, obj):
        """Добавлен ли плейлист в избранное текущим пользователем"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoritePlaylist.objects.filter(
                user=request.user, playlist=obj
            ).exists()
        return False

    def get_favorites_count(self, obj):
        """Количество пользователей, добавивших плейлист в избранное"""
        return obj.favorited_by.count()

    def get_genres(self, obj):
        """Уникальные жанры из аниме в плейлисте"""
        genres = set()
        for item in obj.items.all():
            for genre in item.anime.genres:
                genres.add(genre)
        return list(genres)[:10]  # Ограничиваем 10 жанрами

    def get_cover_urls(self, obj):
        """URL постеров первых 3 аниме для составной обложки"""
        urls = obj.get_cover_urls()
        if urls:
            # Убираем дублирование /media/ в каждом URL
            cleaned_urls = []
            for url in urls:
                if url.startswith('/media/media/'):
                    url = url.replace('/media/media/', '/media/')
                cleaned_urls.append(get_full_url(url))
            return cleaned_urls
        return []


class PlaylistCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания плейлиста"""
    cover_urls = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'is_public', 'cover_urls', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        playlist = super().create(validated_data)
        return playlist

    def get_cover_urls(self, obj):
        """URL постеров первых 3 аниме для составной обложки"""
        urls = obj.get_cover_urls()
        if urls:
            cleaned_urls = []
            for url in urls:
                if url.startswith('/media/media/'):
                    url = url.replace('/media/media/', '/media/')
                cleaned_urls.append(get_full_url(url))
            return cleaned_urls
        return []


class PlaylistUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления плейлиста"""
    cover_urls = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'is_public', 'cover_urls', 'updated_at']
        read_only_fields = ['id', 'updated_at']

    def get_cover_urls(self, obj):
        """URL постеров первых 3 аниме для составной обложки"""
        urls = obj.get_cover_urls()
        if urls:
            cleaned_urls = []
            for url in urls:
                if url.startswith('/media/media/'):
                    url = url.replace('/media/media/', '/media/')
                cleaned_urls.append(get_full_url(url))
            return cleaned_urls
        return []


class PlaylistItemCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления аниме в плейлист"""
    class Meta:
        model = PlaylistItem
        fields = ['anime', 'notes']


class PlaylistItemUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления элемента плейлиста"""
    class Meta:
        model = PlaylistItem
        fields = ['position', 'notes']


class ReorderItemsSerializer(serializers.Serializer):
    """Сериализатор для изменения порядка элементов"""
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_items(self, value):
        """Проверяет, что все элементы принадлежат одному плейлисту"""
        if not value:
            raise serializers.ValidationError("Список элементов не может быть пустым")
        
        # Проверяем, что каждый элемент имеет id и position
        for item in value:
            if 'id' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь id")
            if 'position' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь position")
        
        return value


class FavoriteAnimeSerializer(serializers.ModelSerializer):
    """Сериализатор избранного аниме"""
    anime_id = serializers.IntegerField(source='anime.id', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_poster_url = serializers.CharField(source='anime.poster_url', read_only=True)
    anime_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteAnime
        fields = [
            'id', 'anime_id', 'anime_title', 'anime_title_en',
            'anime_poster', 'anime_poster_url', 'anime_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_anime_poster(self, obj):
        """Возвращает URL локального постера или внешний URL"""
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            # Убираем дублирование /media/
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url

    def get_anime_data(self, obj):
        """Полные данные об аниме"""
        poster_url = None
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            poster_url = get_full_url(poster_url)

        return {
            'id': obj.anime.id,
            'title_ru': obj.anime.title_ru,
            'title_en': obj.anime.title_en,
            'title_jp': obj.anime.title_jp,
            'poster_url': obj.anime.poster_url,
            'poster': poster_url,
            'year': obj.anime.year,
            'status': obj.anime.status,
            'score': obj.anime.score,
            'kind': obj.anime.kind,
            'episodes': obj.anime.episodes,
            'genres': obj.anime.genres,
            'studios': obj.anime.studios,
            'description': obj.anime.description[:500] if obj.anime.description else '',
        }


class FavoritePlaylistSerializer(serializers.ModelSerializer):
    """Сериализатор избранного плейлиста"""
    playlist_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoritePlaylist
        fields = ['id', 'playlist', 'playlist_data', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_playlist_data(self, obj):
        """Полные данные о плейлисте"""
        cover_image_url = None
        if obj.playlist.cover_image:
            cover_image_url = obj.playlist.cover_image.url
            if cover_image_url.startswith('/media/media/'):
                cover_image_url = cover_image_url.replace('/media/media/', '/media/')
            cover_image_url = get_full_url(cover_image_url)

        cover_urls = obj.playlist.get_cover_urls()
        cleaned_cover_urls = []
        for url in cover_urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned_cover_urls.append(get_full_url(url))

        return {
            'id': obj.playlist.id,
            'title': obj.playlist.title,
            'description': obj.playlist.description,
            'is_public': obj.playlist.is_public,
            'cover_image': cover_image_url,
            'cover_urls': cleaned_cover_urls,
            'user_id': obj.playlist.user.id,
            'user_username': obj.playlist.user.username,
            'items_count': obj.playlist.items.count(),
            'favorites_count': obj.playlist.favorited_by.count(),
            'created_at': obj.playlist.created_at,
        }


class AddToPlaylistSerializer(serializers.Serializer):
    """Сериализатор для добавления аниме в плейлист"""
    anime_id = serializers.IntegerField()
    playlist_id = serializers.IntegerField(required=False)
    new_playlist_title = serializers.CharField(required=False, max_length=255)
    new_playlist_description = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Проверяет, что указан либо существующий плейлист, либо название нового"""
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