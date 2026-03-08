export interface Genre {
  id: number
  name: string
  slug: string
}

export interface Anime {
  id: number
  shikimori_id?: string
  title_ru: string
  title_en?: string
  title_jp?: string
  poster?: string | null  // Локальный путь к файлу (приоритетный)
  poster_file?: string | null
  poster_url?: string  // URL Shikimori (НЕ ИСПОЛЬЗОВАТЬ)
  poster_image_url?: string
  description?: string
  year?: number | null
  status?: string
  episodes?: number | null
  score?: number
  favorites?: number
  rank?: number
  popularity?: number
  genres?: Genre[] | string[]
  source?: string
  match_type?: 'exact' | 'fuzzy'
  created_at?: string
}

export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  display_name?: string
  nickname?: string
  avatar?: string
  avatar_url?: string
  is_online?: boolean
  status?: {
    status: string
    last_seen: string
    custom_status: string
  }
  bio?: string
  website?: string
  vk_profile?: string
  telegram?: string
  youtube?: string
  twitter?: string
  gender?: 'male' | 'female' | 'other' | null
  birth_date?: string
  country?: string
  city?: string
  phone_number?: string
  email_verified?: boolean
  phone_verified?: boolean
  two_factor_enabled?: boolean
  level?: number
  experience?: number
  created_at?: string
  last_login?: string
  followers_count?: number
  following_count?: number
  playlists_count?: number
  is_verified?: boolean
  is_premium?: boolean
  competition_wins?: number
  favorite_genres?: string[]
  privacy_settings?: PrivacySettings
}

export interface PrivacySettings {
  profile_visibility: 'public' | 'followers_only' | 'private'
  playlists_visibility: 'public' | 'followers_only' | 'private'
  who_can_follow: 'everyone' | 'approval_required' | 'none'
}

export interface Activity {
  id: number
  type: 'added_to_playlist' | 'created_playlist' | 'review' | 'short' | 'followed' | 'achievement'
  user: User
  content?: any
  metadata?: Record<string, any>
  created_at: string
}

export interface AnimeLibrary {
  id: number
  anime: Anime
  user: User
  status: 'watching' | 'completed' | 'planned' | 'dropped' | 'on_hold'
  rating?: number
  added_at: string
  updated_at: string
}

export interface Video {
  id: number
  title: string
  description?: string
  thumbnail_url?: string
  video_url?: string
  duration?: number
  views_count?: number
  likes_count?: number
  comments_count?: number
  user: User
  created_at: string
}

export interface DubStudio {
  id: number
  name: string
  description?: string
  founded_year?: number
  members_count?: number
  anime_count?: number
  is_verified?: boolean
  avatar?: string
  cover_image?: string
}

export interface DubMember {
  id: number
  studio: DubStudio
  user: User
  role: 'main' | 'secondary' | 'guest'
  joined_at: string
}

export interface Achievement {
  id: number
  name: string
  description: string
  icon?: string
  category: 'basic' | 'contest' | 'social' | 'special'
  reward_xp?: number
  requirement?: string
  progress?: number
  max_progress?: number
  unlocked_at?: string
}

export interface ProfileStats {
  profile_views: number
  unique_visitors: number
  weekly_views: number[]
  new_followers: number
  unfollowed_count: number
  total_followers: number
  post_likes: number
  comments: number
  reposts: number
  popular_content?: any[]
}

export interface Session {
  id: number
  device: string
  browser: string
  os: string
  ip_address: string
  location?: string
  created_at: string
  last_activity: string
  is_current: boolean
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
  user_id?: number
  user_unique_id?: string
  user_username?: string
  user_avatar?: string | null
  user?: {
    id: number
    username: string
    avatar: string | null
  }
  title: string
  description?: string
  cover_image?: string | null
  cover_urls?: string[]
  is_public?: boolean
  is_private?: boolean
  is_link_only?: boolean
  likes_count?: number
  is_favorite?: boolean
  favorites_count?: number
  is_favorited?: boolean
  created_at?: string
  updated_at?: string
  items?: PlaylistItem[]
  items_count?: number
  animes_count?: number
  genres?: string[]
}

export interface PlaylistItem {
  id: number
  anime: Anime
  source_url: string
  episode?: number
  note?: string
  anime_poster?: string
  anime_poster_url?: string
}

export type { Chat } from './chat'
export type { ChatFolder, CreateFolderData, UpdateFolderData } from './chat'

// Типы для домашней страницы
export interface ContinueWatchingItem {
  anime_id: number
  title: string
  title_en: string
  poster: string
  current_episode: number
  total_episodes: number
  progress_percent: number
  last_watched: string | null
}

export interface RewatchItem {
  anime_id: number
  title: string
  title_en: string
  poster: string
  completed_date: string | null
  user_rating: number | null
}

export interface RecommendationItem {
  anime_id: number
  title: string
  title_en: string
  poster: string
  genres: string[]
  rating: number | null
  rating_count: number
  year: number | null
  status: string
  weekly_views?: number
}

export interface HomeData {
  continue_watching: ContinueWatchingItem[]
  rewatch: RewatchItem[]
  recommendations: RecommendationItem[]
  trending: RecommendationItem[]
}