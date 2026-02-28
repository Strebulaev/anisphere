"""
All missing view actions for social app
"""
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
import logging

from .models import (
    Follow, Post, PostLike, PostDislike, Bookmark, Report,
    PostComment, PostCommentLike, PostCommentDislike, Repost,
    Achievement, UserAchievement, Group, GroupMembership,
    Message, PrivateChat, GroupChat, ChatSettings,
    ChatFolder, ChatInvite, ChatRole, Reaction, Attachment,
    EmailLog, FeedView, UserPostHidden, Hashtag, PostMedia,
    PostAttachment, UserMention, PostHashtag
)
from users.models import User

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
        return Response({'following': True, 'message': 'Вы подписались'})


# ==================== POST LIKE/DISLIKE ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_like(request, post_id):
    """Лайк/дизлайк поста"""
    post = get_object_or_404(Post, id=post_id)
    
    if post.author == request.user:
        return Response({'error': 'Нельзя лайкать свой пост'}, status=400)
    
    existing_like = PostLike.objects.filter(user=request.user, post=post).first()
    existing_dislike = PostDislike.objects.filter(user=request.user, post=post).first()
    
    if existing_like:
        existing_like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save(update_fields=['likes_count'])
        return Response({'liked': False, 'likes_count': post.likes_count})
    else:
        if existing_dislike:
            existing_dislike.delete()
            post.dislikes_count = max(0, post.dislikes_count - 1)
        PostLike.objects.create(user=request.user, post=post)
        post.likes_count += 1
        post.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'liked': True, 'likes_count': post.likes_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_post_dislike(request, post_id):
    """Дизлайк поста"""
    post = get_object_or_404(Post, id=post_id)
    
    if post.author == request.user:
        return Response({'error': 'Нельзя дизлайкать свой пост'}, status=400)
    
    existing_dislike = PostDislike.objects.filter(user=request.user, post=post).first()
    existing_like = PostLike.objects.filter(user=request.user, post=post).first()
    
    if existing_dislike:
        existing_dislike.delete()
        post.dislikes_count = max(0, post.dislikes_count - 1)
        post.save(update_fields=['dislikes_count'])
        return Response({'disliked': False, 'dislikes_count': post.dislikes_count})
    else:
        if existing_like:
            existing_like.delete()
            post.likes_count = max(0, post.likes_count - 1)
        PostDislike.objects.create(user=request.user, post=post)
        post.dislikes_count += 1
        post.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'disliked': True, 'dislikes_count': post.dislikes_count})


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
    comment = get_object_or_404(PostComment, id=comment_id)
    
    existing_like = PostCommentLike.objects.filter(user=request.user, comment=comment).first()
    existing_dislike = PostCommentDislike.objects.filter(user=request.user, comment=comment).first()
    
    if existing_like:
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=['likes_count'])
        return Response({'liked': False, 'likes_count': comment.likes_count})
    else:
        if existing_dislike:
            existing_dislike.delete()
            comment.dislikes_count = max(0, comment.dislikes_count - 1)
        PostCommentLike.objects.create(user=request.user, comment=comment)
        comment.likes_count += 1
        comment.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'liked': True, 'likes_count': comment.likes_count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    """Дизлайк комментария"""
    comment = get_object_or_404(PostComment, id=comment_id)
    
    existing_dislike = PostCommentDislike.objects.filter(user=request.user, comment=comment).first()
    existing_like = PostCommentLike.objects.filter(user=request.user, comment=comment).first()
    
    if existing_dislike:
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=['dislikes_count'])
        return Response({'disliked': False, 'dislikes_count': comment.dislikes_count})
    else:
        if existing_like:
            existing_like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
        PostCommentDislike.objects.create(user=request.user, comment=comment)
        comment.dislikes_count += 1
        comment.save(update_fields=['likes_count', 'dislikes_count'])
        return Response({'disliked': True, 'dislikes_count': comment.dislikes_count})


