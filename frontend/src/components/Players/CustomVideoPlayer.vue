<template>
  <div class="custom-video-player">
    <video
      ref="videoElement"
      :src="videoUrl"
      :poster="poster"
      class="video-element"
      @loadstart="onLoadStart"
      @loadedmetadata="onLoadedMetadata"
      @canplay="onCanPlay"
      @play="onPlay"
      @pause="onPause"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @error="onError"
      playsinline
    ></video>

    <!-- Кастомные контролы -->
    <div class="video-controls" v-show="showControls">
      <!-- Прогресс бар -->
      <div class="progress-container" @click="seekToPosition">
        <div class="progress-bar">
          <div class="progress-buffer" :style="{ width: bufferProgress + '%' }"></div>
          <div class="progress-played" :style="{ width: playProgress + '%' }"></div>
          <div class="progress-handle" :style="{ left: playProgress + '%' }"></div>
        </div>
      </div>

      <!-- Основные контролы -->
      <div class="controls-main">
        <!-- Кнопки слева -->
        <div class="controls-left">
          <button @click="togglePlay" class="control-btn">
            <svg v-if="!isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
          </button>

          <button @click="skipBackward" class="control-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="19 20 9 12 19 4 19 20"/>
              <line x1="5" y1="19" x2="5" y2="5"/>
            </svg>
            <span class="skip-label">-10</span>
          </button>

          <button @click="skipForward" class="control-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 4 15 12 5 20 5 4"/>
              <line x1="19" y1="5" x2="19" y2="19"/>
            </svg>
            <span class="skip-label">+10</span>
          </button>

          <div class="volume-control">
            <button @click="toggleMute" class="control-btn">
              <svg v-if="!isMuted && volume > 0" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <line x1="23" y1="9" x2="17" y2="15"/>
                <line x1="17" y1="9" x2="23" y2="15"/>
              </svg>
            </button>
            <input
              type="range"
              v-model.number="volume"
              min="0"
              max="1"
              step="0.1"
              @input="setVolume"
              class="volume-slider"
            >
          </div>

          <span class="time-display">
            {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
          </span>
        </div>

        <!-- Кнопки справа -->
        <div class="controls-right">
          <button @click="toggleSpeed" class="control-btn speed-btn">
            {{ speed }}x
          </button>

          <button @click="toggleFullscreen" class="control-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 3 21 3 21 9"/>
              <polyline points="9 21 3 21 3 15"/>
              <line x1="21" y1="3" x2="14" y2="10"/>
              <line x1="3" y1="21" x2="10" y2="14"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Загрузочный индикатор -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="error-overlay">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
    </div>

    <!-- Большая кнопка Play -->
    <div v-if="!isPlaying && !loading && !error" class="play-overlay" @click="togglePlay">
      <svg width="80" height="80" viewBox="0 0 24 24" fill="currentColor">
        <polygon points="5 3 19 12 5 21 5 3"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  videoUrl: string
  poster?: string
  autoplay?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  poster: '',
  autoplay: false
})

const emit = defineEmits<{
  ready: []
  play: []
  pause: []
  timeUpdate: [time: number]
  durationUpdate: [duration: number]
  videoEnded: []
  error: [error: string]
}>()

const videoElement = ref<HTMLVideoElement | null>(null)
const isPlaying = ref(false)
const loading = ref(true)
const error = ref('')
const showControls = ref(false)
const isMuted = ref(false)
const volume = ref(1)
const speed = ref(1)
const currentTime = ref(0)
const duration = ref(0)

const playProgress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const bufferProgress = ref(0)

const controlsTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

