<template>
  <div class="message-input-container">
    <!-- Превью прикреплённых файлов -->
    <div v-if="attachments.length > 0" class="attachments-preview">
      <div v-for="(file, index) in attachments" :key="index" class="attachment-item">
        <img v-if="file.type === 'image'" :src="file.preview" class="attachment-preview" />
        <div v-else-if="file.type === 'video'" class="attachment-preview video">
          <PlayIcon class="w-12 h-12" />
        </div>
        <div v-else class="attachment-preview document">
          <DocumentIcon class="w-12 h-12" />
          <span>{{ file.name }}</span>
        </div>
        <button @click="removeAttachment(index)" class="btn-remove">×</button>
      </div>
    </div>

    <!-- Превью геолокации -->
    <div v-if="location" class="location-preview">
      <MapPinIcon class="w-5 h-5" />
      <span>{{ location.name || 'Геолокация' }}</span>
      <button @click="location = null" class="btn-remove">×</button>
    </div>

    <!-- Превью поста -->
    <div v-if="sharedPost" class="shared-post-preview">
      <img :src="sharedPost.image_url || sharedPost.image_file" class="post-preview-image" />
      <div class="post-preview-info">
        <span class="post-author">{{ sharedPost.author_username }}</span>
        <span class="post-text">{{ sharedPost.text?.substring(0, 100) }}...</span>
      </div>
      <button @click="sharedPost = null" class="btn-remove">×</button>
    </div>

    <!-- Превью аниме -->
    <div v-if="sharedAnime" class="shared-anime-preview">
      <img :src="sharedAnime.poster_url || sharedAnime.poster_image_url || sharedAnime.poster" class="anime-preview-image" />
      <div class="anime-preview-info">
        <span class="anime-title">{{ sharedAnime.title_ru }}</span>
      </div>
      <button @click="sharedAnime = null" class="btn-remove">×</button>
    </div>

    <!-- Превью плейлиста -->
    <div v-if="sharedPlaylist" class="shared-playlist-preview">
      <div class="playlist-posters">
        <img 
          v-for="(poster, idx) in (sharedPlaylist.posters || [sharedPlaylist.poster_url]).slice(0, 4)" 
          :key="idx" 
          :src="poster" 
          class="playlist-poster"
        />
      </div>
      <div class="playlist-preview-info">
        <span class="playlist-icon">📋</span>
        <span class="playlist-title">{{ sharedPlaylist.title }}</span>
        <span class="playlist-count">{{ sharedPlaylist.items_count || sharedPlaylist.items?.length || 0 }} аниме</span>
      </div>
      <button @click="sharedPlaylist = null" class="btn-remove">×</button>
    </div>

    <!-- Поле ввода -->
    <div class="input-wrapper">
      <button @click="showAttachmentMenu = !showAttachmentMenu" class="btn-attach">
        <PaperClipIcon class="w-6 h-6" />
      </button>

      <input
        ref="fileInput"
        type="file"
        multiple
        style="display: none"
        @change="handleFileSelect"
      />

      <textarea
        v-model="messageText"
        ref="messageInput"
        placeholder="Написать сообщение..."
        rows="1"
        @keydown="handleKeyDown"
        @input="autoResize"
      ></textarea>

      <button v-if="!messageText.trim() && attachments.length === 0" @click="showEmojiPicker = !showEmojiPicker" class="btn-emoji">
        <FaceSmileIcon class="w-6 h-6" />
      </button>

      <button
        @click="sendMessage"
        :disabled="!canSend"
        class="btn-send"
      >
        <PaperAirplaneIcon class="w-6 h-6" />
      </button>
    </div>

    <!-- Меню прикрепления -->
    <div v-if="showAttachmentMenu" class="attachment-menu">
      <!-- Фото / Видео / Аниме через модуль -->
      <MediaAttachmentPicker
        ref="chatAttachmentPicker"
        :allow-photo="true"
        :allow-video="true"
        :allow-anime="true"
        @update:media-files="onChatMediaFiles"
        @update:attached-anime="onChatAnime"
        @error="console.error"
      >
        <template #icon-photo>
          <PhotoIcon class="w-5 h-5" /><span>Изображение</span>
        </template>
        <template #icon-video>
          <VideoCameraIcon class="w-5 h-5" /><span>Видео</span>
        </template>
        <template #icon-anime>
          <FilmIcon class="w-5 h-5" /><span>Аниме</span>
        </template>
      </MediaAttachmentPicker>

      <button @click="selectFiles('document')">
        <DocumentIcon class="w-5 h-5" />
        <span>Документ</span>
      </button>
      <button @click="shareLocation">
        <MapPinIcon class="w-5 h-5" />
        <span>Геолокация</span>
      </button>
      <button @click="sharePost">
        <ShareIcon class="w-5 h-5" />
        <span>Пост</span>
      </button>
      <button @click="sharePlaylist">
        <QueueListIcon class="w-5 h-5" />
        <span>Плейлист</span>
      </button>
    </div>

    <!-- Эмодзи пикер (упрощённый) -->
    <div v-if="showEmojiPicker" class="emoji-picker">
      <button
        v-for="emoji in commonEmojis"
        :key="emoji"
        @click="insertEmoji(emoji)"
        class="emoji-btn"
      >
        {{ emoji }}
      </button>
    </div>

    <!-- Модалка выбора поста -->
    <Modal v-if="showPostSelector" @close="showPostSelector = false">
      <div class="post-selector">
        <h3>Выберите пост</h3>
        <input
          v-model="postSearch"
          type="text"
          placeholder="Поиск постов..."
          class="search-input"
        />
        <div class="posts-list">
          <div
            v-for="post in filteredPosts"
            :key="post.id"
            @click="selectPost(post)"
            class="post-item"
          >
            <span>{{ post.text?.substring(0, 50) }}...</span>
          </div>
        </div>
      </div>
    </Modal>

    <!-- Модалка выбора плейлиста -->
    <Modal v-if="showPlaylistSelector" @close="showPlaylistSelector = false">
      <div class="playlist-selector">
        <h3>Выберите плейлист</h3>
        <input
          v-model="playlistSearch"
          type="text"
          placeholder="Поиск плейлистов..."
          class="search-input"
        />
        <div v-if="isLoadingPlaylists" class="loading-state">
          Загрузка...
        </div>
        <div v-else-if="filteredPlaylists.length === 0" class="empty-state">
          Нет плейлистов
        </div>
        <div v-else class="playlists-list">
          <div
            v-for="playlist in filteredPlaylists"
            :key="playlist.id"
            @click="selectPlaylist(playlist)"
            class="playlist-item"
          >
            <div class="playlist-thumbnails">
              <img 
                v-for="(item, idx) in (playlist.items || []).slice(0, 4)" 
                :key="idx"
                :src="item.anime?.poster_url || item.anime?.poster || '/placeholder-anime.jpg'"
                class="playlist-thumb"
              />
            </div>
            <div class="playlist-info">
              <span class="playlist-name">{{ playlist.title }}</span>
              <span class="playlist-meta">{{ playlist.items_count || playlist.items?.length || 0 }} аниме</span>
            </div>
          </div>
        </div>
      </div>
    </Modal>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  PaperClipIcon,
  PaperAirplaneIcon,
  FaceSmileIcon,
  PhotoIcon,
  VideoCameraIcon,
  DocumentIcon,
  MapPinIcon,
  ShareIcon,
  FilmIcon,
  PlayIcon,
  QueueListIcon
} from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import SearchBar from '@/components/Search/SearchBar.vue'
import MediaAttachmentPicker from '@/components/common/MediaAttachmentPicker.vue'
import api from '@/api'

