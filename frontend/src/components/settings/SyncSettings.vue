<template>
  <div class="settings-section">
    <h2>РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ</h2>

    <div class="settings-group">
      <h3>в‘пёЏ Р§С‚Рѕ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ</h3>
      
      <div class="sync-items">
        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.playlists" />
          <span class="sync-icon">рџ“‹</span>
          <span class="sync-info">
            <span class="sync-name">РџР»РµР№Р»РёСЃС‚С‹</span>
            <span class="sync-desc">Р’СЃРµ РІР°С€Рё РїР»РµР№Р»РёСЃС‚С‹ Рё РёС… СЃРѕРґРµСЂР¶РёРјРѕРµ</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.settings" />
          <span class="sync-icon">вљ™пёЏ</span>
          <span class="sync-info">
            <span class="sync-name">РќР°СЃС‚СЂРѕР№РєРё</span>
            <span class="sync-desc">РўРµРјР°, СѓРІРµРґРѕРјР»РµРЅРёСЏ, РїСЂРёРІР°С‚РЅРѕСЃС‚СЊ</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.favorites" />
          <span class="sync-icon">в­ђ</span>
          <span class="sync-info">
            <span class="sync-name">РР·Р±СЂР°РЅРЅРѕРµ</span>
            <span class="sync-desc">Р›СЋР±РёРјС‹Рµ Р°РЅРёРјРµ Рё РјРѕРјРµРЅС‚С‹</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.history" />
          <span class="sync-icon">рџ“є</span>
          <span class="sync-info">
            <span class="sync-name">РСЃС‚РѕСЂРёСЏ РїСЂРѕСЃРјРѕС‚СЂРѕРІ</span>
            <span class="sync-desc">Р§С‚Рѕ РІС‹ СЃРјРѕС‚СЂРµР»Рё Рё РЅР° С‡С‘Рј РѕСЃС‚Р°РЅРѕРІРёР»РёСЃСЊ</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.drafts" />
          <span class="sync-icon">рџ“ќ</span>
          <span class="sync-info">
            <span class="sync-name">Р§РµСЂРЅРѕРІРёРєРё</span>
            <span class="sync-desc">РќРµР·Р°РІРµСЂС€С‘РЅРЅС‹Рµ РїРѕСЃС‚С‹ Рё РєРѕРјРјРµРЅС‚Р°СЂРёРё</span>
          </span>
        </label>

        <label class="sync-item">
          <input type="checkbox" v-model="syncOptions.watchlist" />
          <span class="sync-icon">рџ“љ</span>
          <span class="sync-info">
            <span class="sync-name">РЎРїРёСЃРѕРє "Р‘СѓРґСѓ СЃРјРѕС‚СЂРµС‚СЊ"</span>
            <span class="sync-desc">Р—Р°РїР»Р°РЅРёСЂРѕРІР°РЅРЅС‹Рµ Рє РїСЂРѕСЃРјРѕС‚СЂСѓ</span>
          </span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ“¶ РЈСЃР»РѕРІРёСЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё</h3>
      
      <div class="sync-conditions">
        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="auto" />
          <div class="condition-info">
            <span class="condition-name">РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё</span>
            <span class="condition-desc">РџСЂРё РєР°Р¶РґРѕРј РёР·РјРµРЅРµРЅРёРё РґР°РЅРЅС‹С…</span>
          </div>
        </label>

        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="manual" />
          <div class="condition-info">
            <span class="condition-name">Р’СЂСѓС‡РЅСѓСЋ</span>
            <span class="condition-desc">РўРѕР»СЊРєРѕ РїРѕ РєРЅРѕРїРєРµ РЅРёР¶Рµ</span>
          </div>
        </label>

        <label class="condition-option">
          <input type="radio" v-model="syncCondition" value="schedule" />
          <div class="condition-info">
            <span class="condition-name">РџРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ</span>
            <select v-model="syncSchedule" class="schedule-select" :disabled="syncCondition !== 'schedule'">
              <option value="hourly">РљР°Р¶РґС‹Р№ С‡Р°СЃ</option>
              <option value="daily">РљР°Р¶РґС‹Р№ РґРµРЅСЊ</option>
              <option value="weekly">РљР°Р¶РґСѓСЋ РЅРµРґРµР»СЋ</option>
            </select>
          </div>
        </label>
      </div>

      <div class="sync-restrictions">
        <label class="restriction-option">
          <input type="checkbox" v-model="wifiOnly" />
          <span class="restriction-icon">рџ“¶</span>
          <span>РўРѕР»СЊРєРѕ РїРѕ Wi-Fi</span>
        </label>

        <label class="restriction-option">
          <input type="checkbox" v-model="chargingOnly" />
          <span class="restriction-icon">рџ”‹</span>
          <span>РўРѕР»СЊРєРѕ РїСЂРё Р·Р°СЂСЏРґРєРµ</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ”„ РЎС‚Р°С‚СѓСЃ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё</h3>
      
      <div class="sync-status" :class="syncStatusClass">
        <div class="status-icon">{{ syncStatusIcon }}</div>
        <div class="status-info">
          <div class="status-title">{{ syncStatusTitle }}</div>
          <div class="status-desc">{{ syncStatusDesc }}</div>
        </div>
      </div>

      <div class="sync-details">
        <div class="detail-row">
          <span class="detail-label">РџРѕСЃР»РµРґРЅСЏСЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ:</span>
          <span class="detail-value">{{ lastSyncTime || 'РќРёРєРѕРіРґР°' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">РЎР»РµРґСѓСЋС‰Р°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ:</span>
          <span class="detail-value">{{ nextSyncTime || 'РќРµ Р·Р°РїР»Р°РЅРёСЂРѕРІР°РЅР°' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ СѓСЃС‚СЂРѕР№СЃС‚РІ:</span>
          <span class="detail-value">{{ syncedDevices }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Р Р°Р·РјРµСЂ СЃРёРЅС…СЂРѕРЅРёР·РёСЂСѓРµРјС‹С… РґР°РЅРЅС‹С…:</span>
          <span class="detail-value">{{ syncDataSize }}</span>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ“± РџРѕРґРєР»СЋС‡С‘РЅРЅС‹Рµ СѓСЃС‚СЂРѕР№СЃС‚РІР°</h3>
      
      <div class="devices-list">
        <div v-for="device in devices" :key="device.id" class="device-item">
          <div class="device-info">
            <span class="device-icon">{{ getDeviceIcon(device.type) }}</span>
            <div class="device-details">
              <div class="device-name">{{ device.name }}</div>
              <div class="device-meta">
                {{ device.platform }} вЂў {{ formatDate(device.lastSync) }}
              </div>
            </div>
          </div>
          <div class="device-status">
            <span v-if="device.current" class="current-badge">РўРµРєСѓС‰РµРµ</span>
            <span v-else class="sync-badge">{{ device.synced ? 'вњ… РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ' : 'вЏі РћР¶РёРґР°РµС‚' }}</span>
          </div>
        </div>
      </div>

      <button class="add-device-btn">
        вћ• Р”РѕР±Р°РІРёС‚СЊ СѓСЃС‚СЂРѕР№СЃС‚РІРѕ
      </button>
    </div>

    <div class="settings-group">
      <h3>вљ пёЏ РљРѕРЅС„Р»РёРєС‚С‹ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё</h3>
      
      <div v-if="hasConflicts" class="conflicts-section">
        <p class="conflicts-info">
          РћР±РЅР°СЂСѓР¶РµРЅС‹ РєРѕРЅС„Р»РёРєС‚С‹ РґР°РЅРЅС‹С… РјРµР¶РґСѓ СѓСЃС‚СЂРѕР№СЃС‚РІР°РјРё. Р’С‹Р±РµСЂРёС‚Рµ, РєР°РєРёРµ РґР°РЅРЅС‹Рµ СЃРѕС…СЂР°РЅРёС‚СЊ:
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
                  <div class="preview-label">Р­С‚Рѕ СѓСЃС‚СЂРѕР№СЃС‚РІРѕ</div>
                  <div class="preview-content">{{ conflict.local }}</div>
                </div>
              </label>
              <label class="conflict-option">
                <input type="radio" :name="`conflict-${conflict.id}`" value="remote" v-model="conflict.resolution" />
                <div class="conflict-preview remote">
                  <div class="preview-label">Р”СЂСѓРіРѕРµ СѓСЃС‚СЂРѕР№СЃС‚РІРѕ</div>
                  <div class="preview-content">{{ conflict.remote }}</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <button @click="resolveConflicts" class="resolve-btn">
          вњ… РџСЂРёРјРµРЅРёС‚СЊ РІС‹Р±РѕСЂ
        </button>
      </div>

      <div v-else class="no-conflicts">
        <div class="no-conflicts-icon">вњ…</div>
        <p>РљРѕРЅС„Р»РёРєС‚РѕРІ РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅРѕ</p>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="syncNow" :disabled="isSyncing" class="sync-btn">
        {{ isSyncing ? 'рџ”„ РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ...' : 'вџІ РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ СЃРµР№С‡Р°СЃ' }}
      </button>
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        рџ’ѕ РЎРѕС…СЂР°РЅРёС‚СЊ РЅР°СЃС‚СЂРѕР№РєРё
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
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
    case 'syncing': return 'рџ”„'
    case 'synced': return 'вњ…'
    case 'error': return 'вќЊ'
    default: return 'вЏі'
  }
})

const syncStatusTitle = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return 'РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ...'
    case 'synced': return 'РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ'
    case 'error': return 'РћС€РёР±РєР° СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё'
    default: return 'РћР¶РёРґР°РµС‚ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё'
  }
})

