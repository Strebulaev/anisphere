<script setup lang="ts">
import { computed } from 'vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

const props = withDefaults(defineProps<{
  rating: number
  maxRating?: number
  size?: number
  showNumber?: boolean
  readonly?: boolean
}>(), {
  maxRating: 5,
  size: 16,
  showNumber: false,
  readonly: true
})

const emit = defineEmits<{
  (e: 'update:rating', value: number): void
}>()

// Вычисляем массив звёзд
const stars = computed(() => {
  const result = []
  for (let i = 1; i <= props.maxRating; i++) {
    result.push({
      index: i,
      filled: i <= Math.floor(props.rating),
      half: i === Math.ceil(props.rating) && props.rating % 1 !== 0,
      empty: i > props.rating
    })
  }
  return result
})

function setRating(value: number) {
  if (!props.readonly) {
    emit('update:rating', value)
  }
}
</script>

<template>
  <div class="star-rating" :class="{ readonly, clickable: !readonly }">
    <div class="stars-container">
      <button
        v-for="star in stars"
        :key="star.index"
        type="button"
        class="star-button"
        :class="{ filled: star.filled, half: star.half, empty: star.empty }"
        :disabled="readonly"
        @click="setRating(star.index)"
      >
        <SakuraIcon
          :name="star.filled ? 'star' : star.half ? 'star-half' : 'star'"
          :size="size"
          :class="{ 'star-empty': star.empty }"
        />
      </button>
    </div>
    
    <span v-if="showNumber" class="rating-number">
      {{ rating.toFixed(1) }}
    </span>
  </div>
</template>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stars-container {
  display: flex;
  align-items: center;
  gap: 2px;
}

.star-button {
  background: none;
  border: none;
  padding: 0;
  cursor: default;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent, #ff7eb3);
  transition: transform 0.2s ease;
}

.star-rating.clickable .star-button {
  cursor: pointer;
}

.star-rating.clickable .star-button:hover {
  transform: scale(1.2);
}

.star-button.filled {
  color: var(--accent, #ff7eb3);
}

.star-button.half {
  color: var(--accent, #ff7eb3);
}

.star-button.empty {
  color: var(--text-muted, #9ca3af);
}

.star-empty {
  opacity: 0.5;
}

.rating-number {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #374151);
  margin-left: 4px;
}
</style>
