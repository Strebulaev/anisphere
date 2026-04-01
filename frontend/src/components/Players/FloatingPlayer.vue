<template>
  <Teleport to="body">
    <Transition name="float">
      <div
        v-if="visible"
        ref="playerContainer"
        class="floating-player"
        :class="{ 
          minimized: isMinimized, 
          'is-dragging': isDragging,
          'is-resizing': isResizing
        }"
        :style="playerStyle"
        @mousedown="startDrag"
        @touchstart.prevent="startDrag"
      >
        <!-- Заголовок с информацией -->
        <div class="fp-header" @dblclick="toggleMinimize">
          <div class="fp-info">
            <span class="fp-title">{{ animeTitle }}</span>
            <span class="fp-episode" v-if="episodeInfo">Серия {{ episodeInfo }}</span>
          </div>
          <div class="fp-controls">
            <button class="fp-btn" @click.stop="toggleFullscreen" :title="isFullscreen ? 'Выйти из полноэкранного' : 'Полноэкранный режим'">
              <svg v-if="isFullscreen" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
              </svg>
            </button>
            <button class="fp-btn" @click.stop="toggleMinimize" :title="isMinimized ? 'Развернуть' : 'Свернуть'">
              <svg v-if="isMinimized" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline>
                <line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="3" x2="9" y2="21"></line>
              </svg>
            </button>
            <button class="fp-btn fp-close" @click.stop="close" title="Закрыть">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <!-- Плеер (только если не минимизирован) -->
        <div v-if="!isMinimized" class="fp-content">
          <div class="fp-video-wrapper">
            <iframe
              v-if="playerLink"
              ref="kodikIframe"
              :src="playerLink"
              class="kodik-iframe"
              frameborder="0"
              allow="autoplay *; fullscreen *; encrypted-media *"
            ></iframe>
            <div v-else class="fp-no-video">
              <span>Видео недоступно</span>
            </div>
          </div>
        </div>

        <!-- Минимизированный режим - только заголовок -->
        <div v-else class="fp-minimized-content">
          <span class="fp-mini-time">{{ formatTime(currentTime) }}</span>
        </div>

        <!-- Ручка для изменения размера -->
        <div 
          v-if="!isMinimized"
          class="fp-resize-handle"
          :class="{ 'fp-resize-hidden': isFullscreen }"
          @mousedown.stop.prevent="startResize"
          @touchstart.stop.prevent="startResize"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
            <circle cx="2" cy="2" r="1.5"/>
            <circle cx="7" cy="2" r="1.5"/>
            <circle cx="2" cy="7" r="1.5"/>
            <circle cx="7" cy="7" r="1.5"/>
          </svg>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  visible: boolean
  animeId?: number
  animeTitle?: string
  episode?: number
  season?: number
  playerLink?: string
  translationId?: number | string | null
  startTime?: number
}

const props = withDefaults(defineProps<Props>(), {
  animeId: 0,
  animeTitle: 'Аниме',
  episode: 1,
  season: 1,
  playerLink: '',
  translationId: null,
  startTime: 0
})

const emit = defineEmits<{
  close: []
  expand: []
  play: []
  pause: []
}>()

const router = useRouter()

// Состояние
const playerContainer = ref<HTMLElement | null>(null)
const kodikIframe = ref<HTMLIFrameElement | null>(null)
const isMinimized = ref(false)
const isDragging = ref(false)
const isResizing = ref(false)
const isFullscreen = ref(false)
const playerReady = ref(false)

// Флаг для отслеживания необходимости перемотки
const needsSeek = ref(false)

// Позиция и размер
const position = ref({ x: 20, y: 20 })
const size = ref({ width: 480, height: 270 })
const dragOffset = ref({ x: 0, y: 0 })
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 })

// Вычисляемые
const episodeInfo = computed(() => props.episode)

const progressPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const currentTime = ref(0)
const duration = ref(0)

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const playerStyle = computed(() => {
  if (isFullscreen.value) {
    return {
      left: '0px',
      top: '0px',
      width: '100vw',
      height: '100vh',
      zIndex: '9999999',
      borderRadius: '0'
    }
  }
  return {
    left: `${position.value.x}px`,
    top: `${position.value.y}px`,
    width: isMinimized.value ? '280px' : `${size.value.width}px`,
    height: isMinimized.value ? '42px' : `${size.value.height}px`,
    zIndex: '999999'
  }
})

// Drag
const startDrag = (e: MouseEvent | TouchEvent) => {
  if ((e.target as HTMLElement).closest('.fp-btn') || (e.target as HTMLElement).closest('.fp-resize-handle')) {
    return
  }
  
  isDragging.value = true
  const touch = 'touches' in e ? e.touches[0] : null
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY
  
  dragOffset.value = {
    x: clientX - position.value.x,
    y: clientY - position.value.y
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return

  const touch = 'touches' in e ? e.touches[0] : null
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY

  let newX = clientX - dragOffset.value.x
  let newY = clientY - dragOffset.value.y

  const w = isMinimized.value ? 280 : size.value.width
  const h = isMinimized.value ? 42 : size.value.height
  
  newX = Math.max(0, Math.min(window.innerWidth - w, newX))
  newY = Math.max(0, Math.min(window.innerHeight - h, newY))

  position.value = { x: newX, y: newY }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  savePosition()
}

// Resize
const startResize = (e: MouseEvent | TouchEvent) => {
  isResizing.value = true
  const touch = 'touches' in e ? e.touches[0] : null
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY
  
  resizeStart.value = {
    x: clientX,
    y: clientY,
    width: size.value.width,
    height: size.value.height
  }

  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', onResize)
  document.addEventListener('touchend', stopResize)
}

const onResize = (e: MouseEvent | TouchEvent) => {
  if (!isResizing.value) return

  const touch = 'touches' in e ? e.touches[0] : null
  const clientX = touch ? touch.clientX : (e as MouseEvent).clientX
  const clientY = touch ? touch.clientY : (e as MouseEvent).clientY

  const deltaX = clientX - resizeStart.value.x
  const deltaY = clientY - resizeStart.value.y

  const newWidth = Math.max(320, Math.min(window.innerWidth - position.value.x, resizeStart.value.width + deltaX))
  const newHeight = Math.max(180, Math.min(window.innerHeight - position.value.y, resizeStart.value.height + deltaY))

  size.value = { width: newWidth, height: newHeight }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', onResize)
  document.removeEventListener('touchend', stopResize)
  saveSize()
}

// Управление
const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value
}

