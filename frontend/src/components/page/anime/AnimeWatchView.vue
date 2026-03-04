<template>
  <div class="anime-watch-page">
    <div class="watch-container">
      <!-- Левая колонка: плеер -->
      <div class="left-column">
        <!-- Плеер -->
        <div class="player-wrapper">
          <div class="player-container" ref="playerContainer">
            <KodikPlayer
              v-if="kodikLink && !useCustomPlayer"
              :link="kodikLink"
              :autoplay="autoplay"
              :season="currentSeason"
              :episode="currentEpisode"
              ref="kodikPlayer"
              @ready="onPlayerReady"
              @play="onPlay"
              @pause="onPause"
              @timeUpdate="onTimeUpdate"
              @durationUpdate="onDurationUpdate"
              @currentEpisode="onCurrentEpisode"
              @videoStarted="onVideoStarted"
              @videoEnded="onVideoEnded"
              @skipButton="onSkipButton"
              @error="onPlayerError"
            />
            <CustomVideoPlayer
              v-else-if="useCustomPlayer && customVideoUrl"
              :video-url="customVideoUrl"
              :poster="anime?.poster_url"
              :autoplay="autoplay"
              @ready="onPlayerReady"
              @play="onPlay"
              @pause="onPause"
              @timeUpdate="onTimeUpdate"
              @durationUpdate="onDurationUpdate"
              @videoEnded="onVideoEnded"
              @error="onPlayerError"
            />
            <div v-else-if="loading" class="player-placeholder loading">
              <div class="spinner"></div>
              <p>Загрузка плеера...</p>
            </div>
            <div v-else-if="error" class="player-placeholder error">
              <div class="error-icon">⚠️</div>
              <p>{{ error }}</p>
              <button @click="retryLoad" class="btn btn-primary retry-btn">Попробовать снова</button>
            </div>
            <div v-else class="player-placeholder">
              <div class="no-video-icon">🎬</div>
              <p>Видео недоступно</p>
            </div>
          </div>
        </div>

        <!-- Информация под плеером -->
        <div class="anime-info-under">
          <div class="anime-header">
            <h1 class="anime-title">{{ anime?.title_ru || anime?.title_en }}</h1>
            <div class="anime-badges">
              <span v-if="anime?.year" class="badge year-badge">{{ anime.year }}</span>
              <span v-if="anime?.kind" class="badge kind-badge">{{ getKindText(anime.kind) }}</span>
              <span v-if="anime?.episodes" class="badge episodes-badge">{{ anime.episodes }} эп.</span>
              <span class="badge status-badge" :class="anime?.status">
                {{ getStatusText(anime?.status) }}
              </span>
            </div>
          </div>

          <div class="anime-rating" v-if="anime?.score">
            <div class="rating-stars">
              <svg v-for="i in 5" :key="i" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <polygon :points="getStarPoints(i, anime.score)"/>
              </svg>
            </div>
            <span class="rating-value">{{ anime.score.toFixed(1) }}</span>
          </div>

          <p class="anime-description">
            {{ anime?.description || 'Описание отсутствует' }}
          </p>
        </div>

        <!-- Озвучки -->
        <div class="translations-section">
          <div class="section-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              Озвучки
            </h3>
            <button @click="showAddDubModal = true" class="btn btn-outline add-dub-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Добавить озвучку
            </button>
          </div>

          <div v-if="loadingTranslations" class="loading-translations">
            <div class="spinner-small"></div>
            <p>Загрузка озвучек...</p>
          </div>
          <div v-else-if="translations.length > 0" class="translations-list">
            <div
              v-for="translation in translations"
              :key="translation.id"
              class="translation-item"
              :class="{ 
                active: selectedTranslationId === translation.id,
                'custom-dub': translation.is_custom
              }"
              @click="selectTranslation(translation)"
            >
              <div class="translation-left">
                <div class="translation-avatar">
                  <img v-if="getTranslationAvatar(translation)" :src="getTranslationAvatar(translation) || undefined" :alt="translation.name">
                  <span v-else>{{ getTranslationInitials(translation.name) }}</span>
                </div>
                <div class="translation-info">
                  <span class="translation-name">{{ translation.name }}</span>
                  <span class="translation-meta">
                    <span class="translation-type">{{ getTranslationType(translation.type) }}</span>
                    <span v-if="translation.quality" class="translation-quality">{{ translation.quality }}</span>
                    <span v-if="translation.is_custom" class="custom-badge">Пользовательская</span>
                  </span>
                </div>
              </div>
              <div class="translation-right">
                <div v-if="translation.episodes_done !== undefined" class="translation-progress">
                  <span>{{ translation.episodes_done }}</span>
                  <span v-if="translation.total_episodes">/ {{ translation.total_episodes }}</span>
                </div>
                <svg v-if="selectedTranslationId === translation.id" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="check-icon">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
            </div>
          </div>
          <div v-else class="no-translations">
            <div class="no-translations-icon">🎤</div>
            <p>Озвучки недоступны</p>
            <button @click="showAddDubModal = true" class="btn btn-primary">
              Добавить первую озвучку
            </button>
          </div>
        </div>
      </div>

      <!-- Правая колонка: постер, прогресс и действия -->
      <div class="right-column">
        <!-- Постер -->
        <div class="poster-side" ref="posterSide">
          <img v-if="anime?.poster_url" :src="anime.poster_url" :alt="anime.title_ru" class="poster-image" @load="syncPosterHeight">
          <div v-else class="poster-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <path d="M21 15l-5-5L5 21"/>
            </svg>
          </div>
        </div>

        <!-- Прогресс просмотра -->
        <div class="progress-card">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Прогресс просмотра
          </h3>
          <div class="progress-info">
            <span class="progress-text">{{ watchedCount }} из {{ anime?.episodes || 1 }} просмотрено</span>
            <span class="progress-percent">{{ progressPercent }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <p class="progress-hint">
            <span v-if="endingStartTime !== null">
              ✅ Серия засчитана — эндинг обнаружен
            </span>
            <span v-else>
              Серия засчитывается при начале эндинга или 85% времени
            </span>
          </p>
        </div>

        <!-- Жанры -->
        <div v-if="anime?.genres && anime.genres.length > 0" class="genres-card">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            Жанры
          </h3>
          <div class="genres-list">
            <span v-for="genre in anime.genres" :key="genre.id" class="genre-tag">{{ genre.name }}</span>
          </div>
        </div>

        <!-- Действия -->
        <div class="actions-card">
          <button @click="addToFavorites" class="action-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            В избранное
          </button>
          <button @click="shareAnime" class="action-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="18" cy="5" r="3"/>
              <circle cx="6" cy="12" r="3"/>
              <circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
            Поделиться
          </button>
        </div>

        <!-- Информация о текущей серии -->
        <div v-if="currentEpisodeData" class="current-episode-card">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="15" rx="2" ry="2"/>
              <polyline points="17 2 12 7 7 2"/>
            </svg>
            Текущая серия
          </h3>
          <div class="episode-info">
            <span class="episode-number">Серия {{ currentEpisode }}</span>
            <span v-if="currentEpisodeData.title" class="episode-title">{{ currentEpisodeData.title }}</span>
          </div>
          <div class="episode-progress">
            <span class="episode-time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
            <div class="episode-progress-bar">
              <div class="episode-progress-fill" :style="{ width: episodeProgress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления озвучки -->
    <AddCustomDubModal
      :show="showAddDubModal"
      :anime-id="anime?.id"
      :anime-title="anime?.title_ru || anime?.title_en"
      @close="showAddDubModal = false"
      @dub-added="onDubAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'
import KodikPlayer from '@/components/Players/KodikPlayer.vue'
import CustomVideoPlayer from '@/components/Players/CustomVideoPlayer.vue'
import AddCustomDubModal from '@/components/modal/anime/AddCustomDubModal.vue'
import { getTranslationAvatarUrl } from '@/utils/translationAvatars'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const anime = ref<any>(null)
const kodikLink = ref('')
const customVideoUrl = ref('')
const loading = ref(true)
const loadingTranslations = ref(false)
const error = ref('')
const autoplay = ref(false)
const useCustomPlayer = ref(false)

const currentSeason = ref(1)
const currentEpisode = ref(1)
const selectedTranslation = ref<any>(null)
const translations = ref<any[]>([])
const showAddDubModal = ref(false)

// Сохранение и загрузка выбранной озвучки из localStorage
const saveSelectedTranslation = () => {
  const animeId = anime.value?.id
  if (!animeId || !selectedTranslation.value) return
  
  const key = `anime_translation_${animeId}`
  localStorage.setItem(key, JSON.stringify({
    id: selectedTranslation.value.id,
    is_custom: selectedTranslation.value.is_custom,
    name: selectedTranslation.value.name
  }))
}

const loadSelectedTranslation = () => {
  const animeId = anime.value?.id
  if (!animeId || translations.value.length === 0) return null
  
  const key = `anime_translation_${animeId}`
  const saved = localStorage.getItem(key)
  if (!saved) return null
  
  try {
    const savedData = JSON.parse(saved)
    // Ищем озвучку с таким же ID
    const found = translations.value.find(t => t.id === savedData.id)
    if (found) {
      console.log('[Translation] Восстановлена сохраненная озвучка:', found.name)
      return found
    }
  } catch (e) {
    console.warn('Ошибка загрузки сохраненной озвучки:', e)
  }
  return null
}

const currentTime = ref(0)
const duration = ref(0)
const isPlaying = ref(false)

// Refs для DOM элементов
const playerContainer = ref<HTMLElement | null>(null)
const posterSide = ref<HTMLElement | null>(null)
const kodikPlayer = ref<InstanceType<typeof KodikPlayer> | null>(null)

// Прогресс просмотра - храним прогресс каждой серии в процентах
const watchProgress = ref<Record<number, number>>({})
const isInLibrary = ref(false)
const libraryItemId = ref<number | null>(null)

// Данные текущей серии
const currentEpisodeData = ref<any>(null)

const availableEpisodes = computed(() => {
  if (!anime.value?.episodes) return []
  return Array.from({ length: anime.value.episodes }, (_, i) => i + 1)
})

const watchedCount = computed(() => {
  // Считаем только те серии, где прогресс >= 95%
  return Object.values(watchProgress.value).filter(p => p >= 50).length
})

const progressPercent = computed(() => {
  if (!anime.value?.episodes) return 0
  return Math.round((watchedCount.value / anime.value.episodes) * 100)
})

const episodeProgress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const isEpisodeWatched = (episode: number) => {
  return (watchProgress.value[episode] ?? 0) >= 95
}

const selectedTranslationId = computed(() => {
  return selectedTranslation.value?.id?.toString() || '0'
})

const getKindText = (kind: string) => {
  const kinds: Record<string, string> = {
    'tv': 'ТВ',
    'movie': 'Фильм',
    'ova': 'OVA',
    'ona': 'ONA',
    'special': 'Спецвыпуск',
    'music': 'Музыка'
  }
  return kinds[kind] || kind
}

const getStatusText = (status: string) => {
  const statuses: Record<string, string> = {
    'ongoing': 'Онгоинг',
    'finished': 'Завершено',
    'announced': 'Анонс',
    'canceled': 'Отменено'
  }
  return statuses[status] || status
}

const getTranslationType = (type: string) => {
  const types: Record<string, string> = {
    'voice': 'Озвучка',
    'subtitles': 'Субтитры',
    'raw': 'Оригинал'
  }
  return types[type] || type
}

const getTranslationInitials = (name: string) => {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

/**
 * Получает URL аватарки для озвучки
 * @param translation - объект озвучки
 * @returns URL аватарки или undefined
 */
const getTranslationAvatar = (translation: any): string | undefined => {
  // Сначала проверяем логотип из API
  if (translation.logo) {
    return translation.logo
  }

  // Если логотипа нет, пробуем найти аватарку в assets
  return getTranslationAvatarUrl(translation.name)
}

const getStarPoints = (index: number, rating: number) => {
  const fullStars = Math.floor(rating / 2)
  const hasHalfStar = (rating % 2) >= 1
  
  if (index <= fullStars) {
    return '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'
  } else if (index === fullStars + 1 && hasHalfStar) {
    return '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'
  }
  return '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'
}

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

const loadAnime = async () => {
  try {
    loading.value = true
    error.value = ''

    const animeId = route.params.id
    const response = await apiClient.get(`/anime/${animeId}/`)
    anime.value = response.data

    // Читаем номер серии из query-параметра ?episode=N
    const episodeFromQuery = route.query.episode
    if (episodeFromQuery) {
      const ep = parseInt(episodeFromQuery as string, 10)
      if (!isNaN(ep) && ep >= 1) {
        currentEpisode.value = ep
        autoplay.value = true
        console.log(`[Watch] Стартуем с серии ${ep} из URL`)
      }
    }

    // Проверяем, есть ли аниме в библиотеке
    await checkLibraryStatus()

    // Загружаем озвучки из Kodik API
    await loadTranslations()

    // Загружаем ссылку на Kodik плеер
    await loadKodikPlayer()

    // Загружаем прогресс
    loadWatchProgress()
  } catch (err: any) {
    console.error('Ошибка загрузки аниме:', err)
    error.value = 'Не удалось загрузить аниме'
  } finally {
    loading.value = false
  }
}

const checkLibraryStatus = async () => {
  if (!authStore.isAuthenticated) return
  try {
    // GET /users/library/ — DRF ViewSet возвращает прямой список
    const response = await apiClient.get('/users/library/')
    // Поддерживаем и pagination (results), и прямой список
    const items: any[] = response.data.results ?? response.data
    if (!Array.isArray(items)) { return }

    const item = items.find((i: any) => {
      const aid = typeof i.anime === 'object' ? i.anime?.id : i.anime
      return aid === anime.value?.id
    })

    if (item) {
      isInLibrary.value = true
      libraryItemId.value = item.id
      addedToLibrary.value = true // защита от повторного добавления
      // Восстанавливаем текущую серию (если ещё не задана через ?episode=)
      const savedEp = item.current_episode ?? 0
      if (savedEp > 0 && !route.query.episode) {
        currentEpisode.value = savedEp
        console.log('[Library] Серия из библиотеки:', savedEp)
      }
      console.log('[Library] Итем:', item.id, 'current_episode:', savedEp)
    } else {
      isInLibrary.value = false
      libraryItemId.value = null
    }
  } catch (err) {
    isInLibrary.value = false
  }
}

const addToLibraryAutomatically = async () => {
  if (!authStore.isAuthenticated) return
  try {
    // Добавляем/обновляем через UserLibraryCreateSerializer (get_or_create)
    const response = await apiClient.post('/users/library/', {
      anime: anime.value?.id,
      status: 'started',
    })
    isInLibrary.value = true
    libraryItemId.value = response.data.id
    console.log('[Library] Аниме добавлено в библиотеку, id=', response.data.id)
    // Сразу сохраняем текущую серию
    await updateLibraryProgress()
  } catch (err: any) {
    // 409 = уже есть — получаем id через GET
    if (err.response?.status === 409 || err.response?.status === 400) {
      await checkLibraryStatus()
      if (isInLibrary.value) await updateLibraryProgress()
    } else {
      console.error('Ошибка автодобавления в библиотеку:', err)
    }
  }
}

const calculateTotalProgress = () => {
  if (!anime.value?.episodes) return 0
  const totalEpisodes = anime.value.episodes
  const watchedEpisodes = Object.values(watchProgress.value).filter(p => p >= 95).length
  return Math.round((watchedEpisodes / totalEpisodes) * 100)
}

const loadTranslations = async () => {
  if (!anime.value?.id) return

  try {
    loadingTranslations.value = true
    
    // Сначала пробуем получить озвучки из Kodik API
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_translations/`)
    const kodikTranslations = response.data.translations || []
    
    // Получаем пользовательские озвучки
    try {
      const customResponse = await apiClient.get(`/anime/${anime.value.id}/custom_dubs/`)
      const customDubs = customResponse.data.dubs || []
      
      // Объединяем озвучки
      translations.value = [
        ...kodikTranslations.map((t: any) => ({ ...t, is_custom: false })),
        ...customDubs.map((d: any) => ({ ...d, is_custom: true, type: 'voice' }))
      ]
    } catch (err) {
      console.warn('Не удалось загрузить пользовательские озвучки:', err)
      translations.value = kodikTranslations.map((t: any) => ({ ...t, is_custom: false }))
    }

    if (translations.value.length > 0) {
      // Пытаемся восстановить ранее выбранную озвучку
      const savedTranslation = loadSelectedTranslation()
      if (savedTranslation) {
        selectedTranslation.value = savedTranslation
        // Сразу обновляем ссылку плеера на сохранённую озвучку
        if (!savedTranslation.is_custom && savedTranslation.kodik_link) {
          kodikLink.value = savedTranslation.kodik_link
        }
      } else {
        // Если нет сохраненной, выбираем первую
        selectedTranslation.value = translations.value[0]
        // Используем kodik_link первой озвучки
        if (!translations.value[0].is_custom && translations.value[0].kodik_link) {
          kodikLink.value = translations.value[0].kodik_link
        }
      }
    }
  } catch (err) {
    console.warn('Не удалось загрузить озвучки из Kodik:', err)
    translations.value = []
  } finally {
    loadingTranslations.value = false
  }
}

const loadKodikPlayer = async () => {
  if (!anime.value?.id) return

  // Если уже есть ссылка на плеер (от выбранной озвучки), не перезаписываем
  if (kodikLink.value) return

  try {
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_player/`)
    kodikLink.value = response.data.kodik_link

    // Если есть данные о последней серии
    if (response.data.last_episode) {
      currentEpisode.value = 1
    }
  } catch (err: any) {
    console.error('Ошибка загрузки плеера:', err)
    if (err.response?.status === 404) {
      error.value = 'Видео для этого аниме не найдено'
    } else if (err.response?.status === 503) {
      error.value = 'Сервис временно недоступен. Попробуйте позже.'
    } else {
      error.value = 'Не удалось загрузить плеер'
    }
  }
}

const selectTranslation = async (translation: any) => {
  selectedTranslation.value = translation
  // Сохраняем выбранную озвучку в localStorage
  saveSelectedTranslation()
  
  if (translation.is_custom) {
    // Для пользовательской озвучки используем свой плеер
    useCustomPlayer.value = true
    await loadCustomDubVideo(translation.id)
  } else {
    // Для Kodik озвучки используем Kodik плеер
    useCustomPlayer.value = false
    customVideoUrl.value = ''
    
    // Обновляем ссылку плеера с учетом озвучки
    if (translation.kodik_link) {
      kodikLink.value = translation.kodik_link
    }
  }
}

const loadCustomDubVideo = async (dubId: number) => {
  try {
    const response = await apiClient.get(`/anime/${anime.value?.id}/custom_dubs/${dubId}/video/`)
    customVideoUrl.value = response.data.video_url
  } catch (err: any) {
    console.error('Ошибка загрузки видео:', err)
    error.value = 'Не удалось загрузить видео для этой озвучки'
  }
}

const selectEpisode = (episode: number) => {
  currentEpisode.value = episode
  // Для Kodik плеера обновление произойдет через URL
}

const onPlayerReady = () => {
  console.log('Плеер готов')
  loading.value = false

  // Синхронизируем высоту постера после готовности плеера
  setTimeout(() => {
    syncPosterHeight()
  }, 100)
}

const onVideoStarted = () => {
  console.log('Видео началось')
  // Синхронизируем высоту постера после начала видео
  setTimeout(() => {
    syncPosterHeight()
  }, 200)
}

const onPlay = () => {
  isPlaying.value = true
}

const onPause = () => {
  isPlaying.value = false
}

// Время начала опенинга и эндинга (через kodik_player_skip_button)
const openingStartTime  = ref<number | null>(null) // Начало опенинга — триггер добавления в библиотеку
const endingStartTime   = ref<number | null>(null) // Начало эндинга — триггер просмотренной серии
const addedToLibrary    = ref(false) // Защита от дубликата
const episodeMarkedWatched = ref(false)

// Добавляем в библиотеку (один раз)
const triggerLibraryAdd = () => {
  if (addedToLibrary.value || isInLibrary.value) return
  addedToLibrary.value = true
  addToLibraryAutomatically()
}

// Засчитываем серию как просмотренную
const markEpisodeWatched = () => {
  if (episodeMarkedWatched.value) return
  episodeMarkedWatched.value = true
  watchProgress.value[currentEpisode.value] = 100
  saveWatchProgress()
  if (isInLibrary.value && libraryItemId.value) {
    updateLibraryProgress()
  } else {
    // Ещё не в библиотеке — добавляем
    addToLibraryAutomatically()
  }
  console.log(`[Watch] Серия ${currentEpisode.value} засчитана просмотренной`)
}

const onTimeUpdate = (time: number) => {
  currentTime.value = time

  if (duration.value > 0) {
    const progress = (time / duration.value) * 100
    watchProgress.value[currentEpisode.value] = Math.min(progress, 100)

    // Триггер добавления — начало опенинга (кнопка skip_button c соотв. текстом)
    // Фоллбэк: если openigStartTime нет, срабатываем после 30 секунд
    if (!addedToLibrary.value && !isInLibrary.value) {
      if (openingStartTime.value !== null || time >= 30) {
        triggerLibraryAdd()
      }
    }

    // Засчитываем как просмотренную:
    // 1. При начале эндинга (кнопка пропустить эндинг появилась)
    if (endingStartTime.value !== null && !episodeMarkedWatched.value) {
      if (time >= endingStartTime.value) {
        markEpisodeWatched()
      }
    }
    // 2. Фоллбэк — 85% длительности (если кнопка эндинга не появилась)
    if (!episodeMarkedWatched.value && progress >= 85) {
      markEpisodeWatched()
    }

    // Сохраняем прогресс каждые 10 секунд
    if (Math.floor(time) % 10 === 0) {
      saveWatchProgress()
      // Если в библиотеке, обновляем прогресс
      if (isInLibrary.value && libraryItemId.value) {
        updateLibraryProgress()
      }
    }
  }
}

const onDurationUpdate = (dur: number) => {
  duration.value = dur
}

const onCurrentEpisode = (data: any) => {
  console.log('Текущая серия:', data)
  if (data.episode && data.episode !== currentEpisode.value) {
    currentEpisode.value = data.episode
    // Сбрасываем флаги при смене серии
    openingStartTime.value = null
    endingStartTime.value = null
    episodeMarkedWatched.value = false
    addedToLibrary.value = isInLibrary.value // если уже в библиотеке, не добавляем ещё раз
  }
  if (data.season) {
    currentSeason.value = data.season
  }
}

const onVideoEnded = () => {
  isPlaying.value = false
  markEpisodeWatched()

  // Автоматически переключаем на следующую серию
  if (currentEpisode.value < (anime.value?.episodes || 1)) {
    selectEpisode(currentEpisode.value + 1)
    autoplay.value = true
  }
}

// Обработка кнопки "Пропустить" от Kodik (опенинг или эндинг)
const onSkipButton = (data: { title: string }) => {
  const title = data?.title?.toLowerCase() || ''
  const isOpening = title.includes('опенинг') || title.includes('опенин') || title.includes('opening') || title.includes('intro')
  const isEnding  = title.includes('эндинг') || title.includes('титры') || title.includes('ending') || title.includes('outro')

  // Опенинг появился — триггер добавления в библиотеку
  if (isOpening && openingStartTime.value === null && currentTime.value >= 0) {
    openingStartTime.value = currentTime.value
    console.log(`[Watch] Опенинг на ${currentTime.value}с — добавляем в библиотеку`)
    triggerLibraryAdd()
  }

  // Эндинг появился — триггер просмотренной серии
  if (isEnding && endingStartTime.value === null && currentTime.value > 0) {
    endingStartTime.value = currentTime.value
    console.log(`[Watch] Эндинг на ${currentTime.value}с — засчитываем серию`)
    markEpisodeWatched()
  }
}

const updateLibraryProgress = async () => {
  if (!libraryItemId.value) return
  try {
    const episodesWatched = Object.values(watchProgress.value).filter(p => p >= 85).length
    await apiClient.patch(`/users/library/${libraryItemId.value}/`, {
      current_episode: currentEpisode.value,
      episodes_watched: episodesWatched,
      status: 'started',
    })
    console.log(`[Library] Прогресс обновлён: серия ${currentEpisode.value}, просмотрено ${episodesWatched}`)
  } catch (err) {
    console.error('Ошибка обновления прогресса:', err)
  }
}

const onPlayerError = (err: string) => {
  console.error('Ошибка плеера:', err)
  error.value = err
}

const loadWatchProgress = () => {
  const animeId = anime.value?.id
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

const saveWatchProgress = async () => {
  const key = `anime_progress_${anime.value?.id}`
  localStorage.setItem(key, JSON.stringify(watchProgress.value))
  
  // Синхронизация с БД
  if (!anime.value?.id || !authStore.isAuthenticated) return
  
  try {
    // Пробуем получить episode_id из episodes_list
    const episodes = anime.value?.episodes_list || []
    const currentEpData = episodes.find((ep: any) => ep.number === currentEpisode.value)
    
    // Если есть episode_id - сохраняем прогресс просмотра
    if (currentEpData?.id && currentTime.value > 0) {
      await apiClient.post(`/anime/${anime.value.id}/save_watch_progress/`, {
        episode_id: currentEpData.id,
        current_time: Math.floor(currentTime.value),
        duration: duration.value ? Math.floor(duration.value) : undefined
      })
    }
    
    // Обновляем прогресс в библиотеке (это основное)
    if (isInLibrary.value && libraryItemId.value) {
      await updateLibraryProgress()
    }
  } catch (err) {
    console.warn('Ошибка синхронизации прогресса с БД:', err)
  }
}

const retryLoad = () => {
  loadKodikPlayer()
}

const addToFavorites = () => {
  console.log('Добавить в избранное')
}

const shareAnime = () => {
  if (navigator.share) {
    navigator.share({
      title: anime.value?.title_ru || anime.value?.title_en,
      url: window.location.href
    })
  } else {
    navigator.clipboard.writeText(window.location.href)
    alert('Ссылка скопирована!')
  }
}

const onDubAdded = () => {
  loadTranslations()
  showAddDubModal.value = false
}

// Синхронизация высоты постера с высотой плеера
const syncPosterHeight = () => {
  if (playerContainer.value && posterSide.value) {
    const playerHeight = playerContainer.value.offsetHeight
    console.log('Синхронизация высоты постера:', playerHeight)

    // Устанавливаем высоту контейнера
    posterSide.value.style.height = `${playerHeight}px`
    posterSide.value.style.maxHeight = `${playerHeight}px`
    posterSide.value.style.minHeight = `${playerHeight}px`
    posterSide.value.style.flexBasis = `${playerHeight}px`
    posterSide.value.style.aspectRatio = 'auto'

    // Устанавливаем высоту изображения напрямую
    const posterImage = posterSide.value.querySelector('.poster-image') as HTMLImageElement
    if (posterImage) {
      posterImage.style.height = `${playerHeight}px`
      posterImage.style.maxHeight = `${playerHeight}px`
      posterImage.style.minHeight = `${playerHeight}px`
      posterImage.style.width = 'auto'
      posterImage.style.maxWidth = '100%'
      console.log('Высота изображения установлена:', playerHeight)
    }
  }
}

// Обработка горячих клавиш
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
    return
  }

  switch (event.code) {
    case 'Space':
      event.preventDefault()
      break
    case 'ArrowLeft':
      event.preventDefault()
      if (currentEpisode.value > 1) {
        selectEpisode(currentEpisode.value - 1)
      }
      break
    case 'ArrowRight':
      event.preventDefault()
      if (currentEpisode.value < (anime.value?.episodes || 1)) {
        selectEpisode(currentEpisode.value + 1)
      }
      break
  }
}

