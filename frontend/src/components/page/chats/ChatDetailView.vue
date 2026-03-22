<template>
  <div class="chat-detail-view">
    <!-- Франшизное обсуждение — отдельный рендер -->
    <FranchiseDiscussionChat
      v-if="isFranchiseDiscussion && franchiseParts.length > 0"
      :franchise-id="chat?.franchise_id"
      :franchise-name="chat?.name"
      :franchise-poster="franchisePosterUrl || chat?.avatar_url || ''"
      :parts="franchiseParts"
      :highlight-anime-id="highlightAnimeId"
    />

    <!-- Обычный чат -->
    <template v-else>
    <div class="chat-header">
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
        <button v-if="isGroup && canManageChat" @click="handleInvite" class="invite-btn" title="Пригласить участников">👥</button>
        <button @click="showSearch = true" class="search-btn" title="Поиск сообщений">🔍</button>
        <button @click="showChatInfo = !showChatInfo" class="info-btn" title="Информация о чате">⋮</button>
      </div>  
    </div>

    <div class="messages-container" ref="messagesContainer" :style="wallpaperStyle">
      <!-- Псевдоэлемент для размытого фона -->
      <div class="wallpaper-bg" :style="wallpaperBgStyle"></div>
      <!-- Панель закрепленных сообщений -->
      <div v-if="pinnedMessages.length > 0 && showPinnedBar" class="pinned-messages-bar">
        <span class="pinned-label">📌 Закреплено:</span>
        <div class="pinned-message-preview">
          {{ pinnedMessages[0].text || 'Медиа-сообщение' }}
        </div>
        <button @click="showPinnedBar = false" class="pinned-close">×</button>
      </div>

      <div v-if="loadingMessages" class="loading">Загрузка...</div>
      <div v-else-if="messages.length === 0" class="no-messages">Нет сообщений</div>
      <div v-else class="messages-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'own-message': message.sender_id === user?.id }]"
          :data-message-id="message.id"
          @contextmenu.prevent="showMessageMenu(message, $event)"
        >
          <div class="message-content">
            <!-- Имя отправителя для групповых чатов -->
            <div v-if="isGroup && message.sender_id !== user?.id" class="message-sender">
              {{ message.sender_username || 'Unknown' }}
            </div>

            <!-- Текст сообщения -->
            <div class="message-text" v-if="message.text">{{ message.text }}</div>
            
            <!-- Медиа -->
            <img v-if="message.media && message.media_type === 'image'" :src="message.media" class="message-image" />
            <div v-if="message.media && message.media_type !== 'image'" class="message-file">
              <a :href="message.media" target="_blank">📎 {{ getFileName(message.media) }}</a>
            </div>

            <!-- Реакции отображаются внутри блока сообщения -->
            <div v-if="getMessageReactions(message.id).length > 0" class="message-reactions">
              <span
                v-for="(reaction, idx) in getGroupedReactions(message.id)"
                :key="idx"
                class="reaction-badge"
                :class="{ 'reaction-collapsed': idx >= 4 }"
                @click.stop="handleReaction(message.id, reaction.emoji)"
              >
                {{ reaction.emoji }} {{ reaction.count }}
              </span>
            </div>

            <!-- Информация о сообщении: время и галочки -->
            <div class="message-footer" :class="{ 'own-footer': message.sender_id === user?.id }">
              <span v-if="message.is_pinned" class="message-pinned">📌</span>
              <span v-if="message.is_edited" class="message-edited">✏️</span>
              <span class="message-time">{{ formatMessageTime(message.created_at) }}</span>
              
              <!-- Статусы сообщения - ТОЛЬКО для своих сообщений -->
              <template v-if="message.sender_id === user?.id">
                <!-- Для личных чатов показываем статус прочтения -->
                <template v-if="chat?.type === 'private'">
                  <span 
                    v-if="message.is_read_by_other" 
                    class="message-status read" 
                    title="Прочитано"
                  >
                    ✓✓
                  </span>
                  <span 
                    v-else 
                    class="message-status sent" 
                    title="Отправлено"
                  >
                    ✓
                  </span>
                </template>
                
                <!-- Для групповых чатов показываем счётчик прочитавших (если есть) -->
                <template v-else-if="chat?.type === 'group'">
                  <span 
                    v-if="message.read_count && message.read_count > 0" 
                    class="message-status group-read" 
                    :title="`Прочитано ${message.read_count} ${pluralize(message.read_count, ['участником', 'участниками', 'участниками'])}`"
                  >
                    ✓{{ message.read_count }}
                  </span>
                  <span 
                    v-else 
                    class="message-status sent" 
                    title="Отправлено"
                  >
                    ✓
                  </span>
                </template>
              </template>
            </div>
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
      v-if="showSettings"
      :chat-id="Number(route.params.id)"
      :chat-type="chat?.type || 'group'"
      :is-owner="canManageChat"
      @close="showSettings = false"
      @settings-changed="handleSettingsChanged"
    />

    <!-- Модальное окно поиска сообщений -->
    <MessageSearchModal
      :is-open="showSearch"
      :chat-id="Number(route.params.id)"
      @close="showSearch = false"
      @message-selected="(id) => scrollToMessage(id)"
    />

    <!-- Модальное окно пересылки сообщений -->
    <ForwardMessageModal
      :is-open="showForward"
      :message="messageToForward"
      :available-chats="chatsForForward"
      @close="showForward = false"
      @forwarded="handleForwardComplete"
    />

    <!-- Модальное окно приглашений -->
    <ChatInviteModal
      :is-open="showInvite"
      :chat-id="Number(route.params.id)"
      @close="showInvite = false"
    />

    <!-- Контекстное меню сообщения + пикер реакций (единый блок) -->
    <div
      v-if="contextMenu.visible"
      class="message-actions-popup"
      :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
      @click.stop
    >
      <!-- Пикер реакций (всегда сверху) -->
      <div class="reaction-picker-container">
        <button
          v-for="emoji in reactionEmojis"
          :key="emoji"
          class="reaction-emoji-btn"
          @click="addReaction(emoji)"
        >
          {{ emoji }}
        </button>
      </div>
      
      <!-- Кнопки действий (всегда снизу) -->
      <div class="context-menu-actions">
        <button class="context-menu-item" @click="handleReply(selectedMessage)">
          <span class="context-menu-icon">↩️</span> Ответить
        </button>
        <button class="context-menu-item" @click="handleForward(selectedMessage)">
          <span class="context-menu-icon">↗️</span> Переслать
        </button>
        <button class="context-menu-item delete" v-if="selectedMessage?.sender_id === user?.id" @click="handleDelete(selectedMessage.id)">
          <span class="context-menu-icon">🗑️</span> Удалить
        </button>
      </div>
    </div>
    </template><!-- end v-else ordinary chat -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'
