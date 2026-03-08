<template>
  <div class="anime-watch-page">
    <div class="watch-container">

      <!-- ══════════════════════════════════════════════
           ЛЕВАЯ КОЛОНКА: плеер + инфо + озвучки
      ══════════════════════════════════════════════ -->
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
              :poster="posterSrc ?? undefined"
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
              <button @click="retryLoad" class="btn-retry">Попробовать снова</button>
            </div>
            <div v-else class="player-placeholder">
              <div class="no-video-icon">🎬</div>
              <p>Видео недоступно</p>
            </div>

            <!-- ── Быстрые действия плеера (правый верх) ── -->
            <div class="player-quick-actions" v-if="kodikLink || customVideoUrl">
              <button
                class="pqa-btn mark-btn"
                :class="{ done: epIsWatched(currentEpisode) }"
                @click="onPlayerMarkWatched"
                :title="epIsWatched(currentEpisode) ? 'Просмотрено ✔' : 'Отметить просмотренной'"
              >
                <span>✓</span>
              </button>
              <button
                class="pqa-btn skip-btn"
                @click="onPlayerSkip"
                title="Пропустить серию"
              >
                <span>⏭</span>
              </button>
            </div>

            <!-- ── Индикатор прогресса серии (левый низ) ── -->
            <div class="player-ep-info" v-if="duration > 0">
              <span class="pei-ep">Серия {{ currentEpisode }}</span>
              <span class="pei-time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
              <div class="pei-bar">
                <div class="pei-fill" :style="{ width: episodeProgress + '%' }" />
              </div>
            </div>
          </div>
        </div>

        <!-- Диалог "Пропустить серию?" (показывается над плеером) -->
        <Transition name="skip-dialog">
          <div class="skip-dialog" v-if="showSkipDialog">
            <div class="skip-dialog-inner">
              <span class="skip-dialog-icon">⏭️</span>
              <div class="skip-dialog-text">
                <strong>Пропустить серию {{ currentEpisode }}?</strong>
                <span>Просмотрено {{ Math.round(episodeProgress) }}% — серия не будет отмечена</span>
              </div>
              <div class="skip-dialog-btns">
                <button class="sd-btn sd-yes" @click="confirmSkip">Пропустить</button>
                <button class="sd-btn sd-filler" @click="confirmSkipAsFiller">Это филлер</button>
                <button class="sd-btn sd-no" @click="cancelSkip">Остаться</button>
              </div>
            </div>
          </div>
        </Transition>

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
              <svg v-for="i in 5" :key="i" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </div>
            <span class="rating-value">{{ anime.score.toFixed(1) }}</span>
          </div>

          <p class="anime-description">{{ anime?.description || 'Описание отсутствует' }}</p>
        </div>

        <!-- Озвучки -->
        <div class="translations-section">
          <div class="section-header">
            <h3>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              Озвучки
            </h3>
            <button @click="showAddDubModal = true" class="btn-outline-sm">
              + Добавить
            </button>
          </div>

          <div v-if="loadingTranslations" class="loading-row">
            <div class="spinner-sm"></div>
            <p>Загрузка озвучек...</p>
          </div>
          <div v-else-if="translations.length > 0" class="translations-list">
            <div
              v-for="translation in translations"
              :key="translation.id"
              class="translation-item"
              :class="{ active: selectedTranslationId === translation.id, 'custom-dub': translation.is_custom }"
              @click="selectTranslation(translation)"
            >
              <div class="translation-left">
                <div class="translation-avatar">
                  <img v-if="getTranslationAvatar(translation)" :src="getTranslationAvatar(translation)" :alt="translation.name">
                  <span v-else>{{ getTranslationInitials(translation.name) }}</span>
                </div>
                <div class="translation-info">
                  <span class="translation-name">{{ translation.name }}</span>
                  <span class="translation-meta">
                    <span class="t-tag">{{ getTranslationType(translation.type) }}</span>
                    <span v-if="translation.quality" class="t-tag">{{ translation.quality }}</span>
                    <span v-if="translation.is_custom" class="t-tag custom">Пользовательская</span>
                  </span>
                </div>
              </div>
              <svg v-if="selectedTranslationId === translation.id" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          </div>
          <div v-else class="no-translations">
            <span>🎤</span>
            <p>Озвучки недоступны</p>
            <button @click="showAddDubModal = true" class="btn-primary-sm">Добавить первую</button>
          </div>
        </div>

      </div>

      <!-- ══════════════════════════════════════════════
           ПРАВАЯ КОЛОНКА: постер + серии + жанры
      ══════════════════════════════════════════════ -->
      <div class="right-column">

        <!-- Постер с оверлеем прогресса -->
        <div class="poster-side" ref="posterSide">
          <img
            v-if="posterSrc"
            :src="posterSrc"
            :alt="anime?.title_ru"
            class="poster-image"
            @load="syncPosterHeight"
          />
          <div v-else class="poster-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <path d="M21 15l-5-5L5 21"/>
            </svg>
          </div>

          <!-- Круглый бейдж прогресса в правом нижнем углу -->
          <div
            v-if="anime?.episodes && epPercent > 0"
            class="poster-progress-badge"
            :class="{ completed: epPercent >= 100 }"
            :title="`Просмотрено ${epWatchedCount} из ${anime.episodes} серий`"
          >
            <svg class="ppb-svg" viewBox="0 0 36 36">
              <circle class="ppb-track" cx="18" cy="18" r="15" />
              <circle
                class="ppb-fill"
                cx="18" cy="18" r="15"
                :stroke-dasharray="`${epPercent * 0.942} 94.2`"
              />
            </svg>
            <span class="ppb-label">
              <span v-if="epPercent >= 100">✓</span>
              <span v-else>{{ epPercent }}%</span>
            </span>
          </div>
        </div>

        <!-- Серии + прогресс -->
        <div v-if="anime?.episodes" class="episodes-card">
          <div class="ec-header">
            <h3>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="15" rx="2"/>
                <polyline points="17 2 12 7 7 2"/>
              </svg>
              Серии
            </h3>
            <button class="btn-sync-sm" @click="showSyncModal = true">⚙</button>
          </div>

          <EpisodeList
            :total-episodes="anime.episodes"
            :current-episode="currentEpisode"
            :episodes="epEpisodes"
            :watched-count="epWatchedCount"
            :progress-percent="epPercent"
            :next-episode="epNextEpisode"
            @select-episode="onSelectEpisodeFromList"
            @mark-watched="onMarkWatched"
            @undo-mark="onUndoMark"
            @skip-episode="onSkipEpisode"
            @open-sync="showSyncModal = true"
          />
        </div>

        <!-- Жанры -->
        <div v-if="anime?.genres && anime.genres.length > 0" class="genres-card">
          <h3>Жанры</h3>
          <div class="genres-list">
            <span
              v-for="genre in anime.genres"
              :key="typeof genre === 'object' ? genre.id : genre"
              class="genre-tag"
            >{{ typeof genre === 'object' ? genre.name : genre }}</span>
          </div>
        </div>

        <!-- Действия -->
        <div class="actions-card">
          <button @click="addToFavorites" class="action-btn">❤ В избранное</button>
          <button @click="shareAnime" class="action-btn">↗ Поделиться</button>
        </div>

      </div>
    </div>

    <!-- Модалки -->
    <AddCustomDubModal
      :show="showAddDubModal"
      :anime-id="anime?.id"
      :anime-title="anime?.title_ru || anime?.title_en"
      @close="showAddDubModal = false"
      @dub-added="onDubAdded"
    />

    <EpisodeProgressModal
      :show="showSyncModal"
      :anime-title="anime?.title_ru || anime?.title_en || ''"
      :total-episodes="anime?.episodes || 0"
      :current-episode="epNextEpisode ?? 1"
      @close="showSyncModal = false"
      @apply="handleSyncApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'
