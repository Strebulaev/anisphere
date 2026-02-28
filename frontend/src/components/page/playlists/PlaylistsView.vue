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
          <PlaylistCard
            v-for="playlist in filteredPlaylists"
            :key="playlist.id"
            :playlist="playlist as any"
            :current-user-id="currentUserId"
            :show-favorite="activeTab !== 'my'"
            @click="goToPlaylist as any"
            @edit="editPlaylist as any"
            @delete="deletePlaylist as any"
            @duplicate="duplicatePlaylist as any"
            @toggle-favorite="toggleFavorite as any"
            @toggle-privacy="togglePrivacy as any"
          />
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
      <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
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

      <!-- Edit Playlist Modal -->
      <EditPlaylistModal
        v-if="editingPlaylist && showEditModal"
        :show="showEditModal"
        :playlist="editingPlaylist"
        @close="closeEditModal"
        @saved="onPlaylistSaved"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'
import EditPlaylistModal from '@/components/modal/playlists/EditPlaylistModal.vue'
import type { Playlist } from '@/api/playlists'

interface Genre {
  id: number
  name: string
}

const router = useRouter()

// State
const playlists = ref<Playlist[]>([])
const genres = ref<Genre[]>([])
const loading = ref(false)
const error = ref('')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingPlaylist = ref<Playlist | null>(null)
const activeTab = ref('my')
const searchQuery = ref('')
const selectedGenre = ref('')
const selectedYear = ref('')
const sortBy = ref('created_at')
const currentPage = ref(1)
const totalPages = ref(1)
const currentUserId = ref<number | undefined>(undefined)

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
    // Загружаем user_id из localStorage
    const userStr = localStorage.getItem('user_id')
    if (userStr) {
      currentUserId.value = parseInt(userStr)
    }

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

const closeEditModal = () => {
  showEditModal.value = false
  editingPlaylist.value = null
}

const goToPlaylist = (playlist: Playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const editPlaylist = (playlist: Playlist) => {
  editingPlaylist.value = playlist
  showEditModal.value = true
}

const deletePlaylist = async (playlist: Playlist) => {
  if (!confirm('Удалить плейлист?')) return

  try {
    await apiClient.delete(`/playlists/playlists/${playlist.id}/`)
    playlists.value = playlists.value.filter(p => p.id !== playlist.id)
  } catch (err) {
    console.error('Error deleting playlist:', err)
    alert('Не удалось удалить плейлист')
  }
}

const duplicatePlaylist = async (playlist: Playlist) => {
  try {
    const response = await apiClient.post(`/playlists/playlists/${playlist.id}/duplicate/`)
    router.push(`/playlist/${response.data.id}`)
  } catch (err) {
    console.error('Error duplicating playlist:', err)
    alert('Не удалось скопировать плейлист')
  }
}

const toggleFavorite = async (playlist: Playlist) => {
  try {
    if (playlist.is_favorited) {
      await apiClient.delete(`/playlists/playlists/${playlist.id}/unfavorite/`)
      playlist.is_favorited = false
      playlist.favorites_count = Math.max(0, (playlist.favorites_count || 0) - 1)
    } else {
      await apiClient.post(`/playlists/playlists/${playlist.id}/favorite/`)
      playlist.is_favorited = true
      playlist.favorites_count = (playlist.favorites_count || 0) + 1
    }
  } catch (err) {
    console.error('Error toggling favorite:', err)
  }
}

const togglePrivacy = async (playlist: Playlist) => {
  try {
    const newPrivacy = !playlist.is_public
    await apiClient.patch(`/playlists/playlists/${playlist.id}/`, {
      is_public: newPrivacy
    })
    playlist.is_public = newPrivacy
  } catch (err) {
    console.error('Error toggling privacy:', err)
    alert('Не удалось изменить приватность')
  }
}

const onPlaylistSaved = (updatedPlaylist: Playlist) => {
  const index = playlists.value.findIndex(p => p.id === updatedPlaylist.id)
  if (index !== -1) {
    playlists.value[index] = updatedPlaylist
  }
  showEditModal.value = false
  editingPlaylist.value = null
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
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
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

  .playlists-view .page-header h1 {
    font-size: 1.5rem;
  }
}
</style>