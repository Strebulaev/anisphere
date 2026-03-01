<template>
  <div class="anime-card-row" @click="$emit('click')">
    <img
      :src="posterUrl || undefined"
      :alt="titleRu"
      class="anime-card-poster"
    >
    <div class="anime-card-info">
      <span class="anime-card-title">{{ titleRu }}</span>
      <span v-if="titleEn" class="anime-card-title-en">{{ titleEn }}</span>
      <div v-if="rating" class="anime-card-rating">
        Оценка автора: {{ rating }}/10
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  posterUrl?: string | null
  titleRu: string
  titleEn?: string | null
  rating?: number | null
}>()

defineEmits<{ click: [] }>()
</script>

<style scoped>
.anime-card-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.anime-card-row:hover {
  background: #252525;
}

.anime-card-poster {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: #2a2a2a;
}

.anime-card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.anime-card-title {
  color: #ddd;
  font-size: 1rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-card-title-en {
  color: #666;
  font-size: 0.8rem;
}

.anime-card-rating {
  color: #667eea;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}
</style>
