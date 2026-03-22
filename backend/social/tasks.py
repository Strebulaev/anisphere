"""
Фоновые задачи для чатов и уведомлений
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from .models import Message, ChatInvite, Attachment, EmailLog, GroupChat, PrivateChat, ChatMember, ChatAdminLog
from users.models import User
import logging

logger = logging.getLogger(__name__)


# ==================== ЧАТЫ - ОСНОВНЫЕ ЗАДАЧИ ====================

@shared_task
def process_bulk_members(chat_id: int, user_ids: list, inviter_id: int):
    """
    Массовое добавление участников в чат.
    """
    try:
        chat = GroupChat.objects.get(id=chat_id)
        inviter = User.objects.get(id=inviter_id)

        added_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                if not ChatMember.objects.filter(chat=chat, user=user).exists():
                    ChatMember.objects.create(
                        user=user,
                        chat=chat,
                        can_send_messages=chat.can_send_media,
                        can_send_media=chat.can_send_media
                    )
                    added_count += 1
            except User.DoesNotExist:
                continue

        # Логируем
        ChatAdminLog.objects.create(
            chat=chat,
            user=inviter,
            action='member_joined',
            details={'count': added_count, 'method': 'bulk_add_task'}
        )

        return {'success': True, 'added_count': added_count}
    
    except (GroupChat.DoesNotExist, User.DoesNotExist) as e:
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_messages(days: int = 30):
    """
    Очистка старых сообщений (soft delete).
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Получаем старые сообщения, которые не закреплены
    old_messages = Message.objects.filter(
        created_at__lt=cutoff_date,
        is_pinned=False,
        is_deleted=False
    )
    
    count = old_messages.count()
    
    # Помечаем как удалённые (soft delete)
    old_messages.update(
        is_deleted=True,
        deleted_at=timezone.now()
    )
    
    logger.info(f"Cleaned up {count} old messages")
    return {'status': 'completed', 'deleted_count': count}


@shared_task
def cleanup_expired_bans():
    """
    Снятие истёкших блокировок.
    """
    from .models_chat import ChatBan
    
    now = timezone.now()
    
    # Удаляем истёкшие временные блокировки
    expired_bans = ChatBan.objects.filter(
        until_date__isnull=False,
        until_date__lt=now
    )
    
    count = expired_bans.count()
    expired_bans.delete()
    
    logger.info(f"Removed {count} expired bans")
    return {'status': 'completed', 'removed_count': count}


@shared_task
def cleanup_expired_restrictions():
    """
    Снятие истёкших ограничений.
    """
    from .models_chat import ChatRestriction
    
    now = timezone.now()
    
    # Удаляем истёкшие ограничения
    expired_restrictions = ChatRestriction.objects.filter(
        until_date__isnull=False,
        until_date__lt=now
    )
    
    count = expired_restrictions.count()
    expired_restrictions.delete()
    
    logger.info(f"Removed {count} expired restrictions")
    return {'status': 'completed', 'removed_count': count}


@shared_task
def cleanup_old_invites():
    """
    Удаление истёкших приглашений.
    """
    from .models_chat import ChatInviteLink
    
    now = timezone.now()
    
    # Находим истёкшие приглашения
    expired_invites = ChatInviteLink.objects.filter(
        expires_at__isnull=False,
        expires_at__lt=now,
        is_revoked=False
    )
    
    count = expired_invites.count()
    expired_invites.update(is_revoked=True)
    
    logger.info(f"Revoked {count} expired invites")
    return {'status': 'completed', 'revoked_count': count}


