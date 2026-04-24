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
        @favorite-toggle="toggleFavorite"
        @share="openShareModal"
        @edit="openEditModal"
        @delete="confirmDelete"
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
import { useRouter } from 'vue-router'

interface Props {
  userId: number
}

const props = defineProps<Props>()
const authStore = useAuthStore()
const router = useRouter()

const loading = ref(true)
const playlists = ref<any[]>([])
const currentUserId = computed(() => authStore.user?.id)

const loadUserPlaylists = async () => {
  loading.value = true
  try {
    const response = await apiClient.get(`/playlists/playlists/`, {
      params: {
        user: props.userId,
        visibility: 'public',
        ordering: '-updated_at'
      }
    })
    
    const rawData = response.data
    
    let dataArray: any[] = []
    
    if (Array.isArray(rawData)) {
      dataArray = rawData
    } else if (rawData?.results) {
      dataArray = rawData.results
    } else {
      dataArray = []
    }
    
    playlists.value = dataArray.filter(p => p && p.id && typeof p.id === 'number')
    
  } catch (error: any) {
    console.error('Error loading playlists:', error)
    playlists.value = []
  } finally {
    loading.value = false
  }
}

// Обработчики событий
const toggleFavorite = async (playlistId: number, isFavorite: boolean) => {
  try {
    await apiClient.post(`/playlists/playlists/${playlistId}/toggle-favorite/`)
    // Перезагружаем плейлисты чтобы обновить счётчики
    await loadUserPlaylists()
  } catch (error) {
    console.error('Error toggling favorite:', error)
  }
}

const openShareModal = async (playlistId: number) => {
  const url = `${window.location.origin}/playlists/${playlistId}`
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Плейлист',
        url: url
      })
    } catch (error) {
      console.log('Error sharing:', error)
      copyToClipboard(url)
    }
  } else {
    copyToClipboard(url)
  }
}

const openEditModal = (playlist: any) => {
  router.push(`/playlists/${playlist.id}/edit`)
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    alert('Ссылка скопирована в буфер обмена')
  }).catch(() => {
    alert(`Ссылка: ${text}`)
  })
}

const confirmDelete = async (playlist: any) => {
  if (!confirm(`Удалить плейлист "${playlist.title}"?`)) return
  
  try {
    await apiClient.delete(`/playlists/playlists/${playlist.id}/`)
    // Удаляем из списка
    playlists.value = playlists.value.filter(p => p.id !== playlist.id)
  } catch (error) {
    console.error('Error deleting playlist:', error)
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
