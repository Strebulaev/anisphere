<template>
  <div class="reactor-feed" ref="feedRef">
    <div class="feed-container">
      <div
        v-for="(post, index) in posts"
        :key="post.id"
        v-show="currentIndex === index"
        class="reactor-post"
        :class="{ active: currentIndex === index }"
        @click="handlePostClick"
      >
        <!-- Видео -->
        <video
          ref="videoRefs"
          :src="post.video_url || post.video_file"
          loop
          playsinline
          @click="togglePlay"
          class="post-video"
        ></video>

        <!-- Оверлей с информацией -->
        <div class="post-overlay">
          <!-- Информация о посте -->
          <div class="post-info">
            <div class="author" @click.stop="goToProfile(post.author.id)">
              <img :src="post.author.avatar || '/img/default-avatar.svg'" class="author-avatar" />
              <span class="author-name">{{ post.author.username }}</span>
              <button
                v-if="!post.is_following && post.author.id !== currentUser?.id"
                @click.stop="toggleFollow(post)"
                class="btn-follow"
              >
                Подписаться
              </button>
            </div>

            <div v-if="post.anime" class="anime-info" @click.stop="goToAnime(post.anime.id)">
              <span class="anime-icon"> <SakuraIcon name="play" /> </span>
              <span class="anime-title">{{ post.anime.title_ru }}</span>
            </div>

            <p class="post-description">{{ post.description }}</p>

            <div class="post-tags">
              <span v-for="tag in post.tags" :key="tag" class="tag">
                #{{ tag }}
              </span>
            </div>
          </div>

          <!-- Кнопки справа -->
          <div class="post-actions">
            <button @click.stop="toggleLike(post)" :class="['action-btn', { liked: post.is_liked }]">
              <HeartIcon class="w-8 h-8" />
              <span class="count">{{ post.likes_count }}</span>
            </button>

            <button @click.stop="openComments(post)" class="action-btn">
              <ChatBubbleLeftIcon class="w-8 h-8" />
              <span class="count">{{ post.comments_count }}</span>
            </button>

            <button @click.stop="sharePost(post)" class="action-btn">
              <ShareIcon class="w-8 h-8" />
              <span class="count">{{ post.shares_count || 0 }}</span>
            </button>

            <button @click.stop="savePost(post)" :class="['action-btn', { saved: post.is_saved }]">
              <BookmarkIcon class="w-8 h-8" />
            </button>

            <button @click.stop="showMore(post)" class="action-btn">
              <EllipsisVerticalIcon class="w-8 h-8" />
            </button>
          </div>
        </div>

        <!-- Индикатор загрузки -->
        <div v-if="loading && currentIndex === index" class="loading-indicator">
          <LoadingSpinner />
        </div>

        <!-- Индикатор паузы -->
        <div v-if="isPaused && currentIndex === index" class="pause-indicator">
          <PlayIcon class="w-16 h-16" />
        </div>
      </div>

      <!-- Пусто -->
      <div v-if="posts.length === 0 && !loading" class="empty">
        <p>Видео пока нет</p>
        <button @click="createPost" class="btn-create">
          <PlusIcon class="w-5 h-5" />
          Создать видео
        </button>
      </div>
    </div>

    <!-- Кнопка создания -->
    <button @click="createPost" class="fab-create">
      <PlusIcon class="w-6 h-6" />
    </button>

    <!-- Модальные окна -->
    <CommentsModal :show="showCommentsModal" :comments="selectedPost?.comments || []" @close="showCommentsModal = false" @send="sendComment" />
    <ShareModal :show="showShareModal" @close="showShareModal = false" @share="shareToPlatform" @copy-link="copyLink" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  HeartIcon,
  ChatBubbleLeftIcon,
  ShareIcon,
  BookmarkIcon,
  EllipsisVerticalIcon,
  PlayIcon,
  PlusIcon,
  LinkIcon
} from '@heroicons/vue/24/outline'
import { HeartIcon as HeartIconSolid } from '@heroicons/vue/24/solid'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import Modal from '@/components/ui/Modal.vue'
import CommentThread from './CommentThread.vue'
import CommentsModal from './modal/feed/CommentsModal.vue'
import ShareModal from './modal/feed/ShareModal.vue'
import api from '@/api'

interface Post {
  id: number
  video_url?: string
  video_file?: string
  author: {
    id: number
    username: string
    avatar?: string
  }
  is_following?: boolean
  anime?: {
    id: number
    title_ru: string
  }
  description?: string
  tags?: string[]
  is_liked?: boolean
  likes_count?: number
  comments_count?: number
  shares_count?: number
  is_saved?: boolean
  comments?: any[]
}

const router = useRouter()
const authStore = useAuthStore()

