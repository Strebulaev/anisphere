<template>
  <div class="settings-section">
    <h2>РЈРґР°Р»РµРЅРёРµ Р°РєРєР°СѓРЅС‚Р°</h2>

    <!-- Step 1: Warning -->
    <div v-if="currentStep === 1" class="settings-group warning-group">
      <div class="warning-icon">вљ пёЏ</div>
      <h3>Р’РќРРњРђРќРР•!</h3>
      <p class="warning-text">
        Р’С‹ СЃРѕР±РёСЂР°РµС‚РµСЃСЊ СѓРґР°Р»РёС‚СЊ Р°РєРєР°СѓРЅС‚. Р­С‚Рѕ РґРµР№СЃС‚РІРёРµ <strong>РќР•РћР‘Р РђРўРРњРћ</strong>.
        Р’СЃРµ РІР°С€Рё РґР°РЅРЅС‹Рµ Р±СѓРґСѓС‚ Р±РµР·РІРѕР·РІСЂР°С‚РЅРѕ СѓРґР°Р»РµРЅС‹:
      </p>

      <div class="data-summary">
        <div class="summary-item">
          <span class="summary-icon">рџ“‹</span>
          <span>РџР»РµР№Р»РёСЃС‚С‹ ({{ accountStats.playlists_count }})</span>
        </div>
        <div class="summary-item">
          <span class="summary-icon">рџЋ¬</span>
          <span>РџРѕСЃС‚С‹ ({{ accountStats.posts_count }})</span>
        </div>
        <div class="summary-item">
          <span class="summary-icon">рџ’¬</span>
          <span>РљРѕРјРјРµРЅС‚Р°СЂРёРё ({{ accountStats.comments_count }})</span>
        </div>
        <div class="summary-item">
          <span class="summary-icon">в­ђ</span>
          <span>Р›Р°Р№РєРё РїРѕР»СѓС‡РµРЅРѕ ({{ accountStats.likes_received }})</span>
        </div>
        <div class="summary-item">
          <span class="summary-icon">рџ“©</span>
          <span>РЎРѕРѕР±С‰РµРЅРёСЏ ({{ accountStats.messages_count }})</span>
        </div>
        <div class="summary-item">
          <span class="summary-icon">рџ’ѕ</span>
          <span>Р‘РёР±Р»РёРѕС‚РµРєР° ({{ accountStats.library_count }})</span>
        </div>
      </div>

      <div class="important-note">
        <strong>вќ— Р’Р°Р¶РЅРѕ:</strong>
        <ul>
          <li>РРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РѕСЃРІРѕР±РѕРґРёС‚СЃСЏ РґР»СЏ РґСЂСѓРіРёС…</li>
          <li>РђРЅРѕРЅРёРјРЅС‹Рµ РґР°РЅРЅС‹Рµ (Р»Р°Р№РєРё, РїСЂРѕСЃРјРѕС‚СЂС‹) РѕСЃС‚Р°РЅСѓС‚СЃСЏ РІ СЃС‚Р°С‚РёСЃС‚РёРєРµ Р±РµР· РїСЂРёРІСЏР·РєРё</li>
          <li>Р•СЃС‚СЊ 7 РґРЅРµР№ РЅР° РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёРµ РїРѕСЃР»Рµ СѓРґР°Р»РµРЅРёСЏ</li>
        </ul>
      </div>

      <div class="action-buttons">
        <button @click="goToStep(2)" class="danger-btn">
          РЇ РїРѕРЅРёРјР°СЋ, РїСЂРѕРґРѕР»Р¶РёС‚СЊ в†’
        </button>
        <button @click="reset" class="cancel-btn">
          РћС‚РјРµРЅР°
        </button>
      </div>
    </div>

    <!-- Step 2: Reason -->
    <div v-if="currentStep === 2" class="settings-group">
      <h3>рџ¤” РџРѕС‡РµРјСѓ РІС‹ СѓС…РѕРґРёС‚Рµ?</h3>
      <p class="info-text">РџРѕРјРѕРіРёС‚Рµ РЅР°Рј СѓР»СѓС‡С€РёС‚СЊ СЃРµСЂРІРёСЃ (РјРѕР¶РЅРѕ РІС‹Р±СЂР°С‚СЊ РЅРµСЃРєРѕР»СЊРєРѕ):</p>

      <div class="reasons-list">
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="interface" />
          <span>рџ• РќРµСѓРґРѕР±РЅС‹Р№ РёРЅС‚РµСЂС„РµР№СЃ</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="content" />
          <span>рџ“є РњР°Р»Рѕ РєРѕРЅС‚РµРЅС‚Р°</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="community" />
          <span>рџ‘Ґ РџСЂРѕР±Р»РµРјС‹ СЃ СЃРѕРѕР±С‰РµСЃС‚РІРѕРј</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="alternative" />
          <span>рџ”„ РќР°С€С‘Р» Р°Р»СЊС‚РµСЂРЅР°С‚РёРІСѓ</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="privacy" />
          <span>рџ”’ Р’РѕРїСЂРѕСЃС‹ РїСЂРёРІР°С‚РЅРѕСЃС‚Рё</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="performance" />
          <span>вљЎ РџСЂРѕР±Р»РµРјС‹ СЃ РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚СЊСЋ</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="ads" />
          <span>рџ“ў РЎР»РёС€РєРѕРј РјРЅРѕРіРѕ СЂРµРєР»Р°РјС‹</span>
        </label>
        <label class="reason-option">
          <input type="checkbox" v-model="reasons" value="other" />
          <span>рџ“ќ Р”СЂСѓРіРѕРµ</span>
        </label>
      </div>

      <div v-if="reasons.includes('alternative')" class="input-group">
        <label>РљР°РєСѓСЋ Р°Р»СЊС‚РµСЂРЅР°С‚РёРІСѓ РІС‹ РЅР°С€Р»Рё?</label>
        <input
          v-model="alternativeName"
          type="text"
          placeholder="РќР°Р·РІР°РЅРёРµ СЃРµСЂРІРёСЃР°"
          class="text-input"
        />
      </div>

      <div v-if="reasons.includes('other')" class="input-group">
        <label>Р Р°СЃСЃРєР°Р¶РёС‚Рµ РїРѕРґСЂРѕР±РЅРµРµ:</label>
        <textarea
          v-model="otherReason"
          placeholder="Р’Р°С€Рё РєРѕРјРјРµРЅС‚Р°СЂРёРё..."
          class="textarea-input"
          rows="3"
          maxlength="500"
        ></textarea>
        <div class="char-count">{{ otherReason.length }}/500</div>
      </div>

      <div class="action-buttons">
        <button @click="goToStep(3)" class="proceed-btn">
          РџСЂРѕРґРѕР»Р¶РёС‚СЊ в†’
        </button>
        <button @click="goToStep(1)" class="back-btn">
          в†ђ РќР°Р·Р°Рґ
        </button>
      </div>
    </div>

    <!-- Step 3: Confirmation -->
    <div v-if="currentStep === 3" class="settings-group">
      <h3>рџ”ђ РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ</h3>

      <div class="verification-methods">
        <label class="method-option">
          <input type="radio" v-model="verificationMethod" value="password" />
          <span>рџ”‘ РџР°СЂРѕР»СЊ</span>
        </label>
        <label v-if="accountStats.has_2fa" class="method-option">
          <input type="radio" v-model="verificationMethod" value="2fa" />
          <span>рџ”ђ РљРѕРґ 2FA</span>
        </label>
      </div>

      <div v-if="verificationMethod === 'password'" class="input-group">
        <label>Р”Р»СЏ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ РІРІРµРґРёС‚Рµ РІР°С€ РїР°СЂРѕР»СЊ:</label>
        <div class="password-input">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="В·В·В·В·В·В·В·В·В·В·В·В·В·В·В·В·"
            class="text-input"
          />
          <button @click="showPassword = !showPassword" class="toggle-visibility">
            {{ showPassword ? 'рџ‘ЃпёЏ' : 'рџ‘ЃпёЏвЂЌрџ—ЁпёЏ' }}
          </button>
        </div>
      </div>

      <div v-if="verificationMethod === '2fa'" class="input-group">
        <label>РљРѕРґ РёР· РїСЂРёР»РѕР¶РµРЅРёСЏ-Р°СѓС‚РµРЅС‚РёС„РёРєР°С‚РѕСЂР° РёР»Рё SMS:</label>
        <input
          v-model="twoFactorCode"
          type="text"
          placeholder="XXXXXX"
          class="code-input"
          maxlength="6"
        />
      </div>

      <div class="final-check">
        <label class="checkbox-label">
          <input type="checkbox" v-model="finalConfirmation" />
          <span>РЇ РїРѕРґС‚РІРµСЂР¶РґР°СЋ, С‡С‚Рѕ С…РѕС‡Сѓ СѓРґР°Р»РёС‚СЊ СЃРІРѕР№ Р°РєРєР°СѓРЅС‚ Рё РїРѕРЅРёРјР°СЋ РїРѕСЃР»РµРґСЃС‚РІРёСЏ</span>
        </label>
      </div>

      <div class="action-buttons">
        <button
          @click="confirmDeletion"
          :disabled="!canConfirm || isDeleting"
          class="danger-btn"
        >
          {{ isDeleting ? 'РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ...' : 'рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ Р°РєРєР°СѓРЅС‚' }}
        </button>
        <button @click="goToStep(2)" class="back-btn">
          в†ђ РќР°Р·Р°Рґ
        </button>
      </div>
    </div>

    <!-- Step 4: Success -->
    <div v-if="currentStep === 4" class="settings-group success-group">
      <div class="success-icon">вњ…</div>
      <h3>Р—Р°РїСЂРѕСЃ РЅР° СѓРґР°Р»РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅ</h3>
      
      <div class="success-message">
        <p v-if="accountStats.deletion_date">
          Р’Р°С€ Р°РєРєР°СѓРЅС‚ Р±СѓРґРµС‚ СѓРґР°Р»С‘РЅ: <strong>{{ formatDate(accountStats.deletion_date) }}</strong>
        </p>
        <p v-else>
          Р’Р°С€ Р°РєРєР°СѓРЅС‚ Р±СѓРґРµС‚ СѓРґР°Р»С‘РЅ С‡РµСЂРµР· <strong>7 РґРЅРµР№</strong>.
        </p>
        <p>Р’ С‚РµС‡РµРЅРёРµ СЌС‚РѕРіРѕ РІСЂРµРјРµРЅРё РІС‹ РјРѕР¶РµС‚Рµ:</p>
        <ul>
          <li>Р’РѕР№С‚Рё Рё РѕС‚РјРµРЅРёС‚СЊ СѓРґР°Р»РµРЅРёРµ</li>
          <li>Р’РѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ РІСЃРµ СЃРІРѕРё РґР°РЅРЅС‹Рµ</li>
        </ul>
      </div>

      <div class="email-confirmation">
        <p>рџ“§ РџРёСЃСЊРјРѕ СЃ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµРј РѕС‚РїСЂР°РІР»РµРЅРѕ РЅР°:</p>
        <p class="email">{{ accountStats.masked_email }}</p>
      </div>

      <div class="info-box">
        <p>Р•СЃР»Рё РІС‹ РїРµСЂРµРґСѓРјР°РµС‚Рµ, РїСЂРѕСЃС‚Рѕ РІРѕР№РґРёС‚Рµ РІ Р°РєРєР°СѓРЅС‚ РІ С‚РµС‡РµРЅРёРµ 7 РґРЅРµР№ Рё РЅР°Р¶РјРёС‚Рµ "РћС‚РјРµРЅРёС‚СЊ СѓРґР°Р»РµРЅРёРµ".</p>
      </div>

      <button @click="reset" class="ok-btn">
        РџРѕРЅСЏС‚РЅРѕ
      </button>
    </div>

    <!-- Cancel Deletion Modal (shown when user tries to login during grace period) -->
    <div v-if="showCancelModal" class="modal-overlay" @click="showCancelModal = false">
      <div class="modal" @click.stop>
        <h3>РћС‚РјРµРЅРёС‚СЊ СѓРґР°Р»РµРЅРёРµ Р°РєРєР°СѓРЅС‚Р°?</h3>
        <p>РњС‹ Р·Р°РјРµС‚РёР»Рё, С‡С‚Рѕ РІС‹ РІРѕС€Р»Рё РІ Р°РєРєР°СѓРЅС‚, РєРѕС‚РѕСЂС‹Р№ РЅР°С…РѕРґРёС‚СЃСЏ РІ РїСЂРѕС†РµСЃСЃРµ СѓРґР°Р»РµРЅРёСЏ.</p>
        <p>РҐРѕС‚РёС‚Рµ РѕС‚РјРµРЅРёС‚СЊ СѓРґР°Р»РµРЅРёРµ Рё РІРѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ РґРѕСЃС‚СѓРї?</p>
        
        <div class="modal-actions">
          <button @click="showCancelModal = false" class="cancel-btn">РќРµС‚, РїСЂРѕРґРѕР»Р¶РёС‚СЊ СѓРґР°Р»РµРЅРёРµ</button>
          <button @click="cancelDeletion" class="confirm-btn">Р”Р°, РѕС‚РјРµРЅРёС‚СЊ СѓРґР°Р»РµРЅРёРµ</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
