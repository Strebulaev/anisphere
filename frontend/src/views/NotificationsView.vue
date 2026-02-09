<template>
  <div class="notifications-page">
    <div class="container">
      <h1 class="page-title">Уведомления</h1>
      
      <div class="notifications-content">
        <div class="notifications-header">
          <div class="tabs">
            <button 
              :class="['tab', { active: activeTab === 'all' }]"
              @click="activeTab = 'all'"
            >
              Все
            </button>
            <button 
              :class="['tab', { active: activeTab === 'unread' }]"
              @click="activeTab = 'unread'"
            >
              Непрочитанные
            </button>
          </div>
          
          <button 
            v-if="notifications.length > 0"
            class="mark-all-read"
            @click="markAllAsRead"
          >
            Отметить все как прочитанные
          </button>
        </div>

        <div v-if="loading" class="loading">
          Загружаем уведомления...
        </div>

        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <h3>Нет уведомлений</h3>
          <p>У вас пока нет уведомлений</p>
        </div>

        <div v-else class="notifications-list">
          <div 
            v-for="notification in filteredNotifications"
            :key="notification.id"
            :class="['notification-item', { unread: !notification.is_read }]"
            @click="markAsRead(notification)"
          >
            <div class="notification-icon">
              <span v-if="notification.type === 'like'">❤️</span>
              <span v-else-if="notification.type === 'comment'">💬</span>
              <span v-else-if="notification.type === 'follow'">👤</span>
              <span v-else-if="notification.type === 'mention'">@</span>
              <span v-else>📢</span>
            </div>
            
            <div class="notification-content">
              <div class="notification-text">
                {{ notification.message }}
              </div>
              <div class="notification-meta">
                <span class="notification-time">
                  {{ formatDate(notification.created_at) }}
                </span>
              </div>
            </div>

            <div class="notification-actions" @click.stop>
              <button 
                v-if="!notification.is_read"
                class="mark-read-btn"
                @click="markAsRead(notification)"
              >
                ✓
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'
import NavBar from '@/components/NavBar.vue'

interface Notification {
  id: number
  type: 'like' | 'comment' | 'follow' | 'mention' | 'system'
  message: string
  is_read: boolean
  created_at: string
  related_user?: {
    id: number
    username: string
    avatar?: string
  }
  related_post?: {
    id: number
    title?: string
  }
}

// Reactive data
const notifications = ref<Notification[]>([])
const loading = ref(false)
const activeTab = ref<'all' | 'unread'>('all')

// Computed
const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return notifications.value.filter(n => !n.is_read)
  }
  return notifications.value
})

// Methods
const loadNotifications = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/notifications/')
    notifications.value = response.data.results || response.data
  } catch (error) {
    console.error('Ошибка загрузки уведомлений:', error)
  } finally {
    loading.value = false
  }
}

const markAsRead = async (notification: Notification) => {
  try {
    await apiClient.patch(`/notifications/${notification.id}/`, {
      read: true
    })
    notification.is_read = true
  } catch (error) {
    console.error('Ошибка отметки уведомления:', error)
  }
}

const markAllAsRead = async () => {
  try {
    await apiClient.post('/notifications/mark-all-as-read/')
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('Ошибка отметки всех уведомлений:', error)
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин. назад`
  if (hours < 24) return `${hours} ч. назад`
  if (days < 7) return `${days} дн. назад`
  
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.page-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 2rem;
  color: var(--color-text);
}

.notifications-content {
  background: var(--color-background-surface);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.tabs {
  display: flex;
  gap: 1rem;
}

.tab {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tab.active {
  background: var(--color-accent);
  color: white;
}

.tab:hover:not(.active) {
  background: var(--color-background-active);
}

.mark-all-read {
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}

.mark-all-read:hover {
  background: #059669;
}

.notifications-list {
  max-height: 600px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-divider-weak);
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background: var(--color-background-active);
}

.notification-item.unread {
  background: rgba(58, 134, 255, 0.1);
  border-left: 4px solid var(--color-accent);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-text {
  color: var(--color-text);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.notification-item.unread .notification-text {
  font-weight: 600;
}

.notification-meta {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.notification-actions {
  flex-shrink: 0;
}

.mark-read-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: var(--color-accent);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mark-read-btn:hover {
  background: var(--color-accent-hover);
}

.loading, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-tertiary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

@media (max-width: 640px) {
  .notifications-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .tabs {
    justify-content: center;
  }
  
  .mark-all-read {
    align-self: center;
  }
  
  .notification-item {
    padding: 1rem;
  }
  
  .notification-icon {
    width: 32px;
    height: 32px;
    font-size: 1rem;
  }
}
</style>