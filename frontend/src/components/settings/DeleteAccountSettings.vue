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
          {{ isDeleting ? 'Удаление...' : '<SakuraIcon name="trash" /> Удалить аккаунт' }}
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
  padding: 20px;
}

.settings-section h2 {
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
}

.settings-group {
  padding: 30px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.danger-zone {
  border: 2px solid #f44336;
  background: rgba(244, 67, 54, 0.05);
}

.warning-icon {
  font-size: 60px;
  text-align: center;
  margin-bottom: 20px;
}

.warning-text {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-color);
  margin-bottom: 20px;
}

.important-note {
  padding: 15px;
  background: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #FFC107;
  border-radius: 4px;
  margin-bottom: 25px;
}

.important-note strong {
  color: #FFC107;
}

.important-note ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.important-note li {
  margin-bottom: 5px;
  color: var(--text-color);
}

.final-check {
  margin: 20px 0;
  padding: 15px;
  background: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 3px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.danger-btn {
  padding: 14px 28px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  background: #f44336;
  color: white;
  border: none;
  transition: all 0.2s;
}

.danger-btn:hover:not(:disabled) {
  background: #d32f2f;
  transform: translateY(-1px);
}

.danger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  color: #f44336;
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
}
</style>
