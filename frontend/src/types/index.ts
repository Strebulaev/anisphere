export interface Genre {
  id: number
  name: string
  slug: string
}

export interface Anime {
  id: number
  title_ru: string
  title_en: string
  title_jp: string
  poster_url: string
  poster_file: string | null
  description: string
  year: number | null
  status: string
  episodes: number | null
  genres: Genre[]
  created_at: string
}

export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  display_name?: string
  avatar?: string
  avatar_url?: string
  is_online?: boolean
  status?: {
    status: string
    last_seen: string
    custom_status: string
  }
}

export interface ChatMember {
  id: number
  user: User
  role: ChatRole | null
  is_owner?: boolean
  is_admin?: boolean
  is_muted?: boolean
  joined_at: string
  effective_permissions: Record<string, boolean>
  role_id?: number
}

export interface ChatRole {
  id: number
  name: string
  level: number
  color: string
  can_delete_messages: boolean
  can_ban_users: boolean
  can_pin_messages: boolean
  can_add_new_admins: boolean
  can_remain_anonymous: boolean
  can_manage_chat: boolean
  can_manage_video_chats: boolean
  can_restrict_members: boolean
  can_promote_members: boolean
  can_change_chat_info: boolean
  can_invite_users: boolean
  can_post_messages: boolean
  can_edit_messages: boolean
  can_delete_chat: boolean
}

export interface Playlist {
  id: number
  title: string
  description?: string
  is_public: boolean
  items: PlaylistItem[]
  user: User
}

export interface PlaylistItem {
  id: number
  anime: Anime
  source_url: string
  episode?: number
  note?: string
}