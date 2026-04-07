<template>
  <div class="settings-section">
    <h2>Конфиденциальность</h2>

    <div class="settings-group">
      <h3><SakuraIcon name="user" /> Кто может видеть мой номер телефона</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="mail" /> Кто может видеть мой email</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="one-oclock" /> Время последнего посещения</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="camera" /> Фотография профиля</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="phone" /> Звонки</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="users" /> Группы и каналы</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="everyone" @change="onSettingsChange">
          <span class="radio-label">Все могут добавлять меня в группы</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="contacts" @change="onSettingsChange">
          <span class="radio-label">Только мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="nobody" @change="onSettingsChange">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="link" /> Пересылка сообщений</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="privacySettings.allow_message_forwarding" @change="onSettingsChange">
          <span>Разрешить пересылку моих сообщений</span>
        </label>
        <div class="sub-settings" v-if="privacySettings.allow_message_forwarding">
          <label class="setting-label">
            <input type="checkbox" v-model="forwardTextOnly" @change="onSettingsChange">
            <span>Только текстовые сообщения</span>
          </label>
          <label class="setting-label">
            <input type="checkbox" v-model="forwardWithAttribution" @change="onSettingsChange">
            <span>С указанием авторства</span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="map-pin" /> Данные о местоположении</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="auto" @change="onSettingsChange">
          <span class="radio-label">Отправлять автоматически</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="manual" @change="onSettingsChange">
          <span class="radio-label">Только при использовании функции</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="never" @change="onSettingsChange">
          <span class="radio-label">Никогда</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="search" /> Поиск по номеру телефона</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="allowPhoneSearch" @change="onSettingsChange">
          <span>Показывать меня по номеру телефона</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="target" /> Рекламные рассылки</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="allowTargetedAds" @change="onSettingsChange">
          <span>Разрешить таргетированную рекламу</span>
        </label>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges || isSaving" class="save-btn">
        {{ isSaving ? 'Сохранение...' : '<SakuraIcon name="save" /> Сохранить настройки' }}
      </button>
    </div>

    <!-- Toast notification -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as settingsApi from '@/api/settings'
import type { PrivacySettingsData } from '@/api/settings'

// Reactive data
const privacySettings = ref<PrivacySettingsData>({
  who_can_see_phone: 'contacts',
  who_can_see_email: 'contacts',
  who_can_see_last_seen: 'everyone',
  who_can_see_profile_photo: 'everyone',
  who_can_call: 'everyone',
  who_can_add_to_groups: 'everyone',
  allow_message_forwarding: true
})

const locationSharing = ref('manual')
const allowPhoneSearch = ref(true)
const allowTargetedAds = ref(false)
const forwardTextOnly = ref(false)
const forwardWithAttribution = ref(true)

const originalSettings = ref<PrivacySettingsData>({ ...privacySettings.value })
const isSaving = ref(false)

const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

const hasChanges = computed(() => {
  return JSON.stringify(privacySettings.value) !== JSON.stringify(originalSettings.value) ||
         locationSharing.value !== 'manual' ||
         allowPhoneSearch.value !== true ||
         allowTargetedAds.value !== false ||
         forwardTextOnly.value !== false ||
         forwardWithAttribution.value !== true
})

// Methods
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const fetchPrivacySettings = async () => {
  try {
    const data = await settingsApi.getPrivacySettings()
    privacySettings.value = {
      who_can_see_phone: data.who_can_see_phone || 'contacts',
      who_can_see_email: data.who_can_see_email || 'contacts',
      who_can_see_last_seen: (data as any).who_can_see_last_seen || 'everyone',
      who_can_see_profile_photo: data.who_can_see_profile_photo || 'everyone',
      who_can_call: data.who_can_call || 'everyone',
      who_can_add_to_groups: data.who_can_add_to_groups || 'everyone',
      allow_message_forwarding: data.allow_message_forwarding ?? true
    }
    originalSettings.value = { ...privacySettings.value }
  } catch (error) {
    console.error('Error fetching privacy settings:', error)
    showToast('Ошибка загрузки настроек', 'error')
  }
}

const onSettingsChange = () => {
  // Автосохранение при изменении настроек
  saveSettings()
}

const saveSettings = async () => {
  isSaving.value = true
  try {
    await settingsApi.updatePrivacySettings(privacySettings.value)
    originalSettings.value = { ...privacySettings.value }
    showToast('Настройки сохранены')
  } catch (error) {
    console.error('Error saving privacy settings:', error)
    showToast('Ошибка сохранения настроек', 'error')
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  fetchPrivacySettings()
})
</script>

<style scoped>
.settings-section h2 {
  margin-bottom: 20px;
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
  font-weight: 600;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.radio-option:hover {
  background: var(--card-bg);
}

.radio-option input[type="radio"] {
  margin: 0;
}

.radio-label {
  font-weight: 500;
  cursor: pointer;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.sub-settings {
  margin-left: 25px;
  margin-top: 10px;
}

.sub-settings .setting-label {
  font-weight: normal;
  font-size: 14px;
}

.settings-actions {
  margin-top: 30px;
  text-align: center;
}

.save-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.save-btn:disabled {
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