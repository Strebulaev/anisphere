  <template>
  <div class="user-profile-view">
    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пользователь не найден -->
    <div v-else-if="!user.id" class="not-found">
      <h2><SakuraIcon name="user" /> Пользователь не найден</h2>
      <p>Пользователь с таким никнеймом не существует или был удалён.</p>
      <button @click="goToFeed" class="btn-back">Вернуться в ленту</button>
    </div>

    <!-- Профиль пользователя -->
    <div v-else class="profile-content">
      <!-- Шапка профиля -->
      <div class="profile-header" :class="{ 'has-cover': user.cover_image_url }">
        <!-- Обложка профиля (только для премиум) -->
        <div
          v-if="user.cover_image_url"
          class="header-background"
          :style="coverImageStyle"
        >
          <!-- Кнопка загрузки обложки (только для своего профиля) -->
          <label v-if="isOwnProfile" class="cover-upload-btn">
            <input 
              type="file" 
              accept="image/*" 
              @change="handleCoverUpload" 
              hidden
            />
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>Изменить обложку</span>
          </label>
        </div>

        <div class="header-content">
          <div class="avatar-section">
            <UserAvatar
              :src="user.avatar || user.avatar_url || '/img/default-avatar.svg'"
              :is-online="isUserOnline(userId)"
              size="2xl"
              shape="circle"
            />
          </div>

          <div class="user-info">
            <h1>
              {{ user.display_name || user.nickname || user.username }}
              <PremiumCrown v-if="user.is_premium" :size="24" class="premium-crown-inline" />
            </h1>
            <p class="username">
              @{{ user.nickname || user.username }}
              <PremiumCrown v-if="user.is_premium" :size="16" class="premium-crown-username" />
            </p>
            <p class="bio">{{ user.bio || 'Пользователь пока ничего не написал о себе' }}</p>

            <div class="user-meta">
              <span v-if="user.experience" class="exp-badge"><SakuraIcon name="sparkles" /> {{ user.experience }} опыта</span>
              <span v-if="user.created_at">🗓 На сайте с {{ formatDate(user.created_at) }}</span>
            </div>
          </div>

          <div class="header-actions">
            <button
              v-if="!isOwnProfile && !isFollowing"
              @click="toggleFollow"
              class="btn-follow"
            >
              Подписаться
            </button>
            <button
              v-if="!isOwnProfile && isFollowing"
              @click="toggleFollow"
              class="btn-unfollow"
            >
              ✓ Подписан
            </button>
            <button v-if="!isOwnProfile" @click="openChat" class="btn-message">
              <ChatBubbleLeftIcon class="w-5 h-5" />
              Написать
            </button>
            <button v-if="!isOwnProfile" @click="reportUser" class="btn-report">
              <FlagIcon class="w-5 h-5" />
              Пожаловаться
            </button>
          </div>

          <!-- Статистика
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
          </div> -->
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
        <!-- <router-link :to="isOwnProfile ? '/chats/create-group' : '/chats/groups'" class="tab-btn-create">
          <SakuraIcon name="plus" :size="16" />
          {{ isOwnProfile ? 'Создать группу' : 'Группы' }}
        </router-link> -->
      </div>

      <!-- Контент вкладок -->
      <div class="tab-content-container">
        <div v-if="activeTab === 'feed'" class="tab-content">
          <UserFeed :user-id="userId" />
        </div>

        <div v-if="activeTab === 'anime'" class="tab-content">
          <UserAnimeCollection :user-id="userId" />
        </div>

        <div v-if="activeTab === 'playlists'" class="tab-content">
          <UserPublicPlaylists :user-id="userId" />
        </div>

        <div v-if="activeTab === 'social'" class="tab-content">
          <UserSocialNetworks :user="user" />
        </div>

        <div v-if="activeTab === 'favorites'" class="tab-content">
          <UserFavorites :user-id="userId" />
        </div>

        <div v-if="activeTab === 'about'" class="tab-content">
          <ProfileAbout :user="user" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOnlineStatus } from '@/composables/useOnlineStatus'
