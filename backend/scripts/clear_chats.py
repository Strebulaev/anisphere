#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from social.models import PrivateChat, GroupChat, Message, MessageReadStatus, ChatMember, ChatRole, ChatAdminLog, ChatSettings

def clear_all_chats():
    print("=== ОЧИСТКА ВСЕХ ЧАТОВ ===")

    # Удаляем в правильном порядке из-за foreign keys
    message_read_count = MessageReadStatus.objects.count()
    MessageReadStatus.objects.all().delete()
    print(f"Удалено статусов прочтения: {message_read_count}")

    message_count = Message.objects.count()
    Message.objects.all().delete()
    print(f"Удалено сообщений: {message_count}")

    chat_settings_count = ChatSettings.objects.count()
    ChatSettings.objects.all().delete()
    print(f"Удалено настроек чатов: {chat_settings_count}")

    admin_log_count = ChatAdminLog.objects.count()
    ChatAdminLog.objects.all().delete()
    print(f"Удалено логов админа: {admin_log_count}")

    member_count = ChatMember.objects.count()
    ChatMember.objects.all().delete()
    print(f"Удалено участников чатов: {member_count}")

    role_count = ChatRole.objects.count()
    ChatRole.objects.all().delete()
    print(f"Удалено ролей чатов: {role_count}")

    private_chat_count = PrivateChat.objects.count()
    PrivateChat.objects.all().delete()
    print(f"Удалено личных чатов: {private_chat_count}")

    group_chat_count = GroupChat.objects.count()
    GroupChat.objects.all().delete()
    print(f"Удалено групповых чатов: {group_chat_count}")

    print("\n=== ВСЕ ЧАТЫ ОЧИЩЕНЫ ===")

if __name__ == '__main__':
    clear_all_chats()