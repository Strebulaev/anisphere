<template>
  <div class="search-page">
    <!-- Заголовок с поиском -->
    <div class="search-header">
      <h1 v-if="searchQuery">Результаты поиска</h1>
      <h1 v-else>Поиск</h1>

      <div class="page-search">
        <SearchBar
          variant="page"
          placeholder="Поиск аниме, пользователей, плейлистов..."
          :categories="searchCategories"
          search-route="/anime"
          search-query-key="q"
          @search="handleSearch"
        />
      </div>
    </div>

    <!-- Состояния -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Поиск...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button @click="performSearch" class="retry-btn">Попробовать снова</button>
    </div>

    <div v-else-if="searchQuery && searchResults.length === 0" class="no-results">
      <p>По запросу "{{ searchQuery }}" ничего не найдено</p>
      <p class="suggestion">Попробуйте изменить поисковый запрос</p>
      <p class="examples">Примеры: "Тетрадь смерти", "Наруто", "Атака титанов"</p>
    </div>

    <!-- Результаты поиска -->
    <div v-else-if="searchResults.length > 0 && searchType === 'anime'" class="search-results">
      <div class="results-header">
        <h2>Найдено: {{ searchResults.length }}</h2>
      </div>

      <div class="anime-grid">
        <div
          v-for="anime in searchResults"
          :key="anime.id || anime.shikimori_id"
          class="anime-card"
          @click="openAnimeDetail(anime)"
        >
          <div class="anime-poster">
            <img
              :src="anime.poster_url || '/placeholder-anime.jpg'"
              :alt="anime.title_ru || anime.title_en"
              @error="handleImageError"
            />
            <div class="poster-overlay">
              <button class="play-btn"> <SakuraIcon name="play" /> </button>
            </div>
          </div>

          <div class="anime-info">
            <h3 class="anime-title">
              {{ anime.title_ru || anime.title_en || 'Без названия' }}
            </h3>

            <p class="anime-meta">
              <span v-if="anime.year">{{ anime.year }}</span>
              <span v-if="anime.episodes"> • {{ anime.episodes }} эп.</span>
            </p>

            <div class="anime-meta">
              <span
                class="status-badge"
                :class="'status-' + (anime.status || 'unknown')"
              >
                {{ getStatusText(anime.status) }}
              </span>

              <span v-if="anime.score" class="score"><SakuraIcon name="star" /> {{ anime.score }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Результаты поиска по хэштегу (посты) -->
    <div v-else-if="hashtagPosts.length > 0 && searchType === 'hashtag'" class="hashtag-results">
      <div class="results-header">
        <h2>#{{ searchQuery.replace('#', '') }} — {{ hashtagPosts.length }} постов</h2>
      </div>

      <div class="posts-list">
        <div
          v-for="post in hashtagPosts"
          :key="post.id"
          class="post-item"
          @click="openPost(post)"
        >
          <div class="post-header">
            <img :src="post.author_avatar || '/default-avatar.png'" class="author-avatar">
            <div class="post-meta">
              <span class="author-name">{{ post.author_display_name || post.author_username }}</span>
              <span class="post-time">{{ formatDate(post.created_at) }}</span>
            </div>
          </div>
          <div class="post-content">
            <h3 v-if="post.title">{{ post.title }}</h3>
            <p>{{ truncateText(post.text, 200) }}</p>
          </div>
          <div class="post-stats">
            <span><SakuraIcon name="heart" /> {{ post.likes_count }}</span>
            <span><SakuraIcon name="message" /> {{ post.comments_count }}</span>
            <span><SakuraIcon name="refresh" /> {{ post.reposts_count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Популярное аниме (когда нет поиска) -->
    <div v-else class="popular-anime">
      <h2>Популярное аниме</h2>
      <p class="popular-description">
        Попробуйте найти что-нибудь интересное
      </p>

      <div v-if="popularAnime.length > 0" class="anime-grid">
        <div
          v-for="anime in popularAnime"
          :key="anime.id"
          class="anime-card"
          @click="openAnimeDetail(anime)"
        >
          <div class="anime-poster">
            <img
              :src="anime.poster_url || '/placeholder-anime.jpg'"
              :alt="anime.title_ru"
              @error="handleImageError"
            />
            <div class="poster-overlay">
              <button class="play-btn"> <SakuraIcon name="play" /> </button>
            </div>
          </div>

          <div class="anime-info">
            <h3 class="anime-title">{{ anime.title_ru }}</h3>
            <p class="anime-meta">{{ anime.year }} • {{ anime.episodes }} эп.</p>
          </div>
        </div>
      </div>

      <div v-else class="empty-popular">
        <p>Загрузка популярного аниме...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SearchBar from '@/components/Search/SearchBar.vue'
import { type SearchCategory } from '@/composables/useSearch'
import apiClient from '@/api/client'

interface SearchResult {
  id?: number
  shikimori_id?: string
  title_ru: string
  title_en?: string
  year?: number
  status?: string
  episodes?: number
  score?: number
  poster_url?: string
  source?: string
}

const router = useRouter()
const route = useRoute()
const isHashtagSearch = ref(false)

const searchCategories: SearchCategory[] = [
  {
    id: 'anime',
    name: 'Аниме',
    icon: 'anime',
    enabled: true,
    limit: 5
  },
  {
    id: 'users',
    name: 'Пользователи',
    icon: 'users',
    enabled: true,
    limit: 3
  },
  {
    id: 'playlists',
    name: 'Плейлисты',
    icon: 'playlists',
    enabled: true,
    limit: 3
  }
]

const searchQuery = ref('')
const searchResults = ref<SearchResult[]>([])
const hashtagPosts = ref<any[]>([])
const popularAnime = ref<SearchResult[]>([])
const loading = ref(false)
const error = ref('')
const searchType = ref<'anime' | 'hashtag'>('anime')

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  loading.value = true
  error.value = ''
  
  // Check if it's a hashtag search (starts with #)
  if (searchQuery.value.trim().startsWith('#')) {
    searchType.value = 'hashtag'
    const tag = searchQuery.value.trim().substring(1)
    await performHashtagSearch(tag)
    return
  }
  
  searchType.value = 'anime'
  
  try {
    const response = await apiClient.get('/anime/search/', {
      params: {
        q: searchQuery.value.trim(),
        limit: 50
      }
    })
    
    searchResults.value = response.data.results || []
    
    if (searchResults.value.length === 0) {
      error.value = 'Ничего не найдено по вашему запросу'
    }
  } catch (err: any) {
    console.error('Ошибка поиска:', err)
    error.value = 'Ошибка поиска. Попробуйте еще раз.'
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

const performHashtagSearch = async (tag: string) => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await apiClient.get(`/hashtags/${tag}/`)
    hashtagPosts.value = response.data.results || response.data || []
    
    if (hashtagPosts.value.length === 0) {
      error.value = 'Постов с таким хэштегом не найдено'
    }
  } catch (err: any) {
    console.error('Ошибка поиска хэштега:', err)
    error.value = 'Ошибка поиска. Попробуйте еще раз.'
    hashtagPosts.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = (query: string) => {
  searchQuery.value = query
  router.push({ path: '/anime', query: { q: query } })
  performSearch()
}

const openAnimeDetail = (anime: SearchResult) => {
  const id = anime.id || anime.shikimori_id
  if (id) {
    router.push(`/anime/${id}`)
  }
}

const getStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'ongoing': 'Онгоинг',
    'finished': 'Завершено',
    'announced': 'Анонс'
  }
  return statusMap[status || ''] || 'Неизвестно'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return minutes <= 1 ? 'только что' : `${minutes} мин. назад`
    }
    return `${hours} ч. назад`
  } else if (days === 1) {
    return 'вчера'
  } else if (days < 7) {
    return `${days} дн. назад`
  } else {
    return date.toLocaleDateString('ru')
  }
}

