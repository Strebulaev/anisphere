<template>
  <div class="continue-card" @click="handleClick">
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

      <!-- Оверлей при наведении -->
      <div class="poster-overlay">
        <div class="play-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </div>
      </div>

      <!-- Прогресс бар снизу -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <div class="card-info">
      <h3 class="card-title">{{ title }}</h3>
      <p class="card-episode">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        Серия {{ currentEpisode }} из {{ totalEpisodes }}
      </p>

      <button class="action-btn" @click.stop="handleAction">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Продолжить
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
  currentEpisode: number
  totalEpisodes: number
  progressPercent: number
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

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

// Переходим на страницу просмотра с нужной серией
const handleAction = () => {
  router.push(`/anime/${props.animeId}/watch?episode=${props.currentEpisode}`)
  emit('action', props.animeId)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.continue-card {
  flex: 0 0 180px;
  width: 180px;
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}

.continue-card:hover { transform: translateY(-4px); }

/* ── Постер ─────────────────────────────────────────── */
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

.continue-card:hover .poster-image { transform: scale(1.05); }

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Оверлей */
.poster-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out);
}

.continue-card:hover .poster-overlay { opacity: 1; }

.play-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  padding-left: 4px;
  box-shadow: 0 0 20px rgba(124,92,252,0.5);
}

/* Прогресс снизу */
.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0,0,0,0.4);
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}

/* ── Инфо ───────────────────────────────────────────── */
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

.card-episode {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  width: 100%;
  padding: 6px var(--space-2);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
  min-height: 30px;
}

.action-btn:hover {
  background: var(--accent-hover);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

@media (max-width: 767px) {
  .continue-card { flex: 0 0 140px; width: 140px; }
  .card-poster   { height: 190px; }
}
</style>
