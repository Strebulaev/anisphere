<template>
  <div class="rating-filter">
    <label class="filter-label">Рейтинг</label>

    <div v-if="mode === 'inputs'" class="rating-inputs">
      <div class="rating-input-group">
        <label>От</label>
        <input
          v-model.number="ratingFrom"
          @input="handleChange"
          type="number"
          placeholder="0"
          :min="0"
          :max="10"
          :step="0.1"
          class="rating-input"
        />
      </div>
      <span class="rating-separator">—</span>
      <div class="rating-input-group">
        <label>До</label>
        <input
          v-model.number="ratingTo"
          @input="handleChange"
          type="number"
          placeholder="10"
          :min="0"
          :max="10"
          :step="0.1"
          class="rating-input"
        />
      </div>
    </div>

    <div v-else class="rating-stars">
      <div class="stars-container">
        <button
          v-for="star in 10"
          :key="star"
          @click="setMinRating(star)"
          :class="['star-btn', { active: (ratingFrom ?? 0) >= star }]"
          type="button"
          :title="`От ${star} звёзд`"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </button>
      </div>
      <div class="rating-value">
        <span class="rating-label">От</span>
        <span class="rating-number">{{ (ratingFrom ?? 0) }}</span>
        <span class="rating-divider">/</span>
        <span class="rating-max">10</span>
      </div>
      <button
        v-if="ratingFrom !== undefined && ratingFrom > 0"
        @click="resetRating"
        class="reset-btn"
        type="button"
      >
        Сбросить
      </button>
    </div>

    <div class="rating-mode-toggle">
      <button
        @click="mode = 'inputs'"
        :class="['mode-btn', { active: mode === 'inputs' }]"
        type="button"
      >
        Числа
      </button>
      <button
        @click="mode = 'stars'"
        :class="['mode-btn', { active: mode === 'stars' }]"
        type="button"
      >
        Звёзды
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Props {
  modelValue?: { from?: number; to?: number }
  initialMode?: 'inputs' | 'stars'
}

const props = withDefaults(defineProps<Props>(), {
  initialMode: 'inputs'
})

const emit = defineEmits<{
  'update:modelValue': [value: { from?: number; to?: number }]
}>()

const mode = ref<'inputs' | 'stars'>(props.initialMode)
const ratingFrom = ref<number | undefined>(props.modelValue?.from)
const ratingTo = ref<number | undefined>(props.modelValue?.to)

const handleChange = () => {
  emit('update:modelValue', {
    from: ratingFrom.value,
    to: ratingTo.value
  })
}

const setMinRating = (value: number) => {
  if (ratingFrom.value === value) {
    ratingFrom.value = undefined
  } else {
    ratingFrom.value = value
    ratingTo.value = undefined
  }
  emit('update:modelValue', {
    from: ratingFrom.value,
    to: ratingTo.value
  })
}

const resetRating = () => {
  ratingFrom.value = undefined
  ratingTo.value = undefined
  emit('update:modelValue', {
    from: undefined,
    to: undefined
  })
}

onMounted(() => {
  if (props.modelValue) {
    ratingFrom.value = props.modelValue.from
    ratingTo.value = props.modelValue.to
  }
})
</script>

<style scoped>
.rating-filter {
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

.rating-inputs {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.rating-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.rating-input-group label {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.rating-input {
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

.rating-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.rating-separator {
  color: var(--color-text-tertiary);
  font-weight: 700;
  font-size: 1rem;
  padding-top: 1rem;
}

.rating-stars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
}

.stars-container {
  display: flex;
  gap: 0.25rem;
}

.star-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-divider);
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.star-btn:hover {
  transform: scale(1.2);
  color: var(--color-accent-orange);
}

.star-btn.active {
  color: var(--color-accent-orange);
}

.rating-value {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.rating-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.rating-number {
  font-size: 1.5rem;
  color: var(--color-accent-orange);
  font-weight: 800;
}

.rating-divider {
  font-size: 1rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.rating-max {
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 600;
}

.reset-btn {
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

.reset-btn:hover {
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
}

.rating-mode-toggle {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.mode-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.75rem;
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

@media (max-width: 768px) {
  .stars-container {
    gap: 0.125rem;
  }

  .star-btn {
    width: 24px;
    height: 24px;
  }

  .rating-number {
    font-size: 1.25rem;
  }
}
</style>
