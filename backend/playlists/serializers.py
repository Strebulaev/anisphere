from rest_framework import serializers
from django.conf import settings
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist, PlaylistShareLink
from anime.models import Anime


def get_full_url(url):
    if not url:
        return None
    if url.startswith('https://') or url.startswith('http://'):
        return url
    base_url = getattr(settings, 'SITE_URL', 'https://anisphere.ru')
    if url.startswith('/media/media/'):
        url = url.replace('/media/media/', '/media/')
    return f"{base_url}{url if url.startswith('/') else '/' + url}"


class PlaylistItemSerializer(serializers.ModelSerializer):
    anime = serializers.IntegerField(source='anime.id', read_only=True)
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
            'id', 'anime', 'anime_id', 'anime_title', 'anime_title_en',
            'anime_poster', 'anime_poster_url', 'anime_year', 'anime_score',
            'anime_status', 'anime_kind', 'anime_genres',
            'position', 'notes', 'added_at', 'created_at'
        ]
        read_only_fields = ['id', 'added_at', 'created_at']

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url or None


class PlaylistSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()

    items = PlaylistItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    cover_image = serializers.ImageField(read_only=True)
    cover_urls = serializers.SerializerMethodField()

    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()

    genres = serializers.SerializerMethodField()

    # Видимость
    visibility = serializers.CharField(read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    is_private = serializers.BooleanField(read_only=True)
    is_link_only = serializers.BooleanField(read_only=True)

    # Токен share-ссылки (только для владельца или когда плейлист link_only)
    share_token = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'user_id', 'user_username', 'user_avatar',
            'title', 'description', 'cover_image', 'cover_urls',
            'visibility', 'is_public', 'is_private', 'is_link_only',
            'is_favorited', 'favorites_count',
            'created_at', 'updated_at', 'items', 'items_count', 'genres',
            'share_token',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            avatar_url = obj.user.avatar.url
            if avatar_url.startswith('/media/media/'):
                avatar_url = avatar_url.replace('/media/media/', '/media/')
            return get_full_url(avatar_url)
        return None

    def get_items_count(self, obj):
        return obj.items.count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoritePlaylist.objects.filter(user=request.user, playlist=obj).exists()
        return False

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()

    def get_genres(self, obj):
        genres = set()
        for item in obj.items.all():
            for genre in item.anime.genres:
                genres.add(genre)
        return list(genres)[:10]

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned

    def get_share_token(self, obj):
        """Возвращает токен share-ссылки владельцу или для link_only"""
        request = self.context.get('request')
        if not request:
            return None
        is_owner = request.user.is_authenticated and obj.user_id == request.user.id
        if is_owner or obj.is_link_only:
            link = obj.get_active_share_link()
            if link:
                return link.token
        return None


class PlaylistCreateSerializer(serializers.ModelSerializer):
    cover_urls = serializers.SerializerMethodField()
    visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        default='public',
        required=False
    )

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'visibility', 'cover_urls', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        playlist = super().create(validated_data)
        # Если создаётся link — сразу генерируем share-ссылку
        if playlist.visibility == 'link':
            playlist.get_or_create_share_link()
        return playlist

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned


class PlaylistUpdateSerializer(serializers.ModelSerializer):
    cover_urls = serializers.SerializerMethodField()
    visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        required=False
    )

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'visibility', 'cover_urls', 'updated_at']
        read_only_fields = ['id', 'updated_at']

    def update(self, instance, validated_data):
        old_visibility = instance.visibility
        instance = super().update(instance, validated_data)
        new_visibility = instance.visibility
        # При переключении на link — создаём ссылку
        if new_visibility == 'link' and old_visibility != 'link':
            instance.get_or_create_share_link()
        # При уходе с link — деактивируем все ссылки
        elif old_visibility == 'link' and new_visibility != 'link':
            instance.invalidate_share_links()
        return instance

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned


class PlaylistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistItem
        fields = ['anime', 'notes']


class PlaylistItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistItem
        fields = ['position', 'notes']


class ReorderItemsSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Список элементов не может быть пустым")
        for item in value:
            if 'id' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь id")
            if 'position' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь position")
        return value


class FavoriteAnimeSerializer(serializers.ModelSerializer):
    anime = serializers.PrimaryKeyRelatedField(queryset=Anime.objects.all())
    anime_id = serializers.IntegerField(source='anime.id', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_poster_url = serializers.CharField(source='anime.poster_url', read_only=True)
    anime_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteAnime
        fields = [
            'id', 'anime', 'anime_id', 'anime_title', 'anime_title_en',
            'anime_poster', 'anime_poster_url', 'anime_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url

    def get_anime_data(self, obj):
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
    playlist_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoritePlaylist
        fields = ['id', 'playlist', 'playlist_data', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_playlist_data(self, obj):
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
            'visibility': obj.playlist.visibility,
            'is_public': obj.playlist.is_public,
            'is_private': obj.playlist.is_private,
            'is_link_only': obj.playlist.is_link_only,
            'cover_image': cover_image_url,
            'cover_urls': cleaned_cover_urls,
            'user_id': obj.playlist.user.id,
            'user_username': obj.playlist.user.username,
            'items_count': obj.playlist.items.count(),
            'favorites_count': obj.playlist.favorited_by.count(),
            'created_at': obj.playlist.created_at,
            'updated_at': obj.playlist.updated_at,
        }


class AddToPlaylistSerializer(serializers.Serializer):
    anime_id = serializers.IntegerField()
    playlist_id = serializers.IntegerField(required=False)
    new_playlist_title = serializers.CharField(required=False, max_length=255)
    new_playlist_description = serializers.CharField(required=False, allow_blank=True)
    new_playlist_visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        default='public',
        required=False
    )
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
