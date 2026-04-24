<template>
  <div class="post-card">
    <!-- Заголовок поста (автор) -->
    <div class="post-header">
      <div class="author-info" @click="openProfile(post.author.id)">
        <img :src="post.author_avatar || '/img/default-avatar.svg'" :alt="post.author_username" class="avatar" />
        <div>
          <span class="author-name">{{ post.author.display_name || post.author_username }}</span>
          <span class="author-username">@{{ post.author_username }}</span>
          <span class="post-time">{{ formatTime(post.created_at) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button
          v-if="post.author.id !== currentUser?.id && !post.is_following"
          @click="toggleFollow"
          class="btn-follow"
        >
          Подписаться
        </button>
        <button
          v-if="post.author.id !== currentUser?.id && post.is_following"
          @click="toggleFollow"
          class="btn-unfollow"
        >
          ✓ Подписан
        </button>
        <button @click="toggleFavorite" :class="['btn-favorite', { active: post.is_favorited }]">
          <StarIcon class="w-5 h-5" />
        </button>
        <button @click="sharePost" class="btn-share">
          <ShareIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Репост -->
    <div v-if="post.post_type === 'repost' && post.original_post_data" class="repost-header">
      <span class="repost-icon"> <SakuraIcon name="refresh" /> </span>
      <span>{{ post.author_username }} репостнул(а)</span>
    </div>

    <!-- Контент поста -->
    <div class="post-content">
      <!-- Текст -->
      <p v-if="post.text" class="post-text">{{ post.text }}</p>

      <!-- Галерея (новая схема) -->
      <div v-if="post.media_files?.length" class="media-gallery">
        <div v-for="(m, i) in post.media_files" :key="i" class="media-item">
          <img v-if="m.media_type === 'image'" :src="m.url" class="post-image" />
          <video v-else :src="m.url" controls class="post-video" />
        </div>
      </div>

      <!-- Фоллбэк на старые поля (для одиночного медиа)
           используем media_url чтобы получить правильный адрес -->
      <img
        v-else-if="post.image_url || post.image_file"
        :src="post.media_url"
        class="post-image"
      />

      <video
        v-else-if="post.video_url || post.video_file"
        :src="post.media_url"
        controls
        class="post-video"
      />

      <!-- Плейлист -->
      <div v-if="post.post_type === 'playlist' && post.playlist" class="post-playlist">
        <div class="playlist-info">
          <span class="playlist-icon"> <SakuraIcon name="folder" /> </span>
          <span class="playlist-title">{{ post.playlist_title }}</span>
        </div>
        <div class="playlist-anime">
          <div v-for="anime in post.playlist.anime.slice(0, 3)" :key="anime.id" class="mini-anime-card">
            <img :src="anime.poster" :alt="anime.title_ru" />
          </div>
        </div>
        <button @click="openPlaylist(post.playlist.id)" class="btn-playlist-link">
          Перейти к плейлисту
        </button>
      </div>

      <!-- Аниме -->
      <div v-if="post.post_type === 'anime' && post.anime" class="post-anime" @click="openAnime(post.anime?.id || post.anime)">
        <img 
          :src="getPostAnimePoster(post)" 
          :alt="post.anime_title || getAnimeTitle(post.anime)"
          class="anime-poster"
        />
        <div class="anime-info">
          <h4 class="anime-title-text">{{ post.anime_title || getAnimeTitle(post.anime) }}</h4>
          <p v-if="post.text" class="anime-description">{{ post.text }}</p>
        </div>
        <button @click.stop="openPlaylistSelector" class="btn-add-playlist" title="Добавить в плейлист"> <SakuraIcon name="folder" /> </button>
        <button @click.stop="removeAnimeAttachment" class="btn-remove" title="Удалить">✕</button>
      </div>

      <!-- Оригинальный пост (для репостов) -->
      <div v-if="post.post_type === 'repost' && post.original_post_data" class="original-post">
        <div class="repost-content">
          <div class="repost-author">{{ post.original_post_data.author_username }}</div>
          <p v-if="post.original_post_data.text" class="repost-text">{{ post.original_post_data.text }}</p>
        </div>
      </div>
    </div>

    <!-- Действия (лайки, комментарии и т.д.) -->
    <div class="post-actions">
      <button
        @click="toggleLike"
        :class="['action-btn', { active: post.is_liked }]"
        :disabled="!canInteract"
        :title="!canInteract ? 'Взаимодействие недоступно' : ''"
      >
        <HandThumbUpIcon class="w-5 h-5" />
        <span v-if="post.likes_count > 0">{{ post.likes_count }}</span>
      </button>

      <button
        @click="toggleDislike"
        :class="['action-btn', { active: post.is_disliked }]"
        :disabled="!canInteract"
        :title="!canInteract ? 'Взаимодействие недоступно' : ''"
      >
        <HandThumbDownIcon class="w-5 h-5" />
        <span v-if="post.dislikes_count > 0">{{ post.dislikes_count }}</span>
      </button>

      <button
        @click="toggleComments"
        class="action-btn"
        :disabled="!canInteract"
        :title="!canInteract ? 'Взаимодействие недоступно' : ''"
      >
        <ChatBubbleLeftIcon class="w-5 h-5" />
        <span v-if="post.comments_count > 0">{{ post.comments_count }}</span>
      </button>

      <button
        @click="repostPost"
        class="action-btn"
        :disabled="!canInteract"
        :title="!canInteract ? 'Взаимодействие недоступно' : ''"
      >
        <ArrowPathIcon class="w-5 h-5" />
        <span v-if="post.reposts_count > 0">{{ post.reposts_count }}</span>
      </button>

      <button
        @click="shareInChat"
        class="action-btn"
        :disabled="!canInteract"
        :title="!canInteract ? 'Взаимодействие недоступно' : ''"
      >
        <ShareIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Сообщение о запрещенных комментариях -->
    <div v-if="!post.allow_comments" class="comments-disabled">
      Комментарии запрещены
    </div>

    <!-- Комментарии -->
    <div v-if="showComments" class="comments-section">
      <CommentThread content-type="post" :object-id="post.id" />
    </div>

    <!-- Модальные окна -->
    <RepostModal :show="showRepostModal" :chats="chats" @close="showRepostModal = false" @repost="confirmRepost" />
    <ShareModal :show="showShareModal" @close="showShareModal = false" @share="shareToPlatform" @copy-link="copyLink" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMediaUrl } from '@/api/client'
import {
  StarIcon,
  ShareIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ChatBubbleLeftIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import CommentThread from '@/components/Comments/CommentThread.vue'
import RepostModal from '@/components/modal/feed/RepostModal.vue'
import ShareModal from '@/components/modal/feed/ShareModal.vue'
import api from '@/api'

const props = defineProps({
  post: {
    type: Object,
    required: true
  },
  isEmbedded: {
    type: Boolean,
    default: false
  },
  canInteract: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['like', 'dislike', 'repost', 'favorite'])

const router = useRouter()
const authStore = useAuthStore()

const currentUser = computed(() => authStore.user)
const showComments = ref(false)
const showRepostModal = ref(false)
const showShareModal = ref(false)
const repostComment = ref('')
const chats = ref([])

const formatTime = (date: string | Date) => {
  const now = new Date()
  const postDate = new Date(date)
  const diff = Math.floor((now.getTime() - postDate.getTime()) / 1000)

  if (diff < 60) return 'только что'
  if (diff < 3600) return `${Math.floor(diff / 60)} мин. назад`
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч. назад`
  if (diff < 604800) return `${Math.floor(diff / 86400)} дн. назад`
  return postDate.toLocaleDateString('ru-RU')
}

const openProfile = (userId: number) => {
  router.push(`/profile/${userId}`)
}

const toggleFollow = async () => {
  try {
    await api.post(`/social/follow/toggle/${props.post.author.id}/`)
    props.post.is_following = !props.post.is_following
  } catch (error) {
    console.error('Ошибка подписки:', error)
  }
}

const toggleFavorite = async () => {
  try {
    await api.post('/social/favorites/toggle/', {
      content_type: 'post',
      post: props.post.id
    })
    props.post.is_favorited = !props.post.is_favorited
  } catch (error) {
    console.error('Ошибка избранного:', error)
  }
}

const toggleLike = async () => {
  if (!props.canInteract) return
  try {
    const response = await api.post(`/social/posts/${props.post.id}/like/`)
    props.post.is_liked = response.data.liked
    props.post.likes_count = response.data.likes_count
    emit('like', props.post)
  } catch (error) {
    console.error('Ошибка лайка:', error)
  }
}

const toggleDislike = async () => {
  if (!props.canInteract) return
  try {
    const response = await api.post(`/social/posts/${props.post.id}/dislike/`)
    props.post.is_disliked = response.data.disliked
    props.post.dislikes_count = response.data.dislikes_count
    emit('dislike', props.post)
  } catch (error) {
    console.error('Ошибка дизлайка:', error)
  }
}

const toggleComments = () => {
  if (!props.canInteract) return
  showComments.value = !showComments.value
}

const repostPost = () => {
  if (!props.canInteract) return
  showRepostModal.value = true
}

const confirmRepost = async (chat: any) => {
  try {
    // Если выбран чат, делаем репост в чат
    if (chat && chat.id) {
      const response = await api.post(`/social/posts/${props.post.id}/repost/action/`, {
        comment: repostComment.value,
        chat_id: chat.id,
        type: 'chat'
      })
      showRepostModal.value = false
      repostComment.value = ''
      emit('repost', response.data)
    } else {
      // Обычный репост в ленту
      const response = await api.post(`/social/posts/${props.post.id}/repost/action/`, {
        comment: repostComment.value,
        type: 'feed'
      })
      props.post.reposts_count++
      showRepostModal.value = false
      repostComment.value = ''
      emit('repost', response.data)
    }
  } catch (error) {
    console.error('Ошибка репоста:', error)
  }
}

const shareToPlatform = async (platform: string) => {
  const shareUrl = `${window.location.origin}/posts/${props.post.id}`
  
  const shareUrls: Record<string, string> = {
    telegram: `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}`,
    vk: `https://vk.com/share.php?url=${encodeURIComponent(shareUrl)}`,
    whatsapp: `https://wa.me/?text=${encodeURIComponent(shareUrl)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}`
  }
  
  if (shareUrls[platform]) {
    window.open(shareUrls[platform], '_blank')
  }
  showShareModal.value = false
}

const copyLink = () => {
  const shareUrl = `${window.location.origin}/posts/${props.post.id}`
  navigator.clipboard.writeText(shareUrl)
  showShareModal.value = false
}

const sharePost = () => {
  showShareModal.value = true
  loadChats()
}

const shareInChat = () => {
  showShareModal.value = true
  loadChats()
}

const loadChats = async () => {
  try {
    const response = await api.get('/chats/')
    chats.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки чатов:', error)
  }
}

const shareToChat = async (chat: any) => {
  try {
    const chatId = chat.chat_id || chat.id
    const chatType = chat.chat_type || 'group'

    await api.post(`/social/messages/`, {
      text: '',
      shared_post: props.post.id,
      chat: chatType === 'group' ? chatId : null,
      private_chat: chatType === 'private' ? chatId : null
    })

    showShareModal.value = false
    router.push(`/chats/${chatId}`)
  } catch (error) {
    console.error('Ошибка отправки в чат:', error)
  }
}

const openAnime = (animeId: number) => {
  if (animeId) {
    router.push(`/anime/${animeId}`)
  }
}


const getAnimePosterUrl = (anime: any): string | undefined => {
  const url = anime?.poster_url || anime?.poster || null
  return getMediaUrl(url) || undefined
}

const getPostAnimePoster = (post: any): string => {
  // `post.anime` may be an object (from API) or a string URL (legacy)
  let url: string | undefined
  if (post.anime) {
    if (typeof post.anime === 'object') {
      url = getAnimePosterUrl(post.anime) || undefined
    } else {
      url = getMediaUrl(post.anime as string) || undefined
    }
  }
  return url || '/placeholder-anime.jpg'
}

const getAnimeTitle = (anime: any) => {
  return anime?.title_ru || anime?.title_en || 'Неизвестное аниме'
}

const openPlaylistSelector = () => {
  // TODO: Открыть селектор плейлиста для добавления аниме
  console.log('Add to playlist:', props.post.anime)
}

const removeAnimeAttachment = () => {
  // TODO: Реализовать удаление аттачмента аниме
  console.log('Remove anime attachment')
}

const openPlaylist = (playlistId: number) => {
  router.push(`/playlists/${playlistId}`)
}
</script>

<style scoped>
/* ── Основа карточки ──────────────────────────────────── */
.post-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
  overflow: hidden;
  transition:
    border-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}

