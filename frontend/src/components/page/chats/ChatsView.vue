<template>
  <div class="chats-view">
    <div class="chats-container">
      <!-- Левая панель с папками и списком чатов -->
      <div 
        ref="chatsSidebar"
        class="chats-sidebar"
        :style="{ width: sidebarWidth + 'px' }"
      >
        <ChatList
          :active-chat-id="activeChatId"
          :active-franchise-id="activeFranchiseId"
          @chat-selected="handleChatSelected"
        />
      </div>

      <!-- Резизер -->
      <div
        class="chats-sidebar-resizer"
        @mousedown="startResize"
      ></div>

      <!-- Правая панель с чатом -->
      <div class="chats-main">
        <!-- Загрузка -->
        <div v-if="isRouteLoading" class="chat-loading">
          <div class="loading-spinner"></div>
          <span>Загрузка...</span>
        </div>

        <!-- Обсуждение франшизы -->
        <div v-else-if="franchiseData && activeFranchiseId" class="chat-detail">
          <FranchiseDiscussionChat
            :key="`fdisc-${activeFranchiseId}`"
            :franchise-id="activeFranchiseId"
            :franchise-slug="franchiseSlug"
            :franchise-name="franchiseName"
            :franchise-poster="franchisePoster"
            :parts="franchiseParts"
            :initial-topic-slug="topicSlug ?? undefined"
          />
        </div>

        <!-- Обычный чат -->
        <div v-else-if="activeChatId" class="chat-detail">
          <ChatDetailView :key="`chat-${activeChatId}`" :chat-id="activeChatId" />
        </div>

        <!-- Ничего не выбрано -->
        <div v-else class="no-chat-selected">
          <div class="no-chat-content">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <h2>Выберите чат</h2>
            <p>Выберите чат из списка слева или создайте новый</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatList from '@/components/Chats/ChatList.vue'
import ChatDetailView from '@/components/page/chats/ChatDetailView.vue'
import FranchiseDiscussionChat from '@/components/Chats/FranchiseDiscussionChat.vue'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const privateChatStore = usePrivateChatStore()
const groupChatStore = useGroupChatStore()

// ── Активный чат/франшиза ──────────────────────────────────
const activeChatId = ref<number | undefined>(undefined)
const activeFranchiseId = ref<number | undefined>(undefined)

// ── Состояние загрузки ─────────────────────────────────────
const isRouteLoading = ref(false)
const isChatsLoaded = ref(false)

// ── Сайдбар ────────────────────────────────────────────────
const sidebarWidth = ref(350)
const chatsSidebar = ref<HTMLElement | null>(null)
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)

// ── Данные франшизы ───────────────────────────────────────
const franchiseData = ref<any>(null)
const franchiseLoading = ref(false)

// ── SLUG UTILS ─────────────────────────────────────────────
const makeSlug = (text: string | null | undefined): string => {
  if (!text) return ''
  const translitMap: Record<string, string> = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i',
    'й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'',
    'э':'e','ю':'yu','я':'ya',
    ' ':'-','_':'-','.':'-',',':'-','!':'','?':'','(': '', ')': '', '"': "", "'": "", ':': '', ';': '', '/': '-', '\\': '-',
  }
  let slug = String(text).toLowerCase()
  for (const [from, to] of Object.entries(translitMap)) {
    slug = slug.split(from).join(to)
  }
  return slug.replace(/-+/g, '-').replace(/[^a-z0-9\-]/g, '').replace(/^-|-$/g, '') || 'unknown'
}

// ── Топик slug для передачи во FranchiseDiscussionChat ─────
// Формат URL: /chats/{franchiseSlug} или /chats/{franchiseSlug}-{topicSuffix}
const topicSlug = computed((): string | null => {
  if (!franchiseData.value) return null
  const urlSlug = route.params.slug as string
  if (!urlSlug) return null
  const baseSlug = franchiseData.value.slug || makeSlug(franchiseData.value.name)
  // Если urlSlug === baseSlug — это общее обсуждение (topicSlug = null)
  if (urlSlug === baseSlug) return null
  // Если urlSlug начинается с baseSlug + '-' — это топик
  if (urlSlug.startsWith(baseSlug + '-')) {
    return urlSlug.slice(baseSlug.length + 1) || null
  }
  return null
})

