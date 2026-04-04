<template>
  <div
    v-if="visible"
    class="folder-context-menu"
    :style="{ left: x + 'px', top: y + 'px' }"
    @click.stop
  >
    <div class="context-menu__items">
      <button
        @click="handleEdit"
        class="context-menu__item"
        type="button"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <span>Редактировать</span>
      </button>

      <div v-if="!isSystem" class="context-menu__divider"></div>

      <button
        v-if="!isSystem"
        @click="handleDelete"
        class="context-menu__item context-menu__item--danger"
        type="button"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
        <span>Удалить</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import type { ChatFolder } from '@/types/chat'

interface Props {
  visible: boolean
  x: number
  y: number
  folder: ChatFolder
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  edit: [folder: ChatFolder]
  delete: [id: number]
}>()

const isSystem = computed(() => props.folder.is_system)

const handleEdit = () => {
  emit('edit', props.folder)
  emit('close')
}

const handleDelete = () => {
  emit('delete', props.folder.id)
  emit('close')
}

const handleClickOutside = (event: MouseEvent) => {
  if (props.visible) {
    emit('close')
  }
}

const handleEscape = (event: KeyboardEvent) => {
  if (props.visible && event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscape)
})
</script>

<script lang="ts">
import { computed } from 'vue'
export default {
  name: 'FolderContextMenu'
}
</script>

<style scoped>
.folder-context-menu {
  position: fixed;
  z-index: 2000;
  min-width: 180px;
  background-color: var(--surface-2);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
  padding: 0.375rem;
  border: 1px solid var(--border-default);
}

.context-menu__items {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.context-menu__item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s var(--ease-petal);
  text-align: left;
}

.context-menu__item:hover {
  background-color: var(--surface-4);
}

.context-menu__item--danger {
  color: var(--danger);
}

.context-menu__item--danger:hover {
  background-color: var(--danger-subtle);
}

.context-menu__item svg {
  flex-shrink: 0;
}

.context-menu__divider {
  height: 1px;
  background-color: var(--border-subtle);
  margin: 0.25rem 0;
}
</style>
