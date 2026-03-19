<template>
  <div 
    class="anime-card franchise-card" 
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <!-- Постер франшизы с прокруткой -->
    <div class="anime-poster" @mouseenter="startPosterRotation" @mouseleave="stopPosterRotation">
      <!-- Основной постер -->
      <img
        v-if="currentPosterUrl"
        :src="currentPosterUrl"
        :alt="franchise.name"
        class="poster-image"
        :class="{ 'poster-transitioning': isTransitioning }"
        loading="lazy"
        decoding="async"
        fetchpriority="high"
        @error="handleImageError"
      />
      <div v-else class="poster-placeholder">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <path d="M12 2v20M2 12h20"/>
        </svg>
      </div>

      <!-- Стрелка влево -->
      <button
        v-if="allPosters.length > 1"
        class="poster-nav-btn poster-nav-left"
        @click.stop="prevPoster"
        @mouseenter="stopPosterRotation"
        @mouseleave="startPosterRotation"
        type="button"
        aria-label="Предыдущий постер"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>

      <!-- Стрелка вправо -->
      <button
        v-if="allPosters.length > 1"
        class="poster-nav-btn poster-nav-right"
        @click.stop="nextPoster"
        @mouseenter="stopPosterRotation"
        @mouseleave="startPosterRotation"
        type="button"
        aria-label="Следующий постер"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>

      <!-- Счётчик частей (верхний левый угол) -->
      <div class="parts-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
        </svg>
        <span>{{ partsCount }} {{ partsWord }}</span>
      </div>

      <!-- Градиентный оверлей снизу -->
      <div class="poster-overlay"></div>

      <!-- Оверлей с кнопкой play при наведении -->
      <div class="hover-overlay" @click.stop="handleClick">
        <button class="play-btn" @click.stop="handleClick">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
      </div>

      <!-- Индикатор живой обложки (правый верхний угол) -->
      <div 
        v-if="hasLiveCover" 
        class="live-cover-indicator"
        @mouseenter="previewLiveCover"
        @mouseleave="stopLiveCoverPreview"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
      </div>

      <!-- Кнопки действий (правый верхний угол, появляются при наведении) -->
      <div v-if="showActions" class="card-actions">
        <button
          :class="['action-btn', 'favorite-btn']"
          @click.stop="toggleFavorite"
          :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
        <button
          class="action-btn discuss-btn"
          @click.stop="handleDiscuss"
          title="Обсудить"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
        <button
          class="action-btn playlist-btn"
          @click.stop="showPlaylistModal = true"
          title="Добавить в плейлист"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
        <button
          class="action-btn reminder-btn"
          @click.stop="showReminderModal = true"
          title="Напомнить о выходе"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="13" r="8"/>
            <path d="M12 9v4l2 2"/>
            <path d="M19 3v2a3 3 0 0 1 3 3v2"/>
            <path d="M5 5a3 3 0 0 1 3-3V3"/>
          </svg>
        </button>
      </div>

      <!-- Рейтинг (левый нижний угол) -->
      <div v-if="avgScore" class="score-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span>{{ avgScore }}</span>
      </div>
    </div>

    <!-- Информационный слой -->
    <div class="anime-info">
      <h3 class="anime-title">{{ franchise.name }}</h3>
      
      <div class="anime-meta">
        <span class="meta-item meta-highlight">
          {{ partsCount }} {{ partsWord }}
        </span>
        <span class="meta-separator">·</span>
        <span class="meta-item" v-if="yearRange">
          {{ yearRange }}
        </span>
        <span class="meta-separator" v-if="franchise.entries?.length">·</span>
        <span class="meta-status status-franchise">
          Франшиза
        </span>
      </div>

      <!-- Жанры (совокупность всех частей) -->
      <div v-if="showGenres && displayGenres.length > 0" class="anime-genres">
        <span
          v-for="(genre, index) in displayGenres"
          :key="index"
          class="genre-tag"
          :title="allGenres.join(', ')"
        >
          {{ genre }}
        </span>
        <span v-if="allGenres.length > maxGenres" class="genre-more">
          +{{ allGenres.length - maxGenres }}
        </span>
      </div>

      <!-- Статусная полоска -->
      <div class="status-bar status-bar-franchise"></div>
    </div>

    <!-- Модальное окно добавления в плейлист -->
    <PlaylistSelectModal
      v-if="showPlaylistModal"
      :show="showPlaylistModal"
      :anime="franchiseAsAnime"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

    <!-- Модальное окно напоминания -->
    <ReminderModal
      v-if="showReminderModal && reminderAnime"
      :show="showReminderModal"
      :anime="reminderAnime"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />

    <!-- Модалка создания нового плейлиста -->
    <Teleport to="body">
      <Transition name="psm-anim">
        <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false" style="position:fixed;inset:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;z-index:10001;padding:1rem;">
          <div style="background:var(--surface-2);border-radius:1rem;max-width:420px;width:100%;padding:1.5rem;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);display:flex;flex-direction:column;gap:1rem;">
            <h3 style="margin:0;font-size:1.1rem;font-weight:700;color:var(--text-primary);">Новый плейлист</h3>
            <input
              v-model="newPlaylistTitle"
              placeholder="Название плейлиста"
              @keydown.enter="saveNewPlaylist"
              style="height:38px;padding:0 12px;background:var(--surface-3);border:1px solid var(--border-subtle);border-radius:var(--radius-md);color:var(--text-primary);font-size:var(--text-sm);outline:none;width:100%;box-sizing:border-box;"
            />
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:var(--text-sm);color:var(--text-secondary);">
              <input type="checkbox" v-model="newPlaylistPublic" />
              Публичный
            </label>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
              <button @click="showCreateModal = false" style="height:36px;padding:0 16px;background:var(--surface-4);color:var(--text-secondary);border:1px solid var(--border-subtle);border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);">Отмена</button>
              <button @click="saveNewPlaylist" :disabled="!newPlaylistTitle.trim() || creatingPlaylist" style="height:36px;padding:0 16px;background:var(--accent);color:white;border:none;border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);font-weight:600;opacity:1;" :style="{ opacity: !newPlaylistTitle.trim() || creatingPlaylist ? '0.5' : '1' }">{{ creatingPlaylist ? 'Создание...' : 'Создать' }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlaylistSelectModal, ReminderModal } from '@/components/Modals'
