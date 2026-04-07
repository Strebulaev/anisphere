<template>
  <Teleport to="body">
  <Transition name="alm-anim">
    <div v-if="show" class="modal-overlay" @click.self="handleClose" @keydown.esc="handleClose">
      <div class="modal-content add-library-modal">
        <div class="modal-header">
          <h2 class="modal-title">Добавить в коллекцию</h2>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- Информация об аниме -->
          <div class="anime-preview">
            <img
              v-if="animeData?.poster"
              :src="getMediaUrl(animeData.poster) || undefined"
              :alt="animeData.title"
              class="anime-poster"
              @error="handleImageError"
            />
            <div v-else class="anime-poster-placeholder">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="2" width="20" height="20" rx="2"/>
                <path d="M12 2v20M2 12h20"/>
              </svg>
            </div>
            <div class="anime-info">
              <h3 class="anime-title">{{ animeData?.title || 'Загрузка...' }}</h3>
              <p v-if="animeData?.year" class="anime-year">{{ animeData.year }}</p>
            </div>
          </div>

          <!-- Выбор статуса -->
          <div class="status-section">
            <label class="section-label">Статус</label>
            <div class="status-options">
              <button
                v-for="option in statusOptions"
                :key="option.value"
                :class="['status-btn', { active: selectedStatus === option.value }]"
                @click="selectedStatus = option.value as 'planned' | 'started' | 'completed' | 'dropped'"
                type="button"
              >
                <span class="status-icon">{{ option.icon }}</span>
                <span class="status-text">{{ option.label }}</span>
              </button>
            </div>
          </div>

          <!-- Оценка -->
          <div v-if="selectedStatus === 'completed'" class="rating-section">
            <label class="section-label">Ваша оценка</label>
            <div class="rating-stars">
              <button
                v-for="star in 10"
                :key="star"
                :class="['star-btn', { active: (selectedRating || 0) >= star }]"
                @click="selectedRating = star"
                type="button"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" :fill="(selectedRating || 0) >= star ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
              </button>
              <span v-if="selectedRating" class="rating-value">{{ selectedRating }}/10</span>
            </div>
          </div>

          <!-- Текущая серия -->
          <div v-if="selectedStatus === 'started'" class="episode-section">
            <label class="section-label">Текущая серия</label>
            <div class="episode-input">
              <button @click="decrementEpisode" class="episode-btn" type="button">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
              <input
                v-model.number="currentEpisode"
                type="number"
                min="1"
                :max="animeData?.episodes || 999"
                class="episode-field"
              />
              <span v-if="animeData?.episodes" class="episode-total">/ {{ animeData.episodes }}</span>
              <button @click="incrementEpisode" class="episode-btn" type="button">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Заметка -->
          <div class="note-section">
            <label class="section-label">Заметка (необязательно)</label>
            <textarea
              v-model="note"
              placeholder="Добавьте заметку к аниме..."
              class="note-input"
              rows="3"
              maxlength="500"
            ></textarea>
            <div class="note-counter">{{ note.length }}/500</div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            Отмена
          </button>
          <button
            @click="handleSave"
            :disabled="saving"
            class="btn btn-primary"
            type="button"
          >
            <svg v-if="saving" class="spinner-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ saving ? 'Сохранение...' : 'Добавить' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { animeApi } from '@/api/anime'
import { getMediaUrl } from '@/api/client'

interface Props {
  show: boolean
  animeId: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  added: []
}>()

interface AnimeInfo {
  title: string
  poster: string | null
  year: number | null
  episodes: number | null
}

const animeData = ref<AnimeInfo | null>(null)
const selectedStatus = ref<'planned' | 'started' | 'completed' | 'dropped'>('planned')
const selectedRating = ref<number | null>(null)
const currentEpisode = ref(1)
const note = ref('')
const saving = ref(false)

const statusOptions = [
  { value: 'planned', label: 'Запланировано', icon: '📋' },
  { value: 'started', label: 'Смотрю', icon: '👀' },
  { value: 'completed', label: 'Просмотрено', icon: '☑️' },
  { value: 'dropped', label: 'Брошено', icon: '✖️' },
]

