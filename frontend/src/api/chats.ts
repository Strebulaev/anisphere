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

// ==================== НОВЫЕ ТИПЫ ====================

export interface ChatInviteLink {
  id: number
  chat: number
  chat_name: string
  creator: {
    id: number
    username: string
    avatar_url?: string
  }
  name: string
  invite_link: string
  expires_at?: string
  usage_limit?: number
  usage_count: number
  remaining_uses?: number
  is_revoked: boolean
  is_primary: boolean
  auto_assign_role?: number
  is_valid: boolean
  created_at: string
  updated_at: string
}

export interface ChatInviteLinkCreate {
  chat: number
  name?: string
  expires_at?: string
  usage_limit?: number
  is_primary?: boolean
  auto_assign_role?: number
}

export interface ChatWallpaper {
  id: number
  user?: number
  chat?: number
  wallpaper_type: 'solid' | 'gradient' | 'pattern' | 'image'
  wallpaper_color: string
  wallpaper_color2?: string
  wallpaper_intensity: number
  wallpaper_blur: number
  wallpaper_motion: string
  wallpaper_image?: string
  wallpaper_image_url?: string
  is_preset: boolean
  preset_name?: string
  created_at: string
}

export interface ChatTheme {
  id: number
  user: number
  chat?: number
  private_chat?: number
  theme: string
  message_color: string
  message_color_other: string
  bubble_style: string
  font_size: string
  time_format: string
  message_animation: string
  reaction_animation: string
  typing_animation: string
  emoji_set: string
  emoji_size: string
  created_at: string
  updated_at: string
}

export interface GroupedReaction {
  emoji: string
  count: number
  users: Array<{
    id: number
    username: string
    avatar_url?: string
  }>
  is_mine: boolean
}

export interface ChatBan {
  id: number
  chat: number
  chat_name: string
  user: {
    id: number
    username: string
    avatar_url?: string
  }
  banned_by: {
    id: number
    username: string
  }
  reason: string
  until_date?: string
  delete_messages: boolean
  is_active: boolean
  created_at: string
}

export interface ChatBanCreate {
  chat: number
  user: number
  reason: string
  until_date?: string
  delete_messages?: boolean
}

export interface ChatRestriction {
  id: number
  chat: number
  user: {
    id: number
    username: string
    avatar_url?: string
  }
  restricted_by: {
    id: number
    username: string
  }
  restriction_type: string
  restriction_type_display: string
  reason?: string
  until_date?: string
  slow_mode_delay?: number
  is_active: boolean
  created_at: string
}

export interface ChatRestrictionCreate {
  chat: number
  user: number
  restriction_type: string
  reason?: string
  until_date?: string
  slow_mode_delay?: number
}

export interface ChatSlowMode {
  id: number
  chat: number
  enabled: boolean
  delay: number
  exempt_admins: boolean
  exempt_moderators: boolean
  custom_delays: Record<number, number>
  created_at: string
  updated_at: string
}

export interface ChatJoinRequest {
  id: number
  chat: number
  chat_name: string
  user: {
    id: number
    username: string
    avatar_url?: string
  }
  message?: string
  answers: Record<string, any>
  status: 'pending' | 'approved' | 'rejected'
  status_display: string
  reviewed_by?: {
    id: number
    username: string
  }
  reviewed_at?: string
  created_at: string
}

export interface ChatJoinRequestCreate {
  chat: number
  message?: string
  answers?: Record<string, any>
}

export interface ChatTag {
  id: number
  user: number
  name: string
  color: string
  emoji?: string
  created_at: string
}

export interface ChatTagCreate {
  name: string
  color: string
  emoji?: string
}

