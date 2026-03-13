<template>
  <div class="own-profile-view">
    <!-- Шапка профиля -->
    <div class="profile-header">
      <!-- Обложка профиля -->
      <div 
        class="header-background" 
        :style="coverImageStyle"
      >
        <label class="cover-upload-btn">
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
          <img :src="user.avatar || '/img/default-avatar.svg'" class="avatar" @click="openAvatarUpload" />
          <div :class="['status-indicator', { online: isOnline }]"></div>
        </div>

        <div class="user-info">
          <h1>{{ user.display_name || user.username }}</h1>
          <p class="username">@{{ user.username }}</p>
          <p v-if="user.nickname" class="nickname">🏷️ {{ user.nickname }}</p>
          <p class="bio">{{ user.bio || 'Напишите что-то о себе...' }}</p>

          <div class="user-meta">
            <span v-if="user.experience" class="exp-badge">✨ {{ user.experience }} опыта</span>
            <span v-if="user.created_at">📅 На сайте с {{ formatDate(user.created_at) }}</span>
          </div>
        </div>

        <div class="header-actions">
          <button @click="openFullSettings" class="btn-edit">
            <CogIcon class="w-5 h-5" />
            Редактировать профиль
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
    <div class="profile-content">
      <!-- Лента -->
      <div v-if="activeTab === 'feed'" class="tab-content">
        <UserFeed :user-id="currentUser?.id" />
      </div>

      <!-- Аниме (Моя коллекция) -->
      <div v-if="activeTab === 'anime'" class="tab-content">
        <MyCollection />
      </div>

      <!-- Плейлисты -->
      <div v-if="activeTab === 'playlists'" class="tab-content">
        <MyPlaylists />
      </div>

      <!-- Shorts -->
      <div v-if="activeTab === 'shorts'" class="tab-content">
        <UserShorts :user-id="currentUser?.id" />
      </div>

      <!-- Достижения -->
      <div v-if="activeTab === 'achievements'" class="tab-content">
        <AchievementsView />
      </div>

      <!-- О себе -->
      <div v-if="activeTab === 'about'" class="tab-content">
        <ProfileAbout :user="user" @edit="openEditProfile" />
      </div>

      <!-- Избранное -->
      <div v-if="activeTab === 'favorites'" class="tab-content">
        <UserFavorites :user-id="currentUser?.id" />
      </div>
    </div>

    <!-- Модалка полных настроек -->
    <FullSettingsModal :is-visible="showFullSettingsModal" @close="showFullSettingsModal = false" @on-save="handleSettingsSaved" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CogIcon } from '@heroicons/vue/24/outline'
import MyCollection from '@/components/Feeds/MyCollection.vue'
import UserFeed from '@/components/Profile/UserFeed.vue'
import MyPlaylists from '@/components/page/playlists/MyPlaylistsView.vue'
import UserShorts from '@/components/Profile/UserShorts.vue'
import AchievementsView from '@/components/page/other/AchievementsView.vue'
import ProfileAbout from '@/components/Profile/ProfileAbout.vue'
import UserFavorites from '@/components/Profile/UserFavorites.vue'
import FullSettingsModal from '@/components/modal/profile/FullSettingsModal.vue'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const user = ref({})
const stats = ref({})
const isOnline = ref(false)
const activeTab = ref('feed')
const showFullSettingsModal = ref(false)

const tabs = [
  { id: 'feed', name: 'Лента' },
  { id: 'anime', name: 'Аниме' },
  { id: 'playlists', name: 'Плейлисты' },
  { id: 'shorts', name: 'Shorts' },
  { id: 'achievements', name: 'Достижения' },
  { id: 'favorites', name: 'Избранное' },
  { id: 'about', name: 'О себе' },
]

const currentUser = computed(() => authStore.user)

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
  try {
    const response = await api.get(`/users/profile/${currentUser.value.id}/`)
    user.value = response.data
    isOnline.value = response.data.is_online
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
  }
}

const loadStats = async () => {
  try {
    const response = await api.get(`/users/${currentUser.value.id}/stats/`)
    stats.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  }
}

const openFullSettings = () => {
  showFullSettingsModal.value = true
}

const openSettings = () => {
  router.push('/settings')
}

const openAvatarUpload = () => {
  showFullSettingsModal.value = true
}

const handleCoverUpload = async (event) => {
  const file = event.target.files[0]
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

const handleSettingsSaved = async () => {
  await authStore.fetchUser()
  loadProfile()
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
})
</script>

<style scoped>
.own-profile-view {
  max-width: 1200px;
  margin: 0 auto;
  background-color: var(--color-background);
  min-height: 100vh;
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
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: transform 0.15s ease;
}

.avatar:hover {
  transform: scale(1.05);
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
  font-style: italic;
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
}

.btn-edit,
.btn-settings {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-edit:hover,
.btn-settings:hover {
  background: var(--color-accent-hover);
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

.profile-content {
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
