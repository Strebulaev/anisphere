import apiClient from './client'

export interface AnimeDiscussionGroup {
  id: number
  name: string
  description: string
  avatar_url?: string
  anime_id: number
  anime_title: string
  anime_poster?: string
  members_count: number
  is_public: boolean
  created_at: string
  user_joined: boolean
  user_joined_at?: string
}

export const animeDiscussionsApi = {
  async getDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.get(`/anime/anime/${animeId}/discussion-group/`)
    return response.data
  },

  async joinDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.post(`/anime/anime/${animeId}/discussion-group/join/`)
    return response.data
  },

  async leaveDiscussionGroup(animeId: number): Promise<void> {
    await apiClient.post(`/anime/anime/${animeId}/discussion-group/leave/`)
  },

  async createDiscussionGroup(animeId: number): Promise<AnimeDiscussionGroup> {
    const response = await apiClient.post(`/anime/anime/${animeId}/discussion-group/create/`)
    return response.data
  },

  async getUserJoinedDiscussions(): Promise<AnimeDiscussionGroup[]> {
    const response = await apiClient.get('/anime/discussions/joined/')
    return response.data.results || response.data
  }
}
