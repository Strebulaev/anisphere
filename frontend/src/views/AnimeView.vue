<template>
  <div class="anime-view">
    <div class="container">
      <!-- Заголовок и поиск -->
      <div class="header-section">
        <div class="title-wrapper">
          <h1 class="main-title">Аниме</h1>
        </div>
        
        <!-- Поиск -->
        <div class="search-section">
          <div class="search-container">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8" stroke-width="2"/>
              <path stroke-width="2" d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              placeholder="Поиск аниме..."
              class="search-input"
            />
            <button @click="clearSearch" v-if="searchQuery" class="clear-search">✕</button>
          </div>
          
          <!-- Кнопки управления -->
          <div class="action-buttons">
            <button @click="refreshList" class="btn btn-outline refresh-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              <span>Обновить</span>
            </button>
            <button @click="showFilters = !showFilters" :class="['btn btn-outline', 'filter-toggle-btn', { active: showFilters }]">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
              </svg>
              <span>Фильтры</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Панель фильтров -->
      <transition name="filters">
        <div v-if="showFilters" class="filters-panel">
          <div class="filter-row">
            <div class="filter-group">
              <label>Статус:</label>
              <select v-model="selectedStatus" @change="applyFilters" class="filter-select">
                <option value="">Все статусы</option>
                <option value="ongoing">🔄 Онгоинг</option>
                <option value="finished">✅ Завершено</option>
                <option value="announced">📢 Анонсировано</option>
              </select>
            </div>
            
            <div class="filter-group">
              <label>Год:</label>
              <div class="year-range">
                <input
                  v-model="yearFrom"
                  @change="applyFilters"
                  type="number"
                  placeholder="От"
                  class="year-input"
                  min="1990"
                  max="2025"
                />
                <span class="year-separator">—</span>
                <input
                  v-model="yearTo"
                  @change="applyFilters"
                  type="number"
                  placeholder="До"
                  class="year-input"
                  min="1990"
                  max="2025"
                />
              </div>
            </div>
            
            <div class="filter-group">
              <label>Сортировка:</label>
              <select v-model="sortBy" @change="applyFilters" class="filter-select">
                <option value="-score">По рейтингу</option>
                <option value="-year">По году (новые)</option>
                <option value="title_ru">По названию (А-Я)</option>
                <option value="year">По году (старые)</option>
                <option value="score">По рейтингу (меньше)</option>
              </select>
            </div>
          </div>
          
          <!-- Жанры -->
          <div class="filter-row">
            <div class="filter-group full-width">
              <label>Жанры:</label>
              <div class="genres-grid">
                <label
                  v-for="genre in genres"
                  :key="genre.id"
                  :class="['genre-checkbox', { checked: selectedGenres.includes(genre.id) }]"
                >
                  <input
                    type="checkbox"
                    :value="genre.id"
                    v-model="selectedGenres"
                    @change="applyFilters"
                  />
                  <span class="genre-label">{{ genre.name }}</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="filter-actions">
            <button @click="clearFilters" class="btn btn-outline clear-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              Сбросить
            </button>
            <span class="results-count">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
              </svg>
              Найдено: <strong>{{ totalCount }}</strong>
            </span>
          </div>
        </div>
      </transition>
      
      <!-- Состояния загрузки -->
      <div v-if="loading" class="loading-state">
        <div class="spinner-container">
          <div class="spinner"></div>
          <div class="spinner-ring"></div>
        </div>
        <p>Загрузка аниме...</p>
      </div>
      
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p class="error-message">{{ error }}</p>
        <button @click="refreshList" class="btn btn-primary retry-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          Попробовать снова
        </button>
      </div>
      
      <!-- Список аниме -->
      <div v-else class="anime-grid">
          <AnimeCard
            v-for="anime in animes"
            :key="anime.id"
            :anime="anime"
            @click="goToDetail(anime as Anime)"
            @watch="startWatching(anime as Anime)"
          />
      </div>
      
      <!-- Пагинация -->
      <div v-if="totalPages > 1 && !searchQuery" class="pagination">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage <= 1"
          class="pagination-btn prev-btn"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Назад
        </button>
        
        <div class="pagination-pages">
          <span class="pagination-info">
            Страница <strong>{{ currentPage }}</strong> из <strong>{{ totalPages }}</strong>
          </span>
        </div>
        
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="pagination-btn next-btn"
        >
          Далее
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
      
      <!-- Плеер для просмотра -->
      <AnimePlayer
        :show="showPlayer"
        :anime="selectedAnime"
        :initial-episode="selectedEpisode"
        @close="closePlayer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import type { Anime, Genre } from '@/types'

