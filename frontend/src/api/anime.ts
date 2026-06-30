import apiClient from './client'
import type { HomeData } from '@/types'

export interface Anime {
  id: number
  slug?: string
  mal_id?: number
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
  | (string & {})

export interface AnimeFilters {
  search?: string

  genres?: string[] | string
  genre_logic?: 'AND' | 'OR'

  status?: string[] | string
  type?:   string[] | string

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

  // Исключить из коллекции пользователя (статусы библиотек)
  excluded_library_statuses?: string[]

  // Дополнительные - бэкенд принимает, но поля в модели нет (игнорируются)
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
  shuffle?: boolean  // Перемешивание результатов
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
  /**
   * Поиск через каталог (как в /anime каталоге)
   * Использует endpoint /anime/ с параметром search для консистентности
   */
  search: async (query: string, options?: SearchOptions): Promise<SearchResults> => {
    // Используем тот же endpoint что и каталог - /anime/ с search параметром
    const params: any = { 
      search: query,
      page_size: options?.limit || 500
    }
    const response = await apiClient.get<AnimeListResponse>('/anime/', { params })
    
    // Форматируем ответ как SearchResults для совместимости
    return {
      query: query,
      results: response.data.results || [],
      total: response.data.count || 0,
      source: 'database'
    }
  },

  /**
   * Старый search endpoint (для совместимости)
   * @deprecated Используйте основной search() вместо этого
   */
  searchLegacy: async (query: string, options?: SearchOptions): Promise<SearchResults> => {
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

    // Перемешивание
    if (filters.shuffle) params.shuffle = 'true'

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

    // Исключить из коллекции пользователя
    const excludedLibraryStatuses = toComma(filters.excluded_library_statuses)
    if (excludedLibraryStatuses) params.excluded_library_statuses = excludedLibraryStatuses

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
    // Получаем анонсы из новой таблицы anime_announcements
    const all: Anime[] = []
    const existingIds = new Set<number>()
    
    try {
      const PAGE_SIZE = 200
      let page = 1
      while (true) {
        const response = await apiClient.get<AnimeListResponse>('/anime/announcements/', {
          params: { ordering: '-created_at', page_size: PAGE_SIZE, page }
        })
        const results = response.data.results || []
        for (const a of results) {
          const id = a.id
          if (id && !existingIds.has(id)) {
            existingIds.add(id)
            all.push(a)
          }
        }
        if (page >= (response.data.total_pages ?? 1) || !results.length) break
        page++
      }
    } catch (e) {
      console.warn('Failed to fetch announcements from anime_announcements:', e)
    }
    
    return all
  },

  // // getAnnouncementsFromKodik: async (): Promise<Anime[]> => {
  // //   // Используем актуальный Kodik API v2
  // //   const KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'
  // //   const all: any[] = []
  // //   let nextPage: string | null = `https://kodik-api.com/list?token=${KODIK_TOKEN}&types=anime-serial,anime&anime_status=anons&with_material_data=true&limit=100`
  // //   let iterations = 0
  // //   while (nextPage && iterations < 10) {
  // //     iterations++
  // //     try {
  // //       const res = await fetch(nextPage)
  // //       if (!res.ok) break
  // //       const data = await res.json()
  // //       const results = data.results || []
  // //       if (!results.length) break
  // //       all.push(...results)
  // //       nextPage = data.next_page || null
  // //     } catch { break }
  // //   }
    
  // //   // Если Kodik вернул данные - маппим и возвращаем
  // //   if (all.length > 0) {
  // //     const seen = new Set<string>()
  // //     const mapped: Anime[] = []
  // //     for (const item of all) {
  // //       const shikiId = item.shikimori_id
  // //       const key = shikiId ? String(shikiId) : item.id
  // //       if (seen.has(key)) continue
  // //       seen.add(key)
  // //       const md = item.material_data || {}
  // //       mapped.push({
  // //         id: shikiId || item.id,
  // //         shikimori_id: shikiId ? String(shikiId) : undefined,
  // //         title_ru: md.title || item.title || '',
  // //         title_en: item.title_orig || '',
  // //         year: item.year || md.year,
  // //         status: 'announced',
  // //         episodes: md.episodes_total || item.episodes_count || null,
  // //         score: md.shikimori_rating || md.kinopoisk_rating || null,
  // //         poster_url: md.anime_poster_url || md.poster_url || null,
  // //         description: md.anime_description || md.description || '',
  // //         genres: md.anime_genres || md.genres || [],
  // //         source: 'kodik',
  // //       } as any)
  // //     }
  // //     return mapped
  // //   }
    
