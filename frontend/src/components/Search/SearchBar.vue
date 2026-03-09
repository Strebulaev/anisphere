<template>
  <div class="search-bar" :class="{ focused: isFocused, [variant]: true }">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        ref="searchInput"
        v-model="searchQuery"
        class="search-input"
        type="text"
        :placeholder="placeholder"
        @input="handleInput"
        @keydown.enter.prevent="handleSearch"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <button 
        v-if="showClearButton"
        class="search-clear"
        @click="clearSearch"
        type="button"
        :aria-label="'Очистить поиск'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <SearchSuggestions
      v-if="showSuggestions && !props.hideSuggestions"
      :show="showSuggestions && !props.hideSuggestions"
      :results="(results || { anime: [], users: [], playlists: [] })"
      :is-loading="(isLoading || false)"
      :categories="categories"
      @select="onSuggestionSelect"
      @close="isFocused = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSearch, type SearchCategory, type UseSearchOptions } from '@/composables/useSearch'
import SearchSuggestions from './SearchSuggestions.vue'

interface Props {
  variant?: 'header' | 'page' | 'sidebar' | 'compact'
  placeholder?: string
  categories?: SearchCategory[]
  minQueryLength?: number
  debounceTime?: number
  searchRoute?: string
  searchQueryKey?: string
  preventNavigationOnSelect?: boolean
  hideSuggestions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'header',
  placeholder: 'Поиск...',
  minQueryLength: 3,
  debounceTime: 400,
  searchRoute: '/anime',
  searchQueryKey: 'search',
  preventNavigationOnSelect: false,
  hideSuggestions: false
})

const emit = defineEmits<{
  search: [query: string]
  clear: []
  focus: []
  blur: []
  'select-item': [category: string, item: any]
}>()

const router = useRouter()
const searchInput = ref<HTMLInputElement | null>(null)

const searchOptions: UseSearchOptions = {
  categories: props.categories,
  debounceTime: props.debounceTime,
  minQueryLength: props.minQueryLength,
  placeholder: props.placeholder,
  searchRoute: props.searchRoute,
  searchQueryKey: props.searchQueryKey
}

const {
  searchQuery,
  isFocused,
  isLoading,
  results,
  showSuggestions,
  showClearButton,
  handleInput,
  handleSearch: baseHandleSearch,
  clearSearch: baseClearSearch,
  handleFocus,
  handleBlur,
  selectItem
} = useSearch(searchOptions)

const handleSearch = () => {
  emit('search', searchQuery.value || '')
  if (!props.preventNavigationOnSelect) {
    baseHandleSearch()
  }
}

const clearSearch = () => {
  emit('clear')
  baseClearSearch()
  if (searchInput.value) {
    searchInput.value.focus()
  }
}

const onSuggestionSelect = (category: string, item: any) => {
  if (props.preventNavigationOnSelect) {
    emit('select-item', category, item)
  } else {
    selectItem(category, item)
  }
  isFocused.value = false
}

watch(() => props.placeholder, (newPlaceholder) => {
  if (searchInput.value) {
    searchInput.value.placeholder = newPlaceholder
  }
})

watch(() => router.currentRoute.value, () => {
  isFocused.value = false
})

const focus = () => {
  searchInput.value?.focus()
}

const blur = () => {
  searchInput.value?.blur()
}

defineExpose({
  focus,
  blur,
  clear: clearSearch
})
</script>

<style scoped>
.search-bar {
  position: relative;
  width: 100%;
  background: transparent;
}

.search-bar.header {
  max-width: 400px;
}

.search-bar.page {
  max-width: 600px;
}

.search-bar.sidebar {
  max-width: 100%;
}

.search-bar.compact {
  max-width: 280px;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  background: transparent !important;
  border: 1px solid var(--color-divider-light);
  border-radius: 20px;
  padding: 0 12px 0 16px;
  transition: all 0.15s var(--transition-smooth);
}

.search-bar.focused .search-input-wrapper {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  background: transparent !important;
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
  background: transparent !important;
  border: none !important;
  outline: none;
  color: var(--color-text);
  font-size: 14px;
  min-width: 0;
  box-shadow: none !important;
}

.search-input:focus {
  background-color: transparent !important;
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
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
  background-color: var(--color-background-active);
}

.search-bar.compact .search-input-wrapper {
  height: 36px;
  padding: 0 10px 0 14px;
}

.search-bar.page .search-input-wrapper {
  height: 48px;
  border-radius: 24px;
  padding: 0 16px 0 20px;
}

.search-bar.page .search-input {
  font-size: 16px;
}

/* Выпадающие результаты */
.search-suggestions {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-card-hover);
  max-height: 500px;
  overflow-y: auto;
  z-index: 1000;
}
</style>
