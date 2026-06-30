<template>
  <div class="random-section">
    <div class="random-hero">
      <div class="hero-content">
        <div class="hero-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2"/>
          </svg>
        </div>
        <h2 class="hero-title">Случайное аниме</h2>
        <p class="hero-description">Не можете выбрать? Пусть случай решит за вас!</p>
        <button
          @click="handleGoToRandom"
          :disabled="isNavigating"
          class="lucky-btn"
          type="button"
        >
          <svg v-if="!isNavigating" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          {{ isNavigating ? 'Поиск...' : 'Мне повезёт!' }}
        </button>
      </div>
    </div>

    <!-- Фильтры -->
    <div v-if="showFilters" class="section-filters">
      <div class="filter-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="filters.search"
          type="text"
          placeholder="Поиск по названию..."
          class="filter-input"
        />
      </div>
      <div class="filter-year">
        <input
          v-model="filters.yearFrom"
          type="number"
          placeholder="От"
          class="filter-input filter-input-small"
          min="1900"
          :max="new Date().getFullYear()"
        />
        <span class="filter-year-sep">-</span>
        <input
          v-model="filters.yearTo"
          type="number"
          placeholder="До"
          class="filter-input filter-input-small"
          min="1900"
          :max="new Date().getFullYear()"
        />
      </div>
      <div class="filter-sort">
        <select v-model="filters.sortBy" class="filter-select">
          <option value="-score">По рейтингу ↓</option>
          <option value="score">По рейтингу ↑</option>
          <option value="-year">По году ↓</option>
          <option value="year">По году ↑</option>
          <option value="title_ru">По названию</option>
        </select>
      </div>
      <button v-if="hasActiveFilters" @click="resetFilters" class="reset-filters-btn" type="button">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        Сбросить
      </button>
    </div>

    <div v-if="loading" class="random-list random-loading">
      <LoadingState type="skeleton" :count="6" />
    </div>

    <div v-else-if="error" class="random-list random-error">
      <ErrorState
        title="Не удалось загрузить случайные аниме"
        :message="error"
        :show-retry="true"
        @retry="handleRefresh"
      />
    </div>

    <div v-else-if="animeList.length === 0" class="random-list random-empty">
      <EmptyState
        title="Нет данных"
        message="Не удалось загрузить случайные аниме"
        icon="default"
      />
    </div>

    <div v-else class="random-list">
      <div class="list-header">
        <h3>Другие случайные аниме</h3>
        <div class="header-actions">
          <button v-if="showShuffle" @click="handleShuffle" class="shuffle-btn" type="button" :disabled="loading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="16 3 21 3 21 8"/>
              <line x1="4" y1="20" x2="21" y2="3"/>
              <polyline points="21 16 21 21 16 21"/>
              <line x1="15" y1="15" x2="21" y2="21"/>
              <line x1="4" y1="4" x2="9" y2="9"/>
            </svg>
            Перемешать
          </button>
          <button v-if="showShuffle && isShuffled" @click="handleUnshuffle" class="unshuffle-btn" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
            </svg>
            Сбросить
          </button>
          <button @click="handleRefresh" class="refresh-btn" type="button" :disabled="loading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Обновить
          </button>
        </div>
      </div>

      <div v-if="filteredAnimeList.length === 0 && hasActiveFilters" class="no-results">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <p>По вашему запросу ничего не найдено</p>
      </div>
      <div v-else class="anime-grid">
        <div
          v-for="anime in filteredAnimeList"
          :key="anime.id"
          @click="handleAnimeClick(anime)"
          class="anime-card"
        >
          <img
            v-if="anime.poster_url"
            :src="getMediaUrl(anime.poster_url) || undefined"
            :alt="anime.title_ru || anime.title_en"
            class="anime-poster"
          />
          <div v-else class="anime-poster-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="20" height="20" rx="2"/>
              <path d="M12 2v20M2 12h20"/>
            </svg>
          </div>
          <div class="anime-info">
            <span class="anime-title">{{ anime.title_ru || anime.title_en }}</span>
            <div class="anime-meta">
              <span v-if="anime.year" class="meta-item">{{ anime.year }}</span>
              <span v-if="anime.episodes" class="meta-item">{{ anime.episodes }} эп.</span>
              <span v-if="(anime as any).score" class="meta-item rating"><SakuraIcon name="star" /> {{ (anime as any).score.toFixed(1) }}</span>
            </div>
          </div>
          <div class="anime-overlay">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="10 8 16 12 10 16 10 8"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { LoadingState, ErrorState, EmptyState } from '@/components/Info'
import { getMediaUrl } from '@/api/client'
import type { Anime } from '@/types'

interface Props {
  animeList: Anime[]
  loading: boolean
  error: string | null
  showShuffle?: boolean
  showFilters?: boolean
  isShuffled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showShuffle: false,
  showFilters: false,
  isShuffled: false
})

const emit = defineEmits<{
  refresh: []
  shuffle: []
  unshuffle: []
  goToRandom: []
  animeClick: [anime: Anime]
}>()

const router = useRouter()
const isNavigating = ref(false)

const filters = ref({
  search: '',
  yearFrom: '',
  yearTo: '',
  sortBy: '-score'
})

const hasActiveFilters = computed(() => {
  return filters.value.search !== '' || 
         filters.value.yearFrom !== '' || 
         filters.value.yearTo !== '' || 
         filters.value.sortBy !== '-score'
})

