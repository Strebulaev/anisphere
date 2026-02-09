#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from social.models import PrivateChat, Message
from users.models import User
from django.contrib.auth import get_user_model

def create_test_data():
    print("=== СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ ЧАТА ===")

    User = get_user_model()

    # Создаем двух тестовых пользователей
    user1, created1 = User.objects.get_or_create(
        username='testuser1',
        defaults={
            'email': 'test1@example.com',
            'first_name': 'Test',
            'last_name': 'User1',
            'is_active': True,
            'is_online': True
        }
    )
    if created1:
        user1.set_password('testpass123')
        user1.save()
        print(f'Создан новый пользователь: {user1.username} (ID: {user1.id})')
    else:
        print(f'Пользователь уже существует: {user1.username} (ID: {user1.id})')

    user2, created2 = User.objects.get_or_create(
        username='testuser2',
        defaults={
            'email': 'test2@example.com',
            'first_name': 'Test',
            'last_name': 'User2',
            'is_active': True,
            'is_online': False
        }
    )
    if created2:
        user2.set_password('testpass123')
        user2.save()
        print(f'Создан новый пользователь: {user2.username} (ID: {user2.id})')
    else:
        print(f'Пользователь уже существует: {user2.username} (ID: {user2.id})')

    # Создаем личный чат между двумя пользователями
    chat, created = PrivateChat.objects.get_or_create(
        user1=user1,
        user2=user2,
        defaults={}
    )

    if created:
        print(f'Создан новый чат: {chat} (ID: {chat.id})')
    else:
        print(f'Чат уже существует: {chat} (ID: {chat.id})')

    # Создаем несколько тестовых сообщений
    messages_data = [
        (user1, 'Привет! Как дела?'),
        (user2, 'Привет! Всё хорошо, спасибо!'),
        (user1, 'Рад слышать! Чем занимаешься?'),
        (user2, 'Смотрю аниме. А ты?'),
        (user1, 'Тоже смотрю. Рекомендую попробовать этот чат!'),
    ]

    for sender, text in messages_data:
        message, created = Message.objects.get_or_create(
            private_chat=chat,
            sender=sender,
            text=text,
            defaults={'text': text}
        )
        if created:
            print(f'Создано сообщение от {sender.username}: "{text}"')
        else:
            print(f'Сообщение от {sender.username} уже существует')

    print("\n=== СТАТИСТИКА ===")
    print(f'Пользователей: {User.objects.count()}')
    print(f'Чатов: {chat.objects.count()}')
    print(f'Сообщений: {Message.objects.count()}')

    print("\n=== ПРОВЕРКА УЧАСТИЯ ===")
    participants = chat.participants.all()
    print(f'Участники чата {chat.id}: {[u.username for u in participants]}')
    print(f'Статус онлайн user1: {user1.is_online}')
    print(f'Статус онлайн user2: {user2.is_online}')

    print("\nТестовые данные созданы! Теперь можно тестировать чат и ленту.")
    print("Используйте логины:")
    print("  testuser1, пароль: testpass123 (онлайн)")
    print("  testuser2, пароль: testpass123 (оффлайн)")

if __name__ == '__main__':
    create_test_data()