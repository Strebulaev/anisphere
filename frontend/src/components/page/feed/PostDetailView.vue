<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-4xl mx-auto px-4 py-4">
        <button
          @click="$router.back()"
          class="flex items-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Назад
        </button>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="max-w-4xl mx-auto px-4 py-8">
      <div class="animate-pulse space-y-4">
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        <div class="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="max-w-4xl mx-auto px-4 py-8">
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <h2 class="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Ошибка</h2>
        <p class="text-red-600 dark:text-red-300">{{ error }}</p>
        <button
          @click="loadPost"
          class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Попробовать снова
        </button>
      </div>
    </div>

    <!-- Post Content -->
    <div v-else-if="post" class="max-w-4xl mx-auto px-4 py-8">
      <article class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- Post Header -->
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-3">
              <router-link :to="`/profile/${post.author.id}`">
                <img
                  :src="post.author.avatar_url || '/default-avatar.png'"
                  :alt="post.author.display_name || post.author.username"
                  class="w-12 h-12 rounded-full object-cover"
                />
              </router-link>
              <div>
                <router-link :to="`/profile/${post.author.id}`" class="font-semibold text-gray-900 dark:text-white hover:underline">
                  {{ post.author.display_name || post.author.username }}
                </router-link>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ formatDate(post.created_at) }}
                  <span v-if="post.edited_at" class="text-gray-400">(изменено)</span>
                </p>
              </div>
            </div>
            <!-- Post Actions -->
            <PostMenu
              v-if="isOwnPost"
              :post="post"
              @edited="loadPost"
              @deleted="onPostDeleted"
            />
          </div>

          <!-- Post Content -->
          <div class="mt-4">
            <h1 v-if="post.title" class="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              {{ post.title }}
            </h1>
            <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {{ post.text }}
            </p>
          </div>

          <!-- Post Attachments -->
          <div v-if="post.anime" class="mt-4 flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
            <span>{{ post.anime.title_ru || post.anime.title_en }}</span>
          </div>

          <!-- Post Media -->
          <div v-if="post.media && post.media.length" class="mt-4 grid grid-cols-2 gap-2">
            <img
              v-for="(media, index) in post.media"
              :key="index"
              :src="media.url"
              :alt="`Media ${Number(index) + 1}`"
              class="rounded-lg object-cover max-h-64 w-full"
            />
          </div>
        </div>

        <!-- Post Stats -->
        <div class="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <span class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                {{ post.likes_count || 0 }}
              </span>
              <span class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                {{ post.comments_count || 0 }}
              </span>
              <span class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                {{ post.shares_count || 0 }}
              </span>
            </div>
            <span>{{ post.views_count || 0 }} просмотров</span>
          </div>
        </div>

        <!-- Post Actions -->
        <div class="px-6 py-3 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <button
                @click="toggleLike"
                :class="hasLiked ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'"
                class="flex items-center space-x-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :disabled="!isOwnPost && !canInteract"
              >
                <svg class="w-5 h-5" :fill="hasLiked ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                <span>{{ hasLiked ? 'Лайк' : 'Нравится' }}</span>
              </button>
              <button
                @click="scrollToComments"
                class="flex items-center space-x-1 px-3 py-2 text-gray-500 dark:text-gray-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :disabled="!isOwnPost && !canInteract"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>Комментировать</span>
              </button>
              <button
                @click="showRepostModal = true"
                class="flex items-center space-x-1 px-3 py-2 text-gray-500 dark:text-gray-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                :disabled="!isOwnPost && !canInteract"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
                <span>Поделиться</span>
              </button>
            </div>
            <button
              @click="toggleBookmark"
              :class="hasBookmarked ? 'text-yellow-500' : 'text-gray-500 dark:text-gray-400'"
              class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <svg class="w-5 h-5" :fill="hasBookmarked ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Comments Section -->
        <div ref="commentsSection" class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Комментарии ({{ comments.length }})
          </h3>

          <!-- Comment Input -->
          <div v-if="canInteract || isOwnPost" class="mb-6">
            <!-- Reply Preview -->
            <div v-if="replyToCommentId" class="mb-3 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  Ответ на комментарий
                </span>
                <button
                  @click="replyToCommentId = null; newComment = ''"
                  class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div class="flex space-x-3">
              <img
                :src="authStore.user?.avatar || '/default-avatar.png'"
                class="w-10 h-10 rounded-full object-cover"
              >
              <div class="flex-1">
                <textarea
                  v-model="newComment"
                  :placeholder="replyToCommentId ? 'Написать ответ...' : 'Напишите комментарий...'"
                  rows="3"
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  @keydown.ctrl.enter="submitComment"
                ></textarea>
                <div class="mt-2 flex justify-end">
                  <button
                    @click="submitComment"
                    :disabled="!newComment.trim() || commentLoading"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ commentLoading ? 'Отправка...' : (replyToCommentId ? 'Ответить' : 'Отправить') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments List -->
          <div class="space-y-4">
            <PostComment
              v-for="comment in comments"
              :key="comment.id"
              :comment="comment"
              :post-id="postId"
              @deleted="loadComments"
              @updated="loadComments"
              @reply="handleCommentReply"
            />
          </div>

          <!-- No Comments -->
          <div v-if="comments.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p>Будьте первым, кто прокомментирует!</p>
          </div>
        </div>
      </article>
    </div>

    <!-- Repost Modal -->
    <RepostModal
      v-if="showRepostModal"
      :post="post!"
      @close="showRepostModal = false"
      @reposted="onReposted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore } from '@/stores/feed'
