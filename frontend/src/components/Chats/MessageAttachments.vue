<template>
  <div v-if="attachments.length > 0" class="message-attachments">
    <div v-for="attachment in attachments" :key="attachment.id" class="attachment-item">
      <img
        v-if="attachment.type === 'image'"
        :src="attachment.thumbnail_url || attachment.file_url"
        :alt="attachment.file_name"
        class="attachment-image"
        @click="openPreview(attachment)"
      />
      <div v-else-if="attachment.type === 'video'" class="attachment-video" @click="openPreview(attachment)">
        <img v-if="attachment.thumbnail_url" :src="attachment.thumbnail_url" class="video-thumbnail" />
        <div class="video-play-btn">▶️</div>
        <span class="video-duration">{{ formatDuration(attachment.duration) }}</span>
      </div>
      <div v-else-if="attachment.type === 'audio'" class="attachment-audio">
        <div class="audio-icon">🎵</div>
        <div class="audio-info">
          <span class="audio-name">{{ attachment.file_name }}</span>
          <span class="audio-duration">{{ formatDuration(attachment.duration) }}</span>
        </div>
      </div>
      <div v-else class="attachment-file">
        <div class="file-icon">📎</div>
        <div class="file-info">
          <span class="file-name">{{ attachment.file_name }}</span>
          <span class="file-size">{{ formatFileSize(attachment.file_size) }}</span>
        </div>
        <a :href="attachment.file_url" download class="file-download" title="Скачать">⬇️</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'
import type { Attachment } from '@/api/chats'

interface Props {
  messageId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'preview-opened', attachment: Attachment): void
}>()

const chatExtrasStore = useChatExtrasStore()

const attachments = computed(() => {
  return chatExtrasStore.getAttachmentsForMessage(props.messageId)
})

const formatDuration = (seconds?: number) => {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const openPreview = (attachment: Attachment) => {
  emit('preview-opened', attachment)
}

onMounted(() => {
  chatExtrasStore.loadMessageAttachments(props.messageId)
})
</script>

<style scoped>
.message-attachments {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.attachment-item {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background-surface);
}

.attachment-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.attachment-image:hover {
  transform: scale(1.05);
}

.attachment-video {
  position: relative;
  width: 100%;
  height: 150px;
  cursor: pointer;
}

.video-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-play-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  backdrop-filter: blur(4px);
}

.video-duration {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.attachment-audio {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background-surface);
  border-radius: 0.5rem;
}

.audio-icon {
  font-size: 1.5rem;
}

.audio-info {
  flex: 1;
  min-width: 0;
}

.audio-name {
  display: block;
  font-size: 0.875rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-duration {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.attachment-file {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background-surface);
  border-radius: 0.5rem;
}

.file-icon {
  font-size: 1.5rem;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  display: block;
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

.file-download {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-background);
  border-radius: 0.375rem;
  color: var(--color-text);
  text-decoration: none;
  transition: background 0.2s;
}

.file-download:hover {
  background: var(--color-background-active);
}
</style>
