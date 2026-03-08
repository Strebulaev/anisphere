<template>
  <div class="chat-list">
    <!-- Folders bar - now on the left -->
    <ChatFoldersBar 
      :show-search="showSearch" 
      @folder-change="handleFolderChange" 
    />

    <!-- Main content area -->
    <div class="chat-list-main">
      <!-- Header -->
      <div class="chat-list-header">
      <div class="flex items-center justify-between p-4 border-b">
        <h1 class="text-xl font-semibold">Чаты</h1>
        <div class="flex items-center space-x-2">
          <button
            @click="showSearch = !showSearch"
            class="p-2 rounded-full hover:bg-gray-100"
            :class="{ 'bg-[#222222]': showSearch }"
          >
            <MagnifyingGlassIcon class="w-5 h-5" />
          </button>
          <button
            @click="showNewChat = true"
            class="p-2 rounded-full hover:bg-gray-100"
          >
            <PlusIcon class="w-5 h-5" />
          </button>
          <button class="p-2 rounded-full hover:bg-gray-100">
            <Cog6ToothIcon class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Search bar -->
      <div v-if="showSearch" class="px-4 pb-4 pt-2">
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
    <div ref="chatListContent" class="chat-list-content overflow-x-auto overflow-y-auto">
      <!-- Pinned chats -->
      <div v-if="displayPinnedChats.length > 0" class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-50">
          <StarIcon class="w-4 h-4 inline mr-1" />
          Закрепленные чаты
        </div>
        <div class="space-y-1">
          <ChatListItem
            v-for="chat in displayPinnedChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- All chats without separation -->
      <div v-if="displayChats.length > 0" class="mb-4">
        <div class="space-y-1">
          <ChatListItem
            v-for="chat in displayChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Archived chats -->
      <div v-if="displayArchivedChats.length > 0" class="mb-4">
        <div class="px-4 py-2 text-sm font-medium text-gray-600 flex items-center justify-between cursor-pointer" @click="showArchived = !showArchived">
          <span>
            <ArchiveBoxIcon class="w-4 h-4 inline mr-1" />
            Архивные чаты ({{ displayArchivedChats.length }})
          </span>
          <ChevronDownIcon
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-180': showArchived }"
          />
        </div>
        <div v-if="showArchived" class="space-y-1">
          <ChatListItem
            v-for="chat in displayArchivedChats"
            :key="chat.id"
            :chat="chat"
            :is-active="activeChatId === chat.id"
            @click="selectChat(chat)"
            @contextmenu="showContextMenu($event, chat)"
          />
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="filteredChats.length === 0 && (searchQuery || chatFoldersStore.activeFolderId !== 0)" class="empty-state">
        <ChatBubbleLeftRightIcon class="w-12 h-12 mb-2 opacity-50" />
        <p>{{ searchQuery ? 'Чаты не найдены' : 'В этой папке нет чатов' }}</p>
      </div>
    </div>
    </div>

    <!-- Context menu -->
    <ContextMenu
      :is-open="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="contextMenu.visible = false"
    >
      <template v-for="(item, index) in contextMenuItems" :key="item.id || index">
        <div v-if="item.type !== 'divider'" :class="['context-menu-item', { danger: item.danger }]" @click="handleContextAction(item.action)">
          <span>{{ item.label }}</span>
        </div>
        <div v-else class="context-menu-divider"></div>
      </template>
    </ContextMenu>

    <NewChatModal 
      :show="showNewChat"
      @close="showNewChat = false"
      @created="handleChatCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  MagnifyingGlassIcon,
  PlusIcon,
  Cog6ToothIcon,
  StarIcon,
  ArchiveBoxIcon,
  ChevronDownIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/vue/24/outline'
import ChatListItem from './ChatListItem.vue'
import ContextMenu from './ContextMenu.vue'
import NewChatModal from '@/components/modal/chats/NewChatModalReal.vue'
import ChatFoldersBar from './ChatFoldersBar.vue'
import { useGroupChatStore } from '@/stores/groupChat'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useAuthStore } from '@/stores/auth'
import { useChatFoldersStore } from '@/stores/chatFolders'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAvatar } from '@/composables/useAvatar'
import apiClient from '@/api/client'
import type { User, Chat as ChatType } from '@/types/index'
import type { Chat as FolderChatType } from '@/types/chat'

