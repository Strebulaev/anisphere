/**
 * useAnimeTab - отслеживает, что пользователь смотрит/открыл аниме.
 *
 * Правила:
 *  activity_type = 'player'   - видео воспроизводится (вызывай setPlayerActive(true))
 *  activity_type = 'watching' - вкладка открыта, но плеер не идёт (по умолчанию)
 *
 * Пинг (POST /anime/active-tab/) отправляется:
 *  • Сразу при mount
 *  • Каждые TAB_PING_INTERVAL мс пока вкладка ВИДИМА или плеер активен
 *  • При смене activity_type
 *  • При возврате на вкладку
 *
 * Удаление (DELETE /anime/active-tab/?anime_id=N) при unmount.
 *
 * Временны́е окна (должны совпадать с бэкендом):
 *  • player:   2 мин  → пингуем каждые 90 сек
 *  • watching: 10 мин → пингуем каждые 3 мин
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const PLAYER_PING_INTERVAL   = 90  * 1000   
const WATCHING_PING_INTERVAL = 3   * 60 * 1000  

export function useAnimeTab(animeId: number) {
  const authStore = useAuthStore()

  const activityType = ref<'watching' | 'player'>('watching')
  const currentEpisode = ref<number | null>(null)
  let _interval: ReturnType<typeof setInterval> | null = null

  
  const sendPing = async () => {
    if (!authStore.isAuthenticated || !animeId) return
    try {
      await apiClient.post('/anime/active-tab/', {
        anime_id: animeId,
        activity_type: activityType.value,
        current_episode: currentEpisode.value,
      })
    } catch {
      
    }
  }

  
  const removeTab = async () => {
    if (!authStore.isAuthenticated || !animeId) return
    try {
      await apiClient.delete('/anime/active-tab/', { params: { anime_id: animeId } })
    } catch { /* ignore */ }
  }

  
  const resetInterval = () => {
    if (_interval) { clearInterval(_interval); _interval = null }
    const ms = activityType.value === 'player'
      ? PLAYER_PING_INTERVAL
      : WATCHING_PING_INTERVAL
    _interval = setInterval(() => {
      if (!document.hidden || activityType.value === 'player') {
        sendPing()
      }
    }, ms)
  }

  

  const setPlayerActive = (active: boolean, episode?: number) => {
    if (episode !== undefined) currentEpisode.value = episode
    const newType = active ? 'player' : 'watching'
    if (activityType.value !== newType) {
      activityType.value = newType
      sendPing()
      resetInterval()
    }
  }

  const setEpisode = (episode: number) => {
    currentEpisode.value = episode
    sendPing()
  }

  
  const onVisibilityChange = () => {
    if (!document.hidden) sendPing()
  }

  
  onMounted(() => {
    sendPing()
    resetInterval()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    if (_interval) clearInterval(_interval)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    removeTab()
  })

  return { activityType, currentEpisode, setPlayerActive, setEpisode, sendPing }
}
