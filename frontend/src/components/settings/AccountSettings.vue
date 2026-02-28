<template>
  <div class="settings-section">
    <h2>Редактировать профиль</h2>

    <div class="settings-group">
      <h3>📸 Аватар</h3>
      <div class="avatar-section">
        <div class="avatar-preview">
          <img v-if="profileData.avatar" :src="profileData.avatar" alt="Аватар" />
          <div v-else class="avatar-placeholder">👤</div>
        </div>
        <div class="avatar-actions">
          <input
            ref="avatarInput"
            type="file"
            accept="image/jpeg,image/png"
            @change="handleAvatarChange"
            class="hidden-input"
          />
          <button @click="selectAvatar" class="upload-btn">
            📁 Загрузить фото
          </button>
          <button v-if="profileData.avatar" @click="removeAvatar" class="remove-btn">
            🗑️ Удалить
          </button>
        </div>
        <p class="avatar-hint">JPEG/PNG, минимум 200x200px, до 5MB</p>
      </div>
    </div>

    <div class="settings-group">
      <h3>👤 Имя (никнейм)</h3>
      <div class="input-group">
        <label>Отображаемое имя:</label>
        <input
          v-model="profileData.display_name"
          type="text"
          placeholder="Введите имя"
          class="text-input"
          :class="{ 'has-error': displayNameError }"
          @input="validateDisplayName"
        />
        <span v-if="displayNameError" class="error-message">{{ displayNameError }}</span>
        <span class="input-hint">3-30 символов, буквы, цифры, _, -</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>📝 Bio / О себе</h3>
      <div class="input-group">
        <textarea
          v-model="profileData.bio"
          placeholder="Расскажите о себе..."
          class="textarea-input"
          rows="4"
          maxlength="500"
        ></textarea>
        <div class="char-count">{{ profileData.bio?.length || 0 }}/500</div>
      </div>
    </div>

    <div class="settings-group">
      <h3>🎂 Дата рождения</h3>
      <div class="input-group">
        <label>Дата рождения:</label>
        <input
          v-model="profileData.birth_date"
          type="date"
          class="date-input"
        />
        <span class="input-hint">Используется для возрастных ограничений контента (18+)</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔗 Ссылки на соцсети</h3>
      <div class="social-links">
        <div v-for="(link, index) in socialLinks" :key="index" class="social-link-item">
          <select v-model="link.platform" class="platform-select">
            <option value="telegram">Telegram</option>
            <option value="vk">VK</option>
            <option value="youtube">YouTube</option>
            <option value="twitter">Twitter/X</option>
            <option value="instagram">Instagram</option>
            <option value="discord">Discord</option>
            <option value="other">Другое</option>
          </select>
          <input
            v-model="link.url"
            type="url"
            placeholder="https://..."
            class="url-input"
          />
          <button @click="removeSocialLink(index)" class="remove-link-btn">✕</button>
        </div>
        <button @click="addSocialLink" class="add-link-btn">
          ➕ Добавить ссылку
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>🟢 Статус</h3>
      <div class="status-options">
        <label class="status-option" :class="{ active: profileData.status === 'online' }">
          <input type="radio" v-model="profileData.status" value="online" />
          <span class="status-dot online"></span>
          <span>Онлайн</span>
        </label>
        <label class="status-option" :class="{ active: profileData.status === 'away' }">
          <input type="radio" v-model="profileData.status" value="away" />
          <span class="status-dot away"></span>
          <span>Отошёл</span>
        </label>
        <label class="status-option" :class="{ active: profileData.status === 'invisible' }">
          <input type="radio" v-model="profileData.status" value="invisible" />
          <span class="status-dot invisible"></span>
          <span>Невидимка</span>
        </label>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveProfile" :disabled="!hasChanges || !isValid" class="save-btn">
        💾 Сохранить изменения
      </button>
      <button @click="resetChanges" class="reset-btn">
        ↻ Отменить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface SocialLink {
  platform: string
  url: string
}

interface ProfileData {
  avatar?: string
  display_name?: string
  bio?: string
  birth_date?: string
  status: string
}

const authStore = useAuthStore()
const avatarInput = ref<HTMLInputElement | null>(null)

const profileData = ref<ProfileData>({
  status: 'online'
})

const socialLinks = ref<SocialLink[]>([])
const originalProfileData = ref<ProfileData>({ status: 'online' })
const displayNameError = ref('')

