<template>
  <div class="comment-thread">
    <div class="comment-form mb-6">
      <h3 class="text-lg font-semibold mb-3">Оставить комментарий</h3>
      <form @submit.prevent="submitComment">
        <textarea
          v-model="newCommentText"
          class="w-full p-3 border border-gray-300 rounded-lg resize-y min-h-[100px]"
          placeholder="Напишите ваш комментарий..."
          required
        ></textarea>
        <button
          type="submit"
          :disabled="!newCommentText.trim() || loading"
          class="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Отправка...' : 'Отправить' }}
        </button>
      </form>
    </div>

    <div class="comments-list">
      <div v-if="comments.length === 0" class="text-gray-500 text-center py-8">
        Пока нет комментариев. Будьте первым!
      </div>

      <div v-else class="space-y-4">
        <CommentItem
          v-for="comment in topLevelComments"
          :key="comment.id"
          :comment="comment"
          :content-type="contentType"
          :object-id="objectId"
          @reply="handleReply"
          @delete="handleDelete"
        />
      </div>

      <div v-if="loading" class="text-center py-4">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/client'
import CommentItem from './CommentItem.vue'

interface Comment {
  id: number
  text: string
  author: number
  author_username: string
  author_avatar: string | null
  parent: number | null
  is_reply: boolean
  replies_count: number
  created_at: string
  updated_at: string
  is_deleted: boolean
}

interface Props {
  contentType: string
  objectId: number
}

const props = defineProps<Props>()

const authStore = useAuthStore()
const comments = ref<Comment[]>([])
const newCommentText = ref('')
const loading = ref(false)

const topLevelComments = computed(() =>
  comments.value.filter(comment => !comment.parent)
)

const fetchComments = async () => {
  try {
    loading.value = true
    const response = await api.get('/social/comments/', {
      params: {
        content_type: props.contentType,
        object_id: props.objectId
      }
    })
    comments.value = response.data
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  } finally {
    loading.value = false
  }
}

const submitComment = async () => {
  if (!newCommentText.value.trim()) return

  try {
    loading.value = true
    await api.post('/social/comments/', {
      text: newCommentText.value,
      content_type: props.contentType,
      object_id: props.objectId
    })
    newCommentText.value = ''
    await fetchComments()
  } catch (error) {
    console.error('Failed to submit comment:', error)
  } finally {
    loading.value = false
  }
}

const handleReply = async (replyText: string, parentId: number) => {
  try {
    await api.post('/social/comments/', {
      text: replyText,
      parent: parentId,
      content_type: props.contentType,
      object_id: props.objectId
    })
    await fetchComments()
  } catch (error) {
    console.error('Failed to reply to comment:', error)
  }
}

const handleDelete = async (commentId: number) => {
  try {
    await api.delete(`/social/comments/${commentId}/`)
    await fetchComments()
  } catch (error) {
    console.error('Failed to delete comment:', error)
  }
}

onMounted(() => {
  fetchComments()
})
</script>

<style scoped>
.comment-thread {
  @apply bg-white p-6 rounded-lg shadow-md;
}
</style>