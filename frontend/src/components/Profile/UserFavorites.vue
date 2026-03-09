<template>
  <div class="user-favorites">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка избранного...</p>
    </div>
    <div v-else-if="favorites.length === 0" class="empty">
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

const loading = ref(true)
const favorites = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch('/api/users/favorites/')
    const data = await response.json()
    favorites.value = data.results || data
  } catch (error) {
    console.error('Ошибка загрузки избранного:', error)
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

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
</style>