type LocalChat = {
  id: number
  type: 'private' | 'group'
  name: string
  avatar?: string | null
  avatar_url?: string | null
  // Поля для группы обсуждения аниме
  anime_id?: number | null
  anime_title?: string | null
  anime_poster?: string | null
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
  chatSelected: [chat: LocalChat]
}>()

// Stores
const groupChatStore = useGroupChatStore()
const privateChatStore = usePrivateChatStore()
const authStore = useAuthStore()
const chatFoldersStore = useChatFoldersStore()
const chatExtrasStore = useChatExtrasStore()
const { getAvatarUrl } = useAvatar()

// State
const showSearch = ref(false)
const showNewChat = ref(false)
const searchQuery = ref('')
const showArchived = ref(false)
const groupChatsList = ref<any[]>([])
const loadingGroupChats = ref(false)
const folderChats = ref<any[]>([])
const loadingFolderChats = ref(false)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  chat: null as LocalChat | null
})

const chatListContent = ref<HTMLElement | null>(null)

// Хелпер для получения полного URL медиа
const getMediaUrl = (path: string): string => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const baseUrl = import.meta.env.VITE_API_URL || 'https://anisphere.ru'
  return `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

// Computed
const allChats = computed((): LocalChat[] => {
  const chats: LocalChat[] = []

  // Add private chats
  privateChatStore.chats.forEach(privateChat => {
    // Debug log
    console.log('PrivateChat data:', privateChat)
    
    // Handle both API response formats - user1/user2 или other_user
    let otherUserData: any = null
    
    // Try to get other_user first (newer API format)
    if (privateChat.other_user) {
      otherUserData = privateChat.other_user
    } 
    // Try user1/user2 format
    else if (privateChat.user1 && privateChat.user2) {
      const currentUserId = authStore.user?.id
      otherUserData = privateChat.user1?.id === currentUserId ? privateChat.user2 : privateChat.user1
    }
    
    const currentUserId = authStore.user?.id
    const isUser1 = privateChat.user1?.id === currentUserId
    const settings = {
      notifications: isUser1 ? privateChat.user1_notifications : privateChat.user2_notifications,
      muted_until: isUser1 ? privateChat.user1_muted_until : privateChat.user2_muted_until,
      archived: isUser1 ? privateChat.user1_archived : privateChat.user2_archived,
      pinned: isUser1 ? privateChat.user1_pinned : privateChat.user2_pinned,
      blocked: isUser1 ? privateChat.user1_blocked : privateChat.user2_blocked,
    }

    // Get name - try different fields
    const userData = otherUserData as any
    let chatName = 'Чат ' + privateChat.id
    
    if (userData) {
      chatName = userData?.display_name 
        || userData?.username 
        || (userData?.first_name ? `${userData.first_name} ${userData.last_name}`.trim() : '')
        || chatName
    }

    chats.push({
      id: privateChat.id,
      type: 'private',
      name: chatName.trim(),
      avatar: getAvatarUrl(userData?.avatar_url || userData?.avatar),
      lastMessage: (privateChat as any).last_message ? {
        text: (privateChat as any).last_message.text,
        timestamp: (privateChat as any).last_message.created_at,
        sender: (privateChat as any).last_message.sender?.username || ''
      } : undefined,
      unreadCount: (privateChat as any).unread_count || 0,
      isPinned: settings.pinned,
      isArchived: settings.archived,
      status: userData?.is_online ? 'online' : 'offline',
    })
  })

  // Add group chats
  groupChatsList.value.forEach(groupChat => {
    // Для групп обсуждений используем постер аниме (уже с полным URL)
    // Проверяем на пустую строку, null и undefined
    const animePoster = groupChat.anime_poster
    const hasAnimePoster = animePoster && typeof animePoster === 'string' && animePoster.trim() !== ''
    const displayAvatar = hasAnimePoster ? animePoster : (groupChat.avatar_url || undefined)
    const displayName = groupChat.anime_title || groupChat.name
    
    chats.push({
      id: groupChat.id,
      type: 'group',
      name: displayName,
      avatar: displayAvatar,
      avatar_url: displayAvatar, // Дублируем для совместимости
      // Поля для группы обсуждения аниме
      anime_id: groupChat.anime_id || null,
      anime_title: groupChat.anime_title || null,
      anime_poster: animePoster || null,
      lastMessage: groupChat.last_message ? {
        text: groupChat.last_message.text,
        timestamp: groupChat.last_message.created_at,
        sender: groupChat.last_message.sender?.username || ''
      } : undefined,
      unreadCount: groupChat.unread_count || 0,
      isPinned: groupChat.user_member_settings?.is_pinned || false,
      isArchived: groupChat.user_member_settings?.is_archived || false,
      membersCount: groupChat.members_count,
      onlineCount: groupChat.online_count,
    })
  })

  // Add folder chats (discussions) when active
  if (chatFoldersStore.activeFolderId === -4) {
    folderChats.value.forEach(folderChat => {
      // Check if already added
      if (!chats.find(c => c.id === folderChat.id)) {
        // Для групп обсуждений используем постер аниме
        // anime_poster уже содержит полный URL из chatFoldersApi
        // Проверяем на пустую строку, null и undefined
        const animePoster = folderChat.anime_poster
        const hasAnimePoster = animePoster && typeof animePoster === 'string' && animePoster.trim() !== ''
        const displayAvatar = hasAnimePoster ? animePoster : (folderChat.avatar_url || undefined)
        const displayName = folderChat.anime_title || folderChat.name
        
        chats.push({
          id: folderChat.id,
          type: 'group',
          name: displayName,
          avatar: displayAvatar,
          avatar_url: displayAvatar, // Дублируем для совместимости
          // Поля для группы обсуждения аниме
          anime_id: folderChat.anime_id || null,
          anime_title: folderChat.anime_title || null,
          anime_poster: animePoster || null,
          lastMessage: folderChat.last_message ? {
            text: folderChat.last_message.text,
            timestamp: folderChat.last_message.created_at,
            sender: folderChat.last_message.sender?.username || ''
          } : undefined,
          unreadCount: folderChat.unread_count || 0,
          isPinned: false,
          isArchived: false,
          membersCount: folderChat.members_count,
        })
      }
    })
  }

  return chats
})

const loadGroupChats = async () => {
  try {
    loadingGroupChats.value = true
    const response = await apiClient.get('/social/group-chats/')
    groupChatsList.value = response.data.results || response.data
    
    // Debug: проверим, какие данные приходят для групп обсуждений
    const discussionChats = (groupChatsList.value as any[]).filter(
      (chat: any) => chat.anime_id || chat.anime_title
    )
    if (discussionChats.length > 0) {
      console.log('DEBUG: Discussion chats from API:', discussionChats)
    }
  } catch (error) {
    console.error('Error loading group chats:', error)
  } finally {
    loadingGroupChats.value = false
  }
}

const loadFolderChats = async () => {
  const activeFolderId = chatFoldersStore.activeFolderId
  if (activeFolderId !== -4) {
    folderChats.value = []
    return
  }

  try {
    loadingFolderChats.value = true
    const discussions = await chatFoldersStore.getFolderChats(-4)
    folderChats.value = discussions
  } catch (error) {
    console.error('Error loading folder chats:', error)
    folderChats.value = []
  } finally {
    loadingFolderChats.value = false
  }
}

const filteredChats = computed(() => {
  let chats = allChats.value

  // Apply folder-based type filter using rules
  const activeFolderId = chatFoldersStore.activeFolderId
  if (activeFolderId && activeFolderId > 0) {
    // Это пользовательская папка - фильтруем по правилам
    const folder = chatFoldersStore.folders.find(f => f.id === activeFolderId)
    if (folder) {
      if (folder.rules.include_groups && !folder.rules.include_private) {
        chats = chats.filter(chat => chat.type === 'group')
      } else if (folder.rules.include_private && !folder.rules.include_groups) {
        chats = chats.filter(chat => chat.type === 'private')
      }
    }
  }

  // Apply system folder filters
  if (activeFolderId === -1) {
    // Личные чаты
    chats = chats.filter(chat => chat.type === 'private')
  } else if (activeFolderId === -2) {
    // Группы
    chats = chats.filter(chat => chat.type === 'group')
  }

  // Apply folder rules from store
  const activeFolder = chatFoldersStore.activeFolder
  if (activeFolder) {
    // Convert LocalChat to FolderChatType for applyFolderRules
    const folderChats: any[] = chats.map(chat => ({
      id: chat.id,
      type: chat.type,
      name: chat.name,
      avatar: chat.avatar,
      avatar_url: chat.avatar,
      last_message: chat.lastMessage ? {
        id: 0,
        text: chat.lastMessage.text,
        sender_id: 0,
        chat_id: chat.id,
        created_at: chat.lastMessage.timestamp,
        updated_at: chat.lastMessage.timestamp,
        is_read: true
      } : undefined,
      unread_count: chat.unreadCount,
      created_at: '',
      updated_at: chat.lastMessage?.timestamp || '',
      is_pinned: chat.isPinned,
      is_archived: chat.isArchived,
      is_muted: false,
      ...(chat.type === 'group' ? {
        members_count: chat.membersCount || 0,
        members: [],
        owner: { id: 0, username: '' },
        description: '',
        is_public: false
      } : {
        other_user: { id: 0, username: chat.name }
      })
    }))
    const filteredFolderChats = chatFoldersStore.applyFolderRules(folderChats, activeFolder)
    // Filter original chats based on filtered folder chats
    const filteredIds = new Set(filteredFolderChats.map(c => c.id))
    chats = chats.filter(c => filteredIds.has(c.id))
  }

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    chats = chats.filter(chat =>
      chat.name.toLowerCase().includes(query) ||
      (chat.lastMessage && chat.lastMessage.text.toLowerCase().includes(query))
    )
  }

  return chats
})

const displayChats = computed(() => {
  return filteredChats.value.filter(chat => !chat.isPinned && !chat.isArchived)
})

const displayPinnedChats = computed(() => {
  return filteredChats.value.filter(chat => chat.isPinned && !chat.isArchived)
})

const displayArchivedChats = computed(() => {
  return filteredChats.value.filter(chat => chat.isArchived)
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
const selectChat = (chat: LocalChat) => {
  emit('chatSelected', chat)
}

const showContextMenu = (event: MouseEvent, chat: LocalChat) => {
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

const togglePin = async (chat: LocalChat) => {
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
    // Обновить данные
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats(),
      chatExtrasStore.loadUnreadChats()
    ])
  } catch (error) {
    console.error('Error toggling pin:', error)
  }
}

const toggleArchive = async (chat: LocalChat) => {
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
    // Обновить данные
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats(),
      chatExtrasStore.loadUnreadChats()
    ])
  } catch (error) {
    console.error('Error toggling archive:', error)
  }
}

const muteChat = async (chat: LocalChat) => {
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
    // Обновить данные
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats()
    ])
  } catch (error) {
    console.error('Error muting chat:', error)
  }
}

const markAsRead = async (chat: LocalChat) => {
  try {
    // Используем разные эндпоинты для private и group чатов
    const endpoint = chat.type === 'private' 
      ? `/social/private-chats/${chat.id}/mark_as_read/`
      : `/social/group-chats/${chat.id}/mark_as_read/`
    
    await apiClient.post(endpoint)
    
    // Обновить списки чатов
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats(),
      chatExtrasStore.loadUnreadChats()
    ])
  } catch (error) {
    console.error('Error marking as read:', error)
  }
}

const deleteChat = async (chat: LocalChat) => {
  if (!confirm('Удалить этот чат? Это действие нельзя отменить.')) return

  try {
    if (chat.type === 'private') {
      await privateChatStore.deleteChat(chat.id)
    } else {
      await apiClient.post(`/social/group-chats/${chat.id}/leave_chat/`)
      groupChatsList.value = groupChatsList.value.filter(gc => gc.id !== chat.id)
    }
    // Обновить данные
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats(),
      chatExtrasStore.loadUnreadChats()
    ])
  } catch (error) {
    console.error('Error deleting chat:', error)
  }
}

const handleChatCreated = async (chatId: number) => {
  // Refresh chat lists after new chat creation
  await Promise.all([
    privateChatStore.loadChats(),
    loadGroupChats(),
    chatExtrasStore.loadUnreadChats()
  ])

  // Find the new chat and switch to it
  const newChat = allChats.value.find(c => c.id === chatId)
  if (newChat) {
    emit('chatSelected', newChat)
  } else {
    // Если чат не найден в списке, пробуем обновить ещё раз
    await Promise.all([
      privateChatStore.loadChats(),
      loadGroupChats()
    ])
    const retryChat = allChats.value.find(c => c.id === chatId)
    if (retryChat) {
      emit('chatSelected', retryChat)
    }
  }
}

const handleFolderChange = (folder: any) => {
  // Folder change logic is handled by the store
  // Additional logic can be added here if needed
}

const debouncedSearch = (() => {
  let timeout: number
  return () => {
    clearTimeout(timeout)
    timeout = window.setTimeout(() => {
      // При поиске также обновляем непрочитанные
      chatExtrasStore.loadUnreadChats()
    }, 300)
  }
})()

// Watch for search changes
watch(searchQuery, () => {
  debouncedSearch()
})

// Lifecycle
onMounted(async () => {
  // Load chats and folders - всегда загружаем свежие данные
  await Promise.all([
    privateChatStore.loadChats(),
    loadGroupChats(),
    chatFoldersStore.loadFolders(),
    chatExtrasStore.loadUnreadChats()
  ])
  
  // Дополнительно загружаем папку обсуждений если она активна или нужно показать все чаты
  if (chatFoldersStore.activeFolderId === -4 || !chatFoldersStore.activeFolderId) {
    await loadFolderChats()
  }
})

// Watch for folder changes to load folder chats
watch(() => chatFoldersStore.activeFolderId, (newFolderId) => {
  if (newFolderId === -4) {
    loadFolderChats()
  }
  // Обновить непрочитанные при смене папки
  chatExtrasStore.loadUnreadChats()
})

// Периодическое обновление непрочитанных (каждые 30 секунд)
let unreadInterval: number | null = null
onMounted(() => {
  unreadInterval = window.setInterval(() => {
    chatExtrasStore.loadUnreadChats()
    privateChatStore.loadChats()
    loadGroupChats()
  }, 30000)
})

onUnmounted(() => {
  if (unreadInterval) {
    clearInterval(unreadInterval)
  }
})
</script>

<style scoped>
.chat-list {
  display: flex;
  flex-direction: row;
  height: 100%;
  background: #1a1a1a;
  border-right: 1px solid #2a2a2a;
  position: relative;
}

.chat-list-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.chat-list-header {
  flex-shrink: 0;
  border-bottom: 1px solid #2a2a2a;
}

.chat-list-header h1 {
  color: #e0e0e0;
}

.chat-list-header button {
  color: #888;
}

.chat-list-header button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #222222;
}

.chat-list-header input {
  background: #0f0f0f;
  border-color: #2a2a2a;
  color: #e0e0e0;
}

.chat-list-header input::placeholder {
  color: #666;
}

.chat-list-content {
  flex: 1;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
}

.chat-list-resizer {
  flex-shrink: 0;
  height: 4px;
  background: #2a2a2a;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.chat-list-resizer:hover {
  background: #3a3a3a;
}

.resizer-handle {
  width: 40px;
  height: 2px;
  background: #555;
  border-radius: 1px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 2rem;
  text-align: center;
  color: #666;
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 0.75rem;
}

.empty-state p {
  margin: 0;
}

.chat-list-content .text-gray-600 {
  color: #888;
}

.chat-list-content .bg-gray-50 {
  background: rgba(255, 255, 255, 0.03);
}

.chat-list-content .text-gray-500 {
  color: #666;
}

/* Folders integration styles */
.chat-folders-bar {
  flex-shrink: 0;
  position: relative !important;
  top: auto !important;
  left: auto !important;
}
</style>