import { ref, computed, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'

const currentStep = ref(1)
const reasons = ref<string[]>([])
const alternativeName = ref('')
const otherReason = ref('')

const verificationMethod = ref('password')
const password = ref('')
const twoFactorCode = ref('')
const showPassword = ref(false)
const finalConfirmation = ref(false)

interface AccountStats {
  playlists_count: number
  comments_count: number
  posts_count: number
  likes_received: number
  messages_count: number
  chats_count: number
  library_count: number
  has_2fa: boolean
  masked_email: string
  deletion_scheduled: boolean
  deletion_date: string | null
}

const accountStats = ref<AccountStats>({
  playlists_count: 0,
  comments_count: 0,
  posts_count: 0,
  likes_received: 0,
  messages_count: 0,
  chats_count: 0,
  library_count: 0,
  has_2fa: false,
  masked_email: '',
  deletion_scheduled: false,
  deletion_date: null
})

const showCancelModal = ref(false)
const isDeleting = ref(false)

const canConfirm = computed(() => {
  if (verificationMethod.value === 'password') {
    return password.value.length > 0 && finalConfirmation.value
  } else {
    return twoFactorCode.value.length === 6 && finalConfirmation.value
  }
})

const fetchAccountStats = async () => {
  try {
    const data = await settingsApi.getAccountStats()
    accountStats.value = data

    // Р•СЃР»Рё СѓРґР°Р»РµРЅРёРµ Р·Р°РїР»Р°РЅРёСЂРѕРІР°РЅРѕ, РїСЂРѕРїСѓСЃРєР°РµРј Рє С€Р°РіСѓ 4
    if (data.deletion_scheduled) {
      currentStep.value = 4
    }
  } catch (error) {
    console.error('Error fetching account stats:', error)
  }
}

const goToStep = (step: number) => {
  currentStep.value = step
}

const confirmDeletion = async () => {
  isDeleting.value = true
  try {
    const data: any = {
      reasons: reasons.value,
      alternative: alternativeName.value,
      other_reason: otherReason.value,
      final_confirmation: true
    }

    if (verificationMethod.value === 'password') {
      data.password = password.value
    } else {
      data.two_factor_code = twoFactorCode.value
    }

    await settingsApi.scheduleAccountDeletion(data)
    await fetchAccountStats()
    currentStep.value = 4
  } catch (error: any) {
    console.error('Error deleting account:', error)
    showToast(error.response?.data?.error || 'РћС€РёР±РєР° РїСЂРё СѓРґР°Р»РµРЅРёРё Р°РєРєР°СѓРЅС‚Р°. РџСЂРѕРІРµСЂСЊС‚Рµ РїСЂР°РІРёР»СЊРЅРѕСЃС‚СЊ РїР°СЂРѕР»СЏ РёР»Рё РєРѕРґР°.')
  } finally {
    isDeleting.value = false
  }
}

const cancelDeletion = async () => {
  try {
    await settingsApi.cancelAccountDeletion()
    showCancelModal.value = false
    await fetchAccountStats()
    currentStep.value = 1
    showToast('РЈРґР°Р»РµРЅРёРµ Р°РєРєР°СѓРЅС‚Р° РѕС‚РјРµРЅРµРЅРѕ!')
  } catch (error) {
    console.error('Error canceling deletion:', error)
    showToast('РћС€РёР±РєР° РїСЂРё РѕС‚РјРµРЅРµ СѓРґР°Р»РµРЅРёСЏ')
  }
}

const reset = () => {
  currentStep.value = 1
  reasons.value = []
  alternativeName.value = ''
  otherReason.value = ''
  password.value = ''
  twoFactorCode.value = ''
  finalConfirmation.value = false
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchAccountStats()
})
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 30px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px;
}

