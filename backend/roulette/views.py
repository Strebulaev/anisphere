"""
Views для рулетки аниме
"""
import random
import math
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    AnimeRoulette,
    AnimeRouletteItem,
    RouletteSpinHistory,
    RoulettePreset,
    RouletteStatistics
)
from .serializers import (
    AnimeRouletteSerializer,
    AnimeRouletteCreateSerializer,
    AnimeRouletteSettingsSerializer,
    AnimeRouletteItemSerializer,
    AnimeRouletteItemCreateSerializer,
    BulkAddAnimeSerializer,
    SpinResultSerializer,
    SpinRequestSerializer,
    RoulettePresetSerializer,
    RoulettePresetCreateSerializer,
    RouletteStatisticsSerializer,
    AddFromCollectionSerializer,
    AddFromPlaylistSerializer,
)


class AnimeRouletteViewSet(viewsets.ModelViewSet):
    """ViewSet для рулеток аниме"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AnimeRoulette.objects.filter(user=self.request.user).prefetch_related('items')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AnimeRouletteCreateSerializer
        return AnimeRouletteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Добавить аниме в рулетку"""
        roulette = self.get_object()
        serializer = AnimeRouletteItemCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, не добавлено ли уже это аниме
        if roulette.items.filter(anime_id=serializer.validated_data['anime_id']).exists():
            return Response(
                {'error': 'Это аниме уже добавлено в рулетку'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Генерируем цвет, если не указан
        if 'color' not in serializer.validated_data or not serializer.validated_data['color']:
            colors = [
                '#667eea', '#764ba2', '#f093fb', '#f5576c',
                '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
                '#fa709a', '#fee140', '#30cfd0', '#c43a30',
                '#f857a6', '#ff5858', '#ff9966', '#ff5e62',
            ]
            existing_colors = list(roulette.items.values_list('color', flat=True))
            available_colors = [c for c in colors if c not in existing_colors]
            serializer.validated_data['color'] = random.choice(available_colors) if available_colors else random.choice(colors)
        
        # Устанавливаем порядок
        max_order = roulette.items.aggregate(max_order=models.Max('order'))['max_order'] or 0
        serializer.validated_data['order'] = max_order + 1
        
        item = serializer.save(roulette=roulette)
        return Response(
            AnimeRouletteItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def bulk_add(self, request, pk=None):
        """Массовое добавление аниме в рулетку"""
        roulette = self.get_object()
        serializer = BulkAddAnimeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        items_data = serializer.validated_data['items']
        created_items = []
        errors = []
        
        # Цвета для генерации
        colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
            '#fa709a', '#fee140', '#30cfd0', '#c43a30',
            '#f857a6', '#ff5858', '#ff9966', '#ff5e62',
        ]
        
        with transaction.atomic():
            max_order = roulette.items.aggregate(max_order=models.Max('order'))['max_order'] or 0
            
            for i, item_data in enumerate(items_data):
                anime_id = item_data.get('anime_id')
                
                # Проверяем, не добавлено ли уже
                if roulette.items.filter(anime_id=anime_id).exists():
                    errors.append({
                        'anime_id': anime_id,
                        'error': 'Уже добавлено'
                    })
                    continue
                
                # Получаем данные аниме из Shikimori/Jikan
                anime_title = item_data.get('anime_title', f'Аниме {anime_id}')
                anime_poster = item_data.get('anime_poster')
                weight = item_data.get('weight', 1)
                color = item_data.get('color', colors[(max_order + i) % len(colors)])
                
                item = AnimeRouletteItem.objects.create(
                    roulette=roulette,
                    anime_id=anime_id,
                    anime_title=anime_title,
                    anime_poster=anime_poster,
                    weight=weight,
                    color=color,
                    order=max_order + i + 1
                )
                created_items.append(item)
        
        return Response({
            'created': AnimeRouletteItemSerializer(created_items, many=True).data,
            'errors': errors,
            'total_created': len(created_items)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Удалить аниме из рулетки"""
        roulette = self.get_object()
        item_id = request.query_params.get('item_id')
        
        if not item_id:
            return Response(
                {'error': 'Требуется item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = roulette.items.get(id=item_id)
            item.delete()
            return Response({'success': True, 'message': 'Элемент удалён'})
        except AnimeRouletteItem.DoesNotExist:
            return Response(
                {'error': 'Элемент не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_weights(self, request, pk=None):
        """Обновить веса нескольких элементов"""
        roulette = self.get_object()
        weights = request.data.get('weights', {})
        
        if not weights:
            return Response(
                {'error': 'Требуется weights'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = []
        for item_id, weight in weights.items():
            try:
                item = roulette.items.get(id=item_id)
                item.weight = max(1, int(weight))
                item.save(update_fields=['weight'])
                updated.append(item_id)
            except (AnimeRouletteItem.DoesNotExist, ValueError):
                pass
        
        return Response({
            'success': True,
            'updated': updated
        })
    
    @action(detail=True, methods=['post'])
    def spin(self, request, pk=None):
        """Крутить рулетку (одно аниме)"""
        roulette = self.get_object()
        
        if roulette.items.count() == 0:
            return Response(
                {'error': 'Рулетка пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем элементы с учётом исключения недавно выпавших
        items = self._get_available_items(roulette)

        if not items:
            return Response(
                {'error': 'Все аниме недавно выпадали. Попробуйте позже или отключите исключение недавних.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Алгоритм выбора с учетом весов
        winner, winner_index, rotation_angle = self._select_winner(items)

        # Сохраняем историю
        spin_history = RouletteSpinHistory.objects.create(
            roulette=roulette,
            winner=winner,
            rotation_angle=rotation_angle,
            spin_duration=roulette.spin_duration,
            spin_type=RouletteSpinHistory.SpinType.SINGLE,
            items_count=1
        )
        
        # Обновляем последний результат
        roulette.last_result = winner
        roulette.last_spin_at = timezone.now()
        roulette.save(update_fields=['last_result', 'last_spin_at'])
        
        # Обновляем статистику
        self._update_statistics(roulette, winner)

        return Response({
            'winner': AnimeRouletteItemSerializer(winner).data,
            'rotation_angle': rotation_angle,
            'spin_duration': roulette.spin_duration,
            'spin_id': spin_history.id
        })
    
    @action(detail=True, methods=['post'])
    def spin_multiple(self, request, pk=None):
        """Крутить рулетку несколько раз (выбрать несколько аниме)"""
        roulette = self.get_object()

        if roulette.items.count() == 0:
            return Response(
                {'error': 'Рулетка пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        count = request.data.get('count', 3)
        count = min(count, roulette.max_spin_items, roulette.items.count())

        # Получаем доступные элементы
        items = self._get_available_items(roulette)

        if len(items) < count:
            return Response(
                {'error': f'Недостаточно аниме для выбора {count}. Доступно: {len(items)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Выбираем несколько победителей без повторений
        winners = []
        selected_items = []

        for i in range(count):
            winner, winner_index, rotation_angle = self._select_winner(items)
            winners.append(winner)
            selected_items.append({
                'item': winner,
                'index': winner_index,
                'rotation_angle': rotation_angle
            })
            # Удаляем выбранное из списка для следующего выбора
            items = [item for item in items if item.id != winner.id]

        # Создаём историю
        spin_history = RouletteSpinHistory.objects.create(
            roulette=roulette,
            winner=winners[0] if winners else None,
            rotation_angle=selected_items[0]['rotation_angle'] if selected_items else 0,
            spin_duration=roulette.spin_duration,
            spin_type=RouletteSpinHistory.SpinType.MULTIPLE,
            items_count=len(winners)
        )
        spin_history.winners.set(winners)

        # Обновляем статистику
        for winner in winners:
            self._update_statistics(roulette, winner)

        return Response({
            'winners': AnimeRouletteItemSerializer(winners, many=True).data,
            'rotation_angle': selected_items[0]['rotation_angle'] if selected_items else 0,
            'spin_duration': roulette.spin_duration,
            'spin_id': spin_history.id,
            'items_count': len(winners)
        })

    @action(detail=True, methods=['post'])
    def marathon(self, request, pk=None):
        """Марафонский режим - выбрать много аниме для марафона"""
        roulette = self.get_object()

        if roulette.items.count() == 0:
            return Response(
                {'error': 'Рулетка пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        count = request.data.get('count', 5)
        count = min(count, roulette.max_spin_items, roulette.items.count())

        # Получаем доступные элементы
        items = self._get_available_items(roulette)

        if len(items) < count:
            count = len(items)

        # Выбираем победителей для марафона
        winners = []
        for i in range(count):
            winner, winner_index, rotation_angle = self._select_winner(items)
            winners.append(winner)
            items = [item for item in items if item.id != winner.id]

        # Создаём историю
        spin_history = RouletteSpinHistory.objects.create(
            roulette=roulette,
            winner=winners[0] if winners else None,
            rotation_angle=random.randint(1440, 2160),  # 4-6 оборотов
            spin_duration=roulette.spin_duration,
            spin_type=RouletteSpinHistory.SpinType.MARATHON,
            items_count=len(winners)
        )
        spin_history.winners.set(winners)

        # Обновляем статистику
        for winner in winners:
            self._update_statistics(roulette, winner)

        # Здесь можно добавить расчёт общей длительности, если есть данные об эпизодах
        total_duration = 0  # TODO: рассчитать из данных аниме

        return Response({
            'spin_id': spin_history.id,
            'selected_anime': AnimeRouletteItemSerializer(winners, many=True).data,
            'total_duration': total_duration,
            'items_count': len(winners),
            'created_at': spin_history.created_at
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """История круток с пагинацией и фильтрами"""
        roulette = self.get_object()

        # Фильтры
        spin_type = request.query_params.get('spin_type')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        history = roulette.spin_history.all()

        if spin_type:
            history = history.filter(spin_type=spin_type)
        if date_from:
            history = history.filter(created_at__gte=date_from)
        if date_to:
            history = history.filter(created_at__lte=date_to)

        # Пагинация
        limit = min(int(request.query_params.get('limit', 50)), roulette.history_limit)
        history = history[:limit]

        serializer = SpinResultSerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получить статистику рулетки"""
        roulette = self.get_object()

        # Получаем или создаём статистику
        stats, created = RouletteStatistics.objects.get_or_create(roulette=roulette)

        # Обновляем статистику если нужно
        self._recalculate_statistics(roulette, stats)

        serializer = RouletteStatisticsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_from_collection(self, request, pk=None):
        """Добавить аниме из коллекции пользователя"""
        roulette = self.get_object()
        serializer = AddFromCollectionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Импортируем модель коллекции
        try:
            from users.models import UserAnimeCollection
            collection = UserAnimeCollection.objects.filter(
                user=request.user
            ).select_related('anime')

            # Применяем фильтры
            collection_status = serializer.validated_data.get('collection_status')
            if collection_status:
                collection = collection.filter(status__in=collection_status)

            min_score = serializer.validated_data.get('min_score')
            if min_score:
                collection = collection.filter(score__gte=min_score)

            # Добавляем в рулетку
            items_data = []
            weight_by_score = serializer.validated_data.get('weight_by_score', False)

            for item in collection:
                # Проверяем, не добавлено ли уже
                if roulette.items.filter(anime_id=item.anime_id).exists():
                    continue

                weight = 1
                if weight_by_score and item.score:
                    weight = item.score

                items_data.append({
                    'anime_id': item.anime_id,
                    'anime_title': item.anime.title_ru or item.anime.title_en,
                    'anime_poster': item.anime.poster_url,
                    'weight': weight
                })

            if not items_data:
                return Response({
                    'message': 'Нет аниме для добавления',
                    'created': 0
                })

            # Массовое добавление
            result = self._bulk_create_items(roulette, items_data)

            return Response({
                'created': result['created'],
                'skipped': result['skipped'],
                'total_created': result['total_created']
            }, status=status.HTTP_201_CREATED)

        except ImportError:
            return Response(
                {'error': 'Модуль коллекций не найден'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def add_from_playlist(self, request, pk=None):
        """Добавить аниме из плейлиста"""
        roulette = self.get_object()
        serializer = AddFromPlaylistSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            from playlists.models import Playlist, PlaylistItem

            playlist_id = serializer.validated_data['playlist_id']
            playlist = Playlist.objects.get(
                id=playlist_id,
                user=request.user
            )

            items = PlaylistItem.objects.filter(playlist=playlist).select_related('anime')
            weight_equal = serializer.validated_data.get('weight_equal', True)

            items_data = []
            for item in items:
                if roulette.items.filter(anime_id=item.anime_id).exists():
                    continue

                items_data.append({
                    'anime_id': item.anime_id,
                    'anime_title': item.anime.title_ru or item.anime.title_en,
                    'anime_poster': item.anime.poster_url,
                    'weight': 1 if weight_equal else item.anime.score or 1
                })

            if not items_data:
                return Response({
                    'message': 'Нет аниме для добавления',
                    'created': 0
                })

            result = self._bulk_create_items(roulette, items_data)

            return Response({
                'created': result['created'],
                'skipped': result['skipped'],
                'total_created': result['total_created']
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get', 'put', 'patch'])
    def settings(self, request, pk=None):
        """Получить или обновить настройки рулетки"""
        roulette = self.get_object()

        if request.method == 'GET':
            serializer = AnimeRouletteSettingsSerializer(roulette)
            return Response(serializer.data)

        serializer = AnimeRouletteSettingsSerializer(
            roulette,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # === Вспомогательные методы ===

    def _get_available_items(self, roulette):
        """Получить доступные элементы с учётом исключения недавних"""
        items = list(roulette.items.all())

        if not roulette.exclude_recent:
            return items

        # Исключаем недавно выпавшие
        exclusion_date = timezone.now() - timedelta(days=roulette.exclusion_period)
        recent_winners = RouletteSpinHistory.objects.filter(
            roulette=roulette,
            created_at__gte=exclusion_date
        ).values_list('winner_id', flat=True)

        available_items = [
            item for item in items
            if item.id not in recent_winners
        ]

        # Если все исключены, возвращаем все элементы
        return available_items if available_items else items

    def _select_winner(self, items):
        """Выбрать победителя с учётом весов"""
        total_weight = sum(item.weight for item in items)
        random_value = random.uniform(0, total_weight)

        current_weight = 0
        winner = None
        winner_index = 0

        for i, item in enumerate(items):
            current_weight += item.weight
            if random_value <= current_weight:
                winner = item
                winner_index = i
                break

        if not winner:
            winner = items[-1]
            winner_index = len(items) - 1

        # Вычисляем угол поворота
        rotation_angle = self._calculate_rotation_angle(items, winner_index, total_weight)

        return winner, winner_index, rotation_angle

    def _calculate_rotation_angle(self, items, winner_index, total_weight):
        """Рассчитать угол поворота колеса"""
        sector_start = 0
        for i, item in enumerate(items):
            if i == winner_index:
                break
            sector_start += (item.weight / total_weight) * 360

        sector_size = (items[winner_index].weight / total_weight) * 360
        random_point_in_sector = random.uniform(0, sector_size)

        target_angle = sector_start + random_point_in_sector
        full_rotations = random.randint(4, 6) * 360
        rotation_angle = full_rotations + (360 - target_angle)

        return rotation_angle

    def _update_statistics(self, roulette, winner):
        """Обновить статистику рулетки"""
        stats, created = RouletteStatistics.objects.get_or_create(roulette=roulette)

        stats.total_spins += 1
        stats.last_7_days_spins += 1
        stats.last_30_days_spins += 1

        # Обновляем счётчики выпадений
        from django.db.models import Count
        most_spun = roulette.spin_history.values('winner__anime_id').annotate(
            count=Count('winner')
        ).order_by('-count').first()

        if most_spun:
            stats.most_spun_anime_id = most_spun['winner__anime_id']
            stats.most_spun_count = most_spun['count']

        # Подсчитываем уникальные аниме
        stats.unique_anime_spun = roulette.spin_history.values(
            'winner__anime_id'
        ).distinct().count()

        stats.save()

    def _recalculate_statistics(self, roulette, stats):
        """Пересчитать статистику рулетки"""
        from django.db.models import Count
        from datetime import timedelta

        now = timezone.now()

        # Общая статистика
        stats.total_spins = roulette.spin_history.count()
        stats.single_spins = roulette.spin_history.filter(
            spin_type=RouletteSpinHistory.SpinType.SINGLE
        ).count()
        stats.multiple_spins = roulette.spin_history.filter(
            spin_type=RouletteSpinHistory.SpinType.MULTIPLE
        ).count()
        stats.marathon_spins = roulette.spin_history.filter(
            spin_type=RouletteSpinHistory.SpinType.MARATHON
        ).count()

        # Самое частое аниме
        most_spun = roulette.spin_history.exclude(
            winner=None
        ).values('winner__anime_id').annotate(
            count=Count('winner')
        ).order_by('-count').first()

        if most_spun:
            stats.most_spun_anime_id = most_spun['winner__anime_id']
            stats.most_spun_count = most_spun['count']

        # Самое редкое аниме
        least_spun = roulette.spin_history.exclude(
            winner=None
        ).values('winner__anime_id').annotate(
            count=Count('winner')
        ).order_by('count').first()

        if least_spun:
            stats.least_spun_anime_id = least_spun['winner__anime_id']
            stats.least_spun_count = least_spun['count']

        # Уникальные аниме
        stats.unique_anime_spun = roulette.spin_history.exclude(
            winner=None
        ).values('winner__anime_id').distinct().count()

        # Временная статистика
        stats.last_7_days_spins = roulette.spin_history.filter(
            created_at__gte=now - timedelta(days=7)
        ).count()
        stats.last_30_days_spins = roulette.spin_history.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()

        stats.save()

    def _bulk_create_items(self, roulette, items_data):
        """Массовое создание элементов рулетки"""
        colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
            '#fa709a', '#fee140', '#30cfd0', '#c43a30',
            '#f857a6', '#ff5858', '#ff9966', '#ff5e62',
        ]

        created_items = []
        skipped = 0

        with transaction.atomic():
            max_order = roulette.items.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0

            for i, item_data in enumerate(items_data):
                if roulette.items.filter(
                    anime_id=item_data['anime_id']
                ).exists():
                    skipped += 1
                    continue

                item = AnimeRouletteItem.objects.create(
                    roulette=roulette,
                    anime_id=item_data['anime_id'],
                    anime_title=item_data.get('anime_title', f"Аниме {item_data['anime_id']}"),
                    anime_poster=item_data.get('anime_poster'),
                    weight=item_data.get('weight', 1),
                    color=item_data.get('color', colors[(max_order + i) % len(colors)]),
                    order=max_order + i + 1
                )
                created_items.append(item)

        return {
            'created': AnimeRouletteItemSerializer(created_items, many=True).data,
            'skipped': skipped,
            'total_created': len(created_items)
        }
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Очистить рулетку"""
        roulette = self.get_object()
        roulette.items.all().delete()
        return Response({'success': True, 'message': 'Рулетка очищена'})


class AnimeRouletteItemViewSet(viewsets.ModelViewSet):
    """ViewSet для элементов рулетки"""
    permission_classes = [IsAuthenticated]
    serializer_class = AnimeRouletteItemSerializer
    
    def get_queryset(self):
        return AnimeRouletteItem.objects.filter(roulette__user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Обновить элемент (вес, цвет)"""
        return super().update(request, *args, **kwargs)


class RoulettePresetViewSet(viewsets.ModelViewSet):
    """ViewSet для пресетов рулетки"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Показываем свои пресеты и публичные других пользователей
        return RoulettePreset.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('user')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoulettePresetCreateSerializer
        return RoulettePresetSerializer

    def perform_create(self, serializer):
        preset = serializer.save(user=self.request.user)
        # Сохраняем количество элементов
        preset.items_count = len(preset.items_data)
        preset.save(update_fields=['items_count'])

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Применить пресет к рулетке"""
        preset = self.get_object()
        roulette_id = request.data.get('roulette_id')

        if not roulette_id:
            return Response(
                {'error': 'Требуется roulette_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            roulette = AnimeRoulette.objects.get(
                id=roulette_id,
                user=request.user
            )
        except AnimeRoulette.DoesNotExist:
            return Response(
                {'error': 'Рулетка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Применяем пресет
        # Очищаем текущие элементы
        roulette.items.all().delete()

        # Добавляем элементы из пресета
        items_data = preset.items_data
        colors = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
            '#fa709a', '#fee140', '#30cfd0', '#c43a30',
        ]

        for i, item_data in enumerate(items_data):
            AnimeRouletteItem.objects.create(
                roulette=roulette,
                anime_id=item_data['anime_id'],
                anime_title=item_data.get('anime_title', f"Аниме {item_data['anime_id']}"),
                anime_poster=item_data.get('anime_poster'),
                weight=item_data.get('weight', 1),
                color=item_data.get('color', colors[i % len(colors)]),
                order=i + 1
            )

        # Обновляем счётчик использований пресета
        preset.times_used += 1
        preset.save(update_fields=['times_used'])

        # Возвращаем обновлённую рулетку
        serializer = AnimeRouletteSerializer(roulette)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Дублировать пресет"""
        preset = self.get_object()

        new_preset = RoulettePreset.objects.create(
            user=request.user,
            name=f"{preset.name} (копия)",
            description=preset.description,
            items_data=preset.items_data,
            settings_snapshot=preset.settings_snapshot,
            items_count=preset.items_count,
            is_public=False
        )

        serializer = RoulettePresetSerializer(new_preset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Получить популярные публичные пресеты"""
        presets = RoulettePreset.objects.filter(
            is_public=True
        ).order_by('-times_used')[:20]

        serializer = self.get_serializer(presets, many=True)
        return Response(serializer.data)
