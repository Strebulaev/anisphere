<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content folder-modal">
      <div class="modal-header">
        <h2 class="modal-title">Редактировать папку</h2>
        <button @click="handleClose" class="modal-close" type="button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="form-section">
          <div class="form-group">
            <label class="form-label required">Название папки</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="Название папки"
              class="form-input"
              maxlength="50"
            />
          </div>

          <div class="form-group">
            <label class="form-label required">Иконка</label>
            <div class="icon-selector">
              <button
                v-for="icon in availableIcons"
                :key="icon"
                @click="form.icon = icon"
                :class="['icon-item', { active: form.icon === icon }]"
                type="button"
              >
                {{ icon }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Цвет</label>
            <div class="color-selector">
              <button
                v-for="color in availableColors"
                :key="color"
                @click="form.color = form.color === color ? undefined : color"
                :class="['color-item', { active: form.color === color }]"
                :style="{ backgroundColor: color }"
                type="button"
              >
                <svg v-if="form.color === color" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">Правила фильтрации</h3>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="form.rules.include_private"
                type="checkbox"
              />
              <span>Включать личные сообщения</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="form.rules.include_groups"
                type="checkbox"
              />
              <span>Включать групповые чаты</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="form.rules.include_bots"
                type="checkbox"
              />
              <span>Включать ботов</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="form.rules.only_unread"
                type="checkbox"
              />
              <span>Только непрочитанные</span>
            </label>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="form.rules.only_pinned"
                type="checkbox"
              />
              <span>Только закреплённые</span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label">Ключевые слова в названии</label>
            <div class="keywords-input">
              <input
                v-model="keywordInput"
                type="text"
                placeholder="Добавить ключевое слово"
                class="form-input"
                @keyup.enter="addKeyword"
              />
              <button @click="addKeyword" class="btn btn-secondary" type="button">
                Добавить
              </button>
            </div>
            <div v-if="form.rules.include_keywords.length > 0" class="keywords-list">
              <span
                v-for="(keyword, index) in form.rules.include_keywords"
                :key="index"
                class="keyword-tag"
              >
                {{ keyword }}
                <button @click="removeKeyword(index)" type="button">×</button>
              </span>
            </div>
          </div>
        </div>

        <div v-if="previewChats.length > 0" class="form-section">
          <h3 class="section-title">Предпросмотр ({{ previewChats.length }} чатов)</h3>
          <div class="preview-list">
            <div v-for="chat in previewChats.slice(0, 10)" :key="chat.id" class="preview-item">
              <div class="preview-icon">{{ chat.type === 'private' ? '👤' : '👥' }}</div>
              <div class="preview-info">
                <div class="preview-name">{{ getChatTitle(chat) }}</div>
                <div class="preview-meta">
                  {{ chat.unread_count }} непрочитанных
                </div>
              </div>
            </div>
            <div v-if="previewChats.length > 10" class="preview-more">
              + ещё {{ previewChats.length - 10 }} чатов
            </div>
          </div>
        </div>

        <div class="form-section form-section--danger">
          <h3 class="section-title section-title--danger">Опасная зона</h3>
          <button
            @click="handleDelete"
            class="btn btn-danger"
            type="button"
          >
            Удалить папку
          </button>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleClose" class="btn btn-secondary" type="button">
          Отмена
        </button>
        <button
          @click="handleUpdate"
          :disabled="!canSubmit || isSubmitting"
          class="btn btn-primary"
          type="button"
        >
          <svg v-if="isSubmitting" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          {{ isSubmitting ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
      </div>
    </div>
  </div>

  <DeleteConfirmModal
    :show="showDeleteModal"
    :title="'Удалить папку?'"
    :message="'Вы уверены, что хотите удалить папку «' + folder.name + '»? Это действие нельзя отменить.'"
    @confirm="confirmDelete"
    @close="showDeleteModal = false"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useChatFoldersStore } from '@/stores/chatFolders'
import type { UpdateFolderData, Chat, FOLDER_ICONS, FOLDER_COLORS, ChatFolder } from '@/types/chat'
import { FOLDER_ICONS as folderIcons, FOLDER_COLORS as folderColors } from '@/types/chat'
import DeleteConfirmModal from '@/components/common/DeleteConfirmModal.vue'

interface Props {
  show: boolean
  folder: ChatFolder
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  updated: [folder: ChatFolder]
  deleted: [id: number]
}>()

const chatFoldersStore = useChatFoldersStore()

const form = ref({
  name: '',
  icon: '',
  color: undefined as string | undefined,
  rules: {
    include_private: true,
    include_groups: true,
    include_bots: false,
    only_unread: false,
    only_pinned: false,
    exclude_keywords: [] as string[],
    include_keywords: [] as string[],
    exclude_user_ids: [] as number[]
  } as {
    include_private: boolean
    include_groups: boolean
    include_bots: boolean
    only_unread: boolean
    only_pinned: boolean
    exclude_keywords: string[]
    include_keywords: string[]
    exclude_user_ids: number[]
  }
})

const keywordInput = ref('')
const isSubmitting = ref(false)
const showDeleteModal = ref(false)

const availableIcons = folderIcons
const availableColors = folderColors

const canSubmit = computed(() => {
  return form.value.name.trim().length > 0 &&
         (form.value.rules.include_private || form.value.rules.include_groups)
})

const previewChats = computed(() => {
  const folder = {
    ...form.value,
    id: props.folder.id,
    position: props.folder.position,
    is_system: props.folder.is_system,
    created_at: props.folder.created_at,
    updated_at: props.folder.updated_at
  }
  return chatFoldersStore.applyFolderRules([], folder)
})

const addKeyword = () => {
  const keyword = keywordInput.value.trim().toLowerCase()
  if (keyword && !form.value.rules.include_keywords.includes(keyword)) {
    form.value.rules.include_keywords.push(keyword)
    keywordInput.value = ''
  }
}

const removeKeyword = (index: number) => {
  form.value.rules.include_keywords.splice(index, 1)
}

const getChatTitle = (chat: Chat): string => {
  if (chat.type === 'private') {
    return chat.other_user?.display_name || chat.other_user?.username || 'Неизвестный'
  }
  return chat.name || 'Без названия'
}

const handleUpdate = async () => {
  if (!canSubmit.value) return

  isSubmitting.value = true

  try {
    const data: UpdateFolderData = {
      name: form.value.name.trim(),
      icon: form.value.icon,
      color: form.value.color,
      rules: form.value.rules
    }

    const updatedFolder = await chatFoldersStore.updateFolder(props.folder.id, data)
    emit('updated', updatedFolder)
  } catch (error: any) {
    console.error('Error updating folder:', error)
    alert('Ошибка при обновлении папки: ' + (error.response?.data?.detail || error.message))
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = () => {
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  try {
    await chatFoldersStore.deleteFolder(props.folder.id)
    showDeleteModal.value = false
    emit('deleted', props.folder.id)
  } catch (error: any) {
    console.error('Error deleting folder:', error)
    alert('Ошибка при удалении папки: ' + (error.response?.data?.detail || error.message))
  }
}

const handleClose = () => {
  emit('close')
}

watch(() => props.show, (newShow) => {
  if (newShow) {
    form.value = {
      name: props.folder.name,
      icon: props.folder.icon,
      color: props.folder.color,
      rules: {
        include_private: props.folder.rules.include_private,
        include_groups: props.folder.rules.include_groups,
        include_bots: props.folder.rules.include_bots,
        only_unread: props.folder.rules.only_unread || false,
        only_pinned: props.folder.rules.only_pinned || false,
        exclude_keywords: [...props.folder.rules.exclude_keywords],
        include_keywords: [...props.folder.rules.include_keywords],
        exclude_user_ids: [...props.folder.rules.exclude_user_ids]
      }
    }
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
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--color-background-active);
  color: #ef4444;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.form-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-divider-light);
}

.form-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.form-section--danger {
  border-top: 1px solid #fee2e2;
  padding-top: 1.5rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 1rem 0;
}

.section-title--danger {
  color: #ef4444;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.form-label.required::after {
  content: ' *';
  color: #ef4444;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.form-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.icon-selector {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(3rem, 1fr));
  gap: 0.5rem;
}

.icon-item {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  border: 2px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.icon-item:hover {
  border-color: var(--color-accent);
}

.icon-item.active {
  border-color: var(--color-accent);
  background-color: rgba(58, 134, 255, 0.1);
}

.color-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.color-item {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s var(--transition-smooth);
}

.color-item:hover {
  transform: scale(1.1);
}

.color-item.active {
  border-color: var(--color-text);
}

.color-item svg {
  color: white;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.9375rem;
  color: var(--color-text);
}

.checkbox-label input[type="checkbox"] {
  width: 1.125rem;
  height: 1.125rem;
  accent-color: var(--color-accent);
}

.keywords-input {
  display: flex;
  gap: 0.5rem;
}

.keywords-input .form-input {
  flex: 1;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: var(--color-accent);
  color: white;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}

.keyword-tag button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.keyword-tag button:hover {
  opacity: 1;
}

.preview-list {
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  overflow: hidden;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--color-divider-light);
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.preview-info {
  flex: 1;
  min-width: 0;
}

.preview-name {
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-meta {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.preview-more {
  padding: 0.75rem;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  background-color: var(--color-background-active);
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-danger {
  background-color: #fee2e2;
  border-color: #fecaca;
  color: #dc2626;
  width: 100%;
}

.btn-danger:hover {
  background-color: #fecaca;
  border-color: #f87171;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }

  .icon-selector {
    grid-template-columns: repeat(auto-fill, minmax(2.5rem, 1fr));
  }
}
</style>
