<template>
  <div class="settings-section">
    <h2>Email уведомления</h2>

    <div class="settings-group">
      <h3>📧 Основные настройки</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="emailEnabled">
          <span>Включить email уведомления</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Основной email:</label>
        <span class="email-display">{{ primaryEmail }}</span>
      </div>

      <div class="setting-item">
        <label>Дополнительный email:</label>
        <button class="add-email-btn">➕ Добавить</button>
      </div>

      <div class="setting-item">
        <button class="verify-email-btn">✅ Подтвердить email</button>
      </div>
    </div>

    <div class="settings-group">
      <h3>⏰ Частота и время</h3>

      <div class="setting-item">
        <label>Частота уведомлений:</label>
        <select v-model="emailFrequency" class="setting-select">
          <option value="immediately">Немедленно</option>
          <option value="hourly">Каждый час (сводка)</option>
          <option value="daily">Ежедневно</option>
          <option value="weekly">Еженедельно</option>
          <option value="important">Только важные</option>
        </select>
      </div>

      <div v-if="emailFrequency === 'daily'" class="setting-item">
        <label>Время ежедневной сводки:</label>
        <input v-model="dailyDigestTime" type="time" class="time-input">
      </div>

      <div v-if="emailFrequency === 'weekly'" class="time-settings">
        <div class="setting-item">
          <label>День недельной сводки:</label>
          <select v-model="weeklyDigestDay" class="setting-select">
            <option value="monday">Понедельник</option>
            <option value="tuesday">Вторник</option>
            <option value="wednesday">Среда</option>
            <option value="thursday">Четверг</option>
            <option value="friday">Пятница</option>
            <option value="saturday">Суббота</option>
            <option value="sunday">Воскресенье</option>
          </select>
        </div>
        <div class="setting-item">
          <label>Время:</label>
          <input v-model="weeklyDigestTime" type="time" class="time-input">
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>📋 Что уведомлять</h3>

      <div class="checkbox-grid">
        <label class="setting-label">
          <input type="checkbox" v-model="notifyPrivateMessages">
          <span>Личные сообщения</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyGroupMessages">
          <span>Групповые сообщения</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyMentions">
          <span>Упоминания (@username)</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyReplies">
          <span>Ответы на мои сообщения</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyReactions">
          <span>Реакции</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyGroupInvites">
          <span>Приглашения в группы</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifySystem">
          <span>Системные уведомления</span>
        </label>

        <label class="setting-label">
          <input type="checkbox" v-model="notifyNews">
          <span>Новости и обновления</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🎨 Формат писем</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="radio" v-model="emailFormat" value="html">
          <span>HTML письма (рекомендуется)</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="radio" v-model="emailFormat" value="text">
          <span>Текстовый формат</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="includePreviews">
          <span>Включать превью сообщений</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="includeAttachments">
          <span>Включать медиавложения</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="includeUnsubscribe">
          <span>Футер с отпиской</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🚫 Исключения</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="noWeekends">
          <span>Не отправлять в выходные</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="noNightHours">
          <span>Не отправлять с 22:00 до 08:00</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Минимальный интервал:</label>
        <select v-model="minInterval" class="setting-select">
          <option value="5">5 минут</option>
          <option value="15">15 минут</option>
          <option value="30">30 минут</option>
          <option value="60">1 час</option>
        </select>
      </div>

      <div class="setting-item">
        <label>Максимум писем в день:</label>
        <select v-model="maxEmailsPerDay" class="setting-select">
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
          <option value="unlimited">Без ограничений</option>
        </select>
      </div>
    </div>

    <div class="stats-section">
      <h3>📊 Статистика за месяц</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">Отправлено писем:</span>
          <span class="stat-value">42</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Прочитано:</span>
          <span class="stat-value">38 (90%)</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">В спаме:</span>
          <span class="stat-value">0</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Последнее письмо:</span>
          <span class="stat-value">сегодня 10:30</span>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="sendTestEmail" class="test-btn">
        ✉️ Тестовое письмо
      </button>
      <button @click="viewHistory" class="history-btn">
        📥 История отправок
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Reactive data
const emailEnabled = ref(true)
const primaryEmail = computed(() => authStore.user?.email || '')
const emailFrequency = ref('immediately')
const dailyDigestTime = ref('09:00')
const weeklyDigestDay = ref('monday')
const weeklyDigestTime = ref('09:00')

const notifyPrivateMessages = ref(true)
const notifyGroupMessages = ref(true)
const notifyMentions = ref(true)
const notifyReplies = ref(true)
const notifyReactions = ref(false)
const notifyGroupInvites = ref(true)
const notifySystem = ref(true)
const notifyNews = ref(false)

const emailFormat = ref('html')
const includePreviews = ref(true)
const includeAttachments = ref(false)
const includeUnsubscribe = ref(true)

const noWeekends = ref(true)
const noNightHours = ref(true)
const minInterval = ref('15')
const maxEmailsPerDay = ref('20')

// Methods
const fetchEmailSettings = async () => {
  try {
    const response = await apiClient.get('/users/notification-settings/')
    const settings = response.data

    emailEnabled.value = settings.email_enabled
    emailFrequency.value = settings.email_frequency || 'immediately'
    // Map other settings...
  } catch (error) {
    console.error('Error fetching email settings:', error)
  }
}

const saveEmailSettings = async () => {
  try {
    await apiClient.put('/users/notification-settings/', {
      email_enabled: emailEnabled.value,
      email_frequency: emailFrequency.value
      // Add other email settings...
    })
  } catch (error) {
    console.error('Error saving email settings:', error)
  }
}

const sendTestEmail = () => {
  console.log('Sending test email...')
}

const viewHistory = () => {
  console.log('Viewing email history...')
}
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.setting-item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
  flex: 1;
}

.setting-label input[type="checkbox"],
.setting-label input[type="radio"] {
  margin: 0;
}

.setting-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
  min-width: 140px;
}

.email-display {
  font-weight: 500;
  color: var(--primary-color);
}

.add-email-btn, .verify-email-btn {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.time-settings {
  display: flex;
  gap: 15px;
}

.time-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.stats-section {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.stats-section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-weight: 500;
}

.stat-value {
  color: var(--primary-color);
  font-weight: 600;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.test-btn, .history-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.test-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.history-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>