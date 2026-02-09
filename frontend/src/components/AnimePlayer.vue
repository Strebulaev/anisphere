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
            <span v-if="selectedTranslation"> • {{ selectedTranslation.name }}</span>
            <span v-if="selectedQuality"> • {{ selectedQuality }}p</span>
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

        <video
          v-else-if="videoUrl"
          ref="videoPlayer"
          class="video-player"
          :src="videoUrl"
          controls
          preload="auto"
          @loadstart="onLoadStart"
          @loadeddata="onLoadedData"
          @timeupdate="onTimeUpdate"
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
              {{ translation.name }} ({{ translation.type }})
            </option>
          </select>
          <span v-if="translations.length === 0" class="demo-notice">
            Демо-переводы
          </span>
        </div>

        <!-- Выбор качества -->
        <div class="control-section">
          <label class="control-label">Качество:</label>
          <select 
            v-model="selectedQuality" 
            @change="changeQuality"
            class="quality-select"
          >
            <option value="720">720p (HD)</option>
            <option value="480">480p</option>
            <option value="360">360p</option>
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
      </div>

      <!-- Список серий -->
      <div class="episodes-list" v-if="seriesCount > 1">
        <h3>Все серии</h3>
        <div class="episodes-grid">
          <button
            v-for="episode in seriesCount"
            :key="episode"
            @click="selectEpisode(episode)"
            :class="['episode-btn', { active: episode === selectedEpisode, watched: isEpisodeWatched(episode) }]"
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
import axios from 'axios'

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
}

const props = withDefaults(defineProps<Props>(), {
  initialEpisode: 1
})

const emit = defineEmits<{
  close: []
}>()

// Data
const videoUrl = ref<string>('')
const loading = ref(true)
const error = ref('')
const selectedEpisode = ref(1)
const selectedTranslationId = ref('')
const selectedQuality = ref('720')
const seriesCount = ref(1)
const translations = ref<Translation[]>([])
const videoPlayer = ref<HTMLVideoElement | null>(null)
const currentTime = ref(0)
const duration = ref(0)
const watchProgress = ref<{[key: number]: number}>({})

// Real video indicator
const isRealVideo = ref(false)

// Reactive data
const isPlaying = ref<boolean>(false)
const volume = ref<number>(1)

// Computed
const selectedTranslation = computed(() => 
  translations.value.find(t => t.id === selectedTranslationId.value)
)
const isDemoContent = computed(() => {
  return translations.value.some(t => t.name.includes('AniDUB') || t.name.includes('2x2'))
})
const availableEpisodes = computed(() => 
  Array.from({ length: seriesCount.value || 1 }, (_, i) => i + 1)
)

// Load video
const loadVideo = async () => {
  loading.value = true
  error.value = ''
  videoUrl.value = ''
  isRealVideo.value = false

  try {
    const params = {
      episode: selectedEpisode.value,
      translation_id: selectedTranslationId.value,
      quality: selectedQuality.value
    }

    console.log('=== Загружаем видео ===')
    console.log('Params:', params)
    console.log('Anime ID:', props.anime?.id)

    const token = localStorage.getItem('access_token')
    const response = await axios.get(
      `http://localhost:8000/api/anime/anime/${props.anime.id}/get_video_link/`,
      {
        params,
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      }
    )
    
    console.log('=== Ответ API ===')
    console.log('Response:', response.data)
    
    if (response.data.video_url) {
      videoUrl.value = response.data.video_url
      isRealVideo.value = response.data.source === 'kodik'
      
      console.log('=== Устанавливаем видео URL ===')
      console.log('Video URL:', videoUrl.value)
      console.log('Is real video:', isRealVideo.value)
    } else {
      console.warn('API не вернул video_url')
    }
  } catch (err: any) {
    console.error('Ошибка загрузки видео:', err)
    console.error('Response:', err.response?.data)
    error.value = 'Ошибка загрузки видео'
  } finally {
    loading.value = false
  }
}

const changeEpisode = async () => {
  await loadVideo()
  saveWatchProgress()
}

const changeTranslation = async () => {
  await loadVideo()
}

const changeQuality = async () => {
  await loadVideo()
}

