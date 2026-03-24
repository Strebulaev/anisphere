<template>
  <div class="franchise-chat">
    <!-- Шапка -->
    <div class="fc-header">
      <img
        v-if="franchisePosterResolved"
        :src="franchisePosterResolved"
        class="fc-poster"
        :alt="franchiseName"
        @error="posterError = true"
      />
      <div v-else class="fc-poster fc-poster-placeholder">🎬</div>
      <div class="fc-header-info">
        <h2 class="fc-title">{{ franchiseName }}</h2>
        <span class="fc-subtitle">{{ topics.length }} {{ topicsWord(topics.length) }}</span>
      </div>
      <!-- Действия чата -->
      <div class="fc-header-actions">
        <!-- Уведомления -->
        <button
          :class="['fc-action-btn', { muted: isMuted }]"
          :title="isMuted ? 'Уведомления заглушены — нажмите чтобы включить' : 'Заглушить уведомления'"
          @click="toggleNotifications"
        >
          <svg v-if="!isMuted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            <path d="M18.63 13A17.89 17.89 0 0 1 18 8"/>
            <path d="M6.26 6.26A5.86 5.86 0 0 0 6 8c0 7-3 9-3 9h14"/>
            <path d="M18 8a6 6 0 0 0-9.33-5"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
        </button>
        <!-- Архивация -->
        <button
          :class="['fc-action-btn', { archived: isArchived }]"
          :title="isArchived ? 'Разархивировать' : 'Архивировать'"
          @click="toggleArchive"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="21 8 21 21 3 21 3 8"/>
            <rect x="1" y="3" width="22" height="5"/>
            <line x1="10" y1="12" x2="14" y2="12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Баннер если заглушено -->
    <div v-if="isMuted" class="fc-muted-banner">
      🔕 Уведомления заглушены
      <button class="fc-unmute-btn" @click="toggleNotifications">Включить</button>
    </div>

    <!-- Баннер если архивирован -->
    <div v-if="isArchived" class="fc-archived-banner">
      📦 Чат в архиве
      <button class="fc-unarchive-btn" @click="toggleArchive">Разархивировать</button>
    </div>

    <!-- Баннер ошибки slug -->
    <div v-if="slugValidationError" class="fc-error-banner">
      ⚠️ Топик не найден — показывается общее обсуждение
    </div>

    <!-- Темы (топики) с постерами -->
    <div class="fc-topics-header" @click="topicsCollapsed = !topicsCollapsed">
      <span class="fc-topics-title">📋 Темы ({{ topics.length }})</span>
      <span class="fc-topics-chevron" :class="{ collapsed: topicsCollapsed }">▾</span>
    </div>
    <div class="fc-topics" v-show="!topicsCollapsed">
      <button
        v-for="topic in topics"
        :key="topic.id"
        :class="['fc-topic-btn', { active: activeTopic?.id === topic.id }]"
        @click="selectTopic(topic)"
      >
        <!-- Постер топика -->
        <div class="topic-poster-wrap">
          <img
            v-if="topic.poster_url && !topicPosterErrors[topic.id]"
            :src="topic.poster_url"
            class="topic-poster"
            :alt="topic.name"
            @error="topicPosterErrors[topic.id] = true"
          />
          <div v-else class="topic-poster topic-poster-fallback">
            {{ topic.animeId ? '📺' : '💬' }}
          </div>
        </div>
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

    <!-- Модалка заглушения -->
    <MuteChatModal
      v-if="showMuteModal"
      @close="showMuteModal = false"
      @muted="onMuted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import MuteChatModal from './MuteChatModal.vue'

interface FranchisePart {
  id: number
  title_ru: string
  title_en: string
  franchise_order: number
}

interface Topic {
  id: number        // topic_id из бэкенда
  name: string
  poster_url: string | null
  animeId: number | null  // null = общее обсуждение
  unread: number
  slug: string      // slug из названия для URL
}

interface Message {
  id: number
  sender_id: number
  sender_username: string
  sender_avatar: string | null
  text: string
  created_at: string
  topic_id: number | null
}

