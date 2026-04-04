<template>
  <div class="chats-view">
    <div class="chats-container">
      <!-- Левая панель с папками и списком чатов -->
      <div 
        ref="chatsSidebar"
        class="chats-sidebar"
        :class="{ 'mobile-hidden': mobileChatOpen }"
        :style="{ width: isMobile ? '100%' : sidebarWidth + 'px' }"
      >
        <ChatList
          :active-chat-id="activeChatId"
          :active-franchise-id="activeFranchiseId"
          @chat-selected="handleChatSelected"
        />
      </div>

      <!-- Резизер (только десктоп) -->
      <div
        v-if="!isMobile"
        class="chats-sidebar-resizer"
        @mousedown="startResize"
      ></div>

      <!-- Правая панель с чатом -->
      <div 
        class="chats-main"
        :class="{ 'mobile-active': mobileChatOpen }"
      >
        <!-- Мобильная стрелка назад -->
        <button 
          v-if="isMobile && (activeChatId || activeFranchiseId)" 
          class="mobile-back-btn"
          @click="goBackToList"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5"/>
            <path d="M12 19l-7-7 7-7"/>
          </svg>
        </button>

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
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
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

// ── Мобильная логика ───────────────────────────────────────
const isMobile = ref(false)
const mobileChatOpen = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const goBackToList = () => {
  mobileChatOpen.value = false
  // Сбрасываем активный чат
  activeChatId.value = undefined
  activeFranchiseId.value = undefined
  franchiseData.value = null
  // Обновляем URL
  router.push('/chats')
}

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
  
  // На мобильных - показывать чат, скрывать список
  if (isMobile.value) {
    mobileChatOpen.value = true
  }
  
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
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  await loadChats()
  const slug = route.params.slug as string | undefined
  if (slug) {
    await handleRouteSlug(slug)
    // На мобильных - сразу показывать чат
    if (isMobile.value && (activeChatId.value || activeFranchiseId.value)) {
      mobileChatOpen.value = true
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
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
  background: var(--surface-1);
  overflow: hidden;
  position: relative;
}

/* Фоновый узор */
.chats-view::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.03) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.03) 0%, transparent 40%);
  pointer-events: none;
}

.chats-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.chats-sidebar {
  min-width: 200px;
  max-width: 600px;
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface-1) 100%);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  position: relative;
}

.chats-sidebar-resizer {
  width: 4px;
  background: var(--border-subtle);
  cursor: ew-resize;
  flex-shrink: 0;
  transition: all var(--duration-base) var(--ease-petal);
}

.chats-sidebar-resizer:hover {
  background: var(--accent);
  box-shadow: var(--shadow-glow-sm);
}

.chats-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
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
  color: var(--text-tertiary);
  font-size: 1rem;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--surface-5);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.no-chat-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-1);
}

.no-chat-content {
  text-align: center;
  color: var(--text-tertiary);
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
  stroke: var(--text-tertiary);
}

.no-chat-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.no-chat-content p {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Мобильная адаптация */
@media (max-width: 767px) {
  .chats-view {
    height: 100vh;
    margin-top: 54px;
  }
  
  .chats-sidebar {
    width: 100% !important;
    border-right: none;
    position: absolute;
    inset: 0;
    z-index: 10;
    transition: transform 0.3s var(--ease-petal);
  }
  
  .chats-sidebar.mobile-hidden {
    transform: translateX(-100%);
  }
  
  .chats-main {
    position: absolute;
    inset: 0;
    z-index: 20;
    background: var(--surface-1);
    transform: translateX(100%);
    transition: transform 0.3s var(--ease-petal);
  }
  
  .chats-main.mobile-active {
    transform: translateX(0);
  }
  
.mobile-back-btn {
  display: none;
  position: absolute;
  top: 54px;
  left: 10px;
  z-index: 30;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 50%;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: all var(--duration-base) var(--ease-petal);
}

.mobile-back-btn:hover {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: var(--accent);
}
}
  
/* md: 768px+ */
@media (min-width: 768px) {
  .chats-view {
    display: flex;
    flex-direction: row;
    height: calc(100vh - 80px);
  }
  
  .chats-sidebar {
    width: 20rem;
    border-right: 1px solid var(--border-subtle);
  }
  
  .chats-main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .chat-header {
    height: 4rem;
    padding: 1rem;
  }
  
  .chat-messages {
    flex: 1;
    padding: 1rem;
    gap: 0.5rem;
  }
  
  .chat-message {
    max-width: 80%;
    padding: 0.75rem 1rem;
  }
  
  .chat-input-wrapper {
    padding: 1rem;
    gap: 0.75rem;
  }
  
  .chat-input {
    padding: 0.75rem 1rem;
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .chats-sidebar {
    width: 24rem;
  }
  
  .chat-message {
    max-width: 70%;
  }
}
</style>
