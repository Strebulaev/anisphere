<template>
  <div
    class="anime-poster-card"
    :class="[variantClass, { 'has-overlay': showOverlay }]"
    @click="handleClick"
  >
    <!-- Постер -->
    <div class="poster-wrap">
      <!-- skeleton пока грузится -->
      <div v-if="isLoading" class="poster-skeleton" />

      <img
        v-if="posterUrl"
        :src="posterUrl"
        :alt="title"
        class="poster-img"
        loading="lazy"
        @error="onPosterError"
        @load="isLoading = false"
      />
      <div v-if="!posterUrl" class="poster-placeholder">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <path d="M12 2v20M2 12h20"/>
        </svg>
      </div>

      <!-- Градиент снизу (для текста на постере) -->
      <div v-if="showGradient" class="poster-gradient" />

      <!-- Hover оверлей — pointer-events всегда auto, скрываем только через opacity -->
      <div v-if="showOverlay" class="hover-overlay">
        <!-- Основная кнопка play -->
        <button
          v-if="overlayConfig.play"
          class="play-btn"
          @click.stop="onPlayClick"
          :title="playLabel"
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>

        <!-- Дополнительные кнопки -->
        <div v-if="overlayConfig.more || overlayConfig.favorite" class="overlay-actions">
          <button
            v-if="overlayConfig.more"
            class="action-btn-overlay"
            @click.stop="onMoreClick"
            title="В коллекцию"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
          <button
            v-if="overlayConfig.favorite"
            class="action-btn-overlay fav-btn"
            :class="{ active: isFavorite }"
            @click.stop="onFavoriteClick"
            :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Бейджи -->
      <div v-if="showStatus && status" class="badge badge-status" :class="`status-${status}`">
        {{ statusLabel }}
      </div>
      <div v-if="showScore && score" class="badge badge-score">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        {{ formattedScore }}
      </div>
      <div v-if="rank" class="badge badge-rank" :class="{ 'rank-top': rank <= 3 }">
        #{{ rank }}
      </div>
      <div v-if="isFranchiseMember" class="badge badge-franchise" title="Часть франшизы">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="2" width="8" height="8"/><rect x="14" y="2" width="8" height="8"/>
          <rect x="2" y="14" width="8" height="8"/><rect x="14" y="14" width="8" height="8"/>
        </svg>
      </div>

      <!-- Прогресс просмотра -->
      <div v-if="showProgress && progressPercent > 0" class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </div>

      <!-- Избранное -->
      <button
        v-if="showFavoriteBtn"
        class="favorite-toggle"
        :class="{ active: isFavorite }"
        @click.stop="onFavoriteClick"
        :title="isFavorite ? 'Убрать из избранного' : 'В избранное'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      </button>
    </div>

    <!-- Информация -->
    <div class="card-info">
      <h3 class="card-title" :title="title">{{ displayTitle }}</h3>
      <div v-if="showMeta" class="card-meta">
        <span v-if="year">{{ year }}</span>
        <span v-if="year && type">·</span>
        <span v-if="type">{{ typeLabel }}</span>
        <span v-if="type && episodes">·</span>
        <span v-if="episodes">{{ episodes }} эп.</span>
      </div>
      <div v-if="showProgress && currentEpisode" class="card-progress">
        <span>{{ currentEpisode }}/{{ episodes || '?' }}</span>
        <span v-if="progressPercent" class="progress-pct">{{ progressPercent }}%</span>
      </div>
      <div v-if="showGenres && genres?.length" class="card-genres">
        <span v-for="g in displayedGenres" :key="g" class="genre-tag">{{ g }}</span>
        <span v-if="remainingGenres > 0" class="genre-more">+{{ remainingGenres }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getMediaUrl } from '@/api/client'

interface OverlayConfig {
  play?: boolean
  more?: boolean
  favorite?: boolean
}

