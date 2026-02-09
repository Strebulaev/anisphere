from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class FavoriteAnime(models.Model):
    """Избранные аниме пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_animes')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'anime']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru}"


class FavoritePlaylist(models.Model):
    """Избранные плейлисты пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_playlists')
    playlist = models.ForeignKey('Playlist', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'playlist']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.playlist.title}"


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    @property
    def favorites_count(self):
        return self.favorited_by.count()


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE)
    episode_number = models.IntegerField(null=True, blank=True)
    source_url = models.URLField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['playlist', 'anime']

    def __str__(self):
        return f"{self.playlist.title}: {self.anime.title_ru}"
