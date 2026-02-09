<template>
  <div class="chats">
    <div class="container">
      <h1 class="page-title">Чаты</h1>

      <!-- Create Chat Button -->
      <div class="create-chat-card">
        <button @click="showCreateChat = true" class="btn-create-chat">
          <span class="icon">💬</span>
          Создать чат
        </button>
      </div>

      <!-- Chats List -->
      <div class="chats-list">
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else-if="chats.length === 0" class="empty-state">
          <p>Пока нет чатов. Начните общение!</p>
        </div>
        <div v-else>
          <div v-for="chat in chats" :key="chat.id" class="chat-item" @click="openChat(chat)">
            <img :src="getChatAvatar(chat)" :alt="getChatName(chat)" class="chat-avatar">
            <div class="chat-info">
              <div class="chat-name">{{ getChatName(chat) }}</div>
              <div class="last-message" v-if="chat.last_message_text">
                {{ chat.last_message_sender }}: {{ chat.last_message_text }}
              </div>
              <div class="chat-meta">
                {{ formatDate(chat.updated_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Chat Modal -->
      <div v-if="showCreateChat" class="modal-overlay" @click="showCreateChat = false">
        <div class="modal-content" @click.stop>
          <h3>Создать чат</h3>
          <form @submit.prevent="createChat">
            <div class="form-group">
              <label>Тип чата:</label>
              <select v-model="newChat.type" required>
                <option value="direct">Личный чат</option>
                <option value="group">Групповой чат</option>
              </select>
            </div>

            <div v-if="newChat.type === 'group'" class="form-group">
              <label>Название чата:</label>
              <input v-model="newChat.name" type="text" placeholder="Название чата" required>
            </div>

            <div v-if="newChat.type === 'group'" class="form-group">
              <label>Аватарка чата (опционально):</label>
              <div class="avatar-upload">
                <img v-if="avatarPreview" :src="avatarPreview" alt="Preview" class="avatar-preview">
                <input type="file" @change="handleAvatarSelect" accept="image/*" class="avatar-input">
              </div>
              <button v-if="avatarPreview" type="button" @click="clearAvatar" class="btn-clear-avatar">Очистить</button>
            </div>

            <div class="form-group">
              <label>{{ newChat.type === 'direct' ? 'Найти пользователя:' : 'Добавить участников:' }}</label>
              <input
                v-model="userSearch"
                type="text"
                :placeholder="newChat.type === 'direct' ? 'Введите имя пользователя' : 'Поиск пользователей'"
                @input="searchUsers"
              />
              <div v-if="userResults.length > 0" class="user-results">
                <div
                  v-for="user in userResults"
                  :key="user.id"
                  @click="selectUser(user)"
                  class="user-result-item"
                >
                  <img :src="getAvatarUrl(user.avatar)" :alt="user.username" class="user-avatar-small">
                  <div class="user-info">
                    <div class="user-name">{{ user.display_name || user.username }}</div>
                    <div class="user-username">@{{ user.username }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedUsers.length > 0" class="selected-users">
              <label>Выбранные {{ newChat.type === 'direct' ? 'пользователи' : 'участники' }}:</label>
              <div class="user-chips">
                <span
                  v-for="user in selectedUsers"
                  :key="user.id"
                  class="user-chip"
                >
                  {{ user.display_name || user.username }}
                  <button type="button" @click="removeUser(user)" class="remove-user">×</button>
                </span>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="showCreateChat = false">Отмена</button>
              <button type="submit" :disabled="!isFormValid">Создать</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { useAvatar } from '@/composables/useAvatar'

interface Chat {
  id: number
  type: string
  name?: string
  participants_usernames?: string[]
  avatar_url?: string
  avatar?: string
  other_user?: {
    id: number
    username: string
    display_name?: string
    avatar?: string
    is_online?: boolean
  }
  last_message_text?: string
  last_message_sender?: string
  updated_at: string
}

interface User {
  id: number
  username: string
  display_name?: string
  avatar?: string
}

const router = useRouter()
const { getAvatarUrl, getUserInitials } = useAvatar()

const chats = ref<Chat[]>([])
const loading = ref(true)
const showCreateChat = ref(false)
const newChat = ref({
  type: 'direct',
  name: '',
  participants: ''
})

// User search functionality
const userSearch = ref('')
const userResults = ref<User[]>([])
const selectedUsers = ref<User[]>([])
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)

const isFormValid = computed(() => {
  if (newChat.value.type === 'group' && !newChat.value.name.trim()) return false
  return selectedUsers.value.length > 0
})

const loadChats = async () => {
  try {
    console.log('Загружаем список чатов...')
    const response = await apiClient.get('/social/chats/')
    chats.value = response.data.results || response.data
    console.log('Загружено чатов:', chats.value.length)
    chats.value.forEach(chat => {
      console.log(`Чат ${chat.id}: ${chat.name} - участники: ${chat.participants_usernames?.join(', ')}`)
    })
  } catch (error) {
    console.error('Ошибка загрузки чатов:', error)
  } finally {
    loading.value = false
  }
}

const createChat = async () => {
  try {
    if (newChat.value.type === 'group') {
      // Create group chat
      const formData = new FormData()
      formData.append('name', newChat.value.name)
      formData.append('participants', JSON.stringify(selectedUsers.value.map((user: any) => user.id)))
      if (avatarFile.value) {
        formData.append('avatar', avatarFile.value)
      }
      await apiClient.post('/social/group-chats/create/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      // Create private chat - only one user should be selected
      if (!selectedUsers.value || selectedUsers.value.length !== 1) {
        throw new Error('Для личного чата нужно выбрать одного пользователя')
      }
      const selectedUser = selectedUsers.value[0]
      if (!selectedUser) {
        throw new Error('Выбранный пользователь не найден')
      }
      const data = {
        user_id: selectedUser.id
      }
      await apiClient.post('/social/private-chats/', data)
    }

    resetForm()
    showCreateChat.value = false
    loadChats()
  } catch (error) {
    console.error('Error creating chat:', error)
  }
}

const openChat = async (chat: Chat) => {
  try {
    // Проверяем доступ
    const response = await apiClient.get(`/social/chats/${chat.id}/`)
    
    // Используем правильный путь
    // Вариант 1: Если у вас есть маршрут /chats/:id
    router.push(`/chat/${chat.id}`)
    
    // Вариант 2: Или попробуйте полный путь к компоненту чата
    // router.push({ name: 'ChatDetail', params: { id: chat.id } })
    
  } catch (error: any) {
    console.error('Чат недоступен:', error)
    alert('У вас нет доступа к этому чату')
    loadChats()
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('ru-RU')
}

const getChatName = (chat: Chat) => {
  if (chat.type === 'private') {
    if (chat.other_user) {
      return chat.other_user.display_name || chat.other_user.username
    }
    return chat.participants_usernames?.[0] || 'Личный чат'
  }
  return chat.name || 'Без названия'
}

const getChatAvatar = (chat: Chat) => {
  if (chat.type === 'private') {
    if (chat.other_user?.avatar) {
      return getAvatarUrl(chat.other_user.avatar)
    }
    return getAvatarUrl(chat.avatar_url)
  }
  return getAvatarUrl(chat.avatar_url)
}

// User search and selection methods
const searchUsers = async () => {
  if (userSearch.value.length < 2) {
    userResults.value = []
    return
  }

  try {
    const response = await apiClient.get(`/users/online/?search=${encodeURIComponent(userSearch.value)}`)
    userResults.value = response.data.results || response.data
  } catch (error) {
    console.error('Error searching users:', error)
  }
}

const selectUser = (user: User) => {
  if (!selectedUsers.value.find(u => u.id === user.id)) {
    selectedUsers.value.push(user)
  }
  userSearch.value = ''
  userResults.value = []
}

const removeUser = (user: User) => {
  selectedUsers.value = selectedUsers.value.filter(u => u.id !== user.id)
}

const handleAvatarSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    avatarFile.value = file
    avatarPreview.value = URL.createObjectURL(file)
  }
}

const clearAvatar = () => {
  avatarFile.value = null
  avatarPreview.value = null
}

const resetForm = () => {
  newChat.value = { type: 'direct', name: '', participants: '' }
  userSearch.value = ''
  userResults.value = []
  selectedUsers.value = []
  clearAvatar()
}

onMounted(() => {
  loadChats()
})
</script>

<style scoped>
.chats {
  padding: 2rem 0;
}

.page-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 2rem;
  color: #1f2937;
}

.create-chat-card {
  background: #222222;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.btn-create-chat {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #111111;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-create-chat:hover {
  background: #2563eb;
}

.chats-list {
  margin-top: 0.5rem;
}

.chat-item {
  background: #111111;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chat-item:hover {
  background: #222222;
}

.chat-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-info {
  flex: 1;
  min-width: 0;
}

.chat-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.last-message {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-meta {
  font-size: 0.75rem;
  color: #9ca3af;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
}

.modal-content h3 {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.form-actions button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: white;
  cursor: pointer;
}

.form-actions button[type="submit"] {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.form-actions button[type="submit"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

/* User search styles */
.user-results {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
}

.user-result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.user-result-item:hover {
  background: #f9fafb;
}

.user-result-item:last-child {
  border-bottom: none;
}

.user-avatar-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 500;
  color: #1f2937;
}

.user-username {
  font-size: 0.875rem;
  color: #6b7280;
}

.selected-users {
  margin-top: 1rem;
}

.user-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #eff6ff;
  color: #1d4ed8;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
}

.remove-user {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  margin-left: 0.25rem;
}

.remove-user:hover {
  color: #dc2626;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.avatar-preview {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
}

.avatar-input {
  flex: 1;
}

.btn-clear-avatar {
  padding: 0.25rem 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-clear-avatar:hover {
  background: #fecaca;
}
</style>