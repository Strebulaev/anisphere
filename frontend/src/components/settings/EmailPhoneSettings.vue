<template>
  <div class="settings-section">
    <h2>Email и телефон</h2>

    <!-- Email Section -->
    <div class="settings-group">
      <h3>📧 Email</h3>
      
      <div class="contact-info">
        <div class="current-info">
          <div class="info-label">Текущий email:</div>
          <div class="info-value">
            {{ maskedEmail }}
            <span v-if="emailVerified" class="verified-badge">✅ Подтверждён</span>
            <span v-else class="unverified-badge">⚠️ Не подтверждён</span>
          </div>
        </div>
      </div>

      <div class="info-benefits">
        <p>Что даёт подтверждённый email:</p>
        <ul>
          <li>✓ Восстановление пароля</li>
          <li>✓ Двухфакторная аутентификация</li>
          <li>✓ Важные уведомления о безопасности</li>
          <li>✓ Еженедельные дайджесты и отчёты</li>
        </ul>
      </div>

      <div class="action-buttons">
        <button v-if="!emailVerified" @click="showVerifyEmailModal = true" class="verify-btn">
          📧 Подтвердить email
        </button>
        <button @click="showChangeEmailModal = true" class="change-btn">
          ✏️ Изменить email
        </button>
      </div>
    </div>

    <!-- Phone Section -->
    <div class="settings-group">
      <h3>📱 Телефон</h3>
      
      <div class="contact-info">
        <div class="current-info">
          <div class="info-label">Текущий телефон:</div>
          <div class="info-value">
            {{ phone ? maskedPhone : 'Не указан' }}
            <span v-if="phone && phoneVerified" class="verified-badge">✅ Подтверждён</span>
            <span v-if="phone && !phoneVerified" class="unverified-badge">⚠️ Не подтверждён</span>
          </div>
        </div>
      </div>

      <div class="info-benefits">
        <p>Что даёт подтверждённый телефон:</p>
        <ul>
          <li>✓ Восстановление аккаунта через SMS</li>
          <li>✓ SMS-код для 2FA</li>
          <li>✓ Дополнительная безопасность</li>
          <li>✓ Уведомления о входе</li>
        </ul>
      </div>

      <div class="action-buttons">
        <button v-if="!phone" @click="showAddPhoneModal = true" class="add-btn">
          ➕ Добавить телефон
        </button>
        <template v-else>
          <button v-if="!phoneVerified" @click="showVerifyPhoneModal = true" class="verify-btn">
            📱 Подтвердить телефон
          </button>
          <button @click="showChangePhoneModal = true" class="change-btn">
            ✏️ Изменить телефон
          </button>
          <button @click="showRemovePhoneConfirm = true" class="remove-btn">
            🗑️ Удалить
          </button>
        </template>
      </div>
    </div>

    <!-- Change Email Modal -->
    <div v-if="showChangeEmailModal" class="modal-overlay" @click="showChangeEmailModal = false">
      <div class="modal" @click.stop>
        <h3>Изменить email</h3>
        
        <div class="change-steps">
          <div class="step" :class="{ active: emailChangeStep >= 1, completed: emailChangeStep > 1 }">
            <div class="step-number">1</div>
            <div class="step-text">Новый email</div>
          </div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: emailChangeStep >= 2, completed: emailChangeStep > 2 }">
            <div class="step-number">2</div>
            <div class="step-text">Код со старого</div>
          </div>
          <div class="step-arrow">→</div>
          <div class="step" :class="{ active: emailChangeStep >= 3, completed: emailChangeStep > 3 }">
            <div class="step-number">3</div>
            <div class="step-text">Код с нового</div>
          </div>
        </div>

        <!-- Step 1: Enter new email -->
        <div v-if="emailChangeStep === 1" class="modal-step">
          <div class="input-group">
            <label>Новый email:</label>
            <input
              v-model="newEmail"
              type="email"
              placeholder="new@example.com"
              class="text-input"
              :class="{ 'has-error': emailError }"
              @input="validateEmail"
            />
            <span v-if="emailError" class="error-message">{{ emailError }}</span>
          </div>
          
          <div class="input-group">
            <label>Подтвердите новый email:</label>
            <input
              v-model="confirmNewEmail"
              type="email"
              placeholder="new@example.com"
              class="text-input"
              :class="{ 'has-error': confirmEmailError }"
              @input="validateConfirmEmail"
            />
            <span v-if="confirmEmailError" class="error-message">{{ confirmEmailError }}</span>
          </div>

          <button @click="sendOldEmailCode" :disabled="!canProceedEmailChange" class="proceed-btn">
            Продолжить →
          </button>
        </div>

        <!-- Step 2: Code from old email -->
        <div v-if="emailChangeStep === 2" class="modal-step">
          <p class="info-text">
            Код подтверждения отправлен на {{ maskedEmail }}
          </p>
          
          <div class="input-group">
            <label>Код из старого email:</label>
            <input
              v-model="oldEmailCode"
              type="text"
              placeholder="XXXXXX"
              class="code-input"
              maxlength="6"
            />
          </div>

          <div class="resend-section">
            <span v-if="emailCooldown > 0">Отправить повторно через {{ emailCooldown }} сек</span>
            <button v-else @click="resendOldEmailCode" class="resend-btn">Отправить повторно</button>
          </div>

          <button @click="verifyOldEmailCode" :disabled="oldEmailCode.length !== 6" class="proceed-btn">
            Продолжить →
          </button>
        </div>

        <!-- Step 3: Code from new email -->
        <div v-if="emailChangeStep === 3" class="modal-step">
          <p class="info-text">
            Код подтверждения отправлен на {{ maskedNewEmail }}
          </p>
          
          <div class="input-group">
            <label>Код из нового email:</label>
            <input
              v-model="newEmailCode"
              type="text"
              placeholder="XXXXXX"
              class="code-input"
              maxlength="6"
            />
          </div>

          <div class="resend-section">
            <span v-if="emailCooldown > 0">Отправить повторно через {{ emailCooldown }} сек</span>
            <button v-else @click="resendNewEmailCode" class="resend-btn">Отправить повторно</button>
          </div>

          <button @click="confirmEmailChange" :disabled="newEmailCode.length !== 6" class="confirm-btn">
            ✅ Подтвердить изменение
          </button>
        </div>

        <button @click="closeEmailModal" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Verify Email Modal -->
    <div v-if="showVerifyEmailModal" class="modal-overlay" @click="showVerifyEmailModal = false">
      <div class="modal" @click.stop>
        <h3>Подтвердить email</h3>
        <p>Код подтверждения будет отправлен на {{ maskedEmail }}</p>
        
        <div class="input-group">
          <input
            v-model="verifyEmailCode"
            type="text"
            placeholder="XXXXXX"
            class="code-input"
            maxlength="6"
          />
        </div>

        <button @click="verifyEmail" :disabled="verifyEmailCode.length !== 6" class="confirm-btn">
          ✅ Подтвердить
        </button>
        <button @click="showVerifyEmailModal = false" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Add Phone Modal -->
    <div v-if="showAddPhoneModal" class="modal-overlay" @click="showAddPhoneModal = false">
      <div class="modal" @click.stop>
        <h3>Добавить телефон</h3>
        
        <div class="input-group">
          <label>Номер телефона:</label>
          <div class="phone-input">
            <select v-model="phoneCountry" class="country-select">
              <option value="+7">🇷🇺 +7</option>
              <option value="+380">🇺🇦 +380</option>
              <option value="+375">🇧🇾 +375</option>
              <option value="+998">🇺🇿 +998</option>
              <option value="+1">🇺🇸 +1</option>
            </select>
            <input
              v-model="phoneNumber"
              type="tel"
              placeholder="(999) 123-45-67"
              class="text-input"
              @input="formatPhone"
            />
          </div>
        </div>

        <button @click="addPhone" :disabled="!isValidPhone" class="proceed-btn">
          Продолжить →
        </button>
        <button @click="showAddPhoneModal = false" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Verify Phone Modal -->
    <div v-if="showVerifyPhoneModal" class="modal-overlay" @click="showVerifyPhoneModal = false">
      <div class="modal" @click.stop>
        <h3>Подтвердить телефон</h3>
        <p>SMS с кодом отправлена на {{ maskedPhone }}</p>
        
        <div class="input-group">
          <input
            v-model="verifyPhoneCode"
            type="text"
            placeholder="XXXXXX"
            class="code-input"
            maxlength="6"
          />
        </div>

        <button @click="verifyPhone" :disabled="verifyPhoneCode.length !== 6" class="confirm-btn">
          ✅ Подтвердить
        </button>
        <button @click="showVerifyPhoneModal = false" class="cancel-btn">Отмена</button>
      </div>
    </div>

    <!-- Remove Phone Confirm Modal -->
    <div v-if="showRemovePhoneConfirm" class="modal-overlay" @click="showRemovePhoneConfirm = false">
      <div class="modal danger-modal" @click.stop>
        <h3>⚠️ Удалить телефон?</h3>
        <p>Вы уверены, что хотите удалить привязанный телефон?</p>
        <p class="warning">Это действие:</p>
        <ul>
          <li>Отключит SMS-уведомления</li>
          <li>Отключит 2FA через SMS</li>
          <li>Уменьшит безопасность аккаунта</li>
        </ul>
        
        <div class="modal-actions">
          <button @click="showRemovePhoneConfirm = false" class="cancel-btn">Отмена</button>
          <button @click="removePhone" class="danger-btn">Удалить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'

