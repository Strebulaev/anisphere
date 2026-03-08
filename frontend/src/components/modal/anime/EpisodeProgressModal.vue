<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="show" class="modal-backdrop" @click.self="$emit('close')">
        <div class="modal-box">

          <!-- Хедер -->
          <div class="modal-header">
            <span class="modal-icon">⚙️</span>
            <h2>Настройка прогресса</h2>
            <button class="close-btn" @click="$emit('close')">✕</button>
          </div>

          <!-- Аниме -->
          <div class="anime-label">
            🎬 {{ animeTitle }}
            <span class="ep-count">(всего {{ totalEpisodes }} серий)</span>
          </div>

          <!-- Варианты -->
          <div class="options">
            <label class="option" :class="{ active: mode === 'new' }">
              <input type="radio" v-model="mode" value="new" />
              <span>Я новичок (не смотрел)</span>
            </label>

            <label class="option" :class="{ active: mode === 'restart' }">
              <input type="radio" v-model="mode" value="restart" />
              <span>Я смотрел, но хочу начать заново</span>
            </label>

            <label class="option" :class="{ active: mode === 'continue' }">
              <input type="radio" v-model="mode" value="continue" />
              <div class="option-continue">
                <span>Я продолжаю с:</span>
                <div class="ep-picker">
                  <button class="ep-btn" @click="dec" :disabled="continueFrom <= 2">−</button>
                  <span class="ep-num">{{ continueFrom }}</span>
                  <button class="ep-btn" @click="inc" :disabled="continueFrom > totalEpisodes">+</button>
                  <span class="ep-label">серии</span>
                </div>
                <span class="already-watched" v-if="continueFrom > 1">
                  (уже просмотрено: {{ continueFrom - 1 }} {{ plural(continueFrom - 1) }})
                </span>
              </div>
            </label>
          </div>

          <!-- Ползунок для режима "continue" -->
          <div v-if="mode === 'continue'" class="slider-wrap">
            <input
              type="range"
              v-model.number="continueFrom"
              :min="2"
              :max="totalEpisodes"
              class="slider"
            />
            <div class="slider-labels">
              <span>2</span>
              <span>{{ totalEpisodes }}</span>
            </div>
          </div>

          <!-- Инфо -->
          <div class="info-row" v-if="mode !== 'new'">
            <span class="info-icon">📌</span>
            <span v-if="mode === 'continue'">
              Отметить серии 1–{{ continueFrom - 1 }} как просмотренные
            </span>
            <span v-else>
              Весь прогресс будет сброшен
            </span>
          </div>

          <!-- Действия -->
          <div class="modal-actions">
            <button class="btn-cancel" @click="$emit('close')">Отмена</button>
            <button class="btn-apply" :disabled="saving" @click="apply">
              <span v-if="saving" class="spinner" />
              {{ saving ? 'Сохраняем...' : 'Применить' }}
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  animeTitle: string
  totalEpisodes: number
  currentEpisode?: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'apply', payload: { mode: string; watchedUpTo?: number }): void
}>()

const mode        = ref<'new' | 'restart' | 'continue'>('continue')
const continueFrom = ref(props.currentEpisode ?? 2)
const saving      = ref(false)

// Сбрасываем при открытии
watch(() => props.show, (v) => {
  if (v) {
    mode.value = props.currentEpisode && props.currentEpisode > 1 ? 'continue' : 'new'
    continueFrom.value = props.currentEpisode ?? 2
    saving.value = false
  }
})

const dec = () => { if (continueFrom.value > 2) continueFrom.value-- }
const inc = () => { if (continueFrom.value <= props.totalEpisodes) continueFrom.value++ }

const plural = (n: number) => {
  if (n % 10 === 1 && n % 100 !== 11) return 'серия'
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'серии'
  return 'серий'
}

const apply = async () => {
  saving.value = true
  if (mode.value === 'new') {
    emit('apply', { mode: 'new' })
  } else if (mode.value === 'restart') {
    emit('apply', { mode: 'restart' })
  } else {
    emit('apply', { mode: 'continue', watchedUpTo: continueFrom.value - 1 })
  }
  saving.value = false
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.modal-box {
  background: #1a1a2e;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 2rem;
  width: 100%;
  max-width: 480px;
  color: #fff;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.modal-icon { font-size: 1.5rem; }

.modal-header h2 {
  flex: 1;
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 6px;
  transition: color .2s;
}
.close-btn:hover { color: #fff; }

.anime-label {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
}
.ep-count {
  font-weight: 400;
  font-size: 0.85rem;
  color: #9ca3af;
  margin-left: 0.4rem;
}

/* Варианты */
.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.07);
  cursor: pointer;
  background: rgba(255,255,255,0.03);
  transition: all .2s;
}
.option:hover { background: rgba(255,255,255,0.07); }
.option.active {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.4);
}

.option input[type="radio"] {
  width: 18px;
  height: 18px;
  margin-top: 1px;
  accent-color: #3b82f6;
  flex-shrink: 0;
  cursor: pointer;
}

.option span,
.option-continue {
  font-size: 0.95rem;
  color: #e2e8f0;
}

.option-continue {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ep-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ep-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.07);
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .15s;
}
.ep-btn:hover:not(:disabled) { background: rgba(59,130,246,0.3); }
.ep-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.ep-num {
  font-size: 1.1rem;
  font-weight: 700;
  color: #3b82f6;
  min-width: 2rem;
  text-align: center;
}
.ep-label { font-size: 0.85rem; color: #9ca3af; }

.already-watched {
  font-size: 0.8rem;
  color: #6b7280;
}

/* Ползунок */
.slider-wrap {
  padding: 0 0.25rem;
}

.slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

/* Инфо */
.info-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.875rem;
  color: #9ca3af;
  background: rgba(255,255,255,0.04);
  border-radius: 10px;
  padding: 0.75rem 1rem;
}
.info-icon { font-size: 1rem; flex-shrink: 0; }

/* Кнопки */
.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn-cancel, .btn-apply {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-cancel {
  background: rgba(255,255,255,0.07);
  color: #9ca3af;
}
.btn-cancel:hover { background: rgba(255,255,255,0.12); color: #fff; }

.btn-apply {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: #fff;
}
.btn-apply:hover:not(:disabled) {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(59,130,246,0.35);
}
.btn-apply:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Анимация */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .modal-box {
  animation: slide-up 0.25s ease;
}
@keyframes slide-up {
  from { transform: translateY(24px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
</style>
