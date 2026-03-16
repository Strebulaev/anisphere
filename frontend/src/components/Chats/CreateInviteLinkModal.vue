<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Создать ссылку-приглашение</h3>
        <button @click="$emit('close')" class="close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <form @submit.prevent="createInvite" class="modal-body">
        <!-- Название -->
        <div class="form-group">
          <label>Название ссылки (необязательно)</label>
          <input
            v-model="form.name"
            type="text"
            class="input"
            placeholder="Например: Для друзей"
          />
          <p class="help-text">Поможет вам запомнить, для кого эта ссылка</p>
        </div>

        <!-- Срок действия -->
        <div class="form-group">
          <label>Срок действия</label>
          <div class="duration-options">
            <button
              v-for="option in expiryOptions"
              :key="option.value"
              type="button"
              @click="selectExpiry(option)"
              class="duration-btn"
              :class="{ active: selectedExpiry === option.value }"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <!-- Кастомная дата -->
        <div v-if="selectedExpiry === 'custom'" class="form-group">
          <label>Действует до</label>
          <input
            v-model="form.expires_at"
            type="datetime-local"
            class="input"
            :min="minDateTime"
          />
        </div>

        <!-- Лимит использований -->
        <div class="form-group">
          <label>Лимит использований</label>
          <div class="limit-options">
            <button
              v-for="option in limitOptions"
              :key="option.value"
              type="button"
              @click="selectLimit(option)"
              class="limit-btn"
              :class="{ active: selectedLimit === option.value }"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <!-- Кастомный лимит -->
        <div v-if="selectedLimit === 'custom'" class="form-group">
          <label>Количество использований</label>
          <input
            v-model.number="form.usage_limit"
            type="number"
            min="1"
            max="1000"
            class="input"
            placeholder="Введите число"
          />
        </div>

        <!-- Авто-назначение роли -->
        <div v-if="availableRoles.length > 0" class="form-group">
          <label>Автоматически назначить роль</label>
          <select v-model="form.auto_assign_role" class="input">
            <option :value="null">Без роли</option>
            <option
              v-for="role in availableRoles"
              :key="role.id"
              :value="role.id"
            >
              {{ role.name }}
            </option>
          </select>
          <p class="help-text">Роль будет автоматически назначена при вступлении</p>
        </div>

        <!-- Предпросмотр -->
        <div class="preview-box">
          <div class="preview-item">
            <span class="preview-label">Срок действия:</span>
            <span class="preview-value">{{ getExpiryText() }}</span>
          </div>
          <div class="preview-item">
            <span class="preview-label">Использований:</span>
            <span class="preview-value">{{ getLimitText() }}</span>
          </div>
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" @click="$emit('close')" class="btn btn-secondary">
          Отмена
        </button>
        <button
          @click="createInvite"
          class="btn btn-primary"
          :disabled="creating"
        >
          {{ creating ? 'Создание...' : 'Создать ссылку' }}
        </button>
      </div>

      <!-- Success modal -->
      <div v-if="createdLink" class="success-overlay" @click.self="createdLink = null">
        <div class="success-content">
          <CheckCircleIcon class="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 class="text-lg font-semibold mb-2">Ссылка создана!</h3>
          
          <div class="link-box">
            <input
              ref="linkInput"
              type="text"
              :value="createdLink.invite_link"
              readonly
              class="link-input"
            />
            <button @click="copyLink" class="copy-btn">
              <ClipboardDocumentIcon class="w-5 h-5" />
            </button>
          </div>

          <div class="link-info">
            <p>Скопируйте и отправьте ссылку тем, кого хотите пригласить</p>
          </div>

          <button @click="createdLink = null" class="btn btn-primary w-full mt-4">
            Готово
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  XMarkIcon,
  CheckCircleIcon,
  ClipboardDocumentIcon
} from '@heroicons/vue/24/outline'
import chatsApi from '@/api/chats'
import { useGroupChatStore } from '@/stores/groupChat'

interface Props {
  chatId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'created'])

const groupChatStore = useGroupChatStore()

// State
const creating = ref(false)
const createdLink = ref<any>(null)
const selectedExpiry = ref('never')
const selectedLimit = ref('unlimited')
const linkInput = ref<HTMLInputElement | null>(null)
const availableRoles = ref<any[]>([])

