
# ──────────────────────────────────────────────────────────────────────
#  Дополнительные задачи Celery для системы чатов — добавить в tasks.py
# ──────────────────────────────────────────────────────────────────────


@shared_task(name='social.cleanup_expired_bans')
def cleanup_expired_bans():
    """Автоматически снимать истёкшие блокировки"""
    from .models_chat import ChatBan
    count = ChatBan.objects.filter(
        until_date__lt=timezone.now(),
        until_date__isnull=False
    ).delete()[0]
    logger.info(f"cleanup_expired_bans: удалено {count} блокировок")
    return count


@shared_task(name='social.cleanup_expired_restrictions')
def cleanup_expired_restrictions():
    """Снимать истёкшие ограничения"""
    from .models_chat import ChatRestriction
    count = ChatRestriction.objects.filter(
        until_date__lt=timezone.now(),
        until_date__isnull=False
    ).delete()[0]
    logger.info(f"cleanup_expired_restrictions: удалено {count} ограничений")
    return count


@shared_task(name='social.cleanup_expired_invite_links')
def cleanup_expired_invite_links():
    """Отзывать истёкшие ссылки-приглашения"""
    from .models_chat import ChatInviteLink
    count = ChatInviteLink.objects.filter(
        expires_at__lt=timezone.now(),
        is_revoked=False
    ).update(is_revoked=True)
    logger.info(f"cleanup_expired_invite_links: отозвано {count} ссылок")
    return count


@shared_task(name='social.update_group_stats_cache')
def update_group_stats_cache(chat_id: int):
    """Обновить кэшированную статистику группы"""
    from .models_chat import GroupChatSettings
    from .models import Message as Msg
    try:
        gs, _ = GroupChatSettings.objects.get_or_create(chat_id=chat_id)
        gs.refresh_cache()
        logger.info(f"update_group_stats_cache: обновлён кэш для группы {chat_id}")
    except Exception as e:
        logger.error(f"update_group_stats_cache error: {e}")


@shared_task(name='social.send_scheduled_messages')
def send_scheduled_messages():
    """Отправить запланированные сообщения"""
    from .models_chat import ScheduledMessage
    from .models import Message as Msg
    now = timezone.now()
    pending = ScheduledMessage.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    ).select_related('sender', 'chat', 'private_chat')

    sent = 0
    for sm in pending:
        try:
            msg = Msg.objects.create(
                sender=sm.sender,
                chat=sm.chat,
                private_chat=sm.private_chat,
                text=sm.text,
                media=sm.media,
                media_type=sm.media_type,
            )
            sm.status = 'sent'
            sm.sent_at = now
            sm.save(update_fields=['status', 'sent_at'])
            sent += 1

            # Обновить время последнего сообщения в чате
            if sm.chat:
                sm.chat.last_message_at = now
                sm.chat.save(update_fields=['last_message_at'])
            elif sm.private_chat:
                sm.private_chat.last_message_at = now
                sm.private_chat.save(update_fields=['last_message_at'])

        except Exception as e:
            sm.status = 'failed'
            sm.error_message = str(e)
            sm.save(update_fields=['status', 'error_message'])
            logger.error(f"send_scheduled_messages: ошибка для {sm.id}: {e}")

    logger.info(f"send_scheduled_messages: отправлено {sent} сообщений")
    return sent


@shared_task(name='social.cleanup_old_messages')
def cleanup_old_messages(days: int = 365):
    """Удалять старые сообщения (не закреплённые)"""
    from .models import Message as Msg
    cutoff = timezone.now() - timedelta(days=days)
    count = Msg.objects.filter(
        created_at__lt=cutoff,
        is_pinned=False,
        is_deleted=False,
    ).update(is_deleted=True, deleted_at=timezone.now())
    logger.info(f"cleanup_old_messages: помечено удалёнными {count} сообщений")
    return count
