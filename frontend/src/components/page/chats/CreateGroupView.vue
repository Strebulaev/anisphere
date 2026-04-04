<template>
  <div class="create-group-view">
    <div class="container mx-auto px-4 py-8 max-w-2xl">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">👥 Создать группу</h1>
        <p class="text-gray-600">Создайте сообщество по интересам для обсуждения аниме</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <form @submit.prevent="createGroup" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Название группы</label>
            <input
              v-model="form.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Фанаты Attack on Titan"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="form.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Расскажите о группе и её правилах"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Связанное аниме</label>
            <input
              v-model="animeSearch"
              type="text"
              @input="searchAnime"
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
            <label class="block text-sm font-medium text-gray-700 mb-2">Тип группы</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  v-model="form.is_private"
                  type="radio"
                  :value="false"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Публичная (любой может вступить)</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="form.is_private"
                  type="radio"
                  :value="true"
                  class="text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2">Приватная (только по приглашению)</span>
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
              {{ loading ? 'Создание...' : 'Создать группу' }}
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
  name: '',
  description: '',
  is_private: false,
  anime: undefined as number | undefined
})

const animeSearch = ref('')
const animeResults = ref<any[]>([])
const selectedAnime = ref<any>(null)

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
  form.value.anime = anime.id
  animeSearch.value = anime.title_ru
  animeResults.value = []
}

const createGroup = async () => {
  loading.value = true

  try {
    const groupData = {
      ...form.value,
      anime: selectedAnime.value?.id
    }
    await apiClient.post('/social/groups/', groupData)
    alert('Группа успешно создана!')
    router.push('/groups')
  } catch (error: any) {
    alert('Ошибка при создании группы: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-group-view {
  min-height: 100vh;
  background: var(--surface-1);
  position: relative;
}

/* Фоновый узор */
.create-group-view::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.03) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.03) 0%, transparent 40%);
  pointer-events: none;
}

/* Мобильная адаптация - отступ сверху под мобильную навигацию */
@media (max-width: 767px) {
  .create-group-view {
    padding-top: 54px;
    box-sizing: border-box;
  }
}
</style>