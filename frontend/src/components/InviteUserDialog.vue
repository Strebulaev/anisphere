<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4">Пригласить пользователя</h2>

      <form @submit.prevent="inviteUser">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Имя пользователя *</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full p-2 border rounded-lg"
              placeholder="Введите имя пользователя"
              :disabled="loading"
            >
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Приветственное сообщение</label>
            <textarea
              v-model="message"
              rows="3"
              class="w-full p-2 border rounded-lg"
              placeholder="Необязательное приветственное сообщение..."
              :disabled="loading"
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 border rounded-lg hover:bg-gray-50"
            :disabled="loading"
          >
            Отмена
          </button>
          <button
            type="submit"
            :disabled="!username || loading"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            <span v-if="loading">Отправка...</span>
            <span v-else>Пригласить</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useGroupChatStore } from '@/stores/groupChat'
import apiClient from '@/api/client'

interface Props {
  chatId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'invited'])

const groupChatStore = useGroupChatStore()
const loading = ref(false)
const username = ref('')
const message = ref('')

const inviteUser = async () => {
  if (!username.value) return

  loading.value = true

  try {
    const userId = await searchUserByUsername(username.value)

    if (!userId) {
      alert('Пользователь не найден')
      return
    }

    await groupChatStore.inviteUser(props.chatId, userId, message.value)
    emit('invited')
  } catch (error) {
    console.error('Error inviting user:', error)
    alert('Ошибка при отправке приглашения')
  } finally {
    loading.value = false
  }
}

const searchUserByUsername = async (username: string): Promise<number | null> => {
  try {
    const response = await apiClient.get('/users/online/', {
      params: { search: username }
    })
    const users = response.data.results || response.data
    if (users.length > 0) {
      return users[0].id
    }
    return null
  } catch (error) {
    console.error('Error searching user:', error)
    return null
  }
}
</script>