<template>
  <Teleport to="body">
  <Transition name="rm-anim">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content reminder-modal">

        <!-- ── Шапка ──────────────────────────────────────────── -->
        <div class="modal-header">
          <div class="header-left">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <h2 class="modal-title">Напоминание</h2>
          </div>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- ── Тело ───────────────────────────────────────────── -->
        <div class="modal-body">

          <!-- Превью аниме -->
          <div class="anime-preview">
            <div class="preview-poster">
              <img
                v-if="animePosterUrl"
                :src="animePosterUrl"
                :alt="anime.title_ru || anime.title_en"
                @error="handlePosterError"
              />
              <span v-else class="poster-fallback"> <SakuraIcon name="play" /> </span>
            </div>
            <div class="preview-info">
              <p class="preview-title">{{ anime.title_ru || anime.title_en }}</p>
              <p v-if="anime.year" class="preview-meta">{{ anime.year }}</p>
            </div>
          </div>

          <!-- ── Секция: Когда ───────────────────────────────── -->
          <div class="section">
            <div class="section-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              Когда напомнить
            </div>

            <!-- Быстрые пресеты -->
            <div class="presets">
              <button
                v-for="p in quickPresets"
                :key="p.value"
                @click="applyPreset(p)"
                :class="['preset-chip', { active: activePreset === p.value }]"
                type="button"
              >{{ p.label }}</button>
            </div>

            <!-- Дата и время — всегда видны -->
            <div class="datetime-row">
              <div class="dt-field">
                <label class="dt-label">Дата</label>
                <input
                  v-model="dateValue"
                  type="date"
                  class="dt-input"
                  :min="minDate"
                  @change="onDateTimeManualChange"
                />
              </div>
              <div class="dt-field">
                <label class="dt-label">Время</label>
                <input
                  v-model="timeValue"
                  type="time"
                  class="dt-input"
                  @change="onDateTimeManualChange"
                />
              </div>
            </div>

            <!-- Превью итоговой даты -->
            <div v-if="dateValue && timeValue" class="datetime-preview">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {{ formattedDateTime }}
            </div>
          </div>

          <!-- ── Секция: Повторение ──────────────────────────── -->
          <div class="section">
            <div class="section-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>
                <polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>
              </svg>
              Повторение
            </div>

            <div class="repeat-grid">
              <button
                v-for="r in repeatOptions"
                :key="r.value"
                @click="selectRepeat(r.value as 'none' | 'custom' | 'weekly' | 'biweekly' | 'monthly')"
                :class="['repeat-btn', { active: repeatMode === r.value }]"
                type="button"
              >
                <span class="repeat-icon">{{ r.icon }}</span>
                <span class="repeat-label">{{ r.label }}</span>
              </button>
            </div>

            <!-- Кастомный интервал -->
            <Transition name="slide-down">
              <div v-if="repeatMode === 'custom'" class="custom-repeat">
                <span class="custom-repeat-text">Каждые</span>
                <div class="custom-repeat-stepper">
                  <button @click="customDays = Math.max(1, customDays - 1)" type="button" class="stepper-btn">−</button>
                  <input
                    v-model.number="customDays"
                    type="number"
                    min="1"
                    max="365"
                    class="stepper-input"
                  />
                  <button @click="customDays = Math.min(365, customDays + 1)" type="button" class="stepper-btn">+</button>
                </div>
                <span class="custom-repeat-text">{{ daysLabel(customDays) }}</span>
              </div>
            </Transition>

            <!-- Дата окончания повторений -->
            <Transition name="slide-down">
              <div v-if="repeatMode !== 'none'" class="repeat-end">
                <label class="repeat-end-toggle">
                  <input v-model="hasEndDate" type="checkbox" class="toggle-check" />
                  <span class="toggle-label">Завершить повторения</span>
                </label>
                <Transition name="slide-down">
                  <div v-if="hasEndDate" class="dt-field" style="margin-top: 8px;">
                    <label class="dt-label">Дата окончания</label>
                    <input
                      v-model="endDate"
                      type="date"
                      class="dt-input"
                      :min="dateValue || minDate"
                    />
                  </div>
                </Transition>
              </div>
            </Transition>
          </div>

          <!-- ── Секция: Заметка ─────────────────────────────── -->
          <div class="section">
            <div class="section-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Заметка
              <span class="label-optional">(необязательно)</span>
            </div>
            <textarea
              v-model="comment"
              placeholder="Добавьте заметку..."
              class="comment-input"
              rows="2"
              maxlength="200"
            ></textarea>
            <div class="char-count">{{ comment.length }}/200</div>
          </div>

        </div><!-- /modal-body -->

        <!-- ── Футер ──────────────────────────────────────────── -->
        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-cancel" type="button">Отмена</button>
          <button
            @click="handleSave"
            :disabled="!canSave"
            class="btn btn-save"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Сохранить
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

