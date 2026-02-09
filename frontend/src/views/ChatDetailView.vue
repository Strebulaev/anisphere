<template>
  <div class="chat-detail-view">
    <div class="chat-header">
      <button @click="$router.back()" class="back-btn">←</button>
      <div class="chat-info">
        <button @click="showSettings = true" title="Настройки чата">
          <img :src="chatAvatar" :alt="chatName" class="chat-avatar">
        </button>
        <div class="chat-details">
          <h2 class="chat-name">{{ chatName }}</h2>
          <div class="chat-status" v-if="chat?.type === 'private' && otherUser">
            <template v-if="isOtherTyping">
              <span class="typing-indicator">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              </span>
              печатает...
            </template>
            <template v-else-if="otherUser?.is_online">
              <span class="status-dot online"></span>онлайн
            </template>
            <template v-else>
              <span class="status-dot offline"></span>оффлайн
            </template>
          </div>
          <div class="chat-members" v-else-if="chat?.type === 'group'">
            {{ chat.participants_usernames?.length || 0 }} участников
          </div>
        </div>
      </div>
      <div class="header-actions">
        <!-- <button @click="showSettings = true" class="settings-btn" title="Настройки чата">⚙️</button> -->
        <button @click="showChatInfo = !showChatInfo" class="info-btn">sssssssssssssssssssssssssssssssssssssssssssssssssss</button>
      </div>  
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="loadingMessages" class="loading">Загрузка...</div>
      <div v-else-if="messages.length === 0" class="no-messages">Нет сообщений</div>
      <div v-else class="messages-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'own-message': message.sender_id === user?.id }]"
        >
          <div class="message-content">
            <div class="message-text" v-if="message.text">{{ message.text }}</div>
            <img v-if="message.media && message.media_type === 'image'" :src="message.media" class="message-image" />
            <div v-if="message.media && message.media_type !== 'image'" class="message-file">
              <a :href="message.media" target="_blank">📎 {{ getFileName(message.media) }}</a>
            </div>
            <div class="message-time">{{ formatMessageTime(message.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="message-input-area">
      <form @submit.prevent="sendMessage" class="message-form">
        <input v-model="newMessage" type="text" placeholder="Сообщение..." class="message-input"
          :disabled="sending || !wsConnected" @input="handleTyping" />
        <input ref="fileInput" type="file" @change="handleFileSelect" style="display:none" accept="image/*,video/*,audio/*,.pdf,.doc*" />
        <button type="button" @click="attachFile" class="attach-btn" :disabled="sending || !wsConnected">📎</button>
        <button type="submit" class="send-btn" :disabled="!newMessage.trim() || sending || !wsConnected">
          {{ sending ? '⏳' : '📤' }}
        </button>
      </form>
      <div v-if="!wsConnected && reconnectAttempts > 0" class="ws-status">
        Переподключение... ({{ reconnectAttempts }})
      </div>
    </div>

    <div v-if="showChatInfo" class="chat-info-sidebar" @click.self="showChatInfo = false">
      <div class="sidebar-header">
        <h3>О чате</h3>
        <button @click="showChatInfo = false" class="close-btn">✕</button>
      </div>
      <div class="sidebar-content">
        <div class="chat-avatar-large">
          <img :src="chatAvatar" :alt="chatName">
        </div>
        <h4>{{ chatName }}</h4>
        <p v-if="chat?.description">{{ chat.description }}</p>
        <div v-if="chat?.type === 'group'" class="participants-list">
          <h5>Участники ({{ chat.participants_usernames?.length || 0 }})</h5>
          <div v-for="username in chat.participants_usernames" :key="username" class="participant">
            <span>{{ username }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно настроек чата -->
    <ChatSettingsModal
      :is-open="showSettings"
      :chat-id="Number(route.params.id)"
      :is-group="chat?.type === 'group'"
      @close="showSettings = false"
      @updated="loadChat"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAvatar } from '@/composables/useAvatar'
import ChatSettingsModal from '@/components/ChatSettingsModal.vue'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { getAvatarUrl } = useAvatar()

const chat = ref<any>(null)
const messages = ref<any[]>([])
const loadingMessages = ref(false)
const sending = ref(false)
const showChatInfo = ref(false)
const showSettings = ref(false)
const newMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const fileInput = ref<HTMLInputElement>()
const isOtherTyping = ref(false)
const wsConnected = ref(false)
const reconnectAttempts = ref(0)

let ws: WebSocket | null = null
let typingDebounceTimer: number | null = null

const user = computed(() => authStore.user)
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const chatName = computed(() => {
  if (!chat.value) return 'Загрузка...'
  if (chat.value.user1 && chat.value.user2) {
    const other = chat.value.other_user
    return other?.display_name || other?.username || 'Личный чат'
  }
  return chat.value.name || 'Групповой чат'
})

const otherUser = computed(() => {
  if (chat.value?.type === 'private') return chat.value.other_user || null
  return null
})

const chatAvatar = computed(() => {
  if (chat.value?.type === 'private' && otherUser.value?.avatar) {
    return getAvatarUrl(otherUser.value.avatar)
  }
  return getAvatarUrl(chat.value?.avatar_url)
})

const getFileName = (url: string) => {
  if (!url) return 'Файл'
  try {
    return new URL(url).pathname.split('/').pop() || 'Файл'
  } catch {
    return url.split('/').pop() || 'Файл'
  }
}

const formatMessageTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const connectWebSocket = () => {
  const chatId = route.params.id
  console.log('WebSocket: chatId из route:', chatId, 'тип:', typeof chatId)
  
  if (!chatId || chatId === 'undefined') {
    console.error('Нет chatId для WebSocket')
    return
  }
  const token = localStorage.getItem('access_token') || localStorage.getItem('access_token')
  if (!token) return

  const wsUrl = `ws://localhost:8000/ws/chat/${chatId}/?token=${token}`
  console.log('Подключаемся к WebSocket:', wsUrl)
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    wsConnected.value = true
    reconnectAttempts.value = 0
  }
  
  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.action === 'init') {
        messages.value = data.messages || []
        await nextTick()
        scrollToBottom()
      } else if (data.action === 'new_message') {
        messages.value.push(data.message)
        await nextTick()
        scrollToBottom()
      } else if (data.action === 'typing_status') {
        if (data.user_id !== user.value?.id) {
          isOtherTyping.value = data.is_typing
        }
      } else if (data.action === 'user_online') {
        if (chat.value?.other_user?.id === data.user_id) {
          chat.value.other_user.is_online = data.is_online
        }
      }
    } catch (e) {
      console.error('WS message error:', e)
    }
  }
  
  ws.onclose = () => {
    wsConnected.value = false
    ws = null
    setTimeout(() => {
      reconnectAttempts.value++
      connectWebSocket()
    }, 3000)
  }
  
  ws.onerror = (error) => console.error('WS error:', error)
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

