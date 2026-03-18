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
            <button @click="showVisibilityMenu = !showVisibilityMenu" class="visibility-btn">
              {{ visibilityOptions[visibility]?.icon }} {{ visibilityOptions[visibility]?.label }} ▼
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
        <!-- Text (БЕЗ заголовка - по умолчанию) -->
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

        <!-- Media Preview (фото/видео) — мультивыбор -->
        <div v-if="mediaFiles.length > 0" class="media-preview">
          <div v-for="(m, idx) in mediaFiles" :key="idx" class="preview-item">
            <img v-if="m.type === 'image'" :src="m.url" alt="">
            <video v-else :src="m.url" muted></video>
            <button class="remove-media-btn" @click="removeMedia(idx)">✕</button>
          </div>
        </div>

        <!-- Attached anime — мультивыбор -->
        <div v-if="attachedAnimes.length > 0" class="attached-list">
          <div v-for="(a, idx) in attachedAnimes" :key="a.id" class="attached-block">
            <span class="attached-icon">🎬</span>
            <span class="attached-label">{{ a.title_ru }}</span>
            <div class="rating-input">
              <label>Оценка:</label>
              <input type="number" v-model.number="animeRatings[idx]" min="1" max="10" placeholder="1-10" class="rating-field">
            </div>
            <button class="remove-btn" @click="removeAnime(idx)">✕</button>
          </div>
        </div>

        <!-- Attached playlists — мультивыбор -->
        <div v-if="attachedPlaylists.length > 0" class="attached-list">
          <div v-for="(p, idx) in attachedPlaylists" :key="p.id" class="attached-block">
            <span class="attached-icon">📁</span>
            <span class="attached-label">{{ p.title || p.name }}</span>
            <button class="remove-btn" @click="removePlaylist(idx)">✕</button>
          </div>
        </div>

        <!-- Attached shorts — мультивыбор -->
        <div v-if="attachedShortsList.length > 0" class="attached-list">
          <div v-for="(s, idx) in attachedShortsList" :key="s.id" class="attached-block">
            <span class="attached-icon">⚡</span>
            <span class="attached-label">{{ s.title || 'Shorts #' + s.id }}</span>
            <button class="remove-btn" @click="removeShorts(idx)">✕</button>
          </div>
        </div>

        <!-- Spoiler / Comments toggles -->
        <div class="toggles-row">
          <label class="toggle-label">
            <span class="toggle-switch" :class="{ active: isSpoiler }">
              <span class="toggle-slider"></span>
            </span>
            <input type="checkbox" v-model="isSpoiler" class="toggle-input">
            <span class="toggle-text">Спойлер</span>
          </label>
          <label class="toggle-label">
            <span class="toggle-switch" :class="{ active: allowComments }">
              <span class="toggle-slider"></span>
            </span>
            <input type="checkbox" v-model="allowComments" class="toggle-input">
            <span class="toggle-text">Комментарии</span>
          </label>
        </div>

        <!-- Spoiler description -->
        <div v-if="isSpoiler" class="spoiler-settings">
          <input
            v-model="spoilerFor"
            type="text"
            placeholder="О чём спойлер? (например: Конец Наруто)"
            class="spoiler-for-input"
          >
        </div>
      </div>

      <!-- Attachment Buttons — ТОЛЬКО скрепочка (объединяет всё) -->
      <div class="attachment-buttons">
        <!-- 📎 Прикрепить (фото/видео/аниме/плейлист/shorts) -->
        <button @click="openAttachModal" title="Прикрепить" class="attach-btn main-attach" :class="{ active: hasAnyAttachments }">
          📎
          <span v-if="totalAttachCount > 0" class="attach-count">{{ totalAttachCount }}</span>
        </button>
      </div>

      <!-- Submit -->
      <div class="submit-row">
        <button @click="submitPost" :disabled="!canSubmit || submitting" class="submit-btn">
          {{ submitting ? 'Публикация...' : 'Опубликовать' }}
        </button>
      </div>
    </div>

    <!-- ── Attach Content Modal ── -->
    <div v-if="showAttachModal" class="selector-modal" @click.self="showAttachModal = false">
      <div class="selector-content" @click.stop>
        <div class="selector-header">
          <span class="selector-title">Прикрепить</span>
          <button class="selector-close" @click="showAttachModal = false">✕</button>
        </div>

        <div class="attach-tabs">
          <button :class="{ active: attachTab === 'media' }" @click="attachTab = 'media'">📷 Фото/Видео</button>
          <button :class="{ active: attachTab === 'anime' }" @click="attachTab = 'anime'">🎬 Аниме</button>
          <button :class="{ active: attachTab === 'playlist' }" @click="switchToPlaylist">📁 Плейлист</button>
          <button :class="{ active: attachTab === 'shorts' }" @click="attachTab = 'shorts'; loadShorts()">⚡ Shorts</button>
        </div>

        <!-- ФОТО/ВИДЕО -->
        <div v-if="attachTab === 'media'" class="tab-content">
          <div class="media-upload-area" @click="triggerMediaPick">
            <div class="upload-icon">📷</div>
            <div class="upload-text">Нажмите для выбора фото или видео</div>
            <div class="upload-hint">Поддерживается мультивыбор</div>
          </div>
          <input ref="mediaInput" type="file" accept="image/*,video/*" multiple class="hidden-input" @change="onMediaSelected">
          
          <!-- Preview уже выбранных медиа -->
          <div v-if="mediaFiles.length > 0" class="selected-media-preview">
            <div class="selected-label">Выбрано {{ mediaFiles.length }} файл(ов):</div>
            <div class="media-preview-grid">
              <div v-for="(m, idx) in mediaFiles" :key="idx" class="preview-thumb">
                <img v-if="m.type === 'image'" :src="m.url" alt="">
                <video v-else :src="m.url" muted></video>
                <button class="remove-thumb-btn" @click="removeMedia(idx)">✕</button>
              </div>
            </div>
          </div>
        </div>

        <!-- АНИМЕ -->
        <div v-if="attachTab === 'anime'" class="tab-content">
          <input v-model="animeSearch" @input="searchAnime" placeholder="Поиск аниме..." class="selector-search">
          <div v-if="animeLoading" class="selector-loading">Загрузка...</div>
          <div class="results-list">
            <div
              v-for="a in animeResults"
              :key="a.id"
              class="result-item"
              :class="{ selected: attachedAnimes.some(x => x.id === a.id) }"
              @click="toggleAnime(a)"
            >
              <img :src="getAnimePoster(a)" alt="">
              <span class="result-item-title">{{ a.title_ru }}</span>
              <span class="check-icon">{{ attachedAnimes.some(x => x.id === a.id) ? '✓' : '' }}</span>
            </div>
            <div v-if="!animeLoading && animeResults.length === 0" class="no-results">Введите название для поиска</div>
          </div>
        </div>

        <!-- ПЛЕЙЛИСТ -->
        <div v-if="attachTab === 'playlist'" class="tab-content">
          <div v-if="playlistLoading" class="selector-loading">Загрузка плейлистов...</div>
          <div v-else-if="playlists.length === 0" class="no-results">
            <div>У вас пока нет плейлистов</div>
            <button class="create-playlist-btn" @click="goToPlaylists">Создать плейлист</button>
          </div>
          <div v-else class="results-list">
            <div
              v-for="p in playlists"
              :key="p.id"
              class="result-item"
              :class="{ selected: attachedPlaylists.some(x => x.id === p.id) }"
              @click="togglePlaylist(p)"
            >
              <img v-if="getPlaylistPoster(p)" :src="getPlaylistPoster(p)" alt="" class="playlist-thumb">
              <span v-else class="result-icon">📁</span>
              <div class="result-info">
                <span class="result-title">{{ p.title || p.name }}</span>
                <span class="result-sub">{{ p.anime_count || p.items_count || p.animes_count || 0 }} аниме</span>
              </div>
              <span class="check-icon">{{ attachedPlaylists.some(x => x.id === p.id) ? '✓' : '' }}</span>
            </div>
          </div>
        </div>

        <!-- SHORTS -->
        <div v-if="attachTab === 'shorts'" class="tab-content">
          <input v-model="shortsSearch" @input="searchShorts" placeholder="Поиск Shorts..." class="selector-search">
          <div v-if="shortsLoading" class="selector-loading">Загрузка...</div>
          <div class="results-list">
            <div
              v-for="s in shortsResults"
              :key="s.id"
              class="result-item"
              :class="{ selected: attachedShortsList.some(x => x.id === s.id) }"
              @click="toggleShorts(s)"
            >
              <span class="result-icon">⚡</span>
              <div class="result-info">
                <span class="result-title">{{ s.title || 'Shorts #' + s.id }}</span>
                <span class="result-sub">@{{ s.user?.username }}</span>
              </div>
              <span class="check-icon">{{ attachedShortsList.some(x => x.id === s.id) ? '✓' : '' }}</span>
            </div>
            <div v-if="!shortsLoading && shortsResults.length === 0" class="no-results">Не найдено</div>
          </div>
        </div>

        <button class="close-selector" @click="showAttachModal = false">Готово</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import apiClient, { getMediaUrl } from '@/api/client'
