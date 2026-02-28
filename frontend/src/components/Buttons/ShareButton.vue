<template>
  <button
    @click="handleShare"
    :class="['share-btn', { shared }]"
    :title="shared ? 'Скопировано!' : 'Поделиться'"
    type="button"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="18" cy="5" r="3"/>
      <circle cx="6" cy="12" r="3"/>
      <circle cx="18" cy="19" r="3"/>
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
    </svg>
    <span v-if="showLabel">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  url?: string
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  url: '',
  showLabel: false
})

const emit = defineEmits<{
  share: [url: string]
}>()

const shared = ref(false)
let timeoutId: number | null = null

const label = computed(() => shared.value ? 'Скопировано!' : 'Поделиться')

const handleShare = async () => {
  const shareUrl = props.url || window.location.href

  if (navigator.share) {
    try {
      await navigator.share({
        title: document.title,
        url: shareUrl
      })
      return
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('Share failed:', err)
      }
    }
  }

  try {
    await navigator.clipboard.writeText(shareUrl)
    shared.value = true
    emit('share', shareUrl)

    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = window.setTimeout(() => {
      shared.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<style scoped>
.share-btn {
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

.share-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-surface);
  transform: translateY(-1px);
}

.share-btn.shared {
  background-color: #22c55e;
  border-color: #22c55e;
  color: #fff;
}

.share-btn.shared:hover {
  background-color: #16a34a;
  border-color: #16a34a;
}

@media (max-width: 768px) {
  .share-btn {
    padding: 0.5rem;
  }

  .share-btn span:not(:first-child) {
    display: none;
  }
}
</style>
