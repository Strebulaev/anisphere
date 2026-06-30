"""
UserLibraryViewSet - полностью переработанная версия
Использует модель UserLibrary для хранения статусов аниме
"""
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFavoritesViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin):
    """Избранное аниме пользователя
    
    Endpoints:
    - GET /api/users/favorites/ - список избранного аниме
    - POST /api/users/favorites/ - добавить в избранное
    - DELETE /api/users/favorites/ - удалить из избранного
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def list(self, request):
        """Получить список избранного аниме"""
        from .models import UserFavorite
        
        # Поддержка просмотра избранного другого пользователя
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)
        else:
            target_user = request.user
        
        queryset = UserFavorite.objects.filter(user=target_user).select_related('anime')
        
        results = []
        for item in queryset:
            anime = item.anime
            # Получаем URL постера - приори тет: локальный файл -> внешний URL
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_id': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'anime_episodes': anime.episodes or 0,
                'anime_kind': anime.kind or '',
                'anime_year': anime.year,
                'added_at': item.added_at.isoformat() if item.added_at else None,
            })
        
        return Response({'results': results, 'count': len(results)})

    def create(self, request):
        """Добавить аниме в избранное"""
        from .models import UserFavorite
        from anime.models import Anime
        
        anime_id = request.data.get('anime')
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        # Проверяем, не добавлено ли уже
        existing = UserFavorite.objects.filter(user=request.user, anime=anime).first()
        if existing:
            return Response({'error': 'Уже в избранном', 'id': existing.id}, status=400)
        
        favorite = UserFavorite.objects.create(user=request.user, anime=anime)
        
        return Response({
            'id': favorite.id,
            'anime': anime.id,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        """Удалить аниме из избранного"""
        from .models import UserFavorite
        
        if pk:
            # Удалить по ID записи
            try:
                item = UserFavorite.objects.get(id=pk, user=request.user)
                item.delete()
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except UserFavorite.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            # Удалить по anime_id
            anime_id = request.data.get('anime')
            if not anime_id:
                return Response({'error': 'anime_id required'}, status=400)
            
            deleted, _ = UserFavorite.objects.filter(user=request.user, anime_id=anime_id).delete()
            if deleted:
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


class FavoriteThemesViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.DestroyModelMixin):
    """Избранные опенинги/эндинги пользователя
    
    Endpoints:
    - GET /api/users/favorite_themes/ - список избранных тем
    - POST /api/users/favorite_themes/ - добавить в избранное
    - DELETE /api/users/favorite_themes/ - удалить из избранного
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить список избранных опенингов/эндингов"""
        from .models import FavoriteTheme
        
        queryset = FavoriteTheme.objects.filter(user=request.user).select_related('anime')
        
        results = []
        for item in queryset:
            anime = item.anime
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'theme_type': item.theme_type,
                'theme_type_display': item.get_theme_type_display(),
                'episode': item.episode,
                'season': item.season,
                'title': item.title or '',
                'start_time': item.start_time,
                'end_time': item.end_time,
                'added_at': item.added_at.isoformat() if item.added_at else None,
            })
        
        return Response({'results': results, 'count': len(results)})

    def create(self, request):
        """Добавить опенинг/эндинг в избранное"""
        from .models import FavoriteTheme
        from anime.models import Anime
        
        anime_id = request.data.get('anime')
        theme_type = request.data.get('theme_type')  # 'opening' или 'ending'
        episode = request.data.get('episode', 1)
        season = request.data.get('season', 1)
        title = request.data.get('title', '')
        start_time = request.data.get('start_time', 0)
        end_time = request.data.get('end_time')
        
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        if theme_type not in ('opening', 'ending'):
            return Response({'error': 'theme_type must be opening or ending'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        # Проверяем, не добавлено ли уже
        existing = FavoriteTheme.objects.filter(
            user=request.user, anime=anime, 
            theme_type=theme_type, episode=episode, season=season
        ).first()
        
        if existing:
            return Response({'error': 'Уже в избранном', 'id': existing.id}, status=400)
        
        theme = FavoriteTheme.objects.create(
            user=request.user,
            anime=anime,
            theme_type=theme_type,
            episode=episode,
            season=season,
            title=title,
            start_time=start_time,
            end_time=end_time,
        )
        
        return Response({
            'id': theme.id,
            'anime': anime.id,
            'theme_type': theme.theme_type,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        """Удалить из избранного"""
        from .models import FavoriteTheme
        
        if pk:
            try:
                item = FavoriteTheme.objects.get(id=pk, user=request.user)
                item.delete()
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except FavoriteTheme.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            # Удалить по параметрам
            anime_id = request.data.get('anime')
            theme_type = request.data.get('theme_type')
            episode = request.data.get('episode')
            season = request.data.get('season', 1)
            
            if not anime_id or not theme_type or not episode:
                return Response({'error': 'anime, theme_type, episode required'}, status=400)
            
            deleted, _ = FavoriteTheme.objects.filter(
                user=request.user, anime_id=anime_id,
                theme_type=theme_type, episode=episode, season=season
            ).delete()
            
            if deleted:
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


class FavoriteEpisodesViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.DestroyModelMixin):
    """Избранные серии пользователя
    
    Endpoints:
    - GET /api/users/favorite_episodes/ - список избранных серий
    - POST /api/users/favorite_episodes/ - добавить в избранное
    - DELETE /api/users/favorite_episodes/ - удалить из избранного
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить список избранных серий"""
        from .models import FavoriteEpisode
        
        queryset = FavoriteEpisode.objects.filter(user=request.user).select_related('anime')
        
        results = []
        for item in queryset:
            anime = item.anime
            # Получаем URL постера - приоритет: локальный файл -> внешний URL
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
            results.append({
                'id': item.id,
                'anime': anime.id,
                'anime_title_ru': anime.title_ru or '',
                'anime_title_en': anime.title_en or '',
                'anime_poster': poster_url,
                'episode': item.episode,
                'season': item.season,
                'note': item.note or '',
                'added_at': item.added_at.isoformat() if item.added_at else None,
            })
        
        return Response({'results': results, 'count': len(results)})

    def create(self, request):
        """Добавить серию в избранное"""
        from .models import FavoriteEpisode
        from anime.models import Anime
        
        anime_id = request.data.get('anime')
        episode = request.data.get('episode', 1)
        season = request.data.get('season', 1)
        note = request.data.get('note', '')
        
        if not anime_id:
            return Response({'error': 'anime is required'}, status=400)
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response({'error': 'Аниме не найдено'}, status=404)
        
        # Проверяем, не добавлено ли уже
        existing = FavoriteEpisode.objects.filter(
            user=request.user, anime=anime,
            episode=episode, season=season
        ).first()
        
        if existing:
            return Response({'error': 'Уже в избранном', 'id': existing.id}, status=400)
        
        fav_episode = FavoriteEpisode.objects.create(
            user=request.user,
            anime=anime,
            episode=episode,
            season=season,
            note=note,
        )
        
        return Response({
            'id': fav_episode.id,
            'anime': anime.id,
            'episode': episode,
            'message': 'Добавлено в избранное',
        }, status=201)

    def destroy(self, request, pk=None):
        """Удалить из избранного"""
        from .models import FavoriteEpisode
        
        if pk:
            try:
                item = FavoriteEpisode.objects.get(id=pk, user=request.user)
                item.delete()
                return Response({'success': True, 'message': 'Удалено из избранного'})
            except FavoriteEpisode.DoesNotExist:
                return Response({'error': 'Запись не найдена'}, status=404)
        else:
            anime_id = request.data.get('anime')
            episode = request.data.get('episode')
            season = request.data.get('season', 1)
            
            if not anime_id or not episode:
                return Response({'error': 'anime, episode required'}, status=400)
            
            deleted, _ = FavoriteEpisode.objects.filter(
                user=request.user, anime_id=anime_id,
                episode=episode, season=season
            ).delete()
            
            if deleted:
                return Response({'success': True, 'message': 'Удалено из избранного'})
            return Response({'error': 'Запись не найдена'}, status=404)


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

    def get_permissions(self):
        """Разрешаем чтение всем, изменение только владельцу"""
        if self.action in ['list', 'retrieve', 'statistics']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        """Получить список аниме в библиотеке пользователя"""
        from .models import UserLibrary
        
        user_id = request.query_params.get('user_id')
        target_user = request.user
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)

        # Базовый queryset - только с существующим anime
        queryset = UserLibrary.objects.filter(
            user=target_user,
            anime__isnull=False
        ).select_related('anime')
        
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
            if not anime:
                continue
            total_episodes = anime.episodes or 0
            
            # Получаем URL постера - приоритет: локальный файл -> внешний URL
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
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
        import logging
        logger = logging.getLogger(__name__)
        
        from .models import UserLibrary
        from django.db.models import Avg, Sum, Count
        
        # Разрешаем просмотр статистики другого пользователя
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=404)
        else:
            user = request.user
        
        # Если пользователь не авторизован и нет user_id - ошибка
        if not user or (not user.is_authenticated and not user_id):
            return Response({'error': 'Требуется авторизация'}, status=401)
        
        # Агрегированная статистика - считаем по current_episode
        all_items = UserLibrary.objects.filter(
            user=user, 
            anime__isnull=False
        ).select_related('anime').only(
            'id', 'status', 'current_episode', 'episodes_watched',
            'anime__id', 'anime__episodes', 'anime__episode_duration', 'anime__kind'
        )
        
        total = 0
        started = 0
        completed = 0
        on_hold = 0
        dropped = 0
        planned = 0
        favorites = 0
        total_episodes_watched = 0
        total_minutes_watched = 0
        remaining_minutes = 0
        
        for item in all_items:
            total += 1
            
            # Считаем по статусу
            if item.status == 'started':
                started += 1
            elif item.status == 'completed':
                completed += 1
            elif item.status == 'on_hold':
                on_hold += 1
            elif item.status == 'dropped':
                dropped += 1
            elif item.status == 'planned':
                planned += 1
            
            if item.is_favorite:
                favorites += 1
            
            # Считаем просмотренные эпизоды и минуты
            try:
                anime = item.anime
                if not anime:
                    continue
                    
                # Длительность эпизода
                if anime.episode_duration:
                    episode_duration = anime.episode_duration
                else:
                    # Дефолт: 24 минуты для сериалов, 60 для фильмов
                    episode_duration = 60 if anime.kind == 'movie' else 24
                
                # Определяем сколько эпизодов просмотрено
                if item.status == 'completed':
                    # Если завершено - считаем ВСЕ эпизоды
                    watched_eps = anime.episodes or 0
                else:
                    # Иначе - текущий прогресс
                    watched_eps = item.current_episode or 0
                
                total_episodes_watched += watched_eps
                
                # Считаем минуты только для started и completed
                if item.status in ('started', 'completed') and watched_eps > 0:
                    total_minutes_watched += watched_eps * episode_duration
                
                # Оставшееся время для started
                if item.status == 'started' and anime.episodes and anime.episodes > 0:
                    remaining_eps = anime.episodes - watched_eps
                    if remaining_eps > 0:
                        remaining_minutes += remaining_eps * episode_duration
                        
            except Exception as e:
                logger.warning(f"Error processing item {item.id}: {e}")
                continue
        
        hours_watched = round(total_minutes_watched / 60, 1)
        hours_remaining = round(remaining_minutes / 60, 1)
        
        return Response({
            'total': total,
            'started': started,
            'completed': completed,
            'on_hold': on_hold,
            'dropped': dropped,
            'planned': planned,
            'favorites': favorites,
            'episodes_watched': total_episodes_watched,
            'hours_watched': hours_watched,
            'hours_remaining': hours_remaining,
            'avg_rating': None,
            'total_rewatches': 0,
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
            item = UserLibrary.objects.get(id=pk)
            # Проверяем права - только владелец может удалять
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
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
            # Разрешаем просмотр чужих записей
            item = UserLibrary.objects.select_related('anime').get(id=pk)
            
            # Проверяем права - только владелец может видеть полную информацию
            if item.user != request.user:
                # Для чужих профилей возвращаем ограниченную информацию
                anime = item.anime
                total_episodes = anime.episodes or 0
                
                poster_url = None
                try:
                    if anime.poster and hasattr(anime.poster, 'url'):
                        poster_url = anime.poster.url
                except Exception:
                    pass
                if not poster_url:
                    poster_url = getattr(anime, 'poster_url', None)
                
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
                })
            
            anime = item.anime
            total_episodes = anime.episodes or 0
            
            # Получаем URL постера - приоритет: локальный файл -> внешний URL
            poster_url = None
            try:
                if anime.poster and hasattr(anime.poster, 'url'):
                    poster_url = anime.poster.url
            except Exception:
                pass
            if not poster_url:
                poster_url = getattr(anime, 'poster_url', None)
            
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
        
        if not pk:
            return Response({'error': 'ID записи обязателен'}, status=400)
        
        try:
            item = UserLibrary.objects.get(id=pk)
            # Проверяем права
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
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
                # При завершении - считаем что просмотрены все эпизоды
                if item.anime and item.anime.episodes:
                    item.episodes_watched = item.anime.episodes
                    item.current_episode = item.anime.episodes
        
        if current_episode is not None:
            item.current_episode = current_episode
            item.episodes_watched = max(item.episodes_watched or 0, current_episode)
        
            # Автоматически переводим в "Просмотрено" при 100%
            if item.anime and item.anime.episodes and item.anime.episodes > 0:
                if current_episode >= item.anime.episodes:
                    item.status = 'completed'
                    if not item.completed_at:
                        item.completed_at = timezone.now()
        
        if episodes_watched is not None:
            item.episodes_watched = episodes_watched
        
        if rating is not None:
            item.rating = rating if 1 <= rating <= 10 else None
        
        if notes is not None:
            item.notes = notes
        
        if is_favorite is not None:
            item.is_favorite = is_favorite
            # Синхронизируем с FavoriteAnime
            try:
                from playlists.models import FavoriteAnime
                if is_favorite:
                    FavoriteAnime.objects.get_or_create(
                        user=request.user,
                        anime=item.anime,
                        defaults={}
                    )
                else:
                    FavoriteAnime.objects.filter(
                        user=request.user,
                        anime=item.anime
                    ).delete()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error syncing FavoriteAnime on update: {e}")
        
        item.save()
        
        # Возвращаем обновлённые данные
        return self.retrieve(request, pk)

    @action(detail=True, methods=['post'])
    def mark_favorite(self, request, pk=None):
        """Отметить/убрать из избранного"""
        from .models import UserLibrary
        from playlists.models import FavoriteAnime
        
        try:
            item = UserLibrary.objects.get(id=pk)
            # Проверяем права
            if item.user != request.user:
                return Response({'error': 'Нет прав'}, status=403)
                
            item.is_favorite = not item.is_favorite
            item.save(update_fields=['is_favorite', 'updated_at'])
            
            # Синхронизируем с FavoriteAnime
            try:
                if item.is_favorite:
                    FavoriteAnime.objects.get_or_create(
                        user=request.user,
                        anime=item.anime,
                        defaults={}
                    )
                else:
                    FavoriteAnime.objects.filter(
                        user=request.user,
                        anime=item.anime
                    ).delete()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error syncing FavoriteAnime: {e}")
            
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