import { useAvatar } from '@/composables/useAvatar'
import ChatSettingsModal from '@/components/Chats/ChatSettingsModal.vue'
import FranchiseDiscussionChat from '@/components/Chats/FranchiseDiscussionChat.vue'
import MessageSearchModal from '@/components/modal/chats/MessageSearchModal.vue'
import ForwardMessageModal from '@/components/modal/chats/ForwardMessageModal.vue'
import ChatInviteModal from '@/components/modal/chats/ChatInviteModal.vue'
import { chatsApi } from '@/api/chats'
import apiClient, { getMediaUrl } from '@/api/client'

interface Props {
  chatId?: number
}
const props = defineProps<Props>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatExtrasStore = useChatExtrasStore()
const privateChatStore = usePrivateChatStore()
const groupChatStore = useGroupChatStore()
const { getAvatarUrl } = useAvatar()

const chat = ref<any>(null)
const messages = ref<any[]>([])
const loadingMessages = ref(false)
const sending = ref(false)
const showChatInfo = ref(false)
const showSettings = ref(false)
const showSearch = ref(false)
const showInvite = ref(false)
const showForward = ref(false)
const messageToForward = ref<any>(null)
const selectedMessage = ref<any>(null)
const showPinnedBar = ref(false)
const newMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const fileInput = ref<HTMLInputElement>()
const isOtherTyping = ref(false)
const wsConnected = ref(false)
const reconnectAttempts = ref(0)
const availableChats = ref<any[]>([])
const loadingChats = ref(false)
const currentWallpaper = ref<any>(null)
const currentTheme = ref<any>(null)

// Контекстное меню + пикер реакций (единый блок)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0
})

// Единая позиция для popup
const popupPosition = ref({ x: 0, y: 0 })

const reactionEmojis = ['👍', '❤️', '😢', '😮', '😡', '🎉', '🔥', '👀', '🙏']

// Computed для получения ID чата - из prop или route
const currentChatId = computed(() => {
  // Приоритет пропа, так как компонент может использоваться внутри ChatsView
  if (props.chatId) {
    return props.chatId
  }
  // Иначе берём из route
  const routeId = route.params.id
  if (routeId && routeId !== 'undefined') {
    return parseInt(routeId as string)
  }
  return undefined
})

let ws: WebSocket | null = null
let globalWs: WebSocket | null = null
let typingDebounceTimer: number | null = null
let messageObserver: IntersectionObserver | null = null
const readMessages = new Set<number>()

const user = computed(() => authStore.user)
const apiUrl = import.meta.env.VITE_API_URL || 'https://anisphere.ru'

const chatName = computed(() => {
  if (!chat.value) return 'Загрузка...'
  
  // Если есть кастомное название (для личных чатов оно приходит в name)
  if (chat.value.name && chat.value.type === 'private') {
    // name уже содержит custom_name если он есть
    const other = (chat.value as any).other_user 
    return chat.value.name || other?.display_name || other?.username || 'Личный чат'
  }
  
  if (chat.value.user1 && chat.value.user2) {
    // Личный чат без кастомного названия
    const other = (chat.value as any).other_user 
      || (chat.value.user1?.id === authStore.user?.id ? chat.value.user2 : chat.value.user1)
    return other?.display_name || other?.username || 'Личный чат'
  }
  // Для групп обсуждений показываем название аниме
  if (chat.value.type === 'group' && chat.value.anime_title) {
    return chat.value.anime_title
  }
  return chat.value.name || 'Групповой чат'
})

