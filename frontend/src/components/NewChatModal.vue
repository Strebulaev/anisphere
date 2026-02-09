<template>
  <div class="anime-player-modal" v-if="show">
    <div class="modal-backdrop" @click="close"></div>
    <div class="player-container">
      <!-- Заголовок модального окна -->
      <div class="player-header">
        <div class="anime-info">
          <h2 class="anime-title">{{ anime?.title_ru || anime?.title_en }}</h2>
          <div class="episode-info">
            <span v-if="currentEpisode">Серия {{ currentEpisode }}</span>
            <span v-if="selectedTranslation"> • {{ selectedTranslation.name }}</span>
            <span v-if="videoQuality"> • {{ videoQuality }}p</span>
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
          <p>{{ error }}</p>
          <button @click="retryLoad" class="btn btn-primary">Попробовать снова</button>
        </div>

        <video
          v-else-if="videoUrl"
          ref="videoPlayer"
          class="video-player"
          :src="videoUrl"
          controls
          preload="metadata"
          @loadstart="onLoadStart"
          @loadeddata="onLoadedData"
          @error="onVideoError"
          @timeupdate="onTimeUpdate"
        >
          Ваш браузер не поддерживает воспроизведение видео.
        </video>
        
        <div v-else class="no-video-state">
          <p>Видео недоступно</p>
        </div>
      </div>

      <!-- Панель управления -->
      <div class="player-controls" v-if="!loading && !error">
        <!-- Выбор серии -->
        <div class="control-section">
          <label class="control-label">Серия:</label>
          <select 
            v-model="currentEpisode" 
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
            v-model="videoQuality" 
            @change="changeQuality"
            class="quality-select"
          >
            <option value="720">720p (HD)</option>
            <option value="480">480p</option>
            <option value="360">360p</option>
          </select>
        </div>

        <!-- Прогресс просмотра -->
        <div class="control-section" v-if="watchProgress[currentEpisode]">
          <label class="control-label">Прогресс:</label>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: watchProgress[currentEpisode] + '%' }"
            ></div>
          </div>
            <span class="progress-text">{{ Math.round(watchProgress[currentEpisode] || 0) }}%</span>
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
            :class="['episode-btn', { active: episode === currentEpisode, watched: isEpisodeWatched(episode) }]"
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

// Состояние
const loading = ref(false)
const error = ref<string | null>(null)
const videoUrl = ref<string | null>(null)
const videoQuality = ref('720')
const currentEpisode = ref(props.initialEpisode)
const selectedTranslationId = ref('0')
const translations = ref<Translation[]>([])
const selectedTranslation = computed(() => 
  translations.value.find(t => t.id === selectedTranslationId.value)
)
const seriesCount = ref(0)
const watchProgress = ref<Record<number, number>>({})
const currentTime = ref(0)

// Refs
const videoPlayer = ref<HTMLVideoElement | null>(null)

// Вычисляемые свойства
const availableEpisodes = computed(() => 
  Array.from({ length: seriesCount.value || 1 }, (_, i) => i + 1)
)

const isDemoContent = computed(() => {
  return translations.value.some(t => t.name.includes('AniDUB') || t.name.includes('2x2'))
})