const sendTypingStart = () => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'typing_start', user_id: user.value?.id, username: user.value?.username }))
  }
}

const sendTypingStop = () => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'typing_stop', user_id: user.value?.id }))
  }
}

const handleTyping = () => {
  sendTypingStart()
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
  typingDebounceTimer = window.setTimeout(sendTypingStop, 3000)
}

const loadChat = async () => {
  try {
    const response = await apiClient.get(`/social/chats/${route.params.id}/`)
    if (response.data) {
      chat.value = response.data
      chat.value.type = (chat.value.user1 && chat.value.user2) ? 'private' : 'group'
    }
  } catch (error) {
    console.error('Chat load error:', error)
  }
}

const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (!text) return
  
  sending.value = true
  try {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'send_message', text }))
      newMessage.value = ''
      sendTypingStop()
    }
  } catch (error) {
    console.error('Send error:', error)
  } finally {
    sending.value = false
  }
}

const attachFile = () => fileInput.value?.click()

const handleFileSelect = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  
  sending.value = true
  try {
    const formData = new FormData()
    formData.append('media', file)
    formData.append('text', '')
    
    if (chat.value?.user1 && chat.value?.user2) {
      formData.append('private_chat', String(route.params.id))
    } else {
      formData.append('chat', String(route.params.id))
    }
    
    const response = await apiClient.post('/social/messages/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.data) {
      messages.value.push(response.data)
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('Upload error:', error)
  } finally {
    sending.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

onMounted(async () => {
  await loadChat()
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
})

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    disconnectWebSocket()
    messages.value = []
    loadChat()
    connectWebSocket()
  }
})
</script>

