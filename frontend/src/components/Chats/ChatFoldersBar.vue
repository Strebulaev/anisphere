<template>
  <div 
    class="chat-folders-bar"
    :class="{ 'chat-folders-bar--collapsed': isCollapsed, 'chat-folders-bar--expanded': !isCollapsed }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <div class="chat-folders-bar__list">
      <button
        v-for="folder in sortedFolders"
        :key="folder.id"
        @click="handleFolderSelect(folder.id)"
        @contextmenu="handleFolderContextMenu($event, folder)"
        @mouseenter="showFolderTooltip($event, folder)"
        @mouseleave="hideFolderTooltip"
        :class="['folder-icon', { 'folder-icon--active': activeFolderId === folder.id }]"
        :style="getIconStyle(folder)"
        type="button"
      >
        <span class="folder-icon__emoji">
          <SakuraIcon v-if="isIconName(folder.icon)" :name="folder.icon" :size="22" />
          <span v-else>{{ folder.icon }}</span>
        </span>
        <span v-if="getUnreadCount(folder.id) > 0" class="folder-icon__badge">
          {{ getUnreadCount(folder.id) > 99 ? '99+' : getUnreadCount(folder.id) }}
        </span>
      </button>
    </div>

    <!-- Custom Tooltip -->
    <div
      v-if="tooltipVisible"
      class="folder-tooltip"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      {{ tooltipText }}
    </div>

    <div class="chat-folders-bar__actions">
      <!-- <button
        @click="showCreateModal = true"
        class="action-button"
        title="Создать папку"
        type="button"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
      </button> -->

      <button
        @click="showShortcutsModal = true"
        class="action-button"
        title="Горячие клавиши"
        type="button"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </button>
    </div>

    <FolderCreateModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @created="handleFolderCreated"
    />

    <FolderEditModal
      v-if="editingFolder"
      :show="showEditModal"
      :folder="editingFolder"
      @close="showEditModal = false"
      @updated="handleFolderUpdated"
      @deleted="handleFolderDeleted"
    />

    <FolderContextMenu
      v-if="contextMenu.folder"
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :folder="contextMenu.folder"
      @close="contextMenu.visible = false"
      @edit="handleContextMenuEdit"
      @delete="handleContextMenuDelete"
    />

    <KeyboardShortcutsModal
      :show="showShortcutsModal"
      @close="showShortcutsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useChatFoldersStore } from '@/stores/chatFolders'
import FolderCreateModal from './FolderCreateModal.vue'
import FolderEditModal from './FolderEditModal.vue'
import FolderContextMenu from './FolderContextMenu.vue'
import KeyboardShortcutsModal from './KeyboardShortcutsModal.vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'
import type { ChatFolder } from '@/types/chat'

// Проверка - является ли icon именем иконки (а не эмодзи)
const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon)
}

interface Props {
  showSearch?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showSearch: false
})

const emit = defineEmits<{
  folderChange: [folder: ChatFolder | null]
}>()

const chatFoldersStore = useChatFoldersStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showShortcutsModal = ref(false)
const editingFolder = ref<ChatFolder | null>(null)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  folder: null as ChatFolder | null
})

const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipX = ref(0)
const tooltipY = ref(0)
let tooltipTimeout: number | null = null
let collapseTimeout: number | null = null
const isCollapsed = ref(false)

const activeFolderId = computed(() => chatFoldersStore.activeFolderId)
const allFolders = computed(() => chatFoldersStore.allFolders)
const userFolders = computed(() => chatFoldersStore.userFolders)

const sortedFolders = computed(() => {
  return allFolders.value
})

const folderTopPosition = computed(() => {
  return props.showSearch ? '180px' : '110px'
})

const getUnreadCount = (folderId: number): number => {
  return chatFoldersStore.getFolderUnreadCount(
    allFolders.value.find(f => f.id === folderId)!,
    []
  )
}

