# Компоненты поиска и фильтров

## Модуль поиска (useSearch)

Универсальный composable для реализации поиска с автодополнением.

### Использование

```typescript
import { useSearch } from '@/composables/useSearch'

const {
  searchQuery,
  isFocused,
  isLoading,
  results,
  showSuggestions,
  hasResults,
  showClearButton,
  handleInput,
  handleSearch,
  clearSearch,
  handleFocus,
  handleBlur,
  selectItem,
  getMediaUrl
} = useSearch({
  categories: [
    { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 5 },
    { id: 'users', name: 'Пользователи', icon: 'users', enabled: true, limit: 3 },
    { id: 'playlists', name: 'Плейлисты', icon: 'playlists', enabled: true, limit: 3 }
  ],
  debounceTime: 400,
  minQueryLength: 3,
  placeholder: 'Поиск...',
  searchRoute: '/anime',
  searchQueryKey: 'q'
})
```

### Props для SearchBar

| Prop | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| variant | 'header' \| 'page' \| 'sidebar' \| 'compact' | 'header' | Вариант отображения |
| placeholder | string | 'Поиск...' | Placeholder для поля ввода |
| categories | SearchCategory[] | defaultCategories | Категории для поиска |
| minQueryLength | number | 3 | Минимальная длина запроса |
| debounceTime | number | 400 | Задержка перед запросом (мс) |
| searchRoute | string | '/anime' | Маршрут для перехода |
| searchQueryKey | string | 'search' | Ключ параметра в URL |

### События

| Событие | Параметры | Описание |
|---------|-----------|----------|
| search | query: string | При отправке поиска |
| clear | - | При очистке поиска |
| focus | - | При фокусе на поле ввода |
| blur | - | При потере фокуса |

---

## Модуль фильтров (useFilters)

Универсальный composable для управления фильтрами аниме.

### Использование

```typescript
import { useFilters } from '@/composables/useFilters'

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
  activeFiltersCount,
  activeFiltersList,
  
  toggleGenre,
  selectAllGenres,
  clearGenres,
  
  setYearRange,
  clearYearRange,
  
  toggleStatus,
  selectAllStatuses,
  clearStatuses,
  
  toggleType,
  selectAllTypes,
  clearTypes,
  
  setEpisodesRange,
  clearEpisodesRange,
  
  setRatingRange,
  clearRatingRange,
  
  setSort,
  toggleSortOrder,
  
  clearAllFilters,
  clearFilter,
  
  toggleFiltersCollapsed,
  
  applyFilters,
  resetFilters,
  getQueryParams,
  loadFromQuery,
  saveToLocalStorage,
  loadFromLocalStorage
} = useFilters({
  persistToUrl: true,
  persistToLocalStorage: true,
  localStorageKey: 'anime-catalog',
  defaultSort: { field: 'score', order: 'desc' },
  defaultItemsPerPage: 20,
  availableGenres: genreOptions,
  availableStatuses: statusOptions,
  availableTypes: typeOptions,
  minYear: 1990,
  maxYear: 2025
})
```

### Опции

| Опция | Тип | По умолчанию | Описание |
|-------|-----|--------------|----------|
| persistToUrl | boolean | true | Сохранять фильтры в URL |
| persistToLocalStorage | boolean | true | Сохранять в localStorage |
| localStorageKey | string | 'anime-catalog' | Ключ для localStorage |
| defaultSort | { field: string; order: 'asc' \| 'desc' } | { field: 'score', order: 'desc' } | Сортировка по умолчанию |
| defaultItemsPerPage | number | 20 | Элементов на странице |
| availableGenres | FilterOption[] | [] | Доступные жанры |
| availableStatuses | FilterOption[] | [] | Доступные статусы |
| availableTypes | FilterOption[] | [] | Доступные типы |
| minYear | number | 1990 | Минимальный год |
| maxYear | number | текущий + 1 | Максимальный год |

### Компоненты фильтров

#### FilterBlock
Основной блок фильтров с кнопками применения и сброса.

```vue
<FilterBlock
  :is-collapsed="isFiltersCollapsed"
  @toggle="toggleFiltersCollapsed"
  @apply="applyFilters"
  @reset="resetFilters"
>
  <!-- Фильтры -->
</FilterBlock>
```

#### GenreFilter
Фильтр по жанрам с поиском.

```vue
<GenreFilter
  v-model="selectedGenres"
  :genres="availableGenres"
  :show-search="true"
  :show-actions="true"
/>
```

#### YearFilter
Фильтр по годам (диапазон или выпадающий список).

```vue
<YearFilter
  v-model="selectedYearRange"
  :min-year="1990"
  :max-year="2025"
  :show-slider="false"
/>
```

#### StatusFilter
Фильтр по статусу (онгоинг, завершён, анонсирован).

```vue
<StatusFilter
  v-model="selectedStatuses"
  :statuses="availableStatuses"
/>
```

#### TypeFilter
Фильтр по типу (TV, Фильм, OVA, ONA, Спешл).

```vue
<TypeFilter
  v-model="selectedTypes"
  :types="availableTypes"
/>
```

#### EpisodesFilter
Фильтр по количеству серий.

