<template>
  <BaseModal
    :show="props.show"
    title="Изменить аватар"
    @update:show="emit('update:show', false)"
  >
    <div class="avatar-editor-modal">
      <div v-if="currentStep === 'upload'" class="upload-step">
        <div class="current-avatar">
          <img
            v-if="currentAvatar"
            :src="currentAvatar"
            alt="Текущий аватар"
            class="avatar-preview"
          >
          <div v-else class="avatar-placeholder">
            {{ getUserInitials() }}
          </div>
        </div>

        <div class="upload-options">
          <button class="upload-btn" @click="triggerFileInput">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Загрузить фото
          </button>
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png"
            @change="handleFileSelect"
            style="display: none"
          >
        </div>

        <div class="requirements">
          <h4>Требования:</h4>
          <ul>
            <li>JPEG/PNG формат</li>
            <li>Максимальный размер: 5 МБ</li>
            <li>Минимальное разрешение: 200x200px</li>
          </ul>
        </div>

        <div class="actions">
          <button class="btn btn-secondary" @click="handleRemove" v-if="currentAvatar">
            Удалить аватар
          </button>
        </div>
      </div>

      <div v-else-if="currentStep === 'crop'" class="crop-step">
        <div class="crop-container">
          <div class="crop-area">
            <img
              ref="cropImage"
              :src="previewImage"
              alt="Для обрезки"
              class="crop-image"
            >
            <div class="crop-overlay">
              <div class="crop-circle"></div>
            </div>
          </div>
        </div>

        <div class="crop-actions">
          <button class="btn btn-secondary" @click="currentStep = 'upload'">
            Отмена
          </button>
          <button class="btn btn-primary" @click="handleSave" :disabled="uploading">
            {{ uploading ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>

      <div v-else-if="currentStep === 'success'" class="success-step">
        <div class="success-icon">✓</div>
        <h3>Аватар обновлён!</h3>
        <p>Ваш аватар успешно изменён и будет отображаться во всех разделах сайта.</p>
        <button class="btn btn-primary" @click="emit('update:show', false)">
          Отлично!
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import BaseModal from '@/components/ui/BaseModal.vue'

interface Props {
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'avatar-updated': [avatarUrl: string]
}>()

const authStore = useAuthStore()
const currentStep = ref<'upload' | 'crop' | 'success'>('upload')
const fileInput = ref<HTMLInputElement>()
const previewImage = ref<string>('')
const selectedFile = ref<File | null>(null)
const uploading = ref(false)

const currentAvatar = computed(() => (authStore.user as any)?.avatar_url || authStore.user?.avatar)

const getUserInitials = () => {
  const user = authStore.user
  if (!user) return ''
  const name = (user as any).display_name || user.username
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return

  if (!file.type.match(/image\/(jpeg|png)/)) {
    alert('Пожалуйста, выберите изображение в формате JPEG или PNG')
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    alert('Размер файла не должен превышать 5 МБ')
    return
  }

  const dimensions = await getImageDimensions(file)
  if (dimensions.width < 200 || dimensions.height < 200) {
    alert('Минимальное разрешение изображения: 200x200px')
    return
  }

  selectedFile.value = file
  previewImage.value = URL.createObjectURL(file)
  currentStep.value = 'crop'
}

const getImageDimensions = (file: File): Promise<{ width: number; height: number }> => {
  return new Promise((resolve) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve({ width: img.width, height: img.height })
    }
    img.src = url
  })
}

const handleRemove = async () => {
  if (!confirm('Вы уверены, что хотите удалить аватар?')) return

  try {
    await authStore.updateProfile({ avatar: null })
    emit('avatar-updated', '')
    currentStep.value = 'success'
  } catch (error) {
    alert('Ошибка при удалении аватара')
    console.error(error)
  }
}

const handleSave = async () => {
  if (!selectedFile.value) return

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('avatar', selectedFile.value)

    const response = await fetch('/api/users/avatar', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error('Failed to upload avatar')
    }

    const data = await response.json()
    
    await authStore.fetchUser()
    emit('avatar-updated', data.avatar_url)
    currentStep.value = 'success'
  } catch (error) {
    alert('Ошибка при загрузке аватара')
    console.error(error)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.avatar-editor-modal {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 400px;
}

.current-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.avatar-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid var(--color-divider);
}

.avatar-placeholder {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
  font-size: 2.5rem;
  font-weight: bold;
  border: 4px solid var(--color-divider);
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.upload-btn:hover {
  background: var(--color-primary-hover);
}

.requirements {
  padding: 1rem;
  background: var(--color-background);
  border-radius: 0.5rem;
}

.requirements h4 {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.requirements ul {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.requirements li {
  margin: 0.25rem 0;
}

.actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.crop-step {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.crop-container {
  display: flex;
  justify-content: center;
  background: var(--color-background);
  border-radius: 0.5rem;
  padding: 1rem;
}

.crop-area {
  position: relative;
  width: 300px;
  height: 300px;
  overflow: hidden;
}

.crop-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.crop-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
}

.crop-circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 2px dashed rgba(255, 255, 255, 0.8);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
}

.crop-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.success-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
  padding: 2rem 1rem;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
}

.success-step h3 {
  font-size: 1.25rem;
  color: var(--color-text-primary);
  margin: 0;
}

.success-step p {
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--color-background-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-divider);
}

.btn-secondary:hover {
  background: var(--color-background-hover);
}

@media (max-width: 640px) {
  .avatar-editor-modal {
    min-width: auto;
  }

  .crop-area {
    width: 250px;
    height: 250px;
  }

  .crop-circle {
    width: 150px;
    height: 150px;
  }
}
</style>
