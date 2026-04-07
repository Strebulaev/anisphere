$<template>
  <div class="modal-overlay" v-if="show" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Добавить озвучку</h2>
        <button @click="close" class="close-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="anime-info">
          <img v-if="animePoster" :src="animePoster" :alt="animeTitle" class="anime-poster">
          <div v-else class="anime-poster-placeholder"> <SakuraIcon name="play" /> </div>
          <div class="anime-details">
            <span class="anime-title">{{ animeTitle }}</span>
          </div>
        </div>

        <form @submit.prevent="handleSubmit" class="dub-form">
          <div class="form-group">
            <label for="dub-name">Название озвучки *</label>
            <input
              id="dub-name"
              v-model="formData.name"
              type="text"
              placeholder="Например: AniMedia, SHIZA Project"
              required
            >
          </div>

          <div class="form-group">
            <label for="dub-studio">Название студии</label>
            <input
              id="dub-studio"
              v-model="formData.studio"
              type="text"
              placeholder="Название вашей студии"
            >
          </div>

          <div class="form-group">
            <label for="dub-quality">Качество видео *</label>
            <select id="dub-quality" v-model="formData.quality" required>
              <option value="">Выберите качество</option>
              <option value="360p">360p</option>
              <option value="480p">480p</option>
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
              <option value="4K">4K</option>
            </select>
          </div>

          <div class="form-group">
            <label for="dub-episodes">Количество озвученных серий</label>
            <input
              id="dub-episodes"
              v-model.number="formData.episodes_done"
              type="number"
              min="0"
              placeholder="Сколько серий уже озвучено"
            >
          </div>

          <div class="form-group">
            <label for="dub-video-url">Ссылка на видео (mp4, m3u8) *</label>
            <input
              id="dub-video-url"
              v-model="formData.video_url"
              type="url"
              placeholder="https://example.com/video.mp4"
              required
            >
            <p class="form-hint">Прямая ссылка на видеофайл или m3u8 плейлист</p>
          </div>

          <div class="form-group">
            <label for="dub-logo">URL логотипа студии</label>
            <input
              id="dub-logo"
              v-model="formData.logo_url"
              type="url"
              placeholder="https://example.com/logo.png"
            >
          </div>

          <div class="form-group">
            <label for="dub-description">Описание</label>
            <textarea
              id="dub-description"
              v-model="formData.description"
              rows="3"
              placeholder="Дополнительная информация об озвучке"
            ></textarea>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="formData.is_complete"
                class="checkbox-input"
              >
              <span>Озвучка завершена полностью</span>
            </label>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <div class="form-actions">
            <button type="button" @click="close" class="btn btn-outline">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <span v-if="loading" class="btn-spinner"></span>
              {{ loading ? 'Отправка...' : 'Отправить на модерацию' }}
            </button>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <p class="footer-text">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Ваша озвучка будет проверена модератором перед публикацией
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import apiClient from '@/api/client'

interface Props {
  show: boolean
  animeId: number
  animeTitle: string
  animePoster?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  dubAdded: []
}>()

const formData = reactive({
  name: '',
  studio: '',
  quality: '',
  episodes_done: 0,
  video_url: '',
  logo_url: '',
  description: '',
  is_complete: false
})

const loading = ref(false)
const errorMessage = ref('')

const close = () => {
  emit('close')
  resetForm()
}

const resetForm = () => {
  formData.name = ''
  formData.studio = ''
  formData.quality = ''
  formData.episodes_done = 0
  formData.video_url = ''
  formData.logo_url = ''
  formData.description = ''
  formData.is_complete = false
  errorMessage.value = ''
  loading.value = false
}

const handleSubmit = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    const response = await apiClient.post(`/anime/${props.animeId}/custom_dubs/`, {
      name: formData.name,
      studio: formData.studio || formData.name,
      quality: formData.quality,
      episodes_done: formData.episodes_done || 0,
      video_url: formData.video_url,
      logo_url: formData.logo_url,
      description: formData.description,
      is_complete: formData.is_complete
    })

    emit('dubAdded')
    close()
  } catch (err: any) {
    console.error('Ошибка добавления озвучки:', err)
    errorMessage.value = err.response?.data?.detail || 'Не удалось добавить озвучку. Попробуйте позже.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 20px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(90deg);
}

.modal-body {
  padding: 1.5rem;
}

/* Информация об аниме */
.anime-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.anime-poster {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 8px;
}

.anime-poster-placeholder {
  width: 60px;
  height: 90px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.anime-details {
  flex: 1;
}

.anime-title {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

/* Форма */
.dub-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #fff;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.875rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  background: rgba(255, 255, 255, 0.08);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #6b7280;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-hint {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-label span {
  font-size: 0.9rem;
  color: #fff;
}

.error-message {
  padding: 0.875rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: #fca5a5;
  font-size: 0.875rem;
  margin: 0;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-outline {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.btn-outline:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.modal-footer {
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.footer-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
  text-align: center;
  justify-content: center;
}

/* Адаптивность */
@media (max-width: 640px) {
  .modal-container {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body {
    padding: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .anime-info {
    flex-direction: column;
    text-align: center;
  }
}
</style>