const getIconStyle = (folder: ChatFolder) => {
  if (activeFolderId.value === folder.id) {
    return {}
  }
  if (folder.color) {
    return {
      '--folder-color': folder.color
    }
  }
  return {}
}

const handleFolderSelect = (folderId: number) => {
  chatFoldersStore.setActiveFolder(folderId)
  const folder = allFolders.value.find(f => f.id === folderId) || null
  emit('folderChange', folder)
}

const showFolderTooltip = (event: MouseEvent, folder: ChatFolder) => {
  tooltipText.value = folder.name
  tooltipX.value = event.clientX
  tooltipY.value = event.clientY - 10

  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout)
  }

  tooltipTimeout = window.setTimeout(() => {
    tooltipVisible.value = true
  }, 100)
}

const hideFolderTooltip = () => {
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout)
    tooltipTimeout = null
  }
  tooltipVisible.value = false
}

const handleMouseEnter = () => {
  // Отменяем сворачивание при наведении
  if (collapseTimeout) {
    clearTimeout(collapseTimeout)
    collapseTimeout = null
  }
  isCollapsed.value = false
}

const handleMouseLeave = () => {
  // Сворачивание через 250 мс
  if (collapseTimeout) {
    clearTimeout(collapseTimeout)
  }
  collapseTimeout = window.setTimeout(() => {
    isCollapsed.value = true
  }, 250)
}

const handleFolderContextMenu = (event: MouseEvent, folder: ChatFolder) => {
  if (folder.is_system) return

  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    folder
  }
}

const handleFolderCreated = (folder: ChatFolder) => {
  showCreateModal.value = false
  chatFoldersStore.setActiveFolder(folder.id)
}

const handleFolderUpdated = (folder: ChatFolder) => {
  showEditModal.value = false
  editingFolder.value = null
}

const handleFolderDeleted = (folderId: number) => {
  showEditModal.value = false
  editingFolder.value = null
}

const handleContextMenuEdit = (folder: ChatFolder) => {
  editingFolder.value = folder
  showEditModal.value = true
}

const handleContextMenuDelete = (folderId: number) => {
  handleFolderDeleted(folderId)
}

const handleKeyboardShortcut = (event: KeyboardEvent) => {
  if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    const folderIndex = parseInt(event.key)

    if (event.key === '0') {
      chatFoldersStore.setActiveFolder(0)
      const folder = allFolders.value.find(f => f.id === 0) || null
      emit('folderChange', folder)
    } else if (!isNaN(folderIndex) && folderIndex >= 1 && folderIndex <= 9) {
      const folder = sortedFolders.value[folderIndex - 1]
      if (folder) {
        chatFoldersStore.setActiveFolder(folder.id)
        emit('folderChange', folder)
      }
    }
  } else if (event.key === '?' && !event.ctrlKey && !event.altKey && !event.metaKey && !event.shiftKey) {
    showShortcutsModal.value = true
  }
}

onMounted(() => {
  chatFoldersStore.loadFolders()
  document.addEventListener('keydown', handleKeyboardShortcut)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyboardShortcut)
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout)
  }
  if (collapseTimeout) {
    clearTimeout(collapseTimeout)
  }
})
</script>

<style scoped>
.chat-folders-bar {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 65px;
  height: 100%;
  max-height: 100vh;
  background-color: var(--surface-2);
  border-right: 1px solid var(--border-default);
  padding: 0;
  gap: 0;
  z-index: 1000;
  transition: width 0.25s var(--ease-petal);
  box-shadow: var(--shadow-md);
  overflow: visible;
  cursor: ew-resize;
  flex-shrink: 0;
}

.chat-folders-bar::before {
  display: none;
}

.chat-folders-bar--collapsed {
  width: 12px;
  padding: 0;
  gap: 0;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  cursor: ew-resize;
}

