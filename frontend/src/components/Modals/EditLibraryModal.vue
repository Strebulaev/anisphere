<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="$emit('close')">
      <div class="modal-box">

        <!-- Шапка -->
        <div class="modal-header">
          <div class="modal-title-row">
            <div class="modal-anime-info">
              <h3 class="modal-title">{{ item.anime_title_ru || item.anime_title_en }}</h3>
              <p class="modal-subtitle">Редактировать запись</p>
            </div>
          </div>
          <button class="modal-close" @click="$emit('close')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Тело -->
        <div class="modal-body">

          <!-- Статус -->
          <div class="field-group">
            <label class="field-label">Статус</label>
            <div class="status-grid">
              <button
                v-for="s in statusOptions"
                :key="s.key"
                class="status-opt"
                :class="{ selected: form.status === s.key }"
                @click="form.status = s.key"
              >
                <span class="s-icon">{{ s.icon }}</span>
                <span class="s-label">{{ s.label }}</span>
              </button>
            </div>
          </div>

          <!-- Прогресс (для started / on_hold) -->
          <div v-if="showEpisodeField" class="field-group">
            <label class="field-label">
              Текущая серия
              <span class="field-hint">из {{ item.anime_episodes_count || '?' }}</span>
            </label>
            <div class="episode-row">
              <button class="ep-btn" @click="form.current_episode = Math.max(0, form.current_episode - 1)">−</button>
              <input
                type="number"
                class="ep-input"
                v-model.number="form.current_episode"
                :min="0"
                :max="item.anime_episodes_count || 9999"
              />
              <button class="ep-btn" @click="form.current_episode = Math.min(form.current_episode + 1, item.anime_episodes_count || 9999)">+</button>
            </div>
          </div>

          <!-- Оценка -->
          <div class="field-group">
            <label class="field-label">Оценка</label>
            <div class="rating-stars">
              <button
                v-for="n in 10"
                :key="n"
                class="star-btn"
                :class="{ filled: n <= (hoverRating || form.rating || 0) }"
                @mouseenter="hoverRating = n"
                @mouseleave="hoverRating = 0"
                @click="form.rating = form.rating === n ? null : n"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" :fill="n <= (hoverRating || form.rating || 0) ? 'var(--warning)' : 'none'" stroke="var(--warning)" stroke-width="1.5">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
              </button>
              <span v-if="form.rating" class="rating-display">{{ form.rating }}/10</span>
              <button v-if="form.rating" class="clear-rating" @click="form.rating = null">✕</button>
            </div>
          </div>

          <!-- Избранное -->
          <div class="field-group">
            <label class="toggle-row">
              <span class="toggle-label">
                <span>⭐</span> В избранном
              </span>
              <div class="toggle-switch" :class="{ on: form.is_favorite }" @click="form.is_favorite = !form.is_favorite">
                <div class="toggle-thumb"></div>
              </div>
            </label>
          </div>

          <!-- Заметка -->
          <div class="field-group">
            <label class="field-label">Заметка</label>
            <textarea
              class="notes-input"
              v-model="form.notes"
              placeholder="Ваши мысли об аниме..."
              rows="3"
            ></textarea>
          </div>

        </div>

        <!-- Футер -->
        <div class="modal-footer">
          <button class="btn-cancel" @click="$emit('close')">Отмена</button>
          <button class="btn-save" :disabled="saving" @click="save">
            <svg v-if="saving" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ saving ? 'Сохраняем...' : 'Сохранить' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { libraryApi, type LibraryItem, type LibraryStatus } from '@/api/library'

const props = defineProps<{ item: LibraryItem }>()
const emit  = defineEmits<{ close: []; saved: [] }>()

const saving      = ref(false)
const hoverRating = ref(0)

const form = reactive({
  status:          props.item.status as LibraryStatus,
  current_episode: props.item.current_episode,
  rating:          props.item.rating as number | null,
  notes:           props.item.notes,
  is_favorite:     props.item.is_favorite,
})