interface Attachment {
  file: number
  type: string
  name: string
  preview: string
}

interface LocationData {
  latitude: number
  longitude: number
  name: string
}

interface PostData {
  id: number
  text?: string
  image_url?: string
  image_file?: string
  author_username?: string
}

interface AnimeData {
  id: number
  title_ru?: string
  poster_url?: string
  poster_image_url?: string
  poster?: string
}

interface PlaylistData {
  id: number
  title: string
  items_count: number
  poster_url?: string
  cover_url?: string
  posters?: string[]
  items?: any[]
}

interface MediaFile {
  file: number | string
  type: string
}

const props = defineProps({
  chatId: {
    type: Number,
    required: true
  },
  chatType: {
    type: String,
    default: 'group'
  }
})

const emit = defineEmits<{
  send: [data: any]
}>()

const messageText = ref('')
const attachments = ref<Attachment[]>([])
const location = ref<LocationData | null>(null)
const sharedPost = ref<PostData | null>(null)
const sharedAnime = ref<AnimeData | null>(null)
const showAttachmentMenu = ref(false)
const showEmojiPicker = ref(false)
const showPostSelector = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const messageInput = ref<HTMLTextAreaElement | null>(null)
const postSearch = ref('')
const posts = ref<PostData[]>([])

// Плейлисты
const playlistSearch = ref('')
const playlists = ref<PlaylistData[]>([])
const showPlaylistSelector = ref(false)
const isLoadingPlaylists = ref(false)
const sharedPlaylist = ref<PlaylistData | null>(null)

