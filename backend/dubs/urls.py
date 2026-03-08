from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'groups', views.DubGroupViewSet, basename='dub-group')
router.register(r'dubs', views.DubViewSet, basename='dub')
router.register(r'actors', views.VoiceActorViewSet, basename='voice-actor')
router.register(r'people', views.PersonViewSet, basename='person')

urlpatterns = [
    path('', include(router.urls)),
    path('anime/<int:anime_id>/dubs/', views.anime_dubs, name='anime-dubs'),
    path('anime/<int:anime_id>/groups/', views.anime_dub_groups, name='anime-dub-groups'),
    path('dubs/<int:dub_id>/', views.dub_detail, name='dub-detail'),
    path('groups/popular/', views.popular_dub_groups, name='popular-dub-groups'),
]