<template>
  <div class="create-video-view">
    <div class="container mx-auto px-4 py-8 max-w-2xl">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">🎬 Создать видео</h1>
        <p class="text-gray-600">Поделитесь коротким видео об аниме с сообществом</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <form @submit.prevent="createVideo" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Связанное аниме</label>
            <input
              v-model="animeSearch"
              type="text"
              @input="searchAnime"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Начните вводить название аниме"
            />
            <div v-if="animeResults.length > 0" class="mt-2 max-h-40 overflow-y-auto border border-gray-300 rounded-md">
              <div
                v-for="anime in animeResults"
                :key="anime.id"
                @click="selectAnime(anime)"
                class="p-2 hover:bg-gray-100 cursor-pointer"
              >
                {{ anime.title_ru }}
              </div>
            </div>
            <div v-if="selectedAnime" class="mt-2 p-2 bg-blue-50 rounded-md">
              Выбрано: {{ selectedAnime.title_ru }}
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Тип контента</label>
            <select
              v-model="form.content_type"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="reaction">Реакция на сцену</option>
              <option value="review">Обзор</option>
              <option value="meme">Мем</option>
              <option value="behind_scenes">За кулисами</option>
              <option value="other">Другое</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Название видео</label>
            <input
              v-model="form.title"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Краткое название вашего видео"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="form.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Расскажите о вашем видео"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Видео файл</label>
            <input
              type="file"
              @change="handleFileUpload"
              accept="video/*"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p class="text-sm text-gray-500 mt-1">Максимальный размер: 100MB, форматы: MP4, WebM, MOV</p>
          </div>

          <div class="flex gap-4">
            <button
              type="button"
              @click="$router.back()"
              class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              :disabled="loading || !selectedFile"
              class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {{ loading ? 'Загрузка...' : 'Опубликовать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const loading = ref(false)

const form = ref({
  content_type: 'reaction',
  title: '',
  description: ''
})

const animeSearch = ref('')
const animeResults = ref<any[]>([])
const selectedAnime = ref<any>(null)
const selectedFile = ref<File | null>(null)

const searchAnime = async () => {
  if (animeSearch.value.length < 2) {
    animeResults.value = []
    return
  }

  try {
    const response = await apiClient.get(`/anime/anime/?search=${encodeURIComponent(animeSearch.value)}&page_size=10`)
    animeResults.value = response.data.results || []
  } catch (error) {
    console.error('Error searching anime:', error)
  }
}

const selectAnime = (anime: any) => {
  selectedAnime.value = anime
  animeSearch.value = anime.title_ru
  animeResults.value = []
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    // Check file size (100MB limit)
    if (file.size > 100 * 1024 * 1024) {
      alert('Файл слишком большой. Максимальный размер: 100MB')
      target.value = ''
      return
    }
    selectedFile.value = file
  }
}

const createVideo = async () => {
  if (!selectedAnime.value || !selectedFile.value) return

  loading.value = true

  try {
    const formData = new FormData()
    formData.append('anime', selectedAnime.value.id.toString())
    formData.append('content_type', form.value.content_type)
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('video_file', selectedFile.value)

    await apiClient.post('/reactor/reactor-posts/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    alert('Видео успешно загружено!')
    router.push('/reactor')
  } catch (error: any) {
    alert('Ошибка при загрузке видео: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-video-view {
  min-height: 100vh;
  background: var(--color-background);
}
</style>