<template>
  <transition name="modal">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content report-modal">
        <div class="modal-header">
          <h2 class="modal-title">Пожаловаться</h2>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="report-info">
            <div class="report-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <h3 class="report-title">Пожаловаться на {{ targetName }}</h3>
            <p class="report-description">
              Если вы считаете, что этот контент нарушает правила или содержит ошибку, пожалуйста, сообщите нам.
            </p>
          </div>

          <div class="form-group">
            <label class="form-label required">Причина жалобы</label>
            <div class="reasons-list">
              <label
                v-for="reason in reportReasons"
                :key="reason.value"
                :class="['reason-option', { active: formData.reason === reason.value }]"
              >
                <input
                  v-model="formData.reason"
                  type="radio"
                  :value="reason.value"
                  class="reason-radio"
                />
                <span class="reason-icon">{{ reason.icon }}</span>
                <span class="reason-label">{{ reason.label }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Дополнительная информация</label>
            <textarea
              v-model="formData.message"
              placeholder="Опишите проблему подробнее..."
              class="form-textarea"
              rows="4"
              maxlength="1000"
            ></textarea>
            <div class="form-hint">{{ formData.message.length }}/1000</div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            Отмена
          </button>
          <button
            @click="handleSubmit"
            :disabled="!canSubmit || isSubmitting"
            class="btn btn-danger"
            type="button"
          >
            <svg v-if="!isSubmitting" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ isSubmitting ? 'Отправка...' : 'Отправить жалобу' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  show: boolean
  targetId?: number
  targetType?: 'anime' | 'dub' | 'comment'
  targetName?: string
}

const props = withDefaults(defineProps<Props>(), {
  targetId: undefined,
  targetType: 'anime',
  targetName: 'контент'
})

const emit = defineEmits<{
  close: []
  submit: [data: ReportData]
}>()

interface ReportData {
  targetId: number
  targetType: string
  reason: string
  message?: string
}

const formData = ref({
  reason: '',
  message: ''
})

const isSubmitting = ref(false)

const reportReasons = [
  { value: 'inappropriate', label: 'Неприемлемый контент', icon: '🚫' },
  { value: 'spam', label: 'Спам', icon: '📧' },
  { value: 'copyright', label: 'Нарушение авторских прав', icon: '©️' },
  { value: 'incorrect', label: 'Неверная информация', icon: '❌' },
  { value: 'quality', label: 'Низкое качество', icon: '📉' },
  { value: 'other', label: 'Другое', icon: '📝' }
]

const canSubmit = computed(() => {
  return formData.value.reason.trim().length > 0
})

const handleSubmit = () => {
  if (!canSubmit.value || !props.targetId) return

  const data: ReportData = {
    targetId: props.targetId,
    targetType: props.targetType,
    reason: formData.value.reason,
    message: formData.value.message.trim() || undefined
  }

  emit('submit', data)
  resetForm()
}

const handleClose = () => {
  emit('close')
}

const resetForm = () => {
  formData.value = {
    reason: '',
    message: ''
  }
  isSubmitting.value = false
}

watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})
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
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.report-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1rem;
  background-color: rgba(239, 68, 68, 0.05);
  border-radius: 0.75rem;
}

.report-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: 50%;
  color: #ef4444;
  margin-bottom: 1rem;
}

.report-icon svg {
  width: 32px;
  height: 32px;
}

.report-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
}

.report-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.form-label.required::after {
  content: ' *';
  color: #ef4444;
}

.reasons-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.5rem;
}

.reason-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.reason-option:hover {
  border-color: var(--color-accent);
}

.reason-option.active {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.reason-radio {
  display: none;
}

.reason-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.reason-label {
  font-size: 0.875rem;
  font-weight: 500;
}

.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
  resize: vertical;
}

.form-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-align: right;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
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

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
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
  background-color: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
  border-color: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
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
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .reasons-list {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