// MediaAttachmentPicker для чата
const chatAttachmentPicker = ref<any>(null)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onChatMediaFiles = (files: any) => {
  chatMediaFiles.value = files || []
  showAttachmentMenu.value = false
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onChatAnime = (anime: any) => {
  if (anime) {
    sharedAnime.value = anime
  }
  showAttachmentMenu.value = false
}

const chatMediaFiles = ref<MediaFile[]>([])

const commonEmojis = [
  '😀', '😂', '🥰', '😎', '🤔', '😢', '😡', '👍', '👎',
  '❤️', '🔥', '✨', '🎉', '💯', '👀', '💪', '🙏', '👋'
]

const canSend = computed(() => {
  return messageText.value.trim() ||
         attachments.value.length > 0 ||
         location.value ||
         sharedPost.value ||
         sharedAnime.value ||
         sharedPlaylist.value
})

const filteredPosts = computed(() => {
  if (!postSearch.value) return posts.value.slice(0, 10)
  return posts.value.filter(post =>
    post.text?.toLowerCase().includes(postSearch.value.toLowerCase())
  )
})

const filteredPlaylists = computed(() => {
  if (!playlistSearch.value) return playlists.value.slice(0, 10)
  return playlists.value.filter(playlist =>
    playlist.title?.toLowerCase().includes(playlistSearch.value.toLowerCase())
  )
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const autoResize = () => {
  const textarea = messageInput.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

const selectFiles = (type: string) => {
  if (fileInput.value) {
    fileInput.value.accept = type === 'image' ? 'image/*' :
                            type === 'video' ? 'video/*' :
                            '*/*'
    fileInput.value.click()
  }
  showAttachmentMenu.value = false
}

const handleFileSelect = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files || [])

  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post('/social/files/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      let fileType = 'document'
      if (file.type.startsWith('image/')) fileType = 'image'
      else if (file.type.startsWith('video/')) fileType = 'video'

      attachments.value.push({
        file: response.data.id as number,
        type: fileType,
        name: file.name,
        preview: response.data.file_url as string
      })
    } catch (error) {
      console.error('Ошибка загрузки файла:', error)
    }
  }

  target.value = ''
}

const removeAttachment = (index: number) => {
  attachments.value.splice(index, 1)
}

const shareLocation = async () => {
  if (!navigator.geolocation) {
    alert('Геолокация не поддерживается вашим браузером')
    return
  }

  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000
      })
    })

    location.value = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      name: 'Моё местоположение'
    }

    showAttachmentMenu.value = false
  } catch (error) {
    console.error('Ошибка геолокации:', error)
    alert('Не удалось получить местоположение')
  }
}

