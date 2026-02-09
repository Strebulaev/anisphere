<template>
  <transition name="modal">
    <div v-if="show" class="modal-overlay" @click="handleOverlayClick">
      <div 
        class="modal-container" 
        :class="modalSizeClass"
        @click.stop
      >
        <div class="modal-header" v-if="$slots.header || title">
          <slot name="header">
            <h2 class="modal-title">{{ title }}</h2>
          </slot>
          <button 
            class="modal-close" 
            @click="close" 
            type="button"
            aria-label="Закрыть"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <slot></slot>
        </div>
        
        <div class="modal-footer" v-if="$slots.footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  show: boolean
  title?: string
  size?: 'small' | 'medium' | 'large' | 'full'
  closeOnOverlay?: boolean
  closeOnEscape?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  size: 'medium',
  closeOnOverlay: true,
  closeOnEscape: true,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  close: []
}>()

const modalSizeClass = computed(() => {
  return `modal-container--${props.size}`
})

const close = () => {
  emit('update:show', false)
  emit('close')
}

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    close()
  }
}

const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.closeOnEscape && props.show) {
    close()
  }
}

watch(() => props.show, (newValue) => {
  if (newValue) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscapeKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-container {
  background-color: var(--color-background-secondary);
  border-radius: var(--radius-modal);
  box-shadow: var(--shadow-modal);
  max-height: calc(100vh - 32px);
  display: flex;
  flex-direction: column;
  animation: modalSlideUp 0.3s var(--transition-smooth);
}

.modal-container--small {
  width: 100%;
  max-width: 400px;
}

.modal-container--medium {
  width: 100%;
  max-width: 560px;
}

.modal-container--large {
  width: 100%;
  max-width: 800px;
}

.modal-container--full {
  width: 100%;
  max-width: 100%;
  height: calc(100vh - 32px);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-divider);
}

.modal-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--color-text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
  border: none;
}

.modal-close:hover {
  background-color: var(--color-background-surface);
  color: var(--color-text);
}

.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-divider);
}

/* Анимации */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s var(--transition-smooth);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s var(--transition-smooth);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: translateY(20px) scale(0.95);
}

@keyframes modalSlideUp {
  from {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* Адаптивность */
@media (max-width: 767px) {
  .modal-overlay {
    padding: 0;
  }
  
  .modal-container {
    border-radius: var(--radius-modal) var(--radius-modal) 0 0;
    max-height: 100vh;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
  }
  
  .modal-container--small,
  .modal-container--medium,
  .modal-container--large,
  .modal-container--full {
    max-width: 100%;
  }
}
</style>
