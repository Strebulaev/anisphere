<template>
  <div
    class="playlist-item-draggable"
    :class="{ dragging: isDragging }"
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @dragover.prevent="onDragOver"
    @drop="onDrop"
  >
    <div class="drag-handle">
      <span class="drag-icon">⋮⋮</span>
    </div>

    <img
      v-if="getItemPoster()"
      :src="getItemPoster()"
      :alt="item.anime_title"
      class="item-poster"
      @error="handleImageError"
    />
    <div v-else class="item-poster placeholder">
      <span>🎌</span>
    </div>

    <div class="item-info">
      <h3 class="item-title">{{ item.anime_title }}</h3>

      <div class="item-meta">
        <span v-if="item.anime_year" class="meta-tag">
          📅 {{ item.anime_year }}
        </span>
        <span v-if="item.anime_status" class="meta-tag">
          {{ getStatusLabel(item.anime_status) }}
        </span>
        <span v-if="item.anime_score" class="meta-tag rating">
          ⭐ {{ item.anime_score.toFixed(1) }}
        </span>
      </div>

      <div v-if="item.notes" class="item-notes">
        {{ item.notes }}
      </div>
    </div>

    <div class="item-actions">
      <button
        class="action-btn edit-btn"
        @click="$emit('edit', item)"
        title="Редактировать заметки"
      >
        ✏️
      </button>
      <button
        class="action-btn remove-btn"
        @click="$emit('remove', item.id)"
        title="Удалить из плейлиста"
      >
        🗑️
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { PlaylistItem } from '@/api/playlists'
import { getMediaUrl } from '@/api/client'

interface Props {
  item: PlaylistItem
  index: number
}

interface Emits {
  (e: 'edit', item: PlaylistItem): void
  (e: 'remove', itemId: number): void
  (e: 'reorder', fromIndex: number, toIndex: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isDragging = ref(false)
const dragStartIndex = ref(-1)

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'anons': 'Анонс',
    'ongoing': 'Выходит',
    'released': 'Вышел',
    'discontinued': 'Заброшен'
  }
  return labels[status] || status
}

const getItemPoster = (): string | undefined => {
  // Сначала пробуем локальный постер
  const localPoster = getMediaUrl(props.item.anime_poster)
  if (localPoster) {
    return localPoster
  }
  // Затем внешний URL
  const externalPoster = getMediaUrl(props.item.anime_poster_url)
  if (externalPoster) {
    return externalPoster
  }
  return undefined
}

const handleImageError = (e: Event) => {
  console.error('Ошибка загрузки изображения:', e)
  const target = e.target as HTMLImageElement
  if (target) {
    target.style.display = 'none'
  }
}

const onDragStart = (e: DragEvent) => {
  isDragging.value = true
  dragStartIndex.value = props.index
  
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', props.index.toString())
  }
}

const onDragEnd = () => {
  isDragging.value = false
  dragStartIndex.value = -1
}

const onDragOver = (e: DragEvent) => {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = (e: DragEvent) => {
  e.preventDefault()
  
  const toIndex = props.index
  const fromIndex = dragStartIndex.value
  
  if (fromIndex !== -1 && fromIndex !== toIndex) {
    emit('reorder', fromIndex, toIndex)
  }
}
</script>

<style scoped>
.playlist-item-draggable {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  cursor: grab;
  transition: all 0.2s;
  user-select: none;
}

.playlist-item-draggable:hover {
  border-color: var(--color-accent);
  background: var(--color-surface);
}

.playlist-item-draggable.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.drag-handle {
  flex-shrink: 0;
  cursor: grab;
  padding: 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}

.drag-handle:hover {
  background: var(--color-surface);
}

.drag-icon {
  color: var(--color-text-tertiary);
  font-size: 1rem;
  letter-spacing: -0.125rem;
}

.item-poster {
  width: 60px;
  height: 85px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.item-poster.placeholder {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-hover) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.meta-tag.rating {
  color: #fbbf24;
}

.item-notes {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.action-btn {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-background);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(59, 130, 246, 0.1);
}

.remove-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}
</style>
