<template>
  <div v-if="hasActiveFilters" class="active-filters">
    <div class="active-filters-header">
      <span class="active-filters-count">Выбрано фильтров: {{ activeFiltersCount }}</span>
      <button
        @click="clearAll"
        class="clear-all-btn"
        type="button"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
        Очистить всё
      </button>
    </div>

    <div class="active-filters-tags">
      <transition-group name="tag">
        <div
          v-for="filter in visibleFilters"
          :key="filter.key"
          class="filter-tag"
          :class="filter.type"
        >
          <span class="filter-tag-label">{{ filter.label }}</span>
          <button
            @click="removeFilter(filter.key)"
            class="filter-tag-remove"
            type="button"
            :title="`Убрать ${filter.label}`"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div
          v-if="hiddenFiltersCount > 0"
          key="more"
          class="filter-tag more-tag"
          @click="showAll = !showAll"
        >
          <span class="filter-tag-label">+{{ hiddenFiltersCount }}</span>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface FilterTag {
  key: string
  label: string
  type: string
}

interface Props {
  filters?: Record<string, any>
  maxVisible?: number
}

const props = withDefaults(defineProps<Props>(), {
  filters: () => ({}),
  maxVisible: 8
})

const emit = defineEmits<{
  remove: [key: string]
  clearAll: []
}>()

const showAll = ref(false)

const activeFilters = computed<FilterTag[]>(() => {
  const tags: FilterTag[] = []
  const filters = props.filters

  if (!filters) return tags

  if (filters.search) {
    tags.push({ key: 'search', label: `Поиск: "${filters.search}"`, type: 'search' })
  }

  if (filters.genres && filters.genres.length > 0) {
    filters.genres.forEach((genre: string, index: number) => {
      tags.push({ key: `genre-${genre}`, label: `Жанр: ${genre}`, type: 'genre' })
    })
  }

  if (filters.status && filters.status.length > 0) {
    filters.status.forEach((status: string) => {
      const labels: Record<string, string> = {
        ongoing: 'Онгоинг',
        finished: 'Завершён',
        announced: 'Анонсирован',
        released: 'Вышедший'
      }
      tags.push({ key: `status-${status}`, label: labels[status] || status, type: 'status' })
    })
  }

  if (filters.type && filters.type.length > 0) {
    filters.type.forEach((type: string) => {
      const labels: Record<string, string> = {
        tv: 'TV',
        movie: 'Фильм',
        ova: 'OVA',
        ona: 'ONA',
        special: 'Спешл'
      }
      tags.push({ key: `type-${type}`, label: labels[type] || type, type: 'type' })
    })
  }

  if (filters.yearFrom || filters.yearTo) {
    const label = filters.yearFrom && filters.yearTo
      ? `Год: ${filters.yearFrom}–${filters.yearTo}`
      : filters.yearFrom
      ? `От ${filters.yearFrom}`
      : `До ${filters.yearTo}`
    tags.push({ key: 'year', label, type: 'year' })
  }

  if (filters.episodesFrom || filters.episodesTo) {
    const label = filters.episodesFrom && filters.episodesTo
      ? `Серии: ${filters.episodesFrom}–${filters.episodesTo}`
      : filters.episodesFrom
      ? `От ${filters.episodesFrom} серий`
      : `До ${filters.episodesTo} серий`
    tags.push({ key: 'episodes', label, type: 'episodes' })
  }

  if (filters.ratingFrom || filters.ratingTo) {
    const label = filters.ratingFrom && filters.ratingTo
      ? `Рейтинг: ${filters.ratingFrom}–${filters.ratingTo}`
      : filters.ratingFrom
      ? `От ${filters.ratingFrom}`
      : `До ${filters.ratingTo}`
    tags.push({ key: 'rating', label, type: 'rating' })
  }

  return tags
})

const activeFiltersCount = computed(() => activeFilters.value.length)

const visibleFilters = computed(() => {
  if (showAll.value) {
    return activeFilters.value
  }
  return activeFilters.value.slice(0, props.maxVisible)
})

const hiddenFiltersCount = computed(() => {
  if (showAll.value) return 0
  return Math.max(0, activeFilters.value.length - props.maxVisible)
})

const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

const removeFilter = (key: string) => {
  emit('remove', key)
}

const clearAll = () => {
  emit('clearAll')
}
</script>

<style scoped>
.active-filters {
  background-color: var(--color-background-surface);
  border-radius: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--color-divider);
}

.active-filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.active-filters-count {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 600;
}

.clear-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background-color: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.clear-all-btn:hover {
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
  background-color: rgba(255, 42, 109, 0.05);
}

.active-filters-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid;
  transition: all 0.2s var(--transition-smooth);
}

.filter-tag.search {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.filter-tag.genre {
  background-color: rgba(0, 212, 170, 0.1);
  border-color: var(--color-accent-teal);
  color: var(--color-accent-teal);
}

.filter-tag.status {
  background-color: rgba(255, 159, 28, 0.1);
  border-color: var(--color-accent-orange);
  color: var(--color-accent-orange);
}

.filter-tag.type {
  background-color: rgba(139, 92, 246, 0.1);
  border-color: #8b5cf6;
  color: #8b5cf6;
}

.filter-tag.year,
.filter-tag.episodes,
.filter-tag.rating {
  background-color: rgba(236, 72, 153, 0.1);
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
}

.filter-tag-label {
  white-space: nowrap;
}

.filter-tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  border-radius: 50%;
  transition: background-color 0.15s var(--transition-smooth);
}

.filter-tag-remove:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.more-tag {
  cursor: pointer;
  background-color: var(--color-background-active);
  border-color: var(--color-divider);
  color: var(--color-text-secondary);
}

.more-tag:hover {
  background-color: var(--color-background-surface);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.tag-enter-active,
.tag-leave-active {
  transition: all 0.2s var(--transition-smooth);
}

.tag-enter-from,
.tag-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .active-filters {
    padding: 0.75rem;
  }

  .active-filters-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .filter-tag {
    font-size: 0.7rem;
    padding: 0.3125rem 0.5rem;
  }
}
</style>
