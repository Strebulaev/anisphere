<template>
  <div class="competition-results">
    <div class="container mx-auto px-4 py-8">
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600"></div>
        <p class="mt-4 text-gray-600">Загрузка результатов...</p>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600 text-lg">{{ error }}</p>
        <button @click="loadResults" class="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Попробовать снова
        </button>
      </div>

      <div v-else-if="contest" class="max-w-4xl mx-auto">
        <div class="mb-6">
          <router-link to="/reactor/competitions" class="text-blue-600 hover:text-blue-800 flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Назад к конкурсам
          </router-link>
        </div>

        <div class="bg-white rounded-xl shadow-lg overflow-hidden">
          <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
            <h1 class="text-3xl font-bold mb-2">{{ contest.title }}</h1>
            <p v-if="contest.description" class="text-blue-100">{{ contest.description }}</p>
            <div class="mt-4 flex gap-4 text-sm">
              <span v-if="contest.start_date">
                <strong>Начало:</strong> {{ formatDate(contest.start_date) }}
              </span>
              <span v-if="contest.end_date">
                <strong>Окончание:</strong> {{ formatDate(contest.end_date) }}
              </span>
              <span v-if="contest.status">
                <strong>Статус:</strong> {{ getStatusText(contest.status) }}
              </span>
            </div>
          </div>

          <div class="p-6">
            <h2 class="text-2xl font-bold mb-6">Результаты конкурса</h2>

            <div v-if="entries.length === 0" class="text-center py-12 text-gray-500">
              <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <p>Результаты ещё не опубликованы</p>
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="(entry, index) in sortedEntries"
                :key="entry.id"
                class="flex items-start gap-4 p-4 rounded-lg border"
                :class="getEntryClass(entry, index)"
              >
                <div class="flex-shrink-0">
                  <div
                    class="w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold"
                    :class="getPlaceClass(entry)"
                  >
                    {{ getPlaceIcon(entry) }}
                  </div>
                </div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <h3 class="font-semibold text-lg">
                        <router-link :to="`/profile/${entry.author.id}`" class="hover:text-blue-600">
                          {{ entry.author.username }}
                        </router-link>
                      </h3>
                      <p v-if="entry.title" class="text-gray-600">{{ entry.title }}</p>
                    </div>
                    <span class="text-sm text-gray-500 flex-shrink-0">
                      {{ formatDate(entry.created_at) }}
                    </span>
                  </div>

                  <div v-if="entry.description" class="mt-2 text-gray-700">
                    {{ entry.description }}
                  </div>

                  <div v-if="entry.image_url" class="mt-3">
                    <img
                      :src="entry.image_url"
                      :alt="entry.title || 'Работа участника'"
                      class="max-w-full h-auto rounded-lg max-h-96 object-cover"
                    />
                  </div>

                  <div v-if="entry.votes_count !== undefined" class="mt-3 flex items-center gap-4 text-sm text-gray-500">
                    <span class="flex items-center gap-1">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                      </svg>
                      {{ entry.votes_count }} голосов
                    </span>
                    <span v-if="entry.comments_count !== undefined" class="flex items-center gap-1">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                      </svg>
                      {{ entry.comments_count }} комментариев
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/api/client'

interface User {
  id: number
  username: string
  avatar_url?: string
}

interface ContestEntry {
  id: number
  author: User
  title?: string
  description?: string
  image_url?: string
  created_at: string
  is_winner: boolean
  winner_place?: number
  votes_count?: number
  comments_count?: number
}

interface Contest {
  id: number
  title: string
  description?: string
  start_date?: string
  end_date?: string
  status: string
}

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const contest = ref<Contest | null>(null)
const entries = ref<ContestEntry[]>([])

const sortedEntries = computed(() => {
  return [...entries.value].sort((a, b) => {
    if (a.is_winner && b.is_winner) {
      const placeA = a.winner_place || 999
      const placeB = b.winner_place || 999
      return placeA - placeB
    }
    if (a.is_winner) return -1
    if (b.is_winner) return 1
    return 0
  })
})

const loadResults = async () => {
  const contestId = route.params.id
  loading.value = true
  error.value = ''

  try {
    const [contestResponse, entriesResponse] = await Promise.all([
      apiClient.get(`/social/contests/${contestId}/`),
      apiClient.get(`/social/contests/${contestId}/entries/`)
    ])

    contest.value = contestResponse.data
    entries.value = entriesResponse.data.results || entriesResponse.data
  } catch (err: any) {
    console.error('Error loading contest results:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить результаты'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'upcoming': 'Скоро начнётся',
    'active': 'Идёт сейчас',
    'voting': 'Голосование',
    'finished': 'Завершён',
    'cancelled': 'Отменён'
  }
  return statusMap[status] || status
}

const getEntryClass = (entry: ContestEntry, index: number) => {
  if (entry.is_winner && entry.winner_place === 1) {
    return 'bg-yellow-50 border-yellow-300'
  }
  if (entry.is_winner && entry.winner_place === 2) {
    return 'bg-gray-50 border-gray-300'
  }
  if (entry.is_winner && entry.winner_place === 3) {
    return 'bg-orange-50 border-orange-300'
  }
  return 'bg-white border-gray-200'
}

const getPlaceClass = (entry: ContestEntry) => {
  if (entry.is_winner && entry.winner_place === 1) {
    return 'bg-yellow-400 text-yellow-900'
  }
  if (entry.is_winner && entry.winner_place === 2) {
    return 'bg-gray-400 text-gray-900'
  }
  if (entry.is_winner && entry.winner_place === 3) {
    return 'bg-orange-400 text-orange-900'
  }
  return 'bg-gray-200 text-gray-600'
}

const getPlaceIcon = (entry: ContestEntry) => {
  if (entry.is_winner && entry.winner_place === 1) return '🥇'
  if (entry.is_winner && entry.winner_place === 2) return '🥈'
  if (entry.is_winner && entry.winner_place === 3) return '🥉'
  if (entry.is_winner) return entry.winner_place || ''
  return ''
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.competition-results {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.container {
  max-width: 1200px;
}

.bg-gradient-to-r {
  background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-blue-600 {
  --tw-gradient-from: #2563eb;
}

.to-purple-600 {
  --tw-gradient-to: #9333ea;
}

.rounded-xl {
  border-radius: 0.75rem;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.rounded-full {
  border-radius: 9999px;
}

@media (max-width: 768px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .text-3xl {
    font-size: 1.5rem;
  }

  .text-2xl {
    font-size: 1.25rem;
  }
}
</style>
