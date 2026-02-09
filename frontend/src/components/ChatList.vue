<template>
  <div class="chat-list">
    <!-- Header -->
    <div class="chat-list-header">
      <div class="flex items-center justify-between p-4 border-b">
        <h1 class="text-xl font-semibold">Чаты</h1>
        <div class="flex items-center space-x-2">
          <button
            @click="showSearch = !showSearch"
            class="p-2 rounded-full hover:bg-gray-100"
            :class="{ 'bg-blue-100': showSearch }"
          >
            <MagnifyingGlassIcon class="w-5 h-5" />
          </button>
          <!-- TODO: Implement new chat creation -->
          <!-- <button
            @click="showNewChat = true"
            class="p-2 rounded-full hover:bg-gray-100"
          >
            <PlusIcon class="w-5 h-5" />
          </button> -->
          <button class="p-2 rounded-full hover:bg-gray-100">
            <Cog6ToothIcon class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Search bar -->
      <div v-if="showSearch" class="px-4 pb-4">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск чатов, сообщений, людей..."
            class="w-full p-3 pl-10 border rounded-lg"
            @input="debouncedSearch"
          >
          <MagnifyingGlassIcon class="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
        </div>
      </div>
    </div>

    <!-- Chat sections -->
    <div class="chat-list-content overflow-y-auto">
      <!-- Pinned chats -->
      <div v-if="pinnedChats.length > 0" class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-50">
          <StarIcon class="w-4 h-4 inline mr-1" />
          Закрепленные чаты
        </div>
        <div class="space-y-1">
          <ChatListItem
            v-for="chat in pinnedChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Regular chats -->
      <div class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600">
          Обычные чаты
        </div>
        <div class="space-y-1">
          <ChatListItem
            v-for="chat in regularChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Groups -->
      <div v-if="groupChats.length > 0" class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600">
          <UsersIcon class="w-4 h-4 inline mr-1" />
          Группы
        </div>
        <div class="space-y-1">
          <ChatListItem
            v-for="chat in groupChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Archived chats -->
      <div v-if="archivedChats.length > 0" class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600 flex items-center justify-between cursor-pointer" @click="showArchived = !showArchived">
          <span>
            <ArchiveBoxIcon class="w-4 h-4 inline mr-1" />
            Архивные чаты ({{ archivedChats.length }})
          </span>
          <ChevronDownIcon
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-180': showArchived }"
          />
        </div>
        <div v-if="showArchived" class="space-y-1">
          <ChatListItem
            v-for="chat in archivedChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="filteredChats.length === 0 && searchQuery" class="text-center py-8 text-gray-500">
        <ChatBubbleLeftRightIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>Чаты не найдены</p>
      </div>
    </div>

    <!-- Context menu -->
    <ContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :items="contextMenuItems as any"
      @close="contextMenu.visible = false"
      @action="handleContextAction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  MagnifyingGlassIcon,
  PlusIcon,
  Cog6ToothIcon,
  StarIcon,
  UsersIcon,
  ArchiveBoxIcon,
  ChevronDownIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/vue/24/outline'
import ChatListItem from './ChatListItem.vue'
import ContextMenu from './ContextMenu.vue'
import { useGroupChatStore } from '@/stores/groupChat'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useAuthStore } from '@/stores/auth'
import { useAvatar } from '@/composables/useAvatar'
import apiClient from '@/api/client'
import type { User } from '@/types/index'


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

const props = defineProps<{
  activeChatId?: number
}>()

const emit = defineEmits<{
  chatSelected: [chat: Chat]
}>()

// Stores
const groupChatStore = useGroupChatStore()
const privateChatStore = usePrivateChatStore()
const authStore = useAuthStore()
const { getAvatarUrl } = useAvatar()

// State
const showSearch = ref(false)
const searchQuery = ref('')
const showArchived = ref(false)
const groupChatsList = ref<any[]>([])
const loadingGroupChats = ref(false)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  chat: null as Chat | null
})

// Computed
const allChats = computed((): Chat[] => {
  const chats: Chat[] = []

  // Add private chats
  privateChatStore.chats.forEach(privateChat => {
    const otherUser = (privateChat.user1.id === authStore.user?.id ? privateChat.user2 : privateChat.user1) as User
    const currentUserId = authStore.user?.id
    const isUser1 = privateChat.user1.id === currentUserId
    const settings = {
      notifications: isUser1 ? privateChat.user1_notifications : privateChat.user2_notifications,
      muted_until: isUser1 ? privateChat.user1_muted_until : privateChat.user2_muted_until,
      archived: isUser1 ? privateChat.user1_archived : privateChat.user2_archived,
      pinned: isUser1 ? privateChat.user1_pinned : privateChat.user2_pinned,
      blocked: isUser1 ? privateChat.user1_blocked : privateChat.user2_blocked,
    }

    chats.push({
      id: privateChat.id,
      type: 'private',
      name: `${otherUser.first_name} ${otherUser.last_name}`.trim() || otherUser.username,
      avatar: getAvatarUrl(otherUser.avatar_url),
      lastMessage: (privateChat as any).last_message ? {
        text: (privateChat as any).last_message.text,
        timestamp: (privateChat as any).last_message.created_at,
        sender: (privateChat as any).last_message.sender.username
      } : undefined,
      unreadCount: (privateChat as any).unread_count || 0,
      isPinned: settings.pinned,
      isArchived: settings.archived,
      status: otherUser.is_online ? 'online' : 'offline',
    })
  })

  groupChatsList.value.forEach(groupChat => {
    chats.push({
      id: groupChat.id,
      type: 'group',
      name: groupChat.name,
      avatar: groupChat.avatar_url || undefined,
      lastMessage: groupChat.last_message ? {
        text: groupChat.last_message.text,
        timestamp: groupChat.last_message.created_at,
        sender: groupChat.last_message.sender.username
      } : undefined,
      unreadCount: groupChat.unread_count || 0,
      isPinned: groupChat.user_member_settings?.is_pinned || false,
      isArchived: groupChat.user_member_settings?.is_archived || false,
      membersCount: groupChat.members_count,
      onlineCount: groupChat.online_count,
    })
  })

  return chats
})

const pinnedChats = computed(() =>
  allChats.value.filter(chat => chat.isPinned && !chat.isArchived)
)

const regularChats = computed(() =>
  allChats.value.filter(chat => !chat.isPinned && !chat.isArchived && chat.type === 'private')
)

const groupChats = computed(() =>
  allChats.value.filter(chat => !chat.isPinned && !chat.isArchived && chat.type === 'group')
)

const loadGroupChats = async () => {
  try {
    loadingGroupChats.value = true
    const response = await apiClient.get('/social/group-chats/')
    groupChatsList.value = response.data.results || response.data
  } catch (error) {
    console.error('Error loading group chats:', error)
  } finally {
    loadingGroupChats.value = false
  }
}

const archivedChats = computed(() =>
  allChats.value.filter(chat => chat.isArchived)
)

const filteredChats = computed(() => {
  if (!searchQuery.value) return allChats.value

  const query = searchQuery.value.toLowerCase()
  return allChats.value.filter(chat =>
    chat.name.toLowerCase().includes(query) ||
    (chat.lastMessage && chat.lastMessage.text.toLowerCase().includes(query))
  )
})

const contextMenuItems = computed(() => {
  if (!contextMenu.value.chat) return []

  const chat = contextMenu.value.chat
  return [
    {
      id: 'pin',
      label: chat.isPinned ? 'Открепить' : 'Закрепить',
      icon: 'pin',
      action: 'togglePin'
    },
    {
      id: 'archive',
      label: chat.isArchived ? 'Разархивировать' : 'Архивировать',
      icon: 'archive',
      action: 'toggleArchive'
    },
    { type: 'divider' } as any,
    {
      id: 'mute',
      label: 'Заглушить уведомления',
      icon: 'bell-slash',
      action: 'mute'
    },
    {
      id: 'mark-read',
      label: 'Отметить как прочитанное',
      icon: 'check',
      action: 'markRead'
    },
    { type: 'divider' } as any,
    {
      id: 'delete',
      label: 'Удалить чат',
      icon: 'trash',
      action: 'delete',
      danger: true
    }
  ]
})

// Methods
const selectChat = (chat: Chat) => {
  emit('chatSelected', chat)
}

const showContextMenu = (event: MouseEvent, chat: Chat) => {
  event.preventDefault()
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    chat
  }
}

const handleContextAction = (action: string) => {
  const chat = contextMenu.value.chat
  if (!chat) return

  switch (action) {
    case 'togglePin':
      togglePin(chat)
      break
    case 'toggleArchive':
      toggleArchive(chat)
      break
    case 'mute':
      muteChat(chat)
      break
    case 'markRead':
      markAsRead(chat)
      break
    case 'delete':
      deleteChat(chat)
      break
  }

  contextMenu.value.visible = false
}