const statusOptions = [
  { key: 'started'   as LibraryStatus, icon: '▶️', label: 'В процессе'    },
  { key: 'completed' as LibraryStatus, icon: '✅', label: 'Просмотрено'   },
  { key: 'planned'   as LibraryStatus, icon: '📅', label: 'Запланировано' },
  { key: 'on_hold'   as LibraryStatus, icon: '⏸️', label: 'Отложено'      },
  { key: 'dropped'   as LibraryStatus, icon: '❌', label: 'Брошено'       },
]

const showEpisodeField = computed(() =>
  form.status === 'started' || form.status === 'on_hold'
)

const save = async () => {
  saving.value = true
  try {
    await libraryApi.updateLibraryItem(props.item.id, {
      status:          form.status,
      current_episode: form.current_episode,
      episodes_watched:form.current_episode,
      rating:          form.rating,
      notes:           form.notes,
      is_favorite:     form.is_favorite,
    })
    emit('saved')
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0,0,0,0.65);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  animation: fade-in 0.15s var(--ease-out);
}

@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }

.modal-box {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  animation: slide-up 0.2s var(--ease-out);
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(16px) scale(0.97); }
  to   { opacity: 1; transform: none; }
}

/* ── Шапка ───────────────────────────────────────────────────  */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
  gap: var(--space-3);
}

.modal-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.modal-subtitle { font-size: var(--text-xs); color: var(--text-tertiary); margin: 3px 0 0 0; }

.modal-close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--surface-4);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-base);
}

.modal-close:hover { background: var(--surface-5); color: var(--text-primary); }

/* ── Тело ────────────────────────────────────────────────────  */
.modal-body {
  padding: var(--space-5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.field-group { display: flex; flex-direction: column; gap: var(--space-2); }

.field-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.field-hint { font-weight: 400; color: var(--text-tertiary); }

/* Статус */
.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.status-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--space-3) var(--space-2);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-base);
}

.status-opt:hover { background: var(--surface-4); border-color: var(--border-default); }
.status-opt.selected { background: var(--accent-subtle); border-color: var(--accent); }

.s-icon  { font-size: 20px; line-height: 1; }
.s-label { font-size: 11px; font-weight: 500; color: var(--text-secondary); text-align: center; }
.status-opt.selected .s-label { color: var(--accent); }

/* Эпизод */
.episode-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.ep-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base);
}

.ep-btn:hover { background: var(--surface-4); color: var(--text-primary); }

.ep-input {
  flex: 1;
  height: 36px;
  text-align: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-base);
  font-weight: 600;
  outline: none;
}

.ep-input:focus { border-color: var(--accent); }

/* Рейтинг */
.rating-stars {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.star-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  transition: transform var(--duration-base);
  line-height: 0;
}

.star-btn:hover { transform: scale(1.2); }

.rating-display {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--warning);
  margin-left: var(--space-2);
}

.clear-rating {
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
}

.clear-rating:hover { color: var(--danger); }

/* Тоггл */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.toggle-switch {
  width: 42px;
  height: 24px;
  border-radius: var(--radius-full);
  background: var(--surface-5);
  position: relative;
  cursor: pointer;
  transition: background var(--duration-base);
}

.toggle-switch.on { background: var(--accent); }

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: white;
  transition: transform var(--duration-base);
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.toggle-switch.on .toggle-thumb { transform: translateX(18px); }

/* Заметка */
.notes-input {
  width: 100%;
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: var(--text-sm);
  line-height: 1.5;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

.notes-input:focus { border-color: var(--accent); }
.notes-input::placeholder { color: var(--text-tertiary); }

/* ── Футер ───────────────────────────────────────────────────  */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-subtle);
}

.btn-cancel {
  height: 38px;
  padding: 0 var(--space-5);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}

.btn-cancel:hover { background: var(--surface-5); color: var(--text-primary); }

.btn-save {
  height: 38px;
  padding: 0 var(--space-6);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base);
}

.btn-save:hover:not(:disabled) { background: var(--accent-hover); }
.btn-save:disabled { opacity: 0.6; cursor: not-allowed; }

@keyframes spin-anim { to { transform: rotate(360deg); } }
.spin { animation: spin-anim 0.8s linear infinite; }
</style>
