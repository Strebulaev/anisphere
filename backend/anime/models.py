from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Manager
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from multiprocessing import connection

# Импорт модели OP/ED
from .models_oped import AnimeOPED


class AnimeEpisodeNotification(models.Model):
    """Подписка на уведомления о новых сериях аниме"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    anime = models.ForeignKey(
        "Anime", on_delete=models.CASCADE, related_name="episode_notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "anime")
        verbose_name = "Подписка на уведомления о сериях"
        verbose_name_plural = "Подписки на уведомления о сериях"

    def __str__(self):
        return f"{self.user.username} -> {self.anime.title_ru}"


class Franchise(models.Model):
    """Франшиза — группировка аниме (сезоны, фильмы, OVA и т.д.)"""

    name = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(max_length=255, blank=True, verbose_name="Слаг")
    description = models.TextField(blank=True, verbose_name="Описание")
    poster_url = models.URLField(blank=True, verbose_name="URL постера")
    poster = models.ImageField(upload_to="franchise_posters/", null=True, blank=True)
    score = models.FloatField(null=True, blank=True, verbose_name="Рейтинг (усредн.)")
    year_start = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Год начала"
    )
    year_end = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Год конца"
    )

    # Агрегированные данные (кэшируются для производительности)
    genres = models.JSONField(
        default=list, blank=True, verbose_name="Жанры всех частей"
    )
    parts_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество частей"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score"]
        verbose_name = "Франшиза"
        verbose_name_plural = "Франшизы"

    def __str__(self):
        return self.name

    @property
    def poster_image_url(self):
        if self.poster and hasattr(self.poster, "url"):
            return self.poster.url
        return self.poster_url

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def update_aggregated_data(self):
        """Обновляет агрегированные данные франшизы (оценка, годы, жанры)"""
        entries = self.entries.all()
        if not entries:
            return

        # Количество частей
        self.parts_count = entries.count()

        # Средняя оценка
        scores = [e.score for e in entries if e.score]
        self.score = sum(scores) / len(scores) if scores else None

        # Годы
        years = [e.year for e in entries if e.year]
        if years:
            self.year_start = min(years)
            self.year_end = max(years)

        # Жанры (совокупность всех жанров)
        all_genres = set()
        for entry in entries:
            if entry.genres:
                all_genres.update(entry.genres)
        self.genres = list(all_genres)

        self.save(
            update_fields=["score", "year_start", "year_end", "genres", "parts_count"]
        )

    @property
    def parts_count(self):
        """Количество частей во франшизе"""
        return self.entries.count()

    @property
    def all_genres(self):
        """Все жанры всех частей франшизы"""
        genres = set()
        for entry in self.entries.all():
            if entry.genres:
                genres.update(entry.genres)
        return list(genres)

    @property
    def all_posters(self):
        """Список постеров всех частей франшизы"""
        posters = []
        for entry in self.entries.all().order_by("franchise_order"):
            if entry.poster and hasattr(entry.poster, "url"):
                posters.append(entry.poster.url)
            elif entry.poster_url:
                posters.append(entry.poster_url)
        return posters

    @property
    def year_range(self):
        """Период выхода (строка)"""
        if self.year_start and self.year_end:
            if self.year_start == self.year_end:
                return str(self.year_start)
            return f"{self.year_start} – {self.year_end}"
        elif self.year_start:
            return str(self.year_start)
        elif self.year_end:
            return str(self.year_end)
        return "—"


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.name


class BulkImportManager(Manager):
    """Менеджер для массовой вставки"""

    def bulk_create_fast(self, objs, batch_size=1000):
        """Быстрая массовая вставка с использованием RAW SQL"""
        if not objs:
            return

        model = self.model
        fields = [f for f in model._meta.fields if not f.auto_created]
        field_names = [f.column for f in fields]

        placeholders = ["%s"] * len(field_names)
        sql = f"""
            INSERT INTO {model._meta.db_table} ({",".join(field_names)})
            VALUES ({",".join(placeholders)})
            ON CONFLICT DO NOTHING
        """

        with connection.cursor() as cursor:
            for i in range(0, len(objs), batch_size):
                batch = objs[i : i + batch_size]
                values = []
                for obj in batch:
                    row = []
                    for field in fields:
                        value = getattr(obj, field.attname)
                        row.append(value)
                    values.append(row)

                cursor.executemany(sql, values)
                for obj in batch:
                    print(
                        f"✅ Bulk imported: {obj.title_ru or obj.title_en or f'ID:{obj.shikimori_id}'}"
                    )
                print(f"Вставлено {i + len(batch)}/{len(objs)} записей")


class Studio(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Студия"
        verbose_name_plural = "Студии"

    def __str__(self):
        return self.name


class Anime(models.Model):
    STATUS_CHOICES = [
        ("ongoing", "Онгоинг"),
        ("finished", "Завершен"),
        ("announced", "Анонсирован"),
        ("released", "Вышел"),
        ("canceled", "Отменен"),
    ]

    KIND_CHOICES = [
        ("tv", "ТВ сериал"),
        ("movie", "Фильм"),
        ("ova", "OVA"),
        ("special", "Спецвыпуск"),
        ("ona", "ONA"),
        ("music", "Клип"),
        ("franchise", "Франшиза"),
    ]

    shikimori_id = models.IntegerField(unique=True, null=True, blank=True)
    mal_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, verbose_name="MAL ID"
    )

    # Дата выхода (для анонсов)
    release_date = models.DateField(null=True, blank=True, verbose_name="Дата выхода")
    release_date_string = models.CharField(
        max_length=100, blank=True, verbose_name="Дата выхода (строка)"
    )

    title_ru = models.CharField(max_length=255, verbose_name="Название на русском")
    title_en = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Название на английском"
    )
    title_jp = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Название на японском"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name="Год")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="finished", verbose_name="Статус"
    )
    kind = models.CharField(
        max_length=20, choices=KIND_CHOICES, default="tv", verbose_name="Тип"
    )
    episodes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Количество эпизодов"
    )
    episode_duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Длительность эпизода (мин)"
    )
    score = models.FloatField(null=True, blank=True, verbose_name="Рейтинг")
    poster_url = models.URLField(blank=True, verbose_name="URL постера")
    poster = models.ImageField(
        upload_to="anime_posters/", null=True, blank=True, verbose_name="Постер аниме"
    )

    # JSON поля для жанров и студий
    genres = models.JSONField(default=list, blank=True, verbose_name="Жанры")
    studios = models.JSONField(default=list, blank=True, verbose_name="Студии")

    # Поля для франшиз
    movies = models.JSONField(default=list, blank=True, verbose_name="Фильмы франшизы")
    ovas = models.JSONField(default=list, blank=True, verbose_name="OVA франшизы")
    movie_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество фильмов"
    )
    ova_count = models.PositiveIntegerField(default=0, verbose_name="Количество OVA")
    total_items = models.PositiveIntegerField(
        default=1, verbose_name="Общее количество элементов"
    )

    # Kodik поля
    kodik_link = models.URLField(blank=True, verbose_name="Ссылка на плеер Kodik")
    kodik_id = models.CharField(max_length=100, blank=True, verbose_name="Kodik ID")
    quality = models.CharField(max_length=20, blank=True, verbose_name="Качество видео")
    screenshots = models.JSONField(default=list, blank=True, verbose_name="Скриншоты")
    seasons = models.JSONField(default=dict, blank=True, verbose_name="Сезоны и серии")
    last_season = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Последний сезон"
    )
    last_episode = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Последняя серия"
    )
    translations = models.JSONField(default=list, blank=True, verbose_name="Переводы")

    data_source = models.CharField(
        max_length=20, default="unknown", verbose_name="Источник данных"
    )
    is_available = models.BooleanField(
        default=True, verbose_name="Доступно для просмотра"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Франшиза
    franchise = models.ForeignKey(
        "Franchise",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
        verbose_name="Франшиза",
    )
    franchise_order = models.PositiveIntegerField(
        default=0, verbose_name="Порядок во франшизе"
    )

    class Meta:
        verbose_name = "Аниме"
        verbose_name_plural = "Аниме"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title_ru

    @property
    def poster_image_url(self):
        """Возвращает URL локального изображения или внешний URL"""
        if self.poster and hasattr(self.poster, "url"):
            return self.poster.url
        return self.poster_url

    @property
    def display_title(self):
        """Возвращает отображаемое название с дополнительной информацией"""
        if self.kind == "franchise":
            return f"{self.title_ru} (Франшиза)"
        return self.title_ru

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="anime_playlists",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Плейлист"
        verbose_name_plural = "Плейлисты"

    def __str__(self):
        return self.name


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="items"
    )
    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="in_playlists"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "added_at"]
        verbose_name = "Элемент плейлиста"
        verbose_name_plural = "Элементы плейлиста"
        unique_together = ["playlist", "anime"]

    def __str__(self):
        return f"{self.playlist.name} - {self.anime.title_ru}"


class VoiceActor(models.Model):
    """Актер озвучки"""

    name = models.CharField(max_length=200)
    name_original = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    photo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # Контакты
    vk_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Статистика
    is_verified = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DubStudio(models.Model):
    """Студия озвучки (AniMedia, AniLibria, SHIZA Project и т.д.)"""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)

    # Контакты
    website_url = models.URLField(blank=True)
    vk_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Статус
    is_official = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Активна"),
            ("inactive", "Неактивна"),
            ("closed", "Закрыта"),
        ],
        default="active",
    )

    # Статистика
    rating = models.FloatField(default=0.0)
    works_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Студия озвучки"
        verbose_name_plural = "Студии озвучки"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Dub(models.Model):
    """Озвучка конкретного аниме"""

    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="anime_dubs"
    )
    studio = models.ForeignKey(
        DubStudio, on_delete=models.CASCADE, related_name="studio_dubs"
    )

    # Информация об озвучке
    title = models.CharField(max_length=500, blank=True)  # "Озвучка AniMedia"
    description = models.TextField(blank=True)
    quality = models.CharField(
        max_length=20,
        choices=[
            ("bd", "Blu-ray"),
            ("dvd", "DVD"),
            ("tv", "TV"),
            ("web", "Web"),
            ("unknown", "Неизвестно"),
        ],
        default="unknown",
    )

    # Ссылки на просмотр
    player_url = models.URLField(blank=True)  # Ссылка на плеер с озвучкой
    download_url = models.URLField(blank=True)  # Ссылка на скачивание
    torrent_url = models.URLField(blank=True)  # Торрент-ссылка

    # Метаданные
    episodes_count = models.IntegerField(default=0)  # Сколько серий озвучено
    is_complete = models.BooleanField(default=False)  # Завершена ли озвучка полностью
    is_ongoing = models.BooleanField(default=True)  # Актуальна ли озвучка

    # Дата выпуска
    released_at = models.DateField(null=True, blank=True)
    updated_at = models.DateField(null=True, blank=True)

    # Рейтинг пользователей
    rating = models.FloatField(default=0.0)
    votes_count = models.IntegerField(default=0)

    # Технические
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-rating", "-released_at"]
        unique_together = ["anime", "studio"]

    def __str__(self):
        return f"{self.anime.title_ru} - {self.studio.name}"


class DubRole(models.Model):
    """Роль актера в озвучке"""

    dub = models.ForeignKey(Dub, on_delete=models.CASCADE, related_name="roles")
    actor = models.ForeignKey(
        VoiceActor, on_delete=models.CASCADE, related_name="roles"
    )
    character_name = models.CharField(max_length=200)  # Имя персонажа
    character_name_original = models.CharField(
        max_length=200, blank=True
    )  # Оригинальное имя

    ROLE_TYPE_CHOICES = [
        ("main", "Главная роль"),
        ("supporting", "Второстепенная роль"),
        ("guest", "Эпизодическая роль"),
        ("narrator", "Рассказчик"),
    ]

    role_type = models.CharField(
        max_length=20, choices=ROLE_TYPE_CHOICES, default="supporting"
    )
    order = models.IntegerField(default=0)  # Для сортировки

    class Meta:
        ordering = ["order", "character_name"]

    def __str__(self):
        return f"{self.character_name} - {self.actor.name}"


class UserDubRating(models.Model):
    """Оценка пользователем озвучки"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="dub_ratings"
    )
    dub = models.ForeignKey(Dub, on_delete=models.CASCADE, related_name="user_ratings")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])  # 1-10
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "dub"]

    def __str__(self):
        return f"{self.user.username} - {self.dub} - {self.rating}"


