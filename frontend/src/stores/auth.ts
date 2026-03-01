import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  nickname?: string
  display_name?: string
  avatar?: string
  avatar_url?: string
  level: number
  experience: number
  is_online: boolean
  email_verified: boolean
  phone_verified: boolean
  two_factor_enabled: boolean
  created_at: string
  last_login: string
  phone_number?: string
  followers_count?: number
  following_count?: number
  playlists_count?: number
  is_verified?: boolean
  is_premium?: boolean
  competition_wins?: number
  following?: number[]
  favorite_genres?: number[]
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const router = useRouter()

  // Login function
  const login = async (username: string, password: string) => {
    try {
      console.log('🔑 Auth Store: Attempting login for', username)

      const response = await apiClient.post('/users/login/', {
        username,
        password
      })

      const { user: userData, tokens } = response.data
      
      console.log('✅ Login response received', {
        hasAccessToken: !!tokens?.access,
        hasRefreshToken: !!tokens?.refresh,
        accessTokenPreview: tokens?.access ? `${tokens.access.substring(0, 20)}...` : 'none',
        user: userData?.username
      })

      // Store tokens
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))

      console.log('💾 Tokens saved to localStorage')

      // Update state
      user.value = userData
      isAuthenticated.value = true

      console.log('✅ Auth Store: Login successful', userData)
      return { success: true, user: userData }
    } catch (error: any) {
      console.error('❌ Auth Store: Login failed', error)
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'Неверные учетные данные'
      return { success: false, error: errorMessage }
    }
  }

  // Register function
  const register = async (data: {
    username: string
    email: string
    password: string
    password_confirm: string
    first_name: string
    last_name: string
    nickname?: string
  }) => {
    try {
      await apiClient.post('/users/register/', data)
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Registration failed', error)
      const errorMessage = error.response?.data?.password?.[0] || 
                          error.response?.data?.username?.[0] || 
                          error.response?.data?.email?.[0] || 
                          'Ошибка регистрации'
      return { success: false, error: errorMessage }
    }
  }

  // Google OAuth
  const googleLogin = async (idToken: string) => {
    try {
      const response = await apiClient.post('/users/google/', {
        id_token: idToken
      })
      const { user: userData, tokens } = response.data
      
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))
      
      user.value = userData
      isAuthenticated.value = true
      
      return { success: true, user: userData }
    } catch (error: any) {
      console.error('Auth Store: Google login failed', error)
      return { success: false, error: 'Ошибка входа через Google' }
    }
  }

  // Phone verification
  const verifyPhone = async (phoneNumber: string, action: 'send' | 'verify', code?: string) => {
    try {
      const response = await apiClient.post('/users/verify/phone/', {
        phone_number: phoneNumber,
        action,
        ...(code && { code })
      })
      return { success: true, data: response.data }
    } catch (error: any) {
      console.error('Auth Store: Phone verification failed', error)
      return { success: false, error: error.response?.data?.error || 'Ошибка верификации телефона' }
    }
  }

  // Email verification
  const verifyEmail = async (email: string, action: 'send' | 'verify', code?: string) => {
    try {
      const response = await apiClient.post('/users/verify/email/', {
        email: email,
      })
      return { success: true, data: response.data }
    } catch (error: any) {
      console.error('Auth Store: Email verification failed', error)
      return { success: false, error: error.response?.data?.error || 'Ошибка верификации email' }
    }
  }

  // Logout function
  const logout = async () => {
    try {
      await apiClient.post('/users/logout/')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local storage and state
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      
      user.value = null
      isAuthenticated.value = false
      
      router.push('/login')
    }
  }

  // Fetch user data
  const fetchUser = async () => {
    try {
      console.log('👤 Auth Store: fetchUser called')
      const response = await apiClient.get('/users/profile/')
      console.log('✅ Auth Store: fetchUser successful, user data:', response.data.username)
      user.value = response.data
      isAuthenticated.value = true
      return { success: true, user: response.data }
    } catch (error: any) {
      console.error('❌ Auth Store: fetchUser failed:', error)
      console.log('❌ Auth Store: error response:', error.response?.data)

      // If unauthorized, clear auth state
      if (error.response?.status === 401) {
        console.log('❌ Auth Store: 401 response, calling logout')
        // Don't call logout here to avoid redirect loop, let the caller handle it
      }
      
      return { success: false, error: error.message }
    }
  }

  // Password reset
  const passwordReset = async (email: string) => {
    try {
      await apiClient.post('/users/password-reset/', { email })
      return { success: true, message: 'Новый пароль отправлен на email' }
    } catch (error: any) {
      console.error('Auth Store: Password reset failed', error)
      return { success: false, error: 'Ошибка сброса пароля' }
    }
  }

  // Update profile
  const updateProfile = async (profileData: FormData | object) => {
    try {
      const response = await apiClient.patch('/users/profile/', profileData)
      user.value = response.data
      return { success: true, user: response.data }
    } catch (error: any) {
      console.error('Auth Store: Profile update failed', error)
      return { success: false, error: 'Ошибка обновления профиля' }
    }
  }

  // Change password
  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      const response = await apiClient.post('/users/change-password/', {
        current_password: currentPassword,
        new_password: newPassword
      })
      return { success: true, data: response.data }
    } catch (error: any) {
      console.error('Auth Store: Change password failed', error)
      const errorMessage = error.response?.data?.detail || 'Ошибка смены пароля'
      return { success: false, error: errorMessage }
    }
  }

  // Check nickname availability
  const checkNickname = async (nickname: string) => {
    try {
      const response = await apiClient.post('/users/nickname/check/', { nickname })
      return { available: true, message: response.data.message }
    } catch (error: any) {
      return { 
        available: false, 
        error: error.response?.data?.error || 'Nickname недоступен' 
      }
    }
  }

  // Get user sessions
  const getUserSessions = async () => {
    try {
      const response = await apiClient.get('/users/sessions/')
      return { success: true, sessions: response.data }
    } catch (error: any) {
      console.error('Auth Store: Get sessions failed', error)
      return { success: false, error: 'Ошибка получения сессий' }
    }
  }

  // Revoke session
  const revokeSession = async (sessionId: number) => {
    try {
      await apiClient.delete(`/users/sessions/${sessionId}/`)
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Revoke session failed', error)
      return { success: false, error: 'Ошибка завершения сессии' }
    }
  }

  // Get user settings
  const getUserSettings = async () => {
    try {
      const response = await apiClient.get('/users/settings/')
      return { success: true, settings: response.data }
    } catch (error: any) {
      console.error('Auth Store: Get settings failed', error)
      return { success: false, error: 'Ошибка получения настроек' }
    }
  }

  // Update user settings
  const updateUserSettings = async (settings: object) => {
    try {
      const response = await apiClient.patch('/users/settings/', settings)
      return { success: true, settings: response.data }
    } catch (error: any) {
      console.error('Auth Store: Update settings failed', error)
      return { success: false, error: 'Ошибка обновления настроек' }
    }
  }

  // Two-factor authentication
  const setupTwoFactor = async (action: 'enable' | 'disable' | 'verify', code?: string) => {
    try {
      const response = await apiClient.post('/users/two-factor/', {
        action,
        ...(code && { code })
      })
      return { success: true, data: response.data }
    } catch (error: any) {
      console.error('Auth Store: 2FA setup failed', error)
      return { success: false, error: error.response?.data?.error || 'Ошибка настройки 2FA' }
    }
  }

  // Check if running in local development mode
  const isLocalDevelopment = () => {
    const hostname = window.location.hostname
    return  hostname === '127.0.0.1' || hostname === '::1'
  }

  // Check authentication status
  const checkAuth = async () => {
    // Skip auth checks in local development mode
    if (isLocalDevelopment()) {
      console.log('🔓 Local development mode: Auth check skipped')
      // Set a mock user for development
      if (!user.value) {
        user.value = {
          id: 1,
          username: 'dev_user',
          email: 'dev@example.com',
          first_name: 'Developer',
          last_name: 'User',
          level: 5,
          experience: 1000,
          is_online: true,
          email_verified: true,
          phone_verified: false,
          two_factor_enabled: false,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString(),
        }
        isAuthenticated.value = true
      }
      return { success: true }
    }

    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    const userData = localStorage.getItem('user')

    console.log('🔐 Auth Store: checkAuth called', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      hasUserData: !!userData,
      tokenPreview: accessToken ? `${accessToken.substring(0, 20)}...` : 'none'
    })

    if (accessToken) {
      try {
        // Set token for requests
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
        console.log('✅ Set Authorization header for requests')
        
        // Try to fetch user data
        await fetchUser()
        console.log('✅ User data fetched successfully')
        
        return { success: true }
      } catch (error: any) {
        console.log('⚠️ Auth Store: Token validation failed, attempting refresh', error.response?.status)

        if (refreshToken) {
          try {
            // Пытаемся обновить токен
            const refreshResponse = await apiClient.post('/users/token/refresh/', {
              refresh: refreshToken
            })

            const { access } = refreshResponse.data
            console.log('✅ Token refreshed successfully')
            
            // Update stored tokens
            localStorage.setItem('access_token', access)
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`
            
            // Retry user fetch
            await fetchUser()
            console.log('✅ User data fetched after refresh')
            
            return { success: true }
          } catch (refreshError) {
            console.log('❌ Auth Store: Refresh failed, clearing auth', refreshError)
            logout()
            return { success: false }
          }
        } else {
          console.log('❌ Auth Store: No refresh token, clearing auth')
          logout()
          return { success: false }
        }
      }
    } else {
      console.log('ℹ️ Auth Store: No access token found')
      return { success: false }
    }
  }

  // Initialize auth state from localStorage
  const initializeAuth = () => {
    // Skip initialization in local development mode - checkAuth will handle it
    if (isLocalDevelopment()) {
      console.log('🔓 Local development mode: Auth initialization skipped')
      return
    }

    const accessToken = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')

    if (accessToken && userData) {
      try {
        user.value = JSON.parse(userData)
        isAuthenticated.value = true
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
        
        // Verify token is still valid
        checkAuth()
      } catch (error) {
        console.error('Auth Store: Failed to parse stored user data', error)
        logout()
      }
    }
  }

  // Follow user
  const followUser = async (userId: number) => {
    try {
      await apiClient.post(`/users/${userId}/follow`)
      if (user.value) {
        user.value.following_count = (user.value.following_count || 0) + 1
      }
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Follow failed', error)
      return { success: false, error: 'Ошибка подписки' }
    }
  }

  // Unfollow user
  const unfollowUser = async (userId: number) => {
    try {
      await apiClient.delete(`/users/${userId}/follow`)
      if (user.value) {
        user.value.following_count = Math.max(0, (user.value.following_count || 0) - 1)
      }
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Unfollow failed', error)
      return { success: false, error: 'Ошибка отписки' }
    }
  }

  // Block user
  const blockUser = async (userId: number) => {
    try {
      await apiClient.post(`/users/${userId}/block`)
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Block failed', error)
      return { success: false, error: 'Ошибка блокировки' }
    }
  }

  // Unblock user
  const unblockUser = async (userId: number) => {
    try {
      await apiClient.delete(`/users/${userId}/block`)
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Unblock failed', error)
      return { success: false, error: 'Ошибка разблокировки' }
    }
  }

  // Report user
  const reportUser = async (userId: number, reason: string) => {
    try {
      await apiClient.post(`/users/${userId}/report`, { reason })
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Report failed', error)
      return { success: false, error: 'Ошибка отправки жалобы' }
    }
  }

  // Upload avatar
  const uploadAvatar = async (file: File): Promise<string> => {
    try {
      const formData = new FormData()
      formData.append('avatar', file)

      const response = await apiClient.post<{ avatar_url: string }>('/users/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (user.value) {
        user.value.avatar = response.data.avatar_url
        localStorage.setItem('user', JSON.stringify(user.value))
      }

      return response.data.avatar_url
    } catch (error: any) {
      console.error('Auth Store: Upload avatar failed', error)
      throw error
    }
  }

  // Remove avatar
  const removeAvatar = async () => {
    try {
      await apiClient.delete('/users/avatar')
      if (user.value) {
        user.value.avatar = undefined
        localStorage.setItem('user', JSON.stringify(user.value))
      }
      return { success: true }
    } catch (error: any) {
      console.error('Auth Store: Remove avatar failed', error)
      return { success: false, error: 'Ошибка удаления аватара' }
    }
  }

  // Update privacy settings
  const updatePrivacySettings = async (settings: any) => {
    try {
      const response = await apiClient.patch('/users/privacy', settings)
      if (user.value) {
        user.value = { ...user.value, ...response.data }
        localStorage.setItem('user', JSON.stringify(user.value))
      }
      return { success: true, user: response.data }
    } catch (error: any) {
      console.error('Auth Store: Update privacy settings failed', error)
      return { success: false, error: 'Ошибка обновления настроек приватности' }
    }
  }

  // Online status management
  const onlineUsers = ref<Map<number, { is_online: boolean; last_seen?: string }>>(new Map())

  const updateUserOnlineStatus = (userId: number, isOnline: boolean) => {
    onlineUsers.value.set(userId, { is_online: isOnline })
    // Диспатчим событие для обновления UI
    window.dispatchEvent(new CustomEvent('userOnlineStatusChanged', { 
      detail: { userId, isOnline } 
    }))
  }

  const isUserOnline = (userId: number): boolean => {
    return onlineUsers.value.get(userId)?.is_online ?? false
  }

  // Friends / Followers
  const friendRequests = ref<any[]>([])
  const loadingFriendRequests = ref(false)

  const loadFriendRequests = async () => {
    loadingFriendRequests.value = true
    try {
      const response = await apiClient.get('/social/follows/requests/')
      friendRequests.value = response.data.results || response.data
      return friendRequests.value
    } catch (error) {
      console.error('Error loading friend requests:', error)
      return []
    } finally {
      loadingFriendRequests.value = false
    }
  }

  const acceptFriendRequest = async (requestId: number) => {
    try {
      await apiClient.post(`/social/follows/requests/${requestId}/accept/`)
      friendRequests.value = friendRequests.value.filter(r => r.id !== requestId)
      return { success: true }
    } catch (error: any) {
      console.error('Error accepting friend request:', error)
      return { success: false, error: 'Ошибка принятия запроса' }
    }
  }

  const rejectFriendRequest = async (requestId: number) => {
    try {
      await apiClient.post(`/social/follows/requests/${requestId}/reject/`)
      friendRequests.value = friendRequests.value.filter(r => r.id !== requestId)
      return { success: true }
    } catch (error: any) {
      console.error('Error rejecting friend request:', error)
      return { success: false, error: 'Ошибка отклонения запроса' }
    }
  }

  // Get token
  const token = computed(() => localStorage.getItem('access_token'))

  return {
    user,
    isAuthenticated,
    loading,
    token,
    login,
    register,
    googleLogin,
    verifyPhone,
    verifyEmail,
    logout,
    fetchUser,
    passwordReset,
    updateProfile,
    changePassword,
    checkNickname,
    getUserSessions,
    revokeSession,
    getUserSettings,
    updateUserSettings,
    setupTwoFactor,
    checkAuth,
    initializeAuth,
    followUser,
    unfollowUser,
    blockUser,
    unblockUser,
    reportUser,
    uploadAvatar,
    removeAvatar,
    updatePrivacySettings,
    onlineUsers,
    updateUserOnlineStatus,
    isUserOnline,
    friendRequests,
    loadFriendRequests,
    acceptFriendRequest,
    rejectFriendRequest
  }
})