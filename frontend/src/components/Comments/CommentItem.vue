<template>
  <div class="comment-item" :class="{ 'is-reply': comment.is_reply }">
    <div class="comment-main">
      <OptimizedImage
        :src="comment.author_avatar || defaultAvatar"
        :alt="comment.author_username"
        class="comment-avatar"
      />
      
      <div class="comment-content">
        <!-- Header -->
        <div class="comment-header">
          <span class="comment-author" @click="$router.push(`/profile/${comment.author_username}`)">
            {{ comment.author_username }}
          </span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <span v-if="comment.is_edited" class="edited-badge">(ред.)</span>
          <div class="comment-actions">
            <button v-if="canEdit" @click="startEdit" class="action-link">Редактировать</button>
            <button v-if="canDelete" @click="$emit('delete', comment.id)" class="action-link danger">Удалить</button>
          </div>
        </div>

        <!-- Reply/Quote to parent -->
        <QuoteCard
          v-if="comment.reply_to && !editing"
          :quote="{
            id: comment.reply_to.id,
            author: {
              id: comment.reply_to.author_id,
              username: comment.reply_to.author_username,
              avatar_url: comment.reply_to.author_avatar || undefined
            },
            content: comment.reply_to.text,
            type: 'text',
            timestamp: comment.reply_to.created_at,
            comment_id: comment.reply_to.id
          }"
          :can-click="true"
          :show-avatar="false"
          @click="goToComment(comment.reply_to.id)"
        />

        <!-- Comment text -->
        <div v-if="!editing" class="comment-text" :class="{ 'has-reply': !!comment.reply_to }">
          {{ comment.text }}
        </div>

        <!-- Edit form -->
        <form v-else @submit.prevent="saveEdit" class="edit-form">
          <textarea
            v-model="editText"
            class="edit-textarea"
            rows="3"
            required
          ></textarea>
          <div class="edit-actions">
            <button
              type="submit"
              :disabled="!editText.trim() || editLoading"
              class="btn-save"
            >
              {{ editLoading ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button
              type="button"
              @click="cancelEdit"
              class="btn-cancel"
            >
              Отмена
            </button>
          </div>
        </form>

        <!-- Footer actions -->
        <div v-if="!editing" class="comment-footer">
          <button v-if="!showReplyForm" @click="showReplyForm = true" class="reply-btn">
            Ответить
          </button>
          <span v-if="comment.replies_count > 0" class="replies-count">
            {{ comment.replies_count }} {{ pluralizeReplies(comment.replies_count) }}
          </span>
        </div>

        <!-- Reply form -->
        <div v-if="showReplyForm" class="reply-form">
          <div class="reply-header">
            <SakuraIcon name="reply" :size="14" />
            <span>Ответ на комментарий</span>
          </div>
          <textarea
            v-model="replyText"
            class="reply-textarea"
            rows="3"
            placeholder="Напишите ответ..."
            required
          ></textarea>
          <div class="reply-actions">
            <button
              type="button"
              @click="submitReply"
              :disabled="!replyText.trim() || replyLoading"
              class="btn-submit"
            >
              {{ replyLoading ? 'Отправка...' : 'Ответить' }}
            </button>
            <button
              type="button"
              @click="showReplyForm = false"
              class="btn-cancel"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Replies -->
    <div v-if="comment.replies && comment.replies.length > 0" class="comment-replies">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :content-type="contentType"
        :object-id="objectId"
        @reply="$emit('reply', $event, reply.id)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import QuoteCard from '@/components/ui/QuoteCard.vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'
import api from '@/api/client'

interface ReplyTo {
  id: number
  author_id: number
  author_username: string
  author_avatar: string | null
  text: string
  created_at: string
}

interface Comment {
  id: number
  text: string
  author: number
  author_username: string
  author_avatar: string | null
  parent: number | null
  reply_to?: ReplyTo
  is_reply: boolean
  is_edited: boolean
  replies_count: number
  created_at: string
  updated_at: string
  is_deleted: boolean
  replies?: Comment[]
}

interface Props {
  comment: Comment
  contentType: string
  objectId: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  reply: [text: string, parentId: number]
  delete: [commentId: number]
}>()

const router = useRouter()
const authStore = useAuthStore()
const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3C/svg%3E`

const showReplyForm = ref(false)
const replyText = ref('')
const replyLoading = ref(false)
const editing = ref(false)
const editText = ref('')
const editLoading = ref(false)

const canEdit = computed(() =>
  authStore.user && authStore.user.id === props.comment.author
)

const canDelete = computed(() =>
  authStore.user && authStore.user.id === props.comment.author
)

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const now = Date.now()
  const diff = now - date.getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(mins / 60)
  const days = Math.floor(hours / 24)
  
  if (mins < 1) return 'только что'
  if (mins < 60) return `${mins} мин назад`
  if (hours < 24) return `${hours} ч назад`
  if (days < 7) return `${days} дн назад`
  return date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })
}

const pluralizeReplies = (count: number) => {
  if (count % 10 === 1 && count % 100 !== 11) return 'ответ'
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return 'ответа'
  return 'ответов'
}

const submitReply = async () => {
  if (!replyText.value.trim()) return

  try {
    replyLoading.value = true
    emit('reply', replyText.value, props.comment.id)
    replyText.value = ''
    showReplyForm.value = false
  } catch (error) {
    console.error('Failed to submit reply:', error)
  } finally {
    replyLoading.value = false
  }
}

const startEdit = () => {
  editText.value = props.comment.text
  editing.value = true
}

const saveEdit = async () => {
  if (!editText.value.trim()) return

  try {
    editLoading.value = true
    await api.patch(`/social/comments/${props.comment.id}/`, {
      text: editText.value
    })
    props.comment.text = editText.value
    props.comment.is_edited = true
    editing.value = false
  } catch (error) {
    console.error('Failed to edit comment:', error)
  } finally {
    editLoading.value = false
  }
}

const cancelEdit = () => {
  editText.value = props.comment.text
  editing.value = false
}

const goToComment = (commentId: number) => {
  // Scroll to comment or open modal
  console.log('Go to comment:', commentId)
}
</script>

<style scoped>
.comment-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-subtle);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-item.is-reply {
  margin-left: 2rem;
  padding-left: 1rem;
  border-left: 2px solid var(--border-subtle);
}

.comment-main {
  display: flex;
  gap: 0.75rem;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.25rem;
}

.comment-author {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--accent-bright);
  cursor: pointer;
  transition: color 0.15s;
}

.comment-author:hover {
  color: var(--accent);
}

.comment-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.edited-badge {
  font-size: 0.68rem;
  color: var(--text-tertiary);
  font-style: italic;
}

.comment-actions {
  margin-left: auto;
  display: flex;
  gap: 0.75rem;
}

.action-link {
  background: none;
  border: none;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.action-link:hover {
  color: var(--accent);
}

.action-link.danger:hover {
  color: var(--danger);
}

.comment-text {
  color: var(--text-primary);
  font-size: 0.875rem;
  line-height: 1.55;
  margin-bottom: 0.5rem;
  word-break: break-word;
}

.comment-text.has-reply {
  margin-top: 0.5rem;
}

.edit-form {
  margin-bottom: 0.5rem;
}

.edit-textarea {
  width: 100%;
  padding: 0.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 0.875rem;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.15s;
}

.edit-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-save,
.btn-cancel,
.btn-submit {
  padding: 0.4rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}

.btn-save {
  background: var(--accent);
  color: var(--text-on-accent);
}

.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-cancel {
  background: var(--surface-4);
  color: var(--text-primary);
}

.btn-cancel:hover {
  background: var(--surface-5);
}

.btn-submit {
  background: var(--accent);
  color: var(--text-on-accent);
}

.btn-submit:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comment-footer {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.reply-btn {
  background: none;
  border: none;
  font-size: 0.8rem;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition: color 0.15s;
}

.reply-btn:hover {
  color: var(--accent);
}

.replies-count {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.reply-form {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: var(--surface-4);
  border-radius: var(--radius-md);
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.reply-textarea {
  width: 100%;
  padding: 0.5rem;
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 0.875rem;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.15s;
}

.reply-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.reply-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.comment-replies {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-left: 2rem;
  margin-top: 0.75rem;
  padding-left: 1rem;
  border-left: 2px solid var(--border-subtle);
}
</style>