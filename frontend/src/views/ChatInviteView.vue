<template>
  <div class="chat-invite-page">
    <div class="invite-container">
      <div v-if="loading" class="invite-loading">
        <div class="loading-spinner"></div>
        <p>Загрузка приглашения...</p>
      </div>

      <div v-else-if="error" class="invite-error">
        <div class="error-icon">❌</div>
        <h2>Ошибка</h2>
        <p>{{ error }}</p>
        <button class="btn-back" @click="goToHome">На главную</button>
      </div>

      <div v-else-if="joined" class="invite-success">
        <div class="success-icon">✅</div>
        <h2>Добро пожаловать!</h2>
        <p>Вы успешно присоединились к чату "{{ chatName }}"</p>
        <button class="btn-go-chat" @click="goToChat">Перейти в чат</button>
      </div>

      <div v-else-if="invite" class="invite-info">
        <div v-if="invite.chat.avatar_url" class="chat-avatar-large">
          <img :src="invite.chat.avatar_url" :alt="invite.chat.name" />
        </div>
        <div v-else class="chat-avatar-placeholder-large">
          {{ getInitials(invite.chat.name) }}
        </div>

        <h1 class="chat-name">{{ invite.chat.name }}</h1>
        <p class="invite-description">Вас приглашают присоединиться к этому чату</p>

        <div class="invite-details">
          <div class="detail-item">
            <span class="detail-icon">👤</span>
            <span class="detail-text">
              Приглашает: <strong>{{ invite.created_by.username }}</strong>
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon">👥</span>
            <span class="detail-text">
              Использовано: {{ invite.uses_count }} / {{ invite.max_uses || '∞' }}
            </span>
          </div>

          <div v-if="invite.expires_at" class="detail-item">
            <span class="detail-icon">⏰</span>
            <span class="detail-text">
              Истекает: {{ formatDate(invite.expires_at) }}
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon">📋</span>
            <span :class="['detail-text', { 'active': invite.is_active, 'inactive': !invite.is_active }]">
              {{ invite.is_active ? 'Приглашение активно' : 'Приглашение неактивно' }}
            </span>
          </div>
        </div>

        <div class="invite-actions">
          <button
            class="btn-join"
            @click="joinChat"
            :disabled="!invite.is_valid || joining"
          >
            {{ joining ? 'Присоединение...' : 'Присоединиться к чату' }}
          </button>
          <button class="btn-cancel" @click="goToHome">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAuthStore } from '@/stores/auth'
import { useModalStore } from '@/stores/modal'

const route = useRoute()
const router = useRouter()
const chatExtrasStore = useChatExtrasStore()
const authStore = useAuthStore()
const modalStore = useModalStore()

const loading = ref(true)
const joining = ref(false)
const error = ref('')
const joined = ref(false)
const invite = ref<any>(null)
const chatName = ref('')

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    modalStore.openAuthModal()
    return
  }

  const token = route.params.token as string
  if (!token) {
    error.value = 'Не указан токен приглашения'
    loading.value = false
    return
  }

  try {
    const result = await chatExtrasStore.joinByToken(token)
    joined.value = true
    chatName.value = result.chat?.name || 'Чат'
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Ошибка при присоединении к чату'
  } finally {
    loading.value = false
  }
})

const joinChat = async () => {
  if (!invite.value?.is_valid) return

  joining.value = true
  try {
    const token = route.params.token as string
    const result = await chatExtrasStore.joinByToken(token)
    joined.value = true
    chatName.value = result.chat?.name || 'Чат'
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Ошибка при присоединении к чату'
  } finally {
    joining.value = false
  }
}

const goToChat = () => {
  if (invite.value?.chat?.id) {
    router.push(`/chats/${invite.value.chat.id}`)
  } else {
    router.push('/chats')
  }
}

const goToHome = () => {
  router.push('/')
}

const getInitials = (name: string) => {
  if (!name) return '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length === 0) return name.substring(0, 2).toUpperCase()
  return words.slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.chat-invite-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--color-background);
}

.invite-container {
  max-width: 500px;
  width: 100%;
}

.invite-loading,
.invite-error,
.invite-success,
.invite-info {
  background: var(--color-background-surface);
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.invite-loading p,
.invite-error p,
.invite-success p {
  margin-top: 1rem;
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--color-divider-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon,
.success-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.invite-error h2 {
  color: #f44336;
}

.invite-success h2 {
  color: #4caf50;
}

.chat-avatar-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  overflow: hidden;
}

.chat-avatar-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-avatar-placeholder-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 600;
}

.chat-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.invite-description {
  color: var(--color-text-secondary);
  margin-bottom: 2rem;
}

.invite-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--color-background);
  border-radius: 12px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-align: left;
}

.detail-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.detail-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.detail-text strong {
  color: var(--color-text);
}

.detail-text.active {
  color: #4caf50;
}

.detail-text.inactive {
  color: #f44336;
}

.invite-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn-join,
.btn-go-chat {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-join:hover,
.btn-go-chat:hover {
  background: var(--color-accent-hover);
}

.btn-join:disabled {
  background: var(--color-text-disabled);
  cursor: not-allowed;
}

.btn-cancel,
.btn-back {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel:hover,
.btn-back:hover {
  background: var(--color-background-active);
}
</style>
