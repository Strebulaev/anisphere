<template>
  <div class="carousel-section">
    <!-- Заголовок секции -->
    <div class="carousel-header">
      <h2 class="carousel-title">{{ title }}</h2>
      <button 
        v-if="showViewAll" 
        class="view-all-btn"
        @click="handleViewAll"
      >
        Все
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </button>
    </div>

    <!-- Карусель -->
    <div class="carousel-container" ref="carouselRef">
      <!-- Кнопка влево -->
      <button 
        v-if="showLeftArrow" 
        class="carousel-arrow carousel-arrow-left"
        @click="scrollLeft"
        :disabled="isAtStart"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>

      <!-- Карточки -->
      <div class="carousel-track" ref="trackRef">
        <!-- Скелетоны при загрузке -->
        <template v-if="loading">
          <div 
            v-for="n in skeletonCount" 
            :key="'skeleton-' + n"
            class="carousel-card skeleton"
          >
            <div class="skeleton-poster"></div>
            <div class="skeleton-info">
              <div class="skeleton-title"></div>
              <div class="skeleton-meta"></div>
            </div>
          </div>
        </template>

        <!-- Ошибка -->
        <template v-else-if="error">
          <div class="carousel-error">
            <p>{{ errorMessage }}</p>
            <button class="retry-btn" @click="$emit('retry')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Повторить
            </button>
          </div>
        </template>

        <!-- Пустое состояние (скрыть) -->
        <template v-else-if="isEmpty && hideOnEmpty">
          <!-- Ничего не показываем -->
        </template>

        <!-- Пустое состояние (показать сообщение) -->
        <template v-else-if="isEmpty && !hideOnEmpty">
          <div class="carousel-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/>
              <path d="M12 2v20M2 12h20"/>
            </svg>
            <p>{{ emptyMessage }}</p>
          </div>
        </template>

        <!-- Карточки контента -->
        <template v-else>
          <slot></slot>
        </template>
      </div>

      <!-- Кнопка вправо -->
      <button 
        v-if="showRightArrow" 
        class="carousel-arrow carousel-arrow-right"
        @click="scrollRight"
        :disabled="isAtEnd"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </button>
    </div>

    <!-- Индикаторы для мобильных -->
    <div v-if="showDots" class="carousel-dots">
      <button 
        v-for="n in totalDots" 
        :key="'dot-' + n"
        class="carousel-dot"
        :class="{ active: currentPage === n - 1 }"
        @click="scrollToPage(n - 1)"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  title: string
  loading?: boolean
  error?: boolean
  errorMessage?: string
  emptyMessage?: string
  hideOnEmpty?: boolean
  showViewAll?: boolean
  viewAllLink?: string
  itemsCount?: number
  scrollStep?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: false,
  errorMessage: 'Не удалось загрузить контент',
  emptyMessage: 'Пусто',
  hideOnEmpty: true,
  showViewAll: false,
  itemsCount: 0,
  scrollStep: 4
})

const emit = defineEmits<{
  retry: []
  'view-all': []
}>()

const carouselRef = ref<HTMLElement | null>(null)
const trackRef = ref<HTMLElement | null>(null)
const isAtStart = ref(true)
const isAtEnd = ref(false)
const currentPage = ref(0)
const containerWidth = ref(0)

const cardWidth = 200 // ширина карточки + gap
const skeletonCount = computed(() => Math.min(props.itemsCount || 5, 5))

const showLeftArrow = computed(() => !props.loading && !props.error && !isAtStart.value)
const showRightArrow = computed(() => !props.loading && !props.error && !isAtEnd.value)
const showDots = computed(() => false) // Отключено для сейчас
const totalDots = computed(() => Math.ceil(props.itemsCount / props.scrollStep))

const isEmpty = computed(() => props.itemsCount === 0)

