<template>
  <div
    class="chat-list-item"
    :class="{ 'active': isActive }"
    @click="$emit('click')"
    @contextmenu="$emit('contextmenu', $event)"
  >
    <div class="flex items-center p-3 cursor-pointer chat-item-content">
      <!-- Avatar with status indicator -->
      <div class="relative mr-3">
        <img
          :src="chat.avatar || '/default-avatar.png'"
          :alt="chat.name"
          class="w-12 h-12 rounded-full object-cover"
        >
        <!-- Status indicator -->
        <div
          v-if="chat.type === 'private'"
          class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#1a1a1a]"
          :class="statusColor"
        ></div>
        <!-- Online count for groups -->
        <div
          v-else-if="chat.onlineCount && chat.onlineCount > 0"
          class="absolute -bottom-0.5 -right-0.5 bg-green-500 text-white text-xs rounded-full px-1 min-w-[18px] h-4 flex items-center justify-center border border-[#1a1a1a]"
        >
          {{ chat.onlineCount }}
        </div>
      </div>

      <!-- Chat info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-gray-100 truncate">{{ chat.name }}</h3>
          <div class="flex items-center space-x-1 ml-2">
            <!-- Pinned indicator -->
            <StarIcon v-if="chat.isPinned" class="w-4 h-4 text-yellow-500" />
            <!-- Time -->
            <span class="text-xs text-gray-400 whitespace-nowrap">
              {{ formatTime(chat.lastMessage?.timestamp) }}
            </span>
          </div>
        </div>

        <div class="flex items-center justify-between mt-1">
          <!-- Last message -->
          <p class="text-sm text-gray-400 truncate max-w-[150px]">
            {{ formatLastMessage(chat.lastMessage) }}
          </p>

          <!-- Unread count -->
          <div
            v-if="chat.unreadCount > 0"
            class="ml-2 bg-blue-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[18px] text-center"
          >
            {{ chat.unreadCount > 99 ? '99+' : chat.unreadCount }}
          </div>
        </div>

        <!-- Group info -->
        <div v-if="chat.type === 'group' && chat.membersCount" class="text-xs text-gray-500 mt-1">
          {{ chat.membersCount }} участников
        </div>
      </div>
    </div>

    <!-- Typing indicator -->
    <div v-if="isTyping" class="px-3 pb-2">
      <div class="flex items-center text-sm text-blue-400">
        <div class="flex space-x-1 mr-2">
          <div class="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></div>
          <div class="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
          <div class="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
        </div>
        Печатает...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { StarIcon } from '@heroicons/vue/24/outline'

interface Chat {
  id: number
  type: 'private' | 'group'
  name: string
  avatar?: string | null
  lastMessage?: {
    text: string
    timestamp: string
    sender: string
  }
  unreadCount: number
  isPinned: boolean
  isArchived: boolean
  status?: string
  membersCount?: number
  onlineCount?: number
}

interface Props {
  chat: Chat
  isActive?: boolean
  isTyping?: boolean
}

const props = defineProps<Props>()

defineEmits<{
  click: []
  contextmenu: [event: MouseEvent]
}>()

// Computed
const statusColor = computed(() => {
  switch (props.chat.status) {
    case 'online':
      return 'bg-green-500'
    case 'away':
      return 'bg-yellow-500'
    case 'busy':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
})

// Methods
const formatTime = (timestamp?: string) => {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // Less than 1 minute
  if (diff < 60000) {
    return 'сейчас'
  }

  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} мин`
  }

  // Less than 24 hours
  if (diff < 86400000) {
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  }

  // More than 24 hours
  return date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })
}

const formatLastMessage = (lastMessage?: Chat['lastMessage']) => {
  if (!lastMessage) return 'Нет сообщений'

  // Handle typing indicator (would come from props)
  if (props.isTyping) return 'Печатает...'

  // Format message text
  let text = lastMessage.text || ''
  
  // Если текст пустой, показываем "Нет сообщений"
  if (!text.trim()) return 'Нет сообщений'

  // Add sender prefix for groups
  if (props.chat.type === 'group' && lastMessage.sender) {
    text = `${lastMessage.sender}: ${text}`
  }

  // Truncate long messages - ВАЖНО: обрезаем до 15 символов, так как для групп добавляется имя отправителя
  const MAX_LENGTH = props.chat.type === 'group' ? 15 : 10;
  if (text.length > MAX_LENGTH) {
    text = text.substring(0, MAX_LENGTH) + '...'
  }

  return text
}

</script>

<style scoped>
.chat-list-item {
  background: transparent;
}

.chat-list-item:hover .chat-item-content {
  background: #222222;
}

.chat-list-item.active {
  background: #222222;
  border-right: 2px solid #3b82f6;
}

.chat-list-item.active .chat-item-content {
  background: #2a2a2a;
}

.chat-list-item.active h3 {
  color: #3b82f6;
}

/* Убедитесь, что класс truncate работает */
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}
</style>