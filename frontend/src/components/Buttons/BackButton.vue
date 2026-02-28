<template>
  <button
    @click="handleClick"
    class="back-btn"
    type="button"
  >
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <line x1="19" y1="12" x2="5" y2="12"/>
      <polyline points="12 19 5 12 12 5"/>
    </svg>
    <span v-if="showLabel">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

interface Props {
  to?: string | (() => void)
  label?: string
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Назад',
  showLabel: true
})

const router = useRouter()

const handleClick = () => {
  if (typeof props.to === 'function') {
    props.to()
  } else if (typeof props.to === 'string') {
    router.push(props.to)
  } else {
    router.back()
  }
}
</script>

<style scoped>
.back-btn {
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

.back-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-surface);
  transform: translateX(-2px);
}

.back-btn:active {
  transform: translateX(0);
}

@media (max-width: 768px) {
  .back-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.8125rem;
  }
}
</style>
