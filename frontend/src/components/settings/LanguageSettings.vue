<template>
  <div class="settings-section">
    <h2>Язык и регион</h2>

    <div class="settings-group">
      <h3>🗣️ Язык приложения</h3>
      <div class="language-options">
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="ru">
          <span class="language-name">Русский</span>
        </label>
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="en">
          <span class="language-name">English</span>
        </label>
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="es">
          <span class="language-name">Español</span>
        </label>
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="de">
          <span class="language-name">Deutsch</span>
        </label>
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="fr">
          <span class="language-name">Français</span>
        </label>
        <label class="language-option">
          <input type="radio" v-model="selectedLanguage" value="zh">
          <span class="language-name">中文</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="globe" /> Регион</h3>
      <div class="region-options">
        <label class="region-option" :class="{ active: selectedRegion === 'ru' }">
          <input type="radio" v-model="selectedRegion" value="ru">
          <span>Россия</span>
        </label>
        <label class="region-option" :class="{ active: selectedRegion === 'us' }">
          <input type="radio" v-model="selectedRegion" value="us">
          <span>США</span>
        </label>
        <label class="region-option" :class="{ active: selectedRegion === 'de' }">
          <input type="radio" v-model="selectedRegion" value="de">
          <span>Германия</span>
        </label>
        <label class="region-option" :class="{ active: selectedRegion === 'gb' }">
          <input type="radio" v-model="selectedRegion" value="gb">
          <span>Великобритания</span>
        </label>
        <label class="region-option" :class="{ active: selectedRegion === 'other' }">
          <input type="radio" v-model="selectedRegion" value="other">
          <span>Другое...</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="calendar" /> Формат даты</h3>
      <div class="format-options">
        <label class="format-option">
          <input type="radio" v-model="dateFormat" value="dd.mm.yyyy">
          <span>ДД.ММ.ГГГГ (15.07.2023)</span>
        </label>
        <label class="format-option">
          <input type="radio" v-model="dateFormat" value="mm/dd/yyyy">
          <span>ММ/ДД/ГГГГ (07/15/2023)</span>
        </label>
        <label class="format-option">
          <input type="radio" v-model="dateFormat" value="yyyy-mm-dd">
          <span>ГГГГ-ММ-ДД (2023-07-15)</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="one-oclock" /> Формат времени</h3>
      <div class="format-options">
        <label class="format-option">
          <input type="radio" v-model="timeFormat" value="24">
          <span>24 часа (14:30)</span>
        </label>
        <label class="format-option">
          <input type="radio" v-model="timeFormat" value="12">
          <span>12 часов (2:30 PM)</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📏 Единицы измерения</h3>
      <div class="units-options">
        <label class="units-option">
          <input type="radio" v-model="units" value="metric">
          <span>Метрическая система (км, м, см)</span>
        </label>
        <label class="units-option">
          <input type="radio" v-model="units" value="auto">
          <span>Автоматически</span>
        </label>
        <label class="units-option">
          <input type="radio" v-model="units" value="imperial">
          <span>Имперская система (мили, футы)</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="dollar" /> Валюта</h3>
      <div class="currency-options">
        <label class="currency-option" :class="{ active: currency === 'RUB' }">
          <input type="radio" v-model="currency" value="RUB">
          <span>RUB - Российский рубль (₽)</span>
        </label>
        <label class="currency-option" :class="{ active: currency === 'USD' }">
          <input type="radio" v-model="currency" value="USD">
          <span>USD - Доллар США ($)</span>
        </label>
        <label class="currency-option" :class="{ active: currency === 'EUR' }">
          <input type="radio" v-model="currency" value="EUR">
          <span>EUR - Евро (€)</span>
        </label>
        <label class="currency-option" :class="{ active: currency === 'CNY' }">
          <input type="radio" v-model="currency" value="CNY">
          <span>CNY - Китайский юань (¥)</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="thermometer" /> Температура</h3>
      <div class="temperature-options">
        <label class="temperature-option">
          <input type="radio" v-model="temperature" value="celsius">
          <span>°C (Цельсий)</span>
        </label>
        <label class="temperature-option">
          <input type="radio" v-model="temperature" value="fahrenheit">
          <span>°F (Фаренгейт)</span>
        </label>
        <label class="temperature-option">
          <input type="radio" v-model="temperature" value="auto">
          <span>Автоматически</span>
        </label>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        <SakuraIcon name="save" /> Сохранить
      </button>
      <button @click="suggestTranslation" class="suggest-btn">
        🌐 Предложить перевод
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'

// Reactive data
const selectedLanguage = ref('ru')
const selectedRegion = ref('ru')
const dateFormat = ref('dd.mm.yyyy')
const timeFormat = ref('24')
const units = ref('metric')
const currency = ref('RUB')
const temperature = ref('celsius')

const originalSettings = ref({
  language: 'ru',
  region: 'ru',
  dateFormat: 'dd.mm.yyyy',
  timeFormat: '24',
  units: 'metric',
  currency: 'RUB',
  temperature: 'celsius'
})

const hasChanges = computed(() => {
  return selectedLanguage.value !== originalSettings.value.language ||
         selectedRegion.value !== originalSettings.value.region ||
         dateFormat.value !== originalSettings.value.dateFormat ||
         timeFormat.value !== originalSettings.value.timeFormat ||
         units.value !== originalSettings.value.units ||
         currency.value !== originalSettings.value.currency ||
         temperature.value !== originalSettings.value.temperature
})

// Methods
const fetchSettings = async () => {
  try {
    // Fetch current language settings
    const response = await apiClient.get('/users/profile-settings/')
    const settings = response.data

    selectedLanguage.value = settings.language || 'ru'
    selectedRegion.value = 'ru' // Would be derived from timezone/country
    dateFormat.value = settings.date_format || 'dd.mm.yyyy'
    timeFormat.value = settings.time_format || '24'

    originalSettings.value = {
      language: selectedLanguage.value,
      region: selectedRegion.value,
      dateFormat: dateFormat.value,
      timeFormat: timeFormat.value,
      units: units.value,
      currency: currency.value,
      temperature: temperature.value
    }
  } catch (error) {
    console.error('Error fetching language settings:', error)
  }
}

const saveSettings = async () => {
  try {
    await apiClient.put('/users/profile-settings/', {
      language: selectedLanguage.value,
      date_format: dateFormat.value,
      time_format: timeFormat.value
    })

    originalSettings.value = {
      language: selectedLanguage.value,
      region: selectedRegion.value,
      dateFormat: dateFormat.value,
      timeFormat: timeFormat.value,
      units: units.value,
      currency: currency.value,
      temperature: temperature.value
    }

    // Show success message
  } catch (error) {
    console.error('Error saving language settings:', error)
  }
}

const suggestTranslation = () => {
  console.log('Suggesting translation...')
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.language-options, .region-options, .format-options, .units-options, .currency-options, .temperature-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.language-option, .region-option, .format-option, .units-option, .currency-option, .temperature-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.language-option:hover, .region-option:hover, .format-option:hover,
.units-option:hover, .currency-option:hover, .temperature-option:hover {
  background: var(--card-bg);
}

.region-option.active, .currency-option.active {
  background: var(--primary-color);
  color: white;
}

.language-option input[type="radio"], .region-option input[type="radio"],
.format-option input[type="radio"], .units-option input[type="radio"],
.currency-option input[type="radio"], .temperature-option input[type="radio"] {
  margin: 0;
}

.language-name {
  font-weight: 500;
  cursor: pointer;
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

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn, .suggest-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.save-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.suggest-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>