<template>
  <div class="create-competition-view">
    <div class="container mx-auto px-4 py-8 max-w-2xl">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2"><SakuraIcon name="trophy" /> Создать конкурс</h1>
        <p class="text-gray-600">Организуйте конкурс для аниме-сообщества</p>
      </div>

      <div class="bg-white rounded-lg shadow-md p-6">
        <form @submit.prevent="createCompetition" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Название конкурса</label>
            <input
              v-model="form.title"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Лучший фанарт к Attack on Titan"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Описание</label>
            <textarea
              v-model="form.description"
              rows="3"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Опишите правила и условия конкурса"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Тип конкурса</label>
              <select
                v-model="form.type"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="weekly">Еженедельный</option>
                <option value="monthly">Ежемесячный</option>
                <option value="seasonal">Сезонный</option>
                <option value="special">Специальный</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Формат работ</label>
              <select
                v-model="form.format"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="image">Изображения</option>
                <option value="video">Видео</option>
                <option value="text">Текст</option>
                <option value="mixed">Смешанный</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Тема конкурса</label>
            <input
              v-model="form.theme"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Например: Персонажи в альтернативной вселенной"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Правила</label>
            <textarea
              v-model="form.rules"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Подробные правила участия"
            ></textarea>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">1 место</label>
              <input
                v-model="form.prize_1st"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Приз за 1 место"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">2 место</label>
              <input
                v-model="form.prize_2nd"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Приз за 2 место"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">3 место</label>
              <input
                v-model="form.prize_3rd"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Приз за 3 место"
              />
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
              {{ loading ? 'Создание...' : 'Создать конкурс' }}
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
  type: 'weekly',
  format: 'image',
  theme: '',
  rules: '',
  prize_1st: '',
  prize_2nd: '',
  prize_3rd: ''
})

const createCompetition = async () => {
  loading.value = true

  try {
    await apiClient.post('/social/contests/', form.value)
    alert('Конкурс успешно создан!')
    router.push('/competitions')
  } catch (error: any) {
    alert('Ошибка при создании конкурса: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-competition-view {
  min-height: 100vh;
  background: var(--color-background);
}
</style>