<template>
  <div class="settings-section">
    <h2>Р”Р°РЅРЅС‹Рµ Рё С…СЂР°РЅРёР»РёС‰Рµ</h2>

    <div class="storage-overview">
      <h3>рџ“Љ РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РїР°РјСЏС‚Рё</h3>

      <div class="storage-bars">
        <div class="storage-item">
          <div class="storage-label">
            <span>рџ’¬ РЎРѕРѕР±С‰РµРЅРёСЏ</span>
            <span>{{ formatBytes(storageUsage.messages) }} ({{ getPercentage(storageUsage.messages) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.messages) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>рџ“· РњРµРґРёР°</span>
            <span>{{ formatBytes(storageUsage.media) }} ({{ getPercentage(storageUsage.media) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.media) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>рџ“Ѓ Р”РѕРєСѓРјРµРЅС‚С‹</span>
            <span>{{ formatBytes(storageUsage.documents) }} ({{ getPercentage(storageUsage.documents) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.documents) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>рџЋµ РђСѓРґРёРѕ</span>
            <span>{{ formatBytes(storageUsage.audio) }} ({{ getPercentage(storageUsage.audio) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.audio) + '%' }"></div>
          </div>
        </div>

        <div class="storage-item">
          <div class="storage-label">
            <span>рџ—ѓпёЏ РљСЌС€</span>
            <span>{{ formatBytes(storageUsage.cache) }} ({{ getPercentage(storageUsage.cache) }}%)</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: getPercentage(storageUsage.cache) + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="total-usage">
        <span>Р’СЃРµРіРѕ РёСЃРїРѕР»СЊР·РѕРІР°РЅРѕ: {{ formatBytes(storageUsage.total) }}</span>
        <span>Р›РёРјРёС‚: 2 GB</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>вљ™пёЏ РђРІС‚РѕРѕС‡РёСЃС‚РєР°</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearCache">
          <span>РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё РѕС‡РёС‰Р°С‚СЊ РєСЌС€ С‡РµСЂРµР· {{ cacheClearDays }} РґРЅРµР№</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearMedia">
          <span>РЈРґР°Р»СЏС‚СЊ РїСЂРѕСЃРјРѕС‚СЂРµРЅРЅС‹Рµ РјРµРґРёР° С‡РµСЂРµР· {{ mediaClearDays }} РґРЅРµР№</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoClearDocuments">
          <span>РЈРґР°Р»СЏС‚СЊ СЃС‚Р°СЂС‹Рµ РґРѕРєСѓРјРµРЅС‚С‹ С‡РµСЂРµР· {{ documentClearDays }} РґРЅРµР№</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ”„ РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="wifiOnlySync">
          <span>РђРІС‚РѕСЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РїСЂРё Wi-Fi</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncMedia">
          <span>РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ РјРµРґРёР°</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncMessages">
          <span>РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ СЃРѕРѕР±С‰РµРЅРёСЏ</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="syncContacts">
          <span>РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ РєРѕРЅС‚Р°РєС‚С‹</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Р›РёРјРёС‚ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё:</label>
        <select v-model="syncLimit" class="sync-select">
          <option value="500">500 MB</option>
          <option value="1000">1 GB</option>
          <option value="2000">2 GB</option>
          <option value="unlimited">Р‘РµР· РѕРіСЂР°РЅРёС‡РµРЅРёР№</option>
        </select>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ“¤ Р­РєСЃРїРѕСЂС‚ РґР°РЅРЅС‹С…</h3>

      <div class="export-options">
        <button @click="exportMessages" class="export-btn">
          рџ“ќ РСЃС‚РѕСЂРёСЏ СЃРѕРѕР±С‰РµРЅРёР№ в†’
        </button>
        <button @click="exportMedia" class="export-btn">
          рџ“· РњРµРґРёР°С„Р°Р№Р»С‹ в†’
        </button>
        <button @click="exportContacts" class="export-btn">
          рџ‘Ґ РљРѕРЅС‚Р°РєС‚С‹ в†’
        </button>
        <button @click="exportSettings" class="export-btn">
          вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё в†’
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ—‘пёЏ Р СѓС‡РЅР°СЏ РѕС‡РёСЃС‚РєР°</h3>

      <div class="cleanup-options">
        <button @click="clearMessages" class="cleanup-btn danger">
          рџ’¬ РћС‡РёСЃС‚РёС‚СЊ РёСЃС‚РѕСЂРёСЋ СЃРѕРѕР±С‰РµРЅРёР№ в†’
        </button>
        <button @click="clearMedia" class="cleanup-btn danger">
          рџ“· РЈРґР°Р»РёС‚СЊ РІСЃРµ РјРµРґРёР°С„Р°Р№Р»С‹ в†’
        </button>
        <button @click="clearCache" class="cleanup-btn">
          рџ—ѓпёЏ РћС‡РёСЃС‚РёС‚СЊ РєСЌС€ РїСЂРёР»РѕР¶РµРЅРёСЏ в†’
        </button>
        <button @click="clearDownloads" class="cleanup-btn danger">
          рџљ® РЈРґР°Р»РёС‚СЊ Р·Р°РіСЂСѓР¶РµРЅРЅС‹Рµ С„Р°Р№Р»С‹ в†’
        </button>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="recalculateUsage" class="recalc-btn">
        рџ”„ РџРµСЂРµСЃС‡РёС‚Р°С‚СЊ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
import { ref, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'

// Reactive data
const storageUsage = ref({
  messages: 0,
  media: 0,
  documents: 0,
  audio: 0,
  cache: 0,
  total: 0,
  limit: 0,
  usage_percent: 0,
  breakdown: {
    messages_count: 0,
    comments_count: 0,
    playlists_count: 0,
    library_count: 0,
  }
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
    const data = await settingsApi.getStorageUsage()
    storageUsage.value = data
  } catch (error) {
    console.error('Error fetching storage usage:', error)
  }
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const getPercentage = (bytes: number) => {
  const totalLimit = storageUsage.value.limit || 2 * 1024 * 1024 * 1024
  return Math.min(100, Math.round((bytes / totalLimit) * 100))
}

const exportMessages = async () => {
  try {
    await settingsApi.requestExportData({
      items: ['messages'],
      format: 'json'
    })
    showToast('Р—Р°РїСЂРѕСЃ РЅР° СЌРєСЃРїРѕСЂС‚ СЃРѕРѕР±С‰РµРЅРёР№ РѕС‚РїСЂР°РІР»РµРЅ!')
  } catch (error) {
    console.error('Error exporting messages:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЌРєСЃРїРѕСЂС‚Рµ')
  }
}

const exportMedia = async () => {
  try {
    await settingsApi.requestExportData({
      items: ['media'],
      format: 'json'
    })
    showToast('Р—Р°РїСЂРѕСЃ РЅР° СЌРєСЃРїРѕСЂС‚ РјРµРґРёР° РѕС‚РїСЂР°РІР»РµРЅ!')
  } catch (error) {
    console.error('Error exporting media:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЌРєСЃРїРѕСЂС‚Рµ')
  }
}

const exportContacts = async () => {
  try {
    await settingsApi.requestExportData({
      items: ['contacts'],
      format: 'json'
    })
    showToast('Р—Р°РїСЂРѕСЃ РЅР° СЌРєСЃРїРѕСЂС‚ РєРѕРЅС‚Р°РєС‚РѕРІ РѕС‚РїСЂР°РІР»РµРЅ!')
  } catch (error) {
    console.error('Error exporting contacts:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЌРєСЃРїРѕСЂС‚Рµ')
  }
}

const exportSettings = async () => {
  try {
    await settingsApi.requestExportData({
      items: ['settings'],
      format: 'json'
    })
    showToast('Р—Р°РїСЂРѕСЃ РЅР° СЌРєСЃРїРѕСЂС‚ РЅР°СЃС‚СЂРѕРµРє РѕС‚РїСЂР°РІР»РµРЅ!')
  } catch (error) {
    console.error('Error exporting settings:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЌРєСЃРїРѕСЂС‚Рµ')
  }
}

const clearMessages = async () => {
  if (confirm('Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ РѕС‡РёСЃС‚РёС‚СЊ РёСЃС‚РѕСЂРёСЋ СЃРѕРѕР±С‰РµРЅРёР№?')) {
    try {
      await settingsApi.clearCache(['messages'])
      await fetchStorageUsage()
      showToast('РСЃС‚РѕСЂРёСЏ СЃРѕРѕР±С‰РµРЅРёР№ РѕС‡РёС‰РµРЅР°!')
    } catch (error) {
      console.error('Error clearing messages:', error)
      showToast('РћС€РёР±РєР° РїСЂРё РѕС‡РёСЃС‚РєРµ')
    }
  }
}

const clearMedia = async () => {
  if (confirm('Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ СѓРґР°Р»РёС‚СЊ РІСЃРµ РјРµРґРёР°С„Р°Р№Р»С‹?')) {
    try {
      await settingsApi.clearCache(['media', 'videos', 'images'])
      await fetchStorageUsage()
      showToast('РњРµРґРёР°С„Р°Р№Р»С‹ СѓРґР°Р»РµРЅС‹!')
    } catch (error) {
      console.error('Error clearing media:', error)
      showToast('РћС€РёР±РєР° РїСЂРё СѓРґР°Р»РµРЅРёРё')
    }
  }
}

const clearCache = async () => {
  try {
    await settingsApi.clearCache(['images', 'videos', 'search', 'thumbnails', 'temp'])
    await fetchStorageUsage()
    showToast('РљСЌС€ РѕС‡РёС‰РµРЅ!')
  } catch (error) {
    console.error('Error clearing cache:', error)
    showToast('РћС€РёР±РєР° РїСЂРё РѕС‡РёСЃС‚РєРµ')
  }
}

const clearDownloads = async () => {
  if (confirm('Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ СѓРґР°Р»РёС‚СЊ РІСЃРµ Р·Р°РіСЂСѓР¶РµРЅРЅС‹Рµ С„Р°Р№Р»С‹?')) {
    try {
      await settingsApi.clearCache(['documents', 'temp'])
      await fetchStorageUsage()
      showToast('Р—Р°РіСЂСѓР¶РµРЅРЅС‹Рµ С„Р°Р№Р»С‹ СѓРґР°Р»РµРЅС‹!')
    } catch (error) {
      console.error('Error clearing downloads:', error)
      showToast('РћС€РёР±РєР° РїСЂРё СѓРґР°Р»РµРЅРёРё')
    }
  }
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