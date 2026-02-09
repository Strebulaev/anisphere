<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ isGroup ? 'Настройки группы' : 'Настройки чата' }}</h3>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="modal-body">
          <!-- Аватарка чата -->
          <div class="settings-section">
            <label class="section-title">Аватарка чата</label>
            <div class="avatar-upload">
              <img
                v-if="avatarPreview || chat.avatar_url"
                :src="avatarPreview || chat.avatar_url || undefined"
                :alt="chat.name || 'Чат'"
                class="current-avatar"
              />
              <div v-else class="avatar-placeholder">
                {{ getInitials(chat.name || 'Чат') }}
              </div>

              <div class="avatar-actions">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleAvatarSelect"
                  class="avatar-input"
                />
                <button
                  v-if="avatarPreview || chat.avatar_url"
                  type="button"
                  class="btn-remove"
                  @click="removeAvatar"
                >
                  Удалить
                </button>
              </div>
            </div>
          </div>

          <!-- Название группы (только для групп) -->
          <div v-if="isGroup" class="settings-section">
            <label class="section-title">Название группы</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="Название группы"
              class="settings-input"
            />
          </div>

          <!-- Описание (только для групп) -->
          <div v-if="isGroup" class="settings-section">
            <label class="section-title">Описание</label>
            <textarea
              v-model="form.description"
              placeholder="Описание группы"
              class="settings-textarea"
              rows="3"
            />
          </div>

          <!-- Персональные настройки (только для личных чатов) -->
          <div v-if="!isGroup" class="settings-section">
            <label class="section-title">Ваше название чата</label>
            <input
              v-model="form.custom_name"
              type="text"
              placeholder="Как вы называете этот чат"
              class="settings-input"
            />
          </div>

          <!-- Кнопки -->
          <div class="modal-actions">
            <button class="btn-cancel" @click="close">Отмена</button>
            <button class="btn-save" @click="saveSettings" :disabled="loading">
              {{ loading ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import apiClient from '@/api/client'
import { useAvatar } from '@/composables/useAvatar'

const { getAvatarUrl } = useAvatar()

interface Props {
  isOpen: boolean
  chatId: number
  isGroup: boolean
}

interface ChatData {
  id: number
  name: string | null
  avatar_url: string | null
  description: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const loading = ref(false)
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
  custom_name: '',
  avatar: null as File | null
})

const chat = reactive<ChatData>({
  id: 0,
  name: null,
  avatar_url: null,
  description: ''
})

// Загружаем данные чата
const loadChatData = async () => {
  try {
    const endpoint = props.isGroup
      ? `/social/group-chats/${props.chatId}/`
      : `/social/private-chats/${props.chatId}/`

    const response = await apiClient.get(endpoint)
    const data = response.data

    chat.id = data.id
    chat.description = data.description || ''

    if (!props.isGroup) {
      // Для личного чата - загружаем персональные настройки
      try {
        const settingsResponse = await apiClient.get(`/social/private-chats/${props.chatId}/settings/`)
        const settings = settingsResponse.data

        // Кастомные настройки пользователя (только для него)
        chat.name = settings.custom_name || null
        chat.avatar_url = settings.custom_avatar_url || (data.other_user?.avatar ? getAvatarUrl(data.other_user.avatar) : null)

        form.custom_name = settings.custom_name || ''
      } catch {
        // Если настроек нет - используем дефолтные значения
        chat.name = null
        chat.avatar_url = data.other_user?.avatar ? getAvatarUrl(data.other_user.avatar) : null
        form.custom_name = ''
      }
    } else {
      // Для группового чата - общие настройки
      chat.name = data.name
      chat.avatar_url = data.avatar_url || data.avatar
      form.name = data.name || ''
      form.description = data.description || ''
    }
  } catch (error) {
    console.error('Ошибка загрузки настроек чата:', error)
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    loadChatData()
  }
})

const handleAvatarSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    avatarFile.value = file
    avatarPreview.value = URL.createObjectURL(file)
    form.avatar = file
  }
}

const removeAvatar = () => {
  avatarFile.value = null
  avatarPreview.value = null
  form.avatar = null
}

const getInitials = (name: string): string => {
  if (!name) return '?'

  const words = name.split(' ').filter(w => w.length > 2)
  if (words.length === 0) return name.substring(0, 2).toUpperCase()

  return words.slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

const saveSettings = async () => {
  loading.value = true

  const chatId = props.chatId
  if (!chatId) {
    console.error('Ошибка: ID чата не определён')
    loading.value = false
    return
  }

  try {
    if (props.isGroup) {
      const formData = new FormData()
      formData.append('name', form.name)
      formData.append('description', form.description)
      if (form.avatar) {
        formData.append('avatar', form.avatar)
      }

      await apiClient.put(`/social/group-chats/${chatId}/settings/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      // Настройки личного чата - персональные
      const formData = new FormData()
      formData.append('custom_name', form.custom_name)
      if (form.avatar) {
        formData.append('custom_avatar', form.avatar)
      }

      await apiClient.put(`/social/private-chats/${chatId}/settings/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }

    emit('updated')
    close()
  } catch (error) {
    console.error('Ошибка сохранения настроек:', error)
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
  avatarFile.value = null
  avatarPreview.value = null
}
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
  z-index: 9999;
}

.modal-content {
  background: var(--color-background-surface);
  border-radius: 12px;
  width: 90%;
  max-width: 450px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background: var(--color-background-active);
}

.modal-body {
  padding: 1.5rem;
}

.settings-section {
  margin-bottom: 1.5rem;
}

.section-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.current-avatar,
.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-divider);
}

.avatar-placeholder {
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 600;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.avatar-input {
  font-size: 0.875rem;
}

.btn-remove {
  padding: 0.5rem 1rem;
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-remove:hover {
  background: rgba(220, 38, 38, 0.2);
}

.settings-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.settings-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.settings-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--color-background);
  color: var(--color-text);
  resize: vertical;
  transition: border-color 0.2s;
}

.settings-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider);
  margin-top: 1.5rem;
}

.btn-cancel {
  padding: 0.625rem 1.25rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: var(--color-background-active);
}

.btn-save {
  padding: 0.625rem 1.25rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-save:hover {
  background: var(--color-accent-hover);
}

.btn-save:disabled {
  background: var(--color-text-disabled);
  cursor: not-allowed;
}
</style>