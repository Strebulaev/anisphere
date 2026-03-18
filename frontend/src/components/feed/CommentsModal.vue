<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="comments-modal" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <h3>Комментарии ({{ post?.comments_count || 0 }})</h3>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Sort Tabs -->
      <div class="sort-tabs">
        <button
          :class="{ active: sortBy === 'top' }"
          @click="sortBy = 'top'"
        >
          Лучшие
        </button>
        <button
          :class="{ active: sortBy === 'new' }"
          @click="sortBy = 'new'"
        >
          Новые
        </button>
        <button
          :class="{ active: sortBy === 'old' }"
          @click="sortBy = 'old'"
        >
          По порядку
        </button>
      </div>

      <!-- Comments List -->
      <div class="comments-list" ref="commentsContainer">
        <div v-if="loading && comments.length === 0" class="loading-state">
          <div class="spinner"></div>
        </div>

        <div v-else-if="!loading && comments.length === 0" class="empty-state">
          <p>Пока нет комментариев. Будьте первым!</p>
        </div>

        <template v-else>
          <div
            v-for="comment in sortedComments"
            :key="comment.id"
            class="comment-thread"
            :id="`comment-${comment.id}`"
            :style="{ marginLeft: comment.level * 20 + 'px' }"
          >
            <div class="comment" :class="{ 'is-reply': comment.level > 0 }">
              <img
                :src="comment.author_avatar || defaultAvatar"
                class="avatar"
                @click="goToProfile(comment.author_username)"
              >
              <div class="comment-body">
                <div class="comment-header">
                  <span class="author" @click="goToProfile(comment.author_username)">
                    {{ comment.author_username }}
                  </span>
                  <!-- Ссылка на родительский комментарий для ответов -->
                  <span v-if="comment.parent_id" class="reply-to-link" @click="scrollToComment(comment.parent_id)">
                    ↳ @{{ comment.parent_username }}
                  </span>
                  <span class="time">{{ formatTime(comment.created_at) }}</span>
                  <span v-if="comment.is_edited" class="edited">(ред.)</span>
                </div>

                <div v-if="comment.is_deleted" class="deleted-comment">
                  [комментарий удалён]
                </div>
                <p v-else class="comment-text">{{ comment.content }}</p>

                <div class="comment-actions">
                  <button
                    @click="likeComment(comment)"
                    :class="{ active: comment.is_liked }"
                  >
                    {{ comment.is_liked ? '❤️' : '🤍' }}
                    <span v-if="comment.likes_count > 0">{{ comment.likes_count }}</span>
                  </button>
                  <button
                    @click="dislikeComment(comment)"
                    :class="{ active: comment.is_disliked }"
                  >
                    {{ comment.is_disliked ? '👎' : '👍' }}
                    <span v-if="comment.dislikes_count > 0">{{ comment.dislikes_count }}</span>
                  </button>
                  <button @click="replyTo(comment)" v-if="!comment.is_deleted">
                    💬 Ответить
                  </button>
                  <button @click="openMenu(comment)" class="more-btn">
                    ⋯
                  </button>
                </div>

                <!-- Replies Preview -->
                <div
                  v-if="comment.replies_count > 0 && !showReplies[comment.id]"
                  class="replies-preview"
                  @click="loadReplies(comment)"
                >
                  Показать ещё {{ comment.replies_count }} ответов
                </div>
              </div>
            </div>

            <!-- Nested Replies -->
            <div v-if="showReplies[comment.id]" class="replies">
              <div
                v-for="reply in comment.replies"
                :key="reply.id"
                class="comment is-reply"
                :style="{ marginLeft: '20px' }"
              >
                <img :src="reply.author_avatar || defaultAvatar" class="avatar">
                <div class="comment-body">
                  <div class="comment-header">
                    <span class="author">{{ reply.author_username }}</span>
                    <span class="time">{{ formatTime(reply.created_at) }}</span>
                  </div>
                  <p class="comment-text">{{ reply.content }}</p>
                  <div class="comment-actions">
                    <button @click="likeComment(reply)">
                      {{ reply.is_liked ? '❤️' : '🤍' }} {{ reply.likes_count }}
                    </button>
                    <button @click="replyTo(reply)">💬 Ответить</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Comment Input -->
      <div class="comment-input-area">
        <img :src="currentUser?.avatar || defaultAvatar" class="avatar">
        <div class="input-wrapper">
          <input
            v-model="newComment"
            :placeholder="replyToComment ? `Ответ @${replyToComment.author_username}...` : 'Написать комментарий...'"
            @keyup.enter="submitComment"
            :disabled="sending"
          >
          <button
            @click="submitComment"
            :disabled="sending || !newComment.trim()"
            class="send-btn"
          >
            ➤
          </button>
        </div>
        <button v-if="replyToComment" class="cancel-reply" @click="replyToComment = null">
          ✕
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { normalizeComment } from '@/utils/normalizers'

