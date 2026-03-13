<template>
  <div class="anime-player-modal" v-if="show">
    <div class="modal-backdrop" @click="close"></div>
    <div class="player-container">
      <!-- Заголовок модального окна -->
      <div class="player-header">
        <div class="anime-info">
          <h2 class="anime-title">{{ anime?.title_ru || anime?.title_en }}</h2>
          <div class="episode-info">
            <span v-if="selectedEpisode">Серия {{ selectedEpisode }}</span>
            <span v-if="selectedSeason && seasonsCount > 1"> • Сезон {{ selectedSeason }}</span>
            <span v-if="selectedTranslation"> • {{ selectedTranslation.name }}</span>
          </div>
        </div>
        <button @click="close" class="close-btn">✕</button>
      </div>

      <!-- Плеер -->
      <div class="video-container">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Загрузка видео...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p style="color: #ef4444; font-weight: 500;">{{ error }}</p>
          <button @click="retryLoad" class="retry-btn">
            Попробовать снова
          </button>
        </div>

        <!-- Kodik плеер -->
        <KodikPlayer
          v-else-if="playerLink && useKodikPlayer"
          ref="kodikPlayer"
          :link="playerLink"
          :season="selectedSeason"
          :episode="selectedEpisode"
          :autoplay="autoplay"
          :skipButton="skipButton"
          @ready="onPlayerReady"
          @play="onPlay"
          @pause="onPause"
          @timeUpdate="onTimeUpdate"
          @durationUpdate="onDurationUpdate"
          @videoEnded="onVideoEnded"
          @currentEpisode="onCurrentEpisode"
          @error="onPlayerError"
        />

        <!-- Обычный HTML5 плеер -->
        <video
          v-else-if="videoUrl && !useKodikPlayer"
          ref="videoPlayer"
          class="video-player"
          :src="videoUrl"
          controls
          preload="auto"
          @loadstart="onLoadStart"
          @loadeddata="onLoadedData"
          @timeupdate="onVideoTimeUpdate"
          @error="onVideoError"
          @ended="saveWatchProgress"
        >
          Ваш браузер не поддерживает воспроизведение видео.
        </video>

        <div v-else class="no-video-state">
          <p>Видео не найдено</p>
        </div>
      </div>

      <!-- Панель управления -->
      <div class="player-controls" v-if="!loading && !error">
        <!-- Выбор сезона -->
        <div class="control-section" v-if="seasonsCount > 1">
          <label class="control-label">Сезон:</label>
          <select 
            v-model="selectedSeason" 
            @change="changeSeason"
            class="season-select"
          >
            <option 
              v-for="season in seasonsCount" 
              :key="season" 
              :value="season"
            >
              Сезон {{ season }}
            </option>
          </select>
        </div>

        <!-- Выбор серии -->
        <div class="control-section">
          <label class="control-label">Серия:</label>
          <select 
            v-model="selectedEpisode" 
            @change="changeEpisode"
            class="episode-select"
          >
            <option 
              v-for="episode in availableEpisodes" 
              :key="episode" 
              :value="episode"
            >
              Серия {{ episode }}
            </option>
          </select>
        </div>

        <!-- Выбор перевода -->
        <div class="control-section">
          <label class="control-label">Перевод:</label>
          <select 
            v-model="selectedTranslationId" 
            @change="changeTranslation"
            class="translation-select"
          >
            <option 
              v-for="translation in translations" 
              :key="translation.id" 
              :value="translation.id"
            >
              {{ translation.name }} ({{ translation.type === 'voice' ? 'Озвучка' : 'Субтитры' }})
            </option>
          </select>
        </div>

        <!-- Прогресс просмотра -->
        <div class="control-section" v-if="watchProgress[selectedEpisode]">
          <label class="control-label">Прогресс:</label>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: watchProgress[selectedEpisode] + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ Math.round(watchProgress[selectedEpisode] || 0) }}%</span>
        </div>

        <!-- Управление плеером -->
        <div class="control-section player-actions">
          <button @click="togglePlay" class="control-btn" :title="isPlaying ? 'Пауза' : 'Воспроизвести'">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <button @click="seekBackward" class="control-btn" title="-10 сек">
            -10
          </button>
          <button @click="seekForward" class="control-btn" title="+10 сек">
            +10
          </button>
          <button @click="toggleMute" class="control-btn" :title="isMuted ? 'Включить звук' : 'Отключить звук'">
            {{ isMuted ? '🔇' : '🔊' }}
          </button>
        </div>
      </div>

      <!-- Список серий -->
      <div class="episodes-list" v-if="episodesCount > 1">
        <h3>Все серии ({{ episodesCount }})</h3>
        <div class="episodes-grid">
          <button
            v-for="episode in episodesCount"
            :key="episode"
            @click="selectEpisode(episode)"
            :class="['episode-btn', { 
              active: episode === selectedEpisode, 
              watched: isEpisodeWatched(episode) 
            }]"
          >
            {{ episode }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import apiClient from '@/api/client'
import KodikPlayer from './KodikPlayer.vue'

interface Translation {
  id: string
  name: string
  type: string
  episodes?: string | number
}

interface Props {
  show: boolean
  anime: any
  initialEpisode?: number
  initialSeason?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialEpisode: 1,
  initialSeason: 1
})

