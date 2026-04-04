<template>
  <div
    :class="[
      'folder-card',
      {
        'folder-card--active': isActive,
        'folder-card--system': isSystem
      }
    ]"
    :style="cardStyle"
    @click="handleClick"
    @contextmenu="handleContextMenu"
  >
    <div class="folder-card__icon">
      {{ folder.icon }}
    </div>

    <div class="folder-card__content">
      <div class="folder-card__name">{{ folder.name }}</div>
    </div>

    <div v-if="unreadCount > 0" class="folder-card__badge">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </div>

    <div v-if="isEditing && !isSystem" class="folder-card__drag-handle">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="9" cy="5" r="1"/>
        <circle cx="15" cy="5" r="1"/>
        <circle cx="9" cy="12" r="1"/>
        <circle cx="15" cy="12" r="1"/>
        <circle cx="9" cy="19" r="1"/>
        <circle cx="15" cy="19" r="1"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatFolder } from '@/types/chat'

interface Props {
  folder: ChatFolder
  isActive: boolean
  isEditing: boolean
  unreadCount: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [id: number]
  contextmenu: [event: MouseEvent, folder: ChatFolder]
}>()

const isSystem = computed(() => props.folder.is_system)

const cardStyle = computed(() => {
  if (!props.folder.color || props.isActive) {
    return {}
  }
  return {
    '--folder-color': props.folder.color
  }
})

const handleClick = () => {
  emit('select', props.folder.id)
}

const handleContextMenu = (event: MouseEvent) => {
  event.preventDefault()
  event.stopPropagation()
  emit('contextmenu', event, props.folder)
}
</script>

<style scoped>
.folder-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  border-radius: var(--radius-lg);
  background-color: var(--surface-4);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  flex-shrink: 0;
  user-select: none;
}

.folder-card:hover:not(.folder-card--active) {
  background-color: var(--surface-5);
  border-color: var(--border-default);
}

.folder-card--active {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  border-color: var(--accent);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.folder-card--active .folder-card__name {
  color: var(--text-on-accent);
}

.folder-card--system {
  opacity: 0.9;
}

.folder-card__icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}

.folder-card__content {
  flex: 1;
  min-width: 0;
}

.folder-card__name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.folder-card__badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  background-color: var(--danger);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.folder-card--active .folder-card__badge {
  background-color: white;
  color: var(--accent);
}

.folder-card__drag-handle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  color: var(--text-tertiary);
  cursor: grab;
  flex-shrink: 0;
}

.folder-card--editing .folder-card__drag-handle {
  display: flex;
}

.folder-card__drag-handle:active {
  cursor: grabbing;
}

@media (max-width: 768px) {
  .folder-card {
    padding: 0.5rem 0.75rem;
  }

  .folder-card__icon {
    font-size: 1.25rem;
  }

  .folder-card__name {
    font-size: 0.8125rem;
  }

  .folder-card__badge {
    min-width: 1.25rem;
    height: 1.25rem;
    font-size: 0.6875rem;
  }
}
</style>
