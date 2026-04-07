<template>
  <div v-if="recommendations.length > 0" class="recommendation-banner">
    <div class="banner-header">
      <div class="banner-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span>{{ title }}</span>
      </div>
      <button
        @click="handleRefresh"
        :disabled="isLoading"
        class="refresh-btn"
        type="button"
        title="Обновить рекомендации"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: isLoading }">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
      </button>
    </div>

    <div class="banner-content">
      <transition name="carousel">
        <div :key="carouselKey" class="recommendation-carousel">
          <div
            v-for="anime in visibleRecommendations"
            :key="anime.id"
            class="recommendation-item"
            @click="handleClick(anime)"
          >
            <div class="recommendation-poster">
              <img
                v-if="anime.poster_url"
                :src="getMediaUrl(anime.poster_url) || undefined"
                :alt="anime.title_ru || anime.title_en"
                loading="lazy"
              />
              <div v-else class="poster-placeholder">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M12 2v20M2 12h20"/>
                </svg>
              </div>
              <div class="recommendation-overlay">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
            </div>
            <div class="recommendation-info">
              <h4 class="recommendation-title">{{ anime.title_ru || anime.title_en }}</h4>
              <div class="recommendation-meta">
                <span v-if="anime.year">{{ anime.year }}</span>
                <span v-if="'score' in anime && anime.score" class="rating"><SakuraIcon name="star" /> {{ (anime.score as number).toFixed(1) }}</span>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <div v-if="hasMore" class="banner-footer">
      <button
        @click="handleShowMore"
        class="show-more-btn"
        type="button"
      >
        Показать ещё
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Anime } from '@/types'
import { getMediaUrl } from '@/api/client'

interface Props {
  recommendations: Anime[]
  title?: string
  maxVisible?: number
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Вам может понравиться',
  maxVisible: 6,
  isLoading: false
})

const emit = defineEmits<{
  refresh: []
  click: [anime: Anime]
  showMore: []
}>()

const router = useRouter()
const carouselKey = ref(0)

const visibleRecommendations = computed(() => {
  return props.recommendations.slice(0, props.maxVisible)
})

const hasMore = computed(() => {
  return props.recommendations.length > props.maxVisible
})

const handleRefresh = () => {
  carouselKey.value++
  emit('refresh')
}

const handleClick = (anime: Anime) => {
  emit('click', anime)
  router.push(`/anime/${anime.id}`)
}

const handleShowMore = () => {
  emit('showMore')
}

onMounted(() => {
  carouselKey.value = Date.now()
})
</script>

<style scoped>
.recommendation-banner {
  background: linear-gradient(135deg, var(--color-background-surface) 0%, var(--color-background-active) 100%);
  border: 1px solid var(--color-divider);
  border-radius: 1rem;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.banner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.banner-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
}

.banner-title svg {
  color: var(--color-accent-orange);
}

.refresh-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}

.refresh-btn svg.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.banner-content {
  overflow: hidden;
}

.recommendation-carousel {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}

.recommendation-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  cursor: pointer;
  transition: transform 0.2s var(--transition-smooth);
}

.recommendation-item:hover {
  transform: translateY(-4px);
}

.recommendation-item:hover .recommendation-poster {
  border-color: var(--color-accent);
}

.recommendation-item:hover .recommendation-overlay {
  opacity: 1;
}

.recommendation-poster {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s var(--transition-smooth);
  background-color: var(--color-background-surface);
}

.recommendation-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

.recommendation-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s var(--transition-smooth);
}

.recommendation-overlay svg {
  color: #fff;
  width: 32px;
  height: 32px;
}

.recommendation-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.recommendation-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recommendation-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.recommendation-meta .rating {
  color: var(--color-accent-orange);
  font-weight: 600;
}

.banner-footer {
  margin-top: 1rem;
  text-align: center;
}

.show-more-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.show-more-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-active);
}

.carousel-enter-active,
.carousel-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.carousel-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.carousel-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@media (max-width: 768px) {
  .recommendation-banner {
    padding: 1rem;
  }

  .banner-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .banner-title {
    font-size: 1rem;
  }

  .recommendation-carousel {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }

  .recommendation-title {
    font-size: 0.75rem;
  }

  .recommendation-meta {
    font-size: 0.6875rem;
  }
}
</style>
