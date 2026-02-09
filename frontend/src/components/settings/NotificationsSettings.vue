<template>
  <div class="settings-section">
    <h2>Уведомления</h2>

    <div class="settings-group">
      <h3>🔔 Push-уведомления</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="pushEnabled">
          <span>Включить push-уведомления</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Звук уведомлений:</label>
        <select v-model="notificationSound" class="setting-select">
          <option value="default">По умолчанию</option>
          <option value="gentle">Мягкий</option>
          <option value="urgent">Срочный</option>
          <option value="silent">Без звука</option>
        </select>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="pushVibration">
          <span>Вибрация</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="showPreview">
          <span>Показывать текст сообщения</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="showSender">
          <span>Показывать имя отправителя</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📱 Типы уведомлений</h3>

      <div class="setting-item">
        <label>Личные сообщения:</label>
        <select v-model="privateMessageSetting" class="setting-select">
          <option value="all">Все</option>
          <option value="important">Только важные</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="setting-item">
        <label>Групповые чаты:</label>
        <select v-model="groupMessageSetting" class="setting-select">
          <option value="all">Все</option>
          <option value="mentions">Только упоминания</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="setting-item">
        <label>Звонки:</label>
        <select v-model="callSetting" class="setting-select">
          <option value="all">Все</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="reactionNotifications">
          <span>Реакции на сообщения</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="systemNotifications">
          <span>Системные уведомления</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>⏰ Не беспокоить</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="doNotDisturbEnabled">
          <span>Включить режим "Не беспокоить"</span>
        </label>
      </div>

      <div v-if="doNotDisturbEnabled" class="dnd-settings">
        <div class="time-settings">
          <div class="setting-item">
            <label>С:</label>
            <input v-model="dndStartTime" type="time" class="time-input">
          </div>
          <div class="setting-item">
            <label>До:</label>
            <input v-model="dndEndTime" type="time" class="time-input">
          </div>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="dndRepeatDaily">
            <span>Повторять каждый день</span>
          </label>
        </div>

        <div class="dnd-exceptions">
          <label>Исключения:</label>
          <button class="exceptions-btn">Настроить →</button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>🎯 Исключения ({{ chatExceptions.length }} чатов)</h3>

      <div class="exceptions-list">
        <div v-for="exception in chatExceptions" :key="exception.id" class="exception-item">
          <span>{{ exception.name }}</span>
          <select v-model="exception.setting" class="mini-select">
            <option value="default">По умолчанию</option>
            <option value="muted">Заглушено</option>
            <option value="custom">Свои настройки</option>
          </select>
        </div>
      </div>

      <button class="manage-exceptions-btn">Управлять исключениями →</button>
    </div>

    <div class="settings-actions">
      <button @click="applyToAllChats" class="apply-btn">
        💾 Применить ко всем чатам
      </button>
      <button @click="resetToDefaults" class="reset-btn">
        ↻ Сбросить все настройки
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

// Reactive data
const pushEnabled = ref(true)
const notificationSound = ref('default')
const pushVibration = ref(true)
const showPreview = ref(true)
const showSender = ref(true)

const privateMessageSetting = ref('all')
const groupMessageSetting = ref('mentions')
const callSetting = ref('all')
const reactionNotifications = ref(false)
const systemNotifications = ref(true)

const doNotDisturbEnabled = ref(false)
const dndStartTime = ref('22:00')
const dndEndTime = ref('08:00')
const dndRepeatDaily = ref(true)

const chatExceptions = ref([
  { id: 1, name: 'Рабочий чат', setting: 'default' },
  { id: 2, name: 'Семья', setting: 'custom' },
  { id: 3, name: 'Друзья', setting: 'muted' }
])

// Methods
const fetchNotificationSettings = async () => {
  try {
    const response = await apiClient.get('/users/notification-settings/')
    const settings = response.data

    pushEnabled.value = settings.push_enabled
    pushVibration.value = settings.push_vibration
    showPreview.value = settings.push_preview

    // Map other settings...
  } catch (error) {
    console.error('Error fetching notification settings:', error)
  }
}

const saveNotificationSettings = async () => {
  try {
    await apiClient.put('/users/notification-settings/', {
      push_enabled: pushEnabled.value,
      push_vibration: pushVibration.value,
      push_preview: showPreview.value,
      message_notifications: privateMessageSetting.value === 'all',
      group_notifications: groupMessageSetting.value !== 'none',
      call_notifications: callSetting.value === 'all',
      mention_notifications: groupMessageSetting.value === 'mentions',
      reaction_notifications: reactionNotifications.value,
      do_not_disturb_start: doNotDisturbEnabled.value ? dndStartTime.value : null,
      do_not_disturb_end: doNotDisturbEnabled.value ? dndEndTime.value : null
    })
  } catch (error) {
    console.error('Error saving notification settings:', error)
  }
}

const applyToAllChats = () => {
  saveNotificationSettings()
}

const resetToDefaults = () => {
  pushEnabled.value = true
  notificationSound.value = 'default'
  pushVibration.value = true
  showPreview.value = true
  showSender.value = true
  privateMessageSetting.value = 'all'
  groupMessageSetting.value = 'mentions'
  callSetting.value = 'all'
  reactionNotifications.value = false
  systemNotifications.value = true
  doNotDisturbEnabled.value = false
}

onMounted(() => {
  fetchNotificationSettings()
})
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

.setting-label input[type="checkbox"] {
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

.dnd-settings {
  margin-top: 15px;
}

.time-settings {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.time-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
}

.dnd-exceptions {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
}

.exceptions-btn {
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.exceptions-list {
  margin-bottom: 15px;
}

.exception-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.exception-item:last-child {
  border-bottom: none;
}

.mini-select {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-color);
  color: var(--text-color);
  font-size: 14px;
}

.manage-exceptions-btn {
  padding: 8px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.apply-btn, .reset-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.apply-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.reset-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>