class VideoSource(models.Model):
    """Источник видео для аниме (Kodik, Aniboom и др.)"""

    SOURCE_CHOICES = [
        ("kodik", "Kodik"),
        ("aniboom", "AniBoom"),
        ("jutsu", "Jutsu"),
        ("shikimori", "Shikimori"),
    ]

    QUALITY_CHOICES = [
        ("360", "360p"),
        ("480", "480p"),
        ("720", "720p"),
        ("1080", "1080p"),
        ("unknown", "Неизвестно"),
    ]

    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="video_sources"
    )
    source = models.CharField("Источник", max_length=20, choices=SOURCE_CHOICES)
    external_id = models.CharField("Внешний ID", max_length=100, blank=True)

    # Основная информация
    title = models.CharField("Название", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)

    # Техническая информация
    quality = models.CharField(
        "Качество", max_length=10, choices=QUALITY_CHOICES, default="unknown"
    )
    video_format = models.CharField("Формат видео", max_length=20, default="mp4")
    duration = models.PositiveIntegerField(
        "Длительность (секунды)", null=True, blank=True
    )
    file_size = models.BigIntegerField("Размер файла (байты)", null=True, blank=True)

    # Ссылки
    video_url = models.URLField("Ссылка на видео", blank=True)
    m3u8_url = models.URLField("M3U8 плейлист", blank=True)
    mpd_content = models.TextField("MPD контент", blank=True)
    download_url = models.URLField("Ссылка для скачивания", blank=True)

    # Статус
    is_available = models.BooleanField("Доступно", default=True)
    is_active = models.BooleanField("Активно", default=True)
    last_checked = models.DateTimeField("Последняя проверка", null=True, blank=True)

    # Метаданные
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Источник видео"
        verbose_name_plural = "Источники видео"
        unique_together = ["anime", "source", "quality"]

    def __str__(self):
        return f"{self.anime.title_ru} - {self.get_source_display()} - {self.get_quality_display()}"


