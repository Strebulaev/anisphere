/**
 * useEpisodeProgress - управление прогрессом просмотра по сериям.
 *
 * Возможности:
 *  - Загрузка прогресса с сервера (GET /anime/{id}/episode-progress/)
 *  - Авто-обновление позиции каждые 10 сек
 *  - Авто-отметка "просмотрено" при 85% / эндинге
 *  - Ручная отметка / пропуск
 *  - Булк-синхр (ползунок "я смотрел до X серии")
 *  - Отмена через тост (undo)
 *  - Тост-уведомления через useToast
 */

import { ref, computed, readonly } from 'vue'
import apiClient from '@/api/client'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'



export type EpisodeStatus = 'not_started' | 'in_progress' | 'watched' | 'skipped'

export interface EpisodeProgressItem {
  episode_number: number
  status: EpisodeStatus
  last_position: number
  duration: number | null
  progress_percent: number
  is_manually_marked: boolean
  watched_at: string | null
}

export interface AnimeProgressSummary {
  anime_id: number
  total: number
  watched_count: number
  percent: number
  episodes: EpisodeProgressItem[]
}



export function useEpisodeProgress(animeId: number) {
  const toast   = useToast()
  const auth    = useAuthStore()

  
  const episodes      = ref<Map<number, EpisodeProgressItem>>(new Map())
  const totalEpisodes = ref(0)
  const loading       = ref(false)
  const loaded        = ref(false)

  
  let saveTimer: ReturnType<typeof setTimeout> | null = null
  let lastSavedTime = 0

  

  const watchedCount = computed(() =>
    [...episodes.value.values()].filter(e => e.status === 'watched' || e.status === 'skipped').length
  )

  const progressPercent = computed(() => {
    if (!totalEpisodes.value) return 0
    return Math.round(watchedCount.value / totalEpisodes.value * 100)
  })

  const nextEpisodeToWatch = computed(() => {
    for (let i = 1; i <= totalEpisodes.value; i++) {
      const ep = episodes.value.get(i)
      if (!ep || ep.status === 'not_started' || ep.status === 'in_progress') {
        return i
      }
    }
    return null
  })

  const lastWatchedEpisode = computed(() => {
    let last = 0
    for (const ep of episodes.value.values()) {
      if ((ep.status === 'watched' || ep.status === 'skipped') && ep.episode_number > last) {
        last = ep.episode_number
      }
    }
    return last || null
  })

  

  const getEpisode = (num: number): EpisodeProgressItem => {
    return episodes.value.get(num) ?? {
      episode_number: num,
      status: 'not_started',
      last_position: 0,
      duration: null,
      progress_percent: 0,
      is_manually_marked: false,
      watched_at: null,
    }
  }

  const isWatched = (num: number) => {
    const ep = episodes.value.get(num)
    return ep?.status === 'watched' || ep?.status === 'skipped'
  }

  const isInProgress = (num: number) => episodes.value.get(num)?.status === 'in_progress'

  

  const loadProgress = async () => {
    if (!auth.isAuthenticated) return
    try {
      loading.value = true
      const res = await apiClient.get<AnimeProgressSummary>(`/anime/${animeId}/episode-progress/`)
      totalEpisodes.value = res.data.total

      const map = new Map<number, EpisodeProgressItem>()
      for (const ep of res.data.episodes) {
        map.set(ep.episode_number, ep)
      }
      episodes.value = map
      loaded.value = true
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка загрузки:', e)
    } finally {
      loading.value = false
    }
  }

  

  const updatePosition = (episodeNum: number, position: number, duration?: number) => {
    if (!auth.isAuthenticated) return

    
    const existing = getEpisode(episodeNum)
    const updated: EpisodeProgressItem = {
      ...existing,
      episode_number: episodeNum,
      last_position: position,
      duration: duration ?? existing.duration,
      status: existing.status === 'not_started' ? 'in_progress' : existing.status,
      progress_percent: duration ? Math.round(position / duration * 100) : existing.progress_percent,
    }
    if (updated.status !== 'watched' && updated.status !== 'skipped') {
      episodes.value.set(episodeNum, updated)
    }

    
    const now = Date.now()
    if (now - lastSavedTime < 9500) return
    lastSavedTime = now

    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(async () => {
      if (isWatched(episodeNum)) return 
      try {
        await apiClient.post(`/anime/${animeId}/episode-progress/`, {
          episode_number: episodeNum,
          last_position: Math.floor(position),
          duration: duration ? Math.floor(duration) : undefined,
          action: 'progress',
        })
      } catch (e) {
        console.warn('[EpisodeProgress] Ошибка сохранения позиции:', e)
      }
    }, 500)
  }

  

  const autoMarkWatched = async (episodeNum: number) => {
    if (!auth.isAuthenticated) return
    if (isWatched(episodeNum)) return

    
    const existing = getEpisode(episodeNum)
    episodes.value.set(episodeNum, {
      ...existing,
      status: 'watched',
      progress_percent: 100,
      watched_at: new Date().toISOString(),
      is_manually_marked: false,
    })

    
    toast.success(`Серия ${episodeNum} просмотрена`, {
      duration: 5000,
      action: {
        label: 'Отменить',
        handler: () => undoMark(episodeNum),
      },
    })

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        episode_number: episodeNum,
        action: 'mark',
      })
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка авто-отметки:', e)
    }
  }

  

  const markWatched = async (episodeNum: number) => {
    if (!auth.isAuthenticated) return
    if (isWatched(episodeNum)) return

    const existing = getEpisode(episodeNum)
    episodes.value.set(episodeNum, {
      ...existing,
      status: 'watched',
      progress_percent: 100,
      watched_at: new Date().toISOString(),
      is_manually_marked: true,
    })

    toast.success(`Серия ${episodeNum} отмечена`, {
      duration: 4000,
      action: {
        label: 'Отменить',
        handler: () => undoMark(episodeNum),
      },
    })

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        episode_number: episodeNum,
        action: 'mark',
      })
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка ручной отметки:', e)
      
      episodes.value.set(episodeNum, existing)
      toast.error('Не удалось сохранить отметку')
    }
  }

  

  const skipEpisode = async (episodeNum: number) => {
    if (!auth.isAuthenticated) return

    const existing = getEpisode(episodeNum)
    episodes.value.set(episodeNum, {
      ...existing,
      status: 'skipped',
      is_manually_marked: true,
    })

    toast.info(`Серия ${episodeNum} пропущена`, {
      duration: 4000,
      action: {
        label: 'Отменить',
        handler: () => undoMark(episodeNum),
      },
    })

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        episode_number: episodeNum,
        action: 'skip',
      })
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка пропуска:', e)
      episodes.value.set(episodeNum, existing)
    }
  }

  

  const undoMark = async (episodeNum: number) => {
    if (!auth.isAuthenticated) return

    const existing = getEpisode(episodeNum)
    episodes.value.set(episodeNum, {
      ...existing,
      status: 'in_progress',
      is_manually_marked: false,
      watched_at: null,
    })

    try {
      await apiClient.post(`/anime/${animeId}/episode-progress/${episodeNum}/undo/`)
      toast.info(`Отметка снята с серии ${episodeNum}`)
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка отмены:', e)
      episodes.value.set(episodeNum, existing)
    }
  }

  

  const bulkSyncUpTo = async (watchedUpTo: number) => {
    if (!auth.isAuthenticated) return
    try {
      loading.value = true
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        action: 'bulk',
        watched_up_to: watchedUpTo,
      })

      
      const now = new Date().toISOString()
      for (let i = 1; i <= watchedUpTo; i++) {
        episodes.value.set(i, {
          episode_number: i,
          status: 'watched',
          last_position: 0,
          duration: null,
          progress_percent: 100,
          is_manually_marked: true,
          watched_at: now,
        })
      }

      toast.success(`${watchedUpTo} серий отмечено как просмотренных`, { duration: 4000 })
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка булк-синхра:', e)
      toast.error('Не удалось сохранить прогресс')
    } finally {
      loading.value = false
    }
  }

  

  const resetProgress = async () => {
    if (!auth.isAuthenticated) return
    try {
      loading.value = true
      await apiClient.post(`/anime/${animeId}/episode-progress/`, {
        action: 'bulk',
        reset: true,
      })
      episodes.value = new Map()
      toast.info('Прогресс сброшен')
    } catch (e) {
      console.warn('[EpisodeProgress] Ошибка сброса:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    
    episodes: readonly(episodes),
    totalEpisodes: readonly(totalEpisodes),
    loading: readonly(loading),
    loaded: readonly(loaded),

    
    watchedCount,
    progressPercent,
    nextEpisodeToWatch,
    lastWatchedEpisode,

    
    getEpisode,
    isWatched,
    isInProgress,

    
    loadProgress,
    updatePosition,
    autoMarkWatched,
    markWatched,
    skipEpisode,
    undoMark,
    bulkSyncUpTo,
    resetProgress,
  }
}
