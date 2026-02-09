<template>
  <div class="create-playlist-view">
    <div class="container mx-auto px-4 py-8 max-w-2xl">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">📁 Создать плейлист</h1>
        <p class="text-gray-600">Создайте коллекцию аниме для себя или поделитесь с сообществом</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <form @submit.prevent="createPlaylist" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Название плейлиста</label>
            <input
              v-model="form.title"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Топ романтических аниме"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="form.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Расскажите о вашей подборке"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Тип плейлиста</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  v-model="form.is_public"
                  type="radio"
                  :value="true"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Публичный (виден всем)</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="form.is_public"
                  type="radio"
                  :value="false"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Приватный (только для меня)</span>
              </label>
            </div>
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
              :disabled="loading"
              class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {{ loading ? 'Создание...' : 'Создать плейлист' }}
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
  title: '',
  description: '',
  is_public: true
})

const createPlaylist = async () => {
  loading.value = true

  try {
    await apiClient.post('/playlists/playlists/', form.value)
    alert('Плейлист успешно создан!')
    router.push('/playlists')
  } catch (error: any) {
    alert('Ошибка при создании плейлиста: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-playlist-view {
  min-height: 100vh;
  background: var(--color-background);
}
</style>