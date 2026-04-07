<template>
  <BaseModal
    :show="show"
    @close="$emit('close')"
    title="Добавить в плейлист"
  >
    <form @submit.prevent="handleSubmit" class="add-to-playlist-form">
      <!-- Выбор плейлиста -->
      <div class="form-group">
        <label class="form-label">Выберите плейлист</label>
        
        <div class="playlists-list">
          <div
            v-for="playlist in playlists"
            :key="playlist.id"
            class="playlist-option"
            :class="{ selected: selectedPlaylistId === playlist.id }"
            @click="selectedPlaylistId = playlist.id"
          >
            <div class="playlist-option-cover">
              <img
                v-if="playlist.cover_image"
                :src="playlist.cover_image"
                :alt="playlist.title"
              />
              <div v-else class="cover-placeholder">
                <span>{{ playlist.title.charAt(0).toUpperCase() }}</span>
              </div>
            </div>
            <div class="playlist-option-info">
              <h4 class="playlist-option-title">{{ playlist.title }}</h4>
              <p class="playlist-option-meta">
                {{ playlist.items_count }} аниме
              </p>
            </div>
            <div class="playlist-option-check">
              <span v-if="selectedPlaylistId === playlist.id">✓</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Создание нового плейлиста -->
      <div class="form-group">
        <label class="form-label">Или создайте новый</label>
        <input
          v-model="newPlaylistTitle"
          type="text"
          class="form-input"
          placeholder="Название нового плейлиста"
        />
        <textarea
          v-model="newPlaylistDescription"
          rows="2"
          class="form-input"
          placeholder="Описание (необязательно)"
          style="margin-top: 0.5rem;"
        ></textarea>
      </div>

      <!-- Дополнительные поля -->
      <div class="form-group">
        <label class="form-label">Заметки</label>
        <textarea
          v-model="form.notes"
          rows="3"
          class="form-input"
          placeholder="Добавьте заметки к аниме..."
        ></textarea>
      </div>

      <!-- Информация об аниме -->
      <div v-if="anime" class="anime-preview">
        <img
          v-if="anime.poster_url"
          :src="anime.poster_url"
          :alt="anime.title_ru"
          class="anime-poster"
        />
        <div class="anime-info">
          <h4 class="anime-title">{{ anime.title_ru }}</h4>
          <div class="anime-meta">
            <span v-if="anime.year"><SakuraIcon name="calendar" /> {{ anime.year }}</span>
            <span v-if="anime.score"><SakuraIcon name="star" /> {{ anime.score?.toFixed(1) }}</span>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button
          type="button"
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Отмена
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading || !canSubmit"
        >
          {{ loading ? 'Добавление...' : 'Добавить' }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import playlistsApi from '@/api/playlists'

interface Anime {
  id: number
  title_ru: string
  title_en: string
  poster_url?: string | null
  year?: number | null
  score?: number | null
}

interface Props {
  show: boolean
  anime: Anime
}

interface Emits {
  (e: 'close'): void
  (e: 'added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const playlists = ref<any[]>([])
const selectedPlaylistId = ref<number | null>(null)
const newPlaylistTitle = ref('')
const newPlaylistDescription = ref('')

const form = ref({
  notes: ''
})

const canSubmit = computed(() => {
  return selectedPlaylistId.value !== null || newPlaylistTitle.value.trim().length > 0
})

// Загрузка плейлистов при открытии
watch(() => props.show, async (show) => {
  if (show) {
    await loadPlaylists()
    // Сброс формы
    selectedPlaylistId.value = null
    newPlaylistTitle.value = ''
    newPlaylistDescription.value = ''
    form.value.notes = ''
  }
})

const loadPlaylists = async () => {
  try {
    const response = await playlistsApi.getMyPlaylists()
    playlists.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки плейлистов:', error)
  }
}

const handleSubmit = async () => {
  if (!canSubmit.value) return

  loading.value = true

  try {
    const data: any = {
      anime_id: props.anime.id,
      notes: form.value.notes
    }

    if (selectedPlaylistId.value !== null) {
      data.playlist_id = selectedPlaylistId.value
    } else {
      data.new_playlist_title = newPlaylistTitle.value
      data.new_playlist_description = newPlaylistDescription.value
    }

    await playlistsApi.addToPlaylist(data)
    emit('added')
    emit('close')
  } catch (error: any) {
    console.error('Ошибка добавления в плейлист:', error)
    alert('Не удалось добавить в плейлист: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.show) {
    loadPlaylists()
  }
})
</script>

<style scoped>
.add-to-playlist-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
  padding: 0.25rem;
}

.playlist-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 2px solid var(--color-border);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.playlist-option:hover {
  border-color: var(--color-accent);
  background: var(--color-surface);
}

.playlist-option.selected {
  border-color: var(--color-accent);
  background: rgba(59, 130, 246, 0.1);
}

.playlist-option-cover {
  width: 48px;
  height: 48px;
  border-radius: 0.375rem;
  overflow: hidden;
  flex-shrink: 0;
}

.playlist-option-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-hover) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.playlist-option-info {
  flex: 1;
  min-width: 0;
}

.playlist-option-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-option-meta {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

.playlist-option-check {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  font-size: 1.25rem;
  font-weight: 700;
}

.form-input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: all 0.2s;
  resize: vertical;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--color-text-disabled);
}

.anime-preview {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-surface);
  border-radius: 0.75rem;
}

.anime-poster {
  width: 60px;
  height: 85px;
  object-fit: cover;
  border-radius: 0.5rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.anime-poster.placeholder {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-hover) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.anime-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.anime-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.anime-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}

.btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-surface-hover);
}

.btn-primary {
  background: var(--color-accent);
  color: white;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
