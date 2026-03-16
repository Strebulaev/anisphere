<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Запланировать сообщение</h3>
        <button @click="$emit('close')" class="close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <form @submit.prevent="scheduleMessage" class="modal-body">
        <!-- Текст сообщения -->
        <div class="form-group">
          <label>Сообщение</label>
          <textarea
            v-model="form.text"
            rows="4"
            class="input textarea"
            placeholder="Введите текст сообщения..."
          ></textarea>
        </div>

        <!-- Медиафайл -->
        <div class="form-group">
          <label>Медиафайл (необязательно)</label>
          <div class="media-upload">
            <input
              ref="fileInput"
              type="file"
              @change="handleFileSelect"
              accept="image/*,video/*,audio/*"
              hidden
            />
            <button type="button" @click="fileInput?.click()" class="upload-btn">
              <PhotoIcon class="w-5 h-5" />
              <span>{{ selectedFile ? selectedFile.name : 'Выбрать файл' }}</span>
            </button>
            <button
              v-if="selectedFile"
              type="button"
              @click="clearFile"
              class="clear-btn"
            >
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>
          <div v-if="mediaPreview" class="preview">
            <img v-if="isImage" :src="mediaPreview" alt="Preview" />
            <video v-else-if="isVideo" :src="mediaPreview" controls />
            <audio v-else-if="isAudio" :src="mediaPreview" controls />
          </div>
        </div>

        <!-- Дата и время -->
        <div class="form-row">
          <div class="form-group">
            <label>Дата</label>
            <input
              v-model="form.date"
              type="date"
              class="input"
              :min="minDate"
            />
          </div>
          <div class="form-group">
            <label>Время</label>
            <input
              v-model="form.time"
              type="time"
              class="input"
            />
          </div>
        </div>

        <!-- Повторение -->
        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="form.is_recurring" type="checkbox" />
            <span>Повторяющееся сообщение</span>
          </label>
        </div>

        <div v-if="form.is_recurring" class="form-group">
          <label>Повторять каждые</label>
          <select v-model="form.recurring_interval" class="input">
            <option :value="1">День</option>
            <option :value="7">Неделю</option>
            <option :value="14">2 недели</option>
            <option :value="30">Месяц</option>
          </select>
        </div>

        <!-- Предпросмотр -->
        <div class="preview-info">
          <CalendarIcon class="w-5 h-5 text-blue-500" />
          <div>
            <div class="preview-label">Будет отправлено</div>
            <div class="preview-value">{{ formatDateTime() }}</div>
          </div>
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" @click="$emit('close')" class="btn btn-secondary">
          Отмена
        </button>
        <button
          @click="scheduleMessage"
          class="btn btn-primary"
          :disabled="!canSubmit || saving"
        >
          {{ saving ? 'Планирование...' : 'Запланировать' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  XMarkIcon,
  PhotoIcon,
  CalendarIcon
} from '@heroicons/vue/24/outline'
import chatsApi from '@/api/chats'

interface Props {
  chatId: number
  chatType?: 'group' | 'private'
}

const props = withDefaults(defineProps<Props>(), {
  chatType: 'group'
})

const emit = defineEmits(['close', 'scheduled'])

// State
const saving = ref(false)
const selectedFile = ref<File | null>(null)
const mediaPreview = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const form = ref({
  text: '',
  date: '',
  time: '',
  is_recurring: false,
  recurring_interval: 1
})

// Computed
const minDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

const canSubmit = computed(() => {
  return (
    (form.value.text.trim() || selectedFile.value) &&
    form.value.date &&
    form.value.time
  )
})

const isImage = computed(() => {
  return selectedFile.value?.type.startsWith('image/')
})

const isVideo = computed(() => {
  return selectedFile.value?.type.startsWith('video/')
})

const isAudio = computed(() => {
  return selectedFile.value?.type.startsWith('audio/')
})

// Methods
const handleFileSelect = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    selectedFile.value = file
    
    const reader = new FileReader()
    reader.onload = (e) => {
      mediaPreview.value = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const clearFile = () => {
  selectedFile.value = null
  mediaPreview.value = null
}

const formatDateTime = () => {
  if (!form.value.date || !form.value.time) return 'Выберите дату и время'
  
  const date = new Date(`${form.value.date}T${form.value.time}`)
  return date.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scheduleMessage = async () => {
  if (!canSubmit.value || saving.value) return

  saving.value = true
  try {
    const scheduledAt = new Date(`${form.value.date}T${form.value.time}`).toISOString()
    
    const data: any = {
      text: form.value.text,
      scheduled_at: scheduledAt,
      is_recurring: form.value.is_recurring,
      recurring_interval: form.value.is_recurring ? form.value.recurring_interval : undefined
    }

    if (props.chatType === 'group') {
      data.chat = props.chatId
    } else {
      data.private_chat = props.chatId
    }

    if (selectedFile.value) {
      data.media = selectedFile.value
      if (selectedFile.value.type.startsWith('image/')) {
        data.media_type = 'image'
      } else if (selectedFile.value.type.startsWith('video/')) {
        data.media_type = 'video'
      } else if (selectedFile.value.type.startsWith('audio/')) {
        data.media_type = 'audio'
      }
    }

    const response = await chatsApi.scheduledMessages.create(data)
    emit('scheduled', response.data)
    emit('close')
  } catch (error) {
    console.error('Error scheduling message:', error)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50;
}

.modal-content {
  @apply bg-gray-800 rounded-xl w-full max-w-lg mx-4 overflow-hidden;
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

.form-group {
  @apply space-y-2;
}

.form-group label {
  @apply block text-sm font-medium text-gray-300;
}

.form-row {
  @apply grid grid-cols-2 gap-4;
}

.input {
  @apply w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.textarea {
  @apply resize-none;
}

.media-upload {
  @apply flex items-center gap-2;
}

.upload-btn {
  @apply flex-1 flex items-center justify-center gap-2 py-3 border-2 border-dashed border-gray-600 rounded-lg text-gray-300 transition-colors;
  @apply hover:border-blue-500 hover:text-blue-500;
}

.clear-btn {
  @apply p-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors;
}

.preview {
  @apply mt-2 rounded-lg overflow-hidden;
}

.preview img {
  @apply w-full max-h-48 object-contain;
}

.preview video, .preview audio {
  @apply w-full;
}

.checkbox-label {
  @apply flex items-center gap-3 cursor-pointer;
}

.checkbox-label input[type="checkbox"] {
  @apply w-5 h-5 rounded;
}

.preview-info {
  @apply flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg;
}

.preview-label {
  @apply text-xs text-gray-400;
}

.preview-value {
  @apply text-sm font-medium text-white;
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

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-primary:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
