import apiClient from './client'
import type { AxiosResponse } from 'axios'

export type PlaylistVisibility = 'public' | 'private' | 'link'

export interface Playlist {
  id: number
  user_id: number
  user_unique_id?: string
  user_username: string
  user_avatar: string | null
  user?: {
    id: number
    username: string
    avatar: string | null
  }
  title: string
  description: string
  cover_image?: string | null
  cover_urls?: string[]
  // Видимость
  visibility: PlaylistVisibility
  is_public: boolean
  is_private: boolean
  is_link_only: boolean
  // Share-токен (для link_only или владельца)
  share_token?: string | null
  is_favorite?: boolean
  favorites_count: number
  is_favorited: boolean
  created_at: string
  updated_at: string
  items: PlaylistItem[]
  items_count: number
  animes_count?: number
  genres?: string[]
}

export interface Genre {
  id: number
  name: string
  slug: string
}

export interface PlaylistItem {
  id: number
  anime: number
  anime_id: number
  anime_title: string
  anime_title_en?: string
  anime_poster: string | null
  anime_poster_url?: string
  anime_year?: number
  anime_score?: number
  anime_status?: string
  anime_kind?: string
  anime_genres?: string[]
  episode_number: number | null
  source_url: string
  notes: string
  position?: number
  created_at: string
}

export interface FavoriteAnime {
  id: number
  anime: number
  anime_title: string
  anime_poster: string | null
  anime_data: AnimeData
  created_at: string
}

export interface FavoritePlaylist {
  id: number
  playlist: number
  playlist_data: PlaylistData
  created_at: string
}

export interface PlaylistData {
  id: number
  title: string
  description: string
  is_public: boolean
  user_username: string
  user_avatar: string | null
  items_count: number
  created_at: string
}

export interface AnimeData {
  id: number
  title_ru: string
  title_en: string
  poster_url: string
  year: number | null
  status: string
  score: number | null
}

export interface AddToPlaylistRequest {
  anime_id: number
  playlist_id?: number
  new_playlist_title?: string
  episode_number?: number | null
  source_url?: string
  notes?: string
}

export interface PlaylistsParams {
  page?: number
  page_size?: number
  my?: boolean
  is_public?: boolean
  favorites?: boolean
  search?: string
  genre?: number | string
  year?: number | string
  ordering?: string
  visibility?: PlaylistVisibility
}

