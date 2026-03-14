"""
Модели для рулетки аниме (Колесо фортуны)
"""
import uuid
from django.db import models
from django.conf import settings


class AnimeRoulette(models.Model):
    """Рулетка аниме (Колесо фортуны)"""

    class Theme(models.TextChoices):
        LIGHT = 'light', 'Светлая'
        DARK = 'dark', 'Тёмная'
        ANIME = 'anime', 'Аниме-тема'

    class WheelSize(models.TextChoices):
        SMALL = 'small', 'Малый (300px)'
        MEDIUM = 'medium', 'Средний (400px)'
        LARGE = 'large', 'Большой (500px)'

    class DisplayMode(models.TextChoices):
        POSTERS = 'posters', 'Постеры'
        TITLES = 'titles', 'Названия'
        BOTH = 'both', 'Постеры и названия'

    class ColorScheme(models.TextChoices):
        RAINBOW = 'rainbow', 'Радуга'
        RATING = 'rating', 'По рейтингу'
        MONOCHROME = 'monochrome', 'Монохром'

    class AnimationStyle(models.TextChoices):
        SMOOTH = 'smooth', 'Плавная'
        FAST = 'fast', 'Быстрая'
        CINEMATIC = 'cinematic', 'Кинематографичная'

    class WeightMode(models.TextChoices):
        PROPORTIONAL = 'proportional', 'Пропорционально'
        RATING = 'rating', 'Только рейтинг'
        MANUAL = 'manual', 'Ручные'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roulettes'
    )
    name = models.CharField('Название рулетки', max_length=100, default='Моя рулетка')
    
    # Настройки рулетки
    spin_duration = models.IntegerField(
        'Длительность вращения (секунды)',
        default=5,
        help_text='Сколько секунд крутится колесо'
    )
    
    # Настройки внешнего вида
    theme = models.CharField(
        'Тема',
        max_length=20,
        choices=Theme.choices,
        default=Theme.DARK
    )
    wheel_size = models.CharField(
        'Размер колеса',
        max_length=20,
        choices=WheelSize.choices,
        default=WheelSize.MEDIUM
    )
    display_mode = models.CharField(
        'Режим отображения',
        max_length=20,
        choices=DisplayMode.choices,
        default=DisplayMode.BOTH
    )
    color_scheme = models.CharField(
        'Цветовая схема',
        max_length=20,
        choices=ColorScheme.choices,
        default=ColorScheme.RAINBOW
    )
    animation_style = models.CharField(
        'Стиль анимации',
        max_length=20,
        choices=AnimationStyle.choices,
        default=AnimationStyle.SMOOTH
    )
    
    # Настройки звука
    sound_enabled = models.BooleanField('Звук включён', default=True)
    sound_type = models.CharField(
        'Тип звука',
        max_length=50,
        default='default',
        help_text='default, tick, whoosh, custom'
    )

    # Настройки поведения
    default_spin_count = models.IntegerField(
        'Количество аниме по умолчанию',
        default=1,
        help_text='Сколько аниме выбирать за раз'
    )
    weight_mode = models.CharField(
        'Режим расчёта весов',
        max_length=20,
        choices=WeightMode.choices,
        default=WeightMode.PROPORTIONAL
    )
    exclude_recent = models.BooleanField(
        'Исключать недавно выпавшие',
        default=False,
        help_text='Исключать аниме, которые недавно выпадали'
    )
    exclusion_period = models.IntegerField(
        'Период исключения (дней)',
        default=7,
        help_text='Сколько дней не показывать выпавшее аниме'
    )

    # Лимиты
    max_items = models.IntegerField(
        'Максимум аниме в колесе',
        default=50,
        help_text='Максимальное количество аниме в колесе'
    )
    max_spin_items = models.IntegerField(
        'Максимум аниме за раз',
        default=10,
        help_text='Максимальное количество аниме, которые можно выбрать за раз'
    )
    history_limit = models.IntegerField(
        'Лимит истории',
        default=100,
        help_text='Сколько записей истории хранить'
    )

    # Автоматическое добавление
    auto_add_from_collection = models.BooleanField(
        'Автоматически добавлять из коллекции',
        default=False
    )
    auto_add_from_playlists = models.BooleanField(
        'Автоматически добавлять из плейлистов',
        default=False
    )

    # Результат последней крутки
    last_result = models.ForeignKey(
        'AnimeRouletteItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_in'
    )
    last_spin_at = models.DateTimeField(null=True, blank=True)

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Рулетка аниме'
        verbose_name_plural = 'Рулетки аниме'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.user.username})'

    @property
    def total_weight(self):
        """Общий вес всех элементов"""
        return self.items.aggregate(total=models.Sum('weight'))['total'] or 0

    @property
    def items_count(self):
        """Количество элементов"""
        return self.items.count()

    def get_wheel_size_px(self):
        """Получить размер колеса в пикселях"""
        sizes = {
            self.WheelSize.SMALL: 300,
            self.WheelSize.MEDIUM: 400,
            self.WheelSize.LARGE: 500,
        }
        return sizes.get(self.wheel_size, 400)


