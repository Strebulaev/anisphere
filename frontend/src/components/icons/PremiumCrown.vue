<template>
  <svg 
    :width="size" 
    :height="size" 
    viewBox="0 0 24 24" 
    fill="none" 
    :class="['premium-crown', { 'crown-animated': animated }]"
  >
    <!-- Основная корона -->
    <path 
      d="M12 2L15 8H21L16 12L18 20L12 16L6 20L8 12L3 8H9L12 2Z" 
      :fill="gradientId ? `url(#${gradientId})` : color"
      stroke="currentColor" 
      :stroke-width="strokeWidth"
      stroke-linejoin="round"
    />
    <!-- Блеск на короне -->
    <path 
      d="M12 4L14 8H18L15 11L16 16L12 13L8 16L9 11L6 8H10L12 4Z" 
      fill="white" 
      :fill-opacity="0.3"
    />
    <!-- Gradient definition -->
    <defs>
      <linearGradient v-if="gradientId" :id="gradientId" x1="3" y1="2" x2="21" y2="20" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#FFD700"/>
        <stop offset="50%" stop-color="#FFA500"/>
        <stop offset="100%" stop-color="#FF8C00"/>
      </linearGradient>
    </defs>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  size?: number
  color?: string
  animated?: boolean
  useGradient?: boolean
}>(), {
  size: 20,
  color: '#FFD700',
  animated: true,
  useGradient: true
})

const gradientId = computed(() => props.useGradient ? 'crownGradient' : null)
const strokeWidth = 1
</script>

<style scoped>
.premium-crown {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.crown-animated {
  animation: crown-pulse 2s ease-in-out infinite;
}

@keyframes crown-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 2px rgba(255, 215, 0, 0.5));
    transform: scale(1);
  }
  50% {
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.8));
    transform: scale(1.05);
  }
}
</style>