const togglePin = async (chat: Chat) => {
  try {
    if (chat.type === 'private') {
      const settings: any = {}
      if (chat.isPinned) {
        settings.pinned = false
      } else {
        settings.pinned = true
        settings.archived = false // Unarchive when pinning
      }
      await privateChatStore.updateSettings(chat.id, settings)
    } else {
      const currentPinned = chat.isPinned
      await apiClient.patch(`/social/group-chats/${chat.id}/update_member_settings/`, {
        is_pinned: !currentPinned
      })
      const groupChat = groupChatsList.value.find(gc => gc.id === chat.id)
      if (groupChat && groupChat.user_member_settings) {
        groupChat.user_member_settings.is_pinned = !currentPinned
        if (!currentPinned) {
          groupChat.user_member_settings.is_archived = false
        }
      }
    }
  } catch (error) {
    console.error('Error toggling pin:', error)
  }
}

const toggleArchive = async (chat: Chat) => {
  try {
    if (chat.type === 'private') {
      const settings: any = {}
      if (chat.isArchived) {
        settings.archived = false
      } else {
        settings.archived = true
        settings.pinned = false // Unpin when archiving
      }
      await privateChatStore.updateSettings(chat.id, settings)
    } else {
      const currentArchived = chat.isArchived
      await apiClient.patch(`/social/group-chats/${chat.id}/update_member_settings/`, {
        is_archived: !currentArchived
      })
      const groupChat = groupChatsList.value.find(gc => gc.id === chat.id)
      if (groupChat && groupChat.user_member_settings) {
        groupChat.user_member_settings.is_archived = !currentArchived
        if (!currentArchived) {
          groupChat.user_member_settings.is_pinned = false
        }
      }
    }
  } catch (error) {
    console.error('Error toggling archive:', error)
  }
}

const muteChat = async (chat: Chat) => {
  try {
    if (chat.type === 'private') {
      const settings: any = {
        muted_until: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // Mute for 24 hours
      }
      await privateChatStore.updateSettings(chat.id, settings)
    } else {
      const mutedUntil = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      await apiClient.patch(`/social/group-chats/${chat.id}/update_member_settings/`, {
        is_muted: true,
        muted_until: mutedUntil
      })
      const groupChat = groupChatsList.value.find(gc => gc.id === chat.id)
      if (groupChat && groupChat.user_member_settings) {
        groupChat.user_member_settings.is_muted = true
        groupChat.user_member_settings.muted_until = mutedUntil
      }
    }
  } catch (error) {
    console.error('Error muting chat:', error)
  }
}

const markAsRead = async (chat: Chat) => {
  try {
    if (chat.type === 'private') {
      await apiClient.post(`/social/private-chats/${chat.id}/mark_as_read/`)
      await privateChatStore.loadChats() // Reload to update unread counts
    } else {
      await apiClient.post(`/social/group-chats/${chat.id}/mark_as_read/`)
      const groupChat = groupChatsList.value.find(gc => gc.id === chat.id)
      if (groupChat) groupChat.unread_count = 0
    }
  } catch (error) {
    console.error('Error marking as read:', error)
  }
}

const deleteChat = async (chat: Chat) => {
  if (!confirm('Удалить этот чат? Это действие нельзя отменить.')) return

  try {
    if (chat.type === 'private') {
      await privateChatStore.deleteChat(chat.id)
    } else {
      await apiClient.post(`/social/group-chats/${chat.id}/leave_chat/`)
      groupChatsList.value = groupChatsList.value.filter(gc => gc.id !== chat.id)
    }
  } catch (error) {
    console.error('Error deleting chat:', error)
  }
}

const handleChatCreated = (chat: Chat) => {
  // Refresh chat lists after new chat creation
  privateChatStore.loadChats()
  loadGroupChats()

  // Switch to the new chat
  emit('chatSelected', chat)
}

const debouncedSearch = (() => {
  let timeout: number
  return () => {
    clearTimeout(timeout)
    timeout = window.setTimeout(() => {
      // Search is handled by the filteredChats computed property
      // Additional search logic can be added here if needed
    }, 300)
  }
})()

// Lifecycle
onMounted(async () => {
  // Load chats
  await Promise.all([
    privateChatStore.loadChats(),
    loadGroupChats()
  ])
})
</script>

<style scoped>
.chat-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-right: 1px solid #e5e7eb;
}

.chat-list-header {
  flex-shrink: 0;
  border-bottom: 1px solid #e5e7eb;
}

.chat-list-content {
  flex: 1;
}
</style>