from django.contrib import admin
from .models import (
    Genre, Studio, Anime, Playlist, PlaylistItem, VoiceActor, DubStudio,
    Dub, DubRole, UserDubRating, VideoSource, Episode, Translation,
    WatchProgress, VideoQuality, AnimeUpdate
)

class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 0
    readonly_fields = ('added_at',)
    fields = ('anime', 'position', 'added_at')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title_ru', 'title_en', 'title_jp', 'year', 'status', 'kind', 'episodes', 'score', 'data_source', 'created_at')
    search_fields = ('title_ru', 'title_en', 'title_jp', 'description')
    list_filter = ('status', 'kind', 'year', 'data_source', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'movie_count', 'ova_count', 'total_items', 'last_season', 'last_episode')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title_ru', 'title_en', 'title_jp', 'description', 'year')
        }),
        ('Статус и тип', {
            'fields': ('status', 'kind', 'episodes', 'score')
        }),
        ('Постер', {
            'fields': ('poster_url', 'poster')
        }),
        ('Жанры и студии', {
            'fields': ('genres', 'studios')
        }),
        ('Связанные тайтлы', {
            'fields': ('movies', 'ovas')
        }),
        ('Счётчики', {
            'fields': ('movie_count', 'ova_count', 'total_items')
        }),
        ('Kodik', {
            'fields': ('kodik_link', 'kodik_id', 'quality', 'screenshots')
        }),
        ('Сезоны', {
            'fields': ('seasons', 'last_season', 'last_episode')
        }),
        ('Переводы', {
            'fields': ('translations',)
        }),
        ('Источник данных', {
            'fields': ('data_source', 'shikimori_id')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'user__username')
    list_filter = ('is_public', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PlaylistItemInline]


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'anime', 'position', 'added_at')
    search_fields = ('playlist__name', 'anime__title_ru', 'anime__title_en')
    list_filter = ('added_at',)
    readonly_fields = ('added_at',)
    raw_id_fields = ('playlist', 'anime')


@admin.register(VoiceActor)
class VoiceActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_original', 'slug', 'is_verified', 'rating', 'created_at')
    search_fields = ('name', 'name_original', 'slug', 'description')
    list_filter = ('is_verified', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'rating')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DubStudio)
class DubStudioAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_official', 'is_verified', 'status', 'rating', 'works_count', 'created_at')
    search_fields = ('name', 'slug', 'description', 'website_url')
    list_filter = ('is_official', 'is_verified', 'status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'rating', 'works_count')
    prepopulated_fields = {'slug': ('name',)}


class DubRoleInline(admin.TabularInline):
    model = DubRole
    extra = 0
    fields = ('actor', 'character_name', 'character_name_original', 'role_type', 'order')


@admin.register(Dub)
class DubAdmin(admin.ModelAdmin):
    list_display = ('anime', 'studio', 'title', 'quality', 'episodes_count', 'is_complete', 'is_ongoing', 'rating', 'votes_count', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'studio__name', 'title', 'description')
    list_filter = ('quality', 'is_complete', 'is_ongoing', 'is_approved', 'created_at', 'released_at', 'updated_at')
    readonly_fields = ('created_at', 'rating', 'votes_count')
    raw_id_fields = ('anime', 'studio')
    inlines = [DubRoleInline]


@admin.register(DubRole)
class DubRoleAdmin(admin.ModelAdmin):
    list_display = ('dub', 'actor', 'character_name', 'character_name_original', 'role_type', 'order')
    search_fields = ('dub__anime__title_ru', 'actor__name', 'character_name')
    list_filter = ('role_type',)
    raw_id_fields = ('dub', 'actor')


@admin.register(UserDubRating)
class UserDubRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'dub', 'rating', 'created_at')
    search_fields = ('user__username', 'dub__anime__title_ru', 'comment')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'dub')


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('number', 'title', 'title_en', 'air_date', 'created_at')


class TranslationInline(admin.TabularInline):
    model = Translation
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('name', 'translation_type', 'studio_name', 'status', 'is_complete', 'episodes_count', 'created_at')


class VideoQualityInline(admin.TabularInline):
    model = VideoQuality
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('quality', 'resolution', 'bitrate', 'file_size', 'is_available', 'created_at')


@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ('anime', 'source', 'external_id', 'quality', 'video_format', 'is_available', 'is_active', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'source', 'external_id', 'title')
    list_filter = ('source', 'quality', 'video_format', 'is_available', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'last_checked')
    raw_id_fields = ('anime',)
    inlines = [EpisodeInline, TranslationInline, VideoQualityInline]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('anime', 'number', 'title', 'title_en', 'air_date', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'title', 'title_en')
    list_filter = ('air_date', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('anime', 'video_source')


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ('anime', 'name', 'translation_type', 'studio_name', 'status', 'is_complete', 'episodes_count', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'name', 'studio_name')
    list_filter = ('translation_type', 'status', 'is_complete', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('anime', 'video_source')


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'anime', 'episode', 'translation', 'current_time', 'duration', 'is_completed', 'watch_count', 'last_watched')
    search_fields = ('user__username', 'anime__title_ru', 'anime__title_en')
    list_filter = ('is_completed', 'last_watched')
    readonly_fields = ('created_at', 'last_watched')
    raw_id_fields = ('user', 'anime', 'episode', 'translation')


@admin.register(VideoQuality)
class VideoQualityAdmin(admin.ModelAdmin):
    list_display = ('video_source', 'quality', 'resolution', 'bitrate', 'file_size', 'is_available', 'created_at')
    search_fields = ('video_source__anime__title_ru', 'quality', 'resolution')
    list_filter = ('quality', 'is_available', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('video_source',)


@admin.register(AnimeUpdate)
class AnimeUpdateAdmin(admin.ModelAdmin):
    list_display = ('anime', 'update_type', 'episode_number', 'is_notified', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'description')
    list_filter = ('update_type', 'is_notified', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('anime',)