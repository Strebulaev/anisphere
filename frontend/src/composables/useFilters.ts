import { ref, computed, watch, type ComputedRef, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export interface FilterOption {
  value: string | number
  label: string
  count?: number
}

export interface GenreFilter {
  genres: string[]
}

export interface YearFilter {
  from?: number
  to?: number
}

export interface StatusFilter {
  statuses: string[]
}

export interface TypeFilter {
  types: string[]
}

export interface EpisodesFilter {
  from?: number
  to?: number
}

export interface RatingFilter {
  from?: number
  to?: number
}

export interface SortFilter {
  field: string
  order: 'asc' | 'desc'
}

export interface ActiveFilters {
  genres?: string[]
  year?: { from?: number; to?: number }
  status?: string[]
  type?: string[]
  episodes?: { from?: number; to?: number }
  rating?: { from?: number; to?: number }
  sort?: { field: string; order: 'asc' | 'desc' }
}

export interface UseFiltersOptions {
  persistToUrl?: boolean
  persistToLocalStorage?: boolean
  localStorageKey?: string
  defaultSort?: { field: string; order: 'asc' | 'desc' }
  defaultItemsPerPage?: number
  availableGenres?: FilterOption[]
  availableStatuses?: FilterOption[]
  availableTypes?: FilterOption[]
  availableSortOptions?: FilterOption[]
  minYear?: number
  maxYear?: number
}

export interface UseFiltersReturn {
  selectedGenres: Ref<string[]>
  selectedYearRange: Ref<{ from?: number; to?: number }>
  selectedStatuses: Ref<string[]>
  selectedTypes: Ref<string[]>
  selectedEpisodesRange: Ref<{ from?: number; to?: number }>
  selectedRatingRange: Ref<{ from?: number; to?: number }>
  currentSort: Ref<{ field: string; order: 'asc' | 'desc' }>
  itemsPerPage: Ref<number>
  isFiltersCollapsed: Ref<boolean>

  hasActiveFilters: ComputedRef<boolean>
  activeFiltersCount: ComputedRef<number>
  activeFiltersList: ComputedRef<ActiveFilters>

  toggleGenre: (genre: string) => void
  selectAllGenres: () => void
  clearGenres: () => void
  
  setYearRange: (from?: number, to?: number) => void
  clearYearRange: () => void
  
  toggleStatus: (status: string) => void
  selectAllStatuses: () => void
  clearStatuses: () => void
  
  toggleType: (type: string) => void
  selectAllTypes: () => void
  clearTypes: () => void
  
  setEpisodesRange: (from?: number, to?: number) => void
  clearEpisodesRange: () => void
  
  setRatingRange: (from?: number, to?: number) => void
  clearRatingRange: () => void
  
  setSort: (field: string, order?: 'asc' | 'desc') => void
  toggleSortOrder: () => void
  
  clearAllFilters: () => void
  clearFilter: (filterType: string) => void
  
  toggleFiltersCollapsed: () => void
  
  applyFilters: () => void
  resetFilters: () => void
  getQueryParams: () => Record<string, any>
  loadFromQuery: (params: Record<string, any>) => void
  saveToLocalStorage: () => void
  loadFromLocalStorage: () => void
}

const STORAGE_KEY_PREFIX = 'anime-filters-'

export function useFilters(options: UseFiltersOptions = {}): UseFiltersReturn {
  const route = useRoute()
  const router = useRouter()

  const {
    persistToUrl = true,
    persistToLocalStorage = true,
    localStorageKey = 'anime-catalog',
    defaultSort = { field: 'score', order: 'desc' },
    defaultItemsPerPage = 20,
    availableGenres = [],
    availableStatuses = [],
    availableTypes = [],
    availableSortOptions = [],
    minYear = 1990,
    maxYear = new Date().getFullYear() + 1
  } = options

  const selectedGenres = ref<string[]>([])
  const selectedYearRange = ref<{ from?: number; to?: number }>({})
  const selectedStatuses = ref<string[]>([])
  const selectedTypes = ref<string[]>([])
  const selectedEpisodesRange = ref<{ from?: number; to?: number }>({})
  const selectedRatingRange = ref<{ from?: number; to?: number }>({})
  const currentSort = ref<{ field: string; order: 'asc' | 'desc' }>(defaultSort)
  const itemsPerPage = ref(defaultItemsPerPage)
  const isFiltersCollapsed = ref(false)

  const hasActiveFilters = computed(() => {
    return activeFiltersCount.value > 0
  })

  const activeFiltersCount = computed(() => {
    let count = 0
    if (selectedGenres.value.length > 0) count += selectedGenres.value.length
    if (selectedYearRange.value.from || selectedYearRange.value.to) count++
    if (selectedStatuses.value.length > 0) count += selectedStatuses.value.length
    if (selectedTypes.value.length > 0) count += selectedTypes.value.length
    if (selectedEpisodesRange.value.from || selectedEpisodesRange.value.to) count++
    if (selectedRatingRange.value.from || selectedRatingRange.value.to) count++
    if (currentSort.value.field !== defaultSort.field || currentSort.value.order !== defaultSort.order) count++
    return count
  })

  const activeFiltersList = computed<ActiveFilters>(() => {
    const filters: ActiveFilters = {}
    if (selectedGenres.value.length > 0) filters.genres = selectedGenres.value
    if (selectedYearRange.value.from || selectedYearRange.value.to) {
      filters.year = selectedYearRange.value
    }
    if (selectedStatuses.value.length > 0) filters.status = selectedStatuses.value
    if (selectedTypes.value.length > 0) filters.type = selectedTypes.value
    if (selectedEpisodesRange.value.from || selectedEpisodesRange.value.to) {
      filters.episodes = selectedEpisodesRange.value
    }
    if (selectedRatingRange.value.from || selectedRatingRange.value.to) {
      filters.rating = selectedRatingRange.value
    }
    if (currentSort.value.field !== defaultSort.field || currentSort.value.order !== defaultSort.order) {
      filters.sort = currentSort.value
    }
    return filters
  })

  const toggleGenre = (genre: string) => {
    const index = selectedGenres.value.indexOf(genre)
    if (index > -1) {
      selectedGenres.value.splice(index, 1)
    } else {
      selectedGenres.value.push(genre)
    }
  }

  const selectAllGenres = () => {
    selectedGenres.value = availableGenres.map(g => g.value.toString())
  }

  const clearGenres = () => {
    selectedGenres.value = []
  }

  const setYearRange = (from?: number, to?: number) => {
    selectedYearRange.value = { from, to }
  }

  const clearYearRange = () => {
    selectedYearRange.value = {}
  }

  const toggleStatus = (status: string) => {
    const index = selectedStatuses.value.indexOf(status)
    if (index > -1) {
      selectedStatuses.value.splice(index, 1)
    } else {
      selectedStatuses.value.push(status)
    }
  }

  const selectAllStatuses = () => {
    selectedStatuses.value = availableStatuses.map(s => s.value.toString())
  }

  const clearStatuses = () => {
    selectedStatuses.value = []
  }

  const toggleType = (type: string) => {
    const index = selectedTypes.value.indexOf(type)
    if (index > -1) {
      selectedTypes.value.splice(index, 1)
    } else {
      selectedTypes.value.push(type)
    }
  }

  const selectAllTypes = () => {
    selectedTypes.value = availableTypes.map(t => t.value.toString())
  }

  const clearTypes = () => {
    selectedTypes.value = []
  }

  const setEpisodesRange = (from?: number, to?: number) => {
    selectedEpisodesRange.value = { from, to }
  }

  const clearEpisodesRange = () => {
    selectedEpisodesRange.value = {}
  }

  const setRatingRange = (from?: number, to?: number) => {
    selectedRatingRange.value = { from, to }
  }

  const clearRatingRange = () => {
    selectedRatingRange.value = {}
  }

  const setSort = (field: string, order?: 'asc' | 'desc') => {
    currentSort.value = { field, order: order || 'desc' }
  }

  const toggleSortOrder = () => {
    currentSort.value.order = currentSort.value.order === 'asc' ? 'desc' : 'asc'
  }

  const clearAllFilters = () => {
    selectedGenres.value = []
    selectedYearRange.value = {}
    selectedStatuses.value = []
    selectedTypes.value = []
    selectedEpisodesRange.value = {}
    selectedRatingRange.value = {}
    currentSort.value = defaultSort
    itemsPerPage.value = defaultItemsPerPage
  }

  const clearFilter = (filterType: string) => {
    switch (filterType) {
      case 'genres':
        clearGenres()
        break
      case 'year':
        clearYearRange()
        break
      case 'status':
        clearStatuses()
        break
      case 'type':
        clearTypes()
        break
      case 'episodes':
        clearEpisodesRange()
        break
      case 'rating':
        clearRatingRange()
        break
      case 'sort':
        currentSort.value = defaultSort
        break
    }
  }

  const toggleFiltersCollapsed = () => {
    isFiltersCollapsed.value = !isFiltersCollapsed.value
    saveToLocalStorage()
  }

  const applyFilters = () => {
    if (persistToUrl) {
      const params = getQueryParams()
      router.push({ query: params })
    }
    if (persistToLocalStorage) {
      saveToLocalStorage()
    }
  }

  const resetFilters = () => {
    clearAllFilters()
    if (persistToUrl) {
      router.push({ query: {} })
    }
    if (persistToLocalStorage) {
      saveToLocalStorage()
    }
  }

  const getQueryParams = (): Record<string, any> => {
    const params: Record<string, any> = {}
    
    if (selectedGenres.value.length > 0) {
      params.genres = selectedGenres.value.join(',')
    }
    if (selectedYearRange.value.from) {
      params.year_from = selectedYearRange.value.from
    }
    if (selectedYearRange.value.to) {
      params.year_to = selectedYearRange.value.to
    }
    if (selectedStatuses.value.length > 0) {
      params.status = selectedStatuses.value.join(',')
    }
    if (selectedTypes.value.length > 0) {
      params.type = selectedTypes.value.join(',')
    }
    if (selectedEpisodesRange.value.from) {
      params.episodes_from = selectedEpisodesRange.value.from
    }
    if (selectedEpisodesRange.value.to) {
      params.episodes_to = selectedEpisodesRange.value.to
    }
    if (selectedRatingRange.value.from) {
      params.rating_from = selectedRatingRange.value.from
    }
    if (selectedRatingRange.value.to) {
      params.rating_to = selectedRatingRange.value.to
    }
    if (currentSort.value.field !== defaultSort.field || currentSort.value.order !== defaultSort.order) {
      params.ordering = currentSort.value.order === 'asc' ? currentSort.value.field : `-${currentSort.value.field}`
    }
    if (itemsPerPage.value !== defaultItemsPerPage) {
      params.page_size = itemsPerPage.value
    }
    
    return params
  }

  const loadFromQuery = (params: Record<string, any>) => {
    if (params.genres) {
      selectedGenres.value = params.genres.split(',').map((g: string) => g.trim())
    }
    if (params.year_from) {
      selectedYearRange.value.from = parseInt(params.year_from)
    }
    if (params.year_to) {
      selectedYearRange.value.to = parseInt(params.year_to)
    }
    if (params.status) {
      selectedStatuses.value = params.status.split(',').map((s: string) => s.trim())
    }
    if (params.type) {
      selectedTypes.value = params.type.split(',').map((t: string) => t.trim())
    }
    if (params.episodes_from) {
      selectedEpisodesRange.value.from = parseInt(params.episodes_from)
    }
    if (params.episodes_to) {
      selectedEpisodesRange.value.to = parseInt(params.episodes_to)
    }
    if (params.rating_from) {
      selectedRatingRange.value.from = parseFloat(params.rating_from)
    }
    if (params.rating_to) {
      selectedRatingRange.value.to = parseFloat(params.rating_to)
    }
    if (params.ordering) {
      const ordering = params.ordering as string
      if (ordering.startsWith('-')) {
        currentSort.value = { field: ordering.slice(1), order: 'desc' }
      } else {
        currentSort.value = { field: ordering, order: 'asc' }
      }
    }
    if (params.page_size) {
      itemsPerPage.value = parseInt(params.page_size)
    }
  }

  const saveToLocalStorage = () => {
    if (!persistToLocalStorage) return
    
    const data = {
      genres: selectedGenres.value,
      yearRange: selectedYearRange.value,
      statuses: selectedStatuses.value,
      types: selectedTypes.value,
      episodesRange: selectedEpisodesRange.value,
      ratingRange: selectedRatingRange.value,
      sort: currentSort.value,
      itemsPerPage: itemsPerPage.value,
      isCollapsed: isFiltersCollapsed.value
    }
    
    try {
      localStorage.setItem(`${STORAGE_KEY_PREFIX}${localStorageKey}`, JSON.stringify(data))
    } catch (e) {
      console.error('Error saving filters to localStorage:', e)
    }
  }

  const loadFromLocalStorage = () => {
    if (!persistToLocalStorage) return
    
    try {
      const stored = localStorage.getItem(`${STORAGE_KEY_PREFIX}${localStorageKey}`)
      if (stored) {
        const data = JSON.parse(stored)
        if (data.genres) selectedGenres.value = data.genres
        if (data.yearRange) selectedYearRange.value = data.yearRange
        if (data.statuses) selectedStatuses.value = data.statuses
        if (data.types) selectedTypes.value = data.types
        if (data.episodesRange) selectedEpisodesRange.value = data.episodesRange
        if (data.ratingRange) selectedRatingRange.value = data.ratingRange
        if (data.sort) currentSort.value = data.sort
        if (data.itemsPerPage) itemsPerPage.value = data.itemsPerPage
        if (typeof data.isCollapsed === 'boolean') isFiltersCollapsed.value = data.isCollapsed
      }
    } catch (e) {
      console.error('Error loading filters from localStorage:', e)
    }
  }

  if (persistToUrl) {
    loadFromQuery(route.query as Record<string, any>)
  } else {
    loadFromLocalStorage()
  }

  watch(() => route.query, (newQuery) => {
    if (persistToUrl) {
      loadFromQuery(newQuery as Record<string, any>)
    }
  })

  return {
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
  }
}
