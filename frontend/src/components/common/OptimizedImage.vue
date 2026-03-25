<script setup lang="ts">
import { computed } from 'vue'
import { Image } from '@unpic/vue'

interface Props {
  src: string
  alt: string
  width?: number | string
  height?: number | string
  priority?: boolean
  layout?: 'constrained' | 'fixed' | 'fullWidth'
  sizes?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  width: undefined,
  height: undefined,
  priority: false,
  layout: 'constrained',
  sizes: '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw'
})

// Используем src как есть (без внешнего CDN)
// @unpic/vue сам генерирует srcset для адаптивности
const imageSrc = computed(() => props.src)

// Генерируем sizes для srcset если не переданы
const computedSizes = computed(() => {
  if (props.sizes) return props.sizes
  return '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw'
})
</script>

<template>
  <Image
    :src="imageSrc"
    :alt="alt"
    :width="width"
    :height="height"
    :layout="layout"
    :sizes="computedSizes"
    :priority="priority"
    :class="props.class"
    loading="lazy"
    decoding="async"
    :background-color="layout === 'fullWidth' ? '#1a1a1a' : undefined"
  />
</template>

<style scoped>
/* Дополнительные стили при необходимости */
</style>
