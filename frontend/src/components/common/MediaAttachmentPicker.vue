<template>
  <!-- Кнопки прикрепления -->
  <div class="map-buttons">
    <button
      v-if="allowPhoto"
      @click="triggerFileInput('image')"
      class="map-btn"
      :class="{ active: hasImages }"
      title="Фото"
      type="button"
    >
      <slot name="icon-photo"> <SakuraIcon name="camera" /> </slot>
    </button>
    <button
      v-if="allowVideo"
      @click="triggerFileInput('video')"
      class="map-btn"
      :class="{ active: hasVideo }"
      title="Видео"
      type="button"
    >
      <slot name="icon-video"> <SakuraIcon name="film" /> </slot>
    </button>
    <button
      v-if="allowAnime"
      @click="openAnimeSelector"
      class="map-btn"
      :class="{ active: !!attachedAnime }"
      title="Аниме"
      type="button"
    >
      <slot name="icon-anime"> <SakuraIcon name="play" /> </slot>
    </button>

    <!-- Скрытые file-инпуты -->
    <input
      ref="imageInputRef"
      type="file"
      accept="image/jpeg,image/png,image/gif,image/webp"
      multiple
      @change="handleImageSelect"
      hidden
    >
    <input
      ref="videoInputRef"
      type="file"
      accept="video/mp4,video/webm,video/quicktime"
      @change="handleVideoSelect"
      hidden
    >
  </div>

  <!-- Превью медиа -->
  <div v-if="mediaFiles.length > 0" class="map-media-preview">
    <div
      v-for="(item, index) in mediaFiles"
      :key="index"
      class="map-preview-item"
    >
      <img v-if="item.type === 'image'" :src="item.url" alt="preview">
      <video v-else :src="item.url" muted></video>
      <button class="map-remove-btn" @click="removeMedia(index)" type="button">✕</button>
    </div>
  </div>

  <!-- Превью аниме -->
  <div v-if="attachedAnime" class="map-anime-preview">
    <img
      :src="resolvedAnimePoster"
      :alt="attachedAnime.title_ru"
      class="map-anime-poster"
      @error="onPosterError"
    >
    <div class="map-anime-info">
      <span class="map-anime-title">{{ attachedAnime.title_ru }}</span>
      <span v-if="attachedAnime.title_en" class="map-anime-subtitle">{{ attachedAnime.title_en }}</span>
      <slot name="anime-extra" :anime="attachedAnime" />
    </div>
    <button class="map-remove-btn map-remove-anime" @click="removeAnime" type="button">✕</button>
  </div>

  <!-- Модалка выбора аниме (телепортируется в body) -->
  <Teleport to="body">
    <div v-if="showAnimeSelector" class="map-overlay" @click.self="showAnimeSelector = false">
      <div class="map-selector-modal" @click.stop>
        <div class="map-selector-header">
          <h3>Выберите аниме</h3>
          <button class="map-close-btn" @click="showAnimeSelector = false" type="button">✕</button>
        </div>

        <div class="map-search-wrap">
          <input
            v-model="animeQuery"
            type="text"
            placeholder="Поиск аниме..."
            class="map-search-input"
            @input="debouncedSearch"
            autofocus
          >
          <span v-if="searching" class="map-search-spinner"> <SakuraIcon name="hourglass" /> </span>
        </div>

        <div class="map-results">
          <div v-if="searching && animeResults.length === 0" class="map-state">Поиск...</div>
          <div v-else-if="!searching && animeQuery.length >= 2 && animeResults.length === 0" class="map-state">Ничего не найдено</div>
          <div v-else-if="animeQuery.length < 2" class="map-state map-hint">Введите 2+ символа для поиска</div>

          <div
            v-for="anime in animeResults"
            :key="anime.id"
            class="map-result-item"
            @click="selectAnime(anime)"
          >
            <img
              :src="resolveAnimeResultPoster(anime)"
              :alt="anime.title_ru"
              class="map-result-poster"
              @error="(e) => (e.target as HTMLImageElement).style.visibility = 'hidden'"
            >
            <div class="map-result-info">
              <span class="map-result-title">{{ anime.title_ru }}</span>
              <span v-if="anime.title_en" class="map-result-subtitle">{{ anime.title_en }}</span>
            </div>
          </div>
        </div>

        <button class="map-cancel-btn" @click="showAnimeSelector = false" type="button">Отмена</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import apiClient, { getMediaUrl } from '@/api/client'

// ─── Props ───────────────────────────────────────────────────────────────────

interface Props {
  allowPhoto?: boolean
  allowVideo?: boolean
  allowAnime?: boolean
  maxImages?: number
  maxImageSizeMb?: number
  maxVideoSizeMb?: number
}

