<template>
  <div class="favorites-page">
    <div class="page-header">
      <h1>Избранное аниме</h1>
      <p v-if="favorites.length > 0" class="count">
        {{ favorites.length }} аниме
      </p>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <span class="icon">💔</span>
      <h2>Пока ничего нет</h2>
      <p>Добавьте аниме в избранное, нажав на ♥</p>
      <router-link to="/" class="browse-btn">
        Обзор аниме
      </router-link>
    </div>

    <div v-else class="anime-grid">
      <AnimeCard
        v-for="item in favorites"
        :key="item.id"
        :anime="item.anime_data"
        @click="goToAnime(item.anime_data.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import playlistsApi, { type FavoriteAnime } from '@/api/playlists'
import AnimeCard from '@/components/AnimeCard.vue'

const router = useRouter()
const favorites = ref<FavoriteAnime[]>([])
const loading = ref(true)

const loadFavorites = async () => {
  try {
    const response = await playlistsApi.getFavoriteAnime()
    favorites.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки избранного:', error)
  } finally {
    loading.value = false
  }
}

const goToAnime = (id: number) => {
  router.push(`/anime/${id}`)
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
}

.count {
  color: var(--color-text-tertiary);
  font-size: 0.9375rem;
}

.loading {
  text-align: center;
  padding: 4rem 1rem;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
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

.browse-btn {
  display: inline-flex;
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  text-decoration: none;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: background 0.2s;
}

.browse-btn:hover {
  background: var(--color-accent-hover);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}
</style>