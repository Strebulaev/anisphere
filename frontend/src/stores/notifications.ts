import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export interface Notification {
  id: number
  kind: string
  text: string
  url?: string
  is_read: boolean
  created_at: string
}

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)

  const hasUnread = computed(() => unreadCount.value > 0)

  async function fetchNotifications() {
    loading.value = true
    try {
      const { data } = await apiClient.get<{ results: Notification[]; count: number }>('/notifications/')
      notifications.value = data.results
      unreadCount.value = data.results.filter(n => !n.is_read).length
    } catch {
      // ignore
    } finally {
      loading.value = false
    }
  }

  async function markAllRead() {
    try {
      await apiClient.post('/notifications/mark-all-read/')
      notifications.value.forEach(n => (n.is_read = true))
      unreadCount.value = 0
    } catch {
      // ignore
    }
  }

  async function markRead(id: number) {
    try {
      await apiClient.post(`/notifications/${id}/read/`)
      const n = notifications.value.find(n => n.id === id)
      if (n && !n.is_read) {
        n.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // ignore
    }
  }

  function addNotification(notification: Notification) {
    notifications.value.unshift(notification)
    if (!notification.is_read) unreadCount.value++
  }

  return {
    notifications,
    unreadCount,
    loading,
    hasUnread,
    fetchNotifications,
    markAllRead,
    markRead,
    addNotification,
  }
})
