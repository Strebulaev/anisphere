<template>
  <div class="create-playlist-view">
    <div class="container mx-auto px-4 py-8 max-w-2xl">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">📁 Создать плейлист</h1>
        <p class="text-gray-600">Создайте коллекцию аниме для себя или поделитесь с сообществом</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <form @submit.prevent="createPlaylist" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Название плейлиста</label>
            <input
              v-model="form.title"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Топ романтических аниме"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="form.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Расскажите о вашей подборке"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Тип плейлиста</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  v-model="form.is_public"
                  type="radio"
                  :value="true"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Публичный (виден всем)</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="form.is_public"
                  type="radio"
                  :value="false"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Приватный (только для меня)</span>
              </label>
            </div>
          </div>

          <!-- Добавление аниме в плейлист -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Добавить аниме <span class="text-red-500">*</span>
            </label>
            <div class="anime-selector">
              <div class="search-box">
                <input
                  v-model="searchQuery"
                  type="text"
                  @input="searchAnime"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Поиск аниме..."
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
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Заметки (необязательно)
                  </label>
                  <textarea
                    v-model="animeNotes"
                    rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Добавьте заметки к аниме..."
                  ></textarea>
                </div>
              </div>

              <div v-if="!selectedAnime && searchQuery && !searching" class="text-center py-4 text-gray-500">
                Ничего не найдено
              </div>
            </div>
            <p v-if="!selectedAnime" class="text-sm text-red-500 mt-1">
              * Обязательно выберите хотя бы одно аниме
            </p>
          </div>

          <div class="flex gap-4">
            <button
              type="button"
              @click="$router.back()"
              class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              :disabled="loading || !selectedAnime"
              class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {{ loading ? 'Создание...' : 'Создать плейлист' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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

const router = useRouter()
const loading = ref(false)
const searching = ref(false)
const searchQuery = ref('')
const searchResults = ref<Anime[]>([])
const selectedAnime = ref<Anime | null>(null)
const animeNotes = ref('')

const form = ref({
  title: '',
  description: '',
  is_public: true
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

const createPlaylist = async () => {
  if (!selectedAnime.value) {
    alert('Выберите хотя бы одно аниме для плейлиста')
    return
  }

  loading.value = true

  try {
    // Создаем плейлист
    const playlistResponse = await apiClient.post('/playlists/playlists/', form.value)
    const playlistId = playlistResponse.data.id

    // Добавляем аниме в плейлист
    await playlistsApi.addToPlaylist({
      anime_id: selectedAnime.value.id,
      playlist_id: playlistId,
      notes: animeNotes.value
    })

    alert('Плейлист успешно создан!')
    router.push(`/playlist/${playlistId}`)
  } catch (error: any) {
    alert('Ошибка при создании плейлиста: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-playlist-view {
  min-height: 100vh;
  background: var(--color-background);
}

.anime-selector {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.search-box {
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.anime-results {
  max-height: 300px;
  overflow-y: auto;
}

.anime-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background 0.2s;
}

.anime-item:hover {
  background: #222222;
}

.anime-item.selected {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid #3b82f6;
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
  color: #1f2937;
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-meta {
  font-size: 0.8125rem;
  color: #6b7280;
}

.anime-check {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  font-size: 1.25rem;
  font-weight: 700;
}

.selected-anime {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
}

.selected-anime-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f9fafb;
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
  color: #1f2937;
  margin: 0;
}

.remove-btn {
  padding: 0.375rem 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
  align-self: flex-start;
}

.remove-btn:hover {
  background: #fecaca;
}

.notes-section {
  margin-top: 0.75rem;
}
</style>