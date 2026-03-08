from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import Q, Count, Max
from rest_framework.pagination import PageNumberPagination
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist
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
    """ViewSet для плейлистов"""
    queryset = Playlist.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_public', 'user']

    def get_serializer_class(self):
        if self.action == 'create':
            return PlaylistCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlaylistUpdateSerializer
        return PlaylistSerializer

    def get_permissions(self):
        """Разрешения"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        """Фильтрация плейлистов"""
        queryset = Playlist.objects.select_related('user').prefetch_related('items__anime')

        if self.action == 'list':
            if self.request.user.is_authenticated:
                # Показываем свои + публичные
                queryset = queryset.filter(
                    Q(is_public=True) | Q(user=self.request.user)
                ).distinct()
            else:
                queryset = queryset.filter(is_public=True)

        # Параметры фильтрации
        search = self.request.query_params.get('search')
        genre = self.request.query_params.get('genre')
        year = self.request.query_params.get('year')
        status = self.request.query_params.get('status')
        kind = self.request.query_params.get('kind')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        if genre:
            queryset = queryset.filter(
                items__anime__genres__icontains=genre
            ).distinct()

        if year:
            queryset = queryset.filter(
                items__anime__year=year
            ).distinct()

        if status:
            queryset = queryset.filter(
                items__anime__status=status
            ).distinct()

        if kind:
            queryset = queryset.filter(
                items__anime__kind=kind
            ).distinct()

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed_orderings = [
            'created_at', '-created_at',
            'updated_at', '-updated_at',
            'title', '-title',
            'items_count', '-items_count',
            'favorites_count', '-favorites_count'
        ]
        if ordering in allowed_orderings:
            if ordering in ['items_count', '-items_count']:
                queryset = queryset.annotate(
                    items_count=Count('items')
                ).order_by(ordering)
            elif ordering in ['favorites_count', '-favorites_count']:
                queryset = queryset.annotate(
                    favorites_count=Count('favorited_by')
                ).order_by(ordering)
            else:
                queryset = queryset.order_by(ordering)

        return queryset

    def perform_create(self, serializer):
        """Создание плейлиста"""
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Удаление плейлиста"""
        playlist = self.get_object()

        # Проверяем права
        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на удаление этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Удаляем обложку если есть
        if playlist.cover_image:
            try:
                playlist.cover_image.delete()
            except:
                pass
        
        return super().destroy(request, *args, **kwargs)

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
    def update_cover(self, request, pk=None):
        """Обновить обложку плейлиста"""
        playlist = self.get_object()
        
        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        cover_url = playlist.update_cover()
        
        if cover_url:
            serializer = self.get_serializer(playlist)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Не удалось создать обложку'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Добавить аниме в плейлист"""
        playlist = self.get_object()

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PlaylistItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            anime = serializer.validated_data['anime']
            
            # Проверяем, есть ли аниме в плейлисте
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

        item = PlaylistItem.objects.create(
            playlist=playlist,
            anime=anime,
            notes=request.data.get('notes', '')
        )

        serializer = PlaylistItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Удалить аниме из плейлиста"""
        playlist = self.get_object()
        anime_id = request.data.get('anime_id')
        item_id = request.data.get('item_id')

        if not anime_id and not item_id:
            return Response(
                {'error': 'Не указан anime_id или item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            if anime_id:
                item = PlaylistItem.objects.get(playlist=playlist, anime_id=anime_id)
            else:
                item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            
            item.delete()
            
            # Обновляем позиции остальных элементов
            PlaylistItem.objects.filter(
                playlist=playlist, position__gt=item.position
            ).update(position=models.F('position') - 1)
            
            # Обновляем обложку
            playlist.update_cover()
            
            return Response({'message': 'Аниме удалено из плейлиста'}, status=status.HTTP_204_NO_CONTENT)
        except PlaylistItem.DoesNotExist:
            return Response(
                {'error': 'Элемент не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def reorder_items(self, request, pk=None):
        """Изменить порядок элементов в плейлисте"""
        playlist = self.get_object()

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ReorderItemsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data['items']
        
        with transaction.atomic():
            for item_data in items_data:
                try:
                    item = PlaylistItem.objects.get(
                        id=item_data['id'], playlist=playlist
                    )
                    item.position = item_data['position']
                    item.save(update_fields=['position'])
                except PlaylistItem.DoesNotExist:
                    continue
        
        # Обновляем обложку
        playlist.update_cover()
        
        return Response({'message': 'Порядок элементов обновлён'})

    @action(detail=True, methods=['post'], url_path='update-item-notes')
    def update_item_notes(self, request, pk=None):
        """Обновить заметки к элементу плейлиста"""
        playlist = self.get_object()

        if playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на изменение этого плейлиста'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_id = request.data.get('item_id')
        notes = request.data.get('notes', '')

        if not item_id:
            return Response(
                {'error': 'Не указан item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.notes = notes
            item.save(update_fields=['notes'])
            
            serializer = PlaylistItemSerializer(item)
            return Response(serializer.data)
        except PlaylistItem.DoesNotExist:
            return Response(
                {'error': 'Элемент не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Добавить плейлист в избранное"""
        playlist = self.get_object()

        if playlist.user == request.user:
            return Response(
                {'error': 'Нельзя добавить свой плейлист в избранное'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite, created = FavoritePlaylist.objects.get_or_create(
            user=request.user, playlist=playlist
        )

        if created:
            return Response({'message': 'Плейлист добавлен в избранное'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Плейлист уже в избранном'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unfavorite(self, request, pk=None):
        """Удалить плейлист из избранного"""
        playlist = self.get_object()

        deleted, _ = FavoritePlaylist.objects.filter(
            user=request.user, playlist=playlist
        ).delete()

        if deleted:
            return Response({'message': 'Плейлист удалён из избранного'}, status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Плейлист не найден в избранном'},
            status=status.HTTP_404_NOT_FOUND
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
                notes=item.notes,
                position=item.position
            )

        # Генерируем обложку
        new_playlist.update_cover()

        serializer = self.get_serializer(new_playlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddToPlaylistView(views.APIView):
    """Добавить аниме в плейлист (создание нового или выбор существующего)"""
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
            return Response(
                {'error': 'Аниме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )

        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')

        if playlist_id:
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                return Response(
                    {'error': 'Плейлист не найден или у вас нет прав'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            playlist = Playlist.objects.create(
                user=request.user,
                title=new_playlist_title,
                description=data.get('new_playlist_description', ''),
                is_public=False
            )

        if PlaylistItem.objects.filter(playlist=playlist, anime=anime).exists():
            return Response(
                {'error': 'Это аниме уже есть в плейлисте'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item = PlaylistItem.objects.create(
            playlist=playlist,
            anime=anime,
            notes=data.get('notes', '')
        )

        # Обновляем обложку плейлиста
        playlist.update_cover()
        
        return Response({
            'message': 'Аниме добавлено в плейлист',
            'playlist_id': playlist.id,
            'item_id': item.id
        }, status=status.HTTP_201_CREATED)


class FavoriteAnimeViewSet(viewsets.ModelViewSet):
    """ViewSet для избранных аниме"""
    queryset = FavoriteAnime.objects.all()
    serializer_class = FavoriteAnimeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteAnime.objects.filter(user=self.request.user).select_related('anime')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Добавление аниме в избранное с защитой от дублирования"""
        anime_id = request.data.get('anime')
        if not anime_id:
            return Response({'error': 'Не указан anime'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существующее избранное
        existing = FavoriteAnime.objects.filter(user=request.user, anime_id=anime_id).first()
        if existing:
            serializer = self.get_serializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Удаление аниме из избранного"""
        anime_id = request.data.get('anime_id')
        
        if anime_id:
            deleted, _ = FavoriteAnime.objects.filter(
                user=request.user, anime_id=anime_id
            ).delete()
            
            if deleted:
                return Response({'message': 'Аниме удалено из избранного'}, status=status.HTTP_204_NO_CONTENT)
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """Проверить, в избранном ли аниме"""
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response(
                {'error': 'Не указан anime_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_favorite = FavoriteAnime.objects.filter(
            user=request.user, anime_id=anime_id
        ).exists()

        return Response({'is_favorite': is_favorite})

    @action(detail=False, methods=['delete'], url_path='remove')
    def remove_favorite(self, request):
        """Удалить аниме из избранного"""
        anime_id = request.data.get('anime_id')

        if not anime_id:
            return Response(
                {'error': 'Не указан anime_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted, _ = FavoriteAnime.objects.filter(
            user=request.user, anime_id=anime_id
        ).delete()

        if deleted:
            return Response({'message': 'Аниме удалено из избранного'}, status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {'error': 'Аниме не найдено в избранном'},
            status=status.HTTP_404_NOT_FOUND
        )


class FavoritePlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet для избранных плейлистов"""
    queryset = FavoritePlaylist.objects.all()
    serializer_class = FavoritePlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoritePlaylist.objects.filter(user=self.request.user).select_related('playlist')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def all(self, request):
        """Получить все избранные плейлисты пользователя"""
        favorites = FavoritePlaylist.objects.filter(user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    """ViewSet для элементов плейлиста"""
    queryset = PlaylistItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return PlaylistItemUpdateSerializer
        return PlaylistItemSerializer

    def get_queryset(self):
        return PlaylistItem.objects.filter(
            playlist__user=self.request.user
        ).select_related('anime', 'playlist')

    def perform_create(self, serializer):
        playlist_id = self.kwargs.get('playlist_pk')
        if playlist_id:
            playlist = get_object_or_404(Playlist, id=playlist_id)
            if playlist.user != self.request.user:
                raise PermissionError("Не хватает прав")
            serializer.save(playlist=playlist)

    def destroy(self, request, *args, **kwargs):
        """Удаление элемента плейлиста"""
        item = self.get_object()
        
        # Проверяем права
        if item.playlist.user != request.user:
            return Response(
                {'error': 'У вас нет прав на удаление этого элемента'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        playlist = item.playlist
        item.delete()
        
        # Обновляем позиции
        PlaylistItem.objects.filter(
            playlist=playlist, position__gt=item.position
        ).update(position=models.F('position') - 1)
        
        # Обновляем обложку
        playlist.update_cover()
        
        return Response({'message': 'Элемент удалён'}, status=status.HTTP_204_NO_CONTENT)


class PlaylistSearchView(views.APIView):
    """Поиск плейлистов"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Поиск плейлистов по названию"""
        search = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))

        if not search:
            return Response({'results': []})

        # Фильтруем плейлисты
        queryset = Playlist.objects.filter(
            Q(title__icontains=search) | Q(description__icontains=search),
            is_public=True
        ).select_related('user').prefetch_related('items__anime')

        # Ограничиваем результат
        queryset = queryset[:limit]

        # Сериализуем
        serializer = PlaylistSerializer(queryset, many=True)

        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })