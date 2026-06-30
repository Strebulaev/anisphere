<template>
  <div class="anime-section" :class="[`section-${type}`, { loading }]">
    <div class="section-header">
      <div class="section-title">
        <slot name="icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="20" rx="2"/>
          </svg>
        </slot>
        <h2>{{ title }}</h2>
      </div>
      <div class="section-actions">
        <button v-if="showShuffle" @click="handleShuffle" class="shuffle-btn" type="button" :disabled="loading">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 3 21 3 21 8"/>
            <line x1="4" y1="20" x2="21" y2="3"/>
            <polyline points="21 16 21 21 16 21"/>
            <line x1="15" y1="15" x2="21" y2="21"/>
            <line x1="4" y1="4" x2="9" y2="9"/>
          </svg>
          Перемешать
        </button>
        <button v-if="showShuffle && isShuffled" @click="handleUnshuffle" class="unshuffle-btn" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
          </svg>
          Сбросить
        </button>
        <button v-if="showRefresh" @click="handleRefresh" class="refresh-btn" type="button" :disabled="loading">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Обновить
        </button>
      </div>
    </div>

    <!-- Фильтры -->
    <div v-if="showFilters" class="section-filters">
      <div class="filter-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="filters.search"
          type="text"
          placeholder="Поиск по названию..."
          class="filter-input"
        />
      </div>
      <div class="filter-year">
        <input
          v-model="filters.yearFrom"
          type="number"
          placeholder="От"
          class="filter-input filter-input-small"
          min="1900"
          :max="new Date().getFullYear()"
        />
        <span class="filter-year-sep">-</span>
        <input
          v-model="filters.yearTo"
          type="number"
          placeholder="До"
          class="filter-input filter-input-small"
          min="1900"
          :max="new Date().getFullYear()"
        />
      </div>
      <div class="filter-sort">
        <select v-model="filters.sortBy" class="filter-select">
          <option value="-score">По рейтингу ↓</option>
          <option value="score">По рейтингу ↑</option>
          <option value="-year">По году ↓</option>
          <option value="year">По году ↑</option>
          <option value="title_ru">По названию</option>
        </select>
      </div>
      <button v-if="hasActiveFilters" @click="resetFilters" class="reset-filters-btn" type="button">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        Сбросить
      </button>
    </div>

    <div v-if="loading" class="section-content section-loading">
      <LoadingState type="skeleton" :count="skeletonCount" />
    </div>

    <div v-else-if="error" class="section-content section-error">
      <ErrorState
        :title="errorTitle"
        :message="error"
        :show-retry="true"
        @retry="handleRefresh"
      />
    </div>

    <div v-else-if="animeList.length === 0" class="section-content section-empty">
      <EmptyState
        :title="emptyTitle"
        :message="emptyMessage"
        :icon="emptyIcon"
        :action-label="emptyActionLabel"
        @action="handleEmptyAction"
      />
    </div>

    <div v-else class="section-content">
      <slot name="content">
        <div v-if="filteredAnimeList.length === 0 && hasActiveFilters" class="no-results">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p>По вашему запросу ничего не найдено</p>
        </div>
        <div v-else class="anime-grid">
          <AnimeCard
            v-for="anime in filteredAnimeList"
            :key="anime.id"
            :anime="anime as any"
            @click="handleAnimeClick(anime)"
            @watch="handleWatchAnime(anime)"
          />
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import { LoadingState, ErrorState, EmptyState } from '@/components/Info'
import type { Anime } from '@/types'

interface Props {
  type: 'ongoings' | 'recommendations' | 'announcements' | 'random' | 'catalog'
  title: string
  animeList: Anime[]
  loading: boolean
  error: string | null
  showRefresh?: boolean
  showShuffle?: boolean
  showFilters?: boolean
  isShuffled?: boolean
  skeletonCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  showRefresh: true,
  showShuffle: false,
  showFilters: false,
  isShuffled: false,
  skeletonCount: 6
})

const emit = defineEmits<{
  refresh: []
  shuffle: []
  unshuffle: []
  animeClick: [anime: Anime]
  watchAnime: [anime: Anime]
  emptyAction: []
}>()

// Состояние фильтров
const filters = ref({
  search: '',
  yearFrom: '',
  yearTo: '',
  sortBy: '-score'
})

// Проверка наличия активных фильтров
const hasActiveFilters = computed(() => {
  return filters.value.search !== '' || 
         filters.value.yearFrom !== '' || 
         filters.value.yearTo !== '' || 
         filters.value.sortBy !== '-score'
})

// Отфильтрованный и отсортированный список
const filteredAnimeList = computed(() => {
  let list = [...props.animeList]
  
  if (filters.value.search) {
    const searchLower = filters.value.search.toLowerCase()
    list = list.filter(anime => 
      (anime.title_ru && anime.title_ru.toLowerCase().includes(searchLower)) ||
      (anime.title_en && anime.title_en.toLowerCase().includes(searchLower))
    )
  }
  
  // Фильтр по году (от)
  if (filters.value.yearFrom) {
    const yearFrom = parseInt(filters.value.yearFrom)
    list = list.filter(anime => anime.year && anime.year >= yearFrom)
  }
  
  // Фильтр по году (до)
  if (filters.value.yearTo) {
    const yearTo = parseInt(filters.value.yearTo)
    list = list.filter(anime => anime.year && anime.year <= yearTo)
  }
  
  // Сортировка
  switch (filters.value.sortBy) {
    case '-score':
      list.sort((a, b) => ((b as any).score || 0) - ((a as any).score || 0))
      break
    case 'score':
      list.sort((a, b) => ((a as any).score || 0) - ((b as any).score || 0))
      break
    case '-year':
      list.sort((a, b) => (b.year || 0) - (a.year || 0))
      break
    case 'year':
      list.sort((a, b) => (a.year || 0) - (b.year || 0))
      break
    case 'title_ru':
      list.sort((a, b) => (a.title_ru || a.title_en || '').localeCompare(b.title_ru || b.title_en || ''))
      break
  }
  
  return list
})