const props = withDefaults(defineProps<Props>(), {
  allowPhoto: true,
  allowVideo: true,
  allowAnime: true,
  maxImages: 10,
  maxImageSizeMb: 10,
  maxVideoSizeMb: 100,
})

// ─── Emits ───────────────────────────────────────────────────────────────────

const emit = defineEmits<{
  /** Список файлов изменился */
  'update:mediaFiles': [files: MediaFile[]]
  /** Прикреплённое аниме изменилось */
  'update:attachedAnime': [anime: AnimeAttachment | null]
  /** Ошибка */
  'error': [message: string]
}>()

// ─── Types ───────────────────────────────────────────────────────────────────

export interface MediaFile {
  type: 'image' | 'video'
  url: string      // ObjectURL для превью
  file: File
}

export interface AnimeAttachment {
  id: number
  title_ru: string
  title_en?: string
  poster_url?: string
  poster_image_url?: string
}

// ─── State ───────────────────────────────────────────────────────────────────

const imageInputRef = ref<HTMLInputElement | null>(null)
const videoInputRef = ref<HTMLInputElement | null>(null)

const mediaFiles = ref<MediaFile[]>([])
const attachedAnime = ref<AnimeAttachment | null>(null)

const showAnimeSelector = ref(false)
const animeQuery = ref('')
const animeResults = ref<any[]>([])
const searching = ref(false)

// ─── Computed ────────────────────────────────────────────────────────────────

const hasImages = computed(() => mediaFiles.value.some(f => f.type === 'image'))
const hasVideo = computed(() => mediaFiles.value.some(f => f.type === 'video'))

const resolvedAnimePoster = computed(() => {
  if (!attachedAnime.value) return ''
  const raw = attachedAnime.value.poster_url || attachedAnime.value.poster_image_url || ''
  return getMediaUrl(raw) || '/placeholder-anime.jpg'
})

// ─── Public API (expose) ─────────────────────────────────────────────────────

/** Сбросить все выбранные медиа и аниме */
const reset = () => {
  mediaFiles.value.forEach(f => URL.revokeObjectURL(f.url))
  mediaFiles.value = []
  attachedAnime.value = null
  emit('update:mediaFiles', [])
  emit('update:attachedAnime', null)
}

defineExpose({ reset, mediaFiles, attachedAnime })

// ─── File handling ────────────────────────────────────────────────────────────

const triggerFileInput = (type: 'image' | 'video') => {
  if (type === 'image') imageInputRef.value?.click()
  else videoInputRef.value?.click()
}

const handleImageSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])

  for (const file of files) {
    if (mediaFiles.value.length >= props.maxImages) {
      emit('error', `Максимум ${props.maxImages} изображений`)
      break
    }
    if (file.size > props.maxImageSizeMb * 1024 * 1024) {
      emit('error', `Максимальный размер фото: ${props.maxImageSizeMb} МБ`)
      continue
    }
    const url = URL.createObjectURL(file)
    mediaFiles.value.push({ type: 'image', url, file })
  }

  input.value = ''
  emit('update:mediaFiles', [...mediaFiles.value])
}

const handleVideoSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > props.maxVideoSizeMb * 1024 * 1024) {
    emit('error', `Максимальный размер видео: ${props.maxVideoSizeMb} МБ`)
    input.value = ''
    return
  }

  // Заменяем предыдущее видео
  const existingVideoIdx = mediaFiles.value.findIndex(f => f.type === 'video')
  if (existingVideoIdx !== -1) {
    URL.revokeObjectURL(mediaFiles.value[existingVideoIdx]!.url)
    mediaFiles.value.splice(existingVideoIdx, 1)
  }

  const url = URL.createObjectURL(file)
  mediaFiles.value.push({ type: 'video', url, file })
  input.value = ''
  emit('update:mediaFiles', [...mediaFiles.value])
}

const removeMedia = (index: number) => {
  URL.revokeObjectURL(mediaFiles.value[index]!.url)
  mediaFiles.value.splice(index, 1)
  emit('update:mediaFiles', [...mediaFiles.value])
}

// ─── Anime ────────────────────────────────────────────────────────────────────

const openAnimeSelector = () => {
  animeQuery.value = ''
  animeResults.value = []
  showAnimeSelector.value = true
}

const removeAnime = () => {
  attachedAnime.value = null
  emit('update:attachedAnime', null)
}

const onPosterError = (e: Event) => {
  (e.target as HTMLImageElement).src = '/placeholder-anime.jpg'
}

