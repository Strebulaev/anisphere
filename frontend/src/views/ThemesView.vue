<template>
  <div class="themes-page">
    <div class="themes-header">
      <h1>Опенинги и Эндинги</h1>
      <p class="themes-subtitle">Ваши избранные опенинги и эндинги для скачивания</p>
    </div>

    <!-- Фильтры -->
    <div class="themes-filters">
      <button 
        v-for="filter in filters" 
        :key="filter.value"
        :class="['filter-btn', { active: activeFilter === filter.value }]"
        @click="activeFilter = filter.value"
      >
        {{ filter.label }}
      </button>
    </div>

    <!-- Список -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="filteredThemes.length === 0" class="empty-state">
      <div class="empty-icon">🎵</div>
      <h3>Пока ничего нет</h3>
      <p>Добавляйте опенинги и эндинги в избранное на странице просмотра аниме</p>
      <router-link to="/anime" class="btn-primary">Смотреть аниме</router-link>
    </div>

    <div v-else class="themes-grid">
      <div 
        v-for="theme in filteredThemes" 
        :key="theme.id" 
        class="theme-card"
      >
        <div class="theme-poster">
          <img 
            v-if="theme.anime_poster" 
            :src="getPosterUrl(theme.anime_poster)" 
            :alt="theme.anime_title_ru || theme.anime_title_en"
          />
          <div v-else class="poster-placeholder">🎬</div>
          
          <!-- Бейдж типа -->
          <span class="theme-type-badge" :class="theme.theme_type">
            {{ theme.theme_type === 'opening' ? 'OP' : 'ED' }}
          </span>
        </div>

        <div class="theme-info">
          <router-link :to="`/anime/${theme.anime}/watch`" class="theme-anime-title">
            {{ theme.anime_title_ru || theme.anime_title_en || 'Аниме' }}
          </router-link>
          
          <div class="theme-meta">
            <span v-if="theme.episode">Серия {{ theme.episode }}</span>
            <span v-if="theme.season > 1">Сезон {{ theme.season }}</span>
          </div>

          <!-- Дата добавления -->
          <div class="theme-added-date" v-if="theme.added_at">
            Добавлено: {{ formatDate(theme.added_at) }}
          </div>

          <!-- Тип (опенинг/эндинг) -->
          <div class="theme-kind">
            {{ theme.theme_type === 'opening' ? 'Опенинг' : 'Эндинг' }}
          </div>

          <div class="theme-actions">
            <!-- Кнопка скачивания с выпадающим меню -->
            <div class="download-dropdown">
              <button 
                class="action-btn download-btn"
                :class="{ loading: downloadingId === theme.id, done: downloadDoneId === theme.id }"
                :disabled="downloadingId === theme.id"
                @click="toggleDownloadMenu(theme.id)"
                title="Скачать"
              >
                <span v-if="downloadingId === theme.id" class="btn-spinner"></span>
                <svg v-else-if="downloadDoneId === theme.id" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                <span>Скачать</span>
              </button>
              
              <!-- Выпадающее меню -->
              <div v-if="activeDownloadMenu === theme.id" class="download-menu" @click.stop>
                <button class="dm-item" @click="downloadTheme(theme, 'video')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="3" width="20" height="14" rx="2"/><polygon points="10 8 16 11 10 14 10 8"/>
                  </svg>
                  <span>Видео (MP4)</span>
                </button>
                <button class="dm-item" @click="downloadTheme(theme, 'audio')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
                  </svg>
                  <span>Аудио (MP3)</span>
                </button>
              </div>
            </div>

            <!-- Удалить из избранного -->
            <button 
              class="action-btn delete-btn"
              @click="removeFromFavorites(theme)"
              title="Удалить из избранного"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>

          <p v-if="downloadError" class="error-text">{{ downloadError }}</p>
        </div>
      </div>
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        class="page-btn" 
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        ← Назад
      </button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button 
        class="page-btn" 
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        Вперёд →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'
import { getMediaUrl } from '@/api/client'
import { useToast } from '@/composables/useToast'

interface Theme {
  id: number
  anime: number
  anime_title_ru: string
  anime_title_en: string
  anime_poster?: string
  theme_type: 'opening' | 'ending'
  episode: number
  season: number
  added_at: string
}

