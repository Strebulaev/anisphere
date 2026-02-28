<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </slot>
    </div>

    <h2 class="empty-title">
      <slot name="title">
        {{ title }}
      </slot>
    </h2>

    <p v-if="message" class="empty-message">
      <slot name="message">
        {{ message }}
      </slot>
    </p>

    <div v-if="suggestions?.length" class="empty-suggestions">
      <p class="suggestions-title">Попробуйте:</p>
      <ul class="suggestions-list">
        <li v-for="(suggestion, index) in suggestions" :key="index" class="suggestion-item">
          {{ suggestion }}
        </li>
      </ul>
    </div>

    <div v-if="$slots.actions" class="empty-actions">
      <slot name="actions"></slot>
    </div>

    <button
      v-if="showAction"
      @click="handleAction"
      class="action-btn"
      type="button"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="1 4 1 10 7 10"/>
        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
      </svg>
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  message?: string
  suggestions?: string[]
  showAction?: boolean
  actionLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Ничего не найдено',
  actionLabel: 'Сбросить фильтры'
})

const emit = defineEmits<{
  action: []
}>()

const handleAction = () => {
  emit('action')
}
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.25rem;
  padding: 4rem 2rem;
  text-align: center;
}

.empty-icon {
  color: var(--color-text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  background-color: var(--color-background-active);
  border-radius: 50%;
  opacity: 0.5;
}

.empty-icon svg {
  color: var(--color-text-tertiary);
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.empty-message {
  font-size: 1rem;
  color: var(--color-text-secondary);
  max-width: 450px;
  margin: 0;
  line-height: 1.6;
}

.empty-suggestions {
  margin-top: 0.5rem;
}

.suggestions-title {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.suggestions-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.suggestion-item {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.suggestion-item::before {
  content: '•';
  color: var(--color-accent);
  font-weight: 700;
}

.empty-actions {
  margin-top: 0.5rem;
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: center;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.75rem;
  background-color: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: 0.75rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.action-btn:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(58, 134, 255, 0.4);
}

@media (max-width: 768px) {
  .empty-state {
    padding: 3rem 1.5rem;
  }

  .empty-icon {
    width: 90px;
    height: 90px;
  }

  .empty-icon svg {
    width: 56px;
    height: 56px;
  }

  .empty-title {
    font-size: 1.25rem;
  }

  .empty-message {
    font-size: 0.9375rem;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
