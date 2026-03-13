from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import Q, Count, Max
from rest_framework.pagination import PageNumberPagination
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist, PlaylistShareLink
from .serializers import (
    PlaylistSerializer, PlaylistCreateSerializer, PlaylistUpdateSerializer,
    PlaylistItemSerializer, PlaylistItemCreateSerializer, PlaylistItemUpdateSerializer,
    ReorderItemsSerializer,
    FavoriteAnimeSerializer, FavoritePlaylistSerializer,
    AddToPlaylistSerializer
)
import re
from anime.models import Anime


def parse_anime_link(url):
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
            anime = Anime.objects.filter(slug__icontains=title_slug).first() or \
                    Anime.objects.filter(title_ru__icontains=title_slug.replace('-', ' ')).first() or \
                    Anime.objects.filter(title_en__icontains=title_slug.replace('-', ' ')).first()
            return anime
    url_lower = url.lower()
    for word in ['anime', 'season', 'series']:
        if word in url_lower:
            for part in reversed(url.split('/')):
                if part and len(part) > 3:
                    anime = Anime.objects.filter(title_ru__icontains=part.replace('-', ' ')).first() or \
                            Anime.objects.filter(title_en__icontains=part.replace('-', ' ')).first()
                    if anime:
                        return anime
    return None


class StandardPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet для плейлистов"""
    queryset = Playlist.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']

    def get_serializer_class(self):
        if self.action == 'create':
            return PlaylistCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlaylistUpdateSerializer
        return PlaylistSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = Playlist.objects.select_related('user').prefetch_related('items__anime')
        user = self.request.user

        if self.action == 'list':
            # --- Мои плейлисты ---
            my = self.request.query_params.get('my')
            if my in ('true', '1', 'True'):
                if not user.is_authenticated:
                    return Playlist.objects.none()
                queryset = queryset.filter(user=user)
                # Подфильтр по visibility для подвкладок
                visibility = self.request.query_params.get('visibility')
                if visibility in ('public', 'private', 'link'):
                    queryset = queryset.filter(visibility=visibility)
                return self._apply_common_filters(queryset)

            # --- Избранные ---
            favorites = self.request.query_params.get('favorites')
            if favorites in ('true', '1', 'True'):
                if not user.is_authenticated:
                    return Playlist.objects.none()
                # Все плейлисты из избранного пользователя (любая видимость)
                fav_ids = FavoritePlaylist.objects.filter(user=user).values_list('playlist_id', flat=True)
                queryset = queryset.filter(id__in=fav_ids)
                return self._apply_common_filters(queryset)

            # --- Публичные (все пользователи) ---
            is_public = self.request.query_params.get('is_public')
            if is_public in ('true', '1', 'True'):
                queryset = queryset.filter(visibility='public')
                return self._apply_common_filters(queryset)

            # --- По умолчанию: свои + публичные ---
            if user.is_authenticated:
                queryset = queryset.filter(
                    Q(visibility='public') | Q(user=user)
                ).distinct()
            else:
                queryset = queryset.filter(visibility='public')

        return self._apply_common_filters(queryset)

    def _apply_common_filters(self, queryset):
        params = self.request.query_params

        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        genre = params.get('genre')
        if genre:
            queryset = queryset.filter(items__anime__genres__icontains=genre).distinct()

        year = params.get('year')
        if year:
            queryset = queryset.filter(items__anime__year=year).distinct()

        ordering = params.get('ordering', '-created_at')
        allowed = [
            'created_at', '-created_at', 'updated_at', '-updated_at',
            'title', '-title', 'items_count', '-items_count',
            'favorites_count', '-favorites_count'
        ]
        if ordering in allowed:
            if ordering in ('items_count', '-items_count'):
                queryset = queryset.annotate(items_count_ann=Count('items')).order_by(
                    ordering.replace('items_count', 'items_count_ann')
                )
            elif ordering in ('favorites_count', '-favorites_count'):
                queryset = queryset.annotate(fav_count_ann=Count('favorited_by')).order_by(
                    ordering.replace('favorites_count', 'fav_count_ann')
                )
            else:
                queryset = queryset.order_by(ordering)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        # Деактивируем все share-ссылки перед удалением
        playlist.invalidate_share_links()
        if playlist.cover_image:
            try:
                playlist.cover_image.delete()
            except:
                pass
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Плейлисты текущего пользователя (без пагинации, для совместимости)"""
        playlists = Playlist.objects.filter(user=request.user)
        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Публичные плейлисты"""
        playlists = Playlist.objects.filter(visibility='public').select_related('user').prefetch_related('items__anime')
        page = self.paginate_queryset(playlists)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)

    # ───────────────────────── Share-ссылки ─────────────────────────

    @action(detail=True, methods=['post'], url_path='share-link')
    def generate_share_link(self, request, pk=None):
        """Сгенерировать / получить share-ссылку (только владелец)"""
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)

        ttl_days = int(request.data.get('ttl_days', 30))
        # Инвалидируем старые и создаём новую
        playlist.invalidate_share_links()
        link = playlist.get_or_create_share_link(ttl_days=ttl_days)

        return Response({
            'token': link.token,
            'expires_at': link.expires_at,
            'share_url': f"{request.build_absolute_uri('/').rstrip('/')}/playlist/shared/{link.token}",
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='share-link')
    def revoke_share_link(self, request, pk=None):
        """Отозвать share-ссылку"""
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist.invalidate_share_links()
        return Response({'message': 'Ссылка деактивирована'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='update-visibility')
    def update_visibility(self, request, pk=None):
        """Быстрое обновление видимости плейлиста"""
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)

        visibility = request.data.get('visibility')
        if visibility not in ('public', 'private', 'link'):
            return Response({'error': 'Допустимые значения: public, private, link'}, status=status.HTTP_400_BAD_REQUEST)

        old = playlist.visibility
        playlist.visibility = visibility
        playlist.save(update_fields=['visibility'])

        if visibility == 'link' and old != 'link':
            playlist.get_or_create_share_link()
        elif old == 'link' and visibility != 'link':
            playlist.invalidate_share_links()

        serializer = self.get_serializer(playlist)
        return Response(serializer.data)

    # ───────────────────────── Прочие actions ─────────────────────────

    @action(detail=True, methods=['post'])
    def update_cover(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        cover_url = playlist.update_cover()
        if cover_url:
            return Response(self.get_serializer(playlist).data)
        return Response({'error': 'Не удалось создать обложку'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PlaylistItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            anime = serializer.validated_data['anime']
            if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
                return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(playlist=playlist)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_by_link(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        url = request.data.get('url')
        if not url:
            return Response({'error': 'Не указана ссылка'}, status=status.HTTP_400_BAD_REQUEST)
        anime = parse_anime_link(url)
        if not anime:
            return Response({'error': 'Не удалось распознать аниме по ссылке'}, status=status.HTTP_400_BAD_REQUEST)
        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)
        item = PlaylistItem.objects.create(playlist=playlist, anime=anime, notes=request.data.get('notes', ''))
        return Response(PlaylistItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        playlist = self.get_object()
        anime_id = request.data.get('anime_id')
        item_id = request.data.get('item_id')
        if not anime_id and not item_id:
            return Response({'error': 'Не указан anime_id или item_id'}, status=status.HTTP_400_BAD_REQUEST)
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        try:
            if anime_id:
                item = PlaylistItem.objects.get(playlist=playlist, anime_id=anime_id)
            else:
                item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.delete()
            PlaylistItem.objects.filter(playlist=playlist, position__gt=item.position).update(
                position=models.F('position') - 1
            )
            playlist.update_cover()
            return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        except PlaylistItem.DoesNotExist:
            return Response({'error': 'Элемент не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def reorder_items(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReorderItemsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            for item_data in serializer.validated_data['items']:
                try:
                    item = PlaylistItem.objects.get(id=item_data['id'], playlist=playlist)
                    item.position = item_data['position']
                    item.save(update_fields=['position'])
                except PlaylistItem.DoesNotExist:
                    continue
        playlist.update_cover()
        return Response({'message': 'Порядок обновлён'})

    @action(detail=True, methods=['post'], url_path='update-item-notes')
    def update_item_notes(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        item_id = request.data.get('item_id')
        notes = request.data.get('notes', '')
        if not item_id:
            return Response({'error': 'Не указан item_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.notes = notes
            item.save(update_fields=['notes'])
            return Response(PlaylistItemSerializer(item).data)
        except PlaylistItem.DoesNotExist:
            return Response({'error': 'Элемент не найден'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        playlist = self.get_object()
        if playlist.user == request.user:
            return Response({'error': 'Нельзя добавить свой плейлист в избранное'}, status=status.HTTP_400_BAD_REQUEST)
        favorite, created = FavoritePlaylist.objects.get_or_create(user=request.user, playlist=playlist)
        if created:
            return Response({'message': 'Добавлено в избранное'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Уже в избранном'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unfavorite(self, request, pk=None):
        playlist = self.get_object()
        deleted, _ = FavoritePlaylist.objects.filter(user=request.user, playlist=playlist).delete()
        if deleted:
            return Response({'message': 'Убрано из избранного'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Не в избранном'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original = self.get_object()
        new_playlist = Playlist.objects.create(
            user=request.user,
            title=f"{original.title} (копия)",
            description=original.description,
            visibility='private'
        )
        for item in original.items.all():
            PlaylistItem.objects.create(
                playlist=new_playlist, anime=item.anime,
                notes=item.notes, position=item.position
            )
        new_playlist.update_cover()
        return Response(self.get_serializer(new_playlist).data, status=status.HTTP_201_CREATED)


# ─────────────────── Share-ссылка: публичный доступ ───────────────────

class PlaylistByShareTokenView(views.APIView):
    """Открыть плейлист по share-токену (публичный эндпоинт)"""
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            link = PlaylistShareLink.objects.select_related('playlist__user').get(token=token)
        except PlaylistShareLink.DoesNotExist:
            return Response({'error': 'Ссылка не найдена или недействительна'}, status=status.HTTP_404_NOT_FOUND)

        if not link.is_valid:
            return Response({'error': 'Ссылка истекла или была отозвана'}, status=status.HTTP_410_GONE)

        playlist = link.playlist
        # Плейлист должен быть link_only или public
        if playlist.visibility == 'private':
            return Response({'error': 'Плейлист недоступен'}, status=status.HTTP_403_FORBIDDEN)

        link.touch()
        serializer = PlaylistSerializer(playlist, context={'request': request})
        return Response(serializer.data)


# ─────────────────── Остальные views ───────────────────

class AddToPlaylistView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToPlaylistSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        anime_id = data['anime_id']
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=status.HTTP_404_NOT_FOUND)

        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')

        if playlist_id:
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                return Response({'error': 'Плейлист не найден или нет прав'}, status=status.HTTP_404_NOT_FOUND)
        else:
            visibility = data.get('new_playlist_visibility', 'public')
            playlist = Playlist.objects.create(
                user=request.user,
                title=new_playlist_title,
                description=data.get('new_playlist_description', ''),
                visibility=visibility,
            )
            if visibility == 'link':
                playlist.get_or_create_share_link()

        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response({'error': 'Аниме уже есть в плейлисте'}, status=status.HTTP_400_BAD_REQUEST)

        item = PlaylistItem.objects.create(playlist=playlist, anime=anime, notes=data.get('notes', ''))
        playlist.update_cover()
        return Response({
            'message': 'Добавлено',
            'playlist_id': playlist.id,
            'item_id': item.id
        }, status=status.HTTP_201_CREATED)


class FavoriteAnimeViewSet(viewsets.ModelViewSet):
    queryset = FavoriteAnime.objects.all()
    serializer_class = FavoriteAnimeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteAnime.objects.filter(user=self.request.user).select_related('anime')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        anime_id = request.data.get('anime')
        if not anime_id:
            return Response({'error': 'Не указан anime'}, status=status.HTTP_400_BAD_REQUEST)
        existing = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).first()
        if existing:
            return Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        anime_id = request.data.get('anime_id')
        if anime_id:
            deleted, _ = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).delete()
            if deleted:
                return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def check(self, request):
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'Нет anime_id'}, status=status.HTTP_400_BAD_REQUEST)
        is_favorite = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).exists()
        return Response({'is_favorite': is_favorite})

    @action(detail=False, methods=['delete'], url_path='remove')
    def remove_favorite(self, request):
        anime_id = request.data.get('anime_id')
        if not anime_id:
            return Response({'error': 'Нет anime_id'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).delete()
        if deleted:
            return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Не в избранном'}, status=status.HTTP_404_NOT_FOUND)


class FavoritePlaylistViewSet(viewsets.ModelViewSet):
    queryset = FavoritePlaylist.objects.all()
    serializer_class = FavoritePlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoritePlaylist.objects.filter(user=self.request.user).select_related('playlist')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def all(self, request):
        favorites = FavoritePlaylist.objects.filter(user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    queryset = PlaylistItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return PlaylistItemUpdateSerializer
        return PlaylistItemSerializer

    def get_queryset(self):
        return PlaylistItem.objects.filter(playlist__user=self.request.user).select_related('anime', 'playlist')

    def perform_create(self, serializer):
        playlist_id = self.kwargs.get('playlist_pk')
        if playlist_id:
            playlist = get_object_or_404(Playlist, id=playlist_id)
            if playlist.user != self.request.user:
                raise PermissionError("Нет прав")
            serializer.save(playlist=playlist)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.playlist.user != request.user:
            return Response({'error': 'Нет прав'}, status=status.HTTP_403_FORBIDDEN)
        playlist = item.playlist
        item.delete()
        PlaylistItem.objects.filter(playlist=playlist, position__gt=item.position).update(
            position=models.F('position') - 1
        )
        playlist.update_cover()
        return Response({'message': 'Удалено'}, status=status.HTTP_204_NO_CONTENT)


class PlaylistSearchView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))
        if not search:
            return Response({'results': []})
        queryset = Playlist.objects.filter(
            Q(title__icontains=search) | Q(description__icontains=search),
            visibility='public'
        ).select_related('user').prefetch_related('items__anime')[:limit]
        serializer = PlaylistSerializer(queryset, many=True, context={'request': request})
        return Response({'results': serializer.data, 'count': len(serializer.data)})