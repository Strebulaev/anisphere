<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content folder-modal">
      <div class="modal-header">
        <h2 class="modal-title">Создать папку</h2>
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
              placeholder="Например: Работа"
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
      </div>

      <div class="modal-footer">
        <button @click="handleClose" class="btn btn-secondary" type="button">
          Отмена
        </button>
        <button
          @click="handleCreate"
          :disabled="!canSubmit || isSubmitting"
          class="btn btn-primary"
          type="button"
        >
          <svg v-if="isSubmitting" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          {{ isSubmitting ? 'Создание...' : 'Создать папку' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useChatFoldersStore } from '@/stores/chatFolders'
import type { CreateFolderData, Chat, FOLDER_ICONS, FOLDER_COLORS } from '@/types/chat'
import { FOLDER_ICONS as folderIcons, FOLDER_COLORS as folderColors } from '@/types/chat'

interface Props {
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [folder: any]
}>()

const chatFoldersStore = useChatFoldersStore()

const form = ref({
  name: '',
  icon: '📁',
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
const allChats = ref<Chat[]>([])

const availableIcons = folderIcons
const availableColors = folderColors

const canSubmit = computed(() => {
  return form.value.name.trim().length > 0 &&
         (form.value.rules.include_private || form.value.rules.include_groups)
})

const previewChats = computed(() => {
  const folder = {
    ...form.value,
    id: 0,
    position: 0,
    is_system: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
  return chatFoldersStore.applyFolderRules(allChats.value, folder)
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

const handleCreate = async () => {
  if (!canSubmit.value) return

  isSubmitting.value = true

  try {
    const data: CreateFolderData = {
      name: form.value.name.trim(),
      icon: form.value.icon,
      color: form.value.color,
      rules: form.value.rules
    }

    const folder = await chatFoldersStore.createFolder(data)
    emit('created', folder)
    resetForm()
  } catch (error: any) {
    console.error('Error creating folder:', error)
    alert('Ошибка при создании папки: ' + (error.response?.data?.detail || error.message))
  } finally {
    isSubmitting.value = false
  }
}

const handleClose = () => {
  emit('close')
  resetForm()
}

const resetForm = () => {
  form.value = {
    name: '',
    icon: '📁',
    color: undefined,
    rules: {
      include_private: true,
      include_groups: true,
      include_bots: false,
      only_unread: false,
      only_pinned: false,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: []
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
  }
  keywordInput.value = ''
  isSubmitting.value = false
}

watch(() => props.show, async (newShow) => {
  if (newShow) {
  } else {
    resetForm()
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
  background-color: rgba(5,4,8,0.88);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
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
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
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
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
}

.modal-close:hover {
  background-color: var(--surface-4);
  color: var(--danger);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.form-section {
  margin-bottom: 1.5rem;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
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
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.form-label.required::after {
  content: ' *';
  color: var(--danger);
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  color: var(--text-primary);
  background-color: var(--surface-4);
  outline: none;
  transition: all 0.2s var(--ease-petal);
}

.form-input:focus {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
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
  background-color: var(--surface-4);
  border: 2px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
}

.icon-item:hover {
  border-color: var(--accent);
}

.icon-item.active {
  border-color: var(--accent);
  background-color: var(--accent-subtle);
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
  transition: all 0.2s var(--ease-petal);
}

.color-item:hover {
  transform: scale(1.1);
}

.color-item.active {
  border-color: var(--text-primary);
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
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 1.125rem;
  height: 1.125rem;
  accent-color: var(--accent);
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
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  color: var(--text-on-accent);
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  box-shadow: var(--shadow-petal-sm);
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
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
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
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-meta {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.preview-more {
  padding: 0.75rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  background-color: var(--surface-4);
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  border: 1px solid;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  border-color: var(--accent);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-sm);
  transform: translateY(-1px);
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--border-default);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background-color: var(--surface-4);
  border-color: var(--accent);
  color: var(--accent);
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
