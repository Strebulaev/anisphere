<template>
  <div class="settings-section">
    <h2>Сменить пароль</h2>

    <div class="settings-group">
      <h3>🔐 Процесс смены пароля</h3>
      <div class="password-steps">
        <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
          <div class="step-number">1</div>
          <div class="step-text">Введите текущий пароль</div>
        </div>
        <div class="step-arrow">↓</div>
        <div class="step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
          <div class="step-number">2</div>
          <div class="step-text">Введите новый пароль</div>
        </div>
        <div class="step-arrow">↓</div>
        <div class="step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
          <div class="step-number">3</div>
          <div class="step-text">Подтвердите пароль</div>
        </div>
        <div class="step-arrow">↓</div>
        <div class="step" :class="{ active: currentStep >= 4, completed: currentStep > 4 }">
          <div class="step-number">4</div>
          <div class="step-text">Код подтверждения</div>
        </div>
      </div>
    </div>

    <!-- Step 1-3: Password Input -->
    <div v-if="currentStep <= 3" class="settings-group">
      <h3>📝 Ввод паролей</h3>
      
      <div class="input-group">
        <label>Текущий пароль:</label>
        <div class="password-input">
          <input
            v-model="currentPassword"
            :type="showCurrentPassword ? 'text' : 'password'"
            placeholder="Введите текущий пароль"
            class="text-input"
            @input="validateCurrentPassword"
          />
          <button @click="showCurrentPassword = !showCurrentPassword" class="toggle-visibility">
            {{ showCurrentPassword ? '👁️' : '👁️‍🗨️' }}
          </button>
        </div>
      </div>

      <div class="input-group">
        <label>Новый пароль:</label>
        <div class="password-input">
          <input
            v-model="newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            placeholder="Введите новый пароль"
            class="text-input"
            @input="validateNewPassword"
          />
          <button @click="showNewPassword = !showNewPassword" class="toggle-visibility">
            {{ showNewPassword ? '👁️' : '👁️‍🗨️' }}
          </button>
        </div>
        
        <!-- Password Strength Indicator -->
        <div class="password-strength">
          <div class="strength-bar">
            <div class="strength-fill" :class="passwordStrengthClass" :style="{ width: passwordStrengthPercent + '%' }"></div>
          </div>
          <div class="strength-text">{{ passwordStrengthText }}</div>
        </div>

        <!-- Password Requirements -->
        <div class="password-requirements">
          <div :class="{ valid: hasMinLength }">✓ Минимум 8 символов</div>
          <div :class="{ valid: hasUppercase }">✓ Заглавная буква</div>
          <div :class="{ valid: hasLowercase }">✓ Строчная буква</div>
          <div :class="{ valid: hasNumber }">✓ Цифра</div>
          <div :class="{ valid: hasSpecialChar }">✓ Специальный символ</div>
        </div>
      </div>

      <div class="input-group">
        <label>Подтвердите новый пароль:</label>
        <div class="password-input">
          <input
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            placeholder="Повторите новый пароль"
            class="text-input"
            :class="{ 'has-error': confirmPassword && !passwordsMatch }"
            @input="validateConfirmPassword"
          />
          <button @click="showConfirmPassword = !showConfirmPassword" class="toggle-visibility">
            {{ showConfirmPassword ? '👁️' : '👁️‍🗨️' }}
          </button>
        </div>
        <span v-if="confirmPassword && !passwordsMatch" class="error-message">Пароли не совпадают</span>
      </div>

      <button 
        @click="initiatePasswordChange" 
        :disabled="!canProceed" 
        class="proceed-btn"
      >
        Продолжить →
      </button>
    </div>

    <!-- Step 4: Verification Code -->
    <div v-if="currentStep === 4" class="settings-group">
      <h3>🔐 Подтверждение смены пароля</h3>
      
      <p class="info-text">
        Для подтверждения смены пароля введите код, отправленный на ваш email или телефон.
      </p>

      <div class="verification-methods">
        <label class="method-option">
          <input type="radio" v-model="verificationMethod" value="email" />
          <span>📧 Email ({{ maskedEmail }})</span>
        </label>
        <label class="method-option">
          <input type="radio" v-model="verificationMethod" value="sms" />
          <span>📱 SMS ({{ maskedPhone }})</span>
        </label>
        <label v-if="hasBackupCodes" class="method-option">
          <input type="radio" v-model="verificationMethod" value="backup" />
          <span>🔑 Резервный код 2FA</span>
        </label>
      </div>

      <div class="input-group">
        <label>Код подтверждения:</label>
        <input
          v-model="verificationCode"
          type="text"
          placeholder="XXXXXX"
          class="code-input"
          maxlength="6"
          @input="validateCode"
        />
      </div>

      <div class="resend-section">
        <span v-if="cooldown > 0">Отправить код повторно через {{ cooldown }} сек</span>
        <button v-else @click="resendCode" class="resend-btn">Отправить код повторно</button>
      </div>

      <button 
        @click="confirmPasswordChange" 
        :disabled="!isCodeValid" 
        class="confirm-btn"
      >
        ✅ Подтвердить смену пароля
      </button>
    </div>

    <!-- Success State -->
    <div v-if="currentStep === 5" class="settings-group success-state">
      <div class="success-icon">✅</div>
      <h3>Пароль успешно изменён!</h3>
      <p class="success-message">
        Ваш пароль был успешно изменён. Все остальные сессии были завершены.
        Вам необходимо будет войти заново на всех устройствах.
      </p>
      <button @click="resetForm" class="ok-btn">Понятно</button>
    </div>

    <!-- Forgot Password Link -->
    <div v-if="currentStep <= 3" class="forgot-section">
      <p>Забыли текущий пароль?</p>
      <button @click="showForgotOptions = true" class="forgot-btn">Восстановить пароль</button>
    </div>

    <!-- Forgot Password Modal -->
    <div v-if="showForgotOptions" class="modal-overlay" @click="showForgotOptions = false">
      <div class="modal" @click.stop>
        <h3>Восстановление пароля</h3>
        <p>Выберите способ восстановления:</p>
        
        <div class="recovery-options">
          <button @click="recoverViaEmail" class="recovery-btn">
            📧 Через email
          </button>
          <button @click="recoverViaSMS" class="recovery-btn">
            📱 Через SMS
          </button>
          <button v-if="hasBackupCodes" @click="recoverViaBackupCodes" class="recovery-btn">
            🔑 Через резервные коды
          </button>
        </div>

        <button @click="showForgotOptions = false" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

