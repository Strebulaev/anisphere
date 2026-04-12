<template>
  <div class="chat-invite-page">
    <div class="invite-container">
      <div v-if="loading" class="invite-loading">
        <div class="loading-spinner"></div>
        <p>Загрузка приглашения...</p>
      </div>

      <div v-else-if="error" class="invite-error">
        <div class="error-icon"> <SakuraIcon name="x" /> </div>
        <h2>Ошибка</h2>
        <p>{{ error }}</p>
        <button class="btn-back" @click="goToHome">На главную</button>
      </div>

      <div v-else-if="joined" class="invite-success">
        <div class="success-icon"> <SakuraIcon name="check" /> </div>
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
            <span class="detail-icon"> <SakuraIcon name="user" /> </span>
            <span class="detail-text">
              Приглашает: <strong>{{ invite.created_by.username }}</strong>
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="users" /> </span>
            <span class="detail-text">
              Использовано: {{ invite.uses_count }} / {{ invite.max_uses || '∞' }}
            </span>
          </div>

          <div v-if="invite.expires_at" class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="clock" /> </span>
            <span class="detail-text">
              Истекает: {{ formatDate(invite.expires_at) }}
            </span>
          </div>

          <div class="detail-item">
            <span class="detail-icon"> <SakuraIcon name="clipboard" /> </span>
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
    router.push(`/chat/${invite.value.chat.id}`)
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
  background: var(--surface-1);
  position: relative;
}

/* Фоновый узор */
.chat-invite-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.05) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.05) 0%, transparent 40%);
  pointer-events: none;
}

.invite-container {
  max-width: 500px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.invite-loading,
.invite-error,
.invite-success,
.invite-info {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: 2rem;
  text-align: center;
  box-shadow: var(--shadow-modal);
}

.invite-loading p,
.invite-error p,
.invite-success p {
  margin-top: 1rem;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--surface-4);
  border-top-color: var(--accent);
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
  color: var(--danger);
}

.invite-success h2 {
  color: var(--success);
}

.chat-avatar-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  overflow: hidden;
  border: 3px solid var(--accent);
  box-shadow: var(--shadow-petal);
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
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  color: var(--text-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 600;
  box-shadow: var(--shadow-petal);
}

.chat-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.invite-description {
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.invite-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
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
  color: var(--accent);
}

.detail-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.detail-text strong {
  color: var(--text-primary);
}

.detail-text.active {
  color: var(--success);
}

.detail-text.inactive {
  color: var(--danger);
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
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  border: none;
  border-radius: var(--radius-lg);
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-on-accent);
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  box-shadow: var(--shadow-petal-sm);
}

.btn-join:hover,
.btn-go-chat:hover {
  box-shadow: var(--shadow-glow-sm);
  transform: translateY(-1px);
}

.btn-join:disabled {
  background: var(--surface-5);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.btn-cancel,
.btn-back {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
}

.btn-cancel:hover,
.btn-back:hover {
  background: var(--surface-5);
  border-color: var(--accent);
  color: var(--accent);
}
</style>
