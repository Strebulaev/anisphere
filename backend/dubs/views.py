from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import DubGroup, Dub, VoiceActor, Person
from .serializers import (
    DubGroupSerializer, DubSerializer,
    VoiceActorSerializer, AnimeDubSerializer, CreateDubSerializer, UpdateDubSerializer,
    PersonSerializer, PersonDetailSerializer
)
from anime.models import Anime

class DubGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для групп озвучки"""
    
    queryset = DubGroup.objects.filter(status='active').order_by('name')
    serializer_class = DubGroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def dubs(self, request, pk=None):
        """Получить все озвучки группы"""
        group = self.get_object()
        dubs = group.dubs.all().select_related('anime')
        
        # Пагинация
        page = self.paginate_queryset(dubs)
        if page is not None:
            serializer = DubSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DubSerializer(dubs, many=True)
        return Response(serializer.data)


class DubViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для озвучек"""
    
    queryset = Dub.objects.all().select_related('group', 'anime')
    serializer_class = DubSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['group', 'anime', 'dub_type', 'is_complete']
    
    @action(detail=False, methods=['get'])
    def by_anime(self, request):
        """Получить все озвучки для конкретного аниме"""
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'anime_id parameter is required'}, status=400)
        
        anime = get_object_or_404(Anime, id=anime_id)
        dubs = self.queryset.filter(anime=anime)
        
        # Сортировка: сначала полные озвучки, потом по рейтингу
        dubs = dubs.order_by('-is_complete', '-average_rating')
        
        serializer = AnimeDubSerializer(dubs, many=True)
        return Response(serializer.data)


class VoiceActorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для актёров озвучки"""
    
    queryset = VoiceActor.objects.all().order_by('name')
    serializer_class = VoiceActorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']


# API функции для получения озвучек аниме
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET', 'POST'])
def anime_dubs(request, anime_id):
    """Получить все озвучки для аниме или создать новую"""
    anime = get_object_or_404(Anime, id=anime_id)

    if request.method == 'GET':
        dubs = Dub.objects.filter(anime=anime).select_related('group').order_by('-average_rating')
        serializer = AnimeDubSerializer(dubs, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CreateDubSerializer(data=request.data, context={'anime': anime, 'user': request.user})
        if serializer.is_valid():
            dub = serializer.save()
            # Возвращаем созданную озвучку в полном формате
            response_serializer = AnimeDubSerializer(dub)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def dub_detail(request, dub_id):
    """Получить, обновить или удалить озвучку"""
    dub = get_object_or_404(Dub.objects.select_related('group', 'anime'), id=dub_id)

    # Проверяем права доступа для изменения
    if request.method in ['PUT', 'PATCH', 'DELETE']:
        # Проверяем аутентификацию пользователя
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Необходимо авторизоваться для изменения озвучки'}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем, что пользователь является создателем озвучки
        try:
            if not hasattr(dub, 'created_by') or not dub.created_by or dub.created_by != request.user:
                return Response({'error': 'У вас нет прав на изменение этой озвучки'}, status=status.HTTP_403_FORBIDDEN)
        except:
            # Если поле created_by ещё не существует в БД, разрешаем изменение для обратной совместимости
            pass

    if request.method == 'GET':
        serializer = AnimeDubSerializer(dub)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        # Для обновления используем специальный сериализатор
        serializer = UpdateDubSerializer(dub, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            updated_dub = serializer.save()
            response_serializer = AnimeDubSerializer(updated_dub)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        dub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def popular_dub_groups(request):
    """Получить популярные группы озвучки"""
    groups = DubGroup.objects.filter(status='active').order_by('-works_count')[:10]
    serializer = DubGroupSerializer(groups, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def anime_dub_groups(request, anime_id):
    """Получить группы озвучки для аниме с информацией о наличии озвучки"""
    anime = get_object_or_404(Anime, id=anime_id)

    # Получаем существующие озвучки для этого аниме
    # Используем defer чтобы избежать проблем с created_by полем, которого нет в БД
    existing_dubs = Dub.objects.filter(anime=anime).select_related('group').defer('created_by').order_by('-average_rating')

    # Формируем ответ только для групп, у которых есть озвучки
    result = []
    for dub in existing_dubs:
        group_data = DubGroupSerializer(dub.group).data
        group_data['has_dub'] = True
        # Создаём копию dub без created_by для сериализации
        dub_copy = dub
        dub_data = {
            'id': dub.id,
            'group': {
                'id': dub.group.id,
                'name': dub.group.name,
                'slug': dub.group.slug,
                'logo_url': dub.group.logo_url
            },
            'dub_type': dub.dub_type,
            'dub_type_display': dub.get_dub_type_display(),
            'quality': dub.quality,
            'episodes_done': dub.episodes_done,
            'total_episodes': dub.total_episodes,
            'is_complete': dub.is_complete,
            'average_rating': dub.average_rating,
            'ratings_count': dub.ratings_count,
            'external_url': dub.external_url,
            'created_by': None  # Временно None пока поле не добавлено в БД
        }
        group_data['dub_info'] = dub_data
        result.append(group_data)

    return Response(result)


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для персон (сейю, режиссёры и т.д.)"""
    
    queryset = Person.objects.all().order_by('name')
    serializer_class = PersonSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'name_jp']
    filterset_fields = ['roles']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PersonDetailSerializer
        return PersonSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по роли
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(roles__contains=[role])
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def anime(self, request, pk=None):
        """Получить аниме с участием персоны"""
        person = self.get_object()
        anime_list = person.related_anime.all()
        
        # Пагинация
        from anime.serializers import AnimeSerializer
        page = self.paginate_queryset(anime_list)
        if page is not None:
            serializer = AnimeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AnimeSerializer(anime_list, many=True)
        return Response(serializer.data)