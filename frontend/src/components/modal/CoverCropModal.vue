<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Выберите область обложки</h2>
          <button class="close-btn" @click="handleClose">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="instruction">Перетащите изображение для выбора нужной области</p>
          
          <div 
            class="crop-container"
            ref="cropContainer"
            @mousedown="startDrag"
            @touchstart="startDrag"
          >
            <div 
              class="crop-image"
              ref="cropImage"
              :style="imageStyle"
            ></div>
            
            <!-- Сетка -->
            <div class="crop-grid">
              <div class="grid-line horizontal" style="top: 33.33%"></div>
              <div class="grid-line horizontal" style="top: 66.66%"></div>
              <div class="grid-line vertical" style="left: 33.33%"></div>
              <div class="grid-line vertical" style="left: 66.66%"></div>
            </div>
          </div>
          
          <div class="preview-section">
            <p>Превью:</p>
            <div class="preview-box" :style="previewStyle"></div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="handleClose">Отмена</button>
          <button class="btn btn-primary" @click="handleSave" :disabled="saving">
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  show: boolean
  imageUrl: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  save: [position: { x: number; y: number }]
}>()

const cropContainer = ref<HTMLElement | null>(null)
const cropImage = ref<HTMLElement | null>(null)

const position = ref({ x: 50, y: 50 }) // Проценты
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const startPosition = ref({ x: 0, y: 0 })
const saving = ref(false)

// Размеры контейнера и изображения
const containerWidth = 600
const containerHeight = 200
const imageAspectRatio = 3 / 1 // Стандартное соотношение для обложки

const imageStyle = computed(() => ({
  backgroundImage: `url(${props.imageUrl})`,
  backgroundSize: 'cover',
  backgroundPosition: `${position.value.x}% ${position.value.y}%`,
  width: '100%',
  height: '100%'
}))

const previewStyle = computed(() => ({
  backgroundImage: `url(${props.imageUrl})`,
  backgroundSize: 'cover',
  backgroundPosition: `${position.value.x}% ${position.value.y}%`,
  width: '100%',
  height: '80px'
}))

const startDrag = (event: MouseEvent | TouchEvent) => {
  isDragging.value = true
  
  const clientX = ('touches' in event ? event.touches[0]?.clientX : event.clientX) ?? 0
  const clientY = ('touches' in event ? event.touches[0]?.clientY : event.clientY) ?? 0
  
  dragStart.value = { x: clientX, y: clientY }
  startPosition.value = { ...position.value }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (event: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return
  
  const clientX = ('touches' in event ? event.touches[0]?.clientX : event.clientX) ?? 0
  const clientY = ('touches' in event ? event.touches[0]?.clientY : event.clientY) ?? 0
  
  const deltaX = clientX - dragStart.value.x
  const deltaY = clientY - dragStart.value.y
  
  // Конвертируем пиксели в проценты (примерно)
  const containerEl = cropContainer.value
  if (!containerEl) return
  
  const containerRect = containerEl.getBoundingClientRect()
  const percentX = (deltaX / containerRect.width) * 100
  const percentY = (deltaY / containerRect.height) * 100
  
  // Ограничиваем движение (чтобы изображение не уходило слишком далеко)
  const newX = Math.max(0, Math.min(100, startPosition.value.x + percentX))
  const newY = Math.max(0, Math.min(100, startPosition.value.y + percentY))
  
  position.value = { x: newX, y: newY }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

const handleClose = () => {
  emit('close')
}

const handleSave = async () => {
  saving.value = true
  try {
    emit('save', { ...position.value })
  } finally {
    saving.value = false
  }
}

// Сброс позиции при открытии нового изображения
import { watch } from 'vue'
watch(() => props.show, (newVal) => {
  if (newVal) {
    position.value = { x: 50, y: 50 }
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: var(--color-background-surface, #1a1a1a);
  border-radius: 12px;
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-divider, #333);
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text, #e0e0e0);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary, #888);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--color-background-active, #333);
  color: var(--color-text, #e0e0e0);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.instruction {
  margin: 0 0 16px;
  color: var(--color-text-secondary, #888);
  font-size: 14px;
}

.crop-container {
  position: relative;
  width: 100%;
  height: 200px;
  background: var(--color-background, #0f0f0f);
  border-radius: 8px;
  overflow: hidden;
  cursor: grab;
  user-select: none;
}

.crop-container:active {
  cursor: grabbing;
}

.crop-image {
  position: absolute;
  inset: 0;
}

.crop-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.grid-line {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
}

.grid-line.horizontal {
  left: 0;
  right: 0;
  height: 1px;
}

.grid-line.vertical {
  top: 0;
  bottom: 0;
  width: 1px;
}

.preview-section {
  margin-top: 16px;
}

.preview-section p {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--color-text-tertiary, #666);
}

.preview-box {
  border-radius: 8px;
  background: var(--color-background, #0f0f0f);
  overflow: hidden;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid var(--color-divider, #333);
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: var(--color-background-active, #333);
  color: var(--color-text, #e0e0e0);
}

.btn-secondary:hover {
  background: var(--color-background-surface, #444);
}

.btn-primary {
  background: var(--color-accent, #3b82f6);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover, #2563eb);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