import KodikPlayer from '@/components/Players/KodikPlayer.vue'
import CustomVideoPlayer from '@/components/Players/CustomVideoPlayer.vue'
import AddCustomDubModal from '@/components/modal/anime/AddCustomDubModal.vue'
import EpisodeProgressModal from '@/components/modal/anime/EpisodeProgressModal.vue'
import EpisodeList from '@/components/Cards/EpisodeList.vue'
import { getTranslationAvatarUrl } from '@/utils/translationAvatars'
import { useEpisodeProgress } from '@/composables/useEpisodeProgress'
import { useToast } from '@/composables/useToast'
import { getMediaUrl } from '@/api/client'

const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

// ── Episode Progress ──────────────────────────────────────────────
let epProgress: ReturnType<typeof useEpisodeProgress> | null = null
const showSyncModal   = ref(false)
const epWatchedCount  = ref(0)
const epPercent       = ref(0)
const epNextEpisode   = ref<number | null>(null)
const epEpisodes      = ref<Map<number, any>>(new Map())
const epTotalEpisodes = ref(0)

const epIsWatched = (num: number) => epEpisodes.value.get(num)?.status === 'watched'

// ── Основное состояние ───────────────────────────────────────────
const anime              = ref<any>(null)
const kodikLink          = ref('')
const customVideoUrl     = ref('')
const loading            = ref(true)
const loadingTranslations = ref(false)
const error              = ref('')
const autoplay           = ref(false)
const useCustomPlayer    = ref(false)

const currentSeason      = ref(1)
const currentEpisode     = ref(1)
const selectedTranslation = ref<any>(null)
const translations       = ref<any[]>([])
const showAddDubModal    = ref(false)

