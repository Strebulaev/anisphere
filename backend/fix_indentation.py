# -*- coding: utf-8 -*-
import re

# Fix views_all_actions.py
with open('social/views_all_actions.py', 'r', encoding='utf-8') as f:
 content = f.read()

# Fix toggle_follow - add proper indentation (4 spaces)
old_toggle_follow = '''@api_view(['POST'])
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
 NotificationService.send_follow_notification(request.user, target_user)
 except Exception as e:
 print(f'Failed to send follow notification: {e}')
        
 return Response({'following': True, 'message': 'Вы подписались'})'''

new_toggle_follow = '''@api_view(['POST'])
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
 NotificationService.send_follow_notification(request.user, target_user)
 except Exception as e:
 print(f'Failed to send follow notification: {e}')
        
 return Response({'following': True, 'message': 'Вы подписались'})'''

content = content.replace(old_toggle_follow, new_toggle_follow)

# Fix toggle_post_like - add proper indentation (4 spaces)
old_toggle_post_like = '''@api_view(['POST'])
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
 else:
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
 NotificationService.send_like_notification(post, request.user)
 except Exception as e:
 print(f'Failed to send like notification: {e}')
 
 return Response({'liked': True, 'likes_count': post.likes_count, 'dislikes_count': post.dislikes_count})'''

new_toggle_post_like = '''@api_view(['POST'])
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
 else:
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
 NotificationService.send_like_notification(post, request.user)
 except Exception as e:
 print(f'Failed to send like notification: {e}')
    
 return Response({'liked': True, 'likes_count': post.likes_count, 'dislikes_count': post.dislikes_count})'''

content = content.replace(old_toggle_post_like, new_toggle_post_like)

with open('social/views_all_actions.py', 'w', encoding='utf-8') as f:
 f.write(content)

print('views_all_actions.py fixed')