export interface AntiSpamRule {
  id: number
  chat: number
  rule_type: string
  rule_type_display: string
  threshold: number
  time_window: number
  keywords?: string[]
  action: string
  action_display: string
  action_duration?: number | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface AntiSpamRuleCreate {
  chat: number
  rule_type: string
  threshold?: number
  time_window?: number
  keywords?: string[]
  action?: string
  action_duration?: number | null
  enabled?: boolean
}

export interface ChatBackup {
  id: number
  chat: number
  chat_name: string
  created_by: {
    id: number
    username: string
  }
  backup_file?: string
  messages_count: number
  members_count: number
  file_size: number
  file_size_mb: number
  status: 'creating' | 'completed' | 'failed'
  status_display: string
  created_at: string
}

export interface ScheduledMessage {
  id: number
  sender: {
    id: number
    username: string
    avatar_url?: string
  }
  chat?: number
  private_chat?: number
  chat_name?: string
  text?: string
  media?: string
  media_url?: string
  media_type?: string
  scheduled_at: string
  is_recurring: boolean
  recurring_interval?: number
  status: 'scheduled' | 'sent' | 'cancelled' | 'failed'
  status_display: string
  sent_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface ScheduledMessageCreate {
  chat?: number
  private_chat?: number
  text?: string
  media?: File
  media_type?: string
  scheduled_at: string
  is_recurring?: boolean
  recurring_interval?: number
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
  grouped: (messageId: number) =>
    apiClient.get<GroupedReaction[]>(`/social/message-reactions/for_message/?message_id=${messageId}`),
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
  delete: (messageId: number) => apiClient.delete(`/social/messages/${messageId}/`),
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

// ==================== НОВЫЕ API ====================

// Ссылки-приглашения
export const inviteLinksApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatInviteLink[]>('/social/chat-invite-links/', {
      params: chatId ? { chat_id: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatInviteLink>(`/social/chat-invite-links/${id}/`),
  create: (data: ChatInviteLinkCreate) =>
    apiClient.post<ChatInviteLink>('/social/chat-invite-links/', data),
  update: (id: number, data: Partial<ChatInviteLinkCreate>) =>
    apiClient.patch<ChatInviteLink>(`/social/chat-invite-links/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chat-invite-links/${id}/`),
  revoke: (id: number) => apiClient.post(`/social/chat-invite-links/${id}/revoke/`),
  join: (token: string) => apiClient.post(`/social/invite-links/join/${token}/`),
}

// Обои чатов
export const wallpapersApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatWallpaper[]>('/social/chat-wallpapers/', {
      params: chatId ? { chat_id: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatWallpaper>(`/social/chat-wallpapers/${id}/`),
  create: (data: FormData) =>
    apiClient.post<ChatWallpaper>('/social/chat-wallpapers/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  update: (id: number, data: Partial<ChatWallpaper>) =>
    apiClient.patch<ChatWallpaper>(`/social/chat-wallpapers/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chat-wallpapers/${id}/`),
  presets: () => apiClient.get<ChatWallpaper[]>('/social/wallpapers/presets/'),
  setForChat: (chatId: number, data: Partial<ChatWallpaper>, type: 'group' | 'private' = 'group') =>
    apiClient.put<ChatWallpaper>(`/social/chats/${chatId}/wallpaper/`, { ...data, type }),
}

// Темы оформления
export const themesApi = {
  list: () => apiClient.get<ChatTheme[]>('/social/chat-themes/'),
  get: (id: number) => apiClient.get<ChatTheme>(`/social/chat-themes/${id}/`),
  create: (data: Partial<ChatTheme>) => apiClient.post<ChatTheme>('/social/chat-themes/', data),
  update: (id: number, data: Partial<ChatTheme>) =>
    apiClient.patch<ChatTheme>(`/social/chat-themes/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chat-themes/${id}/`),
}

// Блокировки
export const bansApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatBan[]>('/social/chat-bans/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatBan>(`/social/chat-bans/${id}/`),
  create: (data: ChatBanCreate) => apiClient.post<ChatBan>('/social/chat-bans/', data),
  unban: (id: number) => apiClient.post(`/social/chat-bans/${id}/unban/`),
  getBannedUsers: (chatId: number) =>
    apiClient.get<ChatBan[]>(`/social/group-chats/${chatId}/banned-users/`),
}

// Ограничения
export const restrictionsApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatRestriction[]>('/social/chat-restrictions/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatRestriction>(`/social/chat-restrictions/${id}/`),
  create: (data: ChatRestrictionCreate) =>
    apiClient.post<ChatRestriction>('/social/chat-restrictions/', data),
  lift: (id: number) => apiClient.post(`/social/chat-restrictions/${id}/lift/`),
  getRestrictedUsers: (chatId: number) =>
    apiClient.get<ChatRestriction[]>(`/social/group-chats/${chatId}/restricted-users/`),
}

// Медленный режим
export const slowModeApi = {
  get: (chatId: number) =>
    apiClient.get<ChatSlowMode[]>(`/social/chat-slow-modes/?chat=${chatId}`),
  update: (id: number, data: Partial<ChatSlowMode>) =>
    apiClient.patch<ChatSlowMode>(`/social/chat-slow-modes/${id}/`, data),
}

// Запросы на вступление
export const joinRequestsApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatJoinRequest[]>('/social/chat-join-requests/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatJoinRequest>(`/social/chat-join-requests/${id}/`),
  create: (data: ChatJoinRequestCreate) =>
    apiClient.post<ChatJoinRequest>('/social/chat-join-requests/', data),
  approve: (id: number) => apiClient.post(`/social/chat-join-requests/${id}/approve/`),
  reject: (id: number) => apiClient.post(`/social/chat-join-requests/${id}/reject/`),
}

// Теги чатов
export const tagsApi = {
  list: () => apiClient.get<ChatTag[]>('/social/chat-tags/'),
  get: (id: number) => apiClient.get<ChatTag>(`/social/chat-tags/${id}/`),
  create: (data: ChatTagCreate) => apiClient.post<ChatTag>('/social/chat-tags/', data),
  update: (id: number, data: Partial<ChatTagCreate>) =>
    apiClient.patch<ChatTag>(`/social/chat-tags/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/chat-tags/${id}/`),
  assign: (tagId: number, chatId?: number, privateChatId?: number) =>
    apiClient.post('/social/chat-tag-assignments/', {
      tag: tagId,
      group_chat: chatId,
      private_chat: privateChatId
    }),
  unassign: (assignmentId: number) =>
    apiClient.delete(`/social/chat-tag-assignments/${assignmentId}/`),
}

// Анти-спам
export const antiSpamApi = {
  list: (chatId?: number) =>
    apiClient.get<AntiSpamRule[]>('/social/anti-spam-rules/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<AntiSpamRule>(`/social/anti-spam-rules/${id}/`),
  create: (data: AntiSpamRuleCreate) =>
    apiClient.post<AntiSpamRule>('/social/anti-spam-rules/', data),
  update: (id: number, data: Partial<AntiSpamRuleCreate>) =>
    apiClient.patch<AntiSpamRule>(`/social/anti-spam-rules/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/anti-spam-rules/${id}/`),
}

// Резервные копии
export const backupsApi = {
  list: (chatId?: number) =>
    apiClient.get<ChatBackup[]>('/social/chat-backups/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ChatBackup>(`/social/chat-backups/${id}/`),
  create: (chatId: number) =>
    apiClient.post<ChatBackup>('/social/chat-backups/', { chat: chatId }),
  restore: (id: number) => apiClient.post(`/social/chat-backups/${id}/restore/`),
  download: (id: number) =>
    apiClient.get(`/social/chat-backups/${id}/download/`, { responseType: 'blob' }),
}

// Запланированные сообщения
export const scheduledMessagesApi = {
  list: (chatId?: number) =>
    apiClient.get<ScheduledMessage[]>('/social/scheduled-messages/', {
      params: chatId ? { chat: chatId } : {}
    }),
  get: (id: number) => apiClient.get<ScheduledMessage>(`/social/scheduled-messages/${id}/`),
  create: (data: ScheduledMessageCreate) => {
    if (data.media) {
      const formData = new FormData()
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formData.append(key, value as string | Blob)
        }
      })
      return apiClient.post<ScheduledMessage>('/social/scheduled-messages/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    }
    return apiClient.post<ScheduledMessage>('/social/scheduled-messages/', data)
  },
  update: (id: number, data: Partial<ScheduledMessageCreate>) =>
    apiClient.patch<ScheduledMessage>(`/social/scheduled-messages/${id}/`, data),
  delete: (id: number) => apiClient.delete(`/social/scheduled-messages/${id}/`),
  cancel: (id: number) => apiClient.post(`/social/scheduled-messages/${id}/cancel/`),
  sendNow: (id: number) => apiClient.post(`/social/scheduled-messages/${id}/send_now/`),
}

// Роли
export const rolesApi = {
  setMemberRole: (chatId: number, userId: number, roleId: number | null) =>
    apiClient.post(`/social/group-chats/${chatId}/members/${userId}/role/`, { role_id: roleId }),
  transferOwnership: (chatId: number, userId: number) =>
    apiClient.post(`/social/group-chats/${chatId}/transfer-ownership/`, { user_id: userId }),
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
  // Новые API
  inviteLinks: inviteLinksApi,
  wallpapers: wallpapersApi,
  themes: themesApi,
  bans: bansApi,
  restrictions: restrictionsApi,
  slowMode: slowModeApi,
  joinRequests: joinRequestsApi,
  tags: tagsApi,
  antiSpam: antiSpamApi,
  backups: backupsApi,
  scheduledMessages: scheduledMessagesApi,
  roles: rolesApi,
}