// Импортируем компоненты
import NavBar from '@/components/NavBar.vue'
import AnimeCard from '@/components/AnimeCard.vue'
import AnimePlayer from '@/components/AnimePlayer.vue'

/* Added interfaces */
interface AnimeData {
  id: number
  title_ru: string
  title_en: string
  title_jp: string
  poster_url: string
  poster_file: string | null
  description?: string
  year: number | null
  status: string
  episodes: number | null
  genres: Genre[]
  created_at: string
  score?: number
  favorites?: number
}

interface AnimeFilters {
  genre?: string
  year?: string
  status?: string
  search?: string
}

const router = useRouter()

// Состояние
const animes = ref<Anime[]>([])
const genres = ref<Genre[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')

// Фильтры
const showFilters = ref(false)
const selectedStatus = ref('')
const selectedGenres = ref<number[]>([])
const yearFrom = ref('')
const yearTo = ref('')
const sortBy = ref('-score')

// Пагинация
const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const itemsPerPage = ref(20)

// Плеер
const showPlayer = ref(false)
const selectedAnime = ref<Anime | null>(null)
const selectedEpisode = ref(1)

// Вычисляемые свойства
const hasActiveFilters = computed(() => {
  return !!(
    searchQuery.value ||
    selectedStatus.value ||
    selectedGenres.value.length > 0 ||
    yearFrom.value ||
    yearTo.value ||
    sortBy.value !== '-score'
  )
})

// Функции загрузки данных
const loadGenres = async () => {
  try {
    const response = await apiClient.get('/anime/genres/')
    genres.value = response.data.genres || []
  } catch (err) {
    console.error('Не удалось загрузить жанры:', err)
  }
}

const loadAnimes = async () => {
  loading.value = true
  error.value = null
  console.log('Загружаем аниме...')
  
  try {
    const params: any = {
      page: currentPage.value,
      page_size: itemsPerPage.value,
      ordering: sortBy.value
    }
    
    // Добавляем фильтры
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    if (selectedStatus.value) {
      params.status = selectedStatus.value
    }
    
    if (selectedGenres.value.length > 0) {
      params.genres = selectedGenres.value.join(',')
    }
    
    if (yearFrom.value) {
      params.year_from = yearFrom.value
    }
    
    if (yearTo.value) {
      params.year_to = yearTo.value
    }
    
    console.log('Параметры запроса:', params)
    
    // Используем правильный URL для аниме API
    const response = await apiClient.get('/anime/anime/', { params })
    console.log('Ответ от API:', response.data)
    
    if (response.data && Array.isArray(response.data.results)) {
      animes.value = response.data.results
      totalPages.value = response.data.total_pages || 1
      totalCount.value = response.data.count || response.data.results.length
      console.log('Загружено аниме:', animes.value.length)
      
      if (animes.value.length === 0) {
        error.value = 'Аниме не найдено. Попробуйте изменить параметры фильтрации.'
      }
    } else if (Array.isArray(response.data)) {
      animes.value = response.data
      totalPages.value = 1
      totalCount.value = animes.value.length
      console.log('Загружен массив аниме:', animes.value.length)
    } else {
      console.warn('Неожиданная структура ответа:', response.data)
      animes.value = []
      error.value = 'Неожиданная структура данных от сервера'
    }
    
  } catch (err: any) {
    console.error('Ошибка загрузки аниме:', err)
    
    if (err.response?.status === 404) {
      error.value = 'API аниме не найден. Проверьте настройки сервера.'
    } else if (err.response?.status >= 500) {
      error.value = 'Ошибка сервера. Попробуйте позже.'
    } else if (err.code === 'NETWORK_ERROR' || err.message?.includes('Network Error')) {
      error.value = 'Ошибка сети. Проверьте подключение к интернету.'
    } else {
      error.value = err.response?.data?.detail || err.message || 'Не удалось загрузить аниме'
    }
    
    animes.value = []
  } finally {
    loading.value = false
  }
}

// Обработчики поиска и фильтрации
let searchTimeout: number | undefined

const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  searchTimeout = window.setTimeout(() => {
    currentPage.value = 1
      loadAnimes()
  }, 300)
}

