from rest_framework import viewsets, filters, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q, Avg
from django.db.models import Count

from .models import DubGroup, Dub, VoiceActor, Person
from .models import DubGroupSubscription, DubGroupRating, DubGroupNews, DubGroupDiscussion, DubGroupDiscussionReply
from .serializers import (
    DubGroupSerializer, DubGroupListSerializer, DubSerializer,
    VoiceActorSerializer, AnimeDubSerializer, CreateDubSerializer, UpdateDubSerializer,
    PersonSerializer, PersonDetailSerializer,
    DubGroupRatingSerializer, DubGroupNewsSerializer, DubGroupDiscussionSerializer,
    DubGroupDiscussionReplySerializer,
)
from anime.models import Anime

class DubGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для групп озвучки"""
    
    queryset = DubGroup.objects.filter(status='active').order_by('name')
    serializer_class = DubGroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_object(self):
        """Поддержка поиска как по slug, так и по ID"""
        queryset = self.filter_queryset(self.get_queryset())
        # Получаем значение из URL - может быть pk (для DRF router) или slug
        lookup_value = self.kwargs.get('pk') or self.kwargs.get('slug')
        
        if not lookup_value:
            raise Http404
        
        # Пробуем сначала как slug
        try:
            obj = queryset.get(slug=lookup_value)
        except DubGroup.DoesNotExist:
            # Если не найден по slug, пробуем как ID
            if lookup_value.isdigit():
                try:
                    obj = queryset.get(pk=lookup_value)
                except DubGroup.DoesNotExist:
                    raise Http404
            else:
                raise Http404
        except DubGroup.MultipleObjectsReturned:
            raise Http404
        
        self.check_object_permissions(self.request, obj)
        return obj
    
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


# API для работы с озвучками из Kodik
import os
import requests
from django.conf import settings

KODIK_API_TOKEN = os.environ.get('KODIK_API_TOKEN', '74ecb013335271e4344ebc994956dd75')
KODIK_API_URL = 'https://kodik-api.com'


@api_view(['GET'])
def kodik_translation_anime(request, translation_id):
    """Получить список аниме для конкретной озвучки из Kodik API"""
    translation_id = str(translation_id)
    
    try:
        # Запрос к Kodik API для получения аниме с этой озвучкой
        params = {
            'token': KODIK_API_TOKEN,
            'translation_id': translation_id,
            'types': 'anime-serial,anime',
            'limit': 30,
        }
        
        response = requests.get(f'{KODIK_API_URL}/search', params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        
        # Форматируем ответ
        anime_list = []
        for item in results:
            anime_list.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'title_orig': item.get('title_orig'),
                'year': item.get('year'),
                'type': item.get('type'),
                'quality': item.get('quality'),
                'link': item.get('link'),
                'poster_url': item.get('material_data', {}).get('poster_url') if item.get('material_data') else None,
                'shikimori_id': item.get('shikimori_id'),
                'kinopoisk_id': item.get('kinopoisk_id'),
                'last_season': item.get('last_season'),
                'last_episode': item.get('last_episode'),
                'episodes_count': item.get('episodes_count'),
                'translation': item.get('translation'),
            })
        
        return Response({
            'count': data.get('total', len(anime_list)),
            'results': anime_list
        })
        
    except requests.RequestException as e:
        return Response({'error': str(e)}, status=500)


# ========== НОВЫЕ ВЬЮХИ ДЛЯ DUBGROUP (ПОЛНЫЙ ФУНКЦИОНАЛ КАК У STUDIO) ==========

def _get_group_by_slug_or_id(slug_or_id):
    """Получить группу по slug или ID"""
    # Пробуем сначала как slug
    try:
        return DubGroup.objects.get(slug=slug_or_id)
    except DubGroup.DoesNotExist:
        # Пробуем как ID
        if slug_or_id.isdigit():
            return DubGroup.objects.get(pk=slug_or_id)
        raise Http404


class DubGroupWorksView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/works/ - озвученные аниме группы"""
    serializer_class = DubSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        qs = group.group_dubs.filter(anime__title_ru__regex=r"[а-яёА-ЯЁ]").select_related('anime')

        # Фильтрация
        dub_type = self.request.query_params.get('dub_type', '')
        if dub_type:
            qs = qs.filter(dub_type=dub_type)

        is_complete = self.request.query_params.get('is_complete', '')
        if is_complete:
            qs = qs.filter(is_complete=is_complete.lower() == 'true')

        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(Q(anime__title_ru__icontains=search) | Q(anime__title_en__icontains=search))

        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-average_rating', 'average_rating', '-anime__year', 'anime__year']
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs


