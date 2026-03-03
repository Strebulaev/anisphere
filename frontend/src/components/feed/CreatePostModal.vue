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

        <!-- Attached Content (playlist / shorts остаются как есть) -->
        <div v-if="attachedContent" class="attached-content">
          <div v-if="attachedContent.type === 'anime'" class="attached-anime-wrap">
            <!-- аниме теперь через MediaAttachmentPicker, но оставляем совместимость -->
            <AnimeCard
              :poster-url="attachedPosterUrl"
              :title-ru="attachedTitleRu"
            >
              <div class="rating-input">
                <label>Оценка:</label>
                <input
                  type="number"
                  v-model.number="animeRating"
                  min="1"
                  max="10"
                  placeholder="1-10"
                  class="rating-field"
                >
              </div>
            </AnimeCard>
            <button class="remove-anime-btn" @click="attachedContent = null">✕</button>
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

        <!-- Аниме через пикер (с оценкой) -->
        <div v-if="attachedAnime && !attachedContent" class="attached-anime-outer">
          <!-- уже отображается внутри MediaAttachmentPicker -->
          <div class="rating-input" style="margin-top:0.5rem">
            <label>Оценка:</label>
            <input
              type="number"
              v-model.number="animeRating"
              min="1"
              max="10"
              placeholder="1-10"
              class="rating-field"
            >
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
        <!-- фото / видео / аниме через модуль -->
        <MediaAttachmentPicker
          ref="attachmentPicker"
          :allow-photo="true"
          :allow-video="true"
          :allow-anime="true"
          @update:media-files="mediaPreview = $event"
          @update:attached-anime="onAnimeSelected"
          @error="onAttachmentError"
        />
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

      <!-- file-инпуты теперь внутри MediaAttachmentPicker -->

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
      <div class="selector-content anime-selector" @click.stop>
        <h3>Выберите аниме</h3>
            <div class="search-box">
          <SearchBar
            placeholder="Поиск аниме..."
            :categories="[{ id: 'anime', name: 'Аниме', icon: 'anime', enabled: true } ]"
              :preventNavigationOnSelect="true"
            :hideSuggestions="true"
          />
        </div>
        <div class="results-list">
          <div
            v-for="anime in animeResults"
            :key="anime.id"
            class="result-item"
            @click="legacySelectAnime(anime)"
          >
            <img :src="getMediaUrl(anime.poster_url || anime.poster_image_url)" alt="">
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
import apiClient, { getMediaUrl } from '@/api/client'
import SearchBar from '@/components/Search/SearchBar.vue'
import { normalizePost } from '@/utils/normalizers'
import AnimeCard from './AnimeCard.vue'
import MediaAttachmentPicker from '@/components/common/MediaAttachmentPicker.vue'
import type { AnimeAttachment } from '@/components/common/MediaAttachmentPicker.vue'

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
  poster?: string     // legacy field, may contain direct URL string
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
const attachmentPicker = ref<InstanceType<typeof MediaAttachmentPicker> | null>(null)
const mediaPreview = ref<any[]>([])
const attachedContent = ref<AttachedContent | null>(null)
const attachedAnime = ref<AnimeAttachment | null>(null)
const animeRating = ref<number | null>(null)

// Selectors
const showAnimeSelector = ref(false)
const showPlaylistSelector = ref(false)
const showShortsSelector = ref(false)
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
  const url = attachedContent.value?.poster_url || (attachedContent.value as any)?.poster || ''
  return getMediaUrl(url) || '/placeholder-anime.jpg'
}) as any as string

const attachedTitleRu = computed((): string => {
  if (attachedContent.value?.type !== 'anime') return ''
  return attachedContent.value?.title_ru || ''
}) as any as string

const canSubmit = computed(() => {
  const hasText = text.value.trim().length > 0
  const hasMedia = mediaPreview.value.length > 0
  const hasAttachment = attachedContent.value !== null || attachedAnime.value !== null
  const withinLimit = text.value.length <= 5000

  return (hasText || hasMedia || hasAttachment) && withinLimit
})

// Обработчик ошибок из пикера
const onAttachmentError = (msg: string) => {
  alert(msg)
}

// Обработчик выбора аниме из пикера
const onAnimeSelected = (anime: AnimeAttachment | null) => {
  attachedAnime.value = anime
  showSpoilerToggle.value = !!anime
}

