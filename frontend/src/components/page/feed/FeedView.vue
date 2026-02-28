<template>
  <div class="feed-page">
    <div class="container">
      <!-- Feed Header -->
      <div class="feed-header">
        <div class="feed-tabs">
          <button
            v-for="tab in feedTabs"
            :key="tab.id"
            @click="switchTab(tab.id)"
            :class="['tab-btn', { active: activeTab === tab.id }]"
          >
            {{ tab.label }}
            <span v-if="tab.id === 'feed' && newPostsCount > 0" class="new-posts-badge">
              {{ newPostsCount }}
            </span>
          </button>
        </div>
        <button @click="() => openCreatePostModal()" class="btn-create-post">
          <span class="icon">✏️</span>
        </button>
      </div>

      <div class="feed-layout">
        <!-- Sidebar -->
        <aside class="feed-sidebar">
          <div class="sidebar-card">
            <h3>Фильтры</h3>
            <div class="filter-options">
              <label v-for="filter in filters" :key="filter.id" class="filter-option">
                <input
                  type="radio"
                  :value="filter.id"
                  v-model="selectedFilter"
                  @change="applyFilter"
                >
                <span>{{ filter.label }}</span>
              </label>
            </div>
          </div>

          <div class="sidebar-card">
            <h3>Интересы</h3>
            <div class="interest-tags">
              <span
                v-for="tag in interestTags"
                :key="tag"
                class="interest-tag"
                :class="{ active: selectedInterests.includes(tag) }"
                @click="toggleInterest(tag)"
              >
                #{{ tag }}
              </span>
            </div>
          </div>
        </aside>

        <!-- Main Feed -->
        <main class="feed-main">
          <!-- Create Post Card -->
          <div class="create-post-card" @click="() => openCreatePostModal()">
            <img :src="currentUser?.avatar || defaultAvatar" class="avatar" alt="Avatar">
            <span class="placeholder">Что у вас нового?</span>
            <div class="create-actions">
              <button type="button" @click="handleCreateImage" title="Фото">
                📷
              </button>
              <button type="button" @click="handleCreateVideo" title="Видео">
                🎥
              </button>
              <button type="button" @click="handleCreatePlaylist" title="Плейлист">
                📁
              </button>
              <button type="button" @click="handleCreateAnime" title="Аниме">
                🎬
              </button>
            </div>
          </div>

          <!-- Posts Feed -->
          <div class="posts-list" ref="postsContainer">
            <!-- Loading State -->
            <div v-if="loading && posts.length === 0" class="loading-state">
              <div class="skeleton-post" v-for="i in 3" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
                <div class="skeleton-content">
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line medium"></div>
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else-if="!loading && posts.length === 0" class="empty-state">
              <div class="empty-icon">📝</div>
              <h3>Пока нет постов</h3>
              <p>Подпишитесь на интересных авторов или создайте свой первый пост!</p>
              <button @click="() => openCreatePostModal()" class="btn-primary">
                Создать пост
              </button>
            </div>

            <!-- Posts -->
            <div v-else>
              <div v-if="newPostsCount > 0" class="new-posts-bar" @click="loadNewPosts">
                <span>Показать {{ newPostsCount }} новых постов</span>
              </div>

              <PostCard
                v-for="post in posts"
                :key="post.id"
                :post="post"
                @like="handleLike"
                @dislike="handleDislike"
                @comment="openComments"
                @repost="openRepostModal"
                @share="sharePost"
                @bookmark="toggleBookmark"
                @menu="openPostMenu"
                @report="openReportModal"
                @click.native="openPostDetail(post)"
              />

              <!-- Load More -->
              <div v-if="hasMore" class="load-more">
                <button @click="loadMorePosts" :disabled="loadingMore" class="btn-load-more">
                  {{ loadingMore ? 'Загрузка...' : 'Показать ещё' }}
                </button>
              </div>
            </div>
          </div>
        </main>

        <!-- Right Sidebar -->
        <aside class="feed-right-sidebar">
          <div class="sidebar-card trending">
            <h3>🔥 Популярное</h3>
            <div class="trending-posts">
              <div
                v-for="trend in trendingPosts"
                :key="trend.id"
                class="trending-item"
                @click="openTrendingPost(trend)"
              >
                <span class="trend-rank">{{ trend.rank }}</span>
                <div class="trend-content">
                  <span class="trend-title">{{ trend.title }}</span>
                  <span class="trend-stats">{{ trend.likes_count }} лайков</span>
                </div>
              </div>
            </div>
          </div>

          <div class="sidebar-card suggested">
            <h3>Кого читать</h3>
            <div class="suggested-users">
              <div
                v-for="user in suggestedUsers"
                :key="user.id"
                class="suggested-user"
              >
                <img :src="user.avatar || defaultAvatar" class="avatar-sm" alt="">
                <div class="user-info">
                  <span class="username">{{ user.username }}</span>
                  <span class="display-name">{{ user.display_name }}</span>
                </div>
                <button
                  @click="toggleFollow(user)"
                  :class="['btn-follow', { following: user.is_following }]"
                >
                  {{ user.is_following ? 'Отписаться' : 'Подписаться' }}
                </button>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>

    <!-- Create Post Modal -->
    <CreatePostModal
      v-if="showCreatePost"
      :initial-type="createPostType"
      @close="showCreatePost = false"
      @created="onPostCreated"
    />

    <!-- Comments Modal -->
    <CommentsModal
      v-if="showComments"
      :post="selectedPost"
      @close="showComments = false"
      @comment-added="onCommentAdded"
    />

    <!-- Repost Modal -->
    <RepostModal
      v-if="showRepost"
      :post="selectedPost"
      @close="showRepost = false"
      @reposted="onReposted"
    />

    <!-- Post Menu -->
    <PostMenu
      v-if="showMenu && selectedPost"
      :post="selectedPost"
      @close="showMenu = false"
      @edit="editPost"
      @delete="deletePost"
      @pin="pinPost"
      @report="openReportModal"
      @bookmark="toggleBookmark"
      @hide="hidePost"
    />

    <!-- Report Modal -->
    <ReportModal
      v-if="showReport"
      :content-type="'post'"
      :content-id="selectedPost?.id"
      @close="showReport = false"
    />

    <!-- Post Detail Modal -->
    <PostDetailModal
      v-if="showPostDetail"
      :post="selectedPost"
      @close="showPostDetail = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import PostCard from '@/components/feed/PostCard.vue'