import {
  ChatBubbleLeftIcon,
  FlagIcon
} from '@heroicons/vue/24/outline'
import UserFeed from '@/components/Profile/UserFeed.vue'
import UserAnimeCollection from '@/components/Profile/UserAnimeCollection.vue'
import UserPublicPlaylists from '@/components/Profile/UserPublicPlaylists.vue'
import UserSocialNetworks from '@/components/Profile/UserSocialNetworks.vue'
import UserFavorites from '@/components/Profile/UserFavorites.vue'
import AchievementsView from '@/components/page/other/AchievementsView.vue'
import ProfileAbout from '@/components/Profile/ProfileAbout.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import UserAvatar from '@/components/ui/UserAvatar.vue'
import PremiumCrown from '@/components/icons/PremiumCrown.vue'
import api from '@/api'

interface UserProfile {
  id?: number
  avatar?: string
  avatar_url?: string
  display_name?: string
  nickname?: string
  username?: string
  bio?: string
  experience?: number
  created_at?: string
  cover_image_url?: string
  cover_image?: string
  social_links?: any[]
  is_online?: boolean
  is_premium?: boolean
}

interface UserStats {
  followers?: number
  following?: number
  posts?: number
  playlists?: number
  achievements?: number
}

const props = defineProps<{
  id?: string | number | null
  nickname?: string | null
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { isUserOnline } = useOnlineStatus()

// route.params.id может быть username (строка) или числовой id
// Приоритет: prop nickname > prop id > route.params.id
const routeId = String(props.id ?? route.params.id ?? '')
const userId = ref<number>(NaN)  // будет заполнен после загрузки профиля
const user = ref<UserProfile>({})
const stats = ref<UserStats>({})
const isFollowing = ref(false)
const activeTab = ref('feed')
const loading = ref(true)

const tabs = computed(() => {
  const baseTabs = [
    { id: 'feed', name: 'Лента' },
    { id: 'anime', name: 'Аниме' },
    { id: 'playlists', name: 'Плейлисты' },
    { id: 'favorites', name: 'Избранное' },
    { id: 'about', name: 'О себе' },
  ]
  // Вкладка соцсетей
  baseTabs.splice(3, 0, { id: 'social', name: 'Соцсети' })
  return baseTabs
})

const currentUser = computed(() => authStore.user)

const isOwnProfile = computed(() => {
  if (!currentUser.value || !userId.value || isNaN(userId.value)) return false
  return currentUser.value.id === userId.value
})

const coverImageStyle = computed(() => {
  if (user.value.cover_image_url) {
    return {
      backgroundImage: `url(${user.value.cover_image_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

const loadProfile = async () => {
  loading.value = true
  try {
    let response

    // Если передан prop nickname (маршрут /@nickname) — ищем по никнейму
    if (props.nickname) {
      const nick = props.nickname.replace(/^@/, '')
      const resp = await api.get(`/users/by-nickname/@${nick}/`)
      user.value = resp.data
      userId.value = resp.data.id

      loading.value = false
      return
    }

    // Пробуем по username (строка), затем по числовому id
    const isNumericId = /^\d+$/.test(String(routeId))
    if (isNumericId) {
      response = await api.get(`/users/profile/${routeId}/`)
    } else {
      // Ищем пользователя по username через поиск
      response = await api.get(`/users/search/?q=${encodeURIComponent(routeId)}&exact=true`)
      if (response.data?.results?.length) {
        const found = response.data.results[0]
        response = await api.get(`/users/profile/${found.id}/`)
      } else {
        // Fallback: попробуем напрямую как username
        response = await api.get(`/users/search/?username=${encodeURIComponent(routeId)}`)
        if (response.data?.id) {
          // search вернул прямой объект
        } else if (response.data?.results?.length) {
          response = await api.get(`/users/profile/${response.data.results[0].id}/`)
        }
      }
    }
    user.value = response.data
    userId.value = response.data.id  // сохраняем числовой id из ответа

  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
    user.value = {}
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  if (!userId.value || isNaN(userId.value)) return
  try {
    const response = await api.get(`/users/${userId.value}/stats/`)
    stats.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  }
}

const loadFollowStatus = async () => {
  if (!authStore.isAuthenticated || !userId.value || isNaN(userId.value)) return

  try {
    const response = await api.get(`/social/follows/check/?following_id=${userId.value}`)
    isFollowing.value = response.data.is_following ?? response.data.following
  } catch (error) {
    console.error('Ошибка загрузки статуса:', error)
  }
}

const toggleFollow = async () => {
  if (!authStore.isAuthenticated) {
    alert('Для подписки необходимо войти в аккаунт')
    return
  }
  try {
    const response = await api.post(`/social/follow/toggle/${userId.value}/`)
    isFollowing.value = response.data.following
    stats.value.followers = response.data.followers_count || stats.value.followers
  } catch (error) {
    console.error('Ошибка подписки:', error)
    alert('Не удалось выполнить подписку')
  }
}

const openChat = async () => {
  if (!authStore.isAuthenticated) {
    alert('Для отправки сообщения необходимо войти в аккаунт')
    return
  }
  try {
    const response = await api.post('/social/private-chats/', { user2: userId.value })
    router.push(`/chats/${response.data.id}`)
  } catch (error) {
    console.error('Ошибка создания чата:', error)
    alert('Не удалось создать чат')
  }
}

const reportUser = () => {
  if (!authStore.isAuthenticated) {
    alert('Для отправки жалобы необходимо войти в аккаунт')
    return
  }
  const reason = prompt('Укажите причину жалобы:')
  if (reason) {
    api.post('/social/reports/', {
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

const handleCoverUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('cover_image', file)

  try {
    const response = await api.patch(`/users/profile/update/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    user.value.cover_image_url = response.data.cover_image_url
    user.value.cover_image = response.data.cover_image
  } catch (error) {
    console.error('Ошибка загрузки обложки:', error)
    alert('Не удалось загрузить обложку')
  }
}

const goToFeed = () => {
  router.push('/feed')
}

const formatDate = (date: string | Date | undefined) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

onMounted(async () => {
  await loadProfile()  // сначала загружаем профиль чтобы получить числовой userId
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
  height: 280px;
  background-color: var(--color-background-surface);
  border-bottom: 1px solid var(--color-divider);
  background-size: cover;
  background-position: center;
  position: relative;
}

.header-background::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.4) 100%);
}

.cover-upload-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 10;
}

