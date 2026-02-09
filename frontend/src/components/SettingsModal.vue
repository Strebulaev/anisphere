<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Настройки</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Tabs Navigation -->
        <div class="settings-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Appearance Tab -->
        <div v-if="activeTab === 'appearance'" class="tab-content">
          <h4>Внешний вид</h4>

          <div class="setting-group">
            <label class="setting-label">Тема приложения</label>
            <div class="theme-options">
              <button
                v-for="theme in themeOptions"
                :key="theme.id"
                @click="selectedTheme = theme.id"
                :class="['theme-btn', { active: selectedTheme === theme.id }]"
              >
                <span class="theme-icon">{{ theme.icon }}</span>
                <span class="theme-name">{{ theme.name }}</span>
              </button>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Стиль интерфейса</label>
            <select v-model="selectedStyle" class="setting-select">
              <option value="modern">Современный</option>
              <option value="classic">Классический</option>
              <option value="minimal">Минималистичный</option>
              <option value="dark">Тёмный</option>
            </select>
          </div>

          <div class="setting-group">
            <label class="setting-label">Размер текста</label>
            <div class="text-size-options">
              <button
                v-for="size in textSizeOptions"
                :key="size.id"
                @click="selectedTextSize = size.id"
                :class="['size-btn', { active: selectedTextSize === size.id }]"
              >
                {{ size.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Notifications Tab -->
        <div v-if="activeTab === 'notifications'" class="tab-content">
          <h4>Уведомления</h4>

          <div class="setting-group">
            <label class="setting-label">Push-уведомления</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="notifications.push">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Уведомления по email</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="notifications.email">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Уведомления о новых сообщениях</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="notifications.messages">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Уведомления о новых конкурсах</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="notifications.contests">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Privacy Tab -->
        <div v-if="activeTab === 'privacy'" class="tab-content">
          <h4>Приватность</h4>

          <div class="setting-group">
            <label class="setting-label">Показывать профиль в поиске</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="privacy.showInSearch">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Показывать онлайн статус</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="privacy.showOnlineStatus">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Показывать статистику профиля</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="privacy.showStats">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- Security Tab -->
        <div v-if="activeTab === 'security'" class="tab-content">
          <h4>Безопасность</h4>

          <div class="setting-group">
            <label class="setting-label"><!-- 2FA removed - not implemented --></label>
            <div class="security-status">
              <span :class="['status-badge', security.twoFactorEnabled ? 'enabled' : 'disabled']">
                {{ security.twoFactorEnabled ? 'Включена' : 'Отключена' }}
              </span>
              <button class="btn-link" @click="toggleTwoFactor">
                {{ security.twoFactorEnabled ? 'Отключить' : 'Включить' }}
              </button>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Активные сессии</label>
            <div class="sessions-list">
              <div v-for="session in security.activeSessions" :key="session.id" class="session-item">
                <div class="session-info">
                  <span class="device">{{ session.device }}</span>
                  <span class="location">{{ session.location }}</span>
                  <span class="last-active">{{ session.lastActive }}</span>
                </div>
                <button v-if="!session.current" class="btn-danger-sm" @click="revokeSession(session.id)">
                  Завершить
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Recommendations Tab -->
        <div v-if="activeTab === 'recommendations'" class="tab-content">
          <h4>Рекомендации</h4>

          <div class="setting-group">
            <label class="setting-label">Персонализированные рекомендации</label>
            <div class="toggle-group">
              <label class="toggle">
                <input type="checkbox" v-model="recommendations.personalized">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <label class="setting-label">Интересы</label>
            <div class="interests-grid">
              <label v-for="interest in availableInterests" :key="interest.id" class="interest-checkbox">
                <input type="checkbox" v-model="recommendations.selectedInterests" :value="interest.id">
                <span class="checkmark"></span>
                {{ interest.name }}
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Отмена</button>
        <button @click="saveSettings" class="btn-primary">Сохранить</button>
      </div>
    </div>

    <!-- Missing Data Modal -->
    <MissingDataModal
      :is-visible="showMissingDataModal"
      :title="missingDataConfig.title"
      :message="missingDataConfig.message"
      :missing-fields="missingDataConfig.fields"
      @close="showMissingDataModal = false"
      @save="handleMissingDataSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useAuthStore } from '@/stores/auth'
import MissingDataModal from '@/components/MissingDataModal.vue'
import apiClient from '@/api/client'

interface Props {
  isVisible: boolean
  onClose: () => void
}

interface Session {
  id: number
  device: string
  location: string
  lastActive: string
  current?: boolean
}

interface Field {
  key: string
  label: string
  type: string
  placeholder: string
}



const props = defineProps<Props>()

const settingsStore = useSettingsStore()
const authStore = useAuthStore()
const activeTab = ref('appearance')

// Локальные переменные для UI состояния
const selectedTheme = ref<string>(settingsStore.settings.theme)
const selectedStyle = ref<string>(settingsStore.settings.ui_style)
const selectedTextSize = ref<string>(settingsStore.settings.text_size)

const tabs = [
  { id: 'appearance', label: 'Внешний вид' },
  { id: 'notifications', label: 'Уведомления' },
  { id: 'privacy', label: 'Приватность' },
  { id: 'security', label: 'Безопасность' },
  { id: 'recommendations', label: 'Рекомендации' }
]

const themeOptions = [
  { id: 'light', name: 'Светлая', icon: '☀️' },
  { id: 'dark', name: 'Тёмная', icon: '🌙' },
  { id: 'auto', name: 'Автоматическая', icon: '🔄' }
]

const textSizeOptions = [
  { id: 'small', label: 'Маленький' },
  { id: 'medium', label: 'Средний' },
  { id: 'large', label: 'Большой' }
]

// Используем настройки из store
const notifications = reactive({
  push: settingsStore.settings.push_notifications,
  email: settingsStore.settings.email_notifications,
  messages: settingsStore.settings.message_notifications,
  contests: settingsStore.settings.contest_notifications
})

const privacy = reactive({
  showInSearch: settingsStore.settings.show_in_search,
  showOnlineStatus: settingsStore.settings.show_online_status,
  showStats: settingsStore.settings.show_stats
})

const security = reactive({
  twoFactorEnabled: authStore.user?.two_factor_enabled || false,
  activeSessions: [] as Session[]
})

const recommendations = reactive({
  personalized: settingsStore.settings.personalized_recommendations,
  selectedInterests: [...settingsStore.settings.selected_interests]
})

const showMissingDataModal = ref(false)
const missingDataConfig = ref({
  title: '',
  message: '',
  fields: [] as Field[]
})

const availableInterests = [
  { id: 'action', name: 'Экшен' },
  { id: 'adventure', name: 'Приключения' },
  { id: 'comedy', name: 'Комедия' },
  { id: 'drama', name: 'Драма' },
  { id: 'fantasy', name: 'Фэнтези' },
  { id: 'romance', name: 'Романтика' },
  { id: 'scifi', name: 'Sci-Fi' },
  { id: 'horror', name: 'Ужасы' },
  { id: 'mystery', name: 'Детектив' },
  { id: 'slice_of_life', name: 'Повседневность' }
]

const closeModal = () => {
  props.onClose()
}

const saveSettings = async () => {
  try {
    // Обновляем локальные настройки
    settingsStore.updateSetting('theme', selectedTheme.value as 'light' | 'dark' | 'auto')
    settingsStore.updateSetting('ui_style', selectedStyle.value as 'modern' | 'classic' | 'minimal' | 'dark')
    settingsStore.updateSetting('text_size', selectedTextSize.value as 'small' | 'medium' | 'large')
    settingsStore.updateSetting('push_notifications', notifications.push)
    settingsStore.updateSetting('email_notifications', notifications.email)
    settingsStore.updateSetting('message_notifications', notifications.messages)
    settingsStore.updateSetting('contest_notifications', notifications.contests)
    settingsStore.updateSetting('show_in_search', privacy.showInSearch)
    settingsStore.updateSetting('show_online_status', privacy.showOnlineStatus)
    settingsStore.updateSetting('show_stats', privacy.showStats)
    settingsStore.updateSetting('personalized_recommendations', recommendations.personalized)
    settingsStore.updateSetting('selected_interests', recommendations.selectedInterests)

    // Отправляем на сервер
    const serverSettings = {
      push_notifications: notifications.push,
      email_notifications: notifications.email,
      message_notifications: notifications.messages,
      contest_notifications: notifications.contests,
      show_in_search: privacy.showInSearch,
      show_online_status: privacy.showOnlineStatus,
      show_stats: privacy.showStats,
      personalized_recommendations: recommendations.personalized,
      selected_interests: recommendations.selectedInterests
    }

    const result = await authStore.updateUserSettings(serverSettings)
    if (result.success) {
      closeModal()
    } else {
      alert('Ошибка сохранения настроек')
    }
  } catch (error) {
    console.error('Error saving settings:', error)
    alert('Ошибка сохранения настроек')
  }
}



const toggleTwoFactor = async () => {
  // Проверяем подтверждение email и телефона
  if (!authStore.user?.email_verified || !authStore.user?.phone_verified) {
    // Показываем модальное окно для добавления недостающих данных
    showMissingDataModal.value = true
    const missingFields = []

    if (!authStore.user?.email_verified) {
      missingFields.push({
        key: 'email',
        label: 'Email адрес (требуется подтверждение)',
        type: 'email',
        placeholder: 'your@email.com'
      })
    }

    if (!authStore.user?.phone_verified) {
      missingFields.push({
        key: 'phone',
        label: 'Номер телефона (требуется подтверждение)',
        type: 'tel',
        placeholder: '+7 (999) 123-45-67'
      })
    }

    missingDataConfig.value = {
      title: 'Необходима верификация для 2FA',
      message: 'Для включения двухфакторной аутентификации необходимо подтвердить email и номер телефона.',
      fields: missingFields
    }
    return
  }

  await performTwoFactorToggle()
}

const performTwoFactorToggle = async () => {
  const action = security.twoFactorEnabled ? 'disable' : 'enable'
  const result = await authStore.setupTwoFactor(action)

  if (result.success) {
    security.twoFactorEnabled = !security.twoFactorEnabled
    // Обновляем статус в user store
    if (authStore.user) {
      authStore.user.two_factor_enabled = security.twoFactorEnabled
    }
  } else {
    alert(result.error || 'Ошибка настройки 2FA')
  }
}

const handleMissingDataSave = async (data: Record<string, string>) => {
  try {
    // Обновляем профиль с новыми данными (email/phone)
    const result = await authStore.updateProfile(data)
    if (result.success) {
      // После обновления профиля нужно отправить запросы на верификацию
      if (data.email && !authStore.user?.email_verified) {
        // Отправляем запрос на верификацию email
        const emailResult = await apiClient.post('/users/verify/email/', {
          action: 'send',
          email: data.email
        })
        if (emailResult.data.message) {
          alert('Письмо с подтверждением отправлено на ваш email. После подтверждения email вы сможете включить 2FA.')
        }
      }
      if (data.phone && !authStore.user?.phone_verified) {
        // Отправляем SMS с кодом подтверждения
        const smsResult = await apiClient.post('/users/verify/phone/', {
          action: 'send',
          phone_number: data.phone
        })
        if (smsResult.data.message) {
          alert('SMS с кодом подтверждения отправлено. Введите код для подтверждения телефона.')
        }
      }
      return true
    }
    return false
  } catch (_error) {
    alert('Ошибка обновления профиля')
    return false
  }
}



const revokeSession = async (sessionId: number) => {
  if (confirm('Вы уверены, что хотите завершить эту сессию?')) {
    const result = await authStore.revokeSession(sessionId)
    if (result.success) {
      security.activeSessions = security.activeSessions.filter(s => s.id !== sessionId)
    }
  }
}

onMounted(async () => {
  // Загружаем сессии пользователя
  const sessionsResult = await authStore.getUserSessions()
  if (sessionsResult.success) {
    security.activeSessions = sessionsResult.sessions
  }
})
</script>

<style scoped>
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

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.375rem;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 1.5rem;
}

.settings-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}