const emit = defineEmits<{
  close: []
}>()

// Data
const videoUrl = ref<string>('')
const playerLink = ref<string>('')
const loading = ref(true)
const error = ref('')
const selectedEpisode = ref(1)
const selectedSeason = ref(1)
const selectedTranslationId = ref('')
const seasonsCount = ref(1)
const episodesCount = ref(1)
const translations = ref<Translation[]>([])
const videoPlayer = ref<HTMLVideoElement | null>(null)
const kodikPlayer = ref<InstanceType<typeof KodikPlayer> | null>(null)
const currentTime = ref(0)
const duration = ref(0)
const watchProgress = ref<{[key: number]: number}>({})
const autoplay = ref(false)
const useKodikPlayer = ref(true)
const skipButton = ref<string | null>(null)

// Player state
const isPlaying = ref<boolean>(false)
const isMuted = ref<boolean>(false)
const volume = ref<number>(1)

// Computed
const selectedTranslation = computed(() => 
  translations.value.find(t => t.id === selectedTranslationId.value)
)
const availableEpisodes = computed(() => 
  Array.from({ length: episodesCount.value || 1 }, (_, i) => i + 1)
)

// Load video
const loadVideo = async () => {
  loading.value = true
  error.value = ''
  videoUrl.value = ''
  playerLink.value = ''

  // Загружаем временные метки опенинга/эндинга параллельно (не блокируем плеер)
  if (props.anime?.id && skipButton.value === null) {
    apiClient.get(`/anime/${props.anime.id}/themes/`)
      .then(r => { skipButton.value = r.data.skip_button ?? null })
      .catch(() => { /* нет меток — не критично */ })
  }

  try {
    // Получаем ссылку на Kodik плеер через официальный API
    if (props.anime?.id) {
      const response = await apiClient.get(`/anime/${props.anime.id}/kodik_player/`)
      const kodikLink = response.data.kodik_link

      if (kodikLink) {
        // Добавляем параметры в URL
        const url = new URL(kodikLink, window.location.origin)
        url.searchParams.set('season', selectedSeason.value.toString())
        url.searchParams.set('episode', selectedEpisode.value.toString())

        // Если выбран конкретный перевод (не "0" - по умолчанию)
        if (selectedTranslationId.value && selectedTranslationId.value !== '0') {
          url.searchParams.set('only_translations', selectedTranslationId.value)
          // auto_translation=true заставляет плеер автоматически выбирать озвучку из only_translations
          // Это сохраняет выбор озвучки при переключении серий
          url.searchParams.set('auto_translation', 'true')
        }

        playerLink.value = url.toString()
        useKodikPlayer.value = true
        console.log('Используем Kodik плеер:', playerLink.value)
      } else {
        error.value = 'Видео для этого аниме недоступно. Попробуйте другое аниме.'
      }
    } else {
      error.value = 'Не удалось определить аниме'
    }
  } catch (err: any) {
    console.error('Ошибка загрузки видео:', err)
    
    if (err.response?.status === 404) {
      error.value = 'Видео не найдено в Kodik API. Это аниме может быть недоступно.'
    } else if (err.response?.status === 503) {
      error.value = 'Kodik API временно недоступен. Попробуйте позже.'
    } else {
      error.value = 'Ошибка загрузки видео. Попробуйте позже.'
    }
  } finally {
    loading.value = false
  }
}

// Modified changeEpisode and changeSeason
const changeEpisode = async () => {
  // Перезагружаем плеер с новым URL
  await loadVideo()
  autoplay.value = true
  saveWatchProgress()
}
  
const changeSeason = async () => {
  selectedEpisode.value = 1
  // Перезагружаем плеер с новым URL
  await loadVideo()
  autoplay.value = true
}

const changeTranslation = async () => {
  // Сохраняем выбранную озвучку
  saveSelectedTranslation()
  // Перезагружаем плеер с новым переводом
  await loadVideo()
}

const selectEpisode = (episode: number) => {
  selectedEpisode.value = episode
  changeEpisode()
}