import CreatePostModal from '@/components/feed/CreatePostModal.vue'
import CommentsModal from '@/components/feed/CommentsModal.vue'
import RepostModal from '@/components/feed/RepostModal.vue'
import PostMenu from '@/components/feed/PostMenu.vue'
import ReportModal from '@/components/feed/ReportModal.vue'
import PostDetailModal from '@/components/feed/PostDetailModal.vue'

interface Post {
  id: number
  author: number
  author_username: string
  author_avatar: string | null
  author_display_name: string | null
  title: string
  post_type: string
  text: string
  image_url: string | null
  image_file: string | null
  video_url: string | null
  video_file: string | null
  anime: any
  anime_rating: number | null
  playlist: any
  group: any
  original_post: any
  repost_comment: string
  likes_count: number
  dislikes_count: number
  comments_count: number
  reposts_count: number
  views_count: number
  is_pinned: boolean
  is_deleted: boolean
  allow_comments: boolean
  created_at: string
  updated_at: string
  edited_at: string | null
  is_spoiler: boolean
  media_files: any[]
  hashtags: string[]
  is_liked: boolean
  is_disliked: boolean
  is_bookmarked: boolean
  is_following: boolean
  can_edit: boolean
  can_delete: boolean
}

interface User {
  id: number
  username: string
  display_name: string
  avatar: string
}

interface TrendingPost {
  id: number
  rank: number
  title: string
  likes_count: number
}

const router = useRouter()