class AnimeRouletteItem(models.Model):
    """Элемент рулетки (аниме с весом)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roulette = models.ForeignKey(
        AnimeRoulette,
        on_delete=models.CASCADE,
        related_name='items'
    )
    anime_id = models.IntegerField('ID аниме')
    anime_title = models.CharField('Название аниме', max_length=255)
    anime_poster = models.URLField('Постер аниме', null=True, blank=True)
    
    # Вес элемента (чем больше, тем больше сектор на колесе)
    weight = models.IntegerField(
        'Вес',
        default=1,
        help_text='Чем больше вес, тем больше сектор на колесе'
    )
    
    # Цвет сектора (автогенерация или ручной выбор)
    color = models.CharField('Цвет сектора', max_length=7, default='#667eea')
    
    # Порядок отображения
    order = models.IntegerField('Порядок', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Элемент рулетки'
        verbose_name_plural = 'Элементы рулетки'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f'{self.anime_title} (вес: {self.weight})'


class RouletteSpinHistory(models.Model):
    """История круток рулетки"""

    class SpinType(models.TextChoices):
        SINGLE = 'single', 'Одиночная'
        MULTIPLE = 'multiple', 'Множественная'
        MARATHON = 'marathon', 'Марафон'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roulette = models.ForeignKey(
        AnimeRoulette,
        on_delete=models.CASCADE,
        related_name='spin_history'
    )
    winner = models.ForeignKey(
        AnimeRouletteItem,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wins'
    )
    
    # Для множественного выбора и марафона
    spin_type = models.CharField(
        'Тип крутки',
        max_length=20,
        choices=SpinType.choices,
        default=SpinType.SINGLE
    )
    winners = models.ManyToManyField(
        'AnimeRouletteItem',
        related_name='multi_wins',
        blank=True,
        help_text='Для множественного выбора и марафона'
    )

    # Данные о крутке
    rotation_angle = models.FloatField('Угол поворота')
    spin_duration = models.FloatField('Длительность вращения')
    items_count = models.IntegerField(
        'Количество выбранных аниме',
        default=1
    )
    
    # Дополнительные данные
    is_favorite = models.BooleanField(
        'В избранном',
        default=False,
        help_text='Пользователь добавил результат в избранное'
    )
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Заметки пользователя к результату'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'История крутки'
        verbose_name_plural = 'История круток'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.spin_type == self.SpinType.SINGLE:
            return f'Крутка {self.roulette.name} - {self.winner.anime_title if self.winner else "N/A"}'
        return f'{self.get_spin_type_display()} {self.roulette.name} - {self.items_count} аниме'


class RoulettePreset(models.Model):
    """Сохранённый набор (пресет) для рулетки"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roulette_presets'
    )
    name = models.CharField('Название набора', max_length=100)
    description = models.TextField('Описание', blank=True)

    # Данные набора
    items_data = models.JSONField(
        'Данные элементов',
        default=list,
        help_text='Список элементов в формате [{"anime_id": 1, "weight": 2, "color": "#fff"}, ...]'
    )

    # Настройки
    settings_snapshot = models.JSONField(
        'Снимок настроек',
        default=dict,
        help_text='Настройки рулетки на момент создания пресета'
    )

    # Статистика
    items_count = models.IntegerField('Количество аниме', default=0)
    times_used = models.IntegerField('Количество использований', default=0)

    # Метаданные
    is_public = models.BooleanField(
        'Публичный набор',
        default=False,
        help_text='Другие пользователи могут использовать этот набор'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Пресет рулетки'
        verbose_name_plural = 'Пресеты рулетки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.username}) - {self.items_count} аниме'


class RouletteStatistics(models.Model):
    """Статистика рулетки"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roulette = models.OneToOneField(
        AnimeRoulette,
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    # Общая статистика
    total_spins = models.IntegerField('Всего круток', default=0)
    single_spins = models.IntegerField('Одиночных круток', default=0)
    multiple_spins = models.IntegerField('Множественных круток', default=0)
    marathon_spins = models.IntegerField('Марафонов', default=0)

    # Статистика по элементам
    most_spun_anime_id = models.IntegerField(
        'ID самого частого аниме',
        null=True,
        blank=True
    )
    most_spun_count = models.IntegerField(
        'Количество выпадений',
        default=0
    )
    least_spun_anime_id = models.IntegerField(
        'ID самого редкого аниме',
        null=True,
        blank=True
    )
    least_spun_count = models.IntegerField(
        'Количество выпадений',
        default=0
    )

    # Разнообразие
    unique_anime_spun = models.IntegerField(
        'Уникальных аниме выпало',
        default=0
    )

    # Временная статистика
    last_7_days_spins = models.IntegerField('Круток за 7 дней', default=0)
    last_30_days_spins = models.IntegerField('Круток за 30 дней', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Статистика рулетки'
        verbose_name_plural = 'Статистика рулеток'

    def __str__(self):
        return f'Статистика {self.roulette.name}'