const email = ref('')
const phone = ref('')
const emailVerified = ref(false)
const phoneVerified = ref(false)

const showChangeEmailModal = ref(false)
const showVerifyEmailModal = ref(false)
const showAddPhoneModal = ref(false)
const showVerifyPhoneModal = ref(false)
const showChangePhoneModal = ref(false)
const showRemovePhoneConfirm = ref(false)

// Email change state
const emailChangeStep = ref(1)
const newEmail = ref('')
const confirmNewEmail = ref('')
const oldEmailCode = ref('')
const newEmailCode = ref('')
const verifyEmailCode = ref('')
const emailCooldown = ref(0)

const emailError = ref('')
const confirmEmailError = ref('')

// Phone state
const phoneCountry = ref('+7')
const phoneNumber = ref('')
const verifyPhoneCode = ref('')

const maskedEmail = computed(() => {
  if (!email.value) return 'user@example.com'
  const [local, domain] = email.value.split('@')
  
  const maskedLocal = local?.[0] + '***' + local?.[local.length - 1]
  return maskedLocal + '@' + domain
})

const maskedNewEmail = computed(() => {
  if (!newEmail.value) return ''
  const [local, domain] = newEmail.value.split('@')
  
  const maskedLocal = local?.[0] + '***' + local?.[local.length - 1]
  return maskedLocal + '@' + domain
})

