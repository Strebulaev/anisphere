7<template>
  <div class="user-card" @click="handleClick">
    <div class="user-avatar">
      <OptimizedImage
        v-if="user.avatar_url"
        :src="getMediaUrl(user.avatar_url) || undefined"
        :alt="user.display_name || user.username"
        class="avatar-image"
      />
      <div v-else class="avatar-placeholder">
        {{ (user.display_name || user.username)?.[0]?.toUpperCase() }}
      </div>
      <div :class="['status-indicator', statusClass]"></div>
    </div>

    <div class="user-info">
      <h3 class="user-name">{{ user.display_name || user.username }}</h3>
      <p class="user-username">@{{ user.username }}</p>
      
      <div v-if="user.nickname" class="user-nickname">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        {{ user.nickname }}
      </div>

      <div class="user-status" v-if="userStatus">
        <span class="status-text">{{ userStatus }}</span>
      </div>

      <div class="user-stats">
        <div class="stat-item" v-if="user.followers_count !== undefined">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>{{ formatNumber(user.followers_count) }}</span>
        </div>
      </div>

      <div v-if="achievements?.length" class="user-achievements">
        <div
          v-for="achievement in achievements.slice(0, 2)"
          :key="achievement.id"
          class="achievement-badge"
          :title="achievement.name"
        >
          <OptimizedImage
            v-if="achievement.icon"
            :src="getMediaUrl(achievement.icon) || undefined"
            :alt="achievement.name"
          />
          <div v-else class="achievement-placeholder">
            {{ achievement.name?.[0] }}
          </div>
        </div>
      </div>
    </div>

    <div class="user-actions">
      <button
        v-if="!isCurrentUser"
        @click.stop="toggleFollow"
        :class="['follow-btn', { following: isFollowing }]"
        type="button"
      >
        <svg v-if="!isFollowing" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="8.5" cy="7" r="4"/>
          <line x1="20" y1="8" x2="20" y2="14"/>
          <line x1="23" y1="11" x2="17" y2="11"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        {{ isFollowing ? 'Подписан' : 'Подписаться' }}
      </button>
      
      <button
        @click.stop="startChat"
        class="message-btn"
        type="button"
        title="Написать сообщение"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMediaUrl } from '@/api/client'
import type { User, Achievement } from '@/types'

interface Props {
  user: User
  achievements?: Achievement[]
  isCurrentUser?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isCurrentUser: false
})

const emit = defineEmits<{
  click: [user: User]
  follow: [userId: number]
  unfollow: [userId: number]
  message: [user: User]
}>()

const router = useRouter()
const isFollowing = ref(false)

const statusClass = computed(() => {
  if (props.user.is_online) return 'online'
  if (props.user.status?.status) {
    return 'away'
  }
  return 'offline'
})

const userStatus = computed(() => {
  if (props.user.is_online) return '🟢 В сети'
  
  const status = props.user.status
  if (status?.custom_status) return status.custom_status
  if (status?.last_seen) {
    const lastSeen = new Date(status.last_seen)
    const now = new Date()
    const diff = Math.floor((now.getTime() - lastSeen.getTime()) / 1000 / 60)
    
    if (diff < 60) return `⚫ Был(а) ${diff} мин. назад`
    if (diff < 1440) return `⚫ Был(а) ${Math.floor(diff / 60)} ч. назад`
    return `⚫ Был(а) ${lastSeen.toLocaleDateString('ru-RU')}`
  }
  
  return '⚫ Не в сети'
})

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const handleClick = () => {
  emit('click', props.user)
}

const toggleFollow = () => {
  if (isFollowing.value) {
    emit('unfollow', props.user.id)
  } else {
    emit('follow', props.user.id)
  }
  isFollowing.value = !isFollowing.value
}

const startChat = () => {
  emit('message', props.user)
}
</script>

<style scoped>
.user-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.user-card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

.user-avatar {
  position: relative;
  flex-shrink: 0;
}

.avatar-image {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-divider-light);
}

.avatar-placeholder {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-pink));
  color: var(--color-text);
  font-size: 1.5rem;
  font-weight: 800;
  border: 2px solid var(--color-divider-light);
}

.status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--color-background-surface);
}

.status-indicator.online {
  background-color: #22c55e;
}

.status-indicator.away {
  background-color: #f59e0b;
}

.status-indicator.offline {
  background-color: #6b7280;
}

.user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-username {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-nickname {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--color-accent);
  margin: 0;
}

.user-status {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.status-text {
  font-weight: 500;
}

.user-stats {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.user-achievements {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.375rem;
}

.achievement-badge {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
}

.achievement-badge img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.achievement-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 800;
}

.user-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-self: center;
}

.follow-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  white-space: nowrap;
}

.follow-btn:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.follow-btn.following {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.follow-btn.following:hover {
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
  background-color: rgba(255, 42, 109, 0.05);
}

.message-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.message-btn:hover {
  border-color: var(--color-accent-teal);
  color: var(--color-accent-teal);
  background-color: rgba(0, 212, 170, 0.05);
}

@media (max-width: 768px) {
  .user-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 0.875rem;
  }

  .user-avatar {
    margin-bottom: 0.5rem;
  }

  .avatar-image,
  .avatar-placeholder {
    width: 56px;
    height: 56px;
  }

  .user-stats {
    justify-content: center;
  }

  .user-achievements {
    justify-content: center;
  }

  .user-actions {
    flex-direction: row;
    width: 100%;
  }

  .follow-btn {
    flex: 1;
  }
}
</style>
