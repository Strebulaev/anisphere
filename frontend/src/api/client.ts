import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

// Определяем baseURL для API
let baseURL = import.meta.env.VITE_API_URL

// Если переменная не задана, определяем по окружению
if (!baseURL) {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    baseURL = 'https://anisphere.ru/api'
  } else {
    baseURL = window.location.origin + '/api'
  }
}

// Убираем возможные дублирования /api
baseURL = baseURL.replace(/\/api\/api$/, '/api').replace(/\/\/$/, '/')

console.log('✅ API Base URL:', baseURL)

const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Получение базового URL для медиа файлов
export const getMediaBaseUrl = () => {
  return baseURL.replace(/\/api$/, '')
}

// Функция для получения полного URL медиа файла
export const getMediaUrl = (path: string | null | undefined): string | undefined => {
  if (!path) return undefined
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  const baseUrl = getMediaBaseUrl()
  return `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  console.log('🔑 Request interceptor:', {
    url: config.url,
    method: config.method,
    hasToken: !!token,
    tokenPreview: token ? `${token.substring(0, 20)}...` : 'none'
  })
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('✅ Authorization header set:', {
      header: config.headers.Authorization?.substring(0, 30) + '...'
    })
  } else {
    console.log('⚠️ No token found, request will be unauthenticated')
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    console.log('🔴 Response error:', {
      url: originalRequest?.url,
      status: error.response?.status,
      hasToken: !!localStorage.getItem('access_token'),
      hasRefreshToken: !!localStorage.getItem('refresh_token'),
      isRetry: originalRequest?._retry
    })

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        console.log('🔄 Attempting token refresh...')
        try {
          const response = await axios.post(
            `${baseURL}/users/token/refresh/`,
            { refresh: refreshToken }
          )
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          console.log('✅ Token refreshed successfully')

          return apiClient(originalRequest)
        } catch (refreshError) {
          console.log('❌ Token refresh failed, clearing auth')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_id')
          window.location.href = '/login'
        }
      } else {
        console.log('❌ No refresh token, redirecting to login')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user_id')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export const get = <T>(url: string, config?: AxiosRequestConfig) =>
  apiClient.get<T>(url, config)

export const post = <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  apiClient.post<T>(url, data, config)

export const put = <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  apiClient.put<T>(url, data, config)

export const patch = <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  apiClient.patch<T>(url, data, config)

export const remove = (url: string, config?: AxiosRequestConfig) =>
  apiClient.delete(url, config)

export default apiClient