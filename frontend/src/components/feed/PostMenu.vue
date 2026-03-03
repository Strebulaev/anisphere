<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="post-menu" @click.stop>
      <!-- Author actions -->
      <template v-if="post.can_edit || post.can_delete">
        <button v-if="post.can_edit" @click="emit('edit', post); emit('close')" class="menu-item">
          <span class="icon">✏️</span>
          <span>Редактировать</span>
          <span class="hint">5 мин</span>
        </button>
        <button v-if="post.can_delete" @click="confirmDelete" class="menu-item danger">
          <span class="icon">🗑️</span>
          <span>Удалить</span>
        </button>
        <button v-if="post.can_edit && !post.is_pinned" @click="emit('pin', post); emit('close')" class="menu-item">
          <span class="icon">📌</span>
          <span>Закрепить в профиле</span>
        </button>
        <div class="menu-divider"></div>
      </template>

      <!-- Common actions -->
      <button @click="handleBookmark" class="menu-item">
        <span class="icon">{{ post.is_bookmarked ? '⭐' : '☆' }}</span>
        <span>{{ post.is_bookmarked ? 'Убрать из закладок' : 'Сохранить в закладки' }}</span>
      </button>

      <button @click="handleHide" class="menu-item">
        <span class="icon">🙈</span>
        <span>Не интересно</span>
      </button>

      <button @click="handleForward" class="menu-item">
        <span class="icon">📨</span>
        <span>Переслать</span>
      </button>

      <button @click="emit('repost', post); emit('close')" class="menu-item">
        <span class="icon">🔁</span>
        <span>Репост</span>
      </button>

      <div class="menu-divider"></div>

      <button @click="handleReport" class="menu-item warn">
        <span class="icon">🚩</span>
        <span>Пожаловаться</span>
      </button>

      <div class="menu-divider"></div>

      <button @click="copyLink" class="menu-item">
        <span class="icon">🔗</span>
        <span>Копировать ссылку</span>
      </button>
      <button v-if="post.text" @click="copyText" class="menu-item">
        <span class="icon">📋</span>
        <span>Копировать текст</span>
      </button>
    </div>

    <!-- Delete Confirm Dialog -->
    <div v-if="showDeleteConfirm" class="confirm-dialog" @click.stop>
      <p class="confirm-text">Удалить пост? Это действие нельзя отменить.</p>
      <div class="confirm-actions">
        <button class="btn-cancel" @click="showDeleteConfirm = false">Отмена</button>
        <button class="btn-confirm-delete" @click="doDelete">Удалить</button>
      </div>
    </div>

    <!-- Hide Dialog -->
    <div v-if="showHideDialog" class="confirm-dialog" @click.stop>
      <p class="confirm-text">Скрыть этот пост?</p>
      <div class="hide-options">
        <button class="hide-option" @click="doHide('post')">
          <span>🚫</span> Только этот пост
        </button>
        <button class="hide-option" @click="doHide('author')">
          <span>👤</span> Все посты от @{{ post.author_username }}
        </button>
      </div>
      <button class="btn-cancel" @click="showHideDialog = false">Отмена</button>
    </div>

    <!-- Report Dialog (inline) -->
    <div v-if="showReport" class="confirm-dialog report-dialog" @click.stop>
      <p class="confirm-text">Причина жалобы:</p>
      <div class="reason-list">
        <button
          v-for="r in reportReasons"
          :key="r.id"
          class="reason-btn"
          :class="{ selected: selectedReason === r.id }"
          @click="selectedReason = r.id"
        >
          {{ r.icon }} {{ r.label }}
        </button>
      </div>
      <textarea
        v-model="reportComment"
        placeholder="Дополнительные пояснения..."
        class="report-textarea"
        rows="2"
      ></textarea>
      <div class="confirm-actions">
        <button class="btn-cancel" @click="showReport = false">Отмена</button>
        <button class="btn-confirm-delete" @click="submitReport" :disabled="!selectedReason || reporting">
          {{ reporting ? '...' : 'Отправить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '@/api/client'

interface Post {
  id: number
  text: string
  can_edit: boolean
  can_delete: boolean
  is_pinned: boolean
  is_bookmarked: boolean
  author_username?: string
}

const props = defineProps<{ post: Post }>()

const emit = defineEmits<{
  close: []
  edit: [post: Post]
  delete: [post: Post]
  pin: [post: Post]
  bookmark: [post: Post]
  hide: [post: Post]
  hideAuthor: [post: Post]
  repost: [post: Post]
  forward: [post: Post]
  reported: []
}>()

const showDeleteConfirm = ref(false)
const showHideDialog = ref(false)
const showReport = ref(false)
const selectedReason = ref('')
const reportComment = ref('')
const reporting = ref(false)

const reportReasons = [
  { id: 'spam', icon: '📢', label: 'Спам' },
  { id: 'copyright', icon: '©️', label: 'Нарушение авторских прав' },
  { id: 'inappropriate', icon: '🔞', label: 'Неприемлемый контент (18+)' },
  { id: 'harassment', icon: '😠', label: 'Оскорбления / травля' },
  { id: 'spoiler', icon: '⚠️', label: 'Спойлер без предупреждения' },
  { id: 'other', icon: '❓', label: 'Другое' },
]

const confirmDelete = () => {
  showDeleteConfirm.value = true
}

const doDelete = () => {
  emit('delete', props.post)
  emit('close')
}

const handleBookmark = () => {
  emit('bookmark', props.post)
  emit('close')
}

const handleHide = () => {
  showHideDialog.value = true
}

const doHide = (mode: 'post' | 'author') => {
  if (mode === 'author') {
    emit('hideAuthor', props.post)
  } else {
    emit('hide', props.post)
  }
  emit('close')
}

const handleForward = () => {
  emit('forward', props.post)
  emit('close')
}

const handleReport = () => {
  showReport.value = true
}

const submitReport = async () => {
  if (!selectedReason.value) return
  reporting.value = true
  try {
    await apiClient.post(`/social/posts/${props.post.id}/report/`, {
      reason: selectedReason.value,
      comment: reportComment.value,
    })
    emit('reported')
    emit('close')
  } catch (e) {
    console.error(e)
  } finally {
    reporting.value = false
  }
}

const copyLink = async () => {
  await navigator.clipboard.writeText(`${window.location.origin}/post/${props.post.id}`)
  emit('close')
}

const copyText = async () => {
  await navigator.clipboard.writeText(props.post.text)
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

@media (min-width: 640px) {
  .modal-overlay {
    align-items: center;
  }
}

.post-menu {
  background: #111;
  border-radius: 16px;
  padding: 0.5rem;
  width: 100%;
  max-width: 320px;
  border: 1px solid #1f1f1f;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  background: none;
  border: none;
  color: #ddd;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: background 0.2s;
  text-align: left;
}

.menu-item:hover {
  background: #1a1a1a;
}

.menu-item.danger { color: #ef4444; }
.menu-item.danger:hover { background: #2a1515; }
.menu-item.warn { color: #f59e0b; }
.menu-item.warn:hover { background: #2a2010; }

.menu-item .icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.hint {
  margin-left: auto;
  color: #555;
  font-size: 0.75rem;
}

.menu-divider {
  height: 1px;
  background: #1f1f1f;
  margin: 0.4rem 0;
}

/* Confirm/Dialog overlays */
.confirm-dialog {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 2rem);
  max-width: 320px;
  background: #161616;
  border: 1px solid #2a2a2a;
  border-radius: 16px;
  padding: 1.25rem;
  z-index: 10;
}

.confirm-text {
  color: #ddd;
  font-size: 0.9rem;
  margin: 0 0 1rem;
  text-align: center;
}

.confirm-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn-cancel {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-confirm-delete {
  background: #ef4444;
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-confirm-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Hide options */
.hide-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.hide-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #ddd;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s;
  width: 100%;
  text-align: left;
}

.hide-option:hover {
  background: #222;
}

/* Report */
.report-dialog {
  padding: 1rem;
}

.reason-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.reason-btn {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #aaa;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  text-align: left;
  transition: all 0.2s;
}

.reason-btn.selected {
  border-color: #667eea;
  background: #1a1f35;
  color: #8b9ef5;
}

.reason-btn:hover:not(.selected) {
  background: #222;
}

.report-textarea {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  color: #aaa;
  font-size: 0.8rem;
  resize: none;
  margin-bottom: 0.75rem;
  box-sizing: border-box;
}
</style>
