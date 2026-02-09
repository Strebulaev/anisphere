<template>
  <div class="add-to-playlist">
    <button
      v-if="!showModal"
      class="add-btn"
      @click="openModal"
    >
      <span class="icon">📋</span>
      <span class="text">В плейлист</span>
    </button>

    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <h3>Добавить в плейлист</h3>
            <button class="close-btn" @click="closeModal">✕</button>
          </div>

          <div class="modal-body">
            <!-- Существующие плейлисты -->
            <div class="playlists-section" v-if="playlists.length > 0">
              <h4>Ваши плейлисты</h4>
              <div class="playlist-list">
                <div
                  v-for="playlist in playlists"
                  :key="playlist.id"
                  :class="['playlist-item', { disabled: playlistItems.has(playlist.id) }]"
                  @click="addToExistingPlaylist(playlist.id)"
                >
                  <div class="playlist-info">
                    <span class="playlist-title">{{ playlist.title }}</span>
                    <span class="playlist-count">{{ playlist.items_count }} аниме</span>
                  </div>
                  <span v-if="playlistItems.has(playlist.id)" class="check-icon">✓</span>
                </div>
              </div>
            </div>

            <!-- Создать новый плейлист -->
            <div class="new-playlist-section">
              <h4>Создать новый плейлист</h4>
              <div class="new-playlist-form">
                <input
                  v-model="newPlaylistTitle"
                  type="text"
                  placeholder="Название плейлиста"
                  class="input"
                  @keyup.enter="createAndAdd"
                />
                <label class="checkbox-label">
                  <input type="checkbox" v-model="newPlaylistPublic" />
                  <span>Публичный</span>
                </label>
                <button
                  class="create-btn"
                  @click="createAndAdd"
                  :disabled="!newPlaylistTitle.trim() || loading"
                >
                  {{ loading ? '...' : 'Создать и добавить' }}
                </button>
              </div>
            </div>

            <!-- Сообщение об ошибке -->
            <div v-if="error" class="error-message">
              {{ error }}
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import playlistsApi, { type Playlist } from '@/api/playlists'

interface Props {
  animeId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  added: [playlistId: number]
  error: [message: string]
}>()

const showModal = ref(false)
const loading = ref(false)
const error = ref('')
const playlists = ref<Playlist[]>([])
const playlistItems = ref<Set<number>>(new Set())
const newPlaylistTitle = ref('')
const newPlaylistPublic = ref(false)

const loadPlaylists = async () => {
  try {
    const response = await playlistsApi.getMyPlaylists()
    playlists.value = response.data

    playlistItems.value = new Set(
      playlists.value
        .filter(p => p.items.some((item: any) => item.anime === props.animeId))
        .map(p => p.id)
    )
  } catch (err) {
    console.error('Ошибка загрузки плейлистов:', err)
  }
}

const openModal = () => {
  showModal.value = true
  loadPlaylists()
}

const closeModal = () => {
  showModal.value = false
  newPlaylistTitle.value = ''
  error.value = ''
}

const addToExistingPlaylist = async (playlistId: number) => {
  if (playlistItems.value.has(playlistId)) return

  loading.value = true
  error.value = ''

  try {
    await playlistsApi.addItemToPlaylist(playlistId, {
      anime: props.animeId
    })

    playlistItems.value.add(playlistId)
    playlistItems.value = new Set(playlistItems.value)
    emit('added', playlistId)
    closeModal()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка добавления в плейлист'
  } finally {
    loading.value = false
  }
}

const createAndAdd = async () => {
  if (!newPlaylistTitle.value.trim()) return

  loading.value = true
  error.value = ''

  try {
    const createResponse = await playlistsApi.createPlaylist({
      title: newPlaylistTitle.value.trim(),
      is_public: newPlaylistPublic.value
    })

    const newPlaylist = createResponse.data

    await playlistsApi.addItemToPlaylist(newPlaylist.id, {
      anime: props.animeId
    })

    emit('added', newPlaylist.id)
    closeModal()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Ошибка создания плейлиста'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  background: var(--color-background-surface);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(58, 134, 255, 0.1);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: var(--color-background-surface);
  border-radius: 1rem;
  width: 100%;
  max-width: 420px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.close-btn {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  font-size: 1.25rem;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--color-background-active);
  color: var(--color-text-primary);
}

.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
}

.playlists-section,
.new-playlist-section {
  margin-bottom: 1.5rem;
}

.playlists-section h4,
.new-playlist-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.playlist-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.playlist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-background);
}

.playlist-item:hover:not(.disabled) {
  border-color: var(--color-accent);
  background: rgba(58, 134, 255, 0.1);
}

.playlist-item.disabled {
  opacity: 0.6;
  cursor: default;
}

.playlist-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.playlist-title {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text);
}

.playlist-count {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.check-icon {
  color: var(--color-accent);
  font-weight: bold;
}

.new-playlist-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  outline: none;
  background: var(--color-background);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.input:focus {
  border-color: var(--color-accent);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.checkbox-label input {
  width: 1rem;
  height: 1rem;
  accent-color: var(--color-accent);
}

.create-btn {
  padding: 0.75rem 1rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.create-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.create-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  padding: 0.75rem 1rem;
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 0.5rem;
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 1rem;
}
</style>