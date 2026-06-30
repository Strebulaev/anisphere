import { ref, computed } from 'vue'


const showFloatingPlayer = ref(false)
const floatingAnimeId = ref<number | null>(null)
const floatingAnimeTitle = ref('')
const floatingEpisode = ref(1)
const floatingSeason = ref(1)
const floatingPlayerLink = ref('')
const floatingTranslationId = ref<number | string | null>(null)
const floatingPosition = ref({ x: 20, y: 20 })
const floatingSize = ref({ width: 480, height: 270 })

export function useFloatingPlayer() {
  const openFloatingPlayer = (params: {
    animeId: number
    animeTitle: string
    episode: number
    season?: number
    playerLink: string
    translationId?: number | string | null
  }) => {
    floatingAnimeId.value = params.animeId
    floatingAnimeTitle.value = params.animeTitle
    floatingEpisode.value = params.episode
    floatingSeason.value = params.season || 1
    floatingPlayerLink.value = params.playerLink
    floatingTranslationId.value = params.translationId || null
    showFloatingPlayer.value = true
    
    
    const saved = localStorage.getItem('floating_player_state')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        floatingPosition.value = parsed.position || floatingPosition.value
        floatingSize.value = parsed.size || floatingSize.value
      } catch {}
    }
  }

  const closeFloatingPlayer = () => {
    showFloatingPlayer.value = false
  }

  const updatePosition = (pos: { x: number; y: number }) => {
    floatingPosition.value = pos
    saveState()
  }

  const updateSize = (size: { width: number; height: number }) => {
    floatingSize.value = size
    saveState()
  }

  const saveState = () => {
    localStorage.setItem('floating_player_state', JSON.stringify({
      position: floatingPosition.value,
      size: floatingSize.value
    }))
  }

  const isOpen = computed(() => showFloatingPlayer.value)

  return {
    
    showFloatingPlayer,
    floatingAnimeId,
    floatingAnimeTitle,
    floatingEpisode,
    floatingSeason,
    floatingPlayerLink,
    floatingTranslationId,
    floatingPosition,
    floatingSize,
    
    
    openFloatingPlayer,
    closeFloatingPlayer,
    updatePosition,
    updateSize,
    isOpen
  }
}
