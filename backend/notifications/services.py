"""
NotificationService - централизованный сервис создания уведомлений
с отправкой через Django Channels (channel_layer → group user_{id}).
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Notification
from users.models import User

logger = logging.getLogger(__name__)


# ── Иконки по типу ───────────────────────────────────────────────────────────

TYPE_ICONS = {
    'like':             '❤️',
    'dislike':          '👎',
    'heart':            '💖',
    'comment':          '💬',
    'reply':            '↩️',
    'mention':          '@',
    'follow':           '👥',
    'repost':           '🔁',
    'message':          '✉️',
    'group_message':    '👥',
    'group_invite':     '📨',
    'achievement':      '🏆',
    'contest':          '🏅',
    'contest_vote':     '🗳️',
    'contest_results':  '📊',
    'contest_win':      '👑',
    'reminder_episode': '⏰',
    'reminder_event':   '📅',
    'reminder_contest': '⏳',
    'system':           '⚙️',
    'warning':          '⚠️',
    'security':         '🔒',
}


class NotificationService:
    """Сервис для управления уведомлениями."""

    # ── Проверка настроек ─────────────────────────────────────────────────────

    @staticmethod
    def should_send_notification(user: User, notification_type: str) -> bool:
        """Возвращает True, если нужно отправить уведомление согласно настройкам."""
        try:
            settings = getattr(user, 'notif_settings', None)
            if not settings:
                return True
            type_cfg = settings.type_settings.get(notification_type, {})
            return type_cfg.get('enabled', True)
        except Exception:
            return True

    # ── Основной метод создания ───────────────────────────────────────────────

    @staticmethod
    def create_notification(
        user: User,
        notification_type: str,
        title: str,
        content: str,
        link: str = '',
        icon: str = '',
        content_object=None,
        send_ws: bool = True,
    ) -> 'Notification | None':
        """Создаёт уведомление и отправляет его через WebSocket."""

        if not NotificationService.should_send_notification(user, notification_type):
            return None

        icon = icon or TYPE_ICONS.get(notification_type, '🔔')

        kwargs = dict(
            user=user,
            type=notification_type,
            title=title,
            content=content,
            icon=icon,
            link=link,
        )
        if content_object is not None:
            from django.contrib.contenttypes.models import ContentType
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = content_object.pk

        notification = Notification.objects.create(**kwargs)

        if send_ws:
            NotificationService._send_ws(notification)

        return notification

    # ── WebSocket ─────────────────────────────────────────────────────────────

    @staticmethod
    def _send_ws(notification: 'Notification'):
        """Отправляет событие notification в channel group user_{id}."""
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            payload = {
                'type': 'notification_event',
                'action': 'notification',
                'notification': {
                    'id': notification.id,
                    'type': notification.type,
                    'title': notification.title,
                    'content': notification.content,
                    'icon': notification.icon,
                    'link': notification.link,
                    'is_read': notification.is_read,
                    'is_important': notification.is_important,
                    'created_at': notification.created_at.isoformat(),
                },
            }
            async_to_sync(channel_layer.group_send)(
                f'user_{notification.user_id}',
                payload,
            )
        except Exception as exc:
            logger.warning('WS notification send failed: %s', exc)

    # ── Счётчик ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_unread_count(user: User) -> int:
        return Notification.objects.filter(
            user=user, is_read=False, is_deleted=False
        ).count()

    # ── Утилиты ───────────────────────────────────────────────────────────────

    @staticmethod
    def mark_as_read(user: User, notification_ids: list):
        Notification.objects.filter(
            user=user, id__in=notification_ids
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def mark_all_as_read(user: User):
        Notification.objects.filter(
            user=user, is_read=False, is_deleted=False
        ).update(is_read=True, read_at=timezone.now())

    # ── Готовые хелперы ───────────────────────────────────────────────────────

    @staticmethod
    def send_like_notification(post, liker):
        if post.author_id == liker.id:
            return
        NotificationService.create_notification(
            user=post.author,
            notification_type='like',
            title=f'{liker.username} лайкнул ваш пост',
            content=f'@{liker.username} поставил лайк: «{(post.text or "")[:60]}»',
            link=f'/reactor',
            content_object=post,
        )

    @staticmethod
    def send_comment_notification(comment):
        post = comment.post
        author = comment.author
        if post.author_id == author.id:
            return
        NotificationService.create_notification(
            user=post.author,
            notification_type='comment',
            title=f'{author.username} прокомментировал ваш пост',
            content=f'«{(comment.text or "")[:80]}»',
            link=f'/reactor',
            content_object=comment,
        )

    @staticmethod
    def send_reply_notification(comment, parent_comment):
        author = comment.author
        if parent_comment.author_id == author.id:
            return
        NotificationService.create_notification(
            user=parent_comment.author,
            notification_type='reply',
            title=f'{author.username} ответил на ваш комментарий',
            content=f'«{(comment.text or "")[:80]}»',
            link=f'/reactor',
            content_object=comment,
        )

    @staticmethod
    def send_follow_notification(follower, following):
        NotificationService.create_notification(
            user=following,
            notification_type='follow',
            title=f'{follower.username} подписался на вас',
            content=f'Теперь @{follower.username} видит ваши посты в ленте',
            link=f'/profile/{follower.id}',
        )

    @staticmethod
    def send_repost_notification(post, reposter, comment=''):
        if post.author_id == reposter.id:
            return
        text = f'@{reposter.username} сделал репост вашего поста'
        if comment:
            text += f': «{comment[:60]}»'
        NotificationService.create_notification(
            user=post.author,
            notification_type='repost',
            title=f'{reposter.username} репостнул ваш пост',
            content=text,
            link=f'/reactor',
            content_object=post,
        )

    @staticmethod
    def send_mention_notification(mentioned_user, author, comment_text, link=''):
        NotificationService.create_notification(
            user=mentioned_user,
            notification_type='mention',
            title=f'{author.username} упомянул вас',
            content=f'«{comment_text[:80]}»',
            link=link,
        )

    @staticmethod
    def send_system_notification(user: User, title: str, content: str, link: str = ''):
        NotificationService.create_notification(
            user=user,
            notification_type='system',
            title=title,
            content=content,
            link=link,
        )

    @staticmethod
    def send_warning_notification(user: User, reason: str):
        NotificationService.create_notification(
            user=user,
            notification_type='warning',
            title='Предупреждение от модератора',
            content=reason,
            link='/settings',
        )

    @staticmethod
    def send_achievement_notification(user: User, achievement_name: str):
        NotificationService.create_notification(
            user=user,
            notification_type='achievement',
            title='Получено достижение!',
            content=achievement_name,
            link='/achievements',
        )

    @staticmethod
    def send_contest_win_notification(user: User, contest_title: str, place: int):
        NotificationService.create_notification(
            user=user,
            notification_type='contest_win',
            title=f'Вы заняли {place} место в конкурсе!',
            content=f'«{contest_title}» - поздравляем!',
            link='/reactor/competitions',
        )


# Глобальный экземпляр для удобного импорта
notification_service = NotificationService()
