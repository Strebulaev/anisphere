<template>
  <div class="modal-overlay" v-if="show" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Добавить аниме</h2>
        <button @click="close" class="close-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <!-- Поиск -->
        <div class="search-section">
          <div class="search-input-wrapper">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск аниме..."
              @input="handleSearch"
              @keydown.enter="handleSearch"
              class="search-input"
            >
            <button @click="handleSearch" class="search-btn">Найти</button>
          </div>
        </div>

        <!-- Результаты поиска -->
        <div v-if="loading" class="loading-container">
          <div class="spinner"></div>
          <p>Поиск...</p>
        </div>

        <div v-else-if="searchResults.length === 0 && searchQuery" class="no-results">
          <div class="no-results-icon">🔍</div>
          <p>Ничего не найдено</p>
        </div>

        <div v-else-if="searchResults.length > 0" class="search-results">
          <div
            v-for="anime in searchResults"
            :key="anime.id"
            class="result-item"
            :class="{ selected: selectedAnime?.id === anime.id }"
            @click="selectAnime(anime)"
          >
            <img :src="anime.poster_url" :alt="anime.title_ru" class="result-poster">
            <div class="result-info">
              <h4 class="result-title">{{ anime.title_ru || anime.title_en }}</h4>
              <div class="result-meta">
                <span v-if="anime.year">{{ anime.year }}</span>
                <span v-if="anime.episodes">{{ anime.episodes }} эп.</span>
                <span v-if="anime.score" class="rating">★ {{ anime.score.toFixed(1) }}</span>
              </div>
            </div>
            <svg v-if="selectedAnime?.id === anime.id" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="check-icon">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
        </div>

        <!-- Подсказка, если нет поиска -->
        <div v-else class="search-hint">
          <div class="hint-icon">📚</div>
          <h3>Найдите аниме</h3>
          <p>Введите название аниме, чтобы добавить его в свой список</p>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="close" class="btn btn-outline">Отмена</button>
        <button @click="addToLibrary" class="btn btn-primary" :disabled="!selectedAnime || loading">
          <span v-if="loading" class="btn-spinner"></span>
          {{ loading ? 'Добавление...' : 'Добавить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '@/api/client'

interface Props {
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  added: []
}>()

const searchQuery = ref('')
const searchResults = ref<any[]>([])
const selectedAnime = ref<any>(null)
const loading = ref(false)

const handleSearch = async () => {
  if (!searchQuery.value.trim() || loading.value) return

  try {
    loading.value = true
    const response = await apiClient.get('/anime/search/', {
      params: { q: searchQuery.value }
    })
    searchResults.value = response.data.results || []
  } catch (err) {
    console.error('Ошибка поиска:', err)
    searchResults.value = []
  } finally {
    loading.value = false
  }
}

const selectAnime = (anime: any) => {
  selectedAnime.value = anime
}

const addToLibrary = async () => {
  if (!selectedAnime.value) return

  try {
    loading.value = true
    await apiClient.post('/library/', {
      anime: selectedAnime.value.id,
      status: 'want_to_watch'
    })
    emit('added')
    close()
  } catch (err: any) {
    console.error('Ошибка добавления:', err)
    if (err.response?.data?.error) {
      alert(err.response.data.error)
    } else {
      alert('Не удалось добавить аниме')
    }
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
  searchQuery.value = ''
  searchResults.value = []
  selectedAnime.value = null
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 20px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(90deg);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

/* Поиск */
.search-section {
  margin-bottom: 1.5rem;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.2s;
}

.search-input-wrapper:focus-within {
  border-color: #3b82f6;
  background: rgba(255, 255, 255, 0.08);
}

.search-icon {
  color: #6b7280;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1rem;
  outline: none;
}

.search-input::placeholder {
  color: #6b7280;
}

.search-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 255, 0.4);
}

/* Результаты */
.loading-container,
.no-results,
.search-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #a0a0a0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-results-icon,
.hint-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(4px);
}

.result-item.selected {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}

.result-poster {
  width: 50px;
  height: 75px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #a0a0a0;
}

.result-meta .rating {
  color: #fbbf24;
}

.check-icon {
  color: #22c55e;
  flex-shrink: 0;
}

/* Футер */
.modal-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-outline {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.btn-outline:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Адаптивность */
@media (max-width: 640px) {
  .modal-container {
    max-height: 90vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 1rem;
  }

  .search-input-wrapper {
    flex-wrap: wrap;
  }

  .search-btn {
    width: 100%;
  }
}
</style>
