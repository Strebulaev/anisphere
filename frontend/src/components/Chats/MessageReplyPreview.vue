<template>
  <div class="message-reply-preview" @click="handleClick">
    <div class="reply-header">
      <span class="reply-author" :style="{ color: authorColor }">
        {{ author }}
      </span>
      <button class="close-btn" @click.stop="$emit('close')" title="Закрыть">
        ✕
      </button>
    </div>
    <div class="reply-content">
      <!-- Текст сообщения -->
      <div v-if="message?.text" class="reply-text">
        {{ truncateText(message.text, 150) }}
      </div>
      
      <!-- Вложения -->
      <div v-if="hasAttachments" class="reply-attachments">
        <!-- Фото -->
        <div v-if="message?.image_url || message?.image_file" class="attachment-photo">
          <img :src="getMediaUrl(message.image_url || message.image_file)" alt="Фото" />
        </div>
        
        <!-- Видео -->
        <div v-if="message?.video_url || message?.video_file" class="attachment-video">
          <div class="video-placeholder">🎥 Видео</div>
        </div>
        
        <!-- Файл -->
        <div v-if="message?.file_url || message?.file" class="attachment-file">
          <span class="file-icon">📎</span>
          <span class="file-name">{{ getFileName(message.file_url || message.file) }}</span>
        </div>
      </div>
      
      <!-- Пустое сообщение -->
      <div v-if="!message?.text && !hasAttachments" class="reply-empty">
        <span class="empty-icon">📷</span>
        <span>Фотография</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getMediaUrl } from '@/api/client'

interface Message {
  id: number
  text?: string | null
  image_url?: string | null
  image_file?: string | null
  video_url?: string | null
  video_file?: string | null
  file_url?: string | null
  file?: string | null
  sender?: {
    username: string
    display_name?: string | null
  }
}

const props = defineProps<{
  message: Message | null
  author?: string
  authorColor?: string
}>()

const emit = defineEmits<{
  close: []
  click: []
}>()

const hasAttachments = computed(() => {
  if (!props.message) return false
  return !!(
    props.message.image_url || 
    props.message.image_file || 
    props.message.video_url || 
    props.message.video_file || 
    props.message.file_url || 
    props.message.file
  )
})

const truncateText = (text: string | null | undefined, maxLen: number): string => {
  if (!text) return ''
  const cleaned = text.replace(/\n/g, ' ').trim()
  return cleaned.length > maxLen ? cleaned.substring(0, maxLen) + '...' : cleaned
}

const getFileName = (url: string | null | undefined): string => {
  if (!url) return 'Файл'
  const parts = url.split('/')
  let filename = parts[parts.length - 1]
  if (!filename) filename = 'Файл'
  return filename.length > 30 ? filename.substring(0, 27) + '...' : filename
}

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.message-reply-preview {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  background: rgba(58, 134, 255, 0.08);
  border-left: 3px solid var(--color-primary);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  max-width: 100%;
  overflow: hidden;
}

.message-reply-preview:hover {
  background: rgba(58, 134, 255, 0.12);
}

.reply-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.reply-author {
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  font-size: 1rem;
  cursor: pointer;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  flex-shrink: 0;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text-primary);
}

.reply-content {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.reply-text {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  word-break: break-word;
}

.reply-attachments {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
}

.attachment-photo {
  flex-shrink: 0;
}

.attachment-photo img {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
}

.attachment-video {
  flex-shrink: 0;
}

.video-placeholder {
  width: 60px;
  height: 60px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

.attachment-file {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.file-icon {
  font-size: 0.9rem;
}

.file-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reply-empty {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
}

.empty-icon {
  font-size: 1rem;
}
</style>