const otherUser = computed(() => {
  if (chat.value?.type === 'private') return (chat.value as any).other_user || null
  return null
})

const chatAvatar = computed(() => {
  // Если это группа обсуждения с аниме - используем постер аниме
  if (chat.value?.type === 'group' && chat.value.anime_poster) {
    return getMediaUrl(chat.value.anime_poster)
  }
  if (chat.value?.type === 'private' && otherUser.value?.avatar) {
    return getAvatarUrl(otherUser.value.avatar)
  }
  return getAvatarUrl(chat.value?.avatar_url)
})

const isGroup = computed(() => chat.value?.type === 'group')

// Франшизное обсуждение — групповой чат с franchise_id
const isFranchiseDiscussion = computed(() =>
  chat.value?.type === 'group' && !!chat.value?.franchise_id
)

const franchiseParts = ref<any[]>([])  // части франшизы для FranchiseDiscussionChat
const franchisePosterUrl = ref<string>('')
const highlightAnimeId = ref<number | undefined>(undefined)

// Загружаем данные франшизы через franchise-discussion/init/
const loadFranchiseParts = async () => {
  if (!isFranchiseDiscussion.value) return
  const franchiseId = chat.value?.franchise_id
  if (!franchiseId) return

  try {
    // Сначала получаем список аниме франшизы
    const { data: franchiseData } = await apiClient.get(`/anime/franchises/${franchiseId}/`)
    const animeIds: number[] = (franchiseData.entries || franchiseData.anime_list || franchiseData.parts || []).map((a: any) => a.id)

    // Инициализируем franchise discussion — получаем топики с постерами
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: franchiseId,
      anime_ids: animeIds,
    })

    // Строим parts из topics бэкенда (всё кроме general)
    franchiseParts.value = (data.topics || [])
      .filter((t: any) => t.anime_id !== null)
      .map((t: any) => ({
        id: t.anime_id,
        title_ru: t.title,
        title_en: t.title,
        franchise_order: t.order,
      }))

    if (data.franchise_poster) {
      franchisePosterUrl.value = data.franchise_poster
    }
  } catch {
    // Фолбек: показываем обычный чат если не удалось загрузить
    franchiseParts.value = []
  }
}

const canManageChat = computed(() => {
  if (!authStore.user || !isGroup.value) return false
  const isAdmin = chat.value?.admins?.some((a: any) => a.id === authStore.user?.id)
  const isCreator = chat.value?.created_by?.id === authStore.user?.id
  return isAdmin || isCreator
})

const pinnedMessages = computed(() => messages.value.filter(m => m.is_pinned))

// Функция для склонения слов (для групповых чатов)
const pluralize = (count: number, words: [string, string, string]) => {
  const cases = [2, 0, 1, 1, 1, 2];
  const mod10 = count % 10;
  const mod100 = count % 100;
  
  const caseIndex = mod100 > 4 && mod100 < 20 ? 2 : Math.min(mod10, 5);
  const index = cases[caseIndex] ?? 2; // если undefined, используем 2
  
  return words[index] ?? words[2]; // если индекс невалидный, используем последнее слово
}