class Episode(models.Model):
    """Эпизод аниме"""

    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="anime_episodes"
    )
    video_source = models.ForeignKey(
        VideoSource,
        on_delete=models.CASCADE,
        related_name="episodes",
        null=True,
        blank=True,
    )

    # Номер и информация
    number = models.PositiveIntegerField("Номер эпизода")
    title = models.CharField("Название", max_length=255, blank=True)
    title_en = models.CharField("Название (англ.)", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)

    # Длительность
    duration = models.PositiveIntegerField(
        "Длительность (секунды)", null=True, blank=True
    )

    # Даты
    air_date = models.DateField("Дата выхода", null=True, blank=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "Эпизод"
        verbose_name_plural = "Эпизоды"
        unique_together = ["anime", "number"]

    def __str__(self):
        return f"{self.anime.title_ru} - Эпизод {self.number}"


class Translation(models.Model):
    """Перевод/озвучка для аниме"""

    TRANSLATION_TYPE_CHOICES = [
        ("voice", "Озвучка"),
        ("subtitles", "Субтитры"),
        ("dubbing", "Дубляж"),
    ]

    STATUS_CHOICES = [
        ("active", "Активный"),
        ("inactive", "Неактивный"),
        ("processing", "В обработке"),
        ("error", "Ошибка"),
    ]

    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="anime_translations"
    )
    video_source = models.ForeignKey(
        VideoSource,
        on_delete=models.CASCADE,
        related_name="translations",
        null=True,
        blank=True,
    )

    # Основная информация
    name = models.CharField("Название перевода", max_length=255)
    translation_type = models.CharField(
        "Тип перевода", max_length=20, choices=TRANSLATION_TYPE_CHOICES, default="voice"
    )
    studio_name = models.CharField("Студия", max_length=255, blank=True)
    external_id = models.CharField("Внешний ID", max_length=100, blank=True)

    # Статус
    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="active"
    )
    is_complete = models.BooleanField("Завершен", default=False)
    episodes_count = models.PositiveIntegerField("Количество эпизодов", default=0)

    # Метаданные
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Перевод"
        verbose_name_plural = "Переводы"
        unique_together = ["anime", "name"]

    def __str__(self):
        return f"{self.anime.title_ru} - {self.name}"