.warning-group {
  border: 2px solid #f44336;
  background: rgba(244, 67, 54, 0.05);
}

.warning-icon {
  font-size: 60px;
  text-align: center;
  margin-bottom: 20px;
}

.warning-text {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-color);
  margin-bottom: 20px;
}

.data-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin: 25px 0;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
}

.summary-icon {
  font-size: 24px;
}

.important-note {
  padding: 15px;
  background: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #FFC107;
  border-radius: 4px;
  margin-bottom: 25px;
}

.important-note strong {
  color: #FFC107;
}

.important-note ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.important-note li {
  margin-bottom: 5px;
  color: var(--text-color);
}

.info-text {
  color: var(--secondary-text);
  margin-bottom: 20px;
}

.reasons-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.reason-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.reason-option:hover {
  background: var(--hover-bg);
}

.reason-option input[type="checkbox"] {
  margin: 0;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.text-input, .textarea-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
}

.textarea-input {
  resize: vertical;
  min-height: 80px;
}

.char-count {
  text-align: right;
  font-size: 13px;
  color: var(--secondary-text);
  margin-top: 5px;
}

.password-input {
  display: flex;
  gap: 10px;
}

.toggle-visibility {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  padding: 5px;
}

.code-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 20px;
  letter-spacing: 10px;
  text-align: center;
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

.final-check {
  margin: 20px 0;
  padding: 15px;
  background: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 3px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.danger-btn, .proceed-btn, .cancel-btn, .back-btn, .ok-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.danger-btn {
  background: #f44336;
  color: white;
  border: none;
}

.danger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.proceed-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.cancel-btn, .back-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}

.success-group {
  text-align: center;
  padding: 40px 30px;
}

.success-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.success-message {
  margin-bottom: 30px;
}

.success-message p {
  margin-bottom: 10px;
  color: var(--text-color);
}

.success-message ul {
  margin: 15px 0;
  padding-left: 20px;
  text-align: left;
  display: inline-block;
}

.email-confirmation {
  padding: 20px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 8px;
  margin-bottom: 20px;
}

.email-confirmation .email {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
  margin: 10px 0 0 0;
}

.info-box {
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  margin-bottom: 25px;
}

.info-box p {
  margin: 0;
  color: var(--secondary-text);
}

.ok-btn {
  background: var(--primary-color);
  color: white;
  border: none;
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

.modal p {
  color: var(--secondary-text);
  line-height: 1.5;
  margin-bottom: 10px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
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
</style>
