<template>
  <div class="settings-section">
    <h2>Очистка кэша</h2>

    <div class="settings-group">
      <h3>📊 Использование памяти</h3>
      
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
              <div class="chart-label">Занято</div>
            </div>
          </div>
        </div>

        <div class="storage-details">
          <div class="total-storage">
            <span class="total-label">Всего:</span>
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
      <h3>🧹 Выберите, что очистить</h3>
      
      <div class="cache-items">
        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.images" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🖼️</span>
              <span class="cache-name">Кэш изображений</span>
              <span class="cache-size">{{ storageItems.images.size }}</span>
            </div>
            <div class="cache-desc">Аватары, постеры, превью</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.videos" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🎬</span>
              <span class="cache-name">Кэш видео</span>
              <span class="cache-size">{{ storageItems.videos.size }}</span>
            </div>
            <div class="cache-desc">Сохранённые видео и превью</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.search" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🔍</span>
              <span class="cache-name">Кэш поиска</span>
              <span class="cache-size">{{ storageItems.search.size }}</span>
            </div>
            <div class="cache-desc">История поиска и результаты</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.history" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">📺</span>
              <span class="cache-name">История просмотров</span>
              <span class="cache-size">{{ storageItems.history.size }}</span>
            </div>
            <div class="cache-desc">Локальная история просмотров</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.cookies" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🍪</span>
              <span class="cache-name">Cookie и сессии</span>
              <span class="cache-size">{{ storageItems.cookies.size }}</span>
            </div>
            <div class="cache-desc">Данные авторизации (выйдет из аккаунта)</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.posters" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🎴</span>
              <span class="cache-name">Загруженные постеры</span>
              <span class="cache-size">{{ storageItems.posters.size }}</span>
            </div>
            <div class="cache-desc">Постеры аниме и персонажей</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.thumbnails" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🖼️</span>
              <span class="cache-name">Миниатюры</span>
              <span class="cache-size">{{ storageItems.thumbnails.size }}</span>
            </div>
            <div class="cache-desc">Миниатюры видео и изображений</div>
          </div>
        </label>

        <label class="cache-item">
          <input type="checkbox" v-model="cacheOptions.temp" />
          <div class="cache-info">
            <div class="cache-header">
              <span class="cache-icon">🗑️</span>
              <span class="cache-name">Временные файлы</span>
              <span class="cache-size">{{ storageItems.temp.size }}</span>
            </div>
            <div class="cache-desc">Временные данные загрузки</div>
          </div>
        </label>
      </div>

      <div class="selection-summary">
        <div class="summary-info">
          <span class="summary-label">Выбрано для очистки:</span>
          <span class="summary-value">{{ selectedSize }}</span>
        </div>
        
        <div class="select-actions">
          <button @click="selectAll" class="select-btn">Выбрать всё</button>
          <button @click="deselectAll" class="select-btn">Снять выделение</button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>⚡ Быстрые действия</h3>
      
      <div class="quick-actions">
        <button @click="clearImages" class="quick-action">
          <span class="action-icon">🖼️</span>
          <div class="action-info">
            <span class="action-name">Очистить кэш изображений</span>
            <span class="action-size">{{ storageItems.images.size }}</span>
          </div>
        </button>

        <button @click="clearVideos" class="quick-action">
          <span class="action-icon">🎬</span>
          <div class="action-info">
            <span class="action-name">Удалить сохранённые видео</span>
            <span class="action-size">{{ storageItems.videos.size }}</span>
          </div>
        </button>

        <button @click="clearAll" class="quick-action danger">
          <span class="action-icon">🗑️</span>
          <div class="action-info">
            <span class="action-name">Очистить весь кэш</span>
            <span class="action-size">{{ totalUsed }}</span>
          </div>
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>⚙️ Автоматическая очистка</h3>
      
      <div class="auto-clean-settings">
        <label class="auto-clean-option">
          <input type="checkbox" v-model="autoCleanEnabled" />
          <span class="auto-clean-info">
            <span class="auto-clean-name">Автоматически очищать кэш</span>
            <span class="auto-clean-desc">Очищать старые данные для экономии места</span>
          </span>
        </label>

        <div v-if="autoCleanEnabled" class="auto-clean-options">
          <div class="option-row">
            <label>Когда очищать:</label>
            <select v-model="autoCleanThreshold" class="threshold-select">
              <option value="80">При достижении 80%</option>
              <option value="90">При достижении 90%</option>
              <option value="95">При достижении 95%</option>
            </select>
          </div>

          <div class="option-row">
            <label>Удалять данные старше:</label>
            <select v-model="autoCleanAge" class="age-select">
              <option value="7">7 дней</option>
              <option value="14">14 дней</option>
              <option value="30">30 дней</option>
              <option value="60">60 дней</option>
            </select>
          </div>

          <label class="auto-clean-option">
            <input type="checkbox" v-model="keepFavorites" />
            <span>Всегда сохранять избранное</span>
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
        {{ isClearing ? '🧹 Очистка...' : '🧹 Очистить выбранное' }}
      </button>
      <button @click="resetSettings" class="reset-btn">
        ↻ Сбросить все настройки
      </button>
    </div>

    <!-- Clear Confirmation Modal -->
    <div v-if="showClearModal" class="modal-overlay" @click="showClearModal = false">
      <div class="modal" @click.stop>
        <h3>Подтвердить очистку?</h3>
        
        <div class="modal-content">
          <p>Вы собираетесь очистить:</p>
          
          <div class="modal-items-list">
            <div v-for="(item, key) in cacheOptions" :key="key">
              <span v-if="item" class="modal-item">✓ {{ getCacheItemName(key) }}</span>
            </div>
          </div>

          <div class="modal-total">
            <strong>Объём:</strong> {{ selectedSize }}
          </div>

          <div class="modal-warning" v-if="cacheOptions.cookies">
            <strong>⚠️ Внимание:</strong>
            <p>Очистка cookies приведёт к выходу из аккаунта на этом устройстве.</p>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showClearModal = false" class="cancel-btn">Отмена</button>
          <button @click="confirmClear" class="confirm-btn danger">Очистить</button>
        </div>
      </div>
    </div>

    <!-- Reset Settings Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="showResetModal = false">
      <div class="modal danger-modal" @click.stop>
        <h3>⚠️ Сбросить все настройки?</h3>
        
        <p>Это действие сбросит все настройки приложения к значениям по умолчанию.</p>
        
        <div class="reset-warning">
          <strong>Что будет сброшено:</strong>
          <ul>
            <li>Настройки внешнего вида</li>
            <li>Настройки уведомлений</li>
            <li>Настройки приватности</li>
            <li>Все остальные настройки</li>
          </ul>
        </div>

        <p class="warning-text">Это действие не затронет ваши данные (плейлисты, историю и т.д.).</p>

        <div class="modal-actions">
          <button @click="showResetModal = false" class="cancel-btn">Отмена</button>
          <button @click="confirmReset" class="confirm-btn danger">Сбросить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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
  images: { id: 'images', name: 'Изображения', size: '450 MB', sizeBytes: 450 * 1024 * 1024, color: '#0084FF' },
  videos: { id: 'videos', name: 'Видео', size: '320 MB', sizeBytes: 320 * 1024 * 1024, color: '#4CAF50' },
  search: { id: 'search', name: 'Поиск', size: '15 MB', sizeBytes: 15 * 1024 * 1024, color: '#FFC107' },
  history: { id: 'history', name: 'История', size: '5 MB', sizeBytes: 5 * 1024 * 1024, color: '#9C27B0' },
  cookies: { id: 'cookies', name: 'Cookies', size: '2 MB', sizeBytes: 2 * 1024 * 1024, color: '#F44336' },
  posters: { id: 'posters', name: 'Постеры', size: '78 MB', sizeBytes: 78 * 1024 * 1024, color: '#00BCD4' },
  thumbnails: { id: 'thumbnails', name: 'Миниатюры', size: '85 MB', sizeBytes: 85 * 1024 * 1024, color: '#FF9800' },
  temp: { id: 'temp', name: 'Временные', size: '25 MB', sizeBytes: 25 * 1024 * 1024, color: '#607D8B' }
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
    alert('Кэш успешно очищен!')
  } catch (error) {
    console.error('Error clearing cache:', error)
    alert('Ошибка при очистке кэша')
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
    alert('Настройки сброшены!')
    // Reload page to apply defaults
    window.location.reload()
  } catch (error) {
    console.error('Error resetting settings:', error)
    alert('Ошибка при сбросе настроек')
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