const sharePost = async () => {
  try {
    const response = await api.get('/social/posts/', { params: { limit: 20 } })
    posts.value = (response.data.results || response.data) as PostData[]
    showPostSelector.value = true
  } catch (error) {
    console.error('Ошибка загрузки постов:', error)
  }
  showAttachmentMenu.value = false
}

const selectPost = (post: PostData) => {
  sharedPost.value = post
  showPostSelector.value = false
}

// Плейлисты
const sharePlaylist = async () => {
  isLoadingPlaylists.value = true
  showPlaylistSelector.value = true
  try {
    const response = await api.get('/playlists/', { 
      params: { my: true, page_size: 20 } 
    })
    playlists.value = (response.data.results || response.data || []) as PlaylistData[]
  } catch (error) {
    console.error('Ошибка загрузки плейлистов:', error)
    playlists.value = []
  } finally {
    isLoadingPlaylists.value = false
  }
  showAttachmentMenu.value = false
}

const selectPlaylist = (playlist: PlaylistData) => {
  sharedPlaylist.value = {
    id: playlist.id,
    title: playlist.title,
    items_count: playlist.items_count || playlist.items?.length || 0,
    poster_url: playlist.cover_url || playlist.poster_url,
    posters: playlist.items?.slice(0, 4).map((item: any) => 
      item.anime?.poster_url || item.anime?.poster || '/placeholder-anime.jpg'
    ).filter(Boolean) as string[],
    items: playlist.items
  }
  showPlaylistSelector.value = false
}

// shareAnime / handleAnimeSearch / selectAnime — теперь в MediaAttachmentPicker

const insertEmoji = (emoji: string) => {
  messageText.value += emoji
  showEmojiPicker.value = false
  messageInput.value?.focus()
}

const sendMessage = async () => {
  if (!canSend.value) return

  const messageData: Record<string, any> = {
    text: messageText.value,
    chat: props.chatType === 'group' ? props.chatId : null,
    private_chat: props.chatType === 'private' ? props.chatId : null
  }

  // Добавляем файлы из старых attachments (документы) или из chatMediaFiles через пикер
  const firstChatMedia = chatMediaFiles.value[0]
  const allMediaFiles: MediaFile[] = firstChatMedia 
    ? [...attachments.value, firstChatMedia]
    : [...attachments.value]
  if (allMediaFiles.length > 0 && allMediaFiles[0]) {
    messageData.media = allMediaFiles[0].file
    messageData.media_type = allMediaFiles[0].type
  }

  // Добавляем геолокацию
  if (location.value) {
    messageData.location_latitude = location.value.latitude
    messageData.location_longitude = location.value.longitude
    messageData.location_name = location.value.name
  }

  // Добавляем пост
  if (sharedPost.value) {
    messageData.shared_post = sharedPost.value.id
  }

  // Добавляем аниме
  if (sharedAnime.value) {
    messageData.shared_anime = sharedAnime.value.id
  }

  // Добавляем плейлист
  if (sharedPlaylist.value) {
    messageData.shared_playlist = sharedPlaylist.value.id
  }

  try {
    emit('send', messageData)

    // Очищаем форму
    messageText.value = ''
    attachments.value = []
    chatMediaFiles.value = []
    location.value = null
    sharedPost.value = null
    sharedAnime.value = null
    sharedPlaylist.value = null
    chatAttachmentPicker.value?.reset()
    if (messageInput.value) {
      messageInput.value.style.height = 'auto'
    }
  } catch (error) {
    console.error('Ошибка отправки сообщения:', error)
  }
}

