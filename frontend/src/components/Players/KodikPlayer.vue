<template>
  <div class="kodik-player-container">
    <iframe
      ref="kodikIframe"
      :src="playerUrl"
      class="kodik-iframe"
      frameborder="0"
      allow="autoplay *; fullscreen *; encrypted-media *"
      @load="onIframeLoad"
    ></iframe>
    
    <!-- Индикатор загрузки -->
    <div v-if="loading" class="player-loading">
      <div class="spinner"></div>
      <p>Загрузка плеера...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { normalizeKodikPlayerLink } from '../../config/kodik'

import { useSubscriptionStore } from '../../stores/subscription'

interface Props {
  link: string
  autoplay?: boolean
  season?: number
  episode?: number
  skipButton?: string | null
  /**
   * ID озвучки, выбранной на сайте.
   * Передаётся как default_translation_id — задаёт дефолтную озвучку,
   * но НЕ убирает остальные из списка выбора в плеере.
   */
  translationId?: number | string | null
}

const props = withDefaults(defineProps<Props>(), {
  autoplay: false,
  season: undefined,
  episode: undefined,
  skipButton: null,
  translationId: null,
})

const emit = defineEmits<{
  ready: []
  play: []
  pause: []
  seek: [time: number]
  timeUpdate: [time: number]
  durationUpdate: [duration: number]
  videoStarted: []
  videoEnded: []
  volumeChange: [data: { muted: boolean, volume: number }]
  currentEpisode: [data: { episode: number, season: number, translation: { id: number, title: string } }]
  speedChange: [data: { speed: number }]
  skipButton: [data: { title: string }]
  enterPip: []
  exitPip: []
  error: [error: string]
  /** Пользователь сменил озвучку прямо в плеере Kodik */
  translationChanged: [data: { id: number, title: string }]
}>()

const kodikIframe = ref<HTMLIFrameElement | null>(null)
const loading = ref(true)
const isReady = ref(false)

/**
 * ID последней озвучки, о которой плеер сообщил через kodik_player_current_episode.
 * Используется, чтобы отличить первое сообщение (инициализация) от реальной смены.
 */
const lastKnownTranslationId = ref<number | null>(null)

const playerUrl = computed(() => {
  let url = normalizeKodikPlayerLink(props.link)
  const params: string[] = []

  if (props.autoplay) params.push('autoplay=1')
  if (props.season  !== undefined && props.season  !== null) params.push(`season=${props.season}`)
  if (props.episode !== undefined && props.episode !== null) params.push(`episode=${props.episode}`)
  if (props.skipButton) params.push(`skip_button=${encodeURIComponent(props.skipButton)}`)

  // Задаём дефолтную озвучку через default_translation_id —
  // плеер откроет именно её, но список всех озвучек остаётся полным.
  if (props.translationId) {
    params.push(`default_translation_id=${props.translationId}`)
  }

  params.push('only_shorts=false')

  if (params.length > 0) {
    url += (url.includes('?') ? '&' : '?') + params.join('&')
  }
  return url
})

const onIframeLoad = () => {
  console.log('[KodikPlayer] Iframe загружен')
  loading.value = false
}

