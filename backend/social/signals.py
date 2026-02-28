"""
Сигналы для автоматического создания системных постов

ПРИМЕЧАНИЕ: Системные посты для уровней и достижений будут создаваться
через API вызовы SystemPostService, а не через сигналы, так как
соответствующие модели (UserLevel, UserAchievement) ещё не созданы.
"""
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from users.models import User
from .models import Post, Follow


@receiver(post_save, sender=Post)
def on_post_created(sender, instance, created, **kwargs):
    """Publish new_post event to Redis for followers"""
    if not created:
        return
    if instance.status != 'published' or instance.is_deleted:
        return
    try:
        from core.redis_events import event_publisher
        follower_ids = list(
            Follow.objects.filter(following=instance.author)
            .values_list('follower_id', flat=True)
        )
        event_publisher.publish_event('new_post', {
            'post_id': instance.id,
            'author_id': instance.author_id,
            'author_username': instance.author.username,
            'post_type': instance.post_type,
            'text_preview': (instance.text or '')[:100],
        }, target_users=follower_ids)
    except Exception:
        pass


# Функции для создания системных постов (вызываются из views/management commands)
def create_level_up_post(user, new_level):
    """Создать системный пост при повышении уровня"""
    from .services import SystemPostService
    
    existing_posts = Post.objects.filter(
        author=user,
        post_type='system',
        system_type='level_up',
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    )
    
    if not existing_posts.exists():
        return SystemPostService.create_level_up_post(
            user=user,
            new_level=new_level
        )
    return None
        

def create_achievement_post(user, achievement_name, achievement_level):
    """Создать системный пост при получении достижения"""
    from .services import SystemPostService
    
    existing_posts = Post.objects.filter(
        author=user,
        post_type='system',
        system_type='achievement_unlocked',
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    )
    
    if not existing_posts.exists():
        return SystemPostService.create_achievement_post(
            user=user,
            achievement_name=achievement_name,
            achievement_level=achievement_level
        )
    return None
        

def create_contest_win_post(user, contest_title, place):
    """Создать системный пост при победе в конкурсе"""
    from .services import SystemPostService
    return SystemPostService.create_contest_win_post(
        user=user,
        contest_title=contest_title,
        place=place
    )
