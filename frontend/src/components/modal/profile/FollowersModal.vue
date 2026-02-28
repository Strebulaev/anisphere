<template>
  <BaseModal
    :show="props.show"
    :title="isFollowers ? 'ПОДПИСЧИКИ' : 'ПОДПИСКИ'"
    @update:show="emit('update:show', false)"
  >
    <div class="followers-modal">
      <div class="search-box">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          type="text"
          :placeholder="isFollowers ? 'Поиск по подписчикам' : 'Поиск по подпискам'"
          v-model="searchQuery"
        >
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка...</p>
      </div>

      <div v-else-if="filteredUsers.length === 0" class="empty-state">
        <div class="empty-icon">👥</div>
        <h3>
          {{ isFollowers ? 'Здесь пока никого нет' : 'Вы ещё не подписались ни на кого' }}
        </h3>
        <p>
          {{ isFollowers 
            ? 'Когда кто-то подпишется, они появятся в этом списке' 
            : 'Находите интересных людей в ленте!' 
          }}
        </p>
      </div>

      <div v-else class="users-list">
        <div
          v-for="user in filteredUsers"
          :key="user.id"
          class="user-item"
        >
          <div class="user-avatar" @click="goToProfile(user)">
            <img
              v-if="user.avatar"
              :src="user.avatar_url || user.avatar"
              :alt="user.display_name || user.username"
              @error="onAvatarError"
            >
            <div v-else class="avatar-placeholder">
              {{ getUserInitials(user) }}
            </div>
            <div v-if="user.is_online" class="online-indicator"></div>
          </div>
          <div class="user-info" @click="goToProfile(user)">
            <h4 class="user-name">{{ user.display_name || user.username }}</h4>
            <p class="user-nickname">@{{ user.nickname || user.username }}</p>
          </div>
          <button
            v-if="!isFollowers && !isFollowing(user.id)"
            class="follow-button"
            @click="followUser(user.id)"
          >
            Подписаться
          </button>
          <button
            v-else-if="!isFollowers"
            class="following-button"
            @click="unfollowUser(user.id)"
          >
            ✓ Подписан
          </button>
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import BaseModal from '@/components/ui/BaseModal.vue'
import type { User } from '@/types'

interface Props {
  show: boolean
  users: User[]
  isFollowers?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isFollowers: true,
  loading: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  follow: [userId: number]
  unfollow: [userId: number]
}>()

const router = useRouter()
const searchQuery = ref('')
const followingList = ref<Set<number>>(new Set())

const filteredUsers = computed(() => {
  if (!searchQuery.value) {
    return props.users
  }
  
  const query = searchQuery.value.toLowerCase()
  return props.users.filter(user => 
    (user.display_name || user.username).toLowerCase().includes(query) ||
    (user.nickname || user.username).toLowerCase().includes(query)
  )
})

const getUserInitials = (user: User) => {
  const name = (user as any).display_name || user.username
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

const isFollowing = (userId: number) => {
  return followingList.value.has(userId)
}

const followUser = (userId: number) => {
  emit('follow', userId)
  followingList.value.add(userId)
}

const unfollowUser = (userId: number) => {
  emit('unfollow', userId)
  followingList.value.delete(userId)
}

const goToProfile = (user: User) => {
  emit('update:show', false)
  router.push(`/@${user.nickname || user.username}`)
}

const onAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}
</script>

<style scoped>
.followers-modal {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 500px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
}

.search-box svg {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  background: none;
  font-size: 0.95rem;
  color: var(--color-text-primary);
  outline: none;
}

.search-box input::placeholder {
  color: var(--color-text-tertiary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
  color: var(--color-text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.1rem;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.empty-state p {
  font-size: 0.9rem;
  margin: 0;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
  max-height: 400px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background-surface);
  border-radius: 0.5rem;
  transition: background-color 0.15s ease;
}

.user-item:hover {
  background: var(--color-background-hover);
}

.user-avatar {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
  font-weight: bold;
  font-size: 1rem;
}

.online-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 10px;
  height: 10px;
  background: #10b981;
  border-radius: 50%;
  border: 2px solid var(--color-background-surface);
}

.user-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.user-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.125rem 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-nickname {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.follow-button {
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
  white-space: nowrap;
}

.follow-button:hover {
  background: var(--color-primary-hover);
}

.following-button {
  padding: 0.5rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider);
  color: var(--color-text-secondary);
  border-radius: 0.375rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.following-button:hover {
  background: var(--color-background-hover);
  color: var(--color-text-primary);
}
</style>
