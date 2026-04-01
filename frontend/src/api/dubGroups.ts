import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface DubGroup {
  id: number
  name: string
  name_jp: string
  slug: string
  translation_type: 'voice' | 'subtitles' | 'both'
  works_count: number
  average_rating: number
  subscribers_count: number
  logo_image_url: string | null
  is_subscribed: boolean
  is_verified: boolean
}

export interface DubGroupDetail extends DubGroup {
  description: string
  website: string
  vk_url: string
  telegram_url: string
  discord_url: string
  youtube_url: string
  twitter_url: string
  founded_year: number | null
  tv_count: number
  movie_count: number
  ova_count: number
  genre_stats: Record<string, number>
  banner_image_url: string | null
  rating_distribution: Record<number, number>
  top_anime: DubGroupAnime[]
  created_at: string
}

export interface DubGroupAnime {
  id: number
  anime_url: string | null
  anime_title: string
  anime_score: number
  anime_poster: string
  anime_kind: string
}

export interface DubGroupStaff {
  id: number
  name: string
  slug: string
  description: string
  photo_url: string
  roles_count: number
  groups: DubGroup[]
}

export interface DubGroupNews {
  id: number
  title: string
  content: string
  author_name: string
  likes_count: number
  comments_count: number
  created_at: string
}

export interface DubGroupDiscussion {
  id: number
  title: string
  content: string
  author_name: string
  author_avatar: string | null
  likes_count: number
  dislikes_count: number
  replies_count: number
  is_pinned: boolean
  created_at: string
  last_reply_at: string | null
}

export interface DubGroupReview {
  id: number
  user_name: string
  user_avatar: string | null
  voice_quality: number
  timing: number
  translation: number
  consistency: number
  overall_rating: number
  comment: string
  created_at: string
}

export interface DubGroupListParams {
  page?: number
  page_size?: number
  search?: string
  translation_type?: string
  ordering?: string
}

const dubGroupsApi = {
  getGroups: (params?: DubGroupListParams): Promise<AxiosResponse<{
    results: DubGroup[]
    count: number
    next: string | null
    previous: string | null
  }>> => apiClient.get('/dubs/groups/', { params }),

  getPopular: (): Promise<AxiosResponse<DubGroup[]>> =>
    apiClient.get('/dubs/groups/popular/'),

  getGroup: (slug: string): Promise<AxiosResponse<DubGroupDetail>> =>
    apiClient.get(`/dubs/groups/${slug}/`),

  getWorks: (slug: string, params?: any): Promise<AxiosResponse<{
    results: any[]
    count: number
    next: string | null
    previous: string | null
  }>> => apiClient.get(`/dubs/groups/${slug}/works/`, { params }),

  getStaff: (slug: string): Promise<AxiosResponse<DubGroupStaff[]>> =>
    apiClient.get(`/dubs/groups/${slug}/staff/`),

  getNews: (slug: string): Promise<AxiosResponse<{
    results: DubGroupNews[]
    count: number
  }>> => apiClient.get(`/dubs/groups/${slug}/news/`),

  getDiscussions: (slug: string, ordering?: string): Promise<AxiosResponse<{
    results: DubGroupDiscussion[]
    count: number
  }>> => apiClient.get(`/dubs/groups/${slug}/discussions/`, { params: ordering ? { ordering } : {} }),

  createDiscussion: (slug: string, data: { title: string; content: string }): Promise<AxiosResponse<DubGroupDiscussion>> =>
    apiClient.post(`/dubs/groups/${slug}/discussions/create/`, data),

  getDiscussionReplies: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.get(`/dubs/groups/${slug}/discussions/${discussionId}/replies/`),

  createDiscussionReply: (slug: string, discussionId: number, content: string): Promise<AxiosResponse<any>> =>
    apiClient.post(`/dubs/groups/${slug}/discussions/${discussionId}/replies/`, { content }),

  likeDiscussion: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.post(`/dubs/groups/${slug}/discussions/${discussionId}/like/`),

  dislikeDiscussion: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.post(`/dubs/groups/${slug}/discussions/${discussionId}/dislike/`),

  getReviews: (slug: string, ordering?: string): Promise<AxiosResponse<{
    results: DubGroupReview[]
    count: number
  }>> => apiClient.get(`/dubs/groups/${slug}/reviews/`, { params: ordering ? { ordering } : {} }),

  createReview: (slug: string, data: any): Promise<AxiosResponse<DubGroupReview>> =>
    apiClient.post(`/dubs/groups/${slug}/reviews/create/`, data),

  getSimilar: (slug: string): Promise<AxiosResponse<DubGroup[]>> =>
    apiClient.get(`/dubs/groups/${slug}/similar/`),

  subscribe: (slug: string): Promise<AxiosResponse<{ subscribed: boolean; subscribers_count: number }>> =>
    apiClient.post(`/dubs/groups/${slug}/subscribe/`),

  unsubscribe: (slug: string): Promise<AxiosResponse<{ subscribed: boolean; subscribers_count: number }>> =>
    apiClient.delete(`/dubs/groups/${slug}/subscribe/`),
}

export default dubGroupsApi