const currentStep = ref(1)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const verificationMethod = ref('email')
const verificationCode = ref('')
const cooldown = ref(0)
const showForgotOptions = ref(false)

const maskedEmail = ref('u***@example.com')
const maskedPhone = ref('+7 (***) ***-**-67')
const hasBackupCodes = ref(false)

// Password strength computed
const hasMinLength = computed(() => newPassword.value.length >= 8)
const hasUppercase = computed(() => /[A-Z]/.test(newPassword.value))
const hasLowercase = computed(() => /[a-z]/.test(newPassword.value))
const hasNumber = computed(() => /[0-9]/.test(newPassword.value))
const hasSpecialChar = computed(() => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(newPassword.value))

const passwordStrength = computed(() => {
  let strength = 0
  if (hasMinLength.value) strength++
  if (hasUppercase.value) strength++
  if (hasLowercase.value) strength++
  if (hasNumber.value) strength++
  if (hasSpecialChar.value) strength++
  return strength
})

const passwordStrengthPercent = computed(() => {
  return (passwordStrength.value / 5) * 100
})

const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 1) return 'weak'
  if (strength <= 3) return 'medium'
  return 'strong'
})

const passwordStrengthText = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 1) return 'Слабый пароль'
  if (strength <= 3) return 'Средний пароль'
  return 'Сильный пароль'
})

const passwordsMatch = computed(() => {
  return newPassword.value === confirmPassword.value && newPassword.value.length > 0
})

const canProceed = computed(() => {
  return currentPassword.value.length > 0 &&
         hasMinLength.value &&
         hasUppercase.value &&
         hasLowercase.value &&
         hasNumber.value &&
         hasSpecialChar.value &&
         passwordsMatch.value
})

const isCodeValid = computed(() => {
  return verificationCode.value.length === 6 && /^\d+$/.test(verificationCode.value)
})

