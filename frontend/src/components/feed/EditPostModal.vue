<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="edit-post-modal" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <h2>Редактирование поста</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Content -->
      <div class="content-area">
        <textarea
          ref="textArea"
          v-model="text"
          class="text-input"
          placeholder="Текст поста..."
          @input="autoResize"
        ></textarea>

        <div class="char-count" :class="{ warning: text.length > 4500, error: text.length > 5000 }">
          {{ text.length }}/5000
        </div>

        <!-- Spoiler toggle -->
        <div class="toggles-row">
          <label class="toggle-label">
            <span class="toggle-switch" :class="{ active: isSpoiler }">
              <span class="toggle-slider"></span>
            </span>
            <input type="checkbox" v-model="isSpoiler" class="toggle-input">
            <span class="toggle-text">Спойлер</span>
          </label>
          <label class="toggle-label">
            <span class="toggle-switch" :class="{ active: allowComments }">
              <span class="toggle-slider"></span>
            </span>
            <input type="checkbox" v-model="allowComments" class="toggle-input">
            <span class="toggle-text">Комментарии</span>
          </label>
        </div>

        <!-- Spoiler description -->
        <div v-if="isSpoiler" class="spoiler-settings">
          <input
            v-model="spoilerDescription"
            type="text"
            placeholder="О чём спойлер? (например: Конец Наруто)"
            class="spoiler-for-input"
          >
        </div>

        <!-- Visibility -->
        <div class="visibility-row">
          <span class="visibility-label">Видимость:</span>
          <div class="visibility-options">
            <button
              v-for="(option, key) in visibilityOptions"
              :key="key"
              @click="visibility = key"
              class="visibility-opt"
              :class="{ active: visibility === key }"
            >
              <SakuraIcon v-if="isIconName(option.icon)" :name="option.icon" :size="16" />
              <span v-else>{{ option.icon }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="submit-row">
        <button @click="savePost" :disabled="!canSubmit || saving" class="submit-btn">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import apiClient from '@/api/client'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

const props = defineProps<{ post: any }>()
const emit = defineEmits<{ close: []; updated: [post: any] }>()

const text = ref('')
const visibility = ref('public')
const allowComments = ref(true)
const isSpoiler = ref(false)
const spoilerDescription = ref('')
const saving = ref(false)
const textArea = ref<HTMLTextAreaElement | null>(null)

// Проверка - является ли icon именем иконки (а не эмодзи)
const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon)
}

const visibilityOptions: Record<string, { icon: string; label: string }> = {
  public:    { icon: 'globe', label: 'Публично' },
  followers: { icon: 'users', label: 'Подписчики' },
  friends:   { icon: 'users', label: 'Друзья' },
  private:   { icon: 'lock', label: 'Только я' },
}

const canSubmit = computed(() => text.value.trim().length > 0 && text.value.length <= 5000)

const autoResize = () => {
  if (!textArea.value) return
  textArea.value.style.height = 'auto'
  textArea.value.style.height = textArea.value.scrollHeight + 'px'
}

const savePost = async () => {
  if (!canSubmit.value || saving.value) return
  saving.value = true
  try {
    const payload: any = {
      text: text.value,
      visibility: visibility.value,
      allow_comments: allowComments.value,
      is_spoiler: isSpoiler.value,
    }
    if (isSpoiler.value && spoilerDescription.value.trim()) {
      payload.spoiler_description = spoilerDescription.value.trim()
    }

    const { data } = await apiClient.put(`/social/posts/${props.post.id}/edit/`, payload)
    emit('updated', data)
  } catch (e: any) {
    alert('Ошибка при сохранении: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  // Заполняем данными из поста
  text.value = props.post.text || ''
  visibility.value = props.post.visibility || 'public'
  allowComments.value = props.post.allow_comments ?? true
  isSpoiler.value = props.post.is_spoiler ?? false
  spoilerDescription.value = props.post.spoiler_description || props.post.spoiler_for || ''
  
  await nextTick()
  autoResize()
  textArea.value?.focus()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.edit-post-modal {
  background: var(--surface-1, #0a0a0a);
  border-radius: 16px;
  border: 1px solid var(--border-subtle, #1a1a1a);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.7);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle, #1a1a1a);
}

.modal-header h2 {
  color: var(--text-primary, #fff);
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary, #555);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: var(--text-primary, #fff);
  background: var(--surface-3, #1a1a1a);
}

.content-area {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.text-input {
  width: 100%;
  min-height: 120px;
  max-height: 50vh;
  background: transparent;
  border: none;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.95rem;
  line-height: 1.65;
  resize: none;
  box-sizing: border-box;
  font-family: inherit;
}

.text-input:focus {
  outline: none;
}

.text-input::placeholder {
  color: var(--text-tertiary, #444);
}

.char-count {
  text-align: right;
  color: var(--text-tertiary, #555);
  font-size: 0.75rem;
}

.char-count.warning {
  color: var(--warning, #f59e0b);
}

.char-count.error {
  color: var(--danger, #ef4444);
}

.toggles-row {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding-top: 0.5rem;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--text-secondary, #888);
  font-size: 0.875rem;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.toggle-label:hover {
  color: var(--text-primary, #ddd);
}

.toggle-input {
  display: none;
}

.toggle-switch {
  position: relative;
  width: 38px;
  height: 22px;
  background: var(--surface-4, #222);
  border-radius: 22px;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.toggle-slider {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: var(--text-tertiary, #555);
  border-radius: 50%;
  transition: all 0.25s ease;
}

.toggle-switch.active {
  background: var(--accent, #7c5cfc);
}

.toggle-switch.active .toggle-slider {
  left: 19px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(124, 92, 252, 0.4);
}

.spoiler-settings {
  margin-top: 0.25rem;
}

.spoiler-for-input {
  width: 100%;
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-default, #252525);
  color: var(--text-primary, #e0e0e0);
  padding: 0.625rem 0.875rem;
  border-radius: 10px;
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.spoiler-for-input:focus {
  outline: none;
  border-color: var(--warning, #fbbf24);
}

.spoiler-for-input::placeholder {
  color: var(--text-tertiary, #555);
}

.visibility-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-top: 0.5rem;
}

.visibility-label {
  color: var(--text-secondary, #888);
  font-size: 0.875rem;
}

.visibility-options {
  display: flex;
  gap: 0.35rem;
}

.visibility-opt {
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-subtle, #1f1f1f);
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.visibility-opt:hover {
  background: var(--surface-4, #1f1f1f);
}

.visibility-opt.active {
  background: var(--accent-subtle, rgba(124, 92, 252, 0.15));
  border-color: var(--accent, #7c5cfc);
}

.submit-row {
  padding: 1rem 1.5rem 1.25rem;
}

.submit-btn {
  width: 100%;
  background: var(--accent, #7c5cfc);
  color: #fff;
  border: none;
  padding: 0.8rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover, #6b4de8);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
