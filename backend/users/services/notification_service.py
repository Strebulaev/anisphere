from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, time, timedelta
from ..models import NotificationSettings, MessageNotification, EmailLog
import json
from typing import Optional


class NotificationService:
    """Сервис для управления уведомлениями с учетом настроек пользователя"""

    def __init__(self, user):
        self.user = user
        self.settings = self._get_notification_settings()

    def _get_notification_settings(self):
        """Получить настройки уведомлений пользователя"""
        return NotificationSettings.objects.get_or_create(user=self.user)[0]

    def should_send_push(self, notification_type: str, chat=None) -> bool:
        """Проверяет, нужно ли отправлять push-уведомление"""

        # Проверка глобальных настроек
        if not self.settings.push_enabled:
            return False

        # Проверка режима "Не беспокоить"
        if self._is_do_not_disturb():
            return False

        # Проверка типа уведомления
        type_mapping = {
            'message': self.settings.message_notifications,
            'group': self.settings.group_notifications,
            'call': self.settings.call_notifications,
            'mention': self.settings.mention_notifications,
            'reaction': self.settings.reaction_notifications,
        }

        if notification_type in type_mapping and not type_mapping[notification_type]:
            return False

        # Проверка настроек конкретного чата
        if chat and self.settings.override_chat_settings:
            # Здесь можно добавить логику для индивидуальных настроек чата
            pass

        return True

    def should_send_email(self, notification_type: str) -> bool:
        """Проверяет, нужно ли отправлять email"""
        if not self.settings.email_enabled:
            return False

        # Проверка частоты
        if self.settings.email_frequency != 'immediately':
            last_email = EmailLog.objects.filter(
                user=self.user,
                sent_at__gte=timezone.now() - self._get_frequency_interval()
            ).exists()
            if last_email:
                return False

        # Проверка типа уведомления
        type_mapping = {
            'message': self.settings.message_notifications,
            'group': self.settings.group_notifications,
            'mention': self.settings.mention_notifications,
        }

        if notification_type in type_mapping and not type_mapping[notification_type]:
            return False

        return True

    def _is_do_not_disturb(self) -> bool:
        """Проверяет, активен ли режим 'Не беспокоить'"""
        if not self.settings.do_not_disturb_start or not self.settings.do_not_disturb_end:
            return False

        now = timezone.now().time()
        start = self.settings.do_not_disturb_start
        end = self.settings.do_not_disturb_end

        if start < end:
            return start <= now <= end
        else:  # Пересекает полночь
            return now >= start or now <= end

    def _get_frequency_interval(self) -> timedelta:
        """Получить интервал для проверки частоты"""
        intervals = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
        }
        return intervals.get(self.settings.email_frequency, timedelta(0))

    def send_push_notification(self, title: str, body: str, data: dict = None) -> bool:
        """Отправка push-уведомления"""
        payload = {
            'head': title,
            'body': body,
            'icon': '/static/icons/icon-192x192.png',
            'badge': '/static/icons/badge-96x96.png',
        }

        if data:
            payload.update(data)

        if self.settings.push_sound:
            payload['sound'] = '/static/sounds/notification.mp3'

        # Здесь должна быть реализация отправки push-уведомлений
        # Например, через Firebase Cloud Messaging или аналогичный сервис
        print(f"Push notification to {self.user.username}: {title} - {body}")
        return True  # Заглушка

    def send_email_notification(self, subject: str, message: str, html_message: str = None) -> bool:
        """Отправка email уведомления"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )

            # Логируем отправку
            EmailLog.objects.create(
                user=self.user,
                subject=subject,
                sent_at=timezone.now()
            )

            return True
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False

    def send_message_notification(self, message, chat) -> bool:
        """Отправка уведомления о новом сообщении"""
        sender_name = message.sender.get_full_name() or message.sender.username

        # Push уведомление
        push_sent = False
        if self.should_send_push('message', chat):
            title = f"{sender_name}"
            body = message.text[:100] if self.settings.push_preview else "Новое сообщение"

            push_sent = self.send_push_notification(title, body, {
                'chat_id': chat.id,
                'message_id': message.id,
                'type': 'new_message'
            })

        # Email уведомление
        email_sent = False
        if self.should_send_email('message'):
            subject = f"Новое сообщение от {sender_name}"
            html_message = f"""
            <h3>Новое сообщение в {chat.name}</h3>
            <p><strong>{sender_name}:</strong> {message.text}</p>
            <p><a href="{settings.SITE_URL}/chat/{chat.id}/">Открыть чат</a></p>
            """

            email_sent = self.send_email_notification(subject, f"У вас новое сообщение", html_message)

            # Помечаем сообщение как уведомленное
            if email_sent:
                MessageNotification.objects.create(
                    user=self.user,
                    message=message,
                    notified_via='email',
                    notified_at=timezone.now()
                )

        return push_sent or email_sent

    def send_mention_notification(self, message, chat, mentioned_users) -> bool:
        """Отправка уведомления об упоминании"""
        if self.user not in mentioned_users:
            return False

        sender_name = message.sender.get_full_name() or message.sender.username

        # Push уведомление
        push_sent = False
        if self.should_send_push('mention', chat):
            title = f"Вас упомянули"
            body = f"{sender_name}: {message.text[:100]}..."

            push_sent = self.send_push_notification(title, body, {
                'chat_id': chat.id,
                'message_id': message.id,
                'type': 'mention'
            })

        # Email уведомление
        email_sent = False
        if self.should_send_email('mention'):
            subject = f"Вас упомянули в {chat.name}"
            html_message = f"""
            <h3>Упоминание в {chat.name}</h3>
            <p><strong>{sender_name}:</strong> {message.text}</p>
            <p><a href="{settings.SITE_URL}/chat/{chat.id}/">Открыть чат</a></p>
            """

            email_sent = self.send_email_notification(subject, f"Вас упомянули", html_message)

        return push_sent or email_sent

    def send_call_notification(self, caller, call_type='audio') -> bool:
        """Отправка уведомления о звонке"""
        caller_name = caller.get_full_name() or caller.username

        push_sent = False
        if self.should_send_push('call'):
            title = f"Входящий {call_type} звонок"
            body = f"Звонок от {caller_name}"

            push_sent = self.send_push_notification(title, body, {
                'caller_id': caller.id,
                'call_type': call_type,
                'type': 'incoming_call'
            })

        return push_sent