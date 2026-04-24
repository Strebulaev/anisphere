import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatFoldersApi } from '@/api/chatFolders'
import type { ChatFolder, CreateFolderData, UpdateFolderData, Chat } from '@/types/chat'
import { SYSTEM_FOLDERS as systemFolders } from '@/types/chat'

export const useChatFoldersStore = defineStore('chatFolders', () => {
  const folders = ref<ChatFolder[]>([])
  const activeFolderId = ref<number | null>(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const folderScrollPositions = ref<Map<number, number>>(new Map())

  const allFolders = computed(() => {
    const systemFoldersList = systemFolders.map(f => ({
      ...f,
      rules: f.rules || {
        include_private: true,
        include_groups: true,
        include_bots: true,
        exclude_keywords: [],
        include_keywords: [],
        exclude_user_ids: []
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })) as ChatFolder[]

    const userFolders = folders.value.filter(f => !f.is_system)
    const sortedFolders = [...userFolders].sort((a, b) => a.position - b.position)

    return [...systemFoldersList, ...sortedFolders]
  })

  const activeFolder = computed(() => {
    return allFolders.value.find(f => f.id === activeFolderId.value) || null
  })

  const userFolders = computed(() => {
    return folders.value.filter(f => !f.is_system)
  })

  async function loadFolders() {
    loading.value = true
    error.value = null

    try {
      const data = await chatFoldersApi.getAll()
      folders.value = (data as any).results || data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось загрузить папки'
      console.error('Error loading folders:', err)
    } finally {
      loading.value = false
    }
  }

  async function createFolder(data: CreateFolderData) {
    loading.value = true
    error.value = null

    try {
      const newFolder = await chatFoldersApi.create(data)
      folders.value.push(newFolder)
      return newFolder
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось создать папку'
      console.error('Error creating folder:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateFolder(id: number, data: UpdateFolderData) {
    loading.value = true
    error.value = null

    try {
      const updatedFolder = await chatFoldersApi.update(id, data)
      const index = folders.value.findIndex(f => f.id === id)
      if (index !== -1) {
        folders.value[index] = updatedFolder
      }
      return updatedFolder
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось обновить папку'
      console.error('Error updating folder:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteFolder(id: number) {
    loading.value = true
    error.value = null

    try {
      await chatFoldersApi.delete(id)
      folders.value = folders.value.filter(f => f.id !== id)

      if (activeFolderId.value === id) {
        activeFolderId.value = 0
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось удалить папку'
      console.error('Error deleting folder:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function reorderFolders(folderIds: number[]) {
    loading.value = true
    error.value = null

    try {
      await chatFoldersApi.reorder(folderIds)

      folderIds.forEach((id, index) => {
        const folder = folders.value.find(f => f.id === id)
        if (folder) {
          folder.position = index
        }
      })
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось изменить порядок папок'
      console.error('Error reordering folders:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getFolderPreview(id: number) {
    try {
      return await chatFoldersApi.getPreview(id)
    } catch (err: any) {
      console.error('Error getting folder preview:', err)
      throw err
    }
  }

  async function getFolderChats(id: number) {
    try {
      return await chatFoldersApi.getFolderChats(id)
    } catch (err: any) {
      console.error('Error getting folder chats:', err)
      throw err
    }
  }

  function setActiveFolder(id: number | null) {
    activeFolderId.value = id
  }

  function saveScrollPosition(folderId: number, position: number) {
    folderScrollPositions.value.set(folderId, position)
  }

  function getScrollPosition(folderId: number): number {
    return folderScrollPositions.value.get(folderId) || 0
  }

  function applyFolderRules(chats: Chat[], folder: ChatFolder): Chat[] {
    const rules = folder.rules

    return chats.filter(chat => {
      if (chat.is_archived && folder.id !== -3) {
        return false
      }

      if (!chat.is_archived && folder.id === -3) {
        return false
      }

      if (rules?.only_unread && chat.unread_count === 0) {
        return false
      }

      if (rules?.only_pinned && !chat.is_pinned) {
        return false
      }

      // Особая логика для папки "Обсуждения"
      if (folder.id === -4 && rules?.include_anime_discussions) {
        if (chat.type === 'group' && chat.anime_id) {
          return true
        }
        return false
      }

      // Проверка исключающих ключевых слов
      if (rules?.exclude_keywords && rules.exclude_keywords.length > 0) {
        const chatName = chat.type === 'private' 
          ? chat.other_user?.display_name || chat.other_user?.username || '' 
          : chat.name || ''
        
        const hasExcludedKeyword = rules.exclude_keywords.some(keyword =>
          chatName.toLowerCase().includes(keyword.toLowerCase())
        )
        
        if (hasExcludedKeyword) {
          return false
        }
      }

      // Проверка включающих ключевых слов
      if (rules?.include_keywords && rules.include_keywords.length > 0) {
        const chatName = chat.type === 'private' 
          ? chat.other_user?.display_name || chat.other_user?.username || '' 
          : chat.name || ''
        
        const hasIncludedKeyword = rules.include_keywords.some(keyword =>
          chatName.toLowerCase().includes(keyword.toLowerCase())
        )
        
        if (!hasIncludedKeyword) {
          return false
        }
      }

      // Проверка исключённых пользователей
      if (rules?.exclude_user_ids && rules.exclude_user_ids.length > 0) {
        if (chat.type === 'private' && rules.exclude_user_ids.includes(chat.other_user?.id || 0)) {
          return false
        }
      }

      if (rules?.include_private && chat.type === 'private') {
        return true
      }

      if (rules?.include_groups && chat.type === 'group') {
        return true
      }

      if (chat.type === 'group' && rules?.include_bots) {
        return true
      }

      return false
    })
  }

  function getFolderUnreadCount(folder: ChatFolder, allChats: Chat[]): number {
    const filteredChats = applyFolderRules(allChats, folder)
    return filteredChats.reduce((sum, chat) => sum + chat.unread_count, 0)
  }

  function getFolderChatCount(folder: ChatFolder, allChats: Chat[]): number {
    return applyFolderRules(allChats, folder).length
  }

  return {
    folders,
    activeFolderId,
    activeFolder,
    userFolders,
    allFolders,
    loading,
    error,
    folderScrollPositions,
    loadFolders,
    createFolder,
    updateFolder,
    deleteFolder,
    reorderFolders,
    getFolderPreview,
    getFolderChats,
    setActiveFolder,
    saveScrollPosition,
    getScrollPosition,
    applyFolderRules,
    getFolderUnreadCount,
    getFolderChatCount
  }
})