import playlistsApi from '@/api/playlists'
import { normalizePost } from '@/utils/normalizers'

const props = defineProps<{ initialType?: string | null }>()
const emit = defineEmits<{ close: []; created: [post: any] }>()

// ─── User ────────────────────────────────────────────
const currentUser = ref<any>(null)
const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3C/svg%3E`
const userAvatar = computed(() => currentUser.value?.avatar || defaultAvatar)
const userDisplayName = computed(() => currentUser.value?.display_name || currentUser.value?.username || '')

// ─── Post fields ──────────────────────────────────────
const text = ref('')
const visibility = ref('public')
const allowComments = ref(true)
const isSpoiler = ref(false)
const spoilerFor = ref('')
const showVisibilityMenu = ref(false)
const submitting = ref(false)
const textArea = ref<HTMLTextAreaElement | null>(null)

const visibilityOptions: Record<string, { icon: string; label: string }> = {
  public:    { icon: '🌍', label: 'Публично' },
  followers: { icon: '👥', label: 'Только подписчики' },
  friends:   { icon: '👫', label: 'Только друзья' },
  private:   { icon: '🔒', label: 'Только я' },
}

const setVisibility = (key: string) => { visibility.value = key; showVisibilityMenu.value = false }

// ─── Media (фото/видео) — мультивыбор ────────────────
interface MediaItem { type: 'image' | 'video'; url: string; file: File }
const mediaFiles = ref<MediaItem[]>([])
const mediaInput = ref<HTMLInputElement | null>(null)

const triggerMediaPick = () => mediaInput.value?.click()

const onMediaSelected = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  for (const file of Array.from(input.files)) {
    const type = file.type.startsWith('image') ? 'image' : 'video'
    const url = URL.createObjectURL(file)
    mediaFiles.value.push({ type, url, file })
  }
  input.value = ''
}

const removeMedia = (idx: number) => {
  const media = mediaFiles.value[idx]
  if (media) URL.revokeObjectURL(media.url)
  mediaFiles.value.splice(idx, 1)
}

// ─── Attached content — мультивыбор ─────────────────
const attachedAnimes = ref<any[]>([])
const animeRatings = ref<(number | null)[]>([])
const attachedPlaylists = ref<any[]>([])
const attachedShortsList = ref<any[]>([])

const hasAttachments = computed(() =>
  attachedAnimes.value.length > 0 || attachedPlaylists.value.length > 0 || attachedShortsList.value.length > 0
)
const attachCount = computed(() =>
  attachedAnimes.value.length + attachedPlaylists.value.length + attachedShortsList.value.length
)

// Общее количество всех прикреплений (включая медиа)
const hasAnyAttachments = computed(() =>
  mediaFiles.value.length > 0 || hasAttachments.value
)
const totalAttachCount = computed(() =>
  mediaFiles.value.length + attachCount.value
)

const removeAnime = (idx: number) => { attachedAnimes.value.splice(idx, 1); animeRatings.value.splice(idx, 1) }
const removePlaylist = (idx: number) => { attachedPlaylists.value.splice(idx, 1) }
const removeShorts = (idx: number) => { attachedShortsList.value.splice(idx, 1) }

const toggleAnime = (a: any) => {
  const idx = attachedAnimes.value.findIndex(x => x.id === a.id)
  if (idx >= 0) { attachedAnimes.value.splice(idx, 1); animeRatings.value.splice(idx, 1) }
  else { attachedAnimes.value.push(a); animeRatings.value.push(null) }
}
const togglePlaylist = (p: any) => {
  const idx = attachedPlaylists.value.findIndex(x => x.id === p.id)
  if (idx >= 0) attachedPlaylists.value.splice(idx, 1)
  else attachedPlaylists.value.push(p)
}
const toggleShorts = (s: any) => {
  const idx = attachedShortsList.value.findIndex(x => x.id === s.id)
  if (idx >= 0) attachedShortsList.value.splice(idx, 1)
  else attachedShortsList.value.push(s)
}

// ─── Attach modal ─────────────────────────────────────
const showAttachModal = ref(false)
const attachTab = ref<'media' | 'anime' | 'playlist' | 'shorts'>('media')

// Anime search
const animeSearch = ref('')
const animeResults = ref<any[]>([])
const animeLoading = ref(false)
let animeTimeout: ReturnType<typeof setTimeout> | null = null

// Функция для получения постера аниме - использует poster (локальный файл), затем poster_url
const getAnimePoster = (anime: any): string => {
  if (!anime) return ''
  // Сначала проверяем локальный файл poster
  if (anime.poster) {
    return getMediaUrl(anime.poster) || anime.poster_url || ''
  }
  // Fallback на poster_url
  if (anime.poster_url) {
    return getMediaUrl(anime.poster_url) || anime.poster_url
  }
  return ''
}

const searchAnime = () => {
  if (animeTimeout) clearTimeout(animeTimeout)
  animeTimeout = setTimeout(async () => {
    if (!animeSearch.value.trim()) { animeResults.value = []; return }
    animeLoading.value = true
    try {
      const { data } = await apiClient.get('/anime/', { params: { search: animeSearch.value, page_size: 20 } })
      animeResults.value = data.results || data || []
    } catch { animeResults.value = [] }
    finally { animeLoading.value = false }
  }, 300)
}

// Playlists — используем правильный API
const playlists = ref<any[]>([])
const playlistLoading = ref(false)

const loadPlaylists = async () => {
  if (playlistLoading.value) return
  playlistLoading.value = true
  
  try {
    // Сначала пробуем getMyPlaylists
    const { data } = await playlistsApi.getMyPlaylists()
    console.log('Playlists API response:', data)
    
    // Нормализуем данные
    if (Array.isArray(data)) {
      playlists.value = data
    } else if (data && typeof data === 'object') {
      // Если пришел объект с results
      playlists.value = (data as any).results || []
    } else {
      playlists.value = []
    }
    
    console.log('Loaded playlists count:', playlists.value.length)
    
    // Если плейлисты не загрузились, пробуем альтернативные варианты
    if (playlists.value.length === 0) {
      // Пробуем с параметром my=true
      try {
        const { data: data2 } = await apiClient.get('/playlists/playlists/', { 
          params: { my: 'true', page_size: 100 } 
        })
        console.log('Playlists my=true response:', data2)
        playlists.value = Array.isArray(data2) ? data2 : (data2 as any).results || []
      } catch (e) {
        console.error('Fallback playlists error:', e)
      }
    }
  } catch (e) {
    console.error('loadPlaylists error', e)
    
    // Fallback - пробуем прямой вызов
    try {
      const { data } = await apiClient.get('/playlists/playlists/my/')
      console.log('Playlists direct fallback:', data)
      playlists.value = Array.isArray(data) ? data : (data as any).results || []
    } catch (e2) {
      console.error('All playlist loading attempts failed', e2)
      playlists.value = []
    }
  } finally {
    playlistLoading.value = false
  }
}

const switchToPlaylist = () => {
  attachTab.value = 'playlist'
  loadPlaylists()
}

// Функция для получения постера плейлиста
const getPlaylistPoster = (playlist: any): string => {
  if (!playlist) return ''
  // Сначала пробуем cover_image
  if (playlist.cover_image) {
    return getMediaUrl(playlist.cover_image) || ''
  }
  // Затем poster_url
  if (playlist.poster_url) {
    return getMediaUrl(playlist.poster_url) || ''
  }
  return ''
}

// Shorts
const shortsSearch = ref('')
const shortsResults = ref<any[]>([])
const shortsLoading = ref(false)
let shortsTimeout: ReturnType<typeof setTimeout> | null = null

const loadShorts = async () => {
  shortsLoading.value = true
  try {
    const { data } = await apiClient.get('/reactor/my-posts/')
    shortsResults.value = data.results || []
  } catch { shortsResults.value = [] }
  finally { shortsLoading.value = false }
}

const searchShorts = () => {
  if (shortsTimeout) clearTimeout(shortsTimeout)
  shortsTimeout = setTimeout(async () => {
    shortsLoading.value = true
    try {
      const q = shortsSearch.value.trim()
      const url = q ? `/reactor/posts/?q=${q}` : '/reactor/my-posts/'
      const { data } = await apiClient.get(url)
      shortsResults.value = data.results || []
    } catch { shortsResults.value = [] }
    finally { shortsLoading.value = false }
  }, 300)
}

const openAttachModal = () => {
  showAttachModal.value = true
  attachTab.value = 'media' // По умолчанию открываем на вкладке медиа
}

const goToPlaylists = () => {
  // Закрываем модальное окно и перенаправляем на страницу плейлистов
  emit('close')
  window.location.href = '/playlists'
}

// ─── Submit ───────────────────────────────────────────
const canSubmit = computed(() => {
  const hasContent = text.value.trim().length > 0
    || mediaFiles.value.length > 0
    || attachedAnimes.value.length > 0
    || attachedPlaylists.value.length > 0
    || attachedShortsList.value.length > 0
  return hasContent && text.value.length <= 5000
})

const submitPost = async () => {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('text', text.value)
    fd.append('visibility', visibility.value)
    fd.append('allow_comments', String(allowComments.value))
    fd.append('is_spoiler', String(isSpoiler.value))
    if (isSpoiler.value && spoilerFor.value.trim()) {
      // Используем spoiler_description вместо spoiler_for (это текстовое описание)
      fd.append('spoiler_description', spoilerFor.value.trim())
    }

    // Аниме (первый — основной)
    if (attachedAnimes.value.length > 0) {
      fd.append('anime', String(attachedAnimes.value[0].id))
      if (animeRatings.value[0]) fd.append('anime_rating', String(animeRatings.value[0]))
      // Дополнительные
      attachedAnimes.value.slice(1).forEach((a, i) => {
        fd.append(`extra_anime_${i}`, String(a.id))
      })
    }
    if (attachedPlaylists.value.length > 0) {
      fd.append('playlist', String(attachedPlaylists.value[0].id))
      attachedPlaylists.value.slice(1).forEach((p, i) => {
        fd.append(`extra_playlist_${i}`, String(p.id))
      })
    }
    if (attachedShortsList.value.length > 0) {
      fd.append('reactor_post', String(attachedShortsList.value[0].id))
    }

    mediaFiles.value.forEach((m, i) => { fd.append(`media_${i}`, m.file) })

    console.log('Creating post with data:', {
      text: text.value,
      visibility: visibility.value,
      allow_comments: allowComments.value,
      is_spoiler: isSpoiler.value,
      spoiler_description: isSpoiler.value ? spoilerFor.value.trim() : '',
    })

    const { data } = await apiClient.post('/social/posts/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    emit('created', normalizePost(data))
  } catch (e: any) {
    console.error('Error creating post:', e)
    console.error('Error response:', e.response?.data)
    alert('Ошибка при публикации поста: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

// ─── Misc ─────────────────────────────────────────────
const autoResize = () => {
  if (!textArea.value) return
  textArea.value.style.height = 'auto'
  textArea.value.style.height = textArea.value.scrollHeight + 'px'
}

onMounted(async () => {
  try {
    const { data } = await apiClient.get('/users/me/')
    currentUser.value = data
  } catch {}
  await nextTick()
  textArea.value?.focus()
  if (props.initialType === 'playlist') { openAttachModal(); attachTab.value = 'playlist'; loadPlaylists() }
  else if (props.initialType === 'anime') { openAttachModal(); attachTab.value = 'anime' }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.82);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 1rem;
}

.create-post-modal {
  background: #111; border-radius: 16px; border: 1px solid #1f1f1f;
  width: 100%; max-width: 620px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
}

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; border-bottom: 1px solid #1f1f1f; }
.modal-header h2 { color: #fff; font-size: 1.1rem; margin: 0; }
.close-btn { background: none; border: none; color: #666; font-size: 1.2rem; cursor: pointer; }
.close-btn:hover { color: #fff; }

.author-row { display: flex; align-items: center; gap: 0.875rem; padding: 0.875rem 1.5rem; border-bottom: 1px solid #1a1a1a; }
.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.author-info { display: flex; flex-direction: column; gap: 0.2rem; }
.name { color: #fff; font-weight: 600; font-size: 0.9rem; }

.visibility-selector { position: relative; }
.visibility-btn {
  background: #1a1a1a; border: 1px solid #2a2a2a; color: #aaa;
  font-size: 0.8rem; padding: 0.25rem 0.6rem; border-radius: 6px; cursor: pointer;
}
.visibility-btn:hover { border-color: #667eea; color: #fff; }
.visibility-menu {
  position: absolute; top: calc(100% + 4px); left: 0;
  background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px;
  z-index: 20; min-width: 180px; padding: 0.25rem;
}
.visibility-menu button {
  display: block; width: 100%; text-align: left;
  background: none; border: none; color: #aaa; padding: 0.5rem 0.75rem;
  cursor: pointer; border-radius: 6px; font-size: 0.85rem;
}
.visibility-menu button:hover, .visibility-menu button.active { background: #252525; color: #fff; }

.content-area { padding: 1rem 1.5rem; display: flex; flex-direction: column; gap: 0.75rem; }
.text-input {
  width: 100%; min-height: 100px; background: transparent; border: none;
  border-bottom: 1px solid #222; color: #ddd; font-size: 1rem;
  line-height: 1.6; resize: none; box-sizing: border-box;
}
.text-input:focus { outline: none; border-bottom-color: #444; }
.text-input::placeholder { color: #444; }

.char-count { text-align: right; color: #555; font-size: 0.75rem; }
.char-count.warning { color: #f59e0b; }
.char-count.error { color: #ef4444; }

.media-preview { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.preview-item { position: relative; width: 80px; height: 80px; border-radius: 8px; overflow: hidden; }
.preview-item img, .preview-item video { width: 100%; height: 100%; object-fit: cover; }
.remove-media-btn {
  position: absolute; top: 3px; right: 3px;
  background: rgba(0,0,0,0.75); color: #fff; border: none;
  width: 20px; height: 20px; border-radius: 50%; cursor: pointer;
  font-size: 0.65rem; display: flex; align-items: center; justify-content: center;
}

.attached-list { display: flex; flex-direction: column; gap: 0.4rem; }
.attached-block {
  display: flex; align-items: center; gap: 0.6rem;
  background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px;
  padding: 0.5rem 0.75rem;
}
.attached-icon { font-size: 1.1rem; }
.attached-label { flex: 1; color: #ddd; font-size: 0.875rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rating-input { display: flex; align-items: center; gap: 0.4rem; color: #888; font-size: 0.8rem; flex-shrink: 0; }
.rating-field { width: 52px; background: #111; border: 1px solid #333; color: #fff; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.8rem; }
.remove-btn { background: none; border: none; color: #555; cursor: pointer; font-size: 0.9rem; padding: 0 0.25rem; }
.remove-btn:hover { color: #ef4444; }

.toggles-row { display: flex; gap: 1.25rem; flex-wrap: wrap; }
.toggle-label { 
  display: flex; align-items: center; gap: 0.5rem; 
  color: #aaa; font-size: 0.85rem; cursor: pointer; 
  user-select: none;
  transition: color 0.2s;
}
.toggle-label:hover { color: #ddd; }
.toggle-input { display: none; }

/* Toggle Switch */
.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 20px;
  transition: all 0.25s ease;
  flex-shrink: 0;
}
.toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: #555;
  border-radius: 50%;
  transition: all 0.25s ease;
}
.toggle-switch.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
}
.toggle-switch.active .toggle-slider {
  left: 18px;
  background: #fff;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
}
.toggle-text { line-height: 1; }

.spoiler-settings { margin-top: 0.5rem; }
.spoiler-for-input {
  width: 100%; background: #1a1a1a; border: 1px solid #2a2a2a;
  color: #ddd; padding: 0.5rem 0.75rem; border-radius: 8px;
  font-size: 0.875rem; box-sizing: border-box;
}
.spoiler-for-input:focus { outline: none; border-color: #fbbf24; }
.spoiler-for-input::placeholder { color: #555; }

.attachment-buttons {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0.75rem 1.5rem; border-top: 1px solid #1a1a1a; border-bottom: 1px solid #1a1a1a;
}
.attach-btn {
  position: relative;
  background: #1a1a1a; border: 1px solid #2a2a2a; font-size: 1.5rem;
  padding: 0.75rem 1.5rem; cursor: pointer; border-radius: 12px;
  transition: all 0.2s; opacity: 0.85;
}
.attach-btn:hover { background: #222; opacity: 1; }
.attach-btn.active { background: rgba(102,126,234,0.2); border-color: #667eea; opacity: 1; }
.attach-btn.main-attach {
  font-size: 1.6rem;
  padding: 0.875rem 2rem;
}
.attach-count {
  position: absolute; top: -4px; right: -4px;
  background: #667eea; color: #fff; font-size: 0.7rem;
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-weight: 700;
}
.hidden-input { display: none; }

.submit-row { padding: 0.875rem 1.5rem; }
.submit-btn {
  width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff; border: none; padding: 0.75rem; border-radius: 8px;
  font-weight: 600; cursor: pointer; font-size: 0.95rem;
  transition: opacity 0.2s, transform 0.2s;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-1px); }
.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Selector Modal ── */
.selector-modal {
  position: fixed; inset: 0; background: rgba(0,0,0,0.88);
  display: flex; align-items: center; justify-content: center; z-index: 1001; padding: 1rem;
}
.selector-content {
  background: #111; border-radius: 14px; border: 1px solid #222;
  width: 100%; max-width: 480px; max-height: 85vh;
  display: flex; flex-direction: column; overflow: hidden;
}
.selector-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 1rem 0; margin-bottom: 0.25rem;
}
.selector-title { color: #fff; font-weight: 600; font-size: 1rem; }
.selector-close {
  background: none; border: none; color: #666; font-size: 1rem; cursor: pointer;
}
.selector-close:hover { color: #fff; }

.attach-tabs { display: flex; border-bottom: 1px solid #1a1a1a; }
.attach-tabs button {
  flex: 1; background: none; border: none; color: #777;
  padding: 0.75rem; font-size: 0.875rem; cursor: pointer; transition: all 0.2s;
}
.attach-tabs button:hover { color: #aaa; }
.attach-tabs button.active { color: #fff; border-bottom: 2px solid #667eea; }

.tab-content { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

.selector-search {
  margin: 0.75rem; background: #1a1a1a;
  border: 1px solid #2a2a2a; color: #fff; padding: 0.6rem 0.875rem;
  border-radius: 8px; font-size: 0.875rem; box-sizing: border-box;
}
.selector-search:focus { outline: none; border-color: #667eea; }

.results-list { flex: 1; overflow-y: auto; padding: 0 0.75rem 0.75rem; max-height: 45vh; }
.result-item {
  display: flex; align-items: center; gap: 0.875rem;
  padding: 0.625rem 0.5rem; border-radius: 8px; cursor: pointer; transition: background 0.2s;
}
.result-item:hover { background: #1a1a1a; }
.result-item.selected { background: rgba(102,126,234,0.12); border: 1px solid rgba(102,126,234,0.3); }
.result-item img { width: 44px; height: 64px; object-fit: cover; border-radius: 5px; flex-shrink: 0; }
.result-item-title { color: #ddd; font-size: 0.9rem; flex: 1; }
.result-icon { font-size: 1.4rem; flex-shrink: 0; }
.result-info { display: flex; flex-direction: column; gap: 0.15rem; flex: 1; }
.result-title { color: #ddd; font-size: 0.9rem; font-weight: 500; }
.result-sub { color: #666; font-size: 0.78rem; }
.check-icon { color: #667eea; font-size: 1rem; font-weight: 700; min-width: 16px; text-align: center; }
.playlist-thumb { width: 44px; height: 64px; object-fit: cover; border-radius: 5px; flex-shrink: 0; }

.selector-loading { color: #666; font-size: 0.875rem; text-align: center; padding: 1.5rem; }
.no-results { color: #555; font-size: 0.875rem; text-align: center; padding: 1.5rem; }

.close-selector {
  margin: 0.75rem; background: #667eea; border: none; color: #fff;
  padding: 0.625rem; border-radius: 8px; cursor: pointer; font-size: 0.875rem;
  font-weight: 600;
}
.close-selector:hover { background: #5a6fd6; }

/* Media Upload Area */
.media-upload-area {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 2rem 1rem; margin: 0.75rem; background: #1a1a1a;
  border: 2px dashed #333; border-radius: 12px; cursor: pointer;
  transition: all 0.2s;
}
.media-upload-area:hover { background: #222; border-color: #444; }
.upload-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.upload-text { color: #aaa; font-size: 0.95rem; font-weight: 500; }
.upload-hint { color: #555; font-size: 0.8rem; margin-top: 0.25rem; }

.selected-media-preview { margin: 0.75rem; padding: 0.75rem; background: #1a1a1a; border-radius: 8px; }
.selected-label { color: #888; font-size: 0.8rem; margin-bottom: 0.5rem; }
.media-preview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 0.5rem; }
.preview-thumb { position: relative; aspect-ratio: 1; border-radius: 8px; overflow: hidden; }
.preview-thumb img, .preview-thumb video { width: 100%; height: 100%; object-fit: cover; }
.remove-thumb-btn {
  position: absolute; top: 4px; right: 4px;
  background: rgba(0,0,0,0.75); color: #fff; border: none;
  width: 22px; height: 22px; border-radius: 50%; cursor: pointer;
  font-size: 0.7rem; display: flex; align-items: center; justify-content: center;
}
.remove-thumb-btn:hover { background: #ef4444; }

.create-playlist-btn {
  margin-top: 0.75rem; background: #667eea; border: none; color: #fff;
  padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; font-size: 0.85rem;
}
</style>