<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="create-post-modal" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <h2>Создание поста</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Author -->
      <div class="author-row">
        <img :src="userAvatar" class="avatar" alt="Avatar">
        <div class="author-info">
          <span class="name">{{ userDisplayName }}</span>
          <div class="visibility-selector">
            <button @click="toggleVisibilityMenu" class="visibility-btn">
              {{ visibilityOptions[visibility]?.icon }} {{ visibilityOptions[visibility]?.label }}
              ▼
            </button>
            <div v-if="showVisibilityMenu" class="visibility-menu">
              <button
                v-for="(option, key) in visibilityOptions"
                :key="key"
                @click="setVisibility(key)"
                :class="{ active: visibility === key }"
              >
                {{ option.icon }} {{ option.label }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="content-area">
        <!-- Title -->
        <input
          v-if="showTitle"
          v-model="title"
          type="text"
          class="title-input"
          placeholder="Заголовок (опционально)"
          maxlength="200"
        >

        <!-- Text -->
        <textarea
          ref="textArea"
          v-model="text"
          class="text-input"
          placeholder="Что у вас нового?"
          @input="autoResize"
        ></textarea>

        <div class="char-count" :class="{ warning: text.length > 4500, error: text.length > 5000 }">
          {{ text.length }}/5000
        </div>

        <!-- Media Preview -->
        <div v-if="mediaPreview.length > 0" class="media-preview">
          <div
            v-for="(item, index) in mediaPreview"
            :key="index"
            class="preview-item"
          >
            <img v-if="item.type === 'image'" :src="item.url" alt="Preview">
            <video v-else :src="item.url"></video>
            <button class="remove-btn" @click="removeMedia(index)">✕</button>
          </div>
        </div>

        <!-- Attached Content -->
        <div v-if="attachedContent" class="attached-content">
          <div v-if="attachedContent.type === 'anime'" class="attached-anime">
            <img :src="attachedPosterUrl" alt="">
            <div class="attached-info">
              <span>{{ attachedTitleRu }}</span>
              <div class="rating-input">
                <label>Оценка:</label>
                <input
                  type="number"
                  v-model.number="animeRating"
                  min="1"
                  max="10"
                  placeholder="1-10"
                >
              </div>
            </div>
            <button class="remove-btn" @click="attachedContent = null">✕</button>
          </div>

          <div v-else-if="attachedContent.type === 'playlist'" class="attached-playlist">
            <span>📁 Плейлист: {{ attachedContent.title }}</span>
            <button class="remove-btn" @click="attachedContent = null">✕</button>
          </div>

          <div v-else-if="attachedContent.type === 'shorts'" class="attached-shorts">
            <div class="shorts-preview">
              <video :src="attachedContent.video_url" muted></video>
              <span class="duration">{{ formatDuration(attachedContent.duration || 0) }}</span>
            </div>
            <div class="attached-info">
              <span class="shorts-title">{{ attachedContent.title }}</span>
              <span class="shorts-author">@{{ attachedContent.author_username }}</span>
              <span class="shorts-link">Смотреть в Reactor</span>
            </div>
            <button class="remove-btn" @click="attachedContent = null">✕</button>
          </div>
        </div>

        <!-- Spoiler Warning -->
        <div v-if="showSpoilerToggle" class="spoiler-toggle">
          <label>
            <input type="checkbox" v-model="isSpoiler">
            Спойлер
          </label>
          <select v-if="isSpoiler" v-model="spoilerFor">
            <option value="">Выберите аниме</option>
          </select>
        </div>

        <!-- Comments Toggle -->
        <div class="comments-toggle">
          <label>
            <input type="checkbox" v-model="allowComments">
            Разрешить комментарии
          </label>
        </div>
      </div>

      <!-- Attachment Buttons -->
      <div class="attachment-buttons">
        <button @click="triggerFileInput('image')" title="Фото">
          📷
        </button>
        <button @click="triggerFileInput('video')" title="Видео">
          🎥
        </button>
        <button @click="openAnimeSelector" title="Аниме">
          🎬
        </button>
        <button @click="openPlaylistSelector" title="Плейлист">
          📁
        </button>
        <button @click="openShortsSelector" title="Shorts">
          ⚡
        </button>
        <button @click="showTitle = !showTitle" title="Заголовок">
          📝
        </button>
      </div>

      <!-- Hidden File Inputs -->
      <input
        ref="imageInput"
        type="file"
        accept="image/jpeg,image/png,image/gif,image/webp"
        multiple
        @change="handleFileSelect"
        hidden
      >
      <input
        ref="videoInput"
        type="file"
        accept="video/mp4,video/webm,video/quicktime"
        @change="handleFileSelect"
        hidden
      >

      <!-- Submit -->
      <div class="submit-row">
        <button
          @click="submitPost"
          :disabled="!canSubmit"
          class="submit-btn"
        >
          Опубликовать
        </button>
      </div>
    </div>

    <!-- Anime Selector Modal -->
    <div v-if="showAnimeSelector" class="selector-modal" @click="showAnimeSelector = false">
      <div class="selector-content" @click.stop>
        <h3>Выберите аниме</h3>
        <div class="search-box">
          <input
            v-model="animeSearch"
            type="text"
            placeholder="Поиск аниме..."
            @input="searchAnime"
          >
        </div>
        <div class="results-list">
          <div
            v-for="anime in animeResults"
            :key="anime.id"
            class="result-item"
            @click="selectAnime(anime)"
          >
            <img :src="anime.poster_url" alt="">
            <span>{{ anime.title_ru }}</span>
          </div>
        </div>
        <button class="close-selector" @click="showAnimeSelector = false">Отмена</button>
      </div>
    </div>

    <!-- Playlist Selector Modal -->
    <div v-if="showPlaylistSelector" class="selector-modal" @click="showPlaylistSelector = false">
      <div class="selector-content" @click.stop>
        <h3>Выберите плейлист</h3>
        <div class="results-list">
          <div
            v-for="playlist in playlists"
            :key="playlist.id"
            class="result-item"
            @click="selectPlaylist(playlist)"
          >
            <span>📁</span>
            <span>{{ playlist.title }}</span>
          </div>
        </div>
        <button class="close-selector" @click="showPlaylistSelector = false">Отмена</button>
      </div>
    </div>

    <!-- Shorts Selector Modal -->
    <div v-if="showShortsSelector" class="selector-modal" @click="showShortsSelector = false">
      <div class="selector-content" @click.stop>
        <h3>Выберите Shorts</h3>
        <div class="search-box">
          <input
            v-model="shortsSearch"
            type="text"
            placeholder="Поиск Shorts..."
            @input="searchShorts"
          >
        </div>
        <div v-if="shortsLoading" class="loading">Загрузка...</div>
        <div class="results-list">
          <div
            v-for="shorts in shortsResults"
            :key="shorts.id"
            class="result-item shorts-item"
            @click="selectShorts(shorts)"
          >
            <div class="shorts-thumb">
              <video :src="shorts.video_url" muted></video>
              <span class="duration-badge">{{ formatDuration(shorts.duration) }}</span>
            </div>
            <div class="shorts-info">
              <span class="shorts-title">{{ shorts.title }}</span>
              <span class="shorts-author">@{{ shorts.user?.username }}</span>
            </div>
          </div>
          <div v-if="shortsResults.length === 0 && !shortsLoading" class="no-results">
            Shorts не найдены
          </div>
        </div>
        <button class="close-selector" @click="showShortsSelector = false">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import apiClient from '@/api/client'

interface User {
  id: number
  username: string
  display_name: string
  avatar: string
}

interface AttachedContent {
  type: 'anime' | 'playlist' | 'shorts'
  id: number
  title_ru?: string
  poster_url?: string
  title?: string
  video_url?: string
  duration?: number
  author_username?: string
}

interface MediaPreview {
  type: 'image' | 'video'
  url: string
  file?: File
}

const props = defineProps<{
  initialType?: string | null
}>()

const emit = defineEmits<{
  close: []
  created: [post: any]
}>()

const defaultAvatar = '/img/default-avatar.svg'

// State
const currentUser = ref<User | null>(null)
const title = ref('')
const text = ref('')
const visibility = ref('public')
const allowComments = ref(true)
const isSpoiler = ref(false)
const spoilerFor = ref('')
const showTitle = ref(false)
const showVisibilityMenu = ref(false)
const showSpoilerToggle = ref(false)

// Media
const imageInput = ref<HTMLInputElement | null>(null)
const videoInput = ref<HTMLInputElement | null>(null)
const mediaPreview = ref<MediaPreview[]>([])
const attachedContent = ref<AttachedContent | null>(null)
const animeRating = ref<number | null>(null)

// Selectors
const showAnimeSelector = ref(false)
const showPlaylistSelector = ref(false)
const showShortsSelector = ref(false)
const animeSearch = ref('')
const animeResults = ref<any[]>([])
const playlists = ref<any[]>([])
const shortsSearch = ref('')
const shortsResults = ref<any[]>([])
const shortsLoading = ref(false)

// Textarea
const textArea = ref<HTMLTextAreaElement | null>(null)

// Visibility options
const visibilityOptions: Record<string, { icon: string; label: string }> = {
  public: { icon: '🌍', label: 'Публично' },
  followers: { icon: '👥', label: 'Только подписчики' },
  friends: { icon: '👫', label: 'Только друзья' },
  private: { icon: '🔒', label: 'Только я' }
}

// Computed
const userAvatar = computed((): string => {
  const avatar = currentUser.value?.avatar
  return avatar ? avatar : defaultAvatar
}) as any as string

const userDisplayName = computed((): string => {
  const name = currentUser.value?.display_name ?? currentUser.value?.username
  return name ? name : ''
}) as any as string

const attachedPosterUrl = computed((): string => {
  if (attachedContent.value?.type !== 'anime') return ''
  return attachedContent.value?.poster_url || ''
}) as any as string

const attachedTitleRu = computed((): string => {
  if (attachedContent.value?.type !== 'anime') return ''
  return attachedContent.value?.title_ru || ''
}) as any as string

const canSubmit = computed(() => {
  const hasText = text.value.trim().length > 0
  const hasMedia = mediaPreview.value.length > 0
  const hasAttachment = attachedContent.value !== null
  const withinLimit = text.value.length <= 5000

  return (hasText || hasMedia || hasAttachment) && withinLimit
})

// Methods
const autoResize = () => {
  if (textArea.value) {
    textArea.value.style.height = 'auto'
    textArea.value.style.height = textArea.value.scrollHeight + 'px'
  }
}

const toggleVisibilityMenu = () => {
  showVisibilityMenu.value = !showVisibilityMenu.value
}

const setVisibility = (key: string) => {
  visibility.value = key
  showVisibilityMenu.value = false
}

const triggerFileInput = (type: 'image' | 'video') => {
  if (type === 'image') {
    imageInput.value?.click()
  } else {
    videoInput.value?.click()
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files || files.length === 0) return

  const file = files[0]
  if (!file) return

  const type = file.type.startsWith('image/') ? 'image' : 'video'

  // Check limits
  if (type === 'image' && mediaPreview.value.length >= 10) {
    alert('Максимум 10 изображений')
    return
  }

  if (file.size > (type === 'image' ? 10 * 1024 * 1024 : 100 * 1024 * 1024)) {
    alert(`Максимальный размер ${type === 'image' ? '10 МБ' : '100 МБ'}`)
    return
  }

  const url = URL.createObjectURL(file)
  mediaPreview.value.push({ type, url, file })

  target.value = ''
}

const removeMedia = (index: number) => {
  URL.revokeObjectURL(mediaPreview.value[index]!.url)
  mediaPreview.value.splice(index, 1)
}

const openAnimeSelector = () => {
  showAnimeSelector.value = true
  searchAnime()
}

const searchAnime = async () => {
  if (animeSearch.value.length < 2) {
    animeResults.value = []
    return
  }

  try {
    const response = await apiClient.get(`/anime/search/?q=${animeSearch.value}`)
    animeResults.value = response.data.results?.slice(0, 10) || []
  } catch (error) {
    console.error('Error searching anime:', error)
  }
}

const selectAnime = (anime: any) => {
  attachedContent.value = {
    type: 'anime',
    id: anime.id,
    title_ru: anime.title_ru,
    poster_url: anime.poster_url
  }
  showAnimeSelector.value = false
  showSpoilerToggle.value = true
}

const openPlaylistSelector = async () => {
  showPlaylistSelector.value = true
  try {
    const response = await apiClient.get('/playlists/my/')
    playlists.value = response.data.results || []
  } catch (error) {
    console.error('Error loading playlists:', error)
  }
}

const selectPlaylist = (playlist: any) => {
  attachedContent.value = {
    type: 'playlist',
    id: playlist.id,
    title: playlist.title
  }
  showPlaylistSelector.value = false
}

const openShortsSelector = () => {
  showShortsSelector.value = true
  loadMyShorts()
}

const loadMyShorts = async () => {
  shortsLoading.value = true
  try {
    const response = await apiClient.get('/reactor/my-posts/')
    shortsResults.value = response.data.results || []
  } catch (error) {
    console.error('Error loading shorts:', error)
    shortsResults.value = []
  } finally {
    shortsLoading.value = false
  }
}

const searchShorts = async () => {
  if (shortsSearch.value.length < 2) {
    loadMyShorts()
    return
  }

  shortsLoading.value = true
  try {
    const response = await apiClient.get(`/reactor/posts/?q=${shortsSearch.value}`)
    shortsResults.value = response.data.results || []
  } catch (error) {
    console.error('Error searching shorts:', error)
  } finally {
    shortsLoading.value = false
  }
}

const selectShorts = (shorts: any) => {
  attachedContent.value = {
    type: 'shorts',
    id: shorts.id,
    title: shorts.title,
    video_url: shorts.video_url,
    duration: shorts.duration,
    author_username: shorts.user?.username
  }
  showShortsSelector.value = false
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const submitPost = async () => {
  if (!canSubmit.value) return

  try {
    // Create form data
    const formData = new FormData()
    formData.append('title', title.value)
    formData.append('text', text.value)
    formData.append('visibility', visibility.value)
    formData.append('allow_comments', allowComments.value.toString())
    formData.append('is_spoiler', isSpoiler.value.toString())

    if (attachedContent.value?.type === 'anime') {
      formData.append('anime', attachedContent.value.id.toString())
      if (animeRating.value) {
        formData.append('anime_rating', animeRating.value.toString())
      }
    } else if (attachedContent.value?.type === 'playlist') {
      formData.append('playlist', attachedContent.value.id.toString())
    } else if (attachedContent.value?.type === 'shorts') {
      formData.append('reactor_post', attachedContent.value.id.toString())
    }

    // Add media files
    mediaPreview.value.forEach((media, index) => {
      if (media.file) {
        formData.append(`media_${index}`, media.file)
      }
    })

    const response = await apiClient.post('/social/posts/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    emit('created', response.data)
  } catch (error) {
    console.error('Error creating post:', error)
    alert('Ошибка при создании поста')
  }
}

const fetchCurrentUser = async () => {
  try {
    const response = await apiClient.get('/users/me/')
    currentUser.value = response.data
  } catch (error) {
    console.error('Error fetching user:', error)
  }
}

onMounted(() => {
  fetchCurrentUser()
  nextTick(() => {
    if (textArea.value) {
      textArea.value.focus()
    }
  })
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.create-post-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
}

.close-btn:hover {
  color: #fff;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.name {
  color: #fff;
  font-weight: 600;
}

.visibility-selector {
  position: relative;
}

.visibility-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.25rem 0;
}

.visibility-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.5rem;
  z-index: 10;
}

.visibility-menu button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  background: none;
  border: none;
  color: #888;
  padding: 0.5rem 1rem;
  cursor: pointer;
  border-radius: 4px;
  white-space: nowrap;
}

.visibility-menu button:hover,
.visibility-menu button.active {
  background: #252525;
  color: #fff;
}

.content-area {
  padding: 1rem 1.5rem;
}

.title-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid #333;
  color: #fff;
  font-size: 1.1rem;
  font-weight: 600;
  padding: 0.5rem 0;
  margin-bottom: 0.75rem;
}