const checkScrollPosition = () => {
  if (!trackRef.value || !carouselRef.value) return
  
  const track = trackRef.value
  const container = carouselRef.value
  
  containerWidth.value = container.clientWidth
  
  isAtStart.value = track.scrollLeft <= 0
  isAtEnd.value = track.scrollLeft + track.clientWidth >= track.scrollWidth - 10
  
  currentPage.value = Math.round(track.scrollLeft / (cardWidth * props.scrollStep))
}

const scrollLeft = () => {
  if (!trackRef.value) return
  trackRef.value.scrollBy({
    left: -(cardWidth * props.scrollStep),
    behavior: 'smooth'
  })
}

const scrollRight = () => {
  if (!trackRef.value) return
  trackRef.value.scrollBy({
    left: cardWidth * props.scrollStep,
    behavior: 'smooth'
  })
}

const scrollToPage = (page: number) => {
  if (!trackRef.value) return
  trackRef.value.scrollTo({
    left: page * cardWidth * props.scrollStep,
    behavior: 'smooth'
  })
}

const handleViewAll = () => {
  if (props.viewAllLink) {
    window.location.href = props.viewAllLink
  } else {
    emit('view-all')
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (trackRef.value) {
    trackRef.value.addEventListener('scroll', checkScrollPosition)
    checkScrollPosition()
    
    resizeObserver = new ResizeObserver(checkScrollPosition)
    if (carouselRef.value) {
      resizeObserver.observe(carouselRef.value)
    }
  }
})

onUnmounted(() => {
  if (trackRef.value) {
    trackRef.value.removeEventListener('scroll', checkScrollPosition)
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

watch(() => props.itemsCount, () => {
  setTimeout(checkScrollPosition, 100)
})
</script>

<style scoped>
.carousel-section {
  margin-bottom: 32px;
}

.carousel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 0 4px;
}

.carousel-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text, #fff);
  margin: 0;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--color-accent, #3a86ff);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.view-all-btn:hover {
  background-color: rgba(58, 134, 255, 0.1);
}

.carousel-container {
  position: relative;
  overflow: hidden;
}

.carousel-track {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 4px;
}

.carousel-track::-webkit-scrollbar {
  display: none;
}

.carousel-card {
  flex: 0 0 180px;
  width: 180px;
  cursor: pointer;
  transition: transform 0.2s;
}

.carousel-card:hover {
  transform: translateY(-4px);
}

/* Скелетоны */
.carousel-card.skeleton {
  pointer-events: none;
}

.skeleton-poster {
  width: 100%;
  height: 240px;
  background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 12px;
}

.skeleton-info {
  padding: 8px 0;
}

.skeleton-title {
  height: 16px;
  width: 80%;
  background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-meta {
  height: 12px;
  width: 60%;
  background: linear-gradient(90deg, #2a2a2a 25%, #3a3a3a 50%, #2a2a2a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Ошибка */
.carousel-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--color-text-secondary, #aaa);
}

.carousel-error p {
  margin: 0 0 16px 0;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: var(--color-accent, #3a86ff);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #2d7af7;
}

/* Пустое состояние */
.carousel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  color: var(--color-text-secondary, #666);
  min-height: 240px;
}

.carousel-empty svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.carousel-empty p {
  margin: 0;
  font-size: 14px;
  text-align: center;
}

/* Стрелки навигации */
.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s;
}

.carousel-container:hover .carousel-arrow {
  opacity: 1;
}

.carousel-arrow:hover:not(:disabled) {
  background-color: var(--color-accent, #3a86ff);
}

.carousel-arrow:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.carousel-arrow-left {
  left: 8px;
}

.carousel-arrow-right {
  right: 8px;
}

/* Точки */
.carousel-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.carousel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-text-tertiary, #666);
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.carousel-dot.active {
  background-color: var(--color-accent, #3a86ff);
}

/* Адаптивность */
@media (max-width: 767px) {
  .carousel-card {
    flex: 0 0 140px;
    width: 140px;
  }
  
  .skeleton-poster {
    height: 190px;
  }
  
  .carousel-arrow {
    display: none;
  }
}
</style>