const props = defineProps<{
  franchiseId: number
  franchiseSlug?: string | null  // slug для URL
  franchiseName: string
  franchisePoster?: string
  parts: FranchisePart[]
  initialTopicSlug?: string | null
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const currentUserId = computed(() => authStore.user?.id)

// ── SLUG UTILS ─────────────────────────────────────────────
// Создание slug из названия (транслитерация)
const makeSlug = (text: string | null | undefined): string => {
  if (!text) return ''
  const str = String(text)
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
  
  let slug = str.toLowerCase()
  for (const [from, to] of Object.entries(translitMap)) {
    slug = slug.split(from).join(to)  // Используем split/join вместо replace с regex
  }
  // Удаляем повторяющиеся дефисы и недопустимые символы
  slug = slug.replace(/-+/g, '-').replace(/[^a-z0-9\-]/g, '')
  // Удаляем дефисы в начале и конце
  slug = slug.replace(/^-|-$/g, '')
  return slug || 'unknown'
}

// Проверка что slug соответствует топику из списка
const findTopicBySlug = (slug: string | null): Topic | null => {
  if (!slug) return null
  const targetSlug = slug.toLowerCase()
  // Ищем точный slug или slug по названию аниме
  return topics.value.find(t => 
    t.slug.toLowerCase() === targetSlug || 
    makeSlug(t.name).toLowerCase() === targetSlug
  ) || null
}

// Проверка что slug валиден для этой франшизы
const isValidTopicSlug = (slug: string): boolean => {
  return findTopicBySlug(slug) !== null
}

// ── State ──────────────────────────────────────────────────
const topics = ref<Topic[]>([])
const activeTopic = ref<Topic | null>(null)
const messages = ref<Message[]>([])
const loadingMessages = ref(false)
const newMessage = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const posterError = ref(false)
const topicPosterErrors = reactive<Record<number, boolean>>({})
const slugValidationError = ref(false)

// Защита от race condition при смене франшизы
const isComponentMounted = ref(false)
const currentComponentId = ref(0)
let componentIdCounter = 0

// Настройки уведомлений и архивации
const isMuted = ref(false)
const isArchived = ref(false)
const showMuteModal = ref(false)
const chatGroupId = ref<number | null>(null)
const topicsCollapsed = ref(false)

let ws: WebSocket | null = null

// Постер франшизы (используем из бэкенда или prop)
const franchisePosterResolved = computed(() => {
  if (posterError.value) return null
  return props.franchisePoster || null
})

// Текущий slug из URL
const currentSlugFromProps = computed(() => props.initialTopicSlug)

// ── Build topics из ответа бэкенда ──────────────────────────
// Все топики используют ОДИН chatGroupId
const buildTopicsFromResponse = (topicsData: any[], groupId: number) => {
  const list: Topic[] = []

  // Сначала добавляем общий топик (general) - это сам чат
  list.push({
    id: 0,
    name: props.franchiseName,
    poster_url: props.franchisePoster || null,
    animeId: null,  // null = общее обсуждение
    unread: 0,
    slug: 'general',
  })

  // Добавляем топики из parts
  const sortedParts = [...props.parts].sort((a, b) => a.franchise_order - b.franchise_order)
  
  for (const part of sortedParts) {
    const slug = makeSlug(part.title_ru || part.title_en || String(part.id))
    list.push({
      id: part.id,  // anime_id как topic_id
      name: part.title_ru || part.title_en || `Часть #${part.id}`,
      poster_url: null,
      animeId: part.id,
      unread: 0,
      slug: slug,
    })
  }

  if (topicsData.length > 0) {
    for (const t of topicsData) {
      const part = props.parts.find(p => p.id === t.anime_id)
      const slug = part ? makeSlug(part.title_ru || part.title_en || String(part.id)) : 'general'
      
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
          slug: slug,
        }
      }
    }
  }

  topics.value = list
}

// ── Загрузка настроек уведомлений ─────────────────────────
const loadNotificationSettings = async (groupId: number) => {
  try {
    const { data } = await apiClient.get(`/social/group-chats/${groupId}/notification-settings/`)
    isMuted.value = !data.notifications_enabled || data.is_muted
    isArchived.value = data.is_archived || false
  } catch {
    // Игнорируем ошибки загрузки настроек
  }
}

// ── Init groups on backend ─────────────────────────────────
const initFranchiseGroups = async () => {
  // Сбрасываем состояние перед загрузкой
  topics.value = []
  activeTopic.value = null
  messages.value = []
  chatGroupId.value = null
  slugValidationError.value = false
  
  // Очищаем ошибки постеров
  for (const key in topicPosterErrors) {
    delete topicPosterErrors[key]
  }
  
  try {
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: props.franchiseId,
      anime_ids: props.parts.map(p => p.id),
    })

    chatGroupId.value = data.group_id

    // Строим топики - все используют ОДИН group_id
    buildTopicsFromResponse(data.topics || [], data.group_id)
    
    // Загружаем настройки уведомлений
    if (data.group_id) {
      await loadNotificationSettings(data.group_id)
    }
  } catch (e) {
    console.error('Failed to init franchise groups:', e)
    // Создаём локальные топики если бэкенд недоступен
    buildTopicsFromResponse([], 0)
  }
}

