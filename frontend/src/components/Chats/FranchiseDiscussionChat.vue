<template>
  <div class="franchise-chat">
    <!-- Шапка чата - как в обычном чате -->
    <div class="chat-header">
      <div class="chat-info">
        <button @click="showSettings = true" title="Настройки чата">
          <img v-if="franchisePosterResolved" :src="franchisePosterResolved" class="chat-avatar" :alt="franchiseName" @error="posterError = true" />
          <div v-else class="chat-avatar chat-avatar-placeholder"> <SakuraIcon name="play" /> </div>
        </button>
        <div class="chat-details">
          <h2 class="chat-name">{{ franchiseName }}</h2>
          <div class="chat-members">{{ topics.length }} {{ topicsWord(topics.length) }}</div>
        </div>
      </div>
      <div class="header-actions">
        <button @click="showSearch = true" class="search-btn" title="Поиск сообщений"> <SakuraIcon name="search" /> </button>
        <button @click="showTopics = !showTopics" class="topics-btn" :title="showTopics ? 'Скрыть темы' : 'Показать темы'"> <SakuraIcon name="clipboard" /> </button>
        <button @click="showSettings = true" class="settings-btn" title="Настройки">⋮</button>
      </div>
    </div>

    <!-- Панель тем (топиков) -->
    <div v-show="showTopics" class="topics-panel">
      <div class="topics-list">
        <button
          v-for="topic in topics"
          :key="topic.id"
          :class="['topic-item', { active: activeTopic?.id === topic.id }]"
          @click="selectTopic(topic)"
        >
          <div class="topic-poster-wrap">
            <img
              v-if="topic.poster_url && !topicPosterErrors[topic.id]"
              :src="topic.poster_url"
              class="topic-poster"
              :alt="topic.name"
              @error="topicPosterErrors[topic.id] = true"
            />
            <div v-else class="topic-poster topic-poster-fallback">
              {{ topic.animeId ? '<SakuraIcon name="tv" />' : '<SakuraIcon name="message" />' }}
            </div>
          </div>
          <div class="topic-info">
            <span class="topic-name">{{ topic.name }}</span>
            <span v-if="topic.unread > 0" class="topic-badge">{{ topic.unread }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Сообщения - полная копия стилей из ChatDetailView -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="loadingMessages" class="loading">Загрузка...</div>
      <div v-else-if="messages.length === 0" class="no-messages">
        <SakuraIcon name="message" :size="48" />
        <p>Начните обсуждение в теме «{{ activeTopic?.name }}»</p>
      </div>
      <div v-else class="messages-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'own-message': message.sender_id === currentUserId }]"
          :data-message-id="message.id"
          @contextmenu.prevent="showMessageMenu(message, $event)"
        >
          <div class="message-content">
            <!-- Имя отправителя для групповых чатов -->
            <div v-if="message.sender_id !== currentUserId" class="message-sender">
              {{ message.sender_username || 'Unknown' }}
            </div>

            <!-- Текст сообщения -->
            <div class="message-text" v-if="message.text">{{ message.text }}</div>

            <!-- Медиа -->
            <img v-if="message.media && message.media_type === 'image'" :src="message.media" class="message-image" />
            <div v-if="message.media && message.media_type !== 'image'" class="message-file">
              <a :href="message.media" target="_blank">📎 {{ getFileName(message.media) }}</a>
            </div>

            <!-- Реакции -->
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

            <!-- Информация о сообщении: время -->
            <div class="message-footer" :class="{ 'own-footer': message.sender_id === currentUserId }">
              <span class="message-time">{{ formatTime(message.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Ввод сообщения - как в обычном чате -->
    <div class="message-input-area">
      <!-- Превью ответа -->
      <div v-if="replyToMessage" class="reply-preview">
        <div class="reply-preview-content">
          <span class="reply-author">↩ {{ replyToMessage.sender_username || 'Пользователь' }}</span>
          <span class="reply-text">{{ (replyToMessage.text || '').substring(0, 80) }}</span>
        </div>
        <button @click="cancelReply" class="reply-cancel">✕</button>
      </div>
      
      <div class="topic-label">
        <SakuraIcon name="clipboard" :size="14" /> Тема: <strong>{{ activeTopic?.name }}</strong>
      </div>
      <form @submit.prevent="sendMessage" class="message-form">
        <input v-model="newMessage" type="text" :placeholder="`Написать в «${activeTopic?.name}»...`" class="message-input" :disabled="sending || !wsConnected" @input="handleTyping" />
        <input ref="fileInput" type="file" @change="handleFileSelect" style="display:none" accept="image/*,video/*,audio/*,.pdf,.doc*" />
        <button type="button" @click="attachFile" class="attach-btn" :disabled="sending || !wsConnected">📎</button>
        <button type="submit" class="send-btn" :disabled="(!newMessage.trim() && !replyToMessage) || sending || !wsConnected">
          <SakuraIcon name="send" :size="18" />
        </button>
      </form>
      <div v-if="!wsConnected && reconnectAttempts > 0" class="ws-status">
        Переподключение... ({{ reconnectAttempts }})
      </div>
    </div>

    <!-- Контекстное меню сообщения + пикер реакций -->
    <div
      v-if="contextMenu.visible"
      class="message-actions-popup"
      :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
      @click.stop
    >
      <!-- Пикер реакций -->
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

      <!-- Кнопки действий -->
      <div class="context-menu-actions">
        <button v-if="selectedMessage" class="context-menu-item" @click="handleReply(selectedMessage)">
          <span class="context-menu-icon">↩️</span> Ответить
        </button>
        <button v-if="selectedMessage" class="context-menu-item" @click="handleForward(selectedMessage)">
          <span class="context-menu-icon"> <SakuraIcon name="arrow-up-right" /> </span> Переслать
        </button>
        <button v-if="selectedMessage && selectedMessage.sender_id === currentUserId" class="context-menu-item delete" @click="handleDelete(selectedMessage.id)">
          <span class="context-menu-icon"> <SakuraIcon name="trash" /> </span> Удалить
        </button>
      </div>
    </div>

    <!-- Модальное окно настроек -->
    <ChatSettingsModal
      v-if="showSettings && chatGroupId"
      :chat-id="chatGroupId"
      chat-type="group"
      :chat-name="franchiseName"
      :chat-avatar="franchisePosterResolved || ''"
      :is-owner="false"
      @close="showSettings = false"
      @settings-changed="handleSettingsChanged"
    />

    <!-- Модальное окно поиска -->
    <MessageSearchModal
      :is-open="showSearch"
      :chat-id="chatGroupId || 0"
      @close="showSearch = false"
      @message-selected="(id) => scrollToMessage(id)"
    />

    <!-- Модальное окно пересылки -->
    <ForwardMessageModal
      :is-open="showForward"
      :message="messageToForward"
      :available-chats="chatsForForward"
      @close="showForward = false"
      @forwarded="handleForwardComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useChatExtrasStore } from '@/stores/chatExtras'
import ChatSettingsModal from './ChatSettingsModal.vue'
import MessageSearchModal from '@/components/modal/chats/MessageSearchModal.vue'
import ForwardMessageModal from '@/components/modal/chats/ForwardMessageModal.vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

interface FranchisePart {
  id: number
  title_ru: string
  title_en: string
  franchise_order: number
}

interface Topic {
  id: number
  name: string
  poster_url: string | null
  animeId: number | null
  unread: number
  slug: string
}

interface Message {
  id: number
  sender_id: number
  sender_username: string
  sender_avatar: string | null
  text: string
  media?: string
  media_type?: string
  created_at: string
  topic_id: number | null
}

const props = defineProps<{
  franchiseId: number
  franchiseSlug?: string | null
  franchiseName: string
  franchisePoster?: string
  parts: FranchisePart[]
  initialTopicSlug?: string | null
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const chatExtrasStore = useChatExtrasStore()
const currentUserId = computed(() => authStore.user?.id)

// ── State ──────────────────────────────────────────────────
const topics = ref<Topic[]>([])
const activeTopic = ref<Topic | null>(null)
const messages = ref<Message[]>([])
const loadingMessages = ref(false)
const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const posterError = ref(false)
const topicPosterErrors = reactive<Record<number, boolean>>({})
const chatGroupId = ref<number | null>(null)
const showTopics = ref(true)
const showSettings = ref(false)
const showSearch = ref(false)
const showForward = ref(false)
const messageToForward = ref<Message | null>(null)
const selectedMessage = ref<Message | null>(null)
const replyToMessage = ref<Message | null>(null)
const sending = ref(false)
const wsConnected = ref(false)
const reconnectAttempts = ref(0)
const chatsForForward = ref<any[]>([])

// Контекстное меню + пикер реакций
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0
})
const popupPosition = ref({ x: 0, y: 0 })
const reactionEmojis = ['👍', '😢', '😮', '😠', '🎉', '🔥', '👀', '🙏']

// Защита от race condition
const isComponentMounted = ref(false)

// Постер франшизы
const franchisePosterResolved = computed(() => {
  if (posterError.value) return null
  // Если есть franchisePoster - используем его
  if (props.franchisePoster) return props.franchisePoster
  // Fallback: берём постер из первой части франшизы
  if (props.parts && props.parts.length > 0) {
    const sortedParts = [...props.parts].sort((a, b) => a.franchise_order - b.franchise_order)
    const firstPart = sortedParts[0] as any
    return firstPart?.poster_image_url || firstPart?.poster_url || null
  }
  return null
})

const currentSlugFromProps = computed(() => props.initialTopicSlug)

// ── Build topics из ответа бэкенда ──────────────────────────
const buildTopicsFromResponse = (topicsData: any[], groupId: number) => {
  const list: Topic[] = []

  // Общий топик
  list.push({
    id: 0,
    name: props.franchiseName,
    poster_url: props.franchisePoster || null,
    animeId: null,
    unread: 0,
    slug: 'general',
  })

  // Топики из parts
  const sortedParts = [...props.parts].sort((a, b) => a.franchise_order - b.franchise_order)
  for (const part of sortedParts) {
    list.push({
      id: part.id,
      name: part.title_ru || part.title_en || `Часть #${part.id}`,
      poster_url: null,
      animeId: part.id,
      unread: 0,
      slug: String(part.id),
    })
  }

  if (topicsData.length > 0) {
    for (const t of topicsData) {
      const part = props.parts.find(p => p.id === t.anime_id)
      const existingIndex = list.findIndex(item => 
        (t.anime_id && item.animeId === t.anime_id) || 
        (!t.anime_id && item.animeId === null)
      )
      
      if (existingIndex >= 0) {
        const existingItem = list[existingIndex]
        if (!existingItem) continue
        list[existingIndex] = {
          id: t.topic_id ?? t.id ?? t.anime_id ?? 0,
          name: t.title || existingItem.name,
          poster_url: t.poster_url || existingItem.poster_url,
          animeId: t.anime_id || null,
          unread: 0,
          slug: part ? String(part.id) : 'general',
        }
      }
    }
  }

  topics.value = list
}

// ── Init franchise groups ──────────────────────────────────
const initFranchiseGroups = async () => {
  topics.value = []
  activeTopic.value = null
  messages.value = []
  chatGroupId.value = null
  
  for (const key in topicPosterErrors) {
    delete topicPosterErrors[key]
  }
  
  try {
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: props.franchiseId,
      anime_ids: props.parts.map(p => p.id),
    })

    chatGroupId.value = data.group_id
    buildTopicsFromResponse(data.topics || [], data.group_id)
  } catch (e) {
    console.error('Failed to init franchise groups:', e)
    buildTopicsFromResponse([], 0)
  }
}

// ── URL Navigation ─────────────────────────────────────────
const makeSlug = (text: string | null | undefined): string => {
  if (!text) return ''
  const translitMap: Record<string, string> = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '',
    'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    ' ': '-', '_': '-', '.': '-', ',': '-', '!': '', '?': '', '(': '', ')': '',
    '"': '', "'": '', ':': '', ';': '', '/': '-', '\\': '-',
  }
  let slug = String(text).toLowerCase()
  for (const [from, to] of Object.entries(translitMap)) {
    slug = slug.split(from).join(to)
  }
  slug = slug.replace(/-+/g, '-').replace(/[^a-z0-9\-]/g, '').replace(/^-|-$/g, '')
  return slug || 'unknown'
}

