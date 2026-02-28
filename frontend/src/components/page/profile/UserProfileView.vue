  <template>
  <div class="user-profile-view">
    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пользователь не найден -->
    <div v-else-if="!user.id" class="not-found">
      <h2>👤 Пользователь не найден</h2>
      <p>Пользователь с таким никнеймом не существует или был удалён.</p>
      <button @click="goToFeed" class="btn-back">Вернуться в ленту</button>
    </div>

    <!-- Профиль пользователя -->
    <div v-else class="profile-content">
      <!-- Шапка профиля -->
      <div class="profile-header">
        <div class="header-background"></div>
        <div class="header-content">
          <div class="avatar-section">
            <img :src="user.avatar || '/img/default-avatar.svg'" class="avatar" />
            <div :class="['status-indicator', { online: isOnline }]"></div>
          </div>

          <div class="user-info">
            <h1>{{ user.display_name || user.username }}</h1>
            <p class="username">@{{ user.username }}</p>
            <p v-if="user.nickname" class="nickname">🏷️ {{ user.nickname }}</p>
            <p class="bio">{{ user.bio || 'Пользователь пока ничего не написал о себе' }}</p>

            <div class="user-meta">
              <span v-if="user.level" class="level-badge">⭐ Уровень {{ user.level }}</span>
              <span v-if="user.experience" class="exp-badge">✨ {{ user.experience }} опыта</span>
              <span v-if="user.created_at">📅 На сайте с {{ formatDate(user.created_at) }}</span>
            </div>
          </div>

          <div class="header-actions">
            <button
              v-if="!isFollowing"
              @click="toggleFollow"
              class="btn-follow"
            >
              Подписаться
            </button>
            <button
              v-else
              @click="toggleFollow"
              class="btn-unfollow"
            >
              ✓ Подписан
            </button>
            <button @click="openChat" class="btn-message">
              <ChatBubbleLeftIcon class="w-5 h-5" />
              Написать
            </button>
            <button @click="toggleFavorite" :class="['btn-favorite', { active: isFavorite }]">
              <StarIcon class="w-5 h-5" />
            </button>
            <button @click="reportUser" class="btn-report">
              <FlagIcon class="w-5 h-5" />
              Пожаловаться
            </button>
          </div>

          <!-- Статистика -->
          <div class="stats">
            <div class="stat-item">
              <span class="stat-value">{{ stats.followers }}</span>
              <span class="stat-label">подписчиков</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.following }}</span>
              <span class="stat-label">подписок</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.posts }}</span>
              <span class="stat-label">постов</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.playlists }}</span>
              <span class="stat-label">плейлистов</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.achievements }}</span>
              <span class="stat-label">достижений</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Вкладки -->
      <div class="profile-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          {{ tab.name }}
        </button>
      </div>

      <!-- Контент вкладок -->
      <div class="tab-content-container">
        <!-- Лента -->
        <div v-if="activeTab === 'feed'" class="tab-content">
          <UserFeed :user-id="userId" />
        </div>

        <!-- Аниме (коллекция) -->
        <div v-if="activeTab === 'anime'" class="tab-content">
          <UserAnimeCollection :user-id="userId" />
        </div>

        <!-- Плейлисты -->
        <div v-if="activeTab === 'playlists'" class="tab-content">
          <UserPublicPlaylists :user-id="userId" />
        </div>

        <!-- Shorts -->
        <div v-if="activeTab === 'shorts'" class="tab-content">
          <UserShorts :user-id="userId" />
        </div>

        <!-- Достижения -->
        <div v-if="activeTab === 'achievements'" class="tab-content">
          <AchievementsView :username="user.username" />
        </div>

        <!-- О себе -->
        <div v-if="activeTab === 'about'" class="tab-content">
          <ProfileAbout :user="user" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  ChatBubbleLeftIcon,
  StarIcon,
  FlagIcon
} from '@heroicons/vue/24/outline'
import UserFeed from '@/components/Profile/UserFeed.vue'
import UserAnimeCollection from '@/components/Profile/UserAnimeCollection.vue'
import UserPublicPlaylists from '@/components/Profile/UserPublicPlaylists.vue'
import UserShorts from '@/components/Profile/UserShorts.vue'
import AchievementsView from '@/components/page/other/AchievementsView.vue'
import ProfileAbout from '@/components/Profile/ProfileAbout.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userId = ref(parseInt(route.params.id))
const user = ref({})
const stats = ref({})
const isOnline = ref(false)
const isFollowing = ref(false)
const isFavorite = ref(false)
const activeTab = ref('feed')
const loading = ref(true)

const tabs = [
  { id: 'feed', name: 'Лента' },
  { id: 'anime', name: 'Аниме' },
  { id: 'playlists', name: 'Плейлисты' },
  { id: 'shorts', name: 'Shorts' },
  { id: 'achievements', name: 'Достижения' },
  { id: 'about', name: 'О себе' },
]

const currentUser = computed(() => authStore.user)

const loadProfile = async () => {
  loading.value = true
  try {
    const response = await api.get(`/users/profile/${userId.value}/`)
    user.value = response.data
    isOnline.value = response.data.is_online
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
    user.value = {}
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await api.get(`/users/${userId.value}/stats/`)
    stats.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  }
}

