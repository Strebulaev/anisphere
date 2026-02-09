<template>
  <div class="profile-page">
    <div class="container profile-container">
      <div class="profile-header">
        <div class="user-avatar-large">
          <img v-if="authStore.user?.avatar" :src="getAvatarUrl(authStore.user.avatar)" :alt="authStore.user?.display_name || authStore.user?.username" class="avatar-image" @error="onAvatarError">
          <div v-else class="avatar-placeholder">
            {{ getUserInitials(authStore.user || { username: '?', display_name: undefined }) }}
          </div>
        </div>
        <div class="user-info">
          <div class="name-row">
            <h1 class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</h1>
            <div v-if="authStore.user?.is_online" class="online-status">
              <span class="online-dot"></span>
              <span class="online-text">онлайн</span>
            </div>
          </div>
          <p class="user-nickname">@{{ authStore.user?.nickname || authStore.user?.username }}</p>
          <p class="user-email">{{ authStore.user?.email }}</p>
          <div class="user-stats">
            <span class="stat-item">
              <strong>{{ userJoinDate }}</strong> в сообществе
            </span>
          </div>
          <div class="user-bio" v-if="(authStore.user as any)?.bio">
            <p>{{ (authStore.user as any).bio }}</p>
          </div>
        </div>
      </div>

      <div class="profile-content">
        <div class="profile-section">
          <h2>Информация об аккаунте</h2>
          <div class="info-grid">
            <div class="info-item">
              <label>Отображаемое имя</label>
              <span>{{ authStore.user?.display_name || 'Не указано' }}</span>
            </div>
            <div class="info-item">
              <label>Никнейм</label>
              <span>@{{ authStore.user?.nickname || authStore.user?.username }}</span>
            </div>
            <div class="info-item">
              <label>Email</label>
              <span>{{ authStore.user?.email }}</span>
            </div>
            <div class="info-item">
              <label>Статус email</label>
              <span :class="['status-badge', authStore.user?.email_verified ? 'verified' : 'unverified']">
                {{ authStore.user?.email_verified ? 'Подтверждён' : 'Не подтверждён' }}
              </span>
            </div>
            <div class="info-item">
              <label>Дата регистрации</label>
              <span>{{ userJoinDate }}</span>
            </div>
            <div class="info-item" v-if="(authStore.user as any)?.website">
              <label>Веб-сайт</label>
              <a :href="(authStore.user as any).website" target="_blank" class="link">{{ (authStore.user as any).website }}</a>
            </div>
            <div class="info-item" v-if="(authStore.user as any)?.vk_profile">
              <label>ВКонтакте</label>
              <a :href="'https://vk.com/' + (authStore.user as any).vk_profile" target="_blank" class="link">{{ (authStore.user as any).vk_profile }}</a>
            </div>
            <div class="info-item" v-if="(authStore.user as any)?.telegram">
              <label>Telegram</label>
              <a :href="'https://t.me/' + (authStore.user as any).telegram" target="_blank" class="link">@{{ (authStore.user as any).telegram }}</a>
            </div>
          </div>
        </div>

        <div class="profile-section" v-if="(authStore.user as any)?.favorite_genres?.length">
          <h2>Любимые жанры</h2>
          <div class="genres-list">
            <span v-for="genreId in (authStore.user as any).favorite_genres" :key="genreId" class="genre-tag">
              {{ getGenreName(genreId) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <EditProfileModal
      :is-visible="showEditProfile"
      :user="authStore.user"
      @close="showEditProfile = false"
      @save="handleProfileSave"
    />

    <!-- Settings Modal -->
    <SettingsModal
      :is-visible="showSettings"
      @close="showSettings = false"
      @save="handleSettingsSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAvatar } from '@/composables/useAvatar'
import EditProfileModal from '@/components/EditProfileModal.vue'
import SettingsModal from '@/components/SettingsModal.vue'

const authStore = useAuthStore()
const { getAvatarUrl, getUserInitials } = useAvatar()

const showEditProfile = ref(false)
const showSettings = ref(false)

const genreNames: Record<string, string> = {
  'action': 'Экшен',
  'adventure': 'Приключения',
  'comedy': 'Комедия',
  'drama': 'Драма',
  'fantasy': 'Фэнтези',
  'romance': 'Романтика',
  'scifi': 'Sci-Fi',
  'horror': 'Ужасы',
  'mystery': 'Детектив',
  'slice_of_life': 'Повседневность'
}

// getUserInitials is now imported from useAvatar composable

const userJoinDate = computed(() => {
  if (!authStore.user?.created_at) return 'Неизвестно'
  return new Date(authStore.user.created_at).toLocaleDateString('ru-RU')
})

const getGenreName = (genreId: string) => {
  return genreNames[genreId] || genreId
}

// getAvatarUrl is now imported from useAvatar composable

const onAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // Скрываем изображение при ошибке загрузки
  img.style.display = 'none'
  // Можно добавить логику для показа placeholder или повторной загрузки
  console.warn('Failed to load avatar:', img.src)
}

const openEditProfile = () => {
  showEditProfile.value = true
}

const openSettings = () => {
  showSettings.value = true
}

const handleProfileSave = async (updatedProfile: any) => {
  // Update user data in store
  authStore.user = { ...authStore.user, ...updatedProfile }
  // Optionally refresh user data from API
  await authStore.fetchUser()
}

const handleSettingsSave = (settings: any) => {
  // Save settings to localStorage
  localStorage.setItem('userSettings', JSON.stringify(settings))
  // Could also send to API
  console.log('Settings saved:', settings)
}

const changePassword = () => {
  // TODO: Реализовать изменение пароля
  alert('Функция изменения пароля будет добавлена позже')
}

const deleteAccount = () => {
  if (confirm('Вы действительно хотите удалить аккаунт? Это действие нельзя отменить.')) {
    // TODO: Реализовать удаление аккаунта
    alert('Функция удаления аккаунта будет добавлена позже')
  }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: var(--color-background);
  padding-bottom: 2rem;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.profile-header {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 2rem;
}

.user-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: white;
  font-size: 2rem;
  font-weight: bold;
}

.user-info {
  flex: 1;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.user-name {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.online-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.online-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.online-text {
  font-size: 0.875rem;
  color: #10b981;
  font-weight: 500;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.user-nickname {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.user-email {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: 1rem;
}

.user-bio {
  margin-top: 0.5rem;
}

.user-bio p {
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.user-stats {
  display: flex;
  gap: 1rem;
}

.stat-item {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.profile-content {
  display: grid;
  gap: 2rem;
}

.profile-section {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.profile-section h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item span {
  font-size: 1rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.verified {
  background-color: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-badge.unverified {
  background-color: rgba(220, 38, 38, 0.2);
  color: #dc2626;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.link {
  color: var(--color-primary);
  text-decoration: none;
  word-break: break-all;
}

.link:hover {
  text-decoration: underline;
}

.genres-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.genre-tag {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.btn-danger {
  background-color: #dc2626;
  color: white;
  border-color: #dc2626;
}

.btn-danger:hover {
  background-color: #b91c1c;
}

.logout-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

/* Адаптивность */
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .user-avatar-large {
    width: 60px;
    height: 60px;
    font-size: 1.5rem;
  }

  .user-name {
    font-size: 1.5rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>