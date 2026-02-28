<template>
  <div class="anime-filters">
    <FilterBlock
      :is-collapsed="isFiltersCollapsed"
      @toggle="toggleFiltersCollapsed"
      @apply="applyFilters"
      @reset="resetFilters"
    >
      <GenreFilter
        v-model="selectedGenres"
        :genres="availableGenres"
        label="Жанры"
      />

      <YearFilter
        v-model="selectedYearRange"
        :min-year="minYear"
        :max-year="maxYear"
      />

      <StatusFilter
        v-model="selectedStatuses"
        :statuses="availableStatuses"
      />

      <TypeFilter
        v-model="selectedTypes"
        :types="availableTypes"
      />

      <EpisodesFilter
        v-model="selectedEpisodesRange"
      />

      <RatingFilter
        v-model="selectedRatingRange"
      />
    </FilterBlock>

    <ActiveFilters
      :filters="activeFiltersList"
      @remove="removeFilter"
      @clear-all="clearAllFilters"
    />
  </div>
</template>

<script setup lang="ts">
import { useFilters } from '@/composables/useFilters'
import FilterBlock from './FilterBlock.vue'
import GenreFilter from './GenreFilter.vue'
import YearFilter from './YearFilter.vue'
import StatusFilter from './StatusFilter.vue'
import TypeFilter from './TypeFilter.vue'
import EpisodesFilter from './EpisodesFilter.vue'
import RatingFilter from './RatingFilter.vue'
import ActiveFilters from './ActiveFilters.vue'

interface Props {
  availableGenres?: Array<{ value: string; label: string }>
  availableStatuses?: Array<{ value: string; label: string }>
  availableTypes?: Array<{ value: string; label: string }>
  minYear?: number
  maxYear?: number
}

const props = withDefaults(defineProps<Props>(), {
  availableGenres: () => [],
  availableStatuses: () => [],
  availableTypes: () => [],
  minYear: 1990,
  maxYear: new Date().getFullYear() + 1
})

const emit = defineEmits<{
  filtersChanged: [filters: Record<string, any>]
}>()

const {
  selectedGenres,
  selectedYearRange,
  selectedStatuses,
  selectedTypes,
  selectedEpisodesRange,
  selectedRatingRange,
  isFiltersCollapsed,
  activeFiltersList,
  applyFilters,
  resetFilters,
  clearAllFilters,
  clearFilter,
  toggleFiltersCollapsed
} = useFilters({
  persistToUrl: true,
  persistToLocalStorage: true,
  localStorageKey: 'anime-catalog',
  availableGenres: props.availableGenres,
  availableStatuses: props.availableStatuses,
  availableTypes: props.availableTypes,
  minYear: props.minYear,
  maxYear: props.maxYear
})

const removeFilter = (key: string) => {
  const filterType = key.split('-')[0] || key
  clearFilter(filterType)
  applyFilters()
}
</script>

<style scoped>
.anime-filters {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
