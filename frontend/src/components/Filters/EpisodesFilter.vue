<template>
  <div class="episodes-filter">
    <label class="filter-label">Количество серий</label>

    <div class="episodes-inputs">
      <div class="episodes-input-group">
        <label>От</label>
        <input
          v-model.number="episodesFrom"
          @input="handleChange"
          type="number"
          placeholder="1"
          :min="0"
          class="episodes-input"
        />
      </div>
      <span class="episodes-separator">—</span>
      <div class="episodes-input-group">
        <label>До</label>
        <input
          v-model.number="episodesTo"
          @input="handleChange"
          type="number"
          placeholder="∞"
          :min="0"
          class="episodes-input"
        />
      </div>
    </div>

    <div v-if="showSlider" class="episodes-slider">
      <div class="slider-header">
        <span class="slider-label">Быстрый выбор</span>
        <span class="slider-value">{{ displayValue }}</span>
      </div>
      <input
        v-model.number="sliderValue"
        @input="handleSliderChange"
        type="range"
        :min="0"
        :max="maxEpisodes"
        :step="step"
        class="slider-input"
      />
      <div class="slider-presets">
        <button
          v-for="preset in presets"
          :key="preset.value"
          @click="setPreset(preset.value)"
          :class="['preset-btn', { active: sliderValue === preset.value }]"
          type="button"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Props {
  modelValue?: { from?: number; to?: number }
  showSlider?: boolean
  maxEpisodes?: number
  step?: number
}

const props = withDefaults(defineProps<Props>(), {
  showSlider: false,
  maxEpisodes: 1000,
  step: 10
})

const emit = defineEmits<{
  'update:modelValue': [value: { from?: number; to?: number }]
}>()

const episodesFrom = ref<number | undefined>(props.modelValue?.from)
const episodesTo = ref<number | undefined>(props.modelValue?.to)
const sliderValue = ref(0)

const presets = [
  { value: 12, label: '12' },
  { value: 24, label: '24' },
  { value: 50, label: '50' },
  { value: 100, label: '100' },
  { value: 0, label: 'Все' }
]

const displayValue = computed(() => {
  if (sliderValue.value === 0) return 'Все'
  if (sliderValue.value >= props.maxEpisodes) return `${props.maxEpisodes}+`
  return sliderValue.value
})

const handleChange = () => {
  emit('update:modelValue', {
    from: episodesFrom.value,
    to: episodesTo.value
  })
}

const handleSliderChange = () => {
  if (sliderValue.value === 0) {
    episodesFrom.value = undefined
    episodesTo.value = undefined
  } else if (sliderValue.value >= props.maxEpisodes) {
    episodesFrom.value = props.maxEpisodes
    episodesTo.value = undefined
  } else {
    episodesFrom.value = 1
    episodesTo.value = sliderValue.value
  }
  
  emit('update:modelValue', {
    from: episodesFrom.value,
    to: episodesTo.value
  })
}

const setPreset = (value: number) => {
  sliderValue.value = value
  handleSliderChange()
}

onMounted(() => {
  if (props.modelValue) {
    episodesFrom.value = props.modelValue.from
    episodesTo.value = props.modelValue.to
  }
})
</script>

<style scoped>
.episodes-filter {
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

.episodes-inputs {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.episodes-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.episodes-input-group label {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.episodes-input {
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

.episodes-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.episodes-separator {
  color: var(--color-text-tertiary);
  font-weight: 700;
  font-size: 1rem;
  padding-top: 1rem;
}

.episodes-slider {
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider-light);
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.slider-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.slider-value {
  font-size: 0.875rem;
  color: var(--color-accent);
  font-weight: 700;
}

.slider-input {
  width: 100%;
  margin-bottom: 0.75rem;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.slider-presets {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.preset-btn {
  flex: 1;
  min-width: 60px;
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

.preset-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.preset-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

@media (max-width: 768px) {
  .episodes-inputs {
    gap: 0.5rem;
  }

  .episodes-input {
    font-size: 0.8rem;
    padding: 0.5rem;
  }

  .slider-presets {
    gap: 0.375rem;
  }

  .preset-btn {
    font-size: 0.7rem;
    padding: 0.4375rem 0.625rem;
  }
}
</style>
