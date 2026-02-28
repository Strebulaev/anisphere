<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Приглашение в чат</h3>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="modal-body">
          <div v-if="invite" class="invite-info">
            <div class="invite-link-container">
              <label class="section-title">Ссылка-приглашение</label>
              <div class="invite-link">
                <input
                  :value="inviteLink"
                  readonly
                  class="invite-input"
                  ref="inviteLinkInput"
                />
                <button class="copy-btn" @click="copyLink" :disabled="copying">
                  {{ copying ? 'Скопировано!' : 'Копировать' }}
                </button>
              </div>
            </div>

            <div class="invite-details">
              <div class="detail-item">
                <span class="detail-label">Использовано:</span>
                <span class="detail-value">
                  {{ invite.uses_count }} / {{ invite.max_uses || '∞' }}
                </span>
              </div>

              <div v-if="invite.expires_at" class="detail-item">
                <span class="detail-label">Истекает:</span>
                <span class="detail-value">{{ formatDate(invite.expires_at) }}</span>
              </div>

              <div class="detail-item">
                <span class="detail-label">Статус:</span>
                <span :class="['detail-value', invite.is_active ? 'active' : 'inactive']">
                  {{ invite.is_active ? 'Активно' : 'Неактивно' }}
                </span>
              </div>
            </div>

            <div class="modal-actions">
              <button
                v-if="invite.is_active"
                class="btn-regenerate"
                @click="regenerateInvite"
                :disabled="loading"
              >
                {{ loading ? 'Пересоздание...' : 'Пересоздать ссылку' }}
              </button>
              <button
                v-if="invite.is_active"
                class="btn-revoke"
                @click="revokeInvite"
                :disabled="loading"
              >
                {{ loading ? 'Отзыв...' : 'Отозвать приглашение' }}
              </button>
            </div>
          </div>

          <div v-else class="create-invite">
            <div class="form-group">
              <label class="section-title">Истекает через</label>
              <select v-model="form.expiresIn" class="form-select">
                <option value="">Никогда</option>
                <option value="1">1 час</option>
                <option value="24">1 день</option>
                <option value="168">1 неделя</option>
                <option value="720">30 дней</option>
              </select>
            </div>

            <div class="form-group">
              <label class="section-title">Максимум использований</label>
              <input
                v-model.number="form.maxUses"
                type="number"
                placeholder="Без ограничений"
                class="form-input"
                min="1"
              />
            </div>

            <div class="modal-actions">
              <button class="btn-cancel" @click="close">Отмена</button>
              <button class="btn-create" @click="createInvite" :disabled="loading || !form.maxUses && !form.expiresIn">
                {{ loading ? 'Создание...' : 'Создать приглашение' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'
import type { ChatInvite } from '@/api/chats'

interface Props {
  isOpen: boolean
  chatId: number
  existingInvite?: ChatInvite | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', invite: ChatInvite): void
}>()

const chatExtrasStore = useChatExtrasStore()

const loading = ref(false)
const copying = ref(false)
const invite = ref<ChatInvite | null>(props.existingInvite || null)
const inviteLinkInput = ref<HTMLInputElement>()

const form = reactive({
  expiresIn: '',
  maxUses: null as number | null
})

const inviteLink = computed(() => {
  if (!invite.value) return ''
  return `${window.location.origin}/chat/invite/${invite.value.token}`
})

watch(() => props.existingInvite, (newVal) => {
  invite.value = newVal || null
})

const createInvite = async () => {
  loading.value = true
  try {
    const expiresAt = form.expiresIn ? new Date(Date.now() + (Number(form.expiresIn) || 0) * 60 * 60 * 1000).toISOString() : undefined

    const newInvite = await chatExtrasStore.createInvite({
      chat: props.chatId,
      expires_at: expiresAt,
      max_uses: form.maxUses || undefined
    })

    invite.value = newInvite
    emit('created', newInvite)
  } catch (error) {
    console.error('Error creating invite:', error)
  } finally {
    loading.value = false
  }
}

const regenerateInvite = async () => {
  if (!invite.value) return
  loading.value = true
  try {
    const newInvite = await chatExtrasStore.regenerateInvite(invite.value.id)
    invite.value = newInvite
  } catch (error) {
    console.error('Error regenerating invite:', error)
  } finally {
    loading.value = false
  }
}

const revokeInvite = async () => {
  if (!invite.value) return
  loading.value = true
  try {
    await chatExtrasStore.revokeInvite(invite.value.id)
  } catch (error) {
    console.error('Error revoking invite:', error)
  } finally {
    loading.value = false
  }
}

const copyLink = async () => {
  if (!inviteLinkInput.value) return
  copying.value = true
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    setTimeout(() => {
      copying.value = false
    }, 2000)
  } catch (error) {
    console.error('Error copying link:', error)
    copying.value = false
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const close = () => {
  emit('close')
  form.expiresIn = ''
  form.maxUses = null
  invite.value = null
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--color-background-surface);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background: var(--color-background-active);
}

.modal-body {
  padding: 1.5rem;
}

.invite-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.invite-link-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
}

.invite-link {
  display: flex;
  gap: 0.5rem;
}

.invite-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 0.875rem;
  background: var(--color-background);
  color: var(--color-text);
}

.copy-btn {
  padding: 0.75rem 1rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.copy-btn:hover {
  background: var(--color-accent-hover);
}

.copy-btn:disabled {
  background: var(--color-text-disabled);
  cursor: not-allowed;
}

.invite-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-background);
  border-radius: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.detail-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
}

.detail-value.active {
  color: #4caf50;
}

.detail-value.inactive {
  color: #f44336;
}

.create-invite {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-select,
.form-input {
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--color-background);
  color: var(--color-text);
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.modal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider);
}

.btn-cancel {
  padding: 0.625rem 1.25rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: var(--color-background-active);
}

.btn-create,
.btn-regenerate {
  padding: 0.625rem 1.25rem;
  background: var(--color-accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-create:hover,
.btn-regenerate:hover {
  background: var(--color-accent-hover);
}

.btn-create:disabled,
.btn-regenerate:disabled {
  background: var(--color-text-disabled);
  cursor: not-allowed;
}

.btn-revoke {
  padding: 0.625rem 1.25rem;
  background: rgba(244, 67, 54, 0.1);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #f44336;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-revoke:hover {
  background: rgba(244, 67, 54, 0.2);
}
</style>
