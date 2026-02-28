<template>
  <div class="file-upload">
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="file-input"
      @change="handleFileChange"
    />

    <button class="upload-btn" @click="triggerFileInput" :disabled="loading">
      <span v-if="!loading" class="btn-icon">📎</span>
      <span v-else class="btn-spinner">⏳</span>
      <span class="btn-text">{{ loading ? 'Загрузка...' : buttonText }}</span>
    </button>

    <div v-if="uploadedFiles.length > 0" class="uploaded-files">
      <div v-for="(file, index) in uploadedFiles" :key="index" class="uploaded-file">
        <div class="file-preview">
          <img v-if="file.type.startsWith('image/')" :src="file.preview" class="preview-image" />
          <div v-else class="preview-icon">{{ getFileIcon(file.type) }}</div>
        </div>
        <div class="file-info">
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
        </div>
        <button class="file-remove" @click="removeFile(index)" title="Удалить">×</button>
      </div>
    </div>

    <div v-if="error" class="upload-error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  messageId?: number
  accept?: string
  multiple?: boolean
  buttonText?: string
  maxSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  accept: 'image/*,video/*,audio/*,.pdf,.doc,.docx,.txt',
  multiple: false,
  buttonText: 'Прикрепить файл',
  maxSize: 10 * 1024 * 1024
})

const emit = defineEmits<any>()

const fileInput = ref<HTMLInputElement>()
const loading = ref(false)
const uploadedFiles = ref<Array<{ file: File; preview: string; type: string; name: string; size: number }>>([])
const error = ref('')

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])

  if (files.length === 0) return

  error.value = ''

  if (props.multiple) {
    emit('files-selected', files)
  } else {
    emit('file-selected', files[0])
  }

  for (const file of files) {
    if (file.size > props.maxSize) {
      error.value = `Файл ${file.name} превышает максимальный размер (${formatFileSize(props.maxSize)})`
      return
    }

    const preview = await createPreview(file)
    uploadedFiles.value.push({
      file,
      preview,
      type: file.type,
      name: file.name,
      size: file.size
    })
  }

  if (props.messageId) {
    await uploadFiles(files)
  }

  target.value = ''
}

const uploadFiles = async (files: File[]) => {
  loading.value = true
  error.value = ''

  try {
    for (const file of files) {
      if (props.messageId) {
        const result = await uploadFile(file, props.messageId)
        emit('upload-complete', result)
      }
    }
  } catch (err: any) {
    error.value = err.message || 'Ошибка загрузки файла'
    emit('upload-error', error.value)
  } finally {
    loading.value = false
  }
}

const uploadFile = async (file: File, messageId: number) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`/api/social/messages/${messageId}/attachments/upload/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken()
    },
    body: formData
  })

  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.error || 'Ошибка загрузки')
  }

  return await response.json()
}

const createPreview = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string)
      reader.readAsDataURL(file)
    } else {
      resolve('')
    }
  })
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const getFileIcon = (mimeType: string) => {
  if (mimeType.startsWith('video/')) return '🎬'
  if (mimeType.startsWith('audio/')) return '🎵'
  if (mimeType.includes('pdf')) return '📄'
  if (mimeType.includes('word')) return '📝'
  return '📎'
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getCsrfToken = (): string => {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return decodeURIComponent(value || '')
    }
  }
  return ''
}
</script>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.file-input {
  display: none;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: var(--color-background-active);
  border-color: var(--color-accent);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon,
.btn-spinner {
  font-size: 1.125rem;
}

.btn-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.btn-text {
  font-size: 0.875rem;
}

.uploaded-files {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 8px;
}

.file-preview {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-background-surface);
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-icon {
  font-size: 1.5rem;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.file-name {
  font-size: 0.875rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.file-remove {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.25rem;
  line-height: 1;
}

.file-remove:hover {
  background: rgba(244, 67, 54, 0.1);
  border-color: #f44336;
  color: #f44336;
}

.upload-error {
  padding: 0.75rem;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  border-radius: 8px;
  font-size: 0.875rem;
  color: #f44336;
}
</style>