interface Post {
  id: number
  comments_count: number
  author_username: string
  author_avatar: string | null
}

interface Comment {
  id: number
  author: number
  author_username: string
  author_avatar: string | null
  parent: number | null
  parent_id: number | null
  parent_username: string | null
  content: string
  likes_count: number
  dislikes_count: number
  replies_count: number
  level: number
  is_edited: boolean
  is_deleted: boolean
  created_at: string
  is_liked: boolean
  is_disliked: boolean
  replies?: Comment[]
}

const props = defineProps<{
  post: Post | null
}>()

const emit = defineEmits<{
  close: []
  'comment-added': [comment: Comment]
}>()

const router = useRouter()
const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`

const comments = ref<Comment[]>([])
const loading = ref(false)
const sending = ref(false)
const newComment = ref('')
const sortBy = ref<'top' | 'new' | 'old'>('top')
const replyToComment = ref<Comment | null>(null)
const currentUser = ref<any>(null)
const showReplies = ref<Record<number, boolean>>({})
const commentsContainer = ref<HTMLElement | null>(null)

// Computed
const sortedComments = computed(() => {
  const rootComments = comments.value.filter(c => c.level === 0)

  if (sortBy.value === 'new') {
    return rootComments.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  } else if (sortBy.value === 'old') {
    return rootComments.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
  } else {
    // Top - комбинация лайков и даты
    return rootComments.sort((a, b) => {
      const scoreA = a.likes_count / Math.pow((Date.now() - new Date(a.created_at).getTime()) / 3600000 + 2, 0.5)
      const scoreB = b.likes_count / Math.pow((Date.now() - new Date(b.created_at).getTime()) / 3600000 + 2, 0.5)
      return scoreB - scoreA
    })
  }
})

// Methods
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин.`
  if (hours < 24) return `${hours} ч.`
  if (days < 7) return `${days} дн.`

  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const loadComments = async () => {
  if (!props.post?.id) return

  loading.value = true
  try {
    const response = await apiClient.get(`/social/posts/${props.post.id}/comments/`)
    comments.value = response.data.results || response.data || []
  } catch (error) {
    console.error('Error loading comments:', error)
  } finally {
    loading.value = false
  }
}

const loadReplies = async (comment: Comment) => {
  if (!comment.id) return

  try {
    // Используем правильный endpoint для replies к комментариям постов
    const response = await apiClient.get(`/social/posts/comments/${comment.id}/replies/`)
    comment.replies = response.data || []
    showReplies.value[comment.id] = true
  } catch (error) {
    console.error('Error loading replies:', error)
    // Fallback - пробуем старый endpoint
    try {
      const response = await apiClient.get(`/social/comments/${comment.id}/replies/`)
      comment.replies = response.data || []
      showReplies.value[comment.id] = true
    } catch (error2) {
      console.error('Error loading replies (fallback):', error2)
    }
  }
}

const submitComment = async () => {
  if (!newComment.value.trim() || !props.post?.id) return

  sending.value = true
  try {
    const data: any = {
      content: newComment.value
    }

    if (replyToComment.value) {
      data.parent = replyToComment.value.id
    }

    const response = await apiClient.post(`/social/posts/${props.post.id}/comments/`, data)
    // normalize missing fields before inserting
    const newC = normalizeComment(response.data)

    // Добавляем комментарий в список
    if (replyToComment.value) {
      // Это ответ
      if (!replyToComment.value.replies) {
        replyToComment.value.replies = []
      }
      replyToComment.value.replies.push(newC)
      replyToComment.value.replies_count++
    } else {
      comments.value.push(newC)
    }

    newComment.value = ''
    replyToComment.value = null
    emit('comment-added', newC)

    // Прокрутка к новому комментарию
    await nextTick()
    if (commentsContainer.value) {
      commentsContainer.value.scrollTop = commentsContainer.value.scrollHeight
    }
  } catch (error) {
    console.error('Error submitting comment:', error)
  } finally {
    sending.value = false
  }
}

const likeComment = async (comment: Comment) => {
  try {
    const response = await apiClient.post(`/social/comments/${comment.id}/like/`)
    comment.is_liked = response.data.liked
    if (response.data.liked) {
      comment.likes_count++
      if (comment.is_disliked) {
        comment.is_disliked = false
        comment.dislikes_count--
      }
    } else {
      comment.likes_count--
    }
  } catch (error) {
    console.error('Error liking comment:', error)
  }
}

