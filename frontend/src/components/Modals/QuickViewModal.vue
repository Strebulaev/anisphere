<template>
  <!-- Используем teleport чтобы модалка рендерилась прямо в body, вне любых stacking context -->
  <Teleport to="body">
    <Transition name="qv-modal">
      <div
        v-if="show"
        class="qv-overlay"
        @click.self="handleClose"
        @keydown.esc="handleClose"
      >
        <div class="qv-modal" role="dialog" aria-modal="true">
          <!-- Кнопка закрытия -->
          <button @click="handleClose" class="qv-close" type="button" aria-label="Закрыть">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>

          <div class="qv-body">
            <!-- Постер -->
            <div class="qv-poster-wrap">
              <img
                v-if="posterSrc && !posterFailed"
                :src="posterSrc"
                :alt="anime.title_ru || anime.title_en || ''"
                class="qv-poster-img"
                @error="posterFailed = true"
                @load="posterLoaded = true"
              />
              <!-- skeleton пока грузится -->
              <div v-if="!posterLoaded && posterSrc && !posterFailed" class="qv-poster-skeleton" />
              <div v-if="!posterSrc || posterFailed" class="qv-poster-placeholder">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M12 2v20M2 12h20"/>
                </svg>
              </div>
            </div>

            <!-- Информация -->
            <div class="qv-info">
              <h2 class="qv-title">{{ anime.title_ru || anime.title_en }}</h2>
              <p
                v-if="anime.title_ru && anime.title_en && anime.title_ru !== anime.title_en"
                class="qv-title-en"
              >{{ anime.title_en }}</p>

              <div class="qv-meta">
                <span v-if="anime.year" class="qv-meta-item">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  {{ anime.year }}
                </span>
                <span v-if="anime.episodes" class="qv-meta-item">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/>
                  </svg>
                  {{ anime.episodes }} эп.
                </span>
                <span v-if="anime.status" class="qv-meta-status" :class="statusClass">
                  {{ statusLabel }}
                </span>
              </div>

              <div v-if="anime.genres?.length" class="qv-genres">
                <span
                  v-for="(genre, idx) in anime.genres.slice(0, 4)"
                  :key="typeof genre === 'string' ? idx : (genre as any).id"
                  class="qv-genre-tag"
                >
                  {{ typeof genre === 'string' ? genre : (genre as any).name }}
                </span>
                <span v-if="anime.genres.length > 4" class="qv-genre-more">+{{ anime.genres.length - 4 }}</span>
              </div>

              <div class="qv-rating">
                <div class="qv-stars">
                  <svg
                    v-for="i in 5"
                    :key="i"
                    width="16" height="16" viewBox="0 0 24 24"
                    :fill="i <= Math.round(((anime as any).score || 0) / 2) ? 'currentColor' : 'none'"
                    stroke="currentColor" stroke-width="2"
                  >
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </div>
                <span class="qv-score">{{ (anime as any).score ? ((anime as any).score as number).toFixed(1) : 'N/A' }}</span>
              </div>

              <p class="qv-desc">
                {{ truncatedDescription }}
                <button
                  v-if="anime.description && anime.description.length > 200"
                  @click="showFullDesc = !showFullDesc"
                  class="qv-show-more"
                  type="button"
                >{{ showFullDesc ? 'Свернуть' : 'Подробнее' }}</button>
              </p>

              <div class="qv-actions">
                <button @click="handleDetail" class="qv-btn qv-btn-primary" type="button">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  Подробнее
                </button>
                <button @click="handleAddToLibrary" class="qv-btn qv-btn-secondary" type="button">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
                  </svg>
                  В коллекцию
                </button>
                <button
                  @click="handleToggleFavorite"
                  :class="['qv-btn', 'qv-btn-fav', { active: isFavorite }]"
                  type="button"
                  :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24"
                    :fill="isFavorite ? 'currentColor' : 'none'"
                    stroke="currentColor" stroke-width="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { Anime } from '@/types'
import { getMediaUrl } from '@/api/client'

interface Props {
  show: boolean
  anime: Anime
  isFavorite?: boolean
}

const props = withDefaults(defineProps<Props>(), { isFavorite: false })
const emit = defineEmits<{
  close: []
  addToLibrary: [anime: Anime]
  toggleFavorite: [anime: Anime]
}>()

const router = useRouter()
const showFullDesc  = ref(false)
const posterFailed  = ref(false)
const posterLoaded  = ref(false)

// Сбрасываем состояние постера при смене аниме
watch(() => props.anime, () => {
  posterFailed.value = false
  posterLoaded.value = false
}, { deep: false })

// Подбираем лучший URL постера: сначала poster_image_url, потом poster_url
const posterSrc = computed<string | null>(() => {
  const a = props.anime as any
  const raw = a.poster_image_url || a.poster_url || null
  if (!raw) return null
  return getMediaUrl(raw) || null
})

const statusClass = computed(() => {
  const s = props.anime.status?.toLowerCase()
  if (s === 'ongoing') return 'status-ongoing'
  if (s === 'finished' || s === 'completed') return 'status-finished'
  if (s === 'announced') return 'status-announced'
  return ''
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    ongoing: 'Онгоинг', finished: 'Завершён',
    completed: 'Завершён', announced: 'Анонсирован', released: 'Вышедший',
  }
  return props.anime.status ? (map[props.anime.status.toLowerCase()] ?? props.anime.status) : ''
})

const truncatedDescription = computed(() => {
  if (!props.anime.description) return 'Описание отсутствует'
  return showFullDesc.value ? props.anime.description : props.anime.description.slice(0, 200)
})

const handleDetail        = () => { router.push(`/anime/${props.anime.id}`); handleClose() }
const handleAddToLibrary  = () => emit('addToLibrary', props.anime)
const handleToggleFavorite= () => emit('toggleFavorite', props.anime)
const handleClose         = () => emit('close')
</script>

