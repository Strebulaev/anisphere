<script setup lang="ts">
import { computed } from 'vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

const props = withDefaults(defineProps<{
  type?: 'success' | 'error' | 'warning' | 'info' | 'default'
  icon?: string
  size?: number
  compact?: boolean
}>(), {
  type: 'default',
  size: 16,
  compact: false
})

const iconName = computed(() => {
  if (props.icon) return props.icon
  
  switch (props.type) {
    case 'success': return 'check-circle'
    case 'error': return 'x-circle'
    case 'warning': return 'alert-circle'
    case 'info': return 'info'
    default: return 'info'
  }
})

const colorClass = computed(() => {
  return `status-${props.type}`
})
</script>

<template>
  <div class="status-badge" :class="[colorClass, { compact }]">
    <SakuraIcon :name="iconName" :size="size" />
    <span v-if="!compact" class="status-text">
      <slot />
    </span>
  </div>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 500;
}

.status-badge.compact {
  padding: 4px;
}

.status-text {
  line-height: 1;
}

.status-success {
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
}

.status-error {
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
}

.status-warning {
  color: #f59e0b;
  background-color: rgba(245, 158, 11, 0.1);
}

.status-info {
  color: var(--accent, #ff7eb3);
  background-color: rgba(255, 126, 179, 0.1);
}

.status-default {
  color: #6b7280;
  background-color: rgba(107, 114, 128, 0.1);
}
</style>
