<template>
  <div class="settings-section">
    <h2>Данные и хранилище</h2>

    <div class="storage-overview">
      <h3>📊 Использование памяти</h3>

      <div class="storage-bars">
        <div class="storage-item">
          <div class="storage-label">
            <span>💬 Сообщения</span>
            <span>{{ formatBytes(storageUsage.messages) }} ({{ getPercentage(storageUsage.messages) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.messages) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>📷 Медиа</span>
            <span>{{ formatBytes(storageUsage.media) }} ({{ getPercentage(storageUsage.media) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.media) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>📁 Документы</span>
            <span>{{ formatBytes(storageUsage.documents) }} ({{ getPercentage(storageUsage.documents) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.documents) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>🎵 Аудио</span>
            <span>{{ formatBytes(storageUsage.audio) }} ({{ getPercentage(storageUsage.audio) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.audio) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>🗃️ Кэш</span>
            <span>{{ formatBytes(storageUsage.cache) }} ({{ getPercentage(storageUsage.cache) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.cache) + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="total-usage">
        <span>Всего использовано: {{ formatBytes(storageUsage.total) }}</span>
        <span>Лимит: 2 GB</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>⚙️ Автоочистка</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearCache">
          <span>Автоматически очищать кэш через {{ cacheClearDays }} дней</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearMedia">
          <span>Удалять просмотренные медиа через {{ mediaClearDays }} дней</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearDocuments">
          <span>Удалять старые документы через {{ documentClearDays }} дней</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔄 Синхронизация</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="wifiOnlySync">
          <span>Автосинхронизация при Wi-Fi</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncMedia">
          <span>Синхронизировать медиа</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncMessages">
          <span>Синхронизировать сообщения</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncContacts">
          <span>Синхронизировать контакты</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Лимит синхронизации:</label>
        <select v-model="syncLimit" class="sync-select">
          <option value="500">500 MB</option>
          <option value="1000">1 GB</option>
          <option value="2000">2 GB</option>
          <option value="unlimited">Без ограничений</option>
        </select>
      </div>
    </div>

    <div class="settings-group">
      <h3>📤 Экспорт данных</h3>

      <div class="export-options">
        <button @click="exportMessages" class="export-btn">
          📝 История сообщений →
        </button>
        <button @click="exportMedia" class="export-btn">
          📷 Медиафайлы →
        </button>
        <button @click="exportContacts" class="export-btn">
          👥 Контакты →
        </button>
        <button @click="exportSettings" class="export-btn">
          ⚙️ Настройки →
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>🗑️ Ручная очистка</h3>

      <div class="cleanup-options">
        <button @click="clearMessages" class="cleanup-btn danger">
          💬 Очистить историю сообщений →
        </button>
        <button @click="clearMedia" class="cleanup-btn danger">
          📷 Удалить все медиафайлы →
        </button>
        <button @click="clearCache" class="cleanup-btn">
          🗃️ Очистить кэш приложения →
        </button>
        <button @click="clearDownloads" class="cleanup-btn danger">
          🚮 Удалить загруженные файлы →
        </button>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="recalculateUsage" class="recalc-btn">
        🔄 Пересчитать использование
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

// Reactive data
const storageUsage = ref({
  messages: 0,
  media: 0,
  documents: 0,
  audio: 0,
  cache: 0,
  total: 0
})

const autoClearCache = ref(true)
const cacheClearDays = ref(7)
const autoClearMedia = ref(false)
const mediaClearDays = ref(30)
const autoClearDocuments = ref(false)
const documentClearDays = ref(90)

const wifiOnlySync = ref(true)
const syncMedia = ref(true)
const syncMessages = ref(true)
const syncContacts = ref(true)
const syncLimit = ref('1000')

// Methods
const fetchStorageUsage = async () => {
  try {
    // This would be a real API call to get storage usage
    // For now, using mock data
    storageUsage.value = {
      messages: 1200000000, // 1.2 GB
      media: 850000000,     // 850 MB
      documents: 420000000, // 420 MB
      audio: 150000000,     // 150 MB
      cache: 85000000,      // 85 MB
      total: 2705000000     // 2.7 GB (over limit)
    }
  } catch (error) {
    console.error('Error fetching storage usage:', error)
  }
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getPercentage = (bytes: number) => {
  const totalLimit = 2 * 1024 * 1024 * 1024 // 2 GB
  return Math.min(100, Math.round((bytes / totalLimit) * 100))
}

const exportMessages = () => {
  console.log('Exporting messages...')
}

const exportMedia = () => {
  console.log('Exporting media...')
}

const exportContacts = () => {
  console.log('Exporting contacts...')
}

const exportSettings = () => {
  console.log('Exporting settings...')
}

const clearMessages = () => {
  console.log('Clearing messages...')
}

const clearMedia = () => {
  console.log('Clearing media...')
}

const clearCache = () => {
  console.log('Clearing cache...')
}

const clearDownloads = () => {
  console.log('Clearing downloads...')
}

const recalculateUsage = () => {
  fetchStorageUsage()
}

onMounted(() => {
  fetchStorageUsage()
})
</script>

<style scoped>
.storage-overview {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.storage-overview h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.storage-bars {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.storage-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.storage-label {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 500;
}

.progress-bar {
  height: 8px;
  background: var(--card-bg);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), #00C853);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.total-usage {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

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

.sync-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
}

.export-options, .cleanup-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-btn, .cleanup-btn {
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.export-btn:hover, .cleanup-btn:hover {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.cleanup-btn.danger:hover {
  background: #f44336;
  border-color: #f44336;
}

.settings-actions {
  margin-top: 30px;
  text-align: center;
}

.recalc-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}
</style>