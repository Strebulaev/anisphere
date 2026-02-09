from django.db.models import Sum, Q
import os
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from ..models import UploadedFile, CachedData
from social.models import Message, PrivateChat
import zipfile
from io import BytesIO
import json
import shutil


class StorageService:
    """Сервис для управления данными и хранилищем пользователя"""

    def __init__(self, user):
        self.user = user

    def get_storage_usage(self) -> dict:
        """Получить использование хранилища пользователем"""
        usage = {
            'messages': 0,
            'media': 0,
            'documents': 0,
            'audio': 0,
            'cache': 0,
            'total': 0
        }

        # Сообщения (текст + метаданные)
        message_count = Message.objects.filter(
            Q(sender=self.user) |
            Q(chat__members__user=self.user) |
            Q(private_chat__user1=self.user) |
            Q(private_chat__user2=self.user)
        ).count()
        usage['messages'] = message_count * 500  # ~500 байт на сообщение

        # Медиафайлы
        media_files = UploadedFile.objects.filter(
            user=self.user,
            file_type__in=['image', 'video']
        ).aggregate(total=Sum('file_size'))
        usage['media'] = media_files['total'] or 0

        # Документы
        documents = UploadedFile.objects.filter(
            user=self.user,
            file_type='document'
        ).aggregate(total=Sum('file_size'))
        usage['documents'] = documents['total'] or 0

        # Аудио
        audio = UploadedFile.objects.filter(
            user=self.user,
            file_type='audio'
        ).aggregate(total=Sum('file_size'))
        usage['audio'] = audio['total'] or 0

        # Кэш (оценочно)
        usage['cache'] = self._estimate_cache_size()

        # Итого
        usage['total'] = sum(usage.values())

        # В процентах от лимита (2GB)
        usage['percentage'] = min(100, (usage['total'] / (2 * 1024 * 1024 * 1024)) * 100)

        return usage

    def _estimate_cache_size(self) -> int:
        """Оценка размера кэша"""
        # Проверяем размер папки кэша пользователя
        cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', f'user_{self.user.id}')
        if os.path.exists(cache_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(cache_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass  # Игнорируем ошибки доступа к файлам
            return total_size
        return 0

    def clear_cache(self) -> bool:
        """Очистить кэш пользователя"""
        cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', f'user_{self.user.id}')
        if os.path.exists(cache_path):
            try:
                shutil.rmtree(cache_path)
                os.makedirs(cache_path)
            except OSError:
                return False

        # Очищаем кэш в БД
        CachedData.objects.filter(user=self.user).delete()

        return True

    def cleanup_old_media(self, days: int = 30) -> int:
        """Удалить старые просмотренные медиафайлы"""
        cutoff_date = timezone.now() - timedelta(days=days)

        # Находим медиафайлы из сообщений, которые были просмотрены
        old_media = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=cutoff_date,
            file_type__in=['image', 'video']
        )

        # Фильтруем только те, что были в прочитанных сообщениях
        # Это упрощенная версия - в реальности нужна более сложная логика
        deleted_count = old_media.count()

        # Удаляем файлы с диска
        for media in old_media:
            self._delete_file(media.file)
            if media.thumbnail:
                self._delete_file(media.thumbnail)

        # Удаляем записи из БД
        old_media.delete()

        return deleted_count

    def _delete_file(self, file_field):
        """Безопасное удаление файла"""
        if file_field and file_field.path and os.path.exists(file_field.path):
            try:
                os.remove(file_field.path)
            except OSError:
                pass  # Игнорируем ошибки удаления

    def export_data(self, data_types: list = None) -> BytesIO:
        """Экспорт данных пользователя"""
        if data_types is None:
            data_types = ['messages', 'contacts', 'media', 'settings']

        export_data = {}

        if 'messages' in data_types:
            export_data['messages'] = self._export_messages()

        if 'contacts' in data_types:
            export_data['contacts'] = self._export_contacts()

        if 'media' in data_types:
            export_data['media'] = self._export_media_info()

        if 'settings' in data_types:
            export_data['settings'] = self._export_settings()

        # Создаем архив
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for data_type, data in export_data.items():
                json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
                zip_file.writestr(f'{data_type}.json', json_data)

        buffer.seek(0)
        return buffer

    def _export_messages(self) -> list:
        """Экспорт истории сообщений"""
        messages = Message.objects.filter(
            Q(sender=self.user) |
            Q(chat__members__user=self.user) |
            Q(private_chat__user1=self.user) |
            Q(private_chat__user2=self.user)
        ).select_related('sender', 'chat', 'private_chat').order_by('created_at')

        export_messages = []
        for msg in messages:
            export_messages.append({
                'id': msg.id,
                'text': msg.text,
                'sender': msg.sender.username if msg.sender else None,
                'chat': msg.chat.name if msg.chat else None,
                'private_chat': True if msg.private_chat else False,
                'created_at': msg.created_at.isoformat(),
                'is_edited': msg.is_edited,
                'is_deleted': msg.is_deleted,
                'media_type': msg.media_type,
                'file_url': msg.file.url if msg.file else None,
            })

        return export_messages

    def _export_contacts(self) -> list:
        """Экспорт контактов"""
        # Получаем пользователей из приватных чатов
        contacts = set()
        private_chats = PrivateChat.objects.filter(
            Q(user1=self.user) | Q(user2=self.user)
        )

        for chat in private_chats:
            contact = chat.user2 if chat.user1 == self.user else chat.user1
            contacts.add(contact)

        export_contacts = []
        for contact in contacts:
            export_contacts.append({
                'id': contact.id,
                'username': contact.username,
                'display_name': contact.display_name,
                'email': contact.email,
                'phone': contact.phone_number,
                'added_at': chat.created_at.isoformat() if 'chat' in locals() else None,
            })

        return export_contacts

    def _export_media_info(self) -> list:
        """Экспорт информации о медиафайлах"""
        media_files = UploadedFile.objects.filter(user=self.user)

        export_media = []
        for media in media_files:
            export_media.append({
                'id': media.id,
                'filename': media.filename,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'uploaded_at': media.uploaded_at.isoformat(),
                'url': media.file.url if media.file else None,
                'thumbnail_url': media.thumbnail.url if media.thumbnail else None,
            })

        return export_media

    def _export_settings(self) -> dict:
        """Экспорт настроек пользователя"""
        settings_data = {}

        # Профиль
        settings_data['profile'] = {
            'username': self.user.username,
            'display_name': self.user.display_name,
            'bio': self.user.bio,
            'avatar': self.user.avatar.url if self.user.avatar else None,
            'favorite_genres': self.user.favorite_genres,
        }

        # Настройки профиля
        if hasattr(self.user, 'profile_settings'):
            settings_data['profile_settings'] = {
                'theme': self.user.profile_settings.theme,
                'accent_color': self.user.profile_settings.accent_color,
                'language': self.user.profile_settings.language,
                'timezone': self.user.profile_settings.timezone,
                'date_format': self.user.profile_settings.date_format,
                'time_format': self.user.profile_settings.time_format,
            }

        # Настройки уведомлений
        if hasattr(self.user, 'notification_settings'):
            settings_data['notification_settings'] = {
                'push_enabled': self.user.notification_settings.push_enabled,
                'email_enabled': self.user.notification_settings.email_enabled,
                'email_frequency': self.user.notification_settings.email_frequency,
            }

        # Настройки приватности
        if hasattr(self.user, 'privacy_settings'):
            settings_data['privacy_settings'] = {
                'who_can_see_phone': self.user.privacy_settings.who_can_see_phone,
                'who_can_see_email': self.user.privacy_settings.who_can_see_email,
                'who_can_see_last_seen': self.user.privacy_settings.who_can_see_last_seen,
            }

        return settings_data

    def delete_account_data(self) -> dict:
        """Полная очистка данных аккаунта (для удаления аккаунта)"""
        stats = {
            'messages_deleted': 0,
            'media_deleted': 0,
            'files_deleted': 0,
        }

        # Удаляем сообщения (помечаем как удаленные, не удаляем физически)
        user_messages = Message.objects.filter(sender=self.user)
        stats['messages_deleted'] = user_messages.update(is_deleted=True, deleted_by=self.user)

        # Удаляем медиафайлы
        user_files = UploadedFile.objects.filter(user=self.user)
        for file_obj in user_files:
            self._delete_file(file_obj.file)
            if file_obj.thumbnail:
                self._delete_file(file_obj.thumbnail)

        stats['files_deleted'] = user_files.count()
        user_files.delete()

        # Очищаем кэш
        self.clear_cache()

        return stats

    def get_cleanup_recommendations(self) -> dict:
        """Получить рекомендации по очистке"""
        recommendations = {}

        # Старые медиафайлы
        old_media_count = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=timezone.now() - timedelta(days=30),
            file_type__in=['image', 'video']
        ).count()

        if old_media_count > 0:
            recommendations['old_media'] = {
                'count': old_media_count,
                'size': self._calculate_old_media_size(),
                'action': 'Удалить медиафайлы старше 30 дней'
            }

        # Размер кэша
        cache_size = self._estimate_cache_size()
        if cache_size > 50 * 1024 * 1024:  # 50MB
            recommendations['cache'] = {
                'size': cache_size,
                'action': 'Очистить кэш приложения'
            }

        return recommendations

    def _calculate_old_media_size(self) -> int:
        """Рассчитать размер старых медиафайлов"""
        old_media = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=timezone.now() - timedelta(days=30),
            file_type__in=['image', 'video']
        ).aggregate(total=Sum('file_size'))

        return old_media['total'] or 0