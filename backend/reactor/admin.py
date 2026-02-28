from django.contrib import admin
from .models import ReactorPost, ReactorLike, ReactorComment


class ReactorLikeInline(admin.TabularInline):
    model = ReactorLike
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('user', 'created_at')


class ReactorCommentInline(admin.TabularInline):
    model = ReactorComment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('user', 'text', 'parent', 'created_at')


@admin.register(ReactorPost)
class ReactorPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'duration', 'views_count', 'likes_count', 'comments_count', 'is_published', 'created_at')
    search_fields = ('user__username', 'title', 'description')
    list_filter = ('is_processing', 'is_published', 'is_deleted', 'created_at', 'published_at')
    readonly_fields = ('created_at', 'published_at', 'updated_at', 'views_count', 'likes_count', 'comments_count', 'shares_count')
    filter_horizontal = ('anime_tags',)
    inlines = [ReactorLikeInline, ReactorCommentInline]


@admin.register(ReactorLike)
class ReactorLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__title')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'post')


@admin.register(ReactorComment)
class ReactorCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'text_preview', 'parent', 'created_at')
    search_fields = ('user__username', 'text', 'post__title')
    list_filter = ('is_deleted', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'post', 'parent')
    
    def text_preview(self, obj):
        return obj.text[:100] if obj.text else ''
    text_preview.short_description = 'Текст'