@shared_task
def update_members_count():
    """
    Обновление счётчиков участников во всех чатах.
    """
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        actual_count = chat.members.count()
        # Обновляем кэшированные настройки если есть
        from .models_chat import GroupChatSettings
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        settings.members_count = actual_count
        settings.save(update_fields=['members_count'])
        updated_count += 1
    
    logger.info(f"Updated members count for {updated_count} chats")
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def update_online_counts():
    """
    Обновление счётчиков онлайн участников.
    """
    from core.online_status import online_status
    from .models_chat import GroupChatSettings
    
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        online_count = sum(
            1 for member in chat.members.all()
            if online_status.is_online(member.user_id)
        )
        
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        settings.online_count = online_count
        settings.save(update_fields=['online_count'])
        updated_count += 1
    
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def process_scheduled_messages():
    """
    Обработка запланированных сообщений.
    """
    from .models_chat import ScheduledMessage
    
    now = timezone.now()
    
    # Находим сообщения, которые нужно отправить
    scheduled = ScheduledMessage.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )
    
    sent_count = 0
    failed_count = 0
    
    for scheduled_msg in scheduled:
        try:
            # Создаём сообщение
            msg_data = {
                'sender': scheduled_msg.sender,
                'text': scheduled_msg.text,
                'media': scheduled_msg.media if scheduled_msg.media else None,
                'media_type': scheduled_msg.media_type,
            }
            
            if scheduled_msg.chat:
                msg_data['chat'] = scheduled_msg.chat
            elif scheduled_msg.private_chat:
                msg_data['private_chat'] = scheduled_msg.private_chat
            
            Message.objects.create(**msg_data)
            
            scheduled_msg.status = 'sent'
            scheduled_msg.sent_at = now
            scheduled_msg.save(update_fields=['status', 'sent_at'])
            
            # Если повторяющееся, создаём следующее
            if scheduled_msg.is_recurring and scheduled_msg.recurring_interval:
                next_date = now + timedelta(days=scheduled_msg.recurring_interval)
                ScheduledMessage.objects.create(
                    sender=scheduled_msg.sender,
                    chat=scheduled_msg.chat,
                    private_chat=scheduled_msg.private_chat,
                    text=scheduled_msg.text,
                    scheduled_at=next_date,
                    is_recurring=True,
                    recurring_interval=scheduled_msg.recurring_interval
                )
            
            sent_count += 1
            
        except Exception as e:
            scheduled_msg.status = 'failed'
            scheduled_msg.error_message = str(e)
            scheduled_msg.save(update_fields=['status', 'error_message'])
            failed_count += 1
            logger.error(f"Error sending scheduled message {scheduled_msg.id}: {e}")
    
    return {
        'status': 'completed',
        'sent_count': sent_count,
        'failed_count': failed_count
    }


@shared_task
def update_chat_statistics():
    """
    Обновление статистики чатов.
    """
    from .models_chat import GroupChatSettings
    
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        
        # Обновляем счётчики
        settings.messages_count = Message.objects.filter(chat=chat).count()
        settings.members_count = chat.members.count()
        
        # Последнее сообщение
        last_msg = Message.objects.filter(chat=chat).order_by('-created_at').first()
        if last_msg:
            settings.last_message_at = last_msg.created_at
        
        # Сообщения за день
        today = timezone.now().replace(hour=0, minute=0, second=0)
        settings.daily_messages = Message.objects.filter(
            chat=chat,
            created_at__gte=today
        ).count()
        
        settings.save()
        updated_count += 1
    
    logger.info(f"Updated statistics for {updated_count} chats")
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def detect_suspicious_activity():
    """
    Обнаружение подозрительной активности.
    """
    from .models_chat import SecurityLog
    
    # Проверяем неудачные входы за последний час
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Группируем по IP
    suspicious_ips = SecurityLog.objects.filter(
        action='login',
        created_at__gte=one_hour_ago
    ).values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gte=5)
    
    marked_count = 0
    for entry in suspicious_ips:
        # Помечаем как подозрительные
        SecurityLog.objects.filter(
            ip_address=entry['ip_address'],
            created_at__gte=one_hour_ago
        ).update(is_suspicious=True)
        marked_count += 1
    
    logger.info(f"Marked {marked_count} IPs as suspicious")
    return {'status': 'completed', 'marked_count': marked_count}


@shared_task
def send_daily_digest():
    """
    Отправка ежедневного дайджеста пользователям.
    """
    # Получаем пользователей с включённым дайджестом
    from .models import UserNotificationSettings
    
    users_with_digest = UserNotificationSettings.objects.filter(
        email_digest='daily'
    ).select_related('user')
    
    sent_count = 0
    for settings in users_with_digest:
        try:
            send_email_digest.delay(settings.user.id, 'daily')
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending digest to user {settings.user.id}: {e}")
    
    return {'status': 'completed', 'sent_count': sent_count}


@shared_task
def send_weekly_digest():
    """
    Отправка еженедельного дайджеста.
    """
    from .models import UserNotificationSettings
    
    users_with_digest = UserNotificationSettings.objects.filter(
        email_digest='weekly'
    ).select_related('user')
    
    sent_count = 0
    for settings in users_with_digest:
        try:
            send_email_digest.delay(settings.user.id, 'weekly')
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending digest to user {settings.user.id}: {e}")
    
    return {'status': 'completed', 'sent_count': sent_count}


