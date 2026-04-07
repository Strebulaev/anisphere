<template>
  <div class="ni-card">
    <div class="user-info" @click="goToProfile">
      <img :src="user.avatar_url || defaultAvatar" :alt="user.username" class="avatar" />
      <div class="user-details">
        <span class="display-name">{{ user.display_name || user.username }}</span>
        <span class="username">@{{ user.username }}</span>
        <span class="hidden-since">Скрыт {{ formatDate(user.hidden_at) }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button class="btn-unblock" :class="{ loading: isRemoving }" @click.stop="handleRemove" :disabled="isRemoving">
        <span v-if="!isRemoving"><SakuraIcon name="eye" /> Разблокировать</span>
        <span v-else>...</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { NotInterestedUser } from '@/api/feed'
import { subscriptionsApi } from '@/api/feed'

const props = defineProps<{ user: NotInterestedUser }>()
const emit = defineEmits<{ removed: [userId: number] }>()

const router = useRouter()
const isRemoving = ref(false)

const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })

const goToProfile = () => router.push(`/profile/${props.user.username}`)

const handleRemove = async () => {
  isRemoving.value = true
  try {
    await subscriptionsApi.removeNotInterested(props.user.id)
    emit('removed', props.user.id)
  } catch (e) {
    console.error(e)
  } finally {
    isRemoving.value = false
  }
}
</script>

<style scoped>
.ni-card {
  display: flex; align-items: center; justify-content: space-between;
  background: #111; border-radius: 12px; padding: 0.875rem 1rem;
  transition: background 0.2s;
}
.ni-card:hover { background: #161616; }

.user-info { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; flex: 1; min-width: 0; }
.avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; flex-shrink: 0; filter: grayscale(30%); }
.user-details { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
.display-name { color: #bbb; font-weight: 600; font-size: 0.95rem; }
.username { color: #555; font-size: 0.8rem; }
.hidden-since { color: #444; font-size: 0.75rem; }

.card-actions { flex-shrink: 0; }
.btn-unblock {
  background: #1a2a1a; border: 1px solid #2a4a2a; color: #4ade80;
  padding: 0.5rem 0.875rem; border-radius: 8px; cursor: pointer;
  font-size: 0.8rem; font-weight: 500; transition: all 0.2s; white-space: nowrap;
}
.btn-unblock:hover:not(:disabled) { background: #1f3a1f; border-color: #4ade80; }
.btn-unblock.loading { opacity: 0.6; cursor: not-allowed; }
</style>