class DubGroupStaffView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/staff/ - команда группы (актёры озвучки)"""
    serializer_class = VoiceActorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        return group.voice_actors.all()


class DubGroupNewsView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/news/ - новости группы"""
    serializer_class = DubGroupNewsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        return group.news.all()


class DubGroupDiscussionsView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/discussions/ - обсуждения группы"""
    serializer_class = DubGroupDiscussionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-likes_count', '-replies_count']
        qs = group.discussions.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class DubGroupDiscussionCreateView(APIView):
    """POST /api/dubs/groups/<slug>/discussions/ - создать обсуждение"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title or not content:
            return Response({'error': 'Заголовок и содержание обязательны'}, status=400)
        disc = DubGroupDiscussion.objects.create(
            group=group,
            author=request.user,
            title=title,
            content=content,
        )
        return Response(DubGroupDiscussionSerializer(disc).data, status=201)


class DubGroupReviewsView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/reviews/ - отзывы о группе"""
    serializer_class = DubGroupRatingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-overall_rating', 'overall_rating']
        qs = group.ratings.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class DubGroupReviewCreateView(APIView):
    """POST /api/dubs/groups/<slug>/reviews/ - создать/обновить отзыв"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        data = request.data
        rating, _ = DubGroupRating.objects.update_or_create(
            user=request.user,
            group=group,
            defaults={
                'voice_quality': int(data.get('voice_quality', 5)),
                'timing': int(data.get('timing', 5)),
                'translation': int(data.get('translation', 5)),
                'consistency': int(data.get('consistency', 5)),
                'comment': data.get('comment', ''),
            }
        )
        # Пересчитываем средний рейтинг группы
        reviews_count = group.ratings.count()
        if reviews_count <= 1:
            initial = group.average_rating if group.average_rating else rating.overall_rating
            n = 10
            new_avg = (initial * n + rating.overall_rating) / (n + 1)
        else:
            avg = group.ratings.aggregate(avg=Avg('overall_rating'))['avg'] or 0
            new_avg = avg
        DubGroup.objects.filter(pk=group.pk).update(average_rating=round(new_avg, 2))
        return Response(DubGroupRatingSerializer(rating).data, status=201)


