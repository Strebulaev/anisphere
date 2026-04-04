<template>
  <div class="support-page">
    <div class="support-header">
      <h1>Поддержка</h1>
      <button class="btn-primary" @click="showCreateModal = true">
        <span class="icon">+</span>
        Новое обращение
      </button>
    </div>

    <!-- Список обращений -->
    <div class="tickets-list" v-if="tickets.length">
      <div 
        v-for="ticket in tickets" 
        :key="ticket.id"
        class="ticket-card"
        :class="{ active: selectedTicket?.id === ticket.id, unread: ticket.unread_count > 0 }"
        @click="selectTicket(ticket)"
      >
        <div class="ticket-header">
          <span class="ticket-id">#{{ ticket.id }}</span>
          <span class="ticket-status" :class="ticket.status">{{ getStatusLabel(ticket.status) }}</span>
        </div>
        <div class="ticket-subject">{{ ticket.subject }}</div>
        <div class="ticket-meta">
          <span class="ticket-category">{{ getCategoryLabel(ticket.category) }}</span>
          <span class="ticket-date">{{ formatDate(ticket.created_at) }}</span>
        </div>
        <div class="ticket-preview" v-if="ticket.last_message">
          {{ ticket.last_message.message }}
        </div>
        <div class="unread-badge" v-if="ticket.unread_count > 0">
          {{ ticket.unread_count }}
        </div>
      </div>
    </div>

    <div class="empty-state" v-else>
      <div class="empty-icon">🎫</div>
      <h3>Нет обращений</h3>
      <p>Создайте новое обращение, если у вас есть вопросы</p>
    </div>

    <!-- Чат с поддержкой -->
    <div class="chat-panel" v-if="selectedTicket">
      <div class="chat-header">
        <div class="chat-info">
          <h3>{{ selectedTicket.subject }}</h3>
          <span class="ticket-id">#{{ selectedTicket.id }}</span>
        </div>
        <div class="chat-actions">
          <button 
            class="btn-icon" 
            @click="closeTicket" 
            v-if="selectedTicket.status !== 'closed'"
            title="Закрыть обращение"
          >
            ✕
          </button>
          <button 
            class="btn-icon" 
            @click="reopenTicket" 
            v-if="selectedTicket.status === 'closed'"
            title="Переоткрыть"
          >
            ↻
          </button>
        </div>
      </div>

      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="msg in selectedTicket.messages" 
          :key="msg.id"
          class="message"
          :class="{ 'from-admin': msg.is_from_admin, 'from-user': !msg.is_from_admin }"
        >
          <div class="message-header">
            <span class="sender">{{ msg.sender_username }}</span>
            <span class="time">{{ formatTime(msg.created_at) }}</span>
          </div>
          <div class="message-content">{{ msg.message }}</div>
        </div>
      </div>

      <div class="chat-input" v-if="selectedTicket.status !== 'closed'">
        <textarea 
          v-model="replyMessage" 
          placeholder="Введите сообщение..."
          @keydown.enter.exact.prevent="sendReply"
          rows="2"
        ></textarea>
        <button class="btn-send" @click="sendReply" :disabled="!replyMessage.trim()">
          Отправить
        </button>
      </div>
      <div class="chat-closed" v-else>
        <p>Обращение закрыто</p>
        <button class="btn-secondary" @click="reopenTicket">Переоткрыть</button>
      </div>
    </div>

    <!-- Модальное окно создания обращения -->
    <div class="modal-overlay" v-if="showCreateModal" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Новое обращение</h2>
          <button class="btn-close" @click="showCreateModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Тема</label>
            <input 
              v-model="newTicket.subject" 
              type="text" 
              placeholder="Кратко опишите проблему"
              maxlength="200"
            />
          </div>
          <div class="form-group">
            <label>Категория</label>
            <select v-model="newTicket.category">
              <option value="general">Общий вопрос</option>
              <option value="account">Проблема с аккаунтом</option>
              <option value="payment">Оплата</option>
              <option value="bug">Баг/ошибка</option>
              <option value="content">Контент</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div class="form-group">
            <label>Приоритет</label>
            <select v-model="newTicket.priority">
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
              <option value="urgent">Срочный</option>
            </select>
          </div>
          <div class="form-group">
            <label>Описание</label>
            <textarea 
              v-model="newTicket.description" 
              placeholder="Подробно опишите вашу проблему..."
              rows="6"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateModal = false">Отмена</button>
          <button 
            class="btn-primary" 
            @click="createTicket"
            :disabled="!isValidTicket"
          >
            Создать обращение
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/api'

