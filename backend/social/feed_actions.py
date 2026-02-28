"""
Дополнительные actions для FeedViewSet с взвешенным алгоритмом
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import F

from .models import Post, Follow
from .services import FeedGenerationService, TrendingService


def add_weighted_action(viewset):
    """Добавить взвешенный алгоритм ленты к FeedViewSet"""
    
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
                return self.get_paginated_response([])
            
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
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                from .serializers import FeedPostSerializer
                serializer = FeedPostSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            from .serializers import FeedPostSerializer
            serializer = FeedPostSerializer(queryset, many=True)
            return Response(serializer.data)
            
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
            
            from .serializers import FeedPostSerializer
            serializer = FeedPostSerializer(posts, many=True)
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
            
            from .serializers import FeedPostSerializer
            serializer = FeedPostSerializer(posts, many=True)
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
            hours = int(request.query_params.get('hours', 6))
            limit = int(request.query_params.get('limit', 20))
            
            # Тренды - посты с наибольшим ростом активности за последние N часов
            time_threshold = timezone.now() - timedelta(hours=hours)
            
            posts = Post.objects.filter(
                status='published',
                is_deleted=False,
                created_at__gte=time_threshold,
                post_type__in=['text', 'image', 'video', 'anime', 'playlist']
            ).annotate(
                activity_score=F('likes_count') + F('comments_count') * 2 + F('views_count')
            ).order_by('-activity_score', '-created_at').select_related(
                'author', 'anime', 'playlist', 'group'
            ).prefetch_related('media_files')[:limit]
            
            from .serializers import FeedPostSerializer
            serializer = FeedPostSerializer(posts, many=True)
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
            user = request.user
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('page_size', 20))
            
            # Получаем ID подписок
            subscriptions = Follow.objects.filter(
                follower=user
            ).values_list('following_id', flat=True)
            
            offset = (page - 1) * per_page
            
            posts = Post.objects.filter(
                author_id__in=subscriptions,
                status='published',
                is_deleted=False,
                visibility__in=['public', 'followers']
            ).select_related(
                'author', 'anime', 'playlist', 'group'
            ).prefetch_related('media_files').order_by('-created_at')[offset:offset + per_page]
            
            from .serializers import FeedPostSerializer
            serializer = FeedPostSerializer(posts, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e), 'detail': 'Error getting followers feed'},
                status=500
            )
    
    # Добавляем методы к viewset
    viewset.weighted = weighted
    viewset.hot = hot
    viewset.top = top
    viewset.trending = trending
    viewset.followers = followers
    
    return viewset
