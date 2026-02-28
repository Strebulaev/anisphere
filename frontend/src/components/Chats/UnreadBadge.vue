<template>
  <div v-if="count > 0" :class="['unread-badge', { 'large': large }]">
    <span class="unread-count">{{ formattedCount }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  count: number
  large?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  large: false
})

const formattedCount = computed(() => {
  if (props.count > 99) return '99+'
  return props.count.toString()
})
</script>

<style scoped>
.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #f44336;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 600;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.unread-badge.large {
  min-width: 24px;
  height: 24px;
  padding: 0 7px;
  font-size: 0.75rem;
  border-radius: 12px;
}

.unread-count {
  line-height: 1;
}
</style>
