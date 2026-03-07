<template>
  <div class="rewatch-card" @click="handleClick">
    <div class="card-poster">
      <img
        v-if="posterUrl"
        :src="posterUrl"
        :alt="title"
        class="poster-image"
        @error="handleImageError"
      />
      <div v-else class="poster-placeholder">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <path d="M12 2v20M2 12h20"/>
        </svg>
      </div>

      <!-- Оверлей -->
      <div class="poster-overlay">
        <div class="rewatch-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </div>
      </div>

      <!-- Рейтинг пользователя -->
      <div v-if="userRating" class="rating-badge">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        {{ userRating }}/10
      </div>
    </div>

    <div class="card-info">
      <h3 class="card-title">{{ title }}</h3>
      <p v-if="completedDate" class="card-date">{{ formattedDate }}</p>

      <button class="action-btn" @click.stop="handleAction">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        Пересмотреть
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'

interface Props {
  animeId: number
  title: string
  poster: string
  completedDate: string | null
  userRating: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [id: number]
  action: [id: number]
}>()

const router = useRouter()

const posterUrl = computed(() => {
  if (!props.poster) return null
  return getMediaUrl(props.poster)
})

const formattedDate = computed(() => {
  if (!props.completedDate) return ''
  try {
    return new Date(props.completedDate).toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'short', year: 'numeric'
    })
  } catch {
    return props.completedDate
  }
})

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

// Пересмотр — всегда с первой серии
const handleAction = () => {
  router.push(`/anime/${props.animeId}/watch?episode=1`)
  emit('action', props.animeId)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.rewatch-card {
  flex: 0 0 180px;
  width: 180px;
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}

.rewatch-card:hover { transform: translateY(-4px); }

.card-poster {
  position: relative;
  width: 100%;
  height: 240px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.rewatch-card:hover .poster-image { transform: scale(1.05); }

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Оверлей как в AnimeCard */
.poster-overlay {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  opacity: 0 !important;
  transition: opacity 0.15s ease-out !important;
  z-index: 100 !important;
  pointer-events: none !important;
}

.rewatch-card:hover .poster-overlay {
  opacity: 1 !important;
  pointer-events: auto !important;
}

/* Квадратная синяя кнопка с анимацией распыления (как в AnimeCard) */
.rewatch-icon {
  width: 64px !important;
  height: 64px !important;
  border-radius: 12px !important;
  border: none !important;
  background: var(--accent) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: white !important;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  transform: scale(0.6) !important;
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0) !important;
}

.rewatch-card:hover .rewatch-icon {
  transform: scale(1) !important;
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5) !important;
}

.rewatch-icon:hover {
  transform: scale(1.15) !important;
  background: var(--accent-hover) !important;
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6) !important;
}

.rating-badge {
  position: absolute;
  bottom: var(--space-2);
  left: var(--space-2);
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px var(--space-2);
  background: rgba(8,8,9,0.88);
  color: var(--warning);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  backdrop-filter: blur(8px);
}

.card-info {
  padding: var(--space-2) var(--space-1) var(--space-1);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.card-date {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  width: 100%;
  padding: 6px var(--space-2);
  background: var(--surface-5);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  min-height: 30px;
}

.action-btn:hover {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: var(--accent);
}

@media (max-width: 767px) {
  .rewatch-card { flex: 0 0 140px; width: 140px; }
  .card-poster   { height: 190px; }

  /* На мобильных оверлей всегда виден */
  .poster-overlay {
    opacity: 1;
    background: rgba(0, 0, 0, 0.3);
  }
}
</style>
