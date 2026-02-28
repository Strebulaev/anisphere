<template>
  <div class="notifications-dropdown" ref="dropdown">
    <!-- Кнопка уведомлений -->
    <button @click="toggleDropdown" class="notifications-btn">
      <BellIcon class="w-6 h-6" />
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </button>

    <!-- Выпадающее меню -->
    <div v-if="isOpen" class="dropdown-menu">
      <div class="dropdown-header">
        <h3>Уведомления</h3>
        <button @click="markAllAsRead" class="mark-all-btn">
          Всё прочитано
        </button>
      </div>

      <!-- Табы -->
      <div class="tabs">
        <button
          @click="activeTab = 'all'"
          :class="['tab-btn', { active: activeTab === 'all' }]"
        >
          Все
        </button>
        <button
          @click="activeTab = 'unread'"
          :class="['tab-btn', { active: activeTab === 'unread' }]"
        >
          Непрочитанные
          <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
        </button>
      </div>

      <!-- Список уведомлений -->
      <div class="notifications-list">
        <div v-if="loading" class="loading">
          <LoadingSpinner />
        </div>

        <div v-else-if="filteredNotifications.length === 0" class="empty">
          <p>{{ activeTab === 'unread' ? 'Нет непрочитанных' : 'Нет уведомлений' }}</p>
        </div>

        <div v-else class="notifications-scroll">
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            :class="['notification-item', { unread: !notification.is_read }]"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon" :style="{ background: getNotificationColor(notification.notification_type) }">
              {{ getNotificationIcon(notification.notification_type) }}
            </div>
            <div class="notification-content">
              <p class="notification-title">{{ notification.title }}</p>
              <p class="notification-text">{{ notification.content }}</p>
              <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
            </div>
            <button @click.stop="deleteNotification(notification.id)" class="btn-delete">
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div v-if="hasMore" class="load-more">
          <button @click="loadMore" :disabled="loadingMore" class="load-more-btn">
            {{ loadingMore ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </div>

      <div class="dropdown-footer">
        <router-link to="/notifications" @click="closeDropdown" class="view-all-link">
          Все уведомления
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { BellIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import api from '@/api'

const router = useRouter()

const isOpen = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const notifications = ref([])
const activeTab = ref('all')
const page = ref(1)
const hasMore = ref(true)
const dropdown = ref(null)

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return notifications.value.filter(n => !n.is_read)
  }
  return notifications.value
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value && notifications.value.length === 0) {
    loadNotifications()
  }
}

const closeDropdown = () => {
  isOpen.value = false
}

const loadNotifications = async () => {
  loading.value = true
  try {
    const response = await api.get('/notifications/', {
      params: { page: page.value, page_size: 10 }
    })
    notifications.value = response.data.results || response.data
    hasMore.value = response.data.next !== null
  } catch (error) {
    console.error('Ошибка загрузки уведомлений:', error)
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  page.value++

  try {
    const response = await api.get('/notifications/', {
      params: { page: page.value, page_size: 10 }
    })
    notifications.value.push(...(response.data.results || response.data))
    hasMore.value = response.data.next !== null
  } catch (error) {
    console.error('Ошибка загрузки уведомлений:', error)
  } finally {
    loadingMore.value = false
  }
}

const markAsRead = async (notification) => {
  if (notification.is_read) return

  try {
    await api.patch(`/notifications/${notification.id}/`, { is_read: true })
    notification.is_read = true
  } catch (error) {
    console.error('Ошибка отметки прочитанным:', error)
  }
}

const markAllAsRead = async () => {
  try {
    await api.post('/notifications/mark-all-read/')
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('Ошибка отметки всех прочитанными:', error)
  }
}

const deleteNotification = async (id) => {
  try {
    await api.delete(`/notifications/${id}/`)
    notifications.value = notifications.value.filter(n => n.id !== id)
  } catch (error) {
    console.error('Ошибка удаления уведомления:', error)
  }
}

const handleNotificationClick = async (notification) => {
  await markAsRead(notification)

  // Переход по ссылке если указана
  if (notification.link) {
    router.push(notification.link)
  } else if (notification.content_type && notification.object_id) {
    // Переход к объекту
    const typeRoutes = {
      post: `/posts/${notification.object_id}`,
      comment: `/posts/${notification.post_id}`,
      follow: `/profile/${notification.actor_id}`,
      like: `/posts/${notification.object_id}`,
    }
    const route = typeRoutes[notification.content_type]
    if (route) router.push(route)
  }

  closeDropdown()
}

const getNotificationIcon = (type) => {
  const icons = {
    like: '❤️',
    dislike: '👎',
    comment: '💬',
    mention: '@',
    follow: '👥',
    repost: '🔁',
    message: '✉️',
    group_message: '👥',
    achievement: '🏆',
    contest: '🏅',
    system: '⚙️',
  }
  return icons[type] || '🔔'
}

const getNotificationColor = (type) => {
  const colors = {
    like: '#f44336',
    dislike: '#9e9e9e',
    comment: '#2196f3',
    mention: '#ff9800',
    follow: '#4caf50',
    repost: '#9c27b0',
    message: '#00bcd4',
    group_message: '#795548',
    achievement: '#ffc107',
    contest: '#e91e63',
    system: '#607d8b',
  }
  return colors[type] || '#667eea'
}

const formatTime = (date) => {
  const now = new Date()
  const notifDate = new Date(date)
  const diff = Math.floor((now - notifDate) / 1000)

  if (diff < 60) return 'только что'
  if (diff < 3600) return `${Math.floor(diff / 60)} мин. назад`
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч. назад`
  if (diff < 604800) return `${Math.floor(diff / 86400)} дн. назад`
  return notifDate.toLocaleDateString('ru-RU')
}

// Закрываем при клике вне компонента
const handleClickOutside = (e) => {
  if (dropdown.value && !dropdown.value.contains(e.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.notifications-dropdown {
  position: relative;
}

.notifications-btn {
  position: relative;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #666;
  transition: all 0.3s;
}

.notifications-btn:hover {
  background: #f5f5f5;
  color: #667eea;
}

.badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #f44336;
  color: white;
  font-size: 11px;
  font-weight: bold;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  width: 380px;
  max-height: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin-top: 8px;
  overflow: hidden;
  z-index: 1000;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-header h3 {
  margin: 0;
  font-size: 16px;
}

.mark-all-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.3s;
}

.mark-all-btn:hover {
  color: #5568d3;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: #f9f9f9;
}

.tab-btn.active {
  color: #667eea;
  border-bottom: 2px solid #667eea;
}

.notifications-list {
  max-height: 350px;
  overflow-y: auto;
}

.loading,
.empty {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.notifications-scroll {
  max-height: 350px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.3s;
  position: relative;
}

.notification-item:hover {
  background: #f9f9f9;
}

.notification-item.unread {
  background: #f0f7ff;
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #667eea;
}

.notification-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
}

.notification-text {
  margin: 0 0 4px;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 11px;
  color: #999;
}

.btn-delete {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #999;
  opacity: 0;
  transition: all 0.3s;
}

.notification-item:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover {
  background: #f5f5f5;
  color: #f44336;
}

.load-more {
  padding: 12px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

.load-more-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: all 0.3s;
}

.load-more-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #d0d0d0;
}

.load-more-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropdown-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}

.view-all-link {
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: color 0.3s;
}

.view-all-link:hover {
  color: #5568d3;
}
</style>
