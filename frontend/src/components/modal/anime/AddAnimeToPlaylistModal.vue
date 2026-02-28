<template>
  <BaseModal
    :show="show"
    @close="$emit('close')"
    title="Добавить аниме в плейлист"
  >
    <form @submit.prevent="handleSubmit" class="add-anime-form">
      <!-- Поиск аниме -->
      <div class="form-group">
        <label class="form-label">Поиск аниме</label>
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            @input="searchAnime"
            class="form-input"
            placeholder="Введите название аниме..."
          />
        </div>

        <div v-if="searching" class="text-center py-4 text-gray-500">
          Поиск...
        </div>

        <div v-else-if="searchResults.length > 0" class="anime-results">
          <div
            v-for="anime in searchResults"
            :key="anime.id"
            class="anime-item"
            :class="{ selected: selectedAnime?.id === anime.id }"
            @click="selectAnime(anime)"
          >
            <img
              :src="anime.poster_url"
              :alt="anime.title_ru"
              class="anime-poster"
            />
            <div class="anime-info">
              <h4 class="anime-title">{{ anime.title_ru }}</h4>
              <div class="anime-meta">
                <span v-if="anime.year">{{ anime.year }}</span>
                <span v-if="anime.score">⭐ {{ anime.score?.toFixed(1) }}</span>
              </div>
            </div>
            <div class="anime-check">
              <span v-if="selectedAnime?.id === anime.id">✓</span>
            </div>
          </div>
        </div>

        <div v-if="!selectedAnime && searchQuery && !searching" class="text-center py-4 text-gray-500">
          Ничего не найдено
        </div>
      </div>

      <!-- Выбранное аниме -->
      <div v-if="selectedAnime" class="selected-anime">
        <div class="selected-anime-card">
          <img
            :src="selectedAnime.poster_url"
            :alt="selectedAnime.title_ru"
            class="selected-poster"
          />
          <div class="selected-info">
            <h4 class="selected-title">{{ selectedAnime.title_ru }}</h4>
            <button
              type="button"
              @click="selectedAnime = null"
              class="remove-btn"
            >
              Убрать
            </button>
          </div>
        </div>

        <!-- Заметки к аниме -->
        <div class="notes-section">
          <label class="form-label">Заметки (необязательно)</label>
          <textarea
            v-model="animeNotes"
            rows="3"
            class="form-input"
            placeholder="Добавьте заметки к аниме..."
          ></textarea>
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
          :disabled="loading || !selectedAnime"
        >
          {{ loading ? 'Добавление...' : 'Добавить' }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import apiClient from '@/api/client'
import playlistsApi from '@/api/playlists'

interface Anime {
  id: number
  title_ru: string
  title_en: string
  poster_url: string
  year?: number | null
  score?: number | null
}

interface Props {
  show: boolean
  playlistId: number
}

interface Emits {
  (e: 'close'): void
  (e: 'added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const searching = ref(false)
const searchQuery = ref('')
const searchResults = ref<Anime[]>([])
const selectedAnime = ref<Anime | null>(null)
const animeNotes = ref('')

// Сброс при открытии
watch(() => props.show, (show) => {
  if (show) {
    searchQuery.value = ''
    searchResults.value = []
    selectedAnime.value = null
    animeNotes.value = ''
  }
})

const searchAnime = async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }

  searching.value = true
  
  try {
    const response = await apiClient.get(`/anime/anime/?search=${encodeURIComponent(searchQuery.value)}`)
    searchResults.value = response.data.results || []
  } catch (error) {
    console.error('Ошибка поиска:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

const selectAnime = (anime: Anime) => {
  selectedAnime.value = anime
  searchQuery.value = ''
  searchResults.value = []
}

const handleSubmit = async () => {
  if (!selectedAnime.value) return

  loading.value = true

  try {
    await playlistsApi.addToPlaylist({
      anime_id: selectedAnime.value.id,
      playlist_id: props.playlistId,
      notes: animeNotes.value
    })

    emit('added')
    emit('close')
  } catch (error: any) {
    console.error('Ошибка добавления:', error)
    alert('Не удалось добавить аниме: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.add-anime-form {
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

.search-box {
  padding: 0.25rem 0;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--color-text-disabled);
}

.anime-results {
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.anime-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.2s;
}

.anime-item:hover {
  background: var(--color-surface);
}

.anime-item.selected {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid var(--color-accent);
}

.anime-poster {
  width: 48px;
  height: 68px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-meta {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.anime-check {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  font-size: 1.25rem;
  font-weight: 700;
}

.selected-anime {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.selected-anime-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-surface);
  border-radius: 0.5rem;
}

.selected-poster {
  width: 80px;
  height: 110px;
  object-fit: cover;
  border-radius: 0.5rem;
  flex-shrink: 0;
}

.selected-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.selected-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.remove-btn {
  padding: 0.375rem 0.75rem;
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
  align-self: flex-start;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.notes-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
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
