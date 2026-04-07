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
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'
import apiClient from '@/api/client'

interface Props {
  userId: number
}

const props = defineProps<Props>()
const authStore = useAuthStore()

const loading = ref(true)
const playlists = ref<any[]>([])
const currentUserId = computed(() => authStore.user?.id)

const loadUserPlaylists = async () => {
  loading.value = true
  try {
    // Запрашиваем публичные плейлисты пользователя
    // Важно: используем правильный endpoint - /playlists/playlists/
    const response = await apiClient.get(`/playlists/playlists/`, {
      params: {
        user: props.userId,
        visibility: 'public',
        ordering: '-updated_at'
      }
    })
    
    // Обрабатываем ответ
    const rawData = response.data
    
    let dataArray: any[] = []
    
    if (Array.isArray(rawData)) {
      dataArray = rawData
    } else if (rawData?.results) {
      dataArray = rawData.results
    } else {
      dataArray = []
    }
    
    // Фильтруем валидные плейлисты
    playlists.value = dataArray.filter(p => p && p.id && typeof p.id === 'number')
    
  } catch (error: any) {
    console.error('Error loading playlists:', error)
    playlists.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.userId,
  (newUserId) => {
    if (newUserId && !isNaN(newUserId)) {
      loadUserPlaylists()
    } else {
      playlists.value = []
    }
  },
  { immediate: true }
)
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
