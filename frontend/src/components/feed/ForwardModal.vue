<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="forward-modal" @click.stop>
      <div class="modal-header">
        <h3>Переслать пост</h3>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="search-section">
        <input
          v-model="search"
          @input="debouncedSearch"
          placeholder="Поиск чатов и пользователей..."
          class="search-input"
          autofocus
        />
      </div>

      <div class="chats-list">
        <div v-if="loading" class="loading">
          <div v-for="i in 4" :key="i" class="skeleton-chat">
            <div class="skeleton-avatar"></div>
            <div class="skeleton-info">
              <div class="skeleton-line short"></div>
            </div>
          </div>
        </div>

        <div v-else-if="chats.length === 0" class="empty">
          <span>Нет доступных чатов</span>
        </div>

        <div
          v-else
          v-for="chat in chats"
          :key="chat.id"
          class="chat-item"
          :class="{ selected: selectedChatId === chat.id }"
          @click="selectChat(chat.id)"
        >
          <div class="chat-avatar">
            <img v-if="chat.avatar" :src="chat.avatar" :alt="chat.name" />
            <div v-else class="avatar-placeholder">{{ chat.name[0] }}</div>
            <span v-if="chat.type === 'private' && chat.is_online" class="online-dot"></span>
          </div>
          <div class="chat-info">
            <span class="chat-name">{{ chat.name }}</span>
            <span v-if="chat.type === 'group'" class="chat-meta">{{ chat.members_count }} участников</span>
          </div>
          <div v-if="selectedChatId === chat.id" class="check">✓</div>
        </div>
      </div>

      <div v-if="selectedChatId" class="comment-section">
        <textarea
          v-model="message"
          placeholder="Добавить сообщение (необязательно)..."
          class="message-input"
          rows="2"
        ></textarea>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
        <button
          class="btn-send"
          :disabled="!selectedChatId || sending"
          @click="sendForward"
        >
          {{ sending ? 'Отправка...' : 'Переслать' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { chatsApi, type ForwardChat } from '@/api/feed'

const props = defineProps<{
  post: { id: number; text?: string }
}>()

const emit = defineEmits<{
  close: []
  forwarded: []
}>()

const search = ref('')
const chats = ref<ForwardChat[]>([])
const loading = ref(true)
const selectedChatId = ref<number | null>(null)
const message = ref('')
const sending = ref(false)

let searchTimeout: ReturnType<typeof setTimeout> | null = null

const loadChats = async () => {
  loading.value = true
  try {
    const { data } = await chatsApi.getChatsForForward(search.value || undefined)
    chats.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Error loading chats:', error)
    chats.value = []
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadChats, 300)
}

const selectChat = (chatId: number) => {
  selectedChatId.value = selectedChatId.value === chatId ? null : chatId
}

const sendForward = async () => {
  if (!selectedChatId.value) return
  sending.value = true
  try {
    // Всегда отправляем пост, даже без комментария
    await chatsApi.forwardPost(selectedChatId.value, props.post.id, message.value || undefined)
    emit('forwarded')
    emit('close')
  } catch (error) {
    console.error('Error forwarding post:', error)
  } finally {
    sending.value = false
  }
}

onMounted(loadChats)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.forward-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  border: 1px solid #1f1f1f;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h3 {
  color: #fff;
  margin: 0;
  font-size: 1rem;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
}

.close-btn:hover { color: #fff; }

.search-section {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #1a1a1a;
}

.search-input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.6rem 0.9rem;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.chats-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
  min-height: 150px;
  max-height: 320px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.chat-item:hover { background: #1a1a1a; }
.chat-item.selected { background: #1a1f35; }

.chat-avatar {
  position: relative;
  flex-shrink: 0;
}

.chat-avatar img,
.avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  background: #2a2a2a;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1rem;
}

.online-dot {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 10px;
  height: 10px;
  background: #22c55e;
  border-radius: 50%;
  border: 2px solid #111;
}

.chat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-name {
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
}

.chat-meta {
  color: #666;
  font-size: 0.75rem;
}

.check {
  color: #667eea;
  font-weight: 700;
}

.comment-section {
  padding: 0.75rem 1rem;
  border-top: 1px solid #1a1a1a;
}

.message-input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.6rem 0.9rem;
  border-radius: 8px;
  font-size: 0.85rem;
  resize: none;
  box-sizing: border-box;
}

.message-input:focus {
  outline: none;
  border-color: #667eea;
}

.modal-footer {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding: 0.75rem 1rem;
  border-top: 1px solid #1f1f1f;
}

.btn-cancel {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-send {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.loading { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.5rem 1rem; }
.skeleton-chat { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; }
.skeleton-avatar { width: 40px; height: 40px; border-radius: 50%; background: #1f1f1f; animation: pulse 1.5s infinite; }
.skeleton-info { flex: 1; }
.skeleton-line { height: 12px; background: #1f1f1f; border-radius: 4px; animation: pulse 1.5s infinite; }
.skeleton-line.short { width: 50%; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.empty { text-align: center; padding: 2rem; color: #666; font-size: 0.9rem; }
</style>
