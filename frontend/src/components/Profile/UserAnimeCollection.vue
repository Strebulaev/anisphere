<template>
  <div class="user-anime-collection">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка коллекции...</p>
    </div>
    <div v-else-if="animeList.length === 0" class="empty">
      <p>Коллекция пуста</p>
    </div>
    <div v-else class="anime-grid">
      <AnimeCard
        v-for="anime in animeList"
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
import apiClient from '@/api/client'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'

interface Props {
  userId: number
}

const props = defineProps<Props>()

const loading = ref(true)
const animeList = ref<any[]>([])

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
  // anime может быть объектом или ID
  const anime = item.anime && typeof item.anime === 'object' ? item.anime : {
    id: item.anime_id,
    title_ru: item.anime_title_ru,
    title_en: item.anime_title_en,
    poster: item.anime_poster,
    poster_url: item.anime_poster,
    poster_image_url: item.anime_poster,
    year: item.anime_year,
    score: item.anime_score,
    status: item.anime_status,
    type: item.anime_kind,
    episodes: item.anime_episodes_count,
    genres: item.anime_genres || []
  }
  
  // Преобразуем жанры в формат, ожидаемый AnimeCard
  let genres = anime.genres || []
  if (Array.isArray(genres) && genres.length > 0) {
    if (typeof genres[0] === 'string') {
      genres = genres.map((genre: string, index: number) => ({
        id: index,
        name: genre,
        slug: genre.toLowerCase().replace(/ /g, '-')
      }))
    }
  }
  
  return {
    ...anime,
    genres,
    // Дополнительные данные для карточки
    watchStatus: mapLibraryStatusToWatchStatus(item.status),
    watchProgress: item.current_episode || item.episodes_watched || 0,
    totalEpisodes: item.anime_episodes_count || anime.episodes || 0,
    // Флаг для показа прогресса
    showProgress: item.status === 'started' && (item.current_episode || item.episodes_watched) > 0
  }
}

const loadAnimeCollection = async () => {
  loading.value = true
  try {
    const response = await apiClient.get(`/users/library/?user_id=${props.userId}`)
    const libraryItems = response.data.results || response.data.library || response.data || []
    animeList.value = libraryItems.map(transformLibraryItemToAnimeCard)
  } catch (error) {
    animeList.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.userId,
  () => {
    loadAnimeCollection()
  },
  { immediate: true }
)
</script>

<style scoped>
.user-anime-collection {
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

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
