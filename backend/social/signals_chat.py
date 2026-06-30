
# Дописываем в signals.py - сигналы для системы чатов

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


@receiver(post_save, sender='social.ChatMember')
def on_member_saved(sender, instance, created, **kwargs):
    """Обновить кэш при изменении участника"""
    try:
        # Инвалидируем кэш настроек чата для всех участников
        cache_pattern_key = f"chat_settings:*:group:{instance.chat_id}"
        cache.delete(f"chat_settings:{instance.user_id}:group:{instance.chat_id}")

        # Обновляем кэшированные настройки группы
        from .models_chat import GroupChatSettings
        gs, _ = GroupChatSettings.objects.get_or_create(chat_id=instance.chat_id)
        gs.members_count = instance.chat.members.count()
        gs.save(update_fields=['members_count', 'cache_updated_at'])
    except Exception:
        pass


@receiver(post_delete, sender='social.ChatMember')
def on_member_deleted(sender, instance, **kwargs):
    """Обновить кэш при удалении участника"""
    try:
        cache.delete(f"chat_settings:{instance.user_id}:group:{instance.chat_id}")
        from .models_chat import GroupChatSettings
        try:
            gs = GroupChatSettings.objects.get(chat_id=instance.chat_id)
            gs.members_count = max(0, gs.members_count - 1)
            gs.save(update_fields=['members_count', 'cache_updated_at'])
        except GroupChatSettings.DoesNotExist:
            pass
    except Exception:
        pass


@receiver(post_save, sender='social.Message')
def on_message_saved(sender, instance, created, **kwargs):
    """Обновить счётчики при новом сообщении"""
    if not created:
        return
    try:
        if instance.chat_id:
            from .models_chat import GroupChatSettings
            gs, _ = GroupChatSettings.objects.get_or_create(chat_id=instance.chat_id)
            gs.messages_count = sender.objects.filter(chat_id=instance.chat_id).count()
            gs.last_message_at = instance.created_at
            gs.save(update_fields=['messages_count', 'last_message_at', 'cache_updated_at'])
    except Exception:
        pass


@receiver(post_save, sender='social.ChatWallpaper')
def on_wallpaper_saved(sender, instance, **kwargs):
    """Инвалидация кэша при изменении обоев"""
    try:
        if instance.user_id:
            chat_type = 'group' if instance.chat_id else 'private'
            chat_id = instance.chat_id or instance.private_chat_id
            if chat_id:
                cache.delete(f"chat_wallpaper:{instance.user_id}:{chat_type}:{chat_id}")
                cache.delete(f"chat_settings:{instance.user_id}:{chat_type}:{chat_id}")
    except Exception:
        pass


@receiver(post_save, sender='social.ChatTheme')
def on_theme_saved(sender, instance, **kwargs):
    """Инвалидация кэша при изменении темы"""
    try:
        if instance.user_id:
            chat_type = 'group' if instance.chat_id else 'private'
            chat_id = instance.chat_id or instance.private_chat_id
            if chat_id:
                cache.delete(f"chat_theme:{instance.user_id}:{chat_type}:{chat_id}")
                cache.delete(f"chat_settings:{instance.user_id}:{chat_type}:{chat_id}")
    except Exception:
        pass


@receiver(post_save, sender='social.PrivateChatSettings')
def on_private_chat_settings_saved(sender, instance, **kwargs):
    """Инвалидация кэша при изменении настроек личного чата"""
    try:
        cache.delete(f"chat_settings:{instance.user_id}:private:{instance.chat_id}")
    except Exception:
        pass
