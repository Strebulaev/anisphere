<template>
  <div class="loading-spinner" :class="sizeClass">
    <div class="spinner"></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg'
}
const props = withDefaults(defineProps<Props>(), { size: 'md' })
import { computed } from 'vue'
const sizeClass = computed(() => `spinner-${props.size}`)
</script>

<style scoped>
.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
}

.spinner {
  border-radius: 50%;
  border-style: solid;
  border-color: var(--border-strong);
  border-top-color: var(--accent);
  animation: spin var(--duration-slower) linear infinite;
}

.spinner-sm .spinner { width: 16px; height: 16px; border-width: 2px; }
.spinner-md .spinner { width: 28px; height: 28px; border-width: 2.5px; }
.spinner-lg .spinner { width: 44px; height: 44px; border-width: 3px; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