// Оставляем совместимость для legacy модалки выбора аниме
const legacySelectAnime = (anime: any) => {
  attachedAnime.value = {
    id: anime.id,
    title_ru: anime.title_ru,
    title_en: anime.title_en,
    poster_url: anime.poster_url,
    poster_image_url: anime.poster_image_url,
  }
  showAnimeSelector.value = false
  showSpoilerToggle.value = true
}

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

// triggerFileInput / handleFileSelect / removeMedia / openAnimeSelector
// теперь инкапсулированы в MediaAttachmentPicker

// handleAnimeSearch / selectAnime теперь инкапсулированы в MediaAttachmentPicker

const openPlaylistSelector = async () => {
  showPlaylistSelector.value = true
  try {
    const response = await apiClient.get('/playlists/playlists/my/')
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

    // Аниме может быть прикреплено либо через legacy attachedContent (совместимость),
    // либо через новый attachedAnime из пикера
    if (attachedAnime.value) {
      formData.append('anime', attachedAnime.value.id.toString())
      if (animeRating.value) {
        formData.append('anime_rating', animeRating.value.toString())
      }
    } else if (attachedContent.value?.type === 'anime') {
      formData.append('anime', attachedContent.value.id.toString())
      if (animeRating.value) {
        formData.append('anime_rating', animeRating.value.toString())
      }
    } else if (attachedContent.value?.type === 'playlist') {
      formData.append('playlist', attachedContent.value.id.toString())
    } else if (attachedContent.value?.type === 'shorts') {
      formData.append('reactor_post', attachedContent.value.id.toString())
    }

    // Add media files (структура { type, url, file } из MediaAttachmentPicker)
    mediaPreview.value.forEach((media: any, index: number) => {
      if (media.file) {
        formData.append(`media_${index}`, media.file)
      }
    })

    const response = await apiClient.post('/social/posts/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Сбрасываем пикер и локальное состояние
    attachmentPicker.value?.reset()
    attachedAnime.value = null
    animeRating.value = null
    const normalized = normalizePost(response.data)
    emit('created', normalized)
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
  border: 1px solid #1f1f1f;
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
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
  border-bottom: 1px solid transparent;
  color: #ddd;
  font-size: 1rem;
  line-height: 1.6;
  resize: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-bottom-color: #333;
}

.text-input::placeholder {
  color: #444;
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
  border-radius: 8px;
}

.attached-anime-wrap {
  position: relative;
}

.remove-anime-btn {
  position: absolute;
  top: 0.4rem;
  right: 0.4rem;
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
  font-size: 0.75rem;
  z-index: 1;
}

.attached-anime {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem;
  background: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #333;
}

.anime-poster {
  width: 80px;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  display: block;
}

.anime-poster-placeholder {
  width: 70px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2a2a2a;
  border-radius: 6px;
  font-size: 2rem;
  flex-shrink: 0;
}

.attached-anime-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: #fff;
}

.anime-title {
  font-weight: 600;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rating-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.rating-field {
  width: 60px;
  background: #1a1a1a;
  border: 1px solid #333;
  color: #fff;
  padding: 0.35rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.rating-field:focus {
  outline: none;
  border-color: #667eea;
}

.btn-add-playlist {
  background: transparent;
  border: 1px solid #333;
  color: #fff;
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
  background: #252525;
  border-color: #667eea;
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
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 1.5rem;
  border-top: 1px solid #1f1f1f;
  border-bottom: 1px solid #1f1f1f;
}

.attachment-buttons button {
  background: none;
  border: none;
  font-size: 1.3rem;
  padding: 0.5rem 0.65rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s, transform 0.1s;
  opacity: 0.7;
}

.attachment-buttons button:hover {
  background: #1a1a1a;
  opacity: 1;
  transform: scale(1.1);
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
  width: 95vw;
  max-width: 95vw;
  max-height: 90vh;
  overflow-y: auto;
}

.selector-content h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.selector-content h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.search-box {
  width: 100%;
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
  gap: 1rem;
  max-height: 60vh;
  overflow-y: auto;
  width: 100%;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}

.result-item:hover {
  background: #252525;
}

.result-item img {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.result-item span {
  color: #ddd;
  font-size: 1rem;
  font-weight: 500;
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
