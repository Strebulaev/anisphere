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

  </div>
</template>

<script setup>
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
  PlayIcon
} from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import SearchBar from '@/components/Search/SearchBar.vue'
import MediaAttachmentPicker from '@/components/common/MediaAttachmentPicker.vue'
import api from '@/api'

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

const emit = defineEmits(['send'])

const messageText = ref('')
const attachments = ref([])
const location = ref(null)
const sharedPost = ref(null)
const sharedAnime = ref(null)
const showAttachmentMenu = ref(false)
const showEmojiPicker = ref(false)
const showPostSelector = ref(false)
const fileInput = ref(null)
const messageInput = ref(null)
const postSearch = ref('')
const posts = ref([])

// MediaAttachmentPicker для чата
const chatAttachmentPicker = ref(null)

const onChatMediaFiles = (files) => {
  // Преобразуем MediaFile[] в формат attachments
  // Файлы будут загружены при отправке через отдельный upload
  chatMediaFiles.value = files
  showAttachmentMenu.value = false
}

const onChatAnime = (anime) => {
  sharedAnime.value = anime
  showAttachmentMenu.value = false
}

const chatMediaFiles = ref([])

const commonEmojis = [
  '😀', '😂', '🥰', '😎', '🤔', '😢', '😡', '👍', '👎',
  '❤️', '🔥', '✨', '🎉', '💯', '👀', '💪', '🙏', '👋'
]

const canSend = computed(() => {
  return messageText.value.trim() ||
         attachments.value.length > 0 ||
         location.value ||
         sharedPost.value ||
         sharedAnime.value
})

const filteredPosts = computed(() => {
  if (!postSearch.value) return posts.value.slice(0, 10)
  return posts.value.filter(post =>
    post.text?.toLowerCase().includes(postSearch.value.toLowerCase())
  )
})

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const autoResize = () => {
  const textarea = messageInput.value
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
}

const selectFiles = (type) => {
  fileInput.value.accept = type === 'image' ? 'image/*' :
                          type === 'video' ? 'video/*' :
                          '*/*'
  fileInput.value.click()
  showAttachmentMenu.value = false
}

const handleFileSelect = async (e) => {
  const files = Array.from(e.target.files)

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
        file: response.data.id,
        type: fileType,
        name: file.name,
        preview: response.data.file_url
      })
    } catch (error) {
      console.error('Ошибка загрузки файла:', error)
    }
  }

  e.target.value = ''
}

const removeAttachment = (index) => {
  attachments.value.splice(index, 1)
}

const shareLocation = async () => {
  if (!navigator.geolocation) {
    alert('Геолокация не поддерживается вашим браузером')
    return
  }

  try {
    const position = await new Promise((resolve, reject) => {
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
    posts.value = response.data.results || response.data
    showPostSelector.value = true
  } catch (error) {
    console.error('Ошибка загрузки постов:', error)
  }
  showAttachmentMenu.value = false
}

const selectPost = (post) => {
  sharedPost.value = post
  showPostSelector.value = false
}

// shareAnime / handleAnimeSearch / selectAnime — теперь в MediaAttachmentPicker

const insertEmoji = (emoji) => {
  messageText.value += emoji
  showEmojiPicker.value = false
  messageInput.value.focus()
}

const sendMessage = async () => {
  if (!canSend.value) return

  const messageData = {
    text: messageText.value,
    chat: props.chatType === 'group' ? props.chatId : null,
    private_chat: props.chatType === 'private' ? props.chatId : null
  }

  // Добавляем файлы из старых attachments (документы) или из chatMediaFiles через пикер
  const allMediaFiles = [
    ...attachments.value,
    ...(chatMediaFiles.value.length > 0 ? [{ file: chatMediaFiles.value[0].file, type: chatMediaFiles.value[0].type }] : [])
  ]
  if (allMediaFiles.length > 0) {
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

  try {
    emit('send', messageData)

    // Очищаем форму
    messageText.value = ''
    attachments.value = []
    chatMediaFiles.value = []
    location.value = null
    sharedPost.value = null
    sharedAnime.value = null
    chatAttachmentPicker.value?.reset()
    messageInput.value.style.height = 'auto'
  } catch (error) {
    console.error('Ошибка отправки сообщения:', error)
  }
}

// Закрываем меню при клике вне
document.addEventListener('click', (e) => {
  if (!e.target.closest('.message-input-container')) {
    showAttachmentMenu.value = false
    showEmojiPicker.value = false
  }
})
</script>

<style scoped>
.message-input-container {
  position: relative;
  padding: 12px;
  background: white;
  border-top: 1px solid #e0e0e0;
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
  border-radius: 8px;
  object-fit: cover;
}

.attachment-preview.video {
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.attachment-preview.document {
  width: 120px;
  height: 80px;
  background: #f0f0f0;
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
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
}

.location-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 8px;
  margin-bottom: 12px;
  color: #1976d2;
}

.shared-post-preview,
.shared-anime-preview {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 12px;
}

.post-preview-image,
.anime-preview-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}

.post-preview-info,
.anime-preview-info {
  flex: 1;
}

.post-author {
  font-weight: 600;
  font-size: 13px;
}

.post-text,
.anime-title {
  font-size: 12px;
  color: #666;
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
  color: #666;
  transition: background 0.3s;
}

.btn-attach:hover,
.btn-emoji:hover {
  background: #f5f5f5;
}

textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 14px;
  resize: none;
  max-height: 120px;
  font-family: inherit;
}

textarea:focus {
  outline: none;
  border-color: #667eea;
}

.btn-send {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-send:hover:not(:disabled) {
  background: #5568d3;
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
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
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  transition: background 0.3s;
}

.attachment-menu button:hover {
  background: #f5f5f5;
}

.emoji-picker {
  position: absolute;
  bottom: 60px;
  right: 12px;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 12px;
  z-index: 100;
}

.emoji-btn {
  width: 36px;
  height: 36px;
  font-size: 20px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.emoji-btn:hover {
  background: #f5f5f5;
}

.post-selector,
.anime-selector {
  padding: 20px;
  max-width: 500px;
}

.post-selector h3,
.anime-selector h3 {
  margin: 0 0 16px;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 16px;
}

.posts-list,
.anime-list {
  max-height: 300px;
  overflow-y: auto;
}

.post-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.post-item:hover {
  background: #f5f5f5;
}

.anime-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.anime-item:hover {
  background: #f5f5f5;
}

.anime-poster {
  width: 50px;
  height: 75px;
  border-radius: 6px;
  object-fit: cover;
}
</style>