const maskedPhone = computed(() => {
  if (!phone.value) return ''
  const digits = phone.value.replace(/\D/g, '')
  if (digits.length < 10) return phone.value
  return phone.value.replace(/(\d{1,3})(\d{3})(\d{3})(\d{2})(\d{2})/, '$1 ($2) $3-$4-$5')
})

const canProceedEmailChange = computed(() => {
  return newEmail.value && 
         confirmNewEmail.value && 
         newEmail.value === confirmNewEmail.value &&
         !emailError.value &&
         !confirmEmailError.value
})

const isValidPhone = computed(() => {
  const digits = phoneNumber.value.replace(/\D/g, '')
  return digits.length === 10
})

const fetchContactInfo = async () => {
  try {
    const response = await apiClient.get('/users/contact-info/')
    email.value = response.data.email
    phone.value = response.data.phone
    emailVerified.value = response.data.email_verified
    phoneVerified.value = response.data.phone_verified
  } catch (error) {
    console.error('Error fetching contact info:', error)
  }
}

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newEmail.value)) {
    emailError.value = 'Некорректный email'
  } else if (newEmail.value === email.value) {
    emailError.value = 'Новый email должен отличаться от текущего'
  } else {
    emailError.value = ''
  }
}

const validateConfirmEmail = () => {
  if (newEmail.value !== confirmNewEmail.value) {
    confirmEmailError.value = 'Email не совпадает'
  } else {
    confirmEmailError.value = ''
  }
}

const sendOldEmailCode = async () => {
  try {
    await apiClient.post('/users/change-email/send-old-code/', {
      new_email: newEmail.value
    })
    emailChangeStep.value = 2
    startEmailCooldown()
  } catch (error) {
    console.error('Error sending old email code:', error)
  }
}

const verifyOldEmailCode = async () => {
  try {
    await apiClient.post('/users/change-email/verify-old-code/', {
      code: oldEmailCode.value
    })
    emailChangeStep.value = 3
  } catch (error) {
    console.error('Error verifying old email code:', error)
    alert('Неверный код')
  }
}

const resendOldEmailCode = async () => {
  await sendOldEmailCode()
}

const resendNewEmailCode = async () => {
  try {
    await apiClient.post('/users/change-email/resend-new-code/')
    startEmailCooldown()
  } catch (error) {
    console.error('Error resending new email code:', error)
  }
}

const confirmEmailChange = async () => {
  try {
    await apiClient.post('/users/change-email/confirm/', {
      code: newEmailCode.value
    })
    email.value = newEmail.value
    emailVerified.value = true
    closeEmailModal()
    alert('Email успешно изменён!')
  } catch (error) {
    console.error('Error confirming email change:', error)
    alert('Неверный код')
  }
}