const formatTime = (seconds: number) => {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

const onLoadStart = () => {
  loading.value = true
}

const onLoadedMetadata = () => {
  if (videoElement.value) {
    duration.value = videoElement.value.duration
    emit('durationUpdate', duration.value)
  }
}

const onCanPlay = () => {
  loading.value = false
  emit('ready')
  
  if (props.autoplay) {
    play()
  }
}

const onPlay = () => {
  isPlaying.value = true
  emit('play')
}

const onPause = () => {
  isPlaying.value = false
  emit('pause')
}

const onTimeUpdate = () => {
  if (videoElement.value) {
    currentTime.value = videoElement.value.currentTime
    emit('timeUpdate', currentTime.value)
    
    // Обновляем буфер
    if (videoElement.value.buffered.length > 0) {
      const bufferedEnd = videoElement.value.buffered.end(videoElement.value.buffered.length - 1)
      bufferProgress.value = (bufferedEnd / duration.value) * 100
    }
  }
}

const onEnded = () => {
  isPlaying.value = false
  emit('videoEnded')
}

const onError = () => {
  loading.value = false
  error.value = 'Не удалось загрузить видео'
  emit('error', error.value)
}

const togglePlay = () => {
  if (isPlaying.value) {
    pause()
  } else {
    play()
  }
}

const play = () => {
  if (videoElement.value) {
    videoElement.value.play()
  }
}

const pause = () => {
  if (videoElement.value) {
    videoElement.value.pause()
  }
}

const skipBackward = () => {
  if (videoElement.value) {
    videoElement.value.currentTime = Math.max(0, videoElement.value.currentTime - 10)
  }
}

const skipForward = () => {
  if (videoElement.value) {
    videoElement.value.currentTime = Math.min(duration.value, videoElement.value.currentTime + 10)
  }
}

const seekToPosition = (event: MouseEvent) => {
  if (!videoElement.value) return
  
  const progressBar = (event.currentTarget as HTMLElement)
  const rect = progressBar.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percentage = x / rect.width
  videoElement.value.currentTime = percentage * duration.value
}

const toggleMute = () => {
  if (videoElement.value) {
    isMuted.value = !isMuted.value
    videoElement.value.muted = isMuted.value
  }
}

const setVolume = () => {
  if (videoElement.value) {
    videoElement.value.volume = volume.value
    if (volume.value === 0) {
      isMuted.value = true
    } else if (isMuted.value) {
      isMuted.value = false
    }
  }
}

const toggleSpeed = () => {
  const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2]
  const currentIndex = speeds.indexOf(speed.value)
  const nextIndex = (currentIndex + 1) % speeds.length
  const nextSpeed = speeds[nextIndex]
  
  if (nextSpeed !== undefined) {
    speed.value = nextSpeed
    
    if (videoElement.value) {
      videoElement.value.playbackRate = speed.value
    }
  }
}

const toggleFullscreen = () => {
  if (!videoElement.value) return
  
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    videoElement.value.requestFullscreen()
  }
}

const showControlsTemp = () => {
  showControls.value = true
  
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
  
  controlsTimeout.value = window.setTimeout(() => {
    if (isPlaying.value) {
      showControls.value = false
    }
  }, 3000)
}

const handleMouseMove = () => {
  showControlsTemp()
}

const handleKeyPress = (event: KeyboardEvent) => {
  switch (event.code) {
    case 'Space':
      event.preventDefault()
      togglePlay()
      break
    case 'ArrowLeft':
      event.preventDefault()
      skipBackward()
      break
    case 'ArrowRight':
      event.preventDefault()
      skipForward()
      break
    case 'ArrowUp':
      event.preventDefault()
      volume.value = Math.min(1, volume.value + 0.1)
      setVolume()
      break
    case 'ArrowDown':
      event.preventDefault()
      volume.value = Math.max(0, volume.value - 0.1)
      setVolume()
      break
    case 'KeyM':
      toggleMute()
      break
    case 'KeyF':
      toggleFullscreen()
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
})
</script>

<style scoped>
.custom-video-player {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  overflow: hidden;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Контролы */
.video-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  padding: 1rem;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.custom-video-player:hover .video-controls,
.video-controls:hover {
  opacity: 1;
}

/* Прогресс бар */
.progress-container {
  margin-bottom: 1rem;
  cursor: pointer;
}

.progress-bar {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-buffer {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  transition: width 0.3s ease;
}

.progress-played {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  transition: width 0.1s linear;
}

.progress-handle {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: left 0.1s linear;
}

.progress-bar:hover .progress-handle {
  transform: translate(-50%, -50%) scale(1.2);
}

/* Основные контролы */
.controls-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.skip-label {
  font-size: 0.7rem;
  font-weight: 600;
}

/* Громкость */
.volume-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.volume-slider {
  width: 60px;
  height: 4px;
  appearance: none;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

/* Время */
.time-display {
  font-size: 0.875rem;
  color: #fff;
  font-weight: 500;
  min-width: 100px;
}

/* Скорость */
.speed-btn {
  width: auto !important;
  padding: 0 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 600;
}

/* Оверлеи */
.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  z-index: 10;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100px;
  height: 100px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #fff;
}

.play-overlay:hover {
  transform: translate(-50%, -50%) scale(1.1);
  background: rgba(0, 0, 0, 0.8);
}

.play-overlay svg {
  margin-left: 4px;
}
</style>