const filteredAnimeList = computed(() => {
  let list = [...props.animeList]
  
  if (filters.value.search) {
    const searchLower = filters.value.search.toLowerCase()
    list = list.filter(anime => 
      (anime.title_ru && anime.title_ru.toLowerCase().includes(searchLower)) ||
      (anime.title_en && anime.title_en.toLowerCase().includes(searchLower))
    )
  }
  
  if (filters.value.yearFrom) {
    const yearFrom = parseInt(filters.value.yearFrom)
    list = list.filter(anime => anime.year && anime.year >= yearFrom)
  }
  
  if (filters.value.yearTo) {
    const yearTo = parseInt(filters.value.yearTo)
    list = list.filter(anime => anime.year && anime.year <= yearTo)
  }
  
  switch (filters.value.sortBy) {
    case '-score':
      list.sort((a, b) => ((b as any).score || 0) - ((a as any).score || 0))
      break
    case 'score':
      list.sort((a, b) => ((a as any).score || 0) - ((b as any).score || 0))
      break
    case '-year':
      list.sort((a, b) => (b.year || 0) - (a.year || 0))
      break
    case 'year':
      list.sort((a, b) => (a.year || 0) - (b.year || 0))
      break
    case 'title_ru':
      list.sort((a, b) => (a.title_ru || a.title_en || '').localeCompare(b.title_ru || b.title_en || ''))
      break
  }
  
  return list
})

const resetFilters = () => {
  filters.value = {
    search: '',
    yearFrom: '',
    yearTo: '',
    sortBy: '-score'
  }
}

const handleGoToRandom = async () => {
  isNavigating.value = true
  try {
    emit('goToRandom')
  } finally {
    setTimeout(() => {
      isNavigating.value = false
    }, 500)
  }
}

const handleRefresh = () => {
  emit('refresh')
}

const handleShuffle = () => {
  emit('shuffle')
}

const handleUnshuffle = () => {
  emit('unshuffle')
}

const handleAnimeClick = (anime: Anime) => {
  emit('animeClick', anime)
  router.push(`/anime/${anime.id}`)
}
</script>

<style scoped>
.random-section {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid var(--color-divider);
}

.random-hero {
  padding: 3rem 2rem;
  background: linear-gradient(135deg, var(--color-accent-purple) 0%, var(--color-accent-pink) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-content {
  text-align: center;
  color: var(--color-text);
}

.hero-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  backdrop-filter: blur(10px);
}

.hero-icon svg {
  color: #fff;
}

.hero-title {
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 0.75rem 0;
  color: #fff;
}

.hero-description {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 2rem 0;
}

.lucky-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2.5rem;
  background-color: #fff;
  border: none;
  border-radius: 1rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-accent-purple);
  cursor: pointer;
  transition: all 0.3s var(--transition-smooth);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.lucky-btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.lucky-btn:active:not(:disabled) {
  transform: translateY(-1px) scale(1);
}

.lucky-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.random-list {
  padding: 1.5rem;
}

.random-loading,
.random-error,
.random-empty {
  min-height: 400px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.list-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.shuffle-btn,
.unshuffle-btn,
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.shuffle-btn:hover:not(:disabled),
.unshuffle-btn:hover:not(:disabled),
.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-accent-purple);
  color: var(--color-accent-purple);
  background-color: var(--color-background-surface);
}

.shuffle-btn:disabled,
.unshuffle-btn:disabled,
.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.unshuffle-btn {
  border-color: var(--color-accent-purple);
  color: var(--color-accent-purple);
  background-color: var(--color-background-surface);
}

.section-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background-color: var(--color-background-elevated);
  border-bottom: 1px solid var(--color-divider);
}

.filter-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.filter-search svg {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-secondary);
  pointer-events: none;
}

.filter-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  transition: border-color 0.2s;
}

.filter-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.filter-input::placeholder {
  color: var(--color-text-secondary);
}

.filter-year {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-input-small {
  width: 80px;
  padding: 0.5rem;
  text-align: center;
}

.filter-year-sep {
  color: var(--color-text-secondary);
}

.filter-sort {
  min-width: 150px;
}

.filter-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-accent);
}

.reset-filters-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background-color: transparent;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.reset-filters-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--color-text-secondary);
}

.no-results svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-results p {
  font-size: 0.9375rem;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.25rem;
}

.anime-card {
  position: relative;
  cursor: pointer;
  border-radius: 0.75rem;
  overflow: hidden;
  transition: all 0.3s var(--transition-smooth);
}

.anime-card:hover {
  transform: translateY(-4px);
}

.anime-poster {
  width: 100%;
  aspect-ratio: 2/3;
  object-fit: cover;
  display: block;
}

.anime-poster-placeholder {
  width: 100%;
  aspect-ratio: 2/3;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  color: var(--color-text-tertiary);
}

.anime-info {
  padding: 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-top: none;
  border-radius: 0 0 0.75rem 0.75rem;
}

.anime-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0.375rem;
}

.anime-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.meta-item.rating {
  color: var(--color-accent-yellow);
  font-weight: 600;
}

.anime-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.6);
  opacity: 0;
  transition: opacity 0.3s var(--transition-smooth);
  color: #fff;
}

.anime-card:hover .anime-overlay {
  opacity: 1;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .random-hero {
    padding: 2rem 1rem;
  }

  .hero-icon {
    width: 64px;
    height: 64px;
    margin-bottom: 1rem;
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .hero-description {
    font-size: 1rem;
  }

  .lucky-btn {
    padding: 0.875rem 2rem;
    font-size: 1rem;
  }

  .random-list {
    padding: 1rem;
  }

  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1rem;
  }
}
</style>
