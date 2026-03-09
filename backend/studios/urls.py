from django.urls import path
from .views import (
    StudioListView, StudioPopularView, StudioDetailView, StudioDetailByIdView,
    StudioWorksView, StudioStaffView, StudioNewsView, StudioAwardsView,
    StudioDiscussionsView, StudioDiscussionCreateView,
    StudioDiscussionRepliesView, StudioDiscussionLikeView, StudioDiscussionDislikeView,
    StudioReviewsView, StudioReviewCreateView,
    StudioSubscribeView, StudioSimilarView, StudioSyncFromAnimeView,
)

urlpatterns = [
    # Списки
    path('', StudioListView.as_view(), name='studio-list'),
    path('popular/', StudioPopularView.as_view(), name='studio-popular'),
    path('sync/', StudioSyncFromAnimeView.as_view(), name='studio-sync'),

    # Детали студии
    path('<slug:slug>/', StudioDetailView.as_view(), name='studio-detail'),
    path('id/<int:pk>/', StudioDetailByIdView.as_view(), name='studio-detail-by-id'),

    # Подстраницы студии
    path('<slug:slug>/works/', StudioWorksView.as_view(), name='studio-works'),
    path('<slug:slug>/staff/', StudioStaffView.as_view(), name='studio-staff'),
    path('<slug:slug>/news/', StudioNewsView.as_view(), name='studio-news'),
    path('<slug:slug>/awards/', StudioAwardsView.as_view(), name='studio-awards'),
    path('<slug:slug>/discussions/', StudioDiscussionsView.as_view(), name='studio-discussions'),
    path('<slug:slug>/discussions/create/', StudioDiscussionCreateView.as_view(), name='studio-discussion-create'),
    path('<slug:slug>/discussions/<int:discussion_id>/replies/', StudioDiscussionRepliesView.as_view(), name='studio-discussion-replies'),
    path('<slug:slug>/discussions/<int:discussion_id>/like/', StudioDiscussionLikeView.as_view(), name='studio-discussion-like'),
    path('<slug:slug>/discussions/<int:discussion_id>/dislike/', StudioDiscussionDislikeView.as_view(), name='studio-discussion-dislike'),
    path('<slug:slug>/reviews/', StudioReviewsView.as_view(), name='studio-reviews'),
    path('<slug:slug>/reviews/create/', StudioReviewCreateView.as_view(), name='studio-review-create'),
    path('<slug:slug>/subscribe/', StudioSubscribeView.as_view(), name='studio-subscribe'),
    path('<slug:slug>/similar/', StudioSimilarView.as_view(), name='studio-similar'),
]
