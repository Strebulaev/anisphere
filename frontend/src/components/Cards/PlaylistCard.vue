<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'

interface PlaylistItem {
  id: number
  anime?: {
    id: number
    title_ru?: string
    title_en?: string
    poster_url?: string
  }
}

interface Author {
  id: number
  username: string
  display_name?: string
  avatar_url?: string
}

interface Playlist {
  id: number
  title: string
  description?: string
  is_public: boolean
  is_private: boolean
  is_link_only: boolean
  items_count: number
  likes_count: number
  updated_at: string
  user: Author
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

const author = computed(() => props.playlist.user || {})

const totalItems = computed(() => props.playlist.items_count || 0)
const likesCount = computed(() => props.playlist.likes_count || 0)

const isOwner = computed(() => {
  return props.currentUserId && props.playlist.user?.id === props.currentUserId
})

const isPrivate = computed(() => props.playlist.is_private)
const privacyClass = computed(() => {
  if (props.playlist.is_private) return 'privacy-private'
  if (props.playlist.is_link_only) return 'privacy-link'
  return 'privacy-public'
})

const displayItems = computed(() => {
  if (props.playlist.items && props.playlist.items.length > 0) {
    return props.playlist.items.slice(0, props.maxPreviewItems)
  }
  if (props.playlist.cover_urls && props.playlist.cover_urls.length > 0) {
    return props.playlist.cover_urls.slice(0, props.maxPreviewItems).map((url, index) => ({
      id: index,
      anime: {
        poster_url: url
      }
    }))
  }
  return Array(Math.min(props.maxPreviewItems, totalItems.value)).fill({})
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
  router.push(`/playlists/${props.playlist.id}`)
  emit('click', props.playlist)
}

const goToAuthor = () => {
  if (author.value.id) {
    router.push(`/profile/${author.value.id}`)
  }
}

const toggleFavorite = () => {
  emit('favoriteToggle', props.playlist.id, !props.isFavorite)
}

const sharePlaylist = () => {
  const url = `${window.location.origin}/playlists/${props.playlist.id}`
  navigator.clipboard.writeText(url).then(() => {
    emit('share', props.playlist.id)
  })
}

const handleEdit = () => {
  emit('edit', props.playlist)
}

const handleDelete = () => {
  emit('delete', props.playlist)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const placeholder = img.parentElement?.querySelector('.cover-placeholder') as HTMLElement
  if (placeholder) {
    placeholder.style.display = 'flex'
  }
}
</script>

<template>
  <div class="playlist-card" :class="{ private: isPrivate }">
    <div class="playlist-cover" @click="handleClick">
      <div class="cover-grid">
        <div v-for="(item, index) in displayItems" :key="index" class="cover-item">
          <img
            v-if="item.anime?.poster_url"
            :src="getMediaUrl(item.anime.poster_url)"
            :alt="item.anime.title_ru || item.anime.title_en"
            @error="handleImageError"
          />
          <div v-else class="cover-placeholder">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/>
              <path d="M12 2v20M2 12h20"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="cover-overlay">
        <div class="cover-actions">
          <button
            @click.stop="toggleFavorite"
            class="action-btn favorite-btn"
            :class="{ active: isFavorite }"
            :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
          </button>

          <button
            @click.stop="sharePlaylist"
            class="action-btn share-btn"
            title="Поделиться"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="18" cy="5" r="3"/>
              <circle cx="6" cy="12" r="3"/>
              <circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="privacy-badge" :class="privacyClass">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>

      <div class="items-count">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
        </svg>
        <span>{{ totalItems }}</span>
      </div>
    </div>

    <div class="playlist-info">
      <h3 class="playlist-title" @click="handleClick" :title="playlist.title">
        {{ playlist.title }}
      </h3>

      <div class="playlist-author" @click="goToAuthor">
        <img
          v-if="author.avatar_url"
          :src="getMediaUrl(author.avatar_url)"
          :alt="author.display_name || author.username"
          class="author-avatar"
        />
        <div v-else class="author-avatar-placeholder">
          {{ (author.display_name || author.username)?.[0]?.toUpperCase() }}
        </div>
        <span class="author-name">{{ author.display_name || author.username }}</span>
      </div>

      <div class="playlist-stats">
        <span class="stat-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          {{ likesCount }}
        </span>
        <span class="stat-separator">·</span>
        <span class="stat-item">
          {{ formattedUpdatedAt }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.playlist-card {
  background-color: #222222;
  border-radius: var(--radius-card);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s var(--transition-smooth), box-shadow 0.2s var(--transition-smooth);
}

.playlist-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.playlist-cover {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  background-color: var(--color-background-secondary);
  overflow: hidden;
}

.cover-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 2px;
  background-color: var(--color-divider);
}

.cover-item {
  position: relative;
  background-color: var(--color-background-surface);
  overflow: hidden;
}

.cover-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s var(--transition-smooth);
}

.playlist-card:hover .cover-item img {
  transform: scale(1.05);
}

.cover-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.2s var(--transition-smooth);
}

.playlist-card:hover .cover-overlay {
  opacity: 1;
}

.cover-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 6px;
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

.favorite-btn.active {
  color: var(--color-accent-pink);
  background-color: rgba(255, 42, 109, 0.9);
}

.favorite-btn.active:hover {
  background-color: rgba(255, 42, 109, 1);
}

.share-btn:hover {
  background-color: var(--color-accent-teal);
}

.privacy-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  backdrop-filter: blur(4px);
}

.privacy-badge.privacy-private {
  background-color: rgba(255, 42, 109, 0.9);
  color: white;
}

.privacy-badge.privacy-link {
  background-color: rgba(58, 134, 255, 0.9);
  color: white;
}

.privacy-badge.privacy-public {
  background-color: rgba(0, 212, 170, 0.9);
  color: white;
}

.items-count {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 4px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.playlist-info {
  padding: 12px;
}

.playlist-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  cursor: pointer;
}

.playlist-title:hover {
  color: var(--color-accent);
}

.playlist-author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.author-avatar-placeholder {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-accent);
  color: white;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
}

.author-name {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.playlist-author:hover .author-name {
  color: var(--color-accent);
}

.playlist-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-separator {
  color: var(--color-divider-light);
}

@media (max-width: 640px) {
  .action-btn {
    width: 32px;
    height: 32px;
  }

  .playlist-title {
    font-size: 13px;
  }
}
</style>