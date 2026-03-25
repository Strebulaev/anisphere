<template>
  <div class="post-card" :class="{ pinned: post.is_pinned }">
    <!-- Pin indicator -->
    <div v-if="post.is_pinned" class="pinned-badge">📌 Закреплён</div>

    <!-- Header -->
    <div class="post-header">
      <div class="author-info" @click.stop="goToProfile">
        <OptimizedImage :src="post.author_avatar || defaultAvatar" class="avatar" alt="" />
        <div class="author-details">
          <div class="author-name">
            <span class="display-name">{{ post.author_display_name || post.author_username }}</span>
            <span v-if="post.author_display_name" class="username">@{{ post.author_username }}</span>
          </div>
          <div class="post-meta">
            <span v-if="post.group" class="group-badge">📁 {{ post.group.name }}</span>
            <span class="time">{{ formatTime(post.created_at) }}</span>
            <span v-if="post.edited_at" class="edited">(ред.)</span>
            <span class="visibility-badge">{{ visibilityIcon(post.visibility) }}</span>
          </div>
        </div>
      </div>
      <button class="menu-btn" @click.stop="$emit('menu', post)">⋯</button>
    </div>

    <!-- Content -->
    <div class="post-content">
      <h3 v-if="post.title" class="post-title">{{ post.title }}</h3>

      <!-- Spoiler Banner - показываем ВСЕГДА если is_spoiler -->
      <div v-if="post.is_spoiler" class="spoiler-banner" :class="{ revealed: spoilerRevealed }">
        <div class="spoiler-banner-left">
          <div class="spoiler-icon-wrap">
            <svg class="spoiler-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="spoiler-meta">
            <span class="spoiler-label">Спойлер</span>
            <span v-if="spoilerText" class="spoiler-subject">{{ spoilerText }}</span>
          </div>
        </div>
        <button 
          v-if="!spoilerRevealed" 
          class="spoiler-reveal-btn" 
          @click.stop="spoilerRevealed = true"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          <span>Показать</span>
        </button>
        <button 
          v-else 
          class="spoiler-hide-btn" 
          @click.stop="spoilerRevealed = false"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
          <span>Скрыть</span>
        </button>
      </div>

      <!-- Content - скрыт если is_spoiler и не раскрыт -->
      <div v-if="!post.is_spoiler || spoilerRevealed" class="post-body" :class="{ 'has-spoiler': post.is_spoiler }">
        <!-- Text с возможностью разворачивания (без модального) -->
        <div v-if="post.text" class="post-text-wrap">
          <div
            class="post-text"
            :class="{ 'is-collapsed': isCollapsed && isLong }"
            v-html="formattedText"
          ></div>
          <button v-if="isLong" class="expand-btn" @click.stop="isCollapsed = !isCollapsed">
            {{ isCollapsed ? '▼ Показать полностью' : '▲ Свернуть' }}
          </button>
        </div>

        <!-- Hashtags -->
        <div v-if="post.hashtags?.length" class="hashtags">
          <span v-for="tag in post.hashtags" :key="tag" class="hashtag" @click.stop="$router.push('/search?tag='+tag)">#{{ tag }}</span>
        </div>

        <!-- Media Gallery -->
        <div v-if="hasMedia" class="media-gallery" :class="'grid-' + Math.min(displayMedia.length, 4)">
          <div v-for="(m, i) in displayMedia" :key="i" class="media-item" @click.stop="openMedia(i)">
            <OptimizedImage v-if="m.type === 'image'" :src="m.url" :alt="m.caption || ''" layout="fullWidth" />
            <video v-else :src="m.url" :poster="m.thumbnail" controls preload="metadata"></video>
          </div>
        </div>
        <div v-else-if="post.image_url" class="single-media"><OptimizedImage :src="post.image_url" alt="" layout="fullWidth" @click.stop /></div>
        <div v-else-if="post.video_url" class="single-media"><video :src="post.video_url" controls preload="metadata"></video></div>

        <!-- Anime Card -->
        <div v-if="post.anime" class="anime-card" @click.stop="$router.push('/anime/'+post.anime.id)">
          <div class="anime-poster-wrap">
            <OptimizedImage 
              v-if="getPosterUrl(post.anime)"
              :src="getPosterUrl(post.anime) || post.anime.poster_url"
              class="anime-poster" 
              alt="poster"
              @error="onPosterError($event, post.anime)"
            >
            </OptimizedImage>

            <div v-else class="anime-poster-placeholder">🎬</div>
          </div>
          <div class="anime-info">
            <span class="anime-title">{{ post.anime.title_ru || post.anime.title_en || 'Название не известно' }}</span>
            <span v-if="shouldShowEnglishTitle(post.anime)" class="anime-title-en">{{ post.anime.title_en }}</span>
            <span v-if="post.anime.year" class="anime-year">{{ post.anime.year }}</span>
            <span v-if="post.anime_rating" class="anime-rating">⭐ {{ post.anime_rating }}/10</span>
            <span v-if="post.anime.description" class="anime-desc">{{ truncateText(post.anime.description, 150) }}</span>
          </div>
        </div>

        <!-- Playlist Card -->
        <div v-if="post.playlist && post.playlist.id" class="playlist-card" @click.stop="goToPlaylist(post.playlist)">
          <div class="playlist-poster-wrap">
            <OptimizedImage
              v-if="getPosterUrl(post.playlist)"
              :src="getPosterUrl(post.playlist)"
              class="playlist-poster"
              alt="poster"
              @error="onPlaylistPosterError($event)"
            >
            </OptimizedImage>
            <div v-else class="playlist-poster-placeholder">📁</div>
          </div>
          <div class="playlist-info">
            <span class="playlist-title">{{ post.playlist.title || 'Плейлист' }}</span>
            <span v-if="post.playlist.description" class="playlist-desc">{{ truncateText(post.playlist.description, 80) }}</span>
            <span class="playlist-count">{{ post.playlist.anime_count || post.playlist.items_count || 0 }} аниме</span>
          </div>
          <span class="playlist-arrow">›</span>
        </div>

        <!-- Reactor/Shorts Card -->
        <div v-if="post.reactor_post" class="shorts-card" @click.stop="$router.push('/reactor/post/'+post.reactor_post.id)">
          <div class="shorts-thumb">
            <video :src="post.reactor_post.video_url" muted></video>
          </div>
          <div class="shorts-info">
            <span class="shorts-title">{{ post.reactor_post.title }}</span>
            <span class="shorts-author">@{{ post.reactor_post.user?.username }}</span>
          </div>
        </div>

        <!-- Repost -->
        <div v-if="post.post_type === 'repost' && post.original_post" class="repost-wrap">
          <PostCard :post="(post.original_post as any)" :is-repost="true" @menu="$emit('menu', $event)" />
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="post-actions">
      <div class="action-group">
        <button class="action-btn" :class="{ liked: post.is_liked }" @click.stop="$emit('like', post)">
          {{ post.is_liked ? '❤️' : '🤍' }} <span>{{ fmt(post.likes_count) }}</span>
        </button>
        <button class="action-btn" :class="{ disliked: post.is_disliked }" @click.stop="$emit('dislike', post)">
          {{ post.is_disliked ? '👎' : '👎🏻' }} <span>{{ fmt(post.dislikes_count) }}</span>
        </button>
      </div>
      <div class="action-group">
        <button class="action-btn" @click.stop="toggleComments">
          💬 <span>{{ fmt(post.comments_count) }}</span>
        </button>
        <button class="action-btn" @click.stop="$emit('repost', post)">
          🔁 <span>{{ fmt(post.reposts_count) }}</span>
        </button>
      </div>
      <div class="action-group">
        <button class="action-btn" @click.stop="$emit('share', post)">📤</button>
        <button class="action-btn" :class="{ bookmarked: post.is_bookmarked }" @click.stop="$emit('bookmark', post)">
          {{ post.is_bookmarked ? '⭐' : '☆' }}
        </button>
      </div>
    </div>

    <!-- ── Inline Comments (древовидные) ── -->
    <div v-if="showComments" class="inline-comments" @click.stop>
      <div v-if="commentsLoading" class="comments-loading"><div class="spinner-sm"></div></div>

      <div v-else class="comments-tree">
        <div v-if="rootComments.length === 0" class="no-comments">Пока нет комментариев</div>
        <template v-else>
          <CommentThreadNode
            v-for="c in rootComments"
            :key="c.id"
            :comment="c"
            :all-comments="allComments"
            :post-id="post.id"
            @reply-added="onReplyAdded"
          />
        </template>
      </div>

      <!-- New comment input -->
      <div class="comment-input-row">
        <OptimizedImage :src="defaultAvatar" class="ci-avatar" alt="" />
        <div class="ci-wrap">
          <textarea
            v-model="newCommentText"
            placeholder="Написать комментарий..."
            class="comment-textarea"
            rows="2"
            @keydown.ctrl.enter="submitComment"
          ></textarea>
          <button class="send-comment-btn" :disabled="!newCommentText.trim() || sendingComment" @click="submitComment">
            {{ sendingComment ? '...' : 'Отправить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { FeedPost, MediaFile } from '@/api/feed'
import { commentsApi } from '@/api/feed'
import { normalizeComment } from '@/utils/normalizers'
import { getMediaUrl } from '@/api/client'
import CommentThreadNode from '@/components/feed/CommentThreadNode.vue'

type Post = FeedPost & { image_file?: string | null; video_file?: string | null; is_following?: boolean }

const props = defineProps<{ post: Post; isRepost?: boolean; showCommentsPreview?: boolean }>()
const emit = defineEmits<{
  like: [post: Post]; dislike: [post: Post]; comment: [post: Post]
  repost: [post: Post]; share: [post: Post]; bookmark: [post: Post]; menu: [post: Post]
}>()

const router = useRouter()
const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3C/svg%3E`

// Debug: логируем данные об аниме
watch(() => props.post.anime, (anime) => {
  if (anime) {
    // console.log('Anime in post:', { id, title_ru, poster, poster_url })
  }
}, { immediate: true })

// ── Text expand ──────────────────────────────────────
const TEXT_LIMIT = 1000  // Увеличено ещё больше для лучшей видимости текста
const isCollapsed = ref(true)
const isLong = computed(() => (props.post.text || '').length > TEXT_LIMIT)
const spoilerRevealed = ref(false)

const formattedText = computed(() => {
  let t = props.post.text || ''
  t = t.replace(/#(\w+)/g, '<span class="ht">#$1</span>')
  t = t.replace(/@(\w+)/g, '<span class="mn">@$1</span>')
  t = t.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
  t = t.replace(/\n/g, '<br>')
  return t
})

// ── Media ────────────────────────────────────────────
interface MediaItem { type: 'image'|'video'; url: string; thumbnail?: string; caption?: string }
const hasMedia = computed(() => (props.post.media_files?.length ?? 0) > 0)
const displayMedia = computed<MediaItem[]>(() =>
  (props.post.media_files || []).slice(0, 10).map((m: MediaFile) => ({
    type: m.media_type,
    url: (m.file_url || m.url || '') as string,
    thumbnail: (m.thumbnail_url || m.thumbnail) as string | undefined,
    caption: m.caption as string | undefined,
  }))
)
const openMedia = (_idx: number) => {}

// ── Helpers ──────────────────────────────────────────
const fmt = (n?: number) => {
  if (!n) return '0'
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'М'
  if (n >= 1e3) return (n/1e3).toFixed(1) + 'К'
  return String(n)
}

const formatTime = (s: string) => {
  const d = new Date(s), now = Date.now(), diff = now - d.getTime()
  const m = Math.floor(diff/60000), h = Math.floor(diff/3600000), days = Math.floor(diff/86400000)
  if (m < 1) return 'только что'
  if (m < 60) return m + ' мин.'
  if (h < 24) return h + ' ч.'
  if (days < 7) return days + ' дн.'
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const visibilityIcon = (v?: string) => {
  const map: Record<string, string> = { public: '🌍', followers: '👥', friends: '👫', private: '🔒' }
  return map[v || 'public'] || '🌍'
}

const goToProfile = () => router.push(`/profile/${props.post.author_username}`)

const goToPlaylist = (playlist: any) => {
  if (playlist && playlist.id) {
    router.push(`/playlist/${playlist.id}`)
  }
}

// Получить заголовок спойлера
const getSpoilerTitle = (spoilerFor: any): string => {
  if (!spoilerFor) return ''
  if (typeof spoilerFor === 'string') return spoilerFor
  if (typeof spoilerFor === 'object') {
    return spoilerFor.title_ru || spoilerFor.title_en || ''
  }
  return ''
}

// Текст описания спойлера
const spoilerText = computed(() => {
  return props.post.spoiler_description || getSpoilerTitle(props.post.spoiler_for) || ''
})

// Функция для обрезания текста
const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// ── Anime Poster Helper ───────────────────────────────
const getPosterUrl = (item: any): string | undefined => {
  if (!item) return undefined
  // Для плейлиста проверяем cover_image или первый аниме
  if (item.cover_image) {
    return getMediaUrl(item.cover_image) ?? undefined
  }
  // Используем getMediaUrl как в AnimeCard.vue
  const url = getMediaUrl(item.poster_url || item.poster)
  return url ?? undefined
}

// Проверяем, нужно ли показывать английское название
const shouldShowEnglishTitle = (anime: any): boolean => {
  if (!anime?.title_en || !anime?.title_ru) return false
  // Показываем только если они отличаются
  return anime.title_en !== anime.title_ru
}

const onPosterError = (event: Event, anime: any) => {
  // Если постер не загрузился, пробуем альтернативный URL
  const img = event.target as HTMLImageElement
  
  if (anime.poster_url && img.src !== anime.poster_url) {
    // Пробуем альтернативный URL
    const altUrl = anime.poster_url.startsWith('/') 
      ? window.location.origin + anime.poster_url 
      : anime.poster_url
    img.src = altUrl
  } else {
    // Скрываем изображение и показываем placeholder
    img.style.display = 'none'
    const parent = img.parentElement
    if (parent && !parent.querySelector('.anime-poster-placeholder')) {
      const placeholder = document.createElement('div')
      placeholder.className = 'anime-poster-placeholder'
      placeholder.textContent = '🎬'
      parent.appendChild(placeholder)
    }
  }
}

const onPlaylistPosterError = (event: Event) => {
  // Если постер плейлиста не загрузился, показываем placeholder
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const parent = img.parentElement
  if (parent && !parent.querySelector('.playlist-poster-placeholder')) {
    const placeholder = document.createElement('div')
    placeholder.className = 'playlist-poster-placeholder'
    placeholder.textContent = '📁'
    parent.appendChild(placeholder)
  }
}

// ── Inline Comments ──────────────────────────────────
const showComments = ref(false)
const commentsLoading = ref(false)
const allComments = ref<any[]>([])
const newCommentText = ref('')
const sendingComment = ref(false)

// Корневые комментарии (без parent), отсортированные по дате (новые сверху)
const rootComments = computed(() => {
  const roots = allComments.value.filter(c => !c.parent)
  return [...roots].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const toggleComments = async () => {
  showComments.value = !showComments.value
  if (showComments.value && allComments.value.length === 0) {
    await loadComments()
  }
}

const loadComments = async () => {
  commentsLoading.value = true
  try {
    const { data } = await commentsApi.getComments(props.post.id)
    allComments.value = (data.results || data || []).map(normalizeComment)
  } catch {}
  finally { commentsLoading.value = false }
}

const submitComment = async () => {
  if (!newCommentText.value.trim() || sendingComment.value) return
  sendingComment.value = true
  try {
    const { data } = await commentsApi.createComment(props.post.id, newCommentText.value)
    allComments.value.push(normalizeComment(data))
    newCommentText.value = ''
    ;(props.post as any).comments_count = (props.post.comments_count || 0) + 1
  } catch {}
  finally { sendingComment.value = false }
}

const onReplyAdded = (reply: any) => {
  allComments.value.push(normalizeComment(reply))
  ;(props.post as any).comments_count = (props.post.comments_count || 0) + 1
}
</script>

<style scoped>
/* ═══ Карточка поста ══════════════════════════════════════════════ */
.post-card {
  background: var(--surface-1, #0a0a0a);
  border-radius: 14px;
  padding: 1rem 1.125rem;
  transition: all 0.25s ease;
  border: 1px solid var(--border-subtle, #111);
  margin-bottom: 0.75rem;
}

.post-card:hover {
  border-color: var(--border-default, #1a1a1a);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.post-card.pinned {
  border-color: rgba(102, 126, 234, 0.25);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, transparent 100%);
}

.pinned-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff; 
  padding: 0.2rem 0.55rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600; 
  margin-bottom: 0.6rem;
}

/* ═══ Header ════════════════════════════════════════════════════ */
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.author-info {
  display: flex;
  gap: 0.6rem;
  cursor: pointer;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.author-details {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.author-name {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.display-name {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.875rem;
}

.username {
  color: var(--text-tertiary, #555);
  font-size: 0.78rem;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.1rem;
  flex-wrap: wrap;
}

.group-badge {
  background: var(--surface-3, #151515);
  color: var(--text-secondary, #777);
  padding: 0.1rem 0.4rem;
  border-radius: 4px; 
  font-size: 0.68rem;
}

.time {
  color: var(--text-tertiary, #555);
  font-size: 0.78rem;
}

.edited {
  color: var(--text-tertiary, #444);
  font-size: 0.68rem;
  font-style: italic;
}

.visibility-badge {
  color: var(--text-tertiary, #444);
  font-size: 0.78rem;
}

.menu-btn {
  background: none; 
  border: none; 
  color: var(--text-tertiary, #555);
  font-size: 1.1rem;
  cursor: pointer; 
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.menu-btn:hover {
  background: var(--surface-3, #1a1a1a);
  color: var(--text-primary, #fff);
}

/* ═══ Content ═══════════════════════════════════════════════════ */
.post-content {
  margin-bottom: 0.6rem;
}

.post-title {
  color: var(--text-primary, #fff);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
}

.post-text-wrap {
  margin-bottom: 0.4rem;
}

.post-text {
  color: var(--text-secondary, #ccc);
  line-height: 1.65;
  font-size: 0.9rem;
  word-break: break-word;
}

.post-text.is-collapsed {
  max-height: 400px;
  overflow: hidden;
  -webkit-mask-image: linear-gradient(to bottom, black 90%, transparent);
  mask-image: linear-gradient(to bottom, black 90%, transparent);
}

.expand-btn {
  background: none;
  border: none;
  color: var(--accent, #7c5cfc);
  cursor: pointer;
  font-size: 0.78rem;
  padding: 0.25rem 0;
  margin-top: 0.15rem;
  display: block;
  font-weight: 500;
}

.expand-btn:hover {
  color: var(--accent-hover, #9d87ff);
}

.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}

.hashtag {
  color: var(--accent, #7c5cfc);
  cursor: pointer;
  font-size: 0.8rem;
  transition: color 0.2s;
}

.hashtag:hover {
  color: var(--accent-hover, #9d87ff);
}

/* ═══ Media ═════════════════════════════════════════════════════ */
.media-gallery {
  display: grid;
  gap: 2px;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  max-height: 450px;
}

.media-gallery.grid-1 {
  grid-template-columns: 1fr;
  max-height: 550px;
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

.media-item {
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: var(--surface-2, #080808);
  max-height: 450px;
}

.single-media {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  background: var(--surface-2, #080808);
}

.single-media img,
.single-media video {
  width: 100%;
  max-height: 550px;
  object-fit: contain;
  background: var(--surface-2, #080808);
  display: block;
}

/* ═══ Anime Card ════════════════════════════════════════════════ */
.anime-card {
  display: flex;
  gap: 0.75rem;
  background: var(--surface-2, #0e0e0e);
  border-radius: 10px;
  padding: 0.625rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background 0.2s;
  border: 1px solid var(--border-subtle, #151515);
}

.anime-card:hover {
  background: var(--surface-3, #141414);
  border-color: var(--border-default, #1f1f1f);
}

.anime-poster-wrap {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 6px;
  overflow: hidden;
  background: var(--surface-4, #1a1a1a);
}

.anime-poster {
  width: 44px;
  object-fit: cover;
  display: block;
}

.anime-poster-placeholder {
  width: 44px;
  height: 62px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  opacity: 0.4;
}

.anime-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
  min-width: 0;
  justify-content: center;
}

.anime-title {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.85rem;
  line-height: 1.25;
}

.anime-title-en {
  color: var(--text-tertiary, #555);
  font-size: 0.75rem;
  line-height: 1.2;
}

.anime-year {
  color: var(--text-secondary, #777);
  font-size: 0.75rem;
}

.anime-rating {
  color: var(--warning, #f59e0b);
  font-size: 0.75rem;
}

.anime-desc {
  color: var(--text-tertiary, #555);
  font-size: 0.7rem;
  line-height: 1.35;
  margin-top: 0.15rem;
  display: block;
}

/* ═══ Playlist Card ═════════════════════════════════════════════ */
.playlist-card {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--surface-2, #0e0e0e);
  border-radius: 10px;
  padding: 0.625rem 0.875rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background 0.2s;
  border: 1px solid var(--border-subtle, #151515);
}

.playlist-card:hover {
  background: var(--surface-3, #141414);
}

.playlist-poster-wrap {
  width: 40px;
  height: 54px;
  flex-shrink: 0;
  border-radius: 5px;
  overflow: hidden;
  background: var(--surface-4, #1a1a1a);
}

.playlist-poster {
  width: 40px;
  height: 54px;
  object-fit: cover;
  display: block;
}

.playlist-poster-placeholder {
  width: 40px;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  opacity: 0.4;
}

.playlist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.playlist-title {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.825rem;
}

.playlist-desc {
  color: var(--text-tertiary, #666);
  font-size: 0.7rem;
  line-height: 1.25;
}

.playlist-count {
  color: var(--text-tertiary, #555);
  font-size: 0.72rem;
}

.playlist-arrow {
  color: var(--text-tertiary, #444);
  font-size: 1.1rem;
}

/* ═══ Shorts Card ═══════════════════════════════════════════════ */
.shorts-card {
  display: flex;
  gap: 0.65rem;
  background: var(--surface-2, #0e0e0e);
  border-radius: 10px;
  padding: 0.625rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  border: 1px solid var(--border-subtle, #151515);
}

.shorts-thumb {
  width: 54px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.shorts-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shorts-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  justify-content: center;
}

.shorts-title {
  color: var(--text-primary, #fff);
  font-size: 0.825rem;
  font-weight: 600;
}

.shorts-author {
  color: var(--text-tertiary, #555);
  font-size: 0.72rem;
}

/* ═══ Repost ════════════════════════════════════════════════════ */
.repost-wrap {
  border: 1px solid var(--border-subtle, #1a1a1a);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

/* ═══ Actions ═══════════════════════════════════════════════════ */
.post-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle, #111);
}

.action-group {
  display: flex;
  gap: 0.15rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: var(--text-tertiary, #555);
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--surface-3, #151515);
  color: var(--text-secondary, #aaa);
}

.action-btn.liked {
  color: #ef4444;
}

.action-btn.disliked {
  color: #f59e0b;
}

.action-btn.bookmarked {
  color: #eab308;
}

/* ═══ Inline Comments ═══════════════════════════════════════════ */
.inline-comments {
  border-top: 1px solid var(--border-subtle, #111);
  margin-top: 0.6rem;
  padding-top: 0.6rem;
}

.comments-loading {
  display: flex;
  justify-content: center;
  padding: 0.875rem;
}

.spinner-sm {
  width: 18px;
  height: 18px;
  border: 2px solid var(--surface-4, #1a1a1a);
  border-top-color: var(--accent, #7c5cfc);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.comments-tree {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 0.6rem;
}

.no-comments {
  color: var(--text-tertiary, #444);
  font-size: 0.8rem;
  text-align: center;
  padding: 0.875rem 0;
}

.comment-input-row {
  display: flex;
  gap: 0.4rem;
  align-items: flex-start;
}

.ci-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.2rem;
}

.ci-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.comment-textarea {
  width: 100%;
  background: var(--surface-2, #0e0e0e);
  border: 1px solid var(--border-subtle, #1a1a1a);
  color: var(--text-primary, #ddd);
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  font-size: 0.8rem;
  resize: none;
  font-family: inherit;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.comment-textarea:focus {
  outline: none;
  border-color: var(--accent, #7c5cfc);
}

.send-comment-btn {
  align-self: flex-end;
  background: var(--accent, #7c5cfc);
  color: #fff;
  border: none;
  padding: 0.35rem 0.875rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  transition: background 0.2s;
}

.send-comment-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-comment-btn:hover:not(:disabled) {
  background: var(--accent-hover, #6b4de8);
}

/* ═══ Comment Nodes ═════════════════════════════════════════════ */
:deep(.comment-node) {
  display: block;
}

:deep(.comment-children) {
  margin-left: 1.75rem;
  padding-left: 0.625rem;
  border-left: 2px solid var(--border-subtle, #1a1a1a);
  margin-top: 0.2rem;
}

:deep(.comment-row) {
  display: flex;
  gap: 0.5rem;
  padding: 0.4rem 0 0.2rem;
}

:deep(.c-avatar) {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  margin-top: 2px;
}

:deep(.c-body) {
  flex: 1;
  min-width: 0;
}

:deep(.c-header) {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.1rem;
  flex-wrap: wrap;
}

:deep(.c-author) {
  color: var(--text-primary, #fff);
  font-weight: 600;
  font-size: 0.78rem;
  cursor: pointer;
}

:deep(.c-author:hover) {
  text-decoration: underline;
}

:deep(.c-reply-arrow) {
  color: var(--text-tertiary, #444);
  font-size: 0.7rem;
}

:deep(.c-reply-to) {
  color: var(--accent, #7c5cfc);
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
}

:deep(.c-reply-to:hover) {
  text-decoration: underline;
  color: var(--accent-hover, #9d87ff);
}

:deep(.c-time) {
  color: var(--text-tertiary, #444);
  font-size: 0.68rem;
}

:deep(.c-text) {
  color: var(--text-secondary, #bbb);
  font-size: 0.8rem;
  line-height: 1.45;
  margin: 0 0 0.25rem;
  word-break: break-word;
}

:deep(.c-actions) {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  align-items: center;
}

:deep(.c-btn) {
  background: none;
  border: none;
  color: var(--text-tertiary, #666);
  font-size: 0.7rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  transition: all 0.15s;
}

:deep(.c-btn:hover) {
  background: var(--surface-3, #151515);
  color: var(--text-primary, #fff);
}

:deep(.c-btn.active) {
  color: #ef4444;
}

:deep(.c-toggle) {
  color: var(--accent, #7c5cfc) !important;
  font-weight: 500;
  background: rgba(124, 92, 252, 0.08);
  border-radius: 999px;
}

:deep(.c-toggle:hover) {
  background: rgba(124, 92, 252, 0.15) !important;
  color: var(--accent-hover, #9d87ff) !important;
}

:deep(.reply-form) {
  margin-top: 0.4rem;
  margin-bottom: 0.4rem;
}

:deep(.reply-textarea) {
  width: 100%;
  background: var(--surface-2, #0e0e0e);
  border: 1px solid var(--border-subtle, #1a1a1a);
  color: var(--text-primary, #ddd);
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  font-size: 0.8rem;
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
}

:deep(.reply-textarea:focus) {
  outline: none;
  border-color: var(--accent, #7c5cfc);
}

:deep(.reply-actions) {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  justify-content: flex-end;
}

:deep(.reply-cancel) {
  background: none;
  border: 1px solid var(--border-subtle, #1a1a1a);
  color: var(--text-secondary, #777);
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.15s;
}

:deep(.reply-cancel:hover) {
  background: var(--surface-3, #151515);
  color: var(--text-primary, #fff);
}

:deep(.reply-send) {
  background: var(--accent, #7c5cfc);
  color: #fff;
  border: none;
  padding: 0.3rem 0.875rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.15s;
}

:deep(.reply-send:hover:not(:disabled)) {
  background: var(--accent-hover, #6b4de8);
}

:deep(.reply-send:disabled) {
  opacity: 0.4;
  cursor: not-allowed;
}

:deep(.ht) {
  color: var(--accent, #7c5cfc);
  cursor: pointer;
}

:deep(.mn) {
  color: var(--accent-hover, #9d87ff);
  cursor: pointer;
}

/* ═══ Spoiler Styles ═════════════════════════════════════════════ */
.spoiler-banner {
  display: flex; 
  justify-content: space-between;
  align-items: center; 
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.08) 0%, rgba(251, 146, 60, 0.05) 100%);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.3s ease;
}

.spoiler-banner.revealed {
  background: linear-gradient(135deg, rgba(124, 92, 252, 0.06) 0%, rgba(118, 75, 162, 0.04) 100%);
  border-color: rgba(124, 92, 252, 0.15);
}

.spoiler-banner-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.spoiler-icon-wrap {
  width: 28px; 
  height: 28px; 
  border-radius: 8px; 
  background: rgba(251, 191, 36, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.spoiler-banner.revealed .spoiler-icon-wrap {
  background: rgba(124, 92, 252, 0.12);
}

.spoiler-svg {
  width: 16px;
  height: 16px;
  color: #fbbf24;
}

.spoiler-banner.revealed .spoiler-svg {
  color: var(--accent, #7c5cfc);
}

.spoiler-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.spoiler-label {
  color: #fbbf24;
  font-weight: 600;
  font-size: 0.8rem; 
  letter-spacing: 0.02em;
}

.spoiler-banner.revealed .spoiler-label {
  color: var(--accent, #7c5cfc);
}

.spoiler-subject {
  color: var(--text-secondary, #888);
  font-size: 0.75rem;
}

.spoiler-reveal-btn,
.spoiler-hide-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  cursor: pointer; 
  font-size: 0.8rem; 
  font-weight: 500; 
  transition: all 0.2s;
  white-space: nowrap;
}

.spoiler-reveal-btn:hover {
  background: rgba(251, 191, 36, 0.18);
  transform: translateY(-1px);
}

.spoiler-hide-btn {
  background: rgba(124, 92, 252, 0.1);
  border-color: rgba(124, 92, 252, 0.2);
  color: var(--accent, #7c5cfc);
}

.spoiler-hide-btn:hover {
  background: rgba(124, 92, 252, 0.18);
}

.post-body {
  transition: opacity 0.3s ease;
}

.post-body.has-spoiler {
  animation: content-reveal 0.4s ease-out;
}

@keyframes content-reveal {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
