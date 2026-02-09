<template>
  <div class="settings-section">
    <h2>Активные сессии</h2>

    <div class="current-session" v-if="currentSession">
      <h3>📱 Это устройство (текущее)</h3>
      <div class="session-info">
        <div class="session-details">
          <div class="device-name">{{ currentSession.device_name || 'Неизвестное устройство' }}</div>
          <div class="device-location">{{ currentSession.location || 'Неизвестно' }}</div>
          <div class="last-activity">Активно сейчас</div>
        </div>
        <div class="device-icon">📱</div>
      </div>
    </div>

    <div class="other-sessions" v-if="otherSessions.length > 0">
      <h3>● Другие устройства ({{ otherSessions.length }})</h3>

      <div class="session-list">
        <div v-for="session in otherSessions" :key="session.id" class="session-item">
          <div class="session-info">
            <div class="device-name">{{ session.device_name }}</div>
            <div class="device-location">{{ session.location }}</div>
            <div class="last-activity">Активно {{ formatLastActivity(session.last_activity) }}</div>
          </div>
          <div class="device-icon">{{ getDeviceIcon(session.device_info) }}</div>
          <button @click="terminateSession(session)" class="terminate-btn" title="Завершить сессию">
            ✕
          </button>
        </div>
      </div>
    </div>

    <div class="inactive-sessions" v-if="inactiveSessions.length > 0">
      <h3>● Неактивные сессии ({{ inactiveSessions.length }})</h3>
      <button class="view-inactive-btn">Показать неактивные сессии →</button>
    </div>

    <div class="security-settings">
      <h3>⚙️ Настройки безопасности</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="loginNotifications">
          <span>Уведомлять о новых входах</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="rememberDevices">
          <span>Запоминать устройства на {{ rememberDays }} дней</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoTerminateOld">
          <span>Автоматически завершать старые сессии</span>
        </label>
      </div>
    </div>

    <div class="danger-actions">
      <button @click="showTerminateAll = true" class="terminate-all-btn">
        🚪 Завершить все другие сессии
      </button>
    </div>

    <!-- Terminate All Confirmation Modal -->
    <div v-if="showTerminateAll" class="modal-overlay" @click="showTerminateAll = false">
      <div class="modal" @click.stop>
        <h3>Завершить все другие сессии?</h3>
        <p>Вы действительно хотите завершить все сессии на других устройствах? Вам придется войти заново на всех этих устройствах.</p>

        <div class="session-list-preview">
          <div v-for="session in otherSessions.slice(0, 3)" :key="session.id" class="session-preview">
            {{ session.device_name }} • {{ session.location }}
          </div>
          <div v-if="otherSessions.length > 3" class="more-sessions">
            ... и еще {{ otherSessions.length - 3 }} устройств
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showTerminateAll = false" class="cancel-btn">Отмена</button>
          <button @click="terminateAllOtherSessions" class="confirm-btn">Завершить все</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface Session {
  id: number
  session_key: string
  device_info: any
  device_name: string
  location: string
  last_activity: string
  ip_address: string
}

const authStore = useAuthStore()
const sessions = ref<Session[]>([])
const showTerminateAll = ref(false)
const loginNotifications = ref(true)
const rememberDevices = ref(true)
const rememberDays = ref(30)
const autoTerminateOld = ref(false)

// Computed properties
const currentSession = computed(() => {
  return sessions.value.find(session => session.device_name?.includes('Current')) || sessions.value[0] || {} as Session
})

const otherSessions = computed(() => {
  return sessions.value.filter(session => session !== currentSession.value && isActive(session))
})

const inactiveSessions = computed(() => {
  return sessions.value.filter(session => !isActive(session))
})

// Methods
const fetchSessions = async () => {
  try {
    const result = await authStore.getUserSessions()
    if (result.success) {
      sessions.value = result.sessions
    }
  } catch (error) {
    console.error('Error fetching sessions:', error)
  }
}

const isActive = (session: Session) => {
  // Consider session active if activity was within last 24 hours
  const lastActivity = new Date(session.last_activity)
  const now = new Date()
  const diffHours = (now.getTime() - lastActivity.getTime()) / (1000 * 60 * 60)
  return diffHours < 24
}

const formatLastActivity = (lastActivity: string) => {
  const date = new Date(lastActivity)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 60) {
    return `${diffMins} минут назад`
  } else if (diffHours < 24) {
    return `${diffHours} часов назад`
  } else {
    return `${diffDays} дней назад`
  }
}

const getDeviceIcon = (deviceInfo: any) => {
  if (deviceInfo?.device?.toLowerCase().includes('mobile') ||
      deviceInfo?.device?.toLowerCase().includes('phone')) {
    return '📱'
  } else if (deviceInfo?.device?.toLowerCase().includes('tablet')) {
    return '📱'
  } else {
    return '💻'
  }
}

const terminateSession = async (session: Session) => {
  try {
    const result = await authStore.revokeSession(session.id)
    if (result.success) {
      sessions.value = sessions.value.filter(s => s.id !== session.id)
    }
  } catch (error) {
    console.error('Error terminating session:', error)
  }
}

const terminateAllOtherSessions = async () => {
  try {
    const response = await apiClient.post('/users/active-sessions/terminate-all/')
    if (response.status === 200) {
      // Remove all other sessions from the list
      sessions.value = sessions.value.filter(session => session === currentSession.value)
      showTerminateAll.value = false
    }
  } catch (error) {
    console.error('Error terminating all sessions:', error)
  }
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.settings-section h2 {
  margin-bottom: 30px;
}

.current-session, .other-sessions, .inactive-sessions, .security-settings {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.current-session h3, .other-sessions h3, .inactive-sessions h3, .security-settings h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: var(--primary-color);
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-details {
  flex: 1;
}

.device-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.device-location {
  color: var(--secondary-text);
  font-size: 14px;
  margin-bottom: 4px;
}

.last-activity {
  color: var(--secondary-text);
  font-size: 13px;
}

.device-icon {
  font-size: 24px;
  margin-left: 15px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.session-item .session-info {
  flex: 1;
}

.terminate-btn {
  background: none;
  border: none;
  color: #f44336;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.terminate-btn:hover {
  background: rgba(244, 67, 54, 0.1);
}

.view-inactive-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.setting-item {
  margin-bottom: 12px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.danger-actions {
  margin-top: 30px;
  text-align: center;
}

.terminate-all-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.modal p {
  margin-bottom: 20px;
  color: var(--secondary-text);
  line-height: 1.5;
}

.session-list-preview {
  background: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: 150px;
  overflow-y: auto;
}

.session-preview {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--secondary-text);
}

.session-preview:last-child {
  border-bottom: none;
}

.more-sessions {
  padding: 8px 0;
  font-style: italic;
  color: var(--secondary-text);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
</style>