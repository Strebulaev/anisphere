<template>
  <Teleport to="body">
  <Transition name="psm-anim">
    <div v-if="show" class="modal-overlay" @click.self="handleClose" @keydown.esc="handleClose">
      <div class="modal-content playlist-select-modal">
        <div class="modal-header">
          <h2 class="modal-title">Добавить в плейлист</h2>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="anime-preview">
            <div v-if="animePosterUrl" style="width: 80px; height: 112px; flex-shrink: 0; border-radius: 8px; overflow: hidden;">
              <img
                :src="animePosterUrl"
                :alt="anime.title_ru || anime.title_en"
                style="width: 100%; height: 100%; object-fit: cover;"
                loading="lazy"
              />
            </div>
            <div v-else class="anime-poster-placeholder">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="2" width="20" height="20" rx="2"/>
                <path d="M12 2v20M2 12h20"/>
              </svg>
            </div>
            <div class="anime-info">
              <h3 class="anime-title">{{ anime.title_ru || anime.title_en }}</h3>
              <p v-if="anime.year" class="anime-year">{{ anime.year }}</p>
            </div>
          </div>

          <div class="playlists-section">
            <div class="playlists-header">
              <h4 class="playlists-title">Выберите плейлисты</h4>
              <button
                @click="handleCreatePlaylist"
                class="create-playlist-btn"
                type="button"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Создать новый
              </button>
            </div>

            <div v-if="searchQuery" class="playlists-search">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Поиск плейлистов..."
                class="search-input"
              />
            </div>

            <div class="playlists-list">
              <div v-if="isLoading" class="playlists-loading">
                <div class="loading-spinner"></div>
                <span>Загрузка...</span>
              </div>

              <div v-else-if="filteredPlaylists.length === 0" class="playlists-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
                <p>{{ searchQuery ? 'Плейлисты не найдены' : 'У вас пока нет плейлистов' }}</p>
              </div>

              <label
                v-for="playlist in filteredPlaylists"
                :key="playlist.id"
                :class="['playlist-item', { selected: selectedPlaylists.includes(playlist.id) }]"
              >
                <input
                  type="checkbox"
                  :value="playlist.id"
                  v-model="selectedPlaylists"
                  class="playlist-checkbox"
                />
                <div class="playlist-cover">
                  <div class="playlist-mini-posters">
                    <template v-if="playlist.cover_urls && playlist.cover_urls.length">
                      <div
                        v-for="(url, index) in playlist.cover_urls.slice(0, 4)"
                        :key="index"
                        class="mini-poster"
                      >
                        <img :src="url" alt="" loading="lazy" />
                      </div>
                    </template>
                    <template v-else-if="playlist.items?.length">
                      <div
                        v-for="(item, index) in playlist.items.slice(0, 4)"
                        :key="index"
                        class="mini-poster"
                      >
                        <img
                          v-if="item.anime_poster || item.anime_poster_url"
                          :src="getMediaUrl(item.anime_poster) || getMediaUrl(item.anime_poster_url) || undefined"
                          alt=""
                          loading="lazy"
                        />
                      </div>
                    </template>
                    <div v-else class="mini-poster-empty">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M9 18V5l12-2v13"/>
                        <circle cx="6" cy="18" r="3"/>
                        <circle cx="18" cy="16" r="3"/>
                      </svg>
                    </div>
                  </div>
                </div>
                <div class="playlist-info">
                  <div class="playlist-name">{{ playlist.title }}</div>
                  <div class="playlist-meta">
                    {{ playlist.items?.length || 0 }} аниме
                  </div>
                </div>
                <div class="playlist-privacy">
                  <svg v-if="!playlist.is_public" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  </svg>
                </div>
              </label>
            </div>
          </div>

          <div class="note-section">
            <label class="note-label">Заметка (необязательно)</label>
            <textarea
              v-model="note"
              placeholder="Добавьте заметку к аниме..."
              class="note-input"
              rows="2"
              maxlength="150"
            ></textarea>
            <div class="note-counter">{{ note.length }}/150</div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            Отмена
          </button>
          <button
            @click="handleSave"
            :disabled="selectedPlaylists.length === 0"
            class="btn btn-primary"
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Добавить
          </button>
        </div>
      </div>
    </div>
  </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Anime, Playlist } from '@/types'
import { getMediaUrl } from '@/api/client'

