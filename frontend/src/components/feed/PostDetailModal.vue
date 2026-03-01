<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="post-detail-modal" @click.stop>
      <!-- Close Button -->
      <button class="close-btn" @click="$emit('close')">✕</button>

      <!-- Post Content -->
      <div class="post-detail" v-if="post">
        <!-- Author -->
        <div class="author-section">
          <img
            :src="post.author_avatar || defaultAvatar"
            class="avatar"
            @click="goToProfile"
          >
          <div class="author-info">
            <span class="name" @click="goToProfile">
              {{ post.author_display_name || post.author_username }}
            </span>
            <span class="username">@{{ post.author_username }}</span>
            <span class="time">{{ formatDate(post.created_at) }}</span>
          </div>
          <button v-if="!post.is_following" class="btn-follow" @click="follow">
            Подписаться
          </button>
        </div>

        <!-- Title -->
        <h2 v-if="post.title" class="post-title">{{ post.title }}</h2>

        <!-- Text -->
        <div class="post-text">
          <p>{{ post.text }}</p>
        </div>

        <!-- Hashtags -->
        <div v-if="post.hashtags?.length" class="hashtags">
          <span
            v-for="hashtag in post.hashtags"
            :key="hashtag"
            class="hashtag"
            @click="searchByTag(hashtag)"
          >
            #{{ hashtag }}
          </span>
        </div>

        <!-- Media -->
        <div v-if="post.media_files?.length" class="media-gallery">
          <div
            v-for="(media, index) in post.media_files"
            :key="index"
            class="media-item"
          >
            <!-- backend now returns media_type field ('image' or 'video') -->
            <img v-if="media.media_type === 'image'" :src="media.url" alt="">
            <video v-else :src="media.url" controls></video>
          </div>
        </div>

        <!-- Single Media -->
        <div v-else-if="post.image_url" class="single-media">
          <img :src="post.image_url" alt="">
        </div>
        <div v-else-if="post.video_url" class="single-media">
          <video :src="post.video_url" controls></video>
        </div>

        <!-- Anime Card -->
        <AnimeCard
          v-if="post.anime"
          :poster-url="post.anime.poster_url"
          :title-ru="post.anime.title_ru"
          :title-en="post.anime.title_en"
          :rating="post.anime_rating"
          style="margin: 0 1.5rem 1rem;"
        />

        <!-- Playlist -->
        <div v-if="post.playlist" class="playlist-card">
          <span>📁 {{ post.playlist.title }}</span>
        </div>

        <!-- Stats -->
        <div class="stats-bar">
          <span>{{ formatCount(post.views_count) }} просмотров</span>
          <span>{{ formatCount(post.likes_count) }} лайков</span>
          <span>{{ formatCount(post.comments_count) }} комментариев</span>
        </div>

        <!-- Actions -->
        <div class="actions-bar">
          <button @click="handleLike" :class="{ active: post.is_liked }">
            {{ post.is_liked ? '❤️' : '🤍' }} {{ formatCount(post.likes_count) }}
          </button>
          <button @click="handleDislike" :class="{ active: post.is_disliked }">
            {{ post.is_disliked ? '👎' : '👍' }} {{ formatCount(post.dislikes_count) }}
          </button>
          <button @click="$emit('comment', post)">
            💬 {{ formatCount(post.comments_count) }}
          </button>
          <button @click="$emit('repost', post)">
            🔁 {{ formatCount(post.reposts_count) }}
          </button>
        </div>

        <!-- Comments Section -->
        <div class="comments-section">
          <h3>Комментарии ({{ post.comments_count }})</h3>

          <!-- Sort -->
          <div class="sort-tabs">
            <button
              :class="{ active: commentSort === 'top' }"
              @click="commentSort = 'top'"
            >
              Лучшие
            </button>
            <button
              :class="{ active: commentSort === 'new' }"
              @click="commentSort = 'new'"
            >
              Новые
            </button>
          </div>

          <!-- Comment Input -->
          <div class="comment-input">
            <img :src="currentUser?.avatar || defaultAvatar" class="avatar-sm">
            <input
              v-model="newComment"
              type="text"
              placeholder="Написать комментарий..."
              @keyup.enter="submitComment"
            >
            <button @click="submitComment" :disabled="!newComment.trim()">
              ➤
            </button>
          </div>

          <!-- Comments List -->
          <div class="comments-list">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment"
            >
              <img :src="comment.author_avatar || defaultAvatar" class="avatar-sm">
              <div class="comment-content">
                <div class="comment-header">
                  <span class="author">{{ comment.author_username }}</span>
                  <span class="time">{{ formatDate(comment.created_at) }}</span>
                </div>
                <p>{{ comment.content }}</p>
                <div class="comment-actions">
                  <button @click="likeComment(comment)">
                    {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.likes_count }}
                  </button>
                  <button @click="replyToComment(comment)">
                    Ответить
                  </button>
                </div>
              </div>
            </div>

            <div v-if="comments.length === 0" class="no-comments">
              Пока нет комментариев. Будьте первым!
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { normalizeComment } from '@/utils/normalizers'
import AnimeCard from './AnimeCard.vue'

interface Post {
  id: number
  author: number
  author_username: string
  author_avatar: string | null
  author_display_name: string | null
  title: string
  post_type: string
  text: string
  image_url: string | null
  video_url: string | null
  anime: any
  anime_rating: number | null
  playlist: any
  likes_count: number
  dislikes_count: number
  comments_count: number
  views_count: number
  reposts_count: number
  created_at: string
  hashtags: string[]
  is_liked: boolean
  is_disliked: boolean
  is_following: boolean
  media_files: any[]
}

