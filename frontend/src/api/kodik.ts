import apiClient from './client'
import { KODIK_API_TOKEN, KODIK_API_BASE, normalizeKodikPlayerLink } from '../config/kodik'

interface MaterialData {
  title: string
  title_en?: string
  year: number
  description?: string
  anime_description?: string
  poster_url?: string
  anime_poster_url?: string
  duration?: number
  countries?: string[]
  genres?: string[]
  anime_genres?: string[]
  anime_studios?: string[]
  kinopoisk_rating?: number
  imdb_rating?: number
  shikimori_rating?: number
  episodes_total?: number
  episodes_aired?: number
  anime_status?: string
  anime_kind?: string
  minimal_age?: number
  rating_mpaa?: string
}

interface KodikAnime {
  id: string
  title: string
  title_orig: string
  other_title?: string
  link: string
  year: number
  type: string
  quality: string
  translation: {
    id: number
    title: string
    type: string
  }
  kinopoisk_id?: string
  imdb_id?: string
  shikimori_id?: number
  created_at: string
  updated_at: string
  screenshots: string[]
  material_data?: MaterialData
  seasons?: {
    [season: number]: {
      link: string
      episodes: {
        [episode: number]: string
      }
    }
  }
  last_season?: number
  last_episode?: number
  episodes_count?: number
}

interface KodikListResponse {
  time: string
  total: number
  prev_page?: string
  next_page?: string
  results: KodikAnime[]
}

interface KodikSearchResponse {
  time: string
  total: number
  results: KodikAnime[]
}

interface KodikFilters {
  genres?: string[]
  anime_genres?: string[]
  year_from?: number
  year_to?: number
  countries?: string[]
  studios?: string[]
  status?: string
  kind?: string
  min_rating?: number
  max_rating?: number
}

