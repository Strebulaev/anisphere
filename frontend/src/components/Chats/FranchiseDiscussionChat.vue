<template>
  <div class="franchise-chat">
    <!-- Шапка -->
    <div class="fc-header">
      <img :src="franchisePoster" class="fc-poster" :alt="franchiseName" />
      <div class="fc-header-info">
        <h2 class="fc-title">{{ franchiseName }}</h2>
        <span class="fc-subtitle">Обсуждение франшизы</span>
      </div>
    </div>

    <!-- Темы (топики) -->
    <div class="fc-topics">
      <button
        v-for="topic in topics"
        :key="topic.id"
        :class="['fc-topic-btn', { active: activeTopic?.id === topic.id }]"
        @click="selectTopic(topic)"
      >
        <span class="topic-icon">{{ topic.icon }}</span>
        <span class="topic-name">{{ topic.name }}</span>
        <span v-if="topic.unread > 0" class="topic-badge">{{ topic.unread }}</span>
      </button>
    </div>

    <!-- Сообщения -->
    <div class="fc-messages" ref="messagesEl">
      <div v-if="loadingMessages" class="fc-loading">Загрузка...</div>
      <div v-else-if="messages.length === 0" class="fc-empty">
        <span>💬</span>
        <p>Начните обсуждение в теме «{{ activeTopic?.name }}»</p>
      </div>
      <div v-else class="fc-messages-list">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['fc-msg', { own: msg.sender_id === currentUserId }]"
        >
          <img :src="msg.sender_avatar || '/default-avatar.png'" class="fc-msg-avatar" />
          <div class="fc-msg-bubble">
            <span class="fc-msg-author">{{ msg.sender_username }}</span>
            <span class="fc-msg-text">{{ msg.text }}</span>
            <span class="fc-msg-time">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Ввод -->
    <div class="fc-input-area">
      <span class="fc-topic-label">{{ activeTopic?.name }}</span>
      <div class="fc-input-row">
        <input
          v-model="newMessage"
          class="fc-input"
          :placeholder="`Написать в «${activeTopic?.name}»...`"
          @keydown.enter.prevent="sendMessage"
        />
        <button class="fc-send-btn" @click="sendMessage" :disabled="!newMessage.trim()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { getMediaUrl } from '@/api/client'

interface FranchisePart {
  id: number
  title_ru: string
  title_en: string
  franchise_order: number
}

interface Topic {
  id: number          // chat group id в бэкенде
  name: string
  icon: string
  animeId: number | null  // null = общая тема
  unread: number
}

interface Message {
  id: number
  sender_id: number
  sender_username: string
  sender_avatar: string | null
  text: string
  created_at: string
}

const props = defineProps<{
  franchiseId: number
  franchiseName: string
  franchisePoster: string
  parts: FranchisePart[]        // части франшизы
  highlightAnimeId?: number     // открыть тему для конкретной части
}>()

const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

// ── State ──────────────────────────────────────────────────
const topics = ref<Topic[]>([])
const activeTopic = ref<Topic | null>(null)
const messages = ref<Message[]>([])
const loadingMessages = ref(false)
const newMessage = ref('')
const messagesEl = ref<HTMLElement | null>(null)

let ws: WebSocket | null = null

// ── Build topics ───────────────────────────────────────────
// Каждая часть + общая тема «О всей франшизе»
const buildTopics = (groupMap: Record<number | string, number>) => {
  const list: Topic[] = []

  // Общая тема
  list.push({
    id: groupMap['general'] ?? 0,
    name: `О франшизе «${props.franchiseName}»`,
    icon: '💬',
    animeId: null,
    unread: 0
  })

  // По частям (отсортированным)
  const sorted = [...props.parts].sort((a, b) => a.franchise_order - b.franchise_order)
  for (const part of sorted) {
    list.push({
      id: groupMap[part.id] ?? 0,
      name: part.title_ru || part.title_en,
      icon: '📺',
      animeId: part.id,
      unread: 0
    })
  }

  topics.value = list
}

// ── Init groups on backend ─────────────────────────────────
// Один эндпоинт: /social/franchise-discussion/ POST {franchise_id}
// Возвращает { group_map: { general: <id>, <anime_id>: <id>, ... } }
const initFranchiseGroups = async () => {
  try {
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: props.franchiseId,
      anime_ids: props.parts.map(p => p.id)
    })
    buildTopics(data.group_map || {})
  } catch (e) {
    // fallback: создаём локальные темы с id=0
    const map: Record<number | string, number> = { general: 0 }
    props.parts.forEach(p => { map[p.id] = 0 })
    buildTopics(map)
  }
}

// ── Select topic ───────────────────────────────────────────
const selectTopic = async (topic: Topic) => {
  if (activeTopic.value?.id === topic.id) return
  disconnectWs()
  activeTopic.value = topic
  await loadMessages(topic.id)
  if (topic.id > 0) connectWs(topic.id)
}

