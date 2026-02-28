import apiClient from './client'

// ==================== TYPES ====================

export interface ChatInvite {
  id: number
  chat: {
    id: number
    name: string
    avatar_url?: string
  }
  token: string
  created_by: {
    id: number
    username: string
  }
  expires_at?: string
  max_uses?: number
  uses_count: number
  is_active: boolean
  is_valid: boolean
  uses_remaining?: number
  created_at: string
  updated_at: string
}

export interface ChatInviteCreate {
  chat: number
  expires_at?: string
  max_uses?: number
}

export interface Reaction {
  id: number
  message: number
  user: {
    id: number
    username: string
    avatar?: string
  }
  emoji: string
  created_at: string
}

export interface ReactionCreate {
  message: number
  emoji: string
}

export interface Attachment {
  id: number
  message: number
  type: 'image' | 'video' | 'audio' | 'file'
  type_display: string
  file: string
  file_url: string
  file_name: string
  file_size: number
  mime_type: string
  thumbnail?: string
  thumbnail_url?: string
  width?: number
  height?: number
  duration?: number
  uploaded_at: string
}

export interface AttachmentCreate {
  message: number
  type: string
  file: File
  file_name: string
  width?: number
  height?: number
  duration?: number
}

export interface EmailLog {
  id: number
  user: {
    id: number
    username: string
  }
  email_type: string
  email_type_display: string
  subject: string
  to_email: string
  content: string
  status: 'pending' | 'sent' | 'failed'
  status_display: string
  sent_at?: string
  error_message?: string
  chat_id?: number
  message_id?: number
  metadata: Record<string, any>
  created_at: string
}

export interface UnreadCount {
  unread_count: number
  chat_id?: number
}

export interface UnreadChat {
  id: number
  type: 'group' | 'private'
  name: string
  avatar_url?: string
  unread_count: number
}

export interface SearchResult {
  query: string
  count: number
  results: any[]
}

// ==================== CHAT INVITES ====================

export const chatInvitesApi = {
  list: () => apiClient.get<ChatInvite[]>('/social/chat-invites/'),
  get: (id: number) => apiClient.get<ChatInvite>(`/social/chat-invites/${id}/`),
  create: (data: ChatInviteCreate) => apiClient.post<ChatInvite>('/social/chat-invites/', data),
  update: (id: number, data: Partial<ChatInvite>) =>
    apiClient.patch<ChatInvite>(`/social/chat-invites/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chat-invites/${id}/`),
  regenerate: (id: number) => apiClient.post<ChatInvite>(`/social/chat-invites/${id}/regenerate/`),
  revoke: (id: number) => apiClient.post(`/social/chat-invites/${id}/revoke/`),
  joinByToken: (token: string) => apiClient.post(`/social/chat-invites/join/${token}/`),
}

// ==================== REACTIONS ====================

export const reactionsApi = {
  list: (messageId?: number) =>
    apiClient.get<Reaction[]>('/social/reactions/', { params: { message: messageId } }),
  getForMessage: (messageId: number) =>
    apiClient.get<Reaction[]>(`/social/messages/${messageId}/reactions/`),
  toggle: (messageId: number, emoji: string) =>
    apiClient.post<{ reacted: boolean; emoji: string }>(
      `/social/messages/${messageId}/reaction/toggle/`,
      { emoji }
    ),
}

// ==================== ATTACHMENTS ====================

export const attachmentsApi = {
  list: (messageId?: number) =>
    apiClient.get<Attachment[]>('/social/attachments/', { params: { message: messageId } }),
  get: (id: number) => apiClient.get<Attachment>(`/social/attachments/${id}/`),
  create: (data: FormData) =>
    apiClient.post<Attachment>('/social/attachments/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  update: (id: number, data: Partial<Attachment>) =>
    apiClient.patch<Attachment>(`/social/attachments/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/attachments/${id}/`),
  uploadToMessage: (messageId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<Attachment>(
      `/social/messages/${messageId}/attachments/upload/`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },
}

// ==================== MESSAGE ACTIONS ====================

export const messageActionsApi = {
  pin: (messageId: number) => apiClient.post(`/social/messages/${messageId}/pin/`),
  unpin: (messageId: number) => apiClient.post(`/social/messages/${messageId}/unpin/`),
  forward: (messageId: number, chatId?: number, privateChatId?: number) =>
    apiClient.post(`/social/messages/${messageId}/forward/`, {
      chat_id: chatId,
      private_chat_id: privateChatId,
    }),
  getPinned: (chatId: number) => apiClient.get(`/social/chats/${chatId}/pinned-messages/`),
}

// ==================== CHATS ====================

export const chatsApi = {
  list: (params?: { search?: string; type?: string }) =>
    apiClient.get('/social/chats/', { params }),
  get: (id: number) => apiClient.get(`/social/chats/${id}/`),
  create: (data: any) => apiClient.post('/social/chats/', data),
  update: (id: number, data: any) => apiClient.patch(`/social/chats/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chats/${id}/`),
}

// ==================== UNREAD MESSAGES ====================

export const unreadApi = {
  getCount: (chatId?: number) =>
    apiClient.get<UnreadCount>('/social/chats/unread-count/', { params: { chat_id: chatId } }),
  getUnreadChats: () => apiClient.get<UnreadChat[] | { results: UnreadChat[] }>('/social/chats/unread/'),
  markAsRead: (chatId: number, messageId?: number) =>
    apiClient.post(`/social/chats/${chatId}/mark-read/`, { message_id: messageId }),
}

// ==================== EMAIL LOGS ====================

export const emailLogsApi = {
  list: () => apiClient.get<EmailLog[]>('/social/email-logs/'),
  get: (id: number) => apiClient.get<EmailLog>(`/social/email-logs/${id}/`),
  create: (data: Partial<EmailLog>) => apiClient.post<EmailLog>('/social/email-logs/', data),
  stats: () => apiClient.get('/social/email-logs/stats/'),
}

// ==================== SEARCH ====================

export const searchApi = {
  searchMessages: (params: {
    q: string
    chat_id?: number
    media_type?: string
    date_from?: string
    date_to?: string
  }) => apiClient.get<SearchResult>('/social/messages/search/', { params }),
  reindex: () => apiClient.post('/social/messages/reindex/'),
}

// ==================== EXPORTS ====================

export default {
  chatInvites: chatInvitesApi,
  reactions: reactionsApi,
  attachments: attachmentsApi,
  messageActions: messageActionsApi,
  unread: unreadApi,
  emailLogs: emailLogsApi,
  search: searchApi,
  chats: chatsApi,
}
