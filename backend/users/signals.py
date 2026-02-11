from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in
from .models import User


@receiver(pre_save, sender=User)
def generate_unique_id(sender, instance, **kwargs):
    """Генерирует уникальный ID перед сохранением пользователя"""
    if not instance.unique_id:
        import random
        import string

        # Генерируем уникальный ID
        while True:
            # Генерируем 12-значный ID
            unique_id = ''.join(random.choices(string.digits, k=12))

            # Проверяем уникальность
            if not User.objects.filter(unique_id=unique_id).exclude(pk=instance.pk).exists():
                instance.unique_id = unique_id
                break


@receiver(user_logged_in, sender=User)
def ensure_unique_id_on_login(sender, request, user, **kwargs):
    """Убеждается, что у пользователя есть уникальный ID при входе"""
    if not user.unique_id:
        user.ensure_unique_id()
