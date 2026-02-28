<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Переслать сообщение</h3>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="modal-body">
          <div v-if="messageToForward" class="message-preview">
            <div class="preview-header">Пересылаемое сообщение</div>
            <div class="preview-content">
              <div class="preview-sender">{{ messageToForward.sender_username }}</div>
              <div class="preview-text">{{ messageToForward.text || 'Медиа-сообщение' }}</div>
            </div>
          </div>

          <div class="chat-search">
            <label class="section-title">Выберите чат</label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Поиск чатов..."
              class="search-input"
            />
          </div>

          <div class="chat-list">
            <div
              v-for="chat in filteredChats"
              :key="chat.id"
              :class="['chat-item', { 'selected': selectedChatId === chat.id }]"
              @click="selectChat(chat.id)"
            >
              <img
                v-if="chat.avatar_url"
                :src="chat.avatar_url"
                :alt="chat.name"
                class="chat-avatar"
              />
              <div v-else class="chat-avatar-placeholder">
                {{ getInitials(chat.name) }}
              </div>
              <div class="chat-info">
                <div class="chat-name">{{ chat.name }}</div>
                <div class="chat-type">
                  {{ chat.type === 'group' ? 'Группа' : 'Личный чат' }}
                </div>
              </div>
              <div v-if="selectedChatId === chat.id" class="check-icon">✓</div>
            </div>

            <div v-if="filteredChats.length === 0" class="no-chats">
              Чаты не найдены
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn-cancel" @click="close">Отмена</button>
            <button
              class="btn-forward"
              @click="forwardMessage"
              :disabled="!selectedChatId || loading"
            >
              {{ loading ? 'Пересылка...' : 'Переслать' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { messageActionsApi } from '@/api/chats'

interface Chat {
  id: number
  name: string
  avatar_url?: string
  type: 'group' | 'private'
}

interface Message {
  id: number
  sender_username: string
  text: string
  chat_id?: number
  private_chat_id?: number
}

interface Props {
  isOpen: boolean
  message: Message | null
  availableChats: Chat[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'forwarded', data: any): void
}>()

const loading = ref(false)
const searchQuery = ref('')
const selectedChatId = ref<number | null>(null)

const messageToForward = computed(() => props.message)

const filteredChats = computed(() => {
  if (!searchQuery.value) {
    return props.availableChats.filter(
      chat => chat.id !== props.message?.chat_id && chat.id !== props.message?.private_chat_id
    )
  }

  const query = searchQuery.value.toLowerCase()
  return props.availableChats.filter(
    chat =>
      chat.name.toLowerCase().includes(query) &&
      chat.id !== props.message?.chat_id &&
      chat.id !== props.message?.private_chat_id
  )
})

const selectChat = (chatId: number) => {
  selectedChatId.value = chatId
}

const forwardMessage = async () => {
  if (!selectedChatId.value || !props.message) return

  loading.value = true
  try {
    const chat = filteredChats.value.find(c => c.id === selectedChatId.value)
    if (!chat) return

    const message = props.message
    if (!message.id) return

    const response = await messageActionsApi.forward(
      message.id!,
      chat.type === 'group' ? chat.id : undefined,
      chat.type === 'private' ? chat.id : undefined
    )

    emit('forwarded', response.data)
    close()
  } catch (error) {
    console.error('Error forwarding message:', error)
  } finally {
    loading.value = false
  }
}

const getInitials = (name: string) => {
  if (!name) return '?'
  const words = name.split(' ').filter(w => w.length > 0)
  if (words.length === 0) return name.substring(0, 2).toUpperCase()
  return words.slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

const close = () => {
  emit('close')
  searchQuery.value = ''
  selectedChatId.value = null
  loading.value = false
}

watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    searchQuery.value = ''
    selectedChatId.value = null
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--color-background-surface);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background: var(--color-background-active);
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.message-preview {
  padding: 1rem;
  background: var(--color-background);
  border-radius: 8px;
  border: 1px solid var(--color-divider-light);
}

.preview-header {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.preview-sender {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.preview-text {
  font-size: 0.9rem;
  color: var(--color-text);
}

.chat-search {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.search-input {
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--color-background);
  color: var(--color-text);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.chat-item:hover {
  background: var(--color-background-active);
}

.chat-item.selected {
  background: rgba(58, 134, 255, 0.1);
}

.chat-avatar,
.chat-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.chat-avatar-placeholder {
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
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

.check-icon {
  width: 24px;
  height: 24px;
  background: var(--color-accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
}

.no-chats {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider);
}

.btn-cancel {
  padding: 0.625rem 1.25rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: var(--color-background-active);
}

.btn-forward {
  padding: 0.625rem 1.25rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-forward:hover {
  background: var(--color-accent-hover);
}

.btn-forward:disabled {
  background: var(--color-text-disabled);
  cursor: not-allowed;
}
</style>
