<template>
  <div class="post-card" :class="{ pinned: post.is_pinned }">
    <!-- Pin indicator -->
    <div v-if="post.is_pinned" class="pinned-badge">
      📌 Закреплён
    </div>

    <!-- Post Header -->
    <div class="post-header">
      <div class="author-info" @click.stop="goToProfile">
        <img
          :src="post.author_avatar || defaultAvatar"
          :alt="post.author_username"
          class="avatar"
        >
        <div class="author-details">
          <div class="author-name">
            <span class="display-name">{{ post.author_display_name || post.author_username }}</span>
            <span v-if="post.author_display_name" class="username">@{{ post.author_username }}</span>
          </div>
          <div class="post-meta">
            <span v-if="post.group" class="group-badge">
              📁 {{ post.group.name }}
            </span>
            <span class="time">{{ formatTime(post.created_at) }}</span>
            <span v-if="post.edited_at" class="edited">(ред.)</span>
          </div>
        </div>
      </div>

      <button class="menu-btn" @click.stop="$emit('menu', post)">
        ⋯
      </button>
    </div>

    <!-- Post Content -->
    <div class="post-content">
      <!-- Title -->
      <h3 v-if="post.title" class="post-title">{{ post.title }}</h3>

      <!-- Text Content -->
      <div class="post-text" :class="{ collapsed: isTextCollapsed }">
        <p v-html="formattedText"></p>
        <button
          v-if="shouldShowExpandText"
          @click.stop="isTextCollapsed = !isTextCollapsed"
          class="expand-btn"
        >
          {{ isTextCollapsed ? 'Показать полностью' : 'Свернуть' }}
        </button>
      </div>

      <!-- Hashtags -->
      <div v-if="post.hashtags?.length" class="hashtags">
        <span
          v-for="hashtag in post.hashtags"
          :key="hashtag"
          class="hashtag"
          @click.stop="searchByTag(hashtag)"
        >
          #{{ hashtag }}
        </span>
      </div>

      <!-- Media Gallery -->
      <div v-if="hasMedia" class="media-gallery" :class="mediaGridClass">
        <div
          v-for="(media, index) in displayMedia"
          :key="index"
          class="media-item"
          @click.stop="openMediaViewer(index)"
        >
          <img
            v-if="media.type === 'image'"
            :src="media.url"
            :alt="media.caption || 'Изображение'"
          >
          <video
            v-else-if="media.type === 'video'"
            :src="media.url"
            :poster="media.thumbnail"
          ></video>
          <div v-if="media.type === 'video'" class="play-icon">▶</div>
          <span v-if="media.caption" class="media-caption">{{ media.caption }}</span>
        </div>
      </div>

      <!-- Single Image -->
      <div v-else-if="post.image_url" class="single-media">
        <img
          :src="post.image_url"
          alt="Изображение поста"
          @click.stop="openMediaViewer(0)"
        >
      </div>

      <!-- Single Video -->
      <div v-else-if="post.video_url" class="single-media video">
        <video
          :src="post.video_url"
          controls
          preload="metadata"
        ></video>
      </div>

      <!-- Anime Card -->
      <div v-if="post.anime" class="anime-card" @click.stop="goToAnime">
        <img
          :src="post.anime.poster_url"
          :alt="post.anime.title_ru"
          class="anime-poster"
        >
        <div class="anime-info">
          <span class="anime-title">{{ post.anime.title_ru }}</span>
          <span v-if="post.anime.title_en" class="anime-title-en">{{ post.anime.title_en }}</span>
          <div v-if="post.anime_rating" class="anime-rating">
            <span class="rating-label">Оценка автора:</span>
            <span class="rating-value">{{ post.anime_rating }}/10</span>
          </div>
          <button class="btn-add-collection">Добавить в коллекцию</button>
        </div>
      </div>

      <!-- Playlist Card -->
      <div v-if="post.playlist" class="playlist-card" @click.stop="goToPlaylist">
        <div class="playlist-preview">
          <div
            v-for="(anime, idx) in post.playlist.anime?.slice(0, 3)"
            :key="idx"
            class="preview-item"
          >
            <img :src="anime.poster_url" :alt="anime.title_ru">
          </div>
        </div>
        <div class="playlist-info">
          <span class="playlist-title">{{ post.playlist.title }}</span>
          <span class="playlist-count">{{ post.playlist.anime_count }} аниме</span>
        </div>
        <button class="btn-playlist">Открыть плейлист</button>
      </div>

      <!-- Shorts/Reactor Card -->
      <div v-if="post.reactor_post" class="shorts-card" @click.stop="goToShorts">
        <div class="shorts-preview">
          <video :src="post.reactor_post.video_url" muted></video>
          <span class="duration-badge">{{ formatDuration(post.reactor_post.duration) }}</span>
        </div>
        <div class="shorts-info">
          <span class="shorts-title">{{ post.reactor_post.title }}</span>
          <span class="shorts-author">@{{ post.reactor_post.user?.username }}</span>
          <div class="shorts-stats">
            <span>❤️ {{ formatCount(post.reactor_post.likes_count) }}</span>
            <span>💬 {{ formatCount(post.reactor_post.comments_count) }}</span>
          </div>
        </div>
        <button class="btn-shorts">Смотреть в Reactor</button>
      </div>

      <!-- System Post -->
      <div v-if="post.post_type === 'system'" class="system-post">
        <div class="system-icon">
          <span v-if="post.system_type === 'level_up'">🎉</span>
          <span v-else-if="post.system_type === 'contest_win'">🏆</span>
          <span v-else-if="post.system_type === 'contest_participation'">🎯</span>
          <span v-else-if="post.system_type === 'group_created'">👥</span>
          <span v-else-if="post.system_type === 'contest_started'">🏁</span>
          <span v-else-if="post.system_type === 'achievement_unlocked'">🏅</span>
          <span v-else>📢</span>
        </div>
        <span class="system-text">{{ post.text }}</span>
      </div>

      <!-- Repost -->
      <div v-if="post.post_type === 'repost' && post.original_post" class="repost-content">
        <div class="repost-header">
          <img
            :src="post.original_post.author_avatar || defaultAvatar"
            class="repost-avatar"
          >
          <span class="repost-author">
            {{ post.original_post.author_display_name || post.original_post.author_username }}
          </span>
        </div>
        <div class="repost-text" v-if="post.repost_comment">
          {{ post.repost_comment }}
        </div>
        <PostCard
          :post="post.original_post"
          :is-repost="true"
          @menu="$emit('menu', $event)"
        />
      </div>

      <!-- Spoiler Warning -->
      <div v-if="post.is_spoiler" class="spoiler-warning">
        <span>⚠️ Спойлер</span>
        <button @click.stop="revealSpoiler" class="btn-reveal">
          Показать
        </button>
      </div>
    </div>

    <!-- Post Actions -->
    <div class="post-actions">
      <div class="action-group">
        <button
          @click.stop="handleLike"
          class="action-btn"
          :class="{ active: post.is_liked, liked: post.is_liked }"
        >
          <span class="icon">{{ post.is_liked ? '❤️' : '🤍' }}</span>
          <span class="count">{{ formatCount(post.likes_count) }}</span>
        </button>

        <button
          @click.stop="handleDislike"
          class="action-btn"
          :class="{ active: post.is_disliked, disliked: post.is_disliked }"
        >
          <span class="icon">{{ post.is_disliked ? '👎' : '👍' }}</span>
          <span class="count">{{ formatCount(post.dislikes_count) }}</span>
        </button>
      </div>

      <div class="action-group">
        <button @click.stop="$emit('comment', post)" class="action-btn">
          <span class="icon">💬</span>
          <span class="count">{{ formatCount(post.comments_count) }}</span>
        </button>

        <button @click.stop="$emit('repost', post)" class="action-btn">
          <span class="icon">🔁</span>
          <span class="count">{{ formatCount(post.reposts_count) }}</span>
        </button>
      </div>

      <div class="action-group">
        <button @click.stop="$emit('share', post)" class="action-btn">
          <span class="icon">📤</span>
        </button>

        <button
          @click.stop="$emit('bookmark', post)"
          class="action-btn"
          :class="{ active: post.is_bookmarked }"
        >
          <span class="icon">{{ post.is_bookmarked ? '⭐' : '☆' }}</span>
        </button>
      </div>
    </div>

    <!-- Comments Preview -->
    <div v-if="showCommentsPreview && post.comments_count > 0" class="comments-preview">
      <div class="preview-comment" @click.stop="$emit('comment', post)">
        <span class="comment-text">Посмотреть комментарии ({{ post.comments_count }})</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { FeedPost, MediaFile } from '@/api/feed'