const validateCurrentPassword = () => {
  // Validation logic
}

const validateNewPassword = () => {
  // Validation is handled by computed properties
}

const validateConfirmPassword = () => {
  // Validation is handled by computed properties
}

const validateCode = () => {
  verificationCode.value = verificationCode.value.replace(/\D/g, '').slice(0, 6)
}

const initiatePasswordChange = async () => {
  try {
    await apiClient.post('/users/change-password/initiate/', {
      current_password: currentPassword.value,
      new_password: newPassword.value
    })
    currentStep.value = 4
    startCooldown()
  } catch (error) {
    console.error('Error initiating password change:', error)
    alert('Неверный текущий пароль')
  }
}

const resendCode = async () => {
  try {
    await apiClient.post('/users/change-password/resend-code/', {
      method: verificationMethod.value
    })
    startCooldown()
  } catch (error) {
    console.error('Error resending code:', error)
  }
}

const confirmPasswordChange = async () => {
  try {
    await apiClient.post('/users/change-password/confirm/', {
      code: verificationCode.value,
      method: verificationMethod.value
    })
    currentStep.value = 5
  } catch (error) {
    console.error('Error confirming password change:', error)
    alert('Неверный код подтверждения')
  }
}

const startCooldown = () => {
  cooldown.value = 60
  const interval = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0) {
      clearInterval(interval)
    }
  }, 1000)
}

const recoverViaEmail = () => {
  showForgotOptions.value = false
  // Navigate to password recovery
  alert('Ссылка для восстановления отправлена на email')
}

const recoverViaSMS = () => {
  showForgotOptions.value = false
  // Navigate to SMS recovery
  alert('Код для восстановления отправлен по SMS')
}

const recoverViaBackupCodes = () => {
  showForgotOptions.value = false
  // Navigate to backup code recovery
}

const resetForm = () => {
  currentStep.value = 1
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  verificationCode.value = ''
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

.password-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  flex-wrap: wrap;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step.active .step-number {
  background: var(--primary-color);
  color: white;
}

.step.completed .step-number {
  background: #4CAF50;
  color: white;
}

.step-text {
  font-size: 12px;
  color: var(--secondary-text);
  max-width: 100px;
  text-align: center;
}

.step-arrow {
  color: var(--border-color);
  font-size: 16px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.password-input {
  display: flex;
  gap: 10px;
}

.text-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
}

.text-input.has-error {
  border-color: #f44336;
}

.toggle-visibility {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  padding: 5px;
}

.password-strength {
  margin-top: 10px;
}

.strength-bar {
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s, background-color 0.3s;
}

.strength-fill.weak {
  background: #f44336;
}

.strength-fill.medium {
  background: #FFC107;
}

.strength-fill.strong {
  background: #4CAF50;
}

.strength-text {
  font-size: 13px;
  margin-top: 5px;
  color: var(--secondary-text);
}

.password-requirements {
  margin-top: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.password-requirements > div {
  font-size: 13px;
  color: var(--secondary-text);
  margin-bottom: 5px;
}

.password-requirements > div.valid {
  color: #4CAF50;
}

.code-input {
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 20px;
  letter-spacing: 10px;
  text-align: center;
  width: 200px;
}

.error-message {
  color: #f44336;
  font-size: 13px;
  margin-top: 5px;
}

.proceed-btn, .confirm-btn {
  width: 100%;
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.proceed-btn:disabled, .confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.verification-methods {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.method-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.method-option:hover {
  background: var(--hover-bg);
}

.resend-section {
  margin-top: 15px;
  text-align: center;
}

.resend-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: underline;
}

.success-state {
  text-align: center;
  padding: 40px 20px;
}

.success-icon {
  font-size: 60px;
  margin-bottom: 20px;
}

.success-message {
  color: var(--secondary-text);
  line-height: 1.6;
  margin-bottom: 20px;
}

.ok-btn {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.forgot-section {
  text-align: center;
  margin-top: 20px;
}

.forgot-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: underline;
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

.recovery-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 20px 0;
}

.recovery-btn {
  padding: 12px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
}

.recovery-btn:hover {
  background: var(--primary-color);
  color: white;
}

.cancel-btn {
  width: 100%;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}
</style>
