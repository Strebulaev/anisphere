<template>
  <div class="fortune-wheel">
    <!-- Колесо -->
    <div class="wheel-container">
      <canvas
        ref="wheelCanvas"
        :width="wheelSize"
        :height="wheelSize"
        class="wheel-canvas"
        :style="{ transform: `rotate(${currentRotation}deg)` }"
      ></canvas>
      
      <!-- Указатель -->
      <div class="wheel-pointer">
        <svg viewBox="0 0 40 60" width="40" height="60">
          <polygon points="20,60 0,20 40,20" fill="#fff" />
          <polygon points="20,55 5,22 35,22" fill="#667eea" />
        </svg>
      </div>
      
      <!-- Центральная кнопка -->
      <button
        v-if="canSpin"
        class="spin-button"
        :disabled="isSpinning"
        @click="$emit('spin')"
      >
        {{ isSpinning ? '🎰' : 'GO!' }}
      </button>
      
      <!-- Пустое состояние - плейсхолдер -->
      <div v-if="itemsList.length === 0 && !isSpinning" class="empty-overlay">
        <div class="empty-icon">🎰</div>
        <div class="empty-text">Добавьте аниме</div>
      </div>
    </div>
    
    <!-- Результат -->
    <transition name="result-fade">
      <div v-if="winner && showResult" class="result-panel">
        <div class="result-title">🎉 Выпало:</div>
        <div class="result-anime">
          <img
            v-if="winner.anime_poster"
            :src="winner.anime_poster"
            :alt="winner.anime_title"
            class="result-poster"
            @error="handleImageError"
          >
          <div class="result-poster-placeholder" v-else> <SakuraIcon name="play" /> </div>
          <div class="result-info">
            <h3>{{ winner.anime_title }}</h3>
            <div class="result-weight">Вес: {{ winner.weight }}</div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import type { RouletteItem } from '@/api/roulette'

const props = defineProps<{
  items?: RouletteItem[]
  totalWeight?: number
  isSpinning?: boolean
  rotationAngle?: number
  winner?: RouletteItem | null
  size?: number
}>()

const emit = defineEmits<{
  spin: []
}>()

const wheelCanvas = ref<HTMLCanvasElement | null>(null)
const currentRotation = ref(0)
const showResult = ref(false)

// Безопасные значения
const itemsList = computed(() => props.items || [])
const weightTotal = computed(() => props.totalWeight || 0)

// Размер колеса
const wheelSize = computed(() => props.size || 400)

const canSpin = computed(() => itemsList.value.length > 0 && !props.isSpinning)

// Обработка ошибки изображения
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

// Цвета для пустых сегментов
const emptyColors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']

// Рисуем колесо
const drawWheel = () => {
  const canvas = wheelCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const centerX = wheelSize.value / 2
  const centerY = wheelSize.value / 2
  const radius = wheelSize.value / 2 - 10

  ctx.clearRect(0, 0, wheelSize.value, wheelSize.value)

  // Если есть элементы - рисуем реальные сегменты
  if (itemsList.value.length > 0 && weightTotal.value > 0) {
    drawRealSegments(ctx, centerX, centerY, radius)
  } else {
    // Рисуем 5 пустых сегментов-плейсхолдеров
    drawEmptySegments(ctx, centerX, centerY, radius)
  }

  // Центральный круг
  ctx.beginPath()
  ctx.arc(centerX, centerY, 40, 0, Math.PI * 2)
  ctx.fillStyle = '#1a1a1a'
  ctx.fill()
  ctx.strokeStyle = '#667eea'
  ctx.lineWidth = 3
  ctx.stroke()
}

const drawRealSegments = (ctx: CanvasRenderingContext2D, centerX: number, centerY: number, radius: number) => {
  let startAngle = -Math.PI / 2

  itemsList.value.forEach((item) => {
    const sliceAngle = (item.weight / weightTotal.value) * 2 * Math.PI
    const endAngle = startAngle + sliceAngle

    // Сектор
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, endAngle)
    ctx.closePath()

    // Градиент для сектора
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius)
    gradient.addColorStop(0, lightenColor(item.color, 30))
    gradient.addColorStop(1, item.color)
    ctx.fillStyle = gradient
    ctx.fill()

    // Граница сектора
    ctx.strokeStyle = 'rgba(0,0,0,0.3)'
    ctx.lineWidth = 2
    ctx.stroke()

    // Текст
    ctx.save()
    ctx.translate(centerX, centerY)
    ctx.rotate(startAngle + sliceAngle / 2)
    ctx.textAlign = 'right'
    ctx.fillStyle = '#fff'
    ctx.font = 'bold 12px sans-serif'
    
    // Обрезаем длинное название
    let title = item.anime_title || 'Аниме'
    if (title.length > 15) {
      title = title.substring(0, 12) + '...'
    }
    
    ctx.fillText(title, radius - 20, 4)
    ctx.restore()

    startAngle = endAngle
  })
}

