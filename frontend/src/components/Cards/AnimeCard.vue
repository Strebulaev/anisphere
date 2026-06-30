<template>
  <div 
    class="anime-card" 
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <div class="anime-poster">
      <OptimizedImage
        v-if="getPosterUrl()"
        :src="getPosterUrl()"
        :alt="anime.title_ru || anime.title_en || ''"
        class="poster-image"
        priority
        @error="handleImageError"
      />
      <div v-else class="poster-placeholder">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <path d="M12 2v20M2 12h20"/>
        </svg>
      </div>

      <div class="poster-overlay"></div>

      <div class="hover-overlay" @click.stop="handleClick">
        <button class="play-btn" @click.stop="handleClick">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
      </div>

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

      <div v-if="watchStatus" class="collection-status">
        <svg :width="16" :height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle v-if="watchStatus === 'watching'" cx="12" cy="12" r="10"/>
          <path v-if="watchStatus === 'watching'" d="M12 6v6l4 2"/>
          <path v-if="watchStatus === 'completed'" d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline v-if="watchStatus === 'completed'" points="22 4 12 14.01 9 11.01"/>
          <circle v-if="watchStatus === 'planned'" cx="12" cy="12" r="10"/>
          <path v-if="watchStatus === 'planned'" d="M12 6v6l4 2"/>
          <path v-if="watchStatus === 'dropped'" d="M15 9l-6 6M9 9l6 6"/>
          <path v-if="watchStatus === 'onhold'" d="M10 9h4M10 13h4M10 17h4"/>
        </svg>
      </div>

      <div v-if="showProgress && watchProgress > 0 && watchProgress < totalEpisodes" class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(watchProgress / totalEpisodes) * 100}%` }"></div>
      </div>

      <div v-if="anime.score" class="score-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span>{{ formattedScore }}</span>
      </div>
    </div>

    <div class="anime-info">
      <h3 class="anime-title">{{ anime.title_ru || anime.title_en }}</h3>
      
      <div class="anime-meta">
        <!-- Дата выхода (для анонсов) -->
        <span class="meta-item meta-release-date" v-if="anime.release_date">
          {{ formatReleaseDate(anime.release_date) }}
        </span>
        <span class="meta-item" v-else-if="anime.year">
          {{ anime.year }}
        </span>
        <span class="meta-separator" v-if="(anime.release_date || anime.year) && anime.type">·</span>
        <span class="meta-item" v-if="anime.type">
          {{ getTypeLabel(anime.type) }}
        </span>
        <span class="meta-separator" v-if="anime.type && anime.episodes">·</span>
        <span class="meta-item" v-if="anime.episodes">
          {{ anime.episodes }} эп.
        </span>
      </div>

      <!-- Статус - всегда на своём месте -->
      <div class="anime-status-row">
        <span class="meta-status" :class="getStatusClass(anime.status)">
          {{ getStatusText(anime.status) }}
        </span>
      </div>

      <!-- Жанры - исправленная версия с проверкой типа -->
      <div v-if="showGenres && hasGenres" class="anime-genres">
        <span
          v-for="(genre, index) in displayedGenres"
          :key="index"
          class="genre-tag"
          :title="allGenresNames"
        >
          {{ getGenreName(genre) }}
        </span>
        <span v-if="genresCount > maxGenres" class="genre-more">
          +{{ genresCount - maxGenres }}
        </span>
      </div>

      <!-- Прогресс просмотра -->
      <div v-if="showProgress && watchProgress > 0 && watchProgress < totalEpisodes" class="anime-progress">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        <span class="progress-text">{{ watchProgress }}/{{ totalEpisodes }} эп.</span>
      </div>

      <div 
        v-if="watchStatus && !showProgress" 
        class="status-bar"
        :class="`status-bar-${watchStatus}`"
      ></div>
    </div>

    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="anime as any"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

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

    <ReminderModal
      :show="showReminderModal"
      :anime="anime as any"
      @close="showReminderModal = false"
      @save="handleReminderSave"/>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PlaylistSelectModal, ReminderModal } from '@/components/Modals'
import playlistsApi from '@/api/playlists'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import { getMediaUrl } from '@/api/client'
import { useToast } from '@/composables/useToast'
import remindersApi from '@/api/reminders'
import { useAuthStore } from '@/stores/auth'

interface Genre {
  id: number
  name: string
  slug: string
}

interface AnimeCardProps {
  id: number
  title_ru: string
  title_en: string
  title_jp?: string
  description?: string
  year?: number | null
  release_date?: string | null
  release_date_string?: string | null
  status: string
  episodes?: number | null
  score?: number | null
  poster_url?: string | null
  poster_image_url?: string | null
  poster_file?: string | null
  created_at?: string
  type?: string
  genres?: Genre[] | string[] | string | null  // Поддержка разных форматов
  poster?: any
}

interface Props {
  anime: AnimeCardProps
  showActions?: boolean
  hasLiveCover?: boolean
  watchStatus?: 'watching' | 'completed' | 'planned' | 'dropped' | 'onhold'
  watchProgress?: number
  totalEpisodes?: number
  showGenres?: boolean
  showProgress?: boolean
  maxGenres?: number
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
  hasLiveCover: false,
  watchProgress: 0,
  showGenres: true,
  showProgress: true,
  maxGenres: 2
})

const emit = defineEmits<{
  click: [anime: AnimeCardProps]
  'favorite-toggle': [isFavorite: boolean]
  'set-reminder': [animeId: number]
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

// Нормализация жанров - приводим к массиву объектов с полем name
const normalizedGenres = computed(() => {
  const genres = props.anime.genres
  
  if (!genres) return []
  if (Array.isArray(genres)) {
    if (genres.length === 0) return []
    // Если первый элемент - объект с полем name, возвращаем как есть
    if (typeof genres[0] === 'object' && genres[0] !== null && 'name' in genres[0]) {
      return genres as Genre[]
    }
    // Если массив строк, преобразуем в объекты
    if (typeof genres[0] === 'string') {
      return (genres as string[]).map(name => ({ id: 0, name, slug: '' }))
    }
    return []
  }
  // Если строка, разбиваем по запятой
  if (typeof genres === 'string') {
    return genres.split(',').map(name => ({ 
      id: 0, 
      name: name.trim(), 
      slug: '' 
    })).filter(g => g.name)
  }
  return []
})

// Проверка наличия жанров
const hasGenres = computed(() => normalizedGenres.value.length > 0)

// Количество жанров
const genresCount = computed(() => normalizedGenres.value.length)

// Отображаемые жанры (с учетом maxGenres)
const displayedGenres = computed(() => {
  return normalizedGenres.value.slice(0, props.maxGenres)
})

// Все названия жанров для tooltip
const allGenresNames = computed(() => {
  return normalizedGenres.value.map(g => getGenreName(g)).join(', ')
})

// Получение имени жанра (безопасно)
const getGenreName = (genre: any): string => {
  if (!genre) return ''
  if (typeof genre === 'string') return genre
  if (typeof genre === 'object' && genre.name) return genre.name
  return String(genre)
}

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

const formattedScore = computed(() => {
  if (props.anime.score) {
    return props.anime.score.toFixed(1)
  }
  return ''
})

const totalEpisodes = computed(() => {
  return props.totalEpisodes || props.anime.episodes || 0
})

const checkFavorite = async () => {
  if (!props.showActions || !props.anime?.id || !authStore.isAuthenticated) {
    return
  }
  
  try {
    const response = await playlistsApi.checkAnimeInFavorites(props.anime.id)
    isFavorite.value = response.data.is_favorite
  } catch (error: any) {
    // игнорируем - не авторизован или нет эндпоинта
  }
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await playlistsApi.removeFromFavorites(props.anime.id)
      isFavorite.value = false
      toast.success('Удалено из избранного')
    } else {
      await playlistsApi.addToFavorites(props.anime.id)
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
  emit('click', props.anime)
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
    toast.success('Аниме добавлено в плейлист!')
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

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'ongoing': 'Онгоинг',
    'finished': 'Завершён',
    'announced': 'Анонсирован',
    'released': 'Завершён'
  }
  return map[status] || status
}

const getTypeLabel = (type?: string) => {
  const labels: Record<string, string> = {
    tv: 'TV',
    movie: 'Фильм',
    ova: 'OVA',
    ona: 'ONA',
    special: 'Спешл'
  }
  return labels[type!.toLowerCase()] || type
}

const handleReminder = () => {
  emit('set-reminder', props.anime.id)
  showReminderModal.value = true
}

const handleReminderSave = async (data: any) => {
  try {
    await remindersApi.createReminder({
      anime_id: props.anime.id,
      reminder_time: new Date(data.reminderTime).toISOString(),
      repeat_weekly: data.repeatWeekly || false,
      repeat_interval_days: data.repeatIntervalDays,
      comment: data.comment || '',
      enable_sound: data.enableSound ?? true,
      enable_push: data.enablePush ?? true,
    })
    toast.success('Напоминание установлено!')
    showReminderModal.value = false
  } catch (error: any) {
    console.error('Ошибка сохранения напоминания:', error)
    toast.error(error.response?.data?.error || 'Не удалось установить напоминание')
  }
}

const handleDiscuss = async () => {
  try {
    let discussionGroup
    try {
      discussionGroup = await animeDiscussionsApi.getDiscussionGroup(props.anime.id)
    } catch (error: any) {
      if (error.response?.status === 404) {
        discussionGroup = await animeDiscussionsApi.createDiscussionGroup(props.anime.id)
      } else {
        throw error
      }
    }

    if (!discussionGroup.user_joined) {
      discussionGroup = await animeDiscussionsApi.joinDiscussionGroup(props.anime.id)
    }

    router.push(`/chats/${discussionGroup.id}`)
  } catch (error: any) {
    console.error('Error handling discuss:', error)
    toast.error(error.response?.data?.detail || 'Не удалось открыть обсуждение')
  }
}

const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    'ongoing': 'status-ongoing',
    'finished': 'status-finished',
    'announced': 'status-announced',
    'released': 'status-released'
  }
  return map[status] || ''
}

const formatReleaseDate = (dateStr: string | null) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const day = date.getDate()
    const month = date.toLocaleString('ru', { month: 'short' })
    const year = date.getFullYear()
    return `${day} ${month} ${year}`
  } catch {
    return dateStr
  }
}

const getPosterUrl = (): string | undefined => {
  const posterImage = props.anime.poster_image_url
  const posterUrl = props.anime.poster_url
  const posterFile = props.anime.poster_file
  const poster = props.anime.poster
  
  if (poster) {
    const url = getMediaUrl(poster)
    if (url) return url
  }
  if (posterFile) {
    const url = getMediaUrl(posterFile)
    if (url) return url
  }
  if (posterImage) {
    const url = getMediaUrl(posterImage)
    if (url) return url
  }
  if (posterUrl) {
    const url = getMediaUrl(posterUrl)
    if (url) return url
  }
  return undefined
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const placeholder = img.nextElementSibling as HTMLElement
  if (placeholder && placeholder.classList.contains('poster-placeholder')) {
    placeholder.style.display = 'flex'
  }
}

const previewLiveCover = () => {
  // превью живой обложки
}

const stopLiveCoverPreview = () => {
  // остановка превью
}

checkFavorite()
</script>

<style>
.anime-card {
  background-color: var(--surface-3);
  border-radius: var(--radius-card);
  border: 1px solid var(--border-subtle);
  overflow: hidden !important;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform var(--duration-slow) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
  width: auto;
  max-width: 100%;
}

.anime-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-default);
}
</style>

<style scoped>
.anime-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  background-color: var(--surface-4);
  overflow: hidden;
  border-radius: var(--radius-lg);
}

.poster-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.anime-card:hover .poster-image {
  transform: scale(1.05);
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

.poster-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(to top, rgba(8, 8, 9, 0.96) 0%, rgba(8, 8, 9, 0.5) 50%, transparent 100%);
  pointer-events: none;
}

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

.anime-card:hover .live-cover-indicator { 
  opacity: 1; 
}

.card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: row;
  gap: 6px;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
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
  background-color: rgba(8, 8, 9, 0.9);
  color: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  border: none;
  backdrop-filter: blur(8px);
  flex-shrink: 0;
  padding: 8px;
}

.action-btn:hover { 
  background-color: var(--accent); 
  transform: scale(1.1); 
}
.favorite-btn { 
  color: var(--text-secondary); 
}
.favorite-btn:hover { 
  background-color: rgba(239,68,68,0.2); 
  color: var(--danger); 
}
.discuss-btn:hover { 
  background-color: var(--accent); 
}
.playlist-btn:hover { 
  background-color: var(--accent-2); 
}
.reminder-btn:hover { 
  background-color: var(--warning); 
}

@media (max-width: 767px) {
  .card-actions { 
    opacity: 1 !important; 
    transform: translateY(0) !important; 
    gap: 6px;
  }
  .action-btn { 
    width: 30px; 
    height: 30px; 
    min-height: 30px;
    padding: 7px;
  }
  
  .anime-card {
    width: auto !important;
    max-width: 100% !important;
  }
  
  .anime-poster {
    width: 100% !important;
    height: auto !important;
  }
}
  
@media (max-width: 480px) {
  .card-actions {
    top: 6px;
    right: 6px;
    gap: 6px;
  }
  
  .action-btn {
    width: 28px;
    height: 28px;
    min-height: 28px;
    padding: 6px;
  }
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0, 0, 0, 0.4);
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}

.collection-status {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.7);
  color: var(--accent);
  z-index: 5;
}

.score-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  border-radius: var(--radius-sm);
  color: var(--warning);
  font-size: 12px;
  font-weight: 600;
  z-index: 5;
}

.score-badge svg {
  width: 14px;
  height: 14px;
}

.anime-info {
  padding: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.anime-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.anime-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 20px;
}

.anime-status-row {
  display: flex;
  align-items: center;
  margin-top: 4px;
  min-height: 22px;
}

.meta-item {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.meta-separator {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.meta-release-date {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.meta-status {
  font-size: 10px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  border-radius: 12px !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  line-height: 1.1 !important;
  white-space: nowrap !important;
  background: var(--surface-4) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border-subtle) !important;
}

.status-ongoing {
  background: rgba(59, 130, 246, 0.08) !important;
  color: #60a5fa !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.status-finished,
.status-released {
  background: rgba(34, 197, 94, 0.08) !important;
  color: #86efac !important;
  border-color: rgba(34, 197, 94, 0.2) !important;
}

.status-announced {
  background: rgba(168, 85, 247, 0.08) !important;
  color: #d8b4fe !important;
  border-color: rgba(168, 85, 247, 0.2) !important;
}

.status-canceled {
  background: rgba(239, 68, 68, 0.08) !important;
  color: #fca5a5 !important;
  border-color: rgba(239, 68, 68, 0.2) !important;
}

.anime-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.genre-tag {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--surface-4);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  cursor: help;
}

.genre-more {
  font-size: 10px;
  color: var(--text-tertiary);
}

.anime-progress {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.anime-progress svg {
  width: 12px;
  height: 12px;
}

.progress-text {
  font-size: 10px;
}

.status-bar {
  height: 2px;
  border-radius: 2px;
  margin-top: 4px;
}

.status-bar-watching {
  background: var(--accent);
}

.status-bar-completed {
  background: #22c55e;
}

.status-bar-planned {
  background: var(--text-tertiary);
}

.status-bar-dropped {
  background: var(--danger);
}

.status-bar-onhold {
  background: var(--warning);
}
</style>