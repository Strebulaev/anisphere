"""
Feed ViewSet - взвешенная лента постов
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Count

from .models import Post, Follow, GroupMembership, UserPostHidden
from .serializers import FeedPostSerializer, PostSerializer
from .services.feed_service import FeedGenerationService, TrendingService


class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для ленты постов с взвешенным алгоритмом.
    Поддерживает различные типы ленты: weighted, hot, top, trending, followers
    """
    serializer_class = FeedPostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Базовая лента - публичные посты"""
        from django.db.models import Count
        
        queryset = Post.objects.filter(
            status='published',
            is_deleted=False,
            visibility='public'
        ).select_related(
            'author', 'anime', 'group', 'playlist', 'reactor_post', 'playlist__cover_image'
        ).prefetch_related('media_files').annotate(
            playlist_items_count=Count('playlist__items')
        ).order_by('-created_at')
        
        # Исключаем скрытые посты
        if self.request.user.is_authenticated:
            hidden_ids = UserPostHidden.objects.filter(
                user=self.request.user
            ).values_list('post_id', flat=True)
            queryset = queryset.exclude(id__in=hidden_ids)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def weighted(self, request):
        """Получить ленту с взвешенным алгоритмом (70% подписки, 15% группы, 10% рекомендации, 5% промо)"""
        user = request.user
        
        try:
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('page_size', 20))
            
            feed_data = FeedGenerationService.get_user_feed_posts(user, page, per_page)
            
            # Объединяем закрепленные и обычные посты
            all_posts = list(feed_data.get('pinned', [])) + list(feed_data.get('posts', []))
            
            if not all_posts:
                return Response({'results': [], 'count': 0, 'next': None, 'previous': None})
            
            # Получаем полные данные постов
            post_ids = [p.id for p in all_posts]
            queryset = Post.objects.filter(
                id__in=post_ids,
                status='published',
                is_deleted=False
            ).select_related(
                'author',
                'anime',
                'group',
                'playlist',
                'reactor_post',
                'reactor_post__user'
            ).prefetch_related(
                'media_files',
                'hashtag_links__hashtag'
            )
            
            # Сохраняем порядок
            post_order = {post_id: index for index, post_id in enumerate(post_ids)}
            queryset = sorted(queryset, key=lambda x: post_order.get(x.id, 999))
            
            # Пагинация
            start = (page - 1) * per_page
            end = start + per_page
            paginated_posts = queryset[start:end]
            
            serializer = FeedPostSerializer(paginated_posts, many=True, context={'request': request})
            
            return Response({
                'results': serializer.data,
                'count': len(queryset),
                'next': page + 1 if end < len(queryset) else None,
                'previous': page - 1 if page > 1 else None
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error generating weighted feed'},
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def hot(self, request):
        """Получить горячие посты (алгоритм: (лайки + комментарии*2) / время^0.5)"""
        try:
            hours = int(request.query_params.get('hours', 24))
            limit = int(request.query_params.get('limit', 20))
            
            posts = TrendingService.get_hot_posts(hours, limit)
            
            serializer = FeedPostSerializer(posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error getting hot posts'},
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def top(self, request):
        """Получить топ постов за период"""
        try:
            days = int(request.query_params.get('days', 7))
            limit = int(request.query_params.get('limit', 20))
            
            posts = TrendingService.get_top_posts(days, limit)
            
            serializer = FeedPostSerializer(posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error getting top posts'},
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Получить трендовые посты (популярные за последнее время)"""
        try:
            from django.db.models import Count
            
            hours = int(request.query_params.get('hours', 6))
            limit = int(request.query_params.get('limit', 20))
            
            time_threshold = timezone.now() - timedelta(hours=hours)
            
            posts = Post.objects.filter(
                status='published',
                is_deleted=False,
                created_at__gte=time_threshold,
                post_type__in=['text', 'image', 'video', 'anime', 'playlist']
            ).annotate(
                activity_score=F('likes_count') + F('comments_count') * 2 + F('views_count'),
                playlist_items_count=Count('playlist__items')
            ).order_by('-activity_score', '-created_at').select_related(
                'author', 'anime', 'playlist', 'group'
            ).prefetch_related('media_files')[:limit]
            
            serializer = FeedPostSerializer(posts, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error getting trending posts'},
                status=500
            )
    
    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Получить посты только от подписок пользователя"""
        try:
            from django.db.models import Count
            
            user = request.user
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('page_size', 20))
            
            subscriptions = Follow.objects.filter(
                follower=user
            ).values_list('following_id', flat=True)
            
            offset = (page - 1) * per_page
            
            posts = Post.objects.filter(
                author_id__in=subscriptions,
                status='published',
                is_deleted=False,
                visibility__in=['public', 'followers']
            ).annotate(
                playlist_items_count=Count('playlist__items')
            ).select_related(
                'author', 'anime', 'playlist', 'group'
            ).prefetch_related('media_files').order_by('-created_at')[offset:offset + per_page]
            
            serializer = FeedPostSerializer(posts, many=True, context={'request': request})
            
            return Response({
                'results': serializer.data,
                'count': len(serializer.data),
                'next': page + 1,
                'previous': page - 1 if page > 1 else None
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error getting followers feed'},
                status=500
            )
