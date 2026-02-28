<template>
  <transition name="modal">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content quick-view-modal">
        <button @click="handleClose" class="modal-close" type="button">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        <div class="modal-body">
          <div class="quick-view-content">
            <div class="poster-section">
              <img
                v-if="anime.poster_url"
                :src="getMediaUrl(anime.poster_url) || undefined"
                :alt="anime.title_ru || anime.title_en"
                class="anime-poster"
              />
              <div v-else class="anime-poster-placeholder">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M12 2v20M2 12h20"/>
                </svg>
              </div>
            </div>

            <div class="info-section">
              <h2 class="anime-title">{{ anime.title_ru || anime.title_en }}</h2>
              <p v-if="anime.title_ru && anime.title_en && anime.title_ru !== anime.title_en" class="anime-title-en">
                {{ anime.title_en }}
              </p>

              <div class="anime-meta">
                <span v-if="anime.year" class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  {{ anime.year }}
                </span>
                <span v-if="anime.episodes" class="meta-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="7" width="20" height="15" rx="2" ry="2"/>
                    <polyline points="17 2 12 7 7 2"/>
                  </svg>
                  {{ anime.episodes }} эп.
                </span>
                <span v-if="anime.status" class="meta-item status" :class="statusClass">
                  {{ statusLabel }}
                </span>
              </div>

              <div v-if="anime.genres?.length" class="anime-genres">
                <span
                  v-for="(genre, idx) in anime.genres.slice(0, 4)"
                  :key="typeof genre === 'string' ? idx : genre.id"
                  class="genre-tag"
                >
                  {{ typeof genre === 'string' ? genre : genre.name }}
                </span>
                <span v-if="anime.genres.length > 4" class="genre-more">
                  +{{ anime.genres.length - 4 }}
                </span>
              </div>

              <div class="anime-rating">
                <div class="rating-stars">
                  <svg
                    v-for="i in 5"
                    :key="i"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    :fill="i <= Math.round((('score' in anime ? (anime as any).score : 0) || 0) / 2) ? 'currentColor' : 'none'"
                    stroke="currentColor"
                    stroke-width="2"
                    class="star"
                  >
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </div>
                <span class="rating-value">{{ ('score' in anime && (anime as any).score) ? ((anime as any).score as number).toFixed(1) : 'N/A' }}</span>
              </div>

              <p class="anime-description">
                {{ truncatedDescription }}
                <button
                  v-if="anime.description && anime.description.length > 200"
                  @click="showFullDescription = !showFullDescription"
                  class="show-more-btn"
                  type="button"
                >
                  {{ showFullDescription ? 'Свернуть' : 'Подробнее' }}
                </button>
              </p>

              <div class="quick-actions">
                <button @click="handleDetail" class="action-btn primary-btn" type="button">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  Подробнее
                </button>
                <button @click="handleAddToLibrary" class="action-btn secondary-btn" type="button">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                  </svg>
                  В коллекцию
                </button>
                <button
                  @click="handleToggleFavorite"
                  :class="['action-btn', 'favorite-btn', { active: isFavorite }]"
                  type="button"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Anime } from '@/types'
import { getMediaUrl } from '@/api/client'

interface Props {
  show: boolean
  anime: Anime
  isFavorite?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isFavorite: false
})

const emit = defineEmits<{
  close: []
  addToLibrary: [anime: Anime]
  toggleFavorite: [anime: Anime]
}>()

const router = useRouter()
const showFullDescription = ref(false)

const statusClass = computed(() => {
  const status = props.anime.status?.toLowerCase()
  if (status === 'ongoing') return 'ongoing'
  if (status === 'finished' || status === 'completed') return 'finished'
  if (status === 'announced') return 'announced'
  return ''
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    ongoing: 'Онгоинг',
    finished: 'Завершён',
    completed: 'Завершён',
    announced: 'Анонсирован',
    released: 'Вышедший'
  }
  const statusKey = props.anime.status?.toLowerCase()
  return statusKey ? labels[statusKey] || props.anime.status : props.anime.status
})

const truncatedDescription = computed(() => {
  if (!props.anime.description) return 'Описание отсутствует'
  
  if (showFullDescription.value) {
    return props.anime.description
  }
  
  return props.anime.description.slice(0, 200)
})

const handleDetail = () => {
  router.push(`/anime/${props.anime.id}`)
  handleClose()
}

const handleAddToLibrary = () => {
  emit('addToLibrary', props.anime)
}

const handleToggleFavorite = () => {
  emit('toggleFavorite', props.anime)
}

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
  position: relative;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  z-index: 10;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(90deg);
}

.modal-body {
  padding: 0;
}

.quick-view-content {
  display: flex;
  gap: 2rem;
}

.poster-section {
  flex-shrink: 0;
}

.anime-poster {
  width: 240px;
  border-radius: 0.75rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.anime-poster-placeholder {
  width: 240px;
  height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  border-radius: 0.75rem;
  color: var(--color-text-tertiary);
}

.info-section {
  flex: 1;
  min-width: 0;
  padding: 2rem;
  padding-right: 3rem;
}

.anime-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.25rem 0;
  line-height: 1.2;
}

.anime-title-en {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 1rem 0;
  font-weight: 400;
}

.anime-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.meta-item svg {
  color: var(--color-text-tertiary);
}

.meta-item.status {
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.meta-item.status.ongoing {
  background-color: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.meta-item.status.finished {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.meta-item.status.announced {
  background-color: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.anime-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.genre-tag {
  padding: 0.375rem 0.75rem;
  background-color: var(--color-background-active);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.genre-more {
  padding: 0.375rem 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
}

.anime-rating {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.rating-stars {
  display: flex;
  gap: 0.125rem;
  color: var(--color-accent-orange);
}

.star {
  flex-shrink: 0;
}

.rating-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-accent-orange);
}

.anime-description {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.show-more-btn {
  background: none;
  border: none;
  color: var(--color-accent);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
  transition: color 0.2s var(--transition-smooth);
}

.show-more-btn:hover {
  color: var(--color-accent-hover);
  text-decoration: underline;
}

.quick-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.primary-btn {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.primary-btn:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.4);
}

.secondary-btn {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text);
}

.secondary-btn:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.favorite-btn {
  width: 44px;
  padding: 0;
  background-color: var(--color-background-active);
  border-color: var(--color-divider-light);
  color: var(--color-text-tertiary);
}

.favorite-btn:hover {
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
  transform: scale(1.05);
}

.favorite-btn.active {
  background-color: var(--color-accent-pink);
  border-color: var(--color-accent-pink);
  color: #fff;
}

.favorite-btn.active:hover {
  background-color: #db2777;
  border-color: #db2777;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(20px);
}

@media (max-width: 768px) {
  .quick-view-content {
    flex-direction: column;
  }

  .poster-section {
    display: flex;
    justify-content: center;
    padding-top: 2rem;
  }

  .anime-poster,
  .anime-poster-placeholder {
    width: 180px;
    height: 254px;
  }

  .info-section {
    padding: 1.5rem;
  }

  .anime-title {
    font-size: 1.25rem;
  }

  .quick-actions {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }

  .favorite-btn {
    width: 100%;
  }
}
</style>
