from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count

from .models import Studio, StudioAnime, StudioSubscription, StudioRating, StudioNews, StudioAward, StudioDiscussion, StudioDiscussionReply, StudioStaff
from .serializers import (
    StudioListSerializer, StudioDetailSerializer, StudioAnimeSerializer,
    StudioStaffSerializer, StudioNewsSerializer, StudioAwardSerializer,
    StudioDiscussionSerializer, StudioRatingSerializer,
)


class StudioListView(generics.ListAPIView):
    """GET /api/studios/ — список студий с фильтрацией и поиском"""
    serializer_class = StudioListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Studio.objects.filter(is_active=True)

        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(name_jp__icontains=search))

        country = self.request.query_params.get('country', '')
        if country:
            qs = qs.filter(country__icontains=country)

        founded_year = self.request.query_params.get('founded_year', '')
        if founded_year:
            qs = qs.filter(founded_year=founded_year)

        min_rating = self.request.query_params.get('min_rating', '')
        if min_rating:
            try:
                qs = qs.filter(average_rating__gte=float(min_rating))
            except ValueError:
                pass

        ordering = self.request.query_params.get('ordering', '-average_rating')
        allowed_orderings = [
            'average_rating', '-average_rating',
            'total_anime', '-total_anime',
            'subscribers_count', '-subscribers_count',
            'founded_year', '-founded_year',
            'name', '-name',
        ]
        if ordering in allowed_orderings:
            qs = qs.order_by(ordering)

        return qs


class StudioPopularView(generics.ListAPIView):
    """GET /api/studios/popular/ — топ студий для карусели"""
    serializer_class = StudioListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Studio.objects.filter(is_active=True).order_by('-subscribers_count', '-average_rating')[:10]


class StudioDetailView(generics.RetrieveAPIView):
    """GET /api/studios/<slug>/ — детали студии"""
    serializer_class = StudioDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Studio.objects.filter(is_active=True)


class StudioDetailByIdView(generics.RetrieveAPIView):
    """GET /api/studios/id/<id>/ — детали студии по ID"""
    serializer_class = StudioDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Studio.objects.filter(is_active=True)


class StudioWorksView(generics.ListAPIView):
    """GET /api/studios/<slug>/works/ — аниме студии"""
    serializer_class = StudioAnimeSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Отключаем пагинацию: дедупликация должна работать до срезки, а не после

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        qs = studio.studio_anime.all()

        kind = self.request.query_params.get('kind', '')
        if kind:
            qs = qs.filter(anime_kind=kind)

        year = self.request.query_params.get('year', '')
        if year:
            qs = qs.filter(anime_year=year)

        status_param = self.request.query_params.get('status', '')
        if status_param:
            qs = qs.filter(anime_status__icontains=status_param)

        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(anime_title__icontains=search) |
                Q(anime_title_en__icontains=search)
            )

        ordering = self.request.query_params.get('ordering', '-anime_year')
        allowed = [
            '-anime_year', 'anime_year', '-anime_score', 'anime_score',
            'anime_title', '-anime_title',
        ]
        if ordering in allowed:
            qs = qs.order_by(ordering)

        # Дедупликация (MySQL-совместимая):
        # Одно аниме может быть импортировано несколько раз с разными kodik_id (разные озвучки).
        # Правило: один shikimori_id = одно аниме.
        from django.db.models import Max, Case, When, IntegerField

        # Для записей с shikimori_id: предпочитаем запись с anime_db_id, иначе с макс. id
        shiki_qs = qs.filter(shikimori_id__gt='').annotate(
            has_db=Case(
                When(anime_db_id__isnull=False, then=1),
                default=0,
                output_field=IntegerField(),
            )
        )
        # Группируем в Python: для каждого shikimori_id берём лучшую запись
        shiki_map: dict[str, tuple[int, int, int]] = {}  # shiki_id -> (id, has_db, rec_id)
        for rec in shiki_qs.values('id', 'shikimori_id', 'has_db'):
            sid = rec['shikimori_id']
            if sid not in shiki_map:
                shiki_map[sid] = (rec['has_db'], rec['id'])
            else:
                prev_has_db, prev_id = shiki_map[sid]
                # Предпочтеем: есть anime_db_id > нет, затем по макс. id
                if rec['has_db'] > prev_has_db or (rec['has_db'] == prev_has_db and rec['id'] > prev_id):
                    shiki_map[sid] = (rec['has_db'], rec['id'])
        shiki_best_ids = [v[1] for v in shiki_map.values()]

        # Для записей без shikimori_id: дедупл. по (anime_title, anime_year)
        no_shiki_map: dict[tuple, tuple[int, int]] = {}  # (title,year) -> (has_db, id)
        for rec in qs.filter(shikimori_id='').annotate(
            has_db=Case(
                When(anime_db_id__isnull=False, then=1),
                default=0, output_field=IntegerField(),
            )
        ).values('id', 'anime_title', 'anime_year', 'has_db'):
            key = (rec['anime_title'], rec['anime_year'])
            if key not in no_shiki_map:
                no_shiki_map[key] = (rec['has_db'], rec['id'])
            else:
                prev_has_db, prev_id = no_shiki_map[key]
                if rec['has_db'] > prev_has_db or (rec['has_db'] == prev_has_db and rec['id'] > prev_id):
                    no_shiki_map[key] = (rec['has_db'], rec['id'])
        no_shiki_best_ids = [v[1] for v in no_shiki_map.values()]

        qs = qs.filter(id__in=shiki_best_ids + no_shiki_best_ids)
        return qs