const close = () => {
  emit('close')
}

const goToWatch = () => {
  if (props.animeId) {
    router.push(`/anime/${props.animeId}/watch?episode=${props.episode}`)
    emit('close')
  }
}

// Fullscreen
const toggleFullscreen = () => {
  if (!playerContainer.value) return
  
  if (!isFullscreen.value) {
    if (playerContainer.value.requestFullscreen) {
      playerContainer.value.requestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// Управление плеером через postMessage
const sendMessage = (data: any) => {
  if (!kodikIframe.value?.contentWindow) return
  kodikIframe.value.contentWindow.postMessage(data, '*')
}

// Обработка сообщений от Kodik плеера
const handlePlayerMessage = (event: MessageEvent) => {
  if (!event.data || typeof event.data !== 'object') return
  
  const { key, value } = event.data
  if (!key || !key.startsWith('kodik_player_')) return

  switch (key) {
    case 'kodik_player_play':
      isPlaying.value = true
      emit('play')
      break
    case 'kodik_player_pause':
      isPlaying.value = false
      emit('pause')
      break
    case 'kodik_player_time_update':
      if (typeof value === 'number') {
        currentTime.value = value
      }
      break
    case 'kodik_player_duration_update':
      if (typeof value === 'number') {
        duration.value = value
        // После получения duration делаем перемотку если нужно
        if (needsSeek.value && props.startTime > 0) {
          setTimeout(() => {
            sendMessage({ key: 'kodik_player_api', value: { method: 'seek', seconds: props.startTime } })
            needsSeek.value = false
          }, 500)
        }
      }
      break
    case 'kodik_player_volume_change':
      if (value && typeof value === 'object') {
        isMuted.value = Boolean((value as any).muted)
      }
      break
    case 'kodik_player_video_started':
      playerReady.value = true
      // Если есть startTime и видео началось - перематываем
      if (props.startTime > 0) {
        needsSeek.value = true
      }
      break
  }
}

const isPlaying = ref(false)
const isMuted = ref(false)

// Сохранение/загрузка позиции
const savePosition = () => {
  localStorage.setItem('floating_player_state', JSON.stringify({
    position: position.value,
    size: size.value
  }))
}

const saveSize = () => {
  localStorage.setItem('floating_player_state', JSON.stringify({
    position: position.value,
    size: size.value
  }))
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  window.addEventListener('message', handlePlayerMessage)
  
  const saved = localStorage.getItem('floating_player_state')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      position.value = parsed.position || position.value
      size.value = parsed.size || size.value
    } catch {}
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('message', handlePlayerMessage)
})

// Следим за изменением episode
watch(() => props.episode, () => {
  if (kodikIframe.value && props.playerLink) {
    const url = new URL(props.playerLink)
    url.searchParams.set('episode', String(props.episode))
    if (props.season) {
      url.searchParams.set('season', String(props.season))
    }
    kodikIframe.value.src = url.toString()
    // Сбрасываем флаг при смене эпизода
    needsSeek.value = false
    playerReady.value = false
  }
})

// Следим за изменением startTime
watch(() => props.startTime, (newTime) => {
  if (newTime > 0 && playerReady.value && kodikIframe.value?.contentWindow) {
    // Если плеер уже готов - сразу перематываем
    sendMessage({ key: 'kodik_player_api', value: { method: 'seek', seconds: newTime } })
  } else if (newTime > 0) {
    // Иначе ждём когда плеер будет готов
    needsSeek.value = true
  }
})
</script>

<style scoped>
.floating-player {
  position: fixed;
  background: #1a1a1a;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  transition: width 0.2s ease, height 0.2s ease;
  cursor: default;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.floating-player.is-dragging {
  cursor: grabbing;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6);
}

.floating-player.is-resizing {
  cursor: se-resize;
}

.floating-player.minimized {
  cursor: pointer;
}

/* Header */
.fp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  user-select: none;
}

.fp-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.fp-title {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fp-episode {
  color: #888;
  font-size: 11px;
}

.fp-controls {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.fp-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #888;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.fp-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.fp-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* Content */
.fp-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 42px);
}

.fp-video-wrapper {
  flex: 1;
  background: #000;
  min-height: 0;
}

.kodik-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.fp-no-video {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 13px;
}

/* Minimized */
.fp-minimized-content {
  padding: 0 12px;
  display: flex;
  align-items: center;
}

.fp-mini-title {
  color: #888;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Resize handle */
.fp-resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  cursor: se-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  opacity: 0.5;
  transition: opacity 0.15s;
}

.fp-resize-handle:hover {
  opacity: 1;
  color: #888;
}

.fp-resize-handle.fp-resize-hidden {
  display: none;
}

/* Transition */
.float-enter-active,
.float-leave-active {
  transition: all 0.3s ease;
}

.float-enter-from,
.float-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