// ── Load messages ──────────────────────────────────────────
const loadMessages = async (groupId: number) => {
  if (!groupId) { messages.value = []; return }
  loadingMessages.value = true
  try {
    const { data } = await apiClient.get(`/social/group-chats/${groupId}/messages/`)
    messages.value = data.results || data || []
    await nextTick()
    scrollToBottom()
  } catch (e) {
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

// ── WebSocket ──────────────────────────────────────────────
const connectWs = (groupId: number) => {
  const token = localStorage.getItem('access_token')
  if (!token || !groupId) return
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/chat/${groupId}/?token=${token}`)
  ws.onmessage = async (e) => {
    const data = JSON.parse(e.data)
    if (data.action === 'new_message') {
      messages.value.push(data.message)
      await nextTick()
      scrollToBottom()
    }
  }
  ws.onclose = () => { ws = null }
}

const disconnectWs = () => { ws?.close(); ws = null }

// ── Send ───────────────────────────────────────────────────
const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (!text || !activeTopic.value?.id) return
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'send_message', text }))
    newMessage.value = ''
  } else {
    // fallback HTTP
    try {
      const { data } = await apiClient.post('/social/messages/', {
        text,
        chat: activeTopic.value.id
      })
      messages.value.push(data)
      newMessage.value = ''
      await nextTick()
      scrollToBottom()
    } catch (e) { console.error(e) }
  }
}

// ── Helpers ────────────────────────────────────────────────
const scrollToBottom = () => {
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

const formatTime = (dt: string) =>
  new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

// ── Lifecycle ──────────────────────────────────────────────
onMounted(async () => {
  await initFranchiseGroups()

  // Если нужно сразу открыть тему для конкретного аниме
  const target = props.highlightAnimeId
    ? topics.value.find(t => t.animeId === props.highlightAnimeId)
    : topics.value[0]

  if (target) await selectTopic(target)
})

// Если извне меняется highlightAnimeId (переход из страницы части)
watch(() => props.highlightAnimeId, async (newId) => {
  if (newId) {
    const topic = topics.value.find(t => t.animeId === newId)
    if (topic) await selectTopic(topic)
  }
})

onUnmounted(disconnectWs)
</script>

<style scoped>
.franchise-chat {
  display: flex;
  flex-direction: column;
  height: 90vh;
  background: #0f0f0f;
}

/* Шапка */
.fc-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.fc-poster {
  width: 42px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}
.fc-title {
  font-size: 1rem;
  font-weight: 700;
  color: #e0e0e0;
  margin: 0;
  line-height: 1.2;
}
.fc-subtitle {
  font-size: 0.75rem;
  color: #666;
}
.fc-header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Темы */
.fc-topics {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 8px;
  background: #141414;
  border-bottom: 1px solid #2a2a2a;
  overflow-y: auto;
  max-height: 220px;
  flex-shrink: 0;
}
.fc-topic-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #888;
  cursor: pointer;
  font-size: 0.85rem;
  text-align: left;
  transition: background 0.15s, color 0.15s;
  width: 100%;
}
.fc-topic-btn:hover {
  background: #222;
  color: #ccc;
}
.fc-topic-btn.active {
  background: #1e3a5f;
  color: #60a5fa;
  font-weight: 600;
}
.topic-icon { font-size: 1rem; flex-shrink: 0; }
.topic-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topic-badge {
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  border-radius: 10px;
  padding: 1px 5px;
  flex-shrink: 0;
}

/* Сообщения */
.fc-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.fc-loading, .fc-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #555;
  gap: 8px;
  font-size: 0.9rem;
}
.fc-empty span { font-size: 2rem; }

.fc-messages-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fc-msg {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.fc-msg.own {
  flex-direction: row-reverse;
}
.fc-msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.fc-msg-bubble {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  padding: 6px 10px;
  border-radius: 12px;
  background: #2d2d2d;
  color: #fff;
  font-size: 0.85rem;
}
.fc-msg.own .fc-msg-bubble {
  background: #1e7cff;
  align-items: flex-end;
}
.fc-msg-author {
  font-size: 0.7rem;
  color: #7c4dff;
  font-weight: 600;
  margin-bottom: 2px;
}
.fc-msg.own .fc-msg-author { display: none; }
.fc-msg-text { line-height: 1.4; word-break: break-word; }
.fc-msg-time {
  font-size: 0.65rem;
  color: rgba(255,255,255,0.5);
  margin-top: 2px;
  align-self: flex-end;
}

/* Ввод */
.fc-input-area {
  flex-shrink: 0;
  padding: 8px 12px 12px;
  background: #1a1a1a;
  border-top: 1px solid #2a2a2a;
}
.fc-topic-label {
  display: block;
  font-size: 0.7rem;
  color: #60a5fa;
  margin-bottom: 4px;
  padding-left: 4px;
}
.fc-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.fc-input {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid #2a2a2a;
  border-radius: 20px;
  background: #0f0f0f;
  color: #fff;
  font-size: 0.9rem;
  outline: none;
}
.fc-input:focus { border-color: #3b82f6; }
.fc-send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #3b82f6;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.fc-send-btn:hover { background: #2563eb; }
.fc-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