import playlistsApi from '@/api/playlists'
import remindersApi from '@/api/reminders'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import { getMediaUrl } from '@/api/client'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

interface FranchiseEntry {
  id: number
  title_ru: string
  title_en?: string
  year?: number
  score?: number
  kind?: string
  episodes?: number
  poster_url?: string
  poster_image_url?: string
  poster?: any
  franchise_order?: number
}

interface FranchiseProps {
  id: number
  name: string
  slug?: string
  description?: string
  poster_url?: string | null
  poster_image_url?: string | null
  poster?: any
  score?: number | null
  year_start?: number | null
  year_end?: number | null
  parts_count?: number
  year_range?: string
  avg_score?: number | null
  all_genres?: string[]
  all_posters?: string[]
  entries?: FranchiseEntry[]
}

interface Props {
  franchise: FranchiseProps
  showActions?: boolean
  hasLiveCover?: boolean
  showGenres?: boolean
  maxGenres?: number
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
  hasLiveCover: false,
  showGenres: true,
  maxGenres: 3
})

const emit = defineEmits<{
  click: [franchise: FranchiseProps]
  'favorite-toggle': [isFavorite: boolean]
}>()

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

const isFavorite = ref(false)
const showPlaylistModal = ref(false)
const showReminderModal = ref(false)
const showCreateModal = ref(false)
const newPlaylistTitle = ref('')
const newPlaylistPublic = ref(false)
const creatingPlaylist = ref(false)
const playlists = ref<any[]>([])
const playlistsLoading = ref(false)