onMounted(() => {
  loadAnime()
  document.addEventListener('keydown', handleKeyPress)

  // Синхронизируем высоту постера с плеером
  nextTick(() => {
    syncPosterHeight()
  })

  // Дополнительная синхронизация после загрузки с несколькими попытками
  const syncAttempts = [100, 300, 500, 1000, 2000, 3000]
  syncAttempts.forEach(delay => {
    setTimeout(() => {
      syncPosterHeight()
    }, delay)
  })

  // Отслеживаем изменение размера плеера
  if (playerContainer.value) {
    const resizeObserver = new ResizeObserver(() => {
      syncPosterHeight()
    })
    resizeObserver.observe(playerContainer.value)

    // Сохраняем observer для очистки
    ;(window as any).playerResizeObserver = resizeObserver
  }

  // Отслеживаем изменение размера окна
  window.addEventListener('resize', syncPosterHeight)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  window.removeEventListener('resize', syncPosterHeight)
  saveWatchProgress()

  // Очищаем ResizeObserver
  const resizeObserver = (window as any).playerResizeObserver
  if (resizeObserver) {
    resizeObserver.disconnect()
    delete (window as any).playerResizeObserver
  }
})

watch(() => route.params.id, () => {
  loadAnime()
})

// При изменении выбранной озвучки обновляем ссылку плеера
watch(selectedTranslation, (newVal, oldVal) => {
  if (newVal && !newVal.is_custom && newVal.kodik_link) {
    kodikLink.value = newVal.kodik_link
  }
})
</script>

