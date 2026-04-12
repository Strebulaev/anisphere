<template>
  <div class="comment-item border-b border-gray-200 dark:border-gray-700 py-4">
    <div class="flex space-x-3">
      <router-link :to="`/profile/${comment.author?.id}`">
        <img
          :src="comment.author?.avatar_url || '/default-avatar.png'"
          :alt="comment.author?.display_name || comment.author?.username"
          class="w-10 h-10 rounded-full object-cover"
        />
      </router-link>
      <div class="flex-1">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <router-link :to="`/profile/${comment.author?.id}`" class="font-semibold text-gray-900 dark:text-white hover:underline text-sm">
              {{ comment.author?.display_name || comment.author?.username || 'Аноним' }}
            </router-link>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatDate(comment.created_at) }}</span>
            <span v-if="comment.edited_at" class="text-xs text-gray-400">(изм.)</span>
          </div>
          <div v-if="canEdit || canDelete" class="relative">
            <button @click="showMenu = !showMenu" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
              <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
              </svg>
            </button>
            <div v-if="showMenu" class="absolute right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10 min-w-[120px]">
              <button
                v-if="canEdit"
                @click="startEditing"
                class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Редактировать
              </button>
              <button
                v-if="canDelete"
                @click="deleteComment"
                class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-if="isEditing" class="mt-2">
          <textarea
            v-model="editText"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          ></textarea>
          <div class="mt-2 flex space-x-2">
            <button
              @click="saveEdit"
              :disabled="editLoading"
              class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {{ editLoading ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button
              @click="cancelEdit"
              class="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Отмена
            </button>
          </div>
        </div>

        <!-- View Mode -->
        <p v-else class="mt-1 text-gray-700 dark:text-gray-300 text-sm whitespace-pre-wrap">
          {{ comment.text }}
        </p>

        <!-- Comment Actions -->
        <div class="mt-2 flex items-center space-x-4">
          <button
            @click="toggleLike"
            :class="isLiked ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'"
            class="flex items-center space-x-1 text-xs hover:text-red-500 transition-colors"
          >
            <svg class="w-4 h-4" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <span>{{ comment.likes_count || 0 }}</span>
          </button>
          <button
            @click="$emit('reply', comment)"
            class="text-xs text-gray-500 dark:text-gray-400 hover:text-blue-500 transition-colors"
          >
            Ответить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const props = defineProps<{
  comment: any
  postId: number
}>()

const emit = defineEmits<{
  deleted: []
  updated: []
  reply: [comment: any]
}>()

const authStore = useAuthStore()

const isEditing = ref(false)
const editText = ref('')
const editLoading = ref(false)
const showMenu = ref(false)
const isLiked = ref(false)

const canEdit = computed(() => {
  return authStore.user?.id === props.comment.author?.id
})

const canDelete = computed(() => {
  return authStore.user?.id === props.comment.author?.id || authStore.user?.is_staff
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return 'Только что'
  if (minutes < 60) return `${minutes} мин. назад`
  if (hours < 24) return `${hours} ч. назад`
  if (days < 7) return date.toLocaleDateString('ru-RU', { weekday: 'long' })
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const startEditing = () => {
  editText.value = props.comment.text
  isEditing.value = true
  showMenu.value = false
}

const cancelEdit = () => {
  isEditing.value = false
  editText.value = ''
}

const saveEdit = async () => {
  if (!editText.value.trim() || editLoading.value) return
  
  editLoading.value = true
  try {
    await apiClient.patch(`/social/comments/${props.comment.id}/`, {
      text: editText.value.trim()
    })
    emit('updated')
    isEditing.value = false
  } catch (e: any) {
    console.error('Error editing comment:', e)
    alert(e.response?.data?.error || 'Ошибка при редактировании')
  } finally {
    editLoading.value = false
  }
}

const deleteComment = async () => {
  if (!confirm('Удалить комментарий?')) return
  
  showMenu.value = false
  try {
    await apiClient.delete(`/social/comments/${props.comment.id}/`)
    emit('deleted')
  } catch (e: any) {
    console.error('Error deleting comment:', e)
    alert(e.response?.data?.error || 'Ошибка при удалении')
  }
}

const toggleLike = async () => {
  try {
    if (isLiked.value) {
      await apiClient.post(`/social/comments/${props.comment.id}/unlike/`)
      props.comment.likes_count = Math.max(0, (props.comment.likes_count || 0) - 1)
    } else {
      await apiClient.post(`/social/comments/${props.comment.id}/like/`)
      props.comment.likes_count = (props.comment.likes_count || 0) + 1
    }
    isLiked.value = !isLiked.value
  } catch (e: any) {
    console.error('Error toggling like:', e)
  }
}
</script>

<style scoped>
.comment-item:last-child {
  border-bottom: none;
}
</style>
