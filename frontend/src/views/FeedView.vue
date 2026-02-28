<template>
  <div class="feed-page">
    <!-- Feed Type Tabs -->
    <div class="feed-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.type"
        class="tab-btn"
        :class="{ active: feedStore.feedType === tab.type }"
        @click="switchFeed(tab.type)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Create Post Button -->
    <div class="create-post-area" @click="showCreatePost = true">
      <img :src="currentUser?.avatar_url || '/img/default-avatar.svg'" class="user-avatar" alt="Аватар" />
      <span class="placeholder">Что у вас нового?</span>
      <button class="btn-post">Написать</button>
    </div>

    <!-- New Posts Indicator -->
    <transition name="slide-down">
      <button
        v-if="feedStore.newPostsAvailable"
        class="new-posts-indicator"
        @click="reloadFeed"
      >
        ↑ Новые посты
      </button>
    </transition>

    <!-- Feed Content -->
    <div class="feed-list" ref="feedListRef">
      <!-- Loading Skeleton -->
      <template v-if="feedStore.loading">
        <div v-for="i in 3" :key="i" class="post-skeleton">
          <div class="skeleton-header">
            <div class="skeleton-avatar"></div>
            <div class="skeleton-meta">
              <div class="skeleton-line short"></div>
              <div class="skeleton-line shorter"></div>
            </div>
          </div>
          <div class="skeleton-body">
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
          </div>
        </div>
      </template>

      <!-- Posts -->
      <template v-else-if="feedStore.posts.length > 0">
        <PostCard
          v-for="post in feedStore.posts"
          :key="post.id"
          :post="post"
          :show-comments-preview="true"
          @like="handleLike"
          @dislike="handleDislike"
          @comment="openComments"
          @repost="openRepost"
          @bookmark="handleBookmark"
          @share="handleShare"
          @menu="openPostMenu"
        />
      </template>

      <!-- Empty State -->
      <div v-else-if="feedStore.isEmpty" class="empty-feed">
        <span class="empty-icon">📭</span>
        <p class="empty-title">Лента пуста</p>
        <p class="empty-desc">
          <template v-if="feedStore.feedType === 'followers'">
            Подписывайтесь на пользователей, чтобы видеть их посты
          </template>
          <template v-else>
            Здесь пока нет постов
          </template>
        </p>
        <button v-if="feedStore.feedType === 'followers'" class="btn-explore" @click="switchFeed('weighted')">
          Смотреть популярное
        </button>
      </div>

      <!-- Error State -->
      <div v-else-if="feedStore.error" class="error-state">
        <span class="error-icon">⚠️</span>
        <p>{{ feedStore.error }}</p>
        <button class="btn-retry" @click="feedStore.loadFeed(feedStore.feedType)">Повторить</button>
      </div>

      <!-- Load More Trigger / Loader -->
      <div ref="loadMoreRef" class="load-more-trigger">
        <div v-if="feedStore.loadingMore" class="loading-more">
          <div class="spinner"></div>
        </div>
        <div v-else-if="!feedStore.hasMore && feedStore.posts.length > 0" class="end-of-feed">
          Вы посмотрели всё 👀
        </div>
      </div>
    </div>

    <!-- Modals -->
    <CreatePostModal
      v-if="showCreatePost"
      @close="showCreatePost = false"
      @created="onPostCreated"
    />

    <CommentsModal
      v-if="activeCommentPost"
      :post="activeCommentPost"
      @close="activeCommentPost = null"
    />

    <RepostModal
      v-if="activeRepostPost"
      :post="activeRepostPost"
      @close="activeRepostPost = null"
      @reposted="onReposted"
    />

    <PostMenu
      v-if="activeMenuPost"
      :post="activeMenuPost"
      @close="activeMenuPost = null"
      @delete="(p) => onPostDeleted(p.id)"
      @hide="(p) => onPostHidden(p.id)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/feed/PostCard.vue'
import CreatePostModal from '@/components/feed/CreatePostModal.vue'
import CommentsModal from '@/components/feed/CommentsModal.vue'
import RepostModal from '@/components/feed/RepostModal.vue'
import PostMenu from '@/components/feed/PostMenu.vue'
import type { FeedPost } from '@/api/feed'

type FeedType = 'weighted' | 'followers' | 'hot' | 'top' | 'trending'

