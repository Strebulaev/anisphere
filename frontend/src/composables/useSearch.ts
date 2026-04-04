import { ref, computed, watch, type ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'
import api from '@/api'

export interface AnimeResult {
  id: number
  title_ru?: string
  title_en?: string
  poster_url?: string
  year?: number
  episodes?: number
  score?: number
  status?: string
  kind?: string
}

export interface UserResult {
  id: number
  username: string
  display_name?: string
  avatar_url?: string
  nickname?: string
  status?: string
}

export interface PlaylistResult {
  id: number
  title: string
  items?: {
    id: number
    poster_url?: string
    title_ru?: string
    title_en?: string
  }[]
}

export interface GroupResult {
  id: number
  name: string
  avatar_url?: string
  members_count?: number
}

export interface SearchResults {
  anime?: AnimeResult[]
  users?: UserResult[]
  playlists?: PlaylistResult[]
  groups?: GroupResult[]
}

export interface SearchCategory {
  id: string
  name: string
  icon: string
  enabled: boolean
  limit?: number
}

export interface UseSearchOptions {
  categories?: SearchCategory[]
  debounceTime?: number
  minQueryLength?: number
  placeholder?: string
  searchRoute?: string
  searchQueryKey?: string
}

export interface UseSearchReturn {
  searchQuery: ReturnType<typeof ref<string>>
  isFocused: ReturnType<typeof ref<boolean>>
  isLoading: ReturnType<typeof ref<boolean>>
  results: ReturnType<typeof ref<SearchResults>>
  showSuggestions: ComputedRef<boolean>
  hasResults: ComputedRef<boolean>
  showClearButton: ComputedRef<boolean>
  handleInput: (event: Event) => void
  handleSearch: () => void
  clearSearch: () => void
  handleFocus: () => void
  handleBlur: () => void
  selectItem: (category: string, item: any) => void
  getMediaUrl: (url: string | undefined) => string | undefined
}

const defaultCategories: SearchCategory[] = [
  {
    id: 'anime',
    name: 'Аниме',
    icon: 'anime',
    enabled: true,
    limit: 5
  },
  {
    id: 'users',
    name: 'Пользователи',
    icon: 'users',
    enabled: true,
    limit: 3
  },
  {
    id: 'playlists',
    name: 'Плейлисты',
    icon: 'playlists',
    enabled: true,
    limit: 3
  },
  {
    id: 'groups',
    name: 'Группы',
    icon: 'groups',
    enabled: false,
    limit: 3
  }
]

export function useSearch(options: UseSearchOptions = {}): UseSearchReturn {
  const router = useRouter()

  const {
    categories = defaultCategories,
    debounceTime = 400,
    minQueryLength = 3,
    placeholder = 'Поиск...',
    searchRoute = '/anime',
    searchQueryKey = 'search'
  } = options

  const searchQuery = ref('')
  const isFocused = ref(false)
  const isLoading = ref(false)
  const results = ref<SearchResults>({})

  let searchTimeout: number | null = null

  const showSuggestions = computed(() => {
    return isFocused.value && (searchQuery.value.length >= minQueryLength || hasResults.value)
  })

  const hasResults = computed(() => {
    return Object.values(results.value).some(arr => arr && arr.length > 0)
  })

  const showClearButton = computed(() => {
    return searchQuery.value.length > 0
  })

  const performSearch = async (query: string) => {
    if (!query || query.length < minQueryLength) {
      results.value = {}
      return
    }

    isLoading.value = true
    const newResults: SearchResults = {}

    try {
      const enabledCategories = categories.filter(cat => cat.enabled)

      await Promise.all(
        enabledCategories.map(async (category) => {
          try {
            let data: any[] = []

            switch (category.id) {
              case 'anime':
                const animeResponse = await api.get('/anime/search/', {
                  params: { q: query, limit: category.limit || 5 }
                })
                data = animeResponse.data.results || []
                break

              case 'users':
                const usersResponse = await api.get('/users/search/', {
                  params: { search: query, limit: category.limit || 3 }
                })
                data = usersResponse.data.results || []
                break

              case 'playlists':
                const playlistsResponse = await api.get('/social/playlists/search/', {
                  params: { q: query, limit: category.limit || 3 }
                })
                data = playlistsResponse.data.results || []
                break

              case 'groups':
                const groupsResponse = await api.get('/social/groups/search/', {
                  params: { q: query, limit: category.limit || 3 }
                })
                data = groupsResponse.data.results || []
                break
            }

            if (data.length > 0) {
              newResults[category.id as keyof SearchResults] = data
            }
          } catch (error: any) {
            console.error(`Error searching ${category.id}:`, error, error?.response?.data)
          }
        })
      )

      results.value = newResults
    } catch (error) {
      console.error('Search error:', error)
      results.value = {}
    } finally {
      isLoading.value = false
    }
  }

  const handleInput = (event: Event) => {
    const target = event.target as HTMLInputElement
    searchQuery.value = target.value || ''

    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }

    if (searchQuery.value.trim().length < minQueryLength) {
      results.value = {}
      return
    }

    searchTimeout = window.setTimeout(() => {
      performSearch(searchQuery.value)
    }, debounceTime)
  }

  const handleSearch = () => {
    if (searchQuery.value.trim()) {
      router.push({
        path: searchRoute,
        query: { [searchQueryKey]: searchQuery.value.trim() }
      })
      isFocused.value = false
    }
  }

  const clearSearch = () => {
    searchQuery.value = ''
    results.value = {}
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
  }

  const handleFocus = () => {
    isFocused.value = true
  }

  const handleBlur = () => {
    setTimeout(() => {
      isFocused.value = false
    }, 200)
  }

  const selectItem = (category: string, item: any) => {
    switch (category) {
      case 'anime':
        router.push(`/anime/${item.id}`)
        break
      case 'users':
        router.push(`/profile/${item.id}`)
        break
      case 'playlists':
        router.push(`/playlists/${item.id}`)
        break
      case 'groups':
        router.push(`/groups/${item.id}`)
        break
    }
    isFocused.value = false
  }

  return {
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
  }
}
