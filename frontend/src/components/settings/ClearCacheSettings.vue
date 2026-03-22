<template>
  <div class="settings-section">
    <h2>РћС‡РёСЃС‚РєР° РєСЌС€Р°</h2>

    <div class="settings-group">
      <h3>рџ“Љ РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РїР°РјСЏС‚Рё</h3>
      
      <div class="storage-chart">
        <div class="chart-container">
          <div class="chart-circle">
            <svg viewBox="0 0 36 36" class="circular-chart">
              <path
                class="circle-bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                class="circle"
                :stroke-dasharray="usagePercent + ', 100'"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div class="chart-center">
              <div class="chart-percent">{{ usagePercent }}%</div>
              <div class="chart-label">Р—Р°РЅСЏС‚Рѕ</div>
            </div>
          </div>
        </div>

        <div class="storage-details">
          <div class="total-storage">
            <span class="total-label">Р’СЃРµРіРѕ:</span>
            <span class="total-value">{{ totalUsed }} / {{ totalSpace }}</span>
          </div>

          <div class="storage-breakdown">
            <div v-for="item in storageItems" :key="item.id" class="breakdown-item">
              <div class="item-info">
                <span class="item-color" :style="{ backgroundColor: item.color }"></span>
                <span class="item-name">{{ item.name }}</span>
              </div>
              <span class="item-size">{{ item.size }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ§№ Р’С‹Р±РµСЂРёС‚Рµ, С‡С‚Рѕ РѕС‡РёСЃС‚РёС‚СЊ</h3>
      
      <div class="cache-items">
        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.images" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџ–јпёЏ</span>
              <span class="cache-name">РљСЌС€ РёР·РѕР±СЂР°Р¶РµРЅРёР№</span>
              <span class="cache-size">{{ storageItems.images.size }}</span>
            </div>
            <div class="cache-desc">РђРІР°С‚Р°СЂС‹, РїРѕСЃС‚РµСЂС‹, РїСЂРµРІСЊСЋ</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.videos" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџЋ¬</span>
              <span class="cache-name">РљСЌС€ РІРёРґРµРѕ</span>
              <span class="cache-size">{{ storageItems.videos.size }}</span>
            </div>
            <div class="cache-desc">РЎРѕС…СЂР°РЅС‘РЅРЅС‹Рµ РІРёРґРµРѕ Рё РїСЂРµРІСЊСЋ</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.search" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџ”Ќ</span>
              <span class="cache-name">РљСЌС€ РїРѕРёСЃРєР°</span>
              <span class="cache-size">{{ storageItems.search.size }}</span>
            </div>
            <div class="cache-desc">РСЃС‚РѕСЂРёСЏ РїРѕРёСЃРєР° Рё СЂРµР·СѓР»СЊС‚Р°С‚С‹</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.history" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџ“є</span>
              <span class="cache-name">РСЃС‚РѕСЂРёСЏ РїСЂРѕСЃРјРѕС‚СЂРѕРІ</span>
              <span class="cache-size">{{ storageItems.history.size }}</span>
            </div>
            <div class="cache-desc">Р›РѕРєР°Р»СЊРЅР°СЏ РёСЃС‚РѕСЂРёСЏ РїСЂРѕСЃРјРѕС‚СЂРѕРІ</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.cookies" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџЌЄ</span>
              <span class="cache-name">Cookie Рё СЃРµСЃСЃРёРё</span>
              <span class="cache-size">{{ storageItems.cookies.size }}</span>
            </div>
            <div class="cache-desc">Р”Р°РЅРЅС‹Рµ Р°РІС‚РѕСЂРёР·Р°С†РёРё (РІС‹Р№РґРµС‚ РёР· Р°РєРєР°СѓРЅС‚Р°)</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.posters" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџЋґ</span>
              <span class="cache-name">Р—Р°РіСЂСѓР¶РµРЅРЅС‹Рµ РїРѕСЃС‚РµСЂС‹</span>
              <span class="cache-size">{{ storageItems.posters.size }}</span>
            </div>
            <div class="cache-desc">РџРѕСЃС‚РµСЂС‹ Р°РЅРёРјРµ Рё РїРµСЂСЃРѕРЅР°Р¶РµР№</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.thumbnails" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџ–јпёЏ</span>
              <span class="cache-name">РњРёРЅРёР°С‚СЋСЂС‹</span>
              <span class="cache-size">{{ storageItems.thumbnails.size }}</span>
            </div>
            <div class="cache-desc">РњРёРЅРёР°С‚СЋСЂС‹ РІРёРґРµРѕ Рё РёР·РѕР±СЂР°Р¶РµРЅРёР№</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.temp" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">рџ—‘пёЏ</span>
              <span class="cache-name">Р’СЂРµРјРµРЅРЅС‹Рµ С„Р°Р№Р»С‹</span>
              <span class="cache-size">{{ storageItems.temp.size }}</span>
            </div>
            <div class="cache-desc">Р’СЂРµРјРµРЅРЅС‹Рµ РґР°РЅРЅС‹Рµ Р·Р°РіСЂСѓР·РєРё</div>
          </div>
        </label>
      </div>

      <div class="selection-summary">
        <div class="summary-info">
          <span class="summary-label">Р’С‹Р±СЂР°РЅРѕ РґР»СЏ РѕС‡РёСЃС‚РєРё:</span>
          <span class="summary-value">{{ selectedSize }}</span>
        </div>
        
        <div class="select-actions">
          <button @click="selectAll" class="select-btn">Р’С‹Р±СЂР°С‚СЊ РІСЃС‘</button>
          <button @click="deselectAll" class="select-btn">РЎРЅСЏС‚СЊ РІС‹РґРµР»РµРЅРёРµ</button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>вљЎ Р‘С‹СЃС‚СЂС‹Рµ РґРµР№СЃС‚РІРёСЏ</h3>
      
      <div class="quick-actions">
        <button @click="clearImages" class="quick-action">
          <span class="action-icon">рџ–јпёЏ</span>
          <div class="action-info">
            <span class="action-name">РћС‡РёСЃС‚РёС‚СЊ РєСЌС€ РёР·РѕР±СЂР°Р¶РµРЅРёР№</span>
            <span class="action-size">{{ storageItems.images.size }}</span>
          </div>
        </button>

        <button @click="clearVideos" class="quick-action">
          <span class="action-icon">рџЋ¬</span>
          <div class="action-info">
            <span class="action-name">РЈРґР°Р»РёС‚СЊ СЃРѕС…СЂР°РЅС‘РЅРЅС‹Рµ РІРёРґРµРѕ</span>
            <span class="action-size">{{ storageItems.videos.size }}</span>
          </div>
        </button>

        <button @click="clearAll" class="quick-action danger">
          <span class="action-icon">рџ—‘пёЏ</span>
          <div class="action-info">
            <span class="action-name">РћС‡РёСЃС‚РёС‚СЊ РІРµСЃСЊ РєСЌС€</span>
            <span class="action-size">{{ totalUsed }}</span>
          </div>
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>вљ™пёЏ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РѕС‡РёСЃС‚РєР°</h3>
      
      <div class="auto-clean-settings">
        <label class="auto-clean-option">
          <input type="checkbox" v-model="autoCleanEnabled" />
          <span class="auto-clean-info">
            <span class="auto-clean-name">РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё РѕС‡РёС‰Р°С‚СЊ РєСЌС€</span>
            <span class="auto-clean-desc">РћС‡РёС‰Р°С‚СЊ СЃС‚Р°СЂС‹Рµ РґР°РЅРЅС‹Рµ РґР»СЏ СЌРєРѕРЅРѕРјРёРё РјРµСЃС‚Р°</span>
          </span>
        </label>

        <div v-if="autoCleanEnabled" class="auto-clean-options">
          <div class="option-row">
            <label>РљРѕРіРґР° РѕС‡РёС‰Р°С‚СЊ:</label>
            <select v-model="autoCleanThreshold" class="threshold-select">
              <option value="80">РџСЂРё РґРѕСЃС‚РёР¶РµРЅРёРё 80%</option>
              <option value="90">РџСЂРё РґРѕСЃС‚РёР¶РµРЅРёРё 90%</option>
              <option value="95">РџСЂРё РґРѕСЃС‚РёР¶РµРЅРёРё 95%</option>
            </select>
          </div>

          <div class="option-row">
            <label>РЈРґР°Р»СЏС‚СЊ РґР°РЅРЅС‹Рµ СЃС‚Р°СЂС€Рµ:</label>
            <select v-model="autoCleanAge" class="age-select">
              <option value="7">7 РґРЅРµР№</option>
              <option value="14">14 РґРЅРµР№</option>
              <option value="30">30 РґРЅРµР№</option>
              <option value="60">60 РґРЅРµР№</option>
            </select>
          </div>

          <label class="auto-clean-option">
            <input type="checkbox" v-model="keepFavorites" />
            <span>Р’СЃРµРіРґР° СЃРѕС…СЂР°РЅСЏС‚СЊ РёР·Р±СЂР°РЅРЅРѕРµ</span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button
        @click="clearSelected"
        :disabled="!hasSelection || isClearing"
        class="clear-btn"
      >
        {{ isClearing ? 'рџ§№ РћС‡РёСЃС‚РєР°...' : 'рџ§№ РћС‡РёСЃС‚РёС‚СЊ РІС‹Р±СЂР°РЅРЅРѕРµ' }}
      </button>
      <button @click="resetSettings" class="reset-btn">
        в†» РЎР±СЂРѕСЃРёС‚СЊ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё
      </button>
    </div>

    <!-- Clear Confirmation Modal -->
    <div v-if="showClearModal" class="modal-overlay" @click="showClearModal = false">
      <div class="modal" @click.stop>
        <h3>РџРѕРґС‚РІРµСЂРґРёС‚СЊ РѕС‡РёСЃС‚РєСѓ?</h3>
        
        <div class="modal-content">
          <p>Р’С‹ СЃРѕР±РёСЂР°РµС‚РµСЃСЊ РѕС‡РёСЃС‚РёС‚СЊ:</p>
          
          <div class="modal-items-list">
            <div v-for="(item, key) in cacheOptions" :key="key">
              <span v-if="item" class="modal-item">вњ“ {{ getCacheItemName(key) }}</span>
            </div>
          </div>

          <div class="modal-total">
            <strong>РћР±СЉС‘Рј:</strong> {{ selectedSize }}
          </div>

          <div class="modal-warning" v-if="cacheOptions.cookies">
            <strong>вљ пёЏ Р’РЅРёРјР°РЅРёРµ:</strong>
            <p>РћС‡РёСЃС‚РєР° cookies РїСЂРёРІРµРґС‘С‚ Рє РІС‹С…РѕРґСѓ РёР· Р°РєРєР°СѓРЅС‚Р° РЅР° СЌС‚РѕРј СѓСЃС‚СЂРѕР№СЃС‚РІРµ.</p>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showClearModal = false" class="cancel-btn">РћС‚РјРµРЅР°</button>
          <button @click="confirmClear" class="confirm-btn danger">РћС‡РёСЃС‚РёС‚СЊ</button>
        </div>
      </div>
    </div>

    <!-- Reset Settings Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="showResetModal = false">
      <div class="modal danger-modal" @click.stop>
        <h3>вљ пёЏ РЎР±СЂРѕСЃРёС‚СЊ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё?</h3>
        
        <p>Р­С‚Рѕ РґРµР№СЃС‚РІРёРµ СЃР±СЂРѕСЃРёС‚ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё РїСЂРёР»РѕР¶РµРЅРёСЏ Рє Р·РЅР°С‡РµРЅРёСЏРј РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ.</p>
        
        <div class="reset-warning">
          <strong>Р§С‚Рѕ Р±СѓРґРµС‚ СЃР±СЂРѕС€РµРЅРѕ:</strong>
          <ul>
            <li>РќР°СЃС‚СЂРѕР№РєРё РІРЅРµС€РЅРµРіРѕ РІРёРґР°</li>
            <li>РќР°СЃС‚СЂРѕР№РєРё СѓРІРµРґРѕРјР»РµРЅРёР№</li>
            <li>РќР°СЃС‚СЂРѕР№РєРё РїСЂРёРІР°С‚РЅРѕСЃС‚Рё</li>
            <li>Р’СЃРµ РѕСЃС‚Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё</li>
          </ul>
        </div>

        <p class="warning-text">Р­С‚Рѕ РґРµР№СЃС‚РІРёРµ РЅРµ Р·Р°С‚СЂРѕРЅРµС‚ РІР°С€Рё РґР°РЅРЅС‹Рµ (РїР»РµР№Р»РёСЃС‚С‹, РёСЃС‚РѕСЂРёСЋ Рё С‚.Рґ.).</p>

        <div class="modal-actions">
          <button @click="showResetModal = false" class="cancel-btn">РћС‚РјРµРЅР°</button>
          <button @click="confirmReset" class="confirm-btn danger">РЎР±СЂРѕСЃРёС‚СЊ</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
import { ref, computed } from 'vue'
import * as settingsApi from '@/api/settings'

interface StorageItem {
  id: string
  name: string
  size: string
  sizeBytes: number
  color: string
}

const storageItems = ref({
  images: { id: 'images', name: 'РР·РѕР±СЂР°Р¶РµРЅРёСЏ', size: '450 MB', sizeBytes: 450 * 1024 * 1024, color: '#0084FF' },
  videos: { id: 'videos', name: 'Р’РёРґРµРѕ', size: '320 MB', sizeBytes: 320 * 1024 * 1024, color: '#4CAF50' },
  search: { id: 'search', name: 'РџРѕРёСЃРє', size: '15 MB', sizeBytes: 15 * 1024 * 1024, color: '#FFC107' },
  history: { id: 'history', name: 'РСЃС‚РѕСЂРёСЏ', size: '5 MB', sizeBytes: 5 * 1024 * 1024, color: '#9C27B0' },
  cookies: { id: 'cookies', name: 'Cookies', size: '2 MB', sizeBytes: 2 * 1024 * 1024, color: '#F44336' },
  posters: { id: 'posters', name: 'РџРѕСЃС‚РµСЂС‹', size: '78 MB', sizeBytes: 78 * 1024 * 1024, color: '#00BCD4' },
  thumbnails: { id: 'thumbnails', name: 'РњРёРЅРёР°С‚СЋСЂС‹', size: '85 MB', sizeBytes: 85 * 1024 * 1024, color: '#FF9800' },
  temp: { id: 'temp', name: 'Р’СЂРµРјРµРЅРЅС‹Рµ', size: '25 MB', sizeBytes: 25 * 1024 * 1024, color: '#607D8B' }
})

const cacheOptions = ref({
  images: false,
  videos: false,
  search: false,
  history: false,
  cookies: false,
  posters: false,
  thumbnails: false,
  temp: false
})

const autoCleanEnabled = ref(false)
const autoCleanThreshold = ref('90')
const autoCleanAge = ref('30')
const keepFavorites = ref(true)

const showClearModal = ref(false)
const showResetModal = ref(false)
const isClearing = ref(false)

const totalSpace = ref('5 GB')
const totalSpaceBytes = 5 * 1024 * 1024 * 1024

const totalUsed = computed(() => {
  const totalBytes = Object.values(storageItems.value).reduce((sum, item) => sum + item.sizeBytes, 0)
  return formatBytes(totalBytes)
})

const totalUsedBytes = computed(() => {
  return Object.values(storageItems.value).reduce((sum, item) => sum + item.sizeBytes, 0)
})

const usagePercent = computed(() => {
  return Math.round((totalUsedBytes.value / totalSpaceBytes) * 100)
})

const hasSelection = computed(() => {
  return Object.values(cacheOptions.value).some(v => v)
})

const selectedSize = computed(() => {
  let totalBytes = 0
  Object.entries(cacheOptions.value).forEach(([key, selected]) => {
    if (selected && storageItems.value[key as keyof typeof storageItems.value]) {
      totalBytes += storageItems.value[key as keyof typeof storageItems.value].sizeBytes
    }
  })
  return formatBytes(totalBytes)
})

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const selectAll = () => {
  Object.keys(cacheOptions.value).forEach(key => {
    cacheOptions.value[key as keyof typeof cacheOptions.value] = true
  })
}

const deselectAll = () => {
  Object.keys(cacheOptions.value).forEach(key => {
    cacheOptions.value[key as keyof typeof cacheOptions.value] = false
  })
}

const clearImages = () => {
  cacheOptions.value.images = true
  showClearModal.value = true
}

const clearVideos = () => {
  cacheOptions.value.videos = true
  showClearModal.value = true
}

const clearAll = () => {
  selectAll()
  showClearModal.value = true
}

const clearSelected = () => {
  showClearModal.value = true
}

const confirmClear = async () => {
  isClearing.value = true
  showClearModal.value = false

  try {
    const itemsToClear = Object.entries(cacheOptions.value)
      .filter(([_, value]) => value)
      .map(([key, _]) => key)

    await settingsApi.clearCache(itemsToClear)

    // Update storage items
    itemsToClear.forEach(key => {
      if (storageItems.value[key as keyof typeof storageItems.value]) {
        storageItems.value[key as keyof typeof storageItems.value].sizeBytes = 0
        storageItems.value[key as keyof typeof storageItems.value].size = '0 MB'
      }
    })

    deselectAll()
    showToast('РљСЌС€ СѓСЃРїРµС€РЅРѕ РѕС‡РёС‰РµРЅ!')
  } catch (error) {
    console.error('Error clearing cache:', error)
    showToast('РћС€РёР±РєР° РїСЂРё РѕС‡РёСЃС‚РєРµ РєСЌС€Р°')
  } finally {
    isClearing.value = false
  }
}

const resetSettings = () => {
  showResetModal.value = true
}

const confirmReset = async () => {
  try {
    await settingsApi.resetSettings()
    showResetModal.value = false
    showToast('РќР°СЃС‚СЂРѕР№РєРё СЃР±СЂРѕС€РµРЅС‹!')
    // Reload page to apply defaults
    window.location.reload()
  } catch (error) {
    console.error('Error resetting settings:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЃР±СЂРѕСЃРµ РЅР°СЃС‚СЂРѕРµРє')
  }
}

const getCacheItemName = (key: string) => {
  const item = storageItems.value[key as keyof typeof storageItems.value]
  return item ? item.name : key
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

.storage-chart {
  display: flex;
  gap: 30px;
  align-items: center;
}

.chart-container {
  flex-shrink: 0;
}

.chart-circle {
  position: relative;
  width: 150px;
  height: 150px;
}

.circular-chart {
  display: block;
  margin: 0;
  max-width: 100%;
  max-height: 100%;
}

.circle-bg {
  fill: none;
  stroke: var(--border-color);
  stroke-width: 3;
}

.circle {
  fill: none;
  stroke: var(--primary-color);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s;
}

.chart-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.chart-percent {
  font-size: 24px;
  font-weight: 600;
  display: block;
}

.chart-label {
  font-size: 12px;
  color: var(--secondary-text);
}

.storage-details {
  flex: 1;
}

.total-storage {
  font-size: 18px;
  margin-bottom: 20px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.total-label {
  color: var(--secondary-text);
}

.total-value {
  font-weight: 600;
  color: var(--primary-color);
}

.storage-breakdown {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--card-bg);
  border-radius: 4px;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.item-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.item-name {
  font-size: 14px;
}

.item-size {
  font-weight: 500;
}

.cache-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.cache-item {
  display: block;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cache-item:hover {
  background: var(--hover-bg);
}

.cache-item input[type="checkbox"] {
  display: none;
}

.cache-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.cache-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cache-icon {
  font-size: 24px;
}

.cache-name {
  flex: 1;
  font-weight: 500;
}

.cache-size {
  font-weight: 600;
  color: var(--primary-color);
}

.cache-desc {
  font-size: 13px;
  color: var(--secondary-text);
  padding-left: 34px;
}

.selection-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 6px;
}

.summary-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.summary-label {
  font-size: 13px;
  color: var(--secondary-text);
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
}

.select-actions {
  display: flex;
  gap: 10px;
}

.select-btn {
  padding: 8px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-action:hover {
  border-color: var(--primary-color);
}

.quick-action.danger {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.05);
}

.quick-action.danger:hover {
  background: rgba(244, 67, 54, 0.1);
}

.action-icon {
  font-size: 28px;
}

.action-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.action-name {
  font-weight: 500;
}

.action-size {
  font-size: 13px;
  color: var(--secondary-text);
}

.auto-clean-settings {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.auto-clean-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.auto-clean-option input[type="checkbox"] {
  margin: 0;
}

.auto-clean-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.auto-clean-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.auto-clean-desc {
  font-size: 13px;
  color: var(--secondary-text);
}

.auto-clean-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.option-row label {
  font-weight: 500;
}

.threshold-select, .age-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--card-bg);
  color: var(--text-color);
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.clear-btn, .reset-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.clear-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
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
  max-width: 450px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.modal-content {
  margin-bottom: 20px;
}

.modal-content p {
  margin-bottom: 15px;
}

.modal-items-list {
  padding: 15px;
  background: var(--hover-bg);
  border-radius: 6px;
  margin-bottom: 15px;
}

.modal-item {
  display: block;
  margin-bottom: 5px;
}

.modal-total {
  padding: 10px 15px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 6px;
  margin-bottom: 15px;
}

.modal-warning {
  padding: 15px;
  background: rgba(244, 67, 54, 0.1);
  border-left: 4px solid #f44336;
  border-radius: 4px;
}

.modal-warning p {
  margin: 10px 0 0 0;
  font-size: 14px;
}

.danger-modal {
  border-color: #f44336;
}

.reset-warning {
  padding: 15px;
  background: var(--hover-bg);
  border-radius: 6px;
  margin-bottom: 15px;
}

.reset-warning ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.reset-warning li {
  margin-bottom: 5px;
  color: var(--secondary-text);
}

.warning-text {
  font-size: 14px;
  color: var(--secondary-text);
  margin-bottom: 15px;
}

.modal-actions {
  display: flex;
  gap: 10px;
}

.cancel-btn {
  flex: 1;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  flex: 1;
  padding: 10px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn.danger {
  background: #f44336;
}

@media (max-width: 768px) {
  .storage-chart {
    flex-direction: column;
  }
  
  .chart-circle {
    width: 120px;
    height: 120px;
  }
  
  .chart-percent {
    font-size: 20px;
  }
}
</style>
