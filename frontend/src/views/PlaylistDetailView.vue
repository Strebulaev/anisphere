<template>
  <div class="playlist-detail-page">
    <PlaylistDetail
      v-if="playlist"
      :playlist="playlist"
      :current-user-id="currentUserId"
      @toggle-favorite="toggleFavorite"
      @duplicate="duplicatePlaylist"
    />
    <div v-else-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>
    <div v-else class="error">
      <p>Плейлист не найден</p>
      <router-link to="/playlists">Вернуться к плейлистам</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import playlistsApi, { type Playlist } from '@/api/playlists'
import PlaylistDetail from '@/components/PlaylistDetail.vue'

const route = useRoute()
const router = useRouter()
const playlist = ref<Playlist | null>(null)
const currentUserId = ref<number | undefined>(undefined)
const loading = ref(true)

const loadPlaylist = async () => {
  const id = route.params.id
  if (!id || typeof id !== 'string') return

  try {
    const response = await playlistsApi.getPlaylist(parseInt(id))
    playlist.value = response.data

    const userStr = localStorage.getItem('user_id')
    if (userStr) {
      currentUserId.value = parseInt(userStr)
    }
  } catch (error) {
    console.error('Ошибка загрузки плейлиста:', error)
  } finally {
    loading.value = false
  }
}

const toggleFavorite = async (pl: Playlist) => {
  try {
    if (pl.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(pl.id)
      if (playlist.value) {
        playlist.value.is_favorited = false
        playlist.value.favorites_count = Math.max(0, playlist.value.favorites_count - 1)
      }
    } else {
      await playlistsApi.addPlaylistToFavorites(pl.id)
      if (playlist.value) {
        playlist.value.is_favorited = true
        playlist.value.favorites_count++
      }
    }
  } catch (error) {
    console.error('Ошибка изменения избранного:', error)
  }
}

const duplicatePlaylist = async (pl: Playlist) => {
  try {
    const response = await playlistsApi.duplicatePlaylist(pl.id)
    router.push(`/playlist/${response.data.id}`)
  } catch (error) {
    console.error('Ошибка копирования плейлиста:', error)
    alert('Не удалось скопировать плейлист')
  }
}

onMounted(() => {
  loadPlaylist()
})
</script>

<style scoped>
.playlist-detail-page {
  padding: 1.5rem;
  max-width: 900px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 4rem 1rem;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--color-text-tertiary);
}

.error {
  text-align: center;
  padding: 4rem 1rem;
}

.error p {
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
  margin-bottom: 1rem;
}

.error a {
  color: var(--color-accent);
  text-decoration: none;
}

.error a:hover {
  text-decoration: underline;
}
</style>