export interface ReminderData {
  animeId: number
  reminderTime: Date
  repeatWeekly: boolean
  repeatIntervalDays?: number
  endDate?: Date
  comment?: string
}

// ── Состояние ────────────────────────────────────────────────
const dateValue   = ref('')
const timeValue   = ref('')
const activePreset = ref<string | null>(null)

const repeatMode  = ref<'none' | 'weekly' | 'biweekly' | 'monthly' | 'custom'>('none')
const customDays  = ref(3)
const hasEndDate  = ref(false)
const endDate     = ref('')

const comment = ref('')

// ── Постер ───────────────────────────────────────────────────
const animePosterUrl = computed(() => {
  const a = props.anime
  for (const f of [a.poster, a.poster_file, a.poster_image_url, a.poster_url]) {
    if (f && typeof f === 'string' && f.trim()) {
      const url = getMediaUrl(f)
      if (url) return url
    }
  }
  return null
})

// ── Минимальная дата ─────────────────────────────────────────
const minDate = computed(() => new Date().toISOString().slice(0, 10))

// ── Быстрые пресеты ──────────────────────────────────────────
const quickPresets = [
  { value: '30m',       label: 'Через 30 мин' },
  { value: '1h',        label: 'Через 1 час'  },
  { value: '3h',        label: 'Через 3 часа' },
  { value: 'evening',   label: 'Сегодня вечером' },
  { value: 'tomorrow',  label: 'Завтра'        },
  { value: 'weekend',   label: 'В выходные'   },
  { value: 'week',      label: 'Через неделю' },
]

const applyPreset = (p: { value: string; label: string }) => {
  activePreset.value = p.value
  const d = new Date()

  switch (p.value) {
    case '30m':
      d.setMinutes(d.getMinutes() + 30)
      break
    case '1h':
      d.setHours(d.getHours() + 1)
      break
    case '3h':
      d.setHours(d.getHours() + 3)
      break
    case 'evening':
      d.setHours(21, 0, 0, 0)
      if (d <= new Date()) d.setDate(d.getDate() + 1)
      break
    case 'tomorrow':
      d.setDate(d.getDate() + 1)
      d.setHours(12, 0, 0, 0)
      break
    case 'weekend': {
      const day = d.getDay()
      const daysUntilSat = day === 6 ? 7 : (6 - day)
      d.setDate(d.getDate() + daysUntilSat)
      d.setHours(14, 0, 0, 0)
      break
    }
    case 'week':
      d.setDate(d.getDate() + 7)
      d.setHours(12, 0, 0, 0)
      break
  }

  dateValue.value = d.toISOString().slice(0, 10)
  timeValue.value = d.toTimeString().slice(0, 5)
}

const onDateTimeManualChange = () => {
  activePreset.value = null
}

// ── Повторение ───────────────────────────────────────────────
const repeatOptions = [
  { value: 'none',      icon: '🚫', label: 'Не повторять' },
  { value: 'weekly',    icon: '📅', label: 'Каждую неделю' },
  { value: 'biweekly',  icon: '🗓️', label: 'Каждые 2 нед.' },
  { value: 'monthly',   icon: '📆', label: 'Каждый месяц' },
  { value: 'custom',    icon: '⚙️', label: 'Свой интервал' },
]

const selectRepeat = (v: typeof repeatMode.value) => {
  repeatMode.value = v
  if (v === 'none') hasEndDate.value = false
}

const daysLabel = (n: number) => {
  if (n === 1) return 'день'
  if (n >= 2 && n <= 4) return 'дня'
  return 'дней'
}

