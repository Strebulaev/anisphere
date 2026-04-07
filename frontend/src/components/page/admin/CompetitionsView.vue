<template>
  <div class="competitions-view">
    <div class="container mx-auto px-4 py-8">
      <div class="mb-6">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex space-x-8">
            <button
              @click="switchTab('feed')"
              :class="[
                'py-2 px-1 border-b-2 font-medium text-sm',
                activeTab === 'feed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              <SakuraIcon name="play" /> Reactor
            </button>
            <button
              @click="switchTab('competitions')"
              :class="[
                'py-2 px-1 border-b-2 font-medium text-sm',
                activeTab === 'competitions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              <SakuraIcon name="trophy" /> Конкурсы
            </button>
          </nav>
        </div>
      </div>
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-8">
        <p class="text-red-800">{{ error }}</p>
        <button @click="loadContests" class="mt-2 text-red-600 hover:text-red-800 underline">
          Попробовать снова
        </button>
      </div>

      <!-- Active Competitions -->
      <section v-else class="mb-12">
        <h2 class="text-2xl font-semibold mb-6">Активные конкурсы</h2>

        <div v-if="activeContests.length === 0" class="text-center py-12 text-gray-500">
          <p>Нет активных конкурсов на данный момент</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="contest in activeContests"
            :key="contest.id"
            class="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow"
          >
            <div class="flex items-center justify-between mb-4">
              <span
                :class="getContestTypeClass(contest.type)"
                class="px-3 py-1 rounded-full text-sm font-medium"
              >
                {{ getContestTypeLabel(contest.type) }}
              </span>
              <span class="text-sm text-gray-500">
                до {{ formatDate(contest.ended_at || contest.voting_started_at) }}
              </span>
            </div>

            <h3 class="text-xl font-semibold mb-2">{{ contest.title }}</h3>
            <p class="text-gray-600 mb-4">{{ contest.description }}</p>

            <div v-if="contest.theme" class="mb-4">
              <p class="text-sm text-gray-700"><strong>Тема:</strong> {{ contest.theme }}</p>
            </div>

            <div v-if="contest.prize_1st || contest.prize_2nd || contest.prize_3rd" class="mb-4">
              <p class="text-sm text-gray-700 mb-1"><SakuraIcon name="gift" /> Призы:</p>
              <ul class="text-sm text-gray-600 list-disc list-inside">
                <li v-if="contest.prize_1st">1 место: {{ contest.prize_1st }}</li>
                <li v-if="contest.prize_2nd">2 место: {{ contest.prize_2nd }}</li>
                <li v-if="contest.prize_3rd">3 место: {{ contest.prize_3rd }}</li>
              </ul>
            </div>

            <div class="flex items-center justify-between mb-4">
              <span class="text-sm text-gray-500">
                {{ contest.entries_count }} участников
              </span>
              <span class="text-sm text-gray-500">
                {{ contest.votes_count }} голосов
              </span>
            </div>

            <button
              @click="participateInContest(contest)"
              class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Участвовать
            </button>
          </div>
        </div>
      </section>

      <!-- Past Competitions -->
      <section v-if="!loading && !error" class="mb-12">
        <h2 class="text-2xl font-semibold mb-6">Завершённые конкурсы</h2>

        <div v-if="finishedContests.length === 0" class="text-center py-12 text-gray-500">
          <p>Нет завершённых конкурсов</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="contest in finishedContests"
            :key="contest.id"
            class="bg-gray-50 rounded-lg shadow-md p-6 border border-gray-200"
          >
            <div class="flex items-center justify-between mb-4">
              <span class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">
                Завершён
              </span>
              <span class="text-sm text-gray-500">
                {{ formatDate(contest.ended_at) }}
              </span>
            </div>

            <h3 class="text-xl font-semibold mb-2">{{ contest.title }}</h3>
            <p class="text-gray-600 mb-4">{{ contest.description }}</p>

            <div v-if="contest.theme" class="mb-4">
              <p class="text-sm text-gray-700"><strong>Тема:</strong> {{ contest.theme }}</p>
            </div>

            <button
              @click="viewContestResults(contest)"
              class="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
            >
              Посмотреть результаты
            </button>
          </div>
        </div>
      </section>

      <!-- My Participations -->
      <section v-if="!loading && !error && myEntries.length > 0">
        <h2 class="text-2xl font-semibold mb-6">Мои участия</h2>
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="space-y-4">
            <div
              v-for="entry in myEntries"
              :key="entry.id"
              class="flex items-center justify-between p-4 border border-gray-200 rounded-md"
            >
              <div>
                <h4 class="font-semibold">{{ entry.contest_title }}</h4>
                <p class="text-sm text-gray-600">
                  Статус: {{ getEntryStatus(entry) }}
                </p>
                <p v-if="entry.is_winner" class="text-sm text-green-600 font-medium">
                  <SakuraIcon name="trophy" /> {{ entry.winner_place }} место!
                </p>
              </div>
              <span :class="getEntryStatusClass(entry)" class="px-3 py-1 rounded-full text-sm">
                {{ getEntryStatusText(entry) }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Participation Modal -->
    <div
      v-if="showParticipationModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="closeParticipationModal"
    >
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4" @click.stop>
        <h3 class="text-xl font-semibold mb-4">Участие в конкурсе</h3>
        <p class="text-gray-600 mb-4">{{ selectedContest?.title }}</p>

        <form @submit.prevent="submitEntry">
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Название работы</label>
            <input
              v-model="entryForm.title"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Название вашей работы"
            />
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="entryForm.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Опишите вашу работу"
            ></textarea>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              {{ selectedContest?.format === 'image' ? 'Изображение' : selectedContest?.format === 'video' ? 'Видео' : 'Файл' }}
            </label>
            <input
              type="file"
              @change="handleFileUpload"
              :accept="getAcceptTypes(selectedContest?.format)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div class="flex gap-3">
            <button
              type="button"
              @click="closeParticipationModal"
              class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {{ submitting ? 'Отправка...' : 'Отправить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'
import { useRouter } from 'vue-router'

// Types
interface Contest {
  id: number
  title: string
  description: string
  type: 'weekly' | 'monthly' | 'seasonal' | 'special'
  format: 'image' | 'video' | 'text' | 'mixed'
  status: string
  theme?: string
  prize_1st?: string
  prize_2nd?: string
  prize_3rd?: string
  ended_at?: string
  voting_started_at?: string
  entries_count: number
  votes_count: number
}

interface ContestEntry {
  id: number
  contest_title: string
  title?: string
  description?: string
  is_winner: boolean
  winner_place?: number
}


const router = useRouter()
const videos = ref<any[]>([])

// Video interface
interface ReactorVideo {
  id: number
  title?: string
  description?: string
  video_file: string
  user_username: string
  likes_count: number
  comments_count: number
  duration?: number
  anime?: {
    id: number
    title_ru: string
    poster_url: string
  }
}


// Reactive data
const loading = ref(false)
const error = ref('')
const activeContests = ref<Contest[]>([])
const finishedContests = ref<Contest[]>([])
const myEntries = ref<ContestEntry[]>([])
const activeTab = ref('feed')

// Participation modal
const showParticipationModal = ref(false)
const selectedContest = ref<Contest | null>(null)
const submitting = ref(false)

const entryForm = ref({
  title: '',
  description: ''
})

const selectedFile = ref<File | null>(null)

// Methods
const loadContests = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get('/social/contests/')
    const allContests = response.data

    // Separate active and finished contests
    activeContests.value = allContests.filter((contest: Contest) =>
      contest.status === 'active' || contest.status === 'voting'
    )

    finishedContests.value = allContests.filter((contest: Contest) =>
      contest.status === 'finished' || contest.status === 'cancelled'
    )

    // Load user's entries
    await loadMyEntries()
  } catch (err: any) {
    error.value = 'Не удалось загрузить конкурсы: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}

const loadMyEntries = async () => {
  try {
    const response = await apiClient.get('/social/contest-entries/')
    myEntries.value = response.data
  } catch (err) {
    // Не показываем ошибку, если не можем загрузить личные участия
    console.error('Error loading my entries:', err)
  }
}

const loadVideos = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get('/reactor/posts/')
    videos.value = response.data.results || response.data
  } catch (err: any) {
    error.value = 'Не удалось загрузить видео: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}

const switchTab = (tab: string) => {
  activeTab.value = tab
  if (tab === 'feed') {
    loadVideos()
  } else if (tab === 'competitions') {
    router.push('/reactor/competitions')
  }
}

const getContestTypeClass = (type: string) => {
  const classes = {
    weekly: 'bg-blue-100 text-blue-800',
    monthly: 'bg-green-100 text-green-800',
    seasonal: 'bg-purple-100 text-purple-800',
    special: 'bg-orange-100 text-orange-800'
  }
  return classes[type as keyof typeof classes] || 'bg-gray-100 text-gray-800'
}

const getContestTypeLabel = (type: string) => {
  const labels = {
    weekly: 'Еженедельный',
    monthly: 'Ежемесячный',
    seasonal: 'Сезонный',
    special: 'Специальный'
  }
  return labels[type as keyof typeof labels] || type
}

const formatDate = (dateString?: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU')
}

const participateInContest = (contest: Contest) => {
  selectedContest.value = contest
  showParticipationModal.value = true

  // Reset form
  entryForm.value = {
    title: '',
    description: ''
  }
  selectedFile.value = null
}

const closeParticipationModal = () => {
  showParticipationModal.value = false
  selectedContest.value = null
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const getAcceptTypes = (format?: string) => {
  switch (format) {
    case 'image':
      return 'image/*'
    case 'video':
      return 'video/*'
    default:
      return '*/*'
  }
}

const submitEntry = async () => {
  if (!selectedContest.value) return

  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('contest', selectedContest.value.id.toString())
    formData.append('title', entryForm.value.title)
    formData.append('description', entryForm.value.description)

    if (selectedFile.value) {
      if (selectedContest.value.format === 'image') {
        formData.append('image_file', selectedFile.value)
      } else if (selectedContest.value.format === 'video') {
        formData.append('video_file', selectedFile.value)
      }
    }

    await apiClient.post('/social/contest-entries/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Reload data
    await loadContests()
    closeParticipationModal()

    // Show success message (you might want to add a toast system)
    alert('Ваша работа успешно отправлена!')

  } catch (err: any) {
    alert('Ошибка при отправке работы: ' + (err.response?.data?.detail || err.message))
  } finally {
    submitting.value = false
  }
}

const viewContestResults = (contest: Contest) => {
  if (contest.id) {
    router.push(`/reactor/competitions/${contest.id}/results`)
  } else {
    alert('Ошибка: отсутствует ID конкурса')
  }
}

const getEntryStatus = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return `Завершено • ${entry.winner_place} место`
  }
  return 'Ожидание результатов'
}

const getEntryStatusText = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return '🏆 Победа'
  }
  return 'Участвую'
}

const getEntryStatusClass = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return 'bg-green-100 text-green-800'
  }
  return 'bg-blue-100 text-blue-800'
}

// Lifecycle
onMounted(() => {
  loadContests()
})
</script>

<style scoped>
/* Additional styles if needed */
</style>