const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const openPost = (post: any) => {
  router.push(`/post/${post.id}`)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/placeholder-anime.jpg'
}

const loadPopularAnime = async () => {
  try {
    const response = await apiClient.get('/anime/', {
      params: {
        page: 1,
        page_size: 12,
        ordering: '-score'
      }
    })
    
    if (response.data.results && response.data.results.length > 0) {
      popularAnime.value = response.data.results
    }
  } catch (err: any) {
    console.error('Ошибка загрузки популярного аниме:', err)
  }
}

onMounted(() => {
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    performSearch()
  } else {
    loadPopularAnime()
  }
})
</script>

<style scoped>
.search-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #373737;
  min-height: 100vh;
}

.search-header {
  text-align: center;
  margin-bottom: 2rem;
}

.search-header h1 {
  color: white;
  font-size: 2rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.page-search {
  max-width: 600px;
  margin: 1.5rem auto 0;
}

.loading-state,
.error-state,
.no-results {
  text-align: center;
  padding: 3rem;
  color: white;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #ef4444;
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #3b82f6;
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}

.no-results p {
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
  color: #a0a0a0;
}

.suggestion {
  color: #6b7280;
  font-size: 1rem;
  margin-top: 0.5rem;
}

.examples {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 1rem;
  font-style: italic;
}

.results-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #333;
}

.results-header h2 {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.popular-anime h2 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.popular-description {
  color: #a0a0a0;
  margin-bottom: 2rem;
}

.empty-popular {
  text-align: center;
  padding: 3rem;
  color: #a0a0a0;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.anime-card {
  background: #1a1a1a;
  border-radius: 0.75rem;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #333;
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  border-color: #3b82f6;
}

.anime-poster {
  position: relative;
  aspect-ratio: 3/4;
  overflow: hidden;
  background: #111;
}

.anime-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.anime-card:hover .anime-poster img {
  transform: scale(1.05);
}

.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.anime-card:hover .poster-overlay {
  opacity: 1;
}

.play-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.anime-info {
  padding: 1rem;
}

.anime-title {
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  line-height: 1.4;
  line-clamp: 2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.anime-meta {
  color: #a0a0a0;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-ongoing {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-finished {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.status-announced {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.score {
  color: #fbbf24;
  font-weight: 500;
  font-size: 0.875rem;
}

/* Hashtag Results */
.hashtag-results {
  margin-top: 1rem;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-item {
  background: #1a1a1a;
  border-radius: 0.75rem;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border: 1px solid #333;
}

.post-item:hover {
  background: #222;
  border-color: #3b82f6;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.post-meta {
  display: flex;
  flex-direction: column;
}

.author-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}

.post-time {
  color: #666;
  font-size: 0.75rem;
}

.post-content h3 {
  color: #fff;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.post-content p {
  color: #ccc;
  font-size: 0.9rem;
  line-height: 1.5;
}

.post-stats {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #333;
}

.post-stats span {
  color: #888;
  font-size: 0.8rem;
}

/* Адаптивность */
@media (max-width: 768px) {
  .search-page {
    padding: 1rem;
  }

  .search-header h1 {
    font-size: 1.5rem;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }

  .anime-info {
    padding: 0.75rem;
  }

  .anime-title {
    font-size: 0.875rem;
  }

  .anime-meta {
    font-size: 0.75rem;
  }
}
</style>