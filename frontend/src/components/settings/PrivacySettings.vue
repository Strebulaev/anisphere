<template>
  <div class="settings-section">
    <h2>Конфиденциальность</h2>

    <div class="settings-group">
      <h3>👤 Кто может видеть мой номер телефона</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="everyone">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="contacts">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_phone" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📧 Кто может видеть мой email</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="everyone">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="contacts">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_email" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🕐 Время последнего посещения</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="everyone">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="contacts">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_last_seen" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📸 Фотография профиля</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="everyone">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="contacts">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_see_profile_photo" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📞 Звонки</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="everyone">
          <span class="radio-label">Все</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="contacts">
          <span class="radio-label">Мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_call" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>👥 Группы и каналы</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="everyone">
          <span class="radio-label">Все могут добавлять меня в группы</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="contacts">
          <span class="radio-label">Только мои контакты</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="privacySettings.who_can_add_to_groups" value="nobody">
          <span class="radio-label">Никто</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔗 Пересылка сообщений</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="privacySettings.allow_message_forwarding">
          <span>Разрешить пересылку моих сообщений</span>
        </label>
        <div class="sub-settings" v-if="privacySettings.allow_message_forwarding">
          <label class="setting-label">
            <input type="checkbox" v-model="forwardTextOnly">
            <span>Только текстовые сообщения</span>
          </label>
          <label class="setting-label">
            <input type="checkbox" v-model="forwardWithAttribution">
            <span>С указанием авторства</span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>📍 Данные о местоположении</h3>
      <div class="radio-group">
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="auto">
          <span class="radio-label">Отправлять автоматически</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="manual">
          <span class="radio-label">Только при использовании функции</span>
        </label>
        <label class="radio-option">
          <input type="radio" v-model="locationSharing" value="never">
          <span class="radio-label">Никогда</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔍 Поиск по номеру телефона</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="allowPhoneSearch">
          <span>Показывать меня по номеру телефона</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>🎯 Рекламные рассылки</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="allowTargetedAds">
          <span>Разрешить таргетированную рекламу</span>
        </label>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        💾 Сохранить настройки
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

// Reactive data
const privacySettings = ref({
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

const originalSettings = ref({ ...privacySettings.value })

const hasChanges = computed(() => {
  return JSON.stringify(privacySettings.value) !== JSON.stringify(originalSettings.value) ||
         locationSharing.value !== 'manual' ||
         allowPhoneSearch.value !== true ||
         allowTargetedAds.value !== false
})

// Methods
const fetchPrivacySettings = async () => {
  try {
    const response = await apiClient.get('/users/privacy-settings/')
    privacySettings.value = response.data
    originalSettings.value = { ...response.data }
  } catch (error) {
    console.error('Error fetching privacy settings:', error)
  }
}

const saveSettings = async () => {
  try {
    await apiClient.put('/users/privacy-settings/', privacySettings.value)
    originalSettings.value = { ...privacySettings.value }
    // Show success message
  } catch (error) {
    console.error('Error saving privacy settings:', error)
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
</style>