interface Props {
  id: number
  title: string
  titleEn?: string
  poster?: string | null
  year?: number | null
  type?: string
  episodes?: number | null
  currentEpisode?: number
  score?: number | null
  status?: string | null | undefined
  genres?: string[]
  progressPercent?: number
  rank?: number | null
  isFranchiseMember?: boolean
  franchiseId?: number | null
  isFavorite?: boolean
  variant?: 'default' | 'compact' | 'detailed'
  showOverlay?: boolean
  showGradient?: boolean
  showScore?: boolean
  showStatus?: boolean
  showProgress?: boolean
  showMeta?: boolean
  showGenres?: boolean
  showFavoriteBtn?: boolean
  maxGenres?: number
  overlayConfig?: OverlayConfig
  playLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  titleEn: '',
  poster: null,
  year: null,
  type: '',
  episodes: null,
  currentEpisode: 0,
  score: null,
  status: undefined,
  genres: () => [],
  progressPercent: 0,
  rank: null,
  isFranchiseMember: false,
  franchiseId: null,
  isFavorite: false,
  variant: 'default',
  showOverlay: true,
  showGradient: false,
  showScore: true,
  showStatus: true,
  showProgress: true,
  showMeta: true,
  showGenres: false,
  showFavoriteBtn: false,
  maxGenres: 2,
  overlayConfig: () => ({ play: true }),
  playLabel: 'Смотреть'
})

const emit = defineEmits<{
  click: [id: number]
  play: [id: number]
  more: [id: number]
  favorite: [toggle: boolean]
}>()

const posterFailed = ref(false)
const isLoading    = ref(true)

// Сбрасываем при смене постера
watch(() => props.poster, () => {
  posterFailed.value = false
  isLoading.value    = true
})

const posterUrl = computed(() => {
  if (posterFailed.value || !props.poster) return null
  return getMediaUrl(props.poster) || null
})

const displayTitle   = computed(() => props.title || props.titleEn || '—')
const formattedScore = computed(() => props.score ? props.score.toFixed(1) : '')

const typeLabel = computed(() => {
  const m: Record<string, string> = { tv:'TV', movie:'Фильм', ova:'OVA', ona:'ONA', special:'Спешл', music:'Музыка' }
  return props.type ? m[props.type.toLowerCase()] || props.type : ''
})

const statusLabel = computed(() => {
  const m: Record<string, string> = { ongoing:'Онгоинг', finished:'Завершено', announced:'Анонс', released:'Вышло' }
  return props.status ? m[props.status] || props.status : ''
})

const displayedGenres = computed(() => props.genres?.slice(0, props.maxGenres) ?? [])
const remainingGenres = computed(() => Math.max(0, (props.genres?.length ?? 0) - props.maxGenres))
const variantClass    = computed(() => `variant-${props.variant}`)

const handleClick    = () => emit('click', props.id)
const onPlayClick    = () => emit('play',  props.id)
const onMoreClick    = () => emit('more',  props.id)
const onFavoriteClick= () => emit('favorite', !props.isFavorite)
const onPosterError  = () => { posterFailed.value = true; isLoading.value = false }
</script>

<style scoped>
/* ═══ Базовые стили ════════════════════════════════════════ */
.anime-poster-card {
  flex: 0 0 180px;
  width: 180px;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: visible; /* overflow:visible чтобы тень была видна */
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}

.anime-poster-card:hover { transform: translateY(-4px); }

/* ═══ Постер ════════════════════════════════════════════════ */
.poster-wrap {
  position: relative;
  width: 100%;
  padding-bottom: 140%;
  background: var(--surface-4);
  border-radius: var(--radius-card);
  overflow: hidden;
}

/* Skeleton shimmer */
.poster-skeleton {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  z-index: 1;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.poster-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 2;
  transition: transform var(--duration-slow) var(--ease-out);
}

.anime-poster-card:hover .poster-img { transform: scale(1.05); }

.poster-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  z-index: 2;
}

.poster-gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(to top, rgba(8,8,9,.96) 0%, rgba(8,8,9,.5) 50%, transparent 100%);
  pointer-events: none;
  z-index: 3;
}

.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.18s ease-out;
  z-index: 4;
  pointer-events: auto; /* ВСЕГДА auto — нет мерцания */
}

.anime-poster-card:hover .hover-overlay { opacity: 1; }

/* Кнопка play */
.play-btn {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  border: none;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transform: scale(0.6);
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}