const chatsForForward = computed(() => {
  if (!Array.isArray(availableChats.value)) return []
  const currentId = currentChatId.value
  return availableChats.value.filter(c => {
    // Исключаем текущий чат
    if (currentId && c.id === currentId) return false

    // Форматируем имя и тип для модального окна
    return {
      id: c.id,
      name: c.type === 'group' ? c.name : (c.other_user?.username || 'Чат'),
      avatar_url: c.type === 'group' ? c.avatar_url : c.other_user?.avatar,
      type: c.type
    }
  })
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
  const chatId = currentChatId.value
  console.log('WebSocket: chatId из route:', chatId, 'тип:', typeof chatId)
  
  if (!chatId) {
    console.error('Нет chatId для WebSocket')
    return
  }
  const token = localStorage.getItem('access_token') || localStorage.getItem('access_token')
  if (!token) return

  // Используем правильный протокол (ws или wss)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/chat/${chatId}/?token=${token}`
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
        console.log('WS init: user.id =', user.value?.id, 'messages count =', data.messages?.length)
        
        // Просто сохраняем сообщения как есть, без принудительной пометки
        messages.value = data.messages || []
        
        await nextTick()
        scrollToBottom()
        
        // Наблюдаем за новыми сообщениями
        setupMessageObserver()
      } else if (data.action === 'new_message') {
        // Добавляем новое сообщение
        messages.value.push(data.message)
        messages.value = [...messages.value]
        await nextTick()
        scrollToBottom()
        
        // Если сообщение от другого пользователя и чат открыт - отмечаем как прочитанное
        if (data.message.sender_id !== user.value?.id) {
          await markMessagesAsRead([data.message.id])
        }
        
        // Обновить observer для нового сообщения
        nextTick(() => setupMessageObserver())
        
        // Обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'messages_read') {
        // Кто-то прочитал сообщения
        console.log('Messages read event:', data)
        
        // Обновляем статусы прочитанных сообщений
        if (data.message_ids && data.message_ids.length > 0) {
          const updatedMessages = messages.value.map(msg => {
            if (data.message_ids.includes(msg.id)) {
              return { ...msg, is_read_by_other: true }
            }
            return msg
          })
          messages.value = updatedMessages
        }
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

const connectGlobalWebSocket = () => {
  const token = localStorage.getItem('access_token')
  if (!token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/global/?token=${token}`
  
  globalWs = new WebSocket(wsUrl)
  
  globalWs.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.action === 'chat_created') {
        // Новый чат создан - перезагрузим список
        privateChatStore.loadChats()
        // Если это текущий чат, обновим данные
        const newChatId = data.chat?.chat_id
        if (newChatId && newChatId == route.params.id) {
          loadChat()
        }
      } else if (data.action === 'chat_deleted') {
        // Чат удалён - перезагрузим список
        privateChatStore.loadChats()
      } else if (data.action === 'user_online') {
        // Обновить статус онлайн
        if (chat.value?.other_user?.id === data.user_id) {
          chat.value.other_user.is_online = true
        }
      } else if (data.action === 'user_offline') {
        // Обновить статус офлайн
        if (chat.value?.other_user?.id === data.user_id) {
          chat.value.other_user.is_online = false
        }
      } else if (data.action === 'user_typing') {
        // Показываем индикатор печати
        if (data.chat_id == route.params.id && data.user_id !== user.value?.id) {
          isOtherTyping.value = data.is_typing
        }
      } else if (data.action === 'new_message') {
        // Новое сообщение в чате
        if (data.message?.chat_id == route.params.id) {
          messages.value.push(data.message)
          nextTick(() => scrollToBottom())
        }
        // Обновить непрочитанные и списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'unread_updated') {
        // Обновить счётчик непрочитанных
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'message_sent') {
        // Сообщение отправлено - обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'unread_count_updated') {
        // Обновить счётчик непрочитанных
        privateChatStore.loadChats()
      }
    } catch (e) {
      console.error('Global WS error:', e)
    }
  }
    
  globalWs.onclose = () => {
    setTimeout(connectGlobalWebSocket, 5000)
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
  const chatId = currentChatId.value
  if (!chatId) {
    console.warn('Нет chatId для загрузки чата')
    return
  }
  try {
    const response = await apiClient.get(`/social/chats/${chatId}/`)
    if (response.data) {
      chat.value = response.data
      chat.value.type = (chat.value.user1 && chat.value.user2) ? 'private' : 'group'
      
      // Загружаем обои и тему параллельно
      const chatType = chat.value.type
      try {
        const [wallpaperRes, themeRes] = await Promise.allSettled([
          apiClient.get(`/social/chat-settings/${chatType}/${chatId}/wallpaper/`),
          apiClient.get(`/social/chat-settings/${chatType}/${chatId}/theme/`)
        ])
        
        if (wallpaperRes.status === 'fulfilled' && wallpaperRes.value.data?.wallpaper) {
          currentWallpaper.value = wallpaperRes.value.data.wallpaper
        }
        
        if (themeRes.status === 'fulfilled' && themeRes.value.data?.theme) {
          currentTheme.value = themeRes.value.data.theme
          applyThemeToDom(themeRes.value.data.theme)
        }
      } catch (e) {
        console.log('Error loading chat settings:', e)
      }
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
      
      // Обновить список чатов после отправки
      privateChatStore.loadChats()
      groupChatStore.loadGroupChats()
      chatExtrasStore.loadUnreadChats()
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

// Reactions
const handleReaction = async (messageId: number, emoji: string) => {
  try {
    await chatExtrasStore.toggleReaction(messageId, emoji)
  } catch (error) {
    console.error('Reaction error:', error)
  }
}

const getMessageReactions = (messageId: number) => {
  return chatExtrasStore.getReactionsForMessage(messageId)
}

const getReactionCount = (messageId: number, emoji: string) => {
  return chatExtrasStore.getReactionCount(messageId, emoji)
}

// Pinned Messages
const togglePinMessage = async (message: any) => {
  try {
    if (message.is_pinned) {
      await chatExtrasStore.unpinMessage(message.id)
      message.is_pinned = false
    } else {
      await chatExtrasStore.pinMessage(message.id)
      message.is_pinned = true
    }
  } catch (error) {
    console.error('Pin error:', error)
  }
}

// Message Actions
const handleReply = (message: any) => {
  newMessage.value = `↩️ ${message.text || ''} `
  ;(document.querySelector('.message-input') as HTMLInputElement)?.focus()
}

const handleForward = (message: any) => {
  messageToForward.value = message
  showForward.value = true
}

const handleDelete = async (messageId: number) => {
  if (!confirm('Удалить сообщение?')) return
  
  try {
    await apiClient.delete(`/social/messages/${messageId}/`)
    messages.value = messages.value.filter(m => m.id !== messageId)
  } catch (error) {
    console.error('Delete error:', error)
  }
}

const showMessageMenu = (message: any, event: MouseEvent) => {
  event.preventDefault()
  selectedMessage.value = message
  
  const messageEl = (event.target as HTMLElement).closest('.message-content')
  if (!messageEl) return
  
  const messageRect = messageEl.getBoundingClientRect()
  const isOwnMessage = message.sender_id === user.value?.id
  
  const popupWidth = 180
  const popupHeight = 130
  
  const screenWidth = window.innerWidth
  const screenHeight = window.innerHeight
  
  let baseX: number
  let baseY = messageRect.top
  
  if (isOwnMessage) {
    baseX = messageRect.right + 12
  } else {
    baseX = messageRect.left - popupWidth - 12
  }
  
  if (baseX + popupWidth > screenWidth - 15) {
    baseX = screenWidth - popupWidth - 15
  }
  if (baseX < 15) {
    baseX = 15
  }
  
  if (baseY + popupHeight > screenHeight - 15) {
    baseY = messageRect.bottom - popupHeight - 8
    if (baseY < 15) {
      baseY = 15
    }
  }
  
  popupPosition.value = { x: baseX, y: baseY }
  contextMenu.value.visible = true
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

const addReaction = async (emoji: string) => {
  if (selectedMessage.value) {
    await handleReaction(selectedMessage.value.id, emoji)
  }
  contextMenu.value.visible = false
}

// Invite
const handleInvite = () => {
  showInvite.value = true
}

const handleForwardComplete = () => {
  showForward.value = false
  messageToForward.value = null
}

// Сгруппировать реакции
const getGroupedReactions = (messageId: number): { emoji: string; count: number }[] => {
  const reactions = getMessageReactions(messageId)
  const grouped: Record<string, { emoji: string; count: number }> = {}
  
  reactions.forEach(r => {
    const emoji = r.emoji
    if (!grouped[emoji]) {
      grouped[emoji] = { emoji, count: 0 }
    }
    grouped[emoji]!.count++
  })
  
  const values = Object.values(grouped)
  return values as { emoji: string; count: number }[]
}

// Прокрутка к сообщению
const scrollToMessage = (messageId: number) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`) as HTMLElement | null
  if (!messageElement) return

  messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  messageElement.classList.add('highlighted')
  setTimeout(() => {
    messageElement.classList.remove('highlighted')
  }, 2000)
}

// Обработка изменений настроек
const handleSettingsChanged = async (data: any) => {
  console.log('Settings changed:', data)
  
  if (data?.type === 'wallpaper') {
    // Перезагружаем обои с сервера для получения актуальных данных
    await loadWallpaper()
  } else if (data?.type === 'theme') {
    // Перезагружаем тему
    await loadTheme()
  } else if (data?.type === 'organize') {
    // Обновляем настройки организации
    await loadChat()
  } else if (data?.type === 'clear' || data?.type === 'restore') {
    messages.value = []
  } else if (data?.type === 'leave' || data?.type === 'delete') {
    router.push('/chats')
  }
}

// Загрузка обоев
const loadWallpaper = async () => {
  const chatId = currentChatId.value
  if (!chatId || !chat.value) return
  
  try {
    const chatType = chat.value.type
    const response = await apiClient.get(`/social/chat-settings/${chatType}/${chatId}/wallpaper/`)
    const data = response.data as any
    
    if (data?.wallpaper) {
      currentWallpaper.value = data.wallpaper
      console.log('Wallpaper loaded:', currentWallpaper.value)
    } else {
      currentWallpaper.value = null
    }
  } catch (error) {
    console.log('No wallpaper for this chat')
    currentWallpaper.value = null
  }
}

// Загрузка темы
const loadTheme = async () => {
  const chatId = currentChatId.value
  if (!chatId || !chat.value) return
  
  try {
    const chatType = chat.value.type
    const response = await apiClient.get(`/social/chat-settings/${chatType}/${chatId}/theme/`)
    const data = response.data as any
    
    if (data?.theme) {
      currentTheme.value = data.theme
      applyThemeToDom(data.theme)
    } else {
      currentTheme.value = null
    }
  } catch (error) {
    console.log('No theme for this chat')
    currentTheme.value = null
  }
}

// Применение темы к DOM
const applyThemeToDom = (theme: any) => {
  if (!theme) return
  const chatId = currentChatId.value
  const root = document.documentElement
  
  // Цвета сообщений
  if (theme.message_color_mine) root.style.setProperty(`--chat-msg-mine-bg`, theme.message_color_mine)
  if (theme.message_color_other) root.style.setProperty(`--chat-msg-other-bg`, theme.message_color_other)
  if (theme.message_text_color_mine) root.style.setProperty(`--chat-msg-mine-text`, theme.message_text_color_mine)
  if (theme.message_text_color_other) root.style.setProperty(`--chat-msg-other-text`, theme.message_text_color_other)
  
  // Шрифт
  if (theme.font_size_px) root.style.setProperty(`--chat-font-size`, theme.font_size_px + 'px')
  if (theme.font_family) root.style.setProperty(`--chat-font-family`, theme.font_family)
  if (theme.font_weight) root.style.setProperty(`--chat-font-weight`, theme.font_weight)
  
  // Пузыри
  if (theme.bubble_border_radius) root.style.setProperty(`--chat-bubble-radius`, theme.bubble_border_radius + 'px')
  if (theme.bubble_shadow !== undefined) root.style.setProperty(`--chat-bubble-shadow`, theme.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none')
  
  // Интерфейс
  if (theme.background_color) root.style.setProperty(`--chat-bg`, theme.background_color)
  if (theme.header_color) root.style.setProperty(`--chat-header-bg`, theme.header_color)
  if (theme.input_color) root.style.setProperty(`--chat-input-bg`, theme.input_color)
  if (theme.accent_color) root.style.setProperty(`--chat-accent`, theme.accent_color)
}

// Стили обоев - blur применяется к псевдоэлементу, а не к контейнеру
const wallpaperStyle = computed(() => {
  if (!currentWallpaper.value) return {}
  
  const wp = currentWallpaper.value as any
  
  if (wp.wallpaper_type === 'solid') {
    return {
      '--wp-bg': wp.wallpaper_color || '#0f0f1a',
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  } else if (wp.wallpaper_type === 'gradient') {
    const angle = wp.gradient_angle || 135
    const color1 = wp.wallpaper_color || '#1a1a2e'
    const color2 = wp.wallpaper_color2 || '#0f0f1a'
    return {
      '--wp-bg': `linear-gradient(${angle}deg, ${color1}, ${color2})`,
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  } else if (wp.wallpaper_type === 'image') {
    const imageUrl = wp.wallpaper_image_url || wp.wallpaper_image
    if (imageUrl) {
      const blur = wp.wallpaper_blur ?? 0
      const intensity = (wp.wallpaper_intensity ?? 100) / 100
      return {
        '--wp-bg': `url(${imageUrl})`,
        '--wp-blur': `${blur}px`,
        '--wp-intensity': String(intensity)
      }
    }
  } else if (wp.wallpaper_type === 'pattern') {
    return {
      '--wp-bg': wp.wallpaper_color || '#0f0f1a',
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  }
  
  return {}
})

// Стили для фонового псевдоэлемента с blur
const wallpaperBgStyle = computed(() => {
  if (!currentWallpaper.value) return {}
  
  const wp = currentWallpaper.value as any
  const blur = wp.wallpaper_blur ?? 0
  const intensity = (wp.wallpaper_intensity ?? 100) / 100
  
  if (wp.wallpaper_type === 'image') {
    const imageUrl = wp.wallpaper_image_url || wp.wallpaper_image
    if (imageUrl) {
      return {
        backgroundImage: `url(${imageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        filter: blur > 0 ? `blur(${blur}px) brightness(${intensity})` : `brightness(${intensity})`
      }
    }
  } else if (wp.wallpaper_type === 'gradient') {
    const angle = wp.gradient_angle || 135
    const color1 = wp.wallpaper_color || '#1a1a2e'
    const color2 = wp.wallpaper_color2 || '#0f0f1a'
    return {
      background: `linear-gradient(${angle}deg, ${color1}, ${color2})`
    }
  } else if (wp.wallpaper_type === 'solid') {
    return {
      background: wp.wallpaper_color || '#0f0f1a'
    }
  }
  
  return {}
})

// Загрузка списка чатов для пересылки
const loadChatsList = async () => {
  loadingChats.value = true
  try {
    const response = await chatsApi.list()
    availableChats.value = (response as any).results || response
  } catch (error) {
    console.error('Error loading chats list:', error)
  } finally {
    loadingChats.value = false
  }
}

// Отметить конкретные сообщения как прочитанные
const markMessagesAsRead = async (messageIds: number[]) => {
  if (!messageIds.length) return
  
  try {
    const chatId = route.params.id
    const chatType = chat.value?.type
    const endpoint = chatType === 'private'
      ? `/social/private-chats/${chatId}/mark_as_read/`
      : `/social/group-chats/${chatId}/mark_as_read/`
    
    // Отправляем IDs сообщений, которые нужно отметить
    await apiClient.post(endpoint, { message_ids: messageIds })
    
    // Обновляем статусы в локальном массиве
    const updatedMessages = messages.value.map(msg => {
      if (messageIds.includes(msg.id)) {
        return { ...msg, is_read_by_other: true }
      }
      return msg
    })
    messages.value = updatedMessages
    
  } catch (e) {
    console.log('Error marking messages as read:', e)
  }
}

// Автоматическое отметка сообщений как прочитанных при скролле
const setupMessageObserver = () => {
  if (!messagesContainer.value) return
  
  // Очищаем предыдущий observer
  if (messageObserver) {
    messageObserver.disconnect()
  }
  
  messageObserver = new IntersectionObserver(
    (entries) => {
      // Собираем IDs сообщений, которые стали видимыми
      const visibleMessageIds: number[] = []
      
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const messageEl = entry.target as HTMLElement
          const messageId = parseInt(messageEl.dataset.messageId || '0')
          const message = messages.value.find(m => m.id === messageId)
          
          // Отмечаем только сообщения от других пользователей, которые ещё не прочитаны
          if (message && 
              message.sender_id !== user.value?.id && 
              !message.is_read_by_other && 
              !readMessages.has(messageId)) {
            
            readMessages.add(messageId)
            visibleMessageIds.push(messageId)
          }
        }
      })
      
      // Отправляем запрос на отметку всех видимых сообщений
      if (visibleMessageIds.length > 0) {
        markMessagesAsRead(visibleMessageIds)
      }
    },
    {
      root: messagesContainer.value,
      threshold: 0.3 // Сообщение должно быть видно на 30%
    }
  )
  
  // Наблюдаем за всеми сообщениями
  nextTick(() => {
    const messageElements = messagesContainer.value?.querySelectorAll('.message-item')
    messageElements?.forEach((el) => {
      messageObserver?.observe(el)
    })
  })
}

onMounted(async () => {
  document.addEventListener('click', closeContextMenu)
  
  const chatId = currentChatId.value
  if (chatId) {
    await loadChat()
    await loadFranchiseParts()
    connectWebSocket()
    
    try {
      const chatType = chat.value?.type
      const endpoint = chatType === 'private'
        ? `/social/private-chats/${chatId}/mark_as_read/`
        : `/social/group-chats/${chatId}/mark_as_read/`
      await apiClient.post(endpoint)
    } catch (e) {
      console.error('Error marking all as read:', e)
    }
    
    nextTick(() => { setupMessageObserver() })
  }
  connectGlobalWebSocket()
  loadChatsList()
  chatExtrasStore.loadUnreadChats()
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
  disconnectWebSocket()
  if (globalWs) {
    globalWs.close()
    globalWs = null
  }
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
  if (messageObserver) {
    messageObserver.disconnect()
    messageObserver = null
  }
  readMessages.clear()
})

// Следим за изменением prop.chatId (ChatsView) или route.params.id
watch(currentChatId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    disconnectWebSocket()
    messages.value = []
    readMessages.clear()
    await loadChat()
    connectWebSocket()
    
    try {
      const chatType = chat.value?.type
      const endpoint = chatType === 'private'
        ? `/social/private-chats/${newId}/mark_as_read/`
        : `/social/group-chats/${newId}/mark_as_read/`
      await apiClient.post(endpoint)
    } catch (e) {
      console.error('Error marking all as read:', e)
    }
  }
})
</script>

<style scoped>
/* Стили остаются без изменений */
.chat-detail-view {
  height: 90vh;
  background: #0f0f0f;
  display: flex;
  flex-direction: column;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.back-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #888;
  cursor: pointer;
  padding: 0.25rem;
}
.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #7c4dff;
  flex-shrink: 0;
}
.chat-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.chat-name {
  font-weight: 600;
  color: #e0e0e0;
}
.chat-status, .chat-members {
  font-size: 0.8rem;
  color: #888;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-dot.online { background: #4caf50; }
.status-dot.offline { background: #666; }
.typing-indicator {
  display: inline-flex;
  gap: 2px;
}
.typing-indicator .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #888;
  animation: typing 1s infinite;
}
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
.info-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  top: 5px;
  cursor: pointer;
  opacity: 100;
  transform: translateY(-5px);
  color: #888;
}
.header-actions { display: flex; gap: 0.5rem; }
.settings-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  color: #888;
}
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  min-height: 0;
  background: var(--chat-bg, #0f0f0f);
  position: relative;
}

/* Псевдоэлемент для размытого фона обоев */
.wallpaper-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

/* Контент сообщений поверх фона */
.messages-container > *:not(.wallpaper-bg) {
  position: relative;
  z-index: 1;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.message-item {
  display: flex;
}
.message-item.own-message {
  justify-content: flex-end;
}
.message-content {
  max-width: 70%;
  padding: 0.5rem 0.75rem;
  border-radius: var(--chat-bubble-radius, 1rem);
  background: var(--chat-msg-other-bg, #2d2d2d);
  color: var(--chat-msg-other-text, #ffffff);
  box-shadow: var(--chat-bubble-shadow, 0 1px 2px rgba(0, 0, 0, 0.4));
  font-size: var(--chat-font-size, 14px);
  font-family: var(--chat-font-family, system-ui);
}
.own-message .message-content {
  background: var(--chat-msg-mine-bg, #1e7cff);
  color: var(--chat-msg-mine-text, #fff);
}
.message-text {
  word-wrap: break-word;
  color: inherit;
  line-height: 1.4;
}
.message-image {
  max-width: 100%;
  border-radius: 0.5rem;
}
.message-file a {
  color: #7c4dff;
  text-decoration: none;
}
.message-file a:hover {
  text-decoration: underline;
}
.message-time {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 0.15rem;
  color: #000000 !important;
}
.own-message .message-time {
  color: #000000 !important;
}
.message-input-area {
  padding: 1rem;
  background: #1a1a1a;
  border-top: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.message-form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.message-input {
  flex: 1;
  padding: 1rem;
  border: 1px solid #2a2a2a;
  border-radius: 1.5rem;
  outline: none;
  background: #0f0f0f;
  color: #ffffff;
  height: 3.5rem;
  font-size: 1rem;
}
.message-input:focus {
  border-color: #7c4dff;
}
.message-input::placeholder {
  color: #666;
}
.attach-btn, .send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.attach-btn {
  background: #0f0f0f;
  color: #888;
}
.send-btn {
  background: #7c4dff;
  color: white;
}
.send-btn:disabled { opacity: 0.5; }
.ws-status {
  font-size: 0.75rem;
  color: #ff9800;
  text-align: center;
  padding-top: 0.25rem;
}
.chat-info-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 280px;
  height: 100vh;
  background: #1a1a1a;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.4);
  z-index: 100;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #2a2a2a;
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #888;
}
.sidebar-content { padding: 1rem; }
.sidebar-content h3,
.sidebar-content h4,
.sidebar-content h5,
.sidebar-content p {
  color: #e0e0e0;
}
.chat-avatar-large {
  text-align: center;
  margin-bottom: 1rem;
}
.chat-avatar-large img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
}
.participants-list { margin-top: 1.5rem; }
.participants-list h5 {
  color: #888;
  margin-bottom: 0.5rem;
}
.participant {
  padding: 0.5rem;
  border-radius: 0.5rem;
  color: #e0e0e0;
}
.participant:hover {
  background: rgba(255, 255, 255, 0.08);
}
.loading, .no-messages {
  text-align: center;
  padding: 2rem;
  color: #888;
}

/* Закрепленные сообщения */
.pinned-messages-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 193, 7, 0.12);
  border-bottom: 1px solid #2a2a2a;
  font-size: 0.875rem;
}
.pinned-label {
  color: #ffc107;
  font-weight: 500;
}
.pinned-message-preview {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #aaa;
}
.pinned-close {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0;
}

/* Сообщения */
.message-sender {
  font-size: 0.75rem;
  color: #7c4dff;
  margin-bottom: 0.25rem;
  font-weight: 500;
}
.message-footer {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.65rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}
.message-footer.own-footer {
  justify-content: flex-end;
}
.message-status {
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.25rem;
}
.message-status.sent {
  color: #000000 !important;
}
.message-status.read {
  color: #000000 !important;
}
.message-status.group-read {
  color: #000000 !important;
}
.message-pinned, .message-edited {
  font-size: 0.75rem;
}
.message-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.35rem;
  margin-bottom: 0.25rem;
  max-width: calc(100% - 80px);
  padding-bottom: 0.25rem;
}
.message-actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}
.message-item:hover .message-actions {
  opacity: 1;
}
.action-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.75rem;
  color: #e0e0e0;
  transition: background 0.2s, border-color 0.2s;
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
}
.action-btn.delete-btn:hover {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.4);
  color: #ff6b6b;
}

/* Кнопки заголовка */
.invite-btn, .search-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.25rem;
  color: #888;
  transition: color 0.2s;
}
.invite-btn:hover, .search-btn:hover {
  color: #e0e0e0;
}

/* Подсветка сообщения */
.message-item.highlighted {
  background: rgba(124, 77, 255, 0.15);
  animation: highlight-pulse 2s ease-out;
}
@keyframes highlight-pulse {
  0%, 100% { background: rgba(124, 77, 255, 0.15); }
  50% { background: rgba(124, 77, 255, 0.25); }
}

/* Скрытый input для файлов */
.file-input {
  display: none;
}

/* Прокрутка */
.messages-container::-webkit-scrollbar {
  width: 6px;
}
.messages-container::-webkit-scrollbar-track {
  background: #0f0f0f;
}
.messages-container::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
}
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #444;
}

.context-menu {
  position: fixed;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 0.5rem;
  padding: 0.25rem;
  z-index: 1000;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  background: none;
  color: #e0e0e0;
  font-size: 0.875rem;
  cursor: pointer;
  border-radius: 0.25rem;
  text-align: left;
  transition: background 0.15s;
}

.context-menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.context-menu-item.delete:hover {
  background: rgba(244, 67, 54, 0.2);
  color: #ff6b6b;
}

.context-menu-icon {
  font-size: 1rem;
}

/* Пикер реакций */
.reaction-picker {
  position: fixed;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 1rem;
  padding: 0.5rem;
  display: flex;
  gap: 0.25rem;
  z-index: 999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.reaction-emoji-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: 0.25rem;
  transition: background 0.15s, transform 0.1s;
}

.reaction-emoji-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: scale(1.2);
}

/* Единый popup с реакциями и контекстным меню */
.message-actions-popup {
  position: fixed;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 0.75rem;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.reaction-picker-container {
  display: flex;
  gap: 0.15rem;
  padding: 0.5rem;
  background: #252525;
  border-bottom: 1px solid #3a3a3a;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 200px;
}

.reaction-picker-container .reaction-emoji-btn {
  font-size: 1.25rem;
  padding: 0.3rem;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 0.35rem;
  transition: background 0.15s, transform 0.1s;
}

.reaction-picker-container .reaction-emoji-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: scale(1.25);
}

.context-menu-actions {
  display: flex;
  flex-direction: column;
  padding: 0.25rem;
}

.context-menu-actions .context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: none;
  background: none;
  color: #ffffff;
  font-size: 0.875rem;
  cursor: pointer;
  border-radius: 0.35rem;
  text-align: left;
  transition: background 0.15s;
}

.context-menu-actions .context-menu-item:hover {
  background: rgba(255, 255, 255, 0.12);
}

.context-menu-actions .context-menu-item.delete:hover {
  background: rgba(244, 67, 54, 0.25);
  color: #ff6b6b;
}

.context-menu-actions .context-menu-icon {
  font-size: 1rem;
}
</style>