class DubGroupSubscribeView(APIView):
    """POST/DELETE /api/dubs/groups/<slug>/subscribe/ - подписка"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        sub, created = DubGroupSubscription.objects.get_or_create(user=request.user, group=group)
        if created:
            DubGroup.objects.filter(pk=group.pk).update(subscribers_count=group.subscriptions.count())
        return Response({'subscribed': True, 'subscribers_count': group.subscriptions.count()})

    def delete(self, request, slug):
        group = _get_group_by_slug_or_id(slug)
        DubGroupSubscription.objects.filter(user=request.user, group=group).delete()
        DubGroup.objects.filter(pk=group.pk).update(subscribers_count=group.subscriptions.count())
        return Response({'subscribed': False, 'subscribers_count': group.subscriptions.count()})


class DubGroupSimilarView(generics.ListAPIView):
    """GET /api/dubs/groups/<slug>/similar/ - похожие группы (по жанрам и типу перевода)"""
    serializer_class = DubGroupListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = _get_group_by_slug_or_id(self.kwargs['slug'])

        # Похожие группы: тот же тип перевода + пересечение жанров
        my_genres = set((group.genre_stats or {}).keys())

        candidates = DubGroup.objects.filter(
            status='active'
        ).exclude(pk=group.pk)

        scored = []
        for g in candidates:
            score = 0
            # Совпадение типа перевода - большой бонус
            if g.translation_type == group.translation_type:
                score += 3
            # Пересечение жанров
            other_genres = set((g.genre_stats or {}).keys())
            if my_genres and other_genres:
                intersection = my_genres & other_genres
                union = my_genres | other_genres
                jaccard = len(intersection) / len(union) if union else 0
                score += jaccard * 5
            # Близкий рейтинг
            if group.average_rating and g.average_rating:
                rating_diff = abs(group.average_rating - g.average_rating)
                if rating_diff < 1.0:
                    score += 1
            scored.append((score, g))

        scored.sort(key=lambda x: (-x[0], -x[1].average_rating))
        return [s for _, s in scored[:8]]


class DubGroupDiscussionRepliesView(APIView):
    """GET/POST /api/dubs/groups/<slug>/discussions/<id>/replies/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        replies = disc.replies.all().select_related('author')
        data = []
        for r in replies:
            avatar = None
            if hasattr(r.author, 'avatar') and r.author.avatar:
                avatar = r.author.avatar.url
            data.append({
                'id': r.id,
                'author_name': r.author.username,
                'author_avatar': avatar,
                'content': r.content,
                'created_at': r.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Содержание обязательно'}, status=400)
        reply = DubGroupDiscussionReply.objects.create(
            discussion=disc,
            author=request.user,
            content=content,
        )
        from django.utils import timezone
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(
            replies_count=disc.replies.count(),
            last_reply_at=timezone.now()
        )
        avatar = None
        if hasattr(reply.author, 'avatar') and reply.author.avatar:
            avatar = reply.author.avatar.url
        return Response({
            'id': reply.id,
            'author_name': reply.author.username,
            'author_avatar': avatar,
            'content': reply.content,
            'created_at': reply.created_at.isoformat(),
        }, status=201)


def _dub_group_safe_increment(val):
    return (val or 0) + 1


class DubGroupDiscussionLikeView(APIView):
    """POST /api/dubs/groups/<slug>/discussions/<id>/like/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        disc.likes_count = _dub_group_safe_increment(disc.likes_count)
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(likes_count=disc.likes_count)
        return Response({'likes_count': disc.likes_count})


class DubGroupDiscussionDislikeView(APIView):
    """POST /api/dubs/groups/<slug>/discussions/<id>/dislike/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        group = _get_group_by_slug_or_id(slug)
        disc = get_object_or_404(DubGroupDiscussion, id=discussion_id, group=group)
        disc.dislikes_count = _dub_group_safe_increment(disc.dislikes_count)
        DubGroupDiscussion.objects.filter(pk=disc.pk).update(dislikes_count=disc.dislikes_count)
        return Response({'dislikes_count': disc.dislikes_count})


@api_view(['GET'])
def kodik_translation_detail(request, translation_id):
    """Получить информацию об озвучке из Kodik API"""
    translation_id = str(translation_id)
    
    try:
        # Сначала получаем информацию об озвучке
        params = {
            'token': KODIK_API_TOKEN,
        }
        
        response = requests.get(f'{KODIK_API_URL}/translations', params=params, timeout=10)
        response.raise_for_status()
        translations = response.json()
        
        # Ищем нужную озвучку
        translation = None
        for t in translations:
            if str(t.get('id')) == translation_id:
                translation = t
                break
        
        if not translation:
            return Response({'error': 'Translation not found'}, status=404)
        
        # Получаем аниме для этой озвучки
        anime_params = {
            'token': KODIK_API_TOKEN,
            'translation_id': translation_id,
            'types': 'anime-serial,anime',
            'limit': 30,
        }
        
        anime_response = requests.get(f'{KODIK_API_URL}/search', params=anime_params, timeout=10)
        anime_data = anime_response.json()
        
        return Response({
            'id': translation.get('id'),
            'title': translation.get('title'),
            'type': translation.get('type'),
            'anime_count': anime_data.get('total', 0),
            'anime': anime_data.get('results', [])[:10],  # Первые 10 аниме для превью
        })
        
    except requests.RequestException as e:
        return Response({'error': str(e)}, status=500)