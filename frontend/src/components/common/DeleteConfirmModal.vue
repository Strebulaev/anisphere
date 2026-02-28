<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content delete-confirm-modal">
      <div class="modal-body">
        <div class="delete-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </div>

        <h2 class="modal-title">{{ title }}</h2>

        <p v-if="message" class="modal-message">{{ message }}</p>

        <div class="modal-actions">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            Отмена
          </button>
          <button
            @click="handleConfirm"
            :disabled="isConfirming"
            class="btn btn-danger"
            type="button"
          >
            <svg v-if="isConfirming" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ isConfirming ? 'Удаление...' : 'Удалить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  show: boolean
  title: string
  message?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  confirm: []
}>()

const isConfirming = ref(false)

const handleConfirm = async () => {
  isConfirming.value = true
  emit('confirm')
  setTimeout(() => {
    isConfirming.value = false
  }, 500)
}

const handleClose = () => {
  if (!isConfirming.value) {
    emit('close')
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 1rem;
}

.modal-content {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  max-width: 400px;
  width: 100%;
  box-shadow: var(--shadow-modal);
}

.modal-body {
  padding: 2rem;
  text-align: center;
}

.delete-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1rem;
  background-color: #fee2e2;
  color: #dc2626;
  border-radius: 50%;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 1rem 0;
}

.modal-message {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0 0 2rem 0;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-danger {
  background-color: #dc2626;
  border-color: #dc2626;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #b91c1c;
  border-color: #b91c1c;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .modal-body {
    padding: 1.5rem;
  }

  .delete-icon {
    width: 3rem;
    height: 3rem;
  }

  .modal-title {
    font-size: 1.125rem;
  }

  .modal-message {
    font-size: 0.875rem;
  }
}
</style>
