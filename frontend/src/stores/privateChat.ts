import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface PrivateChat {
  id: number
  user1: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
  }
  user2: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
  }
  created_at: string
  last_message_at: string | null
  user1_notifications: boolean
  user2_notifications: boolean
  user1_muted_until: string | null
  user2_muted_until: string | null
  user1_archived: boolean
  user2_archived: boolean
  user1_pinned: boolean
  user2_pinned: boolean
  user1_blocked: boolean
  user2_blocked: boolean
}

interface Message {
  id: number
  text: string
  media: string | null
  media_type: string | null
  sender: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
  }
  reply_to: Message | null
  reactions: Record<string, number[]>
  is_edited: boolean
  edited_at: string | null
  is_deleted: boolean
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export const usePrivateChatStore = defineStore('privateChat', () => {
  // State
  const chats = ref<PrivateChat[]>([])
  const currentChat = ref<PrivateChat | null>(null)
  const messages = ref<Message[]>([])

  // Loading states
  const loadingChats = ref(false)
  const loadingMessages = ref(false)
  const sendingMessage = ref(false)

  // Computed
  const authStore = useAuthStore()

  const otherUser = computed(() => {
    if (!currentChat.value) return null
    const currentUserId = authStore.user?.id
    return currentChat.value.user1.id === currentUserId ? currentChat.value.user2 : currentChat.value.user1
  })

  const chatSettings = computed(() => {
    if (!currentChat.value) return {}
    const currentUserId = authStore.user?.id
    const isUser1 = currentChat.value.user1.id === currentUserId

    return {
      notifications: isUser1 ? currentChat.value.user1_notifications : currentChat.value.user2_notifications,
      muted_until: isUser1 ? currentChat.value.user1_muted_until : currentChat.value.user2_muted_until,
      archived: isUser1 ? currentChat.value.user1_archived : currentChat.value.user2_archived,
      pinned: isUser1 ? currentChat.value.user1_pinned : currentChat.value.user2_pinned,
      blocked: isUser1 ? currentChat.value.user1_blocked : currentChat.value.user2_blocked,
    }
  })

  // Actions
  const loadChats = async () => {
    loadingChats.value = true
    try {
      const response = await apiClient.get('/social/private-chats/')
      chats.value = response.data
    } catch (error) {
      console.error('Error loading private chats:', error)
      throw error
    } finally {
      loadingChats.value = false
    }
  }

  const createOrGetChat = async (userId: number) => {
    try {
      const response = await apiClient.post('/social/private-chats/', { user_id: userId })
      const chat = response.data

      // Add to chats list if not already there
      const existingIndex = chats.value.findIndex(c => c.id === chat.id)
      if (existingIndex === -1) {
        chats.value.unshift(chat)
      } else {
        chats.value[existingIndex] = chat
      }

      currentChat.value = chat
      return chat
    } catch (error) {
      console.error('Error creating/getting private chat:', error)
      throw error
    }
  }

  const loadChat = async (chatId: number) => {
    try {
      const response = await apiClient.get(`/social/private-chats/${chatId}/`)
      currentChat.value = response.data

      // Update in chats list
      const existingIndex = chats.value.findIndex(c => c.id === chatId)
      if (existingIndex !== -1) {
        chats.value[existingIndex] = response.data
      }
    } catch (error) {
      console.error('Error loading private chat:', error)
      throw error
    }
  }

  const loadMessages = async (chatId: number) => {
    loadingMessages.value = true
    try {
      const response = await apiClient.get(`/social/private-chats/${chatId}/messages/`)
      messages.value = response.data
    } catch (error) {
      console.error('Error loading messages:', error)
      throw error
    } finally {
      loadingMessages.value = false
    }
  }

  const sendMessage = async (chatId: number, text: string, replyToId?: number) => {
    sendingMessage.value = true
    try {
      const data: any = { text }
      if (replyToId) {
        data.reply_to = replyToId
      }

      const response = await apiClient.post('/social/messages/', {
        ...data,
        chat_id: chatId // This will be handled by the backend to determine chat type
      })

      const message = response.data
      messages.value.unshift(message)

      // Update last message time
      if (currentChat.value) {
        currentChat.value.last_message_at = message.created_at
      }

      return message
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    } finally {
      sendingMessage.value = false
    }
  }

  const updateSettings = async (chatId: number, settings: Partial<{
    notifications: boolean
    muted_until: string | null
    archived: boolean
    pinned: boolean
    blocked: boolean
  }>) => {
    try {
      const response = await apiClient.post(`/social/private-chats/${chatId}/update_settings/`, settings)
      currentChat.value = response.data

      // Update in chats list
      const existingIndex = chats.value.findIndex(c => c.id === chatId)
      if (existingIndex !== -1) {
        chats.value[existingIndex] = response.data
      }
    } catch (error) {
      console.error('Error updating chat settings:', error)
      throw error
    }
  }

  const clearHistory = async (chatId: number) => {
    try {
      await apiClient.post(`/social/private-chats/${chatId}/clear_history/`)
      // Clear messages locally
      messages.value = []
    } catch (error) {
      console.error('Error clearing history:', error)
      throw error
    }
  }

  const deleteChat = async (chatId: number) => {
    try {
      await apiClient.delete(`/social/private-chats/${chatId}/`)
      // Remove from chats list
      chats.value = chats.value.filter(c => c.id !== chatId)
      if (currentChat.value?.id === chatId) {
        currentChat.value = null
        messages.value = []
      }
    } catch (error) {
      console.error('Error deleting private chat:', error)
      throw error
    }
  }

  const markMessageAsRead = async (messageId: number) => {
    try {
      await apiClient.post(`/social/messages/${messageId}/read/`)
      // Update message locally if needed
    } catch (error) {
      console.error('Error marking message as read:', error)
      throw error
    }
  }

  const editMessage = async (messageId: number, newText: string) => {
    try {
      const response = await apiClient.post(`/social/messages/${messageId}/edit/`, {
        text: newText
      })

      // Update message locally
      const index = messages.value.findIndex(m => m.id === messageId)
      if (index !== -1) {
        messages.value[index] = response.data
      }

      return response.data
    } catch (error) {
      console.error('Error editing message:', error)
      throw error
    }
  }

  const deleteMessage = async (messageId: number) => {
    try {
      await apiClient.post(`/social/messages/${messageId}/delete/`)

      // Remove message locally
      messages.value = messages.value.filter(m => m.id !== messageId)
    } catch (error) {
      console.error('Error deleting message:', error)
      throw error
    }
  }

  const addReaction = async (messageId: number, emoji: string) => {
    try {
      const response = await apiClient.post(`/social/messages/${messageId}/react/`, { emoji })

      // Update message locally
      const message = messages.value.find(m => m.id === messageId)
      if (message) {
        message.reactions = response.data.reactions
      }
    } catch (error) {
      console.error('Error adding reaction:', error)
      throw error
    }
  }

  return {
    // State
    chats,
    currentChat,
    messages,
    loadingChats,
    loadingMessages,
    sendingMessage,

    // Computed
    otherUser,
    chatSettings,

    // Actions
    loadChats,
    createOrGetChat,
    loadChat,
    loadMessages,
    sendMessage,
    updateSettings,
    clearHistory,
    deleteChat,
    markMessageAsRead,
    editMessage,
    deleteMessage,
    addReaction
  }
})