const hasChanges = computed(() => {
  return JSON.stringify(profileData.value) !== JSON.stringify(originalProfileData.value)
})

const isValid = computed(() => {
  return !displayNameError.value
})

const fetchProfile = async () => {
  try {
    const response = await apiClient.get('/users/me/')
    profileData.value = {
      avatar: response.data.avatar,
      display_name: response.data.display_name,
      bio: response.data.bio,
      birth_date: response.data.birth_date,
      status: response.data.status || 'online'
    }
    originalProfileData.value = { ...profileData.value }
    
    socialLinks.value = response.data.social_links || []
  } catch (error) {
    console.error('Error fetching profile:', error)
  }
}

const validateDisplayName = () => {
  const name = profileData.value.display_name || ''
  if (name.length > 0) {
    if (name.length < 3) {
      displayNameError.value = 'Минимум 3 символа'
    } else if (name.length > 30) {
      displayNameError.value = 'Максимум 30 символов'
    } else if (!/^[a-zA-Zа-яА-Я0-9_-]+$/.test(name)) {
      displayNameError.value = 'Только буквы, цифры, _ и -'
    } else {
      displayNameError.value = ''
    }
  } else {
    displayNameError.value = ''
  }
}

const selectAvatar = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      alert('Размер файла не должен превышать 5MB')
      return
    }
    
    if (!file.type.match(/image\/(jpeg|png)/)) {
      alert('Только JPEG или PNG форматы')
      return
    }

    const formData = new FormData()
    formData.append('avatar', file)
    
    try {
      const response = await apiClient.post('/users/me/avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      profileData.value.avatar = response.data.avatar
    } catch (error) {
      console.error('Error uploading avatar:', error)
      alert('Ошибка при загрузке аватара')
    }
  }
}

const removeAvatar = async () => {
  try {
    await apiClient.delete('/users/me/avatar/')
    profileData.value.avatar = undefined
  } catch (error) {
    console.error('Error removing avatar:', error)
  }
}

const addSocialLink = () => {
  socialLinks.value.push({ platform: 'telegram', url: '' })
}

const removeSocialLink = (index: number) => {
  socialLinks.value.splice(index, 1)
}

const saveProfile = async () => {
  try {
    await apiClient.put('/users/me/', {
      display_name: profileData.value.display_name,
      bio: profileData.value.bio,
      birth_date: profileData.value.birth_date,
      status: profileData.value.status,
      social_links: socialLinks.value
    })
    originalProfileData.value = { ...profileData.value }
    await authStore.fetchUser()
    alert('Профиль успешно обновлён!')
  } catch (error) {
    console.error('Error saving profile:', error)
    alert('Ошибка при сохранении профиля')
  }
}

const resetChanges = () => {
  profileData.value = { ...originalProfileData.value }
  displayNameError.value = ''
}

onMounted(() => {
  fetchProfile()
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

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--card-bg);
  border: 3px solid var(--border-color);
  flex-shrink: 0;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
}

.avatar-actions {
  display: flex;
  gap: 10px;
}

.upload-btn, .remove-btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.upload-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.remove-btn {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid #f44336;
}

.hidden-input {
  display: none;
}

.avatar-hint {
  margin: 10px 0 0 0;
  font-size: 13px;
  color: var(--secondary-text);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-weight: 500;
}

.text-input, .date-input, .textarea-input {
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

.textarea-input {
  resize: vertical;
  min-height: 80px;
}

.error-message {
  color: #f44336;
  font-size: 13px;
}

.input-hint {
  font-size: 13px;
  color: var(--secondary-text);
}

.char-count {
  text-align: right;
  font-size: 13px;
  color: var(--secondary-text);
}

.social-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.social-link-item {
  display: flex;
  gap: 10px;
}

.platform-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  min-width: 120px;
}

.url-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
}

.remove-link-btn {
  background: none;
  border: none;
  color: #f44336;
  cursor: pointer;
  padding: 5px 10px;
  font-size: 18px;
}

.add-link-btn {
  padding: 8px 16px;
  background: var(--hover-bg);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-color);
}

.status-options {
  display: flex;
  gap: 15px;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.status-option:hover {
  background: var(--hover-bg);
}

.status-option.active {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.status-option input[type="radio"] {
  display: none;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.online {
  background: #4CAF50;
}

.status-dot.away {
  background: #FFC107;
}

.status-dot.invisible {
  background: #9E9E9E;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn, .reset-btn {
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

.reset-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>
