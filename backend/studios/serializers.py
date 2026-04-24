from rest_framework import serializers
from .models import Studio, StudioAnime, StudioSubscription, StudioRating, StudioNews, StudioAward, StudioDiscussion, StudioStaff
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


def _resolve_anime_poster(studio_anime_obj):
    """
    Возвращает постер аниме с приоритетом:
    1. Локальный файл (anime.poster) — абсолютный URL https://anisphere.org/media/...
    2. Внешний URL из нашей БД (anime.poster_url)
    3. Оригинальный URL с Shikimori/Kodik из StudioAnime
    """
    if studio_anime_obj.anime_db_id:
        try:
            from anime.models import Anime
            anime = Anime.objects.only('poster', 'poster_url').get(pk=studio_anime_obj.anime_db_id)
            if anime.poster and hasattr(anime.poster, 'url'):
                site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                return f"{site_url}{anime.poster.url}"
            if anime.poster_url:
                return anime.poster_url
        except Exception:
            pass
    return studio_anime_obj.anime_poster or ''


class StudioListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка студий"""
    logo_image_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    def get_logo_image_url(self, obj):
        return obj.logo_image_url

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StudioSubscription.objects.filter(user=request.user, studio=obj).exists()
        return False

    class Meta:
        model = Studio
        fields = [
            'id', 'name', 'name_jp', 'slug', 'country', 'founded_year',
            'total_anime', 'average_rating', 'subscribers_count',
            'notable_works', 'logo_image_url', 'is_subscribed', 'is_verified',
        ]


class StudioDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной страницы студии"""
    logo_image_url = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()
    top_anime = serializers.SerializerMethodField()

    def get_logo_image_url(self, obj):
        return obj.logo_image_url

    def get_banner_image_url(self, obj):
        return obj.banner_image_url

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StudioSubscription.objects.filter(user=request.user, studio=obj).exists()
        return False

    def get_rating_distribution(self, obj):
        from django.db.models import Count
        ratings = obj.ratings.values('overall_rating').annotate(count=Count('id'))
        dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = obj.ratings.count()
        for r in ratings:
            key = round(r['overall_rating'])
            if key in dist:
                dist[key] += r['count']
        if total > 0:
            return {k: round(v / total * 100) for k, v in dist.items()}
        return dist

    def get_top_anime(self, obj):
        top = obj.studio_anime.filter(anime_score__isnull=False).order_by('-anime_score')[:5]
        return [
            {
                'kodik_id': a.kodik_id,
                'anime_db_id': a.anime_db_id,
                'anime_url': f'/anime/{a.anime_db_id}' if a.anime_db_id else None,
                'anime_title': a.anime_title,
                'anime_score': a.anime_score,
                'anime_poster': _resolve_anime_poster(a),
                'anime_kind': a.anime_kind,
            }
            for a in top
        ]

    class Meta:
        model = Studio
        fields = [
            'id', 'name', 'name_jp', 'slug', 'description',
            'country', 'founded_year', 'employees_count',
            'website', 'twitter', 'youtube', 'facebook',
            'total_anime', 'tv_count', 'movie_count', 'ova_count',
            'average_rating', 'subscribers_count',
            'notable_works', 'genre_stats',
            'logo_image_url', 'banner_image_url',
            'is_subscribed', 'is_verified',
            'rating_distribution', 'top_anime',
            'created_at',
        ]


class StudioAnimeSerializer(serializers.ModelSerializer):
    anime_url = serializers.SerializerMethodField()
    anime_poster = serializers.SerializerMethodField()

    def get_anime_url(self, obj):
        if obj.anime_db_id:
            return f'/anime/{obj.anime_db_id}'
        return None

    def get_anime_poster(self, obj):
        return _resolve_anime_poster(obj)

    class Meta:
        model = StudioAnime
        fields = [
            'id', 'kodik_id', 'anime_db_id', 'anime_url',
            'anime_title', 'anime_title_en', 'anime_kind',
            'anime_year', 'anime_score', 'anime_poster',
            'anime_status', 'shikimori_id', 'episodes_total',
            'description', 'genres',
        ]


class StudioStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudioStaff
        fields = ['id', 'name', 'name_jp', 'role', 'role_detail', 'photo_url', 'works_count', 'notable_works', 'is_key_person', 'awards']


class StudioNewsSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    def get_author_name(self, obj):
        return obj.author.username if obj.author else 'Редакция'

    class Meta:
        model = StudioNews
        fields = ['id', 'title', 'content', 'author_name', 'likes_count', 'comments_count', 'created_at']


class StudioAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudioAward
        fields = ['id', 'year', 'award_name', 'category', 'is_winner']


class StudioDiscussionSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()

    def get_author_name(self, obj):
        return obj.author.username

    def get_author_avatar(self, obj):
        if hasattr(obj.author, 'avatar') and obj.author.avatar:
            return obj.author.avatar.url
        return None

    class Meta:
        model = StudioDiscussion
        fields = [
            'id', 'title', 'content', 'author_name', 'author_avatar',
            'likes_count', 'dislikes_count', 'replies_count',
            'is_pinned', 'created_at', 'last_reply_at',
        ]


class StudioRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.username

    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            return obj.user.avatar.url
        return None

    class Meta:
        model = StudioRating
        fields = [
            'id', 'user_name', 'user_avatar',
            'animation_quality', 'directing', 'soundtrack', 'adaptation',
            'overall_rating', 'comment', 'created_at',
        ]