interface SupportTicket {
  id: number
  user: number
  user_username: string
  subject: string
  description: string
  category: string
  status: string
  priority: string
  messages: SupportMessage[]
  unread_count: number
  last_message: { message: string; sender_username: string } | null
  created_at: string
  updated_at: string
}

interface SupportMessage {
  id: number
  sender: number
  sender_username: string
  message: string
  is_from_admin: boolean
  created_at: string
}

const tickets = ref<SupportTicket[]>([])
const selectedTicket = ref<SupportTicket | null>(null)
const replyMessage = ref('')
const showCreateModal = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const newTicket = ref({
  subject: '',
  category: 'general',
  priority: 'medium',
  description: ''
})

const isValidTicket = computed(() => {
  return newTicket.value.subject.trim().length >= 3 && 
         newTicket.value.description.trim().length >= 10
})

const statusLabels: Record<string, string> = {
  open: 'Открыто',
  in_progress: 'В работе',
  waiting: 'Ожидание',
  resolved: 'Решено',
  closed: 'Закрыто'
}

const categoryLabels: Record<string, string> = {
  general: 'Общий вопрос',
  account: 'Аккаунт',
  payment: 'Оплата',
  bug: 'Баг',
  content: 'Контент',
  other: 'Другое'
}

function getStatusLabel(status: string) {
  return statusLabels[status] || status
}

function getCategoryLabel(category: string) {
  return categoryLabels[category] || category
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { 
    day: 'numeric', 
    month: 'short',
    year: 'numeric'
  })
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit'
  })
}

async function loadTickets() {
  try {
    const response = await api.get('/users/support/tickets/')
    tickets.value = response.data.results || []
  } catch (error) {
    console.error('Failed to load tickets:', error)
  }
}

async function selectTicket(ticket: SupportTicket) {
  selectedTicket.value = ticket
  
  // Загружаем полную информацию
  try {
    const response = await api.get(`/users/support/tickets/${ticket.id}/`)
    selectedTicket.value = response.data
    
    // Отмечаем как прочитанное
    await api.post(`/users/support/tickets/${ticket.id}/mark-read/`)
    
    // Обновляем локально
    const idx = tickets.value.findIndex(t => t.id === ticket.id)
    if (idx !== -1 && tickets.value[idx]) {
      tickets.value[idx].unread_count = 0
    }
  } catch (error) {
    console.error('Failed to load ticket:', error)
  }
  
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function createTicket() {
  if (!isValidTicket.value) return
  
  try {
    const response = await api.post('/users/support/tickets/', newTicket.value)
    tickets.value.unshift(response.data)
    showCreateModal.value = false
    
    // Очищаем форму
    newTicket.value = {
      subject: '',
      category: 'general',
      priority: 'medium',
      description: ''
    }
    
    // Открываем созданное обращение
    selectTicket(response.data)
  } catch (error) {
    console.error('Failed to create ticket:', error)
  }
}

async function sendReply() {
  if (!replyMessage.value.trim() || !selectedTicket.value) return
  
  try {
    const response = await api.post(
      `/users/support/tickets/${selectedTicket.value.id}/reply/`,
      { message: replyMessage.value }
    )
    
    if (!selectedTicket.value.messages) {
      selectedTicket.value.messages = []
    }
    selectedTicket.value.messages.push(response.data)
    replyMessage.value = ''
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to send reply:', error)
  }
}

async function closeTicket() {
  if (!selectedTicket.value) return
  
  try {
    await api.post(`/users/support/tickets/${selectedTicket.value.id}/close/`)
    selectedTicket.value.status = 'closed'
    
    // Обновляем в списке
    const idx = tickets.value.findIndex(t => t.id === selectedTicket.value?.id)
    if (idx !== -1 && tickets.value[idx]) {
      tickets.value[idx].status = 'closed'
    }
  } catch (error) {
    console.error('Failed to close ticket:', error)
  }
}

async function reopenTicket() {
  if (!selectedTicket.value) return
  
  try {
    await api.post(`/users/support/tickets/${selectedTicket.value.id}/reopen/`)
    selectedTicket.value.status = 'in_progress'
    
    // Обновляем в списке
    const idx = tickets.value.findIndex(t => t.id === selectedTicket.value?.id)
    if (idx !== -1 && tickets.value[idx]) {
      tickets.value[idx].status = 'in_progress'
    }
  } catch (error) {
    console.error('Failed to reopen ticket:', error)
  }
}

onMounted(() => {
  loadTickets()
})
</script>

<style scoped>
.support-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 20px;
}

