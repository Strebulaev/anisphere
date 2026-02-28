<template>
  <div class="anime-discussions-list">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка обсуждений...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadDiscussions" class="retry-btn">Попробовать снова</button>
    </div>

    <div v-else-if="discussions.length === 0" class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <p>Вы ещё не участвуете в обсуждениях</p>
      <p class="empty-hint">Нажмите кнопку "Обсудить" на странице аниме, чтобы присоединиться к обсуждению</p>
    </div>

    <div v-else class="discussions-grid">
      <div
        v-for="discussion in discussions"
        :key="discussion.id"
        @click="goToChat(discussion.id)"
        class="discussion-card"
      >
        <div class="discussion-poster">
          <img v-if="discussion.anime_poster" :src="discussion.anime_poster" :alt="discussion.anime_title" />
          <div v-else class="poster-placeholder">🎬</div>
        </div>

        <div class="discussion-info">
          <h3 class="discussion-title">{{ discussion.anime_title }}</h3>
          <p class="discussion-name">{{ discussion.name }}</p>

          <div class="discussion-meta">
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
              </svg>
              {{ discussion.members_count }} участников
            </span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ formatDate(discussion.created_at) }}
            </span>
          </div>

          <div v-if="discussion.user_joined_at" class="joined-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Присоединились {{ formatRelativeDate(discussion.user_joined_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import type { AnimeDiscussionGroup } from '@/api/animeDiscussions'

const router = useRouter()

const discussions = ref<AnimeDiscussionGroup[]>([])
const loading = ref(false)
const error = ref('')

const loadDiscussions = async () => {
  loading.value = true
  error.value = ''

  try {
    discussions.value = await animeDiscussionsApi.getUserJoinedDiscussions()
  } catch (err: any) {
    console.error('Error loading discussions:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить обсуждения'
  } finally {
    loading.value = false
  }
}

const goToChat = (chatId: number) => {
  router.push(`/chats/${chatId}`)
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

const formatRelativeDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'сегодня'
  if (diffDays === 1) return 'вчера'
  if (diffDays < 7) return `${diffDays} дн. назад`
  return formatDate(dateString)
}

onMounted(() => {
  loadDiscussions()
})
</script>

<style scoped>
.anime-discussions-list {
  padding: 1.5rem;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-divider-light);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state p,
.empty-state p {
  color: var(--color-text-secondary);
  margin-bottom: 1rem;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: var(--color-divider);
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  max-width: 400px;
}

.retry-btn {
  padding: 0.75rem 1.5rem;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.retry-btn:hover {
  background-color: var(--color-accent-hover);
}

.discussions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.discussion-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.discussion-card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.discussion-poster {
  width: 80px;
  height: 120px;
  flex-shrink: 0;
  border-radius: 0.5rem;
  overflow: hidden;
  background-color: var(--color-background-active);
}

.discussion-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 2rem;
}

.discussion-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.discussion-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.discussion-name {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.discussion-meta {
  display: flex;
  gap: 1rem;
  margin-top: auto;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.joined-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
  font-size: 0.75rem;
  border-radius: 0.25rem;
  align-self: flex-start;
}

@media (max-width: 768px) {
  .anime-discussions-list {
    padding: 1rem;
  }

  .discussions-grid {
    grid-template-columns: 1fr;
  }

  .discussion-poster {
    width: 60px;
    height: 90px;
  }

  .discussion-title {
    font-size: 0.9375rem;
  }
}
</style>
