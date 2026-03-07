<template>
  <div class="catalog-view">
    <!-- Панель поиска и фильтров -->
    <div class="catalog-header">
      <div class="search-container">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="11" cy="11" r="8" stroke-width="2"/>
          <path stroke-width="2" d="M21 21l-4.35-4.35"/>
        </svg>
        <input
          v-model="searchQuery"
          @input="handleSearch"
          type="text"
          placeholder="Поиск аниме по названию..."
          class="search-input"
        />
        <button v-if="searchQuery" @click="clearSearch" class="clear-search" type="button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="header-actions">
        <!-- Сортировка -->
        <select v-model="sortBy" @change="emitFilters" class="sort-select">
          <option value="-score">По рейтингу ↓</option>
          <option value="score">По рейтингу ↑</option>
          <option value="-year">По году ↓</option>
          <option value="year">По году ↑</option>
          <option value="title_ru">По названию А-Я</option>
          <option value="-title_ru">По названию Я-А</option>
          <option value="-popularity">По популярности ↓</option>
          <option value="popularity">По популярности ↑</option>
          <option value="-favorites">В избранном ↓</option>
          <option value="favorites">В избранном ↑</option>
          <option value="-created_at">Добавлено ↓</option>
          <option value="created_at">Добавлено ↑</option>
        </select>

        <!-- Количество на странице -->
        <select v-model="itemsPerPage" @change="handleItemsPerPageChange" class="items-per-page-select">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>

        <button v-if="showShuffle" @click="handleShuffle" class="btn btn-outline shuffle-btn" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 3 21 3 21 8"/>
            <line x1="4" y1="20" x2="21" y2="3"/>
            <polyline points="21 16 21 21 16 21"/>
            <line x1="15" y1="15" x2="21" y2="21"/>
            <line x1="4" y1="4" x2="9" y2="9"/>
          </svg>
        </button>
        <button v-if="showShuffle && isShuffled" @click="handleUnshuffle" class="btn btn-outline unshuffle-btn" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
          </svg>
        </button>
        <button @click="handleRefresh" class="btn btn-outline" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>
        <button @click="toggleFilters" :class="['btn btn-outline', { active: showFilters }]" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          <span v-if="activeFiltersCount > 0" class="filters-badge">{{ activeFiltersCount }}</span>
        </button>
      </div>
    </div>

    <!-- Панель фильтров -->
    <transition name="filters">
      <div v-if="showFilters" class="filters-panel">
        <AnimeFilters
          v-model="animeFilters"
          :results-count="totalCount"
          @filter-change="handleFilterChange"
        />
      </div>
    </transition>

    <!-- Активные фильтры -->
    <div v-if="activeFiltersCount > 0 && !showFilters" class="active-filters-bar">
      <span class="active-filters-label">Активные фильтры:</span>
      <div class="active-filters-list">
        <span v-if="searchQuery" class="active-filter-chip">
          Поиск: "{{ searchQuery }}"
          <button @click="clearSearch" type="button">×</button>
        </span>
        <span v-if="animeFilters.genres?.length" class="active-filter-chip">
          Жанры: {{ animeFilters.genres.length }}
          <button @click="clearGenreFilters" type="button">×</button>
        </span>
        <span v-if="animeFilters.year_from || animeFilters.year_to" class="active-filter-chip">
          Год: {{ animeFilters.year_from || '?' }} — {{ animeFilters.year_to || '?' }}
          <button @click="clearYearFilters" type="button">×</button>
        </span>
        <span v-if="animeFilters.status?.length" class="active-filter-chip">
          Статус: {{ (animeFilters.status as string[]).join(', ') }}
          <button @click="clearStatusFilters" type="button">×</button>
        </span>
        <span v-if="animeFilters.type?.length" class="active-filter-chip">
          Тип: {{ (animeFilters.type as string[]).join(', ') }}
          <button @click="clearTypeFilters" type="button">×</button>
        </span>
        <span v-if="animeFilters.score_from || animeFilters.score_to" class="active-filter-chip">
          Рейтинг: {{ animeFilters.score_from || 0 }} — {{ animeFilters.score_to || 10 }}
          <button @click="clearRatingFilters" type="button">×</button>
        </span>
      </div>
      <button @click="clearAllFilters" class="clear-all-btn" type="button">Сбросить всё</button>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="loading" class="catalog-loading">
      <LoadingState type="skeleton" :count="itemsPerPage" />
    </div>

    <!-- Состояние ошибки -->
    <div v-else-if="error" class="catalog-error">
      <ErrorState
        title="Не удалось загрузить каталог"
        :message="error"
        :show-retry="true"
        @retry="handleRefresh"
      />
    </div>

    <!-- Пустое состояние -->
    <div v-else-if="deduplicatedList.length === 0" class="catalog-empty">
      <EmptyState
        title="Ничего не найдено"
        message="Попробуйте изменить параметры поиска или сбросить фильтры"
        icon="search"
        :suggestions="['Сбросить фильтры', 'Изменить запрос поиска']"
        action-label="Сбросить фильтры"
        @action="clearAllFilters"
      />
    </div>

    <!-- Список аниме -->
    <div v-else class="catalog-content">
      <div class="results-info">
        <span>Показано {{ deduplicatedList.length }} из {{ totalCount }} аниме</span>
      </div>
      <div class="anime-grid">
        <AnimeCard
          v-for="anime in deduplicatedList"
          :key="(anime as any).franchise_id ? 'f' + (anime as any).franchise_id : anime.id"
          :anime="anime as any"
          @click="handleAnimeClick(anime)"
          @watch="handleWatchAnime(anime)"
        />
      </div>

      <!-- Пагинация -->
      <div v-if="totalPages > 1" class="pagination">
        <Pagination
          :current-page="page"
          :total-pages="totalPages"
          :total-items="totalCount"
          :items-per-page="itemsPerPage"
          @update:current-page="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import { LoadingState, ErrorState, EmptyState } from '@/components/Info'
