<template>
  <div 
    class="anime-card" 
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <!-- Постер аниме -->
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

      <!-- Статус в коллекции -->
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

      <!-- Прогресс просмотра -->
      <div v-if="showProgress && watchProgress > 0 && watchProgress < totalEpisodes" class="progress-bar">
        <div class="progress-fill" :style="{ width: `${(watchProgress / totalEpisodes) * 100}%` }"></div>
      </div>

      <!-- Рейтинг (левый нижний угол) -->
      <div v-if="anime.score" class="score-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span>{{ formattedScore }}</span>
      </div>
    </div>

    <!-- Информационный слой -->
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
        <span class="meta-separator" v-if="anime.episodes && anime.status">·</span>
        <span class="meta-status" :class="getStatusClass(anime.status)">
          {{ getStatusText(anime.status) }}
        </span>
      </div>

      <!-- Жанры -->
      <div v-if="showGenres && anime.genres && anime.genres.length > 0" class="anime-genres">
        <span
          v-for="(genre, index) in displayedGenres"
          :key="index"
          class="genre-tag"
          :title="anime.genres.map(g => g.name).join(', ')"
        >
          {{ genre.name }}
        </span>
        <span v-if="anime.genres.length > maxGenres" class="genre-more">
          +{{ anime.genres.length - maxGenres }}
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

      <!-- Статусная полоска -->
      <div 
        v-if="watchStatus && !showProgress" 
        class="status-bar"
        :class="`status-bar-${watchStatus}`"
      ></div>
    </div>

    <!-- Модальное окно добавления в плейлист (Teleport внутри компонента) -->
    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="anime as any"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
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

    <!-- Модальное окно напоминания (Teleport внутри компонента) -->
    <ReminderModal
      :show="showReminderModal"
      :anime="anime as any"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />
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
  genres?: Genre[]
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

// Загружаем плейлисты при открытии модального окна
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

const displayedGenres = computed(() => {
  if (!props.anime.genres) return []
  return props.anime.genres.slice(0, props.maxGenres)
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
    // Тихо игнорируем — не авторизован или нет эндпоинта
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
    // Возвращаемся к модалке выбора с обновлённым списком
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
    'released': 'Вышедший'
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

const handleDiscuss = async () => {
  try {
    // Сначала пробуем получить существующую группу
    let discussionGroup
    try {
      discussionGroup = await animeDiscussionsApi.getDiscussionGroup(props.anime.id)
    } catch (error: any) {
      // Группы нет, создаём новую
      if (error.response?.status === 404) {
        discussionGroup = await animeDiscussionsApi.createDiscussionGroup(props.anime.id)
      } else {
        throw error
      }
    }

    // Если пользователь ещё не вступил, вступаем
    if (!discussionGroup.user_joined) {
      discussionGroup = await animeDiscussionsApi.joinDiscussionGroup(props.anime.id)
    }

    // Перенаправляем в чат
    router.push(`/chat/${discussionGroup.id}`)
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
  // Пробуем разные поля для постера
  const posterImage = props.anime.poster_image_url
  const posterUrl = props.anime.poster_url
  const posterFile = props.anime.poster_file
  const poster = props.anime.poster
  
  // poster (локальный файл из БД) - приоритетный
  if (poster) {
    const url = getMediaUrl(poster)
    if (url) return url
  }
  // poster_file
  if (posterFile) {
    const url = getMediaUrl(posterFile)
    if (url) return url
  }
  // poster_image_url
  if (posterImage) {
    const url = getMediaUrl(posterImage)
    if (url) return url
  }
  // poster_url (URL Shikimori)
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
  // Placeholder для превью живой обложки
}

const stopLiveCoverPreview = () => {
  // Placeholder для остановки превью
}

checkFavorite()
</script>

<style>
/* ── AnimeCard — глобальные стили (не scoped) ─────────────── */
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
    filter var(--duration-slow) var(--ease-out);
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

/* ── Статус коллекции ────────────────────────────────────── */
.collection-status {
  position: absolute;
  bottom: var(--space-2);
  left: var(--space-2);
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(8, 8, 9, 0.85);
  color: var(--accent-2);
  border-radius: 50%;
  backdrop-filter: blur(6px);
  z-index: 5;
}

/* ── Прогресс-полоска ────────────────────────────────────── */
.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: rgba(8, 8, 9, 0.4);
  z-index: 5;
}

.progress-fill {
  height: 100%;
  background-color: var(--accent);
  transition: width var(--duration-slow) var(--ease-out);
}

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

.status-ongoing  { color: var(--accent); }
.status-finished { color: var(--text-tertiary); }
.status-announced{ color: var(--accent); }
.status-released { color: var(--accent-2); }

.meta-release-date {
  color: var(--accent);
  font-weight: 600;
}

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

/* ── Прогресс просмотра ──────────────────────────────────── */
.anime-progress {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--accent-2);
}

.progress-text { font-weight: 500; }

/* ── Статусная полоска ───────────────────────────────────── */
.status-bar {
  height: 2px;
  width: 100%;
  border-radius: var(--radius-full);
  margin-top: auto;
}

.status-bar-watching  { background-color: var(--status-watching); }
.status-bar-completed { background-color: var(--status-completed); }
.status-bar-planned   { background-color: var(--status-planned); }
.status-bar-dropped   { background-color: var(--status-dropped); }
.status-bar-onhold    { background-color: var(--status-onhold); }

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
}

