<template>
  <div class="page-title">
    <div class="page-title-content">
      <h1 class="page-title-text">
        <slot name="icon"></slot>
        {{ title }}
      </h1>
      <div v-if="subtitle" class="page-subtitle">
        {{ subtitle }}
      </div>
    </div>

    <div v-if="showCount" class="page-title-count">
      <span class="count-number">{{ count }}</span>
      <span class="count-label">{{ countLabel }}</span>
    </div>

    <div v-if="$slots.actions" class="page-title-actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
  count?: number
  countLabel?: string
  showCount?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  countLabel: 'результатов',
  showCount: false
})
</script>

<style scoped>
.page-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.page-title-content {
  flex: 1;
  min-width: 0;
}

.page-title-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.375rem 0;
  line-height: 1.2;
}

.page-title-text :deep(svg) {
  flex-shrink: 0;
  color: var(--color-accent);
}

.page-subtitle {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  font-weight: 400;
  line-height: 1.5;
}

.page-title-count {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.125rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-background-active);
  border-radius: 0.5rem;
}

.count-number {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-accent);
  line-height: 1;
}

.count-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.page-title-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

@media (max-width: 768px) {
  .page-title {
    flex-direction: column;
    gap: 0.75rem;
  }

  .page-title-text {
    font-size: 1.25rem;
  }

  .page-title-count {
    align-self: flex-start;
    flex-direction: row;
    align-items: baseline;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
  }

  .count-number {
    font-size: 1.25rem;
  }

  .page-title-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