// Прокрутка постеров
const currentPosterIndex = ref(0)
const isTransitioning = ref(false)
let rotationTimer: ReturnType<typeof setInterval> | null = null

// Вычисляемые свойства
const partsCount = computed(() => {
  return props.franchise.parts_count || props.franchise.entries?.length || 0
})

const partsWord = computed(() => {
  const count = partsCount.value
  const lastTwo = count % 100
  const lastOne = count % 10
  
  if (lastTwo >= 11 && lastTwo <= 19) return 'частей'
  if (lastOne === 1) return 'часть'
  if (lastOne >= 2 && lastOne <= 4) return 'части'
  return 'частей'
})

const yearRange = computed(() => {
  if (props.franchise.year_range) return props.franchise.year_range
  
  const start = props.franchise.year_start
  const end = props.franchise.year_end
  
  if (start && end) {
    if (start === end) return String(start)
    return `${start} – ${end}`
  }
  if (start) return String(start)
  if (end) return String(end)
  return null
})

const avgScore = computed(() => {
  if (props.franchise.avg_score) return props.franchise.avg_score.toFixed(1)
  if (props.franchise.score) return props.franchise.score.toFixed(1)
  return null
})

const allGenres = computed(() => {
  return props.franchise.all_genres || []
})

const displayGenres = computed(() => {
  return allGenres.value.slice(0, props.maxGenres)
})

const allPosters = computed(() => {
  if (props.franchise.all_posters && props.franchise.all_posters.length > 0) {
    return props.franchise.all_posters.map(p => getMediaUrl(p))
  }
  
  // Если нет all_posters, собираем из entries
  if (props.franchise.entries && props.franchise.entries.length > 0) {
    return props.franchise.entries
      .sort((a, b) => (a.franchise_order || 0) - (b.franchise_order || 0))
      .map(e => {
        if (e.poster && typeof e.poster === 'string') return getMediaUrl(e.poster)
        if (e.poster_image_url) return getMediaUrl(e.poster_image_url)
        if (e.poster_url) return getMediaUrl(e.poster_url)
        return null
      })
      .filter(Boolean) as string[]
  }
  
  return []
})

const currentPosterUrl = computed(() => {
  if (allPosters.value.length > 0) {
    return allPosters.value[currentPosterIndex.value]
  }
  
  // Fallback на основной постер франшизы
  if (props.franchise.poster && typeof props.franchise.poster === 'string') {
    return getMediaUrl(props.franchise.poster)
  }
  if (props.franchise.poster_image_url) {
    return getMediaUrl(props.franchise.poster_image_url)
  }
  if (props.franchise.poster_url) {
    return getMediaUrl(props.franchise.poster_url)
  }
  
  return null
})

// Прокрутка постеров
const startPosterRotation = () => {
  if (allPosters.value.length <= 1) return
  
  stopPosterRotation()
  rotationTimer = setInterval(() => {
    nextPoster()
  }, 3000)
}

const stopPosterRotation = () => {
  if (rotationTimer) {
    clearInterval(rotationTimer)
    rotationTimer = null
  }
}

const prevPoster = () => {
  isTransitioning.value = true
  setTimeout(() => {
    currentPosterIndex.value = currentPosterIndex.value === 0 
      ? allPosters.value.length - 1 
      : currentPosterIndex.value - 1
    setTimeout(() => {
      isTransitioning.value = false
    }, 150)
  }, 150)
}

const nextPoster = () => {
  isTransitioning.value = true
  setTimeout(() => {
    currentPosterIndex.value = (currentPosterIndex.value + 1) % allPosters.value.length
    setTimeout(() => {
      isTransitioning.value = false
    }, 150)
  }, 150)
}

// Для совместимости с PlaylistSelectModal
const franchiseAsAnime = computed(() => ({
  id: props.franchise.id,
  title_ru: props.franchise.name,
  title_en: props.franchise.name,
  poster_url: props.franchise.poster_url || undefined,
  poster_image_url: props.franchise.poster_image_url || undefined,
  poster: props.franchise.poster || undefined
}))

