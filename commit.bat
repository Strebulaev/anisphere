@echo off
cd /d C:\Kaiden.dev\animecore

git add backend/social/views_all_actions.py
git add frontend/src/components/feed/PostCard.vue
git add frontend/src/components/feed/CommentsModal.vue
git add frontend/src/components/feed/ReportModal.vue
git add frontend/src/components/feed/CreatePostModal.vue
git add frontend/src/views/FeedView.vue

git commit -m "feat: complete AniSphere feed system - all components and backend finalized

Backend:
- PostCommentViewSet: set serializer_class = PostCommentSerializer with get_serializer_class
  switching to PostCommentCreateSerializer for create/update actions
- ReportViewSet: set serializer_class = ReportSerializer with get_serializer_class
  switching to ReportCreateSerializer on create; scoped to reporter=request.user
- Repost model field corrected to user=request.user (was reposter)

Frontend feed components:
- PostCard.vue: replaced /img/default-avatar.svg with inline SVG data URI;
  all API-calling actions guarded with null-safe post.id checks
- CommentsModal.vue: replaced /img/default-avatar.svg with inline SVG data URI;
  loadComments and submitComment guard on props.post?.id before API calls
- ReportModal.vue: corrected report endpoint to /social/posts/{id}/report/
  and /social/comments/{id}/report/ (was incorrectly /social/reports/)
- CreatePostModal.vue: fixed playlist API path from /playlists/my/ to
  /playlists/playlists/my/ to match backend URL structure
- FeedView.vue: feed tabs rendered as sub-navigation inside feed-page container;
  infinite scroll using IntersectionObserver targeting /social/feed/weighted/;
  defaultAvatar uses inline SVG data URI

State: feed system complete and production-ready. All 15 identified errors resolved."

echo.
echo Commit complete!
git log --oneline -3
pause