const form = ref({
  name: '',
  expires_at: '',
  usage_limit: null as number | null,
  auto_assign_role: null as number | null
})

// Computed
const minDateTime = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() + 5)
  return now.toISOString().slice(0, 16)
})

// Options
const expiryOptions = [
  { value: 'never', label: 'Никогда', hours: null },
  { value: '1h', label: '1 час', hours: 1 },
  { value: '24h', label: '1 день', hours: 24 },
  { value: '7d', label: '1 неделя', hours: 168 },
  { value: 'custom', label: 'Свой срок', hours: null }
]

const limitOptions = [
  { value: 'unlimited', label: 'Без лимита', limit: null },
  { value: '1', label: '1 раз', limit: 1 },
  { value: '5', label: '5 раз', limit: 5 },
  { value: '10', label: '10 раз', limit: 10 },
  { value: 'custom', label: 'Свой лимит', limit: null }
]

// Methods
const selectExpiry = (option: any) => {
  selectedExpiry.value = option.value
  
  if (option.value === 'never') {
    form.value.expires_at = ''
  } else if (option.value !== 'custom' && option.hours) {
    const date = new Date()
    date.setHours(date.getHours() + option.hours)
    form.value.expires_at = date.toISOString()
  }
}

const selectLimit = (option: any) => {
  selectedLimit.value = option.value
  
  if (option.value === 'unlimited') {
    form.value.usage_limit = null
  } else if (option.value !== 'custom') {
    form.value.usage_limit = option.limit
  }
}

const getExpiryText = () => {
  if (!form.value.expires_at) return 'Бессрочно'
  const date = new Date(form.value.expires_at)
  return date.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getLimitText = () => {
  if (!form.value.usage_limit) return 'Без ограничений'
  return `${form.value.usage_limit} раз(а)`
}

const createInvite = async () => {
  if (creating.value) return

  creating.value = true
  try {
    const response = await chatsApi.inviteLinks.create({
      chat: props.chatId,
      name: form.value.name || undefined,
      expires_at: form.value.expires_at || undefined,
      usage_limit: form.value.usage_limit || undefined,
      auto_assign_role: form.value.auto_assign_role || undefined
    })

    createdLink.value = response.data
    emit('created', response.data)
  } catch (error) {
    console.error('Error creating invite link:', error)
  } finally {
    creating.value = false
  }
}

const copyLink = async () => {
  if (createdLink.value?.invite_link) {
    await navigator.clipboard.writeText(createdLink.value.invite_link)
    // Show toast
  }
}

// Load roles
onMounted(async () => {
  await groupChatStore.loadChatRoles(props.chatId)
  availableRoles.value = groupChatStore.chatRoles
})
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50;
}

.modal-content {
  @apply bg-gray-800 rounded-xl w-full max-w-md mx-4 overflow-hidden relative;
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

.input {
  @apply w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.help-text {
  @apply text-xs text-gray-400;
}

.duration-options, .limit-options {
  @apply grid grid-cols-3 gap-2;
}

.duration-btn, .limit-btn {
  @apply px-3 py-2 text-sm bg-gray-700 border border-gray-600 rounded-lg text-gray-300 transition-colors;
  @apply hover:bg-gray-600;
}

.duration-btn.active, .limit-btn.active {
  @apply bg-blue-600 border-blue-600 text-white;
}

.preview-box {
  @apply p-3 bg-gray-700/50 rounded-lg space-y-2;
}

.preview-item {
  @apply flex justify-between text-sm;
}

.preview-label {
  @apply text-gray-400;
}

.preview-value {
  @apply text-white font-medium;
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

/* Success overlay */
.success-overlay {
  @apply absolute inset-0 bg-black/80 flex items-center justify-center;
}

.success-content {
  @apply bg-gray-800 rounded-xl p-6 max-w-sm mx-4 text-center;
}

.link-box {
  @apply flex gap-2 mt-4;
}

.link-input {
  @apply flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm;
}

.copy-btn {
  @apply p-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors;
}

.link-info {
  @apply mt-3 text-sm text-gray-400;
}
</style>
