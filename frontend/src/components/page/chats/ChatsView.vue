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
        <div v-if="activeChatId" class="chat-detail">
          <ChatDetailView :chat-id="activeChatId" />
        </div>
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
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatList from '@/components/Chats/ChatList.vue'
import ChatDetailView from '@/components/page/chats/ChatDetailView.vue'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'

const route = useRoute()
const router = useRouter()
const privateChatStore = usePrivateChatStore()
const groupChatStore = useGroupChatStore()
const activeChatId = ref<number | undefined>(undefined)
const isLoading = ref(true)
const sidebarWidth = ref(350)
const chatsSidebar = ref<HTMLElement | null>(null)
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)

const handleChatSelected = (chat: any) => {
  activeChatId.value = chat.id
  // Переходим на URL чата
  router.push(`/chats/${chat.id}`)
}

const loadChats = async () => {
  isLoading.value = true
  try {
    await Promise.all([
      privateChatStore.loadChats(),
      groupChatStore.loadGroupChats()
    ])
  } catch (error) {
    console.error('Error loading chats:', error)
  } finally {
    isLoading.value = false
  }
}

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

  const deltaX = event.clientX - startX.value
  const newWidth = startWidth.value + deltaX

  // Ограничиваем ширину от 200px до 600px
  sidebarWidth.value = Math.max(200, Math.min(600, newWidth))
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// Обработка id чата из route (при переходе по ссылке)
onMounted(async () => {
  // Сначала загружаем чаты
  await loadChats()
  
  // Затем устанавливаем активный чат из URL
  if (route.params.id) {
    activeChatId.value = parseInt(route.params.id as string)
  }
})

// Следим за изменением id в route
watch(() => route.params.id, (newId) => {
  if (newId) {
    activeChatId.value = parseInt(newId as string)
  } else {
    activeChatId.value = undefined
  }
})
</script>

<style scoped>
.chats-view {
  height: 90vh;
  display: flex;
  flex-direction: column;
  background-color: #0f0f0f;
  overflow: hidden;
}

.chats-view::-webkit-scrollbar {
  display: none;
}

.chats-view {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.chats-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.chats-container::-webkit-scrollbar {
  display: none;
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
}

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
    width: 100%;
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
