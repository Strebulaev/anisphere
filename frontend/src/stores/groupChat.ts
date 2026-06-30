import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

interface GroupChat {
  id: number
  name: string
  description: string
  avatar: string | null
  created_at: string
  created_by: {
    id: number
    username: string
    email: string
  }
  is_public: boolean
  invite_link: string | null
  max_members: number
  members_count: number
  online_count: number
  user_role: {
    is_owner: boolean
    role: ChatRole | null
    custom_title: string
    is_admin: boolean
  } | null
  user_permissions: Record<string, boolean>
}

interface ChatRole {
  id: number
  name: string
  level: number
  color: string
  can_delete_messages: boolean
  can_ban_users: boolean
  can_pin_messages: boolean
  can_add_new_admins: boolean
  can_remain_anonymous: boolean
  can_manage_chat: boolean
  can_manage_video_chats: boolean
  can_restrict_members: boolean
  can_promote_members: boolean
  can_change_chat_info: boolean
  can_invite_users: boolean
  can_post_messages: boolean
  can_edit_messages: boolean
  can_delete_chat: boolean
}

interface ChatMember {
  id: number
  user: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
    status: {
      status: string
      last_seen: string
      custom_status: string
    } | null
  }
  role: ChatRole | null
  is_admin: boolean
  joined_at: string
  custom_title: string
  is_muted: boolean
  muted_until: string | null
  can_send_messages: boolean
  can_send_media: boolean
  can_add_reactions: boolean
  can_send_polls: boolean
  can_change_info: boolean
  can_invite_users: boolean
  can_pin_messages: boolean
  is_banned: boolean
  effective_permissions: Record<string, boolean>
}

interface ChatAdminLog {
  id: number
  chat: number
  user: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
  } | null
  action: string
  action_display: string
  target_user: {
    id: number
    username: string
    first_name: string
    last_name: string
    email: string
  } | null
  message: number | null
  details: Record<string, any>
  created_at: string
}

