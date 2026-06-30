import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface User {
  id: number
  username: string
  nickname: string | null
  display_name: string | null
  avatar_url: string | null
  is_online: boolean
  is_active?: boolean
  last_login: string | null
  level: number
  bio: string | null
  is_premium?: boolean
  nickname_color?: string
  nickname_gradient_start?: string
  nickname_gradient_end?: string
  nickname_glow_enabled?: boolean
  nickname_glow_color?: string
  nickname_glow_intensity?: number
}

export interface UsersListParams {
  status?: 'all' | 'online' | 'offline'
  tab?: 'all' | 'online' | 'offline'
  search?: string
  page?: number
  page_size?: number
}

export interface UsersListResponse {
  results: User[]
  count: number
  next: string | null
  previous: string | null
  tab?: string
  online_count?: number
  offline_count?: number
}

export interface OnlineStatusResponse {
  statuses: Record<number, { is_online: boolean; is_active: boolean }>
  online_count: number
}

const usersApi = {
  
  getUsers: (params?: UsersListParams): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', { params })
  },

  
  getOnlineUsers: (search?: string): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', {
      params: { status: 'online', search }
    })
  },

  
  getOnlineStatus: (userIds?: number[]): Promise<AxiosResponse<OnlineStatusResponse>> => {
    const params = userIds ? { user_ids: userIds.join(',') } : {}
    return apiClient.get('/users/online-status/', { params })
  },

  
  searchUsers: (query: string): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', {
      params: { search: query }
    })
  }
}

export default usersApi