const franchiseName = computed(() => franchiseData.value?.name || '')
const franchiseSlug = computed(() => {
  if (franchiseData.value?.slug) return franchiseData.value.slug
  return makeSlug(franchiseData.value?.name || '')
})
const franchisePoster = computed(() => franchiseData.value?.poster_image_url || franchiseData.value?.poster_url || '')
const franchiseParts = computed(() => {
  if (!franchiseData.value?.entries) return []
  return [...franchiseData.value.entries].sort((a: any, b: any) => (a.franchise_order || 0) - (b.franchise_order || 0))
})

// ── Загрузка франшизы по slug ──────────────────────────────
const loadFranchiseBySlug = async (slug: string): Promise<boolean> => {
  franchiseLoading.value = true
  try {
    // Пробуем поиск по slug
    for (const params of [{ slug }, { search: slug.replace(/-/g, ' ') }]) {
      const res = await apiClient.get('/anime/franchises/', { params })
      const results = res.data?.results || []
      if (results.length > 0) {
        franchiseData.value = results[0]
        activeFranchiseId.value = results[0].id
        return true
      }
    }
    return false
  } catch {
    return false
  } finally {
    franchiseLoading.value = false
  }
}

// ── Загрузка аниме чата по slug ───────────────────────────
const loadAnimeChatBySlug = async (slug: string): Promise<boolean> => {
  try {
    for (const params of [{ slug }, { search: slug.replace(/-/g, ' ') }]) {
      const res = await apiClient.get('/anime/', { params })
      const results = res.data?.results || []
      if (results.length > 0) {
        const anime = results[0]
        const discussionRes = await apiClient.get(`/anime/${anime.id}/discussion-group/`)
        if (discussionRes.data?.id) {
          activeChatId.value = discussionRes.data.id
          return true
        }
      }
    }
    return false
  } catch {
    return false
  }
}

// ── Основная функция обработки slug из route ──────────────
const handleRouteSlug = async (slug: string | null) => {
  console.log('[ChatsView] handleRouteSlug called with:', slug)
  
  // Полный сброс при ЛЮБОМ изменении
  activeChatId.value = undefined
  activeFranchiseId.value = undefined
  franchiseData.value = null

  if (!slug) return

  isRouteLoading.value = true
  try {
    // Числовой ID → обычный чат
    const num = parseInt(slug)
    if (!isNaN(num)) {
      console.log('[ChatsView] Setting activeChatId:', num)
      activeChatId.value = num
      return
    }

    // Slug (не числовой) — пробуем найти franchise
    console.log('[ChatsView] Trying to find franchise by slug:', slug)
    const found = await loadFranchiseBySlug(slug)
    if (found) {
      console.log('[ChatsView] Franchise found:', franchiseData.value?.name)
      // FranchiseDiscussionChat отобразится и сам обработает топик из URL
      return
    }
    
    // Не нашли franchise — пробуем anime discussion
    const animeFound = await loadAnimeChatBySlug(slug)
    if (animeFound) {
      console.log('[ChatsView] Anime discussion found')
      return
    }
    
    // Ничего не найдено — показываем "выберите чат"
    console.log('[ChatsView] Nothing found, showing no chat')
    
  } finally {
    isRouteLoading.value = false
    console.log('[ChatsView] handleRouteSlug done, chatId:', activeChatId.value, 'franchiseId:', activeFranchiseId.value)
  }
}

// ── Обработчик выбора чата из списка ─────────────────────
const handleChatSelected = async (chat: any) => {
  console.log('[ChatsView] handleChatSelected:', chat)
  
  // Полный сброс перед открытием нового чата
  activeChatId.value = undefined
  activeFranchiseId.value = undefined
  franchiseData.value = null
  
  // Для franchise чатов - загружаем данные франшизы
  if (chat.franchise_id) {
    // Загружаем franchise данные
    const found = await loadFranchiseById(chat.franchise_id)
    if (found) {
      // Открываем FranchiseDiscussionChat
      return
    }
    // Если не нашли - fallback на обычный чат
  }
  
  // Для anime discussion - открываем как обычный чат по ID
  if (chat.discussion_type === 'anime' && chat.anime_id) {
    activeChatId.value = chat.id
    return
  }
  
  // Обычный чат
  if (route.params.slug !== String(chat.id)) {
    router.push(`/chats/${chat.id}`)
  }
}

