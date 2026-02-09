#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from social.models import Post
from users.models import User
from anime.models import Anime
from django.contrib.auth import get_user_model

def create_test_posts():
    print("=== СОЗДАНИЕ ТЕСТОВЫХ ПОСТОВ ===")

    User = get_user_model()

    # Создаем тестового пользователя если не существует
    user, created = User.objects.get_or_create(
        username='testuser1',
        defaults={
            'email': 'test1@example.com',
            'first_name': 'Test',
            'last_name': 'User1',
            'is_active': True,
            'is_online': True
        }
    )

    if created:
        user.set_password('testpass123')
        user.save()
        print(f'Создан пользователь: {user.username}')

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
        print(f'Создан пользователь: {user2.username}')

    # Ищем существующее аниме или создаем новое
    anime = Anime.objects.filter(title_ru='Атака титанов').first()
    if not anime:
        anime = Anime.objects.create(
            title_ru='Атака титанов',
            title_en='Attack on Titan',
            description='История о борьбе человечества с гигантскими существами.',
            year=2013,
            episodes=87,
            poster_url='https://example.com/poster.jpg',
            shikimori_id=16498  # Реальный ID Атаки Титанов на Shikimori
        )
        print(f'Создано аниме: {anime.title_ru}')
    else:
        print(f'Найдено существующее аниме: {anime.title_ru}')

    # Создаем тестовые посты
    posts_data = [
        {
            'author': user,
            'text': 'Смотрю "Атаку титанов" второй раз! Классика аниме. Кто со мной? #аниме #атакаТитанов',
            'anime': anime
        },
        {
            'author': user2,
            'text': 'Закончил смотреть "Твоё имя"! Очень трогательная история. Рекомендую всем! 💖',
        },
        {
            'author': user,
            'text': 'Ищу хорошую озвучку для нового сезона "Демона Слейера". Какие советуете?',
        },
        {
            'author': user2,
            'text': 'Создал свой первый плейлист в AnimeCore! Проверьте, если интересно. 🎵',
        },
        {
            'author': user,
            'text': 'Всем привет! Только что зарегистрировался здесь. Где можно найти хорошие обзоры на аниме?',
        }
    ]

    created_count = 0
    for post_data in posts_data:
        # Проверяем, существует ли уже такой пост
        existing_post = Post.objects.filter(
            author=post_data['author'],
            text=post_data['text']
        ).exists()

        if not existing_post:
            post = Post.objects.create(**post_data)
            print(f'Создан пост от {post.author.username}: "{post.text[:50]}..."')
            created_count += 1
        else:
            print(f'Пост от {post_data["author"].username} уже существует')

    print(f"\nСоздано {created_count} новых постов")

    # Статистика
    total_posts = Post.objects.count()
    print(f'Всего постов в системе: {total_posts}')

    # Выводим последние посты для проверки
    print("\n=== ПОСЛЕДНИЕ ПОСТЫ ===")
    recent_posts = Post.objects.order_by('-created_at')[:5]
    for post in recent_posts:
        print(f'{post.author.username}: {post.text[:60]}...')

    print("\nТестовые посты созданы! Теперь лента должна быть наполнена содержимым.")

if __name__ == '__main__':
    create_test_posts()