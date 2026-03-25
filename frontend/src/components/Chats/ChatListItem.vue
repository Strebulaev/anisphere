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
        <OptimizedImage
          :src="displayAvatar"
          :alt="chat.name"
          class="w-12 h-12 rounded-full object-cover"
        >
        </OptimizedImage>
        <!-- Status indicator -->
        <div
          v-if="chat.type === 'private'"
          class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#1a1a1a]"
          :class="statusColor"
        ></div>
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

          <div class="flex items-center gap-1 ml-2 flex-shrink-0">
            <!-- Заглушен -->
            <span v-if="chat.isMuted" title="Уведомления заглушены" class="text-yellow-500 text-xs">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/>
                <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </span>
            <!-- Архив
            <span v-if="chat.isArchived" title="Из архива" class="text-indigo-400 text-xs">📦</span>
            -->
            <!-- Непрочитанные -->
            <div
              v-if="chat.unreadCount > 0"
              :class="[
                'text-white text-xs rounded-full px-2 py-0.5 min-w-[18px] text-center',
                chat.isMuted ? 'bg-gray-600' : 'bg-blue-500'
              ]"
            >
              {{ chat.unreadCount > 99 ? '99+' : chat.unreadCount }}
            </div>
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
import { getMediaUrl } from '@/api/client'

interface Chat {
  id: number
  type: 'private' | 'group'
  name: string
  avatar?: string | null
  avatar_url?: string | null
  // Поля для группы обсуждения аниме
  anime_id?: number | null
  anime_title?: string | null
  anime_poster?: string | null
  anime_slug?: string | null
  // Поля для franchise discussion
  franchise_id?: number | null
  franchise_slug?: string | null
  discussion_type?: string | null
  lastMessage?: {
    text: string
    timestamp: string
    sender: string
  }
  unreadCount: number
  isPinned: boolean
  isArchived: boolean
  isMuted: boolean
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

// Computed - используем постер аниме для групп обсуждений
const displayAvatar = computed(() => {
  // Если это группа обсуждения (есть anime_id или anime_title) - пробуем использовать постер аниме
  if (props.chat.anime_id || props.chat.anime_title) {
    // Пробуем anime_poster (проверяем на null, undefined и пустую строку)
    const animePoster = props.chat.anime_poster
    if (animePoster && typeof animePoster === 'string' && animePoster.trim() !== '') {
      return getMediaUrl(animePoster)
    }
    // Также пробуем avatar_url который мог быть установлен как anime_poster
    const avatarUrl = props.chat.avatar_url
    if (avatarUrl && typeof avatarUrl === 'string' && avatarUrl.trim() !== '') {
      return getMediaUrl(avatarUrl)
    }
  }
  
  // Иначе используем обычную аватарку
  const avatar = props.chat.avatar || props.chat.avatar_url
  if (avatar && typeof avatar === 'string' && avatar.trim() !== '') {
    return getMediaUrl(avatar)
  }
  return '/default-avatar.png'
})

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