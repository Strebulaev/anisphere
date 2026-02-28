<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content shortcuts-modal">
      <div class="modal-header">
        <h2 class="modal-title">Горячие клавиши</h2>
        <button @click="handleClose" class="modal-close" type="button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="shortcuts-section">
          <h3 class="shortcuts-section-title">Папки</h3>
          <div class="shortcuts-list">
            <div class="shortcut-item">
              <kbd>Alt</kbd> + <kbd>0</kbd>
              <span>Все чаты</span>
            </div>
            <div class="shortcut-item">
              <kbd>Alt</kbd> + <kbd>1-9</kbd>
              <span>Переключить папку</span>
            </div>
          </div>
        </div>

        <div class="shortcuts-section">
          <h3 class="shortcuts-section-title">Навигация</h3>
          <div class="shortcuts-list">
            <div class="shortcut-item">
              <kbd>↑</kbd> / <kbd>↓</kbd>
              <span>Переместиться по чатам</span>
            </div>
            <div class="shortcut-item">
              <kbd>Enter</kbd>
              <span>Открыть чат</span>
            </div>
            <div class="shortcut-item">
              <kbd>Escape</kbd>
              <span>Закрыть модалку</span>
            </div>
          </div>
        </div>

        <div class="shortcuts-section">
          <h3 class="shortcuts-section-title">Поиск</h3>
          <div class="shortcuts-list">
            <div class="shortcut-item">
              <kbd>/</kbd>
              <span>Поиск по чатам</span>
            </div>
            <div class="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>F</kbd>
              <span>Расширенный поиск</span>
            </div>
          </div>
        </div>

        <div class="shortcuts-section">
          <h3 class="shortcuts-section-title">Действия</h3>
          <div class="shortcuts-list">
            <div class="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>N</kbd>
              <span>Новый чат</span>
            </div>
            <div class="shortcut-item">
              <kbd>Ctrl</kbd> + <kbd>E</kbd>
              <span>Редактировать папки</span>
            </div>
            <div class="shortcut-item">
              <kbd>?</kbd>
              <span>Показать горячие клавиши</span>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleClose" class="btn btn-primary" type="button">
          Закрыть
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  show: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

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
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--color-background-active);
  color: #ef4444;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.shortcuts-section {
  margin-bottom: 1.5rem;
}

.shortcuts-section:last-child {
  margin-bottom: 0;
}

.shortcuts-section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  margin: 0 0 0.75rem 0;
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9375rem;
  color: var(--color-text);
}

.shortcut-item span {
  flex: 1;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.75rem;
  padding: 0 0.5rem;
  background: linear-gradient(180deg, #ffffff 0%, #f3f4f6 100%);
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-family: monospace;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #374151;
  box-shadow: 0 2px 0 #9ca3af;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn {
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

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .shortcut-item {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  kbd {
    min-width: 1.5rem;
    height: 1.5rem;
    font-size: 0.75rem;
  }
}
</style>
