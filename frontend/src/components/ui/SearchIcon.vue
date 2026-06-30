<template>
  <svg
    class="search-icon-svg"
    :width="width"
    :height="height"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
</template>

<script setup lang="ts">
defineProps({
  width: {
    type: [String, Number],
    default: '18'
  },
  height: {
    type: [String, Number],
    default: '18'
  },
  strokeWidth: {
    type: [String, Number],
    default: 2
  }
})
</script>

<style scoped>
.search-icon-svg {
  flex-shrink: 0;
  display: block;
}
</style>
