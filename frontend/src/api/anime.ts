import apiClient from './client'
import type { HomeData } from '@/types'

export interface Anime {
  id: number
  shikimori_id?: string
  title_ru: string
  title_en?: string
  title_jp?: string
  year?: number
  status?: string
  episodes?: number
  score?: number
  poster_url?: string
  poster_image_url?: string
  description?: string
  genres?: string[]
  source?: string
  match_type?: 'exact' | 'fuzzy'
}

export interface SearchResults {
  query: string
  results: Anime[]
  total: number
  source: string
  has_fuzzy_matches?: boolean
}

export interface AnimeListResponse {
  results: Anime[]
  count: number
  page: number
  page_size: number
  total_pages: number
}

export interface SearchOptions {
  limit?: number
}

export type SortOrder =
  | 'score' | '-score'
  | 'year' | '-year'
  | 'title_ru' | '-title_ru'
  | 'title_en' | '-title_en'
  | 'episodes' | '-episodes'
  | 'created_at' | '-created_at'
  | (string & {})  // разрешает произвольные строки без потери типовых подсказок

export interface AnimeFilters {
  // Поиск
  search?: string

  // Жанры
  genres?: string[] | string
  genre_logic?: 'AND' | 'OR'

  // Тип и статус — multi-select, передаются через запятую
  // Допустимые status: ongoing | finished | announced | canceled
  // Допустимые type:   tv | movie | ova | ona | special | music
  status?: string[] | string
  type?:   string[] | string

  // Диапазоны
  year_from?: number
  year_to?: number
  score_from?: number
  score_to?: number
  episodes_from?: number
  episodes_to?: number
  duration_from?: number
  duration_to?: number

  // Студия (multi-select, icontains по JSON-полю studios)
  studio?: string[] | string

  // Дополнительные — бэкенд принимает, но поля в модели нет (игнорируются)
  country?: string[] | string
  age_rating?: string[] | string
  rus_translation?: 'full' | 'partial' | 'none' | null
  has_awards?: boolean
  author?: string
  director?: string
  composer?: string
  season?: 'winter' | 'spring' | 'summer' | 'fall'
  season_year?: number

  // Сортировка и пагинация
  ordering?: SortOrder
  page?: number
  page_size?: number
}

const toComma = (v: string[] | string | undefined): string | undefined => {
  if (!v) return undefined
  if (Array.isArray(v)) {
    const filtered = v.filter(Boolean)
    return filtered.length ? filtered.join(',') : undefined
  }
  return v || undefined
}