class StudioStaffView(generics.ListAPIView):
    """GET /api/studios/<slug>/staff/ — команда студии"""
    serializer_class = StudioStaffSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        role = self.request.query_params.get('role', '')
        qs = studio.staff.all()
        if role:
            qs = qs.filter(role=role)
        return qs


class StudioNewsView(generics.ListAPIView):
    """GET /api/studios/<slug>/news/ — новости студии"""
    serializer_class = StudioNewsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        return studio.news.all()


class StudioAwardsView(generics.ListAPIView):
    """GET /api/studios/<slug>/awards/ — награды студии"""
    serializer_class = StudioAwardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        return studio.awards.all()


class StudioDiscussionsView(generics.ListAPIView):
    """GET /api/studios/<slug>/discussions/ — обсуждения студии"""
    serializer_class = StudioDiscussionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-likes_count', '-replies_count']
        qs = studio.discussions.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class StudioDiscussionCreateView(APIView):
    """POST /api/studios/<slug>/discussions/ — создать обсуждение"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        studio = get_object_or_404(Studio, slug=slug)
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title or not content:
            return Response({'error': 'Заголовок и содержание обязательны'}, status=400)
        disc = StudioDiscussion.objects.create(
            studio=studio,
            author=request.user,
            title=title,
            content=content,
        )
        return Response(StudioDiscussionSerializer(disc).data, status=201)


class StudioReviewsView(generics.ListAPIView):
    """GET /api/studios/<slug>/reviews/ — отзывы о студии"""
    serializer_class = StudioRatingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['-created_at', 'created_at', '-overall_rating', 'overall_rating']
        qs = studio.ratings.all()
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs


class StudioReviewCreateView(APIView):
    """POST /api/studios/<slug>/reviews/ — создать/обновить отзыв"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        studio = get_object_or_404(Studio, slug=slug)
        data = request.data
        rating, _ = StudioRating.objects.update_or_create(
            user=request.user,
            studio=studio,
            defaults={
                'animation_quality': int(data.get('animation_quality', 5)),
                'directing': int(data.get('directing', 5)),
                'soundtrack': int(data.get('soundtrack', 5)),
                'adaptation': int(data.get('adaptation', 5)),
                'comment': data.get('comment', ''),
            }
        )
        # Пересчитываем средний рейтинг студии по взвешенной формуле:
        # new_avg = (initial_rating * n + user_rating) / (n + 1)
        # где n = количество отзывов ДО текущего (т.е. теперь reviews_count - 1)
        # Это защищает от резких изменений рейтинга при малом числе голосов.
        reviews_count = studio.ratings.count()  # уже включает текущий отзыв
        if reviews_count <= 1:
            # Первый отзыв: берём среднее между базовым рейтингом и оценкой пользователя
            initial = studio.average_rating if studio.average_rating else rating.overall_rating
            n = 10  # «вес» начального рейтинга
            new_avg = (initial * n + rating.overall_rating) / (n + 1)
        else:
            # Уже есть отзывы — считаем честное среднее по всем отзывам
            avg = studio.ratings.aggregate(avg=Avg('overall_rating'))['avg'] or 0
            new_avg = avg
        Studio.objects.filter(pk=studio.pk).update(average_rating=round(new_avg, 2))
        return Response(StudioRatingSerializer(rating).data, status=201)


