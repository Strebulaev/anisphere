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

      <!-- Кнопки действий (левый верхний угол, появляются при наведении) -->
      <div v-if="showActions" class="card-actions">
        <button
          :class="['action-btn', 'favorite-btn', { active: isFavorite }]"
          @click.stop="toggleFavorite"
          :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
        <button
          class="action-btn playlist-btn"
          @click.stop="showPlaylistModal = true"
          title="Добавить в плейлист"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
        </button>
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
        <span class="meta-item" v-if="anime.episodes">
          {{ anime.episodes }} эп.
        </span>
        <span class="meta-separator">·</span>
        <span class="meta-status" :class="getStatusClass(anime.status)">
          {{ getStatusText(anime.status) }}
        </span>
      </div>

      <!-- Статусная полоска -->
      <div 
        v-if="watchStatus" 
        class="status-bar"
        :class="`status-bar-${watchStatus}`"
      ></div>
    </div>

    <!-- Модальное окно добавления в плейлист -->
    <AddToPlaylist
      v-if="showPlaylistModal"
      :anime-id="anime.id"
      @added="onAddedToPlaylist"
      @error="onPlaylistError"
      @close="showPlaylistModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import playlistsApi from '@/api/playlists'
import AddToPlaylist from './AddToPlaylist.vue'
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
  genres?: Genre[]
  poster?: any
}

interface Props {
  anime: AnimeCardProps
  showActions?: boolean
  hasLiveCover?: boolean
  watchStatus?: 'watching' | 'completed' | 'planned' | 'dropped' | 'onhold'
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
  hasLiveCover: false,
})

const emit = defineEmits<{
  click: [anime: AnimeCardProps]
  'favorite-toggle': [isFavorite: boolean]
}>()

const isFavorite = ref(false)
const showPlaylistModal = ref(false)

const formattedScore = computed(() => {
  if (props.anime.score) {
    return props.anime.score.toFixed(1)
  }
  return ''
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

const onAddedToPlaylist = (playlistId: number) => {
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
  padding-bottom: 100%;  /* <-- ИЗМЕНИТЕ ЗДЕСЬ: уменьшите до 120% или 115% чтобы сделать короче */
  background-color: var(--color-background-secondary);
  overflow: hidden;
}

.poster-image {
  position: absolute;
  top: 0;
  left: 0;
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
  left: 8px;
  display: flex;
  flex-direction: column;
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
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  color: var(--color-text);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid transparent;
}

.action-btn:hover {
  transform: scale(1.1);
}

.favorite-btn:hover {
  background-color: rgba(58, 134, 255, 0.2);
  border-color: var(--color-accent);
}

.favorite-btn.active {
  color: var(--color-accent-pink);
}

.favorite-btn.active:hover {
  background-color: rgba(255, 42, 109, 0.2);
  border-color: var(--color-accent-pink);
}

.playlist-btn:hover {
  background-color: rgba(0, 212, 170, 0.2);
  border-color: var(--color-accent-teal);
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