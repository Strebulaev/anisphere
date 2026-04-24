<template>
  <div class="subscription-card">
    <div class="user-info" @click="goToProfile">
      <div class="avatar-wrapper">
        <img :src="user.avatar_url || defaultAvatar" :alt="user.username" class="avatar" />
        <span class="online-dot" v-if="user.is_online"></span>
      </div>
      <div class="user-details">
        <span class="display-name">{{ user.display_name || user.username }}</span>
        <span class="username">@{{ user.username }}</span>
        <span class="followers">{{ formatCount(user.followers_count || 0) }} подписчиков</span>
        <span v-if="user.followed_at" class="followed-at">с {{ formatDate(user.followed_at) }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button class="btn-message" @click.stop="goToChat" title="Написать"> <SakuraIcon name="message" /> </button>
      <button
        class="btn-unfollow"
        :class="{ loading: isUnfollowing, confirmed: confirmUnfollow }"
        @click.stop="handleUnfollow"
        :disabled="isUnfollowing"
      >
        <span v-if="isUnfollowing">...</span>
        <span v-else-if="confirmUnfollow">Отписаться?</span>
        <span v-else>✓ Подписан</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { SubscriptionUser } from '@/api/feed'
import { subscriptionsApi } from '@/api/feed'

const props = defineProps<{ user: SubscriptionUser }>()
const emit = defineEmits<{ unfollowed: [userId: number] }>()

const router = useRouter()
const isUnfollowing = ref(false)
const confirmUnfollow = ref(false)
let confirmTimer: ReturnType<typeof setTimeout> | null = null

const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`

const formatCount = (n: number) => {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'М'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'К'
  return String(n || 0)
}

const formatDate = (s: string) => {
  return new Date(s).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

const goToProfile = () => router.push(`/profile/${props.user.username}`)
const goToChat = async () => {
  try {
    const api = await import('@/api/client')
    const response = await api.default.post('/social/private-chats/', { user2: props.user.id })
    router.push(`/chats/${response.data.id}`)
  } catch (error) {
    console.error('Error creating chat:', error)
    alert('Не удалось создать чат')
  }
}

const handleUnfollow = async () => {
  if (isUnfollowing.value) return
  // Первый клик — показываем подтверждение
  if (!confirmUnfollow.value) {
    confirmUnfollow.value = true
    confirmTimer = setTimeout(() => { confirmUnfollow.value = false }, 3000)
    return
  }
  // Второй клик — отписываемся
  if (confirmTimer) clearTimeout(confirmTimer)
  confirmUnfollow.value = false
  isUnfollowing.value = true
  try {
    await subscriptionsApi.unfollow(props.user.id)
    emit('unfollowed', props.user.id)
  } catch (e) {
    console.error(e)
  } finally {
    isUnfollowing.value = false
  }
}
</script>

<style scoped>
.subscription-card {
  display: flex; align-items: center; justify-content: space-between;
  background: #111; border-radius: 12px; padding: 0.875rem 1rem;
  transition: background 0.2s; cursor: default;
}
.subscription-card:hover { background: #161616; }

.user-info { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; flex: 1; min-width: 0; }
.avatar-wrapper { position: relative; flex-shrink: 0; }
.avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.online-dot { position: absolute; bottom: 2px; right: 2px; width: 10px; height: 10px; background: #22c55e; border-radius: 50%; border: 2px solid #111; }

.user-details { display: flex; flex-direction: column; gap: 0.05rem; min-width: 0; }
.display-name { color: #fff; font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.username { color: #666; font-size: 0.8rem; }
.followers { color: #555; font-size: 0.75rem; }
.followed-at { color: #444; font-size: 0.72rem; }

.card-actions { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
.btn-message { background: #1a1a1a; border: none; width: 36px; height: 36px; border-radius: 8px; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
.btn-message:hover { background: #252525; }

.btn-unfollow {
  background: #1a2a3a; border: 1px solid #334; color: #667eea;
  padding: 0.5rem 0.875rem; border-radius: 8px; cursor: pointer;
  font-size: 0.8rem; font-weight: 500; transition: all 0.2s; white-space: nowrap; min-width: 90px; text-align: center;
}
.btn-unfollow:hover:not(:disabled) { background: #1f1f2e; border-color: #667eea; }
.btn-unfollow.confirmed { background: #3a1a1a; border-color: #ef4444; color: #ef4444; }
.btn-unfollow.loading { opacity: 0.6; cursor: not-allowed; }
</style>