const handlePlayerMessage = (event: MessageEvent) => {
  if (!event.data || typeof event.data !== 'object') return
  
  const { key, value } = event.data
  
  if (!key || !key.startsWith('kodik_player_')) return
  
  if (key === 'kodik_player_advert_ended' || key === 'kodik_player_advert_started') {
    return
  }
  
  console.log('[KodikPlayer] Событие:', key, value)

  switch (key) {
    case 'kodik_player_play':
      isReady.value = true
      emit('play')
      break

    case 'kodik_player_pause':
      emit('pause')
      break

    case 'kodik_player_seek':
      if (value && typeof value === 'object' && typeof value.time === 'number') {
        emit('seek', value.time)
      }
      break

    case 'kodik_player_time_update':
      if (typeof value === 'number') {
        emit('timeUpdate', value)
      }
      break

    case 'kodik_player_duration_update':
      if (typeof value === 'number') {
        emit('durationUpdate', value)
      }
      break

    case 'kodik_player_video_started':
      isReady.value = true
      loading.value = false
      emit('ready')
      emit('videoStarted')
      break

    case 'kodik_player_video_ended':
      emit('videoEnded')
      break

    case 'kodik_player_volume_change':
      if (value && typeof value === 'object') {
        emit('volumeChange', {
          muted: value.muted || false,
          volume: value.volume || 1
        })
      }
      break

    case 'kodik_player_current_episode':
      if (value && typeof value === 'object') {
        const translationData = value.translation || { id: 0, title: '' }

        emit('currentEpisode', {
          episode: value.episode,
          season: value.season,
          translation: translationData
        })

        // Определяем, сменил ли пользователь озвучку внутри плеера.
        // Первое событие после загрузки iframe — инициализация (lastKnownTranslationId ещё null).
        // Все последующие события с другим id — реальная смена пользователем.
        const incomingId = translationData.id
        if (incomingId) {
          if (lastKnownTranslationId.value !== null && lastKnownTranslationId.value !== incomingId) {
            console.log(
              '[KodikPlayer] Пользователь сменил озвучку в плеере:',
              lastKnownTranslationId.value, '→', incomingId,
              translationData.title
            )
            emit('translationChanged', { id: incomingId, title: translationData.title })
          }
          lastKnownTranslationId.value = incomingId
        }
      }
      break

    case 'kodik_player_speed_change':
      if (value && typeof value === 'object' && typeof value.speed === 'number') {
        emit('speedChange', value)
      }
      break

    case 'kodik_player_skip_button':
      if (value && typeof value === 'object' && value.title) {
        emit('skipButton', { title: value.title })
      }
      break

    case 'kodik_player_enter_pip':
      emit('enterPip')
      break

    case 'kodik_player_exit_pip':
      emit('exitPip')
      break
  }
}

const sendMessage = (data: any) => {
  if (!kodikIframe.value || !kodikIframe.value.contentWindow) {
    console.warn('[KodikPlayer] Iframe не доступен')
    return
  }
  kodikIframe.value.contentWindow.postMessage(data, '*')
}

const play = () => sendMessage({ key: 'kodik_player_api', value: { method: 'play' } })
const pause = () => sendMessage({ key: 'kodik_player_api', value: { method: 'pause' } })
const seek = (seconds: number) => sendMessage({ key: 'kodik_player_api', value: { method: 'seek', seconds } })
const setVolume = (volume: number) => sendMessage({ key: 'kodik_player_api', value: { method: 'volume', volume: Math.max(0, Math.min(1, volume)) } })
const mute = () => sendMessage({ key: 'kodik_player_api', value: { method: 'mute' } })
const unmute = () => sendMessage({ key: 'kodik_player_api', value: { method: 'unmute' } })
const setSpeed = (speed: number) => sendMessage({ key: 'kodik_player_api', value: { method: 'speed', speed: Math.max(0.25, Math.min(2, speed)) } })
const changeEpisode = (episode: number, season?: number) => {
  const data: any = { method: 'change_episode', episode }
  if (season !== undefined) data.season = season
  sendMessage({ key: 'kodik_player_api', value: data })
}
const enterPip = () => sendMessage({ key: 'kodik_player_api', value: { method: 'enter_pip' } })
const exitPip = () => sendMessage({ key: 'kodik_player_api', value: { method: 'exit_pip' } })
const getTime = () => sendMessage({ key: 'kodik_player_api', value: { method: 'get_time' } })

defineExpose({
  play, pause, seek, setVolume, mute, unmute, setSpeed,
  changeEpisode, enterPip, exitPip, getTime,
  isReady: () => isReady.value
})

// ============================================================================
// ==================== КОММЕНТАРИЙ: ПОДПИСКА ОТКЛЮЧЕНА =======================
// ============================================================================
onMounted(() => {
  window.addEventListener('message', handlePlayerMessage)
  //   updateAdBlockerStatus()
  // }).catch(() => {
  //   updateAdBlockerStatus()
  // })
})

onUnmounted(() => {
  window.removeEventListener('message', handlePlayerMessage)
})

watch(() => props.link, () => {
  loading.value = true
  isReady.value = false
  lastKnownTranslationId.value = null  // сбрасываем при смене ссылки
})
</script>

<style scoped>
.kodik-player-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
}

.kodik-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.player-loading {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  z-index: 10;
}

.spinner {
  width: 48px; height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

.player-loading p {
  margin: 0;
  font-size: 0.875rem;
  color: #a0a0a0;
}
</style>
