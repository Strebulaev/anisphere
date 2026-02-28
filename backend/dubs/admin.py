from django.contrib import admin
from .models import DubGroup, VoiceActor, Dub, DubRole, DubReview, DubLink, UserDubPreference


class DubRoleInline(admin.TabularInline):
    model = DubRole
    extra = 0
    fields = ('actor', 'character_name', 'character_name_en', 'is_main')


class DubReviewInline(admin.TabularInline):
    model = DubReview
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('user', 'rating', 'text', 'pros', 'cons', 'created_at')


class DubLinkInline(admin.TabularInline):
    model = DubLink
    extra = 0
    readonly_fields = ('last_checked',)
    fields = ('source', 'url', 'episode', 'quality', 'is_active', 'last_checked')


@admin.register(DubGroup)
class DubGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'is_verified', 'rating', 'review_count', 'works_count', 'followers_count')
    search_fields = ('name', 'slug', 'description', 'website')
    list_filter = ('status', 'is_verified', 'verification_status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'works_count', 'followers_count', 'rating', 'review_count')


@admin.register(VoiceActor)
class VoiceActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'roles_count', 'created_at')
    search_fields = ('name', 'slug', 'description')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'roles_count')
    filter_horizontal = ('groups',)


@admin.register(Dub)
class DubAdmin(admin.ModelAdmin):
    list_display = ('anime', 'group', 'dub_type', 'quality', 'episodes_done', 'total_episodes', 'is_complete', 'average_rating', 'ratings_count', 'created_at')
    search_fields = ('anime__title_ru', 'anime__title_en', 'group__name')
    list_filter = ('dub_type', 'quality', 'is_complete', 'is_abandoned', 'is_approved', 'created_at', 'started_at', 'finished_at')
    readonly_fields = ('created_at', 'updated_at', 'average_rating', 'ratings_count')
    raw_id_fields = ('anime', 'group', 'created_by')
    inlines = [DubRoleInline, DubReviewInline, DubLinkInline]


@admin.register(DubRole)
class DubRoleAdmin(admin.ModelAdmin):
    list_display = ('dub', 'actor', 'character_name', 'character_name_en', 'is_main')
    search_fields = ('dub__anime__title_ru', 'actor__name', 'character_name')
    list_filter = ('is_main',)
    raw_id_fields = ('dub', 'actor')


@admin.register(DubReview)
class DubReviewAdmin(admin.ModelAdmin):
    list_display = ('dub', 'user', 'rating', 'created_at')
    search_fields = ('dub__anime__title_ru', 'user__username', 'text')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('dub', 'user')


@admin.register(DubLink)
class DubLinkAdmin(admin.ModelAdmin):
    list_display = ('dub', 'source', 'episode', 'quality', 'is_active', 'last_checked')
    search_fields = ('dub__anime__title_ru', 'source', 'url')
    list_filter = ('source', 'quality', 'is_active', 'last_checked')
    readonly_fields = ('last_checked',)
    raw_id_fields = ('dub',)


@admin.register(UserDubPreference)
class UserDubPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'rating', 'is_favorite')
    search_fields = ('user__username', 'group__name')
    list_filter = ('rating', 'is_favorite')
    raw_id_fields = ('user', 'group')