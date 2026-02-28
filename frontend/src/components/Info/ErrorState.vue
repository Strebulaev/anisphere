<template>
  <div class="error-state">
    <div class="error-icon">
      <slot name="icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </slot>
    </div>

    <h2 class="error-title">
      <slot name="title">
        {{ title }}
      </slot>
    </h2>

    <p v-if="message" class="error-message">
      <slot name="message">
        {{ message }}
      </slot>
    </p>

    <div v-if="showRetry" class="error-actions">
      <button @click="handleRetry" class="retry-btn" type="button">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        Попробовать снова
      </button>
    </div>

    <div v-if="$slots.extra" class="error-extra">
      <slot name="extra"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  message?: string
  showRetry?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Произошла ошибка',
  showRetry: true
})

const emit = defineEmits<{
  retry: []
}>()

const handleRetry = () => {
  emit('retry')
}
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.25rem;
  padding: 4rem 2rem;
  text-align: center;
}

.error-icon {
  color: var(--color-error);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: 50%;
}

.error-icon svg {
  color: var(--color-error);
}

.error-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.error-message {
  font-size: 1rem;
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0;
  line-height: 1.6;
}

.error-actions {
  margin-top: 0.5rem;
}

.retry-btn {
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

.retry-btn:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(58, 134, 255, 0.4);
}

.error-extra {
  margin-top: 0.75rem;
}

@media (max-width: 768px) {
  .error-state {
    padding: 3rem 1.5rem;
  }

  .error-icon {
    width: 80px;
    height: 80px;
  }

  .error-icon svg {
    width: 48px;
    height: 48px;
  }

  .error-title {
    font-size: 1.25rem;
  }

  .error-message {
    font-size: 0.9375rem;
  }

  .retry-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