// Закрываем меню при клике вне
document.addEventListener('click', (e: Event) => {
  const target = e.target as HTMLElement
  if (!target.closest('.message-input-container')) {
    showAttachmentMenu.value = false
    showEmojiPicker.value = false
  }
})
</script>

<style scoped>
.message-input-container {
  position: relative;
  padding: 12px;
  background: var(--surface-2);
  border-top: 1px solid var(--border-subtle);
}

.attachments-preview {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.attachment-item {
  position: relative;
}

.attachment-preview {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-lg);
  object-fit: cover;
}

.attachment-preview.video {
  background: var(--surface-4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.attachment-preview.document {
  width: 120px;
  height: 80px;
  background: var(--surface-4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  text-align: center;
  font-size: 11px;
}

.btn-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: var(--danger);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: 0 2px 8px rgba(255,138,138,0.3);
}

.btn-remove:hover {
  transform: scale(1.1);
}

.location-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--info-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: 12px;
  color: var(--info);
}

.shared-post-preview,
.shared-anime-preview,
.shared-playlist-preview {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--surface-4);
  border-radius: var(--radius-lg);
  margin-bottom: 12px;
  border: 1px solid var(--border-subtle);
}

.shared-playlist-preview {
  align-items: center;
}

.playlist-posters {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  width: 52px;
  height: 52px;
  flex-shrink: 0;
}

.playlist-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.playlist-preview-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.playlist-icon {
  font-size: 14px;
}

.playlist-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.playlist-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.post-preview-image,
.anime-preview-image {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-lg);
  object-fit: cover;
}

.post-preview-info,
.anime-preview-info {
  flex: 1;
}

.post-author {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.post-text,
.anime-title {
  font-size: 12px;
  color: var(--text-secondary);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.btn-attach,
.btn-emoji {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--duration-base) var(--ease-petal);
}

.btn-attach:hover,
.btn-emoji:hover {
  background: var(--surface-4);
  color: var(--accent);
}

textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  font-size: 14px;
  resize: none;
  max-height: 120px;
  font-family: inherit;
  background: var(--surface-4);
  color: var(--text-primary);
  transition: all var(--duration-base) var(--ease-petal);
}

textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.btn-send {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: var(--shadow-petal-sm);
}

.btn-send:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-sm);
  transform: scale(1.05);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attachment-menu {
  position: absolute;
  bottom: 60px;
  left: 12px;
  display: flex;
  flex-direction: column;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  padding: 8px;
  z-index: 100;
}

.attachment-menu button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--duration-base) var(--ease-petal);
}

.attachment-menu button:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.emoji-picker {
  position: absolute;
  bottom: 60px;
  right: 12px;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  padding: 12px;
  z-index: 100;
}

.emoji-btn {
  width: 36px;
  height: 36px;
  font-size: 20px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.emoji-btn:hover {
  background: var(--surface-4);
  transform: scale(1.15);
}

.post-selector,
.anime-selector,
.playlist-selector {
  padding: 20px;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  background: var(--surface-2);
  border-radius: var(--radius-xl);
}

.post-selector h3,
.anime-selector h3 {
  margin: 0 0 16px;
  color: var(--text-primary);
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
  background: var(--surface-4);
  color: var(--text-primary);
  transition: all var(--duration-base) var(--ease-petal);
}

.search-input:focus {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.posts-list,
.anime-list {
  max-height: 300px;
  overflow-y: auto;
}

.post-item {
  padding: 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.post-item:hover {
  background: var(--surface-4);
}

.loading-state,
.empty-state {
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
}

.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.playlist-item:hover {
  background: var(--surface-4);
}

.playlist-thumbnails {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.playlist-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-sm);
  background: var(--surface-4);
}

.playlist-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.playlist-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-primary);
}

.playlist-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.anime-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.anime-item:hover {
  background: var(--surface-4);
}

.anime-poster {
  width: 50px;
  height: 75px;
  border-radius: var(--radius-md);
  object-fit: cover;
}
</style>