const handleClose = () => {
  emit('close')
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

const incrementEpisode = () => {
  const max = animeData.value?.episodes || 999
  if (currentEpisode.value < max) {
    currentEpisode.value++
  }
}

const decrementEpisode = () => {
  if (currentEpisode.value > 1) {
    currentEpisode.value--
  }
}

const handleSave = async () => {
  if (saving.value) return
  
  saving.value = true
  
  try {
    await animeApi.addToLibrary({
      anime: props.animeId,
      status: selectedStatus.value,
      rating: selectedRating.value,
      current_episode: selectedStatus.value === 'started' ? currentEpisode.value : undefined,
      notes: note.value || undefined
    })
    
    emit('added')
    resetForm()
  } catch (error) {
    console.error('Ошибка добавления в коллекцию:', error)
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  selectedStatus.value = 'planned'
  selectedRating.value = null
  currentEpisode.value = 1
  note.value = ''
}

const loadAnimeInfo = async () => {
  try {
    const response = await animeApi.get(props.animeId)
    animeData.value = {
      title: response.title_ru || response.title_en || '',
      poster: response.poster_url || response.poster_image_url || null,
      year: response.year || null,
      episodes: response.episodes || null
    }
    
    // Установить текущую серию по умолчанию
    if (response.episodes) {
      currentEpisode.value = 1
    }
  } catch (error) {
    console.error('Ошибка загрузки информации об аниме:', error)
  }
}

watch(() => props.show, (newVal) => {
  if (newVal && props.animeId) {
    loadAnimeInfo()
    resetForm()
  }
})

onMounted(() => {
  if (props.show && props.animeId) {
    loadAnimeInfo()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.82);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

.modal-content {
  background-color: #1a1a1a;
  border-radius: 1rem;
  max-width: 450px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #333;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #fff;
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
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background-color: #333;
  color: #fff;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.anime-preview {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: #252525;
  border-radius: 0.5rem;
  margin-bottom: 1.25rem;
}

.anime-poster {
  width: 48px;
  height: 67px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.anime-poster-placeholder {
  width: 48px;
  height: 67px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #333;
  border-radius: 0.375rem;
  color: #666;
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.anime-year {
  font-size: 0.8125rem;
  color: #999;
  margin: 0;
}

.section-label {
  display: block;
  font-size: 0.8125rem;
  color: #999;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.status-section {
  margin-bottom: 1.25rem;
}

.status-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.status-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: #252525;
  border: 1px solid #333;
  border-radius: 0.5rem;
  color: #999;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
}

.status-btn:hover {
  border-color: #3a86ff;
  color: #fff;
}

.status-btn.active {
  background-color: rgba(58, 134, 255, 0.15);
  border-color: #3a86ff;
  color: #3a86ff;
}

.status-icon {
  font-size: 1rem;
}

.status-text {
  font-weight: 500;
}

.rating-section {
  margin-bottom: 1.25rem;
}

.rating-stars {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.star-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #444;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.star-btn:hover,
.star-btn.active {
  color: #ffa500;
  transform: scale(1.1);
}

.rating-value {
  margin-left: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffa500;
}

.episode-section {
  margin-bottom: 1.25rem;
}

.episode-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.episode-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #252525;
  border: 1px solid #333;
  border-radius: 0.5rem;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
}

.episode-btn:hover {
  border-color: #3a86ff;
  color: #fff;
}

.episode-field {
  width: 60px;
  padding: 0.5rem;
  background-color: #252525;
  border: 1px solid #333;
  border-radius: 0.5rem;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
  outline: none;
}

.episode-field:focus {
  border-color: #3a86ff;
}

.episode-total {
  color: #666;
  font-size: 0.875rem;
}

.note-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.note-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #333;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #fff;
  background-color: #252525;
  outline: none;
  resize: vertical;
  transition: all 0.2s;
  font-family: inherit;
}

.note-input:focus {
  border-color: #3a86ff;
}

.note-input::placeholder {
  color: #666;
}

.note-counter {
  font-size: 0.75rem;
  color: #666;
  text-align: right;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #333;
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
  transition: all 0.2s;
  border: 1px solid;
  flex: 1;
}

.btn-primary {
  background-color: #3a86ff;
  border-color: #3a86ff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2d7af7;
  border-color: #2d7af7;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: transparent;
  border-color: #444;
  color: #999;
}

.btn-secondary:hover {
  background-color: #333;
  border-color: #555;
  color: #fff;
}

.spinner-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.alm-anim-enter-active { transition: opacity 0.22s ease; }
.alm-anim-leave-active { transition: opacity 0.18s ease; }
.alm-anim-enter-from, .alm-anim-leave-to { opacity: 0; }

.alm-anim-enter-active .modal-content {
  transition: transform 0.25s cubic-bezier(0.34,1.4,0.64,1), opacity 0.22s ease;
}
.alm-anim-leave-active .modal-content {
  transition: transform 0.18s ease, opacity 0.18s ease;
}
.alm-anim-enter-from .modal-content { transform: scale(0.90) translateY(20px); opacity: 0; }
.alm-anim-leave-to .modal-content   { transform: scale(0.95) translateY(8px);  opacity: 0; }

@media (max-width: 480px) {
  .status-options {
    grid-template-columns: 1fr;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
}
</style>