const feedRef = ref<HTMLElement | null>(null)
const videoRefs = ref<HTMLVideoElement[]>([])
const posts = ref<Post[]>([])
const currentIndex = ref(0)
const loading = ref(false)
const isPaused = ref(false)
const showCommentsModal = ref(false)
const showShareModal = ref(false)
const selectedPost = ref<Post | null>(null)
const observer = ref<IntersectionObserver | undefined>(undefined)

const currentUser = computed(() => authStore.user)

const currentPost = computed(() => posts.value[currentIndex.value])
const currentVideo = computed(() => videoRefs.value[currentIndex.value] || null)

// Загрузка постов
const loadPosts = async () => {
  loading.value = true
  try {
    const response = await api.get('/reactor/posts/', {
      params: { limit: 20 }
    })
    posts.value = response.data.results || response.data
  } catch (error) {
    console.error('Ошибка загрузки постов:', error)
  } finally {
    loading.value = false
  }
}

// Воспроизведение текущего видео
const playCurrentVideo = async () => {
  await nextTick()
  const video = currentVideo.value
  if (video) {
    try {
      await video.play()
      isPaused.value = false
    } catch (e) {
      console.error('Ошибка воспроизведения:', e)
    }
  }
}

// Пауза текущего видео
const pauseCurrentVideo = () => {
  const video = currentVideo.value
  if (video) {
    video.pause()
    isPaused.value = true
  }
}

// Переключение воспроизведения
const togglePlay = () => {
  if (isPaused.value) {
    playCurrentVideo()
  } else {
    pauseCurrentVideo()
  }
}

// Переключение на следующий пост
const nextPost = () => {
  pauseCurrentVideo()
  currentIndex.value = (currentIndex.value + 1) % posts.value.length
  playCurrentVideo()
}

// Переключение на предыдущий пост
const prevPost = () => {
  pauseCurrentVideo()
  currentIndex.value = currentIndex.value === 0 ? posts.value.length - 1 : currentIndex.value - 1
  playCurrentVideo()
}

// Обработка клика по посту (свайпы)
const handlePostClick = (e: MouseEvent) => {
  if (!feedRef.value || !currentPost.value) return

  const rect = feedRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left

  // Свайп влево - профиль автора
  if (x < rect.width * 0.3) {
    goToProfile(currentPost.value.author.id)
  }
  // Свайп вправо - страница аниме
  else if (x > rect.width * 0.7) {
    if (currentPost.value.anime) {
      goToAnime(currentPost.value.anime.id)
    }
  }
  // Центр - пауза/воспроизведение
  else {
    togglePlay()
  }
}

// Обработка свайпов вверх/вниз
let touchStartY = 0

const handleTouchStart = (e: TouchEvent) => {
  if (e.touches[0]) {
    touchStartY = e.touches[0].clientY
  }
}

const handleTouchEnd = (e: TouchEvent) => {
  if (e.changedTouches[0]) {
    const touchEndY = e.changedTouches[0].clientY
    const diff = touchStartY - touchEndY

    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        nextPost()
      } else {
        prevPost()
      }
    }
  }
}

// Лайк
const toggleLike = async (post: Post) => {
  try {
    const response = await api.post(`/reactor/posts/${post.id}/like/`)
    post.is_liked = response.data.liked
    post.likes_count = response.data.likes_count
  } catch (error) {
    console.error('Ошибка лайка:', error)
  }
}

// Подписка
const toggleFollow = async (post: Post) => {
  try {
    const response = await api.post(`/social/follow/toggle/${post.author.id}/`)
    post.is_following = response.data.following
  } catch (error) {
    console.error('Ошибка подписки:', error)
  }
}

// Комментарии
const openComments = (post: Post) => {
  selectedPost.value = post
  showCommentsModal.value = true
}

// Шеринг
const sharePost = (post: Post) => {
  selectedPost.value = post
  showShareModal.value = true
}

const shareToChat = () => {
  showShareModal.value = false
  router.push('/chats')
}

const shareToPlatform = async (platform: string) => {
  const shareUrl = `${window.location.origin}/reactor/posts/${selectedPost.value?.id}`
  
  const shareUrls: Record<string, string> = {
    telegram: `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}`,
    vk: `https://vk.com/share.php?url=${encodeURIComponent(shareUrl)}`,
    whatsapp: `https://wa.me/?text=${encodeURIComponent(shareUrl)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}`
  }
  
  if (shareUrls[platform]) {
    window.open(shareUrls[platform], '_blank')
  }
  showShareModal.value = false
}

const shareLink = async () => {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    alert('Ссылка скопирована!')
  } catch (e) {
    alert('Не удалось скопировать ссылку')
  }
  showShareModal.value = false
}

const copyLink = async () => {
  const shareUrl = `${window.location.origin}/reactor/posts/${selectedPost.value?.id}`
  try {
    await navigator.clipboard.writeText(shareUrl)
  } catch (e) {
    console.error('Ошибка копирования:', e)
  }
  showShareModal.value = false
}

