<template>
  <div class="year-filter">
    <label class="filter-label">Год выпуска</label>

    <div class="year-filter-mode">
      <button
        @click="mode = 'range'"
        :class="['mode-btn', { active: mode === 'range' }]"
        type="button"
      >
        Диапазон
      </button>
      <button
        @click="mode = 'dropdown'"
        :class="['mode-btn', { active: mode === 'dropdown' }]"
        type="button"
      >
        Выбор
      </button>
    </div>

    <div v-if="mode === 'range'" class="year-range">
      <div class="year-input-group">
        <label>От</label>
        <input
          v-model.number="yearFrom"
          @input="handleChange"
          type="number"
          placeholder="1990"
          :min="minYear"
          :max="maxYear"
          class="year-input"
        />
      </div>
      <span class="year-separator">—</span>
      <div class="year-input-group">
        <label>До</label>
        <input
          v-model.number="yearTo"
          @input="handleChange"
          type="number"
          placeholder="2025"
          :min="minYear"
          :max="maxYear"
          class="year-input"
        />
      </div>
    </div>

    <div v-else class="year-dropdown">
      <select
        v-model="selectedYear"
        @change="handleDropdownChange"
        class="year-select"
      >
        <option :value="null">Все годы</option>
        <option
          v-for="year in popularYears"
          :key="year"
          :value="year"
        >
          {{ year }}
        </option>
      </select>
    </div>

    <div v-if="showSlider" class="year-slider">
      <input
        v-model.number="yearFrom"
        @input="handleChange"
        type="range"
        :min="minYear"
        :max="maxYear"
        class="slider-input"
      />
      <input
        v-model.number="yearTo"
        @input="handleChange"
        type="range"
        :min="minYear"
        :max="maxYear"
        class="slider-input"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Props {
  modelValue?: { from?: number; to?: number }
  showSlider?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showSlider: false
})

const emit = defineEmits<{
  'update:modelValue': [value: { from?: number; to?: number }]
}>()

const mode = ref<'range' | 'dropdown'>('range')
const yearFrom = ref<number | undefined>(props.modelValue?.from)
const yearTo = ref<number | undefined>(props.modelValue?.to)
const selectedYear = ref<number | null>(null)

const minYear = 1990
const maxYear = new Date().getFullYear() + 1

const popularYears = computed(() => {
  const years = []
  for (let year = maxYear; year >= minYear; year--) {
    years.push(year)
  }
  return years
})

const handleChange = () => {
  if (mode.value === 'dropdown') {
    selectedYear.value = null
  }
  
  emit('update:modelValue', {
    from: yearFrom.value,
    to: yearTo.value
  })
}

const handleDropdownChange = () => {
  if (selectedYear.value) {
    yearFrom.value = selectedYear.value
    yearTo.value = selectedYear.value
  } else {
    yearFrom.value = undefined
    yearTo.value = undefined
  }
  
  emit('update:modelValue', {
    from: yearFrom.value,
    to: yearTo.value
  })
}

onMounted(() => {
  if (props.modelValue) {
    yearFrom.value = props.modelValue.from
    yearTo.value = props.modelValue.to
  }
})
</script>

<style scoped>
.year-filter {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.year-filter-mode {
  display: flex;
  gap: 0.5rem;
}

.mode-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.mode-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.mode-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.year-range {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.year-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.year-input-group label {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.year-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
  text-align: center;
}

.year-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.year-separator {
  color: var(--color-text-tertiary);
  font-weight: 700;
  font-size: 1rem;
  padding-top: 1rem;
}

.year-dropdown {
  width: 100%;
}

.year-select {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.year-select:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.year-slider {
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider-light);
}

.slider-input {
  width: 100%;
  margin-bottom: 0.5rem;
  accent-color: var(--color-accent);
}

@media (max-width: 768px) {
  .year-range {
    gap: 0.5rem;
  }

  .year-input {
    font-size: 0.8rem;
    padding: 0.5rem;
  }
}
</style>