const selectEpisode = (episode: number) => {
  selectedEpisode.value = episode
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

const isEpisodeWatched = (episode: number) => {
  return (watchProgress.value[episode] || 0) >= 90
}

const onTimeUpdate = () => {
  if (!videoPlayer.value || !props.anime) return

  currentTime.value = videoPlayer.value.currentTime
  duration.value = videoPlayer.value.duration

  if (duration.value > 0) {
    const progress = (currentTime.value / duration.value) * 100
    watchProgress.value[selectedEpisode.value] = Math.min(progress, 100)
    
    if (Math.floor(currentTime.value) % 10 === 0) {
      saveWatchProgress()
    }
  }
}

// Video events
const onLoadStart = () => {
  console.log('Начало загрузки видео')
  loading.value = true
}

const onLoadedData = () => {
  console.log('Видео загружено')
  loading.value = false
  error.value = ''
}

const onVideoError = (event: Event) => {
  console.warn('Ошибка воспроизведения видео:', event)
  console.log('Video URL:', videoUrl.value)
  
  // Если это реальное видео и произошла ошибка, показываем сообщение
  if (isRealVideo.value) {
    error.value = 'Видео недоступно. Попробуйте другой перевод или качество.'
  }
  
  loading.value = false
}

// Modal control
const close = () => {
  saveWatchProgress()
  emit('close')
}

const retryLoad = () => {
  loadVideo()
}

// Keyboard
const handleKeyPress = (event: KeyboardEvent) => {
  if (!videoPlayer.value) return

  switch (event.code) {
    case 'Space':
      event.preventDefault()
      if (videoPlayer.value.paused) {
        videoPlayer.value.play()
      } else {
        videoPlayer.value.pause()
      }
      break
    case 'ArrowLeft':
      event.preventDefault()
      if (selectedEpisode.value > 1) {
        selectedEpisode.value--
        changeEpisode()
      }
      break
    case 'ArrowRight':
      event.preventDefault()
      if (selectedEpisode.value < seriesCount.value) {
        selectedEpisode.value++
        changeEpisode()
      }
      break
  }
}

// Lifecycle
onMounted(() => {
  if (props.show) {
    loadAnimeData()
  }
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
    // Используем данные из props.anime вместо API запросов
    const episodesValue = props.anime.episodes?.toString() || '12'
    seriesCount.value = props.anime.episodes || 12
    
    // Создаем демо-переводы
    translations.value = [
      {
        id: '609',
        name: 'AniDUB (Демо)',
        type: 'Озвучка',
        episodes: episodesValue
      },
      {
        id: '735', 
        name: '2x2 (Демо)',
        type: 'Озвучка',
        episodes: episodesValue
      },
      {
        id: '869',
        name: 'Субтитры (Демо)',
        type: 'Субтитры', 
        episodes: episodesValue
      }
    ]
    
    // Выбираем первый перевод по умолчанию
    if (translations.value.length > 0 && translations.value[0] != null) {
      selectedTranslationId.value = translations.value[0].id
    }

    loadWatchProgress()
    selectedEpisode.value = props.initialEpisode
    await loadVideo()
  } catch (err: any) {
    console.error('Ошибка загрузки данных аниме:', err)
    const episodesValue = props.anime.episodes?.toString() || '12'
    seriesCount.value = props.anime.episodes || 12
    translations.value = [
      {
        id: 'demo',
        name: 'Демо озвучка',
        type: 'Озвучка',
        episodes: episodesValue
      }
    ]
    selectedTranslationId.value = 'demo'
    await loadVideo()
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

/* Заголовок */
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

/* Видео контейнер */
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

/* Состояния загрузки */
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

/* Панель управления */
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

.episode-select,
.translation-select,
.quality-select {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  color: white;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
}

.episode-select:focus,
.translation-select:focus,
.quality-select:focus {
  border-color: #3b82f6;
}

.episode-select option,
.translation-select option,
.quality-select option {
  background: #1a1a1a;
  color: white;
}

.demo-notice {
  color: #fbbf24;
  font-size: 0.75rem;
  font-style: italic;
}

/* Уведомление о демо-контенте */
.demo-notification {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  color: #fbbf24;
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1rem;
}

/* Реальное видео уведомление */
.real-video-notification {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  color: #22c55e;
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1rem;
}

/* Прогресс просмотра */
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

/* Список серий */
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
  max-height: 120px;
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

/* Адаптивность */
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
    max-height: 100px;
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

/* Уведомления о типе контента */
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
</style>