<style scoped>
.chat-detail-view { height: 90vh; background: var(--color-background); display: flex; flex-direction: column; }
.chat-header { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; background: var(--color-background-surface); border-bottom: 1px solid var(--color-border); flex-shrink: 0; }
.back-btn { background: none; border: none; font-size: 1.25rem; color: var(--color-text-secondary); cursor: pointer; padding: 0.25rem; }
.chat-avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: var(--color-accent); flex-shrink: 0; }
.chat-info { flex: 1; min-width: 0; display: flex; align-items: center; gap: 0.75rem; }
.chat-name { font-weight: 600; color: var(--color-text-primary); }
.chat-status, .chat-members { font-size: 0.8rem; color: var(--color-text-tertiary); display: flex; align-items: center; gap: 0.25rem; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.online { background: #4caf50; }
.status-dot.offline { background: #9e9e9e; }
.typing-indicator { display: inline-flex; gap: 2px; }
.typing-indicator .dot { width: 4px; height: 4px; border-radius: 50%; background: var(--color-text-tertiary); animation: typing 1s infinite; }
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
.info-btn { background: none; border: none; font-size: 1.25rem; cursor: pointer; opacity: 0;}
.header-actions { display: flex; gap: 0.5rem; }
.settings-btn { background: none; border: none; font-size: 1.25rem; cursor: pointer; padding: 0.25rem; }
.messages-container { flex: 1; overflow-y: auto; padding: 1rem; min-height: 0; }
.messages-list { display: flex; flex-direction: column; gap: 0.25rem; }
.message-item { display: flex; }
.message-item.own-message { justify-content: flex-end; }
.message-content { max-width: 70%; padding: 0.5rem; border-radius: 1rem; background: var(--color-background-surface); box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
.own-message .message-content { background: var(--color-accent); color: white; }
.message-text { word-wrap: break-word; }
.message-image { max-width: 100%; border-radius: 0.5rem; }
.message-time { font-size: 0.65rem; opacity: 0.7; margin-top: 0.15rem; }
.message-input-area { padding: 1rem; background: var(--color-background-surface); border-top: 1px solid var(--color-border); flex-shrink: 0; }
.message-form { display: flex; gap: 0.5rem; align-items: center; }
.message-input { flex: 1; padding: 1rem; border: 1px solid var(--color-border); border-radius: 1.5rem; outline: none; background: var(--color-background); color: var(--color-text-primary); height: 3.5rem; font-size: 1rem; }
.message-input:focus { border-color: var(--color-accent); }
.attach-btn, .send-btn { width: 44px; height: 44px; border: none; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.attach-btn { background: var(--color-background); }
.send-btn { background: var(--color-accent); color: white; }
.send-btn:disabled { opacity: 0.5; }
.ws-status { font-size: 0.75rem; color: #ff9800; text-align: center; padding-top: 0.25rem; }
.chat-info-sidebar { position: fixed; top: 0; right: 0; width: 280px; height: 100vh; background: var(--color-background-surface); box-shadow: -2px 0 10px rgba(0,0,0,0.1); z-index: 100; }
.sidebar-header { display: flex; justify-content: space-between; padding: 1rem; border-bottom: 1px solid var(--color-border); }
.close-btn { background: none; border: none; font-size: 1.25rem; cursor: pointer; }
.sidebar-content { padding: 1rem; }
.chat-avatar-large { text-align: center; margin-bottom: 1rem; }
.chat-avatar-large img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; }
.participants-list { margin-top: 1.5rem; }
.participant { padding: 0.5rem; border-radius: 0.5rem; }
.participant:hover { background: var(--color-background-active); }
.loading, .no-messages { text-align: center; padding: 2rem; color: var(--color-text-tertiary); }
</style>