.support-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.support-header h1 {
  margin: 0;
  font-size: 24px;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--primary-color, #667eea);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tickets-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.ticket-card {
  padding: 15px;
  background: var(--card-bg, #2d2d2d);
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.ticket-card:hover {
  background: var(--hover-bg, #3d3d3d);
}

.ticket-card.active {
  border-color: var(--primary-color, #667eea);
}

.ticket-card.unread {
  border-left: 3px solid var(--accent-color, #00C853);
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.ticket-id {
  font-size: 12px;
  color: var(--text-secondary, #b0b0b0);
}

.ticket-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--primary-color, #667eea);
  color: white;
}

.ticket-status.closed {
  background: #666;
}

.ticket-status.resolved {
  background: #00C853;
}

.ticket-subject {
  font-weight: 600;
  margin-bottom: 8px;
}

.ticket-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary, #b0b0b0);
}

.ticket-preview {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary, #b0b0b0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: var(--accent-color, #00C853);
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--card-bg, #2d2d2d);
  border-radius: 12px;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--border-color, #404040);
}

.chat-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--hover-bg, #3d3d3d);
  color: var(--text-color, #fff);
  border-radius: 6px;
  cursor: pointer;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 80%;
  padding: 12px;
  border-radius: 12px;
}

.message.from-user {
  align-self: flex-end;
  background: var(--primary-color, #667eea);
  color: white;
}

.message.from-admin {
  align-self: flex-start;
  background: var(--hover-bg, #3d3d3d);
}

.message-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
  opacity: 0.8;
}

.chat-input {
  display: flex;
  gap: 10px;
  padding: 15px;
  border-top: 1px solid var(--border-color, #404040);
}

.chat-input textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color, #404040);
  border-radius: 8px;
  background: var(--bg-color, #1a1a1a);
  color: var(--text-color, #fff);
  resize: none;
}

.btn-send {
  padding: 10px 20px;
  background: var(--primary-color, #667eea);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-closed {
  padding: 20px;
  text-align: center;
  border-top: 1px solid var(--border-color, #404040);
}

.chat-closed p {
  color: var(--text-secondary, #b0b0b0);
  margin-bottom: 10px;
}

.btn-secondary {
  padding: 8px 16px;
  background: var(--hover-bg, #3d3d3d);
  color: var(--text-color, #fff);
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
}

.empty-state p {
  color: var(--text-secondary, #b0b0b0);
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg, #2d2d2d);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color, #404040);
}

.modal-header h2 {
  margin: 0;
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-color, #fff);
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: var(--text-secondary, #b0b0b0);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color, #404040);
  border-radius: 8px;
  background: var(--bg-color, #1a1a1a);
  color: var(--text-color, #fff);
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid var(--border-color, #404040);
}
</style>
