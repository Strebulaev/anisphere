<template>
  <button
    @click="handleClick"
    :class="['collection-btn', { active: status }]"
    :title="title"
    type="button"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
      <polyline points="17 21 17 13 7 13 7 21"/>
      <polyline points="7 3 7 8 15 8"/>
    </svg>
    <span v-if="showLabel">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status?: null | 'watching' | 'completed' | 'planned'
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  status: null,
  showLabel: false
})

const emit = defineEmits<{
  click: []
}>()

const label = computed(() => {
  switch (props.status) {
    case 'watching':
      return 'В процессе'
    case 'completed':
      return 'Просмотрено'
    case 'planned':
      return 'Запланировано'
    default:
      return 'В коллекцию'
  }
})

const title = computed(() => {
  return props.status ? `Статус: ${label.value}` : 'Добавить в коллекцию'
})

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.collection-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.collection-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-surface);
  transform: translateY(-1px);
}

.collection-btn.active {
  background-color: var(--color-accent-teal);
  border-color: var(--color-accent-teal);
  color: #fff;
}

.collection-btn.active:hover {
  background-color: #0d9488;
  border-color: #0d9488;
}

@media (max-width: 768px) {
  .collection-btn {
    padding: 0.5rem;
  }

  .collection-btn span:not(:first-child) {
    display: none;
  }
}
</style>