// shape used internally for template rendering (includes 'type' field)
interface MediaItem {
  type: 'image' | 'video'
  url: string
  thumbnail?: string
  caption?: string
}

// extend API type with a few additional frontend-only props
type Post = FeedPost & {
  image_file: string | null
  video_file: string | null
  is_following: boolean
}

const props = defineProps<{
  post: Post
  isRepost?: boolean
  showCommentsPreview?: boolean
}>()

const emit = defineEmits<{
  like: [post: any]
  dislike: [post: any]
  comment: [post: any]
  repost: [post: any]
  share: [post: any]
  bookmark: [post: any]
  menu: [post: any]
  report: [post: any]
}>()

const router = useRouter()

const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`
const isTextCollapsed = ref(true)
const isSpoilerRevealed = ref(false)

// Computed
const hasMedia = computed(() => {
  return props.post.media_files?.length > 0
})

const displayMedia = computed<MediaItem[]>(() => {
  if (!props.post.media_files) return []
  // convert backend MediaFile objects to MediaItem with `type` field
  return props.post.media_files.slice(0, 10).map((m: MediaFile) => ({
    type: m.media_type,
    url: m.url,
    thumbnail: m.thumbnail,
    caption: m.caption,
  }))
})

const mediaGridClass = computed(() => {
  const count = displayMedia.value.length
  if (count === 1) return 'grid-1'
  if (count === 2) return 'grid-2'
  if (count === 3) return 'grid-3'
  if (count === 4) return 'grid-4'
  return 'grid-many'
})

const shouldShowExpandText = computed(() => {
  return props.post.text && props.post.text.length > 500
})

const formattedText = computed(() => {
  let text = props.post.text || ''

  // Replace hashtags with links
  text = text.replace(/#(\w+)/g, '<span class="hashtag-link" data-tag="$1">#$1</span>')

  // Replace mentions with links
  text = text.replace(/@(\w+)/g, '<span class="mention-link" data-user="$1">@$1</span>')

  // Replace URLs with links
  text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>')

  // Format bold
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Format italic
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>')

  return text
})

// Methods
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин.`
  if (hours < 24) return `${hours} ч.`
  if (days < 7) return `${days} дн.`

  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short'
  })
}

