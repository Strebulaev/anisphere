<template>
  <div class="settings-section">
    <h2>Синхронизация</h2>

    <div class="settings-group">
      <h3>☑️ Что синхронизировать</h3>
      
      <div class="sync-items">
        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.playlists" />
          <span class="sync-icon">📋</span>
          <span class="sync-info">
            <span class="sync-name">Плейлисты</span>
            <span class="sync-desc">Все ваши плейлисты и их содержимое</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.settings" />
          <span class="sync-icon">⚙️</span>
          <span class="sync-info">
            <span class="sync-name">Настройки</span>
            <span class="sync-desc">Тема, уведомления, приватность</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.favorites" />
          <span class="sync-icon">⭐</span>
          <span class="sync-info">
            <span class="sync-name">Избранное</span>
            <span class="sync-desc">Любимые аниме и моменты</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.history" />
          <span class="sync-icon">📺</span>
          <span class="sync-info">
            <span class="sync-name">История просмотров</span>
            <span class="sync-desc">Что вы смотрели и на чём остановились</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.drafts" />
          <span class="sync-icon">📝</span>
          <span class="sync-info">
            <span class="sync-name">Черновики</span>
            <span class="sync-desc">Незавершённые посты и комментарии</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.watchlist" />
          <span class="sync-icon">📚</span>
          <span class="sync-info">
            <span class="sync-name">Список "Буду смотреть"</span>
            <span class="sync-desc">Запланированные к просмотру</span>
          </span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📶 Условия синхронизации</h3>
      
      <div class="sync-conditions">
        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="auto" />
          <div class="condition-info">
            <span class="condition-name">Автоматически</span>
            <span class="condition-desc">При каждом изменении данных</span>
          </div>
        </label>

        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="manual" />
          <div class="condition-info">
            <span class="condition-name">Вручную</span>
            <span class="condition-desc">Только по кнопке ниже</span>
          </div>
        </label>

        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="schedule" />
          <div class="condition-info">
            <span class="condition-name">По расписанию</span>
            <select v-model="syncSchedule" class="schedule-select" :disabled="syncCondition !== 'schedule'">
              <option value="hourly">Каждый час</option>
              <option value="daily">Каждый день</option>
              <option value="weekly">Каждую неделю</option>
            </select>
          </div>
        </label>
      </div>

      <div class="sync-restrictions">
        <label class="restriction-option">
          <input type="checkbox" v-model="wifiOnly" />
          <span class="restriction-icon">📶</span>
          <span>Только по Wi-Fi</span>
        </label>

        <label class="restriction-option">
          <input type="checkbox" v-model="chargingOnly" />
          <span class="restriction-icon">🔋</span>
          <span>Только при зарядке</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔄 Статус синхронизации</h3>
      
      <div class="sync-status" :class="syncStatusClass">
        <div class="status-icon">{{ syncStatusIcon }}</div>
        <div class="status-info">
          <div class="status-title">{{ syncStatusTitle }}</div>
          <div class="status-desc">{{ syncStatusDesc }}</div>
        </div>
      </div>

      <div class="sync-details">
        <div class="detail-row">
          <span class="detail-label">Последняя синхронизация:</span>
          <span class="detail-value">{{ lastSyncTime || 'Никогда' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Следующая синхронизация:</span>
          <span class="detail-value">{{ nextSyncTime || 'Не запланирована' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Синхронизировано устройств:</span>
          <span class="detail-value">{{ syncedDevices }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Размер синхронизируемых данных:</span>
          <span class="detail-value">{{ syncDataSize }}</span>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>📱 Подключённые устройства</h3>
      
      <div class="devices-list">
        <div v-for="device in devices" :key="device.id" class="device-item">
          <div class="device-info">
            <span class="device-icon">{{ getDeviceIcon(device.type) }}</span>
            <div class="device-details">
              <div class="device-name">{{ device.name }}</div>
              <div class="device-meta">
                {{ device.platform }} • {{ formatDate(device.lastSync) }}
              </div>
            </div>
          </div>
          <div class="device-status">
            <span v-if="device.current" class="current-badge">Текущее</span>
            <span v-else class="sync-badge">{{ device.synced ? '✅ Синхронизировано' : '⏳ Ожидает' }}</span>
          </div>
        </div>
      </div>

      <button class="add-device-btn">
        ➕ Добавить устройство
      </button>
    </div>

    <div class="settings-group">
      <h3>⚠️ Конфликты синхронизации</h3>
      
      <div v-if="hasConflicts" class="conflicts-section">
        <p class="conflicts-info">
          Обнаружены конфликты данных между устройствами. Выберите, какие данные сохранить:
        </p>

        <div class="conflicts-list">
          <div v-for="conflict in conflicts" :key="conflict.id" class="conflict-item">
            <div class="conflict-header">
              <span class="conflict-type">{{ conflict.type }}</span>
              <span class="conflict-date">{{ formatDate(conflict.date) }}</span>
            </div>
            <div class="conflict-options">
              <label class="conflict-option">
                <input type="radio" :name="`conflict-${conflict.id}`" value="local" v-model="conflict.resolution" />
                <div class="conflict-preview local">
                  <div class="preview-label">Это устройство</div>
                  <div class="preview-content">{{ conflict.local }}</div>
                </div>
              </label>
              <label class="conflict-option">
                <input type="radio" :name="`conflict-${conflict.id}`" value="remote" v-model="conflict.resolution" />
                <div class="conflict-preview remote">
                  <div class="preview-label">Другое устройство</div>
                  <div class="preview-content">{{ conflict.remote }}</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <button @click="resolveConflicts" class="resolve-btn">
          ✅ Применить выбор
        </button>
      </div>

      <div v-else class="no-conflicts">
        <div class="no-conflicts-icon">✅</div>
        <p>Конфликтов не обнаружено</p>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="syncNow" :disabled="isSyncing" class="sync-btn">
        {{ isSyncing ? '🔄 Синхронизация...' : '⟲ Синхронизировать сейчас' }}
      </button>
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        💾 Сохранить настройки
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'
import apiClient from '@/api/client'

interface Device {
  id: number
  name: string
  type: string
  platform: string
  lastSync: string
  current: boolean
  synced: boolean
}

interface Conflict {
  id: number
  type: string
  date: string
  local: string
  remote: string
  resolution: string
}

const syncOptions = ref({
  playlists: true,
  settings: true,
  favorites: true,
  history: true,
  drafts: true,
  watchlist: true
})

const syncCondition = ref('auto')
const syncSchedule = ref('daily')
const wifiOnly = ref(true)
const chargingOnly = ref(false)

const syncStatus = ref('synced')
const lastSyncTime = ref('')
const nextSyncTime = ref('')
const syncedDevices = ref(2)
const syncDataSize = ref('2.4 MB')

const devices = ref<Device[]>([])

const conflicts = ref<Conflict[]>([])

const hasConflicts = computed(() => conflicts.value.length > 0)
const isSyncing = ref(false)

const originalSettings = ref({})

const syncStatusClass = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return 'syncing'
    case 'synced': return 'synced'
    case 'error': return 'error'
    default: return 'idle'
  }
})

const syncStatusIcon = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return '🔄'
    case 'synced': return '✅'
    case 'error': return '❌'
    default: return '⏳'
  }
})

