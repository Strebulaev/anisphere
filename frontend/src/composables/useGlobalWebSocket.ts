import { ref } from 'vue'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

let globalWs: WebSocket | null = null
const isConnected = ref(false)
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10


type EventCallback = (data: any) => void
const eventListeners: Record<string, EventCallback[]> = {}

export function useGlobalWebSocket() {
  const authStore = useAuthStore()
  const privateChatStore = usePrivateChatStore()
  const groupChatStore = useGroupChatStore()
  const chatExtrasStore = useChatExtrasStore()

  const connect = () => {
    const token = localStorage.getItem('access_token')
    if (!token || !authStore.isAuthenticated) return

    if (globalWs?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}

    globalWs = new WebSocket(wsUrl)

    globalWs.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
      console.log('✅ Global WebSocket connected')
    }

    globalWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleEvent(data)
      } catch (e) {
        console.error('Global WS parse error:', e)
      }
    }

    globalWs.onclose = () => {
      isConnected.value = false
      globalWs = null
      
      
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
        setTimeout(connect, delay)
      }
    }

    globalWs.onerror = (error) => {
      console.error('Global WS error:', error)
    }
  }

  const handleEvent = (data: any) => {
    const { action } = data

    
    if (eventListeners[action]) {
      eventListeners[action].forEach(callback => callback(data))
    }

    
    switch (action) {
      case 'chat_created':
        
        privateChatStore.loadChats()
        
        groupChatStore.loadGroupChats()
        break

      case 'chat_deleted':
        
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'group_chat_created':
        
        groupChatStore.loadGroupChats()
        break

      case 'new_message':
        
        const chatId = data.message?.chat_id || data.chat_id
        if (chatId) {
          
          chatExtrasStore.loadUnreadChats()
        }
        
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'message_read':
        
        chatExtrasStore.loadUnreadChats()
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'chat_updated':
        
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        chatExtrasStore.loadUnreadChats()
        break

      case 'message_deleted':
        
        window.dispatchEvent(new CustomEvent('messageDeleted', { 
          detail: { messageId: data.message_id, chatId: data.chat_id } 
        }))
        privateChatStore.loadChats()
        break

      case 'unread_updated':
        
        chatExtrasStore.loadUnreadChats()
        privateChatStore.loadChats()
        break

      case 'user_online':
        
        authStore.updateUserOnlineStatus(data.user_id, true)
        break

      case 'user_offline':
        
        authStore.updateUserOnlineStatus(data.user_id, false)
        break

      case 'user_typing':
        
        window.dispatchEvent(new CustomEvent('userTyping', { 
          detail: { 
            chatId: data.chat_id, 
            userId: data.user_id, 
            username: data.username,
            isTyping: data.is_typing 
          } 
        }))
        break

      case 'notification':
        
        chatExtrasStore.loadNotifications()
        
        window.dispatchEvent(new CustomEvent('newNotification', { detail: data.notification || null }))
        break

      case 'invite_received':
        
        chatExtrasStore.loadInvites()
        break

      case 'friend_request':
        
        authStore.loadFriendRequests()
        
        window.dispatchEvent(new CustomEvent('newFriendRequest', { 
          detail: { 
            from_user_id: data.from_user_id,
            username: data.username,
            avatar: data.avatar
          } 
        }))
        break

      case 'friend_accepted':
        
        window.dispatchEvent(new CustomEvent('friendAccepted', { 
          detail: { 
            user_id: data.user_id,
            username: data.username
          } 
        }))
        break

      case 'pong':
        
        break
    }
  }

  const disconnect = () => {
    if (globalWs) {
      globalWs.close()
      globalWs = null
      isConnected.value = false
    }
  }

  const subscribe = (action: string, callback: EventCallback) => {
    if (!eventListeners[action]) {
      eventListeners[action] = []
    }
    eventListeners[action].push(callback)

    
    return () => {
      const index = eventListeners[action]?.indexOf(callback) ?? -1
      if (index > -1) {
        eventListeners[action]?.splice(index, 1)
      }
    }
  }

  const send = (data: any) => {
    if (globalWs?.readyState === WebSocket.OPEN) {
      globalWs.send(JSON.stringify(data))
    }
  }

  const sendTyping = (chatId: number, isTyping: boolean) => {
    send({
      action: isTyping ? 'typing_start' : 'typing_stop',
      chat_id: chatId
    })
  }

  
  let heartbeatInterval: number | null = null
  const startHeartbeat = () => {
    if (heartbeatInterval) return
    heartbeatInterval = window.setInterval(() => {
      send({ action: 'ping' })
    }, 30000)
  }

  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
  }

  return {
    isConnected,
    connect,
    disconnect,
    subscribe,
    send,
    sendTyping,
    startHeartbeat,
    stopHeartbeat
  }
}


export function initGlobalWebSocket() {
  const authStore = useAuthStore()
  if (authStore.isAuthenticated) {
    const { connect, startHeartbeat } = useGlobalWebSocket()
    connect()
    startHeartbeat()
  }
}
