<template>
  <Modal @close="$emit('close')">
    <div class="create-playlist-modal">
      <h2>Создание плейлиста</h2>

      <form @submit.prevent="handleSubmit">
        <!-- Название -->
        <div class="form-group">
          <label>Название *</label>
          <input
            v-model="form.title"
            type="text"
            placeholder="Название плейлиста"
            required
          />
        </div>

        <!-- Описание -->
        <div class="form-group">
          <label>Описание</label>
          <textarea
            v-model="form.description"
            placeholder="Описание плейлиста"
            rows="3"
          ></textarea>
        </div>

        <!-- Видимость -->
        <div class="form-group">
          <label>Видимость</label>
          <div class="visibility-options">
            <label class="radio-option">
              <input type="radio" v-model="form.visibility" value="public" />
              <span><SakuraIcon name="globe" /> Публичный</span>
            </label>
            <label class="radio-option">
              <input type="radio" v-model="form.visibility" value="private" />
              <span><SakuraIcon name="lock" /> Приватный</span>
            </label>
            <label class="radio-option">
              <input type="radio" v-model="form.visibility" value="link" />
              <span><SakuraIcon name="link" /> По ссылке</span>
            </label>
          </div>
        </div>

        <!-- Поиск аниме -->
        <div class="form-group">
          <label>Добавить аниме *</label>
          <div class="search-wrapper">
            <SearchBar
              @search="handleAnimeSearch"
              placeholder="Поиск аниме..."
            />
          </div>

          <!-- Результаты поиска -->
          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="anime in searchResults"
              :key="anime.id"
              @click="addAnime(anime)"
              class="anime-result"
            >
              <img :src="anime.poster" :alt="anime.title_ru" class="anime-poster" />
              <div class="anime-info">
                <span class="anime-title">{{ anime.title_ru }}</span>
                <span class="anime-meta">{{ anime.year }} • {{ anime.episodes_count }} эп.</span>
              </div>
              <button type="button" class="btn-add">
                <PlusIcon class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- Добавленные аниме -->
          <div v-if="selectedAnime.length > 0" class="selected-anime">
            <div class="section-title">Добавленные аниме:</div>
            <div class="anime-list">
              <div
                v-for="(anime, index) in selectedAnime"
                :key="anime.id"
                class="selected-anime-item"
              >
                <img :src="anime.poster" :alt="anime.title_ru" class="anime-poster" />
                <span class="anime-title">{{ anime.title_ru }}</span>
                <button type="button" @click="removeAnime(index)" class="btn-remove">
                  <XMarkIcon class="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="selectedAnime.length === 0" class="hint">
            Добавьте хотя бы одно аниме для создания плейлиста
          </div>
        </div>

        <!-- Ошибка -->
        <div v-if="error" class="error">{{ error }}</div>

        <!-- Кнопки -->
        <div class="form-actions">
          <button type="button" @click="$emit('close')" class="btn-cancel">
            Отмена
          </button>
          <button
            type="submit"
            :disabled="!canSubmit || loading"
            class="btn-submit"
          >
            {{ loading ? 'Создание...' : 'Создать плейлист' }}
          </button>
        </div>
      </form>
    </div>
  </Modal>
</template>

<script setup>
import { ref, computed } from 'vue'
import { PlusIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import SearchBar from '@/components/Search/SearchBar.vue'
import api from '@/api'

const emit = defineEmits(['close', 'created'])

const form = ref({
  title: '',
  description: '',
  visibility: 'public',
})

const searchResults = ref([])
const selectedAnime = ref([])
const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  return form.value.title.trim() && selectedAnime.value.length > 0
})

const handleAnimeSearch = async (query) => {
  if (!query || query.length < 2) {
    searchResults.value = []
    return
  }

  try {
    const response = await api.get('/anime/', { params: { search: query, limit: 10 } })
    searchResults.value = response.data.results || response.data

    // Убираем уже добавленные
    const addedIds = selectedAnime.value.map(a => a.id)
    searchResults.value = searchResults.value.filter(a => !addedIds.includes(a.id))
  } catch (err) {
    console.error('Ошибка поиска аниме:', err, err?.response?.data)
    searchResults.value = []
  }
}

const addAnime = (anime) => {
  if (!selectedAnime.value.find(a => a.id === anime.id)) {
    selectedAnime.value.push(anime)
  }
  searchResults.value = []
}

const removeAnime = (index) => {
  selectedAnime.value.splice(index, 1)
}

const handleSubmit = async () => {
  if (!canSubmit.value) {
    error.value = 'Заполните название и добавьте хотя бы одно аниме'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await api.post('/playlists/', {
      title: form.value.title,
      description: form.value.description,
      visibility: form.value.visibility,
      anime_list: selectedAnime.value.map(a => a.id),
    })

    emit('created', response.data)
    emit('close')
  } catch (err) {
    console.error('Ошибка создания плейлиста:', err)
    error.value = err.response?.data?.detail || 'Ошибка создания плейлиста'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-playlist-modal {
  padding: 24px;
  max-width: 600px;
}

.create-playlist-modal h2 {
  margin: 0 0 24px;
  font-size: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.visibility-options {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.radio-option input {
  cursor: pointer;
}

.search-wrapper {
  margin-bottom: 12px;
}

.search-results {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 16px;
}

.anime-result {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  cursor: pointer;
  transition: background 0.3s;
}

.anime-result:hover {
  background: #f9f9f9;
}

.anime-poster {
  width: 40px;
  height: 60px;
  border-radius: 6px;
  object-fit: cover;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  display: block;
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.anime-meta {
  font-size: 12px;
  color: #999;
}

.btn-add {
  width: 32px;
  height: 32px;
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

.btn-add:hover {
  background: #5568d3;
}

.selected-anime {
  margin-top: 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.anime-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.selected-anime-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 8px;
}

.selected-anime-item .anime-poster {
  width: 32px;
  height: 48px;
}

.selected-anime-item .anime-title {
  flex: 1;
  font-size: 13px;
}

.btn-remove {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #999;
  transition: all 0.3s;
}

.btn-remove:hover {
  background: #f5f5f5;
  color: #f44336;
}

.hint {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
}

.error {
  padding: 10px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
  font-size: 13px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #f5f5f5;
}

.btn-submit {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn-submit:hover:not(:disabled) {
  background: #5568d3;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
