/**
 * Утилита для отладки авторизации
 * Вызвать из консоли браузера: window.debugAuth.check()
 */
export const debugAuth = {
  check: () => {
    console.group('🔍 Authorization Debug Info')
    console.log('LocalStorage:', {
      access_token: localStorage.getItem('access_token') ? '✅ Present' : '❌ Missing',
      access_token_preview: localStorage.getItem('access_token')
        ? `${localStorage.getItem('access_token')!.substring(0, 30)}...`
        : 'N/A',
      refresh_token: localStorage.getItem('refresh_token') ? '✅ Present' : '❌ Missing',
      user: localStorage.getItem('user') ? '✅ Present' : '❌ Missing',
    })

    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        
        const payload = token.split('.')[1]
        if (!payload) {
          console.log('⚠️ Invalid token format - no payload part')
        } else {
          const decoded = JSON.parse(atob(payload))
          console.log('Token payload:', decoded)

          
          const now = Math.floor(Date.now() / 1000)
          const isExpired = decoded.exp < now
          console.log('Token expiration:', {
            exp: decoded.exp,
            now,
            expired: isExpired,
            expiresIn: decoded.exp - now
          })
        }
      } catch (e) {
        console.log('⚠️ Could not decode token:', e)
      }
    }

    console.groupEnd()
  },

  clear: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    console.log('✅ Cleared all auth data from localStorage')
  },

  testRequest: async () => {
    const token = localStorage.getItem('access_token')
    console.log('🧪 Testing request with token:', token ? 'Present' : 'Missing')

    if (!token) {
      console.log('❌ No token available for testing')
      return
    }

    try {
      const response = await fetch('/api/users/profile/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Request successful:', data)
      } else {
        const error = await response.json()
        console.log('❌ Request failed:', error)
      }
    } catch (error) {
      console.log('❌ Request error:', error)
    }
  },

  testHeaders: async () => {
    const token = localStorage.getItem('access_token')
    console.log('🔧 Testing headers endpoint with token:', token ? 'Present' : 'Missing')

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/users/headers-debug/', {
        method: 'GET',
        headers
      })

      console.log('Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Headers debug successful:', data)
      } else {
        const error = await response.json()
        console.log('❌ Headers debug failed:', error)
      }
    } catch (error) {
      console.log('❌ Headers debug error:', error)
    }
  },

  testAuthDebug: async () => {
    const token = localStorage.getItem('access_token')
    console.log('🔧 Testing auth debug endpoint with token:', token ? 'Present' : 'Missing')

    if (!token) {
      console.log('❌ No token available for testing')
      return
    }

    try {
      const response = await fetch('/api/users/auth-debug/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Auth debug successful:', data)
      } else {
        const error = await response.json()
        console.log('❌ Auth debug failed:', error)
      }
    } catch (error) {
      console.log('❌ Auth debug error:', error)
    }
  }
}


declare global {
  interface Window {
    debugAuth: typeof debugAuth
  }
}

if (typeof window !== 'undefined') {
  window.debugAuth = debugAuth
}
