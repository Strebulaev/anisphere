import apiClient from './client'

export type LibraryStatus = 'started' | 'completed' | 'on_hold' | 'dropped' | 'planned' | 'favorite'

export interface LibraryItem {
  id: number
  user?: number
  anime: number
  anime_title_ru: string
  anime_title_en: string
  anime_poster: string | null
  anime_episodes_count: number | null
  status: LibraryStatus
  anime_status_display: string
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
}

export const libraryApi = {
  // Получить всю коллекцию (с фильтром)
  getLibrary: async (params?: {
    status?: LibraryStatus | ''
    is_favorite?: boolean
    search?: string
    ordering?: string
  }): Promise<LibraryItem[]> => {
    const response = await apiClient.get<LibraryItem[]>('/users/library/', { params })
    return response.data
  },

  // Добавить/обновить аниме в библиотеке
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

  // Обновить запись
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

  // Удалить из коллекции
  deleteLibraryItem: async (id: number): Promise<void> => {
    await apiClient.delete(`/users/library/${id}/`)
  },

  // Получить статистику
  getStatistics: async (): Promise<LibraryStats> => {
    const response = await apiClient.get<LibraryStats>('/users/library/statistics/')
    return response.data
  },

  // Отметить/убрать из избранного
  toggleFavorite: async (id: number): Promise<{ is_favorite: boolean }> => {
    const response = await apiClient.post<{ is_favorite: boolean }>(`/users/library/${id}/mark_favorite/`)
    return response.data
  },

  // Проверить наличие аниме в библиотеке
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
