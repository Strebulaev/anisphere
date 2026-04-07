<template>
  <div class="settings-section">
    <h2>Двухфакторная аутентификация</h2>

    <div class="twofa-status">
      <div class="status-header">
        <h3><SakuraIcon name="lock" /> Двухфакторная аутентификация</h3>
        <div class="status-indicator" :class="{ enabled: twofaStatus.is_enabled }">
          <span v-if="twofaStatus.is_enabled">● Включена</span>
          <span v-else>○ Отключена</span>
        </div>
      </div>

      <p>Требуйте код из приложения для подтверждения входа на новых устройствах.</p>
    </div>

    <!-- Setup Section -->
    <div v-if="!twofaStatus.is_enabled" class="setup-section">
      <h3>1. <SakuraIcon name="phone" /> Установите приложение</h3>
      <p>Установите приложение Google Authenticator, Authy или Microsoft Authenticator</p>

      <div v-if="!authStore.user?.email_verified" class="warning-box">
        <p><SakuraIcon name="warning" />️ Для включения 2FA необходимо подтвердить email</p>
      </div>

      <div v-if="showSetup" class="setup-steps">
        <h3>2. <SakuraIcon name="camera" /> Отсканируйте QR-код</h3>
        <div class="qr-container">
          <img v-if="qrCode" :src="qrCode" alt="QR Code" class="qr-code">
          <p>Или введите этот код вручную в приложении:</p>
          <div class="secret-code-wrapper">
            <code class="secret-code">{{ secret }}</code>
            <button @click="copySecret" class="copy-secret-btn" title="Копировать"> <SakuraIcon name="clipboard" /> </button>
          </div>
        </div>

        <h3>3. 🔢 Введите 6-значный код из приложения</h3>
        <div class="code-input">
          <input
            v-model="verificationCode"
            type="text"
            maxlength="6"
            placeholder="000000"
            class="code-field"
            @input="formatCode"
            :disabled="isVerifying"
          >
          <button @click="verifyCode" :disabled="!verificationCode || verificationCode.length !== 6 || isVerifying" class="verify-btn">
            {{ isVerifying ? 'Проверка...' : '<SakuraIcon name="check" /> Подтвердить' }}
          </button>
        </div>
        <p v-if="verifyError" class="error-message">{{ verifyError }}</p>
        <button @click="cancelSetup" class="cancel-setup-btn">Отмена</button>
      </div>

      <button v-if="!showSetup" @click="startSetup" :disabled="!authStore.user?.email_verified" class="setup-btn">
        Начать настройку 2FA
      </button>
    </div>

    <!-- Enabled Section -->
    <div v-else class="enabled-section">
      <div class="settings-group">
        <h3><SakuraIcon name="settings" /> Дополнительные настройки</h3>

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
      </div>

      <div class="backup-codes-section">
        <h3><SakuraIcon name="clipboard" /> Резервные коды (осталось: {{ backupCodesCount }})</h3>
        <p class="section-description">
          Сохраните эти коды в безопасном месте. Они позволят вам войти в аккаунт, если вы потеряете доступ к приложению аутентификатора.
        </p>

        <div v-if="showBackupCodes" class="backup-codes-list">
          <div v-for="(code, index) in backupCodes" :key="index" class="backup-code-item">
            {{ index + 1 }}. {{ code }}
          </div>
        </div>

        <div class="backup-actions">
          <button @click="showBackupCodes = !showBackupCodes" class="toggle-btn">
            {{ showBackupCodes ? 'Скрыть' : 'Показать' }} коды
          </button>
          <button @click="copyBackupCodes" class="copy-btn"><SakuraIcon name="clipboard" /> Скопировать все</button>
          <button @click="showRegenerateConfirm = true" class="regenerate-btn"><SakuraIcon name="refresh" /> Сгенерировать новые</button>
        </div>
      </div>

      <div class="alternative-methods">
        <h3><SakuraIcon name="phone" /> Альтернативные методы</h3>

        <div class="method-item">
          <label class="method-label">
            <input type="checkbox" v-model="emailBackupEnabled" @change="updateSettings">
            <SakuraIcon name="mail" /> Email коды на {{ userEmail }}
          </label>
        </div>
      </div>

      <div class="security-log-section">
        <h3><SakuraIcon name="history" /> Лог безопасности</h3>
        <button @click="showSecurityLog = !showSecurityLog" class="toggle-btn">
          {{ showSecurityLog ? 'Скрыть' : 'Показать' }} историю
        </button>

        <div v-if="showSecurityLog" class="security-log-list">
          <div v-for="(log, index) in securityLog" :key="index" class="log-item">
            <div class="log-header">
              <span class="log-action">{{ formatLogAction(log.action) }}</span>
              <span class="log-date">{{ formatDate(log.created_at) }}</span>
            </div>
            <div class="log-details">
              IP: {{ log.ip_address }}
            </div>
          </div>
          <p v-if="securityLog.length === 0" class="no-logs">Нет записей</p>
        </div>
      </div>

      <div class="danger-zone">
        <h3><SakuraIcon name="warning" />️ Опасная зона</h3>
        <button @click="showDisableConfirm = true" class="disable-btn">
          <SakuraIcon name="ban" /> Отключить двухфакторную аутентификацию
        </button>
      </div>
    </div>

    <!-- Disable Confirmation Modal -->
    <div v-if="showDisableConfirm" class="modal-overlay" @click="closeDisableModal">
      <div class="modal" @click.stop>
        <h3>Отключить 2FA?</h3>
        <p>Вы уверены, что хотите отключить двухфакторную аутентификацию? Это сделает ваш аккаунт менее защищенным.</p>

        <div class="password-confirm">
          <label>Введите пароль для подтверждения:</label>
          <input v-model="disablePassword" type="password" class="password-field">
          <p v-if="disableError" class="error-message">{{ disableError }}</p>
        </div>

        <div class="modal-actions">
          <button @click="closeDisableModal" class="cancel-btn">Отмена</button>
          <button @click="disable2FA" :disabled="!disablePassword || isDisabling" class="confirm-btn">
            {{ isDisabling ? 'Отключение...' : 'Отключить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Regenerate Backup Codes Modal -->
    <div v-if="showRegenerateConfirm" class="modal-overlay" @click="closeRegenerateModal">
      <div class="modal" @click.stop>
        <h3>Сгенерировать новые коды?</h3>
        <p>Все старые резервные коды перестанут работать. Убедитесь, что у вас есть доступ к приложению аутентификатора.</p>

        <div class="password-confirm">
          <label>Введите пароль для подтверждения:</label>
          <input v-model="regeneratePassword" type="password" class="password-field">
          <p v-if="regenerateError" class="error-message">{{ regenerateError }}</p>
        </div>

        <div class="modal-actions">
          <button @click="closeRegenerateModal" class="cancel-btn">Отмена</button>
          <button @click="regenerateBackupCodes" :disabled="!regeneratePassword || isRegenerating" class="confirm-btn">
            {{ isRegenerating ? 'Генерация...' : 'Сгенерировать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import * as settingsApi from '@/api/settings'

// Reactive data
const twofaStatus = ref({
  is_enabled: false,
  secret_key: '',
  backup_codes: [] as string[],
  phone_number: '',
  email_enabled: true,
  require_on_new_device: true,
  remember_device_days: 30,
  backup_codes_count: 0
})

const showSetup = ref(false)
const secret = ref('')
const qrCode = ref('')
const verificationCode = ref('')
const verifyError = ref('')
const showBackupCodes = ref(false)
const showSecurityLog = ref(false)
const showDisableConfirm = ref(false)
const showRegenerateConfirm = ref(false)
const disablePassword = ref('')
const regeneratePassword = ref('')
const disableError = ref('')
const regenerateError = ref('')
const isDisabling = ref(false)
const isRegenerating = ref(false)
const isVerifying = ref(false)

const requireOnNewDevice = ref(true)
const rememberDevice = ref(true)
const rememberDays = ref(30)
const emailBackupEnabled = ref(true)

const securityLog = ref<any[]>([])

const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

const authStore = useAuthStore()

const userEmail = computed(() => {
  return authStore.user?.email ? authStore.user.email.replace(/(.{3}).*(@.*)/, '$1***$2') : 'не указан'
})

const backupCodes = computed(() => twofaStatus.value.backup_codes || [])
const backupCodesCount = computed(() => twofaStatus.value.backup_codes_count || backupCodes.value.length)

// Methods
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const fetch2FAStatus = async () => {
  try {
    const data = await settingsApi.getTwoFactorStatus()
    twofaStatus.value = data
    updateLocalSettings()
  } catch (error: any) {
    console.error('Error fetching 2FA status:', error)
    if (error.response?.data?.error) {
      showToast(error.response.data.error, 'error')
    }
  }
}

const startSetup = async () => {
  verifyError.value = ''
  try {
    const data = await settingsApi.enableTwoFactor()
    secret.value = data.secret
    qrCode.value = data.qr_code
    showSetup.value = true
    showToast(data.message || 'Сканируйте QR-код в приложении аутентификатора')
  } catch (error: any) {
    console.error('Error starting 2FA setup:', error)
    if (error.response?.data?.error) {
      showToast(error.response.data.error, 'error')
      if (error.response.data.missing === 'email') {
        showToast('Подтвердите email для включения 2FA', 'error')
      }
    }
  }
}

const cancelSetup = () => {
  showSetup.value = false
  secret.value = ''
  qrCode.value = ''
  verificationCode.value = ''
  verifyError.value = ''
}

const copySecret = () => {
  navigator.clipboard.writeText(secret.value).then(() => {
    showToast('Секретный код скопирован')
  }).catch(() => {
    showToast('Ошибка копирования', 'error')
  })
}

const formatCode = () => {
  verificationCode.value = verificationCode.value.replace(/\D/g, '').slice(0, 6)
}

const verifyCode = async () => {
  verifyError.value = ''
  isVerifying.value = true
  try {
    const data = await settingsApi.verifyTwoFactor(verificationCode.value)
    await fetch2FAStatus()
    showSetup.value = false
    verificationCode.value = ''
    verifyError.value = ''
    showToast(data.message || '2FA успешно включена!')
  } catch (error: any) {
    console.error('Error verifying code:', error)
    if (error.response?.data?.error) {
      verifyError.value = error.response.data.error
      showToast(error.response.data.error, 'error')
    } else {
      verifyError.value = 'Неверный код. Попробуйте еще раз.'
      showToast('Неверный код. Попробуйте еще раз.', 'error')
    }
  } finally {
    isVerifying.value = false
  }
}

const updateSettings = async () => {
  try {
    await settingsApi.updateTwoFactorSettings({
      require_on_new_device: requireOnNewDevice.value,
      remember_device_days: rememberDevice.value ? rememberDays.value : 0,
      email_enabled: emailBackupEnabled.value
    })
    showToast('Настройки 2FA обновлены')
  } catch (error: any) {
    console.error('Error updating 2FA settings:', error)
    if (error.response?.data?.error) {
      showToast(error.response.data.error, 'error')
    }
  }
}

const fetchBackupCodes = async () => {
  try {
    const data = await settingsApi.getBackupCodes()
    twofaStatus.value.backup_codes = data.codes || []
  } catch (error: any) {
    console.error('Error fetching backup codes:', error)
    if (error.response?.data?.error) {
      showToast(error.response.data.error, 'error')
    }
  }
}

// Watch showBackupCodes to load codes when shown
watch(showBackupCodes, async (show) => {
  if (show && backupCodes.value.length === 0) {
    await fetchBackupCodes()
  }
})

// Watch showSecurityLog to load log when shown
watch(showSecurityLog, async (show) => {
  if (show && securityLog.value.length === 0) {
    await fetchSecurityLog()
  }
})

const regenerateBackupCodes = async () => {
  regenerateError.value = ''
  isRegenerating.value = true

  try {
    const data = await settingsApi.regenerateBackupCodes(regeneratePassword.value)
    twofaStatus.value.backup_codes = data.codes || []
    await fetch2FAStatus()
    closeRegenerateModal()
    showBackupCodes.value = true
    showToast(data.message || 'Новые резервные коды сгенерированы')
  } catch (error: any) {
    console.error('Error regenerating backup codes:', error)
    if (error.response?.data?.error) {
      regenerateError.value = error.response.data.error
    }
  } finally {
    isRegenerating.value = false
  }
}

const copyBackupCodes = () => {
  const codes = backupCodes.value.join('\n')
  navigator.clipboard.writeText(codes).then(() => {
    showToast('Коды скопированы в буфер обмена')
  }).catch(() => {
    showToast('Ошибка копирования', 'error')
  })
}

const fetchSecurityLog = async () => {
  try {
    const data = await settingsApi.getTwoFactorSecurityLog()
    securityLog.value = data.logs || []
  } catch (error: any) {
    console.error('Error fetching security log:', error)
    if (error.response?.data?.error) {
      showToast(error.response.data.error, 'error')
    }
  }
}

const disable2FA = async () => {
  disableError.value = ''
  isDisabling.value = true

  try {
    await settingsApi.disableTwoFactor(disablePassword.value)
    await fetch2FAStatus()
    closeDisableModal()
    showToast('2FA отключена')
  } catch (error: any) {
    console.error('Error disabling 2FA:', error)
    if (error.response?.data?.error) {
      disableError.value = error.response.data.error
    }
  } finally {
    isDisabling.value = false
  }
}

const closeDisableModal = () => {
  showDisableConfirm.value = false
  disablePassword.value = ''
  disableError.value = ''
}

const closeRegenerateModal = () => {
  showRegenerateConfirm.value = false
  regeneratePassword.value = ''
  regenerateError.value = ''
}

const updateLocalSettings = () => {
  requireOnNewDevice.value = twofaStatus.value.require_on_new_device
  rememberDevice.value = twofaStatus.value.remember_device_days > 0
  rememberDays.value = twofaStatus.value.remember_device_days
  emailBackupEnabled.value = twofaStatus.value.email_enabled
}

const formatLogAction = (action: string) => {
  const actions: Record<string, string> = {
    '2fa_setup_started': 'Начало настройки',
    '2fa_enabled': 'Включение 2FA',
    '2fa_disabled': 'Отключение 2FA',
    '2fa_backup_code_used': 'Использование резервного кода',
    '2fa_backup_codes_regenerated': 'Генерация новых кодов',
    '2fa_settings_updated': 'Обновление настроек'
  }
  return actions[action] || action
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Только что'
  if (diffMins < 60) return `${diffMins} мин. назад`
  if (diffHours < 24) return `${diffHours} ч. назад`
  if (diffDays < 7) return `${diffDays} дн. назад`

  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
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

.warning-box {
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
}

.warning-box p {
  margin: 0;
  color: #ffc107;
  font-weight: 500;
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

.secret-code-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 10px 0;
}

.secret-code {
  background: var(--hover-bg);
  padding: 10px 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  letter-spacing: 1px;
  word-break: break-all;
  border: 1px solid var(--border-color);
}

.copy-secret-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 10px;
  cursor: pointer;
  font-size: 16px;
  opacity: 0.7;
}

.copy-secret-btn:hover {
  opacity: 1;
}

.code-input {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 20px 0;
}

.cancel-setup-btn {
  background: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.cancel-setup-btn:hover {
  background: var(--border-color);
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

.section-description {
  color: var(--secondary-text);
  font-size: 14px;
  margin-bottom: 15px;
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

.alternative-methods {
  margin-bottom: 30px;
}

.alternative-methods h3 {
  margin-bottom: 15px;
  font-size: 16px;
}

.security-log-section {
  margin-bottom: 30px;
}

.security-log-section h3 {
  margin-bottom: 15px;
  font-size: 16px;
}

.security-log-list {
  background: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.log-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.log-item:last-child {
  border-bottom: none;
}

.log-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.log-action {
  font-weight: 500;
}

.log-date {
  color: var(--secondary-text);
  font-size: 12px;
}

.log-details {
  color: var(--secondary-text);
  font-size: 13px;
}

.no-logs {
  text-align: center;
  color: var(--secondary-text);
  padding: 20px;
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

.code-input .error-message {
  margin-top: 10px;
  text-align: center;
}

.error-message {
  color: #f44336;
  font-size: 13px;
  margin-top: 5px;
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

.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  background: #4caf50;
}

.toast.error {
  background: #f44336;
}

@keyframes slideIn {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>