.post-card:hover {
  border-color: var(--border-default);
}

.post-card.is-embedded {
  box-shadow: none;
  border-color: var(--border-subtle);
  background: var(--surface-4);
}

/* ── Шапка ─────────────────────────────────────────── */
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
}

.author-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-subtle);
  flex-shrink: 0;
  transition: border-color var(--duration-base) var(--ease-out);
}

.author-info:hover .avatar {
  border-color: var(--accent);
}

.author-name {
  display: block;
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--text-primary);
  line-height: 1.2;
}

.author-username {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.post-time {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  margin-left: var(--space-2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-follow {
  padding: 0 var(--space-3);
  height: 30px;
  min-height: 30px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition:
    background-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}

.btn-follow:hover {
  background: var(--accent-hover);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.btn-unfollow {
  padding: 0 var(--space-3);
  height: 30px;
  min-height: 30px;
  background: var(--surface-5);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}

.btn-unfollow:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.btn-favorite,
.btn-share {
  width: 32px;
  height: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-tertiary);
  transition: all var(--duration-base) var(--ease-out);
}

.btn-favorite:hover,
.btn-share:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.btn-favorite.active { color: var(--warning); }

/* ── Репост ────────────────────────────────────────── */
.repost-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--surface-4);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

/* ── Контент ────────────────────────────────────────── */
.post-content {
  padding: 0 var(--space-4) var(--space-4);
}

.post-text {
  margin: 0 0 var(--space-3);
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--text-primary);
  font-size: var(--text-base);
}

.post-image,
.post-video {
  width: 100%;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  border: 1px solid var(--border-subtle);
}

/* ── Плейлист ───────────────────────────────────────── */
.post-playlist {
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
}

.playlist-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.playlist-title {
  font-weight: 600;
  color: var(--text-primary);
}

.playlist-anime {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.mini-anime-card {
  width: 56px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
}

.mini-anime-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-playlist-link {
  width: 100%;
  padding: var(--space-2) var(--space-4);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out);
}

.btn-playlist-link:hover { background: var(--accent-hover); }

/* ── Аниме ──────────────────────────────────────────── */
.post-anime {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  transition: border-color var(--duration-base) var(--ease-out);
}

.post-anime:hover { border-color: var(--border-default); }

.anime-poster {
  max-width: 110px;
  max-height: 80px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out);
}

