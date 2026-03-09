import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Studio {
  id: number
  name: string
  name_jp: string
  slug: string
  country: string
  founded_year: number | null
  total_anime: number
  average_rating: number
  subscribers_count: number
  notable_works: string[]
  logo_image_url: string | null
  is_subscribed: boolean
  is_verified: boolean
}

export interface StudioDetail extends Studio {
  description: string
  employees_count: string
  website: string
  twitter: string
  youtube: string
  facebook: string
  tv_count: number
  movie_count: number
  ova_count: number
  genre_stats: Record<string, number>
  banner_image_url: string | null
  rating_distribution: Record<number, number>
  top_anime: StudioAnime[]
  created_at: string
}

export interface StudioAnime {
  id: number
  kodik_id: string
  anime_db_id: number | null    // ID в нашей БД (если совпал по shikimori_id)
  anime_url: string | null      // Путь на локальную страницу аниме
  anime_title: string
  anime_title_en: string
  anime_kind: string
  anime_year: number | null
  anime_score: number | null
  anime_poster: string
  anime_status: string
  shikimori_id: string
  episodes_total: number | null
  description: string
  genres: string[]
}

export interface StudioStaff {
  id: number
  name: string
  name_jp: string
  role: string
  role_detail: string
  photo_url: string
  works_count: number
  notable_works: string[]
  is_key_person: boolean
  awards: any[]
}

export interface StudioNews {
  id: number
  title: string
  content: string
  author_name: string
  likes_count: number
  comments_count: number
  created_at: string
}

export interface StudioAward {
  id: number
  year: number
  award_name: string
  category: string
  is_winner: boolean
}

export interface StudioDiscussion {
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

export interface StudioReview {
  id: number
  user_name: string
  user_avatar: string | null
  animation_quality: number
  directing: number
  soundtrack: number
  adaptation: number
  overall_rating: number
  comment: string
  created_at: string
}

export interface StudioListParams {
  page?: number
  page_size?: number
  search?: string
  country?: string
  founded_year?: number
  min_rating?: number
  ordering?: string
}

const studiosApi = {
  getStudios: (params?: StudioListParams): Promise<AxiosResponse<{
    results: Studio[]
    count: number
    next: string | null
    previous: string | null
  }>> => apiClient.get('/studios/', { params }),

  getPopular: (): Promise<AxiosResponse<Studio[]>> =>
    apiClient.get('/studios/popular/'),

  getStudio: (slug: string): Promise<AxiosResponse<StudioDetail>> =>
    apiClient.get(`/studios/${slug}/`),

  getWorks: (slug: string, params?: any): Promise<AxiosResponse<{
    results: StudioAnime[]
    count: number
    next: string | null
    previous: string | null
  }>> => apiClient.get(`/studios/${slug}/works/`, { params }),

  getStaff: (slug: string, role?: string): Promise<AxiosResponse<StudioStaff[]>> =>
    apiClient.get(`/studios/${slug}/staff/`, { params: role ? { role } : {} }),

  getNews: (slug: string): Promise<AxiosResponse<{
    results: StudioNews[]
    count: number
  }>> => apiClient.get(`/studios/${slug}/news/`),

  getAwards: (slug: string): Promise<AxiosResponse<StudioAward[]>> =>
    apiClient.get(`/studios/${slug}/awards/`),

  getDiscussions: (slug: string, ordering?: string): Promise<AxiosResponse<{
    results: StudioDiscussion[]
    count: number
  }>> => apiClient.get(`/studios/${slug}/discussions/`, { params: ordering ? { ordering } : {} }),

  createDiscussion: (slug: string, data: { title: string; content: string }): Promise<AxiosResponse<StudioDiscussion>> =>
    apiClient.post(`/studios/${slug}/discussions/create/`, data),

  getDiscussionReplies: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.get(`/studios/${slug}/discussions/${discussionId}/replies/`),

  createDiscussionReply: (slug: string, discussionId: number, content: string): Promise<AxiosResponse<any>> =>
    apiClient.post(`/studios/${slug}/discussions/${discussionId}/replies/`, { content }),

  likeDiscussion: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.post(`/studios/${slug}/discussions/${discussionId}/like/`),

  dislikeDiscussion: (slug: string, discussionId: number): Promise<AxiosResponse<any>> =>
    apiClient.post(`/studios/${slug}/discussions/${discussionId}/dislike/`),

  getReviews: (slug: string, ordering?: string): Promise<AxiosResponse<{
    results: StudioReview[]
    count: number
  }>> => apiClient.get(`/studios/${slug}/reviews/`, { params: ordering ? { ordering } : {} }),

  createReview: (slug: string, data: any): Promise<AxiosResponse<StudioReview>> =>
    apiClient.post(`/studios/${slug}/reviews/create/`, data),

  getSimilar: (slug: string): Promise<AxiosResponse<Studio[]>> =>
    apiClient.get(`/studios/${slug}/similar/`),

  subscribe: (slug: string): Promise<AxiosResponse<{ subscribed: boolean; subscribers_count: number }>> =>
    apiClient.post(`/studios/${slug}/subscribe/`),

  unsubscribe: (slug: string): Promise<AxiosResponse<{ subscribed: boolean; subscribers_count: number }>> =>
    apiClient.delete(`/studios/${slug}/subscribe/`),
}

export default studiosApi
