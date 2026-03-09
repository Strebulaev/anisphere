from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.db.models import Avg, Count


class Studio(models.Model):
    """Аниме-студия"""

    # Основная информация
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')
    name_jp = models.CharField(max_length=200, blank=True, verbose_name='Название (японское)')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, verbose_name='Описание')

    # Визуальные ресурсы
    logo_url = models.URLField(blank=True, verbose_name='URL логотипа')
    logo = models.ImageField(upload_to='studios/logos/', null=True, blank=True, verbose_name='Логотип')
    banner_url = models.URLField(blank=True, verbose_name='URL баннера')
    banner = models.ImageField(upload_to='studios/banners/', null=True, blank=True, verbose_name='Баннер')

    # Детали
    country = models.CharField(max_length=100, default='Япония', verbose_name='Страна')
    founded_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Год основания')
    website = models.URLField(blank=True, verbose_name='Официальный сайт')
    twitter = models.URLField(blank=True, verbose_name='Twitter/X')
    youtube = models.URLField(blank=True, verbose_name='YouTube')
    facebook = models.URLField(blank=True, verbose_name='Facebook')
    employees_count = models.CharField(max_length=50, blank=True, verbose_name='Количество сотрудников')

    # Статистика (кэшированные поля)
    total_anime = models.PositiveIntegerField(default=0, verbose_name='Всего аниме')
    tv_count = models.PositiveIntegerField(default=0, verbose_name='ТВ сериалов')
    movie_count = models.PositiveIntegerField(default=0, verbose_name='Фильмов')
    ova_count = models.PositiveIntegerField(default=0, verbose_name='OVA/ONA')
    average_rating = models.FloatField(default=0.0, verbose_name='Средний рейтинг')
    subscribers_count = models.PositiveIntegerField(default=0, verbose_name='Подписчиков')

    # Известные работы (JSON список названий)
    notable_works = models.JSONField(default=list, blank=True, verbose_name='Известные работы')

    # Жанровая статистика (JSON: {"Экшен": 65, "Фэнтези": 45, ...})
    genre_stats = models.JSONField(default=dict, blank=True, verbose_name='Статистика жанров')

    # Флаги
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    is_verified = models.BooleanField(default=False, verbose_name='Верифицирована')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-average_rating', 'name']
        verbose_name = 'Студия'
        verbose_name_plural = 'Студии'

    def __str__(self):
        return self.name

    @property
    def logo_image_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return self.logo_url or ''

    @property
    def banner_image_url(self):
        if self.banner and hasattr(self.banner, 'url'):
            return self.banner.url
        return self.banner_url or ''

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            if not base_slug:
                base_slug = f'studio-{self.pk or "new"}'
            slug = base_slug
            counter = 1
            while Studio.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class StudioAnime(models.Model):
    """Связь студии с аниме (из Kodik API / JSON поля anime.studios)"""
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='studio_anime')

    # Kodik ID (уникален в паре studio+kodik_id)
    kodik_id = models.CharField(max_length=50, default='', verbose_name='Kodik ID')

    # Ссылка на локальный объект аниме (если совпал по shikimori_id)
    anime_db_id = models.IntegerField(null=True, blank=True, verbose_name='ID аниме в БД')

    # Основные поля
    anime_title = models.CharField(max_length=255, verbose_name='Название аниме')
    anime_title_en = models.CharField(max_length=255, blank=True, verbose_name='Английское название')
    anime_kind = models.CharField(max_length=20, default='tv', verbose_name='Тип аниме')
    anime_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Год аниме')
    anime_score = models.FloatField(null=True, blank=True, verbose_name='Рейтинг аниме')
    anime_poster = models.URLField(max_length=500, blank=True, verbose_name='Постер аниме')
    anime_status = models.CharField(max_length=50, blank=True, verbose_name='Статус аниме')
    shikimori_id = models.CharField(max_length=50, blank=True, verbose_name='Shikimori ID')
    episodes_total = models.PositiveIntegerField(null=True, blank=True, verbose_name='Эпизодов всего')
    description = models.TextField(blank=True, verbose_name='Описание')
    genres = models.JSONField(default=list, blank=True, verbose_name='Жанры')

    class Meta:
        unique_together = ['studio', 'kodik_id']
        ordering = ['-anime_year', '-anime_score']
        verbose_name = 'Аниме студии'
        verbose_name_plural = 'Аниме студий'


