// API для мини-чата поддержки
import apiClient from './client'

export interface SupportTicket {
  id: number
  user_id: number
  username: string
  user_avatar: string | null
  subject: string
  status: 'pending' | 'answered' | 'closed'
  anime_id: number | null
  created_at: string
  updated_at: string
  closed_at: string | null
  last_message: {
    text: string
    sender_id: number
    sender_username: string
    created_at: string
    is_read: boolean
  } | null
  unread_count: number
  is_admin: boolean
}

export interface SupportMessage {
  id: number
  ticket_id: number
  sender_id: number
  sender_username: string
  sender_avatar: string | null
  sender_is_admin: boolean
  text: string
  is_read: boolean
  read_at: string | null
  created_at: string
}

export const supportApi = {
  // Получить моё активное обращение
  getMyActive: (): Promise<{ data: { has_active: boolean } & SupportTicket }> => {
    return apiClient.get('/social/support/my_active/')
  },
  
  // Получить все мои обращения
  getMyTickets: (params?: { status?: string }): Promise<{ data: SupportTicket[] }> => {
    return apiClient.get('/social/support/', { params })
  },
  
  // Создать новое обращение или добавить сообщение в существующее
  createTicket: (data: {
    subject?: string
    text: string
    anime_id?: number
  }): Promise<{ data: { ticket_id: number; message_id: number } }> => {
    return apiClient.post('/social/support/', data)
  },
  
  // Получить обращение по ID
  getTicket: (id: number): Promise<{ data: SupportTicket }> => {
    return apiClient.get(`/social/support/${id}/`)
  },
  
  // Получить сообщения обращения
  getMessages: (ticketId: number): Promise<{ data: SupportMessage[] }> => {
    return apiClient.get(`/social/support/${ticketId}/messages/`)
  },
  
  // Отправить сообщение в обращение
  sendMessage: (ticketId: number, text: string): Promise<{ data: SupportMessage }> => {
    return apiClient.post(`/social/support/${ticketId}/messages/`, { text })
  },
  
  // Закрыть обращение
  closeTicket: (id: number): Promise<{ data: { message: string } }> => {
    return apiClient.post(`/social/support/${id}/close/`)
  },
  
  // Для админов: получить все обращения
  adminList: (params?: { status?: string }): Promise<{ data: SupportTicket[] }> => {
    return apiClient.get('/social/support/admin_list/', { params })
  },
  
  // Для админов: статистика
  adminStats: (): Promise<{ data: {
    total: number
    pending: number
    answered: number
    closed: number
  } }> => {
    return apiClient.get('/social/support/stats/')
  }
}

export default supportApi