```vue
<EpisodesFilter
  v-model="selectedEpisodesRange"
/>
```

#### RatingFilter
Фильтр по рейтингу.

```vue
<RatingFilter
  v-model="selectedRatingRange"
  :min-rating="0"
  :max-rating="10"
/>
```

#### ActiveFilters
Отображение активных фильтров в виде тегов.

```vue
<ActiveFilters
  :filters="activeFiltersList"
  :max-visible="8"
  @remove="removeFilter"
  @clear-all="clearAllFilters"
/>
```

#### SortDropdown
Выпадающий список сортировки.

```vue
<SortDropdown
  v-model="currentSort"
  :options="sortOptions"
/>
```

#### ItemsPerPage
Выбор количества элементов на странице.

```vue
<ItemsPerPage
  v-model="itemsPerPage"
  :options="[10, 20, 50, 100]"
/>
```

---

## Полный пример использования

```vue
<template>
  <div class="anime-catalog">
    <div class="catalog-header">
      <SearchBar
        variant="page"
        placeholder="Поиск аниме..."
        :categories="searchCategories"
        @search="handleSearch"
      />
      
      <div class="catalog-controls">
        <SortDropdown v-model="currentSort" />
        <ItemsPerPage v-model="itemsPerPage" />
      </div>
    </div>

    <div class="catalog-content">
      <aside class="catalog-sidebar">
        <AnimeFilters
          :available-genres="genres"
          :available-statuses="statuses"
          :available-types="types"
          @filters-changed="handleFiltersChanged"
        />
      </aside>

      <main class="catalog-main">
        <ActiveFilters
          :filters="activeFiltersList"
          @remove="removeFilter"
          @clear-all="clearAllFilters"
        />

        <AnimeGrid :anime="filteredAnime" />
        
        <Pagination
          :current-page="currentPage"
          :total-pages="totalPages"
          @page-change="handlePageChange"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFilters } from '@/composables/useFilters'
import { useSearch } from '@/composables/useSearch'
import SearchBar from '@/components/Search/SearchBar.vue'
import AnimeFilters from '@/components/Filters/AnimeFilters.vue'
import ActiveFilters from '@/components/Filters/ActiveFilters.vue'
import SortDropdown from '@/components/Filters/SortDropdown.vue'
import ItemsPerPage from '@/components/Filters/ItemsPerPage.vue'

const {
  searchQuery,
  handleInput,
  handleSearch
} = useSearch({
  categories: [
    { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 5 }
  ],
  searchRoute: '/anime'
})

const {
  selectedGenres,
  selectedYearRange,
  selectedStatuses,
  selectedTypes,
  selectedEpisodesRange,
  selectedRatingRange,
  currentSort,
  itemsPerPage,
  activeFiltersList,
  applyFilters,
  resetFilters,
  clearAllFilters,
  clearFilter,
  getQueryParams
} = useFilters({
  persistToUrl: true,
  persistToLocalStorage: true,
  localStorageKey: 'anime-catalog'
})

const filteredAnime = ref([])
const currentPage = ref(1)
const totalPages = ref(1)

const handleFiltersChanged = (filters: Record<string, any>) => {
  loadAnime()
}

const removeFilter = (key: string) => {
  clearFilter(key.split('-')[0])
  applyFilters()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadAnime()
}

const loadAnime = async () => {
  const params = getQueryParams()
  params.page = currentPage.value
  
  const response = await api.get('/anime/', { params })
  filteredAnime.value = response.data.results
  totalPages.value = Math.ceil(response.data.count / itemsPerPage.value)
}

watch([selectedGenres, selectedYearRange, selectedStatuses, selectedTypes, selectedEpisodesRange, selectedRatingRange, currentSort, itemsPerPage], () => {
  currentPage.value = 1
  applyFilters()
  loadAnime()
}, { deep: true })
</script>
```

---

## Адаптация для разных контекстов

### Поиск в навбаре

```vue
<SearchBar
  variant="header"
  placeholder="Поиск..."
  :categories="[
    { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 5 },
    { id: 'users', name: 'Пользователи', icon: 'users', enabled: true, limit: 3 }
  ]"
  min-query-length="3"
  debounce-time="400"
/>
```

### Поиск на странице каталога

```vue
<SearchBar
  variant="page"
  placeholder="Поиск аниме, пользователей, плейлистов..."
  :categories="[
    { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 8 },
    { id: 'users', name: 'Пользователи', icon: 'users', enabled: true, limit: 5 },
    { id: 'playlists', name: 'Плейлисты', icon: 'playlists', enabled: true, limit: 5 }
  ]"
  min-query-length="2"
  debounce-time="500"
/>
```

### Фильтры для каталога аниме

```vue
<AnimeFilters
  :available-genres="animeGenres"
  :available-statuses="animeStatuses"
  :available-types="animeTypes"
  :min-year="1990"
  :max-year="2025"
  @filters-changed="handleFiltersChanged"
/>
```

### Фильтры для поиска пользователей

```vue
<FilterBlock title="Фильтры пользователей">
  <YearFilter v-model="selectedYearRange" />
  <StatusFilter v-model="selectedStatuses" />
</FilterBlock>
```