// Progress
const loadWatchProgress = () => {
  const animeId = props.anime?.id
  if (!animeId) return
  
  const key = `anime_progress_${animeId}`
  const saved = localStorage.getItem(key)
  if (saved) {
    try {
      watchProgress.value = JSON.parse(saved)
    } catch (e) {
      console.warn('Ошибка загрузки прогресса:', e)
    }
  }
}

const saveWatchProgress = () => {
  const key = `anime_progress_${props.anime?.id}`
  localStorage.setItem(key, JSON.stringify(watchProgress.value))
}

// Сохранение и загрузка выбранной озвучки
const saveSelectedTranslation = () => {
  const animeId = props.anime?.id
  if (!animeId || !selectedTranslationId.value) return
  
  const key = `anime_translation_${animeId}`
  localStorage.setItem(key, selectedTranslationId.value)
}

const loadSelectedTranslation = () => {
  const animeId = props.anime?.id
  if (!animeId) return null
  
  const key = `anime_translation_${animeId}`
  return localStorage.getItem(key)
}

const isEpisodeWatched = (episode: number) => {
  return (watchProgress.value[episode] ?? 0) >= 90
}

const onTimeUpdate = (time: number) => {
  currentTime.value = time

  if (duration.value > 0) {
    const progress = (time / duration.value) * 100
    watchProgress.value[selectedEpisode.value] = Math.min(progress, 100)
    
    if (Math.floor(time) % 10 === 0) {
      saveWatchProgress()
    }
  }
}

const onVideoTimeUpdate = (event: Event) => {
  const video = event.target as HTMLVideoElement
  currentTime.value = video.currentTime

  if (video.duration > 0) {
    const progress = (video.currentTime / video.duration) * 100
    watchProgress.value[selectedEpisode.value] = Math.min(progress, 100)
    
    if (Math.floor(video.currentTime) % 10 === 0) {
      saveWatchProgress()
    }
  }
}

const onDurationUpdate = (dur: number) => {
  duration.value = dur
}

// Player events
const onPlayerReady = () => {
  console.log('Kodik плеер готов')
  loading.value = false
}

const onPlay = () => {
  isPlaying.value = true
}

const onPause = () => {
  isPlaying.value = false
}

const onVideoEnded = () => {
  isPlaying.value = false
  watchProgress.value[selectedEpisode.value] = 100
  saveWatchProgress()
  
  // Автоматически переключаем на следующую серию
  if (selectedEpisode.value < episodesCount.value) {
    selectEpisode(selectedEpisode.value + 1)
  }
}

const onCurrentEpisode = (data: any) => {
  console.log('Текущая серия:', data)
  if (data.episode) {
    selectedEpisode.value = data.episode
  }
  if (data.season) {
    selectedSeason.value = data.season
  }
}

const onPlayerError = (err: string) => {
  console.error('Ошибка плеера:', err)
  error.value = err
}

// Video events (для обычного плеера)
const onLoadStart = () => {
  loading.value = true
}

const onLoadedData = () => {
  loading.value = false
  error.value = ''
}

const onVideoError = (event: Event) => {
  console.warn('Ошибка воспроизведения видео:', event)
  error.value = 'Видео недоступно. Попробуйте другой перевод.'
  loading.value = false
}

// Player controls
const togglePlay = () => {
  if (kodikPlayer.value) {
    if (isPlaying.value) {
      kodikPlayer.value.pause()
    } else {
      kodikPlayer.value.play()
    }
  } else if (videoPlayer.value) {
    if (videoPlayer.value.paused) {
      videoPlayer.value.play()
    } else {
      videoPlayer.value.pause()
    }
  }
}

const seekForward = () => {
  if (kodikPlayer.value) {
    kodikPlayer.value.seek(currentTime.value + 10)
  } else if (videoPlayer.value) {
    videoPlayer.value.currentTime = Math.min(videoPlayer.value.duration, currentTime.value + 10)
  }
}

const seekBackward = () => {
  if (kodikPlayer.value) {
    kodikPlayer.value.seek(Math.max(0, currentTime.value - 10))
  } else if (videoPlayer.value) {
    videoPlayer.value.currentTime = Math.max(0, currentTime.value - 10)
  }
}

const toggleMute = () => {
  if (kodikPlayer.value) {
    if (isMuted.value) {
      kodikPlayer.value.unmute()
      isMuted.value = false
    } else {
      kodikPlayer.value.mute()
      isMuted.value = true
    }
  } else if (videoPlayer.value) {
    videoPlayer.value.muted = !videoPlayer.value.muted
    isMuted.value = videoPlayer.value.muted
  }
}

// Modal control
const close = () => {
  saveWatchProgress()
  
  if (kodikPlayer.value) {
    kodikPlayer.value.pause()
  } else if (videoPlayer.value) {
    videoPlayer.value.pause()
  }
  
  emit('close')
}

const retryLoad = () => {
  loadVideo()
}