// Загрузка видео
const loadVideo = async () => {
  if (!props.anime) return

  loading.value = true
  error.value = null
  videoUrl.value = null

  try {
    const params = {
      episode: currentEpisode.value,
      translation_id: selectedTranslationId.value,
      quality: videoQuality.value
    }

    const response = await apiClient.get(`/anime/anime/${props.anime.id}/get_video_link/`, { params })
    
    if (response.data.video_url) {
      videoUrl.value = response.data.video_url
      
      // Устанавливаем таймстемп, если он указан
      if (props.anime.last_watched_time) {
        currentTime.value = props.anime.last_watched_time
      }
    } else {
      console.error('Не удалось получить ссылку на видео')
    }
  } catch (err: any) {
    console.error('Ошибка загрузки видео:', err)
    
    // Детальная обработка ошибок
    if (err.response?.status === 404) {
      error.value = 'Видео не найдено для данного перевода'
    } else if (err.response?.status === 503) {
      error.value = 'Сервис временно недоступен'
    } else if (err.code === 'ERR_NETWORK') {
      error.value = 'Ошибка сети. Проверьте подключение'
    } else {
      error.value = err.response?.data?.error || 'Не удалось загрузить видео'
    }
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
  currentEpisode.value = episode
}

// Прогресс просмотра
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

  const currentTime = videoPlayer.value.currentTime
  const duration = videoPlayer.value.duration

  if (duration > 0) {
    const progress = (currentTime / duration) * 100
    watchProgress.value[currentEpisode.value] = Math.min(progress, 100)
    
    // Сохраняем прогресс каждые 10 секунд
    if (Math.floor(currentTime) % 10 === 0) {
      saveWatchProgress()
    }
  }
}

// Обработчики событий видео
const onLoadStart = () => {
  console.log('Начало загрузки видео')
}

const onLoadedData = () => {
  console.log('Видео загружено')
}

// Updated onVideoError function
const onVideoError = (event: Event) => {
  console.error('Ошибка воспроизведения видео:', event)
  
  error.value = 'Видео недоступно. Попробуйте другой перевод или качество.'
}

// Управление модальным окном
const close = () => {
  // Сохраняем прогресс перед закрытием
  saveWatchProgress()
  emit('close')
}

const retryLoad = () => {
  loadVideo()
}

// Обработка клавиатуры
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
      if (currentEpisode.value > 1) {
        currentEpisode.value--
        changeEpisode()
      }
      break
    case 'ArrowRight':
      event.preventDefault()
      if (currentEpisode.value < seriesCount.value) {
        currentEpisode.value++
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
  
  // Добавляем обработчик клавиатуры
  document.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  // Удаляем обработчик клавиатуры
  document.removeEventListener('keydown', handleKeyPress)
  
  // Сохраняем прогресс
  saveWatchProgress()
})

// Следим за изменением аниме
watch(() => props.anime, (newAnime) => {
  if (newAnime && props.show) {
    loadAnimeData()
  }
})

// Следим за показом модального окна
watch(() => props.show, (show) => {
  if (show) {
    loadAnimeData()
    // Блокируем скролл страницы
    document.body.style.overflow = 'hidden'
  } else {
    // Возвращаем скролл
    document.body.style.overflow = ''
  }
})

// Загрузка данных об аниме
const loadAnimeData = async () => {
  if (!props.anime) return

  try {
    // Получаем количество серий
    const seriesResponse = await apiClient.get(`/anime/anime/${props.anime.id}/get_series_count/`)
    const seriesCountData = seriesResponse.data.series_count || props.anime.episodes || 1
    seriesCount.value = typeof seriesCountData === 'number' ? seriesCountData : parseInt(seriesCountData.toString()) || 1

    // Получаем переводы
    try {
      const translationsResponse = await apiClient.get(`/anime/anime/${props.anime.id}/get_translations/`)
      translations.value = translationsResponse.data.translations || []
      
      if (translations.value.length > 0 && translations.value[0]) {
          selectedTranslationId.value = translations.value[0].id
      }
    } catch (err) {
      console.warn('Не удалось загрузить переводы:', err)
      const episodesValue = props.anime.episodes?.toString() || '12'
      translations.value = [
        {
          id: '609',
          name: 'AniDUB (Демо)',
          type: 'Озвучка',
          episodes: episodesValue
        }
      ]
      selectedTranslationId.value = '609'
    }

    // Загружаем прогресс просмотра из localStorage
    loadWatchProgress()

    // Загружаем первую серию
    await loadVideo()
  } catch (err: any) {
    console.error('Ошибка загрузки данных аниме:', err)
    
    // Устанавливаем минимальные данные для демонстрации
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
    
    // Загружаем демо-видео
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
</style>