// Для напоминания - берём первое онгоинг или первое аниме из франшизы
const reminderAnime = computed(() => {
  const entries = props.franchise.entries || []
  if (entries.length === 0) return null
  
  // Ищем онгоинг
  const ongoing = entries.find((e: any) => e.status === 'ongoing')
  if (ongoing) {
    return {
      id: ongoing.id,
      title_ru: ongoing.title_ru,
      title_en: ongoing.title_en,
      poster_url: ongoing.poster_url || ongoing.poster_image_url,
      poster_image_url: ongoing.poster_image_url,
    }
  }
  
  // Берём первое аниме
  const first = entries[0]
  if (!first) return null
  
  return {
    id: first.id,
    title_ru: first.title_ru,
    title_en: first.title_en,
    poster_url: first.poster_url || first.poster_image_url,
    poster_image_url: first.poster_image_url,
  }
})

const loadPlaylists = async () => {
  playlistsLoading.value = true
  try {
    const response = await playlistsApi.getMyPlaylists()
    playlists.value = response.data || []
  } catch (error) {
    console.error('Error loading playlists:', error)
    playlists.value = []
  } finally {
    playlistsLoading.value = false
  }
}

watch(showPlaylistModal, (newVal) => {
  if (newVal) {
    loadPlaylists()
  }
})

const checkFavorite = async () => {
  if (!props.showActions || !props.franchise?.id || !authStore.isAuthenticated) {
    return
  }
  
  try {
    const response = await playlistsApi.checkAnimeInFavorites(props.franchise.id)
    isFavorite.value = response.data.is_favorite
  } catch (error: any) {
    // Тихо игнорируем
  }
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await playlistsApi.removeFromFavorites(props.franchise.id)
      isFavorite.value = false
      toast.success('Удалено из избранного')
    } else {
      await playlistsApi.addToFavorites(props.franchise.id)
      isFavorite.value = true
      toast.success('Добавлено в избранное')
    }
    emit('favorite-toggle', isFavorite.value)
  } catch (error: any) {
    console.error('Ошибка изменения избранного:', error)
    toast.error(error.response?.data?.detail || 'Не удалось обновить избранное')
  }
}

const handleClick = () => {
  emit('click', props.franchise)
}

const onAddedToPlaylist = async (data: any) => {
  try {
    const promises = data.playlistIds.map((pid: number) =>
      playlistsApi.addItemToPlaylist(pid, {
        anime: data.animeId,
        notes: data.note || ''
      })
    )
    await Promise.all(promises)
    showPlaylistModal.value = false
    toast.success('Франшиза добавлена в плейлист!')
  } catch (error: any) {
    console.error('Ошибка добавления в плейлист:', error)
    toast.error(error.response?.data?.detail || 'Не удалось добавить в плейлист')
  }
}

const handleCreatePlaylist = () => {
  showPlaylistModal.value = false
  newPlaylistTitle.value = ''
  newPlaylistPublic.value = false
  showCreateModal.value = true
}

const saveNewPlaylist = async () => {
  if (!newPlaylistTitle.value.trim() || creatingPlaylist.value) return
  creatingPlaylist.value = true
  try {
    await playlistsApi.createPlaylist({
      title: newPlaylistTitle.value.trim(),
      visibility: newPlaylistPublic.value ? 'public' : 'private'
    })
    showCreateModal.value = false
    toast.success('Плейлист создан!')
    await loadPlaylists()
    showPlaylistModal.value = true
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Не удалось создать плейлист')
  } finally {
    creatingPlaylist.value = false
  }
}

