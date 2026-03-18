<template>
  <div class="post-card" :class="{ pinned: post.is_pinned }">
    <!-- Pin indicator -->
    <div v-if="post.is_pinned" class="pinned-badge">📌 Закреплён</div>

    <!-- Header -->
    <div class="post-header">
      <div class="author-info" @click.stop="goToProfile">
        <img :src="post.author_avatar || defaultAvatar" class="avatar" alt="">
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

    <!-- Content — текст разворачивается inline, без модального окна -->
    <div class="post-content">
      <h3 v-if="post.title" class="post-title">{{ post.title }}</h3>

      <!-- Spoiler Warning - показываем ПЕРЕД контентом если is_spoiler -->
      <div v-if="post.is_spoiler && !spoilerRevealed" class="spoiler-warning">
        <div class="spoiler-info">
          <span class="spoiler-icon">⚠️</span>
          <div class="spoiler-text">
            <span class="spoiler-label">Спойлер</span>
            <span v-if="post.spoiler_for" class="spoiler-for">{{ post.spoiler_for }}</span>
          </div>
        </div>
        <button class="spoiler-reveal-btn" @click.stop="spoilerRevealed = true">
          👁️ Показать
        </button>
      </div>

      <!-- Spoiler Content - скрыт если is_spoiler и не раскрыт -->
      <div v-if="!post.is_spoiler || spoilerRevealed" class="spoiler-content" :class="{ 'is-revealed': spoilerRevealed && post.is_spoiler }">
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
            <img v-if="m.type === 'image'" :src="m.url" :alt="m.caption || ''">
            <video v-else :src="m.url" :poster="m.thumbnail" controls preload="metadata"></video>
          </div>
        </div>
        <div v-else-if="post.image_url" class="single-media"><img :src="post.image_url" @click.stop></div>
        <div v-else-if="post.video_url" class="single-media"><video :src="post.video_url" controls preload="metadata"></video></div>

        <!-- Anime Card -->
        <div v-if="post.anime" class="anime-card" @click.stop="$router.push('/anime/'+post.anime.id)">
          <div class="anime-poster-wrap">
            <img 
              v-if="getPosterUrl(post.anime)"
              :src="getPosterUrl(post.anime) || post.anime.poster_url"
              class="anime-poster" 
              alt="poster"
              loading="lazy"
              decoding="async"
              @error="onPosterError($event, post.anime)"
            >
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
        <div v-if="post.playlist" class="playlist-card" @click.stop="$router.push('/playlist/'+post.playlist.id)">
          <div class="playlist-poster-wrap">
            <img
              v-if="getPosterUrl(post.playlist)"
              :src="getPosterUrl(post.playlist)"
              class="playlist-poster"
              alt="poster"
              loading="lazy"
              decoding="async"
              @error="onPlaylistPosterError($event)"
            >
            <div v-else class="playlist-poster-placeholder">📁</div>
          </div>
          <div class="playlist-info">
            <span class="playlist-title">{{ post.playlist.title || 'Плейлист' }}</span>
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
        <img :src="defaultAvatar" class="ci-avatar" alt="">
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
.post-card {
  background: #111; border-radius: 12px; padding: 1rem;
  transition: box-shadow 0.2s; border: 1px solid transparent;
  margin-bottom: 1rem;
}
.post-card:hover { border-color: #1e1e1e; box-shadow: 0 2px 8px rgba(0,0,0,0.25); }
.post-card.pinned { border-color: #667eea40; }

.pinned-badge {
  display: inline-block; background: linear-gradient(135deg,#667eea,#764ba2);
  color: #fff; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.72rem; margin-bottom: 0.6rem;
}

.post-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
.author-info { display: flex; gap: 0.7rem; cursor: pointer; }
.avatar { width: 42px; height: 42px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.author-details { display: flex; flex-direction: column; }
.author-name { display: flex; align-items: center; gap: 0.4rem; }
.display-name { color: #fff; font-weight: 600; font-size: 0.9rem; }
.username { color: #555; font-size: 0.8rem; }
.post-meta { display: flex; align-items: center; gap: 0.4rem; margin-top: 0.15rem; flex-wrap: wrap; }
.group-badge { background: #1a1a1a; color: #888; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.72rem; }
.time { color: #555; font-size: 0.8rem; }
.edited { color: #444; font-size: 0.72rem; font-style: italic; }
.visibility-badge { color: #444; font-size: 0.8rem; }
.menu-btn { background: none; border: none; color: #555; font-size: 1.2rem; cursor: pointer; padding: 0.2rem 0.5rem; border-radius: 4px; transition: background 0.2s; }
.menu-btn:hover { background: #1a1a1a; color: #fff; }

.post-content { margin-bottom: 0.75rem; }
.post-title { color: #fff; font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem; }

.post-text-wrap { margin-bottom: 0.5rem; }
/* Показываем больше текста — 7 строк вместо 3 */
.post-text { color: #d0d0d0; line-height: 1.7; font-size: 0.97rem; word-break: break-word; }
.post-text.is-collapsed {
  max-height: 500px; overflow: hidden;
  -webkit-mask-image: linear-gradient(to bottom, black 85%, transparent);
  mask-image: linear-gradient(to bottom, black 85%, transparent);
}
.expand-btn { background: none; border: none; color: #667eea; cursor: pointer; font-size: 0.82rem; padding: 0.3rem 0; margin-top: 0.2rem; display: block; }
.expand-btn:hover { color: #8b9ef5; }

.hashtags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.5rem; }
.hashtag { color: #667eea; cursor: pointer; font-size: 0.875rem; }
.hashtag:hover { color: #8b9ef5; }

.media-gallery { display: grid; gap: 2px; border-radius: 8px; overflow: hidden; margin-bottom: 0.5rem; max-height: 500px; }
.media-gallery.grid-1 { grid-template-columns: 1fr; max-height: 600px; }
.media-gallery.grid-2 { grid-template-columns: 1fr 1fr; }
.media-gallery.grid-3 { grid-template-columns: 2fr 1fr; grid-template-rows: 1fr 1fr; }
.media-gallery.grid-3 .media-item:first-child { grid-row: span 2; }
.media-gallery.grid-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
.media-item { position: relative; overflow: hidden; cursor: pointer; }
.media-item img, .media-item video { width: 100%; height: 100%; object-fit: contain; background: #0a0a0a; max-height: 500px; }
.single-media { border-radius: 8px; overflow: hidden; margin-bottom: 0.5rem; background: #0a0a0a; }
.single-media img, .single-media video { width: 100%; max-height: 600px; object-fit: contain; background: #0a0a0a; display: block; }

.anime-card { display: flex; gap: 0.875rem; background: #1a1a1a; border-radius: 8px; padding: 0.75rem; cursor: pointer; margin-bottom: 0.5rem; transition: background 0.2s; }
.anime-card:hover { background: #222; }
.anime-poster-wrap { 
  width: 50px; 
  height: 70px; 
  flex-shrink: 0; 
  border-radius: 5px; 
  overflow: hidden; 
  background: #2a2a2a; 
}
.anime-poster { 
  width: 50px; 
  object-fit: cover; 
  display: block;
}
.anime-poster-placeholder { 
  width: 50px;
  height: 70px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  font-size: 1.5rem; 
  opacity: 0.5; 
}
.anime-info { display: flex; flex-direction: column; gap: 0.2rem; flex: 1; min-width: 0; justify-content: center; }
.anime-title { color: #fff; font-weight: 600; font-size: 0.9rem; line-height: 1.3; }
.anime-title-en { color: #666; font-size: 0.8rem; line-height: 1.3; }
.anime-year { color: #888; font-size: 0.8rem; }
.anime-rating { color: #f59e0b; font-size: 0.8rem; }
.anime-desc { color: #666; font-size: 0.75rem; line-height: 1.4; margin-top: 0.25rem; display: block; }

.playlist-card { display: flex; align-items: center; gap: 0.75rem; background: #1a1a1a; border-radius: 8px; padding: 0.75rem 1rem; cursor: pointer; margin-bottom: 0.5rem; transition: background 0.2s; }
.playlist-card:hover { background: #222; }
.playlist-poster-wrap { 
  width: 45px; 
  height: 60px; 
  flex-shrink: 0; 
  border-radius: 5px; 
  overflow: hidden; 
  background: #2a2a2a; 
}
.playlist-poster { 
  width: 45px; 
  height: 60px;
  object-fit: cover; 
  display: block;
}
.playlist-poster-placeholder { 
  width: 45px;
  height: 60px;
  display: flex; 
  align-items: center; 
  justify-content: center;
  font-size: 1.2rem; 
  opacity: 0.5; 
}
.playlist-icon { font-size: 1.4rem; }
.playlist-info { flex: 1; display: flex; flex-direction: column; }
.playlist-title { color: #fff; font-weight: 600; font-size: 0.875rem; }
.playlist-count { color: #666; font-size: 0.78rem; }
.playlist-arrow { color: #555; font-size: 1.2rem; }

.shorts-card { display: flex; gap: 0.75rem; background: #1a1a1a; border-radius: 8px; padding: 0.75rem; cursor: pointer; margin-bottom: 0.5rem; }
.shorts-thumb { width: 60px; height: 90px; border-radius: 5px; overflow: hidden; flex-shrink: 0; }
.shorts-thumb video { width: 100%; height: 100%; object-fit: cover; }
.shorts-info { display: flex; flex-direction: column; gap: 0.2rem; }
.shorts-title { color: #fff; font-size: 0.875rem; font-weight: 600; }
.shorts-author { color: #666; font-size: 0.78rem; }

.repost-wrap { border: 1px solid #2a2a2a; border-radius: 8px; overflow: hidden; margin-bottom: 0.5rem; }

/* Spoiler Styles */
.spoiler-warning {
  display: flex; 
  justify-content: space-between;
  align-items: center; 
  background: linear-gradient(135deg, #2a2a1a 0%, #1a1a0a 100%);
  border: 1px solid #665500;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
}
.spoiler-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.spoiler-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.5));
}
.spoiler-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.spoiler-label {
  color: #fbbf24;
  font-weight: 600; 
  font-size: 0.95rem;
}
.spoiler-for {
  color: #888; 
  font-size: 0.8rem; 
}
.spoiler-reveal-btn {
  background: linear-gradient(135deg, #665500 0%, #443300 100%);
  color: #fbbf24;
  border: 1px solid #886600;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer; 
  font-size: 0.85rem;
  font-weight: 500; 
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.spoiler-reveal-btn:hover {
  background: linear-gradient(135deg, #886600 0%, #665500 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.2);
}

.spoiler-content {
  transition: opacity 0.3s ease;
}
.spoiler-content.is-revealed {
  animation: spoiler-reveal 0.5s ease-out;
}
@keyframes spoiler-reveal {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.post-actions { display: flex; justify-content: space-between; padding-top: 0.6rem; border-top: 1px solid #1a1a1a; }
.action-group { display: flex; gap: 0.2rem; }
.action-btn { display: inline-flex; align-items: center; gap: 0.3rem; background: none; border: none; color: #666; padding: 0.45rem 0.65rem; border-radius: 8px; cursor: pointer; font-size: 0.875rem; transition: all 0.15s; }
.action-btn:hover { background: #1a1a1a; color: #aaa; }
.action-btn.liked { color: #ef4444; }
.action-btn.disliked { color: #f59e0b; }
.action-btn.bookmarked { color: #eab308; }

/* ── Inline Comments ── */
.inline-comments { border-top: 1px solid #1a1a1a; margin-top: 0.75rem; padding-top: 0.75rem; }
.comments-loading { display: flex; justify-content: center; padding: 1rem; }
.spinner-sm { width: 20px; height: 20px; border: 2px solid #2a2a2a; border-top-color: #667eea; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.comments-tree { display: flex; flex-direction: column; gap: 0; margin-bottom: 0.75rem; }
.no-comments { color: #555; font-size: 0.85rem; text-align: center; padding: 1rem 0; }

.comment-input-row { display: flex; gap: 0.5rem; align-items: flex-start; }
.ci-avatar { width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0; margin-top: 0.25rem; }
.ci-wrap { flex: 1; display: flex; flex-direction: column; gap: 0.4rem; }
.comment-textarea { width: 100%; background: #1a1a1a; border: 1px solid #2a2a2a; color: #ddd; padding: 0.5rem 0.75rem; border-radius: 8px; font-size: 0.85rem; resize: none; font-family: inherit; transition: border-color 0.2s; box-sizing: border-box; }
.comment-textarea:focus { outline: none; border-color: #667eea; }
.send-comment-btn { align-self: flex-end; background: #667eea; color: #fff; border: none; padding: 0.4rem 1rem; border-radius: 8px; cursor: pointer; font-size: 0.82rem; font-weight: 600; }
.send-comment-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.send-comment-btn:hover:not(:disabled) { background: #5a6fd6; }

/* ── Comment Nodes — 3 уровня: пост → комментарий → ответ ── */
:deep(.comment-node) { display: block; }
:deep(.comment-children) { 
  margin-left: 2rem;
  padding-left: 0.75rem;
  border-left: 2px solid #333;
  margin-top: 0.25rem;
}
:deep(.comment-row) { 
  display: flex; 
  gap: 0.6rem; 
  padding: 0.5rem 0 0.25rem; 
}
/* :deep(.comment-row.is-reply) { 
  /* Ответы без дополнительного отступа */
/* } */
:deep(.c-avatar) { 
  width: 28px; 
  height: 28px; 
  border-radius: 50%; 
  object-fit: cover; 
  flex-shrink: 0; 
  cursor: pointer; 
  margin-top: 2px; 
}
:deep(.c-body) { flex: 1; min-width: 0; }
:deep(.c-header) { 
  display: flex; 
  align-items: center; 
  gap: 0.4rem; 
  margin-bottom: 0.15rem; 
  flex-wrap: wrap;
}
:deep(.c-author) { 
  color: #fff; 
  font-weight: 600; 
  font-size: 0.82rem; 
  cursor: pointer; 
}
:deep(.c-author:hover) { text-decoration: underline; }
:deep(.c-reply-arrow) { 
  color: #555; 
  font-size: 0.75rem; 
}
:deep(.c-reply-to) { 
  color: #667eea; 
  font-size: 0.82rem; 
  font-weight: 500;
  cursor: pointer;
}
:deep(.c-reply-to:hover) { 
  text-decoration: underline; 
  color: #8b9ef5;
}
:deep(.c-time) { color: #555; font-size: 0.72rem; }
:deep(.c-text) { color: #ccc; font-size: 0.875rem; line-height: 1.5; margin: 0 0 0.35rem; word-break: break-word; }
:deep(.c-actions) { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
:deep(.c-btn) { 
  background: none; 
  border: none; 
  color: #888; 
  font-size: 0.75rem; 
  cursor: pointer; 
  padding: 0.25rem 0.5rem; 
  border-radius: 4px; 
  transition: all 0.15s; 
}
:deep(.c-btn:hover) { background: #1a1a1a; color: #fff; }
:deep(.c-btn.active) { color: #ef4444; }
:deep(.c-toggle) { 
  color: #667eea !important; 
  font-weight: 500;
  background: rgba(102,126,234,0.1);
  border-radius: 999px;
}
:deep(.c-toggle:hover) { 
  background: rgba(102,126,234,0.2) !important; 
  color: #8b9ef5 !important;
}

:deep(.reply-form) { 
  margin-top: 0.5rem; 
  margin-bottom: 0.5rem;
}
:deep(.reply-textarea) { 
  width: 100%; 
  background: #1a1a1a; 
  border: 1px solid #2a2a2a; 
  color: #ddd; 
  padding: 0.5rem 0.75rem; 
  border-radius: 8px; 
  font-size: 0.85rem; 
  resize: none; 
  font-family: inherit; 
  box-sizing: border-box; 
}
:deep(.reply-textarea:focus) { outline: none; border-color: #667eea; }
:deep(.reply-actions) { display: flex; gap: 0.5rem; margin-top: 0.5rem; justify-content: flex-end; }
:deep(.reply-cancel) { 
  background: none; 
  border: 1px solid #2a2a2a; 
  color: #888; 
  padding: 0.35rem 0.75rem; 
  border-radius: 6px; 
  cursor: pointer; 
  font-size: 0.8rem; 
  transition: all 0.15s; 
}
:deep(.reply-cancel:hover) { background: #1a1a1a; color: #fff; }
:deep(.reply-send) { 
  background: #667eea; 
  color: #fff; 
  border: none; 
  padding: 0.35rem 1rem; 
  border-radius: 6px; 
  cursor: pointer; 
  font-size: 0.8rem; 
  font-weight: 500; 
  transition: all 0.15s; 
}
:deep(.reply-send:hover:not(:disabled)) { background: #5a6fd6; }
:deep(.reply-send:disabled) { opacity: 0.4; cursor: not-allowed; }

:deep(.ht) { color: #667eea; cursor: pointer; }
:deep(.mn) { color: #8b9ef5; cursor: pointer; }
</style>