.anime-poster:hover { transform: scale(1.04); }

.anime-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.anime-title-text {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  transition: color var(--duration-base) var(--ease-out);
}

.anime-title-text:hover { color: var(--accent); }

.anime-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.4;
}

.btn-add-playlist,
.btn-remove {
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  width: 36px;
  height: 36px;
  min-height: 36px;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--duration-base) var(--ease-out);
}

.btn-add-playlist:hover {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.btn-remove:hover {
  background: var(--danger-subtle);
  border-color: var(--danger);
  color: var(--danger);
}

/* ── Оригинальный пост (репост) ────────────────────────── */
.original-post {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-4);
  overflow: hidden;
}

.repost-content { padding: var(--space-3); }

.repost-author {
  font-weight: 600;
  margin-bottom: var(--space-2);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.repost-text {
  margin: 0;
  line-height: 1.5;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* ── Действия ───────────────────────────────────────── */
.post-actions {
  display: flex;
  gap: 2px;
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  font-weight: 500;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  min-height: 34px;
}

.action-btn:hover {
  background: var(--surface-4);
  color: var(--text-secondary);
}

.action-btn.active { color: var(--accent); }

/* ── Комментарии ─────────────────────────────────────── */
.comments-section {
  border-top: 1px solid var(--border-subtle);
}

.comments-disabled {
  padding: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  text-align: center;
  background: var(--surface-2);
  border-radius: var(--radius-md);
  margin-top: var(--space-2);
}

/* ── Вспомогательные классы (modal, chat) ─────────── */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-cancel {
  padding: 0 var(--space-4);
  height: 36px;
  min-height: 36px;
  background: var(--surface-5);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-base);
}

.btn-confirm {
  padding: 0 var(--space-4);
  height: 36px;
  min-height: 36px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 500;
}

.btn-confirm:hover { background: var(--accent-hover); }

.chats-list { max-height: 400px; overflow-y: auto; }

.chat-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out);
}

.chat-item:hover { background: var(--surface-4); }

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
</style>
