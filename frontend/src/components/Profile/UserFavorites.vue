<template>
  <div class="user-favorites">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка избранного...</p>
    </div>
    <div v-else-if="favorites.length === 0" class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
      <p>Избранное пусто</p>
    </div>
    <div v-else class="favorites-grid">
      <AnimeCard
        v-for="anime in favorites"
        :key="anime.id"
        :anime="anime"
        :watch-status="anime.watchStatus"
        :watch-progress="anime.watchProgress"
        :total-episodes="anime.totalEpisodes"
        :show-progress="anime.showProgress"
        :show-actions="true"
        :show-genres="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import apiClient from '@/api/client'

const props = defineProps<{
  userId: number
}>()

const loading = ref(true)
const favorites = ref<any[]>([])

// Маппинг статусов библиотеки в статусы для карточки
const mapLibraryStatusToWatchStatus = (status: string): 'watching' | 'completed' | 'planned' | 'dropped' | 'onhold' => {
  switch (status) {
    case 'started': return 'watching'
    case 'completed': return 'completed'
    case 'planned': return 'planned'
    case 'dropped': return 'dropped'
    case 'on_hold': return 'onhold'
    default: return 'planned'
  }
}

// Преобразование элемента библиотеки в данные для карточки аниме
const transformLibraryItemToAnimeCard = (item: any) => {
  return {
    id: item.anime_id || item.anime,
    title_ru: item.anime_title_ru || '',
    title_en: item.anime_title_en || '',
    poster_url: item.anime_poster || null,
    poster_image_url: item.anime_poster || null,
    episodes: item.anime_episodes_count || 0,
    type: item.anime_kind || '',
    year: item.anime_year || null,
    // Данные о прогрессе
    watchStatus: mapLibraryStatusToWatchStatus(item.status),
    watchProgress: item.current_episode || 0,
    totalEpisodes: item.anime_episodes_count || 0,
    showProgress: item.status === 'started' && (item.current_episode || 0) > 0
  }
}

const loadFavorites = async () => {
  loading.value = true
  try {
    // Используем библиотеку с фильтром is_favorite=true
    const response = await apiClient.get(`/users/library/?user_id=${props.userId}&is_favorite=true`)
    const items = response.data.results || response.data || []
    favorites.value = items.map(transformLibraryItemToAnimeCard)
  } catch (error) {
    console.error('Error loading favorites:', error)
    favorites.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.userId,
  () => {
    loadFavorites()
  },
  { immediate: true }
)
</script>

<style scoped>
.user-favorites {
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

.empty svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
