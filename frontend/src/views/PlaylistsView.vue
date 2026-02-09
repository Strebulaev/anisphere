<template>
  <div class="playlists-view">
    <div class="container">
      <div class="page-header">
        <h1>Плейлисты</h1>
        <button @click="showCreateModal = true" class="btn-create">
          <span>+</span> Создать плейлист
        </button>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Filters & Sort -->
      <div v-if="activeTab === 'public'" class="filters-section">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск плейлистов..."
            class="search-input"
          />
          <span class="search-icon">🔍</span>
        </div>

        <div class="filters-row">
          <div class="filter-group">
            <label>Жанры:</label>
            <select v-model="selectedGenre" class="filter-select">
              <option value="">Все жанры</option>
              <option v-for="genre in genres" :key="genre.id" :value="genre.id">
                {{ genre.name }}
              </option>
            </select>
          </div>

          <div class="filter-group">
            <label>Сортировка:</label>
            <select v-model="sortBy" class="filter-select">
              <option value="created_at">По дате (новые)</option>
              <option value="-created_at">По дате (старые)</option>
              <option value="title">По названию</option>
              <option value="-items_count">По популярности</option>
              <option value="-favorites_count">По избранным</option>
            </select>
          </div>

          <div class="filter-group">
            <label>Год:</label>
            <select v-model="selectedYear" class="filter-select">
              <option value="">Любой</option>
              <option v-for="year in years" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>

          <button @click="clearFilters" class="btn-clear">
            Сбросить
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка плейлистов...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button @click="loadPlaylists" class="btn btn-primary">Попробовать снова</button>
      </div>

      <!-- Playlists Grid -->
      <div v-else class="playlists-grid">
        <div v-if="filteredPlaylists.length === 0" class="empty-state">
          <span class="empty-icon">📚</span>
          <p>{{ getEmptyMessage() }}</p>
          <button v-if="activeTab === 'my'" @click="showCreateModal = true" class="btn btn-primary">
            Создать первый плейлист
          </button>
        </div>

        <div v-else class="grid">
          <div
            v-for="playlist in filteredPlaylists"
            :key="playlist.id"
            class="playlist-card"
            @click="goToPlaylist(playlist)"
          >
            <div class="playlist-cover">
              <img v-if="playlist.cover_url" :src="playlist.cover_url" :alt="playlist.title" />
              <div v-else class="cover-placeholder">
                <span>📁</span>
              </div>
              <div v-if="playlist.is_private" class="private-badge">🔒</div>
              <div v-else class="public-badge">🌐</div>
            </div>
            <div class="playlist-info">
              <h3 class="playlist-title">{{ playlist.title }}</h3>
              <p class="playlist-description">{{ playlist.description || 'Без описания' }}</p>
              <div class="playlist-meta">
                <span class="anime-count">📺 {{ playlist.items_count || playlist.anime_count || 0 }} аниме</span>
                <span class="author">@{{ playlist.user_username || playlist.user?.username }}</span>
              </div>
              <div class="playlist-stats" v-if="playlist.favorites_count">
                <span>♥ {{ playlist.favorites_count }}</span>
              </div>
              <div class="playlist-genres" v-if="playlist.genres && playlist.genres.length">
                <span v-for="genre in playlist.genres.slice(0, 3)" :key="genre.id" class="genre-tag">
                  {{ genre.name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            @click="currentPage--; loadPlaylists()"
            :disabled="currentPage === 1"
            class="page-btn"
          >
            ← Предыдущая
          </button>
          <span class="page-info">Страница {{ currentPage }} из {{ totalPages }}</span>
          <button
            @click="currentPage++; loadPlaylists()"
            :disabled="currentPage === totalPages"
            class="page-btn"
          >
            Следующая →
          </button>
        </div>
      </div>

      <!-- Create Playlist Modal -->
      <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
        <div class="modal-content" @click.stop>
          <h3>{{ editingPlaylist ? 'Редактировать плейлист' : 'Создать плейлист' }}</h3>
          <form @submit.prevent="savePlaylist">
            <div class="form-group">
              <label for="title">Название плейлиста</label>
              <input
                v-model="playlistForm.title"
                type="text"
                id="title"
                placeholder="Мой крутой плейлист"
                required
              />
            </div>

            <div class="form-group">
              <label for="description">Описание</label>
              <textarea
                v-model="playlistForm.description"
                id="description"
                placeholder="О чем этот плейлист..."
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label>Тип плейлиста:</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="playlistForm.is_public" :value="true" />
                  <span>🌐 Публичный</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="playlistForm.is_public" :value="false" />
                  <span>🔒 Приватный</span>
                </label>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeModal" class="btn-secondary">Отмена</button>
              <button type="submit" :disabled="!playlistForm.title.trim()" class="btn-primary">
                {{ editingPlaylist ? 'Сохранить' : 'Создать' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

interface Genre {
  id: number
  name: string
}

interface Playlist {
  id: number
  title: string
  description: string
  cover_url?: string | null
  is_public: boolean
  is_private?: boolean
  items_count?: number
  anime_count?: number
  favorites_count?: number
  user_username?: string
  user?: { username: string }
  genres?: Genre[]
  created_at?: string
}

const router = useRouter()

// State
const playlists = ref<Playlist[]>([])
const genres = ref<Genre[]>([])
const loading = ref(false)
const error = ref('')
const showCreateModal = ref(false)
const editingPlaylist = ref<Playlist | null>(null)
const activeTab = ref('my')
const searchQuery = ref('')
const selectedGenre = ref('')
const selectedYear = ref('')
const sortBy = ref('created_at')
const currentPage = ref(1)
const totalPages = ref(1)

// Form
const playlistForm = ref({
  title: '',
  description: '',
  is_public: true
})

// Tabs
const tabs = [
  { id: 'my', label: 'Мои плейлисты' },
  { id: 'public', label: 'Публичные' },
  { id: 'favorites', label: 'Избранное' }
]

// Years for filter
const years = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 10 }, (_, i) => currentYear - i)
})

