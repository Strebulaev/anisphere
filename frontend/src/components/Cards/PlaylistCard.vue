<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'

interface PlaylistItem {
  id: number
  anime?: number | {
    id: number
    title_ru?: string
    title_en?: string
    poster_url?: string
  }
  anime_poster?: string | null
  anime_title?: string
}

interface Author {
  id: number
  username: string
  display_name?: string
  avatar_url?: string
  avatar?: string | null
}

interface Playlist {
  id: number
  title: string
  description?: string
  is_public?: boolean
  is_private?: boolean
  is_link_only?: boolean
  items_count: number
  likes_count?: number
  favorites_count?: number
  is_favorited?: boolean
  updated_at: string
  created_at?: string
  user?: Author
  user_id?: number
  user_username?: string
  user_avatar?: string | null
  items?: PlaylistItem[]
  cover_urls?: string[]
}

interface Props {
  playlist: Playlist
  currentUserId?: number
  isFavorite?: boolean
  maxPreviewItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  currentUserId: undefined,
  isFavorite: false,
  maxPreviewItems: 3
})

const emit = defineEmits<{
  click: [playlist: Playlist]
  favoriteToggle: [playlistId: number, isFavorite: boolean]
  share: [playlistId: number]
  edit: [playlist: Playlist]
  delete: [playlist: Playlist]
}>()

const router = useRouter()

const author = computed(() => ({
  ...props.playlist.user,
  username: props.playlist.user?.username || props.playlist.user_username || '',
  avatar_url: props.playlist.user?.avatar_url || props.playlist.user?.avatar || props.playlist.user_avatar || null
}))

const totalItems = computed(() => props.playlist.items_count || 0)
const likesCount = computed(() => props.playlist.favorites_count || props.playlist.likes_count || 0)
const isFav = computed(() => props.isFavorite || props.playlist.is_favorited || false)

const isOwner = computed(() => {
  const uid = props.playlist.user?.id || props.playlist.user_id
  return props.currentUserId && uid === props.currentUserId
})

const privacyClass = computed(() => {
  if (props.playlist.is_private) return 'privacy-private'
  if (props.playlist.is_link_only) return 'privacy-link'
  return 'privacy-public'
})

// Получаем постеры для превью
const displayItems = computed(() => {
  // Сначала пробуем из items
  if (props.playlist.items && props.playlist.items.length > 0) {
    return props.playlist.items.slice(0, props.maxPreviewItems).map(item => {
      const posterUrl = item.anime_poster ||
        (typeof item.anime === 'object' && item.anime?.poster_url) ||
        null
      const title = item.anime_title ||
        (typeof item.anime === 'object' && (item.anime?.title_ru || item.anime?.title_en)) ||
        ''
      return { posterUrl, title }
    })
  }
  // Затем из cover_urls
  if (props.playlist.cover_urls && props.playlist.cover_urls.length > 0) {
    return props.playlist.cover_urls.slice(0, props.maxPreviewItems).map((url, i) => ({
      posterUrl: url,
      title: `Аниме ${i + 1}`
    }))
  }
  return Array(Math.min(props.maxPreviewItems, 4)).fill({ posterUrl: null, title: '' })
})

const formattedUpdatedAt = computed(() => {
  const date = new Date(props.playlist.updated_at)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return 'Сегодня'
  if (days === 1) return 'Вчера'
  if (days < 7) return `${days} дн. назад`
  if (days < 30) return `${Math.floor(days / 7)} нед. назад`
  if (days < 365) return `${Math.floor(days / 30)} мес. назад`
  return `${Math.floor(days / 365)} г. назад`
})

const handleClick = () => {
  router.push(`/playlist/${props.playlist.id}`)
  emit('click', props.playlist)
}

const goToAuthor = (e: Event) => {
  e.stopPropagation()
  const uid = author.value.id
  if (uid) router.push(`/profile/${uid}`)
}

const toggleFavorite = (e: Event) => {
  e.stopPropagation()
  emit('favoriteToggle', props.playlist.id, !isFav.value)
}

const sharePlaylist = (e: Event) => {
  e.stopPropagation()
  emit('share', props.playlist.id)
}

const handleEdit = (e: Event) => {
  e.stopPropagation()
  emit('edit', props.playlist)
}

