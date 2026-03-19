"""
UserLibraryViewSet - исправленная версия
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q


class UserLibraryViewSet(viewsets.ViewSet):
    """Библиотека пользователя - на основе UserEpisodeProgress"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить список аниме в библиотеке пользователя"""
        from anime.models import UserEpisodeProgress, Anime
        
        user = request.user
        
        # Получаем все уникальные аниме с прогрессом
        progress_entries = UserEpisodeProgress.objects.filter(
            user=user
        ).select_related('anime').order_by('-last_watched')
        
        # Группируем по anime_id
        anime_data = {}
        for entry in progress_entries:
            anime_id = entry.anime_id
            if anime_id not in anime_data:
                anime_data[anime_id] = {
                    'anime': entry.anime,
                    'episodes': {},
                    'last_watched': entry.last_watched,
                }
            anime_data[anime_id]['episodes'][entry.episode_number] = entry.status
            if entry.last_watched and entry.last_watched > anime_data[anime_id]['last_watched']:
                anime_data[anime_id]['last_watched'] = entry.last_watched
        
        # Фильтрация
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')
        
        results = []
        for anime_id, data in anime_data.items():
            anime = data['anime']
            episodes = data['episodes']
            
            # Определяем общий статус
            statuses = set(episodes.values())
            if 'watched' in statuses:
                main_status = 'completed' if len([s for s in statuses if s == 'watched']) >= (anime.episodes or 0) else 'watching'
            elif 'in_progress' in statuses:
                main_status = 'watching'
            elif 'skipped' in statuses:
                main_status = 'dropped'
            else:
                main_status = 'planned'
            
            # Фильтр по статусу
            if status_filter and main_status != status_filter:
                continue
            
            # Фильтр по поиску
            if search:
                search_lower = search.lower()
                if search_lower not in anime.title_ru.lower() and search_lower not in (anime.title_en or '').lower():
                    continue
            
            results.append({
                'anime_id': anime.id,
                'title_ru': anime.title_ru,
                'title_en': anime.title_en,
                'poster_url': anime.poster_image_url,
                'status': main_status,
                'watched_episodes': len([s for s in episodes.values() if s == 'watched']),
                'total_episodes': anime.episodes or 0,
                'last_watched': data['last_watched'].isoformat() if data['last_watched'] else None,
            })
        
        return Response({'results': results, 'count': len(results)})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика библиотеки пользователя"""
        from anime.models import UserEpisodeProgress, Anime
        from django.db.models import Count
        
        user = request.user
        
        # Получаем все прогрессы пользователя
        progress_entries = UserEpisodeProgress.objects.filter(user=user)
        
        # Получаем уникальные аниме
        anime_ids = list(progress_entries.values_list('anime_id', flat=True).distinct())
        
        # Считаем просмотренные эпизоды
        watched_episodes = progress_entries.filter(status='watched').count()
        
        # Считаем пропущенные (брошенные)
        skipped_episodes = progress_entries.filter(status='skipped').count()
        
        # Для каждого аниме определяем статус
        completed_count = 0
        watching_count = 0
        dropped_count = 0
        planned_count = 0
        
        animes = Anime.objects.filter(id__in=anime_ids)
        anime_dict = {a.id: a for a in animes}
        
        for anime_id in anime_ids:
            anime = anime_dict.get(anime_id)
            if not anime:
                continue
            
            anime_progress = progress_entries.filter(anime_id=anime_id)
            watched_for_anime = anime_progress.filter(status='watched').count()
            skipped_for_anime = anime_progress.filter(status='skipped').count()
            total_episodes = anime.episodes or 0
            
            if total_episodes > 0 and watched_for_anime >= total_episodes:
                completed_count += 1
            elif skipped_for_anime > 0:
                dropped_count += 1
            elif watched_for_anime > 0:
                watching_count += 1
            else:
                planned_count += 1
        
        # Считаем общее количество серий во всех аниме
        total_episodes_in_collection = sum(
            (anime_dict.get(aid) and anime_dict.get(aid).episodes) or 0 
            for aid in anime_ids
        )
        
        # Считаем часы просмотра (24 минуты на серию по умолчанию)
        DEFAULT_EPISODE_DURATION = 24
        total_minutes_watched = watched_episodes * DEFAULT_EPISODE_DURATION
        hours_watched = round(total_minutes_watched / 60, 1)
        
        # Оставшееся время
        remaining_episodes = total_episodes_in_collection - watched_episodes
        hours_remaining = round((remaining_episodes * DEFAULT_EPISODE_DURATION) / 60, 1)
        
        # Процент завершения
        completion_percentage = 0
        if total_episodes_in_collection > 0:
            completion_percentage = round((watched_episodes / total_episodes_in_collection) * 100, 1)
        
        return Response({
            'total_anime': len(anime_ids),
            'completed_count': completed_count,
            'watching_count': watching_count,
            'dropped_count': dropped_count,
            'planned_count': planned_count,
            'total_episodes': total_episodes_in_collection,
            'watched_episodes': watched_episodes,
            'remaining_episodes': remaining_episodes,
            'total_hours_watched': hours_watched,
            'remaining_hours': hours_remaining,
            'completion_percentage': completion_percentage,
        })

    @action(detail=False, methods=['get'])
    def check_anime(self, request):
        """Проверить наличие аниме в библиотеке"""
        from anime.models import UserEpisodeProgress
        
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        progress_entries = UserEpisodeProgress.objects.filter(
            user=request.user, 
            anime_id=anime_id
        )
        
        if not progress_entries.exists():
            return Response({'in_library': False})
        
        # Определяем статус
        statuses = list(progress_entries.values_list('status', flat=True))
        anime = progress_entries.first().anime
        
        watched_count = len([s for s in statuses if s == 'watched'])
        total_episodes = anime.episodes or 0
        
        if total_episodes > 0 and watched_count >= total_episodes:
            status = 'completed'
        elif 'skipped' in statuses:
            status = 'dropped'
        elif watched_count > 0:
            status = 'watching'
        else:
            status = 'planned'
        
        return Response({
            'in_library': True,
            'status': status,
            'current_episode': progress_entries.order_by('-episode_number').first().episode_number,
            'watched_episodes': watched_count,
        })
