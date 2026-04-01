from django.db import models
from django.utils.text import slugify
from users.models import User
from anime.models import Anime


class Person(models.Model):
    """Персона (сейю, режиссёр, автор и т.д.)"""
    
    ROLE_CHOICES = [
        ('voice_actor', 'Сейю'),
        ('director', 'Режиссёр'),
        ('author', 'Автор оригинала'),
        ('composer', 'Композитор'),
        ('character', 'Персонаж'),
    ]
    
    # Основная информация
    name = models.CharField(max_length=200, verbose_name='Имя')
    name_jp = models.CharField(max_length=200, blank=True, verbose_name='Имя (японское)')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, verbose_name='Биография')
    
    # Фото
    photo_url = models.URLField(blank=True, verbose_name='URL фото')
    photo_file = models.ImageField(upload_to='people/', null=True, blank=True, verbose_name='Фото')
    
    # Дата рождения
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    
    # Роль (может быть несколько ролей)
    roles = models.JSONField(default=list, verbose_name='Роли')
    
    # Статистика
    works_count = models.IntegerField(default=0, verbose_name='Количество работ')
    
    # Связанное аниме (для персонажей)
    related_anime = models.ManyToManyField(Anime, related_name='related_people', blank=True)
    
    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

    def update_works_count(self):
        """Обновление количества работ"""
        self.works_count = self.anime_roles.count()
        self.save()

class DubGroup(models.Model):
    """Группа озвучки (студия озвучки)"""
    
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('inactive', 'Неактивна'),
        ('closed', 'Закрыта'),
    ]
    
    # Основная информация
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')
    name_jp = models.CharField(max_length=200, blank=True, verbose_name='Название (японское)')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Визуальные ресурсы
    logo_url = models.URLField(blank=True, verbose_name='URL логотипа')
    logo = models.ImageField(upload_to='dub_groups/logos/', null=True, blank=True, verbose_name='Логотип')
    banner_url = models.URLField(blank=True, verbose_name='URL баннера')
    banner = models.ImageField(upload_to='dub_groups/banners/', null=True, blank=True, verbose_name='Баннер')
    
    # Контактная информация
    website = models.URLField(blank=True, verbose_name='Официальный сайт')
    vk_url = models.URLField(blank=True, verbose_name='VK')
    telegram_url = models.URLField(blank=True, verbose_name='Telegram')
    discord_url = models.URLField(blank=True, verbose_name='Discord')
    youtube_url = models.URLField(blank=True, verbose_name='YouTube')
    twitter_url = models.URLField(blank=True, verbose_name='Twitter/X')
    
    # Детали
    founded_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Год основания')
    
    # Статистика (кэшированные поля)
    works_count = models.IntegerField(default=0, verbose_name='Всего озвучек')
    tv_count = models.PositiveIntegerField(default=0, verbose_name='ТВ сериалов')
    movie_count = models.PositiveIntegerField(default=0, verbose_name='Фильмов')
    ova_count = models.PositiveIntegerField(default=0, verbose_name='OVA/ONA')
    average_rating = models.FloatField(default=0.0, verbose_name='Средний рейтинг')
    subscribers_count = models.PositiveIntegerField(default=0, verbose_name='Подписчиков')
    
    # Жанровая статистика (JSON: {"Экшен": 65, "Фэнтези": 45, ...})
    genre_stats = models.JSONField(default=dict, blank=True, verbose_name='Статистика жанров')
    
    # Тип озвучки (для фильтрации)
    translation_type = models.CharField(max_length=20, choices=[
        ('voice', 'Озвучка'),
        ('subtitles', 'Субтитры'),
        ('both', 'Оба'),
    ], default='voice', verbose_name='Тип перевода')
    
    # Статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    is_verified = models.BooleanField(default=False, verbose_name='Верифицирована')
    
    # Рейтинги
    rating = models.FloatField(default=0.0)  # Средний рейтинг (устарел, используется average_rating)
    review_count = models.IntegerField(default=0)  # Количество отзывов
    
    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-average_rating', 'name']
        verbose_name = 'Группа озвучки'
        verbose_name_plural = 'Группы озвучки'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            if not base_slug:
                base_slug = f'dub-{self.pk or "new"}'
            slug = base_slug
            counter = 1
            while DubGroup.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
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
    
    def update_works_count(self):
        self.works_count = self.group_dubs.count()
        self.save()
    
    def update_subscribers_count(self):
        self.subscribers_count = self.subscriptions.count()
        self.save()


class DubGroupSubscription(models.Model):
    """Подписка пользователя на группу озвучки"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dub_group_subscriptions'
    )
    group = models.ForeignKey(
        DubGroup,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        verbose_name = 'Подписка на группу озвучки'
        verbose_name_plural = 'Подписки на группы озвучки'

    def __str__(self):
        return f'{self.user} → {self.group}'


class DubGroupRating(models.Model):
    """Оценка группы озвучки пользователем"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dub_group_ratings'
    )
    group = models.ForeignKey(
        DubGroup,
        on_delete=models.CASCADE,
        related_name='ratings'
    )

    # Оценки по категориям (1-5)
    voice_quality = models.IntegerField(default=5, verbose_name='Качество озвучки')
    timing = models.IntegerField(default=5, verbose_name='Синхронизация')
    translation = models.IntegerField(default=5, verbose_name='Перевод')
    consistency = models.IntegerField(default=5, verbose_name='Постоянство')

    overall_rating = models.FloatField(verbose_name='Общая оценка')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'group']
        verbose_name = 'Оценка группы озвучки'
        verbose_name_plural = 'Оценки групп озвучки'

    def save(self, *args, **kwargs):
        self.overall_rating = (
            self.voice_quality + self.timing +
            self.translation + self.consistency
        ) / 4
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} → {self.group}: {self.overall_rating}'


