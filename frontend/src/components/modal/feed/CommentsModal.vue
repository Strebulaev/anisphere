<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal comments-modal" @click.stop>
      <div class="modal-header">
        <h3>Комментарии ({{ comments.length }})</h3>
        <button @click="$emit('close')" class="close-btn">×</button>
      </div>
      
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка комментариев...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button @click="loadComments" class="retry-btn">Попробовать снова</button>
      </div>

      <template v-else>
        <div v-if="comments.length === 0" class="empty-state">
          <p>Пока нет комментариев. Будьте первым!</p>
        </div>

        <div v-else class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-avatar">
              <img v-if="comment.author?.avatar_url" :src="comment.author.avatar_url" />
              <span v-else class="placeholder">{{ comment.author?.username?.[0] || '?' }}</span>
            </div>
            <div class="comment-content">
              <div class="comment-header">
                <span class="comment-author">{{ comment.author?.username || 'Неизвестный' }}</span>
                <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
              </div>
              <p class="comment-text">{{ comment.text }}</p>
            </div>
          </div>
        </div>

        <div class="comment-input">
          <input
            v-model="newComment"
            type="text"
            placeholder="Написать комментарий..."
            @keyup.enter="sendComment"
            :disabled="sending"
          />
          <button @click="sendComment" class="send-btn" :disabled="sending || !newComment.trim()">
            {{ sending ? '...' : '→' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import apiClient from '@/api/client'

interface Author {
  id: number
  username: string
  avatar_url?: string
}

interface Comment {
  id: number
  author: Author
  text: string
  created_at: string
}

interface Post {
  id: number
  author_username: string
  author_avatar: string | null
  text: string
  image_url: string | null
  video_url: string | null
  likes_count: number
  comments_count: number
  created_at: string
}

interface Props {
  show: boolean
  post: Post
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

const comments = ref<Comment[]>([])
const loading = ref(false)
const error = ref('')
const sending = ref(false)
const newComment = ref('')

const loadComments = async () => {
  if (!props.post?.id) return

  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get(`/social/posts/${props.post.id}/comments/`)
    comments.value = response.data.results || response.data || []
  } catch (err: any) {
    console.error('Error loading comments:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить комментарии'
  } finally {
    loading.value = false
  }
}

const sendComment = async () => {
  if (!newComment.value.trim() || !props.post?.id) return

  sending.value = true

  try {
    const response = await apiClient.post(`/social/posts/${props.post.id}/comments/`, {
      text: newComment.value.trim()
    })
    comments.value.push(response.data)
    newComment.value = ''
  } catch (err: any) {
    console.error('Error sending comment:', err)
    alert('Не удалось отправить комментарий')
  } finally {
    sending.value = false
  }
}

const formatDate = (date: string) => {
  const d = new Date(date)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

watch(() => props.show, (newShow) => {
  if (newShow) {
    loadComments()
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
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
}

.comments-modal {
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: var(--secondary-text);
  padding: 0;
  line-height: 1;
}

.comments-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.comment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.comment-avatar .placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.comment-content {
  flex: 1;
}

.comment-header {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.comment-author {
  font-weight: 600;
}

.comment-date {
  font-size: 12px;
  color: var(--secondary-text);
}

.comment-text {
  margin: 0;
  line-height: 1.4;
}

.comment-input {
  display: flex;
  gap: 10px;
  padding: 15px 20px;
  border-top: 1px solid var(--border-color);
}

.comment-input input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--bg-color);
  color: var(--text-color);
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state p,
.empty-state p {
  color: var(--secondary-text);
  margin: 15px 0 20px;
}

.retry-btn {
  padding: 10px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.retry-btn:hover {
  background: var(--primary-color-hover);
}
</style>
