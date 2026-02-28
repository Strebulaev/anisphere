"""Сигналы для пользователей"""

from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.auth import user_logged_in

from social.models import Post
from .models import User


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
    
@receiver(pre_save, sender=User)
def generate_unique_id(sender, instance, **kwargs):
    """Генерирует уникальный ID перед сохранением пользователя"""
    if not instance.unique_id:
        import random
        import string

        while True:
            unique_id = ''.join(random.choices(string.digits, k=12))
            if not User.objects.filter(unique_id=unique_id).exclude(pk=instance.pk).exists():
                instance.unique_id = unique_id
                break


@receiver(user_logged_in, sender=User)
def ensure_unique_id_on_login(sender, request, user, **kwargs):
    """Убеждается, что у пользователя есть уникальный ID при входе"""
    if not user.unique_id:
        user.ensure_unique_id()
