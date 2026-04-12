"""
All missing view actions for social app
"""
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from django.db.models import Q, Count
from datetime import timedelta
import logging

from .models import (
    Follow, Post, PostLike, PostDislike, Bookmark, Report,
    PostComment, PostCommentLike, PostCommentDislike, Repost,
    Achievement, UserAchievement, Group, GroupMembership,
    Message, PrivateChat, GroupChat, ChatSettings, ChatMember,
    ChatFolder, ChatInvite, ChatRole, Reaction, Attachment,
    EmailLog, FeedView, UserPostHidden, UserNotInterested, Hashtag, PostMedia,
    PostAttachment, UserMention, PostHashtag, Comment
)
from users.models import User
from .serializers import (
    ChatFolderCreateSerializer, ChatFolderSerializer, ChatInviteCreateSerializer, ChatInviteSerializer, GroupChatSerializer, PostCommentSerializer, PostCommentCreateSerializer,
    ReportSerializer,
    PostAttachmentSerializer, FeedPostSerializer, UserSimpleSerializer
)

logger = logging.getLogger(__name__)


# ==================== FOLLOW ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_follow(request, user_id):
    """Подписаться/отписаться от пользователя"""
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return Response({'error': 'Нельзя подписаться на самого себя'}, status=400)

    follow = Follow.objects.filter(follower=request.user, following=target_user).first()

    if follow:
        follow.delete()
        return Response({'following': False, 'message': 'Вы отписались'})
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        
    # Отправляем уведомление о новом подписчике
    try:
        from notifications.services import NotificationService
        NotificationService.create_notification(
        user=target_user,
        notification_type='follow',
        title=f'Новый подписчик',
        content=f'{request.user.username} подписался на вас',
        link=f'/profile/{request.user.id}',
        icon='👤',
        )
    except Exception as e:
        print(f"Failed to send follow notification: {e}")
        
    return Response({'following': True, 'message': 'Вы подписались'})


