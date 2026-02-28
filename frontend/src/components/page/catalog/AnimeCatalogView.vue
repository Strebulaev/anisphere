<template>
  <div class="anime-catalog">
    <div class="catalog-header">
      <h1 class="catalog-title">Каталог аниме</h1>

      <div class="catalog-search">
        <SearchBar
          variant="page"
          placeholder="Поиск аниме..."
          :categories="searchCategories"
          @search="handleSearch"
        />
      </div>

      <div class="catalog-controls">
        <SortDropdown v-model="sortValue" :options="sortOptions" />
        <ItemsPerPage v-model="itemsPerPage" />
      </div>
    </div>

    <div class="catalog-content">
      <aside class="catalog-sidebar">
        <FilterBlock
          :is-collapsed="isFiltersCollapsed"
          @toggle="toggleFiltersCollapsed"
          @apply="applyFilters"
          @reset="resetFilters"
        >
          <GenreFilter
            v-model="selectedGenres"
            :genres="availableGenres"
            label="Жанры"
          />

          <YearFilter
            v-model="selectedYearRange"
            :min-year="minYear"
            :max-year="maxYear"
          />

          <StatusFilter
            v-model="selectedStatuses"
            :statuses="availableStatuses"
          />

          <TypeFilter
            v-model="selectedTypes"
            :types="availableTypes"
          />

          <EpisodesFilter
            v-model="selectedEpisodesRange"
          />

          <RatingFilter
            v-model="selectedRatingRange"
            :min-rating="0"
            :max-rating="10"
          />
        </FilterBlock>
      </aside>

      <main class="catalog-main">
        <ActiveFilters
          v-if="hasActiveFilters"
          :filters="activeFiltersList"
          @remove="removeFilter"
          @clear-all="clearAllFilters"
        />

        <div v-if="isLoading" class="catalog-loading">
          <div class="spinner"></div>
          <p>Загрузка аниме...</p>
        </div>

        <div v-else-if="error" class="catalog-error">
          <p>{{ error }}</p>
          <button @click="loadAnime" class="retry-btn">Попробовать снова</button>
        </div>

        <div v-else-if="filteredAnime.length === 0" class="catalog-empty">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p>Ничего не найдено</p>
          <p class="hint">Попробуйте изменить параметры поиска или фильтры</p>
        </div>

        <template v-else>
          <div class="catalog-results">
            <p class="results-count">Найдено: {{ totalCount }} аниме</p>
          </div>

          <div class="anime-grid">
            <div
              v-for="anime in filteredAnime"
              :key="anime.id"
              class="anime-card"
              @click="goToAnime(anime.id)"
            >
              <div class="anime-poster">
                <img
                  :src="anime.poster_url || '/placeholder-anime.jpg'"
                  :alt="anime.title_ru || anime.title_en"
                  @error="handleImageError"
                />
                <div v-if="anime.score" class="anime-rating">
                  ★ {{ anime.score }}
                </div>
              </div>

              <div class="anime-info">
                <h3 class="anime-title">
                  {{ anime.title_ru || anime.title_en }}
                </h3>
                <p class="anime-meta">
                  <span v-if="anime.year">{{ anime.year }}</span>
                  <span v-if="anime.episodes">{{ anime.episodes }} эп.</span>
                  <span v-if="anime.status" class="status-badge" :class="'status-' + anime.status">
                    {{ getStatusText(anime.status) }}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <Pagination
            v-if="totalPages > 1"
            :current-page="currentPage"
            :total-pages="totalPages"
            @page-change="handlePageChange"
          />
        </template>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useFilters } from '@/composables/useFilters'
import { useSearch } from '@/composables/useSearch'
import SearchBar from '@/components/Search/SearchBar.vue'
import FilterBlock from '@/components/Filters/FilterBlock.vue'
import GenreFilter from '@/components/Filters/GenreFilter.vue'
import YearFilter from '@/components/Filters/YearFilter.vue'
import StatusFilter from '@/components/Filters/StatusFilter.vue'
import TypeFilter from '@/components/Filters/TypeFilter.vue'
import EpisodesFilter from '@/components/Filters/EpisodesFilter.vue'
import RatingFilter from '@/components/Filters/RatingFilter.vue'
import ActiveFilters from '@/components/Filters/ActiveFilters.vue'
import SortDropdown from '@/components/Filters/SortDropdown.vue'
import ItemsPerPage from '@/components/Filters/ItemsPerPage.vue'
import Pagination from '@/components/Pagination/Pagination.vue'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const searchCategories = [
  { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 8 }
]

const sortOptions = [
  { value: 'score', label: 'По рейтингу' },
  { value: 'year', label: 'По дате выхода' },
  { value: 'title_ru', label: 'По названию (рус.)' },
  { value: 'title_en', label: 'По названию (англ.)' },
  { value: 'episodes', label: 'По количеству серий' },
  { value: 'created_at', label: 'По дате добавления' },
  { value: 'popularity', label: 'По популярности' }
]

const availableGenres = [
  { value: 'action', label: 'Экшен' },
  { value: 'adventure', label: 'Приключения' },
  { value: 'comedy', label: 'Комедия' },
  { value: 'drama', label: 'Драма' },
  { value: 'fantasy', label: 'Фэнтези' },
  { value: 'horror', label: 'Ужасы' },
  { value: 'mystery', label: 'Мистика' },
  { value: 'romance', label: 'Романтика' },
  { value: 'sci-fi', label: 'Sci-Fi' },
  { value: 'slice_of_life', label: 'Повседневность' },
  { value: 'sports', label: 'Спорт' },
  { value: 'supernatural', label: 'Сверхъестественное' },
  { value: 'thriller', label: 'Триллер' }
]