/* ═══ АДАПТИВНЫЕ РАЗМЕРЫ КАРТОЧКИ ═══ */

/* xs: 320px */
@media (max-width: 374px) {
  .anime-card {
    width: 130px;
  }
  
  .anime-poster {
    padding-bottom: 140%;
  }
  
  .play-btn {
    width: 48px;
    height: 48px;
    border-radius: 8px;
  }
  
  .play-btn svg {
    width: 20px;
    height: 20px;
  }
  
  .action-btn {
    width: 24px;
    height: 24px;
    min-height: 24px;
  }
  
  .action-btn svg {
    width: 12px;
    height: 12px;
  }
  
  .score-badge {
    padding: 2px 4px;
    font-size: 10px;
  }
  
  .score-badge svg {
    width: 10px;
    height: 10px;
  }
  
  .collection-status {
    width: 22px;
    height: 22px;
  }
  
  .collection-status svg {
    width: 12px;
    height: 12px;
  }
  
  .anime-info {
    padding: 6px 8px 8px;
  }
  
  .anime-title {
    font-size: 11px;
    -webkit-line-clamp: 2;
    line-clamp: 2;
  }
  
  .anime-meta {
    font-size: 9px;
    gap: 2px;
  }
  
  .anime-genres {
    gap: 2px;
  }
  
  .genre-tag {
    font-size: 9px;
    padding: 1px 4px;
  }
  
  .genre-more {
    font-size: 9px;
  }
  
  .anime-progress {
    font-size: 9px;
  }
  
  .progress-bar {
    height: 2px;
  }
  
  .live-cover-indicator {
    width: 16px;
    height: 16px;
  }
  
  .live-cover-indicator svg {
    width: 12px;
    height: 12px;
  }
}

/* sm: 375px */
@media (min-width: 375px) and (max-width: 413px) {
  .anime-card {
    width: 140px;
  }
  
  .anime-poster {
    padding-bottom: 140%;
  }
  
  .play-btn {
    width: 56px;
    height: 56px;
  }
  
  .play-btn svg {
    width: 24px;
    height: 24px;
  }
  
  .action-btn {
    width: 26px;
    height: 26px;
    min-height: 26px;
  }
  
  .anime-title {
    font-size: 12px;
  }
  
  .anime-meta {
    font-size: 10px;
  }
  
  .genre-tag {
    font-size: 10px;
  }
}

/* md: 414px - 767px */
@media (min-width: 414px) and (max-width: 767px) {
  .anime-card {
    width: 150px;
  }
  
  .anime-poster {
    padding-bottom: 145%;
  }
  
  .play-btn {
    width: 60px;
    height: 60px;
  }
  
  .play-btn svg {
    width: 26px;
    height: 26px;
  }
  
  .action-btn {
    width: 28px;
    height: 28px;
    min-height: 28px;
  }
  
  .anime-title {
    font-size: 13px;
  }
  
  .anime-meta {
    font-size: 11px;
  }
}

/* tablet: 768px+ */
@media (min-width: 768px) {
  .anime-card {
    width: 160px;
  }
  
  .anime-poster {
    padding-bottom: 145%;
  }
  
  .anime-info {
    padding: 8px 12px 12px;
  }
  
  .anime-title {
    font-size: 14px;
  }
  
  .anime-meta {
    font-size: 12px;
  }
  
  .genre-tag {
    font-size: 11px;
  }
  
  .action-btn {
    width: 32px;
    height: 32px;
    min-height: 32px;
  }
  
  .play-btn {
    width: 64px;
    height: 64px;
    border-radius: 12px;
  }
  
  .play-btn svg {
    width: 28px;
    height: 28px;
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .anime-card {
    width: 170px;
  }
  
  .anime-poster {
    padding-bottom: 150%;
  }
  
  .anime-title {
    font-size: 15px;
  }
  
  .anime-meta {
    font-size: 13px;
  }
}

/* desktop: 1536px+ */
@media (min-width: 1536px) {
  .anime-card {
    width: 180px;
  }
  
  .anime-poster {
    padding-bottom: 150%;
  }
  
  .anime-title {
    font-size: 16px;
  }
  
  .anime-meta {
    font-size: 14px;
  }
}
</style>