const formatCount = (count: number | undefined): string => {
  if (count === undefined || count === null) return '0'
  if (count >= 1000000) {
    return (count / 1000000).toFixed(1) + 'М'
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'К'
  }
  return count.toString()
}

const handleLike = () => {
  emit('like', props.post)
}

const handleDislike = () => {
  emit('dislike', props.post)
}

const goToProfile = () => {
  router.push(`/profile/${props.post.author_username}`)
}

const goToAnime = () => {
  if (props.post.anime) {
    router.push(`/anime/${props.post.anime.id}`)
  }
}

const goToPlaylist = () => {
  if (props.post.playlist) {
    router.push(`/playlist/${props.post.playlist.id}`)
  }
}

const goToShorts = () => {
  if (props.post.reactor_post) {
    router.push(`/reactor/post/${props.post.reactor_post.id}`)
  }
}

const formatDuration = (seconds: number | undefined): string => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const searchByTag = (tag: string) => {
  router.push(`/search?tag=${tag}`)
}

const openMediaViewer = (index: number) => {
  // Open media viewer modal
}

const revealSpoiler = () => {
  isSpoilerRevealed.value = true
}
</script>

<style scoped>
.post-card {
  background: #111;
  border-radius: 12px;
  padding: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.post-card.pinned {
  border: 1px solid #667eea;
}

.pinned-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  display: inline-block;
  margin-bottom: 0.75rem;
}

/* Header */
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.author-info {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.author-details {
  display: flex;
  flex-direction: column;
}

.author-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.display-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
}

.username {
  color: #666;
  font-size: 0.85rem;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.group-badge {
  background: #1a1a1a;
  color: #888;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.time {
  color: #666;
  font-size: 0.85rem;
}

.edited {
  color: #555;
  font-size: 0.75rem;
  font-style: italic;
}

.menu-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.menu-btn:hover {
  background: #1a1a1a;
  color: #fff;
}

/* Content */
.post-content {
  margin-bottom: 1rem;
}

.post-title {
  color: #fff;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.post-text {
  color: #ddd;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.post-text.collapsed {
  max-height: 150px;
  overflow: hidden;
  position: relative;
}

.post-text.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: linear-gradient(transparent, #111);
}

.expand-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}

