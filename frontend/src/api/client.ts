import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

let baseURL = import.meta.env.VITE_API_URL

if (!baseURL) {
  baseURL = window.location.origin + '/api'
}

baseURL = baseURL.replace(/\/api\/api$/, '/api').replace(/\/\/$/, '/')

const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, 
  withCredentials: true,
})

export const getMediaBaseUrl = () => {
  return baseURL.replace(/\/api$/, '')
}

export const getMediaUrl = (path: string | null | undefined): string | undefined => {
  if (!path) return undefined
  
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  
  if (import.meta.env.DEV && path.startsWith('/media/')) {
    return path
  }
  
  const baseUrl = getMediaBaseUrl()
  return `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`
}

export const getWebpUrl = (url: string | undefined): string | undefined => {
  if (!url) return undefined
  
  if (url.endsWith('.webp')) return url
  
  if (url.includes('/media/') && 
      (url.endsWith('.png') || url.endsWith('.jpg') || url.endsWith('.jpeg'))) {
    return url.replace(/\.(png|jpg|jpeg)(\?.*)?$/i, '.webp$2')
  }
  
  return url
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

    const status = error.response?.status
    if (status && status >= 500) {
      console.error(`⚠️ API ${status}:`, originalRequest?.url)
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const response = await axios.post(
            `${baseURL}/users/token/refresh/`,
            { refresh: refreshToken }
          )
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          console.log('❌ Token refresh failed, clearing auth')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_id')
          // Редирект только если мы на защищённой странице (не публичной)
          const publicPaths = ['/anime', '/anime/', '/']
          const isPublicPage = publicPaths.some(p => window.location.pathname.startsWith(p))
          if (!isPublicPage) {
            window.location.href = '/login'
          }
        }
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_id')
        const protectedPaths = ['/profile', '/library', '/settings', '/chat']
        const isProtected = protectedPaths.some(p => window.location.pathname.startsWith(p))
        if (isProtected) {
          window.location.href = '/login'
        }
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

export { apiClient }
export default apiClient