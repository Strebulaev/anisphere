"""
Сервисы для социальной ленты
"""
from django.utils import timezone
from django.db.models import Count, Q
from typing import Optional, List
from datetime import timedelta

from social.models import Post, Group, Follow
from users.models import User


class SystemPostService:
    """Сервис для создания системных постов"""
    
    SYSTEM_TYPES = {
        'level_up': 'достиг нового уровня',
        'contest_win': 'победил в конкурсе',
        'contest_participation': 'участвует в конкурсе',
        'group_created': 'создал новую группу',
        'contest_started': 'начался новый конкурс',
        'achievement_unlocked': 'получил достижение',
        'milestone_reached': 'достиг важной отметки',
    }
    
    @classmethod
    def create_level_up_post(cls, user: User, new_level: int) -> Post:
        """Создать системный пост о повышении уровня"""
        return cls._create_system_post(
            user=user,
            system_type='level_up',
            title=f'🎉 Новый уровень!',
            text=f'{user.username} достиг {new_level} уровня! Поздравляем!',
        )
    
    @classmethod
    def create_contest_win_post(cls, user: User, contest_title: str, place: int) -> Post:
        """Создать системный пост о победе в конкурсе"""
        place_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}
        emoji = place_emoji.get(place, '🏆')
        
        return cls._create_system_post(
            user=user,
            system_type='contest_win',
            title=f'{emoji} Победа в конкурсе!',
            text=f'{user.username} занял(а) {place} место в конкурсе "{contest_title}"! Поздравляем!',
        )
    
    @classmethod
    def create_contest_participation_post(cls, user: User, contest_title: str) -> Post:
        """Создать системный пост об участии в конкурсе"""
        return cls._create_system_post(
            user=user,
            system_type='contest_participation',
            title=f'🎯 Участие в конкурсе',
            text=f'{user.username} участвует в конкурсе "{contest_title}"!',
        )
    
    @classmethod
    def create_group_created_post(cls, user: User, group: Group) -> Post:
        """Создать системный пост о создании группы"""
        return cls._create_system_post(
            user=user,
            system_type='group_created',
            title=f'👥 Новая группа',
            text=f'{user.username} создал(а) новую группу "{group.name}"!',
        )
    
    @classmethod
    def create_contest_started_post(cls, contest_title: str, organizer: User) -> Post:
        """Создать системный пост о начале конкурса"""
        return cls._create_system_post(
            user=organizer,
            system_type='contest_started',
            title=f'🏆 Новый конкурс!',
            text=f'Начался новый конкурс "{contest_title}"! Участвуйте!',
        )
    
    @classmethod
    def create_achievement_post(cls, user: User, achievement_name: str, achievement_level: str) -> Post:
        """Создать системный пост о получении достижения"""
        level_emoji = {
            'bronze': '🥉',
            'silver': '🥈', 
            'gold': '🥇',
            'legendary': '⭐',
        }
        emoji = level_emoji.get(achievement_level, '🏅')
        
        return cls._create_system_post(
            user=user,
            system_type='achievement_unlocked',
            title=f'{emoji} Достижение получено!',
            text=f'{user.username} разблокировал(а) достижение "{achievement_name}"!',
        )
    
    @classmethod
    def create_milestone_post(cls, user: User, milestone_type: str, value: int) -> Post:
        """Создать системный пост о достижении важной отметки"""
        milestone_texts = {
            'followers': f'{user.username} достиг {value} подписчиков!',
            'posts': f'{user.username} опубликовал(а) {value} постов!',
            'likes': f'{user.username} получил(а) {value} лайков!',
        }
        
        text = milestone_texts.get(milestone_type, f'{user.username} достиг новой отметки: {value}!')
        
        return cls._create_system_post(
            user=user,
            system_type='milestone_reached',
            title=f'🎯 Важная отметка!',
            text=text,
        )
    
    @classmethod
    def _create_system_post(cls, user: User, system_type: str, title: str, text: str) -> Post:
        """Внутренний метод для создания системного поста"""
        post = Post.objects.create(
            author=user,
            post_type='system',
            system_type=system_type,
            title=title,
            text=text,
            status='published',
            visibility='public',
            allow_comments=False,
            published_at=timezone.now(),
        )
        return post


