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
    
    # === НОВЫЕ МАРШРУТЫ ДЛЯ DUBGROUP (ПОЛНЫЙ ФУНКЦИОНАЛ) ===
    # Работы (озвученные аниме)
    path('groups/<str:slug>/works/', views.DubGroupWorksView.as_view(), name='dub-group-works'),
    # Команда (актёры)
    path('groups/<str:slug>/staff/', views.DubGroupStaffView.as_view(), name='dub-group-staff'),
    # Новости
    path('groups/<str:slug>/news/', views.DubGroupNewsView.as_view(), name='dub-group-news'),
    # Обсуждения
    path('groups/<str:slug>/discussions/', views.DubGroupDiscussionsView.as_view(), name='dub-group-discussions'),
    path('groups/<str:slug>/discussions/create/', views.DubGroupDiscussionCreateView.as_view(), name='dub-group-discussion-create'),
    # Ответы на обсуждения
    path('groups/<str:slug>/discussions/<int:discussion_id>/replies/', views.DubGroupDiscussionRepliesView.as_view(), name='dub-group-discussion-replies'),
    path('groups/<str:slug>/discussions/<int:discussion_id>/like/', views.DubGroupDiscussionLikeView.as_view(), name='dub-group-discussion-like'),
    path('groups/<str:slug>/discussions/<int:discussion_id>/dislike/', views.DubGroupDiscussionDislikeView.as_view(), name='dub-group-discussion-dislike'),
    # Отзывы
    path('groups/<str:slug>/reviews/', views.DubGroupReviewsView.as_view(), name='dub-group-reviews'),
    path('groups/<str:slug>/reviews/create/', views.DubGroupReviewCreateView.as_view(), name='dub-group-review-create'),
    # Подписка
    path('groups/<str:slug>/subscribe/', views.DubGroupSubscribeView.as_view(), name='dub-group-subscribe'),
    # Похожие группы
    path('groups/<str:slug>/similar/', views.DubGroupSimilarView.as_view(), name='dub-group-similar'),
    
    # Kodik translation endpoints
    path('kodik/translation/<int:translation_id>/anime/', views.kodik_translation_anime, name='kodik-translation-anime'),
    path('kodik/translation/<int:translation_id>/', views.kodik_translation_detail, name='kodik-translation-detail'),
]