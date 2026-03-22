"""
UserLibraryViewSet - полностью переработанная версия
Использует модель UserLibrary для хранения статусов аниме
"""
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone


class UserLibraryViewSet(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin):
    """Библиотека пользователя - использует модель UserLibrary
    
    Endpoints:
    - GET /api/users/library/ - список аниме в библиотеке
    - GET /api/users/library/{id}/ - информация о конкретной записи
    - PATCH /api/users/library/{id}/ - обновить статус
    - DELETE /api/users/library/{id}/ - удалить аниме из библиотеки
    - GET /api/users/library/statistics/ - статистика
    - GET /api/users/library/check_anime/ - проверить наличие аниме
    - POST /api/users/library/{id}/mark_favorite/ - добавить в избранное
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def list(self, request):
        """Получить список аниме в библиотеке пользователя"""
        from .models import UserLibrary
        
        user = request.user
        
        # Базовый queryset
        queryset = UserLibrary.objects.filter(user=user).select_related('anime')
        
        # Фильтрация по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтр по избранному
        is_favorite = request.query_params.get('is_favorite')
        if is_favorite in ('true', '1', 'True'):
            queryset = queryset.filter(is_favorite=True)
        
        # Поиск
        search = request.query_params.get('search')
        if search:
            search_lower = search.lower()
            queryset = queryset.filter(
                Q(anime__title_ru__icontains=search_lower) |
                Q(anime__title_en__icontains=search_lower)
            )
        
        # Сортировка
        ordering = request.query_params.get('ordering', '-updated_at')
        allowed_ordering = ['-updated_at', 'updated_at', '-added_at', 'added_at', '-rating', 'rating', 'current_episode']
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)
        
        results = []
        for item in queryset:
            anime = item.anime
            total_episodes = anime.episodes or 0
            
            # Получаем URL постера
            poster_url = None
            if hasattr(anime, 'poster_image_url'):
                poster_url = anime.poster_image_url
            elif anime.poster and hasattr(anime.poster, 'url'):
                poster_url = anime.poster.url
            elif anime.poster_url:
                poster_url = anime.poster_url
            
            results.append({
                'id': item.id,
                'anime': anime.id,  # ID аниме для навигации
                'anime_id': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'anime_episodes_count': total_episodes,
                'anime_status_display': anime.get_status_display() if hasattr(anime, 'get_status_display') else anime.status,
                'status': item.status,
                'current_episode': item.current_episode or 0,
                'episodes_watched': item.episodes_watched or 0,
                'progress_percentage': item.get_progress_percentage() if hasattr(item, 'get_progress_percentage') else (round((item.current_episode / total_episodes) * 100, 1) if total_episodes > 0 else 0),
                'is_favorite': item.is_favorite,
                'rating': item.rating,
                'notes': item.notes or '',
                'added_at': item.added_at.isoformat() if item.added_at else None,
                'started_at': item.started_at.isoformat() if item.started_at else None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                'rewatch_count': item.rewatch_count or 0,
            })
        
        return Response({'results': results, 'count': len(results)})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика библиотеки пользователя"""
        from .models import UserLibrary
        from django.db.models import Avg, Sum, Count
        
        user = request.user
        
        # Агрегированная статистика
        stats = UserLibrary.objects.filter(user=user).aggregate(
            total=Count('id'),
            started=Count('id', filter=Q(status='started')),
            completed=Count('id', filter=Q(status='completed')),
            on_hold=Count('id', filter=Q(status='on_hold')),
            dropped=Count('id', filter=Q(status='dropped')),
            planned=Count('id', filter=Q(status='planned')),
            favorites=Count('id', filter=Q(is_favorite=True)),
            episodes_watched=Sum('episodes_watched'),
            avg_rating=Avg('rating'),
            total_rewatches=Sum('rewatch_count'),
        )
        
        # Считаем часы просмотра (24 минуты на серию)
        episodes_watched = stats['episodes_watched'] or 0
        hours_watched = round((episodes_watched * 24) / 60, 1)
        
        # Считаем оставшееся время для аниме в процессе
        started_items = UserLibrary.objects.filter(user=user, status='started').select_related('anime')
        remaining_episodes = 0
        for item in started_items:
            if item.anime and item.anime.episodes:
                remaining_episodes += item.anime.episodes - (item.current_episode or 0)
        
        hours_remaining = round((remaining_episodes * 24) / 60, 1)
        
        return Response({
            'total': stats['total'] or 0,
            'started': stats['started'] or 0,
            'completed': stats['completed'] or 0,
            'on_hold': stats['on_hold'] or 0,
            'dropped': stats['dropped'] or 0,
            'planned': stats['planned'] or 0,
            'favorites': stats['favorites'] or 0,
            'episodes_watched': episodes_watched,
            'hours_watched': hours_watched,
            'hours_remaining': hours_remaining,
            'avg_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else None,
            'total_rewatches': stats['total_rewatches'] or 0,
        })

    @action(detail=False, methods=['get'])
    def check_anime(self, request):
        """Проверить наличие аниме в библиотеке"""
        from .models import UserLibrary
        
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        try:
            item = UserLibrary.objects.get(user=request.user, anime_id=anime_id)
            return Response({
                'in_library': True,
                'status': item.status,
                'current_episode': item.current_episode,
                'watched_episodes': item.episodes_watched,
                'is_favorite': item.is_favorite,
                'rating': item.rating,
            })
        except UserLibrary.DoesNotExist:
            return Response({'in_library': False})

    def destroy(self, request, pk=None):
        """Удалить аниме из библиотеки"""
        from .models import UserLibrary
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.get(id=pk, user=request.user)
            item.delete()
            return Response({'success': True, 'message': 'Аниме удалено из библиотеки'})
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def retrieve(self, request, pk=None):
        """Получить информацию о конкретной записи в библиотеке"""
        from .models import UserLibrary
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.select_related('anime').get(id=pk, user=request.user)
            anime = item.anime
            total_episodes = anime.episodes or 0
            
            # Получаем URL постера
            poster_url = None
            if hasattr(anime, 'poster_image_url'):
                poster_url = anime.poster_image_url
            elif anime.poster and hasattr(anime.poster, 'url'):
                poster_url = anime.poster.url
            elif anime.poster_url:
                poster_url = anime.poster_url
            
            return Response({
                'id': item.id,
                'anime': anime.id,
                'anime_id': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'anime_episodes_count': total_episodes,
                'anime_status_display': anime.get_status_display() if hasattr(anime, 'get_status_display') else anime.status,
                'status': item.status,
                'current_episode': item.current_episode or 0,
                'episodes_watched': item.episodes_watched or 0,
                'progress_percentage': item.get_progress_percentage() if hasattr(item, 'get_progress_percentage') else 0,
                'is_favorite': item.is_favorite,
                'rating': item.rating,
                'notes': item.notes or '',
                'added_at': item.added_at.isoformat() if item.added_at else None,
                'started_at': item.started_at.isoformat() if item.started_at else None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None,
                'updated_at': item.updated_at.isoformat() if item.updated_at else None,
                'rewatch_count': item.rewatch_count or 0,
            })
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def partial_update(self, request, pk=None):
        """Обновить статус аниме в библиотеке"""
        from .models import UserLibrary
        from anime.models import Anime
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.get(id=pk, user=request.user)
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)
        
        # Обновляем поля
        status = request.data.get('status')
        current_episode = request.data.get('current_episode')
        episodes_watched = request.data.get('episodes_watched')
        rating = request.data.get('rating')
        notes = request.data.get('notes')
        is_favorite = request.data.get('is_favorite')
        
        if status is not None:
            item.status = status
            if status == 'started' and not item.started_at:
                item.started_at = timezone.now()
            elif status == 'completed' and not item.completed_at:
                item.completed_at = timezone.now()
        
        if current_episode is not None:
            item.current_episode = current_episode
            item.episodes_watched = max(item.episodes_watched or 0, current_episode)
        
        if episodes_watched is not None:
            item.episodes_watched = episodes_watched
        
        if rating is not None:
            item.rating = rating if 1 <= rating <= 10 else None
        
        if notes is not None:
            item.notes = notes
        
        if is_favorite is not None:
            item.is_favorite = is_favorite
        
        item.save()
        
        # Возвращаем обновлённые данные
        return self.retrieve(request, pk)

    @action(detail=True, methods=['post'])
    def mark_favorite(self, request, pk=None):
        """Отметить/убрать из избранного"""
        from .models import UserLibrary
        
        try:
            item = UserLibrary.objects.get(id=pk, user=request.user)
            item.is_favorite = not item.is_favorite
            item.save(update_fields=['is_favorite', 'updated_at'])
            return Response({
                'is_favorite': item.is_favorite,
                'message': 'Добавлено в избранное' if item.is_favorite else 'Убрано из избранного'
            })
        except UserLibrary.DoesNotExist:
            return Response({'error': 'Запись не найдена'}, status=404)

    def create(self, request):
        """Добавить аниме в библиотеку"""
        from .models import UserLibrary
        from anime.models import Anime
        
        anime_id = request.data.get('anime')
        status = request.data.get('status', 'planned')
        current_episode = request.data.get('current_episode', 0)
        episodes_watched = request.data.get('episodes_watched', 0)
        rating = request.data.get('rating')
        notes = request.data.get('notes', '')
        
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        # Создаём или обновляем запись
        item, created = UserLibrary.objects.get_or_create(
            user=request.user,
            anime=anime,
            defaults={
                'status': status,
                'current_episode': current_episode,
                'episodes_watched': episodes_watched,
                'rating': rating,
                'notes': notes,
            }
        )
        
        if not created:
            # Обновляем существующую запись
            if status:
                item.status = status
            if current_episode:
                item.current_episode = current_episode
                item.episodes_watched = max(item.episodes_watched, current_episode)
            if episodes_watched:
                item.episodes_watched = episodes_watched
            if rating:
                item.rating = rating
            if notes:
                item.notes = notes
            item.save()
        
        # Возвращаем данные
        return Response({
            'id': item.id,
            'anime_id': anime.id,
            'status': item.status,
            'message': 'Добавлено в библиотеку' if created else 'Обновлено',
        }, status=201 if created else 200)