const syncStatusDesc = computed(() => {
  switch (syncStatus.value) {
    case 'syncing': return 'РРґС‘С‚ РѕР±РјРµРЅ РґР°РЅРЅС‹РјРё СЃ СЃРµСЂРІРµСЂРѕРј'
    case 'synced': return 'Р’СЃРµ РґР°РЅРЅС‹Рµ Р°РєС‚СѓР°Р»СЊРЅС‹'
    case 'error': return 'РџСЂРѕРІРµСЂСЊС‚Рµ РїРѕРґРєР»СЋС‡РµРЅРёРµ Рє РёРЅС‚РµСЂРЅРµС‚Сѓ'
    default: return 'РќР°Р¶РјРёС‚Рµ РєРЅРѕРїРєСѓ РґР»СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё'
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
      nextSyncTime.value = 'РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё'
    } else if (syncCondition.value === 'schedule') {
      nextSyncTime.value = 'РџРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ'
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
    showToast('РќР°СЃС‚СЂРѕР№РєРё СЃРѕС…СЂР°РЅРµРЅС‹!')
  } catch (error) {
    console.error('Error saving sync settings:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё РЅР°СЃС‚СЂРѕРµРє')
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
    showToast('РљРѕРЅС„Р»РёРєС‚С‹ СѓСЃРїРµС€РЅРѕ СЂР°Р·СЂРµС€РµРЅС‹!')
  } catch (error) {
    console.error('Error resolving conflicts:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЂР°Р·СЂРµС€РµРЅРёРё РєРѕРЅС„Р»РёРєС‚РѕРІ')
  }
}

const getDeviceIcon = (type: string) => {
  switch (type) {
    case 'mobile': return 'рџ“±'
    case 'tablet': return 'рџ“±'
    case 'desktop': return 'рџ’»'
    default: return 'рџ–ҐпёЏ'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  
  if (diffMins < 1) return 'РўРѕР»СЊРєРѕ С‡С‚Рѕ'
  if (diffMins < 60) return `${diffMins} РјРёРЅ РЅР°Р·Р°Рґ`
  if (diffHours < 24) return `${diffHours} С‡ РЅР°Р·Р°Рґ`
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
