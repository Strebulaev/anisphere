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

// Интервал heartbeat: 2 минуты (TTL в Redis 30 мин, поэтому достаточно)
const HEARTBEAT_INTERVAL = 2 * 60 * 1000   // 2 мин

// Singleton — один экземпляр на приложение
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
      // Молча игнорируем: сеть может быть недоступна
    }
  }

  const handleVisibilityChange = () => {
    isTabVisible.value = !document.hidden
    // При возврате на вкладку сразу отправляем пинг
    if (!document.hidden) {
      sendHeartbeat()
    }
  }

  const start = () => {
    if (_intervalId !== null) return   // уже запущен

    // Первый пинг сразу
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
