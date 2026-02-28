<template>
  <div class="genre-filter">
    <div class="filter-label">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
        <line x1="7" y1="7" x2="7.01" y2="7"/>
      </svg>
      <span>Жанры</span>
      <span v-if="selectedCount > 0" class="selected-count">({{ selectedCount }})</span>
    </div>

    <div class="genre-search">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск жанра..."
        class="search-input"
      />
    </div>

    <div class="genre-actions">
      <button @click="selectAll" class="action-btn" :disabled="filteredGenres.length === 0">
        Выбрать все
      </button>
      <button @click="clearAll" class="action-btn" :disabled="selectedGenres.length === 0">
        Сбросить
      </button>
    </div>

    <div class="genre-list">
      <div
        v-for="genre in filteredGenres"
        :key="genre.value"
        :class="['genre-item', { selected: isSelected(String(genre.value)) }]"
        @click="toggleGenre(String(genre.value))"
      >
        <span class="genre-name">{{ genre.label }}</span>
        <span v-if="genre.count" class="genre-count">{{ genre.count }}</span>
      </div>
    </div>

    <div v-if="filteredGenres.length === 0 && searchQuery" class="no-results">
      Жанры не найдены
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FilterOption } from '@/composables/useFilters'

interface Props {
  genres: FilterOption[]
  modelValue: string[]
  showSearch?: boolean
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showSearch: true,
  showActions: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const searchQuery = ref('')

const filteredGenres = computed(() => {
  if (!searchQuery.value) return props.genres
  const query = searchQuery.value.toLowerCase()
  return props.genres.filter(genre =>
    genre.label.toLowerCase().includes(query)
  )
})

const selectedGenres = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const selectedCount = computed(() => selectedGenres.value.length)

const isSelected = (genre: string) => {
  return selectedGenres.value.includes(genre)
}

const toggleGenre = (genre: string) => {
  const index = selectedGenres.value.indexOf(genre)
  if (index > -1) {
    selectedGenres.value = [...selectedGenres.value.slice(0, index), ...selectedGenres.value.slice(index + 1)]
  } else {
    selectedGenres.value = [...selectedGenres.value, genre]
  }
}

const selectAll = () => {
  selectedGenres.value = filteredGenres.value.map(g => String(g.value))
}

const clearAll = () => {
  selectedGenres.value = []
}

const clearGenre = (genre: string) => {
  selectedGenres.value = selectedGenres.value.filter(g => g !== genre)
}

const filterBySearch = (query: string) => {
  searchQuery.value = query
}

const applyFilters = () => {
  // Apply any additional filter logic here
}
</script>

<style scoped>
.genre-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.selected-count {
  color: var(--color-accent);
  font-weight: 500;
}

.genre-search {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  background-color: var(--color-background);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  color: var(--color-text);
  font-size: 14px;
  transition: border-color 0.15s var(--transition-smooth);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.genre-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background-color: transparent;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-divider-light);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.action-btn:hover:not(:disabled) {
  background-color: var(--color-background-surface);
  color: var(--color-text);
  border-color: var(--color-accent);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.genre-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.genre-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: var(--color-background);
  border: 1px solid var(--color-divider);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.genre-item:hover {
  background-color: var(--color-background-surface);
  border-color: var(--color-accent);
}

.genre-item.selected {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: white;
}

.genre-name {
  font-size: 13px;
  font-weight: 500;
}

.genre-count {
  font-size: 11px;
  opacity: 0.8;
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
}
</style>
