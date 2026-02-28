<template>
  <div class="user-public-playlists">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка плейлистов...</p>
    </div>
    <div v-else-if="playlists.length === 0" class="empty">
      <p>Нет публичных плейлистов</p>
    </div>
    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        :current-user-id="currentUserId"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'

interface Props {
  userId: number
}

const props = defineProps<Props>()
const authStore = useAuthStore()

const loading = ref(true)
const playlists = ref<any[]>([])
const currentUserId = ref<number | undefined>(authStore.user?.id)

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/users/${props.userId}/public-playlists/`)
    const data = await response.json()
    playlists.value = data.results || data
  } catch (error) {
    console.error('Ошибка загрузки плейлистов:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-public-playlists {
  min-height: 400px;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--color-text-secondary);
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
</style>