.title-input:focus {
  outline: none;
  border-color: #667eea;
}

.text-input {
  width: 100%;
  min-height: 120px;
  background: transparent;
  border: none;
  color: #ddd;
  font-size: 1rem;
  line-height: 1.6;
  resize: none;
}

.text-input:focus {
  outline: none;
}

.char-count {
  text-align: right;
  color: #555;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.char-count.warning {
  color: #f59e0b;
}

.char-count.error {
  color: #ef4444;
}

.media-preview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 1rem;
}

.preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
}

.preview-item img,
.preview-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 0.25rem;
  right: 0.25rem;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attached-content {
  margin-top: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
}

.attached-anime {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.attached-anime img {
  width: 50px;
  height: 75px;
  object-fit: cover;
  border-radius: 4px;
}

.attached-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: #fff;
}

.rating-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rating-input input {
  width: 50px;
  background: #252525;
  border: 1px solid #333;
  color: #fff;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.attached-playlist {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.attached-shorts {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.shorts-preview {
  position: relative;
  width: 80px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.shorts-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shorts-preview .duration {
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
  color: #888;
  font-size: 0.85rem;
}

.shorts-link {
  color: #667eea;
  font-size: 0.8rem;
}

.spoiler-toggle,
.comments-toggle {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.spoiler-toggle label,
.comments-toggle label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #888;
  cursor: pointer;
}

.spoiler-toggle input[type="checkbox"] {
  accent-color: #667eea;
}

.comments-toggle input[type="checkbox"] {
  accent-color: #667eea;
}

.attachment-buttons {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.attachment-buttons button {
  background: none;
  border: none;
  font-size: 1.5rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.attachment-buttons button:hover {
  background: #1a1a1a;
}

.submit-row {
  padding: 1rem 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.submit-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Selector Modal */
.selector-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.selector-content {
  background: #111;
  border-radius: 12px;
  padding: 1.5rem;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
}

.selector-content h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.search-box input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #333;
  color: #fff;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.search-box input:focus {
  outline: none;
  border-color: #667eea;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: #252525;
}

.result-item img {
  width: 32px;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
}

.result-item span {
  color: #ddd;
}

.shorts-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.shorts-thumb {
  position: relative;
  width: 60px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  background: #000;
  flex-shrink: 0;
}

.shorts-thumb video {
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
  font-size: 0.65rem;
  padding: 0.125rem 0.25rem;
  border-radius: 2px;
}

.shorts-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.shorts-info .shorts-title {
  color: #ddd;
  font-size: 0.9rem;
}

.shorts-info .shorts-author {
  color: #666;
  font-size: 0.8rem;
}

.loading {
  text-align: center;
  color: #666;
  padding: 1rem;
}

.no-results {
  text-align: center;
  color: #666;
  padding: 1rem;
}

.close-selector {
  width: 100%;
  background: #1a1a1a;
  color: #888;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 1rem;
}
</style>
