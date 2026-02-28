<template>
  <div class="type-filter">
    <label class="filter-label">Тип</label>

    <div class="type-options">
      <label
        v-for="option in typeOptions"
        :key="option.value"
        :class="['type-option', { checked: isSelected(option.value) }]"
      >
        <input
          type="checkbox"
          :value="option.value"
          :checked="isSelected(option.value)"
          @change="toggleType(option.value)"
        />
        <span class="type-badge">{{ option.badge }}</span>
        <span class="type-label">{{ option.label }}</span>
      </label>
    </div>

    <div class="type-actions">
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

const selectedTypes = ref<string[]>([...props.modelValue])

const typeOptions = [
  { value: 'tv', label: 'TV', badge: 'TV' },
  { value: 'movie', label: 'Фильм', badge: 'MOV' },
  { value: 'ova', label: 'OVA', badge: 'OVA' },
  { value: 'ona', label: 'ONA', badge: 'ONA' },
  { value: 'special', label: 'Спешл', badge: 'SP' }
]

const isSelected = (value: string) => {
  return selectedTypes.value.includes(value)
}

const toggleType = (value: string) => {
  const index = selectedTypes.value.indexOf(value)
  if (index > -1) {
    selectedTypes.value.splice(index, 1)
  } else {
    selectedTypes.value.push(value)
  }
  emit('update:modelValue', [...selectedTypes.value])
}

const selectAll = () => {
  selectedTypes.value = typeOptions.map(opt => opt.value)
  emit('update:modelValue', [...selectedTypes.value])
}

const clearAll = () => {
  selectedTypes.value = []
  emit('update:modelValue', [])
}

onMounted(() => {
  selectedTypes.value = [...props.modelValue]
})
</script>

<style scoped>
.type-filter {
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

.type-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.type-option:hover {
  border-color: var(--color-accent);
  background-color: var(--color-background-surface);
}

.type-option.checked {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--color-accent);
}

.type-option input[type="checkbox"] {
  display: none;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  padding: 0.125rem 0.375rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.25rem;
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--color-text-tertiary);
  letter-spacing: 0.05em;
}

.type-option.checked .type-badge {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.type-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
}

.type-option.checked .type-label {
  color: var(--color-accent);
}

.type-actions {
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
  .type-options {
    gap: 0.375rem;
  }

  .type-option {
    padding: 0.4375rem 0.625rem;
  }

  .type-label {
    font-size: 0.75rem;
  }
}
</style>
