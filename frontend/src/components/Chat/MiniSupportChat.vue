<template>
  <Teleport to="body">
    <!-- Основной чат -->
    <Transition name="mini-chat">
      <div
        v-if="isOpen"
        class="mini-chat"
        :class="{ 'mini-chat-closed': isMinimized }"
      >
        <!-- Заголовок -->
        <div class="mc-header" @click="toggleMinimize">
          <div class="mc-header-info">
            <div class="mc-avatar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <span class="mc-title">Поддержка</span>
            <span v-if="unreadCount > 0" class="mc-badge">{{ unreadCount }}</span>
          </div>
          <button class="mc-close-btn" @click.stop="closeChat" title="Закрыть">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <!-- Контент -->
        <div v-if="!isMinimized" class="mc-content">
          <!-- Форма создания обращения (если нет активного) -->
          <div v-if="!activeTicket && !isLoading" class="mc-new-ticket">
            <div class="mc-welcome">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                <line x1="9" y1="10" x2="15" y2="10"/>
              </svg>
              <p>Есть вопрос? Напишите нам!</p>
              <span>Ответим в течение дня</span>
            </div>
            <div class="mc-form">
              <textarea
                v-model="newMessage"
                placeholder="Опишите вашу проблему или вопрос..."
                rows="3"
                class="mc-textarea"
                @keydown.enter.exact.prevent="submitNewTicket"
              ></textarea>
              <button 
                class="mc-submit-btn" 
                :disabled="!newMessage.trim() || isSending"
                @click="submitNewTicket"
              >
                <span v-if="isSending" class="mc-spinner"></span>
                <span v-else>Отправить</span>
              </button>
            </div>
          </div>

          <!-- Список сообщений (если есть активное обращение) -->
          <div v-else-if="activeTicket" class="mc-messages">
            <div v-if="isLoadingMessages" class="mc-loading">
              <div class="mc-spinner-lg"></div>
            </div>
            <div v-else ref="messagesContainer" class="mc-messages-list">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="mc-message"
                :class="{ 
                  'mc-message-own': msg.sender_id === currentUserId,
                  'mc-message-admin': msg.sender_is_admin 
                }"
              >
                <div class="mc-message-avatar">
                  <img v-if="msg.sender_avatar" :src="msg.sender_avatar" alt="" />
                  <span v-else>{{ msg.sender_username[0]?.toUpperCase() }}</span>
                </div>
                <div class="mc-message-content">
                  <span class="mc-message-sender">{{ msg.sender_username }}</span>
                  <p class="mc-message-text">{{ msg.text }}</p>
                  <span class="mc-message-time">{{ formatTime(msg.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- Форма отправки -->
            <div class="mc-input-area">
              <textarea
                v-model="replyMessage"
                placeholder="Написать сообщение..."
                rows="2"
                class="mc-reply-input"
                @keydown.enter.exact.prevent="sendReply"
              ></textarea>
              <button 
                class="mc-reply-btn"
                :disabled="!replyMessage.trim() || isSending"
                @click="sendReply"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              </button>
            </div>

            <!-- Кнопка закрытия обращения -->
            <button 
              v-if="activeTicket.status !== 'closed'"
              class="mc-close-ticket-btn"
              @click="handleCloseTicket"
            >
              Закрыть обращение
            </button>
            <div v-else class="mc-closed-notice">
              Обращение закрыто
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Кнопка FAB (отдельный Transition) -->
    <Transition name="fab">
      <button
        v-if="!isOpen"
        class="mini-chat-fab"
        @click="openChat"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span v-if="unreadCount > 0" class="fab-badge">{{ unreadCount }}</span>
      </button>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import supportApi, { type SupportTicket, type SupportMessage } from '@/api/support'

const authStore = useAuthStore()

const isOpen = ref(false)
const isMinimized = ref(false)
const isLoading = ref(false)
const isLoadingMessages = ref(false)
const isSending = ref(false)

const activeTicket = ref<SupportTicket | null>(null)
const messages = ref<SupportMessage[]>([])
const messagesContainer = ref<HTMLElement | null>(null)

const newMessage = ref('')
const replyMessage = ref('')
const unreadCount = ref(0)

const currentUserId = computed(() => authStore.user?.id || 0)

const openChat = async () => {
  isOpen.value = true
  isMinimized.value = false
  await loadActiveTicket()
}

const closeChat = () => {
  isOpen.value = false
}

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value
}

const loadActiveTicket = async () => {
  if (!authStore.isAuthenticated) return
  
  isLoading.value = true
  try {
    const response = await supportApi.getMyActive()
    if (response.data.has_active) {
      activeTicket.value = response.data
      await loadMessages()
    }
    unreadCount.value = response.data.unread_count || 0
  } catch (error) {
    console.error('Error loading active ticket:', error)
  } finally {
    isLoading.value = false
  }
}

const loadMessages = async () => {
  if (!activeTicket.value) return
  
  isLoadingMessages.value = true
  try {
    const response = await supportApi.getMessages(activeTicket.value.id)
    messages.value = response.data
    unreadCount.value = 0
    scrollToBottom()
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    isLoadingMessages.value = false
  }
}

const submitNewTicket = async () => {
  if (!newMessage.value.trim() || isSending.value) return
  
  isSending.value = true
  try {
    const response = await supportApi.createTicket({ text: newMessage.value.trim() })
    await loadActiveTicket()
    newMessage.value = ''
  } catch (error: any) {
    console.error('Error creating ticket:', error)
  } finally {
    isSending.value = false
  }
}

const sendReply = async () => {
  if (!replyMessage.value.trim() || isSending.value || !activeTicket.value) return
  
  isSending.value = true
  try {
    await supportApi.sendMessage(activeTicket.value.id, replyMessage.value.trim())
    await loadMessages()
    replyMessage.value = ''
  } catch (error) {
    console.error('Error sending message:', error)
  } finally {
    isSending.value = false
  }
}

const handleCloseTicket = async () => {
  if (!activeTicket.value) return
  
  try {
    await supportApi.closeTicket(activeTicket.value.id)
    await loadActiveTicket()
  } catch (error) {
    console.error('Error closing ticket:', error)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'сейчас'
  if (diffMins < 60) return `${diffMins} мин`
  if (diffHours < 24) return `${diffHours} ч`
  if (diffDays < 7) return `${diffDays} д`
  
  return date.toLocaleDateString('ru')
}

// Автообновление сообщений
let pollInterval: number | null = null

const startPolling = () => {
  if (pollInterval) return
  pollInterval = window.setInterval(() => {
    if (isOpen.value && activeTicket.value) {
      loadMessages()
    }
  }, 10000) // каждые 10 секунд
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

watch(isOpen, (newVal) => {
  if (newVal) {
    startPolling()
  } else {
    stopPolling()
  }
})

onMounted(() => {
  if (isOpen.value) {
    startPolling()
  }
})
</script>

<style scoped>
.mini-chat {
  position: fixed;
  bottom: 20px;
  left: 20px;
  width: 360px;
  max-height: 500px;
  background: var(--surface-2);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  z-index: 99999;
  overflow: hidden;
  border: 1px solid var(--border-default);
  transition: all var(--duration-base) var(--ease-petal);
}

.mini-chat:hover {
  border-color: var(--accent-subtle);
  box-shadow: var(--shadow-glow);
}

.mini-chat.mini-chat-closed {
  max-height: none;
}

/* Header */
.mc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  cursor: pointer;
  user-select: none;
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-header:hover {
  filter: brightness(1.05);
}

.mc-header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mc-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border: 2px solid rgba(255,255,255,0.3);
}

.mc-title {
  font-weight: 600;
  color: white;
  font-size: 15px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.mc-badge {
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  min-width: 18px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(255,138,138,0.3);
}

.mc-close-btn {
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-close-btn:hover {
  color: white;
  background: rgba(255,255,255,0.15);
}

/* Content */
.mc-content {
  display: flex;
  flex-direction: column;
  height: 400px;
}

/* New ticket form */
.mc-new-ticket {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mc-welcome {
  text-align: center;
  padding: 20px 10px;
  color: var(--text-tertiary);
}

.mc-welcome svg {
  margin-bottom: 12px;
  color: var(--accent);
  filter: drop-shadow(0 0 8px var(--accent-glow));
}

.mc-welcome p {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.mc-welcome span {
  font-size: 13px;
}

.mc-form {
  margin-top: auto;
}

.mc-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: 14px;
  resize: none;
  font-family: inherit;
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.mc-submit-btn {
  width: 100%;
  margin-top: 10px;
  padding: 12px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: var(--shadow-petal-sm);
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-submit-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-sm);
  transform: translateY(-1px);
}

.mc-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Messages */
.mc-messages {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mc-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mc-messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mc-message {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.mc-message.mc-message-own {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.mc-message-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: var(--shadow-petal-sm);
}

.mc-message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mc-message-admin .mc-message-avatar {
  background: linear-gradient(135deg, var(--success) 0%, #34d399 100%);
}

.mc-message-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mc-message-sender {
  font-size: 11px;
  color: var(--text-tertiary);
  padding-left: 8px;
}

.mc-message-own .mc-message-sender {
  text-align: right;
  padding-left: 0;
  padding-right: 8px;
}

.mc-message-text {
  background: var(--surface-4);
  padding: 8px 12px;
  border-radius: var(--radius-xl);
  border-bottom-left-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-primary);
  margin: 0;
  word-wrap: break-word;
  border: 1px solid var(--border-subtle);
}

.mc-message-own .mc-message-text {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  border-bottom-left-radius: var(--radius-xl);
  border-bottom-right-radius: var(--radius-sm);
  border: none;
  box-shadow: var(--shadow-petal-sm);
}

.mc-message-time {
  font-size: 10px;
  color: var(--text-tertiary);
  padding-left: 8px;
}

.mc-message-own .mc-message-time {
  text-align: right;
  padding-left: 0;
  padding-right: 8px;
}

/* Input area */
.mc-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border-subtle);
  background: var(--surface-3);
}

.mc-reply-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: 13px;
  resize: none;
  font-family: inherit;
  max-height: 80px;
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-reply-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.mc-reply-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-petal-sm);
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-reply-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-sm);
  transform: scale(1.05);
}

.mc-reply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Close ticket button */
.mc-close-ticket-btn {
  margin: 8px 12px 12px;
  padding: 8px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.mc-close-ticket-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-subtle);
}

.mc-closed-notice {
  margin: 8px 12px 12px;
  padding: 8px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 12px;
  background: var(--surface-4);
  border-radius: var(--radius-md);
}

/* Spinner */
.mc-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.mc-spinner-lg {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-default);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* FAB button */
.mini-chat-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-petal);
  z-index: 99998;
  transition: all var(--duration-base) var(--ease-petal);
}

.mini-chat-fab:hover {
  transform: scale(1.08);
  box-shadow: var(--shadow-glow);
}

.fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  color: white;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: var(--radius-full);
  min-width: 14px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(255,138,138,0.4);
}

/* Transition */
.mini-chat-enter-active,
.mini-chat-leave-active {
  transition: all var(--duration-slow) var(--ease-bloom);
}

.mini-chat-enter-from,
.mini-chat-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* FAB Transition */
.fab-enter-active,
.fab-leave-active {
  transition: all var(--duration-slow) var(--ease-bloom);
}

.fab-enter-from,
.fab-leave-to {
  opacity: 0;
  transform: scale(0.5);
}

/* Responsive */
@media (max-width: 480px) {
  .mini-chat {
    width: calc(100vw - 32px);
    right: 16px;
    left: auto;
    bottom: 16px;
  }
  
  .mini-chat-fab {
    right: 16px;
    bottom: 16px;
    width: 44px;
    height: 44px;
  }
}
</style>
