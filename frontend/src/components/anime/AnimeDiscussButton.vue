<template>
  <button
    @click="handleDiscuss"
    :class="['anime-discuss-button', { 'loading': isLoading }]"
    :disabled="isLoading"
    type="button"
  >
    <svg v-if="isLoading" class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
    </svg>
    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
    <span>{{ isLoading ? 'Загрузка...' : 'Обсудить' }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import type { Anime } from '@/types'

interface Props {
  anime: Anime
}

const props = defineProps<Props>()

const router = useRouter()
const isLoading = ref(false)

const handleDiscuss = async () => {
  if (isLoading.value) return

  isLoading.value = true

  try {
    // Сначала пробуем получить существующую группу
    let discussionGroup
    try {
      discussionGroup = await animeDiscussionsApi.getDiscussionGroup(props.anime.id)
    } catch (error: any) {
      // Группы нет, создаём новую
      if (error.response?.status === 404) {
        discussionGroup = await animeDiscussionsApi.createDiscussionGroup(props.anime.id)
      } else {
        throw error
      }
    }

    // Если пользователь ещё не вступил, вступаем
    if (!discussionGroup.user_joined) {
      discussionGroup = await animeDiscussionsApi.joinDiscussionGroup(props.anime.id)
    }

    // Перенаправляем в чат
    router.push(`/chats/${discussionGroup.id}`)
  } catch (error: any) {
    console.error('Error handling discuss:', error)
    alert('Не удалось открыть обсуждение: ' + (error.response?.data?.detail || error.message))
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.anime-discuss-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.anime-discuss-button:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.anime-discuss-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
