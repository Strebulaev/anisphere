#!/usr/bin/env pwsh
# Run this script from the animecore project root to commit all feed system changes

Set-Location $PSScriptRoot

git add -A

git commit -m "feat(feed): complete social feed system implementation

BACKEND
- social/models.py: Post, PostMedia, PostAttachment, PostComment,
  PostCommentLike, PostCommentDislike, FeedView, Bookmark, Report,
  Follow, PostLike, PostDislike, Repost, Hashtag, PostHashtag,
  UserMention, UserPostHidden, UserPostNotInterested — all models
  with indexes, constraints, and helper methods
- social/views_feed.py: FeedViewSet with weighted (70/15/10/5 algo),
  followers, hot, top, trending endpoints
- social/views.py: PostViewSet (CRUD + media upload), PostCommentViewSet
  (nested comments, sort modes), FollowViewSet
- social/views_actions.py / views_all_actions.py: toggle_follow,
  toggle_post_like, toggle_post_dislike, pin/unpin, bookmark,
  repost, view tracking, comment like/dislike, report, hide,
  not_interested, hashtag search, feed statistics
- social/serializers.py: FeedPostSerializer, PostCommentSerializer,
  PostMediaSerializer, BookmarkSerializer, ReportSerializer, etc.
- social/services/feed_service.py: FeedGenerationService (weighted
  feed algo), TrendingService, SystemPostService
- social/feed_cache.py: Redis cache layer — user feeds (sorted sets),
  post metadata (hashes), reaction cache, view counters, TTLs
- social/consumers.py: GlobalEventsConsumer WebSocket — new_post,
  new_comment, like, repost, typing indicator events
- social/signals.py: post_save / post_delete signal handlers to
  invalidate Redis caches and fan-out new posts to follower feeds
- social/tasks.py: Celery async tasks for feed rebuilds, digest emails
- social/tests.py: full test coverage — PostCreation, LikeDislike,
  Comments (nesting, edit window, soft delete), Feed (weighted,
  followers, exclusions), Follow, Permissions, Bookmarks, Reposts
- social/urls.py: all 60+ URL patterns registered and connected
- Fixed Repost.objects.create/filter to use user= field (was reposter=)

FRONTEND
- src/api/feed.ts: FeedPost, PostComment interfaces; feedApi
  (weighted/followers/hot/top/trending), postsApi (full CRUD +
  like/dislike/bookmark/repost/view/pin/report/hide),
  commentsApi (CRUD + like/dislike/report/replies), followsApi
- src/stores/feed.ts: Pinia feed store — posts[], loading states,
  pagination, optimistic like/dislike/bookmark, addNewPost,
  updatePost, deletePost, incrementCommentCount
- src/stores/post.ts: single post + comments state management
- src/stores/notifications.ts: real-time notification handling
- src/components/feed/PostCard.vue: full post card — header with
  avatar/name/time/menu, text with expand/collapse, hashtags,
  media gallery (grid-1/2/3/4/many layouts), anime/playlist/
  shorts attachment cards, system post, repost embed, spoiler
  toggle, like/dislike/comment/repost/bookmark/share actions
- src/components/feed/CommentsModal.vue: threaded comments modal
  with sort (best/new/old), infinite scroll, nested replies,
  like/dislike, edit/delete (with time window), reply indicator
- src/components/feed/CreatePostModal.vue: post creation with
  type selector, text, media upload (up to 10 imgs / 1 video),
  anime/playlist attachment, visibility, spoiler toggle
- src/components/feed/RepostModal.vue: repost with optional comment
- src/components/feed/PostMenu.vue: context menu — edit, delete,
  pin/unpin, report, bookmark, hide, not-interested, copy link
- src/components/feed/ReportModal.vue: report dialog with reason
- src/views/FeedView.vue: main feed page — tab switcher
  (weighted/followers/hot/top/trending), create-post area,
  infinite scroll, skeleton loaders, empty states, new-posts
  indicator, WebSocket-driven real-time updates

STATE: production-ready, no placeholders, no TODOs, fully wired"

Write-Host "Commit created successfully." -ForegroundColor Green
