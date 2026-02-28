<template>
  <div class="comment-item">
    <div class="flex space-x-3">
      <img
        :src="comment.author_avatar || '/missing_original.jpg'"
        :alt="comment.author_username"
        class="w-10 h-10 rounded-full"
      >
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-1">
          <span class="font-semibold text-sm">{{ comment.author_username }}</span>
          <span class="text-xs text-gray-500">{{ formatDate(comment.created_at) }}</span>
          <button
            v-if="canEdit"
            @click="editing = true"
            class="text-xs text-blue-600 hover:underline"
          >
            Редактировать
          </button>
          <button
            v-if="canDelete"
            @click="$emit('delete', comment.id)"
            class="text-xs text-red-600 hover:underline"
          >
            Удалить
          </button>
        </div>

        <div v-if="!editing" class="text-gray-700 mb-2">
          {{ comment.text }}
        </div>

        <form v-else @submit.prevent="saveEdit" class="mb-2">
          <textarea
            v-model="editText"
            class="w-full p-2 border border-gray-300 rounded resize-y min-h-[60px]"
            required
          ></textarea>
          <div class="flex space-x-2 mt-1">
            <button
              type="submit"
              :disabled="!editText.trim() || editLoading"
              class="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {{ editLoading ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button
              type="button"
              @click="cancelEdit"
              class="px-3 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600"
            >
              Отмена
            </button>
          </div>
        </form>

        <div class="flex items-center space-x-4 text-sm text-gray-500">
          <button
            v-if="!showReplyForm"
            @click="showReplyForm = true"
            class="hover:text-blue-600"
          >
            Ответить
          </button>
          <span v-if="comment.replies_count > 0">
            {{ comment.replies_count }} {{ pluralizeReplies(comment.replies_count) }}
          </span>
        </div>

        <div v-if="showReplyForm" class="mt-3">
          <form @submit.prevent="submitReply">
            <textarea
              v-model="replyText"
              class="w-full p-2 border border-gray-300 rounded resize-y min-h-[60px]"
              placeholder="Напишите ответ..."
              required
            ></textarea>
            <div class="flex space-x-2 mt-1">
              <button
                type="submit"
                :disabled="!replyText.trim() || replyLoading"
                class="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {{ replyLoading ? 'Отправка...' : 'Ответить' }}
              </button>
              <button
                type="button"
                @click="showReplyForm = false"
                class="px-3 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Replies -->
    <div v-if="comment.replies && comment.replies.length > 0" class="ml-12 mt-3 space-y-3">
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
import { useAuthStore } from '@/stores/auth'
import api from '@/api/client'

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

const authStore = useAuthStore()
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

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

const saveEdit = async () => {
  if (!editText.value.trim()) return

  try {
    editLoading.value = true
    await api.patch(`/social/comments/${props.comment.id}/`, {
      text: editText.value
    })
    props.comment.text = editText.value
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
</script>

<style scoped>
.comment-item {
  @apply border-l-2 border-gray-200 pl-4;
}
</style>