class WatchProgress(models.Model):
    """Прогресс просмотра пользователя"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="watch_progress"
    )
    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="user_progress"
    )
    episode = models.ForeignKey(
        Episode, on_delete=models.CASCADE, related_name="user_progress"
    )
    translation = models.ForeignKey(
        Translation,
        on_delete=models.CASCADE,
        related_name="user_progress",
        null=True,
        blank=True,
    )

    # Прогресс
    current_time = models.PositiveIntegerField("Текущее время (секунды)", default=0)
    duration = models.PositiveIntegerField(
        "Длительность (секунды)", null=True, blank=True
    )
    is_completed = models.BooleanField("Завершено", default=False)
    watch_count = models.PositiveIntegerField("Количество просмотров", default=1)

    # Метаданные
    last_watched = models.DateTimeField("Последний просмотр", auto_now=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["-last_watched"]
        verbose_name = "Прогресс просмотра"
        verbose_name_plural = "Прогрессы просмотра"
        unique_together = ["user", "episode"]

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru} - Эпизод {self.episode.number}"


class VideoQuality(models.Model):
    """Доступные качества видео"""

    video_source = models.ForeignKey(
        VideoSource, on_delete=models.CASCADE, related_name="qualities"
    )
    quality = models.CharField("Качество", max_length=10)
    resolution = models.CharField("Разрешение", max_length=20, blank=True)
    bitrate = models.PositiveIntegerField("Битрейт", null=True, blank=True)
    file_size = models.BigIntegerField("Размер файла", null=True, blank=True)

    # Ссылки
    video_url = models.URLField("Ссылка на видео", blank=True)
    m3u8_url = models.URLField("M3U8 плейлист", blank=True)

    is_available = models.BooleanField("Доступно", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["-quality"]
        verbose_name = "Качество видео"
        verbose_name_plural = "Качества видео"
        unique_together = ["video_source", "quality"]

    def __str__(self):
        return f"{self.video_source.anime.title_ru} - {self.quality}"


class AnimeUpdate(models.Model):
    """Отслеживание обновлений аниме"""

    UPDATE_TYPE_CHOICES = [
        ("new_episode", "Новый эпизод"),
        ("new_translation", "Новый перевод"),
        ("quality_update", "Обновление качества"),
        ("status_change", "Изменение статуса"),
        ("info_update", "Обновление информации"),
    ]

    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="updates")
    update_type = models.CharField(
        "Тип обновления", max_length=20, choices=UPDATE_TYPE_CHOICES
    )
    description = models.TextField("Описание")
    episode_number = models.PositiveIntegerField("Номер эпизода", null=True, blank=True)

    is_notified = models.BooleanField("Уведомлено", default=False)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обновление аниме"
        verbose_name_plural = "Обновления аниме"

    def __str__(self):
        return f"{self.anime.title_ru} - {self.get_update_type_display()}"


class UserEpisodeProgress(models.Model):
    """Прогресс просмотра по каждой серии — основа системы отметок"""

    STATUS_CHOICES = [
        ("not_started", "Не начато"),
        ("in_progress", "В процессе"),
        ("watched", "Просмотрено"),
        ("skipped", "Пропущено"),
    ]

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="episode_progress"
    )
    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="episode_progress"
    )
    episode_number = models.PositiveIntegerField("Номер серии")

    status = models.CharField(
        "Статус", max_length=20, choices=STATUS_CHOICES, default="not_started"
    )
    last_position = models.PositiveIntegerField("Позиция (сек)", default=0)
    duration = models.PositiveIntegerField("Длительность (сек)", null=True, blank=True)
    is_manually_marked = models.BooleanField("Ручная отметка", default=False)

    watched_at = models.DateTimeField("Дата просмотра", null=True, blank=True)
    last_watched = models.DateTimeField("Последнее обновление", auto_now=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        unique_together = ["user", "anime", "episode_number"]
        ordering = ["episode_number"]
        verbose_name = "Прогресс серии"
        verbose_name_plural = "Прогресс серий"

    def __str__(self):
        return f"{self.user.username} | {self.anime.title_ru} ep{self.episode_number} — {self.status}"

    @property
    def progress_percent(self):
        if self.duration and self.duration > 0:
            return round(self.last_position / self.duration * 100, 1)
        return 0


class UserActiveTab(models.Model):
    """
    Отслеживание активных вкладок пользователя на страницах аниме.
    Используется для раздела "Сейчас смотрят" — показывает аниме,
    которые пользователи открыли в данный момент (даже без воспроизведения).
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="active_tabs"
    )
    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="active_viewers"
    )

    # Тип активности: 'watching' (открыта страница аниме), 'player' (воспроизведение идёт)
    activity_type = models.CharField(
        "Тип активности",
        max_length=20,
        choices=[
            ("watching", "Просмотр страницы"),
            ("player", "Воспроизведение"),
        ],
        default="watching",
    )

    # Текущая серия (если известно)
    current_episode = models.PositiveIntegerField(
        "Текущая серия", null=True, blank=True
    )

    # Последняя активность
    last_ping = models.DateTimeField("Последний пинг", auto_now=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        unique_together = ["user", "anime"]
        ordering = ["-last_ping"]
        verbose_name = "Активная вкладка"
        verbose_name_plural = "Активные вкладки"

    def __str__(self):
        return f"{self.user.username} | {self.anime.title_ru} ({self.activity_type})"


class CustomDub(models.Model):
    """Пользовательская озвучка аниме"""

    MODERATION_STATUS_CHOICES = [
        ("pending", "На модерации"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    ]

    QUALITY_CHOICES = [
        ("360p", "360p"),
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("4K", "4K"),
    ]

    anime = models.ForeignKey(
        Anime, on_delete=models.CASCADE, related_name="custom_dubs"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_dubs"
    )

    # Основная информация
    name = models.CharField("Название озвучки", max_length=255)
    studio = models.CharField("Студия", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)

    # Техническая информация
    quality = models.CharField(
        "Качество", max_length=10, choices=QUALITY_CHOICES, default="720p"
    )
    video_url = models.URLField("Ссылка на видео")
    logo_url = models.URLField("URL логотипа", blank=True)

    # Прогресс
    episodes_done = models.PositiveIntegerField("Озвучено серий", default=0)
    total_episodes = models.PositiveIntegerField("Всего серий", null=True, blank=True)
    is_complete = models.BooleanField("Завершено", default=False)

    # Модерация
    status = models.CharField(
        "Статус модерации",
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default="pending",
    )
    moderation_comment = models.TextField("Комментарий модератора", blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_dubs",
    )
    moderated_at = models.DateTimeField("Дата модерации", null=True, blank=True)

    # Статистика
    views_count = models.PositiveIntegerField("Просмотров", default=0)
    rating = models.FloatField("Рейтинг", default=0.0)
    ratings_count = models.PositiveIntegerField("Оценок", default=0)

    # Метаданные
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Пользовательская озвучка"
        verbose_name_plural = "Пользовательские озвучки"
        unique_together = ["anime", "created_by", "name"]

    def __str__(self):
        return f"{self.anime.title_ru} - {self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