// Computed для получения URL постера аниме
const animePosterUrl = computed(() => {
  const a = props.anime
  
  // Пробуем разные поля для постера (приоритет: poster -> poster_file -> poster_image_url -> poster_url)
  const posterFields = [
    a.poster,
    a.poster_file,
    a.poster_image_url,
    a.poster_url
  ]
  
  for (const poster of posterFields) {
    if (poster && typeof poster === 'string' && poster.trim() !== '') {
      const url = getMediaUrl(poster)
      if (url) return url
    }
  }
  return null
})

interface Props {
  show: boolean
  anime: Anime
  playlists?: Playlist[]
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  playlists: () => [],
  isLoading: false
})

const emit = defineEmits<{
  close: []
  save: [data: PlaylistSaveData]
  createPlaylist: []
}>()

interface PlaylistSaveData {
  animeId: number
  playlistIds: number[]
  note?: string
}

const selectedPlaylists = ref<number[]>([])
const searchQuery = ref('')
const note = ref('')

const filteredPlaylists = computed(() => {
  if (!searchQuery.value) {
    return props.playlists
  }
  
  const query = searchQuery.value.toLowerCase()
  return props.playlists.filter(playlist =>
    playlist.title.toLowerCase().includes(query)
  )
})

const handleSave = () => {
  const data: PlaylistSaveData = {
    animeId: props.anime.id,
    playlistIds: selectedPlaylists.value,
    note: note.value || undefined
  }
  
  emit('save', data)
  resetForm()
}

const handleCreatePlaylist = () => {
  emit('createPlaylist')
}

const handleClose = () => {
  emit('close')
}

const resetForm = () => {
  selectedPlaylists.value = []
  searchQuery.value = ''
  note.value = ''
}

onMounted(() => {
  if (props.show) {
    selectedPlaylists.value = []
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--surface-2, var(--color-background-surface));
  border-radius: 1rem;
  max-width: 500px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  transform: scale(1);
  opacity: 1;
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle, var(--color-divider));
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--color-background-active);
  color: var(--color-accent-pink);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.anime-preview {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: var(--color-background-active);
  border-radius: 0.5rem;
  margin-bottom: 1.25rem;
}

.anime-poster {
  width: 48px;
  height: 67px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.anime-poster-placeholder {
  width: 48px;
  height: 67px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  border-radius: 0.375rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.anime-year {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.playlists-section {
  margin-bottom: 1.25rem;
}

.playlists-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.playlists-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.create-playlist-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-accent);
  border: none;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.create-playlist-btn:hover {
  background-color: var(--color-accent-hover);
  transform: translateY(-1px);
}

.playlists-search {
  margin-bottom: 0.75rem;
}

.search-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.search-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.playlists-list {
  max-height: 250px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.playlists-loading,
.playlists-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem 1rem;
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.playlists-empty p {
  margin: 0;
  font-size: 0.875rem;
  text-align: center;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.playlist-item:hover {
  border-color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.playlist-item.selected {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--color-accent);
}

.playlist-checkbox {
  display: none;
}

.playlist-cover {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 0.375rem;
  overflow: hidden;
  background-color: var(--color-background-surface);
}

.playlist-mini-posters {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 1px;
  width: 100%;
  height: 100%;
}

.mini-poster {
  background-color: var(--color-background-active);
}

.mini-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-poster-empty {
  grid-column: span 2;
  grid-row: span 2;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  background-color: var(--color-background-active);
  width: 100%;
  height: 100%;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.125rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.playlist-privacy {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.note-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.note-label {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.note-input {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  resize: vertical;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
}

.note-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.note-counter {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-align: right;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* Анимация на overlay (fade) и на modal-content (scale+slide) */
.psm-anim-enter-active { transition: opacity 0.22s ease; }
.psm-anim-leave-active { transition: opacity 0.18s ease; }
.psm-anim-enter-from,
.psm-anim-leave-to { opacity: 0; }

.psm-anim-enter-active .modal-content {
  transition: transform 0.25s cubic-bezier(0.34, 1.4, 0.64, 1), opacity 0.22s ease;
}
.psm-anim-leave-active .modal-content {
  transition: transform 0.18s ease, opacity 0.18s ease;
}
.psm-anim-enter-from .modal-content {
  transform: scale(0.90) translateY(20px);
  opacity: 0;
}
.psm-anim-leave-to .modal-content {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .playlists-list {
    max-height: 200px;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