const dislikeComment = async (comment: Comment) => {
  try {
    const response = await apiClient.post(`/social/comments/${comment.id}/dislike/`)
    comment.is_disliked = response.data.disliked
    if (response.data.disliked) {
      comment.dislikes_count++
      if (comment.is_liked) {
        comment.is_liked = false
        comment.likes_count--
      }
    } else {
      comment.dislikes_count--
    }
  } catch (error) {
    console.error('Error disliking comment:', error)
  }
}

const replyTo = (comment: Comment) => {
  replyToComment.value = comment
}

const openMenu = (comment: Comment) => {
  // Открыть меню комментария
}

const goToProfile = (username: string) => {
  router.push(`/profile/${username}`)
}

const scrollToComment = async (commentId: number) => {
  // Ищем комментарий в списке
  const findComment = (list: Comment[]): Comment | null => {
    for (const c of list) {
      if (c.id === commentId) return c
      if (c.replies) {
        const found = findComment(c.replies)
        if (found) return found
      }
    }
    return null
  }
  
  const targetComment = findComment(comments.value)
  
  if (targetComment) {
    // Если нужно, загружаем replies для родительского комментария
    if (targetComment.replies_count > 0 && !showReplies.value[targetComment.id]) {
      await loadReplies(targetComment)
    }
    
    // Прокрутка к комментарию
    await nextTick()
    const element = document.getElementById(`comment-${commentId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Подсветка комментария
      element.classList.add('highlighted')
      setTimeout(() => element.classList.remove('highlighted'), 2000)
    }
  }
}

const fetchCurrentUser = async () => {
  try {
    const response = await apiClient.get('/users/me/')
    currentUser.value = response.data
  } catch (error) {
    console.error('Error fetching user:', error)
  }
}

onMounted(() => {
  fetchCurrentUser()
  loadComments()
})

watch(() => props.post?.id, () => {
  if (props.post?.id) {
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
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.comments-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h3 {
  color: #fff;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
}

.sort-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.sort-tabs button {
  background: none;
  border: none;
  color: #666;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
}

.sort-tabs button.active {
  background: #667eea;
  color: white;
}

.comments-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.comment-thread {
  margin-bottom: 1rem;
  transition: background-color 0.3s;
}

.comment-thread.highlighted {
  background-color: rgba(102, 126, 234, 0.15);
  border-radius: 8px;
  padding: 0.5rem;
  margin: 0 -0.5rem 1rem -0.5rem;
}

.comment {
  display: flex;
  gap: 0.75rem;
}

.comment.is-reply {
  margin-top: 0.75rem;
  padding-left: 0.5rem;
  border-left: 2px solid #252525;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
  flex-shrink: 0;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.author {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.reply-to-link {
  color: #667eea;
  font-size: 0.8rem;
  cursor: pointer;
}

.reply-to-link:hover {
  text-decoration: underline;
}

.author:hover {
  text-decoration: underline;
}

.time {
  color: #555;
  font-size: 0.8rem;
}

.edited {
  color: #444;
  font-size: 0.75rem;
  font-style: italic;
}

.deleted-comment {
  color: #555;
  font-style: italic;
}

.comment-text {
  color: #ddd;
  line-height: 1.5;
  margin: 0 0 0.5rem;
}

.comment-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.comment-actions button {
  background: none;
  border: none;
  color: #666;
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.comment-actions button:hover {
  background: #1a1a1a;
  color: #888;
}

.comment-actions button.active {
  color: #667eea;
}

.more-btn {
  margin-left: auto;
}

.replies-preview {
  color: #667eea;
  font-size: 0.85rem;
  cursor: pointer;
  margin-top: 0.5rem;
}

.replies-preview:hover {
  text-decoration: underline;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #1f1f1f;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state p {
  color: #666;
}

.comment-input-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.comment-input-area .avatar {
  width: 32px;
  height: 32px;
}

.input-wrapper {
  flex: 1;
  display: flex;
  gap: 0.5rem;
  background: #1a1a1a;
  border-radius: 20px;
  padding: 0.25rem;
}

.input-wrapper input {
  flex: 1;
  background: transparent;
  border: none;
  color: #ddd;
  padding: 0.5rem 1rem;
  border-radius: 20px;
}

.input-wrapper input:focus {
  outline: none;
}

.input-wrapper input::placeholder {
  color: #555;
}

.send-btn {
  background: #667eea;
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-reply {
  background: #1a1a1a;
  color: #666;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
}
</style>