const playlistsApi = {
  // Плейлисты пользователя
  getMyPlaylists: (): Promise<AxiosResponse<Playlist[]>> => {
    return apiClient.get<Playlist[]>('/playlists/playlists/my/')
  },

  getPublicPlaylists: (params?: PlaylistsParams): Promise<AxiosResponse<{
    results: Playlist[]
    count: number
  }>> => {
    return apiClient.get<{ results: Playlist[]; count: number }>('/playlists/playlists/public/', { params })
  },

  getAllPlaylists: (params?: PlaylistsParams): Promise<AxiosResponse<{
    results: Playlist[]
    count: number
  }>> => {
    return apiClient.get<{ results: Playlist[]; count: number }>('/playlists/playlists/', { params })
  },

  getPlaylist: (id: number): Promise<AxiosResponse<Playlist>> => {
    return apiClient.get<Playlist>(`/playlists/playlists/${id}/`)
  },

  createPlaylist: (data: {
    title: string
    description?: string
    visibility?: PlaylistVisibility
  }): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>('/playlists/playlists/', data)
  },

  updateVisibility: (id: number, visibility: PlaylistVisibility): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/update-visibility/`, { visibility })
  },

  generateShareLink: (id: number, ttlDays?: number): Promise<AxiosResponse<{
    token: string
    expires_at: string
    share_url: string
  }>> => {
    return apiClient.post(`/playlists/playlists/${id}/share-link/`, { ttl_days: ttlDays ?? 30 })
  },

  revokeShareLink: (id: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete(`/playlists/playlists/${id}/share-link/`)
  },

  getPlaylistByToken: (token: string): Promise<AxiosResponse<Playlist>> => {
    return apiClient.get<Playlist>(`/playlists/playlists/shared/${token}/`)
  },

  updatePlaylist: (id: number, data: Partial<Playlist>): Promise<AxiosResponse<Playlist>> => {
    return apiClient.patch<Playlist>(`/playlists/playlists/${id}/`, data)
  },

  uploadPlaylistCover: (id: number, file: File): Promise<AxiosResponse<Playlist>> => {
    const formData = new FormData()
    formData.append('cover_image', file)
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/update_cover/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  deletePlaylist: (id: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/playlists/playlists/${id}/`)
  },

  duplicatePlaylist: (id: number): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/duplicate/`)
  },

  updatePlaylistCover: (id: number): Promise<AxiosResponse<Playlist>> => {
    return apiClient.post<Playlist>(`/playlists/playlists/${id}/update_cover/`)
  },

  // Элементы плейлиста
  addToPlaylist: (data: AddToPlaylistRequest): Promise<AxiosResponse<{
    message: string
    playlist_id: number
    item_id: number
  }>> => {
    return apiClient.post('/playlists/add-to-playlist/', data)
  },

  addItemToPlaylist: (playlistId: number, data: {
    anime: number
    episode_number?: number | null
    source_url?: string
    notes?: string
  }): Promise<AxiosResponse<PlaylistItem>> => {
    // Преобразуем anime в anime_id для бэкенда
    const payload = {
      anime_id: data.anime,
      episode_number: data.episode_number,
      source_url: data.source_url,
      notes: data.notes
    }
    return apiClient.post<PlaylistItem>(`/playlists/playlists/${playlistId}/add_item/`, payload)
  },

  addItemByLink: (playlistId: number, data: {
    url: string
    episode_number?: number | null
    notes?: string
  }): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.post<PlaylistItem>(`/playlists/playlists/${playlistId}/add_by_link/`, data)
  },

  removeFromPlaylist: (playlistId: number, itemId: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/playlists/playlists/${playlistId}/remove_item/`, {
      data: { item_id: itemId }
    })
  },

  updatePlaylistItem: (playlistId: number, itemId: number, data: {
    notes?: string
    position?: number
  }): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.patch<PlaylistItem>(`/playlists/items/${itemId}/`, data)
  },

  updatePlaylistItemNotes: (playlistId: number, itemId: number, notes: string): Promise<AxiosResponse<PlaylistItem>> => {
    return apiClient.post<PlaylistItem>(`/playlists/playlists/${playlistId}/update-item-notes/`, {
      item_id: itemId,
      notes
    })
  },

  reorderPlaylistItems: (playlistId: number, items: Array<{ id: number; position: number }>): Promise<AxiosResponse<{
    message: string
  }>> => {
    return apiClient.post<{ message: string }>(`/playlists/playlists/${playlistId}/reorder_items/`, { items })
  },

  // Избранное аниме
  getFavoriteAnime: (): Promise<AxiosResponse<FavoriteAnime[]>> => {
    return apiClient.get<FavoriteAnime[]>('/playlists/favorites/anime/')
  },

  checkAnimeInFavorites: (animeId: number): Promise<AxiosResponse<{ is_favorite: boolean }>> => {
    return apiClient.get<{ is_favorite: boolean }>('/playlists/favorites/anime/check/', {
      params: { anime_id: animeId }
    })
  },

  addToFavorites: (animeId: number): Promise<AxiosResponse<FavoriteAnime>> => {
    return apiClient.post<FavoriteAnime>('/playlists/favorites/anime/', { anime: animeId })
  },

  removeFromFavorites: (animeId: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>('/playlists/favorites/anime/remove/', {
      data: { anime_id: animeId }
    })
  },

  // Избранные плейлисты
  getFavoritePlaylists: (): Promise<AxiosResponse<FavoritePlaylist[]>> => {
    return apiClient.get<FavoritePlaylist[]>('/playlists/favorites/')
  },

  addPlaylistToFavorites: (playlistId: number): Promise<AxiosResponse<void>> => {
    return apiClient.post<void>(`/playlists/playlists/${playlistId}/favorite/`)
  },

  removePlaylistFromFavorites: (playlistId: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/playlists/playlists/${playlistId}/unfavorite/`)
  },
}

export default playlistsApi