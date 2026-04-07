<template>
  <div class="unread-chats-list">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>Загрузка...</span>
    </div>

    <div v-else-if="unreadChats.length === 0" class="empty-state">
      <div class="empty-icon"> <SakuraIcon name="check" /> </div>
      <p>Нет непрочитанных сообщений</p>
    </div>

    <div v-else class="chats-container">
      <div class="chats-header">
        <h3>Непрочитанные сообщения</h3>
        <span class="unread-count">{{ totalUnreadCount }}</span>
      </div>

      <div class="chats-list">
        <div
          v-for="chat in unreadChats"
          :key="chat.id"
          :class="['chat-item', { 'group': chat.type === 'group', 'private': chat.type === 'private' }]"
          @click="openChat(chat)"
        >
          <div class="chat-avatar-container">
            <img
              v-if="chat.avatar_url"
              :src="chat.avatar_url"
              :alt="chat.name"
              class="chat-avatar"
            />
            <div v-else class="chat-avatar-placeholder">
              {{ getInitials(chat.name) }}
            </div>
          </div>

          <div class="chat-info">
            <div class="chat-name">{{ chat.name }}</div>
            <div class="chat-type">
              {{ chat.type === 'group' ? 'Группа' : 'Личный чат' }}
            </div>
          </div>

          <UnreadBadge :count="chat.unread_count" large />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatExtrasStore } from '@/stores/chatExtras'
import UnreadBadge from './UnreadBadge.vue'

interface Props {
  autoLoad?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoLoad: true
})

const router = useRouter()
const chatExtrasStore = useChatExtrasStore()

const loading = computed(() => chatExtrasStore.loadingUnread)
const unreadChats = computed(() => chatExtrasStore.unreadChats)
const totalUnreadCount = computed(() => chatExtrasStore.totalUnreadCount)

const openChat = (chat: any) => {
  router.push(`/chats/${chat.id}`)
}

const getInitials = (name: string) => {
  if (!name) return '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length === 0) return name.substring(0, 2).toUpperCase()
  return words.slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

onMounted(() => {
  if (props.autoLoad) {
    chatExtrasStore.loadUnreadChats()
  }
})

defineExpose({
  refresh: () => chatExtrasStore.loadUnreadChats()
})
</script>

<style scoped>
.unread-chats-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--color-divider-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.chats-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.chats-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.unread-count {
  padding: 0.25rem 0.75rem;
  background: #f44336;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.chats-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background-surface);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.chat-item:hover {
  background: var(--color-background-active);
  transform: translateX(4px);
}

.chat-item.group {
  border-left: 3px solid var(--color-accent);
}

.chat-item.private {
  border-left: 3px solid #9c27b0;
}

.chat-avatar-container {
  position: relative;
}

.chat-avatar,
.chat-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-avatar-placeholder {
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
}

.chat-item.private .chat-avatar-placeholder {
  background: #9c27b0;
}

.chat-info {
  flex: 1;
  min-width: 0;
}

.chat-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-type {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}
</style>
