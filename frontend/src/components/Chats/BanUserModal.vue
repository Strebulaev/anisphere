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
  @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50;
}

.modal-content {
  @apply bg-gray-800 rounded-xl w-full max-w-md mx-4 overflow-hidden;
}

.modal-header {
  @apply flex items-center justify-between p-4 border-b border-gray-700;
}

.modal-header h3 {
  @apply text-lg font-semibold text-white;
}

.close-btn {
  @apply p-1 rounded hover:bg-gray-700 transition-colors text-gray-400;
}

.modal-body {
  @apply p-4 space-y-4;
}

.user-info {
  @apply flex items-center gap-4 p-4 bg-gray-700/50 rounded-lg;
}

.avatar {
  @apply w-12 h-12 rounded-full;
}

.username {
  @apply font-medium text-white;
}

.user-status {
  @apply text-sm text-gray-400;
}

.form {
  @apply space-y-4;
}

.form-group {
  @apply space-y-2;
}

.form-group label {
  @apply block text-sm font-medium text-gray-300;
}

.input {
  @apply w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.textarea {
  @apply resize-none;
}

.duration-options {
  @apply grid grid-cols-3 gap-2;
}

.duration-btn {
  @apply px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-lg text-gray-300 transition-colors;
  @apply hover:bg-gray-600;
}

.duration-btn.active {
  @apply bg-red-600 border-red-600 text-white;
}

.checkbox-label {
  @apply flex items-center gap-3 cursor-pointer;
}

.checkbox-label input[type="checkbox"] {
  @apply w-5 h-5 rounded;
}

.help-text {
  @apply text-xs text-gray-400;
}

.warning-box {
  @apply flex gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg;
}

.warning-title {
  @apply text-sm font-medium text-yellow-500;
}

.warning-text {
  @apply text-xs text-gray-400;
}

.modal-footer {
  @apply flex justify-end gap-3 p-4 border-t border-gray-700;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-secondary {
  @apply bg-gray-700 text-white hover:bg-gray-600;
}

.btn-danger {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.btn-danger:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
