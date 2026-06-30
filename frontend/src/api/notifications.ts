import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface NotificationItem {
  id: number
  type: string
  title: string
  content: string
  icon: string
  link: string
  is_read: boolean
  is_important: boolean
  is_deleted: boolean
  is_flashing?: boolean  
  created_at: string
  read_at: string | null
  expires_at: string | null
}

export interface NotificationListResponse {
  count: number
  next: string | null
  previous: string | null
  results: NotificationItem[]
}

export interface RecentResponse {
  results: NotificationItem[]
  unread_count: number
  flashing_count?: number  
}

export interface NotificationSettings {
  push_enabled: boolean
  email_enabled: boolean
  sound_enabled: boolean
  type_settings: Record<string, { enabled: boolean; sound?: string }>
  dnd_enabled: boolean
  dnd_start: string | null
  dnd_end: string | null
  auto_clean_read_days: number
  auto_clean_unread_days: number
  updated_at: string
}

const notificationsApi = {
  
  list(params?: {
    page?: number
    page_size?: number
    type?: string
    unread?: '1'
    important?: '1'
  }): Promise<AxiosResponse<NotificationListResponse | NotificationItem[]>> {
    return apiClient.get('/notifications/notifications/', { params })
  },

  
  recent(): Promise<AxiosResponse<RecentResponse>> {
    return apiClient.get('/notifications/notifications/recent/')
  },

  
  count(): Promise<AxiosResponse<{ count: number; flashing_count?: number }>> {
    return apiClient.get('/notifications/notifications/count/')
  },

  
  markRead(id: number): Promise<AxiosResponse<{ status: string; id: number; is_read: boolean }>> {
    return apiClient.post(`/notifications/notifications/${id}/mark_read/`)
  },

  
  markAllRead(): Promise<AxiosResponse<{ status: string; count: number }>> {
    return apiClient.post('/notifications/notifications/mark_all_read/')
  },

  
  toggleImportant(id: number): Promise<AxiosResponse<{ status: string; id: number; is_important: boolean }>> {
    return apiClient.post(`/notifications/notifications/${id}/toggle_important/`)
  },

  
  delete(id: number): Promise<AxiosResponse<void>> {
    return apiClient.delete(`/notifications/notifications/${id}/`)
  },

  
  cleanRead(): Promise<AxiosResponse<{ status: string }>> {
    return apiClient.delete('/notifications/notifications/clean/')
  },

  
  deleteAll(): Promise<AxiosResponse<{ status: string }>> {
    return apiClient.delete('/notifications/notifications/delete_all/')
  },

  
  getSettings(): Promise<AxiosResponse<NotificationSettings>> {
    return apiClient.get('/notifications/settings/')
  },

  saveSettings(data: Partial<NotificationSettings>): Promise<AxiosResponse<NotificationSettings>> {
    return apiClient.patch('/notifications/settings/', data)
  },
}

export default notificationsApi
