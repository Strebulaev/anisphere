import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import notificationsApi from '@/api/notifications'
import type { NotificationItem, NotificationSettings } from '@/api/notifications'

export type { NotificationItem as Notification }

export interface Reminder {
  id: number
  anime: number
  anime_detail: {
    id: number
    title_ru: string
    title_en: string
    poster: string | null
    poster_url?: string
  }
  reminder_time: string
  repeat_weekly: boolean
  comment: string
  enable_sound: boolean
  enable_push: boolean
  is_active: boolean
  is_triggered: boolean
  created_at: string
}

export const useNotificationStore = defineStore('notifications', () => {
  const notifications   = ref<NotificationItem[]>([])
  const recentNotifications = ref<NotificationItem[]>([]) 
  const reminders       = ref<Reminder[]>([])
  const unreadCount     = ref(0)
  const flashingCount   = ref(0) 
  const loading         = ref(false)
  const loadingMore     = ref(false)
  const hasMore         = ref(true)
  const currentPage     = ref(1)
  const settings        = ref<NotificationSettings | null>(null)

  const ringingReminderIds = ref<number[]>([])
  
  const isBellRinging = computed(() => {
    if (flashingCount.value > 0) return true
    if (ringingReminderIds.value.length > 0) return true
    return false
  })

  const _ringTimers = new Map<number, ReturnType<typeof setTimeout>>()

  function startRinging(reminderId: number) {
    if (!ringingReminderIds.value.includes(reminderId)) {
      ringingReminderIds.value = [...ringingReminderIds.value, reminderId]
    }

    const t = setTimeout(() => {
      stopRinging(reminderId)
    }, 60_000)
    _ringTimers.set(reminderId, t)
  }

  function stopRinging(reminderId: number) {
    const t = _ringTimers.get(reminderId)
    if (t) { clearTimeout(t); _ringTimers.delete(reminderId) }
    ringingReminderIds.value = ringingReminderIds.value.filter(id => id !== reminderId)
  }

  function isReminderRinging(reminderId: number): boolean {
    return ringingReminderIds.value.includes(reminderId)
  }

  let ws: WebSocket | null = null
  let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
  let wsReconnectDelay = 2000

  const hasUnread = computed(() => unreadCount.value > 0)

  async function fetchNotifications(reset = true) {
    if (reset) {
      loading.value = true
      currentPage.value = 1
      hasMore.value = true
    } else {
      loadingMore.value = true
    }

    try {
      const { data } = await notificationsApi.list({
        page: currentPage.value,
        page_size: 20,
      })

      const list: NotificationItem[] = Array.isArray(data)
        ? data
        : (data as any).results ?? []

      if (reset) {
        notifications.value = list
      } else {
        const existing = new Set(notifications.value.map(n => n.id))
        notifications.value = [...notifications.value, ...list.filter(n => !existing.has(n.id))]
      }

      const pageData = data as any
      hasMore.value = !!pageData.next

      unreadCount.value = notifications.value.filter(n => !n.is_read).length
      flashingCount.value = notifications.value.filter(n => (n as any).is_flashing).length
    } catch (e) {
      console.error('Error fetching notifications:', e)
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  async function fetchRecent() {
    try {
      const { data } = await notificationsApi.recent()
      unreadCount.value = data.unread_count
      flashingCount.value = data.flashing_count || 0
      recentNotifications.value = data.results.slice(0, 5)
      const existing = new Set(notifications.value.map(n => n.id))
      const fresh = data.results.filter(n => !existing.has(n.id))
      if (fresh.length) {
        notifications.value = [...fresh, ...notifications.value]
      }
      return data.results
    } catch (e) {
      return []
    }
  }

  async function fetchCount() {
    try {
      const { data } = await notificationsApi.count()
      unreadCount.value = data.count
      flashingCount.value = data.flashing_count || 0
    } catch {}
  }

  async function loadMoreNotifications() {
    if (loadingMore.value || !hasMore.value) return
    currentPage.value++
    await fetchNotifications(false)
  }

  async function markRead(id: number) {
    const n = notifications.value.find(n => n.id === id)
    if (!n || n.is_read) return
    try {
      await notificationsApi.markRead(id)
      n.is_read = true
      ;(n as any).is_flashing = false
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      flashingCount.value = Math.max(0, flashingCount.value - 1)
    } catch (e) {
      console.error('markRead error:', e)
    }
  }

  async function markAllRead() {
    try {
      await notificationsApi.markAllRead()
      notifications.value.forEach(n => {
        n.is_read = true
        ;(n as any).is_flashing = false
      })
      unreadCount.value = 0
      flashingCount.value = 0
    } catch (e) {
      console.error('markAllRead error:', e)
    }
  }

  async function toggleImportant(id: number) {
    const n = notifications.value.find(n => n.id === id)
    if (!n) return
    try {
      const { data } = await notificationsApi.toggleImportant(id)
      n.is_important = data.is_important
    } catch (e) {
      console.error('toggleImportant error:', e)
    }
  }

  async function deleteNotification(id: number) {
    try {
      await notificationsApi.delete(id)
      const n = notifications.value.find(n => n.id === id)
      notifications.value = notifications.value.filter(n => n.id !== id)
      unreadCount.value = notifications.value.filter(n => !n.is_read).length
      if (n && (n as any).is_flashing) {
        flashingCount.value = Math.max(0, flashingCount.value - 1)
      }
    } catch (e) {
      console.error('deleteNotification error:', e)
    }
  }

  async function cleanReadNotifications() {
    try {
      await notificationsApi.cleanRead()
      notifications.value = notifications.value.filter(n => !n.is_read || n.is_important)
    } catch (e) {
      console.error('cleanRead error:', e)
    }
  }

  async function deleteAllNotifications() {
    try {
      await notificationsApi.deleteAll()
      notifications.value = notifications.value.filter(n => n.is_important)
    } catch (e) {
      console.error('deleteAll error:', e)
    }
  }

  function addNotification(notification: NotificationItem) {
    if (!notifications.value.some(n => n.id === notification.id)) {
      notifications.value.unshift(notification)
    }
    if (!recentNotifications.value.some(n => n.id === notification.id)) {
      recentNotifications.value = [notification, ...recentNotifications.value].slice(0, 5)
    }
    if (!notification.is_read) unreadCount.value++
    if ((notification as any).is_flashing) {
      flashingCount.value++
    }
  }

  async function fetchReminders() {
    try {
      const { default: apiClient } = await import('@/api/client')
      const { data } = await apiClient.get('/notifications/reminders/', { params: { page_size: 50 } })
      reminders.value = Array.isArray(data) ? data : (data.results ?? [])
    } catch (e) {
      console.error('fetchReminders error:', e)
    }
  }

  async function createReminder(payload: {
    anime_id: number
    reminder_time: string
    repeat_weekly?: boolean
    comment?: string
  }) {
    const { default: apiClient } = await import('@/api/client')
    const { data } = await apiClient.post('/notifications/reminders/', payload)
    reminders.value.unshift(data)
    return data
  }

  async function deleteReminder(id: number) {
    const { default: apiClient } = await import('@/api/client')
    await apiClient.delete(`/notifications/reminders/${id}/`)
    reminders.value = reminders.value.filter(r => r.id !== id)
  }

  async function deactivateReminder(id: number) {
    const { default: apiClient } = await import('@/api/client')
    await apiClient.post(`/notifications/reminders/${id}/deactivate/`)
    const r = reminders.value.find(r => r.id === id)
    if (r) r.is_active = false
  }

  async function acknowledgeReminder(id: number) {
    const { default: apiClient } = await import('@/api/client')
    await apiClient.post(`/notifications/reminders/${id}/acknowledge/`)
    const r = reminders.value.find(r => r.id === id)
    if (r) r.is_triggered = false
    stopRinging(id)
  }

  async function checkAndTriggerReminders() {
    try {
      const { default: apiClient } = await import('@/api/client')
      const { data } = await apiClient.post('/notifications/reminders/check_and_trigger/')
      
      if (data.triggered_count > 0) {
        await fetchReminders()
        
        data.triggered_ids.forEach((id: number) => {
          startRinging(id)
        })
        
        await fetchRecent()
        
        try {
          const audio = new Audio('/sounds/notification.mp3')
          audio.volume = 0.5
          audio.play().catch(() => {})
        } catch {}
      }
      return data
    } catch (e) {
      console.error('checkAndTriggerReminders error:', e)
      return { triggered_count: 0, triggered_ids: [] }
    }
  }

  const upcomingReminders = computed(() =>
    reminders.value
      .filter(r => r.is_active)
      .sort((a, b) => new Date(a.reminder_time).getTime() - new Date(b.reminder_time).getTime())
      .slice(0, 10)
  )

  const allActiveReminders = computed(() =>
    reminders.value
      .filter(r => r.is_active)
      .sort((a, b) => new Date(b.reminder_time).getTime() - new Date(a.reminder_time).getTime())
  )

  async function fetchSettings() {
    try {
      const { data } = await notificationsApi.getSettings()
      settings.value = data
    } catch (e) {
      console.error('fetchSettings error:', e)
    }
  }

  async function saveSettings(patch: Partial<NotificationSettings>) {
    try {
      const { data } = await notificationsApi.saveSettings(patch)
      settings.value = data
    } catch (e) {
      console.error('saveSettings error:', e)
    }
  }


  function connectWS(token: string) {
    if (ws && ws.readyState === WebSocket.OPEN) return

    const base = import.meta.env.VITE_API_URL || 'https://anisphere.org'
    const wsBase = base.replace(/^https/, 'wss').replace(/^http/, 'ws')
    const url = `${wsBase}/ws/global/?token=${token}`

    ws = new WebSocket(url)

    ws.onopen = () => {
      wsReconnectDelay = 2000
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.action === 'notification' && data.notification) {
          addNotification(data.notification as NotificationItem)
        }
      } catch {}
    }

    ws.onclose = () => {
      ws = null
      wsReconnectTimer = setTimeout(() => {
        connectWS(token)
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000)
      }, wsReconnectDelay)
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function disconnectWS() {
    if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
  }

  return {
    notifications,
    recentNotifications,
    reminders,
    unreadCount,
    flashingCount,
    loading,
    loadingMore,
    hasMore,
    hasUnread,
    settings,
    upcomingReminders,
    allActiveReminders,
    isBellRinging,
    ringingReminderIds,
    isReminderRinging,
    startRinging,
    stopRinging,

    fetchNotifications,
    fetchRecent,
    fetchCount,
    loadMoreNotifications,
    markRead,
    markAllRead,
    toggleImportant,
    deleteNotification,
    cleanReadNotifications,
    deleteAllNotifications,
    addNotification,

    fetchReminders,
    createReminder,
    deleteReminder,
    deactivateReminder,
    acknowledgeReminder,
    checkAndTriggerReminders,

    fetchSettings,
    saveSettings,

    connectWS,
    disconnectWS,
  }
})
