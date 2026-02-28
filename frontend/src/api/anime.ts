import apiClient from './client'

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

// Типы для фильтров
export type AnimeStatus = 'ongoing' | 'announced' | 'released'
export type AnimeType = 'tv' | 'movie' | 'ova' | 'ona' | 'special'
export type Season = 'winter' | 'spring' | 'summer' | 'fall'
export type SortOrder = 'score' | '-score' | 'year' | '-year' | 'popularity' | '-popularity' | 'title_ru' | '-title_ru' | 'favorites' | '-favorites' | 'created_at' | '-created_at' | string

export interface AnimeFilters {
  // Основные фильтры
  search?: string
  genres?: string[] | string // множественный выбор
  genre_logic?: 'AND' | 'OR' // логика жанров
  year_from?: number
  year_to?: number
  status?: (AnimeStatus | string)[] | AnimeStatus | string
  type?: (AnimeType | string)[] | AnimeType | string
  episodes_from?: number
  episodes_to?: number
  score_from?: number
  score_to?: number
  studio?: string[] | string
  country?: string[] | string
  rus_translation?: 'full' | 'partial' | 'none' | null
  age_rating?: string[] | string
  has_awards?: boolean
  
  // Дополнительные фильтры
  duration_from?: number // длительность эпизода в минутах
  duration_to?: number
  author?: string // автор оригинала
  director?: string
  composer?: string
  season?: Season
  season_year?: number
  popularity_from?: number
  popularity_to?: number
  added_from?: string // дата в формате YYYY-MM-DD
  added_to?: string
  in_collection?: boolean // в моей коллекции
  my_ratings?: boolean // с моими оценками
  
  // Сортировка и пагинация
  ordering?: SortOrder
  page?: number
  page_size?: number
}