.anime-poster-card:hover .play-btn {
  transform: scale(1);
  box-shadow: 0 0 28px 4px rgba(124, 92, 252, 0.5);
}

.play-btn:hover {
  transform: scale(1.12) !important;
  background: var(--accent-hover, var(--accent));
  box-shadow: 0 0 38px 8px rgba(124, 92, 252, 0.65) !important;
}

.play-btn svg { margin-left: 3px; }

/* Дополнительные кнопки оверлея */
.overlay-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity 0.18s ease-out, transform 0.18s ease-out;
  z-index: 5;
}

.anime-poster-card:hover .overlay-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-btn-overlay {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 8, 9, 0.78);
  color: var(--text-primary);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.15s ease-out;
  border: none;
  backdrop-filter: blur(8px);
  transform: scale(0.7);
}

.anime-poster-card:hover .action-btn-overlay { transform: scale(1); }
.action-btn-overlay:hover { background: var(--accent) !important; transform: scale(1.1) !important; }

.action-btn-overlay.fav-btn.active { color: var(--danger); background: rgba(239,68,68,.85); }
.action-btn-overlay.fav-btn.active:hover { background: var(--danger) !important; }

/* ═══ Бейджи ════════════════════════════════════════════════ */
.badge {
  position: absolute;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  backdrop-filter: blur(6px);
  z-index: 5;
}

.badge-status { top: var(--space-2); left: var(--space-2); }
.badge-status.status-ongoing  { background: #22c55e; color: white; }
.badge-status.status-finished { background: var(--surface-5); color: var(--text-secondary); }
.badge-status.status-announced{ background: #a855f7; color: white; }
.badge-status.status-released { background: var(--accent); color: white; }

.badge-score {
  bottom: var(--space-2);
  left: var(--space-2);
  display: flex;
  align-items: center;
  gap: 3px;
  background: rgba(0,0,0,.85);
  color: var(--warning);
  padding: 3px 8px;
}

.badge-franchise {
  top: var(--space-2);
  right: var(--space-2);
  background: rgba(0,0,0,.75);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 5px;
}

.badge-rank {
  top: var(--space-2);
  left: var(--space-2);
  background: rgba(0,0,0,.85);
  color: var(--text-secondary);
}
.badge-rank.rank-top { background: var(--accent); color: white; }

/* ═══ Прогресс ════════════════════════════════════════════════ */
.progress-bar {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: rgba(0,0,0,.4);
  z-index: 5;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width .3s ease;
}

/* ═══ Избранное ════════════════════════════════════════════════ */
.favorite-toggle {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,.5);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--duration-base), color var(--duration-base);
  backdrop-filter: blur(4px);
  z-index: 6;
}
.anime-poster-card:hover .favorite-toggle { opacity: 1; }
.favorite-toggle.active { color: #f59e0b; opacity: 1; }
.favorite-toggle:hover  { background: rgba(0,0,0,.7); }

/* ═══ Информация ════════════════════════════════════════════════ */
.card-info {
  padding: var(--space-2) var(--space-1) 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.card-progress {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.progress-pct { color: var(--accent); font-weight: 600; }

.card-genres { display: flex; flex-wrap: wrap; gap: 3px; }

.genre-tag {
  font-size: 10px;
  color: var(--accent);
  background: var(--accent-subtle);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.genre-more { font-size: 10px; color: var(--text-tertiary); }

/* ═══ Варианты ════════════════════════════════════════════════ */
.variant-compact .card-info { padding-top: var(--space-1); }
.variant-detailed .poster-wrap { aspect-ratio: 3/4; }

/* ═══ Mobile ════════════════════════════════════════════════ */
@media (max-width: 767px) {
  .anime-poster-card { flex: 0 0 140px; width: 140px; }
  .favorite-toggle   { opacity: 1; }

  .hover-overlay {
    opacity: 1;
    background: rgba(0,0,0,.3);
  }

  .overlay-actions { opacity: 1; transform: translateY(0); }

  .play-btn { transform: scale(0.85); width: 52px; height: 52px; }
  .anime-poster-card:hover .play-btn { transform: scale(1); }
}
</style>
