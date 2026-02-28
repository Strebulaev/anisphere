<template>
  <div class="items-per-page">
    <label class="items-label">На странице:</label>
    <select
      v-model="selectedValue"
      @change="handleChange"
      class="items-select"
    >
      <option
        v-for="option in options"
        :key="option"
        :value="option"
      >
        {{ option }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Props {
  modelValue?: number
  options?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 20,
  options: () => [10, 20, 50, 100]
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const STORAGE_KEY = 'items-per-page'
const selectedValue = ref(props.modelValue)

const handleChange = () => {
  const value = Number(selectedValue.value)
  emit('update:modelValue', value)
  
  try {
    localStorage.setItem(STORAGE_KEY, String(value))
  } catch (e) {
    console.error('Failed to save items per page:', e)
  }
}

const loadSavedValue = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const value = Number(saved)
      if (props.options.includes(value)) {
        selectedValue.value = value
        emit('update:modelValue', value)
      }
    }
  } catch (e) {
    console.error('Failed to load items per page:', e)
  }
}

onMounted(() => {
  loadSavedValue()
})
</script>

<style scoped>
.items-per-page {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.items-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.items-select {
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  outline: none;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 1rem;
  min-width: 80px;
}

.items-select:hover {
  border-color: var(--color-accent);
}

.items-select:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

@media (max-width: 768px) {
  .items-label {
    font-size: 0.8rem;
  }

  .items-select {
    font-size: 0.8rem;
    padding: 0.4375rem 1.75rem 0.4375rem 0.625rem;
    min-width: 70px;
  }
}
</style>