// ── Форматированная дата ──────────────────────────────────────
const formattedDateTime = computed(() => {
  if (!dateValue.value || !timeValue.value) return ''
  const d = new Date(`${dateValue.value}T${timeValue.value}`)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    weekday: 'long', day: 'numeric', month: 'long',
    hour: '2-digit', minute: '2-digit'
  })
})

// ── Валидация ─────────────────────────────────────────────────
const canSave = computed(() => {
  if (!dateValue.value || !timeValue.value) return false
  const d = new Date(`${dateValue.value}T${timeValue.value}`)
  if (isNaN(d.getTime()) || d <= new Date()) return false
  if (repeatMode.value === 'custom' && (customDays.value < 1 || customDays.value > 365)) return false
  return true
})

// ── Интервал в днях ───────────────────────────────────────────
const repeatIntervalDays = computed<number | undefined>(() => {
  switch (repeatMode.value) {
    case 'weekly':   return 7
    case 'biweekly': return 14
    case 'monthly':  return 30
    case 'custom':   return customDays.value
    default:         return undefined
  }
})

// ── Сохранение ───────────────────────────────────────────────
const handleSave = () => {
  if (!canSave.value) return
  const reminderTime = new Date(`${dateValue.value}T${timeValue.value}`)
  const data: ReminderData = {
    animeId:            props.anime.id,
    reminderTime,
    repeatWeekly:       repeatMode.value === 'weekly',
    repeatIntervalDays: repeatIntervalDays.value,
    endDate:            (hasEndDate.value && endDate.value) ? new Date(endDate.value) : undefined,
    comment:            comment.value || undefined,
  }
  emit('save', data)
  resetForm()
}

const handleClose = () => emit('close')

const handlePosterError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

const resetForm = () => {
  dateValue.value    = ''
  timeValue.value    = ''
  activePreset.value = null
  repeatMode.value   = 'none'
  customDays.value   = 3
  hasEndDate.value   = false
  endDate.value      = ''
  comment.value      = ''
}

watch(() => props.show, (v) => { if (!v) resetForm() })
</script>

<style scoped>
/* ── Оверлей ─────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

/* ── Модал ───────────────────────────────────────────────── */
.modal-content {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 24px 60px rgba(0,0,0,.5);
  display: flex;
  flex-direction: column;
}

/* ── Шапка ───────────────────────────────────────────────── */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent);
}

.modal-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: none;
  border: none;
  border-radius: 8px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: background .15s, color .15s;
}
.modal-close:hover { background: var(--surface-4); color: var(--text-primary); }

/* ── Тело ────────────────────────────────────────────────── */
.modal-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  flex: 1;
  overflow-y: auto;
}

/* ── Превью аниме ────────────────────────────────────────── */
.anime-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--surface-3);
  border-radius: 10px;
}

.preview-poster {
  width: 48px; height: 68px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--surface-4);
  display: flex; align-items: center; justify-content: center;
}

.preview-poster img { width: 100%; height: 100%; object-fit: cover; }
.poster-fallback { font-size: 22px; }

.preview-title {
  font-size: .875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.preview-meta {
  font-size: .8rem;
  color: var(--text-tertiary);
  margin: 0;
}

/* ── Секция ──────────────────────────────────────────────── */
.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .75rem;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: .06em;
}

.label-optional {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--text-tertiary);
  opacity: .7;
}

/* ── Пресеты ─────────────────────────────────────────────── */
.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preset-chip {
  height: 30px;
  padding: 0 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 99px;
  font-size: .8rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}

.preset-chip:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.preset-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* ── Дата/Время ──────────────────────────────────────────── */
.datetime-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.dt-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dt-label {
  font-size: .75rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.dt-input {
  height: 38px;
  padding: 0 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: .875rem;
  outline: none;
  transition: border-color .15s;
  width: 100%;
  cursor: pointer;
}

.dt-input:focus { border-color: var(--accent); }

/* colorscheme для нативных пикеров */
.dt-input { color-scheme: dark; }

/* ── Превью даты ─────────────────────────────────────────── */
.datetime-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .8rem;
  color: var(--accent);
  font-weight: 500;
  padding: 6px 10px;
  background: var(--accent-subtle);
  border-radius: 7px;
}

