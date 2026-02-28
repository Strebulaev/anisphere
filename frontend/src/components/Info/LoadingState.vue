<template>
  <div class="loading-state">
    <div v-if="type === 'spinner'" class="loading-spinner">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" opacity="0.25"/>
        <path d="M12 2a10 10 0 0 1 10 10" opacity="0.5"/>
      </svg>
    </div>

    <div v-else class="loading-skeleton">
      <slot name="skeleton">
        <div class="skeleton-grid">
          <div v-for="i in count" :key="i" class="skeleton-card">
            <div class="skeleton-poster"></div>
            <div class="skeleton-content">
              <div class="skeleton-title"></div>
              <div class="skeleton-meta"></div>
              <div class="skeleton-meta short"></div>
            </div>
          </div>
        </div>
      </slot>
    </div>

    <div v-if="message" class="loading-message">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'spinner' | 'skeleton'
  message?: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'spinner',
  count: 8
})
</script>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 3rem 1rem;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

.loading-spinner svg {
  color: var(--color-accent);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-skeleton {
  width: 100%;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.25rem;
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-poster {
  aspect-ratio: 2 / 3;
  background: linear-gradient(
    90deg,
    var(--color-background-active) 0%,
    var(--color-background-surface) 50%,
    var(--color-background-active) 100%
  );
  background-size: 200% 100%;
  border-radius: 0.5rem;
  animation: shimmer 1.5s infinite;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-title {
  height: 1rem;
  background: linear-gradient(
    90deg,
    var(--color-background-active) 0%,
    var(--color-background-surface) 50%,
    var(--color-background-active) 100%
  );
  background-size: 200% 100%;
  border-radius: 0.25rem;
  animation: shimmer 1.5s infinite;
  width: 100%;
}

.skeleton-meta {
  height: 0.75rem;
  background: linear-gradient(
    90deg,
    var(--color-background-active) 0%,
    var(--color-background-surface) 50%,
    var(--color-background-active) 100%
  );
  background-size: 200% 100%;
  border-radius: 0.25rem;
  animation: shimmer 1.5s infinite;
  width: 70%;
}

.skeleton-meta.short {
  width: 40%;
  animation-delay: 0.2s;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.loading-message {
  font-size: 1rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .loading-state {
    padding: 2rem 1rem;
  }

  .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .loading-spinner svg {
    width: 40px;
    height: 40px;
  }
}
</style>