class StudioSubscribeView(APIView):
    """POST/DELETE /api/studios/<slug>/subscribe/ — подписка"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug):
        studio = get_object_or_404(Studio, slug=slug)
        sub, created = StudioSubscription.objects.get_or_create(user=request.user, studio=studio)
        if created:
            Studio.objects.filter(pk=studio.pk).update(subscribers_count=studio.subscriptions.count())
        return Response({'subscribed': True, 'subscribers_count': studio.subscriptions.count()})

    def delete(self, request, slug):
        studio = get_object_or_404(Studio, slug=slug)
        StudioSubscription.objects.filter(user=request.user, studio=studio).delete()
        Studio.objects.filter(pk=studio.pk).update(subscribers_count=studio.subscriptions.count())
        return Response({'subscribed': False, 'subscribers_count': studio.subscriptions.count()})


class StudioSimilarView(generics.ListAPIView):
    """GET /api/studios/<slug>/similar/ — похожие студии (по жанрам и стране)"""
    serializer_class = StudioListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        studio = get_object_or_404(Studio, slug=self.kwargs['slug'])

        # Получаем жанры текущей студии из genre_stats
        my_genres = set((studio.genre_stats or {}).keys())

        candidates = Studio.objects.filter(
            is_active=True
        ).exclude(pk=studio.pk)

        # Считаем score похожести для каждой студии
        scored = []
        for s in candidates:
            score = 0
            # Совпадение страны — большой бонус
            if s.country == studio.country:
                score += 3
            # Пересечение жанров
            other_genres = set((s.genre_stats or {}).keys())
            if my_genres and other_genres:
                intersection = my_genres & other_genres
                union = my_genres | other_genres
                jaccard = len(intersection) / len(union) if union else 0
                score += jaccard * 5  # до 5 баллов за жанры
            # Небольшой бонус за близкий рейтинг
            if studio.average_rating and s.average_rating:
                rating_diff = abs(studio.average_rating - s.average_rating)
                if rating_diff < 1.0:
                    score += 1
            scored.append((score, s))

        # Сортируем по убыванию похожести, потом по рейтингу
        scored.sort(key=lambda x: (-x[0], -x[1].average_rating))
        return [s for _, s in scored[:8]]


class StudioDiscussionRepliesView(APIView):
    """GET/POST /api/studios/<slug>/discussions/<id>/replies/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, slug, discussion_id):
        disc = get_object_or_404(StudioDiscussion, id=discussion_id, studio__slug=slug)
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
        disc = get_object_or_404(StudioDiscussion, id=discussion_id, studio__slug=slug)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Содержание обязательно'}, status=400)
        reply = StudioDiscussionReply.objects.create(
            discussion=disc,
            author=request.user,
            content=content,
        )
        # Обновляем счётчик ответов и время последнего ответа
        from django.utils import timezone
        StudioDiscussion.objects.filter(pk=disc.pk).update(
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


class StudioDiscussionLikeView(APIView):
    """POST /api/studios/<slug>/discussions/<id>/like/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        disc = get_object_or_404(StudioDiscussion, id=discussion_id, studio__slug=slug)
        disc.likes_count = Q_safe_increment(disc.likes_count)
        StudioDiscussion.objects.filter(pk=disc.pk).update(likes_count=disc.likes_count)
        return Response({'likes_count': disc.likes_count})


class StudioDiscussionDislikeView(APIView):
    """POST /api/studios/<slug>/discussions/<id>/dislike/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, slug, discussion_id):
        disc = get_object_or_404(StudioDiscussion, id=discussion_id, studio__slug=slug)
        disc.dislikes_count = Q_safe_increment(disc.dislikes_count)
        StudioDiscussion.objects.filter(pk=disc.pk).update(dislikes_count=disc.dislikes_count)
        return Response({'dislikes_count': disc.dislikes_count})


def Q_safe_increment(val):
    return (val or 0) + 1


class StudioSyncFromAnimeView(APIView):
    """POST /api/studios/sync/ — синхронизировать студии из таблицы аниме"""
    permission_classes = [AllowAny]  # В проде поставить IsAdminUser

    def post(self, request):
        from anime.models import Anime as AnimeModel
        import re

        created = 0
        updated = 0

        # Собираем все уникальные студии из JSON поля anime.studios
        studio_anime_map = {}  # {studio_name: [anime_obj, ...]}

        for anime in AnimeModel.objects.all():
            studios_data = anime.studios or []
            for s in studios_data:
                name = s if isinstance(s, str) else s.get('name', '')
                if not name:
                    continue
                if name not in studio_anime_map:
                    studio_anime_map[name] = []
                studio_anime_map[name].append(anime)

        for studio_name, anime_list in studio_anime_map.items():
            studio, was_created = Studio.objects.get_or_create(name=studio_name)
            if was_created:
                created += 1

            # Обновляем статистику
            tv = sum(1 for a in anime_list if a.kind == 'tv')
            movies = sum(1 for a in anime_list if a.kind == 'movie')
            ovas = sum(1 for a in anime_list if a.kind in ('ova', 'ona'))
            scores = [a.score for a in anime_list if a.score]
            avg = round(sum(scores) / len(scores), 2) if scores else 0.0

            studio.total_anime = len(anime_list)
            studio.tv_count = tv
            studio.movie_count = movies
            studio.ova_count = ovas
            studio.average_rating = avg

            # Известные работы — топ-5 по рейтингу
            top = sorted(anime_list, key=lambda a: a.score or 0, reverse=True)[:5]
            studio.notable_works = [a.title_ru for a in top]
            studio.save()

            # Обновляем StudioAnime
            for anime in anime_list:
                poster = ''
                if anime.poster:
                    poster = anime.poster.url
                elif anime.poster_url:
                    poster = anime.poster_url
                StudioAnime.objects.update_or_create(
                    studio=studio,
                    kodik_id=f'local-{anime.pk}',
                    defaults={
                        'anime_db_id': anime.pk,
                        'anime_title': anime.title_ru or '',
                        'anime_kind': anime.kind or 'tv',
                        'anime_year': anime.year,
                        'anime_score': anime.score,
                        'anime_poster': poster,
                    }
                )
            updated += 1

        return Response({
            'message': f'Синхронизация завершена. Создано: {created}, обновлено: {updated}',
            'total_studios': Studio.objects.count(),
        })
