<template>
  <div class="my-playlists-page">
    <div class="page-header">
      <h1>Мои плейлисты</h1>
      <router-link to="/playlists/create" class="create-btn">
        + Создать плейлист
      </router-link>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="playlists.length === 0" class="empty-state">
      <span class="icon">📚</span>
      <h2>Пока нет плейлистов</h2>
      <p>Создайте свой первый плейлист</p>
      <router-link to="/playlists/create" class="create-btn">
        Создать плейлист
      </router-link>
    </div>

    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        :current-user-id="currentUserId"
        @click="goToPlaylist(playlist)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import playlistsApi, { type Playlist } from '@/api/playlists'
import PlaylistCard from '@/components/PlaylistCard.vue'

const router = useRouter()
const playlists = ref<Playlist[]>([])
const currentUserId = ref<number | undefined>(undefined)
const loading = ref(true)

const loadPlaylists = async () => {
  try {
    const response = await playlistsApi.getMyPlaylists()
    playlists.value = response.data

    const userStr = localStorage.getItem('user_id')
    if (userStr) {
      currentUserId.value = parseInt(userStr)
    }
  } catch (error) {
    console.error('Ошибка загрузки плейлистов:', error)
  } finally {
    loading.value = false
  }
}

const goToPlaylist = (playlist: Playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

onMounted(() => {
  loadPlaylists()
})
</script>

<style scoped>
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--color-text-tertiary);
}

.empty-state {
  text-align: center;
  padding: 4rem 1rem;
}

.empty-state .icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-state h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.75rem 0;
}

.empty-state p {
  color: var(--color-text-tertiary);
  margin-bottom: 1.5rem;
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}
</style>