/**
 * API для рулетки аниме (Колесо фортуны)
 */
import apiClient from './client'

export interface RouletteItem {
  id: string
  anime_id: number
  anime_title: string
  anime_poster: string | null
  weight: number
  color: string
  order: number
  created_at: string
}

export interface RouletteSettings {
  
  theme: 'light' | 'dark' | 'anime'
  wheel_size: 'small' | 'medium' | 'large'
  display_mode: 'posters' | 'titles' | 'both'
  color_scheme: 'rainbow' | 'rating' | 'monochrome'
  animation_style: 'smooth' | 'fast' | 'cinematic'
  sound_enabled: boolean
  sound_type: string

  
  default_spin_count: number
  weight_mode: 'proportional' | 'rating' | 'manual'
  exclude_recent: boolean
  exclusion_period: number

  
  max_items: number
  max_spin_items: number
  history_limit: number

  
  auto_add_from_collection: boolean
  auto_add_from_playlists: boolean
}

export interface Roulette {
  id: string
  name: string
  spin_duration: number
  items: RouletteItem[]
  total_weight: number
  items_count: number
  wheel_size_px: number
  last_result: RouletteItem | null
  last_spin_at: string | null
  created_at: string
  updated_at: string
  
  theme: string
  wheel_size: string
  display_mode: string
  color_scheme: string
  animation_style: string
  sound_enabled: boolean
  sound_type: string
  default_spin_count: number
  weight_mode: string
  exclude_recent: boolean
  exclusion_period: number
  max_items: number
  max_spin_items: number
  history_limit: number
  auto_add_from_collection: boolean
  auto_add_from_playlists: boolean
}

export interface SpinResult {
  winner: RouletteItem
  winners?: RouletteItem[]
  selected_anime?: RouletteItem[]
  rotation_angle: number
  spin_duration: number
  spin_id: string
  items_count?: number
}

export interface SpinHistory {
  id: string
  winner: RouletteItem | null
  winners: RouletteItem[]
  spin_type: 'single' | 'multiple' | 'marathon'
  rotation_angle: number
  spin_duration: number
  items_count: number
  is_favorite: boolean
  notes: string
  created_at: string
}

export interface RouletteStatistics {
  total_spins: number
  single_spins: number
  multiple_spins: number
  marathon_spins: number
  most_spun_anime_id: number | null
  most_spun_count: number
  least_spun_anime_id: number | null
  least_spun_count: number
  unique_anime_spun: number
  last_7_days_spins: number
  last_30_days_spins: number
}

export interface RoulettePreset {
  id: string
  name: string
  description: string
  items_data: Array<{
    anime_id: number
    anime_title?: string
    anime_poster?: string
    weight?: number
    color?: string
  }>
  settings_snapshot: Partial<RouletteSettings>
  items_count: number
  times_used: number
  is_public: boolean
  created_at: string
  updated_at: string
}