@shared_task
def invalidate_settings_cache():
    """
    Периодическая инвалидация кэша настроек.
    """
    from .services.chat_services import settings_cache
    
    # Инвалидируем кэш для чатов с недавней активностью
    recent_chats = GroupChat.objects.filter(
        last_message_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    count = 0
    for chat in recent_chats:
        settings_cache.invalidate_all_for_chat('group', chat.id)
        count += 1
    
    return {'status': 'completed', 'invalidated_count': count}


@shared_task
def backup_chat_task(backup_id: int):
    """
    Асинхронное создание бэкапа чата.
    """
    from .models_chat import ChatBackup
    from .services.chat_services import ChatBackupService
    
    try:
        backup = ChatBackup.objects.get(id=backup_id)
        service = ChatBackupService()
        
        result = service.create_backup(backup.chat, backup.created_by)
        
        if result['success']:
            backup.status = 'completed'
            backup.messages_count = result['messages_count']
            backup.members_count = result['members_count']
            backup.file_size = result['file_size']
        else:
            backup.status = 'failed'
        
        backup.save()
        return result
        
    except ChatBackup.DoesNotExist:
        return {'success': False, 'error': 'Backup not found'}


# ==================== ИСХОДНЫЕ ЗАДАЧИ ====================

@shared_task
def send_push_notification(user_id, notification_data):
    """
    Отправить push-уведомление пользователю
    """
    from notifications.services import notification_service

    try:
        user = User.objects.get(id=user_id)
        # Интеграция с существующей системой уведомлений
        notification_service.send_push(user, notification_data)
        return {'status': 'sent', 'user_id': user_id}
    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_email_digest(user_id, digest_type='daily'):
    """
    Отправить email-дайджест пользователю
    """
    try:
        user = User.objects.get(id=user_id)

        # Получаем данные для дайджеста
        if digest_type == 'daily':
            since = timezone.now() - timedelta(days=1)
        else:
            since = timezone.now() - timedelta(weeks=1)

        # Получаем непрочитанные сообщения
        unread_messages = []

        # Групповые чаты
        group_chats = GroupChat.objects.filter(members__user=user)
        for chat in group_chats:
            messages = Message.objects.filter(
                chat=chat,
                created_at__gte=since,
                is_deleted=False
            ).exclude(sender=user).count()

            if messages > 0:
                unread_messages.append({
                    'type': 'group',
                    'chat_id': chat.id,
                    'chat_name': chat.name,
                    'count': messages
                })

        # Личные чаты
        private_chats = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)  # Используем Q вместо models.Q
        )

        for chat in private_chats:
            messages = Message.objects.filter(
                private_chat=chat,
                created_at__gte=since,
                is_deleted=False
            ).exclude(sender=user).count()

            if messages > 0:
                other_user = chat.user1 if chat.user2 == user else chat.user2
                unread_messages.append({
                    'type': 'private',
                    'chat_id': chat.id,
                    'chat_name': other_user.username,
                    'count': messages
                })

        if not unread_messages:
            return {'status': 'skipped', 'message': 'No unread messages'}

        # Формируем email
        subject = f'Ваш {digest_type} дайджест на AniStream'
        message = render_to_string('emails/digest.html', {
            'user': user,
            'digest_type': digest_type,
            'messages': unread_messages,
            'site_url': settings.SITE_URL
        })

        # Отправляем
        send_mail(
            subject,
            '',  # plain text version
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False
        )

        # Логируем
        EmailLog.objects.create(
            user=user,
            email_type=f'{digest_type}_digest',
            subject=subject,
            to_email=user.email,
            content=message,
            status='sent',
            sent_at=timezone.now()
        )

        return {'status': 'sent', 'user_id': user_id, 'messages_count': len(unread_messages)}

    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}
    except Exception as e:
        # Логируем ошибку
        try:
            EmailLog.objects.create(
                user_id=user_id,
                email_type=f'{digest_type}_digest',
                subject='Ошибка дайджеста',
                to_email='',
                content='',
                status='failed',
                error_message=str(e)
            )
        except:
            pass

        return {'status': 'error', 'message': str(e)}