const currentTime = ref(0)
const duration    = ref(0)
const isPlaying   = ref(false)

const playerContainer = ref<HTMLElement | null>(null)
const posterSide      = ref<HTMLElement | null>(null)
const kodikPlayer     = ref<InstanceType<typeof KodikPlayer> | null>(null)

// Старая система прогресса (localStorage fallback)
const watchProgress       = ref<Record<number, number>>({})
const isInLibrary         = ref(false)
const libraryItemId       = ref<number | null>(null)
const currentEpisodeData  = ref<any>(null)
const openingStartTime    = ref<number | null>(null)
const endingStartTime     = ref<number | null>(null)
const addedToLibrary      = ref(false)
const episodeMarkedWatched = ref(false)

// Диалог "Пропустить серию?"
const showSkipDialog      = ref(false)
const skipDialogTargetEp  = ref<number | null>(null)

// ── Вычисляемые ─────────────────────────────────────────────────
const episodeProgress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const selectedTranslationId = computed(() => selectedTranslation.value?.id?.toString() || '0')

/**
 * Постер — приоритет: локальный файл (poster_image_url / poster) → внешний URL (poster_url).
 * poster_image_url уже возвращает локальный путь /media/anime_posters/... если файл есть.
 */
const posterSrc = computed((): string | null => {
  if (!anime.value) return null
  // poster_image_url — серверный метод: сначала смотрит на локальный файл, потом poster_url
  const local = anime.value.poster_image_url || anime.value.poster
  if (local) return getMediaUrl(local) || null
  return anime.value.poster_url || null
})

// ── Хелперы ──────────────────────────────────────────────────────
const syncEpRefs = () => {
  if (!epProgress) return
  epWatchedCount.value = epProgress.watchedCount.value
  epPercent.value      = epProgress.progressPercent.value
  epNextEpisode.value  = epProgress.nextEpisodeToWatch.value
  epEpisodes.value     = new Map(epProgress.episodes.value)
}

const formatTime = (seconds: number) => {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`
  return `${m}:${s.toString().padStart(2,'0')}`
}

const getKindText = (kind: string) => ({
  tv:'ТВ', movie:'Фильм', ova:'OVA', ona:'ONA', special:'Спецвыпуск', music:'Музыка'
}[kind] || kind)

const getStatusText = (status: string) => ({
  ongoing:'Онгоинг', finished:'Завершено', announced:'Анонс', canceled:'Отменено'
}[status] || status)

const getTranslationType = (type: string) => ({
  voice:'Озвучка', subtitles:'Субтитры', raw:'Оригинал'
}[type] || type)

const getTranslationInitials = (name: string) => {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

const getTranslationAvatar = (translation: any): string | undefined => {
  if (translation.logo) return translation.logo
  return getTranslationAvatarUrl(translation.name)
}

// ── Загрузка аниме ───────────────────────────────────────────────
const loadAnime = async () => {
  try {
    loading.value = true
    error.value = ''

    const animeId = route.params.id
    const response = await apiClient.get(`/anime/${animeId}/`)
    anime.value = response.data

    const episodeFromQuery = route.query.episode
    if (episodeFromQuery) {
      const ep = parseInt(episodeFromQuery as string, 10)
      if (!isNaN(ep) && ep >= 1) {
        currentEpisode.value = ep
        autoplay.value = true
      }
    }

    await checkLibraryStatus()
    await loadTranslations()
    await loadKodikPlayer()
    loadWatchProgress()

    // Инициализируем систему прогресса серий
    if (anime.value?.id) {
      epProgress = useEpisodeProgress(anime.value.id)
      epTotalEpisodes.value = anime.value.episodes || 0
      await epProgress.loadProgress()
      syncEpRefs()

      // Тост "Вы смотрели это аниме ранее?" если нет истории
      if (authStore.isAuthenticated && epProgress.watchedCount.value === 0 && !route.query.episode) {
        setTimeout(() => showFirstVisitToast(), 800)
      }
    }
  } catch (err: any) {
    console.error('Ошибка загрузки аниме:', err)
    error.value = 'Не удалось загрузить аниме'
  } finally {
    loading.value = false
  }
}

// ── Тост первого посещения ───────────────────────────────────────
const showFirstVisitToast = () => {
  toast.info('Вы смотрели это аниме ранее?', {
    duration: 8000,
    action: {
      label: 'Настроить прогресс',
      handler: () => { showSyncModal.value = true },
    },
  })
}

// ── Библиотека ───────────────────────────────────────────────────
const checkLibraryStatus = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const response = await apiClient.get('/users/library/')
    const items: any[] = response.data.results ?? response.data
    if (!Array.isArray(items)) return

    const item = items.find((i: any) => {
      const aid = typeof i.anime === 'object' ? i.anime?.id : i.anime
      return aid === anime.value?.id
    })

    if (item) {
      isInLibrary.value = true
      libraryItemId.value = item.id
      addedToLibrary.value = true
      const savedEp = item.current_episode ?? 0
      if (savedEp > 0 && !route.query.episode) {
        currentEpisode.value = savedEp
      }
    } else {
      isInLibrary.value = false
      libraryItemId.value = null
    }
  } catch { isInLibrary.value = false }
}

const addToLibraryAutomatically = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const response = await apiClient.post('/users/library/', { anime: anime.value?.id, status: 'started' })
    isInLibrary.value = true
    libraryItemId.value = response.data.id
    await updateLibraryProgress()
  } catch (err: any) {
    if (err.response?.status === 409 || err.response?.status === 400) {
      await checkLibraryStatus()
      if (isInLibrary.value) await updateLibraryProgress()
    }
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
  } catch { /* silent */ }
}

// ── Озвучки ──────────────────────────────────────────────────────
const saveSelectedTranslation = () => {
  const animeId = anime.value?.id
  if (!animeId || !selectedTranslation.value) return
  localStorage.setItem(`anime_translation_${animeId}`, JSON.stringify({
    id: selectedTranslation.value.id,
    is_custom: selectedTranslation.value.is_custom,
    name: selectedTranslation.value.name,
  }))
}

const loadSelectedTranslation = () => {
  const animeId = anime.value?.id
  if (!animeId || translations.value.length === 0) return null
  const saved = localStorage.getItem(`anime_translation_${animeId}`)
  if (!saved) return null
  try {
    const data = JSON.parse(saved)
    return translations.value.find(t => t.id === data.id) || null
  } catch { return null }
}

const loadTranslations = async () => {
  if (!anime.value?.id) return
  try {
    loadingTranslations.value = true
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_translations/`)
    const kodikTranslations = response.data.translations || []

    try {
      const customResponse = await apiClient.get(`/anime/${anime.value.id}/custom_dubs/`)
      const customDubs = customResponse.data.dubs || []
      translations.value = [
        ...kodikTranslations.map((t: any) => ({ ...t, is_custom: false })),
        ...customDubs.map((d: any) => ({ ...d, is_custom: true, type: 'voice' })),
      ]
    } catch {
      translations.value = kodikTranslations.map((t: any) => ({ ...t, is_custom: false }))
    }

    if (translations.value.length > 0) {
      const saved = loadSelectedTranslation()
      selectedTranslation.value = saved || translations.value[0]
      if (!selectedTranslation.value.is_custom && selectedTranslation.value.kodik_link) {
        kodikLink.value = selectedTranslation.value.kodik_link
      }
    }
  } catch {
    translations.value = []
  } finally {
    loadingTranslations.value = false
  }
}