const applyFilters = () => {
  currentPage.value = 1
  loadAnimes()
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedStatus.value = ''
  selectedGenres.value = []
  yearFrom.value = ''
  yearTo.value = ''
  sortBy.value = '-score'
  currentPage.value = 1
  loadAnimes()
}

const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  loadAnimes()
}

// Пагинация
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadAnimes()
    // Прокрутка к началу списка
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// Обновление списка
const refreshList = () => {
  loadAnimes()
}

// Навигация
const goToDetail = (anime: Anime) => {
  router.push(`/anime/${anime.id}`)
}

// Просмотр
const startWatching = (anime: Anime) => {
  selectedAnime.value = anime
  selectedEpisode.value = 1
  showPlayer.value = true
}

const closePlayer = () => {
  showPlayer.value = false
  selectedAnime.value = null
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadGenres(),
    loadAnimes()
  ])
})

// Следим за изменениями сортировки
watch(sortBy, () => {
  if (animes.value.length > 0) {
    applyFilters()
  }
})
</script>

<style scoped>
.anime-view {
  min-height: 100vh;
  background-color: var(--color-background);
  padding: 2rem 1rem 4rem;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
}

/* Header Section */
.header-section {
  background-color: var(--color-background-surface);
  border-radius: 1.5rem;
  padding: 2rem;
  margin-bottom: 2rem;
  border: 1px solid var(--color-divider);
}

.title-wrapper {
  margin-bottom: 1.5rem;
  text-align: center;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--color-text);
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Search Section */
.search-section {
  display: flex;
  gap: 1rem;
  align-items: stretch;
  flex-wrap: wrap;
}

.search-container {
  flex: 1;
  min-width: 300px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.875rem 3rem 0.875rem 3rem;
  border: 2px solid var(--color-divider-light);
  border-radius: 1rem;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
  background-color: var(--color-background-active);
  color: var(--color-text);
}

.search-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 4px rgba(58, 134, 255, 0.1);
  background-color: var(--color-background-surface);
}

.clear-search {
  position: absolute;
  right: 0.75rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 0.5rem;
  background-color: var(--color-background-active);
  color: var(--color-text-tertiary);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-search:hover {
  background-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.75rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border: 2px solid;
  border-radius: 1rem;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-outline {
  background-color: var(--color-background-surface);
  border-color: var(--color-divider-light);
  color: var(--color-text-primary);
}

.btn-outline:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(58, 134, 255, 0.2);
}

.filter-toggle-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(58, 134, 255, 0.4);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* Filters Panel */
.filters-panel {
  background-color: var(--color-background-surface);
  border-radius: 1.5rem;
  padding: 1.75rem;
  margin-bottom: 2rem;
  border: 1px solid var(--color-divider);
}

.filters-enter-active,
.filters-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.filters-enter-from,
.filters-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}

/* Filter Row */
.filter-row {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

/* Filter Group */
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

/* Filter Group full width */
.filter-group.full-width {
  flex: 1;
  min-width: 100%;
}

/* Filter Group label */
.filter-group label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Filter Select */
.filter-select {
  padding: 0.875rem 1.25rem;
  border: 2px solid var(--color-divider-light);
  border-radius: 0.875rem;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s ease;
  background-color: var(--color-background-active);
  min-width: 220px;
  cursor: pointer;
  font-weight: 600;
  color: var(--color-text);
}

.filter-select:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 4px rgba(58, 134, 255, 0.15);
  background-color: var(--color-background-surface);
}

/* Year Range */
.year-range {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Year Input */
.year-input {
  width: 110px;
  padding: 0.875rem;
  border: 2px solid var(--color-divider-light);
  border-radius: 0.875rem;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s ease;
  text-align: center;
  font-weight: 600;
  color: var(--color-text);
  background-color: var(--color-background-active);
}

/* Year Input focus */
.year-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 4px rgba(58, 134, 255, 0.15);
  background-color: var(--color-background-surface);
}

/* Year Separator */
.year-separator {
  color: var(--color-text-tertiary);
  font-weight: 700;
  font-size: 1.25rem;
}

