import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Reminder {
  id: number
  anime: number
  anime_detail: {
    id: number
    title_ru: string
    title_en: string
    poster_url: string | null
    year: number | null
    status: string
    score: number | null
  }
  reminder_time: string
  repeat_weekly: boolean
  comment: string
  is_active: boolean
  is_triggered: boolean
  created_at: string
}

export interface ReminderCreateData {
  anime_id: number
  reminder_time: string
  repeat_weekly?: boolean
  comment?: string
}

const remindersApi = {
  // Получить список напоминаний пользователя
  getReminders: (): Promise<AxiosResponse<Reminder[]>> => {
    return apiClient.get<Reminder[]>('/notifications/reminders/')
  },

  // Получить предстоящие напоминания
  getUpcomingReminders: (): Promise<AxiosResponse<Reminder[]>> => {
    return apiClient.get<Reminder[]>('/notifications/reminders/upcoming/')
  },

  // Создать напоминание
  createReminder: (data: ReminderCreateData): Promise<AxiosResponse<Reminder>> => {
    return apiClient.post<Reminder>('/notifications/reminders/', data)
  },

  // Удалить напоминание
  deleteReminder: (id: number): Promise<AxiosResponse<void>> => {
    return apiClient.delete<void>(`/notifications/reminders/${id}/`)
  },

  // Деактивировать напоминание
  deactivateReminder: (id: number): Promise<AxiosResponse<{ status: string }>> => {
    return apiClient.post(`/notifications/reminders/${id}/deactivate/`)
  }
}

export default remindersApi
