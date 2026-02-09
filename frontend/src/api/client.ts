import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

let baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

if (baseURL.endsWith('/api/api')) {
  baseURL = baseURL.replace(/\/api\/api$/, '/api')
}
const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Получение базового URL для медиа файлов
export const getMediaBaseUrl = () => {
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  return apiBase.replace(/\/api$/, '')
}

// Функция для получения полного URL медиа файла
export const getMediaUrl = (path: string | null | undefined): string | null => {
  if (!path) return null
  // Если путь уже полный URL (http:// или https://), возвращаем как есть
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // Иначе формируем полный URL
  const baseUrl = getMediaBaseUrl()
  return `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const response = await axios.post(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/users/token/refresh/`,
            { refresh: refreshToken }
          )
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`

          return apiClient(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_id')
          window.location.href = '/login'
        }
      } else {
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
