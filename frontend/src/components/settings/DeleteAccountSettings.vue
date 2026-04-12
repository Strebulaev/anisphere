<template>
  <div class="settings-section">
    <h2>Удаление аккаунта</h2>

    <!-- Упрощённая версия - только кнопка удаления с подтверждением -->
    <div class="settings-group danger-zone">
      <div class="warning-icon"><SakuraIcon name="warning" />️</div>
      <h3>ВНИМАНИЕ!</h3>
      <p class="warning-text">
        Вы собираетесь удалить аккаунт. Это действие <strong>НЕОБРАТИМО</strong>.
        Все ваши данные будут безвозвратно удалены.
      </p>

      <div class="important-note">
        <strong><SakuraIcon name="warning" />️ Важно:</strong>
        <ul>
          <li>Имя пользователя освобождается для других</li>
          <li>Есть 7 дней на восстановление после удаления</li>
        </ul>
      </div>

      <div class="final-check">
        <label class="checkbox-label">
          <input type="checkbox" v-model="finalConfirmation" />
          <span>Я подтверждаю, что хочу удалить свой аккаунт и понимаю последствия</span>
        </label>
      </div>

      <div class="action-buttons">
        <button
          @click="confirmDeletion"
          :disabled="!finalConfirmation || isDeleting"
          class="danger-btn"
        >
          <SakuraIcon v-if="!isDeleting" name="trash" :size="18" style="vertical-align: middle; margin-right: 8px;" />
          {{ isDeleting ? 'Удаление...' : 'Удалить аккаунт' }}
        </button>
      </div>

      <p v-if="deletionError" class="error-msg">{{ deletionError }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

const router = useRouter()
const authStore = useAuthStore()

const finalConfirmation = ref(false)
const isDeleting = ref(false)
const deletionError = ref('')

const confirmDeletion = async () => {
  if (!finalConfirmation.value) return
  
  if (!confirm('Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.')) {
    return
  }
  
  isDeleting.value = true
  deletionError.value = ''
  
  try {
    await apiClient.delete('/users/me/')
    authStore.logout()
    router.push('/')
    alert('Аккаунт удалён. Вы можете восстановить его в течение 7 дней, войдя в аккаунт.')
  } catch (error: any) {
    console.error('Error deleting account:', error)
    deletionError.value = error.response?.data?.detail || 'Ошибка при удалении аккаунта'
  } finally {
    isDeleting.value = false
  }
}
</script>

<style scoped>
.settings-section {
  padding: 22px 24px;
}

.settings-section h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.settings-group {
  padding: 24px;
  background: var(--surface-2);
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.danger-zone {
  border: 1px solid var(--danger-subtle);
  background: var(--danger-subtle);
}

.warning-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 20px;
  color: var(--warning);
}

.warning-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 20px;
  text-align: center;
}

.important-note {
  padding: 16px;
  background: var(--warning-subtle);
  border-left: 3px solid var(--warning);
  border-radius: 8px;
  margin-bottom: 25px;
}

.important-note strong {
  color: var(--warning);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.important-note ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.important-note li {
  margin-bottom: 6px;
  color: var(--text-primary);
  font-size: 14px;
}

.final-check {
  margin: 20px 0;
  padding: 16px;
  background: var(--surface-3);
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 2px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

.danger-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  background: var(--danger);
  color: white;
  border: none;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.danger-btn:hover:not(:disabled) {
  background: var(--danger-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--danger-subtle);
}

.danger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error-msg {
  color: var(--danger);
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
}
</style>
