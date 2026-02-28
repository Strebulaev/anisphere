<template>
  <div class="load-more-container">
    <div class="load-more-info">
      Показано {{ shown }} из {{ total }}
    </div>
    
    <button
      @click="handleLoadMore"
      :disabled="isLoading || !hasMore"
      :class="['load-more-btn', { loading: isLoading }]"
      type="button"
    >
      <svg v-if="isLoading" class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" opacity="0.25"/>
        <path d="M12 2a10 10 0 0 1 10 10" opacity="0.5"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="16"/>
        <line x1="8" y1="12" x2="16" y2="12"/>
      </svg>
      <span>{{ isLoading ? 'Загрузка...' : hasMore ? 'Загрузить ещё' : 'Все загружено' }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  shown: number
  total: number
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false
})

const emit = defineEmits<{
  loadMore: []
}>()

const hasMore = computed(() => props.shown < props.total)

const handleLoadMore = () => {
  if (!props.isLoading && hasMore.value) {
    emit('loadMore')
  }
}
</script>

<style scoped>
.load-more-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  padding: 2rem 0;
}

.load-more-info {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.load-more-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 2rem;
  background-color: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: 0.75rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.load-more-btn:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(58, 134, 255, 0.4);
}

.load-more-btn:disabled {
  background-color: var(--color-background-active);
  border-color: var(--color-divider-light);
  color: var(--color-text-tertiary);
  cursor: not-allowed;
  transform: none;
}

.load-more-btn.loading {
  cursor: wait;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .load-more-container {
    padding: 1.5rem 0;
  }

  .load-more-btn {
    width: 100%;
    padding: 0.75rem 1.5rem;
    font-size: 0.875rem;
  }
}
</style>
