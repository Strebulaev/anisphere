"""
Сериализаторы для рулетки аниме
"""
from rest_framework import serializers
from .models import (
    AnimeRoulette,
    AnimeRouletteItem,
    RouletteSpinHistory,
    RoulettePreset,
    RouletteStatistics
)


class AnimeRouletteItemSerializer(serializers.ModelSerializer):
    """Сериализатор элемента рулетки"""
    class Meta:
        model = AnimeRouletteItem
        fields = [
            'id', 'anime_id', 'anime_title', 'anime_poster',
            'weight', 'color', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnimeRouletteItemCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания элемента рулетки"""
    class Meta:
        model = AnimeRouletteItem
        fields = ['anime_id', 'anime_title', 'anime_poster', 'weight', 'color']


class AnimeRouletteSerializer(serializers.ModelSerializer):
    """Сериализатор рулетки"""
    items = AnimeRouletteItemSerializer(many=True, read_only=True)
    total_weight = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()
    wheel_size_px = serializers.ReadOnlyField()
    
    class Meta:
        model = AnimeRoulette
        fields = [
            'id', 'name', 'spin_duration', 'items',
            'total_weight', 'items_count', 'wheel_size_px',
            # Настройки внешнего вида
            'theme', 'wheel_size', 'display_mode', 'color_scheme',
            'animation_style', 'sound_enabled', 'sound_type',
            # Настройки поведения
            'default_spin_count', 'weight_mode', 'exclude_recent',
            'exclusion_period',
            # Лимиты
            'max_items', 'max_spin_items', 'history_limit',
            # Автоматическое добавление
            'auto_add_from_collection', 'auto_add_from_playlists',
            # Результаты
            'last_result', 'last_spin_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'last_result', 'last_spin_at', 'created_at', 'updated_at']


class AnimeRouletteCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рулетки"""
    class Meta:
        model = AnimeRoulette
        fields = ['name', 'spin_duration']


class AnimeRouletteSettingsSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления настроек рулетки"""
    class Meta:
        model = AnimeRoulette
        fields = [
            'name', 'spin_duration',
            # Настройки внешнего вида
            'theme', 'wheel_size', 'display_mode', 'color_scheme',
            'animation_style', 'sound_enabled', 'sound_type',
            # Настройки поведения
            'default_spin_count', 'weight_mode', 'exclude_recent',
            'exclusion_period',
            # Лимиты
            'max_items', 'max_spin_items', 'history_limit',
            # Автоматическое добавление
            'auto_add_from_collection', 'auto_add_from_playlists',
        ]


class BulkAddAnimeSerializer(serializers.Serializer):
    """Сериализатор для массового добавления аниме"""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text='Список аниме для добавления. Формат: [{"anime_id": 1, "weight": 2}, ...]'
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Список не может быть пустым')

        for item in value:
            if 'anime_id' not in item:
                raise serializers.ValidationError('Каждый элемент должен содержать anime_id')
            if 'weight' in item and item['weight'] < 1:
                raise serializers.ValidationError('Вес должен быть >= 1')

        return value


class SpinResultSerializer(serializers.ModelSerializer):
    """Сериализатор результата крутки"""
    winner = AnimeRouletteItemSerializer(read_only=True)
    winners = AnimeRouletteItemSerializer(many=True, read_only=True)

    class Meta:
        model = RouletteSpinHistory
        fields = [
            'id', 'winner', 'winners', 'spin_type', 'rotation_angle',
            'spin_duration', 'items_count', 'is_favorite', 'notes',
            'created_at'
        ]


class SpinRequestSerializer(serializers.Serializer):
    """Сериализатор запроса на крутку"""
    roulette_id = serializers.UUIDField()
    count = serializers.IntegerField(
        default=1,
        min_value=1,
        max_value=50,
        help_text='Количество аниме для выбора'
    )
    spin_type = serializers.ChoiceField(
        choices=RouletteSpinHistory.SpinType.choices,
        default=RouletteSpinHistory.SpinType.SINGLE,
        help_text='Тип крутки: single, multiple, marathon'
    )


class RoulettePresetSerializer(serializers.ModelSerializer):
    """Сериализатор пресета рулетки"""
    class Meta:
        model = RoulettePreset
        fields = [
            'id', 'name', 'description', 'items_data', 'settings_snapshot',
            'items_count', 'times_used', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'times_used', 'created_at', 'updated_at']


class RoulettePresetCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пресета"""
    class Meta:
        model = RoulettePreset
        fields = ['name', 'description', 'items_data', 'settings_snapshot', 'is_public']


class RouletteStatisticsSerializer(serializers.ModelSerializer):
    """Сериализатор статистики рулетки"""
    most_spun_anime = AnimeRouletteItemSerializer(read_only=True)
    least_spun_anime = AnimeRouletteItemSerializer(read_only=True)

    class Meta:
        model = RouletteStatistics
        fields = [
            'total_spins', 'single_spins', 'multiple_spins', 'marathon_spins',
            'most_spun_anime_id', 'most_spun_count',
            'least_spun_anime_id', 'least_spun_count',
            'unique_anime_spun',
            'last_7_days_spins', 'last_30_days_spins',
            'created_at', 'updated_at'
        ]


class AddFromCollectionSerializer(serializers.Serializer):
    """Сериализатор для добавления из коллекции"""
    collection_status = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='Фильтр по статусу: watching, completed, planned, dropped, on_hold'
    )
    min_score = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        help_text='Минимальный рейтинг аниме'
    )
    weight_by_score = serializers.BooleanField(
        default=False,
        help_text='Устанавливать вес пропорционально рейтингу'
    )


class AddFromPlaylistSerializer(serializers.Serializer):
    """Сериализатор для добавления из плейлиста"""
    playlist_id = serializers.UUIDField(help_text='ID плейлиста')
    weight_equal = serializers.BooleanField(
        default=True,
        help_text='Установить одинаковый вес для всех'
    )


class MarathonResultSerializer(serializers.Serializer):
    """Сериализатор результата марафона"""
    spin_id = serializers.UUIDField()
    selected_anime = AnimeRouletteItemSerializer(many=True)
    total_duration = serializers.IntegerField(
        help_text='Общая длительность всех эпизодов (минуты)'
    )
    created_at = serializers.DateTimeField()