  // //   // Если Kodik не вернул данные - пробуем Shikimori API
  // //   return animeApi.getAnnouncementsFromShikimori()
  // // },

  // getAnnouncementsFromShikimori: async (): Promise<Anime[]> => {
  //   // Используем Shikimori API для получения анонсов
  //   try {
  //     const all: any[] = []
  //     // Запрашиваем аниме со статусом "anons" (анонсированные)
  //     for (let page = 1; page <= 3; page++) {
  //       const res = await fetch(
  //         `https://shikimori.one/api/animes?kind=tv,movie,ona,ova,special&status=anons&order=rank&limit=50&page=${page}`,
  //         { headers: { 'Content-Type': 'application/json' } }
  //       )
  //       if (!res.ok) break
  //       const data = await res.json()
  //       if (!Array.isArray(data) || data.length === 0) break
  //       all.push(...data)
  //     }
      
  //     if (all.length === 0) return []
      
  //     // Маппинг Shikimori → формат AnimeCard
  //     const mapped: Anime[] = all.map(item => ({
  //       id: item.id,
  //       shikimori_id: String(item.id),
  //       title_ru: item.name || '',
  //       title_en: item.english || '',
  //       year: item.released_on ? new Date(item.released_on).getFullYear() : null,
  //       status: 'announced',
  //       episodes: item.episodes || null,
  //       score: item.score ? parseFloat(item.score) : null,
  //       poster_url: item.image ? `https://shikimori.one${item.image.original}` : null,
  //       description: item.description || '',
  //       genres: [],
  //       source: 'shikimori',
  //     } as any))
      
  //     return mapped
  //   } catch {
  //     return []
  //   }
  // },

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

  getPersonalizedRecommendations: async () => {
    const response = await apiClient.get('/anime/home/personalized/')
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
  },

  // ════════════════════════════════════════════════════════
  // CLIPS & SCREENSHOTS
  // ════════════════════════════════════════════════════════
  
  createClipTask: async (data: {
    anime: number
    episode: number
    season?: number
    start_time: number
    end_time: number
    label?: string
    quality?: string
  }) => {
    const response = await apiClient.post('/anime/clips/', {
      ...data,
      task_type: 'clip',
    })
    return response.data
  },

  createScreenshotTask: async (data: {
    anime: number
    episode?: number
    timestamp: number
    quality?: string
  }) => {
    const response = await apiClient.post('/anime/clips/', {
      ...data,
      task_type: 'screenshot',
    })
    return response.data
  },

  getClipTask: async (taskId: string) => {
    const response = await apiClient.get(`/anime/clips/${taskId}/`)
    return response.data
  },

  getClipTaskStatus: async (taskId: string) => {
    const response = await apiClient.get(`/anime/clips/${taskId}/status/`)
    return response.data
  },

  retryClipTask: async (taskId: string) => {
    const response = await apiClient.post(`/anime/clips/${taskId}/retry/`)
    return response.data
  },

  deleteClipTask: async (taskId: string) => {
    const response = await apiClient.delete(`/anime/clips/${taskId}/`)
    return response.data
  },

  listClipTasks: async () => {
    const response = await apiClient.get('/anime/clips/')
    return response.data
  },

  // Legacy endpoints for backward compatibility
  createScreenshotLegacy: async (data: {
    anime_id: number
    episode?: number
    timestamp: number
  }) => {
    const response = await apiClient.post('/anime/screenshot/', data)
    return response.data
  },

  createClipLegacy: async (data: {
    anime_id: number
    episode?: number
    start: number
    end: number
    label?: string
  }) => {
    const response = await apiClient.post('/anime/clip/create/', data)
    return response.data
  },
}

export default animeApi