export const animeApi = {
  search: async (query: string, options?: SearchOptions): Promise<SearchResults> => {
    const params: any = { q: query }
    if (options?.limit) params.limit = options.limit
    const response = await apiClient.get<SearchResults>('/anime/search/', { params })
    return response.data
  },

  list: async (filters?: AnimeFilters): Promise<AnimeListResponse> => {
    const params: Record<string, any> = {}

    if (!filters) {
      const response = await apiClient.get<AnimeListResponse>('/anime/', { params })
      return response.data
    }

    // Пагинация
    if (filters.page)       params.page      = filters.page
    params.page_size = filters.page_size ?? 50

    // Сортировка
    params.ordering = filters.ordering ?? '-score'

    // Поиск
    if (filters.search) params.search = filters.search

    // Жанры
    const genres = toComma(filters.genres)
    if (genres) {
      params.genres      = genres
      params.genre_logic = filters.genre_logic ?? 'OR'
    }

    // Год
    if (filters.year_from != null) params.year_from = filters.year_from
    if (filters.year_to   != null) params.year_to   = filters.year_to

    // Статус (multi → comma-separated)
    const status = toComma(filters.status)
    if (status) params.status = status

    // Тип (multi → comma-separated)
    const type = toComma(filters.type)
    if (type) params.type = type

    // Серии
    if (filters.episodes_from != null) params.episodes_from = filters.episodes_from
    if (filters.episodes_to   != null) params.episodes_to   = filters.episodes_to

    // Рейтинг
    if (filters.score_from != null) params.score_from = filters.score_from
    if (filters.score_to   != null) params.score_to   = filters.score_to

    // Студия (multi → comma-separated)
    const studio = toComma(filters.studio)
    if (studio) params.studio = studio

    // Длительность
    if (filters.duration_from != null) params.duration_from = filters.duration_from
    if (filters.duration_to   != null) params.duration_to   = filters.duration_to

    // Дополнительные (бэкенд принимает, молча игнорирует несуществующие поля)
    if (filters.season)      params.season      = filters.season
    if (filters.season_year) params.season_year = filters.season_year
    if (filters.author)      params.author      = filters.author
    if (filters.director)    params.director    = filters.director

    const country    = toComma(filters.country)
    const age_rating = toComma(filters.age_rating)
    if (country)    params.country    = country
    if (age_rating) params.age_rating = age_rating
    if (filters.rus_translation) params.rus_translation = filters.rus_translation
    if (filters.has_awards)      params.has_awards      = 'true'

    const response = await apiClient.get<AnimeListResponse>('/anime/', { params })
    return response.data
  },

  get: async (id: number | string): Promise<Anime> => {
    const response = await apiClient.get<Anime>(`/anime/${id}/`)
    return response.data
  },

  getEpisodes: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/episodes/`)
    return response.data
  },

  getTranslations: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/translations/`)
    return response.data
  },

  getVideoLink: async (id: number | string, params: {
    episode?: number; translation_id?: string; quality?: string
  }) => {
    const response = await apiClient.get(`/anime/${id}/get_video_link/`, { params })
    return response.data
  },

  saveWatchProgress: async (id: number | string, data: {
    episode_id: number; current_time: number; duration?: number
  }) => {
    const response = await apiClient.post(`/anime/${id}/save_watch_progress/`, data)
    return response.data
  },

  getWatchProgress: async (id: number | string) => {
    const response = await apiClient.get(`/anime/${id}/watch_progress/`)
    return response.data
  },

  getOngoings: async (): Promise<Anime[]> => {
    const PAGE_SIZE = 200
    const all: Anime[] = []
    let page = 1
    while (true) {
      const response = await apiClient.get<AnimeListResponse>('/anime/', {
        params: { status: 'ongoing', ordering: '-score', page_size: PAGE_SIZE, page }
      })
      const results = response.data.results || []
      all.push(...results)
      if (page >= (response.data.total_pages ?? 1) || !results.length) break
      page++
    }
    return all
  },

  getAnnouncements: async (): Promise<Anime[]> => {
    const PAGE_SIZE = 200
    const all: Anime[] = []
    let page = 1
    while (true) {
      const response = await apiClient.get<AnimeListResponse>('/anime/', {
        params: { status: 'announced', ordering: '-year', page_size: PAGE_SIZE, page }
      })
      const results = response.data.results || []
      all.push(...results)
      if (page >= (response.data.total_pages ?? 1) || !results.length) break
      page++
    }
    return all
  },

  getRecommendations: async (limit: number = 12): Promise<Anime[]> => {
    const response = await apiClient.get<AnimeListResponse>('/anime/', {
      params: { ordering: '-score', page_size: limit }
    })
    return response.data.results || []
  },

  getRandomAnime: async (): Promise<Anime> => {
    const response = await apiClient.get<Anime>('/anime/random/')
    return response.data
  },

  getRandomAnimeList: async (limit: number = 6): Promise<Anime[]> => {
    const response = await apiClient.get<Anime[]>('/anime/random/', { params: { limit } })
    return Array.isArray(response.data) ? response.data : [response.data]
  },

  getHomeData: async (): Promise<HomeData> => {
    const response = await apiClient.get<HomeData>('/anime/home/')
    return response.data
  },

  addToLibrary: async (data: {
    anime: number
    status: 'planned' | 'started' | 'completed' | 'dropped'
    rating?: number | null
    current_episode?: number
    notes?: string
  }) => {
    const response = await apiClient.post('/users/library/', data)
    return response.data
  }
}

export default animeApi
