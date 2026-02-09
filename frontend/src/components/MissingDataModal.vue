<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div class="modal-body">
        <div class="warning-icon">⚠️</div>
        <p class="warning-message">{{ message }}</p>

        <div class="missing-fields">
          <div v-for="field in missingFields" :key="field.key" class="field-item">
            <label :for="field.key" class="field-label">{{ field.label }}</label>
            <input
              :id="field.key"
              v-model="formData[field.key]"
              :type="field.type || 'text'"
              :placeholder="field.placeholder"
              class="field-input"
              required
            >
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Отмена</button>
        <button @click="saveAndContinue" class="btn-primary" :disabled="!isFormValid">
          Сохранить и продолжить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface MissingField {
  key: string
  label: string
  type?: string
  placeholder: string
}

interface Props {
  isVisible: boolean
  title: string
  message: string
  missingFields: MissingField[]
  onClose: () => void
  onSave: (data: any) => Promise<boolean>
}

const props = defineProps<Props>()

const authStore = useAuthStore()
const formData = reactive<Record<string, string>>({})

// Инициализируем formData текущими значениями пользователя
const initFormData = () => {
  props.missingFields.forEach(field => {
    if (authStore.user) {
      formData[field.key] = (authStore.user as any)[field.key] || ''
    } else {
      formData[field.key] = ''
    }
  })
}

const isFormValid = computed(() => {
  return props.missingFields.every(field => {
    const value = formData[field.key]
    return value && value.trim().length > 0
  })
})

const closeModal = () => {
  props.onClose()
}

const saveAndContinue = async () => {
  if (!isFormValid.value) return

  try {
    const result = await props.onSave(formData)
    if (result) {
      closeModal()
    }
  } catch (error) {
    console.error('Error saving data:', error)
    alert('Ошибка сохранения данных')
  }
}

// Инициализируем данные при открытии модального окна
watch(() => props.isVisible, (visible) => {
  if (visible) {
    initFormData()
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: var(--shadow);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.375rem;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  text-align: center;
}

.warning-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.warning-message {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.missing-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-item {
  text-align: left;
}

.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.field-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.field-input:focus {
  outline: none;
  border-color: var(--accent-color);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: var(--bg-tertiary);
}

.btn-primary {
  padding: 0.5rem 1rem;
  border: 1px solid var(--accent-color);
  background: var(--accent-color);
  color: white;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-secondary, .btn-primary {
    width: 100%;
  }
}
</style>