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
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'

interface Props {
  userId: number
}

const props = defineProps<Props>()

const loading = ref(true)
const animeList = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/users/${props.userId}/anime-collection/`)
    const data = await response.json()
    animeList.value = data.results || data
  } catch (error) {
    console.error('Ошибка загрузки коллекции:', error)
  } finally {
    loading.value = false
  }
})
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