class FeedGenerationService:
    """Сервис для генерации ленты пользователя"""
    
    WEIGHTS = {
        'subscriptions': 0.70,
        'groups': 0.15,
        'recommended': 0.10,
        'promoted': 0.05,
    }
    
    @classmethod
    def get_feed_queryset(cls, user: User, limit: int = 20, offset: int = 0):
        """Получить ленту для пользователя с учетом весов источников"""
        from social.models import GroupMembership, UserPostHidden
        
        subscriptions = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        member_groups = GroupMembership.objects.filter(
            user=user
        ).values_list('group_id', flat=True)
        
        hidden_post_ids = list(UserPostHidden.objects.filter(
            user=user
        ).values_list('post_id', flat=True))
        
        base_filter = Q(status='published') & ~Q(is_deleted=True)
        exclude_filter = Q(id__in=hidden_post_ids)
        visibility_filter = Q(visibility='public') | Q(author_id__in=subscriptions) | Q(author_id=user.id)
        
        # Свои посты — всегда показываем
        own_posts = Post.objects.filter(
            base_filter &
            Q(author_id=user.id)
        ).exclude(exclude_filter).select_related('author', 'anime', 'playlist')

        subscription_posts = Post.objects.filter(
            base_filter &
            visibility_filter &
            Q(author_id__in=subscriptions)
        ).exclude(exclude_filter).select_related('author', 'anime', 'playlist')
        
        group_posts = Post.objects.filter(
            base_filter &
            Q(group_id__in=member_groups)
        ).exclude(exclude_filter).select_related('author', 'anime', 'playlist', 'group')
        
        recommended_posts = Post.objects.filter(
            base_filter &
            Q(visibility='public') &
            ~Q(author_id__in=subscriptions) &
            ~Q(author_id=user.id) &
            ~Q(group_id__in=member_groups)
        ).exclude(
            id__in=hidden_post_ids
        ).order_by('-likes_count', '-comments_count', '-created_at').select_related(
            'author', 'anime', 'playlist'
        )[:50]
        
        subscription_count = int(limit * 1.5)
        group_count = int(limit * 0.5)

        own_posts_list = list(own_posts)
        subscription_posts = list(subscription_posts[:subscription_count])
        group_posts = list(group_posts[:group_count])
        
        mixed_posts = cls._mix_posts(
            own_posts_list,
            subscription_posts,
            group_posts,
            list(recommended_posts),
            limit
        )
        
        return mixed_posts[offset:offset + limit]
    
    @classmethod
    def _mix_posts(cls, own_posts: List[Post], subscription_posts: List[Post],
                   group_posts: List[Post], recommended_posts: List[Post], limit: int) -> List[Post]:
        """Смешать посты из разных источников с учетом весов"""
        import random

        random.shuffle(subscription_posts)
        random.shuffle(group_posts)
        random.shuffle(recommended_posts)
        # own_posts не перемешиваем — порядок по дате важен

        sub_count = int(limit * cls.WEIGHTS['subscriptions'])
        group_count = int(limit * cls.WEIGHTS['groups'])
        rec_count = limit - sub_count - group_count

        result = []
        result.extend(own_posts)              # свои посты — все
        result.extend(subscription_posts[:sub_count])
        result.extend(group_posts[:group_count])
        result.extend(recommended_posts[:rec_count])

        # Убираем дубли (собственные могут пересекаться с подписками)
        seen_ids = set()
        unique_result = []
        for post in result:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_result.append(post)

        unique_result.sort(key=lambda x: x.created_at, reverse=True)

        return unique_result
    
    @classmethod
    def get_user_feed_posts(cls, user: User, page: int = 1, per_page: int = 20):
        """Получить посты для ленты пользователя с пагинацией"""
        offset = (page - 1) * per_page
        posts = cls.get_feed_queryset(user, limit=per_page, offset=offset)
        
        pinned_posts = Post.objects.filter(
            author=user,
            is_pinned=True,
            status='published',
            is_deleted=False
        ).select_related('author', 'anime', 'playlist')
        
        return {
            'pinned': pinned_posts,
            'posts': posts,
        }
    
    @classmethod
    def get_group_feed(cls, group: Group, page: int = 1, per_page: int = 20):
        """Получить ленту группы"""
        offset = (page - 1) * per_page
        
        posts = Post.objects.filter(
            group=group,
            status='published',
            is_deleted=False
        ).select_related(
            'author', 'anime', 'playlist'
        ).order_by('-is_pinned', '-created_at')[offset:offset + per_page]
        
        return posts
    
    @classmethod
    def get_profile_posts(cls, user: User, page: int = 1, per_page: int = 20):
        """Получить посты профиля пользователя"""
        offset = (page - 1) * per_page
        
        posts = Post.objects.filter(
            author=user,
            status='published',
            is_deleted=False
        ).select_related(
            'author', 'anime', 'playlist', 'group'
        ).order_by('-is_pinned', '-created_at')[offset:offset + per_page]
        
        return posts


class TrendingService:
    """Сервис для определения популярных постов"""
    
    @classmethod
    def get_hot_posts(cls, hours: int = 24, limit: int = 20) -> List[Post]:
        """Получить горячие посты за последние N часов"""
        from django.db.models import F
        
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=time_threshold,
            post_type__in=['text', 'image', 'video', 'anime', 'playlist']
        ).select_related(
            'author', 'anime', 'group', 'playlist', 'reactor_post'
        ).prefetch_related(
            'media_files', 'hashtag_links__hashtag'
        ).order_by(
            '-likes_count', '-comments_count', '-created_at'
        )[:limit]
        
        return list(posts)
    
    @classmethod
    def get_top_posts(cls, days: int = 7, limit: int = 20) -> List[Post]:
        """Получить топ постов за последние N дней по лайкам"""
        time_threshold = timezone.now() - timedelta(days=days)
        
        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=time_threshold,
            post_type__in=['text', 'image', 'video', 'anime', 'playlist']
        ).order_by('-likes_count', '-comments_count', '-created_at')[:limit]
        
        return list(posts)
