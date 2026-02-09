<template>
  <div class="feed">
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
          </button>
        </div>
        <button @click="showCreatePost = true" class="btn-create-post">
          ✏️ Создать пост
        </button>
      </div>

      <!-- Posts Feed -->
      <div class="posts-list">
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="posts.length === 0" class="empty-state">
          <p>Пока нет постов. Будьте первым!</p>
        </div>
        <div v-else>
          <div v-for="post in posts" :key="post.id" class="post-card">
            <div class="post-header">
              <img :src="post.author_avatar || '/missing_original.jpg'" :alt="post.author_username" class="avatar">
              <div class="post-info">
                <strong>{{ post.author_username }}</strong>
                <small>{{ formatDate(post.created_at) }}</small>
              </div>
            </div>
            <div class="post-content">
              <!-- Anime reference -->
              <div v-if="post.anime" class="anime-reference">
                <img :src="post.anime.poster_url" :alt="post.anime.title_ru" class="anime-mini-poster" />
                <div class="anime-info">
                  <span class="anime-title">{{ post.anime.title_ru }}</span>
                  <span class="anime-link">🎬 Перейти к аниме</span>
                </div>
              </div>

              <p v-if="post.text">{{ post.text }}</p>

              <!-- Hashtags -->
              <div v-if="post.hashtags && post.hashtags.length" class="hashtags">
                <span v-for="hashtag in post.hashtags" :key="hashtag" class="hashtag">#{{ hashtag }}</span>
              </div>

              <img v-if="post.image_url" :src="post.image_url" class="post-image" />
              <video v-if="post.video_url" :src="post.video_url" controls class="post-video"></video>
            </div>
            <div class="post-actions">
              <button @click="toggleLike(post)" class="action-btn" :class="{ liked: post.is_liked }">
                ❤️ {{ post.likes_count }}
              </button>
              <button @click="showComments(post)" class="action-btn">
                💬 {{ post.comments_count }}
              </button>
              <button @click="repost(post)" class="action-btn">
                🔄 {{ post.reposts_count }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Post Modal -->
      <div v-if="showCreatePost" class="modal-overlay" @click="showCreatePost = false">
        <div class="modal-content" @click.stop>
          <h3>Создать пост</h3>
          <form @submit.prevent="createPost">
            <textarea v-model="newPost.text" placeholder="Что нового?" required></textarea>
            <div class="form-actions">
              <button type="button" @click="showCreatePost = false">Отмена</button>
              <button type="submit" :disabled="!newPost.text.trim()">Опубликовать</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

interface Post {
  id: number
  author_username: string
  author_avatar: string | null
  text: string
  image_url: string | null
  video_url: string | null
  likes_count: number
  comments_count: number
  reposts_count: number
  created_at: string
  hashtags?: string[]
  anime?: {
    id: number
    title_ru: string
    poster_url: string
  }
  type?: 'post' | 'news' | 'recommendation'
  is_liked?: boolean
}

const posts = ref<Post[]>([])
const loading = ref(true)
const showCreatePost = ref(false)
const newPost = ref({ text: '' })

// Feed tabs
const activeTab = ref('feed')
const feedTabs = [
  { id: 'feed', label: 'Лента' },
  { id: 'following', label: 'Подписки' },
  { id: 'trending', label: 'Популярное' }
]

const loadPosts = async () => {
  loading.value = true
  try {
      let url = '/social/posts/'
      if (activeTab.value === 'feed') {
        url += '?feed=true'
      } else if (activeTab.value === 'trending') {
        url += '?ordering=-likes_count'
      }
    const response = await apiClient.get(url)
    posts.value = response.data.results || response.data
  } catch (error) {
    console.error('Error loading posts:', error)
  } finally {
    loading.value = false
  }
}

const switchTab = (tabId: string) => {
  activeTab.value = tabId
  loadPosts()
}

const createPost = async () => {
  try {
    await apiClient.post('/social/posts/', newPost.value)
    newPost.value.text = ''
    showCreatePost.value = false
    loadPosts() // Reload posts
  } catch (error) {
    console.error('Error creating post:', error)
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('ru-RU')
}

// Post interaction methods
const toggleLike = async (post: Post) => {
  try {
    if (post.is_liked) {
      // Unlike - assuming there's an API endpoint for this
      await apiClient.delete(`/social/posts/${post.id}/unlike/`)
      post.is_liked = false
      post.likes_count--
    } else {
      // Like
      await apiClient.post(`/social/posts/${post.id}/like/`)
      post.is_liked = true
      post.likes_count++
    }
  } catch (error) {
    console.error('Error toggling like:', error)
  }
}

const showComments = (post: Post) => {
  // TODO: Open comments modal or navigate to post detail
  alert(`Комментарии к посту ${post.id} будут реализованы позже`)
}

const repost = async (post: Post) => {
  try {
    await apiClient.post(`/social/posts/${post.id}/repost/`)
    post.reposts_count++
    // Show success message
  } catch (error) {
    console.error('Error reposting:', error)
  }
}

onMounted(() => {
  loadPosts()
})
</script>

<style scoped>
.feed {
  padding: 2rem 0;
}

/* Feed Header */
.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

/* Feed Tabs */
.feed-tabs {
  display: flex;
  gap: 1rem;
}

.tab-btn {
  background: none;
  border: none;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  border-radius: 6px;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
  background: #111111;
}

.tab-btn:hover {
  color: #374151;
  background: #222222;
}

.create-post-card {
  background: #111111;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.btn-create-post {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #111111;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-create-post:hover {
  background: #222222;
}

.posts-list {
  margin-top: 1rem;
}

.post-card {
  background: #111111;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.post-info strong {
  display: block;
  color: #1f2937;
}

.post-info small {
  color: #6b7280;
  font-size: 0.875rem;
}

.post-content {
  margin-bottom: 1rem;
}

.post-content p {
  margin-bottom: 1rem;
  line-height: 1.6;
}

.post-image, .post-video {
  max-width: 100%;
  border-radius: 8px;
}

.post-actions {
  display: flex;
  gap: 1rem;
}

.action-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background: #222222;
}

.action-btn.liked {
  color: #ef4444;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
}

.modal-content h3 {
  margin-bottom: 1rem;
}

.modal-content textarea {
  width: 100%;
  min-height: 120px;
  padding: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  resize: vertical;
  margin-bottom: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.form-actions button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
}

.form-actions button[type="submit"] {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.form-actions button[type="submit"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

/* Anime reference */
.anime-reference {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid #e5e7eb;
}

.anime-mini-poster {
  width: 40px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
}

.anime-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.anime-title {
  font-weight: 500;
  color: #1f2937;
  font-size: 0.875rem;
}

.anime-link {
  font-size: 0.75rem;
  color: #3b82f6;
  cursor: pointer;
}

.anime-link:hover {
  text-decoration: underline;
}

/* Hashtags */
.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.hashtag {
  color: #3b82f6;
  font-size: 0.875rem;
  cursor: pointer;
}

.hashtag:hover {
  text-decoration: underline;
}
</style>