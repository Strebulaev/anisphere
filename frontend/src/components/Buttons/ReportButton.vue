<template>
  <button
    @click="handleClick"
    class="report-btn"
    title="Пожаловаться"
    type="button"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
    <span v-if="showLabel">Пожаловаться</span>
  </button>
</template>

<script setup lang="ts">
interface Props {
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showLabel: false
})

const emit = defineEmits<{
  click: []
}>()

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.report-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.report-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.05);
}

@media (max-width: 768px) {
  .report-btn {
    padding: 0.5rem;
  }

  .report-btn span:not(:first-child) {
    display: none;
  }
}
</style>