.chat-folders-bar--collapsed .chat-folders-bar__list,
.chat-folders-bar--collapsed .chat-folders-bar__actions {
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
  transition: opacity 0.2s var(--ease-petal);
}

.chat-folders-bar--expanded .chat-folders-bar__list {
  opacity: 1;
  padding: 16px 0.5rem 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: var(--surface-5) transparent;
  transition: opacity 0.2s var(--ease-petal);
  gap: 12px;
}

.chat-folders-bar--expanded .chat-folders-bar__list::-webkit-scrollbar {
  width: 6px;
}

.chat-folders-bar--expanded .chat-folders-bar__list::-webkit-scrollbar-track {
  background: transparent;
}

.chat-folders-bar--expanded .chat-folders-bar__list::-webkit-scrollbar-thumb {
  background: var(--surface-5);
  border-radius: 3px;
}

.chat-folders-bar--expanded .chat-folders-bar__list::-webkit-scrollbar-thumb:hover {
  background: var(--surface-4);
}

.chat-folders-bar__list {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-height: 0;
}

.folder-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.3s var(--ease-petal);
  flex-shrink: 0;
}

.chat-folders-bar--expanded .folder-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
}

.folder-icon:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
  transform: scale(1.1);
}

.folder-icon--active {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.folder-icon--active:hover {
  transform: scale(1.1);
}

.folder-icon--active::before {
  content: '';
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, var(--accent), var(--accent-press));
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.folder-icon__emoji {
  font-size: 1rem;
  line-height: 1;
  transition: font-size 0.3s var(--ease-petal);
}

.chat-folders-bar--expanded .folder-icon__emoji {
  font-size: 1.5rem;
}

.folder-icon__badge {
  position: absolute;
  top: 2px;
  right: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 14px;
  height: 14px;
  padding: 0 2px;
  background: var(--danger);
  color: white;
  font-size: 0.625rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  border: 2px solid var(--surface-2);
  flex-shrink: 0;
  transition: all 0.3s var(--ease-petal);
}

.chat-folders-bar--expanded .folder-icon__badge {
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-size: 0.6875rem;
}

.folder-icon--active .folder-icon__badge {
  background-color: white;
  color: var(--accent);
  border-color: var(--accent);
}

.chat-folders-bar__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  padding: 0 0 12px 0;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0;
  opacity: 0;
  transition: opacity 0.3s var(--ease-petal), padding 0.3s var(--ease-petal);
}

.chat-folders-bar--expanded .chat-folders-bar__actions {
  opacity: 1;
  padding: 0.5rem 0 12px 0;
  transition: opacity 0.2s var(--ease-petal) 0.1s, padding 0.3s var(--ease-petal);
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.3s var(--ease-petal);
  flex-shrink: 0;
}

.chat-folders-bar--expanded .action-button {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
}

.action-button:hover {
  background-color: var(--surface-4);
  color: var(--accent);
  transform: scale(1.1);
}

.action-button svg {
  width: 16px;
  height: 16px;
  transition: all 0.3s var(--ease-petal);
}

.chat-folders-bar--expanded .action-button svg {
  width: 18px;
  height: 18px;
}

.folder-tooltip {
  position: fixed;
  padding: 0.5rem 0.75rem;
  background-color: var(--surface-3);
  color: var(--text-primary);
  font-size: 0.8125rem;
  font-weight: 500;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
  z-index: 10000;
  pointer-events: none;
  white-space: nowrap;
  border: 1px solid var(--border-default);
}

@media (max-width: 768px) {
  .chat-folders-bar {
    width: 50px;
    padding: 0.5rem 0;
  }

  .folder-icon,
  .action-button {
    width: 40px;
    height: 40px;
  }

  .folder-icon__emoji {
    font-size: 1.25rem;
  }

  .folder-icon__badge {
    min-width: 16px;
    height: 16px;
    font-size: 0.625rem;
  }

  .action-button svg {
    width: 16px;
    height: 16px;
  }
}
</style>