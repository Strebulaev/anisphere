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
  inset: 0;
  background-color: rgba(0, 0, 0, 0.78);
  backdrop-filter: var(--blur-md);
  -webkit-backdrop-filter: var(--blur-md);
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
}

.modal-container {
  background-color: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  animation: scaleIn var(--duration-slow) var(--ease-spring);
}

.modal-container--small  { width: 100%; max-width: 400px; }
.modal-container--medium { width: 100%; max-width: 560px; }
.modal-container--large  { width: 100%; max-width: 800px; }
.modal-container--full   { width: 100%; max-width: 100%; height: calc(100vh - 48px); }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.modal-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.modal-close {
  width: 32px;
  height: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--text-tertiary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  border: none;
}

.modal-close:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.modal-body {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

/* Анимации */
.modal-enter-active { transition: opacity var(--duration-base) var(--ease-out); }
.modal-leave-active { transition: opacity var(--duration-base) var(--ease-out); }
.modal-enter-from,
.modal-leave-to     { opacity: 0; }

.modal-enter-active .modal-container { transition: transform var(--duration-slow) var(--ease-spring); }
.modal-leave-active .modal-container  { transition: transform var(--duration-base) var(--ease-out); }
.modal-enter-from   .modal-container  { transform: translateY(16px) scale(0.96); }
.modal-leave-to     .modal-container  { transform: translateY(8px) scale(0.98); }

@keyframes scaleIn {
  from { transform: translateY(16px) scale(0.96); opacity: 0; }
  to   { transform: translateY(0) scale(1); opacity: 1; }
}

/* Адаптивность */
@media (max-width: 767px) {
  .modal-overlay { padding: 0; align-items: flex-end; }

  .modal-container {
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    border-bottom: none;
    max-height: 92vh;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
  }

  .modal-container--small,
  .modal-container--medium,
  .modal-container--large,
  .modal-container--full { max-width: 100%; }

  .modal-enter-from .modal-container,
  .modal-leave-to   .modal-container { transform: translateY(100%); }
}
</style>