const loadFollowStatus = async () => {
  if (!currentUser.value) return

  try {
    const [followResponse, favoriteResponse] = await Promise.all([
      api.get(`/social/follows/check/?following_id=${userId.value}`),
      api.get(`/social/favorites/check/?content_type=user&object_id=${userId.value}`)
    ])

    isFollowing.value = followResponse.data.following
    isFavorite.value = favoriteResponse.data.favorited
  } catch (error) {
    console.error('Ошибка загрузки статуса:', error)
  }
}

const toggleFollow = async () => {
  try {
    const response = await api.post(`/social/follow/toggle/${userId.value}/`)
    isFollowing.value = response.data.following
    stats.value.followers = response.data.followers_count || stats.value.followers
  } catch (error) {
    console.error('Ошибка подписки:', error)
  }
}

const toggleFavorite = async () => {
  try {
    const response = await api.post('/social/favorites/toggle/', {
      content_type: 'user',
      target_user: userId.value
    })
    isFavorite.value = response.data.favorited
  } catch (error) {
    console.error('Ошибка избранного:', error)
  }
}

const openChat = async () => {
  try {
    const response = await api.post('/chats/private/', { user_id: userId.value })
    router.push(`/chats/${response.data.id}`)
  } catch (error) {
    console.error('Ошибка создания чата:', error)
  }
}

const reportUser = () => {
  const reason = prompt('Укажите причину жалобы:')
  if (reason) {
    api.post(`/social/reports/`, {
      content_type: 'user',
      object_id: userId.value,
      reason
    }).then(() => {
      alert('Жалоба отправлена')
    }).catch(() => {
      alert('Ошибка отправки жалобы')
    })
  }
}

const goToFeed = () => {
  router.push('/feed')
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

onMounted(() => {
  loadProfile()
  loadStats()
  loadFollowStatus()
})
</script>

<style scoped>
.user-profile-view {
  max-width: 1200px;
  margin: 0 auto;
  background-color: var(--color-background);
  min-height: 100vh;
}

.loading,
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 40px;
}

.not-found h2 {
  font-size: 32px;
  margin: 0 0 16px;
  color: var(--color-text);
}

.not-found p {
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.btn-back {
  padding: 12px 24px;
  background: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-back:hover {
  background: var(--color-accent-hover);
}

.profile-header {
  position: relative;
  margin-bottom: 20px;
}

.header-background {
  height: 200px;
  background-color: var(--color-background-surface);
  border-bottom: 1px solid var(--color-divider);
}

.header-content {
  position: relative;
  padding: 0 24px 24px;
  margin-top: -80px;
}

.avatar-section {
  position: relative;
  display: inline-block;
}

.avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  border: 4px solid var(--color-background-surface);
  object-fit: cover;
  box-shadow: var(--shadow-card);
}

.status-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background: var(--color-text-tertiary);
  border: 3px solid var(--color-background-surface);
  border-radius: 50%;
}

.status-indicator.online {
  background: var(--color-accent-teal);
}

.user-info {
  margin-top: 16px;
  max-width: 600px;
}

.user-info h1 {
  margin: 0 0 4px;
  font-size: 28px;
  color: var(--color-text);
}

.username {
  margin: 0 0 4px;
  color: var(--color-text-secondary);
  font-size: 16px;
}

.nickname {
  margin: 0 0 8px;
  color: var(--color-accent);
  font-size: 14px;
  font-weight: 500;
}

.bio {
  margin: 0 0 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--color-text-tertiary);
  font-size: 14px;
  align-items: center;
}

.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-weight: 600;
}

.exp-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: var(--color-background-surface);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 20px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.btn-follow {
  padding: 10px 24px;
  background: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-follow:hover {
  background: var(--color-accent-hover);
}

.btn-unfollow {
  padding: 10px 24px;
  background: var(--color-background-surface);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-unfollow:hover {
  background: var(--color-background-active);
}

.btn-message,
.btn-favorite,
.btn-report {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background 0.15s ease;
  color: var(--color-text-secondary);
}

.btn-message:hover,
.btn-favorite:hover,
.btn-report:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

.btn-favorite.active {
  color: var(--color-accent-orange);
  background: var(--color-background-active);
  border-color: var(--color-accent-orange);
}

.stats {
  display: flex;
  gap: 32px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-divider);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: var(--color-text);
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.profile-tabs {
  display: flex;
  gap: 8px;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-divider);
  overflow-x: auto;
}

.tab-btn {
  padding: 14px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all 0.15s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--color-text);
}

.tab-btn.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-content-container {
  padding: 24px;
}

.tab-content {
  min-height: 400px;
}

@media (max-width: 768px) {
  .header-background {
    height: 150px;
  }

  .header-content {
    padding: 0 16px 16px;
  }

  .avatar {
    width: 120px;
    height: 120px;
  }

  .user-info h1 {
    font-size: 24px;
  }

  .stats {
    gap: 16px;
  }

  .stat-value {
    font-size: 20px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
