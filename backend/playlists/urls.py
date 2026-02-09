from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlaylistViewSet, PlaylistItemViewSet,
    FavoriteAnimeViewSet, FavoritePlaylistViewSet,
    AddToPlaylistView
)

router = DefaultRouter()
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'playlist-items', PlaylistItemViewSet, basename='playlist-item')
router.register(r'favorites/anime', FavoriteAnimeViewSet, basename='favorite-anime')
router.register(r'favorites/playlists', FavoritePlaylistViewSet, basename='favorite-playlist')

urlpatterns = [
    path('', include(router.urls)),
    path('add-to-playlist/', AddToPlaylistView.as_view(), name='add-to-playlist'),
]