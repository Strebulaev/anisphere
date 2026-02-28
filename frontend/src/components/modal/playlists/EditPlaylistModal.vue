<template>
  <BaseModal
    :show="show"
    @close="$emit('close')"
    title="Изменить плейлист"
  >
    <form @submit.prevent="handleSubmit" class="edit-playlist-form">
      <div class="form-group">
        <label for="title" class="form-label">Название плейлиста</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          required
          class="form-input"
          placeholder="Введите название"
        />
      </div>

      <div class="form-group">
        <label for="description" class="form-label">Описание</label>
        <textarea
          id="description"
          v-model="form.description"
          rows="4"
          class="form-input"
          placeholder="Расскажите о плейлисте"
        ></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">Обложка</label>
        
        <div class="cover-upload">
          <!-- Текущая обложка -->
          <div v-if="currentCover" class="current-cover">
            <img :src="currentCover" alt="Текущая обложка" />
            <button
              type="button"
              class="remove-cover-btn"
              @click="removeCover"
            >
              Удалить обложку
            </button>
          </div>
          
          <div v-else class="cover-placeholder">
            <span class="placeholder-icon">📁</span>
            <p>Нет обложки</p>
            <p class="placeholder-text">Обложка будет автоматически создана из постеров аниме</p>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Тип плейлиста</label>
        <div class="radio-group">
          <label class="radio-option">
            <input
              v-model="form.is_public"
              type="radio"
              :value="true"
            />
            <span class="radio-label">
              <span class="radio-icon">🌍</span>
              <span>Публичный</span>
              <span class="radio-desc">Виден всем пользователям</span>
            </span>
          </label>
          <label class="radio-option">
            <input
              v-model="form.is_public"
              type="radio"
              :value="false"
            />
            <span class="radio-label">
              <span class="radio-icon">🔒</span>
              <span>Приватный</span>
              <span class="radio-desc">Только для вас</span>
            </span>
          </label>
        </div>
      </div>

      <div class="form-actions">
        <button
          type="button"
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Отмена
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading"
        >
          {{ loading ? 'Сохранение...' : 'Сохранить изменения' }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import playlistsApi, { type Playlist } from '@/api/playlists'

interface Props {
  show: boolean
  playlist: Playlist
}

interface Emits {
  (e: 'close'): void
  (e: 'saved', playlist: Playlist): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const form = ref({
  title: '',
  description: '',
  is_public: true
})

const currentCover = computed(() => {
  return props.playlist.cover_image || null
})

// Инициализация формы при открытии
watch(() => props.show, (show) => {
  if (show && props.playlist) {
    form.value = {
      title: props.playlist.title,
      description: props.playlist.description || '',
      is_public: props.playlist.is_public
    }
  }
})

const handleSubmit = async () => {
  loading.value = true
  
  try {
    const response = await playlistsApi.updatePlaylist(
      props.playlist.id,
      form.value
    )
    emit('saved', response.data)
    emit('close')
  } catch (error: any) {
    console.error('Ошибка обновления плейлиста:', error)
    alert('Не удалось обновить плейлист: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const removeCover = async () => {
  if (!confirm('Удалить обложку?')) return
  
  try {
    await playlistsApi.updatePlaylist(props.playlist.id, { cover_image: null })
    emit('saved', { ...props.playlist, cover_image: null })
    emit('close')
  } catch (error: any) {
    console.error('Ошибка удаления обложки:', error)
    alert('Не удалось удалить обложку')
  }
}
</script>

<style scoped>
.edit-playlist-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.form-input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: var(--color-text-disabled);
}

.cover-upload {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.current-cover {
  position: relative;
  border-radius: 0.75rem;
  overflow: hidden;
}

.current-cover img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}

.remove-cover-btn {
  position: absolute;
  bottom: 0.75rem;
  right: 0.75rem;
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.remove-cover-btn:hover {
  background: rgba(239, 68, 68, 1);
}

.cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 2px dashed var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-surface);
  color: var(--color-text-tertiary);
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.placeholder-text {
  font-size: 0.8125rem;
  margin-top: 0.25rem;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-option:hover {
  border-color: var(--color-accent);
  background: var(--color-surface);
}

.radio-option input[type="radio"] {
  margin-top: 0.25rem;
}

.radio-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.radio-icon {
  font-size: 1.125rem;
}

.radio-desc {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}

.btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-surface-hover);
}

.btn-primary {
  background: var(--color-accent);
  color: white;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