const syncStatusTitle = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return 'Синхронизация...'
    case 'synced': return 'Синхронизировано'
    case 'error': return 'Ошибка синхронизации'
    default: return 'Ожидает синхронизации'
  }
})

const syncStatusDesc = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return 'Идёт обмен данными с сервером'
    case 'synced': return 'Все данные актуальны'
    case 'error': return 'Проверьте подключение к интернету'
    default: return 'Нажмите кнопку для синхронизации'
  }
})

const hasChanges = computed(() => {
  const current = {
    syncOptions: syncOptions.value,
    syncCondition: syncCondition.value,
    syncSchedule: syncSchedule.value,
    wifiOnly: wifiOnly.value,
    chargingOnly: chargingOnly.value
  }
  return JSON.stringify(current) !== JSON.stringify(originalSettings.value)
})

const fetchSyncSettings = async () => {
  try {
    const data = await settingsApi.getSyncSettings()
    syncOptions.value = data.sync_options || syncOptions.value
    syncCondition.value = data.sync_condition || 'auto'
    syncSchedule.value = data.sync_schedule || 'daily'
    wifiOnly.value = data.wifi_only ?? true
    chargingOnly.value = data.charging_only || false
    lastSyncTime.value = data.last_sync_time || ''
    nextSyncTime.value = data.next_sync_time || ''
    syncedDevices.value = data.synced_devices || 2
    syncDataSize.value = data.sync_data_size || '2.4 MB'
    syncStatus.value = data.sync_status || 'synced'
    devices.value = data.devices || []

    originalSettings.value = {
      syncOptions: { ...syncOptions.value },
      syncCondition: syncCondition.value,
      syncSchedule: syncSchedule.value,
      wifiOnly: wifiOnly.value,
      chargingOnly: chargingOnly.value
    }
  } catch (error) {
    console.error('Error fetching sync settings:', error)
  }
}

const syncNow = async () => {
  isSyncing.value = true
  syncStatus.value = 'syncing'
  
  try {
    await settingsApi.startSync()
    syncStatus.value = 'synced'
    lastSyncTime.value = new Date().toLocaleString('ru-RU')
    
    if (syncCondition.value === 'auto') {
      nextSyncTime.value = 'Автоматически'
    } else if (syncCondition.value === 'schedule') {
      nextSyncTime.value = 'По расписанию'
    }
  } catch (error) {
    console.error('Error syncing:', error)
    syncStatus.value = 'error'
  } finally {
    isSyncing.value = false
  }
}