const authStore = useAuthStore()
const toast = useToast()

// Состояние
const themes = ref<Theme[]>([])
const loading = ref(true)
const activeFilter = ref<'all' | 'opening' | 'ending'>('all')
const currentPage = ref(1)
const totalPages = ref(1)
const downloadingId = ref<number | null>(null)
const downloadDoneId = ref<number | null>(null)
const downloadError = ref('')
const activeDownloadMenu = ref<number | null>(null)

const filters: { value: 'all' | 'opening' | 'ending', label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'opening', label: 'Опенинги' },
  { value: 'ending', label: 'Эндинги' }
]

// Вычисляемые
const filteredThemes = computed(() => {
  if (activeFilter.value === 'all') return themes.value
  return themes.value.filter(t => t.theme_type === activeFilter.value)
})

// Получить URL постера
const getPosterUrl = (url?: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return getMediaUrl(url) || url
}

// Форматировать дату
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Переключить меню скачивания
const toggleDownloadMenu = (themeId: number) => {
  if (activeDownloadMenu.value === themeId) {
    activeDownloadMenu.value = null
  } else {
    activeDownloadMenu.value = themeId
  }
}

// Закрыть меню при клике вне
const closeDownloadMenu = () => {
  activeDownloadMenu.value = null
}

onMounted(() => {
  document.addEventListener('click', closeDownloadMenu)
  loadFavorites()
})

onUnmounted(() => {
  document.removeEventListener('click', closeDownloadMenu)
})

// Загрузка избранных тем
const loadFavorites = async () => {
  if (!authStore.isAuthenticated) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const response = await apiClient.get('/users/favorite_themes/', {
      params: {
        page: currentPage.value,
        page_size: 20
      }
    })
    themes.value = response.data.results || []
    totalPages.value = Math.ceil((response.data.count || 0) / 20)
  } catch (err) {
    console.error('Ошибка загрузки избранного:', err)
    toast.error('Не удалось загрузить избранное')
  } finally {
    loading.value = false
  }
}

// Скачивание темы
const downloadTheme = async (theme: Theme, format: 'video' | 'audio') => {
  if (!theme.anime) return

  activeDownloadMenu.value = null
  downloadingId.value = theme.id
  downloadError.value = ''

  const isAudio = format === 'audio'
  const ext = isAudio ? 'mp3' : 'mp4'

  try {
    const params: Record<string, string> = {
      episode: String(theme.episode),
      season: String(theme.season || 1),
    }

    // Для аудио получаем тайминги темы
    if (isAudio) {
      const themeRes = await apiClient.get(`/anime/${theme.anime}/themes/`, {
        params: { episode: params.episode, season: params.season }
      })
      const themeData = themeRes.data?.[theme.theme_type]
      
      if (themeData && themeData.start != null && themeData.stop != null) {
        params.start = String(Math.floor(themeData.start))
        params.end = String(Math.ceil(themeData.stop))
      } else {
        params.start = '0'
        params.end = '99999'
      }
      params.label = theme.theme_type === 'opening' ? 'Opening' : 'Ending'
      params.format = 'audio'
    }

    const response = await apiClient.get(`/anime/${theme.anime}/clip/`, {
      params,
      responseType: 'blob',
      timeout: 360_000,
    })

    const animeTitle = theme.anime_title_ru || theme.anime_title_en || 'anime'
    const label = isAudio 
      ? (theme.theme_type === 'opening' ? 'Opening' : 'Ending')
      : `Ep${theme.episode}`
    
    const disposition = response.headers['content-disposition'] || ''
    let filename = `${animeTitle} - ${label}.${ext}`
    const fnMatch = disposition.match(/filename\*=UTF-8''([^;\n]+)/) || disposition.match(/filename="?([^";\n]+)"?/)
    if (fnMatch) filename = decodeURIComponent(fnMatch[1])

    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 5000)

    downloadDoneId.value = theme.id
    setTimeout(() => {
      downloadDoneId.value = null
    }, 3000)

  } catch (err: any) {
    console.error('Ошибка скачивания:', err)
    downloadError.value = err?.message || 'Ошибка скачивания'
  } finally {
    downloadingId.value = null
  }
}

