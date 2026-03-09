from django.contrib import admin
from .models import Studio, StudioAnime, StudioSubscription, StudioRating, StudioNews, StudioAward, StudioDiscussion, StudioStaff


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'founded_year', 'total_anime', 'average_rating', 'subscribers_count', 'is_active', 'is_verified']
    list_filter = ['country', 'is_active', 'is_verified']
    search_fields = ['name', 'name_jp']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'name_jp', 'slug', 'description', 'is_active', 'is_verified')
        }),
        ('Визуальные ресурсы', {
            'fields': ('logo', 'logo_url', 'banner', 'banner_url')
        }),
        ('Детали', {
            'fields': ('country', 'founded_year', 'employees_count', 'website', 'twitter', 'youtube', 'facebook')
        }),
        ('Статистика', {
            'fields': ('total_anime', 'tv_count', 'movie_count', 'ova_count', 'average_rating', 'subscribers_count', 'notable_works', 'genre_stats')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(StudioStaff)
class StudioStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'studio', 'role', 'is_key_person']
    list_filter = ['role', 'is_key_person', 'studio']
    search_fields = ['name', 'name_jp']


@admin.register(StudioNews)
class StudioNewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'studio', 'author', 'created_at']
    list_filter = ['studio']


@admin.register(StudioAward)
class StudioAwardAdmin(admin.ModelAdmin):
    list_display = ['studio', 'year', 'award_name', 'category', 'is_winner']
    list_filter = ['year', 'is_winner']


@admin.register(StudioRating)
class StudioRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'studio', 'overall_rating', 'created_at']
    list_filter = ['studio']


@admin.register(StudioDiscussion)
class StudioDiscussionAdmin(admin.ModelAdmin):
    list_display = ['title', 'studio', 'author', 'is_pinned', 'created_at']
    list_filter = ['studio', 'is_pinned']


admin.site.register(StudioAnime)
admin.site.register(StudioSubscription)
