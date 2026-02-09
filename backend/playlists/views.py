from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist
from .serializers import (
    PlaylistSerializer, PlaylistCreateSerializer,
    PlaylistItemSerializer, PlaylistItemCreateSerializer,
    FavoriteAnimeSerializer, FavoritePlaylistSerializer,
    AddToPlaylistSerializer
)
import re
from anime.models import Anime


def parse_anime_link(url):
    """Парсит ссылку и пытается найти аниме по названию или ID"""
    patterns = {
        'jut.su': r'jut\.su/([^/]+)/?',
        'animego.org': r'animego\.org/anime/([^/]+)',
        'sovetromantica.com': r'sovetromantica\.com/anime/([^/]+)',
        'anilibria.tv': r'anilibria\.tv/release/([^/]+)',
    }

    for site, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            title_slug = match.group(1)
            anime = Anime.objects.filter(
                slug__icontains=title_slug
            ).first() or Anime.objects.filter(
                title_ru__icontains=title_slug.replace('-', ' ')
            ).first() or Anime.objects.filter(
                title_en__icontains=title_slug.replace('-', ' ')
            ).first()
            return anime

    url_lower = url.lower()
    anime_words = ['anime', 'season', 'series']
    for word in anime_words:
        if word in url_lower:
            parts = url.split('/')
            for part in reversed(parts):
                if part and len(part) > 3:
                    anime = Anime.objects.filter(
                        title_ru__icontains=part.replace('-', ' ')
                    ).first() or Anime.objects.filter(
                        title_en__icontains=part.replace('-', ' ')
                    ).first()
                    if anime:
                        return anime

    return None


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_public', 'user']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PlaylistCreateSerializer
        return PlaylistSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = Playlist.objects.all()

        # Фильтрация по типу плейлиста
        if self.action == 'list':
            if self.request.user.is_authenticated:
                # Показываем свои + публичные
                queryset = queryset.filter(
                    is_public=True
                ) | queryset.filter(user=self.request.user)
            else:
                queryset = queryset.filter(is_public=True)

        # Параметры фильтрации
        search = self.request.query_params.get('search')
        genre = self.request.query_params.get('genre')
        year = self.request.query_params.get('year')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        if genre:
            queryset = queryset.filter(anime__genres=genre).distinct()

        if year:
            queryset = queryset.filter(anime__year=year).distinct()

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed_orderings = [
            'created_at', '-created_at',
            'title', '-title',
            'items_count', '-items_count',
            'favorites_count', '-favorites_count'
        ]
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Получить плейлисты текущего пользователя"""
        playlists = Playlist.objects.filter(user=request.user)
        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Получить публичные плейлисты"""
        playlists = Playlist.objects.filter(is_public=True)
        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Добавить элемент в плейлист"""
        playlist = self.get_object()

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PlaylistItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            anime = serializer.validated_data['anime']
            if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
                return Response(
                    {'error': 'Это аниме уже есть в плейлисте'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(playlist=playlist)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_by_link(self, request, pk=None):
        """Добавить аниме в плейлист по ссылке"""
        playlist = self.get_object()

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        url = request.data.get('url')
        if not url:
            return Response(
                {'error': 'Не указана ссылка'},
                status=status.HTTP_400_BAD_REQUEST
            )

        anime = parse_anime_link(url)
        if not anime:
            return Response(
                {'error': 'Не удалось распознать аниме по ссылке'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response(
                {'error': 'Это аниме уже есть в плейлисте'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item_data = {
            'anime': anime.id,
            'episode_number': request.data.get('episode_number'),
            'source_url': url,
            'notes': request.data.get('notes', ''),
        }

        serializer = PlaylistItemCreateSerializer(data=item_data)
        if serializer.is_valid():
            serializer.save(playlist=playlist)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Удалить элемент из плейлиста"""
        playlist = self.get_object()
        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {'error': 'Не указан item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            if playlist.user != request.user:
                return Response(
                    {'error': 'У вас нет прав на изменение этого плейлиста'},
                    status.HTTP_403_FORBIDDEN
                )
            item.delete()
            return Response({'message': 'Элемент удалён'}, status.HTTP_204_NO_CONTENT)
        except PlaylistItem.DoesNotExist:
            return Response(
                {'error': 'Элемент не найден'},
                status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Добавить плейлист в избранное"""
        playlist = self.get_object()

        if playlist.user == request.user:
            return Response(
                {'error': 'Нельзя добавить свой плейлист в избранное'},
                status.HTTP_400_BAD_REQUEST
            )

        favorite, created = FavoritePlaylist.objects.get_or_create(
            user=request.user, playlist=playlist
        )

        if created:
            return Response({'message': 'Плейлист добавлен в избранное'}, status.HTTP_201_CREATED)
        return Response({'message': 'Плейлист уже в избранном'}, status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unfavorite(self, request, pk=None):
        """Удалить плейлист из избранного"""
        playlist = self.get_object()

        deleted, _ = FavoritePlaylist.objects.filter(
            user=request.user, playlist=playlist
        ).delete()

        if deleted:
            return Response({'message': 'Плейлист удалён из избранного'}, status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Плейлист не найден в избранном'},
            status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Дублировать плейлист"""
        original = self.get_object()

        new_playlist = Playlist.objects.create(
            user=request.user,
            title=f"{original.title} (копия)",
            description=original.description,
            is_public=False
        )

        for item in original.items.all():
            PlaylistItem.objects.create(
                playlist=new_playlist,
                anime=item.anime,
                episode_number=item.episode_number,
                source_url=item.source_url,
                notes=item.notes
            )

        serializer = self.get_serializer(new_playlist)
        return Response(serializer.data, status.HTTP_201_CREATED)


class AddToPlaylistView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Добавить аниме в плейлист (создание нового или выбор существующего)"""
        serializer = AddToPlaylistSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        anime_id = data['anime_id']

        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {'error': 'Аниме не найдено'},
                status.HTTP_404_NOT_FOUND
            )

        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')

        if playlist_id:
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                return Response(
                    {'error': 'Плейлист не найден или у вас нет прав'},
                    status.HTTP_404_NOT_FOUND
                )
        else:
            playlist = Playlist.objects.create(
                user=request.user,
                title=new_playlist_title,
                is_public=False
            )

        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response(
                {'error': 'Это аниме уже есть в плейлисте'},
                status.HTTP_400_BAD_REQUEST
            )

        item = PlaylistItem.objects.create(
            playlist=playlist,
            anime=anime,
            episode_number=data.get('episode_number'),
            source_url=data.get('source_url', ''),
            notes=data.get('notes', '')
        )

        return Response({
            'message': 'Аниме добавлено в плейлист',
            'playlist_id': playlist.id,
            'item_id': item.id
        }, status.HTTP_201_CREATED)


class FavoriteAnimeViewSet(viewsets.ModelViewSet):
    queryset = FavoriteAnime.objects.all()
    serializer_class = FavoriteAnimeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteAnime.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """Проверить, в избранном ли аниме"""
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response(
                {'error': 'Не указан anime_id'},
                status.HTTP_400_BAD_REQUEST
            )

        is_favorite = FavoriteAnime.objects.filter(
            user=request.user, anime_id=anime_id
        ).exists()

        return Response({'is_favorite': is_favorite})

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        """Удалить аниме из избранного"""
        anime_id = request.data.get('anime_id')
        if not anime_id:
            return Response(
                {'error': 'Не указан anime_id'},
                status.HTTP_400_BAD_REQUEST
            )

        deleted, _ = FavoriteAnime.objects.filter(
            user=request.user, anime_id=anime_id
        ).delete()

        if deleted:
            return Response({'message': 'Аниме удалено из избранного'}, status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Аниме не найдено в избранном'},
            status.HTTP_404_NOT_FOUND
        )


class FavoritePlaylistViewSet(viewsets.ModelViewSet):
    queryset = FavoritePlaylist.objects.all()
    serializer_class = FavoritePlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoritePlaylist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def all(self, request):
        """Получить все избранные плейлисты пользователя"""
        favorites = FavoritePlaylist.objects.filter(user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    queryset = PlaylistItem.objects.all()
    serializer_class = PlaylistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlaylistItem.objects.filter(
            playlist__user=self.request.user
        ) | PlaylistItem.objects.filter(
            playlist__is_public=True
        ).distinct()

    def perform_create(self, serializer):
        playlist_id = self.kwargs.get('playlist_pk')
        if playlist_id:
            playlist = get_object_or_404(Playlist, id=playlist_id)
            if playlist.user != self.request.user:
                raise PermissionError("Не хватает прав")
            serializer.save(playlist=playlist)
        else:
            serializer.save()