// Сбросить фильтры
const resetFilters = () => {
  filters.value = {
    search: '',
    yearFrom: '',
    yearTo: '',
    sortBy: '-score'
  }
}

const handleShuffle = () => {
  emit('shuffle')
}

const handleUnshuffle = () => {
  emit('unshuffle')
}

const router = useRouter()

const errorTitle = computed(() => {
  switch (props.type) {
    case 'ongoings':
      return 'Не удалось загрузить онгоинги'
    case 'recommendations':
      return 'Не удалось загрузить рекомендации'
    case 'announcements':
      return 'Не удалось загрузить анонсы'
    case 'random':
      return 'Не удалось загрузить случайные аниме'
    case 'catalog':
      return 'Не удалось загрузить каталог'
    default:
      return 'Ошибка загрузки'
  }
})

const emptyTitle = computed(() => {
  switch (props.type) {
    case 'ongoings':
      return 'Нет онгоингов'
    case 'recommendations':
      return 'Нет рекомендаций'
    case 'announcements':
      return 'Нет анонсов'
    case 'random':
      return 'Нет данных'
    case 'catalog':
      return 'Каталог пуст'
    default:
      return 'Ничего не найдено'
  }
})

const emptyMessage = computed(() => {
  switch (props.type) {
    case 'ongoings':
      return 'Сейчас нет выходящих аниме'
    case 'recommendations':
      return 'Добавьте аниме в избранное для персональных рекомендаций'
    case 'announcements':
      return 'Нет предстоящих релизов'
    case 'random':
      return 'Не удалось загрузить случайные аниме'
    case 'catalog':
      return 'В каталоге пока нет аниме'
    default:
      return 'Попробуйте позже'
  }
})

const emptyIcon = computed(() => {
  switch (props.type) {
    case 'ongoings':
      return 'search'
    case 'recommendations':
      return 'heart'
    case 'announcements':
      return 'search'
    case 'random':
      return 'default'
    case 'catalog':
      return 'folder'
    default:
      return 'default'
  }
})

const emptyActionLabel = computed(() => {
  switch (props.type) {
    case 'recommendations':
      return 'Добавить в избранное'
    default:
      return ''
  }
})

const handleRefresh = () => {
  emit('refresh')
}

const handleAnimeClick = (anime: Anime) => {
  emit('animeClick', anime)
  router.push(`/anime/${anime.id}`)
}

const startWatching = (anime: any) => {
  emit('watchAnime', anime)
  router.push(`/anime/${anime.id}/watch`)
}

const handleWatchAnime = (anime: Anime) => {
  emit('watchAnime', anime)
  const identifier = (anime as any).slug || anime.id
  router.push(`/anime/${identifier}/watch`)
}

const handleEmptyAction = () => {
  emit('emptyAction')
}
</script>

<style scoped>
.anime-section {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid var(--color-divider);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title svg {
  color: var(--color-accent);
  flex-shrink: 0;
}

.section-title h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.section-ongoings .section-title svg {
  color: var(--color-accent-teal);
}

.section-recommendations .section-title svg {
  color: var(--color-accent-pink);
}

.section-announcements .section-title svg {
  color: var(--color-accent-yellow);
}

.section-random .section-title svg {
  color: var(--color-accent-purple);
}

.section-actions {
  display: flex;
  gap: 0.75rem;
}

.shuffle-btn,
.unshuffle-btn,
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.shuffle-btn:hover:not(:disabled),
.unshuffle-btn:hover:not(:disabled),
.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.shuffle-btn:disabled,
.unshuffle-btn:disabled,
.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.unshuffle-btn {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.section-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background-color: var(--color-background-elevated);
  border-bottom: 1px solid var(--color-divider);
}

.filter-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.filter-search svg {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  pointer-events: none;
}

.filter-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  transition: border-color 0.2s;
}

.filter-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.filter-input::placeholder {
  color: var(--color-text-secondary);
}

.filter-year {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-input-small {
  width: 80px;
  padding: 0.5rem;
  text-align: center;
}

.filter-year-sep {
  color: var(--color-text-secondary);
}

.filter-sort {
  min-width: 150px;
}

.filter-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-accent);
}

.reset-filters-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background-color: transparent;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.reset-filters-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--color-text-secondary);
}

.no-results svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-results p {
  font-size: 0.9375rem;
}

.section-content {
  padding: 1.5rem;
}

.section-loading,
.section-error,
.section-empty {
  min-height: 400px;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

@media (max-width: 767px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.75rem;
  }
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
  }

  .section-title h2 {
    font-size: 1.25rem;
  }

  .section-content {
    padding: 1rem;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.75rem;
  }
}

@media (max-width: 767px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.75rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 320px) and (max-width: 374px) {
  .anime-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 375px) and (max-width: 413px) {
  .anime-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 414px) and (max-width: 767px) {
  .anime-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 768px) {
  .anime-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 1024px) {
  .anime-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1.1rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 1280px) {
  .anime-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1.25rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}

@media (min-width: 1536px) {
  .anime-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1.5rem;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}
</style>