class StudioSubscription(models.Model):
    """Подписка пользователя на студию"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='studio_subscriptions'
    )
    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'studio']
        verbose_name = 'Подписка на студию'
        verbose_name_plural = 'Подписки на студии'

    def __str__(self):
        return f'{self.user} → {self.studio}'


class StudioRating(models.Model):
    """Оценка студии пользователем"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='studio_ratings'
    )
    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name='ratings'
    )

    # Оценки по категориям (1-5)
    animation_quality = models.IntegerField(default=5, verbose_name='Качество анимации')
    directing = models.IntegerField(default=5, verbose_name='Режиссура')
    soundtrack = models.IntegerField(default=5, verbose_name='Саундтрек')
    adaptation = models.IntegerField(default=5, verbose_name='Адаптация')

    overall_rating = models.FloatField(verbose_name='Общая оценка')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'studio']
        verbose_name = 'Оценка студии'
        verbose_name_plural = 'Оценки студий'

    def save(self, *args, **kwargs):
        self.overall_rating = (
            self.animation_quality + self.directing +
            self.soundtrack + self.adaptation
        ) / 4
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} → {self.studio}: {self.overall_rating}'


class StudioNews(models.Model):
    """Новости студии"""
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=300, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='studio_news'
    )
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Новость студии'
        verbose_name_plural = 'Новости студий'

    def __str__(self):
        return f'{self.studio.name}: {self.title}'


class StudioAward(models.Model):
    """Награда студии"""
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='awards')
    year = models.PositiveIntegerField(verbose_name='Год')
    award_name = models.CharField(max_length=200, verbose_name='Название премии')
    category = models.CharField(max_length=200, verbose_name='Категория/Номинация')
    is_winner = models.BooleanField(default=True, verbose_name='Победитель')

    class Meta:
        ordering = ['-year']
        verbose_name = 'Награда студии'
        verbose_name_plural = 'Награды студий'


class StudioDiscussion(models.Model):
    """Обсуждение на странице студии"""
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='discussions')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='studio_discussions'
    )
    title = models.CharField(max_length=300, verbose_name='Заголовок темы')
    content = models.TextField(verbose_name='Содержание')
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_reply_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Обсуждение студии'
        verbose_name_plural = 'Обсуждения студий'


class StudioDiscussionReply(models.Model):
    """Reply to a studio discussion"""
    discussion = models.ForeignKey(StudioDiscussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='studio_discussion_replies'
    )
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ответ на обсуждение'
        verbose_name_plural = 'Ответы на обсуждения'

    def __str__(self):
        return f'Reply by {self.author} on {self.discussion}'


class StudioStaff(models.Model):
    """Сотрудник студии"""
    ROLE_CHOICES = [
        ('director', 'Режиссёр'),
        ('animator', 'Аниматор'),
        ('composer', 'Композитор'),
        ('voice_actor', 'Актёр озвучки'),
        ('founder', 'Основатель'),
        ('ceo', 'CEO'),
        ('other', 'Другое'),
    ]

    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='staff')
    name = models.CharField(max_length=200, verbose_name='Имя')
    name_jp = models.CharField(max_length=200, blank=True, verbose_name='Имя (японское)')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, verbose_name='Роль')
    role_detail = models.CharField(max_length=200, blank=True, verbose_name='Детали роли')
    photo_url = models.URLField(blank=True, verbose_name='URL фото')
    works_count = models.PositiveIntegerField(default=0, verbose_name='Количество работ')
    notable_works = models.JSONField(default=list, blank=True, verbose_name='Известные работы')
    is_key_person = models.BooleanField(default=False, verbose_name='Ключевая персона')
    awards = models.JSONField(default=list, blank=True, verbose_name='Награды')

    class Meta:
        ordering = ['-is_key_person', 'role', 'name']
        verbose_name = 'Сотрудник студии'
        verbose_name_plural = 'Сотрудники студий'

    def __str__(self):
        return f'{self.name} ({self.studio.name})'
