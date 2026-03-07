from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnimeViewSet, GenresViewSet, FranchiseViewSet, proxy_video,
    SearchAPIView, ParserStatusAPIView, UpdatesAPIView,
    KodikImportView, KodikFiltersView, KodikTranslationsView,
    CustomDubListView, CustomDubDetailView, HomeAPIView,
    RandomAnimeView, CurrentlyWatchingView,
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
]