@shared_task
def send_mention_notification(message_id, mentioned_user_id):
    """
    Отправить уведомление об упоминании пользователя
    """
    try:
        message = Message.objects.get(id=message_id)
        mentioned_user = User.objects.get(id=mentioned_user_id)

        notification_data = {
            'type': 'mention',
            'title': f'Вас упомянул {message.sender.username}',
            'body': message.text[:100] if message.text else 'Медиа-сообщение',
            'data': {
                'message_id': message.id,
                'chat_id': message.chat_id or message.private_chat_id,
                'sender_id': message.sender_id
            }
        }

        # Отправляем push-уведомление
        send_push_notification.delay(mentioned_user_id, notification_data)

        # Отправляем email если пользователь офлайн
        from core.online_status import online_status
        if not online_status.is_online(mentioned_user_id):
            subject = f'Вас упомянули в чате'
            message_text = render_to_string('emails/mention.html', {
                'user': mentioned_user,
                'sender': message.sender,
                'message': message,
                'site_url': settings.SITE_URL
            })

            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [mentioned_user.email],
                html_message=message_text,
                fail_silently=True
            )

            EmailLog.objects.create(
                user=mentioned_user,
                email_type='mention',
                subject=subject,
                to_email=mentioned_user.email,
                content=message_text,
                status='sent',
                message_id=message_id
            )

        return {'status': 'sent', 'user_id': mentioned_user_id}

    except (Message.DoesNotExist, User.DoesNotExist):
        return {'status': 'error', 'message': 'Message or user not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_messages():
    """
    Очистка старых сообщений (ежедневно)
    """
    cutoff_date = timezone.now() - timedelta(days=30)

    # Получаем старые сообщения, которые не закреплены
    old_messages = Message.objects.filter(
        created_at__lt=cutoff_date,
        is_pinned=False,
        is_deleted=False
    )

    count = old_messages.count()

    # Помечаем как удалённые (soft delete)
    old_messages.update(
        is_deleted=True,
        deleted_at=timezone.now()
    )

    return {'status': 'completed', 'deleted_count': count}


@shared_task
def cleanup_unused_attachments():
    """
    Очистка неиспользуемых вложений
    """
    # Получаем вложения, сообщения которых удалены
    unused_attachments = Attachment.objects.filter(
        Q(message__is_deleted=True) | Q(message__isnull=True)  # Уже используем Q, импорт есть в начале
    )

    count = unused_attachments.count()

    # Удаляем файлы
    for attachment in unused_attachments:
        if attachment.file:
            attachment.file.delete(save=False)
        if attachment.thumbnail:
            attachment.thumbnail.delete(save=False)

    # Удаляем записи
    unused_attachments.delete()

    return {'status': 'completed', 'deleted_count': count}


@shared_task
def cleanup_expired_invites():
    """
    Очистка просроченных приглашений
    """
    now = timezone.now()

    expired_invites = ChatInvite.objects.filter(
        is_active=True,
        expires_at__lt=now
    )

    count = expired_invites.count()

    # Деактивируем приглашения
    expired_invites.update(is_active=False)

    return {'status': 'completed', 'deactivated_count': count}


@shared_task
def generate_thumbnail_for_attachment(attachment_id):
    """
    Генерация миниатюры для вложения (асинхронно)
    """
    try:
        attachment = Attachment.objects.get(id=attachment_id)

        if attachment.type != 'image':
            return {'status': 'skipped', 'message': 'Not an image'}

        from PIL import Image
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile

        img = Image.open(attachment.file)

        # Сохраняем размеры
        attachment.width = img.width
        attachment.height = img.height
        attachment.save(update_fields=['width', 'height'])

        # Создаём миниатюру
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        thumbnail_file = InMemoryUploadedFile(
            buffer,
            None,
            f'{attachment.id}_thumb.jpg',
            'image/jpeg',
            buffer.getbuffer().nbytes,
            None
        )
        attachment.thumbnail.save(f'{attachment.id}_thumb.jpg', thumbnail_file)
        attachment.save(update_fields=['thumbnail'])

        return {'status': 'completed', 'attachment_id': attachment_id}

    except Attachment.DoesNotExist:
        return {'status': 'error', 'message': 'Attachment not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_chat_invite_notification(chat_id, user_id, inviter_id):
    """
    Отправить уведомление о приглашении в чат
    """
    try:
        chat = GroupChat.objects.get(id=chat_id)
        user = User.objects.get(id=user_id)
        inviter = User.objects.get(id=inviter_id)

        notification_data = {
            'type': 'chat_invite',
            'title': f'Приглашение в чат {chat.name}',
            'body': f'{inviter.username} приглашает вас в чат',
            'data': {
                'chat_id': chat.id,
                'chat_name': chat.name,
                'inviter_id': inviter.id
            }
        }

        # Отправляем push-уведомление
        send_push_notification.delay(user_id, notification_data)

        return {'status': 'sent', 'user_id': user_id}

    except (GroupChat.DoesNotExist, User.DoesNotExist):
        return {'status': 'error', 'message': 'Chat or user not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def index_message_for_search(message_id):
    """
    Индексация сообщения для поиска (Elasticsearch)
    """
    try:
        message = Message.objects.get(id=message_id)

        # Интеграция с Elasticsearch
        # TODO: Реализовать интеграцию с Elasticsearch
        # from .search import MessageDocument
        # doc = MessageDocument(
        #     meta={'id': message.id},
        #     text=message.text,
        #     sender_id=message.sender_id,
        #     sender_username=message.sender.username,
        #     chat_id=message.chat_id,
        #     private_chat_id=message.private_chat_id,
        #     created_at=message.created_at,
        #     media_type=message.media_type
        # )
        # doc.save()

        return {'status': 'indexed', 'message_id': message_id}

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def archive_old_chats():
    """
    Архивация неактивных чатов
    """
    from django.db.models import Count

    # Находим чаты без активности более 90 дней
    cutoff_date = timezone.now() - timedelta(days=90)

    # Групповые чаты
    inactive_group_chats = GroupChat.objects.annotate(
        message_count=Count('group_messages')
    ).filter(
        created_at__lt=cutoff_date,
        message_count__gt=0
    )

    # Можно добавить логику архивации
    # Например, создать статус is_archived

    return {'status': 'completed', 'checked_count': inactive_group_chats.count()}


@shared_task
def process_new_message(message_id):
    """
    Обработка нового сообщения (отправка уведомлений, индексация и т.д.)
    """
    try:
        message = Message.objects.get(id=message_id)

        # Индексация для поиска
        index_message_for_search.delay(message_id)

        # Проверяем упоминания
        if message.text:
            import re
            # Находим упоминания вида @username
            mentions = re.findall(r'@(\w+)', message.text)
            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    send_mention_notification.delay(message_id, mentioned_user.id)
                except User.DoesNotExist:
                    continue

        # Генерация миниатюры если нужно
        if message.media and message.media_type in ['image', 'video']:
            # TODO: Создать вложение и сгенерировать миниатюру
            pass

        return {'status': 'completed', 'message_id': message_id}

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# ==================== FEED TASKS ====================

@shared_task
def update_followers_feeds(post_id: int, author_id: int):
    """Обновить ленты подписчиков после нового поста"""
    from .models import Follow
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Получаем всех подписчиков
        follower_ids = list(Follow.objects.filter(
            following_id=author_id
        ).values_list('follower_id', flat=True))

        timestamp = timezone.now().timestamp()

        for follower_id in follower_ids:
            feed_cache.add_post_to_feed(follower_id, post_id, timestamp)

        logger.info(f"Updated feeds for {len(follower_ids)} followers of user {author_id}")
        return {'success': True, 'followers_count': len(follower_ids)}

    except Exception as e:
        logger.error(f"Error updating followers feeds: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_feed_posts():
    """Очистка старых постов из Redis-лент"""
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Удаляем посты старше 7 дней из всех лент
        feed_cache.invalidate_all_feeds()

        logger.info("Old feed posts cleaned up")
        return {'success': True}

    except Exception as e:
        logger.error(f"Error cleaning up feed: {e}")
        return {'error': str(e)}


@shared_task
def send_post_like_notification(post_id: int, user_id: int):
    """Отправить уведомление о лайке поста"""
    from .models import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.select_related('author').get(id=post_id)
        user = post.author

        # Не отправляем уведомление о своём лайке
        if user.id == user_id:
            return {'success': True, 'message': 'Self-like notification skipped'}

        # Проверяем, не первый ли это лайк
        if post.likes_count > 1:
            return {'success': True, 'message': 'Not first like'}

        # Проверяем наличие модели уведомлений
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                type='like',
                title='Новый лайк',
                content=f'Ваш пост получил лайк',
                link=f'/post/{post_id}'
            )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error sending like notification: {e}")
        return {'error': str(e)}


@shared_task
def send_post_comment_notification(post_id: int, comment_id: int, author_id: int):
    """Отправить уведомление о комментарии к посту"""
    from .models import Post, PostComment
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        comment = PostComment.objects.get(id=comment_id)

        try:
            from notifications.models import Notification

            # Уведомление автору поста
            if post.author.id != author_id:
                Notification.objects.create(
                    user=post.author,
                    type='comment',
                    title='Новый комментарий',
                    content=f'К вашему посту оставили комментарий',
                    link=f'/post/{post_id}#comment-{comment_id}'
                )

            # Уведомление автору родительского комментария (если это ответ)
            if comment.parent and comment.parent.author.id != author_id:
                Notification.objects.create(
                    user=comment.parent.author,
                    type='reply',
                    title='Новый ответ',
                    content=f'Вам ответили на комментарий',
                    link=f'/post/{post_id}#comment-{comment_id}'
                )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except (Post.DoesNotExist, PostComment.DoesNotExist) as e:
        return {'error': str(e)}
    except Exception as e:
        logger.error(f"Error sending comment notification: {e}")
        return {'error': str(e)}


@shared_task
def send_post_repost_notification(post_id: int, user_id: int):
    """Отправить уведомление о репосте"""
    from .models import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        # TODO: Implement notification
        return {'success': True}
    except Post.DoesNotExist:
        return {'error': 'Post not found'}


@shared_task
def notify_moderators_new_report(report_id: int):
    """
    Уведомить модераторов о новой жалобе.
    Все жалобы отправляются на специальный аккаунт модератора.
    """
    from .models import Report, Post, PostComment
    from users.models import User
    from notifications.models import Notification
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    try:
        report = Report.objects.select_related('reporter').get(id=report_id)

        # Получаем специальный аккаунт для жалоб из настроек
        moderator_username = getattr(settings, 'REPORTS_MODERATOR_USERNAME', 'moderator')
        moderator_email = getattr(settings, 'REPORTS_MODERATOR_EMAIL', '')

        # Сначала ищем по username
        moderator = User.objects.filter(username=moderator_username).first()

        # Если не найден, ищем по email
        if not moderator and moderator_email:
            moderator = User.objects.filter(email=moderator_email).first()

        # Если всё ещё не найден, ищем любого staff/superuser
        if not moderator:
            moderator = User.objects.filter(is_staff=True, is_superuser=True).first()

        if not moderator:
            logger.warning(f"No moderator account found for report {report_id}")
            return {'error': 'No moderator account found'}

        # Формируем сообщение
        content_type_display = 'Пост' if report.content_type == 'post' else 'Комментарий' if report.content_type == 'comment' else 'Пользователь'
        reason_display = dict(Report.REASON_CHOICES).get(report.reason, report.reason)

        # Получаем превью контента
        content_preview = ''
        content_author = ''
        if report.content_type == 'post':
            try:
                post = Post.objects.get(id=report.content_id)
                content_preview = post.text[:100] if post.text else ''
                content_author = post.author.username
            except Post.DoesNotExist:
                pass
        elif report.content_type == 'comment':
            try:
                comment = PostComment.objects.get(id=report.content_id)
                content_preview = comment.content[:100] if comment.content else ''
                content_author = comment.author.username if comment.author else 'Удалён'
            except PostComment.DoesNotExist:
                pass
        elif report.content_type == 'user':
            try:
                target_user = User.objects.get(id=report.content_id)
                content_author = target_user.username
            except User.DoesNotExist:
                pass

        # Создаём уведомление (используем поле user вместо recipient)
        Notification.objects.create(
            user=moderator,
            type='system',
            title=f'🚨 Новая жалоба: {content_type_display}',
            content=f'Причина: {reason_display}\nАвтор: @{content_author}\nЖалоба от: @{report.reporter.username}',
            link=f'/moderation/reports/{report_id}'
        )

        logger.info(f"Moderator {moderator.username} notified about report {report_id}")
        return {'success': True, 'moderator_id': moderator.id}

    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {'error': 'Report not found'}
    except Exception as e:
        logger.error(f"Error notifying moderators: {e}")
        return {'error': str(e)}


@shared_task
def send_mention_in_post_notification(post_id: int, user_id: int, mentioned_by_id: int):
    """Отправить уведомление об упоминании в посте"""
    from users.models import User
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = User.objects.get(id=user_id)
        mentioned_by = User.objects.get(id=mentioned_by_id)

        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                type='mention',
                title='Упоминание',
                content=f'{mentioned_by.username} упомянул вас в посте',
                link=f'/post/{post_id}'
            )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending mention notification: {e}")
        return {'error': str(e)}


@shared_task
def update_post_popularity():
    """Обновить популярность постов (запускается каждый час)"""
    from .models import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Получаем посты за последние 24 часа
        yesterday = timezone.now() - timedelta(days=1)

        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=yesterday
        )

        # Здесь можно добавить логику пересчёта популярности
        logger.info(f"Updated popularity for {posts.count()} posts")
        return {'success': True, 'posts_count': posts.count()}

    except Exception as e:
        logger.error(f"Error updating popularity: {e}")
        return {'error': str(e)}


@shared_task
def reindex_post_for_search(post_id: int):
    """Переиндексировать пост для поиска"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Здесь будет интеграция с Elasticsearch
        logger.info(f"Reindexing post {post_id} for search")
        return {'success': True}

    except Exception as e:
        logger.error(f"Error reindexing post: {e}")
        return {'error': str(e)}


@shared_task
def process_post_hashtags(post_id: int):
    """Обработать хэштеги поста"""
    from django.db import models
    from .models import Post, PostHashtag, Hashtag
    import re
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        # Извлекаем хэштеги
        hashtags = re.findall(r'#(\w+)', post.text)

        for tag_name in hashtags:
            tag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            PostHashtag.objects.get_or_create(post=post, hashtag=tag)

            # Увеличиваем счётчик
            Hashtag.objects.filter(id=tag.id).update(
                posts_count=models.F('posts_count') + 1
            )

        return {'success': True, 'hashtags_count': len(hashtags)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error processing hashtags: {e}")
        return {'error': str(e)}


@shared_task
def process_post_mentions(post_id: int):
    """Обработать упоминания в посте"""
    from .models import Post, UserMention
    from users.models import User
    import re
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        # Извлекаем упоминания
        mentions = re.findall(r'@(\w+)', post.text)

        for username in mentions:
            try:
                user = User.objects.get(username=username)
                if user != post.author:
                    UserMention.objects.get_or_create(post=post, user=user)
            except User.DoesNotExist:
                pass

        return {'success': True, 'mentions_count': len(mentions)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error processing mentions: {e}")
        return {'error': str(e)}


@shared_task
def calculate_post_popularity(post_id: int):
    """Рассчитать популярность поста для рекомендаций"""
    from .models import Post
    import math
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        # Формула: (лайки + комментарии * 2 + репосты * 3) / (возраст в часах + 2) ^ 1.5
        age_hours = (timezone.now() - post.created_at).total_seconds() / 3600
        if age_hours < 0.1:
            age_hours = 0.1

        score = (
            post.likes_count * 1 +
            post.comments_count * 2 +
            post.reposts_count * 3
        ) / math.pow(age_hours + 2, 1.5)

        # Сохраняем в кэш
        from .feed_cache import feed_cache
        feed_cache.add_to_popular(post_id, score)

        return {'success': True, 'score': score}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error calculating popularity: {e}")
        return {'error': str(e)}


@shared_task
def sync_feed_views_to_db(post_id: int):
    """Синхронизировать количество просмотров из Redis в БД"""
    from .models import Post
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        cached_views = feed_cache.get_views_count(post_id)

        if cached_views > 0:
            post.views_count = cached_views
            post.save(update_fields=['views_count'])

        return {'success': True, 'views_synced': cached_views}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error syncing views: {e}")
        return {'error': str(e)}


@shared_task
def send_like_notification(post_id: int, user_id: int):
    """Отправить уведомление о лайке поста"""
    from .models import Post
    from users.models import User
    from notifications.models import Notification

    try:
        post = Post.objects.get(id=post_id)
        user = User.objects.get(id=user_id)

        # Не отправляем уведомление себе
        if post.author == user:
            return {'skipped': 'Cannot notify yourself'}

        # Проверяем настройки уведомлений
        profile = getattr(post.author, 'profile', None)
        if profile and not getattr(profile, 'notify_likes', True):
            return {'skipped': 'User disabled like notifications'}

        # Проверяем, что это первый лайк (с 0 на 1)
        if post.likes_count > 1:
            return {'skipped': 'Not the first like'}

        # Создаём уведомление (используем поле user)
        Notification.objects.create(
            user=post.author,
            type='like',
            title='Новый лайк',
            content=f'{user.username} лайкнул ваш пост',
            link=f'/post/{post.id}'
        )

        return {'success': True, 'notification_id': post.id}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending like notification: {e}")
        return {'error': str(e)}


@shared_task
def send_comment_notification(post_id: int, comment_id: int, parent_comment_id: int = None):
    """Отправить уведомление о новом комментарии"""
    from .models import Post, PostComment
    from users.models import User
    from notifications.models import Notification

    try:
        post = Post.objects.get(id=post_id)
        comment = PostComment.objects.get(id=comment_id)

        # Определяем получателей уведомлений
        recipients = set()

        # Автор поста
        if post.author != comment.author:
            recipients.add(post.author)

        # Автор родительского комментария (если это ответ)
        if parent_comment_id:
            try:
                parent_comment = PostComment.objects.get(id=parent_comment_id)
                if parent_comment.author != comment.author:
                    recipients.add(parent_comment.author)
            except PostComment.DoesNotExist:
                pass

        # Участники ветки комментариев
        if comment.parent:
            ancestors = comment.parent.get_ancestors()
            for ancestor in ancestors:
                if ancestor.author != comment.author:
                    recipients.add(ancestor.author)

        # Проверяем настройки и отправляем уведомления
        for recipient in recipients:
            profile = getattr(recipient, 'profile', None)
            if profile and not getattr(profile, 'notify_comments', True):
                continue

            Notification.objects.create(
                user=recipient,
                type='comment',
                title='Новый комментарий',
                content=f'{comment.author.username} прокомментировал ваш пост',
                link=f'/post/{post.id}?comment={comment.id}'
            )

        return {'success': True, 'notifications_sent': len(recipients)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except PostComment.DoesNotExist:
        return {'error': 'Comment not found'}
    except Exception as e:
        logger.error(f"Error sending comment notification: {e}")
        return {'error': str(e)}


@shared_task
def send_mention_notification(post_id: int, mentioned_user_id: int):
    """Отправить уведомление об упоминании (@username)"""
    from .models import Post
    from users.models import User
    from notifications.models import Notification

    try:
        post = Post.objects.get(id=post_id)
        mentioned_user = User.objects.get(id=mentioned_user_id)

        # Не отправляем уведомление себе
        if post.author == mentioned_user:
            return {'skipped': 'Cannot notify yourself'}

        Notification.objects.create(
            user=mentioned_user,
            type='mention',
            title='Упоминание',
            content=f'{post.author.username} упомянул вас в посте',
            link=f'/post/{post.id}'
        )

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending mention notification: {e}")
        return {'error': str(e)}


@shared_task
def send_repost_notification(original_post_id: int, user_id: int):
    """Отправить уведомление о репосте"""
    from .models import Post
    from users.models import User
    from notifications.models import Notification

    try:
        original_post = Post.objects.get(id=original_post_id)
        user = User.objects.get(id=user_id)

        # Не отправляем уведомление себе
        if original_post.author == user:
            return {'skipped': 'Cannot notify yourself'}

        Notification.objects.create(
            user=original_post.author,
            type='repost',
            title='Новый репост',
            content=f'{user.username} сделал репост вашего поста',
            link=f'/post/{original_post.id}'
        )

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending repost notification: {e}")
        return {'error': str(e)}


@shared_task
def update_post_popularity_scores():
    """Обновить популярность постов (вызывается каждый час)"""
    from .models import Post
    from django.utils import timezone
    import math

    try:
        # Получаем посты за последние 7 дней
        since = timezone.now() - timedelta(days=7)
        posts = Post.objects.filter(
            status='published',
            created_at__gte=since
        )

        updated_count = 0
        for post in posts:
            # Формула: (лайки + комментарии + репосты) / (возраст в часах ^ 0.5)
            age_hours = max(1, (timezone.now() - post.created_at).total_seconds() / 3600)
            score = (post.likes_count + post.comments_count + post.reposts_count) / math.sqrt(age_hours)

            # Здесь можно сохранить score в отдельное поле или использовать для сортировки
            # Пока просто обновляем кэш
            from .feed_cache import feed_cache
            feed_cache.set_post_popularity(post.id, score)
            updated_count += 1

        return {'success': True, 'posts_updated': updated_count}

    except Exception as e:
        logger.error(f"Error updating popularity: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_feed_cache():
    """Очистка старых постов из кэша ленты"""
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Удаляем посты старше 7 дней из всех лент
        from social.models import Post
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=7)
        old_posts = Post.objects.filter(
            status='published',
            created_at__lt=cutoff_date
        ).values_list('id', flat=True)[:1000]

        cleaned = 0
        for post_id in old_posts:
            feed_cache.invalidate_post(post_id)
            cleaned += 1

        logger.info(f"Cleaned {cleaned} old posts from feed cache")
        return {'success': True, 'posts_cleaned': cleaned}

    except Exception as e:
        logger.error(f"Error cleaning feed cache: {e}")
        return {'error': str(e)}


@shared_task
def index_post_for_search(post_id: int):
    """Индексировать пост для поиска (Elasticsearch)"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        from .models import Post
        from .serializers import PostSerializer

        post = Post.objects.get(id=post_id)

        # Формируем данные для индексации
        data = {
            'id': post.id,
            'title': post.title or '',
            'content': post.text or '',
            'author_id': post.author_id,
            'author_username': post.author.username,
            'type': post.post_type,
            'created_at': post.created_at.isoformat(),
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
        }

        # Добавляем хэштеги
        hashtags = post.hashtags.values_list('name', flat=True)
        data['hashtags'] = list(hashtags)

        # Индексируем в Elasticsearch (если настроен)
        # elasticsearch_client.index(index='posts', id=post.id, body=data)

        logger.info(f"Indexed post {post_id} for search")
        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error indexing post: {e}")
        return {'error': str(e)}