// Computed
const filteredPlaylists = computed(() => {
  return playlists.value
})

// Methods
const loadGenres = async () => {
  try {
    const response = await apiClient.get('/anime/genres/')
    genres.value = response.data.results || response.data
  } catch (err) {
    console.error('Error loading genres:', err)
  }
}

const loadPlaylists = async () => {
  loading.value = true
  error.value = ''

  try {
    const params: any = {
      page: currentPage.value,
      ordering: sortBy.value
    }

    if (activeTab.value === 'my') {
      params.my = true
    } else if (activeTab.value === 'public') {
      params.is_public = true
      if (searchQuery.value) params.search = searchQuery.value
      if (selectedGenre.value) params.genre = selectedGenre.value
      if (selectedYear.value) params.year = selectedYear.value
    } else if (activeTab.value === 'favorites') {
      params.favorites = true
    }

    const response = await apiClient.get('/playlists/playlists/', { params })
    playlists.value = response.data.results || response.data
    totalPages.value = Math.ceil((response.data.count || playlists.value.length) / 12)
  } catch (err: any) {
    error.value = err.message || 'Не удалось загрузить плейлисты'
    console.error('Error loading playlists:', err)
  } finally {
    loading.value = false
  }
}

const savePlaylist = async () => {
  try {
    const data = { ...playlistForm.value }

    if (editingPlaylist.value) {
      await apiClient.patch(`/playlists/playlists/${editingPlaylist.value.id}/`, data)
    } else {
      await apiClient.post('/playlists/playlists/', data)
    }

    closeModal()
    loadPlaylists()
  } catch (err: any) {
    console.error('Error saving playlist:', err)
    alert('Ошибка сохранения плейлиста')
  }
}

const closeModal = () => {
  showCreateModal.value = false
  editingPlaylist.value = null
  playlistForm.value = { title: '', description: '', is_public: true }
}

const goToPlaylist = (playlist: Playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedGenre.value = ''
  selectedYear.value = ''
  sortBy.value = 'created_at'
  currentPage.value = 1
  loadPlaylists()
}

const getEmptyMessage = () => {
  if (activeTab.value === 'my') return 'У вас пока нет плейлистов'
  if (activeTab.value === 'public') return 'Нет публичных плейлистов'
  return 'Нет избранных плейлистов'
}

// Watch tab changes
watch(activeTab, () => {
  currentPage.value = 1
  loadPlaylists()
})

watch([searchQuery, selectedGenre, selectedYear, sortBy], () => {
  currentPage.value = 1
  loadPlaylists()
})

// Mount
onMounted(() => {
  loadGenres()
  loadPlaylists()
})
</script>

<style scoped>
.playlists-view {
  min-height: 100vh;
  background-color: #222222;
}

.playlists-view .container {
  background-color: #222222;
}

.playlists-view {
  min-height: 100vh;
  background-color: #222222;
}

.playlists-view .container {
  background-color: #222222;
}

/* Rest of the original CSS */
.container {
  padding: 2rem 1rem;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #111111;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #3b82f6;
  color: #222222;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-create:hover {
  background: #2563eb;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.tab-btn {
  background: none;
  border: none;
  padding: 0.75rem 1.25rem;
  font-size: 0.9375rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #3b82f6;
  background: #111111;
}

.tab-btn:hover:not(.active) {
  color: #374151;
  background: #f3f4f6;
}

/* Filters */
.filters-section {
  background: #111111;
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.search-box {
  position: relative;
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
  opacity: 0.5;
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.filter-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #6b7280;
}

.filter-select {
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background: #222222;
  cursor: pointer;
  min-width: 150px;
}

.btn-clear {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background: #111111;
  color: #6b7280;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear:hover {
  background: #f3f4f6;
  color: #374151;
}

/* States */
.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
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

.error-state {
  color: #dc2626;
}

/* Grid */
.playlists-grid {
  margin-top: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.playlist-card {
  background: #222222;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.playlist-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.playlist-cover {
  height: 140px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  color: #111111;
  opacity: 0.9;
}

.private-badge,
.public-badge {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  padding: 0.375rem 0.625rem;
  background: rgba(0,0,0,0.7);
  color: #222222;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.public-badge {
  background: rgba(34, 197, 94, 0.9);
}

.playlist-info {
  padding: 1.25rem;
}

.playlist-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.playlist-description {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.playlist-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8125rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
}

.playlist-stats {
  font-size: 0.8125rem;
  color: #ef4444;
  margin-bottom: 0.5rem;
}

.playlist-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.genre-tag {
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background: #222222;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.875rem;
  color: #6b7280;
}

/* Modal */
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
  background: #222222;
  border-radius: 0.75rem;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
}

.modal-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.375rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.radio-group {
  display: flex;
  gap: 1.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9375rem;
}

.radio-label input {
  width: auto;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  border: 1px solid #111111;
  background: #222222;
  color: #374151;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: #111111;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  border: 1px solid #3b82f6;
  background: #3b82f6;
  color: #222222;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .filters-row {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .grid {
    grid-template-columns: 1fr;
  }

  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
  }

  .tab-btn {
    white-space: nowrap;
  }
}
</style>