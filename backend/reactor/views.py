from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import ReactorPost, ReactorLike, ReactorComment
from .serializers import ReactorPostSerializer, ReactorLikeSerializer, ReactorCommentSerializer, ReactorCommentCreateSerializer


class ReactorPostViewSet(ModelViewSet):
    queryset = ReactorPost.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    serializer_class = ReactorPostSerializer

    def get_queryset(self):
        queryset = ReactorPost.objects.filter(is_published=True, is_deleted=False).select_related('user')

        # Фильтр по аниме
        anime_id = self.request.query_params.get('anime')
        if anime_id:
            queryset = queryset.filter(anime_tags__id=anime_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Поставить/снять лайк с поста"""
        post = self.get_object()
        like, created = ReactorLike.objects.get_or_create(
            user=request.user,
            post=post
        )

        if not created:
            # Если лайк уже существует, удаляем его
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save()
            return Response({'liked': False, 'likes_count': post.likes_count})

        # Обновляем счетчик
        post.likes_count += 1
        post.save()

        return Response({'liked': True, 'likes_count': post.likes_count})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Получить комментарии к посту"""
        post = self.get_object()
        comments = post.comments.filter(parent__isnull=True, is_deleted=False).select_related('user')
        serializer = ReactorCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Добавить комментарий к посту"""
        post = self.get_object()
        data = request.data.copy()
        data['post'] = post.id

        serializer = ReactorCommentCreateSerializer(data=data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user)
            post.comments_count += 1
            post.save()

            # Возвращаем полный комментарий
            response_serializer = ReactorCommentSerializer(comment, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
