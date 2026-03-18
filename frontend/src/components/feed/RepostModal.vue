<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="repost-modal" @click.stop>
      <div class="modal-header">
        <h2>Сделать репост</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Original Post Preview -->
      <div class="original-post" v-if="post">
        <div class="preview-label">Оригинальный пост:</div>
        <div class="post-preview">
          <img :src="post.author_avatar || defaultAvatar" class="avatar">
          <div class="preview-content">
            <span class="author">{{ post.author_display_name || post.author_username }}</span>
            <span class="text">{{ truncateText(post.text, 100) }}</span>
          </div>
        </div>
      </div>

      <!-- Comment -->
      <div class="comment-section">
        <label>Добавить комментарий:</label>
        <textarea
          v-model="comment"
          placeholder="Ваш комментарий (опционально)"
          maxlength="500"
        ></textarea>
        <span class="char-count">{{ comment.length }}/500</span>
      </div>

      <!-- Destination -->
      <div class="destination-section">
        <label>Куда репостнуть:</label>
        <div class="destination-options">
          <label class="option" :class="{ selected: destination === 'feed' }">
            <input type="radio" value="feed" v-model="destination">
            <span class="icon">📱</span>
            <div class="option-content">
              <span class="title">В мою ленту</span>
              <span class="desc">Пост появится в вашем профиле</span>
            </div>
          </label>

          <label class="option" :class="{ selected: destination === 'chat' }">
            <input type="radio" value="chat" v-model="destination">
            <span class="icon">💬</span>
            <div class="option-content">
              <span class="title">В чат</span>
              <span class="desc">Отправить в личку или группу</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Chat Selector -->
      <div v-if="destination === 'chat'" class="selector-section">
        <label>Выберите чат:</label>
        <div class="search-row">
          <input
            type="text"
            v-model="chatSearch"
            placeholder="Поиск чатов..."
            class="search-input"
          >
        </div>
        <div v-if="loadingChats" class="loading-chats">Загрузка...</div>
        <div v-else class="chats-list">
          <div
            v-for="chat in filteredChats"
            :key="chat.id + '-' + chat.type"
            class="chat-item"
            :class="{ selected: selectedChat?.id === chat.id && selectedChat?.type === chat.type }"
            @click="selectedChat = chat"
          >
            <img :src="chat.avatar || defaultAvatar" class="avatar-sm">
            <div class="chat-item-info">
              <span class="chat-item-name">{{ chat.name }}</span>
              <span class="chat-item-type">{{ chat.type === 'private' ? 'Личный чат' : 'Группа' }}</span>
            </div>
            <span v-if="chat.is_online" class="online-dot"></span>
          </div>
          <div v-if="filteredChats.length === 0" class="empty">
            Нет чатов
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
        <button
          class="btn-repost"
          :disabled="!canRepost || reposting"
          @click="submitRepost"
        >
          {{ reposting ? 'Отправка...' : 'Репостнуть' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import apiClient from '@/api/client'

interface Post {
  id: number
  author_username: string
  author_avatar: string | null
  author_display_name: string | null
  text: string
}

interface Chat {
  id: number
  type: 'private' | 'group'
  name: string
  avatar: string | null
  is_online?: boolean
  members_count?: number
}

const props = defineProps<{
  post: Post | null
}>()

const emit = defineEmits<{
  close: []
  reposted: [post: Post]
}>()

const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3C/svg%3E`

const comment = ref('')
const destination = ref<'feed' | 'chat'>('feed')
const selectedChat = ref<Chat | null>(null)
const chats = ref<Chat[]>([])
const chatSearch = ref('')
const loadingChats = ref(false)
const reposting = ref(false)

const canRepost = computed(() => {
  if (destination.value === 'feed') return true
  if (destination.value === 'chat') return selectedChat.value !== null
  return false
})

const filteredChats = computed(() => {
  if (!chatSearch.value.trim()) return chats.value
  const search = chatSearch.value.toLowerCase()
  return chats.value.filter(chat => 
    chat.name.toLowerCase().includes(search)
  )
})

const truncateText = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const loadChats = async () => {
  loadingChats.value = true
  try {
    const response = await apiClient.get('/social/chats/for-forward/')
    chats.value = response.data || []
  } catch (error) {
    console.error('Error loading chats:', error)
  } finally {
    loadingChats.value = false
  }
}

const submitRepost = async () => {
  if (!props.post || !canRepost.value) return

  reposting.value = true

  try {
    if (destination.value === 'feed') {
      // Репост в ленту
      const { data } = await apiClient.post(`/social/posts/${props.post.id}/repost/action/`, {
        comment: comment.value
      })
      console.log('Repost response:', data)
      emit('reposted', props.post)
    } else if (destination.value === 'chat' && selectedChat.value) {
      // Пересылка в чат
      await apiClient.post(`/social/chats/${selectedChat.value.id}/forward/`, {
        post_id: props.post.id,
        message: comment.value
      })
      emit('reposted', props.post)
    }
    emit('close')
  } catch (error) {
    console.error('Error reposting:', error)
    alert('Ошибка при репосте')
  } finally {
    reposting.value = false
  }
}

onMounted(() => {
  loadChats()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.repost-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
}

.original-post {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.preview-label {
  color: #666;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.post-preview {
  display: flex;
  gap: 0.75rem;
  background: #1a1a1a;
  padding: 0.75rem;
  border-radius: 8px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.author {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}

.text {
  color: #888;
  font-size: 0.85rem;
}

.comment-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.comment-section label {
  display: block;
  color: #888;
  margin-bottom: 0.5rem;
}

.comment-section textarea {
  width: 100%;
  min-height: 60px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.75rem;
  color: #ddd;
  resize: vertical;
}

.comment-section textarea:focus {
  outline: none;
  border-color: #667eea;
}

.char-count {
  display: block;
  text-align: right;
  color: #555;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.destination-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.destination-section label {
  display: block;
  color: #888;
  margin-bottom: 0.75rem;
}

.destination-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option:hover {
  background: #252525;
}

.option.selected {
  background: #252525;
  border: 1px solid #667eea;
}

.option input {
  display: none;
}

.option .icon {
  font-size: 1.25rem;
}

.option-content {
  display: flex;
  flex-direction: column;
}

.option-content .title {
  color: #fff;
  font-weight: 500;
}

.option-content .desc {
  color: #666;
  font-size: 0.8rem;
}

.selector-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.selector-section label {
  display: block;
  color: #888;
  margin-bottom: 0.75rem;
}

.groups-list,
.chats-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.group-item,
.chat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.group-item:hover,
.chat-item:hover {
  background: #1a1a1a;
}

.group-item.selected,
.chat-item.selected {
  background: #252525;
  border: 1px solid #667eea;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.group-item span,
.chat-item span {
  color: #ddd;
}

.empty {
  color: #666;
  text-align: center;
  padding: 1rem;
}

.search-row {
  margin-bottom: 0.75rem;
}

.search-input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  color: #ddd;
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.loading-chats {
  color: #666;
  text-align: center;
  padding: 1rem;
}

.chat-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-item-name {
  color: #ddd;
}

.chat-item-type {
  color: #666;
  font-size: 0.75rem;
}

.online-dot {
  width: 8px;
  height: 8px;
  background: #22c55e;
  border-radius: 50%;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
}

.btn-cancel {
  background: #1a1a1a;
  color: #888;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
}

.btn-repost {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-repost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
