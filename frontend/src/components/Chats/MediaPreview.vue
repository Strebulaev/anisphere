<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isOpen" class="preview-overlay" @click="close">
        <div class="preview-content" @click.stop>
          <button class="close-btn" @click="close">×</button>

          <div v-if="attachment" class="preview-header">
            <span class="file-name">{{ attachment.file_name }}</span>
            <span class="file-size">{{ formatFileSize(attachment.file_size) }}</span>
          </div>

          <div v-if="attachment" class="preview-body">
            <img
              v-if="attachment.type === 'image'"
              :src="attachment.file_url"
              :alt="attachment.file_name"
              class="preview-image"
            />
            <video
              v-else-if="attachment.type === 'video'"
              :src="attachment.file_url"
              controls
              class="preview-video"
            />
            <audio
              v-else-if="attachment.type === 'audio'"
              :src="attachment.file_url"
              controls
              class="preview-audio"
            />
            <div v-else class="preview-file">
              <div class="file-icon-large">{{ getFileIcon(attachment.mime_type) }}</div>
              <div class="file-info-large">
                <div class="file-name-large">{{ attachment.file_name }}</div>
                <div class="file-meta">
                  <span>{{ formatFileSize(attachment.file_size) }}</span>
                  <span v-if="attachment.mime_type">{{ attachment.mime_type }}</span>
                </div>
              </div>
              <a :href="attachment.file_url" download class="download-btn">Скачать файл</a>
            </div>
          </div>

          <div class="preview-footer">
            <button class="nav-btn" @click="previous" :disabled="!hasPrevious">← Предыдущий</button>
            <span class="counter">{{ currentIndex + 1 }} / {{ attachments.length }}</span>
            <button class="nav-btn" @click="next" :disabled="!hasNext">Следующий →</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import type { Attachment } from '@/api/chats'

interface Props {
  isOpen: boolean
  attachment: Attachment | null
  attachments: Attachment[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'change', attachment: Attachment): void
}>()

const currentIndex = computed(() => {
  if (!props.attachment) return -1
  return props.attachments.findIndex(a => a.id === props.attachment?.id)
})

const hasPrevious = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < props.attachments.length - 1)

const previous = () => {
  if (hasPrevious.value) {
    const prevAttachment = props.attachments[currentIndex.value - 1]
    if (prevAttachment) {
      emit('change', prevAttachment)
    }
  }
}

const next = () => {
  if (hasNext.value) {
    const nextAttachment = props.attachments[currentIndex.value + 1]
    if (nextAttachment) {
      emit('change', nextAttachment)
    }
  }
}

const close = () => {
  emit('close')
}

const getFileIcon = (mimeType: string) => {
  if (mimeType?.startsWith('video/')) return '🎬'
  if (mimeType?.startsWith('audio/')) return '🎵'
  if (mimeType?.includes('pdf')) return '📄'
  if (mimeType?.includes('word')) return '📝'
  if (mimeType?.includes('excel')) return '📊'
  if (mimeType?.includes('zip') || mimeType?.includes('rar')) return '📦'
  return '📎'
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})
</script>

<style scoped>
.preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.preview-content {
  position: relative;
  width: 90vw;
  height: 90vh;
  background: var(--color-background-surface);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
  background: var(--color-background);
}

.file-name {
  font-size: 0.875rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 1rem;
}

.file-size {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.preview-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  overflow: auto;
  background: var(--color-background);
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-video {
  max-width: 100%;
  max-height: 100%;
}

.preview-audio {
  width: 100%;
  max-width: 600px;
}

.preview-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2rem;
  text-align: center;
}

.file-icon-large {
  font-size: 5rem;
}

.file-info-large {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-name-large {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-text);
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.download-btn {
  padding: 0.75rem 2rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s;
}

.download-btn:hover {
  background: var(--color-accent-hover);
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-divider);
  background: var(--color-background);
}

.nav-btn {
  padding: 0.5rem 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 6px;
  font-size: 0.875rem;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: var(--color-background-active);
  border-color: var(--color-accent);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.counter {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
