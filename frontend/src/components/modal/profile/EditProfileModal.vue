<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Редактировать профиль</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="saveProfile">
          <!-- Avatar Upload -->
          <div class="form-group avatar-group">
            <label class="form-label">Фото профиля</label>
            <div class="avatar-upload">
              <div class="current-avatar">
                <img v-if="profileData.avatarUrl" :src="profileData.avatarUrl" :alt="profileData.displayName || 'Avatar'" class="avatar-preview">
                <div v-else class="avatar-placeholder">
                  {{ getInitials(profileData.displayName || profileData.nickname || 'U') }}
                </div>
              </div>
              <div class="upload-controls">
                <input
                  type="file"
                  ref="fileInput"
                  @change="handleFileSelect"
                  accept="image/*"
                  style="display: none"
                >
                <button type="button" @click="fileInput?.click()" class="btn-upload">
                  Выбрать фото
                </button>
                <p class="upload-hint">JPG, PNG или GIF. Макс. 5MB</p>
              </div>
            </div>
          </div>

          <!-- Display Name -->
          <div class="form-group">
            <label for="displayName" class="form-label">Отображаемое имя</label>
            <input
              id="displayName"
              v-model="profileData.displayName"
              type="text"
              class="form-input"
              placeholder="Ваше имя"
              maxlength="50"
            >
            <p class="field-hint">Это имя будет видно другим пользователям</p>
          </div>

          <!-- Nickname -->
          <div class="form-group">
            <label for="nickname" class="form-label">Никнейм <span class="required">*</span></label>
            <input
              id="nickname"
              v-model="profileData.nickname"
              type="text"
              class="form-input"
              placeholder="уникальный_ник"
              maxlength="30"
              required
            >
            <p class="field-hint">Уникальное имя для добавления в чаты. Только буквы, цифры и подчеркивания</p>
            <p v-if="nicknameError" class="error-message">{{ nicknameError }}</p>
          </div>

          <!-- Bio -->
          <div class="form-group">
            <label for="bio" class="form-label">О себе</label>
            <textarea
              id="bio"
              v-model="profileData.bio"
              class="form-textarea"
              placeholder="Расскажите о себе..."
              maxlength="500"
              rows="3"
            ></textarea>
            <p class="field-hint">{{ profileData.bio.length }}/500 символов</p>
          </div>

          <!-- Links -->
          <div class="form-group">
            <label class="form-label">Ссылки</label>
            <div class="links-group">
              <div class="link-input">
                <span class="link-prefix">https://</span>
                <input
                  v-model="profileData.website"
                  type="text"
                  class="form-input link-field"
                  placeholder="ваш-сайт.com"
                >
              </div>
              <div class="link-input">
                <span class="link-prefix">VK: </span>
                <input
                  v-model="profileData.vk"
                  type="text"
                  class="form-input link-field"
                  placeholder="vk.com/username"
                >
              </div>
              <div class="link-input">
                <span class="link-prefix">Telegram: </span>
                <input
                  v-model="profileData.telegram"
                  type="text"
                  class="form-input link-field"
                  placeholder="@username"
                >
              </div>
            </div>
          </div>

          <!-- Anime Interests -->
          <div class="form-group">
            <label class="form-label">Любимые жанры аниме</label>
            <div class="genres-grid">
              <label v-for="genre in availableGenres" :key="genre.id" class="genre-checkbox">
                <input
                  type="checkbox"
                  v-model="profileData.favoriteGenres"
                  :value="genre.id"
                >
                <span class="checkmark"></span>
                {{ genre.name }}
              </label>
            </div>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Отмена</button>
        <button @click="saveProfile" class="btn-primary" :disabled="isLoading">
          <span v-if="isLoading">Сохранение...</span>
          <span v-else>Сохранить</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import apiClient from '@/api/client'

interface Props {
  isVisible: boolean
  user: any
  onClose: () => void
  onSave?: (profile: any) => void
}

const props = defineProps<Props>()

const fileInput = ref<HTMLInputElement>()

const isLoading = ref(false)
const nicknameError = ref('')

const profileData = reactive({
  displayName: '',
  nickname: '',
  bio: '',
  avatarUrl: '',
  website: '',
  vk: '',
  telegram: '',
  favoriteGenres: [] as string[]
})

const availableGenres = [
  { id: 'action', name: 'Экшен' },
  { id: 'adventure', name: 'Приключения' },
  { id: 'comedy', name: 'Комедия' },
  { id: 'drama', name: 'Драма' },
  { id: 'fantasy', name: 'Фэнтези' },
  { id: 'romance', name: 'Романтика' },
  { id: 'scifi', name: 'Sci-Fi' },
  { id: 'horror', name: 'Ужасы' },
  { id: 'mystery', name: 'Детектив' },
  { id: 'slice_of_life', name: 'Повседневность' }
]