const drawEmptySegments = (ctx: CanvasRenderingContext2D, centerX: number, centerY: number, radius: number) => {
  const segmentAngle = (2 * Math.PI) / 5
  let startAngle = -Math.PI / 2

  for (let i = 0; i < 5; i++) {
    const endAngle = startAngle + segmentAngle

    // Сектор
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, endAngle)
    ctx.closePath()

    // Цвет плейсхолдера
    const color = emptyColors[i] ?? '#667eea'
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius)
    gradient.addColorStop(0, lightenColor(color, 20))
    gradient.addColorStop(1, color)
    ctx.fillStyle = gradient
    ctx.fill()

    // Граница
    ctx.strokeStyle = 'rgba(0,0,0,0.2)'
    ctx.lineWidth = 2
    ctx.stroke()

    // Текст плейсхолдера
    ctx.save()
    ctx.translate(centerX, centerY)
    ctx.rotate(startAngle + segmentAngle / 2)
    ctx.textAlign = 'right'
    ctx.fillStyle = 'rgba(255,255,255,0.5)'
    ctx.font = 'bold 12px sans-serif'
    ctx.fillText(`Слот ${i + 1}`, radius - 20, 4)
    ctx.restore()

    startAngle = endAngle
  }
}

// Осветляет цвет
const lightenColor = (color: string | undefined, percent: number): string => {
  if (!color) return '#667eea'
  const hex = color.replace('#', '')
  const num = parseInt(hex, 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.min(255, (num >> 16) + amt)
  const G = Math.min(255, ((num >> 8) & 0x00FF) + amt)
  const B = Math.min(255, (num & 0x0000FF) + amt)
  return `#${(1 << 24 | R << 16 | G << 8 | B).toString(16).slice(1)}`
}

// Анимация вращения
watch(() => props.rotationAngle, (newAngle) => {
  if (newAngle && props.isSpinning) {
    currentRotation.value = newAngle
  }
})

// Показываем результат
watch(() => props.winner, (newWinner) => {
  if (newWinner && !props.isSpinning) {
    setTimeout(() => {
      showResult.value = true
    }, 500)
  }
})

watch(() => props.isSpinning, (spinning) => {
  if (spinning) {
    showResult.value = false
  }
})

// Перерисовываем при изменении элементов
watch(() => [itemsList.value, weightTotal.value], () => {
  drawWheel()
}, { deep: true })

onMounted(() => {
  drawWheel()
})
</script>

<style scoped>
.fortune-wheel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.wheel-container {
  position: relative;
  width: v-bind('wheelSize + "px"');
  height: v-bind('wheelSize + "px"');
}

.wheel-canvas {
  transition: transform 5s cubic-bezier(0.17, 0.67, 0.12, 0.99);
  filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.5));
}

.wheel-pointer {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.spin-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 1.2rem;
  font-weight: bold;
  border: 3px solid #fff;
  cursor: pointer;
  z-index: 20;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.spin-button:hover:not(:disabled) {
  transform: translate(-50%, -50%) scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.spin-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 5;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.3;
}

.empty-text {
  color: rgba(255,255,255,0.4);
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.result-panel {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border: 2px solid #667eea;
  border-radius: 16px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.result-title {
  font-size: 1.2rem;
  color: #fbbf24;
  margin-bottom: 1rem;
}

.result-anime {
  display: flex;
  gap: 1rem;
  align-items: center;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1rem;
}

.result-poster {
  width: 60px;
  height: 85px;
  object-fit: cover;
  border-radius: 8px;
}

.result-poster-placeholder {
  width: 60px;
  height: 85px;
  background: #2a2a2a;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.result-info {
  flex: 1;
  text-align: left;
}

.result-info h3 {
  color: #fff;
  font-size: 1rem;
  margin: 0 0 0.5rem 0;
}

.result-weight {
  color: #888;
  font-size: 0.85rem;
}

.result-fade-enter-active,
.result-fade-leave-active {
  transition: all 0.5s ease;
}

.result-fade-enter-from,
.result-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 500px) {
  .wheel-container {
    width: 300px;
    height: 300px;
  }
  
  .wheel-canvas {
    width: 300px !important;
    height: 300px !important;
  }
  
  .spin-button {
    width: 60px;
    height: 60px;
    font-size: 1rem;
  }
}
</style>
