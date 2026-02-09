<template>
  <div class="settings-section">
    <h2>Расширенные настройки</h2>

    <div class="settings-group">
      <h3>⚡ Производительность</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="hardwareAcceleration">
          <span>Аппаратное ускорение</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="mediaCaching">
          <span>Кэширование медиа</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="lazyLoading">
          <span>Ленивая загрузка изображений</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="dataCompression">
          <span>Сжатие передаваемых данных</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🌐 Сеть</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="ipv6Support">
          <span>Использовать IPv6</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Предзагрузка медиа:</label>
        <select v-model="mediaPreload" class="setting-select">
          <option value="wifi">Только Wi-Fi</option>
          <option value="always">Всегда</option>
          <option value="never">Никогда</option>
        </select>
      </div>

      <div class="setting-item">
        <label>Лимит мобильного трафика:</label>
        <select v-model="mobileLimit" class="setting-select">
          <option value="50">50 MB</option>
          <option value="100">100 MB</option>
          <option value="200">200 MB</option>
          <option value="unlimited">Без ограничений</option>
        </select>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="compressOnRoaming">
          <span>Сжатие данных в роуминге</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>💾 Хранилище</h3>

      <div class="setting-item">
        <label>Автоочистка кэша:</label>
        <select v-model="cacheAutoClear" class="setting-select">
          <option value="7">7 дней</option>
          <option value="14">14 дней</option>
          <option value="30">30 дней</option>
          <option value="never">Никогда</option>
        </select>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="storeMediaOnSD">
          <span>Хранить медиа на SD карте</span>
        </label>
      </div>

      <div class="setting-item">
        <label>Лимит хранения медиа:</label>
        <select v-model="mediaStorageLimit" class="setting-select">
          <option value="500">500 MB</option>
          <option value="1000">1 GB</option>
          <option value="2000">2 GB</option>
          <option value="5000">5 GB</option>
        </select>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="encryptLocalData">
          <span>Шифрование локальных данных</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔒 Безопасность</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="connectionEncryption">
          <span>Шифрование соединения</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="certificateValidation">
          <span>Проверка сертификатов</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="disableScreenshots">
          <span>Запрет скриншотов</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="backgroundLock">
          <span>Блокировка в фоне</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🛠️ Отладка</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="developerMode">
          <span>Режим разработчика</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="logNetworkRequests">
          <span>Логирование сетевых запросов</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="sendErrorLogs">
          <span>Отправлять логи об ошибках</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="showFPS">
          <span>Показывать FPS</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔄 Автоматизация</h3>

      <div class="automation-item">
        <span>Автоответчик</span>
        <button class="configure-btn">Настроить →</button>
      </div>

      <div class="automation-item">
        <span>Фильтры сообщений</span>
        <button class="configure-btn">Настроить →</button>
      </div>

      <div class="automation-item">
        <span>Умные уведомления</span>
        <button class="configure-btn">Настроить →</button>
      </div>
    </div>

    <div class="settings-group">
      <h3>⚙️ Экспериментальные функции</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="newMessageEngine">
          <span>Новый движок сообщений</span>
        </label>
        <span class="experimental-badge">Бета</span>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="enhancedVideoCalls">
          <span>Улучшенные видеозвонки</span>
        </label>
        <span class="experimental-badge">Бета</span>
      </div>

      <div class="experimental-actions">
        <button class="beta-features-btn">Бета-функции →</button>
      </div>
    </div>

    <div class="danger-zone">
      <h3>⚠️ Сброс настроек</h3>
      <p>Это действие сбросит все настройки к значениям по умолчанию. Действие нельзя отменить.</p>
      <button @click="showResetConfirm = true" class="reset-btn">
        🔄 Сбросить все настройки
      </button>
    </div>

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetConfirm" class="modal-overlay" @click="showResetConfirm = false">
      <div class="modal" @click.stop>
        <h3>Сбросить все настройки?</h3>
        <p>Вы действительно хотите сбросить все настройки к значениям по умолчанию? Это действие нельзя отменить.</p>

        <div class="reset-warning">
          <strong>Что будет сброшено:</strong>
          <ul>
            <li>Настройки внешнего вида</li>
            <li>Настройки уведомлений</li>
            <li>Настройки приватности</li>
            <li>Настройки производительности</li>
            <li>Все остальные настройки</li>
          </ul>
        </div>

        <div class="modal-actions">
          <button @click="showResetConfirm = false" class="cancel-btn">Отмена</button>
          <button @click="resetAllSettings" class="confirm-btn">Сбросить все</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Reactive data
const hardwareAcceleration = ref(true)
const mediaCaching = ref(true)
const lazyLoading = ref(true)
const dataCompression = ref(true)

const ipv6Support = ref(true)
const mediaPreload = ref('wifi')
const mobileLimit = ref('100')
const compressOnRoaming = ref(true)

const cacheAutoClear = ref('7')
const storeMediaOnSD = ref(false)
const mediaStorageLimit = ref('1000')
const encryptLocalData = ref(true)

const connectionEncryption = ref(true)
const certificateValidation = ref(true)
const disableScreenshots = ref(false)
const backgroundLock = ref(true)

const developerMode = ref(false)
const logNetworkRequests = ref(false)
const sendErrorLogs = ref(true)
const showFPS = ref(false)

const newMessageEngine = ref(false)
const enhancedVideoCalls = ref(false)

const showResetConfirm = ref(false)

// Methods
const resetAllSettings = () => {
  // Reset all settings to defaults
  hardwareAcceleration.value = true
  mediaCaching.value = true
  lazyLoading.value = true
  dataCompression.value = true

  ipv6Support.value = true
  mediaPreload.value = 'wifi'
  mobileLimit.value = '100'
  compressOnRoaming.value = true

  cacheAutoClear.value = '7'
  storeMediaOnSD.value = false
  mediaStorageLimit.value = '1000'
  encryptLocalData.value = true

  connectionEncryption.value = true
  certificateValidation.value = true
  disableScreenshots.value = false
  backgroundLock.value = true

  developerMode.value = false
  logNetworkRequests.value = false
  sendErrorLogs.value = true
  showFPS.value = false

  newMessageEngine.value = false
  enhancedVideoCalls.value = false

  showResetConfirm.value = false
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

.setting-label input[type="checkbox"] {
  margin: 0;
}

.setting-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
  min-width: 120px;
}

.automation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.automation-item:last-child {
  border-bottom: none;
}

.configure-btn {
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.experimental-badge {
  background: #FF6D00;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.experimental-actions {
  margin-top: 15px;
}

.beta-features-btn {
  padding: 8px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.danger-zone {
  border: 1px solid #f44336;
  border-radius: 8px;
  padding: 20px;
  background: rgba(244, 67, 54, 0.05);
}

.danger-zone h3 {
  color: #f44336;
  margin-bottom: 10px;
}

.danger-zone p {
  margin-bottom: 15px;
  color: var(--secondary-text);
}

.reset-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
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
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.modal p {
  margin-bottom: 20px;
  color: var(--secondary-text);
  line-height: 1.5;
}

.reset-warning {
  background: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.reset-warning ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.reset-warning li {
  margin-bottom: 5px;
  color: var(--secondary-text);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
</style>