import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface FloatingPlayerState {
  isVisible: boolean
  videoUrl: string | null
  title: string | null
  episode?: number | null
  animeId?: number | null
  position?: { x: number; y: number }
}

interface CurrentAnime {
  anime_id: number
  anime_title: string
  episode: number | null
  season: string | null
  player_link: string
  translation_id: number | null
  start_time?: number
}

export const useFloatingPlayerStore = defineStore('floatingPlayer', () => {
  const state = ref<FloatingPlayerState>({
    isVisible: false,
    videoUrl: null,
    title: null,
    episode: null,
    animeId: null,
    position: { x: 0, y: 0 }
  })

  const currentAnime = ref<CurrentAnime | null>(null)

  const isVisible = computed(() => state.value.isVisible)
  const videoUrl = computed(() => state.value.videoUrl)
  const title = computed(() => state.value.title)
  const episode = computed(() => state.value.episode)
  const animeId = computed(() => state.value.animeId)

  const show = (videoUrl: string, title?: string, episode?: number, animeId?: number) => {
    state.value = {
      isVisible: true,
      videoUrl,
      title: title || null,
      episode: episode || null,
      animeId: animeId || null,
      position: state.value.position
    }
  }

  const hide = () => {
    state.value.isVisible = false
    state.value.videoUrl = null
  }

  const updatePosition = (x: number, y: number) => {
    state.value.position = { x, y }
  }

  const setCurrentAnime = (anime: CurrentAnime) => {
    currentAnime.value = anime
  }

  const clearCurrentAnime = () => {
    currentAnime.value = null
  }

  const reset = () => {
    state.value = {
      isVisible: false,
      videoUrl: null,
      title: null,
      episode: null,
      animeId: null,
      position: { x: 0, y: 0 }
    }
    currentAnime.value = null
  }

  return {
    state,
    isVisible,
    videoUrl,
    title,
    episode,
    animeId,
    currentAnime,
    show,
    hide,
    updatePosition,
    setCurrentAnime,
    clearCurrentAnime,
    reset
  }
})