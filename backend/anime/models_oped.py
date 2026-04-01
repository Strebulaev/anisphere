"""
Модель для хранения времени опенингов/эндингов аниме
"""
from django.db import models
from django.conf import settings


class AnimeOPED(models.Model):
    """Время опенингов и эндингов для аниме"""
    anime = models.ForeignKey(
        'anime.Anime',
        on_delete=models.CASCADE,
        related_name='oped',
        verbose_name='Аниме'
    )
    
    # Номер эпизода (null = одинаково для всех эпизодов)
    episode_number = models.PositiveIntegerField(
        'Номер эпизода',
        null=True,
        blank=True,
        help_text='Оставьте пустым, если тайминг одинаковый для всех эпизодов'
    )
    
    # Опенинг
    op_start = models.PositiveIntegerField(
        'Начало опенинга (сек)',
        null=True,
        blank=True
    )
    op_end = models.PositiveIntegerField(
        'Конец опенинга (сек)',
        null=True,
        blank=True
    )
    op_song = models.CharField(
        'Песня опенинга',
        max_length=500,
        blank=True,
        help_text='Название песни опенинга'
    )
    
    # Эндинг
    ed_start = models.PositiveIntegerField(
        'Начало эндинга (сек)',
        null=True,
        blank=True
    )
    ed_end = models.PositiveIntegerField(
        'Конец эндинга (сек)',
        null=True,
        blank=True
    )
    ed_song = models.CharField(
        'Песня эндинга',
        max_length=500,
        blank=True,
        help_text='Название песни эндинга'
    )
    
    # Источник данных
    data_source = models.CharField(
        'Источник',
        max_length=50,
        blank=True,
        default='manual'
    )
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'OP/ED аниме'
        verbose_name_plural = 'OP/ED аниме'
        ordering = ['anime', 'episode_number']
        unique_together = ['anime', 'episode_number']
    
    def __str__(self):
        ep = f" эпизод {self.episode_number}" if self.episode_number else " все эпизоды"
        return f"{self.anime.title_ru}{ep}"
