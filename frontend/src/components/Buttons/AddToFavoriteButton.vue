<template>
  <button
    :class="['favorite-btn', { 'is-favorite': isFavorite }]"
    @click.stop="toggleFavorite"
    :disabled="loading"
  >
    <span v-if="loading" class="loading-spinner"></span>
    <span v-else :class="['icon', isFavorite ? 'heart-filled' : 'heart-outline']"></span>
    <span class="text">{{ isFavorite ? 'В избранном' : 'В избранное' }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import playlistsApi from '@/api/playlists'

interface Props {
  animeId: number
  animeTitle?: string
  animePoster?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  toggle: [isFavorite: boolean]
  error: [message: string]
}>()

const isFavorite = ref(false)
const loading = ref(false)

const checkStatus = async () => {
  try {
    const response = await playlistsApi.checkAnimeInFavorites(props.animeId)
    isFavorite.value = response.data.is_favorite
  } catch (error) {
    console.error('Ошибка проверки избранного:', error)
  }
}

const toggleFavorite = async () => {
  if (loading.value) return

  loading.value = true
  try {
    if (isFavorite.value) {
      await playlistsApi.removeFromFavorites(props.animeId)
      isFavorite.value = false
      emit('toggle', false)
    } else {
      await playlistsApi.addToFavorites(props.animeId)
      isFavorite.value = true
      emit('toggle', true)
    }
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Ошибка при изменении избранного'
    emit('error', message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkStatus()
})

watch(() => props.animeId, () => {
  checkStatus()
})
</script>

<style scoped>
.favorite-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  background: var(--color-background-surface);
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.favorite-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.favorite-btn.is-favorite {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.favorite-btn.is-favorite:hover {
  background: rgba(239, 68, 68, 0.2);
}

.favorite-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.icon {
  font-size: 1rem;
}

.heart-filled::before {
  content: '♥';
}

.heart-outline::before {
  content: '♡';
}

.is-favorite .heart-filled::before {
  color: #ef4444;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--color-divider);
  border-top-color: #ef4444;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>