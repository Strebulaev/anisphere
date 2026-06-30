/**
 * usePresence — управляет heartbeat онлайн-статуса пользователя.
 *
 * Логика:
 *  • Пока браузерная вкладка ВИДИМА (document.visibilityState === 'visible'),
 *    каждые HEARTBEAT_INTERVAL мс отправляем POST /api/users/heartbeat/.
 *  • Когда вкладка скрывается — интервал НЕ останавливаем, TTL в Redis 30 мин.
 *    Таким образом, пользователь считается онлайн ещё 30 минут после скрытия вкладки.
 *  • Автоматически запускается при монтировании App.vue (один раз за жизнь приложения).
 *  • Очищается при unmount (выход из приложения / выход пользователя).
 */

import { ref, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'


const HEARTBEAT_INTERVAL = 2 * 60 * 1000   


let _intervalId: ReturnType<typeof setInterval> | null = null
let _refCount = 0

export function usePresence() {
  const authStore = useAuthStore()
  const isTabVisible = ref(!document.hidden)

  const sendHeartbeat = async () => {
    if (!authStore.isAuthenticated) return
    try {
      await apiClient.post('/users/heartbeat/')
    } catch {
      
    }
  }

  const handleVisibilityChange = () => {
    isTabVisible.value = !document.hidden
    
    if (!document.hidden) {
      sendHeartbeat()
    }
  }

  const start = () => {
    if (_intervalId !== null) return   

    
    sendHeartbeat()

    _intervalId = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  }

  const stop = () => {
    if (_intervalId !== null) {
      clearInterval(_intervalId)
      _intervalId = null
    }
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  }

  onMounted(() => {
    _refCount++
    start()
  })

  onUnmounted(() => {
    _refCount--
    if (_refCount <= 0) {
      stop()
      _refCount = 0
    }
  })

  return { isTabVisible, sendHeartbeat }
}