const loadKodikPlayer = async () => {
  if (!anime.value?.id || kodikLink.value) return
  try {
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_player/`)
    kodikLink.value = response.data.kodik_link
    if (response.data.last_episode) currentEpisode.value = 1
  } catch (err: any) {
    if (err.response?.status === 404) error.value = 'Видео для этого аниме не найдено'
    else if (err.response?.status === 503) error.value = 'Сервис временно недоступен'
    else error.value = 'Не удалось загрузить плеер'
  }
}

const selectTranslation = async (translation: any) => {
  selectedTranslation.value = translation
  saveSelectedTranslation()
  if (translation.is_custom) {
    useCustomPlayer.value = true
    try {
      const res = await apiClient.get(`/anime/${anime.value?.id}/custom_dubs/${translation.id}/video/`)
      customVideoUrl.value = res.data.video_url
    } catch { error.value = 'Не удалось загрузить видео' }
  } else {
    useCustomPlayer.value = false
    customVideoUrl.value = ''
    if (translation.kodik_link) kodikLink.value = translation.kodik_link
  }
}

// ── Навигация по сериям ──────────────────────────────────────────
const selectEpisode = (episode: number) => {
  currentEpisode.value = episode
}

/**
 * Переход на серию из списка — проверяем, нужно ли спросить о пропуске
 */
const onSelectEpisodeFromList = (num: number) => {
  if (num === currentEpisode.value) return

  // Если переходим вперёд и текущая серия < 50% — показываем диалог
  if (num > currentEpisode.value && episodeProgress.value < 50 && episodeProgress.value > 5) {
    skipDialogTargetEp.value = num
    showSkipDialog.value = true
  } else {
    selectEpisode(num)
  }
}

// ── Диалог пропуска ──────────────────────────────────────────────
const confirmSkip = () => {
  showSkipDialog.value = false
  if (skipDialogTargetEp.value !== null) {
    selectEpisode(skipDialogTargetEp.value)
    skipDialogTargetEp.value = null
  }
}

const confirmSkipAsFiller = async () => {
  showSkipDialog.value = false
  const epNum = currentEpisode.value
  if (epProgress) {
    await epProgress.skipEpisode(epNum)
    syncEpRefs()
  }
  if (skipDialogTargetEp.value !== null) {
    selectEpisode(skipDialogTargetEp.value)
    skipDialogTargetEp.value = null
  }
}

const cancelSkip = () => {
  showSkipDialog.value = false
  skipDialogTargetEp.value = null
}

// ── Кнопки плеера ────────────────────────────────────────────────
const onPlayerMarkWatched = async () => {
  if (!epProgress) return
  if (epIsWatched(currentEpisode.value)) {
    await epProgress.undoMark(currentEpisode.value)
  } else {
    await epProgress.markWatched(currentEpisode.value)
  }
  syncEpRefs()
}

const onPlayerSkip = () => {
  if (episodeProgress.value > 0) {
    skipDialogTargetEp.value = currentEpisode.value + 1
    showSkipDialog.value = true
  } else {
    onSkipEpisode(currentEpisode.value)
    if (currentEpisode.value < (anime.value?.episodes || 1)) {
      selectEpisode(currentEpisode.value + 1)
    }
  }
}

// ── События плеера ───────────────────────────────────────────────
const onPlayerReady = () => {
  loading.value = false
  setTimeout(syncPosterHeight, 100)
}

const onVideoStarted = () => { setTimeout(syncPosterHeight, 200) }
const onPlay  = () => { isPlaying.value = true }
const onPause = () => { isPlaying.value = false }

const triggerLibraryAdd = () => {
  if (addedToLibrary.value || isInLibrary.value) return
  addedToLibrary.value = true
  addToLibraryAutomatically()
}

const markEpisodeWatched = () => {
  if (episodeMarkedWatched.value) return
  episodeMarkedWatched.value = true
  watchProgress.value[currentEpisode.value] = 100
  saveWatchProgress()
  if (isInLibrary.value && libraryItemId.value) updateLibraryProgress()
  else addToLibraryAutomatically()
}

const onTimeUpdate = (time: number) => {
  currentTime.value = time
  if (duration.value <= 0) return

  const pct = (time / duration.value) * 100
  watchProgress.value[currentEpisode.value] = Math.min(pct, 100)

  // Добавляем в библиотеку после 30 сек
  if (!addedToLibrary.value && !isInLibrary.value && (openingStartTime.value !== null || time >= 30)) {
    triggerLibraryAdd()
  }

  // Засчитываем при эндинге
  if (endingStartTime.value !== null && !episodeMarkedWatched.value && time >= endingStartTime.value) {
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }

  // Засчитываем при 85%
  if (!episodeMarkedWatched.value && pct >= 85) {
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }

  // Сохраняем позицию каждые 10 сек
  if (Math.floor(time) % 10 === 0) {
    saveWatchProgress()
    if (isInLibrary.value && libraryItemId.value) updateLibraryProgress()
    epProgress?.updatePosition(currentEpisode.value, Math.floor(time), duration.value || undefined)
  }
}

const onDurationUpdate = (dur: number) => { duration.value = dur }

const onCurrentEpisode = (data: any) => {
  if (data.episode && data.episode !== currentEpisode.value) {
    currentEpisode.value = data.episode
    openingStartTime.value = null
    endingStartTime.value  = null
    episodeMarkedWatched.value = false
    addedToLibrary.value = isInLibrary.value
  }
  if (data.season) currentSeason.value = data.season
}

const onVideoEnded = () => {
  isPlaying.value = false
  markEpisodeWatched()
  epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  if (currentEpisode.value < (anime.value?.episodes || 1)) {
    selectEpisode(currentEpisode.value + 1)
    autoplay.value = true
  }
}

const onSkipButton = (data: { title: string }) => {
  const title = data?.title?.toLowerCase() || ''
  const isOpening = title.includes('опенинг') || title.includes('opening') || title.includes('intro')
  const isEnding  = title.includes('эндинг') || title.includes('ending') || title.includes('outro') || title.includes('титры')

  if (isOpening && openingStartTime.value === null) {
    openingStartTime.value = currentTime.value
    triggerLibraryAdd()
  }
  if (isEnding && endingStartTime.value === null && currentTime.value > 0) {
    endingStartTime.value = currentTime.value
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }
}

const onPlayerError = (err: string) => { error.value = err }

// ── Прогресс (localStorage) ──────────────────────────────────────
const loadWatchProgress = () => {
  const animeId = anime.value?.id
  if (!animeId) return
  const saved = localStorage.getItem(`anime_progress_${animeId}`)
  if (saved) {
    try { watchProgress.value = JSON.parse(saved) } catch { /* ignore */ }
  }
}

const saveWatchProgress = async () => {
  localStorage.setItem(`anime_progress_${anime.value?.id}`, JSON.stringify(watchProgress.value))
  if (!anime.value?.id || !authStore.isAuthenticated) return
  try {
    if (isInLibrary.value && libraryItemId.value) await updateLibraryProgress()
  } catch { /* silent */ }
}

// ── Обработчики EpisodeList ──────────────────────────────────────
const handleSyncApply = async (payload: { mode: string; watchedUpTo?: number }) => {
  if (!epProgress) return
  if (payload.mode === 'new' || payload.mode === 'restart') {
    await epProgress.resetProgress()
  } else if (payload.mode === 'continue' && payload.watchedUpTo) {
    await epProgress.bulkSyncUpTo(payload.watchedUpTo)
    const next = payload.watchedUpTo + 1
    if (next <= (anime.value?.episodes || 1)) selectEpisode(next)
  }
  syncEpRefs()
}

const onMarkWatched = async (num: number) => {
  if (!epProgress) return
  await epProgress.markWatched(num)
  syncEpRefs()
}

const onUndoMark = async (num: number) => {
  if (!epProgress) return
  await epProgress.undoMark(num)
  syncEpRefs()
}

const onSkipEpisode = async (num: number) => {
  if (!epProgress) return
  await epProgress.skipEpisode(num)
  syncEpRefs()
}

// ── Прочие действия ──────────────────────────────────────────────
const retryLoad = () => loadKodikPlayer()

const addToFavorites = () => { /* TODO */ }

const shareAnime = () => {
  if (navigator.share) {
    navigator.share({ title: anime.value?.title_ru, url: window.location.href })
  } else {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Ссылка скопирована!')
  }
}

const onDubAdded = () => {
  loadTranslations()
  showAddDubModal.value = false
}

// ── Синхронизация высоты постера ─────────────────────────────────
const syncPosterHeight = () => {
  if (!playerContainer.value || !posterSide.value) return
  const h = playerContainer.value.offsetHeight
  posterSide.value.style.height    = `${h}px`
  posterSide.value.style.maxHeight = `${h}px`
  posterSide.value.style.minHeight = `${h}px`
  posterSide.value.style.aspectRatio = 'auto'
  const img = posterSide.value.querySelector('.poster-image') as HTMLImageElement
  if (img) {
    img.style.height    = `${h}px`
    img.style.maxHeight = `${h}px`
    img.style.width     = 'auto'
    img.style.maxWidth  = '100%'
  }
}

// ── Горячие клавиши ──────────────────────────────────────────────
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return
  switch (event.code) {
    case 'ArrowLeft':
      event.preventDefault()
      if (currentEpisode.value > 1) selectEpisode(currentEpisode.value - 1)
      break
    case 'ArrowRight':
      event.preventDefault()
      if (currentEpisode.value < (anime.value?.episodes || 1)) selectEpisode(currentEpisode.value + 1)
      break
  }
}

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(() => {
  loadAnime()
  document.addEventListener('keydown', handleKeyPress)

  nextTick(syncPosterHeight)
  ;[100,300,500,1000,2000].forEach(d => setTimeout(syncPosterHeight, d))

  if (playerContainer.value) {
    const ro = new ResizeObserver(syncPosterHeight)
    ro.observe(playerContainer.value)
    ;(window as any)._playerRO = ro
  }
  window.addEventListener('resize', syncPosterHeight)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  window.removeEventListener('resize', syncPosterHeight)
  saveWatchProgress()
  const ro = (window as any)._playerRO
  if (ro) { ro.disconnect(); delete (window as any)._playerRO }
})

watch(() => route.params.id, () => { loadAnime() })
watch(selectedTranslation, (v) => {
  if (v && !v.is_custom && v.kodik_link) kodikLink.value = v.kodik_link
})
</script>

<style scoped>
/* ════════════════════════════════════════════════════════
   LAYOUT
════════════════════════════════════════════════════════ */
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

.left-column  { display: flex; flex-direction: column; gap: 2rem; }
.right-column { display: flex; flex-direction: column; gap: 1.5rem; align-self: start; }

/* ════════════════════════════════════════════════════════
   ПЛЕЕР
════════════════════════════════════════════════════════ */
.player-wrapper {
  background: #000;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.player-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.player-placeholder {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; color: #a0a0a0;
}

.player-placeholder .spinner {
  width: 44px; height: 44px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-icon, .no-video-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }

.btn-retry {
  margin-top: 0.75rem;
  padding: 0.6rem 1.25rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

/* ── Быстрые действия плеера (✓ ⏭) ─────────────────── */
.player-quick-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
  z-index: 10;
  opacity: 0;
  transition: opacity .2s;
}

.player-container:hover .player-quick-actions { opacity: 1; }

.pqa-btn {
  width: 34px; height: 34px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  transition: all .15s;
  backdrop-filter: blur(4px);
}

.pqa-btn.mark-btn {
  background: rgba(34,197,94,0.25);
  color: #22c55e;
  border: 1px solid rgba(34,197,94,0.4);
}
.pqa-btn.mark-btn:hover { background: rgba(34,197,94,0.45); }
.pqa-btn.mark-btn.done  { background: rgba(34,197,94,0.5); color: #fff; }

.pqa-btn.skip-btn {
  background: rgba(245,158,11,0.2);
  color: #f59e0b;
  border: 1px solid rgba(245,158,11,0.35);
}
.pqa-btn.skip-btn:hover { background: rgba(245,158,11,0.4); }

/* ── Индикатор прогресса серии (левый низ плеера) ──── */
.player-ep-info {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  padding: 1rem 1rem 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  pointer-events: none;
  opacity: 0;
  transition: opacity .2s;
}

.player-container:hover .player-ep-info { opacity: 1; }

.pei-ep {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.7);
  font-weight: 600;
  white-space: nowrap;
}

.pei-time {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.5);
  white-space: nowrap;
}

.pei-bar {
  flex: 1;
  height: 3px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  overflow: hidden;
}

.pei-fill {
  height: 100%;
  background: #3b82f6;
  transition: width .3s;
}

/* ── Диалог "Пропустить серию?" ──────────────────────── */
.skip-dialog {
  background: rgba(15,15,26,0.97);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  backdrop-filter: blur(8px);
}

.skip-dialog-inner {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  flex-wrap: wrap;
}

.skip-dialog-icon { font-size: 1.5rem; flex-shrink: 0; }

.skip-dialog-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.skip-dialog-text strong { font-size: 0.9rem; color: #fff; }
.skip-dialog-text span { font-size: 0.78rem; color: #9ca3af; }

.skip-dialog-btns {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.sd-btn {
  padding: 0.375rem 0.875rem;
  border-radius: 7px;
  border: none;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}

.sd-yes    { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.sd-yes:hover { background: rgba(245,158,11,0.35); }

.sd-filler { background: rgba(139,92,246,0.2); color: #a78bfa; border: 1px solid rgba(139,92,246,0.3); }
.sd-filler:hover { background: rgba(139,92,246,0.35); }

.sd-no { background: rgba(255,255,255,0.07); color: #9ca3af; border: 1px solid rgba(255,255,255,0.1); }
.sd-no:hover { background: rgba(255,255,255,0.12); color: #fff; }

.skip-dialog-enter-active, .skip-dialog-leave-active { transition: all .2s ease; }
.skip-dialog-enter-from, .skip-dialog-leave-to { opacity: 0; transform: translateY(-8px); }

/* ════════════════════════════════════════════════════════
   ИНФО ПОД ПЛЕЕРОМ
════════════════════════════════════════════════════════ */
.anime-info-under { display: flex; flex-direction: column; gap: 1.25rem; }
.anime-header { display: flex; flex-direction: column; gap: 0.6rem; }

.anime-title {
  font-size: 1.875rem;
  font-weight: 800;
  margin: 0;
  line-height: 1.2;
  background: linear-gradient(135deg, #fff 0%, #9ca3af 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.anime-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.badge {
  padding: 0.3rem 0.75rem;
  border-radius: 7px;
  font-size: 0.75rem;
  font-weight: 600;
}

.year-badge     { background: rgba(59,130,246,0.2); color: #3b82f6; }
.kind-badge     { background: rgba(139,92,246,0.2);  color: #a78bfa; }
.episodes-badge { background: rgba(34,197,94,0.2);   color: #22c55e; }
.status-badge   { background: rgba(251,191,36,0.2);  color: #fbbf24; }
.status-badge.ongoing  { background: rgba(34,197,94,0.2); color: #22c55e; }
.status-badge.finished { background: rgba(156,163,175,0.15); color: #9ca3af; }

.anime-rating { display: flex; align-items: center; gap: 0.75rem; }
.rating-stars { display: flex; gap: 0.2rem; color: #fbbf24; }
.rating-value { font-size: 1.375rem; font-weight: 800; color: #fbbf24; }

.anime-description { color: #9ca3af; line-height: 1.75; font-size: 0.95rem; }

/* ════════════════════════════════════════════════════════
   ОЗВУЧКИ
════════════════════════════════════════════════════════ */
.translations-section {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.375rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  display: flex; align-items: center; gap: 0.4rem;
  margin: 0; font-size: 1rem; font-weight: 600;
}

.btn-outline-sm {
  padding: 0.35rem 0.875rem;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05);
  color: #9ca3af;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all .2s;
}
.btn-outline-sm:hover { background: rgba(255,255,255,0.1); color: #fff; }

.loading-row { display: flex; align-items: center; gap: 0.75rem; padding: 1.5rem; color: #9ca3af; }

.spinner-sm {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.translations-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 440px; overflow-y: auto; }

.translation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px;
  cursor: pointer;
  transition: all .15s;
}
.translation-item:hover { background: rgba(255,255,255,0.06); }
.translation-item.active { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.35); }
.translation-item.custom-dub { background: rgba(139,92,246,0.08); border-color: rgba(139,92,246,0.25); }

.translation-left { display: flex; align-items: center; gap: 0.875rem; flex: 1; min-width: 0; }

.translation-avatar {
  width: 42px; height: 42px;
  border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700; color: #fff;
  overflow: hidden; flex-shrink: 0;
}
.translation-avatar img { width: 100%; height: 100%; object-fit: cover; }

.translation-info { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.translation-name { font-size: 0.9rem; font-weight: 600; color: #fff; }
.translation-meta { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }

.t-tag {
  font-size: 0.7rem; color: #9ca3af;
  padding: 0.1rem 0.4rem;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
}
.t-tag.custom { background: rgba(139,92,246,0.25); color: #a78bfa; }

.no-translations { text-align: center; padding: 2rem 1rem; color: #9ca3af; }
.no-translations span { font-size: 2.5rem; }
.no-translations p { margin: 0.5rem 0 1rem; }

.btn-primary-sm {
  padding: 0.5rem 1.25rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
}

/* ════════════════════════════════════════════════════════
   ПРАВАЯ КОЛОНКА
════════════════════════════════════════════════════════ */

/* Постер */
.poster-side {
  background: rgba(0,0,0,0.3);
  border-radius: 12px;
  overflow: hidden;
  width: 100%;
  max-width: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  aspect-ratio: 2/3;
  position: relative;
}

.poster-image {
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: center;
  border-radius: 8px;
  display: block;
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
}

.poster-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: #6b7280; background: rgba(255,255,255,0.03);
}

/* ── Бейдж прогресса на постере ──────────────────────── */
.poster-progress-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 40px;
  height: 40px;
  background: rgba(0,0,0,0.75);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
  cursor: default;
  z-index: 2;
}

.ppb-svg {
  position: absolute;
  width: 40px; height: 40px;
  transform: rotate(-90deg);
}

.ppb-track {
  fill: none;
  stroke: rgba(255,255,255,0.15);
  stroke-width: 3;
}

.ppb-fill {
  fill: none;
  stroke: #3b82f6;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray .4s ease;
}

.poster-progress-badge.completed .ppb-fill { stroke: #22c55e; }

.ppb-label {
  font-size: 0.55rem;
  font-weight: 700;
  color: #fff;
  z-index: 1;
  line-height: 1;
}

/* Серии */
.episodes-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.ec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.ec-header h3 {
  display: flex; align-items: center; gap: 0.4rem;
  margin: 0; font-size: 0.95rem; font-weight: 600;
}

.btn-sync-sm {
  width: 28px; height: 28px;
  border-radius: 7px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #9ca3af;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.btn-sync-sm:hover { background: rgba(255,255,255,0.1); color: #fff; }

/* Жанры */
.genres-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.genres-card h3 {
  margin: 0 0 0.875rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.72rem;
}

.genres-list { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.genre-tag {
  padding: 0.3rem 0.7rem;
  background: rgba(139,92,246,0.12);
  color: #a78bfa;
  border-radius: 7px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid rgba(139,92,246,0.25);
  cursor: default;
  transition: all .15s;
}
.genre-tag:hover { background: rgba(139,92,246,0.22); }

/* Действия */
.actions-card {
  display: flex;
  gap: 0.75rem;
}

.action-btn {
  flex: 1;
  padding: 0.75rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  color: #9ca3af;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
}
.action-btn:hover { background: rgba(255,255,255,0.1); color: #fff; transform: translateY(-1px); }

/* ════════════════════════════════════════════════════════
   АНИМАЦИИ
════════════════════════════════════════════════════════ */
@keyframes spin { to { transform: rotate(360deg); } }

/* ════════════════════════════════════════════════════════
   АДАПТИВНОСТЬ
════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .watch-container { grid-template-columns: 1fr 300px; }
}

@media (max-width: 1024px) {
  .watch-container { grid-template-columns: 1fr; }

  .right-column {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .poster-side {
    width: 180px;
    flex-shrink: 0;
    height: auto !important;
    aspect-ratio: 2/3 !important;
  }

  .episodes-card { flex: 1; min-width: 280px; }
  .genres-card, .actions-card { flex: 1; min-width: 200px; }
}

@media (max-width: 768px) {
  .anime-watch-page { padding: 0.75rem; }
  .anime-title { font-size: 1.375rem; }
  .watch-container { gap: 1.25rem; }
  .translations-section, .episodes-card { padding: 1rem; }
  .skip-dialog-inner { flex-direction: column; align-items: flex-start; }
}

@media (max-width: 480px) {
  .anime-title { font-size: 1.125rem; }
  .section-header { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
  .btn-outline-sm { width: 100%; justify-content: center; }
}
</style>