// Watch for nickname changes to validate uniqueness
watch(() => profileData.nickname, async (newNickname) => {
  if (!newNickname || newNickname.length < 3) {
    nicknameError.value = ''
    return
  }

  if (!/^[a-zA-Z0-9_]+$/.test(newNickname)) {
    nicknameError.value = 'Никнейм может содержать только буквы, цифры и подчеркивания'
    return
  }

  try {
    // Check nickname availability
    const response = await apiClient.get(`/users/check-nickname/?nickname=${newNickname}`)
    if (!response.data.available && newNickname !== props.user?.nickname) {
      nicknameError.value = 'Этот никнейм уже занят'
    } else {
      nicknameError.value = ''
    }
  } catch (error) {
    console.error('Error checking nickname:', error)
  }
})

const getInitials = (name: string) => {
  return name.charAt(0).toUpperCase()
}

const handleFileSelect = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      alert('Файл слишком большой. Максимальный размер: 5MB')
      return
    }

    if (!file.type.startsWith('image/')) {
      alert('Пожалуйста, выберите изображение')
      return
    }

    // Create preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      profileData.avatarUrl = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const validateForm = () => {
  if (!profileData.nickname.trim()) {
    alert('Никнейм обязателен')
    return false
  }

  if (nicknameError.value) {
    alert('Исправьте ошибки в форме')
    return false
  }

  return true
}

const saveProfile = async () => {
  if (!validateForm()) return

  isLoading.value = true

  try {
    const formData = new FormData()

    // Add text fields
    formData.append('display_name', profileData.displayName)
    formData.append('nickname', profileData.nickname)
    formData.append('bio', profileData.bio)
    formData.append('website', profileData.website)
    formData.append('vk_profile', profileData.vk)
    formData.append('telegram', profileData.telegram)
    formData.append('favorite_genres', JSON.stringify(profileData.favoriteGenres))

    // Add avatar file if changed
    if (fileInput.value?.files?.[0]) {
      formData.append('avatar', fileInput.value.files[0])
    }

    const response = await apiClient.patch('/users/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    props.onSave?.(response.data)
    closeModal()
  } catch (error: any) {
    console.error('Error saving profile:', error)
    if (error.response?.data?.nickname) {
      nicknameError.value = error.response.data.nickname[0]
    } else {
      alert('Ошибка при сохранении профиля')
    }
  } finally {
    isLoading.value = false
  }
}

const closeModal = () => {
  // Reset form
  nicknameError.value = ''
  props.onClose()
}

// Initialize form data when modal opens
watch(() => props.isVisible, (visible) => {
  if (visible && props.user) {
    profileData.displayName = props.user.display_name || props.user.first_name || ''
    profileData.nickname = props.user.nickname || ''
    profileData.bio = props.user.bio || ''
    profileData.avatarUrl = props.user.avatar || ''
    profileData.website = props.user.website || ''
    profileData.vk = props.user.vk_profile || ''
    profileData.telegram = props.user.telegram || ''
    profileData.favoriteGenres = props.user.favorite_genres || []
  }
})
</script>

<style scoped>
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

.modal-content {
  background: var(--color-background-surface);
  border-radius: var(--radius-modal);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-button);
  transition: background-color 0.15s ease;
}

.close-btn:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.required {
  color: var(--color-accent-pink);
}

.form-input, .form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-button);
  font-size: 0.875rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.field-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

.error-message {
  font-size: 0.75rem;
  color: var(--color-accent-pink);
  margin-top: 0.25rem;
}

/* Avatar upload */
.avatar-group {
  text-align: center;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.current-avatar {
  position: relative;
}

.avatar-preview, .avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  background: var(--color-accent);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
}

.upload-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.btn-upload {
  padding: 0.5rem 1rem;
  background: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.15s ease;
}

.btn-upload:hover {
  background: var(--color-accent-hover);
}

.upload-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Links */
.links-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.link-input {
  display: flex;
  align-items: center;
}

.link-prefix {
  padding: 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-right: none;
  border-radius: var(--radius-button) 0 0 var(--radius-button);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.link-field {
  border-radius: 0 var(--radius-button) var(--radius-button) 0;
  border-left: none;
}

/* Genres */
.genres-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
}

.genre-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0.5rem;
  border-radius: var(--radius-button);
  transition: background-color 0.15s ease;
  color: var(--color-text-secondary);
}

.genre-checkbox:hover {
  background: var(--color-background);
}

.genre-checkbox input {
  margin-right: 0.5rem;
}

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn-secondary {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-divider-light);
  background: var(--color-background);
  color: var(--color-text);
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-secondary:hover {
  background: var(--color-background-active);
}

.btn-primary {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-accent);
  background: var(--color-accent);
  color: var(--color-text);
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .genres-grid {
    grid-template-columns: 1fr;
  }

  .avatar-upload {
    flex-direction: row;
    gap: 1rem;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-secondary, .btn-primary {
    width: 100%;
  }
}
</style>