// ── Уведомления ────────────────────────────────────────────
const toggleNotifications = async () => {
  if (!chatGroupId.value) return

  if (isMuted.value) {
    try {
      await apiClient.post(`/social/group-chats/${chatGroupId.value}/unmute/`)
      isMuted.value = false
    } catch (e) {
      console.error('Failed to unmute:', e)
    }
  } else {
    showMuteModal.value = true
  }
}

const onMuted = async (until: string | null) => {
  if (!chatGroupId.value) return
  try {
    const duration = until
      ? Math.round((new Date(until).getTime() - Date.now()) / 60000)
      : null
    await apiClient.post(`/social/group-chats/${chatGroupId.value}/mute/`, { duration })
    isMuted.value = true
  } catch (e) {
    console.error('Failed to mute:', e)
  }
}

// ── Архивация ──────────────────────────────────────────────
const toggleArchive = async () => {
  if (!chatGroupId.value) return
  try {
    const newVal = !isArchived.value
    await apiClient.post(`/social/group-chats/${chatGroupId.value}/archive/`, { is_archived: newVal })
    isArchived.value = newVal
  } catch (e) {
    console.error('Failed to archive:', e)
  }
}

// ── URL Navigation ─────────────────────────────────────────
const navigateToTopic = (topic: Topic) => {
  // Используем franchiseSlug если передан, иначе создаём из franchiseName
  const baseSlug = props.franchiseSlug || makeSlug(props.franchiseName)
  const targetUrl = topic.animeId === null 
    ? `/chats/${baseSlug}` 
    : `/chats/${baseSlug}-${topic.slug}`
  
  // Только если URL отличается
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
  
  const prevTopic = activeTopic.value
  activeTopic.value = topic
  topicsCollapsed.value = true
  
  // НЕ меняем URL при смене топика - это вызывает проблемы
  // navigateToTopic(topic) - УБРАЛ
  
  // Загружаем сообщения для нового топика
  // Используем ОДИН chatGroupId для всех топиков - это ключевое изменение
  await loadMessagesSingleChat(topic.animeId)
  
  // WS - переподключаемся с новым топиком (но тот же chatId)
  disconnectWs()
  if (chatGroupId.value) {
    connectWsSingle(chatGroupId.value, topic.animeId)
  }
}

// ── Load messages - ОДИН чат, разные topic_id ─────────────
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
  
