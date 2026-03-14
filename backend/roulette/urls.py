"""
URL маршруты для рулетки аниме
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnimeRouletteViewSet,
    AnimeRouletteItemViewSet,
    RoulettePresetViewSet
)

router = DefaultRouter()
router.register(r'roulettes', AnimeRouletteViewSet, basename='roulette')
router.register(r'items', AnimeRouletteItemViewSet, basename='roulette-item')
router.register(r'presets', RoulettePresetViewSet, basename='roulette-preset')

urlpatterns = [
    path('', include(router.urls)),
]