const findTopicBySlug = (slug: string | null): Topic | null => {
  if (!slug) return null
  const targetSlug = slug.toLowerCase()
  return topics.value.find(t => 
    t.slug.toLowerCase() === targetSlug || 
    makeSlug(t.name).toLowerCase() === targetSlug
  ) || null
}

const navigateToTopic = (topic: Topic) => {
  const baseSlug = props.franchiseSlug || makeSlug(props.franchiseName)
  const targetUrl = topic.animeId === null 
    ? `/chats/${baseSlug}` 
    : `/chats/${baseSlug}-${topic.slug}`
  if (route.path !== targetUrl) {
    router.push(targetUrl)
  }
}

const navigateToGeneral = () => {
  const baseSlug = props.franchiseSlug || makeSlug(props.franchiseName)
  router.push(`/chats/${baseSlug}`)
}

// ── Select topic ───────────────────────────────────────────
const selectTopic = async (topic: Topic) => {
  if (activeTopic.value?.id === topic.id && activeTopic.value?.animeId === topic.animeId) return
  
  activeTopic.value = topic
  showTopics.value = false
  
  // Сначала обновляем URL
  navigateToTopic(topic)
  
  await loadMessagesSingleChat(topic.animeId)
  
  disconnectWs()
  if (chatGroupId.value) {
    connectWsSingle(chatGroupId.value, topic.animeId)
  }
}

