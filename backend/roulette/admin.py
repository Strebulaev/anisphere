from django.contrib import admin
from .models import AnimeRoulette, AnimeRouletteItem, RouletteSpinHistory


class AnimeRouletteItemInline(admin.TabularInline):
    model = AnimeRouletteItem
    extra = 0
    fields = ['anime_id', 'anime_title', 'weight', 'color', 'order']


@admin.register(AnimeRoulette)
class AnimeRouletteAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'items_count', 'total_weight', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username']
    inlines = [AnimeRouletteItemInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AnimeRouletteItem)
class AnimeRouletteItemAdmin(admin.ModelAdmin):
    list_display = ['anime_title', 'roulette', 'weight', 'color', 'order']
    list_filter = ['roulette', 'weight']
    search_fields = ['anime_title', 'anime_id']


@admin.register(RouletteSpinHistory)
class RouletteSpinHistoryAdmin(admin.ModelAdmin):
    list_display = ['roulette', 'winner', 'rotation_angle', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['roulette', 'winner', 'rotation_angle', 'spin_duration', 'created_at']