export const useGroupChatStore = defineStore('groupChat', () => {
  
  const currentChat = ref<GroupChat | null>(null)
  const chatMembers = ref<ChatMember[]>([])
  const chatRoles = ref<ChatRole[]>([])
  const adminLogs = ref<ChatAdminLog[]>([])
  const userPermissions = ref<Record<number, Record<string, boolean>>>({})

  
  const loadingChat = ref(false)
  const loadingMembers = ref(false)
  const loadingRoles = ref(false)
  const loadingLogs = ref(false)

  
  const isOwner = computed(() => currentChat.value?.user_role?.is_owner || false)
  const isAdmin = computed(() => currentChat.value?.user_role?.is_admin || false)
  const currentUserPermissions = computed(() =>
    currentChat.value ? userPermissions.value[currentChat.value.id] || {} : {}
  )

  
  const loadChat = async (chatId: number) => {
    loadingChat.value = true
    try {
      const response = await apiClient.get(`/social/group-chats/${chatId}/`)
      currentChat.value = response.data
      if (currentChat.value) {
        userPermissions.value[currentChat.value.id] = currentChat.value.user_permissions
      }
    } catch (error) {
      console.error('Error loading group chat:', error)
      throw error
    } finally {
      loadingChat.value = false
    }
  }

  const loadChatMembers = async (chatId: number) => {
    loadingMembers.value = true
    try {
      const response = await apiClient.get(`/social/group-chats/${chatId}/members/`)
      const data = response.data as ChatMember[] | { results: ChatMember[] }
      chatMembers.value = 'results' in data ? data.results : data
    } catch (error) {
      console.error('Error loading chat members:', error)
      throw error
    } finally {
      loadingMembers.value = false
    }
  }

  const loadChatRoles = async (chatId: number) => {
    loadingRoles.value = true
    try {
      const response = await apiClient.get(`/social/group-chats/${chatId}/roles/`)
      const data = response.data as ChatRole[] | { results: ChatRole[] }
      chatRoles.value = 'results' in data ? data.results : data
    } catch (error) {
      console.error('Error loading chat roles:', error)
      throw error
    } finally {
      loadingRoles.value = false
    }
  }

  const loadAdminLogs = async (chatId: number) => {
    loadingLogs.value = true
    try {
      const response = await apiClient.get(`/social/group-chats/${chatId}/admin-logs/`)
      const data = response.data as ChatAdminLog[] | { results: ChatAdminLog[] }
      adminLogs.value = 'results' in data ? data.results : data
    } catch (error) {
      console.error('Error loading admin logs:', error)
      throw error
    } finally {
      loadingLogs.value = false
    }
  }

  const createGroupChat = async (data: {
    name: string
    description?: string
    is_public?: boolean
  }) => {
    try {
      const response = await apiClient.post('/social/group-chats/', data)
      return response.data
    } catch (error) {
      console.error('Error creating group chat:', error)
      throw error
    }
  }

  const updateGroupChat = async (chatId: number, data: Partial<GroupChat>) => {
    try {
      const response = await apiClient.patch(`/social/group-chats/${chatId}/`, data)
      if (currentChat.value && currentChat.value.id === chatId) {
        currentChat.value = { ...currentChat.value, ...response.data }
      }
      return response.data
    } catch (error) {
      console.error('Error updating group chat:', error)
      throw error
    }
  }

  const deleteGroupChat = async (chatId: number) => {
    try {
      await apiClient.delete(`/social/group-chats/${chatId}/`)
      if (currentChat.value && currentChat.value.id === chatId) {
        currentChat.value = null
      }
    } catch (error) {
      console.error('Error deleting group chat:', error)
      throw error
    }
  }

  const inviteUser = async (chatId: number, userId: number, message?: string) => {
    try {
      const response = await apiClient.post(`/social/group-chats/${chatId}/invite_user/`, {
        user_id: userId,
        message: message || ''
      })
      return response.data
    } catch (error) {
      console.error('Error inviting user:', error)
      throw error
    }
  }

  const removeMember = async (chatId: number, userId: number, reason?: string) => {
    try {
      await apiClient.post(`/social/group-chats/${chatId}/remove_member/`, {
        user_id: userId,
        reason: reason || ''
      })
    } catch (error) {
      console.error('Error removing member:', error)
      throw error
    }
  }

  const banUser = async (chatId: number, userId: number, reason?: string, untilDate?: string) => {
    try {
      await apiClient.post(`/social/group-chats/${chatId}/ban_user/`, {
        user_id: userId,
        reason: reason || '',
        until_date: untilDate
      })
    } catch (error) {
      console.error('Error banning user:', error)
      throw error
    }
  }

  const updateMemberRole = async (chatId: number, userId: number, roleId: number | null) => {
    try {
      const response = await apiClient.post(`/social/group-chats/${chatId}/set_member_role/`, {
        user_id: userId,
        role_id: roleId
      })
      return response.data
    } catch (error) {
      console.error('Error updating member role:', error)
      throw error
    }
  }

  const createChatRole = async (chatId: number, roleData: Partial<ChatRole>) => {
    try {
      const response = await apiClient.post(`/social/group-chats/${chatId}/roles/`, roleData)
      chatRoles.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Error creating chat role:', error)
      throw error
    }
  }

  const updateChatRole = async (chatId: number, roleId: number, roleData: Partial<ChatRole>) => {
    try {
      const response = await apiClient.patch(`/social/group-chats/${chatId}/roles/${roleId}/`, roleData)
      const index = chatRoles.value.findIndex(role => role.id === roleId)
      if (index !== -1) {
        chatRoles.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Error updating chat role:', error)
      throw error
    }
  }

  const deleteChatRole = async (chatId: number, roleId: number) => {
    try {
      await apiClient.delete(`/social/group-chats/${chatId}/roles/${roleId}/`)
      chatRoles.value = chatRoles.value.filter(role => role.id !== roleId)
    } catch (error) {
      console.error('Error deleting chat role:', error)
      throw error
    }
  }

  const toggleMemberMute = async (chatId: number, userId: number, muted: boolean) => {
    
    
    const member = chatMembers.value.find(m => m.user.id === userId)
    if (member) {
      member.is_muted = muted
      if (!muted) {
        member.muted_until = null
      }
    }
  }

  const leaveChat = async (chatId: number) => {
    
    
    if (currentChat.value && currentChat.value.id === chatId) {
      currentChat.value = null
    }
    chatMembers.value = []
    chatRoles.value = []
    adminLogs.value = []
  }

  
  const loadGroupChats = async () => {
    loadingChat.value = true
    try {
      const response = await apiClient.get('/social/group-chats/')
      const data = response.data.results || response.data
      
      localStorage.setItem('groupChats', JSON.stringify(data))
      
      window.dispatchEvent(new CustomEvent('groupChatsUpdated', { detail: data }))
      return data
    } catch (error) {
      console.error('Error loading group chats:', error)
      return []
    } finally {
      loadingChat.value = false
    }
  }

  
  const hasPermission = (permission: string): boolean => {
    return currentUserPermissions.value[permission] || false
  }

  const canManageChat = (): boolean => {
    return hasPermission('can_manage_chat') || isOwner.value
  }

  const canBanUsers = (): boolean => {
    return hasPermission('can_ban_users') || isOwner.value
  }

  const canInviteUsers = (): boolean => {
    return hasPermission('can_invite_users') || isOwner.value
  }

  const canDeleteMessages = (): boolean => {
    return hasPermission('can_delete_messages') || isOwner.value
  }

  const canChangeChatInfo = (): boolean => {
    return hasPermission('can_change_chat_info') || isOwner.value
  }

  const canPinMessages = (): boolean => {
    return hasPermission('can_pin_messages') || isOwner.value
  }

  const canPromoteMembers = (): boolean => {
    return hasPermission('can_promote_members') || isOwner.value
  }

  return {
    
    currentChat,
    chatMembers,
    chatRoles,
    adminLogs,
    userPermissions,
    loadingChat,
    loadingMembers,
    loadingRoles,
    loadingLogs,

    
    isOwner,
    isAdmin,
    currentUserPermissions,

    
    loadChat,
    loadChatMembers,
    loadChatRoles,
    loadAdminLogs,
    loadGroupChats,
    createGroupChat,
    updateGroupChat,
    deleteGroupChat,
    inviteUser,
    removeMember,
    banUser,
    updateMemberRole,
    createChatRole,
    updateChatRole,
    deleteChatRole,
    toggleMemberMute,
    leaveChat,

    
    hasPermission,
    canManageChat,
    canBanUsers,
    canInviteUsers,
    canDeleteMessages,
    canChangeChatInfo,
    canPinMessages,
    canPromoteMembers
  }
})