const availableStatuses = [
  { value: 'ongoing', label: 'Онгоинг' },
  { value: 'finished', label: 'Завершён' },
  { value: 'announced', label: 'Анонсирован' }
]

const availableTypes = [
  { value: 'tv', label: 'TV' },
  { value: 'movie', label: 'Фильм' },
  { value: 'ova', label: 'OVA' },
  { value: 'ona', label: 'ONA' },
  { value: 'special', label: 'Спешл' }
]

const minYear = 1990
const maxYear = new Date().getFullYear() + 1

const {
  selectedGenres,
  selectedYearRange,
  selectedStatuses,
  selectedTypes,
  selectedEpisodesRange,
  selectedRatingRange,
  currentSort,
  itemsPerPage,
  isFiltersCollapsed,
  hasActiveFilters,
  activeFiltersList,
  applyFilters,
  resetFilters,
  clearAllFilters,
  clearFilter,
  toggleFiltersCollapsed,
  getQueryParams,
  setSort
} = useFilters({
  persistToUrl: true,
  persistToLocalStorage: true,
  localStorageKey: 'anime-catalog',
  defaultSort: { field: 'score', order: 'desc' },
  defaultItemsPerPage: 20,
  availableGenres,
  availableStatuses,
  availableTypes,
  minYear,
  maxYear
})

const sortValue = computed({
  get: () => {
    if (!currentSort.value) return '-score'
    const prefix = currentSort.value.order === 'desc' ? '-' : ''
    return prefix + currentSort.value.field
  },
  set: (value: string) => {
    const prefix = value.startsWith('-') ? '-' : ''
    const field = value.replace(/^-/, '')
    const order = prefix ? 'desc' : 'asc'
    setSort(field, order)
  }
})

const filteredAnime = ref<any[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const totalPages = ref(1)
const isLoading = ref(false)
const error = ref('')

const { searchQuery, handleInput } = useSearch({
  categories: searchCategories,
  searchRoute: '/anime'
})

const getStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    'ongoing': 'Онгоинг',
    'finished': 'Завершено',
    'announced': 'Анонс'
  }
  return statusMap[status || ''] || 'Неизвестно'
}

const handleSearch = (query: string) => {
  router.push({ path: '/anime', query: { ...getQueryParams(), q: query } })
}

const removeFilter = (key: string) => {
  const filterType = key.split('-')[0] || key
  clearFilter(filterType)
  applyFilters()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadAnime()
}

const goToAnime = (id: number) => {
  router.push(`/anime/${id}`)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/placeholder-anime.jpg'
}

const loadAnime = async () => {
  isLoading.value = true
  error.value = ''

  try {
    const params = getQueryParams()
    params.page = currentPage.value
    
    const response = await api.get('/anime/', { params })
    filteredAnime.value = response.data.results || []
    totalCount.value = response.data.count || 0
    totalPages.value = Math.ceil(totalCount.value / (itemsPerPage.value || 20))
  } catch (err: any) {
    console.error('Error loading anime:', err)
    error.value = 'Ошибка загрузки аниме. Попробуйте позже.'
    filteredAnime.value = []
  } finally {
    isLoading.value = false
  }
}

watch([selectedGenres, selectedYearRange, selectedStatuses, selectedTypes, selectedEpisodesRange, selectedRatingRange, currentSort, itemsPerPage], () => {
  currentPage.value = 1
  applyFilters()
  loadAnime()
}, { deep: true })

watch(() => route.query, (newQuery) => {
  const page = newQuery.page as string
  if (page) {
    currentPage.value = parseInt(page)
    loadAnime()
  }
})

onMounted(() => {
  const page = route.query.page as string
  if (page) {
    currentPage.value = parseInt(page)
  }
  loadAnime()
})
</script>

<style scoped>
.anime-catalog {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  background-color: #373737;
  min-height: 100vh;
}

.catalog-header {
  margin-bottom: 2rem;
}

.catalog-title {
  margin: 0 0 1.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: white;
}

.catalog-search {
  max-width: 600px;
  margin: 0 auto 1.5rem;
}

.catalog-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
}

.catalog-content {
  display: flex;
  gap: 2rem;
}

.catalog-sidebar {
  width: 300px;
  flex-shrink: 0;
}

.catalog-main {
  flex: 1;
  min-width: 0;
}

.catalog-loading,
.catalog-error,
.catalog-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}

.retry-btn:hover {
  background-color: var(--color-accent-hover);
}

.catalog-results {
  margin-bottom: 1.5rem;
}

.results-count {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.anime-card {
  cursor: pointer;
  transition: transform 0.15s;
}

.anime-card:hover {
  transform: translateY(-4px);
}

.anime-poster {
  position: relative;
  width: 100%;
  padding-top: 140%;
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--color-background-surface);
  margin-bottom: 0.75rem;
}

.anime-poster img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.anime-rating {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  background-color: rgba(0, 0, 0, 0.8);
  color: var(--color-accent-orange);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.anime-info {
  padding: 0 4px;
}

.anime-title {
  font-size: 14px;
  font-weight: 600;
  color: white;
  margin: 0 0 0.5rem 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.anime-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin: 0;
}

.status-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-ongoing {
  background-color: rgba(0, 212, 170, 0.2);
  color: var(--color-accent-teal);
}

.status-finished {
  background-color: rgba(58, 134, 255, 0.2);
  color: var(--color-accent);
}

.status-announced {
  background-color: rgba(255, 159, 28, 0.2);
  color: var(--color-accent-orange);
}

@media (max-width: 1024px) {
  .catalog-content {
    flex-direction: column;
  }

  .catalog-sidebar {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .anime-catalog {
    padding: 1rem;
  }

  .catalog-title {
    font-size: 1.5rem;
  }

  .anime-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
}
</style>