/* Genres Grid */
.genres-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}

/* Genre Checkbox */
.genre-checkbox {
  position: relative;
  cursor: pointer;
  user-select: none;
}

/* Genre Checkbox input */
.genre-checkbox input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

/* Genre Label */
.genre-label {
  display: block;
  padding: 0.75rem 1rem;
  background-color: var(--color-background-active);
  border: 2px solid var(--color-divider-light);
  border-radius: 0.875rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Genre Checkbox checked */
.genre-checkbox input:checked + .genre-label,
.genre-checkbox.checked .genre-label {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(58, 134, 255, 0.4);
}

/* Genre Checkbox hover */
.genre-checkbox:hover .genre-label {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.2);
}

/* Genre Checkbox checked hover */
.genre-checkbox input:checked:hover + .genre-label {
  transform: scale(1.05);
}

/* Filter Actions */
.filter-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1.75rem;
  border-top: 2px solid var(--color-divider);
}

/* Clear Button */
.clear-btn {
  padding: 0.75rem 1.5rem;
  background-color: rgba(255, 42, 109, 0.1);
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
  font-weight: 700;
}

/* Clear Button hover */
.clear-btn:hover {
  background-color: rgba(255, 42, 109, 0.2);
  border-color: var(--color-accent-pink);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 42, 109, 0.3);
}

/* Results Count */
.results-count {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 600;
  padding: 0.75rem 1.25rem;
  background-color: var(--color-background-active);
  border-radius: 0.875rem;
}

/* Results Count strong */
.results-count strong {
  color: var(--color-accent);
  font-weight: 800;
  font-size: 1.125rem;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  background-color: var(--color-background-surface);
  border-radius: 1.5rem;
  border: 1px solid var(--color-divider);
}

.spinner-container {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
}

.spinner {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring {
  position: absolute;
  width: 70%;
  height: 70%;
  top: 15%;
  left: 15%;
  border: 4px solid transparent;
  border-top-color: var(--color-accent-pink);
  border-radius: 50%;
  animation: spin 1.5s linear infinite reverse;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Error State */
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  background-color: var(--color-background-surface);
  border-radius: 1.5rem;
  border: 1px solid var(--color-divider);
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-message {
  font-size: 1.125rem;
  color: var(--color-accent-pink);
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.retry-btn {
  padding: 0.875rem 2rem;
}

/* Anime Grid - 4 карточки в строку */
.anime-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.25rem;
  margin-top: 2.5rem;
  padding: 1.75rem;
  background-color: var(--color-background-surface);
  border-radius: 1.25rem;
  border: 1px solid var(--color-divider);
}

.pagination-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.875rem 1.75rem;
  background-color: var(--color-accent);
  border: none;
  border-radius: 0.875rem;
  color: var(--color-text);
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(58, 134, 255, 0.3);
}

.pagination-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(58, 134, 255, 0.4);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.pagination-pages {
  flex: 1;
  text-align: center;
}

.pagination-info {
  font-size: 1.0625rem;
  color: var(--color-text-primary);
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  background-color: var(--color-background-active);
  border-radius: 0.875rem;
  display: inline-block;
}

.pagination-info strong {
  color: var(--color-accent);
  font-weight: 800;
  font-size: 1.125rem;
}

/* Responsive */
@media (max-width: 768px) {
  .anime-view {
    padding: 1rem 0.5rem 3rem;
  }
  
  .header-section {
    padding: 1.5rem;
    border-radius: 1.25rem;
  }
  
  .main-title {
    font-size: 2rem;
  }
  .subtitle {
    font-size: 0.9rem;
  }
  .search-section {
    flex-direction: column;
  }
  .search-container {
    min-width: 100%;
  }
  .action-buttons {
    width: 100%;
  }
  .btn {
    flex: 1;
    justify-content: center;
  }
  
  .filters-panel {
    padding: 1.25rem;
    border-radius: 1.25rem;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-select,
  .year-input {
    width: 100%;
  }
  
  .filter-actions {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .results-count {
    justify-content: center;
  }
  
  /* На мобильных - 2 карточки в строку */
  .anime-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .pagination {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
  }
  
  .pagination-pages {
    order: -1;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  /* На планшетах - 3 карточки в строку */
  .anime-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
