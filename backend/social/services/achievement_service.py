from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from social.models import Achievement, UserAchievement, Post, Follow, Repost
from users.models import User


class AchievementService:
    """Сервис для работы с достижениями"""

    def check_and_award(self, user):
        """Проверить все достижения и выдать новые"""
        new_achievements = []

        # Получаем все достижения
        achievements = Achievement.objects.all()

        for achievement in achievements:
            # Проверяем, уже ли получено достижение
            if UserAchievement.objects.filter(
                user=user,
                achievement=achievement,
                is_unlocked=True
            ).exists():
                continue

            # Проверяем условие достижения
            progress = self._check_achievement_condition(user, achievement)

            if progress >= achievement.condition_value:
                # Выдаём достижение
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'progress': progress,
                        'is_unlocked': True,
                        'unlocked_at': timezone.now()
                    }
                )

                if created:
                    achievement.unlocked_count += 1
                    achievement.save(update_fields=['unlocked_count'])
                    new_achievements.append(user_achievement)
            else:
                # Обновляем прогресс
                UserAchievement.objects.update_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'progress': progress,
                        'is_unlocked': False
                    }
                )

        return new_achievements

    def _check_achievement_condition(self, user, achievement):
        """Проверить условие достижения и вернуть прогресс"""
        condition_type = achievement.condition_type

        if condition_type == 'posts_count':
            return Post.objects.filter(author=user, is_deleted=False).count()

        elif condition_type == 'followers_count':
            return Follow.objects.filter(following=user).count()

        elif condition_type == 'following_count':
            return Follow.objects.filter(follower=user).count()

        elif condition_type == 'likes_received':
            return Post.objects.filter(author=user).aggregate(
                total=Count('likes')
            )['total'] or 0

        elif condition_type == 'reposts_count':
            return Repost.objects.filter(user=user).count()

        elif condition_type == 'reposts_received':
            return Post.objects.filter(author=user).aggregate(
                total=Count('reposts')
            )['total'] or 0

        elif condition_type == 'comments_count':
            from social.models import Comment
            return Comment.objects.filter(author=user, is_deleted=False).count()

        elif condition_type == 'registration_days':
            days = (timezone.now() - user.date_joined).days
            return days

        elif condition_type == 'profile_completed':
            score = 0
            if user.display_name:
                score += 25
            if user.avatar:
                score += 25
            if user.bio:
                score += 25
            if user.website:
                score += 25
            return score

        return 0


# Создаём экземпляр сервиса
achievement_service = AchievementService()
