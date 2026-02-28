<template>
  <div 
    class="anime-card" 
    @click="handleClick"
    :class="{ 'has-live-cover': hasLiveCover }"
  >
    <!-- Постер аниме -->
    <div class="anime-poster">
      <img
        v-if="getPosterUrl()"
        :src="getPosterUrl()"
        :alt="anime.title_ru || anime.title_en || ''"
        class="poster-image"
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
          :class="['action-btn', 'favorite-btn', { active: isFavorite }]"
          @click.stop="toggleFavorite"
          :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          type="button"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
        <span class="meta-item" v-if="anime.year">
          {{ anime.year }}
        </span>
        <span class="meta-separator" v-if="anime.year && anime.type">·</span>
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

    <!-- Модальное окно добавления в плейлист -->
    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="anime as any"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="showPlaylistModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlaylistSelectModal } from '@/components/Modals'
import playlistsApi from '@/api/playlists'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import { getMediaUrl } from '@/api/client'

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

const isFavorite = ref(false)
const showPlaylistModal = ref(false)
const showReminderModal = ref(false)

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
  if (!props.showActions || !props.anime?.id) {
    return
  }
  
  try {
    const response = await playlistsApi.checkAnimeInFavorites(props.anime.id)
    isFavorite.value = response.data.is_favorite
  } catch (error: any) {
    console.error('Ошибка проверки избранного:', error)
  }
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await playlistsApi.removeFromFavorites(props.anime.id)
      isFavorite.value = false
    } else {
      await playlistsApi.addToFavorites(props.anime.id)
      isFavorite.value = true
    }
    emit('favorite-toggle', isFavorite.value)
  } catch (error) {
    console.error('Ошибка изменения избранного:', error)
  }
}

const handleClick = () => {
  emit('click', props.anime)
}

const onAddedToPlaylist = () => {
  showPlaylistModal.value = false
}

const onPlaylistError = (message: string) => {
  console.error('Ошибка добавления в плейлист:', message)
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
  showReminderModal.value = false
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
    router.push(`/chats/${discussionGroup.id}`)
  } catch (error: any) {
    console.error('Error handling discuss:', error)
    alert('Не удалось открыть обсуждение: ' + (error.response?.data?.detail || error.message))
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

const getPosterUrl = (): string | undefined => {
  const posterImage = props.anime.poster_image_url
  const posterUrl = props.anime.poster_url
  
  if (posterImage) {
    const url = getMediaUrl(posterImage)
    return url || undefined
  }
  if (posterUrl) {
    const url = getMediaUrl(posterUrl)
    return url || undefined
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
.anime-card {
  background-color: #222222;
  border-radius: var(--radius-card);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: transform 0.2s var(--transition-smooth), box-shadow 0.2s var(--transition-smooth);
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.anime-poster {
  position: relative;
  width: 100%;
  padding-bottom: 115%;  /* <-- ИЗМЕНИТЕ ЗДЕСЬ: уменьшите до 120% или 115% чтобы сделать короче */
  background-color: var(--color-background-secondary);
  overflow: hidden;
}

.poster-image {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s var(--transition-smooth), filter 0.3s var(--transition-smooth);
}

.anime-card:hover .poster-image {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.poster-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: none;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  color: var(--color-text-tertiary);
}

/* Градиентный оверлей */
.poster-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(to top, rgba(10, 10, 10, 0.95) 0%, transparent 100%);
  pointer-events: none;
}

/* Индикатор живой обложки */
.live-cover-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  opacity: 0.5;
  transition: opacity 0.2s var(--transition-smooth);
  z-index: 5;
}

.live-cover-indicator:hover {
  opacity: 1;
}

.anime-card:hover .live-cover-indicator {
  opacity: 1;
  animation: pulse-slow 1.5s infinite;
}

/* Кнопки действий */
.card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: row;
  gap: 6px;
  opacity: 0;
  transform: translateY(-10px);
  transition: opacity 0.2s var(--transition-smooth), transform 0.2s var(--transition-smooth);
  z-index: 10;
}

.anime-card:hover .card-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: none;
  backdrop-filter: blur(4px);
}

.action-btn:hover {
  background-color: var(--color-accent);
  transform: scale(1.1);
}

.favorite-btn:hover {
  background-color: rgba(58, 134, 255, 0.9);
}

.favorite-btn.active {
  color: var(--color-accent-pink);
  background-color: rgba(255, 42, 109, 0.9);
}

.favorite-btn.active:hover {
  background-color: rgba(255, 42, 109, 1);
}

.discuss-btn:hover {
  background-color: var(--color-accent-purple);
}

.playlist-btn:hover {
  background-color: var(--color-accent-teal);
}

.reminder-btn:hover {
  background-color: var(--color-accent-orange);
}

/* Статус в коллекции */
.collection-status {
  position: absolute;
  bottom: 8px;
  left: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.8);
  color: var(--color-accent-teal);
  border-radius: 50%;
  backdrop-filter: blur(4px);
  z-index: 5;
}

/* Прогресс просмотра */
.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 5;
}

.progress-fill {
  height: 100%;
  background-color: var(--color-accent);
  transition: width 0.3s var(--transition-smooth);
}

/* Рейтинг */
.score-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 4px 8px;
  background-color: rgba(10, 10, 10, 0.9);
  color: var(--color-accent-orange);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(12px);
  z-index: 5;
}

/* Информация */
.anime-info {
  padding: 8px;
  position: relative;
  background-color: #222222;
}

.anime-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.anime-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-secondary);
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.meta-item {
  font-weight: 400;
}

.meta-separator {
  color: var(--color-text-tertiary);
}

.meta-status {
  font-weight: 500;
}

.status-ongoing {
  color: var(--color-accent);
}

.status-finished {
  color: var(--color-text-secondary);
}

.status-announced {
  color: var(--color-accent);
}

.status-released {
  color: var(--color-accent-teal);
}

/* Жанры */
.anime-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.genre-tag {
  font-size: 10px;
  color: var(--color-accent);
  background-color: rgba(58, 134, 255, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
  white-space: nowrap;
  font-weight: 500;
}

.genre-more {
  font-size: 10px;
  color: var(--color-text-tertiary);
}

/* Прогресс просмотра */
.anime-progress {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 11px;
  color: var(--color-accent-teal);
}

.progress-text {
  font-weight: 500;
}

/* Статусная полоска */
.status-bar {
  height: 3px;
  width: 100%;
  border-radius: 2px;
  margin-top: 6px;
}

.status-bar-watching {
  background-color: var(--color-status-watching);
}

.status-bar-completed {
  background-color: var(--color-status-completed);
}

.status-bar-planned {
  background-color: var(--color-status-planned);
}

.status-bar-dropped {
  background-color: var(--color-status-dropped);
}

.status-bar-onhold {
  background-color: var(--color-status-onhold);
}

/* Адаптивность для мобильных */
@media (max-width: 767px) {
  .card-actions {
    opacity: 1;
    transform: translateY(0);
  }
  
  .action-btn {
    width: 28px;
    height: 28px;
  }
  
  .anime-title {
    font-size: 12px;
  }
  
  .anime-meta {
    font-size: 10px;
  }
}
</style>