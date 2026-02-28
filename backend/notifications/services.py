from .models import Notification
from users.models import User


class NotificationService:
    """Сервис для управления уведомлениями с учетом настроек пользователя"""

    @staticmethod
    def should_send_notification(user: User, notification_type: str) -> bool:
        """Проверяет, нужно ли отправлять уведомление пользователю"""
        if not user.settings:
            return True  # Если настроек нет, отправляем по умолчанию

        settings = user.settings

        # Проверяем настройки уведомлений
        if notification_type == 'comment':
            return settings.message_notifications
        elif notification_type == 'like':
            return settings.message_notifications
        elif notification_type == 'follow':
            return settings.message_notifications
        elif notification_type == 'mention':
            return settings.message_notifications
        elif notification_type == 'message':
            return settings.message_notifications
        elif notification_type == 'contest':
            return settings.contest_notifications
        elif notification_type == 'group_invite':
            return settings.message_notifications
        elif notification_type == 'system':
            return settings.push_notifications

        return True

    @staticmethod
    def create_notification(user: User, notification_type: str, title: str, content: str,
                          content_object=None, send_push=True):
        """Создает уведомление с учетом настроек пользователя"""

        # Проверяем, нужно ли отправлять уведомление
        if not NotificationService.should_send_notification(user, notification_type):
            return None

        # Создаем уведомление
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            content=content,
            content_object=content_object
        )

        # Отправляем push-уведомление, если включено
        if send_push and user.settings and user.settings.push_notifications:
            NotificationService.send_push_notification(user, title, content)

        return notification

    @staticmethod
    def send_push_notification(user: User, title: str, content: str):
        """Отправляет push-уведомление пользователю"""
        # Здесь должна быть реализация отправки push-уведомлений
        # Например, через Firebase Cloud Messaging или аналогичный сервис
        # Пока просто заглушка
        print(f"Push notification to {user.username}: {title} - {content}")

    @staticmethod
    def send_email_notification(user: User, title: str, content: str):
        """Отправляет email-уведомление"""
        if user.settings and user.settings.email_notifications:
            # Здесь должна быть реализация отправки email
            print(f"Email notification to {user.email}: {title} - {content}")

    @staticmethod
    def get_unread_count(user: User) -> int:
        """Возвращает количество непрочитанных уведомлений"""
        return Notification.objects.filter(
            user=user,
            is_read=False,
            is_deleted=False
        ).count()

    @staticmethod
    def mark_as_read(user: User, notification_ids: list):
        """Отмечает уведомления как прочитанные"""
        Notification.objects.filter(
            user=user,
            id__in=notification_ids
        ).update(is_read=True)

    @staticmethod
    def mark_all_as_read(user: User):
        """Отмечает все уведомления пользователя как прочитанные"""
        Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True)

    @staticmethod
    def send_like_notification(post, liker):
        """Отправляет уведомление о лайке поста"""
        if post.author == liker:
            return

        notification_service.create_notification(
            user=post.author,
            notification_type='like',
            title=f'{liker.username} лайкнул(а) ваш пост',
            content=f'Пользователь @{liker.username} поставил лайк на ваш пост: "{post.text[:50]}..."',
            content_object=post
        )

    @staticmethod
    def send_repost_notification(post, reposter, comment=''):
        """Отправляет уведомление о репосте"""
        if post.author == reposter:
            return

        content = f'Пользователь @{reposter.username} сделал репост вашего поста'
        if comment:
            content += f' с комментарием: "{comment}"'

        notification_service.create_notification(
            user=post.author,
            notification_type='repost',
            title=f'{reposter.username} репостнул(а) ваш пост',
            content=content,
            content_object=post
        )

    @staticmethod
    def send_follow_notification(follower, following):
        """Отправляет уведомление о новой подписке"""
        notification_service.create_notification(
            user=following,
            notification_type='follow',
            title=f'{follower.username} подписался на вас',
            content=f'Теперь @{follower.username} видит ваши посты в ленте'
        )

    @staticmethod
    def send_comment_notification(comment):
        """Отправляет уведомление о новом комментарии"""
        post = comment.post
        author = comment.author

        # Не отправляем, если автор комментария - автор поста
        if post.author == author:
            return

        notification_service.create_notification(
            user=post.author,
            notification_type='comment',
            title=f'{author.username} прокомментировал(а) ваш пост',
            content=f'"{comment.text[:50]}..."',
            content_object=comment
        )


# Глобальный экземпляр сервиса
notification_service = NotificationService()