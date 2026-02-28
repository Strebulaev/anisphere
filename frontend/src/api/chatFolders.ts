import apiClient from './client'
import type { ChatFolder, CreateFolderData, UpdateFolderData, FolderPreview, Chat } from '@/types/chat'
import { animeDiscussionsApi, type AnimeDiscussionGroup } from './animeDiscussions'

export const chatFoldersApi = {
  async getAll(): Promise<ChatFolder[]> {
    try {
      const response = await apiClient.get('/social/chat-folders/')
      return response.data
    } catch (error) {
      // Если API не работает, возвращаем пустой массив
      // Системные папки будут показаны из types/chat.ts
      return []
    }
  },

  async create(data: CreateFolderData): Promise<ChatFolder> {
    const response = await apiClient.post('/social/chat-folders/', data)
    return response.data
  },

  async update(id: number, data: UpdateFolderData): Promise<ChatFolder> {
    const response = await apiClient.patch(`/social/chat-folders/${id}/`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/social/chat-folders/${id}/`)
  },

  async reorder(folderIds: number[]): Promise<void> {
    try {
      await apiClient.patch('/social/chat-folders/reorder/', { folder_ids: folderIds })
    } catch (error) {
      console.error('Error reordering folders:', error)
    }
  },

  async getPreview(id: number): Promise<FolderPreview> {
    // Для папки обсуждений используем специальный API
    if (id === -4) {
      const discussions = await animeDiscussionsApi.getUserJoinedDiscussions()
      return {
        folder_id: id,
        chat_count: discussions.length,
        unread_count: discussions.reduce((sum, d) => sum + 0, 0), // TODO: добавить unread_count
        chats: discussions.map(d => ({
          id: d.id,
          type: 'group' as const,
          name: d.name,
          description: d.description,
          avatar_url: d.avatar_url,
          members_count: d.members_count,
          unread_count: 0,
          created_at: d.created_at,
          updated_at: d.created_at,
          is_pinned: false,
          is_archived: false,
          is_muted: false,
          members: [],
          owner: { id: 0, username: '' },
          is_public: d.is_public
        })) as Chat[]
      }
    }

    const response = await apiClient.get(`/social/chat-folders/${id}/preview/`)
    return response.data
  },

  async getFolderChats(id: number): Promise<Chat[]> {
    // Для папки обсуждений используем специальный API
    if (id === -4) {
      const discussions = await animeDiscussionsApi.getUserJoinedDiscussions()
      return discussions.map(d => ({
        id: d.id,
        type: 'group' as const,
        name: d.name,
        description: d.description,
        avatar_url: d.avatar_url,
        members_count: d.members_count,
        unread_count: 0,
        created_at: d.created_at,
        updated_at: d.created_at,
        is_pinned: false,
        is_archived: false,
        is_muted: false,
        members: [],
        owner: { id: 0, username: '' },
        is_public: d.is_public
      })) as Chat[]
    }

    const response = await apiClient.get(`/social/chat-folders/${id}/chats/`)
    return response.data.results || response.data
  }
}
