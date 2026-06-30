import apiClient from './client'

export type LibraryStatus = 'started' | 'completed' | 'on_hold' | 'dropped' | 'planned'


export type CollectionTab = LibraryStatus | 'favorite'

export interface LibraryItem {
  id: number
  user?: number
  anime: number | {
    id: number
    title_ru: string
    title_en: string
    poster?: string
    poster_url?: string
    poster_image_url?: string
    episodes?: number
    episodes_count?: number
    status?: string
    score?: number
    year?: number
    type?: string
    kind?: string
  }
  anime_id: number
  anime_title_ru: string
  anime_title_en: string
  anime_poster: string | null
  anime_episodes_count: number | null
  anime_status_display?: string
  status: LibraryStatus
  current_episode: number
  episodes_watched: number
  rating: number | null
  added_at: string
  started_at: string | null
  completed_at: string | null
  updated_at: string
  notes: string
  is_favorite: boolean
  rewatch_count: number
  progress_percentage: number
}

export interface LibraryStats {
  total: number
  started: number
  completed: number
  on_hold: number
  dropped: number
  planned: number
  favorites: number
  episodes_watched: number
  hours_watched: number
  hours_remaining: number
  avg_rating: number
  total_rewatches: number
}

export const libraryApi = {
  
  getLibrary: async (params?: {
    status?: LibraryStatus | ''
    is_favorite?: boolean
    search?: string
    ordering?: string
  }): Promise<LibraryItem[] | { results: LibraryItem[]; count: number }> => {
    const response = await apiClient.get<LibraryItem[] | { results: LibraryItem[]; count: number }>('/users/library/', { params })
    return response.data
  },

  
  addToLibrary: async (data: {
    anime: number
    status?: LibraryStatus
    current_episode?: number
    episodes_watched?: number
    rating?: number | null
    notes?: string
    is_favorite?: boolean
  }): Promise<LibraryItem> => {
    const response = await apiClient.post<LibraryItem>('/users/library/', data)
    return response.data
  },

  
  updateLibraryItem: async (id: number, data: Partial<{
    status: LibraryStatus
    current_episode: number
    episodes_watched: number
    rating: number | null
    notes: string
    is_favorite: boolean
  }>): Promise<LibraryItem> => {
    const response = await apiClient.patch<LibraryItem>(`/users/library/${id}/`, data)
    return response.data
  },

  
  deleteLibraryItem: async (id: number): Promise<void> => {
    await apiClient.delete(`/users/library/${id}/`)
  },

  
  getStatistics: async (): Promise<LibraryStats> => {
    const response = await apiClient.get<LibraryStats>('/users/library/statistics/')
    return response.data
  },

  
  toggleFavorite: async (id: number): Promise<{ is_favorite: boolean }> => {
    const response = await apiClient.post<{ is_favorite: boolean }>(`/users/library/${id}/mark_favorite/`)
    return response.data
  },

  
  checkAnime: async (animeId: number): Promise<{
    in_library: boolean
    status?: LibraryStatus
    current_episode?: number
    rating?: number | null
    is_favorite?: boolean
  }> => {
    const response = await apiClient.get('/users/library/check_anime/', {
      params: { anime_id: animeId }
    })
    return response.data
  }
}

export default libraryApi