interface Comment {
  id: number
  author: number
  author_username: string
  author_avatar: string | null
  content: string
  likes_count: number
  created_at: string
  is_liked: boolean
}

const props = defineProps<{
  post: Post | null
}>()

const emit = defineEmits<{
  close: []
  comment: [post: Post]
  repost: [post: Post]
}>()

const router = useRouter()
const defaultAvatar = '/img/default-avatar.svg'

const currentUser = ref<any>(null)
const comments = ref<Comment[]>([])
const newComment = ref('')
const commentSort = ref('top')

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCount = (count: number | undefined): string => {
  if (count === undefined || count === null) return '0'
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'М'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'К'
  return count.toString()
}

const goToProfile = () => {
  if (props.post) {
    router.push(`/profile/${props.post.author_username}`)
  }
}

const searchByTag = (tag: string) => {
  router.push(`/search?tag=${tag}`)
}

const follow = async () => {
  if (!props.post) return
  try {
    await apiClient.post(`/social/follow/toggle/${props.post.author}/`)
    props.post.is_following = true
  } catch (error) {
    console.error('Error following:', error)
  }
}

const handleLike = async () => {
  if (!props.post) return
  try {
    await apiClient.post(`/social/posts/${props.post.id}/like/`)
    props.post.is_liked = !props.post.is_liked
    props.post.likes_count += props.post.is_liked ? 1 : -1
  } catch (error) {
    console.error('Error liking:', error)
  }
}

const handleDislike = async () => {
  if (!props.post) return
  try {
    await apiClient.post(`/social/posts/${props.post.id}/dislike/`)
    props.post.is_disliked = !props.post.is_disliked
    props.post.dislikes_count += props.post.is_disliked ? 1 : -1
  } catch (error) {
    console.error('Error disliking:', error)
  }
}

const loadComments = async () => {
  if (!props.post) return
  try {
    const response = await apiClient.get(`/social/posts/${props.post.id}/comments/`)
    comments.value = response.data.results || []
  } catch (error) {
    console.error('Error loading comments:', error)
  }
}

const submitComment = async () => {
  if (!props.post || !newComment.value.trim()) return
  try {
    const response = await apiClient.post(`/social/posts/${props.post.id}/comments/`, {
      content: newComment.value
    })
    const newC = normalizeComment(response.data)
    comments.value.unshift(newC)
    newComment.value = ''
    props.post.comments_count++
  } catch (error) {
    console.error('Error submitting comment:', error)
  }
}

const likeComment = async (comment: Comment) => {
  try {
    await apiClient.post(`/social/comments/${comment.id}/like/`)
    comment.is_liked = !comment.is_liked
    comment.likes_count += comment.is_liked ? 1 : -1
  } catch (error) {
    console.error('Error liking comment:', error)
  }
}

const replyToComment = (comment: Comment) => {
  newComment.value = `@${comment.author_username} `
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
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.post-detail-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
}

.author-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.name {
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.username, .time {
  color: #666;
  font-size: 0.85rem;
}

.btn-follow {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
}

.post-title {
  color: #fff;
  padding: 1.5rem 1.5rem 0;
}

.post-text {
  padding: 1rem 1.5rem;
  color: #ddd;
  line-height: 1.6;
}

.hashtags {
  padding: 0 1.5rem 1rem;
}

.hashtag {
  color: #667eea;
  margin-right: 0.5rem;
  cursor: pointer;
}

.media-gallery {
  padding: 0 1.5rem 1rem;
}

.media-item img,
.media-item video {
  width: 100%;
  border-radius: 8px;
}

.single-media {
  padding: 0 1.5rem 1rem;
}

.single-media img,
.single-media video {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
  background: #000;
  border-radius: 8px;
}

.anime-card {
  margin: 0 1.5rem 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 1rem;
}

.playlist-card {
  margin: 0 1.5rem 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.anime-poster {
  width: 80px;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.anime-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.anime-info .title {
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
}

.anime-info .title-en {
  color: #888;
  font-size: 0.8rem;
}

.anime-info .rating {
  color: #667eea;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.stats-bar {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-top: 1px solid #1f1f1f;
  border-bottom: 1px solid #1f1f1f;
  color: #666;
  font-size: 0.9rem;
}

.actions-bar {
  display: flex;
  justify-content: space-around;
  padding: 0.75rem 1.5rem;
}

.actions-bar button {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.actions-bar button:hover {
  background: #1a1a1a;
}

.actions-bar button.active {
  color: #667eea;
}

.comments-section {
  padding: 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.comments-section h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.sort-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.sort-tabs button {
  background: #1a1a1a;
  color: #666;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
}

.sort-tabs button.active {
  background: #667eea;
  color: white;
}

.comment-input {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.comment-input input {
  flex: 1;
  background: #1a1a1a;
  border: none;
  color: #ddd;
  padding: 0.75rem;
  border-radius: 20px;
}

.comment-input input:focus {
  outline: none;
}

.comment-input button {
  background: #667eea;
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
}

.comment-input button:disabled {
  opacity: 0.5;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.comment {
  display: flex;
  gap: 0.75rem;
}

.comment-content {
  flex: 1;
  background: #1a1a1a;
  padding: 0.75rem;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.comment-header .author {
  color: #fff;
  font-weight: 600;
}

.comment-header .time {
  color: #555;
  font-size: 0.8rem;
}

.comment-content p {
  color: #ddd;
  margin-bottom: 0.5rem;
}

.comment-actions {
  display: flex;
  gap: 1rem;
}

.comment-actions button {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 0.8rem;
}

.no-comments {
  text-align: center;
  color: #666;
  padding: 2rem;
}
</style>
