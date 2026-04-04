<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Заблокировать пользователя</h3>
        <button @click="$emit('close')" class="close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <div class="modal-body">
        <!-- User info -->
        <div class="user-info">
          <img
            :src="member.user.avatar || '/default-avatar.png'"
            class="avatar"
          />
          <div>
            <div class="username">{{ member.user.username }}</div>
            <div class="user-status">
              {{ member.role?.name || 'Участник' }}
            </div>
          </div>
        </div>

        <form @submit.prevent="banUser" class="form">
          <!-- Причина -->
          <div class="form-group">
            <label>Причина блокировки</label>
            <textarea
              v-model="form.reason"
              rows="3"
              class="input textarea"
              placeholder="Укажите причину блокировки..."
              required
            ></textarea>
          </div>

          <!-- Срок блокировки -->
          <div class="form-group">
            <label>Срок блокировки</label>
            <div class="duration-options">
              <button
                v-for="option in durationOptions"
                :key="option.value"
                type="button"
                @click="selectDuration(option)"
                class="duration-btn"
                :class="{ active: selectedDuration === option.value }"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <!-- Кастомная дата -->
          <div v-if="selectedDuration === 'custom'" class="form-group">
            <label>До какой даты</label>
            <input
              v-model="form.until_date"
              type="datetime-local"
              class="input"
              :min="minDateTime"
            />
          </div>

          <!-- Удаление сообщений -->
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="form.delete_messages" type="checkbox" />
              <span>Удалить все сообщения пользователя</span>
            </label>
            <p class="help-text">Все сообщения этого пользователя будут удалены из чата</p>
          </div>

          <!-- Предупреждение -->
          <div class="warning-box">
            <ExclamationTriangleIcon class="w-5 h-5 text-yellow-500" />
            <div>
              <div class="warning-title">Внимание</div>
              <div class="warning-text">
                Пользователь будет удалён из чата и не сможет вернуться до окончания срока блокировки.
                {{ form.delete_messages ? 'Все его сообщения будут удалены.' : '' }}
              </div>
            </div>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <button type="button" @click="$emit('close')" class="btn btn-secondary">
          Отмена
        </button>
        <button
          @click="banUser"
          class="btn btn-danger"
          :disabled="!form.reason || banning"
        >
          {{ banning ? 'Блокировка...' : 'Заблокировать' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import chatsApi from '@/api/chats'

interface Props {
  member: {
    id: number
    user: {
      id: number
      username: string
      avatar?: string
    }
    role?: {
      id: number
      name: string
    } | null
    chat: {
      id: number
    }
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'banned'])

// State
const banning = ref(false)
const selectedDuration = ref('forever')

const form = ref({
  reason: '',
  until_date: '',
  delete_messages: false
})

// Computed
const minDateTime = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() + 5)
  return now.toISOString().slice(0, 16)
})

// Options
const durationOptions = [
  { value: '1h', label: '1 час', hours: 1 },
  { value: '24h', label: '1 день', hours: 24 },
  { value: '7d', label: '1 неделя', hours: 168 },
  { value: '30d', label: '1 месяц', hours: 720 },
  { value: 'forever', label: 'Навсегда', hours: null },
  { value: 'custom', label: 'Свой срок', hours: null }
]

// Methods
const selectDuration = (option: any) => {
  selectedDuration.value = option.value
  
  if (option.value === 'forever') {
    form.value.until_date = ''
  } else if (option.value !== 'custom') {
    const date = new Date()
    date.setHours(date.getHours() + option.hours)
    form.value.until_date = date.toISOString()
  }
}

const banUser = async () => {
  if (!form.value.reason || banning.value) return

  banning.value = true
  try {
    await chatsApi.bans.create({
      chat: props.member.chat.id,
      user: props.member.user.id,
      reason: form.value.reason,
      until_date: form.value.until_date || undefined,
      delete_messages: form.value.delete_messages
    })

    emit('banned', props.member.user.id)
    emit('close')
  } catch (error) {
    console.error('Error banning user:', error)
  } finally {
    banning.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5,4,8,0.88);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 28rem;
  margin: 0 1rem;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  padding: 0.25rem;
  border-radius: var(--radius-md);
  transition: all 0.2s var(--ease-petal);
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
}

.close-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.modal-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface-4);
  border-radius: var(--radius-lg);
}

.avatar {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent-subtle);
}

.username {
  font-weight: 500;
  color: var(--text-primary);
}

.user-status {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  transition: all 0.2s var(--ease-petal);
}

.input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.textarea {
  resize: none;
}

.duration-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.duration-btn {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  transition: all 0.2s var(--ease-petal);
  cursor: pointer;
}

.duration-btn:hover {
  background: var(--surface-5);
}

.duration-btn.active {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: var(--radius-sm);
  accent-color: var(--accent);
}

.help-text {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.warning-box {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--warning-subtle);
  border: 1px solid var(--warning);
  border-radius: var(--radius-lg);
}

.warning-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--warning);
}

.warning-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  font-weight: 500;
  transition: all 0.2s var(--ease-petal);
  cursor: pointer;
}

.btn-secondary {
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.btn-secondary:hover {
  background: var(--surface-5);
}

.btn-danger {
  background: var(--danger);
  color: white;
  border: none;
}

.btn-danger:hover {
  background: var(--danger-press);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
