<template>
  <div class="admin-support-panel">
    <!-- Заголовок -->
    <div class="asp-header">
      <h2>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        Поддержка пользователей
      </h2>
      <div class="asp-stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.pending }}</span>
          <span class="stat-label">Ожидают</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.answered }}</span>
          <span class="stat-label">В работе</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.closed }}</span>
          <span class="stat-label">Закрыто</span>
        </div>
      </div>
    </div>

    <!-- Список обращений -->
    <div class="asp-tickets-list">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка обращений...</p>
      </div>

      <div v-else-if="tickets.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <p>Нет обращений</p>
      </div>

      <div v-else class="tickets-grid">
        <div
          v-for="ticket in tickets"
          :key="ticket.id"
          class="ticket-card"
          :class="{ 
            'ticket-active': ticket.status === 'pending' || ticket.status === 'answered',
            'ticket-closed': ticket.status === 'closed'
          }"
          @click="openTicket(ticket)"
        >
          <div class="ticket-header">
            <div class="ticket-user">
              <div class="user-avatar">
                <img v-if="ticket.user_avatar" :src="ticket.user_avatar" alt="" />
                <span v-else>{{ ticket.username?.[0]?.toUpperCase() || '?' }}</span>
              </div>
              <div class="user-info">
                <span class="user-name">{{ ticket.username || 'Аноним' }}</span>
                <span class="ticket-subject">{{ ticket.subject || 'Без темы' }}</span>
              </div>
            </div>
            <div class="ticket-status" :class="ticket.status">
              {{ getStatusLabel(ticket.status) }}
            </div>
          </div>

          <div class="ticket-preview">
            <p>{{ ticket.last_message?.text || 'Нет сообщений' }}</p>
          </div>

          <div class="ticket-footer">
            <span class="ticket-time">{{ formatTime(ticket.updated_at) }}</span>
            <span v-if="ticket.unread_count > 0" class="unread-badge">{{ ticket.unread_count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно с чатом -->
    <Transition name="modal">
      <div v-if="selectedTicket" class="ticket-chat-modal" @click.self="closeTicket">
        <div class="modal-content">
          <!-- Шапка -->
          <div class="modal-header">
            <div class="modal-user-info">
              <div class="modal-user-avatar">
                <img v-if="selectedTicket.user_avatar" :src="selectedTicket.user_avatar" alt="" />
                <span v-else>{{ selectedTicket.username?.[0]?.toUpperCase() || '?' }}</span>
              </div>
              <div>
                <h3>{{ selectedTicket.username || 'Аноним' }}</h3>
                <span class="ticket-status-badge" :class="selectedTicket.status">
                  {{ getStatusLabel(selectedTicket.status) }}
                </span>
              </div>
            </div>
            <div class="modal-actions">
              <button v-if="selectedTicket.status !== 'closed'" class="btn-close-ticket" @click="closeTicketAction">
                Закрыть обращение
              </button>
              <button class="btn-close" @click="closeTicket">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>

          <!-- Сообщения -->
          <div class="modal-messages" ref="messagesContainer">
            <div v-if="loadingMessages" class="loading-messages">
              <div class="spinner"></div>
            </div>

            <div v-else class="messages-list">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message"
                :class="{ 'message-admin': msg.sender_is_admin }"
              >
                <div class="message-avatar">
                  <img v-if="msg.sender_avatar" :src="msg.sender_avatar" alt="" />
                  <span v-else>{{ msg.sender_username?.[0]?.toUpperCase() || '?' }}</span>
                </div>
                <div class="message-content">
                  <span class="message-sender">{{ msg.sender_username }}</span>
                  <p class="message-text">{{ msg.text }}</p>
                  <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Форма ответа -->
          <div class="modal-input-area">
            <textarea
              v-model="replyMessage"
              placeholder="Написать ответ..."
              rows="3"
              class="reply-textarea"
              @keydown.enter.exact.prevent="sendReply"
            ></textarea>
            <button 
              class="reply-btn"
              :disabled="!replyMessage.trim() || sending"
              @click="sendReply"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
              <span>Отправить</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import supportApi, { type SupportTicket, type SupportMessage } from '@/api/support'

interface TicketWithUser {
  id: number
  user_id: number
  username: string
  user_avatar: string | null
  subject: string
  status: 'pending' | 'answered' | 'closed'
  anime_id: number | null
  created_at: string
  updated_at: string
  closed_at: string | null
  last_message: {
    text: string
    sender_id: number
    sender_username: string
    created_at: string
    is_read: boolean
  } | null
  unread_count: number
  is_admin: boolean
}

const tickets = ref<TicketWithUser[]>([])
const selectedTicket = ref<TicketWithUser | null>(null)
const messages = ref<SupportMessage[]>([])
const loading = ref(false)
const loadingMessages = ref(false)
const sending = ref(false)
const replyMessage = ref('')
const stats = ref({ pending: 0, answered: 0, closed: 0 })

const messagesContainer = ref<HTMLElement | null>(null)

const loadTickets = async () => {
  loading.value = true
  try {
    const response = await supportApi.adminList()
    tickets.value = response.data || []
    await loadStats()
  } catch (error) {
    console.error('Error loading tickets:', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await supportApi.adminStats()
    stats.value = response.data || { pending: 0, answered: 0, closed: 0 }
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

const loadMessages = async () => {
  if (!selectedTicket.value) return
  
  loadingMessages.value = true
  try {
    const response = await supportApi.getMessages(selectedTicket.value.id)
    messages.value = response.data || []
    scrollToBottom()
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    loadingMessages.value = false
  }
}

const openTicket = async (ticket: TicketWithUser) => {
  selectedTicket.value = ticket
  await loadMessages()
}

const closeTicket = () => {
  selectedTicket.value = null
  messages.value = []
  replyMessage.value = ''
}

const closeTicketAction = async () => {
  if (!selectedTicket.value) return
  
  try {
    await supportApi.closeTicket(selectedTicket.value.id)
    selectedTicket.value.status = 'closed'
    closeTicket()
    await loadTickets()
  } catch (error) {
    console.error('Error closing ticket:', error)
  }
}

const sendReply = async () => {
  if (!replyMessage.value.trim() || sending.value || !selectedTicket.value) return
  
  sending.value = true
  try {
    await supportApi.sendMessage(selectedTicket.value.id, replyMessage.value.trim())
    replyMessage.value = ''
    await loadMessages()
    await loadTickets()
  } catch (error) {
    console.error('Error sending reply:', error)
  } finally {
    sending.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const getStatusLabel = (status: string) => {
  return {
    pending: 'Ожидает',
    answered: 'В работе',
    closed: 'Закрыто'
  }[status] || status
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  
  if (diffMins < 1) return 'Сейчас'
  if (diffMins < 60) return `${diffMins} мин назад`
  if (diffHours < 24) return `${diffHours} ч назад`
  return date.toLocaleDateString('ru')
}

const formatMessageTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}

let pollInterval: number | null = null

const startPolling = () => {
  if (pollInterval) return
  pollInterval = window.setInterval(() => {
    if (selectedTicket.value) {
      loadMessages()
    }
    loadTickets()
  }, 10000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(() => {
  loadTickets()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.admin-support-panel {
  padding: 20px;
  background: var(--surface-1);
  border-radius: var(--radius-xl);
  min-height: 100%;
}

/* Header */
.asp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.asp-header h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.asp-header svg {
  color: var(--accent);
}

.asp-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Tickets List */
.asp-tickets-list {
  background: var(--surface-2);
  border-radius: var(--radius-lg);
  padding: 20px;
  min-height: 400px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  gap: 16px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-default);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.tickets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.ticket-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.ticket-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.ticket-active {
  border-left: 4px solid var(--accent);
}

.ticket-closed {
  opacity: 0.6;
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.ticket-user {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.ticket-subject {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-status {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  flex-shrink: 0;
}

.ticket-status.pending {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.ticket-status.answered {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.ticket-status.closed {
  background: rgba(156, 163, 175, 0.15);
  color: #9ca3af;
}

.ticket-preview p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ticket-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.ticket-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

.unread-badge {
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  min-width: 20px;
  text-align: center;
}

/* Modal */
.ticket-chat-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100000;
  padding: 20px;
}

.modal-content {
  background: var(--surface-2);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--border-default);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: var(--surface-3);
  border-bottom: 1px solid var(--border-subtle);
}

.modal-user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
  overflow: hidden;
}

.modal-user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-user-info h3 {
  margin: 0 0 4px;
  font-size: 18px;
  color: var(--text-primary);
}

.ticket-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
}

.ticket-status-badge.pending {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.ticket-status-badge.answered {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.ticket-status-badge.closed {
  background: rgba(156, 163, 175, 0.15);
  color: #9ca3af;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-close-ticket {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-close-ticket:hover {
  border-color: var(--danger);
  color: var(--danger);
  background: var(--danger-subtle);
}

.btn-close {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

/* Messages */
.modal-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--surface-1);
}

.loading-messages {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.message-admin {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
  overflow: hidden;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-sender {
  font-size: 11px;
  color: var(--text-tertiary);
  padding-left: 4px;
}

.message.message-admin .message-sender {
  text-align: right;
  padding-left: 0;
  padding-right: 4px;
}

.message-text {
  background: var(--surface-3);
  padding: 10px 14px;
  border-radius: var(--radius-xl);
  border-bottom-left-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.4;
  color: var(--text-primary);
  margin: 0;
  word-wrap: break-word;
  border: 1px solid var(--border-subtle);
}

.message.message-admin .message-text {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  border-bottom-left-radius: var(--radius-xl);
  border-bottom-right-radius: var(--radius-sm);
  border: none;
  color: white;
}

.message-time {
  font-size: 10px;
  color: var(--text-tertiary);
  padding-left: 4px;
}

.message.message-admin .message-time {
  text-align: right;
  padding-left: 0;
  padding-right: 4px;
}

/* Input Area */
.modal-input-area {
  display: flex;
  gap: 12px;
  padding: 20px;
  background: var(--surface-3);
  border-top: 1px solid var(--border-subtle);
}

.reply-textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-2);
  color: var(--text-primary);
  font-size: 14px;
  resize: none;
  font-family: inherit;
  max-height: 120px;
  transition: all 0.2s;
}

.reply-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.reply-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.reply-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow-sm);
}

.reply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9) translateY(20px);
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: all 0.3s ease;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .asp-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .asp-stats {
    width: 100%;
    justify-content: space-around;
  }

  .tickets-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    max-width: 100%;
    max-height: 90vh;
  }
}
</style>