.tab-btn {
  background: none;
  border: none;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-btn:hover {
  color: #374151;
}

.tab-content h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.setting-group {
  margin-bottom: 1.5rem;
}

.setting-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

/* Theme options */
.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.theme-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-btn.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.theme-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.theme-name {
  font-size: 0.875rem;
  font-weight: 500;
}

/* Text size options */
.text-size-options {
  display: flex;
  gap: 0.5rem;
}

.size-btn {
  padding: 0.5rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.size-btn.active {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #3b82f6;
}

/* Toggle switches */
.toggle-group {
  display: flex;
  align-items: center;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

.toggle input:checked + .toggle-slider {
  background-color: #3b82f6;
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

/* Security status */
.security-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-badge.enabled {
  background: #d1fae5;
  color: #065f46;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.disabled {
  background: #fee2e2;
  color: #dc2626;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.btn-link {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-link:hover {
  text-decoration: underline;
}

/* Sessions */
.sessions-list {
  space-y: 0.75rem;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.device {
  font-weight: 500;
  color: #1f2937;
}

.location, .last-active {
  font-size: 0.75rem;
  color: #6b7280;
}

.btn-danger-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.btn-danger-sm:hover {
  background: #b91c1c;
}

/* Interests */
.interests-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.interest-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 0.875rem;
}

.interest-checkbox input {
  margin-right: 0.5rem;
}

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-primary {
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  background: #3b82f6;
  color: white;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

/* Select */
.setting-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 0.875rem;
}

@media (max-width: 640px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .settings-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .theme-options {
    grid-template-columns: repeat(3, 1fr);
  }

  .interests-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-secondary, .btn-primary {
    width: 100%;
  }
}
</style>