// Keyboard
const handleKeyPress = (event: KeyboardEvent) => {
  if (!props.show) return

  switch (event.code) {
    case 'Space':
      event.preventDefault()
      togglePlay()
      break
    case 'ArrowLeft':
      event.preventDefault()
      seekBackward()
      break
    case 'ArrowRight':
      event.preventDefault()
      seekForward()
      break
    case 'KeyM':
      event.preventDefault()
      toggleMute()
      break
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  saveWatchProgress()
})

watch(() => props.anime, (newAnime) => {
  if (newAnime && props.show) {
    loadAnimeData()
  }
})

watch(() => props.show, (show) => {
  if (show) {
    loadAnimeData()
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// Load anime data
const loadAnimeData = async () => {
  if (!props.anime) return

  try {
    // Загружаем данные из props.anime
    episodesCount.value = props.anime.episodes || 1
    seasonsCount.value = props.anime.seasons_count || 1
    
    // Если есть данные о сезонах из Kodik
    if (props.anime.seasons && Object.keys(props.anime.seasons).length > 0) {
      seasonsCount.value = Object.keys(props.anime.seasons).length
      
      // Определяем количество эпизодов в текущем сезоне
      const currentSeasonData = props.anime.seasons[selectedSeason.value]
      if (currentSeasonData && currentSeasonData.episodes) {
        episodesCount.value = Object.keys(currentSeasonData.episodes).length
      }
    }
    
    // Формируем переводы
    if (props.anime.translations && props.anime.translations.length > 0) {
      translations.value = props.anime.translations.map((t: any) => ({
        id: t.id || t.external_id?.toString() || '0',
        name: t.name,
        type: t.type || 'voice'
      }))
    }
    
    if (translations.value.length > 0 && translations.value[0] != undefined) {
      // Пробуем загрузить сохраненную озвучку из localStorage
      const savedTranslation = loadSelectedTranslation()
      if (savedTranslation && translations.value.some(t => t.id === savedTranslation)) {
        selectedTranslationId.value = savedTranslation
      } else {
        selectedTranslationId.value = translations.value[0].id
      }
    }

    loadWatchProgress()
    selectedEpisode.value = props.initialEpisode
    selectedSeason.value = props.initialSeason
    await loadVideo()
  } catch (err: any) {
    console.error('Ошибка загрузки данных аниме:', err)
    error.value = 'Ошибка загрузки данных'
  }
}
</script>

<style scoped>
.anime-player-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(4px);
}

.player-container {
  position: relative;
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  max-height: 800px;
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.anime-info {
  flex: 1;
}

.anime-title {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.episode-info {
  color: #a0a0a0;
  font-size: 0.875rem;
}

.close-btn {
  background: none;
  border: none;
  color: #a0a0a0;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.25rem;
  transition: all 0.2s;
}

.close-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.video-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading-state,
.error-state,
.no-video-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.player-controls {
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 1.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-label {
  color: #a0a0a0;
  font-size: 0.875rem;
  white-space: nowrap;
}

.season-select,
.episode-select,
.translation-select {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  color: white;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
  min-width: 120px;
}

.season-select:focus,
.episode-select:focus,
.translation-select:focus {
  border-color: #3b82f6;
}

.season-select option,
.episode-select option,
.translation-select option {
  background: #1a1a1a;
  color: white;
}

.player-actions {
  margin-left: auto;
}

.control-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  color: white;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.progress-bar {
  width: 100px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  transition: width 0.3s ease;
}

.progress-text {
  color: #a0a0a0;
  font-size: 0.75rem;
  min-width: 35px;
}

.episodes-list {
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.episodes-list h3 {
  color: white;
  font-size: 1rem;
  margin: 0 0 0.75rem 0;
}

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
  gap: 0.5rem;
  max-height: 150px;
  overflow-y: auto;
}

.episode-btn {
  aspect-ratio: 1;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.episode-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.episode-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
}

.episode-btn.watched {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.4);
}

.retry-btn {
  background: #3b82f6;
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
}

@media (max-width: 768px) {
  .player-container {
    width: 95vw;
    height: 85vh;
  }

  .player-header {
    padding: 0.75rem 1rem;
  }

  .anime-title {
    font-size: 1.125rem;
  }

  .player-controls {
    padding: 0.75rem 1rem;
    gap: 1rem;
    flex-direction: column;
    align-items: stretch;
  }

  .control-section {
    justify-content: space-between;
  }

  .episodes-list {
    padding: 0.75rem 1rem;
  }

  .episodes-grid {
    grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
    max-height: 120px;
  }
}

@media (max-width: 480px) {
  .player-container {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .episodes-grid {
    grid-template-columns: repeat(auto-fill, minmax(45px, 1fr));
  }
}
</style>