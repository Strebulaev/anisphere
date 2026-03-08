<template>
  <Teleport to="body">
  <Transition name="rm-anim">
    <div v-if="show" class="modal-overlay" @click.self="handleClose" @keydown.esc="handleClose">
      <div class="modal-content reminder-modal">
        <div class="modal-header">
          <h2 class="modal-title">Напомнить о просмотре</h2>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="anime-preview">
            <div v-if="animePosterUrl" style="width: 80px; height: 112px; flex-shrink: 0; border-radius: 8px; overflow: hidden;">
              <img
                :src="animePosterUrl"
                :alt="anime.title_ru || anime.title_en"
                style="width: 100%; height: 100%; object-fit: cover;"
                loading="lazy"
                @error="handlePosterError"
                @load=""
              />
            </div>
            <div v-else class="anime-poster-placeholder">
              <span>Нет постера</span>
            </div>
            <div class="anime-info">
              <h3 class="anime-title">{{ anime.title_ru || anime.title_en }}</h3>
              <p v-if="anime.year" class="anime-year">{{ anime.year }}</p>
            </div>
          </div>

          <div class="reminder-options">
            <label class="section-label">Когда напомнить:</label>
            <div class="time-presets">
              <button
                v-for="preset in timePresets"
                :key="preset.value"
                @click="selectPreset(preset.value)"
                :class="['preset-btn', { active: selectedPreset === preset.value }]"
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ preset.label }}
              </button>
            </div>

            <div v-if="showCalendar" class="custom-date">
              <label class="date-label">Выберите дату и время:</label>
              <input
                v-model="customDateTime"
                type="datetime-local"
                class="date-input"
                :min="minDateTime"
              />
            </div>

            <label v-if="isSeries" class="checkbox-label">
              <input
                v-model="repeatWeekly"
                type="checkbox"
                class="checkbox-input"
              />
              <span>Повторять каждую неделю</span>
            </label>
          </div>

          <div class="reminder-comment">
            <label class="comment-label">Комментарий (необязательно):</label>
            <textarea
              v-model="comment"
              placeholder="Добавьте заметку к напоминанию..."
              class="comment-input"
              rows="3"
              maxlength="200"
            ></textarea>
            <div class="comment-counter">{{ comment.length }}/200</div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            Отмена
          </button>
          <button
            @click="handleSave"
            :disabled="!canSave"
            class="btn btn-primary"
            type="button"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Установить напоминание
          </button>
        </div>
      </div>
    </div>
  </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Anime } from '@/types'
import { getMediaUrl } from '@/api/client'

interface Props {
  show: boolean
  anime: Anime
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  save: [data: ReminderData]
}>()

interface ReminderData {
  animeId: number
  reminderTime: Date
  repeatWeekly: boolean
  comment?: string
}

const selectedPreset = ref<string | null>(null)
const customDateTime = ref('')
const repeatWeekly = ref(false)
const comment = ref('')

// Computed для получения URL постера аниме
const animePosterUrl = computed(() => {
  const a = props.anime
  
  // Пробуем разные поля для постера (приоритет: poster -> poster_file -> poster_image_url -> poster_url)
  const posterFields = [
    a.poster,
    a.poster_file,
    a.poster_image_url,
    a.poster_url
  ]
  
  for (const poster of posterFields) {
    if (poster && typeof poster === 'string' && poster.trim() !== '') {
      const url = getMediaUrl(poster)
      // getMediaUrl может вернуть undefined, преобразуем в null для v-if
      if (url) return url
    }
  }
  return null
})

const timePresets = [
  { value: '1h', label: 'Через 1 час' },
  { value: '3h', label: 'Через 3 часа' },
  { value: 'tomorrow', label: 'Завтра' },
  { value: 'week', label: 'Через неделю' },
  { value: 'custom', label: 'Выбрать дату' }
]

const showCalendar = computed(() => selectedPreset.value === 'custom')

const isSeries = computed(() => {
  return props.anime.episodes && props.anime.episodes > 1
})

const minDateTime = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
})
  
const canSave = computed(() => {
  if (selectedPreset.value === 'custom') {
    return !!customDateTime.value
  }
  return !!selectedPreset.value
})

const selectPreset = (preset: string) => {
  selectedPreset.value = preset
  if (preset !== 'custom') {
    customDateTime.value = ''
  }
}

const calculateReminderTime = (): Date => {
  const now = new Date()
  
  switch (selectedPreset.value) {
    case '1h':
      now.setHours(now.getHours() + 1)
      return now
    case '3h':
      now.setHours(now.getHours() + 3)
      return now
    case 'tomorrow':
      now.setDate(now.getDate() + 1)
      now.setHours(12, 0, 0, 0)
      return now
    case 'week':
      now.setDate(now.getDate() + 7)
      now.setHours(12, 0, 0, 0)
      return now
    case 'custom':
      return new Date(customDateTime.value)
    default:
      return now
  }
}

const handleSave = () => {
  const data: ReminderData = {
    animeId: props.anime.id,
    reminderTime: calculateReminderTime(),
    repeatWeekly: repeatWeekly.value,
    comment: comment.value || undefined
  }
  
  emit('save', data)
  resetForm()
}

const handleClose = () => {
  emit('close')
}

const handlePosterError = (event: Event) => {
  const img = event.target as HTMLImageElement
  console.error('🎬 Poster load error:', img.src)
}

const resetForm = () => {
  selectedPreset.value = null
  customDateTime.value = ''
  repeatWeekly.value = false
  comment.value = ''
}

watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--surface-2, var(--color-background-surface));
  border-radius: 1rem;
  max-width: 480px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  transform: scale(1);
  opacity: 1;
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
}

.reminder-modal {
  padding: 0;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle, var(--color-divider));
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 36px;
  height: 36px;
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
  color: var(--color-accent-pink);
}

.modal-body {
  padding: 1.5rem;
}

.anime-preview {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: var(--color-background-active);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
}

.anime-poster {
  width: 60px;
  height: 84px;
  object-fit: cover;
  border-radius: 0.5rem;
  flex-shrink: 0;
}

.anime-poster-placeholder {
  width: 60px;
  height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  border-radius: 0.5rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.anime-year {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.reminder-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.section-label {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.time-presets {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.5rem;
}

.preset-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.preset-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.preset-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.custom-date {
  padding: 1rem;
  background-color: var(--color-background-active);
  border-radius: 0.5rem;
}

.date-label {
  display: block;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.date-input {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.date-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.reminder-comment {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.comment-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.comment-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  resize: vertical;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
}

.comment-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.comment-counter {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-align: right;
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

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.rm-anim-enter-active { transition: opacity 0.22s ease; }
.rm-anim-leave-active { transition: opacity 0.18s ease; }
.rm-anim-enter-from,
.rm-anim-leave-to { opacity: 0; }

.rm-anim-enter-active .modal-content {
  transition: transform 0.25s cubic-bezier(0.34, 1.4, 0.64, 1), opacity 0.22s ease;
}
.rm-anim-leave-active .modal-content {
  transition: transform 0.18s ease, opacity 0.18s ease;
}
.rm-anim-enter-from .modal-content {
  transform: scale(0.90) translateY(20px);
  opacity: 0;
}
.rm-anim-leave-to .modal-content {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
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

  .time-presets {
    grid-template-columns: repeat(2, 1fr);
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
