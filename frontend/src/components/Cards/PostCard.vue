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
      <span class="repost-icon">🔁</span>
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
          <span class="playlist-icon">📁</span>
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
        <button @click.stop="openPlaylistSelector" class="btn-add-playlist" title="Добавить в плейлист">📁</button>
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
      >
        <HandThumbUpIcon class="w-5 h-5" />
        <span v-if="post.likes_count > 0">{{ post.likes_count }}</span>
      </button>

      <button
        @click="toggleDislike"
        :class="['action-btn', { active: post.is_disliked }]"
      >
        <HandThumbDownIcon class="w-5 h-5" />
        <span v-if="post.dislikes_count > 0">{{ post.dislikes_count }}</span>
      </button>

      <button @click="toggleComments" class="action-btn">
        <ChatBubbleLeftIcon class="w-5 h-5" />
        <span v-if="post.comments_count > 0">{{ post.comments_count }}</span>
      </button>

      <button @click="repostPost" class="action-btn">
        <ArrowPathIcon class="w-5 h-5" />
        <span v-if="post.reposts_count > 0">{{ post.reposts_count }}</span>
      </button>

      <button @click="shareInChat" class="action-btn">
        <ShareIcon class="w-5 h-5" />
      </button>
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
  showComments.value = !showComments.value
}

const repostPost = () => {
  showRepostModal.value = true
}

const confirmRepost = async (chat: any) => {
  try {
    const response = await api.post(`/social/posts/${props.post.id}/repost/`, {
      comment: repostComment.value
    })
    props.post.reposts_count++
    showRepostModal.value = false
    repostComment.value = ''
    emit('repost', response.data)
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
  let url = anime?.poster_url || anime?.poster || null
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
.post-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  overflow: hidden;
}

.post-card.is-embedded {
  box-shadow: none;
  border: 1px solid #e0e0e0;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.author-name {
  display: block;
  font-weight: 600;
  font-size: 15px;
}

.author-username {
  color: #999;
  font-size: 13px;
}

.post-time {
  color: #999;
  font-size: 12px;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-follow {
  padding: 6px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-follow:hover {
  background: #5568d3;
}

.btn-unfollow {
  padding: 6px 16px;
  background: #e0e0e0;
  color: #666;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

.btn-favorite,
.btn-share {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #999;
  transition: all 0.3s;
}

.btn-favorite:hover,
.btn-share:hover {
  background: #f5f5f5;
  color: #667eea;
}

.btn-favorite.active {
  color: #ffc107;
}

.repost-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f9f9f9;
  font-size: 13px;
  color: #666;
}

.repost-icon {
  font-size: 16px;
}

.post-content {
  padding: 0 16px 16px;
}

.post-text {
  margin: 0 0 16px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.post-image,
.post-video {
  width: 100%;
  border-radius: 8px;
  margin-bottom: 16px;
}

.post-playlist {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.playlist-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.playlist-icon {
  font-size: 24px;
}

.playlist-title {
  font-weight: 600;
}

.playlist-anime {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.mini-anime-card {
  width: 60px;
  height: 90px;
  border-radius: 6px;
  overflow: hidden;
}

.mini-anime-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-playlist-link {
  width: 100%;
  padding: 10px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-playlist-link:hover {
  background: #5568d3;
}

.post-anime {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 16px;
}

.anime-poster {
  max-width: 120px;
  max-height: 90px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  transition: transform 0.2s;
}

.anime-poster:hover {
  transform: scale(1.05);
}

.anime-poster-placeholder {
  width: 120px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eee;
  border-radius: 6px;
  font-size: 2rem;
  flex-shrink: 0;
  cursor: pointer;
}

.anime-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.anime-title-text {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s;
}

.anime-title-text:hover {
  color: #667eea;
}

.anime-description {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.btn-add-playlist {
  background: transparent;
  border: 1px solid #ddd;
  color: #333;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn-add-playlist:hover {
  background: #f0f0f0;
  border-color: #667eea;
}

.btn-remove {
  background: transparent;
  border: 1px solid #ddd;
  color: #333;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: #ffebee;
  border-color: #d32f2f;
  color: #d32f2f;
}

.original-post {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.repost-content {
  padding: 12px;
}

.repost-author {
  font-weight: 600;
  margin-bottom: 8px;
}

.repost-text {
  margin: 0;
  line-height: 1.5;
}

.post-actions {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #f5f5f5;
}

.action-btn.active {
  color: #667eea;
}

.comments-section {
  border-top: 1px solid #f0f0f0;
}

.repost-modal,
.share-modal {
  padding: 20px;
  max-width: 500px;
}

.repost-modal h3,
.share-modal h3 {
  margin: 0 0 16px;
}

.repost-modal textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 8px 16px;
  background: #e0e0e0;
  color: #666;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-confirm {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.chats-list {
  max-height: 400px;
  overflow-y: auto;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.chat-item:hover {
  background: #f5f5f5;
}

.chat-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}
</style>