export const rouletteApi = {
  

  getRoulettes: () =>
    apiClient.get<Roulette[]>('/roulette/roulettes/'),

  getRoulette: (id: string) =>
    apiClient.get<Roulette>(`/roulette/roulettes/${id}/`),

  createRoulette: (data: { name?: string; spin_duration?: number }) =>
    apiClient.post<Roulette>('/roulette/roulettes/', data),

  updateRoulette: (id: string, data: Partial<Roulette>) =>
    apiClient.patch<Roulette>(`/roulette/roulettes/${id}/`, data),

  deleteRoulette: (id: string) =>
    apiClient.delete(`/roulette/roulettes/${id}/`),

  

  getSettings: async (rouletteId: string) => {
    try {
      return await apiClient.get<RouletteSettings>(`/roulette/roulettes/${rouletteId}/settings/`)
    } catch (error) {
      console.warn('Settings not available:', error)
      throw error
    }
  },

  updateSettings: async (rouletteId: string, settings: Partial<RouletteSettings>) => {
    try {
      return await apiClient.patch<RouletteSettings>(`/roulette/roulettes/${rouletteId}/settings/`, settings)
    } catch (error) {
      console.warn('Update settings not available:', error)
      throw error
    }
  },

  

  addItem: (rouletteId: string, data: {
    anime_id: number
    anime_title: string
    anime_poster?: string
    weight?: number
    color?: string
  }) =>
    apiClient.post<RouletteItem>(`/roulette/roulettes/${rouletteId}/add_item/`, data),

  bulkAdd: (rouletteId: string, items: Array<{
    anime_id: number
    anime_title?: string
    anime_poster?: string
    weight?: number
  }>) =>
    apiClient.post(`/roulette/roulettes/${rouletteId}/bulk_add/`, { items }),

  removeItem: (rouletteId: string, itemId: string) =>
    apiClient.delete(`/roulette/roulettes/${rouletteId}/remove_item/?item_id=${itemId}`),

  updateWeights: (rouletteId: string, weights: Record<string, number>) =>
    apiClient.post(`/roulette/roulettes/${rouletteId}/update_weights/`, { weights }),

  

  spin: async (rouletteId: string) => {
    try {
      return await apiClient.post<SpinResult>(`/roulette/roulettes/${rouletteId}/spin/`)
    } catch (error) {
      console.warn('Spin not available:', error)
      throw error
    }
  },

  spinMultiple: async (rouletteId: string, count: number = 3) => {
    try {
      return await apiClient.post<SpinResult>(`/roulette/roulettes/${rouletteId}/spin_multiple/`, { count })
    } catch (error) {
      console.warn('Spin multiple not available:', error)
      throw error
    }
  },

  marathon: async (rouletteId: string, count: number = 5) => {
    try {
      return await apiClient.post<SpinResult>(`/roulette/roulettes/${rouletteId}/marathon/`, { count })
    } catch (error) {
      console.warn('Marathon not available:', error)
      throw error
    }
  },

  

  getHistory: async (rouletteId: string, params?: {
    spin_type?: string
    date_from?: string
    date_to?: string
    limit?: number
  }) => {
    try {
      const { data } = await apiClient.get<SpinHistory[]>(`/roulette/roulettes/${rouletteId}/history/`, { params })
      return { data: data || [] }
    } catch (error) {
      console.warn('History not available:', error)
      return { data: [] }
    }
  },

  getStatistics: async (rouletteId: string) => {
    try {
      return await apiClient.get<RouletteStatistics>(`/roulette/roulettes/${rouletteId}/statistics/`)
    } catch (error) {
      console.warn('Statistics not available:', error)
      
      return {
        data: {
          total_spins: 0,
          single_spins: 0,
          multiple_spins: 0,
          marathon_spins: 0,
          most_spun_anime_id: null,
          most_spun_count: 0,
          least_spun_anime_id: null,
          least_spun_count: 0,
          unique_anime_spun: 0,
          last_7_days_spins: 0,
          last_30_days_spins: 0
        }
      }
    }
  },

  

  addFromCollection: async (rouletteId: string, params: {
    collection_status?: string[]
    min_score?: number
    weight_by_score?: boolean
  }) => {
    try {
      return await apiClient.post(`/roulette/roulettes/${rouletteId}/add_from_collection/`, params)
    } catch (error) {
      console.warn('Add from collection not available:', error)
      throw error
    }
  },

  addFromPlaylist: async (rouletteId: string, playlistId: string, weightEqual: boolean = true) => {
    try {
      return await apiClient.post(`/roulette/roulettes/${rouletteId}/add_from_playlist/`, {
        playlist_id: playlistId,
        weight_equal: weightEqual
      })
    } catch (error) {
      console.warn('Add from playlist not available:', error)
      throw error
    }
  },

  

  clear: (rouletteId: string) =>
    apiClient.post(`/roulette/roulettes/${rouletteId}/clear/`),

  

  getPresets: async () => {
    try {
      const { data } = await apiClient.get<RoulettePreset[]>('/roulette/presets/')
      return { data: data || [] }
    } catch (error) {
      console.warn('Presets not available:', error)
      return { data: [] }
    }
  },

  getPreset: async (id: string) => {
    try {
      return await apiClient.get<RoulettePreset>(`/roulette/presets/${id}/`)
    } catch (error) {
      console.warn('Preset not available:', error)
      throw error
    }
  },

  createPreset: async (data: {
    name: string
    description?: string
    items_data: Array<{
      anime_id: number
      anime_title?: string
      anime_poster?: string
      weight?: number
      color?: string
    }>
    settings_snapshot?: Partial<RouletteSettings>
    is_public?: boolean
  }) => {
    try {
      return await apiClient.post<RoulettePreset>('/roulette/presets/', data)
    } catch (error) {
      console.warn('Create preset not available:', error)
      throw error
    }
  },

  updatePreset: async (id: string, data: Partial<RoulettePreset>) => {
    try {
      return await apiClient.patch<RoulettePreset>(`/roulette/presets/${id}/`, data)
    } catch (error) {
      console.warn('Update preset not available:', error)
      throw error
    }
  },

  deletePreset: async (id: string) => {
    try {
      return await apiClient.delete(`/roulette/presets/${id}/`)
    } catch (error) {
      console.warn('Delete preset not available:', error)
      throw error
    }
  },

  applyPreset: async (presetId: string, rouletteId: string) => {
    try {
      return await apiClient.post<Roulette>(`/roulette/presets/${presetId}/apply/`, { roulette_id: rouletteId })
    } catch (error) {
      console.warn('Apply preset not available:', error)
      throw error
    }
  },

  duplicatePreset: async (id: string) => {
    try {
      return await apiClient.post<RoulettePreset>(`/roulette/presets/${id}/duplicate/`)
    } catch (error) {
      console.warn('Duplicate preset not available:', error)
      throw error
    }
  },

  getPopularPresets: async () => {
    try {
      const { data } = await apiClient.get<RoulettePreset[]>('/roulette/presets/popular/')
      return { data: data || [] }
    } catch (error) {
      console.warn('Popular presets not available:', error)
      return { data: [] }
    }
  },
}