const feedStore = useFeedStore()
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const feedListRef = ref<HTMLElement | null>(null)
const loadMoreRef = ref<HTMLElement | null>(null)
const showCreatePost = ref(false)
const activeCommentPost = ref<FeedPost | null>(null)
const activeRepostPost = ref<FeedPost | null>(null)
const activeMenuPost = ref<FeedPost | null>(null)

const tabs = [
  { type: 'weighted' as FeedType, label: 'Для вас' },
  { type: 'followers' as FeedType, label: 'Подписки' },
  { type: 'trending' as FeedType, label: 'Тренды' },
  { type: 'hot' as FeedType, label: 'Горячее' },
  { type: 'top' as FeedType, label: 'Топ' },
]

// Infinite scroll observer
let intersectionObserver: IntersectionObserver | null = null

function setupInfiniteScroll() {
  intersectionObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && feedStore.hasMore && !feedStore.loadingMore) {
        feedStore.loadMore()
      }
    },
    { rootMargin: '200px' }
  )

  if (loadMoreRef.value) {
    intersectionObserver.observe(loadMoreRef.value)
  }
}

async function switchFeed(type: FeedType) {
  await feedStore.loadFeed(type, true)
}

async function reloadFeed() {
  feedStore.newPostsAvailable = false
  await feedStore.loadFeed(feedStore.feedType, true)
  feedListRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleLike(post: FeedPost) {
  feedStore.likePost(post.id)
}

function handleDislike(post: FeedPost) {
  feedStore.dislikePost(post.id)
}

function openComments(post: FeedPost) {
  activeCommentPost.value = post
}

function openRepost(post: FeedPost) {
  activeRepostPost.value = post
}

function handleBookmark(post: FeedPost) {
  feedStore.bookmarkPost(post.id)
}

function handleShare(post: FeedPost) {
  const url = `${window.location.origin}/post/${post.id}`
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url)
  }
}

function openPostMenu(post: FeedPost) {
  activeMenuPost.value = post
}

function onPostCreated(post: FeedPost) {
  feedStore.addNewPost(post)
  showCreatePost.value = false
}

function onReposted() {
  activeRepostPost.value = null
}

function onPostDeleted(postId: number) {
  feedStore.deletePost(postId)
  activeMenuPost.value = null
}

function onPostHidden(postId: number) {
  feedStore.posts.splice(feedStore.posts.findIndex(p => p.id === postId), 1)
  activeMenuPost.value = null
}

onMounted(async () => {
  await feedStore.loadFeed('weighted')
  setupInfiniteScroll()
})

onUnmounted(() => {
  intersectionObserver?.disconnect()
})
</script>

<style scoped>
.feed-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Tabs */
.feed-tabs {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
  scrollbar-width: none;
}

.feed-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  background: #1a1a1a;
  color: #888;
  border: 1px solid #2a2a2a;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.875rem;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #222;
  color: #aaa;
}

.tab-btn.active {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

/* Create Post Area */
.create-post-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #111;
  border: 1px solid #222;
  border-radius: 12px;
  padding: 0.875rem 1rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.create-post-area:hover {
  border-color: #667eea;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.placeholder {
  flex: 1;
  color: #555;
  font-size: 0.9rem;
}

.btn-post {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-post:hover {
  background: #5a6fd6;
}

/* New Posts Indicator */
.new-posts-indicator {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.875rem;
  align-self: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: transform 0.2s;
}

.new-posts-indicator:hover {
  transform: translateY(-1px);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Feed List */
.feed-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Skeletons */
.post-skeleton {
  background: #111;
  border-radius: 12px;
  padding: 1rem;
}

.skeleton-header {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #1f1f1f;
  animation: pulse 1.5s infinite;
  flex-shrink: 0;
}

.skeleton-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  justify-content: center;
}

.skeleton-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-line {
  height: 14px;
  background: #1f1f1f;
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-line.shorter {
  width: 40%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Empty State */
.empty-feed {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
}

.empty-title {
  color: #fff;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.empty-desc {
  color: #666;
  margin: 0;
}

.btn-explore {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.6rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 0.5rem;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  text-align: center;
  color: #888;
}

.error-icon {
  font-size: 2rem;
}

.btn-retry {
  background: #333;
  color: #fff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
}

/* Load More */
.load-more-trigger {
  padding: 1rem 0;
  display: flex;
  justify-content: center;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: 1rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.end-of-feed {
  color: #555;
  font-size: 0.875rem;
  padding: 1rem;
}
</style>
