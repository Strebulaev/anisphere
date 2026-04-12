/**
 * Store для управления подпиской и премиум статусом
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export interface SubscriptionInfo {
  is_active: boolean
  is_premium: boolean
  started_at?: string
  expires_at?: string
  auto_renew: boolean
  payment_method?: string
  days_left?: number
}

export const useSubscriptionStore = defineStore('subscription', () => {
  const subscription = ref<SubscriptionInfo | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Вычисляемые свойства
  const isActive = computed(() => subscription.value?.is_active ?? false)
  const isPremium = computed(() => subscription.value?.is_premium ?? false)
  const daysLeft = computed(() => subscription.value?.days_left ?? 0)
  const expiresAt = computed(() => subscription.value?.expires_at)

  /**
   * Загрузка информации о подписке
   */
  const fetchSubscription = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/users/subscription/')
      subscription.value = response.data
      
      // Синхронизируем с auth store если есть премиум
      if (response.data.is_premium) {
        // Обновляем локальные данные пользователя
        try {
          const userData = localStorage.getItem('user')
          if (userData) {
            const user = JSON.parse(userData)
            user.is_premium = true
            localStorage.setItem('user', JSON.stringify(user))
          }
        } catch (e) {
          console.warn('[Subscription] Failed to update local user data')
        }
      }
      
      return { success: true, data: response.data }
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Ошибка загрузки подписки'
      console.error('[Subscription] Fetch error:', e)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Активация подписки через промокод
   */
  const activateWithPromo = async (promoCode: string) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.post('/users/subscription/activate/', {
        promo_code: promoCode
      })
      
      subscription.value = response.data
      
      return { success: true, data: response.data }
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Ошибка активации подписки'
      console.error('[Subscription] Activate error:', e)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Деактивация подписки
   */
  const deactivateSubscription = async () => {
    loading.value = true
    error.value = null
    
    try {
      await apiClient.post('/users/subscription/deactivate/')
      subscription.value = null
      
      // Обновляем локальные данные
      try {
        const userData = localStorage.getItem('user')
        if (userData) {
          const user = JSON.parse(userData)
          user.is_premium = false
          localStorage.setItem('user', JSON.stringify(user))
        }
      } catch (e) {
        console.warn('[Subscription] Failed to update local user data')
      }
      
      return { success: true }
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Ошибка деактивации подписки'
      console.error('[Subscription] Deactivate error:', e)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  /**
   * Проверка премиум статуса (быстрая, без запроса к API)
   */
  const checkPremiumSync = (): boolean => {
    // Проверяем локальные данные
    try {
      const userData = localStorage.getItem('user')
      if (userData) {
        const user = JSON.parse(userData)
        if (user?.is_premium === true) {
          return true
        }
      }
    } catch (e) {
      // Игнорируем
    }
    
    // Проверяем store
    return subscription.value?.is_premium ?? false
  }

  /**
   * Принудительное обновление премиум статуса
   */
  const refreshPremiumStatus = async () => {
    await fetchSubscription()
    return isPremium.value
  }

  /**
   * Очистка данных
   */
  const reset = () => {
    subscription.value = null
    loading.value = false
    error.value = null
  }

  return {
    // State
    subscription,
    loading,
    error,
    
    // Getters
    isActive,
    isPremium,
    daysLeft,
    expiresAt,
    
    // Actions
    fetchSubscription,
    activateWithPromo,
    deactivateSubscription,
    checkPremiumSync,
    refreshPremiumStatus,
    reset
  }
})
