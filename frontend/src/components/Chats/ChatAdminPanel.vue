<template>
  <div class="chat-admin-panel">
    <!-- Header with tabs -->
    <div class="border-b">
      <nav class="flex space-x-4 px-4 pt-2 overflow-x-auto">
        <button
          v-for="tab in visibleTabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-3 py-2 text-sm font-medium whitespace-nowrap"
          :class="{
            'border-b-2 border-blue-500 text-blue-600': activeTab === tab.id,
            'text-gray-500 hover:text-gray-700': activeTab !== tab.id
          }"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Content -->
    <div class="p-4 overflow-y-auto" style="max-height: calc(80vh - 60px);">
      <!-- Members tab -->
      <div v-if="activeTab === 'members'" class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Участники ({{ members.length }})</h3>
          <div class="flex gap-2">
            <button
              v-if="canInviteUsers"
              @click="showInviteDialog = true"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Пригласить
            </button>
            <button
              v-if="canManageChat"
              @click="showInviteLinksDialog = true"
              class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
            >
              Ссылки
            </button>
          </div>
        </div>

        <!-- Search -->
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск участников..."
            class="w-full p-2 pl-10 border rounded-lg"
          >
          <SearchIcon class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
        </div>

        <!-- Members list -->
        <div class="space-y-2">
          <div
            v-for="member in filteredMembers"
            :key="member.id"
            class="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <img
                :src="member.user.avatar || '/default-avatar.png'"
                class="w-10 h-10 rounded-full"
              >
              <div>
                <div class="flex items-center space-x-2">
                  <span class="font-medium">{{ member.user.username }}</span>
                  <span
                    v-if="member.role"
                    class="px-2 py-1 text-xs rounded-full"
                    :style="{ backgroundColor: member.role.color + '20', color: member.role.color }"
                  >
                    {{ member.role.name }}
                  </span>
                  <span
                    v-if="member.is_owner"
                    class="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full"
                  >
                    Владелец
                  </span>
                  <span
                    v-else-if="member.is_admin"
                    class="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full"
                  >
                    Админ
                  </span>
                </div>
                <div class="flex items-center space-x-1 text-sm text-gray-500">
                  <span
                    class="w-2 h-2 rounded-full"
                    :class="member.user.status?.status === 'online' ? 'bg-green-500' : 'bg-gray-400'"
                  ></span>
                  <span>{{ member.user.status?.custom_status || getStatusText(member.user.status?.status) }}</span>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center space-x-2">
              <select
                v-if="canPromoteMembers && !member.is_owner"
                v-model="member.role_id"
                @change="updateMemberRole(member)"
                class="border rounded px-2 py-1 text-sm"
              >
                <option :value="null">Участник</option>
                <option
                  v-for="role in chatRoles"
                  :key="role.id"
                  :value="role.id"
                >
                  {{ role.name }}
                </option>
              </select>

              <button
                v-if="canRestrictMembers && !member.is_owner && !member.is_admin"
                @click="showRestrictDialog(member)"
                class="p-1 text-gray-500 hover:text-orange-600"
                title="Ограничить"
              >
                <ShieldCheckIcon class="w-5 h-5" />
              </button>

              <button
                v-if="canManageChat && !member.is_owner"
                @click="toggleMuteMember(member)"
                class="p-1 text-gray-500 hover:text-gray-700"
                :title="member.is_muted ? 'Разглушить' : 'Заглушить'"
              >
                <SpeakerXMarkIcon v-if="member.is_muted" class="w-5 h-5" />
                <SpeakerWaveIcon v-else class="w-5 h-5" />
              </button>

              <button
                v-if="canBanUsers && !member.is_owner"
                @click="showBanDialog(member)"
                class="p-1 text-gray-500 hover:text-red-600"
                title="Забанить"
              >
                <NoSymbolIcon class="w-5 h-5" />
              </button>

              <button
                v-if="canManageChat && !member.is_owner"
                @click="removeMember(member)"
                class="p-1 text-gray-500 hover:text-red-600"
                title="Удалить из чата"
              >
                <TrashIcon class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Invite Links tab -->
      <div v-else-if="activeTab === 'invites'" class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Ссылки-приглашения</h3>
          <button
            v-if="canInviteUsers"
            @click="showCreateInviteLink = true"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Создать ссылку
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="link in inviteLinks"
            :key="link.id"
            class="p-4 border rounded-lg"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ link.name || 'Без названия' }}</span>
                  <span v-if="link.is_primary" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                    Основная
                  </span>
                  <span v-if="!link.is_valid" class="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded">
                    Недействительна
                  </span>
                </div>
                <div class="text-sm text-gray-500 mt-1">
                  {{ link.invite_link }}
                </div>
                <div class="flex gap-4 mt-2 text-xs text-gray-400">
                  <span>Использований: {{ link.usage_count }}/{{ link.usage_limit || '∞' }}</span>
                  <span v-if="link.expires_at">
                    До: {{ formatDate(link.expires_at) }}
                  </span>
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  @click="copyInviteLink(link.invite_link)"
                  class="p-2 text-gray-500 hover:text-blue-600"
                  title="Копировать"
                >
                  <ClipboardDocumentIcon class="w-4 h-4" />
                </button>
                <button
                  v-if="!link.is_revoked"
                  @click="revokeInviteLink(link)"
                  class="p-2 text-gray-500 hover:text-red-600"
                  title="Отозвать"
                >
                  <XMarkIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="inviteLinks.length === 0" class="text-center py-8 text-gray-400">
            Нет созданных ссылок
          </div>
        </div>
      </div>

      <!-- Join Requests tab -->
      <div v-else-if="activeTab === 'requests'" class="space-y-4">
        <h3 class="text-lg font-semibold">Запросы на вступление ({{ joinRequests.length }})</h3>

        <div class="space-y-3">
          <div
            v-for="request in joinRequests"
            :key="request.id"
            class="p-4 border rounded-lg"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img
                  :src="request.user.avatar || '/default-avatar.png'"
                  class="w-10 h-10 rounded-full"
                />
                <div>
                  <div class="font-medium">{{ request.user.username }}</div>
                  <div class="text-sm text-gray-500">{{ request.message }}</div>
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  @click="approveJoinRequest(request)"
                  class="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  Принять
                </button>
                <button
                  @click="rejectJoinRequest(request)"
                  class="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                >
                  Отклонить
                </button>
              </div>
            </div>
          </div>

          <div v-if="joinRequests.length === 0" class="text-center py-8 text-gray-400">
            Нет запросов на вступление
          </div>
        </div>
      </div>

      <!-- Banned Users tab -->
      <div v-else-if="activeTab === 'banned'" class="space-y-4">
        <h3 class="text-lg font-semibold">Заблокированные пользователи</h3>

        <div class="space-y-3">
          <div
            v-for="ban in bannedUsers"
            :key="ban.id"
            class="p-4 border rounded-lg"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img
                  :src="ban.user.avatar || '/default-avatar.png'"
                  class="w-10 h-10 rounded-full"
                />
                <div>
                  <div class="font-medium">{{ ban.user.username }}</div>
                  <div class="text-sm text-gray-500">{{ ban.reason }}</div>
                  <div class="text-xs text-gray-400">
                    {{ ban.until_date ? `До: ${formatDate(ban.until_date)}` : 'Навсегда' }}
                  </div>
                </div>
              </div>
              <button
                @click="unbanUser(ban)"
                class="px-3 py-1 bg-gray-700 text-white rounded text-sm hover:bg-gray-600"
              >
                Разблокировать
              </button>
            </div>
          </div>

          <div v-if="bannedUsers.length === 0" class="text-center py-8 text-gray-400">
            Нет заблокированных пользователей
          </div>
        </div>
      </div>

      <!-- Roles tab -->
      <div v-else-if="activeTab === 'roles'" class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Роли и разрешения</h3>
          <button
            v-if="canManageChat"
            @click="showCreateRoleDialog = true"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Создать роль
          </button>
        </div>

        <!-- Roles list -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="role in chatRoles"
            :key="role.id"
            class="border rounded-lg p-4"
          >
            <div class="flex justify-between items-start mb-2">
              <div class="flex items-center space-x-2">
                <div
                  class="w-3 h-3 rounded-full"
                  :style="{ backgroundColor: role.color }"
                ></div>
                <h4 class="font-semibold">{{ role.name }}</h4>
              </div>
              <span class="text-sm text-gray-500">{{ getRoleLevelText(role.level) }}</span>
            </div>

            <!-- Permissions -->
            <div class="space-y-1 text-sm">
              <div
                v-for="permission in getRolePermissions(role)"
                :key="permission"
                class="flex items-center space-x-2"
              >
                <CheckIcon v-if="role[permission]" class="w-4 h-4 text-green-500" />
                <XMarkIcon v-else class="w-4 h-4 text-gray-300" />
                <span>{{ getPermissionText(permission) }}</span>
              </div>
            </div>

            <!-- Actions -->
            <div class="mt-4 flex space-x-2">
              <button
                v-if="role.level < 3 && canManageChat"
                @click="editRole(role)"
                class="flex-1 px-3 py-1 text-sm border rounded hover:bg-gray-50"
              >
                Редактировать
              </button>
              <button
                v-if="role.level < 3 && canManageChat && !hasMembersWithRole(role)"
                @click="deleteRole(role)"
                class="flex-1 px-3 py-1 text-sm border border-red-200 text-red-600 rounded hover:bg-red-50"
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs tab -->
      <div v-else-if="activeTab === 'logs'" class="space-y-4">
        <h3 class="text-lg font-semibold">Логи администраторов</h3>

        <div class="space-y-2">
          <div
            v-for="log in adminLogs"
            :key="log.id"
            class="p-3 border rounded-lg"
          >
            <div class="flex justify-between items-start">
              <div class="space-y-1">
                <div class="flex items-center space-x-2">
                  <span class="font-medium">{{ log.user?.username || 'Система' }}</span>
                  <span class="text-sm text-gray-500">{{ log.action_display }}</span>
                </div>

                <div v-if="log.target_user" class="text-sm text-gray-600">
                  Цель: {{ log.target_user.username }}
                </div>

                <div v-if="log.details" class="text-sm text-gray-500">
                  {{ formatLogDetails(log.details) }}
                </div>
              </div>

              <div class="text-sm text-gray-400">
                {{ formatDate(log.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Settings tab -->
      <div v-else-if="activeTab === 'settings'" class="space-y-6">
        <h3 class="text-lg font-semibold">Настройки чата</h3>

        <!-- Basic settings -->
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Название чата</label>
            <input
              v-model="chatName"
              type="text"
              class="w-full p-2 border rounded-lg"
              :disabled="!canChangeChatInfo"
            >
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Описание</label>
            <textarea
              v-model="chatDescription"
              rows="3"
              class="w-full p-2 border rounded-lg"
              :disabled="!canChangeChatInfo"
            ></textarea>
          </div>
        </div>

        <!-- Privacy -->
        <div class="space-y-3">
          <h4 class="font-medium">Приватность</h4>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium">Публичный чат</div>
              <div class="text-sm text-gray-500">Могут присоединиться все по ссылке</div>
            </div>
            <input
              v-model="isPublic"
              type="checkbox"
              class="toggle"
              :disabled="!canManageChat"
            >
          </div>

          <div v-if="inviteLink" class="p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center justify-between">
              <div class="font-mono text-sm">{{ inviteLink }}</div>
              <button
                @click="copyInviteLink(inviteLink)"
                class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Копировать
              </button>
            </div>
          </div>
        </div>

        <!-- Message settings -->
        <div class="space-y-3">
          <h4 class="font-medium">Отправка сообщений</h4>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium">Медленный режим</div>
              <div class="text-sm text-gray-500">Задержка между сообщениями</div>
            </div>
            <select
              v-model="slowModeDelay"
              class="border rounded px-3 py-1"
              :disabled="!canManageChat"
            >
              <option :value="0">Выкл</option>
              <option :value="10">10 сек</option>
              <option :value="30">30 сек</option>
              <option :value="60">1 мин</option>
              <option :value="300">5 мин</option>
            </select>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center space-x-2">
              <input
                v-model="canSendMedia"
                type="checkbox"
                :disabled="!canManageChat"
              >
              <span>Медиафайлы</span>
            </div>

            <div class="flex items-center space-x-2">
              <input
                v-model="canSendStickers"
                type="checkbox"
                :disabled="!canManageChat"
              >
              <span>Стикеры</span>
            </div>

            <div class="flex items-center space-x-2">
              <input
                v-model="canSendPolls"
                type="checkbox"
                :disabled="!canManageChat"
              >
              <span>Опросы</span>
            </div>

            <div class="flex items-center space-x-2">
              <input
                v-model="canPinMessages"
                type="checkbox"
                :disabled="!canManageChat"
              >
              <span>Закрепление</span>
            </div>
          </div>
        </div>

        <!-- Save button -->
        <div class="pt-4 border-t">
          <button
            @click="saveSettings"
            class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            :disabled="!hasChanges"
          >
            Сохранить изменения
          </button>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <InviteUserDialog
      v-if="showInviteDialog"
      :chat-id="chatId"
      @close="showInviteDialog = false"
      @invited="handleUserInvited"
    />

    <CreateRoleDialog
      v-if="showCreateRoleDialog"
      :chat-id="chatId"
      @close="showCreateRoleDialog = false"
      @created="handleRoleCreated"
    />

    <CreateRoleDialog
      v-if="showEditRoleDialog"
      :chat-id="chatId"
      :role="currentEditingRole"
      @close="showEditRoleDialog = false"
      @updated="handleRoleUpdated"
    />

    <BanUserModal
      v-if="banDialog.member"
      :member="banDialog.member"
      @close="banDialog.member = null"
      @banned="handleUserBanned"
    />

    <RestrictUserModal
      v-if="restrictDialog.member"
      :member="restrictDialog.member"
      @close="restrictDialog.member = null"
      @restricted="handleUserRestricted"
    />

    <CreateInviteLinkModal
      v-if="showCreateInviteLink"
      :chat-id="chatId"
      @close="showCreateInviteLink = false"
      @created="handleInviteLinkCreated"
    />

    <ChatSettingsModal
      v-if="showSettingsModal"
      :chat-id="chatId"
      chat-type="group"
      :is-owner="isOwner"
      @close="showSettingsModal = false"
      @settings-changed="handleSettingsChanged"
    />

    <!-- Toast notification -->
    <div v-if="toastMessage" class="fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white z-50" :class="toastType === 'success' ? 'bg-green-500' : 'bg-red-500'">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  MagnifyingGlassIcon as SearchIcon,
  CheckIcon,
  XMarkIcon,
  TrashIcon,
  NoSymbolIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ShieldCheckIcon,
  ClipboardDocumentIcon
} from '@heroicons/vue/24/outline'
import { useGroupChatStore } from '@/stores/groupChat'
import chatsApi from '@/api/chats'

// Types
import type { ChatMember, ChatRole } from '@/types'

// Components
import BanUserModal from './BanUserModal.vue'
import RestrictUserModal from './RestrictUserModal.vue'
import CreateInviteLinkModal from './CreateInviteLinkModal.vue'
import ChatSettingsModal from './ChatSettingsModal.vue'

interface Props {
  chatId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const groupChatStore = useGroupChatStore()

// State
const activeTab = ref('members')
const searchQuery = ref('')
const showInviteDialog = ref(false)
const showCreateRoleDialog = ref(false)
const showEditRoleDialog = ref(false)
const showCreateInviteLink = ref(false)
const showInviteLinksDialog = ref(false)
const showSettingsModal = ref(false)
const currentEditingRole = ref(null)
const banDialog = ref({ member: null })
const restrictDialog = ref({ member: null })
const toastMessage = ref('')
const toastType = ref('')

// New state for invite links and join requests
const inviteLinks = ref<any[]>([])
const joinRequests = ref<any[]>([])
const bannedUsers = ref<any[]>([])

const tabs = [
  { id: 'members', name: 'Участники' },
  { id: 'invites', name: 'Ссылки' },
  { id: 'requests', name: 'Запросы', requiresPermission: 'can_invite_users' },
  { id: 'banned', name: 'Забаненные', requiresPermission: 'can_ban_users' },
  { id: 'roles', name: 'Роли' },
  { id: 'logs', name: 'Логи' },
  { id: 'settings', name: 'Настройки' }
]

// Computed
const members = computed(() => groupChatStore.chatMembers as any[])
const chatRoles = computed(() => groupChatStore.chatRoles as any[])
const adminLogs = computed(() => groupChatStore.adminLogs)
const currentChat = computed(() => groupChatStore.currentChat)
const isOwner = computed(() => groupChatStore.isOwner)

const canManageChat = computed(() => groupChatStore.canManageChat())
const canBanUsers = computed(() => groupChatStore.canBanUsers())
const canInviteUsers = computed(() => groupChatStore.canInviteUsers())
const canChangeChatInfo = computed(() => groupChatStore.canChangeChatInfo())
const canPromoteMembers = computed(() => groupChatStore.canPromoteMembers())
const canRestrictMembers = computed(() => groupChatStore.hasPermission('can_restrict_members'))

const visibleTabs = computed(() => {
  return tabs.filter(tab => {
    if (!tab.requiresPermission) return true
    return groupChatStore.hasPermission(tab.requiresPermission) || isOwner.value
  })
})

const filteredMembers = computed(() => {
  if (!searchQuery.value) return members.value

  const query = searchQuery.value.toLowerCase()
  return members.value.filter(member =>
    member.user.username.toLowerCase().includes(query) ||
    (member.user.first_name && member.user.first_name.toLowerCase().includes(query)) ||
    (member.user.last_name && member.user.last_name.toLowerCase().includes(query))
  )
})

const chatName = computed({
  get: () => currentChat.value?.name || '',
  set: (value) => {
    if (currentChat.value) {
      currentChat.value.name = value
    }
  }
})

const chatDescription = computed({
  get: () => currentChat.value?.description || '',
  set: (value) => {
    if (currentChat.value) {
      currentChat.value.description = value
    }
  }
})

const isPublic = ref(currentChat.value?.is_public || false)
const inviteLink = computed(() => currentChat.value?.invite_link)
const slowModeDelay = ref(0)
const canSendMedia = ref(true)
const canSendStickers = ref(true)
const canSendPolls = ref(true)
const canPinMessages = ref(true)

const hasChanges = computed(() => {
  if (!currentChat.value) return false
  return (
    chatName.value !== currentChat.value.name ||
    chatDescription.value !== currentChat.value.description ||
    isPublic.value !== currentChat.value.is_public
  )
})

// Methods
const getRoleLevelText = (level: number) => {
  const levels = ['Участник', 'Модератор', 'Администратор', 'Владелец']
  return levels[level] || 'Участник'
}

const getRolePermissions = (role: any) => {
  return Object.keys(role).filter(key =>
    key.startsWith('can_') && typeof role[key] === 'boolean'
  )
}

const getPermissionText = (permission: string) => {
  const map: Record<string, string> = {
    'can_delete_messages': 'Удаление сообщений',
    'can_ban_users': 'Блокировка пользователей',
    'can_pin_messages': 'Закрепление сообщений',
    'can_add_new_admins': 'Добавление администраторов',
    'can_manage_chat': 'Управление чатом',
    'can_restrict_members': 'Ограничение участников',
    'can_promote_members': 'Повышение участников',
    'can_change_chat_info': 'Изменение информации чата',
    'can_invite_users': 'Приглашение пользователей'
  }
  return map[permission] || permission.replace('can_', '').replace('_', ' ')
}

const getStatusText = (status: string | undefined) => {
  const statusMap: Record<string, string> = {
    'online': 'В сети',
    'away': 'Отошёл',
    'busy': 'Занят',
    'offline': 'Не в сети'
  }
  return statusMap[status || 'offline'] || 'Не в сети'
}

const updateMemberRole = async (member: any) => {
  try {
    await chatsApi.roles.setMemberRole(props.chatId, member.user.id, member.role_id)
    showToast('Роль обновлена', 'success')
  } catch (error) {
    console.error('Error updating member role:', error)
    showToast('Ошибка обновления роли', 'error')
  }
}

const toggleMuteMember = async (member: any) => {
  try {
    await groupChatStore.toggleMemberMute(props.chatId, member.user.id, !member.is_muted)
    showToast(member.is_muted ? 'Пользователь разглушён' : 'Пользователь заглушён', 'success')
  } catch (error) {
    console.error('Error toggling member mute:', error)
    showToast('Ошибка', 'error')
  }
}

const removeMember = async (member: any) => {
  if (!confirm(`Удалить ${member.user.username} из чата?`)) return

  try {
    await groupChatStore.removeMember(props.chatId, member.user.id)
    await groupChatStore.loadChatMembers(props.chatId)
    showToast('Пользователь удалён', 'success')
  } catch (error) {
    console.error('Error removing member:', error)
    showToast('Ошибка удаления', 'error')
  }
}

const showBanDialog = (member: any) => {
  banDialog.value.member = {
    ...member,
    chat: { id: props.chatId }
  }
}

const showRestrictDialog = (member: any) => {
  restrictDialog.value.member = {
    ...member,
    chat: { id: props.chatId }
  }
}

const handleUserBanned = async () => {
  await groupChatStore.loadChatMembers(props.chatId)
  await loadBannedUsers()
  showToast('Пользователь заблокирован', 'success')
}

const handleUserRestricted = async () => {
  await groupChatStore.loadChatMembers(props.chatId)
  showToast('Ограничение применено', 'success')
}

const handleUserInvited = async () => {
  await groupChatStore.loadChatMembers(props.chatId)
  showInviteDialog.value = false
  showToast('Пользователь приглашён', 'success')
}

const handleRoleCreated = async () => {
  await groupChatStore.loadChatRoles(props.chatId)
  showCreateRoleDialog.value = false
  showToast('Роль создана', 'success')
}

const handleRoleUpdated = async () => {
  await groupChatStore.loadChatRoles(props.chatId)
  showEditRoleDialog.value = false
  showToast('Роль обновлена', 'success')
}

const editRole = (role: any) => {
  currentEditingRole.value = role
  showEditRoleDialog.value = true
}

const deleteRole = async (role: any) => {
  if (!confirm(`Удалить роль "${role.name}"?`)) return

  try {
    await groupChatStore.deleteChatRole(props.chatId, role.id)
    showToast('Роль удалена', 'success')
  } catch (error) {
    console.error('Error deleting role:', error)
    showToast('Ошибка удаления роли', 'error')
  }
}

const hasMembersWithRole = (role: any) => {
  return members.value.some(member => member.role?.id === role.id)
}

const formatLogDetails = (details: any) => {
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ')
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('ru-RU')
}

const copyInviteLink = async (link: string) => {
  await navigator.clipboard.writeText(link)
  showToast('Ссылка скопирована', 'success')
}

const showToast = (message: string, type: string) => {
  toastMessage.value = message
  toastType.value = type
  setTimeout(() => {
    toastMessage.value = ''
    toastType.value = ''
  }, 3000)
}

const saveSettings = async () => {
  try {
    await groupChatStore.updateGroupChat(props.chatId, {
      name: chatName.value,
      description: chatDescription.value,
      is_public: isPublic.value
    })
    showToast('Настройки сохранены', 'success')
  } catch (error) {
    console.error('Error saving settings:', error)
    showToast('Ошибка сохранения настроек', 'error')
  }
}

// New methods for invite links
const loadInviteLinks = async () => {
  try {
    const response = await chatsApi.inviteLinks.list(props.chatId)
    inviteLinks.value = response.data
  } catch (error) {
    console.error('Error loading invite links:', error)
  }
}

const revokeInviteLink = async (link: any) => {
  if (!confirm('Отозвать эту ссылку?')) return
  
  try {
    await chatsApi.inviteLinks.revoke(link.id)
    await loadInviteLinks()
    showToast('Ссылка отозвана', 'success')
  } catch (error) {
    console.error('Error revoking invite link:', error)
    showToast('Ошибка', 'error')
  }
}

const handleInviteLinkCreated = async () => {
  await loadInviteLinks()
  showCreateInviteLink.value = false
  showToast('Ссылка создана', 'success')
}

// Load join requests
const loadJoinRequests = async () => {
  try {
    const response = await chatsApi.joinRequests.list(props.chatId)
    joinRequests.value = response.data.filter((r: any) => r.status === 'pending')
  } catch (error) {
    console.error('Error loading join requests:', error)
  }
}

const approveJoinRequest = async (request: any) => {
  try {
    await chatsApi.joinRequests.approve(request.id)
    await loadJoinRequests()
    await groupChatStore.loadChatMembers(props.chatId)
    showToast('Запрос одобрен', 'success')
  } catch (error) {
    console.error('Error approving join request:', error)
    showToast('Ошибка', 'error')
  }
}

const rejectJoinRequest = async (request: any) => {
  try {
    await chatsApi.joinRequests.reject(request.id)
    await loadJoinRequests()
    showToast('Запрос отклонён', 'success')
  } catch (error) {
    console.error('Error rejecting join request:', error)
    showToast('Ошибка', 'error')
  }
}

// Load banned users
const loadBannedUsers = async () => {
  try {
    const response = await chatsApi.bans.getBannedUsers(props.chatId)
    bannedUsers.value = response.data.filter((b: any) => b.is_active)
  } catch (error) {
    console.error('Error loading banned users:', error)
  }
}

const unbanUser = async (ban: any) => {
  try {
    await chatsApi.bans.unban(ban.id)
    await loadBannedUsers()
    showToast('Пользователь разблокирован', 'success')
  } catch (error) {
    console.error('Error unbanning user:', error)
    showToast('Ошибка', 'error')
  }
}

const handleSettingsChanged = (data: any) => {
  showToast('Настройки обновлены', 'success')
  // Reload relevant data based on change type
}

// Load data
onMounted(async () => {
  if (currentChat.value?.id !== props.chatId) {
    await groupChatStore.loadChat(props.chatId)
  }
  await groupChatStore.loadChatMembers(props.chatId)
  await groupChatStore.loadChatRoles(props.chatId)
  await groupChatStore.loadAdminLogs(props.chatId)
  
  // Load new data
  await loadInviteLinks()
  await loadJoinRequests()
  await loadBannedUsers()
})
</script>

<style scoped>
.chat-admin-panel {
  @apply bg-white rounded-lg shadow-lg max-h-[80vh] overflow-hidden flex flex-col;
}

.toggle {
  @apply w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2;
}
</style>