.cover-upload-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.header-content {
  position: relative;
  padding: 0 24px 24px;
  margin-top: -80px;
}

/* Если нет обложки - аватар не накладывается */
.profile-header:not(.has-cover) .header-content {
  margin-top: 24px;
}

.profile-header.has-cover .header-content {
  margin-top: -80px;
}

.avatar-section {
  position: relative;
  display: inline-block;
}

.user-info {
  margin-top: 16px;
  max-width: 600px;
}

.user-info h1 {
  margin: 0 0 4px;
  font-size: 28px;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.premium-crown-inline {
  vertical-align: middle;
}

.premium-crown-username {
  vertical-align: middle;
  margin-left: 4px;
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
.btn-report:hover {
  background: var(--color-background-active);
  color: var(--color-text);
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

.tab-btn-create {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 14px 20px;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: var(--radius-button) var(--radius-button) 0 0;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.15s ease;
  white-space: nowrap;
  text-decoration: none;
  margin-left: auto;
}

.tab-btn-create:hover {
  background: var(--color-accent-hover);
  color: #fff;
}

.tab-content-container {
  padding: 24px;
}

.tab-content {
  min-height: 400px;
}

@media (max-width: 768px) {
  .header-background {
    height: 180px;
  }

  .header-content {
    padding: 0 16px 16px;
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