const resolveAnimeResultPoster = (anime: any): string => {
  const raw = anime.poster_url || anime.poster_image_url || ''
  return getMediaUrl(raw) || '/placeholder-anime.jpg'
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(doSearch, 350)
}

const doSearch = async () => {
  const q = animeQuery.value.trim()
  if (q.length < 2) {
    animeResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await apiClient.get('/anime/search/', { params: { q, limit: 15 } })
    animeResults.value = res.data.results || []
  } catch {
    animeResults.value = []
  } finally {
    searching.value = false
  }
}

const selectAnime = (anime: any) => {
  attachedAnime.value = {
    id: anime.id,
    title_ru: anime.title_ru,
    title_en: anime.title_en,
    poster_url: anime.poster_url,
    poster_image_url: anime.poster_image_url,
  }
  showAnimeSelector.value = false
  emit('update:attachedAnime', attachedAnime.value)
}
</script>

<style scoped>
/* ── Кнопки ── */
.map-buttons {
  display: contents; /* не добавляет обёртку, кнопки вставляются прямо в родительский flex/grid */
}

.map-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  padding: 0.45rem 0.6rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s, transform 0.1s, opacity 0.15s;
  opacity: 0.65;
  line-height: 1;
}

.map-btn:hover {
  background: rgba(255,255,255,0.06);
  opacity: 1;
  transform: scale(1.1);
}

.map-btn.active {
  opacity: 1;
  background: rgba(102, 126, 234, 0.15);
}

/* ── Превью медиа ── */
.map-media-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.map-preview-item {
  position: relative;
  width: 90px;
  height: 90px;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
  flex-shrink: 0;
}

.map-preview-item img,
.map-preview-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ── Превью аниме ── */
.map-anime-preview {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.75rem;
  padding: 0.65rem 0.85rem;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  position: relative;
}

.map-anime-poster {
  width: 48px;
  height: 68px;
  object-fit: cover;
  border-radius: 5px;
  flex-shrink: 0;
}

.map-anime-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.map-anime-title {
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.map-anime-subtitle {
  color: #666;
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Кнопка удаления ── */
.map-remove-btn {
  position: absolute;
  top: 0.25rem;
  right: 0.25rem;
  width: 22px;
  height: 22px;
  background: rgba(0,0,0,0.75);
  color: #ccc;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  transition: background 0.15s, color 0.15s;
  line-height: 1;
  padding: 0;
}

.map-remove-btn:hover {
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
}

.map-remove-anime {
  position: static; /* в аниме-превью кнопка не абсолютная */
  flex-shrink: 0;
  margin-left: auto;
}

/* ── Оверлей модалки ── */
.map-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.map-selector-modal {
  background: #111;
  border: 1px solid #1f1f1f;
  border-radius: 14px;
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
}

.map-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1f1f1f;
}

.map-selector-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
}

.map-close-btn {
  background: none;
  border: none;
  color: #555;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
  transition: color 0.15s;
}

.map-close-btn:hover { color: #fff; }

/* ── Поиск ── */
.map-search-wrap {
  position: relative;
  padding: 0.85rem 1.25rem 0.6rem;
}

.map-search-input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.65rem 2.5rem 0.65rem 0.85rem;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.map-search-input:focus {
  outline: none;
  border-color: #667eea;
}

.map-search-input::placeholder { color: #444; }

.map-search-spinner {
  position: absolute;
  right: 2rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.85rem;
  margin-top: 0.1rem;
}

/* ── Результаты ── */
.map-results {
  flex: 1;
  overflow-y: auto;
  padding: 0.4rem 1.25rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.map-state {
  color: #555;
  font-size: 0.85rem;
  text-align: center;
  padding: 1.5rem 0;
}

.map-hint { color: #3a3a3a; }

.map-result-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.map-result-item:hover { background: #1a1a1a; }

.map-result-poster {
  width: 44px;
  height: 62px;
  object-fit: cover;
  border-radius: 5px;
  flex-shrink: 0;
  background: #1a1a1a;
}

.map-result-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.map-result-title {
  color: #e0e0e0;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.map-result-subtitle {
  color: #555;
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Кнопка отмены ── */
.map-cancel-btn {
  margin: 0.5rem 1.25rem 1rem;
  background: #1a1a1a;
  color: #666;
  border: none;
  border-radius: 8px;
  padding: 0.65rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.map-cancel-btn:hover {
  background: #222;
  color: #aaa;
}

/* ── Scrollbar ── */
.map-results::-webkit-scrollbar { width: 4px; }
.map-results::-webkit-scrollbar-track { background: transparent; }
.map-results::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
</style>