// ── WebSocket - ОДИН чат с фильтром по topic_id ───────────
const connectWsSingle = (groupId: number, topicId: number | null = null) => {
  const token = localStorage.getItem('access_token')
  if (!token || !groupId) return
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/chat/${groupId}/?token=${token}`)
  
  ws.onopen = () => {
    // Устанавливаем топик при подключении
    if (topicId !== null) {
      ws?.send(JSON.stringify({ action: 'set_topic', topic_id: topicId }))
    }
  }
  
  ws.onmessage = async (e) => {
    const data = JSON.parse(e.data)
    if (data.action === 'init') {
      if (data.messages?.length > 0 && messages.value.length === 0) {
        // Фильтруем сообщения по текущему топику:
        // - Главный топик (null): показываем ВСЕ сообщения
        // - Конкретный топик: показываем ТОЛЬКО сообщения с matching topic_id
        const filtered = data.messages.filter((m: any) => {
          if (topicId === null) return true // Главный топик - все
          return m.topic_id === topicId // Конкретный топик - только свои
        })
        messages.value = filtered
        await nextTick()
        scrollToBottom()
      }
    } else if (data.action === 'new_message') {
      const msg = data.message
      // Логика отображения:
      // - Главный топик (null): показываем ВСЕ сообщения
      // - Конкретный топик: показываем ТОЛЬКО сообщения с matching topic_id
      if (topicId === null) {
        messages.value.push(msg)
        await nextTick()
        scrollToBottom()
      } else if (msg.topic_id === topicId) {
        messages.value.push(msg)
        await nextTick()
        scrollToBottom()
      }
    }
  }
  ws.onclose = () => { ws = null }
}

const disconnectWs = () => { ws?.close(); ws = null }

// ── Send ───────────────────────────────────────────────────
const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (!text || !chatGroupId.value) return
  const topicId = activeTopic.value?.animeId

  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'send_message', text, topic_id: topicId }))
    newMessage.value = ''
  } else {
    try {
      const { data } = await apiClient.post(`/social/group-chats/${chatGroupId.value}/messages/`, { 
        text, 
        topic_id: topicId 
      })
      messages.value.push({
        id: data.id,
        sender_id: data.sender,
        sender_username: data.sender_username || authStore.user?.username || '',
        sender_avatar: data.sender_avatar || null,
        text: data.text,
        created_at: data.created_at,
        topic_id: data.topic_id || null,
      })
      newMessage.value = ''
      await nextTick()
      scrollToBottom()
    } catch (e) { console.error('sendMessage HTTP error:', e) }
  }
}

// ── Helpers ────────────────────────────────────────────────
const scrollToBottom = () => {
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
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

// ── Инициализация при монтировании ─────────────────────────
onMounted(async () => {
  isComponentMounted.value = true
  componentIdCounter++
  
  await initFranchiseGroups()

  // Проверяем slug из URL
  const slug = currentSlugFromProps.value
  
  if (slug) {
    // Проверяем что slug валиден
    if (isValidTopicSlug(slug)) {
      const topic = findTopicBySlug(slug)
      if (topic) {
        await selectTopic(topic)
        return
      }
    } else {
      // Slug невалиден - показываем ошибку и редиректим на общее
      slugValidationError.value = true
      navigateToGeneral()
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
// При смене топика через URL - просто перезагружаем сообщения
watch(() => props.initialTopicSlug, async (newSlug) => {
  if (!isComponentMounted.value || !chatGroupId.value) return
  
  if (!newSlug) {
    // Переход на общее обсуждение (topic_id = null)
    const generalTopic = topics.value.find(t => t.animeId === null)
    if (generalTopic && activeTopic.value?.animeId !== null) {
      activeTopic.value = generalTopic
      await loadMessagesSingleChat(null)
      // Переподключаем WS с новым топиком
      disconnectWs()
      connectWsSingle(chatGroupId.value, null)
    }
    return
  }
  
  // Проверяем slug
  if (!isValidTopicSlug(newSlug)) {
    slugValidationError.value = true
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

// Полная очистка состояния при смене франшизы
const resetState = () => {
  disconnectWs()
  topics.value = []
  activeTopic.value = null
  messages.value = []
  chatGroupId.value = null
  isMuted.value = false
  isArchived.value = false
  topicsCollapsed.value = false
  newMessage.value = ''
  posterError.value = false
  slugValidationError.value = false
  for (const key in topicPosterErrors) {
    delete topicPosterErrors[key]
  }
}

// Следим за сменой franchiseId - полный ресет
watch(() => props.franchiseId, async (newId, oldId) => {
  if (newId && newId !== oldId && isComponentMounted.value) {
    // Полный сброс
    resetState()
    await new Promise(r => setTimeout(r, 50))
    await initFranchiseGroups()
    
    // После загрузки топиков - выбираем общий топик
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
  background: #0f0f0f;
}

/* Шапка */
.fc-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}
.fc-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 5px;
  flex-shrink: 0;
}
.fc-poster-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2a2a2a;
  font-size: 1.4rem;
}
.fc-header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}
.fc-title {
  font-size: .95rem;
  font-weight: 700;
  color: #e0e0e0;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fc-subtitle { font-size: .7rem; color: #666; }

.fc-header-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.fc-action-btn {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid #333;
  border-radius: 8px;
  background: transparent;
  color: #888;
  cursor: pointer;
  transition: all .15s;
}
.fc-action-btn:hover { background: #222; color: #ccc; }
.fc-action-btn.muted { color: #f59e0b; border-color: #f59e0b44; background: #f59e0b0a; }
.fc-action-btn.archived { color: #6366f1; border-color: #6366f144; background: #6366f10a; }

/* Баннеры */
.fc-muted-banner, .fc-archived-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 16px;
  font-size: .78rem;
  flex-shrink: 0;
}
.fc-muted-banner { background: #f59e0b1a; color: #f59e0b; border-bottom: 1px solid #f59e0b22; }
.fc-archived-banner { background: #6366f11a; color: #6366f1; border-bottom: 1px solid #6366f122; }
.fc-error-banner { background: #ef44441a; color: #ef4444; border-bottom: 1px solid #ef444422; padding: 8px 16px; font-size: .8rem; text-align: center; }
.fc-unmute-btn, .fc-unarchive-btn {
  background: none; border: 1px solid currentColor;
  border-radius: 5px; color: inherit; cursor: pointer;
  padding: 2px 10px; font-size: .75rem; transition: background .15s;
}
.fc-unmute-btn:hover, .fc-unarchive-btn:hover { background: rgba(255,255,255,.1); }

/* Темы */
.fc-topics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #141414;
  border-bottom: 1px solid #2a2a2a;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}
.fc-topics-header:hover { background: #1a1a1a; }
.fc-topics-title { font-size: .75rem; color: #666; font-weight: 600; }
.fc-topics-chevron {
  font-size: .75rem;
  color: #555;
  transition: transform .2s;
  display: inline-block;
}
.fc-topics-chevron.collapsed { transform: rotate(-90deg); }
.fc-topics {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 6px;
  background: #141414;
  border-bottom: 1px solid #2a2a2a;
  overflow-y: auto;
  max-height: 220px;
  flex-shrink: 0;
}
.fc-topic-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 8px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #888;
  cursor: pointer;
  font-size: .83rem;
  text-align: left;
  transition: background .15s, color .15s;
  width: 100%;
}
.fc-topic-btn:hover { background: #222; color: #ccc; }
.fc-topic-btn.active { background: #1e3a5f; color: #60a5fa; font-weight: 600; }

/* Постер топика */
.topic-poster-wrap {
  width: 26px; height: 38px;
  flex-shrink: 0;
  border-radius: 3px;
  overflow: hidden;
}
.topic-poster {
  width: 100%; height: 100%;
  object-fit: cover;
}
.topic-poster-fallback {
  display: flex; align-items: center; justify-content: center;
  background: #2a2a2a; font-size: .9rem;
  width: 100%; height: 100%;
}
.topic-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topic-badge {
  background: #ef4444; color: white;
  font-size: .6rem; font-weight: 700;
  border-radius: 10px; padding: 1px 5px; flex-shrink: 0;
}

/* Сообщения */
.fc-messages {
  flex: 1; overflow-y: auto; padding: 10px;
  display: flex; flex-direction: column; gap: 5px;
}
.fc-loading, .fc-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  flex: 1; color: #555; gap: 8px; font-size: .9rem;
}
.fc-empty span { font-size: 2rem; }
.fc-messages-list { display: flex; flex-direction: column; gap: 5px; }

.fc-msg { display: flex; align-items: flex-end; gap: 7px; }
.fc-msg.own { flex-direction: row-reverse; }
.fc-msg-avatar { width: 26px; height: 26px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.fc-msg-bubble {
  display: flex; flex-direction: column; max-width: 70%;
  padding: 5px 10px; border-radius: 12px;
  background: #2d2d2d; color: #fff; font-size: .83rem;
}
.fc-msg.own .fc-msg-bubble { background: #1e7cff; align-items: flex-end; }
.fc-msg-author { font-size: .68rem; color: #7c4dff; font-weight: 600; margin-bottom: 2px; }
.fc-msg.own .fc-msg-author { display: none; }
.fc-msg-text { line-height: 1.4; word-break: break-word; }
.fc-msg-time { font-size: .6rem; color: rgba(255,255,255,.5); margin-top: 2px; align-self: flex-end; }

/* Ввод */
.fc-input-area {
  flex-shrink: 0; padding: 7px 10px 10px;
  background: #1a1a1a; border-top: 1px solid #2a2a2a;
}
.fc-topic-label { display: block; font-size: .68rem; color: #60a5fa; margin-bottom: 4px; padding-left: 2px; }
.fc-input-row { display: flex; gap: 7px; align-items: center; }
.fc-input {
  flex: 1; padding: 7px 13px;
  border: 1px solid #2a2a2a; border-radius: 18px;
  background: #0f0f0f; color: #fff; font-size: .88rem; outline: none;
}
.fc-input:focus { border-color: #3b82f6; }
.fc-send-btn {
  width: 34px; height: 34px; border: none; border-radius: 50%;
  background: #3b82f6; color: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0; transition: background .15s;
}
.fc-send-btn:hover { background: #2563eb; }
.fc-send-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