const handleDiscuss = async () => {
  try {
    // Для франшизы используем отдельный API
    const franchiseId = props.franchise.id
    
    let discussionGroup
    try {
      discussionGroup = await animeDiscussionsApi.getFranchiseDiscussion(franchiseId)
    } catch (error: any) {
      if (error.response?.status === 404) {
        discussionGroup = await animeDiscussionsApi.joinFranchiseDiscussion(franchiseId)
      } else {
        throw error
      }
    }

    // Переходим к чату
    const chatId = discussionGroup.group?.id || discussionGroup.id
    const topicId = discussionGroup.current_topic_id
    
    if (topicId) {
      router.push(`/chats/${chatId}?topic=${topicId}`)
    } else {
      router.push(`/chats/${chatId}`)
    }
  } catch (error: any) {
    console.error('Error handling discuss:', error)
    toast.error(error.response?.data?.detail || 'Не удалось открыть обсуждение')
  }
}

const handleReminderSave = async (data: any) => {
  if (!reminderAnime.value) {
    toast.error('Нет аниме для напоминания')
    return
  }
  
  try {
    await remindersApi.createReminder({
      anime_id: reminderAnime.value.id,
      reminder_time: new Date(data.reminderTime).toISOString(),
      repeat_weekly: data.repeatWeekly || false,
      repeat_interval_days: data.repeatIntervalDays,
      end_date: data.endDate ? new Date(data.endDate).toISOString().slice(0, 10) : undefined,
      comment: data.comment || ''
    })
    toast.success('Напоминание установлено!')
    showReminderModal.value = false
  } catch (error: any) {
    console.error('Ошибка сохранения напоминания:', error)
    toast.error(error.response?.data?.error || 'Не удалось установить напоминание')
  }
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const placeholder = img.nextElementSibling as HTMLElement
  if (placeholder && placeholder.classList.contains('poster-placeholder')) {
    placeholder.style.display = 'flex'
  }
}

const previewLiveCover = () => {}
const stopLiveCoverPreview = () => {}

checkFavorite()

onUnmounted(() => {
  stopPosterRotation()
})
</script>

<style scoped>
/* ── Франшиза карточка ───────────────────────────────────── */
.franchise-card {
  position: relative;
}

/* ── Бейдж количества частей ─────────────────────────────── */
.parts-badge {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px var(--space-2);
  background: linear-gradient(135deg, var(--accent) 0%, #9333ea 100%);
  color: white;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  z-index: 6;
  box-shadow: 0 2px 8px rgba(124, 92, 252, 0.4);
}

.parts-badge svg {
  flex-shrink: 0;
}

/* ── Стрелки навигации ───────────────────────────────────── */
.poster-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 8, 9, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  opacity: 0;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.anime-card:hover .poster-nav-btn {
  opacity: 1;
}

.poster-nav-btn:hover {
  background: var(--accent);
  transform: translateY(-50%) scale(1.1);
}

.poster-nav-left {
  left: 8px;
}

.poster-nav-right {
  right: 8px;
}

.poster-nav-btn svg {
  flex-shrink: 0;
}

/* ── Переход постера ─────────────────────────────────────── */
.poster-transitioning {
  opacity: 0.5;
  transform: scale(1.02);
}

/* ── Мета информация ─────────────────────────────────────── */
.meta-highlight {
  color: var(--accent);
  font-weight: 600;
}

.status-franchise {
  color: #a855f7;
  font-weight: 600;
}

/* ── Статусная полоска франшизы ──────────────────────────── */
.status-bar-franchise {
  background: linear-gradient(90deg, var(--accent) 0%, #a855f7 100%);
}
</style>

<style>
/* ── Общие стили карточки (наследуются от AnimeCard) ─────── */
.anime-card {
  background-color: var(--surface-3);
  border-radius: var(--radius-card);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative;
  width: 100%;
  transition:
    transform var(--duration-slow) var(--ease-out),
    box-shadow var(--duration-slow) var(--ease-out),
    border-color var(--duration-slow) var(--ease-out);
}

.anime-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-default);
}

/* ── Постер ──────────────────────────────────────────────── */
.anime-poster {
  position: relative;
  width: 100%;
  padding-bottom: 140%;
  background-color: var(--surface-4);
  overflow: hidden;
}

.poster-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition:
    transform var(--duration-slow) var(--ease-out),
    filter var(--duration-slow) var(--ease-out),
    opacity 0.15s ease;
}

