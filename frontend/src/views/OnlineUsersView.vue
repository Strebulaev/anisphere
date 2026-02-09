<template>
  <div class="online-users-page">
    <div class="container">
      <div class="page-header">
        <h1>👥 Люди онлайн</h1>
        <p class="page-subtitle">Найди единомышленников и новых друзей</p>
      </div>

      <!-- Filters and Search -->
      <div class="filters-section">
        <!-- Search -->
        <div class="search-box">
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            type="text"
            placeholder="Поиск по имени или nickname..."
            class="search-input"
          />
          <div class="search-icon">🔍</div>
        </div>

        <!-- Genre Filters -->
        <div class="genre-filters">
          <h3>Любимые жанры:</h3>
          <div class="genre-buttons">
            <button
              v-for="genre in availableGenres"
              :key="genre.id"
              @click="toggleGenreFilter(genre.id)"
              :class="['genre-btn', { active: selectedGenres.includes(genre.id) }]"
            >
              {{ genre.name }}
            </button>
          </div>
        </div>

        <!-- Sort Options -->
        <div class="sort-options">
          <label>Сортировка:</label>
          <select v-model="sortBy" @change="loadUsers" class="sort-select">
            <option value="-last_login">По времени входа</option>
            <option value="username">По имени (A-Z)</option>
            <option value="-level">По уровню</option>
            <option value="-experience">По опыту</option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка пользователей...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <p>Ошибка: {{ error }}</p>
        <button @click="loadUsers" class="btn btn-primary">Попробовать снова</button>
      </div>

      <!-- Users Grid -->
      <div v-else class="users-grid">
        <div v-if="users.length === 0" class="empty-state">
          <p>Никого не найдено онлайн</p>
          <p class="text-sm text-gray-500 mt-2">Пользователи появятся здесь, когда войдут в систему</p>
        </div>

        <div v-else class="users-list">
          <div
            v-for="user in users"
            :key="user.id"
            class="user-card"
            @click="goToUserProfile(user)"
          >
            <div class="user-avatar">
              <img
                v-if="user.avatar"
                :src="getAvatarUrl(user.avatar)"
                :alt="user.display_name || user.username"
                class="avatar-image"
                @error="onAvatarError"
              >
              <div v-else class="avatar-placeholder">
                {{ getUserInitials(user) }}
              </div>
              <div v-if="user.is_online" class="online-indicator">
                <span class="online-dot"></span>
              </div>
            </div>

            <div class="user-info">
              <h3 class="user-name">{{ user.display_name || user.username }}</h3>
              <p class="user-nickname" v-if="user.nickname">@{{ user.nickname }}</p>
              <p class="user-level">Уровень {{ user.level || 1 }}</p>

              <!-- Favorite genres -->
              <div v-if="user.favorite_genres && user.favorite_genres.length" class="user-genres">
                <span
                  v-for="genreId in user.favorite_genres.slice(0, 3)"
                  :key="genreId"
                  class="genre-tag"
                >
                  {{ getGenreName(genreId) }}
                </span>
                <span v-if="user.favorite_genres.length > 3" class="more-genres">
                  +{{ user.favorite_genres.length - 3 }}
                </span>
              </div>

              <div v-if="user.show_stats" class="user-stats">
                <span class="stat">📝 {{ user.posts_count || 0 }}</span>
                <span class="stat">💬 {{ user.comments_count || 0 }}</span>
                <span class="stat">❤️ {{ user.likes_received || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { useAvatar } from '@/composables/useAvatar'

interface User {
  id: number
  username: string
  display_name?: string
  nickname?: string
  avatar?: string
  is_online: boolean
  level: number
  experience: number
  favorite_genres: string[]
  posts_count: number
  comments_count: number
  likes_received: number
  show_online_status: boolean
  show_in_search: boolean
  show_stats: boolean
}

const router = useRouter()
const { getAvatarUrl, getUserInitials } = useAvatar()

// State
const users = ref<User[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const searchQuery = ref('')
const selectedGenres = ref<string[]>([])
const sortBy = ref('-last_login')

// Available genres
const availableGenres = [
  { id: 'action', name: 'Экшен' },
  { id: 'adventure', name: 'Приключения' },
  { id: 'comedy', name: 'Комедия' },
  { id: 'drama', name: 'Драма' },
  { id: 'fantasy', name: 'Фэнтези' },
  { id: 'romance', name: 'Романтика' },
  { id: 'scifi', name: 'Sci-Fi' },
  { id: 'horror', name: 'Ужасы' },
  { id: 'mystery', name: 'Детектив' },
  { id: 'slice_of_life', name: 'Повседневность' }
]

// Debounced search
let searchTimeout: number | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadUsers()
  }, 500)
}

// Load users
const loadUsers = async () => {
  loading.value = true
  error.value = null

  try {
    const params: any = {
      ordering: sortBy.value
    }

    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }

    if (selectedGenres.value.length > 0) {
      params.genres = selectedGenres.value
    }

    const response = await apiClient.get('/users/online/', { params })
    users.value = response.data.results || response.data
  } catch (err: any) {
    error.value = err.message || 'Не удалось загрузить пользователей'
    console.error('Error loading online users:', err)
  } finally {
    loading.value = false
  }
}

// Toggle genre filter
const toggleGenreFilter = (genreId: string) => {
  const index = selectedGenres.value.indexOf(genreId)
  if (index === -1) {
    selectedGenres.value.push(genreId)
  } else {
    selectedGenres.value.splice(index, 1)
  }
  loadUsers()
}

// Get genre name
const getGenreName = (genreId: string) => {
  const genre = availableGenres.find(g => g.id === genreId)
  return genre ? genre.name : genreId
}

// Avatar functions are now imported from useAvatar composable

// Handle avatar error
const onAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// Go to user profile
const goToUserProfile = (user: User) => {
  router.push(`/profile/${user.id}`)
}

// Initialize
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.online-users-page {
  min-height: 100vh;
  background-color: #f9fafb;
  padding-bottom: 2rem;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
  padding: 2rem 0;
}

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.125rem;
  color: #6b7280;
}

.filters-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.search-box {
  position: relative;
  max-width: 400px;
  margin-bottom: 2rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}

.genre-filters h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.genre-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.genre-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 9999px;
  background: white;
  color: #4b5563;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.genre-btn:hover {
  background: #f3f4f6;
}

.genre-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sort-options label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.sort-select {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
}

.users-grid {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.users-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.user-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #e5e7eb;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.user-avatar {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem;
}

.avatar-image, .avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.online-indicator {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.online-dot {
  width: 12px;
  height: 12px;
  background: #10b981;
  border-radius: 50%;
}

.user-info {
  text-align: center;
}

.user-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.user-nickname {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.user-level {
  font-size: 0.75rem;
  color: #3b82f6;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.user-genres {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.genre-tag {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.more-genres {
  background: #f3f4f6;
  color: #6b7280;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.user-stats {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.stat {
  font-size: 0.75rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: 1px solid #3b82f6;
}

.btn-primary:hover {
  background: #2563eb;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .filters-section {
    padding: 1.5rem;
  }

  .users-list {
    grid-template-columns: 1fr;
  }

  .genre-buttons {
    justify-content: center;
  }

  .sort-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>