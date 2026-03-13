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
        :show-actions="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import api from '@/api'

const props = defineProps<{
  userId: number
}>()

const loading = ref(true)
const favorites = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get(`/users/${props.userId}/favorites/`)
    favorites.value = response.data.results || response.data || []
  } catch (error) {
    console.error('Ошибка загрузки избранного:', error)
    // Пробуем альтернативный эндпоинт
    try {
      const altResponse = await api.get(`/anime/favorites/?user=${props.userId}`)
      favorites.value = altResponse.data.results || altResponse.data || []
    } catch (altError) {
      console.error('Альтернативный эндпоинт тоже не работает:', altError)
    }
  } finally {
    loading.value = false
  }
})
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
