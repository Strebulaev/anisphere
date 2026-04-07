<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <!-- Заголовок -->
      <!-- <div class="modal-header">
        <h2><SakuraIcon name="wheel" /> Добавить аниме в колесо</h2>
        <button class="btn-close" @click="$emit('close')">×</button>
      </div> -->

      <!-- Поиск -->
      <div class="search-section">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск аниме..."
          class="search-input"
          @input="debouncedSearch"
        >
      </div>

      <!-- Источники -->
      <div class="sources-tabs">
        <button
          :class="['source-tab', { active: activeSource === 'all' }]"
          @click="activeSource = 'all'"
        >
          🌐 Все аниме
        </button>
        <button
          :class="['source-tab', { active: activeSource === 'collection' }]"
          @click="loadFromCollection"
        >
          <SakuraIcon name="book" /> Моя коллекция
        </button>
        <button
          :class="['source-tab', { active: activeSource === 'playlists' }]"
          @click="loadFromPlaylists"
        >
          <SakuraIcon name="folder" /> Мои плейлисты
        </button>
        <button
          :class="['source-tab', { active: activeSource === 'favorites' }]"
          @click="loadFromFavorites"
        >
          <SakuraIcon name="star" /> Избранное
        </button>
      </div>

      <!-- Результаты поиска -->
      <div class="results-section">
        <div class="results-header">
          <span class="results-count">
            Результаты: {{ filteredResults.length }}
          </span>
          <div class="results-actions">
            <button
              class="btn-select-all"
              @click="selectAllVisible"
              :disabled="filteredResults.length === 0"
            >
              <SakuraIcon name="check" /> Выбрать все
            </button>
            <button
              class="btn-deselect-all"
              @click="selectedItems = []"
              :disabled="selectedItems.length === 0"
            >
              ☐ Снять выбор
            </button>
          </div>
        </div>

        <div class="results-grid" v-if="!isLoading">
          <div
            v-for="anime in filteredResults"
            :key="anime.id"
            :class="['anime-card', { selected: isSelected(anime.id) }]"
            @click="toggleSelection(anime)"
          >
            <div class="card-checkbox">
              <span v-if="isSelected(anime.id)"> <SakuraIcon name="check" /> </span>
              <span v-else>☐</span>
            </div>
            <img
              v-if="anime.poster || anime.poster_url"
              :src="anime.poster || anime.poster_url"
              :alt="anime.title_ru || anime.title"
              class="card-poster"
            >
            <div class="card-info">
              <h4 class="card-title">{{ anime.title_ru || anime.title }}</h4>
              <div class="card-meta">
                <span v-if="anime.score" class="meta-item">
                  <SakuraIcon name="star" /> {{ anime.score }}
                </span>
                <span v-if="anime.kind" class="meta-item">
                  {{ formatKind(anime.kind) }}
                </span>
                <span v-if="anime.episodes" class="meta-item">
                  {{ anime.episodes }} эп.
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="loading-state">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <div v-if="!isLoading && filteredResults.length === 0" class="empty-results">
          <p>Ничего не найдено</p>
        </div>

        <button
          v-if="filteredResults.length > 0 && hasMore"
          class="btn-load-more"
          @click="loadMore"
        >
          Загрузить ещё
        </button>
      </div>

      <!-- Настройки весов -->
      <div v-if="selectedItems.length > 0" class="weights-section">
        <h3><SakuraIcon name="scale" /> Настройки весов для выбранных ({{ selectedItems.length }})</h3>

        <div class="weight-modes">
          <button
            :class="['weight-mode-btn', { active: weightMode === 'equal' }]"
            @click="setWeightMode('equal')"
          >
            <SakuraIcon name="scale" /> Равные веса
          </button>
          <button
            :class="['weight-mode-btn', { active: weightMode === 'rating' }]"
            @click="setWeightMode('rating')"
          >
            <SakuraIcon name="star" /> По рейтингу
          </button>
          <button
            :class="['weight-mode-btn', { active: weightMode === 'custom' }]"
            @click="weightMode = 'custom'"
          >
            <SakuraIcon name="writing-hand" /> Ручные
          </button>
        </div>

        <div v-if="weightMode === 'custom'" class="custom-weights">
          <div
            v-for="item in selectedItems"
            :key="item.id"
            class="weight-item"
          >
            <span class="weight-item-title">{{ item.title_ru || item.title }}</span>
            <input
              type="range"
              min="1"
              max="10"
              :value="item.weight || 1"
              @input="updateItemWeight(item, $event)"
              class="weight-slider"
            >
            <span class="weight-value">{{ item.weight || 1 }}</span>
          </div>
        </div>
      </div>

      <!-- Футер -->
      <div class="modal-footer">
        <div class="footer-info">
          <span>Выбрано: {{ selectedItems.length }}</span>
          <span v-if="roulette"> / Максимум: {{ roulette.max_items }}</span>
        </div>
        <div class="footer-actions">
          <button class="btn-cancel" @click="$emit('close')">
            Отмена
          </button>
          <button
            class="btn-add"
            :disabled="selectedItems.length === 0"
            @click="addSelected"
          >
            <SakuraIcon name="plus" /> Добавить выбранные ({{ selectedItems.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { animeApi } from '@/api/anime'
import { useToast } from '@/composables/useToast'
// Простая реализация debounce
const useDebounceFn = (fn: Function, delay: number) => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  return (...args: any[]) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

interface Anime {
  id: number
  title?: string
  title_ru?: string
  poster_url?: string
  poster?: string
  score?: number
  kind?: string
  episodes?: number
  weight?: number
}

const props = defineProps<{
  roulette?: any
}>()

const emit = defineEmits<{
  close: []
  add: [items: Array<{
    anime_id: number
    anime_title: string
    anime_poster?: string
    weight?: number
  }>]
}>()

const toast = useToast()

const searchQuery = ref('')
const activeSource = ref('all')
const searchResults = ref<Anime[]>([])
const selectedItems = ref<Anime[]>([])
const weightMode = ref<'equal' | 'rating' | 'custom'>('equal')
const isLoading = ref(false)
const hasMore = ref(false)
const currentPage = ref(1)

// Фильтрованные результаты
const filteredResults = computed(() => {
  // Исключаем уже добавленные в рулетку
  const existingIds = props.roulette?.items?.map((i: any) => i.anime_id) || []
  return searchResults.value.filter(anime => !existingIds.includes(anime.id))
})

// Дебаунс для поиска
const debouncedSearch = useDebounceFn(() => {
  if (searchQuery.value) {
    performSearch()
  }
}, 500)

// Поиск аниме
const performSearch = async () => {
  if (!searchQuery.value) return

  isLoading.value = true
  currentPage.value = 1

  try {
    const data = await animeApi.search(searchQuery.value)
    searchResults.value = data.results || []
    hasMore.value = data.total > (data.results?.length || 0)
  } catch (error) {
    console.error('Search failed:', error)
    toast.error('Ошибка поиска')
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
    const data = await animeApi.search(searchQuery.value, { limit: 20 })
    searchResults.value.push(...(data.results || []))
    hasMore.value = data.total > searchResults.value.length
  } catch (error) {
    console.error('Load more failed:', error)
    toast.error('Ошибка загрузки')
  } finally {
    isLoading.value = false
  }
}

// Загрузка из коллекции
const loadFromCollection = async () => {
  activeSource.value = 'collection'
  isLoading.value = true

  try {
    // TODO: Реализовать загрузку из коллекции пользователя
    // const { data } = await userApi.getCollection()
    // searchResults.value = data
    toast.info('Загрузка из коллекции...')
  } catch (error) {
    console.error('Load from collection failed:', error)
    toast.error('Ошибка загрузки коллекции')
  } finally {
    isLoading.value = false
  }
}

// Загрузка из плейлистов
const loadFromPlaylists = async () => {
  activeSource.value = 'playlists'
  isLoading.value = true

  try {
    // TODO: Реализовать загрузку из плейлистов
    toast.info('Загрузка из плейлистов...')
  } catch (error) {
    console.error('Load from playlists failed:', error)
    toast.error('Ошибка загрузки плейлистов')
  } finally {
    isLoading.value = false
  }
}

// Загрузка из избранного
const loadFromFavorites = async () => {
  activeSource.value = 'favorites'
  isLoading.value = true

  try {
    // TODO: Реализовать загрузку из избранного
    toast.info('Загрузка из избранного...')
  } catch (error) {
    console.error('Load from favorites failed:', error)
    toast.error('Ошибка загрузки избранного')
  } finally {
    isLoading.value = false
  }
}

// Проверка выбора
const isSelected = (animeId: number) => {
  return selectedItems.value.some(item => item.id === animeId)
}

// Переключение выбора
const toggleSelection = (anime: Anime) => {
  const index = selectedItems.value.findIndex(item => item.id === anime.id)
  if (index > -1) {
    selectedItems.value.splice(index, 1)
  } else {
    // Проверяем лимит
    const maxItems = props.roulette?.max_items || 50
    if (selectedItems.value.length >= maxItems) {
      toast.warning(`Максимум ${maxItems} аниме`)
      return
    }
    selectedItems.value.push({ ...anime, weight: 1 })
  }
}

// Выбрать все видимые
const selectAllVisible = () => {
  const maxItems = props.roulette?.max_items || 50
  const available = maxItems - selectedItems.value.length

  for (const anime of filteredResults.value.slice(0, available)) {
    if (!isSelected(anime.id)) {
      selectedItems.value.push({ ...anime, weight: 1 })
    }
  }
}

// Установка режима весов
const setWeightMode = (mode: 'equal' | 'rating') => {
  weightMode.value = mode

  if (mode === 'equal') {
    selectedItems.value.forEach(item => {
      item.weight = 1
    })
  } else if (mode === 'rating') {
    selectedItems.value.forEach(item => {
      item.weight = item.score || 5
    })
  }
}

// Обновление веса элемента
const updateItemWeight = (item: Anime, event: Event) => {
  const target = event.target as HTMLInputElement
  item.weight = parseInt(target.value)
}

// Добавить выбранные
const addSelected = () => {
  if (selectedItems.value.length === 0) return

  const items = selectedItems.value.map(anime => ({
    anime_id: anime.id,
    anime_title: anime.title_ru || anime.title || `Аниме ${anime.id}`,
    anime_poster: anime.poster || anime.poster_url,
    weight: anime.weight || 1
  }))

  emit('add', items)
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

onMounted(async () => {
  // Загружаем популярные аниме по умолчанию
  isLoading.value = true
  try {
    const data = await animeApi.list({ page_size: 50, ordering: '-score' })
    searchResults.value = data.results || []
  } catch (error) {
    console.error('Initial load failed:', error)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: #1a1a1a;
  border-radius: 16px;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #2a2a2a;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  color: #888;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.btn-close:hover {
  color: #fff;
}

.search-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #2a2a2a;
}

.search-input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.sources-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #2a2a2a;
  overflow-x: auto;
}

.source-tab {
  background: #2a2a2a;
  border: none;
  color: #888;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.source-tab:hover {
  background: #3a3a3a;
}

.source-tab.active {
  background: #667eea;
  color: #fff;
}

.results-section {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.5rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.results-count {
  color: #888;
  font-size: 0.9rem;
}

.results-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-select-all,
.btn-deselect-all {
  background: none;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn-select-all:hover,
.btn-deselect-all:hover {
  border-color: #667eea;
  color: #667eea;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.anime-card {
  background: #0a0a0a;
  border: 2px solid #2a2a2a;
  border-radius: 12px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.anime-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.anime-card.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.card-checkbox {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  font-size: 1.25rem;
}

.card-poster {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.card-info {
  padding: 0.25rem 0;
}

.card-title {
  color: #fff;
  font-size: 0.9rem;
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.meta-item {
  color: #888;
  font-size: 0.75rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #2a2a2a;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-results {
  text-align: center;
  padding: 3rem;
  color: #888;
}

.btn-load-more {
  width: 100%;
  background: #2a2a2a;
  border: none;
  color: #888;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
  transition: all 0.2s;
}

.btn-load-more:hover {
  background: #3a3a3a;
  color: #fff;
}

.weights-section {
  padding: 1rem 1.5rem;
  border-top: 1px solid #2a2a2a;
  background: #0f0f0f;
}

.weights-section h3 {
  color: #fff;
  font-size: 1rem;
  margin: 0 0 1rem 0;
}

.weight-modes {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.weight-mode-btn {
  background: #2a2a2a;
  border: none;
  color: #888;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.weight-mode-btn:hover {
  background: #3a3a3a;
}

.weight-mode-btn.active {
  background: #667eea;
  color: #fff;
}

.custom-weights {
  max-height: 200px;
  overflow-y: auto;
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #1a1a1a;
}

.weight-item-title {
  flex: 1;
  color: #fff;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weight-slider {
  width: 120px;
  accent-color: #667eea;
}

.weight-value {
  color: #667eea;
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 2rem;
  text-align: right;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid #2a2a2a;
  background: #0f0f0f;
}

.footer-info {
  color: #888;
  font-size: 0.9rem;
}

.footer-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-cancel {
  background: #2a2a2a;
  border: none;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #3a3a3a;
}

.btn-add {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
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
  .modal-content {
    max-height: 100vh;
    border-radius: 0;
  }

  .sources-tabs {
    padding: 0.75rem 1rem;
  }

  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .modal-footer {
    flex-direction: column;
    gap: 1rem;
  }

  .footer-actions {
    width: 100%;
    flex-direction: column;
  }

  .btn-cancel,
  .btn-add {
    width: 100%;
  }
}
</style>