.anime-card:hover .poster-image {
  transform: scale(1.04);
}

.poster-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--surface-4);
  color: var(--text-tertiary);
}

/* ── Градиент ────────────────────────────────────────────── */
.poster-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(
    to top,
    rgba(8, 8, 9, 0.96) 0%,
    rgba(8, 8, 9, 0.5) 50%,
    transparent 100%
  );
  pointer-events: none;
}

/* ── Hover оверлей с кнопкой play ────────────────────────── */
.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out);
  z-index: 4;
}

.anime-card:hover .hover-overlay {
  opacity: 1;
}

/* Квадратная синяя кнопка с анимацией распыления */
.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: none;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: scale(0.6);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}

.anime-card:hover .play-btn {
  transform: scale(1);
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}

.play-btn:hover {
  transform: scale(1.15) !important;
  background: var(--accent-hover);
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.play-btn svg {
  width: 28px;
  height: 28px;
  margin-left: 4px;
}

/* ── Live cover ──────────────────────────────────────────── */
.live-cover-indicator {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  opacity: 0.5;
  transition: opacity var(--duration-base) var(--ease-out);
  z-index: 5;
}

.anime-card:hover .live-cover-indicator { opacity: 1; }

/* ── Кнопки действий ─────────────────────────────────────── */
.card-actions {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: flex;
  flex-direction: row;
  gap: var(--space-1);
  opacity: 0;
  transform: translateY(-6px);
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out);
  z-index: 10;
}

.anime-card:hover .card-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-btn {
  width: 32px;
  height: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(8, 8, 9, 0.8);
  color: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  border: none;
  backdrop-filter: blur(8px);
}

.action-btn:hover           { background-color: var(--accent); transform: scale(1.1); }
.favorite-btn               { color: var(--text-secondary); }
.favorite-btn:hover         { background-color: rgba(239,68,68,0.2); color: var(--danger); }
.discuss-btn:hover          { background-color: var(--accent); }
.playlist-btn:hover         { background-color: var(--accent-2); }
.reminder-btn:hover         { background-color: var(--warning); }

/* ── Рейтинг ─────────────────────────────────────────────── */
.score-badge {
  position: absolute;
  bottom: var(--space-2);
  left: var(--space-2);
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px var(--space-2);
  background-color: rgba(8, 8, 9, 0.88);
  color: var(--warning);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  backdrop-filter: blur(10px);
  z-index: 5;
}

/* ── Информация ──────────────────────────────────────────── */
.anime-info {
  padding: var(--space-2) var(--space-3) var(--space-3);
  background-color: var(--surface-3);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.anime-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.35;
}

.anime-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.meta-item      { font-weight: 400; }
.meta-separator { color: var(--text-tertiary); }
.meta-status    { font-weight: 500; }

/* ── Жанры ───────────────────────────────────────────────── */
.anime-genres {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.genre-tag {
  font-size: var(--text-xs);
  color: var(--accent);
  background-color: var(--accent-subtle);
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  white-space: nowrap;
  font-weight: 500;
}

.genre-more {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* ── Статусная полоска ───────────────────────────────────── */
.status-bar {
  height: 2px;
  width: 100%;
  border-radius: var(--radius-full);
  margin-top: auto;
}

/* ── Мобильная адаптация ─────────────────────────────────── */
@media (max-width: 767px) {
  .card-actions {
    opacity: 1;
    transform: translateY(0);
  }

  .action-btn {
    width: 28px;
    height: 28px;
    min-height: 28px;
  }

  .anime-title  { font-size: var(--text-sm); }
  .anime-meta   { font-size: calc(var(--text-xs) - 1px); }
  
  .parts-badge {
    font-size: 10px;
    padding: 3px 6px;
  }
  
  .poster-nav-btn {
    width: 28px;
    height: 28px;
    opacity: 1;
  }
  
  .poster-nav-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .poster-nav-left {
    left: 4px;
  }
  
  .poster-nav-right {
    right: 4px;
  }
}
</style>
