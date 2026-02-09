import { ref } from 'vue'
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
  level: number
  experience: number
  is_online: boolean
  email_verified: boolean
  phone_verified: boolean
  two_factor_enabled: boolean
  created_at: string
  last_login: string
  phone_number?: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const router = useRouter()

  // Login function
  const login = async (username: string, password: string) => {
    try {
      console.log('Auth Store: Attempting login for', username)
      
      const response = await apiClient.post('/users/login/', {
        username,
        password
      })

      const { user: userData, tokens } = response.data
      
      // Store tokens
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      localStorage.setItem('user', JSON.stringify(userData))

      // Update state
      user.value = userData
      isAuthenticated.value = true

      console.log('Auth Store: Login successful', userData)
      return { success: true, user: userData }
    } catch (error: any) {
      console.error('Auth Store: Login failed', error)
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
      console.log('Auth Store: fetchUser called')
      const response = await apiClient.get('/users/profile/')
      console.log('Auth Store: fetchUser successful, user data:', response.data)
      user.value = response.data
      isAuthenticated.value = true
      return { success: true, user: response.data }
    } catch (error: any) {
      console.error('Auth Store: fetchUser failed:', error)
      console.log('Auth Store: error response:', error.response?.data)
      
      // If unauthorized, clear auth state
      if (error.response?.status === 401) {
        logout()
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

  // Check authentication status
  const checkAuth = async () => {
    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    const userData = localStorage.getItem('user')

    console.log('Auth Store: checkAuth called, token exists:', !!accessToken)

    if (accessToken) {
      try {
        // Set token for requests
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
        
        // Try to fetch user data
        await fetchUser()
        
        return { success: true }
      } catch (error: any) {
        console.log('Auth Store: Token validation failed, attempting refresh')
        
        if (refreshToken) {
          try {
            // Пытаемся обновить токен
            const refreshResponse = await apiClient.post('/users/token/refresh/', {
              refresh: refreshToken
            })

            const { access } = refreshResponse.data
            
            // Update stored tokens
            localStorage.setItem('access_token', access)
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`
            
            // Retry user fetch
            await fetchUser()
            
            return { success: true }
          } catch (refreshError) {
            console.log('Auth Store: Refresh failed, clearing auth')
            logout()
            return { success: false }
          }
        } else {
          console.log('Auth Store: No refresh token, clearing auth')
          logout()
          return { success: false }
        }
      }
    } else {
      console.log('Auth Store: No access token found')
      return { success: false }
    }
  }

  // Initialize auth state from localStorage
  const initializeAuth = () => {
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

  return {
    user,
    isAuthenticated,
    loading,
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
    initializeAuth
  }
})