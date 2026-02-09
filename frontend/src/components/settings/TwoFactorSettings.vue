<template>
  <div class="settings-section">
    <h2>Двухфакторная аутентификация</h2>

    <div class="twofa-status">
      <div class="status-header">
        <h3>🔒 Двухфакторная аутентификация</h3>
        <div class="status-indicator" :class="{ enabled: twofaStatus.is_enabled }">
          <span v-if="twofaStatus.is_enabled">● Включена</span>
          <span v-else>○ Отключена</span>
        </div>
      </div>

      <p>Требуйте код из приложения для подтверждения входа на новых устройствах.</p>
    </div>

    <!-- Setup Section -->
    <div v-if="!twofaStatus.is_enabled" class="setup-section">
      <h3>1. 📱 Установите приложение</h3>
      <p>Установите приложение Google Authenticator, Authy или Microsoft Authenticator</p>

      <div v-if="showSetup" class="setup-steps">
        <h3>2. 📷 Отсканируйте QR-код</h3>
        <div class="qr-container">
          <img v-if="qrCode" :src="qrCode" alt="QR Code" class="qr-code">
          <p>Или введите код вручную:</p>
          <code class="secret-code">{{ secret }}</code>
        </div>

        <h3>3. 🔢 Введите 6-значный код</h3>
        <div class="code-input">
          <input
            v-model="verificationCode"
            type="text"
            maxlength="6"
            placeholder="000000"
            class="code-field"
            @input="formatCode"
          >
          <button @click="verifyCode" :disabled="!verificationCode || verificationCode.length !== 6" class="verify-btn">
            ✅ Подтвердить
          </button>
        </div>
      </div>

      <button v-if="!showSetup" @click="startSetup" class="setup-btn">
        Начать настройку 2FA
      </button>
    </div>

    <!-- Enabled Section -->
    <div v-else class="enabled-section">
      <div class="settings-group">
        <h3>⚙️ Дополнительные настройки</h3>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="requireOnNewDevice" @change="updateSettings">
            Требовать при входе с нового устройства
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="rememberDevice" @change="updateSettings">
            Запоминать это устройство на {{ rememberDays }} дней
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="useBackupCodes" @change="updateSettings">
            Разрешить вход по резервным кодам
          </label>
        </div>
      </div>

      <div class="backup-codes-section">
        <h3>📋 Резервные коды (осталось: {{ backupCodes.length }})</h3>

        <div v-if="showBackupCodes" class="backup-codes-list">
          <div v-for="(code, index) in backupCodes" :key="index" class="backup-code-item">
            {{ index + 1 }}. {{ code }}
          </div>
        </div>

        <div class="backup-actions">
          <button @click="showBackupCodes = !showBackupCodes" class="toggle-btn">
            {{ showBackupCodes ? 'Скрыть' : 'Показать' }} коды
          </button>
          <button @click="copyBackupCodes" class="copy-btn">📋 Скопировать все</button>
          <button @click="regenerateBackupCodes" class="regenerate-btn">🔄 Сгенерировать новые</button>
        </div>
      </div>

      <div class="alternative-methods">
        <h3>📞 Альтернативные методы</h3>

        <div class="method-item">
          <label class="method-label">
            <input type="checkbox" v-model="smsEnabled" @change="updateSmsSettings">
            📱 SMS на {{ userPhone }}
          </label>
        </div>

        <div class="method-item">
          <label class="method-label">
            <input type="checkbox" v-model="emailBackupEnabled" @change="updateEmailSettings">
            📧 Email на {{ userEmail }}
          </label>
        </div>
      </div>

      <div class="danger-zone">
        <h3>⚠️ Опасная зона</h3>
        <button @click="showDisableConfirm = true" class="disable-btn">
          🚫 Отключить двухфакторную аутентификацию
        </button>
      </div>
    </div>

    <!-- Disable Confirmation Modal -->
    <div v-if="showDisableConfirm" class="modal-overlay" @click="showDisableConfirm = false">
      <div class="modal" @click.stop>
        <h3>Отключить 2FA?</h3>
        <p>Вы уверены, что хотите отключить двухфакторную аутентификацию? Это сделает ваш аккаунт менее защищенным.</p>

        <div class="password-confirm">
          <label>Введите пароль для подтверждения:</label>
          <input v-model="disablePassword" type="password" class="password-field">
        </div>

        <div class="modal-actions">
          <button @click="showDisableConfirm = false" class="cancel-btn">Отмена</button>
          <button @click="disable2FA" :disabled="!disablePassword" class="confirm-btn">Отключить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

// Reactive data
const twofaStatus = ref({
  is_enabled: false,
  secret_key: '',
  backup_codes: [] as string[],
  phone_number: '',
  email_enabled: true,
  require_on_new_device: true,
  remember_device_days: 30
})