import { Pagination } from '@/components/Navigation'
import AnimeFilters from '@/components/Filters/AnimeFilters.vue'
import type { Anime } from '@/types'
import type { AnimeFilters as AnimeFiltersType } from '@/api/anime'

interface Props {
  animeList: Anime[]
  loading: boolean
  error: string | null
  page: number
  totalPages: number
  totalCount: number
  showShuffle?: boolean
  isShuffled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showShuffle: false,
  isShuffled: false
})

const emit = defineEmits<{
  pageChange: [page: number]
  refresh: []
  shuffle: []
  unshuffle: []
  animeClick: [anime: Anime]
  watchAnime: [anime: Anime]
  filterChange: [filters: AnimeFiltersType]
}>()

const searchQuery = ref('')
const showFilters = ref(false)
const sortBy = ref('-score')
const itemsPerPage = ref(50)

const animeFilters = reactive<AnimeFiltersType>({
  genres: [],
  genre_logic: 'OR',
  status: [],
  type: [],
  score_from: undefined,
  score_to: undefined,
  year_from: undefined,
  year_to: undefined,
  episodes_from: undefined,
  episodes_to: undefined,
  season: undefined,
  season_year: undefined,
  country: [],
  rus_translation: null,
  age_rating: [],
  has_awards: false,
  duration_from: undefined,
  duration_to: undefined,
  author: '',
  director: '',
  composer: '',
  popularity_from: undefined,
  popularity_to: undefined,
  added_from: undefined,
  added_to: undefined
})

// Вычисляем количество активных фильтров
const activeFiltersCount = computed(() => {
  let count = 0
  if (searchQuery.value) count++
  if (animeFilters.genres?.length) count += animeFilters.genres.length
  if (animeFilters.status?.length) count += animeFilters.status.length
  if (animeFilters.type?.length) count += animeFilters.type.length
  if (animeFilters.year_from || animeFilters.year_to) count++
  if (animeFilters.score_from || animeFilters.score_to) count++
  if (animeFilters.season) count++
  if (animeFilters.country?.length) count++
  if (animeFilters.rus_translation) count++
  if (animeFilters.age_rating?.length) count++
  if (animeFilters.has_awards) count++
  return count
})

let searchTimeout: number | undefined

