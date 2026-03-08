from rest_framework import serializers
from .models import DubGroup, Dub, VoiceActor, DubRole, DubLink, Person

class DubGroupSerializer(serializers.ModelSerializer):
    """Сериализатор группы озвучки"""
    
    class Meta:
        model = DubGroup
        fields = [
            'id', 'name', 'slug', 'description',
            'website', 'vk_url', 'telegram_url', 'discord_url',
            'logo_url', 'works_count', 'followers_count',
            'status', 'is_verified', 'created_at'
        ]


class VoiceActorSerializer(serializers.ModelSerializer):
    """Сериализатор актёра озвучки"""
    
    groups = DubGroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = VoiceActor
        fields = [
            'id', 'name', 'slug', 'description',
            'photo_url', 'groups', 'roles_count',
            'created_at'
        ]


class DubLinkSerializer(serializers.ModelSerializer):
    """Сериализатор ссылки на озвучку"""
    
    class Meta:
        model = DubLink
        fields = ['id', 'source', 'url', 'episode', 'quality', 'is_active']


class DubRoleSerializer(serializers.ModelSerializer):
    """Сериализатор роли актёра"""
    
    actor = VoiceActorSerializer(read_only=True)
    
    class Meta:
        model = DubRole
        fields = ['id', 'actor', 'character_name', 'character_name_en', 'is_main']


class DubSerializer(serializers.ModelSerializer):
    """Сериализатор озвучки"""
    
    group = DubGroupSerializer(read_only=True)
    roles = DubRoleSerializer(many=True, read_only=True)
    links = DubLinkSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dub
        fields = [
            'id', 'group', 'dub_type', 'quality',
            'episodes_done', 'total_episodes', 'is_complete', 'is_abandoned',
            'external_url', 'average_rating', 'ratings_count',
            'started_at', 'finished_at', 'last_episode_at',
            'roles', 'links', 'created_at'
        ]


class AnimeDubSerializer(serializers.ModelSerializer):
    """Сериализатор озвучки для аниме (сокращённый)"""

    group = serializers.SerializerMethodField()
    dub_type_display = serializers.CharField(source='get_dub_type_display', read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Dub
        fields = [
            'id', 'group', 'dub_type', 'dub_type_display', 'quality',
            'episodes_done', 'total_episodes', 'is_complete',
            'average_rating', 'ratings_count', 'external_url', 'created_by'
        ]

    def get_group(self, obj):
        return {
            'id': obj.group.id,
            'name': obj.group.name,
            'slug': obj.group.slug,
            'logo_url': obj.group.logo_url
        }

    def get_created_by(self, obj):
        try:
            if hasattr(obj, 'created_by') and obj.created_by:
                return {
                    'id': obj.created_by.id,
                    'username': obj.created_by.username
                }
        except:
            pass
        return None


class UpdateDubSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления озвучки"""

    group_name = serializers.CharField(write_only=True, max_length=200, required=False)
    group_links = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Dub
        fields = [
            'group_name', 'group_links',
            'dub_type', 'external_url', 'episodes_done', 'total_episodes'
        ]

    def update(self, instance, validated_data):
        group_name = validated_data.pop('group_name', None)
        group_links = validated_data.pop('group_links', [])

        # Обновляем группу если указано новое имя
        if group_name and group_name != instance.group.name:
            from .models import DubGroup

            # Распределяем ссылки по доступным полям
            links_data = {}
            link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
            for i, url in enumerate(group_links[:4]):
                if url.strip():
                    links_data[link_fields[i]] = url.strip()

            # Ищем существующую группу или создаём новую
            group, created = DubGroup.objects.get_or_create(
                name__iexact=group_name,
                defaults={
                    'name': group_name,
                    'status': 'active',
                    **links_data
                }
            )

            # Если группа уже существовала, обновляем ссылки
            if not created:
                for key, value in links_data.items():
                    if value:
                        setattr(group, key, value)
                group.save()

            # Проверяем, что такая озвучка уже не существует для другой группы
            if Dub.objects.filter(anime=instance.anime, group=group).exclude(id=instance.id).exists():
                raise serializers.ValidationError("Озвучка этой группы для данного аниме уже существует.")

            instance.group = group
        elif group_links:
            # Обновляем только ссылки группы
            links_data = {}
            link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
            for i, url in enumerate(group_links[:4]):
                if url.strip():
                    links_data[link_fields[i]] = url.strip()

            for key, value in links_data.items():
                if value:
                    setattr(instance.group, key, value)
            instance.group.save()

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CreateDubSerializer(serializers.ModelSerializer):
    """Сериализатор для создания озвучки"""

    group_name = serializers.CharField(write_only=True, max_length=200)
    group_links = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        default=list
    )

    class Meta:
        model = Dub
        fields = [
            'group_name', 'group_links',
            'dub_type', 'external_url', 'episodes_done', 'total_episodes'
        ]

    def validate_group_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Название группы озвучки обязательно.")
        return value.strip()

    def validate_group_links(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Ссылки должны быть списком.")

        for url in value:
            if not url.strip():
                raise serializers.ValidationError("URL ссылки не может быть пустым.")

        return value

    def create(self, validated_data):
        anime = self.context['anime']
        group_name = validated_data.pop('group_name')
        group_links = validated_data.pop('group_links', [])

        from .models import DubGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Получаем пользователя из контекста (если есть)
        user = self.context.get('user')
        if user and not user.is_authenticated:
            user = None

        # Распределяем ссылки по доступным полям
        links_data = {}
        link_fields = ['website', 'vk_url', 'telegram_url', 'discord_url']
        for i, url in enumerate(group_links[:4]):  # Максимум 4 ссылки
            if url.strip():
                links_data[link_fields[i]] = url.strip()

        # Ищем существующую группу или создаём новую
        group, created = DubGroup.objects.get_or_create(
            name__iexact=group_name,
            defaults={
                'name': group_name,
                'status': 'active',
                **links_data
            }
        )

        # Если группа уже существовала, обновляем ссылки если они предоставлены
        if not created:
            for key, value in links_data.items():
                if value:
                    setattr(group, key, value)
            group.save()

        # Проверяем, что такая озвучка уже не существует
        if Dub.objects.filter(anime=anime, group=group).exists():
            raise serializers.ValidationError("Озвучка этой группы для данного аниме уже существует.")

        # Создаём озвучку с created_by только если пользователь аутентифицирован
        dub_data = {'anime': anime, 'group': group, **validated_data}
        if user and user.is_authenticated:
            dub_data['created_by'] = user
        dub = Dub.objects.create(**dub_data)
        return dub


class PersonSerializer(serializers.ModelSerializer):
    """Сериализатор персоны"""
    
    roles_display = serializers.SerializerMethodField()
    anime_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Person
        fields = [
            'id', 'name', 'name_jp', 'slug', 'description',
            'photo_url', 'birth_date', 'roles', 'roles_display',
            'works_count', 'anime_count', 'created_at'
        ]
    
    def get_roles_display(self, obj):
        return [dict(Person.ROLE_CHOICES).get(r, r) for r in obj.roles]
    
    def get_anime_count(self, obj):
        return obj.works_count


class PersonDetailSerializer(PersonSerializer):
    """Детальный сериализатор персоны"""
    
    related_anime = serializers.SerializerMethodField()
    
    class Meta(PersonSerializer.Meta):
        fields = PersonSerializer.Meta.fields + ['related_anime']
    
    def get_related_anime(self, obj):
        from anime.serializers import AnimeSerializer
        anime_list = obj.related_anime.all()[:10]
        return AnimeSerializer(anime_list, many=True).data