// API методы для работы с аниме
export const animeApi = {
  // Поиск аниме
  search: async (query: string, options?: SearchOptions): Promise<SearchResults> => {
    const params: any = { q: query }
    if (options?.limit) {
      params.limit = options.limit
    }
    const response = await apiClient.get<SearchResults>('/anime/search/', { params })
    return response.data
  },

  // Получить список аниме с фильтрами
  list: async (filters?: AnimeFilters): Promise<AnimeListResponse> => {
    const params: any = {}
    
    if (!filters) {
      const response = await apiClient.get<AnimeListResponse>('/anime/', { params })
      return response.data
    }
    
    // Пагинация
    if (filters.page) params.page = filters.page
    if (filters.page_size) params.page_size = filters.page_size
    else params.page_size = 50
    
    // Сортировка
    if (filters.ordering) params.ordering = filters.ordering
    else params.ordering = '-score'
    
    // Поиск
    if (filters.search) params.search = filters.search
    
    // Жанры
    if (filters.genres && filters.genres.length > 0) {
      params.genres = Array.isArray(filters.genres) ? (filters.genres as string[]).join(',') : filters.genres
      params.genre_logic = filters.genre_logic || 'OR'
    }
    
    // Год выпуска
    if (filters.year_from) params.year_from = filters.year_from
    if (filters.year_to) params.year_to = filters.year_to
    
    // Статус
    if (filters.status) {
      if (Array.isArray(filters.status)) {
        params.status = (filters.status as string[]).join(',')
      } else {
        params.status = filters.status as string
      }
    }
    
    // Тип
    if (filters.type) {
      if (Array.isArray(filters.type)) {
        params.type = (filters.type as string[]).join(',')
      } else {
        params.type = filters.type as string
      }
    }
    
    // Количество серий
    if (filters.episodes_from) params.episodes_from = filters.episodes_from
    if (filters.episodes_to) params.episodes_to = filters.episodes_to
    
    // Рейтинг
    if (filters.score_from) params.score_from = filters.score_from
    if (filters.score_to) params.score_to = filters.score_to
    
    // Студия
    if (filters.studio && filters.studio.length > 0) {
      params.studio = Array.isArray(filters.studio) ? (filters.studio as string[]).join(',') : filters.studio
    }
    
    // Страна
    if (filters.country && filters.country.length > 0) {
      params.country = Array.isArray(filters.country) ? (filters.country as string[]).join(',') : filters.country
    }
    
    // Озвучка
    if (filters.rus_translation) params.rus_translation = filters.rus_translation
    
    // Возрастной рейтинг
    if (filters.age_rating && filters.age_rating.length > 0) {
      params.age_rating = Array.isArray(filters.age_rating) ? (filters.age_rating as string[]).join(',') : filters.age_rating
    }
    
    // Награды
    if (filters.has_awards) params.has_awards = 'true'
    
    // Длительность эпизода
    if (filters.duration_from) params.duration_from = filters.duration_from
    if (filters.duration_to) params.duration_to = filters.duration_to
    
    // Автор оригинала
    if (filters.author) params.author = filters.author
    
    // Режиссёр
    if (filters.director) params.director = filters.director
    
    // Композитор
    if (filters.composer) params.composer = filters.composer
    
    // Сезон
    if (filters.season) params.season = filters.season
    if (filters.season_year) params.season_year = filters.season_year
    
    // Популярность
    if (filters.popularity_from) params.popularity_from = filters.popularity_from
    if (filters.popularity_to) params.popularity_to = filters.popularity_to
    
    // Дата добавления
    if (filters.added_from) params.added_from = filters.added_from
    if (filters.added_to) params.added_to = filters.added_to
    
    // В коллекции / с оценками
    if (filters.in_collection !== undefined) params.in_collection = filters.in_collection
    if (filters.my_ratings !== undefined) params.my_ratings = filters.my_ratings
    
    const response = await apiClient.get<AnimeListResponse>('/anime/', { params })
    return response.data
  },

  // Получить детальную информацию об аниме
  get: async (id: number | string): Promise<Anime> => {
    const response = await apiClient.get<Anime>(`/anime/${id}/`)
    return response.data
  },

  // Получить эпизоды аниме
  getEpisodes: async (id: number | string): Promise<{
    anime_id: number
    anime_title: string
    episodes: any[]
    total_episodes: number
  }> => {
    const response = await apiClient.get(`/anime/${id}/episodes/`)
    return response.data
  },

  // Получить переводы аниме
  getTranslations: async (id: number | string): Promise<{
    anime_id: number
    anime_title: string
    translations: any[]
    total_translations: number
  }> => {
    const response = await apiClient.get(`/anime/${id}/translations/`)
    return response.data
  },

  // Получить ссылку на видео
  getVideoLink: async (id: number | string, params: {
    episode?: number
    translation_id?: string
    quality?: string
  }): Promise<any> => {
    const response = await apiClient.get(`/anime/${id}/get_video_link/`, { params })
    return response.data
  },

  // Сохранить прогресс просмотра
  saveWatchProgress: async (id: number | string, data: {
    episode_id: number
    current_time: number
    duration?: number
  }): Promise<any> => {
    const response = await apiClient.post(`/anime/${id}/save_watch_progress/`, data)
    return response.data
  },

  // Получить прогресс просмотра
  getWatchProgress: async (id: number | string): Promise<any> => {
    const response = await apiClient.get(`/anime/${id}/watch_progress/`)
    return response.data
  },

  // Получить онгоинги
  getOngoings: async (limit: number = 12): Promise<Anime[]> => {
    const response = await apiClient.get<AnimeListResponse>('/anime/', {
      params: { status: 'ongoing', ordering: '-score', page_size: limit }
    })
    return response.data.results || []
  },

  // Получить анонсы
  getAnnouncements: async (limit: number = 12): Promise<Anime[]> => {
    const response = await apiClient.get<AnimeListResponse>('/anime/', {
      params: { status: 'announced', ordering: '-year', page_size: limit }
    })
    return response.data.results || []
  },

  // Получить рекомендации (базовая реализация на сервере)
  getRecommendations: async (limit: number = 12): Promise<Anime[]> => {
    const response = await apiClient.get<AnimeListResponse>('/anime/', {
      params: { ordering: '-score,-favorites', page_size: limit }
    })
    return response.data.results || []
  },

  // Получить случайное аниме
  getRandomAnime: async (): Promise<Anime> => {
    const response = await apiClient.get<Anime>('/anime/random/')
    return response.data
  },

  // Получить несколько случайных аниме
  getRandomAnimeList: async (limit: number = 6): Promise<Anime[]> => {
    const response = await apiClient.get<Anime[]>('/anime/random/', {
      params: { limit }
    })
    return Array.isArray(response.data) ? response.data : [response.data]
  }
}

export default animeApi