# ==================== POST ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    """Закрепить пост"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    # Снимаем закрепление с других постов
    Post.objects.filter(author=request.user, is_pinned=True).update(is_pinned=False)
    
    post.is_pinned = True
    post.pinned_at = timezone.now()
    post.save(update_fields=['is_pinned', 'pinned_at'])
    
    return Response({'success': True, 'message': 'Пост закреплен'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    """Открепить пост"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    post.is_pinned = False
    post.pinned_at = None
    post.save(update_fields=['is_pinned', 'pinned_at'])
    
    return Response({'success': True, 'message': 'Пост откреплен'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    """Пожаловаться на пост"""
    post = get_object_or_404(Post, id=post_id)
    
    reason = request.data.get('reason', 'other')
    comment = request.data.get('comment', '')
    
    report = Report.objects.create(
        reporter=request.user,
        content_type='post',
        content_id=post_id,
        reason=reason,
        comment=comment,
        status='pending'
    )
    
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
    """Сделать репост"""
    original_post = get_object_or_404(Post, id=post_id)
    
    if original_post.post_type == 'system':
        return Response({'error': 'Нельзя репостнуть системный пост'}, status=400)
    
    if original_post.visibility == 'private':
        return Response({'error': 'Нельзя репостнуть приватный пост'}, status=400)
    
    comment = request.data.get('comment', '')
    
    repost = Repost.objects.create(
        original_post=original_post,
        user=request.user,
        comment=comment
    )
    
    original_post.reposts_count += 1
    original_post.save(update_fields=['reposts_count'])
    
    return Response({'success': True, 'repost_id': repost.id})


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
    """Получить ответы на комментарий"""
    comment = get_object_or_404(PostComment, id=comment_id)
    replies = PostComment.objects.filter(parent=comment).select_related('author')[:20]
    
    from .serializers import CommentSerializer
    serializer = CommentSerializer(replies, many=True)
    
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
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    # Проверка времени (5 минут)
    if (timezone.now() - post.created_at).total_seconds() > 300:
        return Response({'error': 'Время редактирования истекло'}, status=400)
    
    # Нельзя менять тип поста
    new_type = request.data.get('post_type')
    if new_type and new_type != post.post_type:
        return Response({'error': 'Нельзя менять тип поста'}, status=400)
    
    if 'title' in request.data:
        post.title = request.data['title']
    
    if 'text' in request.data:
        text = request.data['text']
        if text and len(text) > 5000:
            return Response({'error': 'Максимум 5000 символов'}, status=400)
        post.text = text
    
    if 'visibility' in request.data:
        post.visibility = request.data['visibility']
    
    if 'allow_comments' in request.data:
        post.allow_comments = request.data['allow_comments']
    
    if 'is_spoiler' in request.data:
        post.is_spoiler = request.data['is_spoiler']
    
    post.edited_at = timezone.now()
    post.save()
    
    from .serializers import PostSerializer
    return Response(PostSerializer(post, context={'request': request}).data)


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
    """Получить популярные посты"""
    posts = Post.objects.filter(
        status='published',
        is_deleted=False
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

class FavoriteViewSet(viewsets.ModelViewSet):
    """Избранное"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # Заглушка


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
    
    def get_queryset(self):
        return ChatInvite.objects.filter(created_by=self.request.user)


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
    """Загрузить вложение"""
    return Response({'success': True, 'url': ''})


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
    
    # Приватные чаты
    private_chats = PrivateChat.objects.filter(members__user=user)
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
    serializer_class = None
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return PostComment.objects.filter(post_id=post_id).select_related('author')


class BookmarkViewSet(viewsets.ModelViewSet):
    """Закладки"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('post')


class ReportViewSet(viewsets.ModelViewSet):
    """Жалобы"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)


class PostMediaViewSet(viewsets.ModelViewSet):
    """Медиа постов"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PostMedia.objects.all()
