<template>
  <Teleport to="body">
    <Transition name="lightbox">
      <div v-if="show" class="lightbox-overlay" @click.self="close" @keydown.esc="close">
        <!-- Затемненный фон -->
        <div class="lightbox-backdrop" @click="close"></div>
        
        <!-- Кнопка закрытия -->
        <button class="lightbox-close" @click="close" aria-label="Закрыть">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
        
        <!-- Навигация влево -->
        <button 
          v-if="images.length > 1 && currentIndex > 0"
          class="lightbox-nav lightbox-nav-prev"
          @click="prev"
          aria-label="Предыдущее изображение"
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        
        <!-- Навигация вправо -->
        <button 
          v-if="images.length > 1 && currentIndex < images.length - 1"
          class="lightbox-nav lightbox-nav-next"
          @click="next"
          aria-label="Следующее изображение"
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
        
        <!-- Изображение -->
        <div class="lightbox-content">
          <img
            :src="currentImage"
            :alt="`Изображение ${currentIndex + 1}`"
            class="lightbox-image"
            @load="onImageLoad"
            @click="handleImageClick"
          />
          
          <!-- Индикатор загрузки -->
          <div v-if="loading" class="lightbox-loader">
            <div class="spinner"></div>
          </div>
        </div>
        
        <!-- Счетчик изображений -->
        <div v-if="images.length > 1" class="lightbox-counter">
          {{ currentIndex + 1 }} / {{ images.length }}
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  show: boolean
  images: string[]
  initialIndex?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialIndex: 0
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const currentIndex = ref(0)
const loading = ref(true)

const currentImage = computed(() => {
  if (props.images.length === 0) return ''
  return props.images[currentIndex.value] || ''
})

// Сброс индекса при открытии
watch(() => props.show, (newVal) => {
  if (newVal) {
    currentIndex.value = props.initialIndex
    loading.value = true
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

const close = () => {
  emit('close')
}

const prev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    loading.value = true
  }
}

const next = () => {
  if (currentIndex.value < props.images.length - 1) {
    currentIndex.value++
    loading.value = true
  }
}

// Обработка клика по изображению
const handleImageClick = (e: MouseEvent) => {
  e.stopPropagation() // Предотвращаем всплытие
  
  if (props.images.length <= 1) return
  
  // Определяем, в какой половине изображения произошел клик
  const img = e.currentTarget as HTMLImageElement
  const rect = img.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  const middleX = rect.width / 2
  
  if (clickX < middleX) {
    // Клик в левой половине - предыдущее изображение
    prev()
  } else {
    // Клик в правой половине - следующее изображение
    next()
  }
}

const onImageLoad = () => {
  loading.value = false
}

// Клавиатурная навигация
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.show) return
  
  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      prev()
      break
    case 'ArrowRight':
      next()
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(10px);
  cursor: pointer;
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.lightbox-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.lightbox-nav:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-50%) scale(1.1);
}

.lightbox-nav-prev {
  left: 20px;
}

.lightbox-nav-next {
  right: 20px;
}

.lightbox-content {
  position: relative;
  z-index: 5;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  user-select: none;
  -webkit-user-drag: none;
}

.lightbox-loader {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.lightbox-counter {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

/* Анимации */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: all 0.3s ease;
}

.lightbox-enter-active .lightbox-backdrop,
.lightbox-leave-active .lightbox-backdrop {
  transition: opacity 0.3s ease;
}

.lightbox-enter-active .lightbox-image,
.lightbox-leave-active .lightbox-image {
  transition: all 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-from .lightbox-backdrop,
.lightbox-leave-to .lightbox-backdrop {
  opacity: 0;
}

.lightbox-enter-from .lightbox-image,
.lightbox-leave-to .lightbox-image {
  transform: scale(0.9);
  opacity: 0;
}

/* Мобильная адаптация */
@media (max-width: 768px) {
  .lightbox-close {
    top: 10px;
    right: 10px;
    width: 40px;
    height: 40px;
  }
  
  .lightbox-nav {
    width: 44px;
    height: 44px;
  }
  
  .lightbox-nav-prev {
    left: 10px;
  }
  
  .lightbox-nav-next {
    right: 10px;
  }
  
  .lightbox-counter {
    bottom: 10px;
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
