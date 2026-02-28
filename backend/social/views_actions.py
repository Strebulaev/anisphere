"""
Дополнительные функции для социальных представлений
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Follow, Post, PostLike, PostDislike, Bookmark, Report


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_follow(request, user_id):
    """Подписаться/отписаться от пользователя"""
    from users.models import User
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Нельзя подписаться на самого себя
    if target_user == request.user:
        return Response({'error': 'Нельзя подписаться на самого себя'}, status=400)
    
    # Проверяем, существует ли подписка
    follow = Follow.objects.filter(
        follower=request.user,
        following=target_user
    ).first()
    
    if follow:
        # Отписываемся
        follow.delete()
        return Response({
            'following': False,
            'message': 'Вы отписались от пользователя'
        })
    else:
        # Подписываемся
        Follow.objects.create(
            follower=request.user,
            following=target_user
        )
        return Response({
            'following': True,
            'message': 'Вы подписались на пользователя'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_like(request, post_id):
    """Поставить/убрать лайк с поста"""
    post = get_object_or_404(Post, id=post_id)
    
    # Нельзя лайкать свой пост
    if post.author == request.user:
        return Response({'error': 'Нельзя лайкать свой пост'}, status=400)
    
    # Проверяем, есть ли уже лайк
    existing_like = PostLike.objects.filter(
        user=request.user,
        post=post
    ).first()
    
    # Проверяем, есть ли дизлайк
    existing_dislike = PostDislike.objects.filter(
        user=request.user,
        post=post
    ).first()
    
    if existing_like:
        # Убираем лайк
        existing_like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save(update_fields=['likes_count'])
        return Response({
            'liked': False,
            'likes_count': post.likes_count
        })
    else:
        # Ставим лайк
        # Если был дизлайк - удаляем его
        if existing_dislike:
            existing_dislike.delete()
            post.dislikes_count = max(0, post.dislikes_count - 1)
        
        PostLike.objects.create(user=request.user, post=post)
        post.likes_count += 1
        post.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({
            'liked': True,
            'likes_count': post.likes_count
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_dislike(request, post_id):
    """Поставить/убрать дизлайк с поста"""
    post = get_object_or_404(Post, id=post_id)
    
    # Нельзя дизлайкать свой пост
    if post.author == request.user:
        return Response({'error': 'Нельзя дизлайкать свой пост'}, status=400)
    
    existing_dislike = PostDislike.objects.filter(
        user=request.user,
        post=post
    ).first()
    
    existing_like = PostLike.objects.filter(
        user=request.user,
        post=post
    ).first()
    
    if existing_dislike:
        # Убираем дизлайк
        existing_dislike.delete()
        post.dislikes_count = max(0, post.dislikes_count - 1)
        post.save(update_fields=['dislikes_count'])
        return Response({
            'disliked': False,
            'dislikes_count': post.dislikes_count
        })
    else:
        # Ставим дизлайк
        # Если был лайк - удаляем его
        if existing_like:
            existing_like.delete()
            post.likes_count = max(0, post.likes_count - 1)
        
        PostDislike.objects.create(user=request.user, post=post)
        post.dislikes_count += 1
        post.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({
            'disliked': True,
            'dislikes_count': post.dislikes_count
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes(request, post_id):
    """Получить список лайкнувших пост"""
    post = get_object_or_404(Post, id=post_id)
    likes = PostLike.objects.filter(post=post).select_related('user__profile')[:50]
    
    from .serializers import UserSerializer
    users = [like.user for like in likes]
    serializer = UserSerializer(users, many=True)
    
    return Response({
        'count': post.likes_count,
        'users': serializer.data
    })