<style scoped>
/* ─── Overlay ─────────────────────────────────────────────── */
.qv-overlay {
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
  /* Важно: overlay сам не имеет transform, чтобы не создавать stacking context */
}

/* ─── Modal box ───────────────────────────────────────────── */
.qv-modal {
  background: var(--surface-2, var(--color-background-surface));
  border-radius: 1.25rem;
  max-width: 720px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255,255,255,0.06);
  position: relative;
  /* scrollbar */
  scrollbar-width: thin;
  scrollbar-color: var(--border-default) transparent;
}

.qv-modal::-webkit-scrollbar { width: 6px; }
.qv-modal::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 3px; }

/* ─── Анимация — только на .qv-modal ──────────────────────── */
.qv-modal-enter-active,
.qv-modal-leave-active {
  transition: opacity 0.25s ease;
}
.qv-modal-enter-active .qv-modal,
.qv-modal-leave-active .qv-modal {
  transition: transform 0.25s cubic-bezier(0.34, 1.4, 0.64, 1), opacity 0.25s ease;
}
.qv-modal-enter-from,
.qv-modal-leave-to {
  opacity: 0;
}
.qv-modal-enter-from .qv-modal {
  transform: scale(0.92) translateY(16px);
  opacity: 0;
}
.qv-modal-leave-to .qv-modal {
  transform: scale(0.96) translateY(8px);
  opacity: 0;
}

/* ─── Close button ────────────────────────────────────────── */
.qv-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 2;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
  border: none;
  border-radius: 50%;
  color: rgba(255,255,255,0.85);
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}
.qv-close:hover {
  background: rgba(255,255,255,0.2);
  transform: rotate(90deg) scale(1.1);
}

/* ─── Body layout ─────────────────────────────────────────── */
.qv-body {
  display: flex;
  gap: 0;
}

/* ─── Постер ──────────────────────────────────────────────── */
.qv-poster-wrap {
  flex-shrink: 0;
  width: 220px;
  min-height: 310px;
  position: relative;
  background: var(--surface-4);
  border-radius: 1.25rem 0 0 1.25rem;
  overflow: hidden;
}

.qv-poster-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.qv-poster-skeleton {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s infinite;
}

@keyframes skeleton-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.qv-poster-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* ─── Info section ────────────────────────────────────────── */
.qv-info {
  flex: 1;
  min-width: 0;
  padding: 2rem 2.5rem 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.qv-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
  padding-right: 2rem; /* чтобы не перекрывало кнопку закрытия */
}

.qv-title-en {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
}

/* ─── Meta ────────────────────────────────────────────────── */
.qv-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.qv-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.qv-meta-status {
  padding: 0.2rem 0.6rem;
  border-radius: 0.375rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.status-ongoing  { background: rgba(34,197,94,.15);  color: #22c55e; }
.status-finished { background: rgba(59,130,246,.15);  color: #60a5fa; }
.status-announced{ background: rgba(251,191,36,.15); color: #fbbf24; }

/* ─── Genres ──────────────────────────────────────────────── */
.qv-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.qv-genre-tag {
  padding: 0.3rem 0.65rem;
  background: var(--accent-subtle, rgba(124,92,252,0.12));
  color: var(--accent);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.qv-genre-more {
  padding: 0.3rem 0.65rem;
  background: var(--surface-4);
  color: var(--text-tertiary);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
}

/* ─── Rating ──────────────────────────────────────────────── */
.qv-rating {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.qv-stars {
  display: flex;
  gap: 2px;
  color: var(--warning, #f59e0b);
}

.qv-score {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--warning, #f59e0b);
}

/* ─── Description ─────────────────────────────────────────── */
.qv-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 0;
}

.qv-show-more {
  background: none;
  border: none;
  color: var(--accent);
  font-weight: 600;
  cursor: pointer;
  padding: 0 0 0 4px;
  font-size: inherit;
  transition: color 0.15s;
}
.qv-show-more:hover { text-decoration: underline; }

/* ─── Actions ─────────────────────────────────────────────── */
.qv-actions {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 0.5rem;
}

.qv-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.65rem 1.15rem;
  border-radius: 0.6rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  border: 1px solid transparent;
  white-space: nowrap;
}

.qv-btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.qv-btn-primary:hover {
  filter: brightness(1.12);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124,92,252,0.4);
}

.qv-btn-secondary {
  background: transparent;
  border-color: var(--border-default);
  color: var(--text-primary);
}
.qv-btn-secondary:hover {
  background: var(--surface-4);
  border-color: var(--accent);
  color: var(--accent);
}

.qv-btn-fav {
  width: 42px;
  padding: 0;
  background: var(--surface-4);
  border-color: var(--border-default);
  color: var(--text-tertiary);
}
.qv-btn-fav:hover {
  border-color: #f43f5e;
  color: #f43f5e;
  transform: scale(1.08);
}
.qv-btn-fav.active {
  background: rgba(244,63,94,0.15);
  border-color: #f43f5e;
  color: #f43f5e;
}

/* ─── Mobile ──────────────────────────────────────────────── */
@media (max-width: 640px) {
  .qv-body { flex-direction: column; }

  .qv-poster-wrap {
    width: 100%;
    min-height: 0;
    aspect-ratio: 16/9;
    border-radius: 1.25rem 1.25rem 0 0;
  }

  .qv-poster-img { object-position: center top; }

  .qv-info {
    padding: 1.25rem 1.25rem 1.5rem;
  }

  .qv-title { font-size: 1.25rem; }

  .qv-actions { flex-direction: column; }
  .qv-btn { width: 100%; }
  .qv-btn-fav { width: 100%; }
}
</style>
