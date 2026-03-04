<template>
  <div class="recommend-card" @click="handleClick">
    <div class="card-poster">
      <!-- Номер в топе -->
      <div v-if="rank && rank <= 10" class="rank-badge" :class="rank <= 3 ? 'rank-top' : ''">#{{ rank }}</div>
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

      <!-- Статус -->
      <div v-if="status" class="status-badge" :class="`status-${status}`">
        {{ statusText }}
      </div>

      <!-- Рейтинг -->
      <div v-if="rating" class="rating-badge">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        {{ formattedRating }}
      </div>
    </div>

    <div class="card-info">
      <h3 class="card-title">{{ title }}</h3>

      <div v-if="displayGenres.length" class="card-genres">
        <span v-for="genre in displayGenres" :key="genre" class="genre-tag">{{ genre }}</span>
      </div>

      <button class="action-btn" @click.stop="handleAddToCollection">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        В коллекцию
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
  genres: string[]
  rating: number | null
  ratingCount: number
  status: string
  year: number | null
  rank?: number   // позиция в топе (необязательно)
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [id: number]
  'add-to-collection': [id: number]
}>()

const router = useRouter()

const posterUrl = computed(() => {
  if (!props.poster) return null
  return getMediaUrl(props.poster)
})

const formattedRating = computed(() => props.rating ? props.rating.toFixed(1) : '')

const displayGenres = computed(() => props.genres?.slice(0, 2) ?? [])

const statusText = computed(() => {
  const map: Record<string, string> = {
    ongoing: 'Онгоинг', finished: 'Завершено', announced: 'Анонс', released: 'Вышло'
  }
  return map[props.status] || props.status
})

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

const handleAddToCollection = () => {
  emit('add-to-collection', props.animeId)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.recommend-card {
  flex: 0 0 180px;
  width: 180px;
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}

.recommend-card:hover { transform: translateY(-4px); }

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

.recommend-card:hover .poster-image { transform: scale(1.05); }

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
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

.status-badge {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.status-ongoing   { background: var(--accent);  color: white; }
.status-finished  { background: var(--surface-5); color: var(--text-secondary); }
.status-announced { background: var(--warning);  color: #000; }
.status-released  { background: var(--accent-2); color: white; }

.rank-badge {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 800;
  background: rgba(8,8,9,0.85);
  color: var(--text-secondary);
  backdrop-filter: blur(8px);
  letter-spacing: 0.02em;
  z-index: 2;
}

.rank-badge.rank-top {
  background: var(--accent);
  color: white;
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

.card-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.genre-tag {
  font-size: 10px;
  color: var(--accent);
  background: var(--accent-subtle);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-weight: 500;
  white-space: nowrap;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  width: 100%;
  padding: 6px var(--space-2);
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  min-height: 30px;
}

.action-btn:hover {
  background: var(--accent);
  color: var(--text-on-accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

@media (max-width: 767px) {
  .recommend-card { flex: 0 0 140px; width: 140px; }
  .card-poster    { height: 190px; }
}
</style>
