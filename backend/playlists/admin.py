from django.contrib import admin
from .models import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist

class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 0
    readonly_fields = ['created_at']
    fields = ['anime', 'position', 'notes']

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_public', 'items_count', 'favorites_count', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'items_count', 'favorites_count', 'updated_at']
    inlines = [PlaylistItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Количество элементов'

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'В избранном'

@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ['playlist', 'anime', 'position', 'created_at']
    list_filter = ['created_at']
    search_fields = ['playlist__title', 'anime__title_ru', 'anime__title_en']
    readonly_fields = ['created_at', 'added_at']
    raw_id_fields = ['playlist', 'anime']

@admin.register(FavoriteAnime)
class FavoriteAnimeAdmin(admin.ModelAdmin):
    list_display = ['user', 'anime', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'anime__title_ru', 'anime__title_en']
    raw_id_fields = ['user', 'anime']

@admin.register(FavoritePlaylist)
class FavoritePlaylistAdmin(admin.ModelAdmin):
    list_display = ['user', 'playlist', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'playlist__title']
    raw_id_fields = ['user', 'playlist']