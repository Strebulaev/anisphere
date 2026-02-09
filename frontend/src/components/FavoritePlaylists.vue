<template>
  <div class="favorites-page">
    <div class="page-header">
      <h1>Избранные плейлисты</h1>
      <p v-if="favorites.length > 0" class="count">
        {{ favorites.length }} плейлистов
      </p>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <span class="icon">📚</span>
      <h2>Пока ничего нет</h2>
      <p>Добавьте плейлисты в избранное, нажав на ♥</p>
      <router-link to="/playlists" class="browse-btn">
        Обзор плейлистов
      </router-link>
    </div>

    <div v-else class="playlists-grid">
      <div
        v-for="item in favorites"
        :key="item.id"
        class="playlist-card"
        @click="goToPlaylist(item.playlist_data)"
      >
        <div class="playlist-header">
          <h3 class="playlist-title">{{ item.playlist_data.title }}</h3>
          <span v-if="!item.playlist_data.is_public" class="private-badge">Приватный</span>
        </div>

        <p class="playlist-description" v-if="item.playlist_data.description">
          {{ item.playlist_data.description.slice(0, 100) }}
          <span v-if="item.playlist_data.description.length > 100">...</span>
        </p>

        <div class="playlist-meta">
          <span class="meta-item">
            <span class="icon">📺</span>
            {{ item.playlist_data.items_count }} аниме
          </span>
          <span class="meta-item">
            <span class="icon">👤</span>
            {{ item.playlist_data.user_username }}
          </span>
        </div>

        <div class="playlist-stats">
          <span class="stat">
            <span class="icon">📅</span>
            {{ formatDate(item.created_at) }}
          </span>
        </div>

        <div class="playlist-actions">
          <button
            class="action-btn favorite-btn active"
            @click.stop="toggleFavorite(item.playlist_data.id)"
          >
            <span class="icon">♥</span>
            В избранном
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import playlistsApi from '@/api/playlists'

interface PlaylistData {
  id: number
  title: string
  description: string
  is_public: boolean
  user_username: string
  items_count: number
  created_at: string
}

interface FavoriteItem {
  id: number
  playlist_data: PlaylistData
  created_at: string
}

const router = useRouter()
const favorites = ref<FavoriteItem[]>([])
const loading = ref(true)

const loadFavorites = async () => {
  try {
    const response = await playlistsApi.getFavoritePlaylists()
    favorites.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки избранных плейлистов:', error)
  } finally {
    loading.value = false
  }
}

const goToPlaylist = (playlist: PlaylistData) => {
  router.push(`/playlist/${playlist.id}`)
}

const toggleFavorite = async (playlistId: number) => {
  try {
    await playlistsApi.removePlaylistFromFavorites(playlistId)
    favorites.value = favorites.value.filter(f => f.playlist_data.id !== playlistId)
  } catch (error) {
    console.error('Ошибка удаления из избранного:', error)
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorite-playlists {
  background: var(--color-background);
  min-height: 100vh;
  padding: 1.5rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: all 0.2s;
}

.back-btn:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}

.header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.loading,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.loading .icon,
.empty-state .icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.loading p,
.empty-state p {
  color: var(--color-text-tertiary);
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}

.playlist-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.75rem;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.playlist-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.15);
}

.playlist-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.playlist-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
  line-height: 1.3;
}

.private-badge {
  padding: 0.25rem 0.5rem;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 0.25rem;
  white-space: nowrap;
}

.playlist-description {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  line-height: 1.5;
  margin: 0 0 1rem 0;
}

.playlist-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.meta-item .icon {
  font-size: 0.875rem;
}

.playlist-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-divider-weak);
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--color-text-disabled);
}

.stat .icon {
  font-size: 0.875rem;
}

.playlist-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-divider-weak);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text-tertiary);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(58, 134, 255, 0.1);
}

.favorite-btn.active {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.favorite-btn.active:hover {
  background: rgba(239, 68, 68, 0.2);
}

.action-btn .icon {
  font-size: 0.9375rem;
}
</style>