.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.hashtag {
  color: #667eea;
  cursor: pointer;
  transition: color 0.2s;
}

.hashtag:hover {
  color: #8b9ef5;
}

/* Media */
.media-gallery {
  display: grid;
  gap: 0.25rem;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.media-gallery.grid-1 {
  grid-template-columns: 1fr;
}

.media-gallery.grid-2 {
  grid-template-columns: 1fr 1fr;
}

.media-gallery.grid-3 {
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.media-gallery.grid-3 .media-item:first-child {
  grid-row: span 2;
}

.media-gallery.grid-4 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.media-gallery.grid-many {
  grid-template-columns: repeat(3, 1fr);
}

.media-item {
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.media-item:hover img,
.media-item:hover video {
  transform: scale(1.05);
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.media-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem;
  font-size: 0.85rem;
}

.single-media {
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.single-media img,
.single-media video {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
  background: #000;
}

/* Anime Card */
.anime-card {
  display: flex;
  gap: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  margin-bottom: 0.75rem;
  transition: background 0.2s;
}

.anime-card:hover {
  background: #222;
}

.anime-poster {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 4px;
}

.anime-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.anime-title {
  color: #fff;
  font-weight: 600;
}

.anime-title-en {
  color: #666;
  font-size: 0.85rem;
}

.anime-rating {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.rating-label {
  color: #666;
  font-size: 0.8rem;
}

.rating-value {
  color: #667eea;
  font-weight: 600;
}

.btn-add-collection {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s;
}

.btn-add-collection:hover {
  background: #5a6fd6;
}

/* Playlist Card */
.playlist-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  margin-bottom: 0.75rem;
}

.playlist-preview {
  display: flex;
  gap: 0.25rem;
}

.preview-item img {
  width: 40px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
}

.playlist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.playlist-title {
  color: #fff;
  font-weight: 600;
}

.playlist-count {
  color: #666;
  font-size: 0.85rem;
}

.btn-playlist {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
}

/* Shorts Card */
.shorts-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  margin-bottom: 0.75rem;
  transition: background 0.2s;
}

.shorts-card:hover {
  background: #222;
}

.shorts-preview {
  position: relative;
  width: 80px;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
  flex-shrink: 0;
}

.shorts-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.duration-badge {
  position: absolute;
  bottom: 0.25rem;
  right: 0.25rem;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 0.7rem;
  padding: 0.125rem 0.25rem;
  border-radius: 4px;
}

.shorts-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.shorts-title {
  color: #fff;
  font-weight: 600;
}

.shorts-author {
  color: #666;
  font-size: 0.85rem;
}

.shorts-stats {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.shorts-stats span {
  color: #888;
  font-size: 0.8rem;
}

.btn-shorts {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
}

/* System Post */
.system-post {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.75rem;
}

.system-icon {
  font-size: 2rem;
}

.system-text {
  color: #ddd;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* Repost */
.repost-content {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.repost-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.repost-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.repost-author {
  color: #888;
  font-size: 0.85rem;
}

.repost-text {
  color: #ddd;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

/* Spoiler */
.spoiler-warning {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #2a2a1a;
  border: 1px solid #665500;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.spoiler-warning span {
  color: #ffcc00;
}

.btn-reveal {
  background: #665500;
  color: white;
  border: none;
  padding: 0.4rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}

/* Actions */
.post-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid #1f1f1f;
}

.action-group {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: none;
  border: none;
  color: #666;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.action-btn:hover {
  background: #1a1a1a;
  color: #888;
}

.action-btn.active {
  color: #667eea;
}

.action-btn.liked {
  color: #ef4444;
}

.action-btn.disliked {
  color: #f59e0b;
}

.action-btn .icon {
  font-size: 1.1rem;
}

.action-btn .count {
  font-size: 0.85rem;
}

/* Comments Preview */
.comments-preview {
  padding-top: 0.75rem;
  border-top: 1px solid #1f1f1f;
}

.preview-comment {
  color: #666;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.preview-comment:hover {
  background: #1a1a1a;
}

.comment-text {
  font-size: 0.9rem;
}
</style>