// ── Load messages ──────────────────────────────────────────
const loadMessagesSingleChat = async (topicId: number | null) => {
  if (!chatGroupId.value) { messages.value = []; return }
  loadingMessages.value = true
  
  try {
    const params: Record<string, string> = {}
    if (topicId !== undefined && topicId !== null) {
      params.topic_id = String(topicId)
    }
    
    const { data } = await apiClient.get(`/social/group-chats/${chatGroupId.value}/messages/`, { params })
    messages.value = data.results || data || []
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('loadMessages error:', e)
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}
  
// ── WebSocket ──────────────────────────────────────────────
let ws: WebSocket | null = null

const connectWsSingle = (groupId: number, topicId: number | null = null) => {
  const token = localStorage.getItem('access_token')
  if (!token || !groupId) return
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/chat/${groupId}/?token=${token}`)
  
  ws.onopen = () => {
    wsConnected.value = true
    reconnectAttempts.value = 0
    if (topicId !== null) {
      ws?.send(JSON.stringify({ action: 'set_topic', topic_id: topicId }))
    }
  }
  
  ws.onmessage = async (e) => {
    const data = JSON.parse(e.data)
    if (data.action === 'init') {
      if (data.messages?.length > 0 && messages.value.length === 0) {
        const filtered = data.messages.filter((m: any) => {
          if (topicId === null) return true
          return m.topic_id === topicId
        })
        messages.value = filtered
        await nextTick()
        scrollToBottom()
      }
    } else if (data.action === 'new_message') {
      const msg = data.message
      if (topicId === null || msg.topic_id === topicId) {
        messages.value.push(msg)
        await nextTick()
        scrollToBottom()
      }
    } else if (data.action === 'typing_status') {
      // Можно добавить индикатор печати
    }
  }
  ws.onclose = () => { 
    wsConnected.value = false
    ws = null
    setTimeout(() => {
      reconnectAttempts.value++
      if (chatGroupId.value && activeTopic.value) {
        connectWsSingle(chatGroupId.value, activeTopic.value.animeId ?? null)
      }
    }, 3000)
  }
  ws.onerror = (error) => console.error('WS error:', error)
}

const disconnectWs = () => { ws?.close(); ws = null }

// ── Send message ───────────────────────────────────────────
const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (!text && !replyToMessage.value) return
  const topicId = activeTopic.value?.animeId ?? null

  if (ws?.readyState === WebSocket.OPEN) {
    const messageData: any = { action: 'send_message', text, topic_id: topicId }
    
    // Добавляем reply_to если есть ответ
    if (replyToMessage.value) {
      messageData.reply_to = replyToMessage.value.id
    }
    
    ws.send(JSON.stringify(messageData))
    newMessage.value = ''
    replyToMessage.value = null
  } else {
    sending.value = true
    try {
      const messageData: any = { text, topic_id: topicId }
      
      // Добавляем reply_to если есть ответ
      if (replyToMessage.value) {
        messageData.reply_to = replyToMessage.value.id
      }
      
      const { data } = await apiClient.post(`/social/group-chats/${chatGroupId.value}/messages/`, messageData)
      messages.value.push({
        id: data.id,
        sender_id: data.sender,
        sender_username: data.sender_username || authStore.user?.username || '',
        sender_avatar: data.sender_avatar || null,
        text: data.text,
        media: data.media,
        media_type: data.media_type,
        created_at: data.created_at,
        topic_id: data.topic_id || null,
      })
      newMessage.value = ''
      replyToMessage.value = null
      await nextTick()
      scrollToBottom()
    } catch (e) { console.error('sendMessage HTTP error:', e) }
    finally { sending.value = false }
  }
}

// ── Helpers ────────────────────────────────────────────────
const scrollToBottom = () => {
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

const formatTime = (dt: string) =>
  new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const topicsWord = (n: number) => {
  if (n % 100 >= 11 && n % 100 <= 19) return 'топиков'
  const r = n % 10
  if (r === 1) return 'топик'
  if (r >= 2 && r <= 4) return 'топика'
  return 'топиков'
}

const getFileName = (url: string) => {
  if (!url) return 'Файл'
  try {
    return new URL(url).pathname.split('/').pop() || 'Файл'
  } catch {
    return url.split('/').pop() || 'Файл'
  }
}

const attachFile = () => fileInput.value?.click()

const handleFileSelect = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file || !chatGroupId.value) return
  
  sending.value = true
  try {
    const formData = new FormData()
    formData.append('media', file)
    formData.append('text', '')
    if (activeTopic.value?.animeId !== null) {
      formData.append('topic_id', String(activeTopic.value?.animeId))
    }
    
    const { data } = await apiClient.post(`/social/group-chats/${chatGroupId.value}/messages/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    messages.value.push({
      id: data.id,
      sender_id: data.sender,
      sender_username: data.sender_username || authStore.user?.username || '',
      sender_avatar: data.sender_avatar || null,
      text: data.text,
      media: data.media,
      media_type: data.media_type,
      created_at: data.created_at,
      topic_id: data.topic_id || null,
    })
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Upload error:', error)
  } finally {
    sending.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

// ── Reactions ──────────────────────────────────────────────
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
  
  return Object.values(grouped)
}

// ── Context Menu ───────────────────────────────────────────
const showMessageMenu = (message: Message, event: MouseEvent) => {
  event.preventDefault()
  selectedMessage.value = message
  
  const messageEl = (event.target as HTMLElement).closest('.message-content')
  if (!messageEl) return
  
  const messageRect = messageEl.getBoundingClientRect()
  const isOwnMessage = message.sender_id === currentUserId.value
  
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
    if (baseY < 15) baseY = 15
  }
  
  popupPosition.value = { x: baseX, y: baseY }
  contextMenu.value.visible = true
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

// ── Message Actions ────────────────────────────────────────
const handleReply = (message: Message) => {
  replyToMessage.value = message
  ;(document.querySelector('.message-input') as HTMLInputElement)?.focus()
  closeContextMenu()
}

const cancelReply = () => {
  replyToMessage.value = null
}

const handleForward = (message: Message) => {
  messageToForward.value = message
  showForward.value = true
  closeContextMenu()
}

const handleDelete = async (messageId: number) => {
  if (!confirm('Удалить сообщение?')) return
  
  try {
    await apiClient.delete(`/social/messages/${messageId}/`)
    messages.value = messages.value.filter(m => m.id !== messageId)
  } catch (error) {
    console.error('Delete error:', error)
  }
  closeContextMenu()
}

const handleReactionClick = async (messageId: number, emoji: string) => {
  await handleReaction(messageId, emoji)
  closeContextMenu()
}

const addReaction = (emoji: string) => {
  if (selectedMessage.value) {
    handleReactionClick(selectedMessage.value.id, emoji)
  }
}

// ── Forward Complete ───────────────────────────────────────
const handleForwardComplete = () => {
  showForward.value = false
  messageToForward.value = null
}

const handleSettingsChanged = (data: any) => {
  console.log('Settings changed:', data)
  showSettings.value = false
}

// ── Scroll to message ──────────────────────────────────────
const scrollToMessage = (messageId: number) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`) as HTMLElement | null
  if (!messageElement) return
  messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  messageElement.classList.add('highlighted')
  setTimeout(() => messageElement.classList.remove('highlighted'), 2000)
  closeContextMenu()
}

// ── Typing ─────────────────────────────────────────────────
let typingDebounceTimer: number | null = null

const handleTyping = () => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'typing_start', user_id: currentUserId.value }))
  }
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
  typingDebounceTimer = window.setTimeout(() => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'typing_stop', user_id: currentUserId.value }))
    }
  }, 3000)
}

// ── Инициализация при монтировании ─────────────────────────
onMounted(async () => {
  isComponentMounted.value = true
  
  await initFranchiseGroups()

  const slug = currentSlugFromProps.value
  
  if (slug) {
    const topic = findTopicBySlug(slug)
    if (topic) {
      await selectTopic(topic)
      return
    }
  }
  
  // По умолчанию - общее обсуждение
  const generalTopic = topics.value.find(t => t.animeId === null)
  if (generalTopic) {
    await selectTopic(generalTopic)
  } else {
    const firstTopic = topics.value[0]
    if (firstTopic) {
      await selectTopic(firstTopic)
    }
  }
})

// ── Слежение за changes в props (роутинг) ─────────────────
watch(() => props.initialTopicSlug, async (newSlug) => {
  if (!isComponentMounted.value || !chatGroupId.value) return
  
  if (!newSlug) {
    const generalTopic = topics.value.find(t => t.animeId === null)
    if (generalTopic && activeTopic.value?.animeId !== null) {
      activeTopic.value = generalTopic
      await loadMessagesSingleChat(null)
      disconnectWs()
      connectWsSingle(chatGroupId.value, null)
    }
    return
  }
  
  const topic = findTopicBySlug(newSlug)
  if (topic && activeTopic.value?.animeId !== topic.animeId) {
    activeTopic.value = topic
    await loadMessagesSingleChat(topic.animeId)
    disconnectWs()
    connectWsSingle(chatGroupId.value, topic.animeId)
  }
})

// Следим за сменой franchiseId - полный ресет
watch(() => props.franchiseId, async (newId, oldId) => {
  if (newId && newId !== oldId && isComponentMounted.value) {
    disconnectWs()
    topics.value = []
    activeTopic.value = null
    messages.value = []
    chatGroupId.value = null
    newMessage.value = ''
    posterError.value = false
    for (const key in topicPosterErrors) {
      delete topicPosterErrors[key]
    }
    
    await new Promise(r => setTimeout(r, 50))
    await initFranchiseGroups()
    
    const generalTopic = topics.value.find(t => t.animeId === null)
    if (generalTopic) await selectTopic(generalTopic)
    else {
      const firstTopic = topics.value[0]
      if (firstTopic) await selectTopic(firstTopic)
    }
  }
})
    
onUnmounted(() => {
  isComponentMounted.value = false
  disconnectWs()
})
</script>

<style scoped>
.franchise-chat {
  display: flex;
  flex-direction: column;
  height: 90vh;
  background: var(--color-background, #0f0f0f);
}

/* Мобильная адаптация */
@media (max-width: 767px) {
  .franchise-chat {
    height: 100vh;
    padding-top: 60px;
    box-sizing: border-box;
  }
}

/* ═══ ШАПКА ЧАТА ════════════════════════════════════════════ */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--surface-2, #1a1a1a);
  border-bottom: 1px solid var(--border-subtle, #2a2a2a);
  flex-shrink: 0;
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.chat-info button {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3, #2a2a2a);
  color: var(--text-tertiary, #666);
  font-size: 1.2rem;
}

.chat-details {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
  flex: 1;
}

.chat-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary, #e0e0e0);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-members {
  font-size: 0.7rem;
  color: var(--text-tertiary, #666);
}

.header-actions {
  display: flex;
  gap: 0.35rem;
  flex-shrink: 0;
}

.search-btn, .topics-btn, .settings-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-subtle, #2a2a2a);
  border-radius: 8px;
  color: var(--text-tertiary, #888);
  cursor: pointer;
  transition: all 0.15s;
}

.search-btn:hover, .topics-btn:hover, .settings-btn:hover {
  background: var(--surface-3, #222);
  color: var(--text-primary, #ccc);
}

/* ═══ ПАНЕЛЬ ТЕМ ════════════════════════════════════════════ */
.topics-panel {
  background: var(--surface-1, #141414);
  border-bottom: 1px solid var(--border-subtle, #2a2a2a);
  max-height: 220px;
  overflow-y: auto;
  flex-shrink: 0;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 0.35rem;
}

.topic-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.5rem;
  border: none;
  border-radius: 0.35rem;
  background: transparent;
  color: var(--text-tertiary, #888);
  cursor: pointer;
  font-size: 0.83rem;
  text-align: left;
  transition: all 0.15s;
  width: 100%;
}

.topic-item:hover {
  background: var(--surface-2, #222);
  color: var(--text-primary, #ccc);
}

.topic-item.active {
  background: var(--accent-subtle, rgba(58, 134, 255, 0.12));
  color: var(--accent, #60a5fa);
  font-weight: 600;
}

.topic-poster-wrap {
  width: 28px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 0.2rem;
  overflow: hidden;
}

.topic-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.topic-poster-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3, #2a2a2a);
  font-size: 0.9rem;
  width: 100%;
  height: 100%;
}

.topic-info {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}

.topic-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-badge {
  background: #ef4444;
  color: white;
  font-size: 0.6rem;
  font-weight: 700;
  border-radius: 10px;
  padding: 0.1rem 0.3rem;
  flex-shrink: 0;
  margin-left: 0.25rem;
}

/* ═══ СООБЩЕНИЯ ═════════════════════════════════════════════ */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.625rem;
  position: relative;
}

.loading, .no-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-tertiary, #555);
  gap: 0.5rem;
  font-size: 0.9rem;
  min-height: 200px;
}

.no-messages svg {
  color: var(--text-tertiary, #444);
  margin-bottom: 0.5rem;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
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
  border-radius: 0.75rem;
  background: var(--surface-3, #2d2d2d);
  color: var(--text-primary, #fff);
  font-size: 0.83rem;
  line-height: 1.4;
  word-break: break-word;
}

.own-message .message-content {
  background: linear-gradient(135deg, var(--accent, #3b82f6) 0%, var(--accent-hover, #2563eb) 100%);
  color: #fff;
}

.message-sender {
  font-size: 0.68rem;
  color: var(--accent, #7c4dff);
  font-weight: 600;
  margin-bottom: 0.1rem;
}

.own-message .message-sender {
  display: none;
}

.message-text {
  word-break: break-word;
  line-height: 1.4;
}

.message-image {
  max-width: 100%;
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.message-file {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.35rem;
}

.message-file a {
  color: var(--accent, #60a5fa);
  text-decoration: none;
}

.message-file a:hover {
  text-decoration: underline;
}

.message-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.35rem;
  padding-top: 0.35rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.reaction-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.15rem 0.4rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.15s;
}

.reaction-badge:hover {
  background: rgba(255, 255, 255, 0.15);
}

.reaction-collapsed {
  font-size: 0.65rem;
  padding: 0.1rem 0.3rem;
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  margin-top: 0.15rem;
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.5);
}

.own-footer {
  justify-content: flex-end;
}

.message-time {
  margin-left: auto;
}

/* ═══ ВВОД СООБЩЕНИЯ ════════════════════════════════════════ */
.message-input-area {
  flex-shrink: 0;
  padding: 0.5rem 0.625rem 0.625rem;
  background: var(--surface-2, #1a1a1a);
  border-top: 1px solid var(--border-subtle, #2a2a2a);
}

/* Превью ответа */
.reply-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
  background: rgba(58, 134, 255, 0.08);
  border-left: 3px solid var(--accent, #3b82f6);
  border-radius: 6px;
}

.reply-preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.reply-author {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent, #3b82f6);
}

.reply-text {
  font-size: 0.8rem;
  color: var(--text-secondary, #888);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reply-cancel {
  background: none;
  border: none;
  color: var(--text-tertiary, #666);
  font-size: 1rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.reply-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #ccc);
}

.topic-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.68rem;
  color: var(--accent, #60a5fa);
  margin-bottom: 0.25rem;
  padding-left: 0.1rem;
}

.topic-label strong {
  color: var(--accent, #60a5fa);
}

.message-form {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.message-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-subtle, #2a2a2a);
  border-radius: 1rem;
  background: var(--surface-1, #0f0f0f);
  color: var(--text-primary, #fff);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s;
}

.message-input:focus {
  border-color: var(--accent, #3b82f6);
}

.message-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attach-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-tertiary, #888);
  cursor: pointer;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.attach-btn:hover:not(:disabled) {
  background: var(--surface-3, #222);
  color: var(--text-primary, #ccc);
}

.attach-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--accent, #3b82f6);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover, #2563eb);
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ws-status {
  text-align: center;
  font-size: 0.7rem;
  color: #f59e0b;
  margin-top: 0.25rem;
}

/* ═══ КОНТЕКСТНОЕ МЕНЮ ══════════════════════════════════════ */
.message-actions-popup {
  position: fixed;
  background: var(--surface-3, #2a2a2a);
  border: 1px solid var(--border-default, #3a3a3a);
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  z-index: 9999;
  min-width: 160px;
  overflow: hidden;
}

.reaction-picker-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-subtle, #3a3a3a);
  max-width: 200px;
}

.reaction-emoji-btn {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.35rem;
  transition: all 0.15s;
}

.reaction-emoji-btn:hover {
  background: var(--surface-4, #3a3a3a);
  transform: scale(1.15);
}

.context-menu-actions {
  display: flex;
  flex-direction: column;
  padding: 0.25rem;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.625rem;
  background: transparent;
  border: none;
  border-radius: 0.35rem;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  width: 100%;
}

.context-menu-item:hover {
  background: var(--surface-4, #353535);
}

.context-menu-item.delete:hover {
  background: var(--danger-subtle, rgba(239, 68, 68, 0.15));
  color: var(--danger, #ef4444);
}

.context-menu-icon {
  font-size: 1rem;
  width: 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Подсветка сообщения */
.message-item.highlighted {
  background: var(--accent-subtle, rgba(58, 134, 255, 0.1));
  animation: highlight-pulse 2s ease-out;
}

@keyframes highlight-pulse {
  0%, 100% { background: transparent; }
  50% { background: var(--accent-subtle, rgba(58, 134, 255, 0.15)); }
}
</style>