const shareExternal = () => {
  if (navigator.share && currentPost.value) {
    navigator.share({
      title: currentPost.value.description || '',
      url: window.location.href
    })
  }
  showShareModal.value = false
}

const sendComment = async (text: string) => {
  if (!selectedPost.value) return
  try {
    await api.post(`/reactor/posts/${selectedPost.value.id}/comments/`, { text })
  } catch (error) {
    console.error('Ошибка отправки комментария:', error)
  }
}

// Сохранение
const savePost = async (post: Post) => {
  try {
    await api.post('/social/favorites/toggle/', {
      content_type: 'reactor_post',
      reactor_post: post.id
    })
    post.is_saved = !post.is_saved
  } catch (error) {
    console.error('Ошибка сохранения:', error)
  }
}

// Ещё действия
const showMore = (post: Post) => {
  // Показать меню действий
}

// Навигация
const goToProfile = (userId: number) => {
  router.push(`/profile/${userId}`)
}

const goToAnime = (animeId: number) => {
  router.push(`/anime/${animeId}`)
}

const createPost = () => {
  router.push('/reactor/create')
}

// Наблюдатель за видимостью
const setupIntersectionObserver = () => {
  observer.value?.disconnect()

  const newObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const target = entry.target as HTMLElement
          const index = parseInt(target.dataset.index || '0')
          if (index !== currentIndex.value && !isNaN(index)) {
            currentIndex.value = index
            playCurrentVideo()
          }
        } else {
          const target = entry.target as HTMLElement
          const index = parseInt(target.dataset.index || '0')
          const video = videoRefs.value[index]
          if (video) {
            video.pause()
          }
        }
      })
    },
    { threshold: 0.7 }
  )

  observer.value = newObserver

  // Наблюдаем за постами
  nextTick(() => {
    videoRefs.value.forEach((video, index) => {
      if (video && video.parentElement) {
        (video.parentElement as HTMLElement).dataset.index = index.toString()
        observer.value?.observe(video.parentElement)
      }
    })
  })
}

onMounted(() => {
  loadPosts()
  setupIntersectionObserver()

  // Обработка свайпов
  if (feedRef.value) {
    feedRef.value.addEventListener('touchstart', handleTouchStart)
    feedRef.value.addEventListener('touchend', handleTouchEnd)
  }

  // Обработка клавиш
  document.addEventListener('keydown', handleKeydown)

  // Воспроизводим первый пост
  playCurrentVideo()
})

onUnmounted(() => {
  observer.value?.disconnect()
  observer.value = undefined

  if (feedRef.value) {
    feedRef.value.removeEventListener('touchstart', handleTouchStart)
    feedRef.value.removeEventListener('touchend', handleTouchEnd)
  }

  document.removeEventListener('keydown', handleKeydown)

  // Останавливаем все видео
  videoRefs.value.forEach(video => {
    if (video) video.pause()
  })
})

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'ArrowDown') {
    nextPost()
  } else if (e.key === 'ArrowUp') {
    prevPost()
  } else if (e.key === ' ' || e.key === 'k') {
    e.preventDefault()
    togglePlay()
  }
}
</script>

<style scoped>
.reactor-feed {
  position: relative;
  width: 100%;
  height: 100vh;
  background: #000;
  overflow: hidden;
}

.feed-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.reactor-post {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: none;
}

.reactor-post.active {
  display: block;
}

.post-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #000;
}

.post-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
  background: linear-gradient(transparent 50%, rgba(0, 0, 0, 0.8));
}

.post-info {
  flex: 1;
  margin-bottom: 16px;
}

.author {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.author-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid white;
}

.author-name {
  font-weight: 600;
  color: white;
}

.btn-follow {
  padding: 6px 16px;
  background: #fe2c55;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

.anime-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: white;
  cursor: pointer;
}

.anime-icon {
  font-size: 20px;
}

.anime-title {
  font-weight: 500;
}

.post-description {
  color: white;
  margin-bottom: 12px;
  line-height: 1.5;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  color: #fe2c55;
  font-size: 13px;
}

.post-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-end;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  transition: transform 0.3s;
}

.action-btn:hover {
  transform: scale(1.1);
}

.action-btn.liked {
  color: #fe2c55;
}

.action-btn.saved {
  color: #ffc107;
}

.count {
  font-size: 12px;
  font-weight: 500;
}

.loading-indicator,
.pause-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
}

.pause-indicator {
  opacity: 0.8;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: white;
  text-align: center;
}

.btn-create {
  margin-top: 20px;
  padding: 12px 24px;
  background: #fe2c55;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fab-create {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #fe2c55;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(254, 44, 85, 0.4);
  transition: transform 0.3s;
  z-index: 100;
}

.fab-create:hover {
  transform: scale(1.1);
}
</style>
