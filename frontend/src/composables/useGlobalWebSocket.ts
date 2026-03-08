import { ref } from 'vue'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

let globalWs: WebSocket | null = null
let isConnected = ref(false)
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10

// Event callbacks storage
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
    const wsUrl = `${protocol}//${host}/ws/global/?token=${token}`

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
      
      // Reconnect with exponential backoff
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

    // Call registered listeners
    if (eventListeners[action]) {
      eventListeners[action].forEach(callback => callback(data))
    }

    // Default handlers
    switch (action) {
      case 'chat_created':
        // Обновить списки чатов
        privateChatStore.loadChats()
        // Загрузить групповые чаты
        groupChatStore.loadGroupChats()
        break

      case 'chat_deleted':
        // Обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'group_chat_created':
        // Новый групповой чат
        groupChatStore.loadGroupChats()
        break

      case 'new_message':
        // Новое сообщение
        const chatId = data.message?.chat_id || data.chat_id
        if (chatId) {
          // Обновить непрочитанные
          chatExtrasStore.loadUnreadChats()
        }
        // Обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'message_read':
        // Сообщение прочитано - обновить непрочитанные
        chatExtrasStore.loadUnreadChats()
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        break

      case 'chat_updated':
        // Чат обновлён - перезагрузить списки
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        chatExtrasStore.loadUnreadChats()
        break

      case 'message_deleted':
        // Сообщение удалено - перезагрузить сообщения
        window.dispatchEvent(new CustomEvent('messageDeleted', { 
          detail: { messageId: data.message_id, chatId: data.chat_id } 
        }))
        privateChatStore.loadChats()
        break

      case 'unread_updated':
        // Обновить непрочитанные
        chatExtrasStore.loadUnreadChats()
        privateChatStore.loadChats()
        break

      case 'user_online':
        // Пользователь онлайн - обновить статус
        authStore.updateUserOnlineStatus(data.user_id, true)
        break

      case 'user_offline':
        // Пользователь офлайн - обновить статус
        authStore.updateUserOnlineStatus(data.user_id, false)
        break

      case 'user_typing':
        // Пользователь печатает - обрабатывается в компоненте чата
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
        // Новое уведомление — добавляем в стор и обновляем список
        chatExtrasStore.loadNotifications()
        // Динамический импорт notifications store без await (fire-and-forget)
        import('@/stores/notifications').then(({ useNotificationStore }) => {
          try {
            const notifStore = useNotificationStore()
            if (data.notification) {
              notifStore.addNotification(data.notification)
            } else {
              notifStore.fetchNotifications()
            }
          } catch { /* store может быть не инициализирован */ }
        }).catch(() => {})
        break

      case 'invite_received':
        // Получено приглашение в чат
        chatExtrasStore.loadInvites()
        break

      case 'friend_request':
        // Новый запрос в друзья
        authStore.loadFriendRequests()
        // Показать уведомление
        window.dispatchEvent(new CustomEvent('newFriendRequest', { 
          detail: { 
            from_user_id: data.from_user_id,
            username: data.username,
            avatar: data.avatar
          } 
        }))
        break

      case 'friend_accepted':
        // Запрос в друзья принят
        window.dispatchEvent(new CustomEvent('friendAccepted', { 
          detail: { 
            user_id: data.user_id,
            username: data.username
          } 
        }))
        break

      case 'pong':
        // Heartbeat response
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

    // Return unsubscribe function
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

  // Heartbeat
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

// Auto-connect on import if authenticated
export function initGlobalWebSocket() {
  const authStore = useAuthStore()
  if (authStore.isAuthenticated) {
    const { connect, startHeartbeat } = useGlobalWebSocket()
    connect()
    startHeartbeat()
  }
}
