<template>
  <div class="search-bar" :class="{ focused: isFocused }">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <div
        ref="searchInput"
        class="search-input"
        contenteditable="true"
        data-placeholder="Поиск аниме..."
        @input="handleInput"
        @keydown.enter.prevent="handleSearch"
        @focus="isFocused = true"
        @blur="handleBlur"
      ></div>
      <button 
        v-if="searchQuery" 
        class="search-clear"
        @click="clearSearch"
        type="button"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- Выпадающие результаты -->
    <transition name="dropdown">
      <div v-if="showResults && (hasResults || isLoading)" class="search-results">
        <!-- Загрузка -->
        <div v-if="isLoading" class="search-loading">
          <div class="loading-spinner"></div>
          <span>Поиск...</span>
        </div>

        <!-- Результаты -->
        <template v-else>
          <!-- Аниме -->
          <div v-if="searchResults.anime?.length" class="search-section">
            <div class="search-section-title">Аниме</div>
            <div 
              v-for="anime in searchResults.anime.slice(0, 5)" 
              :key="anime.id"
              class="search-result-item"
              @click="goToAnime(anime.id)"
            >
              <img 
                v-if="anime.poster_image_url && getMediaUrl(anime.poster_image_url)"
                :src="getMediaUrl(anime.poster_image_url) || undefined"
                :alt="anime.title_ru || anime.title_en"
                class="result-poster"
              />
              <div v-else class="result-poster-placeholder">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M12 2v20M2 12h20"/>
                </svg>
              </div>
              <div class="result-info">
                <div class="result-title">{{ anime.title_ru || anime.title_en }}</div>
                <div class="result-meta">
                  <span v-if="anime.year">{{ anime.year }}</span>
                  <span v-if="anime.episodes">{{ anime.episodes }} эп.</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Нет результатов -->
          <div v-if="!hasResults" class="search-no-results">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <p>Ничего не найдено</p>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'

interface SearchResult {
  id: number
  title_ru?: string
  title_en?: string
  poster_image_url?: string
  year?: number
  episodes?: number
}

interface SearchResults {
  anime?: SearchResult[]
}

const router = useRouter()
const searchInput = ref<HTMLDivElement | null>(null)

const searchQuery = ref('')
const isFocused = ref(false)
const isLoading = ref(false)
const searchResults = ref<SearchResults>({})

const showResults = computed(() => {
  return isFocused.value && (searchQuery.value.length >= 2 || Object.keys(searchResults.value).length > 0)
})

const hasResults = computed(() => {
  return Object.values(searchResults.value).some(arr => arr && arr.length > 0)
})

let searchTimeout: number | null = null

const handleInput = () => {
  if (searchInput.value) {
    const text = searchInput.value.innerText.trim()
    searchQuery.value = text
    
    // Если текст пустой, очищаем div полностью
    if (!text) {
      searchInput.value.innerHTML = ''
    }
  }

  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  if (searchQuery.value.length < 2) {
    searchResults.value = {}
    return
  }

  searchTimeout = window.setTimeout(() => {
    // TODO: Implement search when API is available
    // performSearch()
  }, 300)
}

const performSearch = async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    return
  }

  isLoading.value = true
  
  try {
    // TODO: Implement search API call
    // const response = await animeApi.search(searchQuery.value, { limit: 20 })
    // searchResults.value = { anime: response.data.results || [] }
    searchResults.value = { anime: [] }
  } catch (error) {
    console.error('Search error:', error)
    searchResults.value = {}
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  if (searchQuery.value) {
    router.push({ path: '/search', query: { q: searchQuery.value } })
    isFocused.value = false
    searchInput.value?.blur()
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = {}
  if (searchInput.value) {
    searchInput.value.innerHTML = ''
  }
  searchInput.value?.focus()
}

const handleBlur = () => {
  setTimeout(() => {
    isFocused.value = false
  }, 200)
}

const goToAnime = (id: number) => {
  router.push({ path: `/anime/${id}` })
  isFocused.value = false
}

watch(() => router.currentRoute.value, () => {
  isFocused.value = false
})
</script>

<style scoped>
.search-bar {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  background-color: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 20px;
  padding: 0 12px 0 16px;
}

.search-icon {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  transition: color 0.15s var(--transition-smooth);
}

.search-bar.focused .search-icon {
  color: var(--color-accent);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text);
  font-size: 14px;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-input:empty::before {
  content: attr(data-placeholder);
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-clear {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-text-tertiary);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s var(--transition-smooth);
}

.search-clear:hover {
  color: var(--color-text);
}

/* Результаты поиска */
.search-results {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-card-hover);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

.search-section {
  padding: 8px 0;
}

.search-section-title {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  background-color: var(--color-background-secondary);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.15s var(--transition-smooth);
}

.search-result-item:hover {
  background-color: var(--color-background-surface);
}

.result-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.result-poster-placeholder {
  width: 40px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  border-radius: 4px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin: 0 0 2px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin: 0;
  display: flex;
  gap: 8px;
}

/* Загрузка */
.search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Нет результатов */
.search-no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 32px;
  color: var(--color-text-tertiary);
  text-align: center;
}

.search-no-results p {
  margin: 0;
  font-size: 14px;
}

/* Анимации */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s var(--transition-smooth);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
