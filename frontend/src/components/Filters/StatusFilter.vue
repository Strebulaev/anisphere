<template>
  <div class="status-filter">
    <label class="filter-label">Статус</label>

    <div class="status-options">
      <label
        v-for="option in statusOptions"
        :key="option.value"
        :class="['status-option', { checked: isSelected(option.value) }]"
      >
        <input
          type="checkbox"
          :value="option.value"
          :checked="isSelected(option.value)"
          @change="toggleStatus(option.value)"
        />
        <span class="status-icon">{{ option.icon }}</span>
        <span class="status-label">{{ option.label }}</span>
      </label>
    </div>

    <div class="status-actions">
      <button
        @click="selectAll"
        class="action-btn"
        type="button"
      >
        Выбрать все
      </button>
      <button
        @click="clearAll"
        class="action-btn"
        type="button"
      >
        Сбросить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Props {
  modelValue?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const selectedStatuses = ref<string[]>([...props.modelValue])

const statusOptions = [
  { value: 'ongoing', label: 'Онгоинг', icon: '🔄' },
  { value: 'finished', label: 'Завершён', icon: '✅' },
  { value: 'announced', label: 'Анонсирован', icon: '📢' },
  { value: 'released', label: 'Вышедший', icon: '🎬' }
]

const isSelected = (value: string) => {
  return selectedStatuses.value.includes(value)
}

const toggleStatus = (value: string) => {
  const index = selectedStatuses.value.indexOf(value)
  if (index > -1) {
    selectedStatuses.value.splice(index, 1)
  } else {
    selectedStatuses.value.push(value)
  }
  emit('update:modelValue', [...selectedStatuses.value])
}

const selectAll = () => {
  selectedStatuses.value = statusOptions.map(opt => opt.value)
  emit('update:modelValue', [...selectedStatuses.value])
}

const clearAll = () => {
  selectedStatuses.value = []
  emit('update:modelValue', [])
}

onMounted(() => {
  selectedStatuses.value = [...props.modelValue]
})
</script>

<style scoped>
.status-filter {
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

.status-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.status-option:hover {
  border-color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.status-option.checked {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--color-accent);
}

.status-option input[type="checkbox"] {
  display: none;
}

.status-icon {
  font-size: 1.25rem;
  width: 24px;
  text-align: center;
}

.status-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.status-option.checked .status-label {
  color: var(--color-accent);
}

.status-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.action-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background-color: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.action-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-active);
}

@media (max-width: 768px) {
  .status-options {
    gap: 0.375rem;
  }

  .status-option {
    padding: 0.625rem 0.875rem;
  }

  .status-label {
    font-size: 0.8rem;
  }
}
</style>