const showSetup = ref(false)
const secret = ref('')
const qrCode = ref('')
const verificationCode = ref('')
const showBackupCodes = ref(false)
const showDisableConfirm = ref(false)
const disablePassword = ref('')

const requireOnNewDevice = ref(true)
const rememberDevice = ref(true)
const rememberDays = ref(30)
const useBackupCodes = ref(true)
const smsEnabled = ref(false)
const emailBackupEnabled = ref(true)

const authStore = useAuthStore()

const userPhone = computed(() => {
  return authStore.user?.phone_number ? `+${authStore.user.phone_number.slice(-4)}` : 'не указан'
})

const userEmail = computed(() => {
  return authStore.user?.email ? authStore.user.email.replace(/(.{3}).*(@.*)/, '$1***$2') : 'не указан'
})

const backupCodes = computed(() => twofaStatus.value.backup_codes || [])

// Methods
const fetch2FAStatus = async () => {
  try {
    const response = await apiClient.get('/users/2fa/status/')
    twofaStatus.value = response.data
    updateLocalSettings()
  } catch (error) {
    console.error('Error fetching 2FA status:', error)
  }
}

const startSetup = async () => {
  try {
    const response = await apiClient.post('/users/2fa/enable/')
    const data = response.data
    secret.value = data.secret
    qrCode.value = data.qr_code
    showSetup.value = true
  } catch (error) {
    console.error('Error starting 2FA setup:', error)
  }
}

const formatCode = () => {
  verificationCode.value = verificationCode.value.replace(/\D/g, '').slice(0, 6)
}

const verifyCode = async () => {
  try {
    await apiClient.post('/users/2fa/verify/', { code: verificationCode.value })
    await fetch2FAStatus()
    showSetup.value = false
    verificationCode.value = ''
  } catch (error) {
    console.error('Error verifying code:', error)
  }
}

const updateSettings = async () => {
  // Update 2FA settings
}

const updateSmsSettings = async () => {
  // Update SMS settings
}

const updateEmailSettings = async () => {
  // Update email backup settings
}

const regenerateBackupCodes = async () => {
  try {
    await apiClient.post('/users/2fa/backup-codes/')
    await fetch2FAStatus()
  } catch (error) {
    console.error('Error regenerating backup codes:', error)
  }
}

const copyBackupCodes = () => {
  const codes = backupCodes.value.join('\n')
  navigator.clipboard.writeText(codes)
}

const disable2FA = async () => {
  try {
    await apiClient.post('/users/2fa/disable/', { password: disablePassword.value })
    await fetch2FAStatus()
    showDisableConfirm.value = false
    disablePassword.value = ''
  } catch (error) {
    console.error('Error disabling 2FA:', error)
  }
}

const updateLocalSettings = () => {
  requireOnNewDevice.value = twofaStatus.value.require_on_new_device
  rememberDevice.value = twofaStatus.value.remember_device_days > 0
  rememberDays.value = twofaStatus.value.remember_device_days
  smsEnabled.value = !!twofaStatus.value.phone_number
  emailBackupEnabled.value = twofaStatus.value.email_enabled
}

onMounted(() => {
  fetch2FAStatus()
})
</script>

<style scoped>
.twofa-status {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.status-header h3 {
  margin: 0;
  font-size: 18px;
}

.status-indicator {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.status-indicator.enabled {
  background: #4caf50;
  color: white;
}

.status-indicator:not(.enabled) {
  background: #9e9e9e;
  color: white;
}

.setup-section, .enabled-section {
  margin-bottom: 30px;
}

.setup-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.setup-steps {
  margin-top: 20px;
}

.qr-container {
  text-align: center;
  margin: 20px 0;
}

.qr-code {
  width: 200px;
  height: 200px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.secret-code {
  display: block;
  background: var(--hover-bg);
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  margin: 10px 0;
  word-break: break-all;
}

.code-input {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 20px 0;
}

.code-field {
  flex: 1;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 18px;
  text-align: center;
  font-family: monospace;
  max-width: 200px;
}

.verify-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
}

.verify-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings-group {
  margin-bottom: 30px;
}

.settings-group h3 {
  margin-bottom: 15px;
  font-size: 16px;
}

.setting-item, .method-item {
  margin-bottom: 12px;
}

.setting-label, .method-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.backup-codes-section {
  margin-bottom: 30px;
}

.backup-codes-list {
  background: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
  font-family: monospace;
  font-size: 14px;
}

.backup-code-item {
  margin-bottom: 8px;
}

.backup-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.toggle-btn, .copy-btn, .regenerate-btn {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.copy-btn {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.danger-zone {
  border: 1px solid #f44336;
  border-radius: 8px;
  padding: 20px;
  background: rgba(244, 67, 54, 0.05);
}

.danger-zone h3 {
  color: #f44336;
  margin-bottom: 15px;
}

.disable-btn {
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
}

.password-confirm {
  margin-bottom: 20px;
}

.password-confirm label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.password-field {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-color);
  color: var(--text-color);
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

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>