import apiClient from '@/api/client'
import PostMenu from '@/components/feed/PostMenu.vue'
import PostComment from '@/components/feed/PostComment.vue'
import RepostModal from '@/components/feed/RepostModal.vue'

const route = useRoute()
const authStore = useAuthStore()
const feedStore = useFeedStore()

const postId = computed(() => Number(route.params.id))

const loading = ref(true)
const error = ref<string | null>(null)
const post = ref<any>(null)
const comments = ref<any[]>([])
const newComment = ref('')
const commentLoading = ref(false)
const replyToCommentId = ref<number | null>(null)
const hasLiked = ref(false)
const hasBookmarked = ref(false)
const showRepostModal = ref(false)

const commentsSection = ref<HTMLElement | null>(null)

const isOwnPost = computed(() => {
  return authStore.user?.id === post.value?.author.id
})

const canInteract = computed(() => {
  // На странице поста всегда можно взаимодействовать (это не профиль другого пользователя)
  return true
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return 'Вчера'
  } else if (days < 7) {
    return date.toLocaleDateString('ru-RU', { weekday: 'long' })
  } else {
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
  }
}

const loadPost = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Используем публичный endpoint для загрузки поста
    const response = await apiClient.get(`/social/posts/${postId.value}/public/`)
    post.value = response.data
    
    // Track view
    await apiClient.post(`/social/posts/${postId.value}/view/`).catch(() => {})
    
    // Check like status
    hasLiked.value = post.value.is_liked || false
    hasBookmarked.value = post.value.is_bookmarked || false
    
    await loadComments()
  } catch (e: any) {
    console.error('Error loading post:', e)
    error.value = e.response?.data?.error || 'Не удалось загрузить пост'
  } finally {
    loading.value = false
  }
}

const loadComments = async () => {
  try {
    const response = await apiClient.get(`/social/posts/${postId.value}/comments/`)
    comments.value = response.data.results || response.data || []
  } catch (e: any) {
    console.error('Error loading comments:', e)
  }
}

const toggleLike = async () => {
  if (!post.value) return
  
  try {
    if (hasLiked.value) {
      await apiClient.post(`/social/posts/${postId.value}/dislike/`)
      post.value.likes_count = Math.max(0, (post.value.likes_count || 0) - 1)
    } else {
      await apiClient.post(`/social/posts/${postId.value}/like/`)
      post.value.likes_count = (post.value.likes_count || 0) + 1
    }
    hasLiked.value = !hasLiked.value
  } catch (e: any) {
    console.error('Error toggling like:', e)
  }
}

const toggleBookmark = async () => {
  if (!post.value) return
  
  try {
    if (hasBookmarked.value) {
      await apiClient.post(`/social/posts/${postId.value}/bookmark/remove/`)
    } else {
      await apiClient.post(`/social/posts/${postId.value}/bookmark/`)
    }
    hasBookmarked.value = !hasBookmarked.value
  } catch (e: any) {
    console.error('Error toggling bookmark:', e)
  }
}

const handleCommentReply = (comment: any) => {
  replyToCommentId.value = comment.id
  newComment.value = `@${comment.author?.username || ''} `
  scrollToComments()
  // Фокус на поле ввода после прокрутки
  setTimeout(() => {
    const input = document.querySelector('textarea[name="comment"]') as HTMLTextAreaElement | null
    if (input) input.focus()
  }, 300)
}

const submitComment = async () => {
  if (!newComment.value.trim() || commentLoading.value) return
  
  commentLoading.value = true
  
  try {
    const data: any = {
      content: newComment.value.trim(),
      post: postId.value
    }
    
    // Если это ответ на комментарий
    if (replyToCommentId.value) {
      data.parent = replyToCommentId.value
    }
    
    const response = await apiClient.post(`/social/posts/${postId.value}/comments/`, data)
    
    newComment.value = ''
    replyToCommentId.value = null
    
    // Добавляем комментарий без полной перезагрузки
    const newCommentData = response.data
    if (replyToCommentId.value) {
      // Это ответ - ищем родительский комментарий и добавляем ответ
      const parentComment = comments.value.find(c => c.id === replyToCommentId.value)
      if (parentComment) {
        if (!parentComment.replies) {
          parentComment.replies = []
        }
        parentComment.replies.push(newCommentData)
        parentComment.replies_count = (parentComment.replies_count || 0) + 1
      }
    } else {
      // Это корневой комментарий
      comments.value.push(newCommentData)
    }
    
    // Update comments count
    if (post.value) {
      post.value.comments_count = (post.value.comments_count || 0) + 1
    }
  } catch (e: any) {
    console.error('Error submitting comment:', e)
    alert(e.response?.data?.error || 'Ошибка при отправке комментария')
  } finally {
    commentLoading.value = false
  }
}

const scrollToComments = () => {
  commentsSection.value?.scrollIntoView({ behavior: 'smooth' })
}

const onReposted = () => {
  showRepostModal.value = false
  if (post.value) {
    post.value.shares_count = (post.value.shares_count || 0) + 1
  }
}

const onPostDeleted = () => {
  // Показываем уведомление и перенаправляем на главную страницу ленты
  // Но делаем это без полной перезагрузки страницы
  alert('Пост успешно удалён')
  // Перенаправляем на ленту
  window.location.href = '/'
}

onMounted(() => {
  loadPost()
})
</script>