// Удаление из избранного
const removeFromFavorites = async (theme: Theme) => {
  try {
    await apiClient.delete(`/users/favorite_themes/${theme.id}/`)
    themes.value = themes.value.filter(t => t.id !== theme.id)
    toast.success('Удалено из избранного')
  } catch (err) {
    console.error('Ошибка удаления:', err)
    toast.error('Не удалось удалить')
  }
}

// Пагинация
const changePage = (page: number) => {
  currentPage.value = page
  loadFavorites()
}

// Watch для фильтра
watch(activeFilter, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.themes-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.themes-header {
  margin-bottom: 2rem;
}

.themes-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary, #fff);
  margin: 0 0 0.5rem;
}

.themes-subtitle {
  color: var(--text-secondary, #888);
  font-size: 0.9rem;
  margin: 0;
}

/* Фильтры */
.themes-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: var(--surface-3, #2a2a2a);
  border: 1px solid var(--border-subtle, #333);
  border-radius: 6px;
  color: var(--text-secondary, #aaa);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: var(--surface-4, #333);
}

.filter-btn.active {
  background: var(--accent, #3b82f6);
  border-color: var(--accent, #3b82f6);
  color: #fff;
}

/* Загрузка */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
  color: var(--text-secondary, #888);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--accent, #3b82f6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Пустое состояние */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--surface-2, #1f1f1f);
  border-radius: 12px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.25rem;
  color: var(--text-primary, #fff);
  margin: 0 0 0.5rem;
}

.empty-state p {
  color: var(--text-secondary, #888);
  margin: 0 0 1.5rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--accent, #3b82f6);
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

/* Сетка карточек */
.themes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.theme-card {
  background: var(--surface-2, #1f1f1f);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-subtle, #333);
  transition: transform 0.2s, box-shadow 0.2s;
}

.theme-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.theme-poster {
  position: relative;
  aspect-ratio: 16/9;
  background: var(--surface-3, #2a2a2a);
  overflow: hidden;
}

.theme-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: var(--text-tertiary, #555);
}

.theme-type-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.theme-type-badge.opening {
  background: rgba(59, 130, 246, 0.9);
  color: #fff;
}

.theme-type-badge.ending {
  background: rgba(168, 85, 247, 0.9);
  color: #fff;
}

.theme-info {
  padding: 1rem;
}

.theme-anime-title {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #fff);
  text-decoration: none;
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.theme-anime-title:hover {
  color: var(--accent, #3b82f6);
}

.theme-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-tertiary, #777);
  margin-bottom: 1rem;
}

.theme-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background: var(--surface-3, #2a2a2a);
  border: 1px solid var(--border-subtle, #333);
  border-radius: 6px;
  color: var(--text-secondary, #aaa);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: var(--surface-4, #333);
  color: #fff;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.download-btn.loading,
.audio-btn.loading {
  pointer-events: none;
}

.download-btn.done,
.audio-btn.done {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.4);
  color: #22c55e;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #ef4444;
}

.btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.error-text {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #ef4444;
}

/* Выпадающее меню скачивания */
.download-dropdown {
  position: relative;
}

.download-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: var(--surface-2, #1f1f1f);
  border: 1px solid var(--border-subtle, #333);
  border-radius: 8px;
  overflow: hidden;
  z-index: 50;
  min-width: 150px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.dm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: none;
  color: var(--text-secondary, #aaa);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.dm-item:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #fff;
}

.dm-item svg {
  flex-shrink: 0;
  color: #8b5cf6;
}

/* Дата добавления и тип */
.theme-added-date {
  font-size: 0.7rem;
  color: var(--text-tertiary, #777);
  margin-bottom: 0.25rem;
}

.theme-kind {
  font-size: 0.75rem;
  color: var(--accent, #3b82f6);
  font-weight: 500;
  margin-bottom: 0.5rem;
}

/* Пагинация */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.5rem 1rem;
  background: var(--surface-3, #2a2a2a);
  border: 1px solid var(--border-subtle, #333);
  border-radius: 6px;
  color: var(--text-primary, #fff);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--surface-4, #333);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  color: var(--text-secondary, #888);
  font-size: 0.875rem;
}
</style>