const verifyEmail = async () => {
  try {
    await apiClient.post('/users/verify-email/', {
      code: verifyEmailCode.value
    })
    emailVerified.value = true
    showVerifyEmailModal.value = false
    alert('Email успешно подтверждён!')
  } catch (error) {
    console.error('Error verifying email:', error)
    alert('Неверный код')
  }
}

const formatPhone = () => {
  let digits = phoneNumber.value.replace(/\D/g, '')
  if (digits.length > 10) digits = digits.slice(0, 10)
  
  if (digits.length >= 7) {
    phoneNumber.value = `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 8)}-${digits.slice(8)}`
  } else if (digits.length >= 4) {
    phoneNumber.value = `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  } else if (digits.length > 0) {
    phoneNumber.value = `(${digits}`
  }
}

const addPhone = async () => {
  try {
    const fullPhone = phoneCountry.value + phoneNumber.value.replace(/\D/g, '')
    await apiClient.post('/users/add-phone/', { phone: fullPhone })
    phone.value = fullPhone
    phoneVerified.value = false
    showAddPhoneModal.value = false
    showVerifyPhoneModal.value = true
  } catch (error) {
    console.error('Error adding phone:', error)
    alert('Ошибка при добавлении телефона')
  }
}

const verifyPhone = async () => {
  try {
    await apiClient.post('/users/verify-phone/', {
      code: verifyPhoneCode.value
    })
    phoneVerified.value = true
    showVerifyPhoneModal.value = false
    alert('Телефон успешно подтверждён!')
  } catch (error) {
    console.error('Error verifying phone:', error)
    alert('Неверный код')
  }
}

const removePhone = async () => {
  try {
    await apiClient.delete('/users/phone/')
    phone.value = ''
    phoneVerified.value = false
    showRemovePhoneConfirm.value = false
    alert('Телефон удалён')
  } catch (error) {
    console.error('Error removing phone:', error)
    alert('Ошибка при удалении телефона')
  }
}

const startEmailCooldown = () => {
  emailCooldown.value = 60
  const interval = setInterval(() => {
    emailCooldown.value--
    if (emailCooldown.value <= 0) {
      clearInterval(interval)
    }
  }, 1000)
}

const closeEmailModal = () => {
  showChangeEmailModal.value = false
  emailChangeStep.value = 1
  newEmail.value = ''
  confirmNewEmail.value = ''
  oldEmailCode.value = ''
  newEmailCode.value = ''
  emailError.value = ''
  confirmEmailError.value = ''
}

onMounted(() => {
  fetchContactInfo()
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

.contact-info {
  margin-bottom: 20px;
}

.current-info {
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.info-label {
  font-size: 13px;
  color: var(--secondary-text);
  margin-bottom: 5px;
}

.info-value {
  font-size: 18px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
}

.verified-badge {
  background: #4CAF50;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.unverified-badge {
  background: #FFC107;
  color: #333;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.info-benefits {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 6px;
}

.info-benefits p {
  margin: 0 0 10px 0;
  font-weight: 500;
}

.info-benefits ul {
  margin: 0;
  padding-left: 20px;
}

.info-benefits li {
  margin-bottom: 5px;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.verify-btn, .change-btn, .add-btn, .remove-btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
}

.verify-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.change-btn, .add-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}

.remove-btn {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid #f44336;
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
  margin-bottom: 15px;
}

.change-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 25px;
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
  font-size: 11px;
  color: var(--secondary-text);
}

.step-arrow {
  color: var(--border-color);
}

.modal-step {
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 15px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.text-input {
  width: 100%;
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

.phone-input {
  display: flex;
  gap: 10px;
}

.country-select {
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
}

.code-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 20px;
  letter-spacing: 8px;
  text-align: center;
}

.error-message {
  color: #f44336;
  font-size: 13px;
  margin-top: 5px;
}

.proceed-btn, .confirm-btn {
  width: 100%;
  padding: 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.proceed-btn:disabled, .confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.resend-section {
  text-align: center;
  margin-top: 15px;
}

.resend-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: underline;
}

.cancel-btn {
  width: 100%;
  padding: 10px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  margin-top: 10px;
}

.danger-modal {
  border-color: #f44336;
}

.danger-modal p {
  color: var(--secondary-text);
  line-height: 1.5;
}

.danger-modal .warning {
  font-weight: 500;
  color: #f44336;
}

.danger-modal ul {
  margin: 10px 0;
  padding-left: 20px;
}

.danger-modal li {
  margin-bottom: 5px;
  color: var(--secondary-text);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.danger-btn {
  flex: 1;
  padding: 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.info-text {
  color: var(--secondary-text);
  margin-bottom: 15px;
  line-height: 1.5;
}
</style>
