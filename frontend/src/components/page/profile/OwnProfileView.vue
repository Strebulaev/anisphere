<template>
  <div class="own-profile-view">
    <!-- Шапка профиля -->
    <div class="profile-header" :class="{ 'has-cover': user.cover_image_url }">
      <!-- Обложка профиля (только для премиум) -->
      <div
        v-if="user.cover_image_url"
        class="header-background"
        :style="coverImageStyle"
      >
        <label class="cover-upload-btn">
          <input 
            type="file" 
            accept="image/*" 
            @change="handleCoverSelect" 
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
            :is-online="isOnline"
            size="2xl"
            shape="circle"
          />
        </div>

        <div class="user-info">
          <!-- Отображаемое имя (то, что задал сам пользователь) -->
          <h1>
            {{ user.display_name || user.nickname || user.username }}
            <PremiumCrown v-if="user.is_premium" :size="24" class="premium-crown-inline" />
          </h1>
          <!-- Уникальный никнейм — один, не два -->
          <p class="username">
            @{{ user.nickname || user.username }}
            <PremiumCrown v-if="user.is_premium" :size="16" class="premium-crown-username" />
          </p>
          <p class="bio">{{ user.bio || 'Напишите что-то о себе...' }}</p>

          <div class="user-meta">
            <span v-if="user.experience" class="exp-badge"><SakuraIcon name="sparkles" /> {{ user.experience }} опыта</span>
            <span v-if="user.created_at">🗓 На сайте с {{ formatDate(user.created_at) }}</span>
          </div>
        </div>

        <div class="header-actions">
          <button @click="openSettings" class="btn-edit">
            <CogIcon class="w-5 h-5" />
            Настройки профиля
          </button>
          <!-- Админская панель -->
          <button v-if="isAdmin" @click="router.push('/admin')" class="btn-admin">
            🛡️ Админ
          </button>
        </div>

    <!-- Статистика -->
    <!-- <div class="stats">
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
        <span class="stat-label">достижений</span> -->
      </div>
    </div>
  </div>
  
  <!-- Модальное окно выбора области обложки -->
  <CoverCropModal 
    :show="showCoverModal"
    :image-url="selectedCoverUrl"
    @close="handleCoverModalClose"
    @save="handleCoverSave"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CogIcon } from '@heroicons/vue/24/outline'
import api from '@/api'
import CoverCropModal from '@/components/modal/CoverCropModal.vue'
import UserAvatar from '@/components/ui/UserAvatar.vue'
import PremiumCrown from '@/components/icons/PremiumCrown.vue'

interface UserProfile {
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
  cover_position_x?: number
  cover_position_y?: number
  is_premium?: boolean
}

interface UserStats {
  followers?: number
  following?: number
  posts?: number
  playlists?: number
  achievements?: number
}

const router = useRouter()
const authStore = useAuthStore()

const user = ref<UserProfile>({})
const stats = ref<UserStats>({})
const isOnline = ref<boolean | null>(null)

// Модальное окно обрезки обложки
const showCoverModal = ref(false)
const selectedCoverFile = ref<File | null>(null)
const selectedCoverUrl = ref('')

// Администраторские права
const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return false
  return u.is_admin || u.is_staff || u.username === 'kaiden812'
})

const currentUser = computed(() => authStore.user)

const coverImageStyle = computed(() => {
  if (user.value.cover_image_url) {
    const positionX = user.value.cover_position_x ?? 50
    const positionY = user.value.cover_position_y ?? 50
    return {
      backgroundImage: `url(${user.value.cover_image_url})`,
      backgroundSize: 'cover',
      backgroundPosition: `${positionX}% ${positionY}%`
    }
  }
  return {}
})

const loadProfile = async () => {
  if (!currentUser.value?.id) return
  try {
    const response = await api.get(`/users/profile/${currentUser.value.id}/`)
    user.value = response.data
    isOnline.value = response.data.is_online ?? null
  } catch (error) {
    console.error('Ошибка загрузки профиля:', error)
  }
}

const loadStats = async () => {
  if (!currentUser.value?.id) return
  try {
    const response = await api.get(`/users/${currentUser.value.id}/stats/`)
    stats.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  }
}

const openSettings = () => {
  router.push('/settings')
}

// Выбор файла обложки - открываем модальное окно
const handleCoverSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) return
  const file = target.files[0]
  if (!file) return

  // Проверяем тип файла
  if (!file.type.startsWith('image/')) {
    alert('Пожалуйста, выберите изображение')
    return
  }
  
  // Проверяем размер (макс 10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert('Размер файла не должен превышать 10MB')
    return
  }
  
  selectedCoverFile.value = file
  // Создаём URL для предпросмотра
  selectedCoverUrl.value = URL.createObjectURL(file)
  showCoverModal.value = true
  
  // Сбрасываем input
  target.value = ''
}

// Закрытие модального окна
const handleCoverModalClose = () => {
  showCoverModal.value = false
  if (selectedCoverUrl.value) {
    URL.revokeObjectURL(selectedCoverUrl.value)
  }
  selectedCoverFile.value = null
  selectedCoverUrl.value = ''
}

// Сохранение обложки с позицией
interface CoverPosition {
  x: number
  y: number
}

const handleCoverSave = async (position: CoverPosition) => {
  if (!selectedCoverFile.value) return
  
  const formData = new FormData()
  formData.append('cover_image', selectedCoverFile.value)
  formData.append('cover_position_x', position.x.toString())
  formData.append('cover_position_y', position.y.toString())
  
  try {
    const response = await api.patch(`/users/profile/update/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    user.value.cover_image_url = response.data.cover_image_url
    user.value.cover_image = response.data.cover_image
    user.value.cover_position_x = position.x
    user.value.cover_position_y = position.y
    
    handleCoverModalClose()
  } catch (error) {
    console.error('Ошибка загрузки обложки:', error)
    alert('Не удалось загрузить обложку')
  }
}


const formatDate = (date: string | Date | undefined) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

onMounted(() => {
  // Если есть ID пользователя - редирект на /profile/{id}
  if (currentUser.value?.id) {
    router.replace(`/profile/${currentUser.value.id}`)
    return
  }
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

.btn-admin {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid #ef4444;
  border-radius: var(--radius-button);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-admin:hover {
  background: rgba(239, 68, 68, 0.25);
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
