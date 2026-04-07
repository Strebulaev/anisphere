<template>
  <div class="anime-selector">
    <!-- Поиск -->
    <div class="search-section">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск аниме..."
        class="search-input"
        @input="onSearch"
      >
    </div>

    <!-- Вкладки -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="switchTab(tab.id)"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- Контент вкладок -->
    <div class="tab-content">
      <!-- Поиск -->
      <div v-if="activeTab === 'search'" class="tab-panel">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          <span>Загрузка...</span>
        </div>
        <div v-else-if="displayItems.length === 0" class="empty">
          <span v-if="searchQuery">Ничего не найдено</span>
          <span v-else>Введите название для поиска</span>
        </div>
        <div v-else class="items-grid">
          <div
            v-for="anime in displayItems"
            :key="anime.id"
            :class="['anime-card', { selected: isSelected(anime.id) }]"
            @click="toggleSelect(anime)"
          >
            <div class="card-check">{{ isSelected(anime.id) ? '✓' : '' }}</div>
            <img
              v-if="anime.poster"
              :src="anime.poster"
              :alt="anime.title_ru || anime.title"
              class="card-poster"
              @error="handleImageError"
            >
            <div class="card-poster-placeholder" v-else> <SakuraIcon name="play" /> </div>
            <div class="card-info">
              <div class="card-title">{{ anime.title_ru || anime.title }}</div>
              <div class="card-meta">
                <span v-if="anime.score"><SakuraIcon name="star" /> {{ anime.score }}</span>
                <span v-if="anime.kind">{{ formatKind(anime.kind) }}</span>
              </div>
            </div>
          </div>
        </div>
        <button v-if="hasMore && !isLoading" class="load-more" @click="loadMore">
          Загрузить ещё
        </button>
      </div>

      <!-- Коллекция -->
      <div v-else-if="activeTab === 'collection'" class="tab-panel">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          <span>Загрузка коллекции...</span>
        </div>
        <div v-else-if="displayItems.length === 0" class="empty">
          <span>В коллекции пусто</span>
          <p>Добавьте аниме в коллекцию</p>
        </div>
        <div v-else class="items-grid">
          <div
            v-for="anime in displayItems"
            :key="anime.id"
            :class="['anime-card', { selected: isSelected(anime.id) }]"
            @click="toggleSelect(anime)"
          >
            <div class="card-check">{{ isSelected(anime.id) ? '✓' : '' }}</div>
            <img
              v-if="anime.poster"
              :src="anime.poster"
              :alt="anime.title_ru || anime.title || 'Аниме'"
              class="card-poster"
              @error="handleImageError"
            >
            <div class="card-poster-placeholder" v-else> <SakuraIcon name="play" /> </div>
            <div class="card-info">
              <div class="card-title">{{ anime.title_ru || anime.title }}</div>
              <div class="card-meta">
                <span v-if="anime.score"><SakuraIcon name="star" /> {{ anime.score }}</span>
                <span v-if="anime.status" class="status-badge" :class="anime.status">{{ formatStatus(anime.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Плейлисты -->
      <div v-else-if="activeTab === 'playlists'" class="tab-panel">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          <span>Загрузка плейлистов...</span>
        </div>
        <div v-else-if="playlists.length === 0" class="empty">
          <span>Нет плейлистов</span>
          <p>Создайте плейлист для добавления сюда</p>
        </div>
        <div v-else class="playlists-list">
          <div
            v-for="playlist in playlists"
            :key="playlist.id"
            class="playlist-item"
            @click="loadPlaylistItems(Number(playlist.id))"
          >
            <span class="playlist-icon"> <SakuraIcon name="clipboard" /> </span>
              <div class="playlist-info">
              <!-- Используем title вместо name -->
              <div class="playlist-name">{{ playlist.title || 'Без названия' }}</div>
              <div class="playlist-count">{{ playlist.items_count || 0 }} аниме</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Избранное -->
      <div v-else-if="activeTab === 'favorites'" class="tab-panel">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          <span>Загрузка избранного...</span>
        </div>
        <div v-else-if="displayItems.length === 0" class="empty">
          <span>Избранное пусто</span>
        </div>
        <div v-else class="items-grid">
          <div
            v-for="anime in displayItems"
            :key="anime.id"
            :class="['anime-card', { selected: isSelected(anime.id) }]"
            @click="toggleSelect(anime)"
          >
            <div class="card-check">{{ isSelected(anime.id) ? '✓' : '' }}</div>
            <img
              v-if="anime.poster"
              :src="anime.poster"
              :alt="anime.title_ru || anime.title"
              class="card-poster"
              @error="handleImageError"
            >
            <div class="card-poster-placeholder" v-else> <SakuraIcon name="play" /> </div>
            <div class="card-info">
              <div class="card-title">{{ anime.title_ru || anime.title }}</div>
              <div class="card-meta">
                <span v-if="anime.score"><SakuraIcon name="star" /> {{ anime.score }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Выбранные элементы -->
    <div v-if="selectedItems.length > 0" class="selection-bar">
      <span>Выбрано: {{ selectedItems.length }}</span>
      <div class="selection-actions">
        <button class="btn-action" @click="selectAllVisible">Выбрать все</button>
        <button class="btn-action btn-clear" @click="clearSelection">Очистить</button>
      </div>
    </div>

    <!-- Кнопка добавления -->
    <!-- <div class="add-bar">
      <button
        class="btn-add"
        :disabled="selectedItems.length === 0"
        @click="addSelected"
      >
        <SakuraIcon name="plus" /> Добавить в колесо ({{ selectedItems.length }})
      </button>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { animeApi } from '@/api/anime'
import playlistsApi from '@/api/playlists'
import { libraryApi, type LibraryItem } from '@/api/library'
import { useToast } from '@/composables/useToast'

interface AnimeItem {
  id: number
  title?: string
  title_ru?: string
  poster?: string | null
  score?: number | null
  kind?: string
  status?: string
}

const props = defineProps<{
  currentItems?: Array<{ anime_id: number }>
}>()

const emit = defineEmits<{
  add: [items: Array<{ anime_id: number; anime_title: string; anime_poster?: string; weight: number }>]
}>()

const toast = useToast()

const tabs = [
  { id: 'search', label: 'Поиск', icon: '🔎' },
  { id: 'collection', label: 'Коллекция', icon: '📖' },
  { id: 'playlists', label: 'Плейлисты', icon: '📋' },
  { id: 'favorites', label: 'Избранное', icon: '🌠' }
]

const activeTab = ref('search')
const searchQuery = ref('')
const items = ref<AnimeItem[]>([])
const selectedItems = ref<AnimeItem[]>([])
const playlists = ref<Array<{ id: number; title: string; items_count: number }>>([])
const isLoading = ref(false)
const hasMore = ref(false)
const currentPage = ref(1)

// IDs уже добавленных аниме
const currentIds = computed(() => new Set((props.currentItems || []).map(i => i.anime_id)))

// Отображаемые элементы (без уже добавленных)
const displayItems = computed(() => 
  items.value.filter(item => !currentIds.value.has(item.id))
)

// Обработка ошибки изображения
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

// Переключение вкладки
const switchTab = async (tabId: string) => {
  activeTab.value = tabId
  selectedItems.value = []
  currentPage.value = 1
  items.value = []

  switch (tabId) {
    case 'search':
      if (searchQuery.value) {
        await search()
      } else {
        await loadPopular()
      }
      break
    case 'collection':
      await loadCollection()
      break
    case 'playlists':
      await loadPlaylists()
      break
    case 'favorites':
      await loadFavorites()
      break
  }
}

// Поиск
const onSearch = async () => {
  if (activeTab.value !== 'search') {
    activeTab.value = 'search'
  }
  
  if (searchQuery.value.length < 2) {
    items.value = []
    return
  }

  await search()
}

const search = async () => {
  isLoading.value = true
  try {
    const data = await animeApi.search(searchQuery.value)
    items.value = (data.results || []).map((anime): AnimeItem => ({
      id: anime.id,
      title_ru: anime.title_ru,
      title: anime.title_en,
      poster: anime.poster_url || anime.poster_image_url || null,
      score: anime.score ?? null,
      kind: undefined,
      status: undefined
    }))
    hasMore.value = data.total > (data.results?.length || 0)
    currentPage.value = 1
  } catch (error) {
    console.error('Search failed:', error)
    toast.error('Ошибка поиска')
  } finally {
    isLoading.value = false
  }
}

// Загрузка популярных
const loadPopular = async () => {
  isLoading.value = true
  try {
    const data = await animeApi.list({ page_size: 30, ordering: '-score' })
    items.value = (data.results || []).map((anime): AnimeItem => ({
      id: anime.id,
      title_ru: anime.title_ru,
      title: anime.title_en,
      poster: anime.poster_url || anime.poster_image_url || null,
      score: anime.score ?? null,
      kind: undefined,
      status: undefined
    }))
  } catch (error) {
    console.error('Load popular failed:', error)
  } finally {
    isLoading.value = false
  }
}

// Загрузка коллекции из library API
const loadCollection = async () => {
  isLoading.value = true
  try {
    const libraryItems = await libraryApi.getLibrary({})
    // API может вернуть массив или объект { results: [], count: N }
    const libraryData = Array.isArray(libraryItems) ? libraryItems : libraryItems.results || []
    items.value = libraryData.map((item: LibraryItem) => ({
      id: typeof item.anime === 'number' ? item.anime : item.anime.id,
      title_ru: item.anime_title_ru,
      title: item.anime_title_en,
      poster: item.anime_poster,
      score: item.rating,
      status: item.status
    }))
  } catch (error) {
    console.error('Load collection failed:', error)
    // Fallback - загружаем популярные
    await loadPopular()
  } finally {
    isLoading.value = false
  }
}

// Загрузка плейлистов
const loadPlaylists = async () => {
  isLoading.value = true
  try {
    const { data } = await playlistsApi.getMyPlaylists()
    playlists.value = data || []
  } catch (error) {
    console.error('Load playlists failed:', error)
    playlists.value = []
  } finally {
    isLoading.value = false
  }
}

// Загрузка элементов плейлиста
const loadPlaylistItems = async (playlistId: number | string) => {
  const id = typeof playlistId === 'string' ? Number(playlistId) : playlistId
  isLoading.value = true
  try {
    const { data } = await playlistsApi.getPlaylist(id)
    items.value = (data?.items || []).map((item): AnimeItem => ({
      id: item.anime_id,
      title_ru: item.anime_title,
      title: item.anime_title_en,
      poster: item.anime_poster_url || item.anime_poster || null,
      score: item.anime_score ?? null,
      kind: item.anime_kind
    }))
    activeTab.value = 'search' // Показываем как результаты поиска
  } catch (error) {
    console.error('Load playlist items failed:', error)
    toast.error('Ошибка загрузки плейлиста')
  } finally {
    isLoading.value = false
  }
}

// Загрузка избранного - из library с is_favorite
const loadFavorites = async () => {
  isLoading.value = true
  try {
    // Загружаем избранное из library
    const libraryItems = await libraryApi.getLibrary({ is_favorite: true })
    // API может вернуть массив или объект { results: [], count: N }
    const libraryData = Array.isArray(libraryItems) ? libraryItems : libraryItems.results || []
    items.value = libraryData.map((item: LibraryItem) => ({
      id: typeof item.anime === 'number' ? item.anime : item.anime.id,
      title_ru: item.anime_title_ru,
      title: item.anime_title_en,
      poster: item.anime_poster,
      score: item.rating
    }))
    
    // Если пусто, пробуем из playlists/favorites
    if (items.value.length === 0) {
      const { data } = await playlistsApi.getFavoriteAnime()
      items.value = (data || []).map((item) => ({
        id: item.anime,
        title_ru: item.anime_title,
        title: item.anime_data?.title_en,
        poster: item.anime_poster || item.anime_data?.poster_url,
        score: item.anime_data?.score
      }))
    }
  } catch (error) {
    console.error('Load favorites failed:', error)
    // Fallback - загружаем популярные
    await loadPopular()
  } finally {
    isLoading.value = false
  }
}

// Загрузить ещё
const loadMore = async () => {
  if (!hasMore.value || isLoading.value) return

  isLoading.value = true
  currentPage.value++

  try {
    const data = await animeApi.search(searchQuery.value, { limit: 30 })
    const newItems = (data.results || []).map((anime): AnimeItem => ({
      id: anime.id,
      title_ru: anime.title_ru,
      title: anime.title_en,
      poster: anime.poster_url || anime.poster_image_url || null,
      score: anime.score ?? null,
      kind: undefined,
      status: undefined
    }))
    items.value = [...items.value, ...newItems]
    hasMore.value = data.total > items.value.length
  } catch (error) {
    console.error('Load more failed:', error)
  } finally {
    isLoading.value = false
  }
}

// Проверка выбора
const isSelected = (animeId: number) => {
  return selectedItems.value.some(item => item.id === animeId)
}

// Переключение выбора
const toggleSelect = (anime: AnimeItem) => {
  const index = selectedItems.value.findIndex(item => item.id === anime.id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    selectedItems.value.push({ ...anime })
  }
}

// Выбрать все видимые
const selectAllVisible = () => {
  for (const anime of displayItems.value) {
    if (!isSelected(anime.id)) {
      selectedItems.value.push({ ...anime })
    }
  }
}

// Очистить выбор
const clearSelection = () => {
  selectedItems.value = []
}

// Добавить выбранные
const addSelected = () => {
  if (selectedItems.value.length === 0) return

  const itemsToAdd = selectedItems.value.map(anime => ({
    anime_id: anime.id,
    anime_title: anime.title_ru || anime.title || `Аниме ${anime.id}`,
    anime_poster: anime.poster ?? undefined,
    weight: 1
  }))

  emit('add', itemsToAdd)
  selectedItems.value = []
  toast.success(`Добавлено ${itemsToAdd.length} аниме`)
}

// Форматирование типа
const formatKind = (kind: string) => {
  const kinds: Record<string, string> = {
    tv: 'ТВ',
    movie: 'Фильм',
    ova: 'OVA',
    ona: 'ONA',
    special: 'Спешл',
    music: 'Клип'
  }
  return kinds[kind] || kind
}

// Форматирование статуса
const formatStatus = (status: string) => {
  const statuses: Record<string, string> = {
    started: 'Смотрю',
    completed: 'Досмотрено',
    on_hold: 'На паузе',
    dropped: 'Брошено',
    planned: 'Запланировано'
  }
  return statuses[status] || status
}

// Загружаем популярные при монтировании
onMounted(() => {
  loadPopular()
})
</script>

<style scoped>
.anime-selector {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

/* Поиск */
.search-section {
  padding: 1rem;
  border-bottom: 1px solid #2a2a2a;
}

.search-input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.95rem;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

/* Вкладки */
.tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  background: #151515;
  border-bottom: 1px solid #2a2a2a;
  overflow-x: auto;
}

.tab-btn {
  flex: 1;
  min-width: fit-content;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: none;
  color: #888;
  font-size: 0.8rem;
  cursor: pointer;
  border-radius: 6px;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #2a2a2a;
  color: #fff;
}

.tab-btn.active {
  background: #667eea;
  color: #fff;
}

/* Контент */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  min-height: 300px;
}

.tab-panel {
  min-height: 100%;
}

/* Сетка аниме */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}

.anime-card {
  background: #0a0a0a;
  border: 2px solid #2a2a2a;
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.anime-card:hover {
  border-color: #444;
  transform: translateY(-2px);
}

.anime-card.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.card-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: #667eea;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.7rem;
}

.card-poster {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.card-poster-placeholder {
  width: 100%;
  height: 180px;
  background: #2a2a2a;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.card-info {
  padding: 0.25rem;
}

.card-title {
  color: #fff;
  font-size: 0.8rem;
  line-height: 1.3;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.7rem;
  color: #888;
}

/* Список плейлистов */
.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.playlist-item:hover {
  border-color: #667eea;
  background: #151515;
}

.playlist-icon {
  font-size: 1.5rem;
}

.playlist-name {
  color: #fff;
  font-size: 0.9rem;
}

.playlist-count {
  color: #666;
  font-size: 0.75rem;
}

/* Загрузка */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #888;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #2a2a2a;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Пусто */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
  text-align: center;
}

.empty p {
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

/* Кнопка загрузить ещё */
.load-more {
  width: 100%;
  margin-top: 1rem;
  padding: 0.75rem;
  background: #2a2a2a;
  border: none;
  color: #888;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.load-more:hover {
  background: #3a3a3a;
  color: #fff;
}

/* Панель выбора */
.selection-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #151515;
  border-top: 1px solid #2a2a2a;
  color: #888;
  font-size: 0.85rem;
}

.selection-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  background: none;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action:hover {
  border-color: #667eea;
  color: #667eea;
}

.btn-clear:hover {
  border-color: #dc2626;
  color: #dc2626;
}

/* Кнопка добавления */
.add-bar {
  padding: 1rem;
  border-top: 1px solid #2a2a2a;
}

.btn-add {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .items-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }

  .card-poster,
  .card-poster-placeholder {
    height: 140px;
  }

  .tabs {
    gap: 0;
  }

  .tab-btn {
    padding: 0.5rem;
    font-size: 0.7rem;
  }
}
</style>
