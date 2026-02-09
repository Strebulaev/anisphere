from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnimeViewSet, GenresViewSet, proxy_video, 
    SearchAPIView, ParserStatusAPIView, UpdatesAPIView
)

router = DefaultRouter()
router.register(r'anime', AnimeViewSet, basename='anime')
router.register(r'genres', GenresViewSet, basename='genres')

urlpatterns = [
    path('', include(router.urls)),
    
    # Новые API endpoints для anime-parsers-ru
    path('search/', SearchAPIView.as_view(), name='anime-search'),
    path('parser/status/', ParserStatusAPIView.as_view(), name='parser-status'),
    path('updates/', UpdatesAPIView.as_view(), name='anime-updates'),
    
    # Явно добавьте маршрут для get_video_link
    path('anime/<int:pk>/get_video_link/', 
         AnimeViewSet.as_view({'get': 'get_video_link'}), 
         name='anime-get-video-link'),
    path('proxy/video/', proxy_video, name='proxy-video'),
]