# ==================== POST LIKE/DISLIKE ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_like(request, post_id):
 """Лайк/дизлайк поста"""
 try:
    post = Post.objects.get(id=post_id)
 except Post.DoesNotExist:
    return Response({'error': 'Пост не найден'}, status=404)

 # Разрешаем самолайк (многие соцсети это поддерживают)
 existing_like = PostLike.objects.filter(user=request.user, post=post).first()
 existing_dislike = PostDislike.objects.filter(user=request.user, post=post).first()

 if existing_like:
    existing_like.delete()
    post.likes_count = max(0, post.likes_count -1)
    post.save(update_fields=['likes_count'])
    return Response({'liked': False, 'likes_count': post.likes_count, 'dislikes_count': post.dislikes_count})

 if existing_dislike:
    existing_dislike.delete()
    post.dislikes_count = max(0, post.dislikes_count -1)

 PostLike.objects.create(user=request.user, post=post)
 post.likes_count +=1
 post.save(update_fields=['likes_count', 'dislikes_count'])

 # Отправляем уведомление автору поста о лайке
 if post.author_id != request.user.id:
    try:
        from notifications.services import NotificationService
        NotificationService.create_notification(
        user=post.author,
        notification_type='like',
        title='Новый лайк',
        content=f'{request.user.username} лайкнул ваш пост',
        link=f'/post/{post.id}',
        icon='❤️',
        )
    except Exception:
        pass

 return Response({'liked': True, 'likes_count': post.likes_count, 'dislikes_count': post.dislikes_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_dislike(request, post_id):
    """Дизлайк поста"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Пост не найден'}, status=404)

    existing_dislike = PostDislike.objects.filter(user=request.user, post=post).first()
    existing_like = PostLike.objects.filter(user=request.user, post=post).first()

    if existing_dislike:
        existing_dislike.delete()
        post.dislikes_count = max(0, post.dislikes_count - 1)
        post.save(update_fields=['dislikes_count'])
        return Response({'disliked': False, 'dislikes_count': post.dislikes_count, 'likes_count': post.likes_count})
    else:
        if existing_like:
            existing_like.delete()
            post.likes_count = max(0, post.likes_count - 1)
        PostDislike.objects.create(user=request.user, post=post)
        post.dislikes_count += 1
        post.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'disliked': True, 'dislikes_count': post.dislikes_count, 'likes_count': post.likes_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes(request, post_id):
    """Получить список лайкнувших"""
    post = get_object_or_404(Post, id=post_id)
    likes = PostLike.objects.filter(post=post).select_related('user__profile')[:50]
    
    from users.serializers import UserSerializer
    users = [like.user for like in likes]
    serializer = UserSerializer(users, many=True)
    
    return Response({'count': post.likes_count, 'users': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_dislikers(request, post_id):
    """Получить список дизлайкнувших"""
    post = get_object_or_404(Post, id=post_id)
    dislikes = PostDislike.objects.filter(post=post).select_related('user__profile')[:50]
    
    from users.serializers import UserSerializer
    users = [d.user for d in dislikes]
    serializer = UserSerializer(users, many=True)
    
    return Response({'count': post.dislikes_count, 'users': serializer.data})


# ==================== COMMENT LIKE/DISLIKE ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """Лайк комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Используем Django User like system
    existing_like = comment.likes.filter(user=request.user).first()
    
    if existing_like:
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=['likes_count'])
        return Response({'liked': False, 'likes_count': comment.likes_count})
    else:
        # Удаляем дизлайк если есть
        comment.dislikes.filter(user=request.user).delete()
        comment.likes.create(user=request.user)
        comment.likes_count += 1
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'liked': True, 'likes_count': comment.likes_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    """Дизлайк комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    existing_dislike = comment.dislikes.filter(user=request.user).first()
    
    if existing_dislike:
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=['dislikes_count'])
        return Response({'disliked': False, 'dislikes_count': comment.dislikes_count})
    else:
        # Удаляем лайк если есть
        comment.likes.filter(user=request.user).delete()
        comment.dislikes.create(user=request.user)
        comment.dislikes_count += 1
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'disliked': True, 'dislikes_count': comment.dislikes_count})


# ==================== POST ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    """Закрепить пост - работает без ограничения по времени"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    # Снимаем закрепление с других постов
    Post.objects.filter(author=request.user, is_pinned=True).update(is_pinned=False)
    
    post.is_pinned = True
    post.pinned_at = timezone.now()
    post.save(update_fields=['is_pinned', 'pinned_at'])
    
    return Response({'success': True, 'message': 'Пост закреплен', 'is_pinned': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    """Открепить пост - работает без ограничения по времени"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    post.is_pinned = False
    post.pinned_at = None
    post.save(update_fields=['is_pinned', 'pinned_at'])
    
    return Response({'success': True, 'message': 'Пост откреплен', 'is_pinned': False})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    """Пожаловаться на пост"""
    post = get_object_or_404(Post, id=post_id)
    
    # Нельзя жаловаться на свой пост
    if post.author == request.user:
        return Response({'error': 'Нельзя жаловаться на свой пост'}, status=400)

    reason = request.data.get('reason', 'other')
    comment = request.data.get('comment', '')

    # Проверяем, не жаловался ли уже пользователь
    existing_report = Report.objects.filter(
        reporter=request.user,
        content_type='post',
        content_id=post_id,
        status='pending'
    ).first()
    
    if existing_report:
        return Response({'error': 'Вы уже отправили жалобу на этот пост'}, status=400)

    report = Report.objects.create(
        reporter=request.user,
        content_type='post',
        content_id=post_id,
        reason=reason,
        comment=comment,
        status='pending'
    )
    
    # Запускаем фоновое задание для уведомления модераторов
    try:
        from social.tasks import notify_moderators_new_report
        notify_moderators_new_report.delay(report.id)
    except Exception as e:
        logger.warning(f"Failed to notify moderators: {e}")

    return Response({'success': True, 'message': 'Жалоба отправлена'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bookmark(request, post_id):
    """Добавить в закладки"""
    post = get_object_or_404(Post, id=post_id)
    
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    return Response({
        'success': True,
        'bookmarked': created,
        'message': 'Добавлено в закладки' if created else 'Уже в закладках'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, post_id):
    """Удалить из закладок"""
    post = get_object_or_404(Post, id=post_id)
    
    deleted = Bookmark.objects.filter(user=request.user, post=post).delete()[0]
    
    return Response({
        'success': True,
        'removed': deleted > 0,
        'message': 'Удалено из закладок' if deleted else 'Не было в закладках'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark_view(request):
    """Переключить закладку"""
    post_id = request.data.get('post_id')
    if not post_id:
        return Response({'error': 'Требуется post_id'}, status=400)
    
    post = get_object_or_404(Post, id=post_id)
    
    bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
    
    if bookmark:
        bookmark.delete()
        return Response({
            'success': True,
            'bookmarked': False,
            'message': 'Удалено из закладок'
        })
    else:
        Bookmark.objects.create(user=request.user, post=post)
        return Response({
            'success': True,
            'bookmarked': True,
            'message': 'Добавлено в закладки'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarks_folders(request):
    """Получить папки закладок"""
    # Заглушка - можно расширить
    return Response({'folders': []})


# ==================== REPOST ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def repost_post(request, post_id):
    """Сделать репост или выполнить действие с репостом.
    
    Поддерживает репост:
    - В ленту (destination='feed')
    - В группу (destination='group', target_id=group_id)
    - В чат (destination='chat', target_id=chat_id)
    """
    original_post = get_object_or_404(Post, id=post_id)
    
    # Проверяем действие
    action = request.data.get('action', 'repost')  # repost, unrepost, forward
    destination = request.data.get('destination', 'feed')  # feed, group, chat
    
    if action == 'unrepost':
        # Удалить репост
        deleted = Repost.objects.filter(
            original_post=original_post,
            user=request.user
        ).delete()[0]
        
        if deleted:
            original_post.reposts_count = max(0, original_post.reposts_count - 1)
            original_post.save(update_fields=['reposts_count'])
        
        return Response({'success': True, 'removed': deleted > 0, 'action': 'unrepost'})
    
    elif action == 'forward' or destination == 'chat':
        # Переслать в чат
        chat_id = request.data.get('chat_id') or request.data.get('target_id')
        chat_type = request.data.get('chat_type', 'private')
        message_text = request.data.get('message', '')
        
        if not chat_id:
            return Response({'error': 'Требуется chat_id или target_id'}, status=400)
        
        # Проверяем доступ к чату
        if chat_type == 'group':
            chat = get_object_or_404(GroupChat, id=chat_id)
            if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
                return Response({'error': 'Нет доступа к чату'}, status=403)
        else:
            chat = get_object_or_404(PrivateChat, id=chat_id)
            if request.user not in [chat.user1, chat.user2]:
                return Response({'error': 'Нет доступа к чату'}, status=403)
        
        # Создаём сообщение с постом
        message = Message.objects.create(
            sender=request.user,
            text=message_text,
            shared_post=original_post
        )
        
        if chat_type == 'group':
            message.chat = chat
        else:
            message.private_chat = chat
        
        message.save()
        
        # Обновляем счётчик
        original_post.shares_count += 1
        original_post.save(update_fields=['shares_count'])
        
        return Response({
            'success': True,
            'message_id': message.id,
            'chat_id': chat.id,
            'action': 'forward'
        })
    
    elif destination == 'group':
        # Репост в группу - создаём пост в группе
        group_id = request.data.get('target_id') or request.data.get('group_id')
        comment = request.data.get('comment', '')
        
        if not group_id:
            return Response({'error': 'Требуется group_id или target_id'}, status=400)
        
        group = get_object_or_404(GroupChat, id=group_id)
        
        # Проверяем доступ к группе
        if not ChatMember.objects.filter(chat=group, user=request.user).exists():
            return Response({'error': 'Нет доступа к группе'}, status=403)
        
        # Создаём новый пост в группе как репост
        new_post = Post.objects.create(
            author=request.user,
            group=group,
            post_type='repost',
            original_post=original_post,
            text=comment,
            title=original_post.title,
            visibility='public',
            allow_comments=True,
        )
        
        # Копируем медиа если есть
        for media in original_post.media_files.all():
            PostMedia.objects.create(
                post=new_post,
                media=media.media,
                media_type=media.media_type,
                order=media.order
            )
        
        # Обновляем счётчик
        original_post.reposts_count += 1
        original_post.save(update_fields=['reposts_count'])
        
        from .serializers import PostSerializer
        return Response({
            'success': True,
            'post_id': new_post.id,
            'action': 'repost_to_group',
            'post': PostSerializer(new_post, context={'request': request}).data
        })
    
    else:
        # Обычный репост в ленту
        if original_post.post_type == 'system':
            return Response({'error': 'Нельзя репостнуть системный пост'}, status=400)
        
        if original_post.visibility == 'private':
            return Response({'error': 'Нельзя репостнуть приватный пост'}, status=400)
        
        # Проверяем, не делал ли пользователь уже репост
        existing_repost = Repost.objects.filter(
            original_post=original_post,
            user=request.user
        ).first()
        
        if existing_repost:
            return Response({
                'success': True,
                'repost_id': existing_repost.id,
                'already_reposted': True,
                'action': 'repost'
            })
        
        comment = request.data.get('comment', '')
        
        repost = Repost.objects.create(
            original_post=original_post,
            user=request.user,
            comment=comment
        )
        
        # Создаём пост-репост в ленте
        new_post = Post.objects.create(
            author=request.user,
            post_type='repost',
            original_post=original_post,
            text=comment,
            title=original_post.title,
            visibility='public',
            allow_comments=True,
        )
        
        original_post.reposts_count += 1
        original_post.save(update_fields=['reposts_count'])
        
        from .serializers import PostSerializer
        return Response({
            'success': True,
            'repost_id': repost.id,
            'post_id': new_post.id,
            'action': 'repost',
            'post': PostSerializer(new_post, context={'request': request}).data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unrepost_post(request, post_id):
    """Удалить репост"""
    original_post = get_object_or_404(Post, id=post_id)
    
    deleted = Repost.objects.filter(
        original_post=original_post,
        user=request.user
    ).delete()[0]
    
    if deleted:
        original_post.reposts_count = max(0, original_post.reposts_count - 1)
        original_post.save(update_fields=['reposts_count'])
    
    return Response({'success': True, 'removed': deleted > 0})


def create_repost(request, post_id):
    return repost_post(request, post_id)


def delete_repost(request, post_id):
    return unrepost_post(request, post_id)


# ==================== POST VIEW TRACKING ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_post_view(request, post_id):
    """Отследить просмотр поста"""
    post = get_object_or_404(Post, id=post_id)
    
    if post.author == request.user:
        return Response({'success': True, 'message': 'Автор'})
    
    existing_view = FeedView.objects.filter(user=request.user, post=post).first()
    
    if not existing_view:
        FeedView.objects.create(user=request.user, post=post)
        post.views_count += 1
        post.save(update_fields=['views_count'])
    
    return Response({'success': True, 'views_count': post.views_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_viewers(request, post_id):
    """Получить список просмотревших"""
    post = get_object_or_404(Post, id=post_id)
    views = FeedView.objects.filter(post=post).select_related('user__profile')[:50]
    
    from users.serializers import UserSerializer
    users = [v.user for v in views]
    serializer = UserSerializer(users, many=True)
    
    return Response({'count': post.views_count, 'users': serializer.data})


# ==================== COMMENTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_comment_replies(request, comment_id):
    """Получить ответы на комментарий (для старой модели Comment)"""
    comment = get_object_or_404(Comment, id=comment_id)
    replies = Comment.objects.filter(parent=comment).select_related('author')[:20]
    
    from .serializers import CommentSerializer
    serializer = CommentSerializer(replies, many=True)
    
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_post_comment_replies(request, comment_id):
    """Получить ответы на комментарий к посту (модель PostComment)"""
    comment = get_object_or_404(PostComment, id=comment_id)
    replies = PostComment.objects.filter(parent=comment).select_related('author')[:20]
    
    from .serializers import PostCommentSerializer
    serializer = PostCommentSerializer(replies, many=True)
    
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    """Пожаловаться на комментарий"""
    comment = get_object_or_404(PostComment, id=comment_id)
    
    reason = request.data.get('reason', 'other')
    comment_text = request.data.get('comment', '')
    
    Report.objects.create(
        reporter=request.user,
        content_type='comment',
        content_id=comment_id,
        reason=reason,
        comment=comment_text,
        status='pending'
    )
    
    return Response({'success': True, 'message': 'Жалоба отправлена'})


# ==================== EDIT POST/COMMENT ====================

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    """Редактировать пост"""
    from .serializers import PostSerializer
    
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    # Проверка времени (5 минут)
    if (timezone.now() - post.created_at).total_seconds() > 300:
        return Response({'error': 'Время редактирования истекло'}, status=400)
    
    # Нельзя менять тип поста
    new_type = request.data.get('post_type')
    if new_type and new_type != post.post_type:
        return Response({'error': 'Нельзя менять тип поста'}, status=400)
    
    if 'title' in request.data:
        post.title = request.data['title'][:200] if request.data['title'] else None
    
    if 'text' in request.data:
        text = request.data['text']
        if text and len(text) > 5000:
            return Response({'error': 'Максимум 5000 символов'}, status=400)
        post.text = text
    
    if 'visibility' in request.data:
        if request.data['visibility'] in ['public', 'followers', 'friends', 'private']:
            post.visibility = request.data['visibility']
    
    if 'allow_comments' in request.data:
        post.allow_comments = bool(request.data['allow_comments'])
    
    if 'is_spoiler' in request.data:
        post.is_spoiler = bool(request.data['is_spoiler'])
    
    post.edited_at = timezone.now()
    post.save()
    
    return Response({
        'success': True,
        'message': 'Пост обновлён',
        'post': PostSerializer(post, context={'request': request}).data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    """Редактировать комментарий"""
    comment = get_object_or_404(PostComment, id=comment_id, author=request.user)
    
    # Проверка времени (10 минут)
    if (timezone.now() - comment.created_at).total_seconds() > 600:
        return Response({'error': 'Время редактирования истекло'}, status=400)
    
    new_text = request.data.get('text', '').strip()
    if not new_text:
        return Response({'error': 'Текст не может быть пустым'}, status=400)
    
    if len(new_text) > 2000:
        return Response({'error': 'Максимум 2000 символов'}, status=400)
    
    comment.text = new_text
    comment.is_edited = True
    comment.save()
    
    from .serializers import CommentSerializer
    return Response(CommentSerializer(comment).data)


# ==================== CONTENT MODERATION ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hide_post_from_feed(request, post_id):
    """Скрыть пост из ленты"""
    post = get_object_or_404(Post, id=post_id)
    
    UserPostHidden.objects.get_or_create(user=request.user, post=post)
    
    return Response({'success': True, 'message': 'Пост скрыт'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_post_not_interested(request, post_id):
    """Отметить как неинтересное"""
    return hide_post_from_feed(request, post_id)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hide_author_from_feed(request, user_id):
    """Скрыть все посты автора из ленты"""
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return Response({'error': 'Нельзя скрыть самого себя'}, status=400)

    # Создаём запись о скрытом пользователе
    _, created = UserNotInterested.objects.get_or_create(
        user=request.user,
        target_user=target_user
    )

    return Response({
        'success': True,
        'hidden': True,
        'message': 'Автор скрыт из ленты' if created else 'Автор уже был скрыт'
    })


# ==================== HIDDEN POSTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hidden_posts(request):
    """Получить список скрытых постов с полными данными постов"""
    hidden_posts = UserPostHidden.objects.filter(user=request.user).select_related('post').order_by('-created_at')

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    offset = (page - 1) * page_size

    total = hidden_posts.count()
    hidden_posts_page = hidden_posts[offset:offset + page_size]

    results = []
    for hp in hidden_posts_page:
        if hp.post:
            from .serializers import PostSerializer
            try:
                serializer = PostSerializer(hp.post, context={'request': request})
                data = serializer.data
                data['hidden_at'] = hp.created_at.isoformat()
                results.append(data)
            except:
                pass

    return Response({
        'results': results,
        'count': total,
        'next': page + 1 if offset + page_size < total else None,
        'previous': page - 1 if page > 1 else None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarked_posts(request):
    """Получить список закладок с полными данными постов"""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post').order_by('-created_at')

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    offset = (page - 1) * page_size

    total = bookmarks.count()
    bookmarks_page = bookmarks[offset:offset + page_size]

    results = []
    for bm in bookmarks_page:
        if bm.post:
            from .serializers import PostSerializer
            try:
                serializer = PostSerializer(bm.post, context={'request': request})
                data = serializer.data
                data['bookmarked_at'] = bm.created_at.isoformat()
                data['bookmark_folder'] = bm.folder
                results.append(data)
            except:
                pass

    return Response({
        'results': results,
        'count': total,
        'next': page + 1 if offset + page_size < total else None,
        'previous': page - 1 if page > 1 else None
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def restore_hidden_post(request, post_id):
    """Восстановить скрытый пост"""
    try:
        hidden = UserPostHidden.objects.get(user=request.user, post_id=post_id)
        hidden.delete()
        return Response({'success': True, 'message': 'Пост восстановлен'})
    except UserPostHidden.DoesNotExist:
        return Response({'error': 'Пост не найден в скрытых'}, status=404)


# ==================== FEED STATISTICS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feed_statistics(request):
    """Получить статистику ленты"""
    user = request.user
    
    posts_count = Post.objects.filter(author=user, status='published').count()
    likes_received = PostLike.objects.filter(post__author=user).count()
    comments_received = PostComment.objects.filter(post__author=user).count()
    reposts_received = Repost.objects.filter(original_post__author=user).count()
    bookmarks_count = Bookmark.objects.filter(user=user).count()
    
    following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    new_posts_count = Post.objects.filter(
        author_id__in=following_ids,
        status='published',
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    return Response({
        'posts_count': posts_count,
        'likes_received': likes_received,
        'comments_received': comments_received,
        'reposts_received': reposts_received,
        'bookmarks_count': bookmarks_count,
        'new_posts_count': new_posts_count
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_popular_posts(request):
    """Получить популярные посты (только с лайками)"""
    posts = Post.objects.filter(
        status='published',
        is_deleted=False,
        likes_count__gte=1  # Только посты с хотя бы 1 лайком
    ).order_by('-likes_count', '-created_at')[:20]
    
    from .serializers import PostSerializer
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    """Получить посты пользователя"""
    user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(
        author=user,
        status='published',
        is_deleted=False
    ).order_by('-created_at')[:20]
    
    from .serializers import PostSerializer
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_group_posts(request, group_id):
    """Получить посты группы"""
    group = get_object_or_404(Group, id=group_id)
    posts = Post.objects.filter(
        group=group,
        status='published',
        is_deleted=False
    ).order_by('-created_at')[:20]
    
    from .serializers import PostSerializer
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


# ==================== HASHTAGS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_hashtag_posts(request, tag_name):
    """Получить посты по хэштегу"""
    hashtag = get_object_or_404(Hashtag, name=tag_name.lstrip('#'))
    posts = Post.objects.filter(
        hashtag_links__hashtag=hashtag,
        status='published',
        is_deleted=False
    ).order_by('-created_at')[:20]
    
    from .serializers import PostSerializer
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_hashtags(request):
    """Поиск хэштегов"""
    query = request.query_params.get('q', '')
    hashtags = Hashtag.objects.filter(name__icontains=query).order_by('-posts_count')[:10]
    
    return Response([{'name': h.name, 'posts_count': h.posts_count} for h in hashtags])


# ==================== NOTIFICATION SETTINGS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notification_settings(request):
    """Получить настройки уведомлений"""
    user = request.user
    return Response({
        'notify_likes': user.notify_likes,
        'notify_comments': user.notify_comments,
        'notify_mentions': user.notify_mentions,
        'email_digest': user.email_digest,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_notification_settings(request):
    """Обновить настройки уведомлений"""
    user = request.user
    
    if 'notify_likes' in request.data:
        user.notify_likes = request.data['notify_likes']
    if 'notify_comments' in request.data:
        user.notify_comments = request.data['notify_comments']
    if 'notify_mentions' in request.data:
        user.notify_mentions = request.data['notify_mentions']
    if 'email_digest' in request.data:
        user.email_digest = request.data['email_digest']
    
    user.save()
    
    return Response({'success': True})


# ==================== ACHIEVEMENTS ====================

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """Достижения"""
    queryset = Achievement.objects.all()
    permission_classes = [AllowAny]


class UserAchievementViewSet(viewsets.ModelViewSet):
    """Достижения пользователя"""
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)


# ==================== FILES ====================

class UploadedFileViewSet(viewsets.ModelViewSet):
    """Загруженные файлы"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # Заглушка


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """Загрузить файл"""
    return Response({'success': True, 'url': ''})


# ==================== FAVORITES ====================

from django.contrib.contenttypes.models import ContentType
from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    """Избранное"""
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """Проверить, добавлен ли объект в избранное"""
        content_type_str = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')

        if not content_type_str or not object_id:
            return Response({'error': 'content_type и object_id обязательны'}, status=400)

        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            return Response({'error': 'Неверный content_type'}, status=400)

        is_favorited = Favorite.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).exists()

        return Response({
            'is_favorited': is_favorited,
            'content_type': content_type_str,
            'object_id': object_id
        })

    def create(self, request, *args, **kwargs):
        """Добавить в избранное"""
        content_type_str = request.data.get('content_type')
        object_id = request.data.get('object_id')

        if not content_type_str or not object_id:
            return Response({'error': 'content_type и object_id обязательны'}, status=400)

        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            return Response({'error': 'Неверный content_type'}, status=400)

        # Проверяем, не добавлено ли уже
        existing = Favorite.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if existing:
            return Response({'success': True, 'is_favorited': True, 'id': existing.id})

        favorite = Favorite.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )

        return Response({
            'success': True,
            'is_favorited': True,
            'id': favorite.id
        }, status=201)

    def destroy(self, request, *args, **kwargs):
        """Удалить из избранного"""
        instance = self.get_object()
        instance.delete()
        return Response({'success': True, 'is_favorited': False}, status=204)

    @action(detail=False, methods=['post', 'delete'])
    def toggle(self, request):
        """Переключить избранное (добавить/удалить)"""
        content_type_str = request.data.get('content_type') or request.query_params.get('content_type')
        object_id = request.data.get('object_id') or request.query_params.get('object_id')

        if not content_type_str or not object_id:
            return Response({'error': 'content_type и object_id обязательны'}, status=400)

        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            return Response({'error': 'Неверный content_type'}, status=400)

        try:
            object_id = int(object_id)
        except (ValueError, TypeError):
            return Response({'error': 'object_id должен быть числом'}, status=400)

        # Ищем существующую запись
        existing = Favorite.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if existing:
            # Удаляем из избранного
            existing.delete()
            return Response({
                'success': True,
                'is_favorited': False,
                'message': 'Удалено из избранного'
            })
        else:
            # Добавляем в избранное
            favorite = Favorite.objects.create(
                user=request.user,
                content_type=content_type,
                object_id=object_id
            )
            return Response({
                'success': True,
                'is_favorited': True,
                'id': favorite.id,
                'message': 'Добавлено в избранное'
            }, status=201)


# ==================== GROUPS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_online_users(request):
    """Получить онлайн пользователей"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    users = User.objects.filter(
        is_online=True
    ).exclude(id=request.user.id if request.user.is_authenticated else 0)[:20]
    
    from users.serializers import UserSerializer
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


class GroupSearchView(viewsets.ReadOnlyModelViewSet):
    """Поиск групп"""
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        return Group.objects.filter(name__icontains=query)[:20]


# ==================== CHAT INVITES ====================

class ChatInviteViewSet(viewsets.ModelViewSet):
    """Приглашения в чат"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatInviteSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChatInviteCreateSerializer
        return ChatInviteSerializer

    def get_queryset(self):
        try:
            return ChatInvite.objects.filter(created_by=self.request.user).select_related('chat', 'created_by')
        except Exception:
            return ChatInvite.objects.none()

    def create(self, request, *args, **kwargs):
        """Создать приглашение в чат"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error creating chat invite: {e}")
            return Response({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_chat_by_invite(request, token):
    """Присоединиться по приглашению"""
    invite = get_object_or_404(ChatInvite, token=token)
    
    if invite.is_expired():
        return Response({'error': 'Приглашение истекло'}, status=400)
    
    chat = invite.chat
    
    if isinstance(chat, GroupChat):
        GroupMembership.objects.get_or_create(user=request.user, group=chat)
    elif isinstance(chat, PrivateChat):
        pass  # Приватный чат уже существует
    
    invite.delete()
    
    return Response({'success': True, 'chat_id': chat.id})
     

# ==================== REACTIONS ====================

class ReactionViewSet(viewsets.ModelViewSet):
    """Реакции"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # Заглушка


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_reaction(request, message_id):
    """Переключить реакцию"""
    message = get_object_or_404(Message, id=message_id)
    emoji = request.data.get('emoji', '👍')
    
    reaction = Reaction.objects.filter(
        user=request.user,
        message=message,
        emoji=emoji
    ).first()
    
    if reaction:
        reaction.delete()
        return Response({'reacted': False})
    else:
        Reaction.objects.create(user=request.user, message=message, emoji=emoji)
        return Response({'reacted': True})


# ==================== ATTACHMENTS ====================

class AttachmentViewSet(viewsets.ModelViewSet):
    """Вложения"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return []  # Заглушка


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_attachment(request, message_id):
    """Загрузить вложение к сообщению"""
    from .models import Message, Attachment
    from django.core.files.storage import default_storage
    import os
    
    message = get_object_or_404(Message, id=message_id)
    
    # Проверяем доступ к сообщению (пользователь должен быть отправителем или получателем)
    if message.sender != request.user:
        # Для групповых чатов
        if hasattr(message, 'chat') and message.chat:
            from .models import ChatMember
            if not ChatMember.objects.filter(chat=message.chat, user=request.user).exists():
                return Response({'error': 'Нет доступа'}, status=403)
        # Для приватных чатов
        elif hasattr(message, 'private_chat') and message.private_chat:
            pc = message.private_chat
            if pc.user1 != request.user and pc.user2 != request.user:
                return Response({'error': 'Нет доступа'}, status=403)
        else:
            return Response({'error': 'Нет доступа'}, status=403)

    if 'file' not in request.FILES:
        return Response({'error': 'Файл не найден'}, status=400)
    
    file = request.FILES['file']
    
    # Определяем тип файла
    mime_type = file.content_type
    media_type = 'file'
    if mime_type.startswith('image/'):
        media_type = 'image'
    elif mime_type.startswith('video/'):
        media_type = 'video'
    elif mime_type.startswith('audio/'):
        media_type = 'audio'
    
    # Сохраняем файл
    file_path = f'message_attachments/{message_id}/{file.name}'
    file_url = default_storage.save(file_path, file)
    file_full_url = request.build_absolute_uri(default_storage.url(file_url))
    
    # Создаём запись Attachment
    attachment = Attachment.objects.create(
        message=message,
        file=file,
        file_name=file.name,
        file_size=file.size,
        mime_type=mime_type,
        type=media_type
    )
    
    return Response({
        'success': True,
        'id': attachment.id,
        'url': file_full_url,
        'file_name': file.name,
        'file_size': file.size,
        'mime_type': mime_type,
        'type': media_type
    })


# ==================== MESSAGE ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_message(request, message_id):
    """Закрепить сообщение"""
    message = get_object_or_404(Message, id=message_id)
    message.is_pinned = True
    message.save(update_fields=['is_pinned'])
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_message(request, message_id):
    """Открепить сообщение"""
    message = get_object_or_404(Message, id=message_id)
    message.is_pinned = False
    message.save(update_fields=['is_pinned'])
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forward_message(request, message_id):
    """Переслать сообщение"""
    return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pinned_messages(request, chat_id):
    """Получить закрепленные сообщения"""
    chat = get_object_or_404(GroupChat, id=chat_id)
    messages = Message.objects.filter(chat=chat, is_pinned=True)[:10]
    
    from .serializers import MessageSerializer
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


# ==================== UNREAD ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Получить количество непрочитанных"""
    user = request.user
    
    private_chats = PrivateChat.objects.filter(members__user=user)
    group_chats = GroupChat.objects.filter(members__user=user)
    
    private_unread = sum(c.get_unread_count(user) for c in private_chats)
    group_unread = sum(g.get_unread_count(user) for g in group_chats)
    
    return Response({
        'total': private_unread + group_unread,
        'private': private_unread,
        'group': group_unread
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_chats(request):
    """Получить чаты с непрочитанными"""
    user = request.user
    
    chats = []
    
    # Приватные чаты - используем Q для фильтрации по user1 или user2
    private_chats = PrivateChat.objects.filter(Q(user1=user) | Q(user2=user))
    for chat in private_chats:
        unread = chat.get_unread_count(user)
        if unread > 0:
            chats.append({'id': chat.id, 'type': 'private', 'unread': unread})
    
    # Групповые чаты
    group_chats = GroupChat.objects.filter(members__user=user)
    for chat in group_chats:
        unread = chat.get_unread_count(user)
        if unread > 0:
            chats.append({'id': chat.id, 'type': 'group', 'unread': unread})
    
    return Response(chats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_chat_read(request, chat_id):
    """Отметить чат прочитанным"""
    # Пробуем GroupChat, затем PrivateChat
    chat = None
    try:
        chat = GroupChat.objects.get(id=chat_id)
    except GroupChat.DoesNotExist:
        try:
            chat = PrivateChat.objects.get(id=chat_id)
        except PrivateChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    if hasattr(chat, 'mark_as_read'):
        chat.mark_as_read(request.user)
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_private_chat_read(request, chat_id):
    """Отметить приватный чат прочитанным"""
    chat = get_object_or_404(PrivateChat, id=chat_id)
    chat.mark_as_read(request.user)
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_group_chat_read(request, chat_id):
    """Отметить групповой чат прочитанным"""
    chat = get_object_or_404(GroupChat, id=chat_id)
    chat.mark_as_read(request.user)
    return Response({'success': True})


# ==================== SEARCH ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_messages(request):
    """Поиск сообщений"""
    query = request.query_params.get('q', '')
    chat_id = request.query_params.get('chat_id')
    
    messages = Message.objects.filter(
        text__icontains=query,
        chat_id=chat_id
    ).order_by('-created_at')[:50]
    
    from .serializers import MessageSerializer
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reindex_messages(request):
    """Переиндексировать сообщения"""
    return Response({'success': True, 'indexed': 0})


# ==================== CHAT FOLDERS ====================

class ChatFolderViewSet(viewsets.ModelViewSet):
    """Папки чатов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatFolderSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChatFolderCreateSerializer
        return ChatFolderSerializer
    
    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folder_chats(request, folder_id):
    """Получить чаты в папке"""
    folder = get_object_or_404(ChatFolder, id=folder_id, user=request.user)
    chats = folder.chats.all()
    
    from .serializers import ChatSerializer
    serializer = ChatSerializer(chats, many=True)
    return Response(serializer.data)


# ==================== EMAIL LOGS ====================

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Логи email"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EmailLog.objects.filter(user=self.request.user)


# ==================== VIEWSETS (STUBS) ====================

class RepostViewSet(viewsets.ModelViewSet):
    """Репосты"""
    permission_classes = [IsAuthenticated]
    queryset = Repost.objects.none()


class PostCommentViewSet(viewsets.ModelViewSet):
    """Комментарии к постам"""
    permission_classes = [IsAuthenticated]
    serializer_class = PostCommentSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCommentCreateSerializer
        return PostCommentSerializer
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        # Возвращаем ВСЕ комментарии (и корневые, и ответы), отсортированные по дате
        return PostComment.objects.filter(
            post_id=post_id,
            is_deleted=False
        ).select_related('author').order_by('-created_at')
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        serializer.save(author=self.request.user, post_id=post_id)


class BookmarkViewSet(viewsets.ModelViewSet):
    """Закладки"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('post')

    def list(self, request):
        """Получить список закладок"""
        bookmarks = self.get_queryset().order_by('-created_at')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size
        
        total = bookmarks.count()
        bookmarks_page = bookmarks[offset:offset + page_size]

        posts = [b.post for b in bookmarks_page if b.post]
        serializer = FeedPostSerializer(posts, many=True, context={'request': request})

        return Response({
            'results': serializer.data,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None
        })

    @action(detail=False, methods=['get'], url_path='posts')
    def posts(self, request):
        """Получить посты из закладок"""
        return self.list(request)


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet для жалоб"""
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    
    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Создать жалобу"""
        # Логируем входящие данные для отладки
        logger.info(f"Report create request data: {request.data}")
        
        # Поддерживаем разные форматы запроса
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        reason = request.data.get('reason', 'other')
        comment = request.data.get('comment', '')
        
        # Альтернативные имена полей (для совместимости с фронтендом)
        if not content_type:
            content_type = request.data.get('type')
        if not content_id:
            content_id = request.data.get('object_id') or request.data.get('id') or request.data.get('post_id') or request.data.get('comment_id') or request.data.get('user_id')
        
        # Если content_type не указан, пытаемся определить по наличию полей
        if not content_type:
            if request.data.get('post_id'):
                content_type = 'post'
                content_id = request.data.get('post_id')
            elif request.data.get('comment_id'):
                content_type = 'comment'
                content_id = request.data.get('comment_id')
            elif request.data.get('user_id'):
                content_type = 'user'
                content_id = request.data.get('user_id')
        
        # Проверка обязательных полей
        if not content_type:
            logger.warning(f"Report missing content_type: {request.data}")
            return Response({
                'error': 'Поле content_type обязательно',
                'valid_types': ['post', 'comment', 'user'],
                'received_data': request.data
            }, status=400)
        
        if not content_id:
            logger.warning(f"Report missing content_id: {request.data}")
            return Response({
                'error': 'Поле content_id обязательно',
                'received_data': request.data
            }, status=400)
        
        # Нормализация content_type
        content_type = str(content_type).lower()
        if content_type not in ['post', 'comment', 'user']:
            logger.warning(f"Report invalid content_type: {content_type}")
            return Response({
                'error': f'Недопустимый content_type: {content_type}',
                'valid_types': ['post', 'comment', 'user']
            }, status=400)
        
        # Конвертация content_id в int
        try:
            content_id = int(content_id)
        except (ValueError, TypeError):
            logger.warning(f"Report invalid content_id: {content_id}")
            return Response({
                'error': f'Неверный формат content_id: {content_id}'
            }, status=400)
        
        # Проверка существования контента
        if content_type == 'post':
            if not Post.objects.filter(id=content_id).exists():
                return Response({
                    'error': 'Пост не найден'
                }, status=404)
        elif content_type == 'comment':
            if not PostComment.objects.filter(id=content_id).exists():
                return Response({
                    'error': 'Комментарий не найден'
                }, status=404)
        elif content_type == 'user':
            if not User.objects.filter(id=content_id).exists():
                return Response({
                    'error': 'Пользователь не найден'
                }, status=404)
            # Нельзя жаловаться на самого себя
            if content_id == request.user.id:
                return Response({
                    'error': 'Нельзя пожаловаться на самого себя'
                }, status=400)
        
        # Создание жалобы (разрешаем неограниченное количество жалоб от одного пользователя)
        report = Report.objects.create(
            reporter=request.user,
            content_type=content_type,
            content_id=content_id,
            reason=reason,
            comment=comment,
            status='pending'
        )

        logger.info(f"Report created: id={report.id}, type={content_type}, content_id={content_id}")
        
        # Отправляем уведомление модераторам НАПРЯМУЮ (без Celery)
        try:
            from notifications.models import Notification, Complaint
            from django.contrib.contenttypes.models import ContentType
            
            # Ищем модератора - сначала по is_staff/is_superuser
            moderator = User.objects.filter(
                models.Q(is_staff=True) | models.Q(is_superuser=True)
            ).first()
            
            if moderator:
                content_type_display = 'Пост' if content_type == 'post' else 'Комментарий' if content_type == 'comment' else 'Пользователь'
                reason_display = dict(Report.REASON_CHOICES).get(reason, reason)
                
                # Создаём уведомление
                Notification.objects.create(
                    user=moderator,
                    type='system',
                    title=f'🚨 Новая жалоба: {content_type_display}',
                    content=f'Причина: {reason_display}\nЖалоба от: @{request.user.username}\nID контента: {content_id}',
                    link=f'/admin/social/report/{report.id}/'
                )
                logger.info(f"Moderator notification sent to {moderator.username}")
                
                # Также создаём запись в Complaint для админ-панели
                content_type_map = {
                    'post': 'comment',  # nearest match
                    'comment': 'comment',
                    'user': 'user',
                }
                complaint_type = content_type_map.get(content_type, 'other')
                
                # Получаем ContentType для generic relation
                try:
                    from social.models import Post, PostComment
                    if content_type == 'post':
                        ct = ContentType.objects.get_for_model(Post)
                    elif content_type == 'comment':
                        ct = ContentType.objects.get_for_model(PostComment)
                    else:
                        ct = ContentType.objects.get_for_model(User)
                    
                    Complaint.objects.create(
                        content_type=ct,
                        object_id=content_id,
                        complainant=request.user,
                        complaint_type=complaint_type,
                        reason=reason,
                        description=comment or '',
                        status='pending'
                    )
                    logger.info(f"Complaint created for admin panel")
                except Exception as e:
                    logger.error(f"Failed to create Complaint: {e}")
            else:
                logger.warning("No moderator found for report notification")
        except Exception as e:
            logger.error(f"Failed to send moderator notification: {e}")
        
        return Response({
            'success': True,
            'id': report.id,
            'message': 'Жалоба отправлена'
        }, status=201)


class PostMediaViewSet(viewsets.ModelViewSet):
    """Медиа постов"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostMedia.objects.all()


class PostAttachmentViewSet(viewsets.ModelViewSet):
    """Прикреплённый контент к постам (аниме, плейлист, shorts)"""
    permission_classes = [IsAuthenticated]
    serializer_class = PostAttachmentSerializer

    def get_queryset(self):
        qs = PostAttachment.objects.all()
        post_id = self.request.query_params.get('post')
        if post_id:
            try:
                qs = qs.filter(post_id=int(post_id))
            except (ValueError, TypeError):
                pass
        return qs

    def perform_create(self, serializer):
        # Ensure user is owner of the post before attaching
        post = serializer.validated_data.get('post')
        if post and post.author != self.request.user:
            raise PermissionDenied('Cannot add attachment to another user\'s post')
        serializer.save()


# ==================== SUBSCRIPTIONS (FOLLOW) ====================

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """Подписки пользователя"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related('following')
    
    def list(self, request):
        """Получить список подписок"""
        follows = self.get_queryset().order_by('-created_at')
        
        # Пагинация
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size
        
        # Поиск
        search = request.query_params.get('search', '')
        if search:
            follows = follows.filter(following__username__icontains=search) | \
                      follows.filter(following__display_name__icontains=search)
        
        # Сортировка
        sort = request.query_params.get('sort', 'date')  # date, name, activity
        if sort == 'name':
            follows = follows.order_by('following__username')
        elif sort == 'activity':
            follows = follows.order_by('-following__last_activity')
        else:
            follows = follows.order_by('-created_at')
        
        total = follows.count()
        follows = follows[offset:offset + page_size]
        
        from users.serializers import UserSerializer
        users = [f.following for f in follows]
        data = UserSerializer(users, many=True, context={'request': request}).data
        
        # Добавляем информацию о подписке
        for i, user_data in enumerate(data):
            user_data['subscribed_at'] = follows[i].created_at.isoformat() if follows else None
            user_data['is_subscribed'] = True
        
        return Response({
            'results': data,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None
        })


# ==================== NOT INTERESTED (HIDDEN PROFILES) ====================

class NotInterestedViewSet(viewsets.ReadOnlyModelViewSet):
    """Скрытые профили пользователя"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserNotInterested.objects.filter(user=self.request.user).select_related('target_user')
    
    def list(self, request):
        """Получить список скрытых профилей"""
        not_interested = self.get_queryset().order_by('-created_at')
        
        # Пагинация
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size
        
        # Поиск
        search = request.query_params.get('search', '')
        if search:
            not_interested = not_interested.filter(target_user__username__icontains=search)
        
        total = not_interested.count()
        not_interested = not_interested[offset:offset + page_size]
        
        from users.serializers import UserSerializer
        users = [ni.target_user for ni in not_interested]
        data = UserSerializer(users, many=True, context={'request': request}).data
        
        # Добавляем информацию о скрытии
        for i, user_data in enumerate(data):
            user_data['hidden_at'] = not_interested[i].created_at.isoformat() if not_interested else None
            user_data['reason'] = not_interested[i].reason if not_interested else None
        
        return Response({
            'results': data,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None
        })

    @action(detail=False, methods=['post'], url_path='(?P<user_id>[^/.]+)')
    def add_or_remove(self, request, user_id=None):
        """Добавить/удалить пользователя из скрытых"""
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user == request.user:
            return Response({'error': 'Нельзя скрыть самого себя'}, status=400)
        
        existing = UserNotInterested.objects.filter(
            user=request.user,
            target_user=target_user
        ).first()
        
        if existing:
            existing.delete()
            return Response({'hidden': False, 'message': 'Пользователь удалён из скрытых'})
        else:
            reason = request.data.get('reason', '')
            UserNotInterested.objects.create(
                user=request.user,
                target_user=target_user,
                reason=reason
            )
            return Response({'hidden': True, 'message': 'Пользователь добавлен в скрытые'})


# ==================== CHATS FOR FORWARD ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chats_for_forward(request):
    """Получить список чатов для пересылки постов"""
    user = request.user
    
    # Поиск
    search = request.query_params.get('search', '')
    
    results = []
    
    try:
        # Приватные чаты
        private_chats = PrivateChat.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        )
        
        if search:
            private_chats = private_chats.filter(
                models.Q(user1__username__icontains=search, user2=user) |
                models.Q(user2__username__icontains=search, user1=user) |
                models.Q(user1__display_name__icontains=search, user2=user) |
                models.Q(user2__display_name__icontains=search, user1=user)
            )

        for chat in private_chats[:20]:
            try:
                other = chat.other_user(user)
                if other:
                    results.append({
                        'id': chat.id,
                        'type': 'private',
                        'name': other.display_name or other.username,
                        'avatar': other.avatar.url if other.avatar else None,
                        'is_online': getattr(other, 'is_online', False)
                    })
            except Exception:
                continue
        
        # Групповые чаты
        group_chats = GroupChat.objects.filter(
            members__user=user
        )
        
        if search:
            group_chats = group_chats.filter(name__icontains=search)
        
        for chat in group_chats[:20]:
            try:
                results.append({
                    'id': chat.id,
                    'type': 'group',
                    'name': chat.name,
                    'avatar': chat.avatar.url if chat.avatar else None,
                    'members_count': chat.members_count
                })
            except Exception:
                continue
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in get_chats_for_forward: {e}")
    
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forward_post_to_chat(request, chat_id=None):
    """Переслать пост в чат.
    
    Поддерживает два формата:
    1. URL с chat_id: POST /chats/{chat_id}/forward/
    2. URL без chat_id: POST /chats/forward/ с chat_id в body
    """
    post_id = request.data.get('post_id')
    if not post_id:
        return Response({'error': 'Требуется post_id'}, status=400)
    
    # Получаем chat_id из URL или из body
    if chat_id is None:
        chat_id = request.data.get('chat_id')
        if not chat_id:
            return Response({'error': 'Требуется chat_id (в URL или в body)'}, status=400)
    
    try:
        chat_id = int(chat_id)
    except (ValueError, TypeError):
        return Response({'error': 'chat_id должен быть числом'}, status=400)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Пробуем групповой чат, затем приватный
    chat = None
    chat_type = None
    
    try:
        chat = GroupChat.objects.get(id=chat_id)
        chat_type = 'group'
    except GroupChat.DoesNotExist:
        try:
            chat = PrivateChat.objects.get(id=chat_id)
            chat_type = 'private'
        except PrivateChat.DoesNotExist:
            return Response({'error': 'Чат не найден'}, status=404)
    
    # Проверяем доступ к чату
    if chat_type == 'group':
        # Проверяем через ChatMember
        try:
            from .models import ChatMember
            is_member = ChatMember.objects.filter(chat=chat, user=request.user).exists()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error checking group membership: {e}")
            is_member = False
        
        if not is_member:
            return Response({'error': 'Вы не состоите в этом чате'}, status=403)
    else:
        # Приватный чат - проверяем direct comparison
        try:
            user1_id = chat.user1_id if hasattr(chat, 'user1_id') else chat.user1.id
            user2_id = chat.user2_id if hasattr(chat, 'user2_id') else chat.user2.id
            current_user_id = request.user.id
            
            if user1_id != current_user_id and user2_id != current_user_id:
                return Response({'error': 'Вы не состоите в этом чате'}, status=403)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error checking private chat membership: {e}")
            return Response({'error': 'Ошибка проверки доступа к чату'}, status=403)
    
    # Создаём сообщение с постом
    message_text = request.data.get('message', '')
    message = Message.objects.create(
        sender=request.user,
        text=message_text,
        shared_post=post
    )
    
    if chat_type == 'group':
        message.chat = chat
    else:
        message.private_chat = chat
    
    message.save()
    
    # Обновляем счётчик репостов
    post.shares_count = (post.shares_count or 0) + 1
    post.save(update_fields=['shares_count'])
    
    return Response({
        'success': True,
        'message_id': message.id,
        'chat_id': chat.id,
        'message': 'Пост переслан'
    })


# ==================== MODERATION (REPORTS) ====================

class ModerationReportViewSet(viewsets.ModelViewSet):
    """Жалобы для модераторов"""
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            # Обычные пользователи видят только свои жалобы
            return Report.objects.filter(reporter=user)
        
        # Модераторы видят все жалобы
        queryset = Report.objects.all()
        
        # Фильтры
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        reason_filter = self.request.query_params.get('reason')
        if reason_filter:
            queryset = queryset.filter(reason=reason_filter)
        
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        return queryset.select_related('reporter')
    
    def retrieve(self, request, *args, **kwargs):
        """Получить детали жалобы"""
        instance = self.get_object()
        
        # Получаем связанный контент
        content = None
        if instance.content_type == 'post':
            try:
                content = Post.objects.get(id=instance.content_id)
                from .serializers import PostSerializer
                content_data = PostSerializer(content, context={'request': request}).data
            except Post.DoesNotExist:
                content_data = None
        elif instance.content_type == 'comment':
            try:
                content = PostComment.objects.get(id=instance.content_id)
                content_data = {
                    'id': content.id,
                    'text': content.content,
                    'author': UserSimpleSerializer(content.author).data
                }
            except PostComment.DoesNotExist:
                content_data = None
        
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['content_data'] = content_data
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Рассмотреть жалобу"""
        report = self.get_object()
        
        action = request.data.get('action')  # 'delete_content', 'warn_author', 'ban_author', 'reject'
        comment = request.data.get('comment', '')
        
        if report.status != 'pending':
            return Response({'error': 'Жалоба уже рассмотрена'}, status=400)
        
        report.status = 'resolved'
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.moderation_comment = comment
        
        # Выполняем действие
        if action == 'delete_content':
            if report.content_type == 'post':
                try:
                    post = Post.objects.get(id=report.content_id)
                    post.is_deleted = True
                    post.deleted_at = timezone.now()
                    post.save(update_fields=['is_deleted', 'deleted_at'])
                except Post.DoesNotExist:
                    pass
            elif report.content_type == 'comment':
                try:
                    comment = PostComment.objects.get(id=report.content_id)
                    comment.is_deleted = True
                    comment.deleted_at = timezone.now()
                    comment.save(update_fields=['is_deleted', 'deleted_at'])
                except PostComment.DoesNotExist:
                    pass
            report.action_taken = 'content_deleted'

        elif action == 'warn_author':
            report.action_taken = 'author_warned'
            # Здесь можно добавить отправку уведомления автору
        
        elif action == 'ban_author':
            report.action_taken = 'author_banned'
            # Получаем автора контента и блокируем
            if report.content_type == 'post':
                try:
                    post = Post.objects.get(id=report.content_id)
                    post.author.is_active = False
                    post.author.save(update_fields=['is_active'])
                except Post.DoesNotExist:
                    pass
            elif report.content_type == 'comment':
                try:
                    comment = PostComment.objects.get(id=report.content_id)
                    comment.author.is_active = False
                    comment.author.save(update_fields=['is_active'])
                except PostComment.DoesNotExist:
                    pass
        
        elif action == 'reject':
            report.status = 'rejected'
            report.action_taken = 'rejected'
        
        report.save()
        
        return Response({
            'success': True,
            'message': f'Жалоба рассмотрена: {report.get_action_taken_display() if hasattr(report, "get_action_taken_display") else action}'
        })


# ==================== EXTENDED FEED ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_extended_feed(request):
    """Расширенная лента с фильтрами и сортировкой"""
    user = request.user
    
    # Параметры
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    sort = request.query_params.get('sort', 'new')  # new, old, best, discussed
    
    # Фильтры
    anime_id = request.query_params.get('anime_id')
    my_posts = request.query_params.get('my_posts') == 'true'
    subscriptions = request.query_params.get('subscriptions') == 'true'
    groups = request.query_params.get('groups') == 'true'
    tags = request.query_params.getlist('tags')
    date_range = request.query_params.get('date_range')  # all, month, week, day
    
    # Базовый запрос
    queryset = Post.objects.filter(
        status='published',
        is_deleted=False
    )
    
    # Исключаем скрытые посты и профили
    hidden_post_ids = UserPostHidden.objects.filter(user=user).values_list('post_id', flat=True)
    hidden_user_ids = UserNotInterested.objects.filter(user=user).values_list('target_user_id', flat=True)
    queryset = queryset.exclude(id__in=hidden_post_ids).exclude(author_id__in=hidden_user_ids)
    
    # Применяем фильтры
    if anime_id:
        try:
            anime_id_int = int(anime_id)
            queryset = queryset.filter(anime_id=anime_id_int)
        except (ValueError, TypeError):
            pass  # Игнорируем невалидный anime_id (NaN, пустая строка и т.д.)
    
    if my_posts:
        queryset = queryset.filter(author=user)
    
    if subscriptions:
        following_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        queryset = queryset.filter(author_id__in=following_ids)
    
    if groups:
        group_ids = GroupMembership.objects.filter(user=user).values_list('group_id', flat=True)
        queryset = queryset.filter(group_id__in=group_ids)
    
    if tags:
        queryset = queryset.filter(hashtag_links__hashtag__name__in=tags)
    
    if date_range:
        from datetime import timedelta
        now = timezone.now()
        if date_range == 'month':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
        elif date_range == 'week':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        elif date_range == 'day':
            queryset = queryset.filter(created_at__gte=now - timedelta(days=1))
    
    # Сортировка
    if sort == 'old':
        queryset = queryset.order_by('created_at')
    elif sort == 'best':
        queryset = queryset.order_by('-likes_count', '-created_at')
    elif sort == 'discussed':
        queryset = queryset.order_by('-comments_count', '-created_at')
    else:  # new
        queryset = queryset.order_by('-created_at')
    
    # Оптимизация запроса
    queryset = queryset.select_related(
        'author', 'anime', 'group', 'playlist', 'reactor_post'
    ).prefetch_related('media_files', 'hashtag_links__hashtag')
    
    # Пагинация
    offset = (page - 1) * page_size
    total = queryset.count()
    posts = queryset[offset:offset + page_size]
    
    serializer = FeedPostSerializer(posts, many=True, context={'request': request})
    
    return Response({
        'results': serializer.data,
        'count': total,
        'next': page + 1 if offset + page_size < total else None,
        'previous': page - 1 if page > 1 else None,
        'page': page,
        'page_size': page_size
    })


# ==================== SUBSCRIPTION VIEWSET ====================

class SubscriptionViewSet(viewsets.ViewSet):
    """Управление подписками текущего пользователя"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Список пользователей, на которых подписан текущий пользователь"""
        sort = request.query_params.get('sort', 'date')  # date | name
        search = request.query_params.get('search', '').strip()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        follows = Follow.objects.filter(
            follower=request.user
        ).select_related('following')

        if search:
            follows = follows.filter(
                Q(following__username__icontains=search) |
                Q(following__display_name__icontains=search)
            )

        if sort == 'name':
            follows = follows.order_by('following__display_name', 'following__username')
        else:
            follows = follows.order_by('-created_at')

        total = follows.count()
        offset = (page - 1) * page_size
        follows_page = follows[offset:offset + page_size]

        from core.online_status import online_status as os_service
        results = []
        for follow in follows_page:
            u = follow.following
            is_online = False
            try:
                is_online = os_service.is_online(u.id)
            except Exception:
                pass
            results.append({
                'id': u.id,
                'username': u.username,
                'display_name': u.display_name or u.username,
                'avatar_url': u.avatar.url if u.avatar else None,
                'followers_count': Follow.objects.filter(following=u).count(),
                'is_online': is_online,
                'followed_at': follow.created_at.isoformat(),
            })

        return Response({
            'results': results,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None,
        })

    @action(detail=True, methods=['delete'])
    def unfollow(self, request, pk=None):
        """Отписаться от пользователя"""
        target_user = get_object_or_404(User, id=pk)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=target_user
        ).delete()
        if deleted:
            return Response({'success': True, 'message': 'Вы отписались'})
        return Response({'error': 'Вы не подписаны на этого пользователя'}, status=400)


# ==================== NOT INTERESTED VIEWSET ====================

class NotInterestedViewSet(viewsets.ViewSet):
    """Пользователи, отмеченные как неинтересные"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Список скрытых пользователей"""
        search = request.query_params.get('search', '').strip()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        qs = UserNotInterested.objects.filter(
            user=request.user
        ).select_related('target_user')

        if search:
            qs = qs.filter(
                Q(target_user__username__icontains=search) |
                Q(target_user__display_name__icontains=search)
            )
            
        qs = qs.order_by('-created_at')
        total = qs.count()
        offset = (page - 1) * page_size
        page_qs = qs[offset:offset + page_size]

        results = []
        for item in page_qs:
            u = item.target_user
            results.append({
                'id': u.id,
                'username': u.username,
                'display_name': u.display_name or u.username,
                'avatar_url': u.avatar.url if u.avatar else None,
                'hidden_at': item.created_at.isoformat(),
            })

        return Response({
            'results': results,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None,
        })

    def destroy(self, request, pk=None):
        """Убрать пользователя из списка неинтересных"""
        target_user = get_object_or_404(User, id=pk)
        deleted, _ = UserNotInterested.objects.filter(
            user=request.user, target_user=target_user
        ).delete()
        if deleted:
            return Response({'success': True, 'message': 'Пользователь убран из списка'})
        return Response({'error': 'Пользователь не найден в списке'}, status=404)


# ==================== HIDE/NOT-INTERESTED FOR AUTHOR ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hide_author_from_feed(request, user_id):
    """Скрыть все посты автора (добавить в список неинтересных)"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return Response({'error': 'Нельзя скрыть самого себя'}, status=400)
    UserNotInterested.objects.get_or_create(
        user=request.user, target_user=target_user
    )
    return Response({'success': True, 'message': f'Посты от @{target_user.username} скрыты'})


# ==================== MODERATION REPORTS VIEWSET ====================

class ModerationReportViewSet(viewsets.ViewSet):
    """Модерация жалоб (только для модераторов)"""
    permission_classes = [IsAuthenticated]

    def _check_moderator(self, user):
        return user.is_staff or user.is_superuser or getattr(user, 'role', None) in ('moderator', 'admin')

    def list(self, request):
        """Список жалоб для модераторов"""
        if not self._check_moderator(request.user):
            return Response({'error': 'Нет доступа'}, status=403)

        report_status = request.query_params.get('status', 'pending')
        content_type = request.query_params.get('content_type', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        qs = Report.objects.select_related('reporter', 'resolved_by')

        if report_status:
            qs = qs.filter(status=report_status)
        if content_type:
            qs = qs.filter(content_type=content_type)

        qs = qs.order_by('-created_at')
        total = qs.count()
        offset = (page - 1) * page_size
        page_qs = qs[offset:offset + page_size]

        results = []
        for report in page_qs:
            # Получаем данные о контенте
            content_data = None
            if report.content_type == 'post':
                try:
                    post = Post.objects.get(id=report.content_id)
                    content_data = {
                        'id': post.id,
                        'text': post.text[:200] if post.text else '',
                        'author': post.author.username if post.author else None,
                    }
                except Post.DoesNotExist:
                    pass
            elif report.content_type == 'comment':
                from .models import PostComment
                try:
                    comment = PostComment.objects.get(id=report.content_id)
                    content_data = {
                        'id': comment.id,
                        'text': comment.content[:200] if comment.content else '',
                        'author': comment.author.username if comment.author else None,
                    }
                except Exception:
                    pass

            results.append({
                'id': report.id,
                'content_type': report.content_type,
                'content_id': report.content_id,
                'reason': report.reason,
                'comment': report.comment,
                'status': report.status,
                'reporter': {
                    'id': report.reporter.id,
                    'username': report.reporter.username,
                },
                'resolved_by': {
                    'id': report.resolved_by.id,
                    'username': report.resolved_by.username,
                } if report.resolved_by else None,
                'resolved_at': report.resolved_at.isoformat() if report.resolved_at else None,
                'created_at': report.created_at.isoformat(),
                'content': content_data,
            })

        return Response({
            'results': results,
            'count': total,
            'next': page + 1 if offset + page_size < total else None,
            'previous': page - 1 if page > 1 else None,
        })

    def partial_update(self, request, pk=None):
        """Обработать жалобу (resolve/reject + optional action)"""
        if not self._check_moderator(request.user):
            return Response({'error': 'Нет доступа'}, status=403)

        report = get_object_or_404(Report, id=pk)

        new_status = request.data.get('status')  # resolved / rejected
        action_type = request.data.get('action')  # delete_content | warn | None
        moderator_comment = request.data.get('moderator_comment', '')

        if new_status not in ('resolved', 'rejected'):
            return Response({'error': 'Неверный статус'}, status=400)

        report.status = new_status
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        if moderator_comment:
            report.comment = (report.comment or '') + f'\n[Модератор]: {moderator_comment}'
        report.save()

        # Действие над контентом
        if action_type == 'delete_content' and new_status == 'resolved':
            if report.content_type == 'post':
                try:
                    post = Post.objects.get(id=report.content_id)
                    post.is_deleted = True
                    post.save(update_fields=['is_deleted'])
                except Post.DoesNotExist:
                    pass
            elif report.content_type == 'comment':
                from .models import PostComment
                try:
                    comment = PostComment.objects.get(id=report.content_id)
                    comment.is_deleted = True
                    comment.save(update_fields=['is_deleted'])
                except Exception:
                    pass

        return Response({
            'success': True,
            'report_id': report.id,
            'status': report.status,
            'action': action_type,
        })


# ==================== ANIME DISCUSSION GROUP ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_franchise_discussions(request):
    """Получить список всех обсуждений франшиз"""
    from anime.models import Franchise
    from .models import GroupChat, ChatMember, ChatTopic
    
    # Получаем все группы обсуждений франшиз
    franchise_groups = GroupChat.objects.filter(
        discussion_type='franchise'
    ).select_related('created_by').prefetch_related('members')
    
    result = []
    for group in franchise_groups:
        # Получаем топики
        topics = ChatTopic.objects.filter(chat=group).order_by('order')[:10]
        
        # Считаем участников
        members_count = group.members.count()
        
        result.append({
            'id': group.id,
            'name': group.name,
            'franchise_id': group.franchise_id,
            'members_count': members_count,
            'topics_count': topics.count(),
            'avatar_url': group.avatar.url if group.avatar else None,
            'created_at': group.created_at,
        })
    
    return Response({
        'discussions': result,
        'total': len(result)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_franchise_discussion_group(request, franchise_id):
    """Получить групповой чат для обсуждения франшизы по franchise_id.
    
    Если группа ещё не создана — создаём её автоматически.
    """
    from anime.models import Franchise, Anime
    from .models import GroupChat, ChatMember
    from .models_chat import ChatTopic
    
    # Получаем чистый Django request для построения URL
    django_request = request._request if hasattr(request, '_request') else request
    
    def _get_poster_url(obj, req=None):
        if obj is None:
            return None
        if getattr(obj, 'poster', None) and hasattr(obj.poster, 'url'):
            url = obj.poster.url
            if req:
                return req.build_absolute_uri(url)
            return url
        if getattr(obj, 'poster_url', None):
            return obj.poster_url
        return None

    try:
        franchise = Franchise.objects.get(id=franchise_id)
    except Franchise.DoesNotExist:
        return Response({'error': 'Франшиза не найдена'}, status=404)
    
    # Постер франшизы — берём у первой части
    first_part = (
        Anime.objects.filter(franchise=franchise)
        .order_by('franchise_order', 'year', 'id')
        .first()
    )
    franchise_poster_url = _get_poster_url(franchise, django_request) or _get_poster_url(first_part, django_request)
    
    # Ищем или создаём главную группу франшизы
    chat, created = GroupChat.objects.get_or_create(
        franchise_id=franchise.id,
        defaults={
            'name': franchise.name,
            'description': franchise.description or '',
            'created_by': request.user,
            'is_public': True,
            'discussion_type': 'franchise',
            'folder_type': 'discussions',
        }
    )
    
    # Исправляем название если нужно
    if not created:
        dirty = False
        clean_name = franchise.name
        if chat.name != clean_name and (
            chat.name.startswith('Обсуждение:') or
            chat.name.startswith('Обсуждение ') or
            chat.name.lower().startswith('обсуждение')
        ):
            chat.name = clean_name
            dirty = True
        if dirty:
            chat.save(update_fields=['name'])
    
    # Убеждаемся что пользователь в чате
    ChatMember.objects.get_or_create(
        chat=chat, user=request.user,
        defaults={'is_admin': created}
    )
     
    # Общая тема
    ChatTopic.objects.get_or_create(
        chat=chat, anime=None,
        defaults={'title': franchise.name, 'order': 0}
    )
    
    # Темы для каждой части
    parts = Anime.objects.filter(franchise=franchise).order_by('franchise_order', 'year', 'id')
    for idx, part in enumerate(parts, start=1):
        ChatTopic.objects.get_or_create(
            chat=chat, anime=part,
            defaults={
                'title': part.title_ru or part.title_en or f'Часть #{part.id}',
                'order': idx,
            }
        )
        
    # Сериализуем с топиками
    topics = ChatTopic.objects.filter(chat=chat).order_by('order').select_related('anime')
    topics_data = []
    for t in topics:
        poster = _get_poster_url(t.anime, django_request) if t.anime else franchise_poster_url
        topics_data.append({
            'id': t.id,
            'title': t.title,
            'order': t.order,
            'anime_id': t.anime_id,
            'anime_title': (t.anime.title_ru or t.anime.title_en) if t.anime else None,
            'poster_url': poster,
            'is_general': t.anime_id is None,
            'is_current': False,
        })
    
    chat_data = GroupChatSerializer(chat, context={'request': request}).data
    if not chat_data.get('avatar') and franchise_poster_url:
        chat_data['avatar'] = franchise_poster_url
    if not chat_data.get('avatar_url') and franchise_poster_url:
        chat_data['avatar_url'] = franchise_poster_url
    chat_data['topics'] = topics_data
    chat_data['discussion_type'] = 'franchise'
    chat_data['type'] = 'franchise'
    chat_data['franchise_id'] = franchise.id
    chat_data['franchise'] = {
        'id': franchise.id,
        'name': franchise.name,
    }
    
    return Response(chat_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_franchise_discussion_group(request, franchise_id):
    """Присоединиться к групповому чату обсуждения франшизы"""
    from anime.models import Franchise
    from .models import GroupChat, ChatMember
    
    try:
        franchise = Franchise.objects.get(id=franchise_id)
    except Franchise.DoesNotExist:
        return Response({'error': 'Франшиза не найдена'}, status=404)
    
    # Ищем группу
    chat = GroupChat.objects.filter(franchise_id=franchise_id).first()
    if not chat:
        return Response({'error': 'Группа обсуждения не найдена. Сначала получите её через GET /franchise/<id>/discussion/'}, status=404)
    
    # Проверяем, не забанен ли пользователь
    member = ChatMember.objects.filter(chat=chat, user=request.user).first()
    if member and member.is_banned:
        return Response({'error': 'Вы заблокированы в этом чате'}, status=403)
    
    # Добавляем пользователя
    ChatMember.objects.get_or_create(chat=chat, user=request.user)
    
    return Response({'success': True, 'chat_id': chat.id})
     