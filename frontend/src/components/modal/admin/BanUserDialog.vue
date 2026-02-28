<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md">
      <h2 class="text-xl font-bold mb-4">Заблокировать пользователя</h2>

      <div class="mb-4">
        <p class="text-gray-600">
          Заблокировать пользователя <strong>{{ member?.user.username }}</strong> в этом чате?
        </p>
      </div>

      <form @submit.prevent="banUser">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Причина блокировки *</label>
            <textarea
              v-model="reason"
              rows="3"
              required
              class="w-full p-2 border rounded-lg"
              placeholder="Укажите причину блокировки..."
              :disabled="loading"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Срок блокировки</label>
            <select
              v-model="untilDate"
              class="w-full p-2 border rounded-lg"
              :disabled="loading"
            >
              <option :value="null">Навсегда</option>
              <option value="1">1 час</option>
              <option value="24">24 часа</option>
              <option value="168">1 неделя</option>
              <option value="720">1 месяц</option>
            </select>
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
            :disabled="!reason || loading"
            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
          >
            <span v-if="loading">Блокировка...</span>
            <span v-else>Заблокировать</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGroupChatStore } from '@/stores/groupChat'

interface Props {
  member: any
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'banned'])

const groupChatStore = useGroupChatStore()
const loading = ref(false)
const reason = ref('')
const untilDate = ref<string | null>(null)

const banUser = async () => {
  if (!reason.value || !props.member) return

  loading.value = true

  try {
    let banUntilDate = null
    if (untilDate.value) {
      const hours = parseInt(untilDate.value)
      const banDate = new Date()
      banDate.setHours(banDate.getHours() + hours)
      banUntilDate = banDate.toISOString()
    }

    await groupChatStore.banUser(
      groupChatStore.currentChat?.id || 0,
      props.member.user.id,
      reason.value,
      banUntilDate || undefined
    )

    emit('banned')
  } catch (error) {
    console.error('Error banning user:', error)
    alert('Ошибка при блокировке пользователя')
  } finally {
    loading.value = false
  }
}
</script>