<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Ограничить пользователя</h3>
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

        <form @submit.prevent="restrictUser" class="form">
          <!-- Тип ограничения -->
          <div class="form-group">
            <label>Тип ограничения</label>
            <div class="restriction-types">
              <button
                v-for="type in restrictionTypes"
                :key="type.value"
                type="button"
                @click="form.restriction_type = type.value"
                class="type-btn"
                :class="{ active: form.restriction_type === type.value }"
              >
                <component :is="type.icon" class="w-5 h-5" />
                <span>{{ type.label }}</span>
              </button>
            </div>
            <p class="help-text">{{ getTypeDescription(form.restriction_type) }}</p>
          </div>

          <!-- Причина -->
          <div class="form-group">
            <label>Причина (необязательно)</label>
            <textarea
              v-model="form.reason"
              rows="2"
              class="input textarea"
              placeholder="Укажите причину ограничения..."
            ></textarea>
          </div>

          <!-- Срок -->
          <div class="form-group">
            <label>Срок ограничения</label>
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

          <!-- Дополнительные настройки для slow_mode -->
          <div v-if="form.restriction_type === 'slow_mode'" class="form-group">
            <label>Задержка между сообщениями</label>
            <select v-model="form.slow_mode_delay" class="input">
              <option :value="10">10 секунд</option>
              <option :value="30">30 секунд</option>
              <option :value="60">1 минута</option>
              <option :value="120">2 минуты</option>
              <option :value="300">5 минут</option>
              <option :value="600">10 минут</option>
            </select>
          </div>

          <!-- Инфо -->
          <div class="info-box">
            <InformationCircleIcon class="w-5 h-5 text-blue-500" />
            <div class="info-text">
              Ограничение можно снять в любой момент через панель администратора.
            </div>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <button type="button" @click="$emit('close')" class="btn btn-secondary">
          Отмена
        </button>
        <button
          @click="restrictUser"
          class="btn btn-warning"
          :disabled="restricting"
        >
          {{ restricting ? 'Применение...' : 'Ограничить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  XMarkIcon,
  EyeIcon,
  PhotoIcon,
  FaceSmileIcon,
  LinkIcon,
  MicrophoneIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'
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
const emit = defineEmits(['close', 'restricted'])

// State
const restricting = ref(false)
const selectedDuration = ref('1d')

const form = ref({
  restriction_type: 'read_only',
  reason: '',
  until_date: '',
  slow_mode_delay: 60
})

// Computed
const minDateTime = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() + 5)
  return now.toISOString().slice(0, 16)
})

// Options
const restrictionTypes = [
  { value: 'read_only', label: 'Только чтение', icon: EyeIcon },
  { value: 'no_media', label: 'Без медиа', icon: PhotoIcon },
  { value: 'no_stickers', label: 'Без стикеров', icon: FaceSmileIcon },
  { value: 'no_links', label: 'Без ссылок', icon: LinkIcon },
  { value: 'no_voice', label: 'Без голосовых', icon: MicrophoneIcon },
  { value: 'slow_mode', label: 'Медленный режим', icon: ClockIcon }
]

const durationOptions = [
  { value: '1h', label: '1 час', hours: 1 },
  { value: '1d', label: '1 день', hours: 24 },
  { value: '7d', label: '1 неделя', hours: 168 },
  { value: '30d', label: '1 месяц', hours: 720 },
  { value: 'custom', label: 'Свой срок', hours: null }
]

// Methods
const getTypeDescription = (type: string): string => {
  const descriptions: Record<string, string> = {
    read_only: 'Пользователь не сможет отправлять сообщения',
    no_media: 'Пользователь не сможет отправлять фото, видео и файлы',
    no_stickers: 'Пользователь не сможет отправлять стикеры и GIF',
    no_links: 'Пользователь не сможет отправлять ссылки',
    no_voice: 'Пользователь не сможет отправлять голосовые сообщения',
    slow_mode: 'Пользователь сможет отправлять сообщения с задержкой'
  }
  return descriptions[type] || ''
}

const selectDuration = (option: any) => {
  selectedDuration.value = option.value
  
  if (option.value !== 'custom' && option.hours) {
    const date = new Date()
    date.setHours(date.getHours() + option.hours)
    form.value.until_date = date.toISOString()
  }
}

const restrictUser = async () => {
  if (restricting.value) return

  restricting.value = true
  try {
    await chatsApi.restrictions.create({
      chat: props.member.chat.id,
      user: props.member.user.id,
      restriction_type: form.value.restriction_type,
      reason: form.value.reason || undefined,
      until_date: form.value.until_date || undefined,
      slow_mode_delay: form.value.restriction_type === 'slow_mode' 
        ? form.value.slow_mode_delay 
        : undefined
    })

    emit('restricted', props.member.user.id)
    emit('close')
  } catch (error) {
    console.error('Error restricting user:', error)
  } finally {
    restricting.value = false
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
  @apply p-4 space-y-4 max-h-[60vh] overflow-y-auto;
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

.restriction-types {
  @apply grid grid-cols-2 gap-2;
}

.type-btn {
  @apply flex items-center gap-2 px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-lg text-gray-300 transition-colors;
  @apply hover:bg-gray-600;
}

.type-btn.active {
  @apply bg-orange-600 border-orange-600 text-white;
}

.help-text {
  @apply text-xs text-gray-400;
}

.duration-options {
  @apply grid grid-cols-3 gap-2;
}

.duration-btn {
  @apply px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-lg text-gray-300 transition-colors;
  @apply hover:bg-gray-600;
}

.duration-btn.active {
  @apply bg-orange-600 border-orange-600 text-white;
}

.info-box {
  @apply flex gap-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg;
}

.info-text {
  @apply text-sm text-gray-300;
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

.btn-warning {
  @apply bg-orange-600 text-white hover:bg-orange-700;
}

.btn-warning:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
