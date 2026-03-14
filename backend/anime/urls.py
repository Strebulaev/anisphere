from django.urls import path, include
from rest_framework.routers import DefaultRouter

from anime.services import kodik_proxy


from .views import (
    AnimeViewSet, GenresViewSet, FranchiseViewSet, proxy_video,
    SearchAPIView, ParserStatusAPIView, UpdatesAPIView,
    KodikImportView, KodikFiltersView, KodikTranslationsView,
    CustomDubListView, CustomDubDetailView, HomeAPIView,
    RandomAnimeView, CurrentlyWatchingView, UserActiveTabView,
    EpisodeProgressView, EpisodeProgressUndoView,
    AnimeThemesView, KodikVideoUrlView, KodikClipDownloadView,
)

router = DefaultRouter()
router.register(r'franchises', FranchiseViewSet, basename='franchise')
router.register(r'genres', GenresViewSet, basename='genres')
router.register(r'', AnimeViewSet, basename='anime')

urlpatterns = [
    # Новые API endpoints для anime-parsers-ru (должны идти до router.urls)
    path('search/', SearchAPIView.as_view(), name='anime-search'),
    path('parser/status/', ParserStatusAPIView.as_view(), name='parser-status'),
    path('updates/', UpdatesAPIView.as_view(), name='anime-updates'),
    path('home/', HomeAPIView.as_view(), name='anime-home'),
    path('random/', RandomAnimeView.as_view(), name='anime-random'),
    path('currently-watching/', CurrentlyWatchingView.as_view(), name='anime-currently-watching'),
    path('active-tab/', UserActiveTabView.as_view(), name='anime-active-tab'),

    # Episode Progress System
    path('<int:anime_id>/episode-progress/', EpisodeProgressView.as_view(), name='episode-progress'),
    path('<int:anime_id>/episode-progress/<int:episode_number>/undo/', EpisodeProgressUndoView.as_view(), name='episode-progress-undo'),

    path('', include(router.urls)),
    
    # Kodik API endpoints
    path('import-from-kodik/', KodikImportView.as_view(), name='import-from-kodik'),
    path('kodik-filters/', KodikFiltersView.as_view(), name='kodik-filters'),
    path('<int:pk>/kodik_translations/', KodikTranslationsView.as_view(), name='kodik-translations'),
    
    # Custom dubs endpoints
    path('<int:anime_id>/custom_dubs/', CustomDubListView.as_view(), name='custom-dubs-list'),
    path('<int:anime_id>/custom_dubs/<int:dub_id>/', CustomDubDetailView.as_view(), name='custom-dub-detail'),
    
    # Proxy endpoint
    path('proxy/video/', proxy_video, name='proxy-video'),

    # Theme times (opening/ending) from Shikimori
    path('<int:pk>/themes/', AnimeThemesView.as_view(), name='anime-themes'),

    # Direct Kodik video URL (m3u8) for downloading
    path('<int:pk>/kodik_video_url/', KodikVideoUrlView.as_view(), name='kodik-video-url'),
    path('<int:pk>/clip/', KodikClipDownloadView.as_view(), name='kodik-clip-download'),
]

# kodik_proxy маршруты (без 'api/' префикса — он добавляется в корневом urls.py)
urlpatterns += [
    path('kodik/studios/', kodik_proxy.kodik_studios, name='kodik-studios'),
    path('kodik/proxy/', kodik_proxy.kodik_proxy, name='kodik-proxy'),
]