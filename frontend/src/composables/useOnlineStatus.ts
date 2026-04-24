import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const onlineUsers = ref<Set<number>>(new Set())
let globalWs: WebSocket | null = null

export function useOnlineStatus() {
  const authStore = useAuthStore()

  const connectGlobalWebSocket = () => {
    if (globalWs?.readyState === WebSocket.OPEN) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/global/?token=${token}`

    globalWs = new WebSocket(wsUrl)

    globalWs.onopen = () => {
      console.log('Global WS connected for online status')
    }

    globalWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.action === 'user_online') {
          if (data.is_online) {
            onlineUsers.value.add(data.user_id)
          } else {
            onlineUsers.value.delete(data.user_id)
          }
        }
      } catch (e) {
        console.error('Global WS message error:', e)
      }
    }

    globalWs.onclose = () => {
      globalWs = null
      // Reconnect after delay
      setTimeout(connectGlobalWebSocket, 5000)
    }

    globalWs.onerror = (error) => {
      console.error('Global WS error:', error)
    }
  }

  const disconnectGlobalWebSocket = () => {
    if (globalWs) {
      globalWs.close()
      globalWs = null
    }
  }

  const isUserOnline = (userId: number): boolean => {
    return onlineUsers.value.has(userId)
  }

  const getOnlineCount = (): number => {
    return onlineUsers.value.size
  }

// Auto-connect when auth user is available
if (authStore.isAuthenticated && !globalWs) {
  connectGlobalWebSocket()
}

// Watch for auth changes
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && !globalWs) {
    connectGlobalWebSocket()
  } else if (!isAuth && globalWs) {
    disconnectGlobalWebSocket()
  }
})

  return {
    isUserOnline,
    getOnlineCount,
    connectGlobalWebSocket,
    disconnectGlobalWebSocket,
  }
}