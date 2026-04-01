export interface User {
  id: number
  username: string
  display_name?: string
  avatar?: string
  avatar_url?: string
}

export interface Message {
  id: number
  text: string
  sender_id: number
  sender?: User
  chat_id: number
  created_at: string
  updated_at: string
  is_read_by_other?: boolean
  read_count?: number  
  is_read: boolean
  reply_to?: number
  attachments?: Attachment[]
}

export interface Attachment {
  id: number
  type: 'image' | 'video' | 'file' | 'audio'
  url: string
  filename?: string
  size?: number
  mime_type?: string
}

export interface PrivateChat {
  id: number
  type: 'private'
  other_user: User
  last_message?: Message
  unread_count: number
  created_at: string
  updated_at: string
  is_pinned: boolean
  is_archived: boolean
  is_muted: boolean
  isMuted?: boolean  // alias for compatibility
}

export interface GroupChatMember {
  id: number
  user: User
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

export interface MemberSettings {
  is_muted: boolean
  muted_until?: string
  notifications_enabled: boolean
}

export interface GroupChat {
  id: number
  type: 'group'
  name: string
  description?: string
  avatar?: string
  avatar_url?: string
  // Поля для группы обсуждения аниме
  anime_id?: number | null
  anime_title?: string | null
  anime_poster?: string | null
  members_count: number
  members: GroupChatMember[]
  owner: User
  last_message?: Message
  unread_count: number
  created_at: string
  updated_at: string
  is_pinned: boolean
  is_archived: boolean
  is_public: boolean
  invite_token?: string
  user_member_settings?: MemberSettings
  isMuted?: boolean  // alias for compatibility
}

export type Chat = PrivateChat | GroupChat

export interface UnifiedChat {
  id: number
  type: 'private' | 'group'
  title: string
  avatar?: string
  avatar_url?: string
  last_message?: Message
  unread_count: number
  is_pinned: boolean
  is_archived: boolean
  is_muted: boolean
  updated_at: string
}

export interface ChatFolderRules {
  include_private: boolean
  include_groups: boolean
  include_bots: boolean
  exclude_keywords: string[]
  include_keywords: string[]
  exclude_user_ids: number[]
  only_unread?: boolean
  only_pinned?: boolean
}

export interface ChatFolder {
  id: number
  name: string
  icon: string
  color?: string
  position: number
  is_system: boolean
  rules: ChatFolderRules
  created_at: string
  updated_at: string
}

export interface CreateFolderData {
  name: string
  icon: string
  color?: string
  rules: Partial<ChatFolderRules>
}

export interface UpdateFolderData {
  name?: string
  icon?: string
  color?: string
  rules?: Partial<ChatFolderRules>
}

export interface FolderPreview {
  folder_id: number
  chat_count: number
  unread_count: number
  chats: Chat[]
}

export const SYSTEM_FOLDERS: Partial<ChatFolder>[] = [
  {
    id: 0,
    name: 'Все чаты',
    icon: '🗯️',
    is_system: true,
    position: 0,
    rules: {
      include_private: true,
      include_groups: true,
      include_bots: true,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: []
    }
  },
  {
    id: -1,
    name: 'Личные',
    icon: '👤',
    is_system: true,
    position: 1,
    rules: {
      include_private: true,
      include_groups: false,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: []
    }
  },
  {
    id: -2,
    name: 'Группы',
    icon: '👥',
    is_system: true,
    position: 2,
    rules: {
      include_private: false,
      include_groups: true,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: []
    }
  },
  {
    id: -4,
    name: 'Обсуждения',
    icon: '🎬',
    is_system: true,
    position: 3,
    rules: {
      include_private: false,
      include_groups: true,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: ['Обсуждение:'],
      exclude_user_ids: [],
      only_unread: false,
      only_pinned: false
    }
  },
  {
    id: -3,
    name: 'Архив',
    icon: '📦',
    is_system: true,
    position: 999,
    rules: {
      include_private: true,
      include_groups: true,
      include_bots: true,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: [],
      only_unread: false,
      only_pinned: false
    }
  }
]

export const FOLDER_ICONS = [
  '🗯️', '👤', '👥', '📦',
  '🏢', '🏠', '⭐', '❤️',
  '🔥', '💡', '📌', '🎯',
  '🚀', '💼', '🎮', '🎨',
  '📚', '🎵', '🎬', '📷',
  '🏆', '🌟', '✨', '🔔',
  '📊', '📈', '💰', '🎁',
  '🌈', '☀️', '🌙', '⚡'
]

export const FOLDER_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#84CC16', // lime
  '#6366F1', // indigo
  '#F97316', // orange
]