// ── Загрузка франшизы по ID ──────────────────────────────
const loadFranchiseById = async (id: number): Promise<boolean> => {
  franchiseLoading.value = true
  try {
    const res = await apiClient.get(`/anime/franchises/${id}/`)
    if (res.data) {
      franchiseData.value = res.data
      activeFranchiseId.value = res.data.id
      return true
    }
    return false
  } catch {
    return false
  } finally {
    franchiseLoading.value = false
  }
}

// ── Загрузка списков чатов ────────────────────────────────
const loadChats = async () => {
  try {
    await Promise.all([
      privateChatStore.loadChats(),
      groupChatStore.loadGroupChats()
    ])
  } catch (error) {
    console.error('Error loading chats:', error)
  } finally {
    isChatsLoaded.value = true
  }
}

// ── Ресайзер ──────────────────────────────────────────────
const startResize = (event: MouseEvent) => {
  isResizing.value = true
  startX.value = event.clientX
  startWidth.value = sidebarWidth.value
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}
const handleResize = (event: MouseEvent) => {
  if (!isResizing.value) return
  sidebarWidth.value = Math.max(200, Math.min(600, startWidth.value + event.clientX - startX.value))
}
const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// ── Инициализация ─────────────────────────────────────────
onMounted(async () => {
  await loadChats()
  const slug = route.params.slug as string | undefined
  if (slug) {
    await handleRouteSlug(slug)
  }
})

// ── Watch: реагируем на смену slug в URL ──────────────────
watch(
  () => route.params.slug as string | undefined,
  async (newSlug, oldSlug) => {
    // Пропускаем если slug не изменился
    if (newSlug === oldSlug) return

    // Если уже загружена franchise - проверяем, это смена топика или новый чат
    if (franchiseData.value && newSlug) {
      const baseSlug = franchiseData.value.slug || makeSlug(franchiseData.value.name)
      // Если новый slug начинается с того же baseSlug - это смена топика, НЕ сбрасываем
      if (newSlug === baseSlug || newSlug.startsWith(baseSlug + '-')) {
        // Это смена топика - НЕ сбрасываем franchise данные
        // FranchiseDiscussionChat сам обработает смену топика через props.initialTopicSlug
        return
      }
    }

    // Полный сброс при смене на другой чат
    activeChatId.value = undefined
    activeFranchiseId.value = undefined
    franchiseData.value = null
    
    await handleRouteSlug(newSlug ?? null)
  }
)
</script>

<style scoped>
.chats-view {
  height: 90vh;
  display: flex;
  flex-direction: column;
  background-color: #0f0f0f;
  overflow: hidden;
}

.chats-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.chats-sidebar {
  min-width: 200px;
  max-width: 600px;
  flex-shrink: 0;
  background: #1a1a1a;
  border-right: 1px solid #2a2a2a;
  display: flex;
  flex-direction: column;
  position: relative;
}

.chats-sidebar-resizer {
  width: 4px;
  background: #2a2a2a;
  cursor: ew-resize;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.chats-sidebar-resizer:hover {
  background: #3b82f6;
}

.chats-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f0f0f;
  overflow: hidden;
}

.chat-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #666;
  font-size: 1rem;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #333;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.no-chat-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0f0f;
}

.no-chat-content {
  text-align: center;
  color: #888;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.no-chat-content svg {
  width: 80px;
  height: 80px;
  margin-bottom: 1rem;
  opacity: 0.4;
  stroke: #666;
}

.no-chat-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0 0 0.5rem 0;
}

.no-chat-content p {
  font-size: 1rem;
  color: #888;
  margin: 0;
}

@media (max-width: 768px) {
  .chats-sidebar {
    width: 100% !important;
    border-right: none;
  }
  .chats-main {
    display: none;
  }
  .chats-main.active {
    display: flex;
  }
}
</style>
