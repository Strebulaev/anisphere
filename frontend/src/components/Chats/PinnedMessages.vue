<template>
  <div v-if="pinnedMessages.length > 0" class="pinned-messages">
    <div class="pinned-header">
      <span class="pinned-icon">📌</span>
      <span class="pinned-title">Закреплённые сообщения ({{ pinnedMessages.length }})</span>
    </div>

    <div class="pinned-list">
      <div
        v-for="message in pinnedMessages"
        :key="message.id"
        class="pinned-item"
        @click="goToMessage(message.id)"
      >
        <div class="pinned-content">
          <div class="pinned-sender">{{ message.sender_username }}</div>
          <div class="pinned-text">{{ message.text || 'Медиа-сообщение' }}</div>
          <div class="pinned-meta">
            <span class="pinned-date">{{ formatDate(message.pinned_at || message.created_at) }}</span>
            <span v-if="message.pinned_by_username" class="pinned-by">
              закрепил {{ message.pinned_by_username }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'

interface Props {
  chatId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'message-selected', messageId: number): void
}>()

const chatExtrasStore = useChatExtrasStore()

const pinnedMessages = computed(() => {
  return chatExtrasStore.pinnedMessages
})

const goToMessage = (messageId: number) => {
  emit('message-selected', messageId)
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Только что'
  if (diffMins < 60) return `${diffMins} мин. назад`
  if (diffHours < 24) return `${diffHours} ч. назад`
  if (diffDays < 7) return `${diffDays} дн. назад`

  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}

onMounted(() => {
  chatExtrasStore.loadPinnedMessages(props.chatId)
})
</script>

<style scoped>
.pinned-messages {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-background-surface);
  border-bottom: 1px solid var(--color-divider);
  margin-bottom: 1rem;
}

.pinned-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.pinned-icon {
  font-size: 1rem;
}

.pinned-title {
  color: var(--color-text);
}

.pinned-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pinned-item {
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border-left: 3px solid var(--color-accent);
}

.pinned-item:hover {
  background: var(--color-background-active);
}

.pinned-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pinned-sender {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.pinned-text {
  font-size: 0.9rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pinned-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.pinned-date {
  color: var(--color-text-tertiary);
}

.pinned-by {
  color: var(--color-accent);
}
</style>
