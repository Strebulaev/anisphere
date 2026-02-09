<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
      <h2 class="text-xl font-bold mb-4">Создать новую роль</h2>

      <form @submit.prevent="createRole">
        <!-- Basic info -->
        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium mb-1">Название роли *</label>
            <input
              v-model="roleName"
              type="text"
              required
              class="w-full p-2 border rounded-lg"
              placeholder="Например, Старший модератор"
            >
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Уровень роли *</label>
            <select
              v-model="roleLevel"
              class="w-full p-2 border rounded-lg"
            >
              <option :value="0">Участник</option>
              <option :value="1">Модератор</option>
              <option :value="2">Администратор</option>
            </select>
            <div class="text-sm text-gray-500 mt-1">
              Уровень определяет приоритет роли в иерархии
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Цвет роли</label>
            <div class="flex space-x-2">
              <button
                v-for="color in colorOptions"
                :key="color"
                type="button"
                @click="roleColor = color"
                class="w-8 h-8 rounded-full border-2"
                :class="roleColor === color ? 'border-gray-800' : 'border-transparent'"
                :title="getColorName(color)"
                :style="{ backgroundColor: color }"
              ></button>
            </div>
          </div>
        </div>

        <!-- Permissions -->
        <div class="mb-6">
          <h3 class="font-semibold mb-3">Разрешения</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="permission in permissionGroups"
              :key="permission.id"
              class="flex items-center space-x-2"
            >
              <input
                :id="permission.id"
                v-model="selectedPermissions"
                :value="permission.id"
                type="checkbox"
                class="rounded"
              >
              <label :for="permission.id" class="text-sm">
                {{ permission.label }}
              </label>
            </div>
          </div>
        </div>

        <!-- Buttons -->
        <div class="flex justify-end space-x-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Отмена
          </button>
          <button
            type="submit"
            :disabled="!roleName || loading"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            <span v-if="loading">Создание...</span>
            <span v-else>Создать роль</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useGroupChatStore } from '@/stores/groupChat'

interface Props {
  chatId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'created'])

const groupChatStore = useGroupChatStore()
const loading = ref(false)

// Role data
const roleName = ref('')
const roleLevel = ref(1) // Moderator by default
const roleColor = ref('#3B82F6') // Blue by default
const selectedPermissions = ref<string[]>([])

// Options
const colorOptions = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Yellow
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#6366F1', // Indigo
]

const permissionGroups = [
  { id: 'can_delete_messages', label: 'Удаление сообщений' },
  { id: 'can_ban_users', label: 'Блокировка пользователей' },
  { id: 'can_pin_messages', label: 'Закрепление сообщений' },
  { id: 'can_restrict_members', label: 'Ограничение участников' },
  { id: 'can_promote_members', label: 'Повышение участников' },
  { id: 'can_change_chat_info', label: 'Изменение информации чата' },
  { id: 'can_invite_users', label: 'Приглашение пользователей' },
  { id: 'can_manage_video_chats', label: 'Управление видеозвонками' },
]

// Methods
const getColorName = (hex: string) => {
  const colors: Record<string, string> = {
    '#3B82F6': 'Синий',
    '#10B981': 'Зеленый',
    '#F59E0B': 'Желтый',
    '#EF4444': 'Красный',
    '#8B5CF6': 'Фиолетовый',
    '#EC4899': 'Розовый',
    '#06B6D4': 'Голубой',
    '#6366F1': 'Индиго',
  }
  return colors[hex] || hex
}

const createRole = async () => {
  if (!roleName.value) return

  loading.value = true

  try {
    const permissions: Record<string, boolean> = {}
    permissionGroups.forEach(perm => {
      permissions[perm.id] = selectedPermissions.value.includes(perm.id)
    })

    await groupChatStore.createChatRole(props.chatId, {
      name: roleName.value,
      level: roleLevel.value,
      color: roleColor.value,
      ...permissions
    })

    emit('created')
  } catch (error) {
    console.error('Error creating role:', error)
  } finally {
    loading.value = false
  }
}
</script>