/* ── Повторение ──────────────────────────────────────────── */
.repeat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 6px;
}

.repeat-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  cursor: pointer;
  transition: all .15s;
}

.repeat-btn:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.repeat-btn.active {
  border-color: var(--accent);
  background: var(--accent-subtle);
  box-shadow: 0 0 0 1px var(--accent);
}

.repeat-icon { font-size: 16px; line-height: 1; }
.repeat-label { font-size: .75rem; font-weight: 600; color: var(--text-secondary); text-align: center; line-height: 1.2; }

.repeat-btn.active .repeat-label { color: var(--accent); }

/* ── Кастомный интервал ──────────────────────────────────── */
.custom-repeat {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--surface-3);
  border-radius: 9px;
}

.custom-repeat-text {
  font-size: .875rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.custom-repeat-stepper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stepper-btn {
  width: 28px; height: 28px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background .15s;
}
.stepper-btn:hover { background: var(--surface-5); }

.stepper-input {
  width: 50px;
  height: 28px;
  text-align: center;
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: .875rem;
  font-weight: 700;
  outline: none;
}

.stepper-input::-webkit-inner-spin-button,
.stepper-input::-webkit-outer-spin-button { -webkit-appearance: none; }

/* ── Дата окончания ──────────────────────────────────────── */
.repeat-end {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--surface-3);
  border-radius: 9px;
}

.repeat-end-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.toggle-check {
  width: 16px; height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
}

.toggle-label {
  font-size: .875rem;
  color: var(--text-secondary);
  user-select: none;
}

/* ── Заметка ─────────────────────────────────────────────── */
.comment-input {
  width: 100%;
  padding: 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: .875rem;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color .15s;
  box-sizing: border-box;
}

.comment-input:focus { border-color: var(--accent); }
.comment-input::placeholder { color: var(--text-tertiary); }

.char-count {
  font-size: .75rem;
  color: var(--text-tertiary);
  text-align: right;
}

/* ── Футер ───────────────────────────────────────────────── */
.modal-footer {
  display: flex;
  gap: 8px;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  padding: 0 1.25rem;
  border-radius: 9px;
  font-size: .875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .15s;
}

.btn-cancel {
  background: var(--surface-3);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}
.btn-cancel:hover { background: var(--surface-4); color: var(--text-primary); }

.btn-save {
  flex: 1;
  background: var(--accent);
  color: #fff;
}
.btn-save:hover:not(:disabled) { filter: brightness(1.1); }
.btn-save:disabled { opacity: .45; cursor: not-allowed; }

/* ── Анимации ────────────────────────────────────────────── */
.slide-down-enter-active { transition: all .2s ease; }
.slide-down-leave-active { transition: all .15s ease; }
.slide-down-enter-from   { opacity: 0; transform: translateY(-6px); }
.slide-down-leave-to     { opacity: 0; transform: translateY(-4px); }

.rm-anim-enter-active { transition: opacity .2s ease; }
.rm-anim-leave-active { transition: opacity .15s ease; }
.rm-anim-enter-from, .rm-anim-leave-to { opacity: 0; }

.rm-anim-enter-active .modal-content {
  transition: transform .25s cubic-bezier(.34,1.4,.64,1), opacity .2s ease;
}
.rm-anim-leave-active .modal-content {
  transition: transform .15s ease, opacity .15s ease;
}
.rm-anim-enter-from .modal-content  { transform: scale(.92) translateY(16px); opacity: 0; }
.rm-anim-leave-to .modal-content    { transform: scale(.96) translateY(6px);  opacity: 0; }

/* ── Адаптив ─────────────────────────────────────────────── */
@media (max-width: 480px) {
  .modal-content { max-height: 96vh; border-radius: 14px 14px 0 0; }
  .modal-overlay { align-items: flex-end; padding: 0; }
  .repeat-grid { grid-template-columns: repeat(3, 1fr); }
  .datetime-row { grid-template-columns: 1fr 1fr; }
  .modal-footer { flex-direction: column-reverse; }
  .btn { width: 100%; }
}
</style>
