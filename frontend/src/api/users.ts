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
  // Получить список пользователей с фильтрами
  getUsers: (params?: UsersListParams): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', { params })
  },

  // Получить онлайн пользователей
  getOnlineUsers: (search?: string): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', {
      params: { status: 'online', search }
    })
  },

  // Быстрая проверка статуса онлайн (для polling)
  getOnlineStatus: (userIds?: number[]): Promise<AxiosResponse<OnlineStatusResponse>> => {
    const params = userIds ? { user_ids: userIds.join(',') } : {}
    return apiClient.get('/users/online-status/', { params })
  },

  // Поиск пользователей
  searchUsers: (query: string): Promise<AxiosResponse<UsersListResponse>> => {
    return apiClient.get('/users/users/', {
      params: { search: query }
    })
  }
}

export default usersApi
