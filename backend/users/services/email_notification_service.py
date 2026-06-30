from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from ..models import EmailLog, MessageNotification
from social.models import Message
import threading


class EmailNotificationService:
    """Сервис для отправки email уведомлений"""

    def __init__(self, user):
        self.user = user

    def can_send_email(self, notification_type: str) -> bool:
        """Проверяет, можно ли отправить email"""
        if not self.user.notification_settings.email_enabled:
            return False

        # Проверка частоты
        if self.user.notification_settings.email_frequency != 'immediately':
            last_email = EmailLog.objects.filter(
                user=self.user,
                sent_at__gte=timezone.now() - self._get_frequency_interval()
            ).exists()
            if last_email:
                return False

        # Проверка типа уведомления
        type_mapping = {
            'message': self.user.notification_settings.message_notifications,
            'group': self.user.notification_settings.group_notifications,
            'mention': self.user.notification_settings.mention_notifications,
        }

        if notification_type in type_mapping and not type_mapping[notification_type]:
            return False

        # Проверка времени (не отправлять ночью)
        now = timezone.now()
        if self.user.notification_settings.do_not_disturb_start and self.user.notification_settings.do_not_disturb_end:
            if self._is_time_between(now.time(),
                                   self.user.notification_settings.do_not_disturb_start,
                                   self.user.notification_settings.do_not_disturb_end):
                return False

        # Проверка лимитов
        today = now.date()
        emails_today = EmailLog.objects.filter(
            user=self.user,
            sent_at__date=today
        ).count()

        if emails_today >= 20:  # Максимум 20 писем в день
            return False

        # Проверка минимального интервала (15 минут)
        last_email_time = EmailLog.objects.filter(
            user=self.user
        ).order_by('-sent_at').first()

        if last_email_time:
            time_since_last = now - last_email_time.sent_at
            if time_since_last < timedelta(minutes=15):
                return False

        return True

    def _get_frequency_interval(self) -> timedelta:
        """Получить интервал для проверки частоты"""
        intervals = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
        }
        return intervals.get(self.user.notification_settings.email_frequency, timedelta(0))

    def _is_time_between(self, check_time, start_time, end_time) -> bool:
        """Проверка, находится ли время между start_time и end_time"""
        if start_time < end_time:
            return start_time <= check_time <= end_time
        else:  # Пересекает полночь
            return check_time >= start_time or check_time <= end_time

    def send_digest_email(self) -> bool:
        """Отправка сводного email"""
        # Получаем непрочитанные сообщения за период
        unread_messages = self._get_unread_messages_since_last_email()

        if not unread_messages:
            return False

        # Группируем по чатам
        chats_data = {}
        for message in unread_messages:
            chat_id = message.chat.id if hasattr(message, 'chat') else message.private_chat.id
            chat_name = message.chat.name if hasattr(message, 'chat') else "Личный чат"

            if chat_id not in chats_data:
                chats_data[chat_id] = {
                    'chat_name': chat_name,
                    'messages': [],
                    'unread_count': 0
                }
            chats_data[chat_id]['messages'].append(message)
            chats_data[chat_id]['unread_count'] += 1

        # Подготавливаем контекст для шаблона
        context = {
            'user': self.user,
            'chats': list(chats_data.values()),
            'total_unread': len(unread_messages),
            'date': timezone.now().strftime('%d.%m.%Y'),
        }

        # Рендерим HTML и текстовую версию
        html_content = render_to_string('emails/digest.html', context)
        text_content = render_to_string('emails/digest.txt', context)

        # Отправляем email
        subject = f"Сводка сообщений за {context['date']}"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.user.email],
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send(fail_silently=False)

            # Помечаем сообщения как "уведомленные"
            for message in unread_messages:
                MessageNotification.objects.create(
                    user=self.user,
                    message=message,
                    notified_via='email',
                    notified_at=timezone.now()
                )

            # Логируем отправку
            EmailLog.objects.create(
                user=self.user,
                subject=subject,
                sent_at=timezone.now()
            )

            return True
        except Exception as e:
            print(f"Ошибка отправки сводного email: {e}")
            return False

    def send_immediate_email(self, notification_type: str, data: dict) -> bool:
        """Немедленная отправка email уведомления"""
        templates = {
            'message': ('emails/new_message.html', 'emails/new_message.txt'),
            'mention': ('emails/mention.html', 'emails/mention.txt'),
            'group_invite': ('emails/group_invite.html', 'emails/group_invite.txt'),
            'call_missed': ('emails/call_missed.html', 'emails/call_missed.txt'),
        }

        if notification_type not in templates:
            return False

        html_template, text_template = templates[notification_type]

        context = {
            'user': self.user,
            **data
        }

        html_content = render_to_string(html_template, context)
        text_content = render_to_string(text_template, context)

        subject = self._get_subject_for_type(notification_type, data)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.user.email],
        )
        email.attach_alternative(html_content, "text/html")

        try:
            email.send(fail_silently=False)

            EmailLog.objects.create(
                user=self.user,
                subject=subject,
                sent_at=timezone.now()
            )

            return True
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False

    def _get_subject_for_type(self, notification_type: str, data: dict) -> str:
        """Получить заголовок письма в зависимости от типа"""
        subjects = {
            'message': f"Новое сообщение от {data.get('sender_name')}",
            'mention': f"Вас упомянули в {data.get('chat_name')}",
            'group_invite': f"Приглашение в группу {data.get('group_name')}",
            'call_missed': f"Пропущенный звонок от {data.get('caller_name')}",
        }
        return subjects.get(notification_type, "Уведомление")

    def _get_unread_messages_since_last_email(self):
        """Получить непрочитанные сообщения с момента последнего email"""
        last_email = EmailLog.objects.filter(
            user=self.user
        ).order_by('-sent_at').first()

        since_date = last_email.sent_at if last_email else timezone.now() - timedelta(days=1)

        # Получаем сообщения, которые пользователь не видел
        # Это упрощенная версия - в реальности нужна более сложная логика
        messages = Message.objects.filter(
            created_at__gte=since_date
        ).exclude(sender=self.user).select_related('sender', 'chat', 'private_chat')[:50]

        return messages

    def send_test_email(self) -> bool:
        """Отправка тестового email"""
        subject = "Тестовое уведомление - AniSphere"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Тестовое уведомление</h2>
            <p>Привет, {self.user.username}!</p>
            <p>Это тестовое email уведомление от AniSphere.</p>
            <p>Если вы получили это письмо, значит настройки email работают корректно.</p>
            <p>Время отправки: {timezone.now().strftime('%d.%m.%Y %H:%M')}</p>
        </body>
        </html>
        """

        return self.send_email_notification(subject, "Тестовое уведомление", html_content)


class EmailDigestScheduler:
    """Планировщик для отправки сводных email"""

    @staticmethod
    def schedule_digests():
        """Запланировать отправку сводок для всех пользователей"""
        from ..models import User

        users_with_digest = User.objects.filter(
            notification_settings__email_enabled=True,
            notification_settings__email_frequency__in=['daily', 'weekly']
        )

        for user in users_with_digest:
            EmailDigestScheduler.schedule_user_digest(user)

    @staticmethod
    def schedule_user_digest(user):
        """Запланировать сводку для конкретного пользователя"""
        from ..models import NotificationSettings

        settings = NotificationSettings.objects.get(user=user)

        if settings.email_frequency == 'daily':
            # Отправлять каждый день в указанное время
            # Здесь должна быть логика планировщика (Celery и т.д.)
            print(f"Scheduled daily digest for {user.username}")
        elif settings.email_frequency == 'weekly':
            # Отправлять раз в неделю в указанный день и время
            # Здесь должна быть логика планировщика
            print(f"Scheduled weekly digest for {user.username}")