// State
const posts = ref<Post[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const activeTab = ref('feed')
const selectedFilter = ref('all')
const newPostsCount = ref(0)
const currentPage = ref(1)
const selectedInterests = ref<string[]>([])

// UI State
const showCreatePost = ref(false)
const showComments = ref(false)
const showRepost = ref(false)
const showMenu = ref(false)
const showReport = ref(false)
const showPostDetail = ref(false)
const createPostType = ref<string | null>(null)

// Selected items
const selectedPost = ref<Post | null>(null)

// User
const currentUser = ref<User | null>(null)
const defaultAvatar = '/img/default-avatar.svg'

// Feed tabs
const feedTabs = [
  { id: 'feed', label: 'Лента' },
  { id: 'following', label: 'Подписки' },
  { id: 'top', label: 'Топ' },
  { id: 'trending', label: 'Горячее' },
  { id: 'groups', label: 'Группы' }
]

// Filters
const filters = [
  { id: 'all', label: 'Все посты' },
  { id: 'text', label: 'Текстовые' },
  { id: 'image', label: 'С изображениями' },
  { id: 'video', label: 'С видео' },
  { id: 'anime', label: 'Об аниме' }
]

// Interest tags
const interestTags = ['аниме', 'манга', 'рецензии', 'персонажи', 'музыка', 'арт', 'новости', 'обсуждения']

// Trending posts (mock data)
const trendingPosts = ref<TrendingPost[]>([
  { id: 1, rank: 1, title: 'Топ аниме 2024 года', likes_count: 1250 },
  { id: 2, rank: 2, title: 'Обзор на новый сезон', likes_count: 980 },
  { id: 3, rank: 3, title: 'Мой топ манги', likes_count: 750 }
])

// Suggested users (mock data)
const suggestedUsers = ref([
  { id: 1, username: 'anime_fan', display_name: 'Аниме Фан', avatar: null, is_following: false },
  { id: 2, username: 'manga_lover', display_name: 'Манга Лав', avatar: null, is_following: false }
])

// Computed
const filteredPosts = computed(() => {
  if (selectedFilter.value === 'all') return posts.value
  return posts.value.filter(p => p.post_type === selectedFilter.value)
})

// Methods
const loadPosts = async () => {
  loading.value = true
  try {
    let url = '/social/feed/weighted/'
    
    if (activeTab.value === 'following') {
      url = '/social/feed/followers/'
    } else if (activeTab.value === 'trending') {
      url = '/social/feed/hot/'
    } else if (activeTab.value === 'top') {
      url = '/social/feed/top/'
    } else if (activeTab.value === 'groups') {
      url = '/social/posts/?group=true'
    }

    const response = await apiClient.get(url)
    posts.value = response.data.posts || response.data.results || []
    newPostsCount.value = 0
  } catch (error) {
    console.error('Error loading posts:', error)
    // Fallback to regular feed if weighted fails
    try {
      const response = await apiClient.get('/social/feed/')
      posts.value = response.data.results || response.data || []
    } catch (fallbackError) {
      console.error('Fallback feed also failed:', fallbackError)
    }
  } finally {
    loading.value = false
  }
}

const loadMorePosts = async () => {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  try {
    currentPage.value++
    const response = await apiClient.get(`/social/feed/?page=${currentPage.value}`)
    const newPosts = response.data.posts || response.data.results || []
    posts.value.push(...newPosts)
    hasMore.value = newPosts.length > 0
  } catch (error) {
    console.error('Error loading more posts:', error)
  } finally {
    loadingMore.value = false
  }
}

const loadNewPosts = async () => {
  await loadPosts()
}

const switchTab = (tabId: string) => {
  activeTab.value = tabId
  currentPage.value = 1
  loadPosts()
}

const applyFilter = () => {
  currentPage.value = 1
  loadPosts()
}

const toggleInterest = (tag: string) => {
  const index = selectedInterests.value.indexOf(tag)
  if (index > -1) {
    selectedInterests.value.splice(index, 1)
  } else {
    selectedInterests.value.push(tag)
  }
}

const openCreatePostModal = (type?: string) => {
  createPostType.value = type || null
  showCreatePost.value = true
}

// Wrapper functions for template
const handleCreateImage = () => openCreatePostModal('image')
const handleCreateVideo = () => openCreatePostModal('video')
const handleCreatePlaylist = () => openCreatePostModal('playlist')
const handleCreateAnime = () => openCreatePostModal('anime')

const openComments = (post: any) => {
  selectedPost.value = post
  showComments.value = true
}

const openRepostModal = (post: any) => {
  selectedPost.value = post
  showRepost.value = true
}

const openPostMenu = (post: any) => {
  selectedPost.value = post
  showMenu.value = true
}

const openReportModal = (post: any) => {
  selectedPost.value = post
  showReport.value = true
}

const openPostDetail = (post: any) => {
  selectedPost.value = post
  showPostDetail.value = true
}

const openTrendingPost = (trend: TrendingPost) => {
  // Для trending постов нужно загрузить полный пост
  const post: Post = {
    id: trend.id,
    author: 0,
    author_username: '',
    author_avatar: null,
    author_display_name: null,
    title: trend.title,
    post_type: 'text',
    text: '',
    image_url: null,
    image_file: null,
    video_url: null,
    video_file: null,
    anime: null,
    anime_rating: null,
    playlist: null,
    group: null,
    original_post: null,
    repost_comment: '',
    likes_count: trend.likes_count,
    dislikes_count: 0,
    comments_count: 0,
    reposts_count: 0,
    views_count: 0,
    is_pinned: false,
    is_deleted: false,
    allow_comments: true,
    created_at: '',
    updated_at: '',
    edited_at: null,
    is_spoiler: false,
    media_files: [],
    hashtags: [],
    is_liked: false,
    is_disliked: false,
    is_bookmarked: false,
    is_following: false,
    can_edit: false,
    can_delete: false
  }
  selectedPost.value = post
  showPostDetail.value = true
}

const handleLike = async (post: any) => {
  try {
    if (post.is_liked) {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_liked = false
      post.likes_count--
    } else {
      await apiClient.post(`/social/posts/${post.id}/like/`)
      post.is_liked = true
      post.likes_count++
      if (post.is_disliked) {
        post.is_disliked = false
        post.dislikes_count--
      }
    }
  } catch (error) {
    console.error('Error toggling like:', error)
  }
}

const handleDislike = async (post: any) => {
  try {
    if (post.is_disliked) {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_disliked = false
      post.dislikes_count--
    } else {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_disliked = true
      post.dislikes_count++
      if (post.is_liked) {
        post.is_liked = false
        post.likes_count--
      }
    }
  } catch (error) {
    console.error('Error toggling dislike:', error)
  }
}

const toggleBookmark = async (post: any) => {
  try {
    await apiClient.post('/social/bookmarks/toggle/', { post_id: post.id })
    post.is_bookmarked = !post.is_bookmarked
  } catch (error) {
    console.error('Error toggling bookmark:', error)
  }
}

const sharePost = async (post: any) => {
  try {
    await navigator.clipboard.writeText(`${window.location.origin}/post/${post.id}`)
  } catch (error) {
    console.error('Error sharing post:', error)
  }
}

const editPost = (_post: any) => {
  showMenu.value = false
}

const deletePost = async (post: any) => {
  try {
    await apiClient.delete(`/social/posts/${post.id}/`)
    posts.value = posts.value.filter(p => p.id !== post.id)
    showMenu.value = false
  } catch (error) {
    console.error('Error deleting post:', error)
  }
}

const pinPost = async (post: any) => {
  try {
    await apiClient.post(`/social/posts/${post.id}/pin/`)
    post.is_pinned = true
    showMenu.value = false
  } catch (error) {
    console.error('Error pinning post:', error)
  }
}

const hidePost = (post: any) => {
  posts.value = posts.value.filter(p => p.id !== post.id)
  showMenu.value = false
}

const toggleFollow = async (user: any) => {
  try {
    await apiClient.post(`/social/follow/toggle/${user.id}/`)
    user.is_following = !user.is_following
  } catch (error) {
    console.error('Error toggling follow:', error)
  }
}

const onPostCreated = (post: any) => {
  posts.value.unshift(post)
  showCreatePost.value = false
}

const onCommentAdded = (_comment: any) => {
  if (selectedPost.value && selectedPost.value.comments_count !== undefined) {
    selectedPost.value.comments_count++
  }
}

const onReposted = (_post: any) => {
  if (selectedPost.value) {
    selectedPost.value.reposts_count++
  }
  showRepost.value = false
}

// Fetch current user
const fetchCurrentUser = async () => {
  try {
    const response = await apiClient.get('/users/me/')
    currentUser.value = response.data
  } catch (error) {
    console.error('Error fetching current user:', error)
  }
}

// Scroll handler for infinite scroll
const handleScroll = () => {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight ?? 0
  const documentHeight = document.documentElement.scrollHeight

  if (scrollTop + windowHeight >= documentHeight - 500) {
    loadMorePosts()
  }
}

// Lifecycle
onMounted(async () => {
  await fetchCurrentUser()
  await loadPosts()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.feed-page {
  min-height: 100vh;
  background: #0a0a0a;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Feed Header */
.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #1f1f1f;
  position: sticky;
  top: 0;
  background: #0a0a0a;
  z-index: 100;
}

.feed-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: #888;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #151515;
  color: #fff;
}

.tab-btn.active {
  background: #1a1a1a;
  color: #fff;
}

.new-posts-badge {
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
}

.btn-create-post {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-create-post:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-create-post .icon {
  font-size: 1.1rem;
}

/* Feed Layout */
.feed-layout {
  display: grid;
  grid-template-columns: 250px 1fr 280px;
  gap: 1.5rem;
  padding: 1.5rem 0;
}

/* Sidebar */
.feed-sidebar {
  position: sticky;
  top: 80px;
  height: fit-content;
}

.sidebar-card {
  background: #111;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.sidebar-card h3 {
  font-size: 0.9rem;
  color: #888;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.filter-option:hover {
  background: #1a1a1a;
}

.filter-option input {
  accent-color: #667eea;
}

.interest-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.interest-tag {
  background: #1a1a1a;
  color: #888;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.interest-tag:hover,
.interest-tag.active {
  background: #667eea;
  color: white;
}

/* Main Feed */
.feed-main {
  min-height: 500px;
}

.create-post-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #111;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.create-post-card:hover {
  background: #151515;
}

.create-post-card .avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.create-post-card .placeholder {
  flex: 1;
  color: #555;
  font-size: 0.95rem;
}

.create-actions {
  display: flex;
  gap: 0.5rem;
}

.create-actions button {
  background: none;
  border: none;
  font-size: 1.2rem;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.create-actions button:hover {
  background: #1f1f1f;
}

/* Posts List */
.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.new-posts-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 0.75rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  transition: transform 0.2s;
}

.new-posts-bar:hover {
  transform: scale(1.02);
}

.load-more {
  text-align: center;
  padding: 1rem;
}

.btn-load-more {
  background: #1a1a1a;
  color: #888;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-load-more:hover:not(:disabled) {
  background: #252525;
  color: #fff;
}

.btn-load-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-post {
  background: #111;
  border-radius: 12px;
  padding: 1.5rem;
}

.skeleton-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #1f1f1f;
  animation: pulse 1.5s infinite;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-line {
  height: 12px;
  background: #1f1f1f;
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

.skeleton-line.short {
  width: 40%;
}

.skeleton-line.medium {
  width: 70%;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #111;
  border-radius: 12px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #fff;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #666;
  margin-bottom: 1.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

/* Right Sidebar */
.feed-right-sidebar {
  position: sticky;
  top: 80px;
  height: fit-content;
}

.trending-posts {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.trending-item {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.trending-item:hover {
  background: #1a1a1a;
}

.trend-rank {
  font-size: 1.2rem;
  font-weight: 700;
  color: #667eea;
  width: 24px;
}

.trend-content {
  display: flex;
  flex-direction: column;
}

.trend-title {
  color: #fff;
  font-size: 0.9rem;
}

.trend-stats {
  color: #666;
  font-size: 0.75rem;
}

.suggested-users {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.suggested-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.username {
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
}

.display-name {
  color: #666;
  font-size: 0.75rem;
}

.btn-follow {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-follow:hover {
  background: #5a6fd6;
}

.btn-follow.following {
  background: transparent;
  border: 1px solid #444;
  color: #888;
}

.btn-follow.following:hover {
  border-color: #ef4444;
  color: #ef4444;
}

/* Responsive */
@media (max-width: 1024px) {
  .feed-layout {
    grid-template-columns: 1fr;
  }

  .feed-sidebar,
  .feed-right-sidebar {
    display: none;
  }
}
</style>