class DubGroupNews(models.Model):
    """Новости группы озвучки"""
    group = models.ForeignKey(DubGroup, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=300, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dub_group_news'
    )
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Новость группы озвучки'
        verbose_name_plural = 'Новости групп озвучки'

    def __str__(self):
        return f'{self.group.name}: {self.title}'


class DubGroupDiscussion(models.Model):
    """Обсуждение на странице группы озвучки"""
    group = models.ForeignKey(DubGroup, on_delete=models.CASCADE, related_name='discussions')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dub_group_discussions'
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
        verbose_name = 'Обсуждение группы озвучки'
        verbose_name_plural = 'Обсуждения групп озвучки'


class DubGroupDiscussionReply(models.Model):
    """Ответ на обсуждение группы озвучки"""
    discussion = models.ForeignKey(DubGroupDiscussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dub_group_discussion_replies'
    )
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ответ на обсуждение'
        verbose_name_plural = 'Ответы на обсуждения'

    def __str__(self):
        return f'Reply by {self.author} on {self.discussion}'


class VoiceActor(models.Model):
    """Актёр озвучки"""
    
    # Основная информация
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Фото
    photo_url = models.URLField(blank=True)
    photo_file = models.ImageField(upload_to='voice_actors/', null=True, blank=True)
    
    # Связи
    groups = models.ManyToManyField(DubGroup, related_name='voice_actors', blank=True)
    
    # Статистика
    roles_count = models.IntegerField(default=0)
    
    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Актёр озвучки'
        verbose_name_plural = 'Актёры озвучки'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Dub(models.Model):
    """Озвучка аниме (конкретная работа группы)"""
    
    TYPE_CHOICES = [
        ('full', 'Полная озвучка'),
        ('subtitles', 'Субтитры'),
        ('partial', 'Частичная озвучка'),
        ('voiceover', 'Закадровый перевод'),
    ]
    
    QUALITY_CHOICES = [
        ('unknown', 'Неизвестно'),
        ('low', 'Низкое'),
        ('medium', 'Среднее'),
        ('high', 'Высокое'),
        ('excellent', 'Отличное'),
    ]
    
    # Связи
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='dubs_works')
    group = models.ForeignKey(DubGroup, on_delete=models.CASCADE, related_name='group_dubs')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_dubs')
    
    # Информация об озвучке
    dub_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='full')
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, default='unknown')
    episodes_done = models.IntegerField(default=0)  # Сколько эпизодов озвучено
    total_episodes = models.IntegerField(null=True, blank=True)  # Всего эпизодов в аниме
    
    # Статус
    is_complete = models.BooleanField(default=False)
    is_abandoned = models.BooleanField(default=False)
    
    # Ссылки
    external_url = models.URLField(blank=True)  # Ссылка на озвучку
    torrent_url = models.URLField(blank=True)
    player_url = models.URLField(blank=True)  # Прямая ссылка на плеер
    
    # Даты
    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    last_episode_at = models.DateField(null=True, blank=True)
    
    # Рейтинги
    average_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    
    # Технические
    is_approved = models.BooleanField(default=True)
    
    # Время
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['anime', 'group']  # Одна группа может озвучить аниме только один раз
        verbose_name = 'Озвучка'
        verbose_name_plural = 'Озвучки'
    
    def __str__(self):
        return f"{self.group.name} - {self.anime.title_ru}"
    
    def save(self, *args, **kwargs):
        # Автоматически определяем завершённость
        if self.episodes_done == self.total_episodes:
            self.is_complete = True
        super().save(*args, **kwargs)
        
        # Обновляем счётчик работ группы
        self.group.update_works_count()


class DubRole(models.Model):
    """Роль актёра в конкретной озвучке"""
    
    dub = models.ForeignKey(Dub, on_delete=models.CASCADE, related_name='roles')
    actor = models.ForeignKey(VoiceActor, on_delete=models.CASCADE, related_name='roles')
    character_name = models.CharField(max_length=200)
    character_name_en = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_main', 'character_name']
        unique_together = ['dub', 'actor', 'character_name']


class DubReview(models.Model):
    """Отзыв на озвучку"""
    
    dub = models.ForeignKey(Dub, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dub_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    text = models.TextField()
    pros = models.TextField(blank=True)  # Плюсы
    cons = models.TextField(blank=True)  # Минусы
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['dub', 'user']


class DubLink(models.Model):
    """Ссылка на просмотр озвучки"""
    
    SOURCE_CHOICES = [
        ('jutsu', 'Jut.su'),
        ('animego', 'AnimeGo'),
        ('animedia', 'Animedia'),
        ('anime365', 'Anime365'),
        ('other', 'Другое'),
    ]
    
    dub = models.ForeignKey(Dub, on_delete=models.CASCADE, related_name='links')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    url = models.URLField()
    episode = models.IntegerField(null=True, blank=True)  # Конкретный эпизод
    quality = models.CharField(max_length=20, blank=True)  # 480p, 720p, 1080p
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['episode']


class UserDubPreference(models.Model):
    """Предпочтения пользователя по озвучкам"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dub_preferences')
    group = models.ForeignKey(DubGroup, on_delete=models.CASCADE, related_name='preferences')
    rating = models.IntegerField(default=0)  # -1, 0, 1 (не нравится, нейтрально, нравится)
    is_favorite = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'group']