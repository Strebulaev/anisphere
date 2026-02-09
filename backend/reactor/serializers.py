from rest_framework import serializers
from .models import ReactorPost, ReactorLike, ReactorComment


class ReactorPostSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    thumbnail_url = serializers.ReadOnlyField()
    video_url = serializers.ReadOnlyField()

    class Meta:
        model = ReactorPost
        fields = [
            'id', 'user', 'user_username', 'user_avatar', 'title', 'description',
            'video_file', 'thumbnail_file', 'video_url', 'thumbnail_url', 'duration',
            'anime_tags', 'views_count', 'likes_count', 'comments_count', 'shares_count',
            'created_at', 'published_at'
        ]
        read_only_fields = ['id', 'user', 'views_count', 'likes_count', 'comments_count', 'shares_count', 'created_at', 'published_at']


class ReactorLikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ReactorLike
        fields = ['id', 'user', 'user_username', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReactorCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ReactorComment
        fields = [
            'id', 'user', 'user_username', 'user_avatar', 'post', 'text', 'parent',
            'replies', 'created_at', 'updated_at', 'is_reply'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_reply']

    def get_replies(self, obj):
        if obj.replies.exists():
            return ReactorCommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []


class ReactorCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReactorComment
        fields = ['post', 'text', 'parent']