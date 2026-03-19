import apiClient from './client'

export interface DiscussionTopic {
  id: number
  title: string
  anime_id: number | null
  is_general: boolean
  is_current?: boolean
}

export interface AnimeDiscussionGroup {
  id: number
  name: string
  description?: string
  avatar_url?: string
  anime_id?: number
  anime_title?: string
  anime_poster?: string
  members_count: number
  is_public: boolean
  created_at?: string
  user_joined?: boolean
  user_joined_at?: string
  discussion_type?: string
  // Для франшиз
  type?: 'anime' | 'franchise'
  group?: {
    id: number
    name: string
    avatar_url?: string
    members_count: number
    discussion_type: string
    user_joined?: boolean
  }
  franchise?: {
    id: number
    name: string
  }
  topics?: DiscussionTopic[]
  current_topic_id?: number
}

export const animeDiscussionsApi = {
  async getDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.get(`/social/anime/${animeId}/discussion-group/`)
    return response.data
  },

  async getFranchiseDiscussion(franchiseId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.get(`/social/franchise/${franchiseId}/discussion/`)
    return response.data
  },

  async joinDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.post(`/social/anime/${animeId}/discussion-group/join/`)
    return response.data
  },

  async joinFranchiseDiscussion(franchiseId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.post(`/social/franchise/${franchiseId}/discussion/join/`)
    return response.data
  },

  async leaveDiscussionGroup(animeId: number): Promise<void> {
    await apiClient.post(`/social/anime/${animeId}/discussion-group/join/`)
  },

  async createDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.post(`/social/anime/${animeId}/discussion-group/create/`)
    return response.data
  },

  async getUserJoinedDiscussions(): Promise<AnimeDiscussionGroup[]> {
    const response = await apiClient.get('/anime/discussions/joined/')
    return response.data.results || response.data
  }
}