export const kodikApi = {
  async searchAnime(params: {
    title?: string
    title_orig?: string
    shikimori_id?: number
    kinopoisk_id?: string
    types?: string
    with_material_data?: boolean
    with_seasons?: boolean
    with_episodes?: boolean
    limit?: number
  } = {}): Promise<KodikSearchResponse> {
    const queryParams: any = {
      token: KODIK_API_TOKEN,
      types: 'anime-serial,anime',
      with_material_data: true,
      ...params
    }
    
    const response = await apiClient.get(`${KODIK_API_BASE}/search`, {
      params: queryParams,
      baseURL: ''
    })
    
    return response.data
  },

  async getAnimeList(params: {
    types?: string
    with_material_data?: boolean
    with_seasons?: boolean
    with_episodes?: boolean
    limit?: number
    sort?: string
    order?: string
    next_page?: string
    filters?: KodikFilters
  } = {}): Promise<KodikListResponse> {
    const queryParams: any = {
      token: KODIK_API_TOKEN,
      types: 'anime-serial,anime',
      with_material_data: true,
      with_seasons: true,
      with_episodes: true,
      limit: 100,
      sort: 'updated_at',
      order: 'desc',
      ...params
    }

    if (params.filters) {
      const f = params.filters
      if (f.genres?.length) queryParams.anime_genres = f.genres.join(',')
      if (f.year_from) queryParams.year = `${f.year_from}-${f.year_to || 9999}`
      if (f.countries?.length) queryParams.countries = f.countries.join(',')
      if (f.studios?.length) queryParams.anime_studios = f.studios.join(',')
      if (f.status) queryParams.anime_status = f.status
      if (f.kind) queryParams.anime_kind = f.kind
      if (f.min_rating) queryParams.shikimori_rating = `${f.min_rating}-10`
    }
    
    const url = params.next_page || `${KODIK_API_BASE}/list`
    const response = await apiClient.get(url, {
      params: queryParams,
      baseURL: ''
    })
    
    return response.data
  },

  async getAllGenres(): Promise<{ results: { title: string; count: number }[] }> {
    const response = await apiClient.get(`${KODIK_API_BASE}/genres`, {
      params: {
        token: KODIK_API_TOKEN,
        types: 'anime-serial,anime',
        genres_type: 'shikimori',
        sort: 'title'
      },
      baseURL: ''
    })
    
    return response.data
  },

  async getAllYears(): Promise<{ results: { year: number; count: number }[] }> {
    const response = await apiClient.get(`${KODIK_API_BASE}/years`, {
      params: {
        token: KODIK_API_TOKEN,
        types: 'anime-serial,anime',
        sort: 'year',
        order: 'desc'
      },
      baseURL: ''
    })
    
    return response.data
  },

  async getAllStudios(): Promise<{ results: { title: string; count: number }[] }> {
    const response = await apiClient.get(`${KODIK_API_BASE}/anime_studios`, {
      params: {
        token: KODIK_API_TOKEN,
        types: 'anime-serial,anime',
        sort: 'title'
      },
      baseURL: ''
    })
    
    return response.data
  },

  async getAllTranslations(): Promise<{ results: { id: number; title: string; count: number }[] }> {
    const response = await apiClient.get(`${KODIK_API_BASE}/translations/v2`, {
      params: {
        token: KODIK_API_TOKEN,
        types: 'anime-serial,anime',
        sort: 'title'
      },
      baseURL: ''
    })
    
    return response.data
  },

  async getAllQualities(): Promise<{ results: { title: string; count: number }[] }> {
    const response = await apiClient.get(`${KODIK_API_BASE}/qualities/v2`, {
      params: {
        token: KODIK_API_TOKEN,
        types: 'anime-serial,anime',
        sort: 'title'
      },
      baseURL: ''
    })
    
    return response.data
  },

  async importAllAnime(onProgress?: (current: number, total: number, title: string) => void): Promise<number> {
    let allAnime: KodikAnime[] = []
    let next_page: string | undefined = undefined
    let importedCount = 0
    
    do {
      const response: KodikListResponse = await this.getAnimeList({
        with_material_data: true,
        with_seasons: true,
        with_episodes: true,
        limit: 100,
        next_page
      })
      
      allAnime = [...allAnime, ...response.results]
      
      if (onProgress) {
        onProgress(allAnime.length, response.total, `Загрузка: ${allAnime.length}/${response.total}`)
      }
      
      next_page = response.next_page
      
      if (next_page) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    } while (next_page)
    
    for (const anime of allAnime) {
      try {
        await this.importAnimeToBackend(anime)
        importedCount++
        
        if (onProgress) {
          onProgress(importedCount, allAnime.length, `Импорт: ${anime.title}`)
        }
      } catch (error) {
        console.error(`Ошибка импорта ${anime.title}:`, error)
      }
    }
    
    return importedCount
  },

  async importAnimeToBackend(anime: KodikAnime): Promise<void> {
    const materialData: MaterialData = anime.material_data || {} as MaterialData
    
    const payload = {
      shikimori_id: anime.shikimori_id,
      title_ru: anime.title,
      title_en: anime.title_orig,
      title_jp: anime.other_title || '',
      description: materialData.description || materialData.anime_description || '',
      year: anime.year,
      status: this.mapStatus(materialData.anime_status),
      kind: this.mapKind(materialData.anime_kind || anime.type),
      episodes: materialData.episodes_total || anime.episodes_count || 1,
      score: materialData.shikimori_rating || materialData.kinopoisk_rating || 0,
      poster_url: materialData.poster_url || materialData.anime_poster_url || '',
      genres: materialData.anime_genres || materialData.genres || [],
      studios: materialData.anime_studios || [],
      kodik_link: normalizeKodikPlayerLink(anime.link),
      kodik_id: anime.id,
      quality: anime.quality,
      screenshots: anime.screenshots || [],
      seasons: anime.seasons || {},
      last_season: anime.last_season,
      last_episode: anime.last_episode,
      episodes_count: anime.episodes_count,
      translations: [{
        id: anime.translation.id.toString(),
        name: anime.translation.title,
        type: anime.translation.type,
        external_id: anime.translation.id.toString()
      }],
      data_source: 'kodik'
    }
    
    await apiClient.post('/anime/import-from-kodik/', payload)
  },

  mapStatus(status?: string): string {
    const statusMap: { [key: string]: string } = {
      'anons': 'announced',
      'ongoing': 'ongoing',
      'released': 'finished',
      'discontinued': 'canceled'
    }
    return statusMap[status || ''] || 'finished'
  },

  mapKind(kind?: string): string {
    const kindMap: { [key: string]: string } = {
      'tv': 'tv',
      'tv_13': 'tv',
      'tv_24': 'tv',
      'tv_48': 'tv',
      'movie': 'movie',
      'ova': 'ova',
      'ona': 'ona',
      'special': 'special',
      'music': 'music'
    }
    return kindMap[kind || ''] || 'tv'
  },

  async getAnimeFilters(): Promise<{
    genres: { title: string; count: number }[]
    years: { year: number; count: number }[]
    studios: { title: string; count: number }[]
    translations: { id: number; title: string; count: number }[]
    qualities: { title: string; count: number }[]
  }> {
    const [genres, years, studios, translations, qualities] = await Promise.all([
      this.getAllGenres(),
      this.getAllYears(),
      this.getAllStudios(),
      this.getAllTranslations(),
      this.getAllQualities()
    ])
    
    return {
      genres: genres.results,
      years: years.results,
      studios: studios.results,
      translations: translations.results,
      qualities: qualities.results
    }
  }
}

export default kodikApi