const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = window.setTimeout(() => {
    emitFilters()
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  emitFilters()
}

const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const emitFilters = () => {
  const filters: AnimeFiltersType = {
    ...animeFilters,
    search: searchQuery.value || undefined,
    ordering: sortBy.value as any,
    page_size: itemsPerPage.value
  }
  emit('filterChange', filters)
}

const handleFilterChange = (filters: AnimeFiltersType) => {
  Object.assign(animeFilters, filters)
  emitFilters()
}

const handleItemsPerPageChange = () => {
  emitFilters()
}

const clearGenreFilters = () => {
  animeFilters.genres = []
  emitFilters()
}

const clearYearFilters = () => {
  animeFilters.year_from = undefined
  animeFilters.year_to = undefined
  emitFilters()
}

const clearStatusFilters = () => {
  animeFilters.status = []
  emitFilters()
}

const clearTypeFilters = () => {
  animeFilters.type = []
  emitFilters()
}

const clearRatingFilters = () => {
  animeFilters.score_from = undefined
  animeFilters.score_to = undefined
  emitFilters()
}

const clearAllFilters = () => {
  searchQuery.value = ''
  Object.assign(animeFilters, {
    genres: [],
    genre_logic: 'OR',
    status: [],
    type: [],
    score_from: undefined,
    score_to: undefined,
    year_from: undefined,
    year_to: undefined,
    episodes_from: undefined,
    episodes_to: undefined,
    season: undefined,
    season_year: undefined,
    country: [],
    rus_translation: null,
    age_rating: [],
    has_awards: false,
    duration_from: undefined,
    duration_to: undefined,
    author: '',
    director: '',
    composer: '',
    popularity_from: undefined,
    popularity_to: undefined,
    added_from: undefined,
    added_to: undefined
  })
  emitFilters()
}

const handleRefresh = () => {
  emitFilters()
}

const handleShuffle = () => {
  emit('shuffle')
}

const handleUnshuffle = () => {
  emit('unshuffle')
}

const handlePageChange = (newPage: number) => {
  emit('pageChange', newPage)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Дедуплицируем список: из аниме одной франшизы оставляем только лучшую карточку
// и подменяем title/poster на данные самой франшизы
const deduplicatedList = computed(() => {
  const seen = new Map<string, any>()
  for (const a of props.animeList) {
    const fid = (a as any).franchise_id
    if (fid) {
      const key = `franchise_${fid}`
      const existing = seen.get(key)
      if (!existing || ((a as any).score || 0) > ((existing as any).score || 0)) {
        // Подменяем название и постер на данные франшизы если есть
        const franchiseName = (a as any).franchise_name
        const franchisePoster = (a as any).franchise_poster_image_url
        seen.set(key, {
          ...a,
          // Используем название франшизы если оно есть
          title_ru: franchiseName || (a as any).title_ru,
          // Используем постер франшизы если он есть
          poster_image_url: franchisePoster || (a as any).poster_image_url,
          poster_url: franchisePoster || (a as any).poster_url,
        })
      }
    } else {
      seen.set(`anime_${a.id}`, a)
    }
  }
  return Array.from(seen.values())
})

const handleAnimeClick = (anime: Anime) => {
  emit('animeClick', anime)
}

const handleWatchAnime = (anime: Anime) => {
  emit('watchAnime', anime)
}

watch(() => props.page, () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
})
</script>

<style scoped>
.catalog-view {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid var(--color-divider);
}

.catalog-header {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-divider);
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
  padding: 0.875rem 3rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  outline: none;
  transition: all 0.2s var(--transition-smooth);
  background-color: var(--color-background-active);
  color: var(--color-text);
}

.search-input:focus {
  border-color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.clear-search {
  position: absolute;
  right: 0.75rem;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s var(--transition-smooth);
}

.clear-search:hover {
  background-color: var(--color-background-surface);
  color: var(--color-text);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.sort-select,
.items-per-page-select {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.875rem;
  background-color: var(--color-background-surface);
  color: var(--color-text);
  cursor: pointer;
  min-width: 120px;
}

.sort-select:focus,
.items-per-page-select:focus {
  outline: none;
  border-color: var(--color-accent);
}

.filters-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background-color: var(--color-accent-pink);
  color: white;
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  background-color: var(--color-background-surface);
  color: var(--color-text-secondary);
}

.btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.shuffle-btn:hover {
  border-color: var(--color-accent-purple);
  color: var(--color-accent-purple);
}

.unshuffle-btn {
  border-color: var(--color-accent-purple);
  color: var(--color-accent-purple);
  background-color: var(--color-background-active);
}

.unshuffle-btn:hover {
  background-color: rgba(139, 92, 246, 0.1);
}

.filters-panel {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-divider);
  background-color: var(--color-background-active);
}

.filters-enter-active,
.filters-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.filters-enter-from,
.filters-leave-to {
  opacity: 0;
  max-height: 0;
}

.active-filters-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--color-background-active);
  border-bottom: 1px solid var(--color-divider);
  flex-wrap: wrap;
}

.active-filters-label {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.active-filters-list {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  flex: 1;
}

.active-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  background-color: var(--color-accent);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 1rem;
}

.active-filter-chip button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.active-filter-chip button:hover {
  background: rgba(255, 255, 255, 0.4);
}

.clear-all-btn {
  padding: 0.375rem 0.75rem;
  background: none;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.clear-all-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.results-info {
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.filter-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-select {
  padding: 0.625rem 1rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background-color: var(--color-background-surface);
  color: var(--color-text);
  cursor: pointer;
  min-width: 180px;
}

.year-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.year-input {
  width: 90px;
  padding: 0.625rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  text-align: center;
  background-color: var(--color-background-surface);
  color: var(--color-text);
}

.year-separator {
  color: var(--color-text-tertiary);
  font-weight: 700;
}

.filter-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider);
}

.clear-btn {
  color: var(--color-accent-pink);
  border-color: var(--color-accent-pink);
}

.clear-btn:hover {
  background-color: rgba(255, 42, 109, 0.1);
}

.results-count {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 600;
}

.results-count strong {
  color: var(--color-accent);
}

.catalog-loading,
.catalog-error,
.catalog-empty {
  padding: 3rem;
}

.catalog-content {
  padding: 1.5rem;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.pagination {
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-divider);
}

@media (max-width: 768px) {
  .catalog-header {
    flex-direction: column;
    padding: 1rem;
  }

  .search-container {
    min-width: 100%;
  }

  .header-actions {
    width: 100%;
  }

  .btn {
    flex: 1;
    justify-content: center;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-select,
  .year-input {
    width: 100%;
  }

  .filter-actions {
    flex-direction: column;
    gap: 1rem;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1rem;
  }
}
</style>