const handleDelete = (e: Event) => {
  e.stopPropagation()
  emit('delete', props.playlist)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<template>
  <div class="playlist-card" @click="handleClick">
    <!-- Обложка -->
    <div class="playlist-cover">
      <div class="cover-grid" :class="`grid-${Math.min(displayItems.length, 4)}`">
        <div v-for="(item, index) in displayItems" :key="index" class="cover-item">
          <img
            v-if="item.posterUrl"
            :src="getMediaUrl(item.posterUrl)"
            :alt="item.title"
            @error="handleImageError"
          />
          <div v-else class="cover-placeholder">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/>
              <path d="M8 12l3 3 5-5"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Overlay с кнопками -->
      <div class="cover-overlay">
        <div class="overlay-top">
          <button
            @click="toggleFavorite"
            :class="['action-btn', 'favorite-btn', { active: isFav }]"
            :title="isFav ? 'Убрать из избранного' : 'В избранное'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" :fill="isFav ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </button>

          <button
            @click="sharePlaylist"
            class="action-btn"
            title="Поделиться"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="18" cy="5" r="3"/>
              <circle cx="6" cy="12" r="3"/>
              <circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
          </button>

          <!-- Для владельца -->
          <template v-if="isOwner">
            <button @click="handleEdit" class="action-btn" title="Редактировать">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button @click="handleDelete" class="action-btn danger-btn" title="Удалить">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </template>
        </div>
      </div>

      <!-- Privacy badge -->
      <div class="privacy-badge" :class="privacyClass">
        <svg v-if="playlist.is_private" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
        <svg v-else-if="playlist.is_link_only" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
        <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
      </div>

      <!-- Счётчик аниме -->
      <div class="items-count-badge">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
        </svg>
        {{ totalItems }}
      </div>
    </div>

    <!-- Информация -->
    <div class="playlist-info">
      <h3 class="playlist-title">{{ playlist.title }}</h3>

      <div class="playlist-author" @click="goToAuthor">
        <img
          v-if="author.avatar_url"
          :src="getMediaUrl(author.avatar_url)"
          :alt="author.username"
          class="author-avatar"
          @error="(e: Event) => ((e.target as HTMLImageElement).style.display = 'none')"
        />
        <div v-else class="author-avatar-ph">
          {{ (author.username || '?')[0]?.toUpperCase() ?? '?' }}
        </div>
        <span class="author-name">@{{ author.username }}</span>
      </div>

      <div class="playlist-stats">
        <span class="stat-item">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          {{ likesCount }}
        </span>
        <span class="stat-sep">·</span>
        <span class="stat-item">{{ formattedUpdatedAt }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.playlist-card {
  background: var(--color-background-surface);
  border-radius: var(--radius-card, 0.75rem);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.22s var(--transition-smooth), box-shadow 0.22s var(--transition-smooth);
  border: 1px solid var(--color-divider-light);
}
.playlist-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover, 0 12px 32px rgba(0,0,0,0.25));
  border-color: var(--color-accent);
}

/* Cover */
.playlist-cover {
  position: relative;
  width: 100%;
  padding-bottom: 70%;
  background: var(--color-background-active);
  overflow: hidden;
}

.cover-grid {
  position: absolute;
  inset: 0;
  display: grid;
  gap: 2px;
  background: var(--color-divider);
}
.grid-1 { grid-template-columns: 1fr; grid-template-rows: 1fr; }
.grid-2 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr; }
.grid-3 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
.grid-3 .cover-item:first-child { grid-column: 1 / -1; }
.grid-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }

.cover-item {
  position: relative;
  background: var(--color-background-active);
  overflow: hidden;
}
.cover-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s var(--transition-smooth);
}
.playlist-card:hover .cover-item img { transform: scale(1.06); }
.cover-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text-tertiary);
}

/* Overlay */
.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 45%);
  opacity: 0;
  transition: opacity 0.2s;
}
.playlist-card:hover .cover-overlay { opacity: 1; }
.overlay-top {
  position: absolute;
  top: 8px; right: 8px;
  display: flex; gap: 5px;
}

.action-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.65);
  border: none; border-radius: 50%;
  color: #fff; cursor: pointer;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}
.action-btn:hover { background: var(--color-accent); transform: scale(1.1); }
.favorite-btn.active { background: rgba(245,158,11,0.9); color: #fff; }
.favorite-btn.active:hover { background: rgba(245,158,11,1); }
.danger-btn:hover { background: rgba(239,68,68,0.9) !important; }

/* Badges */
.privacy-badge {
  position: absolute;
  top: 8px; left: 8px;
  width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  backdrop-filter: blur(4px);
}
.privacy-public { background: rgba(34,197,94,0.85); color: #fff; }
.privacy-private { background: rgba(239,68,68,0.85); color: #fff; }
.privacy-link { background: rgba(58,134,255,0.85); color: #fff; }

.items-count-badge {
  position: absolute;
  bottom: 8px; left: 8px;
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px;
  background: rgba(0,0,0,0.75);
  border-radius: 4px;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  backdrop-filter: blur(4px);
}

/* Info */
.playlist-info { padding: 0.875rem; }

.playlist-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  transition: color 0.2s;
}
.playlist-card:hover .playlist-title { color: var(--color-accent); }

.playlist-author {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}
.playlist-author:hover .author-name { color: var(--color-accent); }
.author-avatar {
  width: 20px; height: 20px;
  border-radius: 50%; object-fit: cover;
}
.author-avatar-ph {
  width: 20px; height: 20px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700;
}
.author-name { font-size: 0.75rem; color: var(--color-text-secondary); font-weight: 500; }

.playlist-stats {
  display: flex; align-items: center; gap: 0.375rem;
  font-size: 0.72rem; color: var(--color-text-tertiary);
}
.stat-item { display: flex; align-items: center; gap: 0.2rem; }
.stat-sep { color: var(--color-divider-light); }
</style>