const saveSettings = async () => {
  try {
    await settingsApi.updateSyncSettings({
      sync_options: syncOptions.value,
      sync_condition: syncCondition.value,
      sync_schedule: syncSchedule.value,
      wifi_only: wifiOnly.value,
      charging_only: chargingOnly.value
    })
    originalSettings.value = {
      syncOptions: { ...syncOptions.value },
      syncCondition: syncCondition.value,
      syncSchedule: syncSchedule.value,
      wifiOnly: wifiOnly.value,
      chargingOnly: chargingOnly.value
    }
    alert('Настройки сохранены!')
  } catch (error) {
    console.error('Error saving sync settings:', error)
    alert('Ошибка при сохранении настроек')
  }
}

const resolveConflicts = async () => {
  try {
    const resolutions = conflicts.value.map(conflict => ({
      id: conflict.id,
      type: conflict.type,
      resolution: conflict.resolution
    }))

    await apiClient.post('/settings/sync/resolve-conflicts/', { resolutions })
    conflicts.value = []
    alert('Конфликты успешно разрешены!')
  } catch (error) {
    console.error('Error resolving conflicts:', error)
    alert('Ошибка при разрешении конфликтов')
  }
}

const getDeviceIcon = (type: string) => {
  switch (type) {
    case 'mobile': return '📱'
    case 'tablet': return '📱'
    case 'desktop': return '💻'
    default: return '🖥️'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  
  if (diffMins < 1) return 'Только что'
  if (diffMins < 60) return `${diffMins} мин назад`
  if (diffHours < 24) return `${diffHours} ч назад`
  return date.toLocaleDateString('ru-RU')
}

onMounted(() => {
  fetchSyncSettings()
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

.sync-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sync-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sync-item:hover {
  background: var(--hover-bg);
}

.sync-item input[type="checkbox"] {
  margin: 0;
}

.sync-icon {
  font-size: 24px;
  width: 40px;
  text-align: center;
}

.sync-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sync-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.sync-desc {
  font-size: 13px;
  color: var(--secondary-text);
}

.sync-conditions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.condition-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.condition-option input[type="radio"] {
  margin: 0;
}

.condition-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.condition-name {
  font-weight: 500;
}

.condition-desc {
  font-size: 13px;
  color: var(--secondary-text);
}

.schedule-select {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 13px;
}

.sync-restrictions {
  display: flex;
  gap: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.restriction-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.restriction-option input[type="checkbox"] {
  margin: 0;
}

.restriction-icon {
  font-size: 20px;
}

.sync-status {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  margin-bottom: 20px;
}

.sync-status.synced {
  border-left: 4px solid #4CAF50;
}

.sync-status.syncing {
  border-left: 4px solid var(--primary-color);
}

.sync-status.error {
  border-left: 4px solid #f44336;
}

.status-icon {
  font-size: 32px;
}

.status-info {
  flex: 1;
}

.status-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.status-desc {
  font-size: 14px;
  color: var(--secondary-text);
}

.sync-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: var(--card-bg);
  border-radius: 4px;
}

.detail-label {
  color: var(--secondary-text);
}

.detail-value {
  font-weight: 500;
}

.devices-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.device-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon {
  font-size: 24px;
}

.device-name {
  font-weight: 500;
}

.device-meta {
  font-size: 13px;
  color: var(--secondary-text);
}

.device-status {
  text-align: right;
}

.current-badge {
  background: #4CAF50;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.sync-badge {
  font-size: 13px;
  color: var(--secondary-text);
}

.add-device-btn {
  width: 100%;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-color);
}

.conflicts-section {
  padding: 20px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid #FFC107;
  border-radius: 6px;
}

.conflicts-info {
  margin-bottom: 20px;
  color: var(--text-color);
}

.conflicts-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.conflict-item {
  background: var(--card-bg);
  border-radius: 6px;
  padding: 15px;
}

.conflict-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.conflict-type {
  font-weight: 500;
}

.conflict-date {
  font-size: 13px;
  color: var(--secondary-text);
}

.conflict-options {
  display: flex;
  gap: 15px;
}

.conflict-option {
  flex: 1;
  display: block;
}

.conflict-option input[type="radio"] {
  display: none;
}

.conflict-preview {
  padding: 15px;
  border: 2px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.conflict-option input[type="radio"]:checked + .conflict-preview {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.preview-label {
  font-size: 12px;
  color: var(--secondary-text);
  margin-bottom: 5px;
}

.preview-content {
  font-weight: 500;
}

.resolve-btn {
  width: 100%;
  padding: 12px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.no-conflicts {
  text-align: center;
  padding: 40px 20px;
}

.no-conflicts-icon {
  font-size: 60px;
  margin-bottom: 15px;
}

.no-conflicts p {
  color: var(--secondary-text);
  margin: 0;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.sync-btn, .save-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.sync-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