<style scoped>
.anime-watch-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
  color: #fff;
  padding: 1.5rem;
}

.watch-container {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
}

/* Левая колонка */
.left-column {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Плеер */
.player-wrapper {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.player-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.player-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #a0a0a0;
}

.player-placeholder .spinner {
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

.error-icon,
.no-video-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
}

/* Постер в правой колонке */
.poster-side {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  overflow: hidden;        /* Важно: скрываем всё, что выходит за пределы */
  padding: 0.5rem;
  width: 100%;
  max-width: 350px;
  display: flex;
  align-items: center;     /* Центрирование по вертикали */
  justify-content: center; /* Центрирование по горизонтали */
  margin: 0 auto;
  aspect-ratio: 2/3;
  position: relative;      /* Добавляем для контроля дочерних элементов */
}

.poster-image {
  width: 100%;
  height: 100%;            /* Важно: занимает всю высоту родителя */
  object-fit: cover;       /* МЕНЯЕМ contain НА cover - заполняет всю область */
  object-position: center; /* Центрирует изображение */
  border-radius: 8px;
  display: block;
  position: absolute;      /* Абсолютное позиционирование */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: auto;            /* Дополнительное центрирование */
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a0a0a0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 1.5rem;
}

/* Информация под плеером */
.anime-info-under {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.anime-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.anime-title {
  font-size: 2rem;
  font-weight: 800;
  margin: 0;
  line-height: 1.2;
  background: linear-gradient(135deg, #fff 0%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.anime-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge {
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
}

.year-badge {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.kind-badge {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.episodes-badge {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.status-badge.ongoing {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-badge.finished {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

/* Рейтинг */
.anime-rating {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rating-stars {
  display: flex;
  gap: 0.25rem;
  color: #fbbf24;
}

.rating-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #fbbf24;
}

/* Описание */
.anime-description {
  color: #a0a0a0;
  line-height: 1.8;
  font-size: 1rem;
}

/* Секция озвучек */
.translations-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.section-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #fff;
}

.add-dub-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.loading-translations {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #a0a0a0;
}

.spinner-small {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Список озвучек */
.translations-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 500px;
  overflow-y: auto;
}

.translation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.translation-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
}

.translation-item.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}

.translation-item.custom-dub {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
}

.translation-item.custom-dub:hover {
  background: rgba(139, 92, 246, 0.15);
}

.translation-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.translation-avatar {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  font-weight: 700;
  color: white;
  overflow: hidden;
}

.translation-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.translation-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.translation-name {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.translation-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.translation-type,
.translation-quality {
  font-size: 0.8rem;
  color: #a0a0a0;
  padding: 0.125rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.custom-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
  border-radius: 4px;
  font-weight: 600;
}

.translation-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.translation-progress {
  font-size: 0.875rem;
  color: #a0a0a0;
  text-align: right;
}

.check-icon {
  color: #22c55e;
}

.no-translations {
  text-align: center;
  padding: 3rem 1rem;
  color: #a0a0a0;
}

.no-translations-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* Правая колонка */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  height: fit-content;
  align-self: start;
  align-items: stretch;
}

/* Карточки */
.progress-card,
.actions-card,
.current-episode-card,
.genres-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
  width: 100%;
}

.progress-card h3,
.actions-card h3,
.current-episode-card h3,
.genres-card h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

/* Прогресс */
.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.progress-text {
  font-size: 0.9rem;
  color: #a0a0a0;
}

.progress-percent {
  font-size: 1.25rem;
  font-weight: 700;
  color: #3b82f6;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  transition: width 0.3s ease;
}

.progress-hint {
  font-size: 0.75rem;
  color: #6b7280;
  text-align: center;
  margin: 0;
}

/* Действия */
.actions-card {
  display: flex;
  flex-direction: row;
  gap: 0.75rem;
  padding: 1.5rem;
}

.actions-card h3 {
  display: none;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Текущая серия */
.current-episode-card {
  padding: 1.5rem;
}

/* Жанры */
.genres-card {
  padding: 1.5rem;
}

.genres-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.genre-tag {
  padding: 0.375rem 0.75rem;
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid rgba(139, 92, 246, 0.3);
  transition: all 0.2s;
}

.genre-tag:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
  transform: translateY(-1px);
}

.episode-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 1rem;
}

.episode-number {
  font-size: 0.8rem;
  color: #3b82f6;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.episode-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

.episode-progress {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.episode-time {
  font-size: 0.875rem;
  color: #a0a0a0;
  text-align: right;
}

.episode-progress-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.episode-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  transition: width 0.3s ease;
}

/* Адаптивность */
@media (max-width: 1200px) {
  .watch-container {
    grid-template-columns: 1fr 300px;
  }
}

@media (max-width: 1024px) {
  .watch-container {
    grid-template-columns: 1fr;
  }

  .right-column {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .poster-side {
    width: 200px;
    flex-shrink: 0;
    height: auto !important;
    aspect-ratio: 2/3 !important;
  }

  .progress-card,
  .actions-card,
  .current-episode-card,
  .genres-card {
    flex: 1;
    min-width: 200px;
  }

  .actions-card {
    flex-direction: row;
  }
}

@media (max-width: 768px) {
  .anime-watch-page {
    padding: 1rem;
  }

  .anime-title {
    font-size: 1.5rem;
  }

  .translations-section,
  .progress-card,
  .actions-card,
  .current-episode-card {
    padding: 1.25rem;
  }

  .translation-left {
    gap: 0.75rem;
  }

  .translation-avatar {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 480px) {
  .anime-title {
    font-size: 1.25rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .add-dub-btn {
    width: 100%;
    justify-content: center;
  }

  .translation-item {
    padding: 0.875rem;
  }
}
</style>
