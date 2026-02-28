<template>
  <div class="message-actions">
    <div class="actions-trigger" @click="toggleMenu">
      <span class="trigger-icon">⋯</span>
    </div>

    <Transition name="fade">
      <div v-if="isOpen" class="actions-menu" @click.stop>
        <div class="menu-header">
          <span class="menu-title">Действия</span>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="menu-items">
          <button v-if="canPin" class="menu-item" @click="handlePin" :disabled="loading">
            <span class="item-icon">{{ message.is_pinned ? '📌' : '📍' }}</span>
            <span class="item-text">{{ message.is_pinned ? 'Открепить' : 'Закрепить' }}</span>
          </button>

          <button class="menu-item" @click="handleForward" :disabled="loading">
            <span class="item-icon">↗️</span>
            <span class="item-text">Переслать</span>
          </button>

          <button class="menu-item" @click="handleReply" :disabled="loading">
            <span class="item-icon">↩️</span>
            <span class="item-text">Ответить</span>
          </button>

          <button v-if="message.sender_id === currentUserId" class="menu-item" @click="handleEdit" :disabled="loading">
            <span class="item-icon">✏️</span>
            <span class="item-text">Редактировать</span>
          </button>

          <button v-if="message.sender_id === currentUserId" class="menu-item delete" @click="handleDelete" :disabled="loading">
            <span class="item-icon">🗑️</span>
            <span class="item-text">Удалить</span>
          </button>

          <button class="menu-item" @click="handleCopy" :disabled="loading">
            <span class="item-icon">📋</span>
            <span class="item-text">Копировать текст</span>
          </button>

          <button class="menu-item" @click="handleReport" :disabled="loading">
            <span class="item-icon">⚠️</span>
            <span class="item-text">Пожаловаться</span>
          </button>
        </div>
      </div>
    </Transition>

    <ForwardMessageModal
      :is-open="showForwardModal"
      :message="message"
      :available-chats="availableChats"
      @close="showForwardModal = false"
      @forwarded="handleForwarded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAuthStore } from '@/stores/auth'
import ForwardMessageModal from '../modal/chats/ForwardMessageModal.vue'

interface Props {
  message: any
  availableChats: any[]
  canPin?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canPin: false
})

const emit = defineEmits<{
  (e: 'reply', message: any): void
  (e: 'edit', message: any): void
  (e: 'delete', messageId: number): void
  (e: 'pinned', message: any): void
  (e: 'unpinned', messageId: number): void
  (e: 'forwarded', data: any): void
}>()

const chatExtrasStore = useChatExtrasStore()
const authStore = useAuthStore()

const showNotification = (message: string, type: 'success' | 'error') => {
  console.log(`[${type}] ${message}`)
}

const showModal = (type: string, data?: any) => {
  console.log(`Modal: ${type}`, data)
}

const isOpen = ref(false)
const loading = ref(false)
const showForwardModal = ref(false)

const currentUserId = computed(() => authStore.user?.id || 0)

const toggleMenu = () => {
  isOpen.value = !isOpen.value
}

const close = () => {
  isOpen.value = false
}

const handlePin = async () => {
  loading.value = true
  try {
    if (props.message.is_pinned) {
      await chatExtrasStore.unpinMessage(props.message.id)
      emit('unpinned', props.message.id)
      showNotification('Сообщение откреплено', 'success')
    } else {
      const result = await chatExtrasStore.pinMessage(props.message.id)
      emit('pinned', result)
      showNotification('Сообщение закреплено', 'success')
    }
  } catch (error) {
    console.error('Error pinning message:', error)
    showNotification('Ошибка при закреплении сообщения', 'error')
  } finally {
    loading.value = false
    close()
  }
}

const handleForward = () => {
  showForwardModal.value = true
  close()
}

const handleForwarded = (data: any) => {
  emit('forwarded', data)
  showNotification('Сообщение переслано', 'success')
}

const handleReply = () => {
  emit('reply', props.message)
  close()
}

const handleEdit = () => {
  emit('edit', props.message)
  close()
}

const handleDelete = () => {
  showModal('confirm', {
    title: 'Удалить сообщение?',
    message: 'Это действие нельзя отменить.',
    onConfirm: async () => {
      loading.value = true
      try {
        emit('delete', props.message.id)
        showNotification('Сообщение удалено', 'success')
      } catch (error) {
        console.error('Error deleting message:', error)
        showNotification('Ошибка при удалении сообщения', 'error')
      } finally {
        loading.value = false
      }
    }
  })
  close()
}

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.message.text || '')
    showNotification('Текст скопирован', 'success')
  } catch (error) {
    console.error('Error copying text:', error)
    showNotification('Ошибка при копировании', 'error')
  }
  close()
}

const handleReport = () => {
  showModal('report', {
    type: 'message',
    id: props.message.id
  })
  close()
}

const handleInviteCreated = (invite: any) => {
  showNotification('Приглашение создано', 'success')
}

document.addEventListener('click', () => {
  isOpen.value = false
})
</script>

<style scoped>
.message-actions {
  position: relative;
}

.actions-trigger {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.actions-trigger:hover {
  background: var(--color-background-active);
  border-color: var(--color-accent);
}

.trigger-icon {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
}

.actions-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 100;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-divider-light);
}

.menu-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: var(--color-text);
}

.menu-items {
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  background: none;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  text-align: left;
  width: 100%;
}

.menu-item:hover:not(:disabled) {
  background: var(--color-background-active);
}

.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item.delete {
  color: #f44336;
}

.menu-item.delete:hover {
  background: rgba(244, 67, 54, 0.1);
}

.item-icon {
  font-size: 1.125rem;
}

.item-text {
  font-size: 0.875rem;
  color: var(--color-text);
}

.menu-item.delete .item-text {
  color: #f44336;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
