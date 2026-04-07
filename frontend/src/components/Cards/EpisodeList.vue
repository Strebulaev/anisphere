<template>
  <div class="episode-list">

    <!-- Прогресс-бар аниме -->
    <div class="anime-progress-bar" v-if="totalEpisodes > 1">
      <div class="apb-header">
        <span class="apb-label">Прогресс</span>
        <span class="apb-stats">
          {{ watchedCount }}/{{ totalEpisodes }}
          <span class="apb-pct">{{ progressPercent }}%</span>
        </span>
      </div>
      <div class="apb-track">
        <div class="apb-fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <div class="apb-actions" v-if="progressPercent < 100">
        <button class="apb-btn continue-btn" v-if="nextEpisode" @click="$emit('select-episode', nextEpisode)">
          <SakuraIcon name="play" /> Продолжить с {{ nextEpisode }}
        </button>
        <button class="apb-btn sync-btn" @click="$emit('open-sync')"> <SakuraIcon name="settings" /> </button>
      </div>
      <div class="apb-completed" v-else>
        <span class="completed-badge"><SakuraIcon name="check" /> Просмотрено</span>
        <button class="apb-btn sync-btn" @click="$emit('open-sync')">Пересмотреть</button>
      </div>
    </div>

    <!-- Список серий -->
    <div class="episodes-scroll">
      <div
        v-for="num in episodeNumbers"
        :key="num"
        class="ep-row"
        :class="[
          getEp(num).status,
          { 'is-current': num === currentEpisode }
        ]"
      >
        <!-- Номер + иконка статуса -->
        <div class="ep-left">
          <div class="ep-status-wrap">
            <span v-if="getEp(num).status === 'watched'" class="ep-status-icon watched"> <SakuraIcon name="heavy-check" /> </span>
            <span v-else-if="getEp(num).status === 'skipped'" class="ep-status-icon skipped">⏭</span>
            <span v-else-if="getEp(num).status === 'in_progress'" class="ep-status-icon in-progress"> <SakuraIcon name="play" /> </span>
            <span v-else class="ep-num-plain">{{ num }}</span>
          </div>
        </div>

        <!-- Центр: название + прогресс серии -->
        <div class="ep-center" @click="$emit('select-episode', num)" style="cursor:pointer">
          <div class="ep-title-row">
            <span class="ep-num-label" v-if="getEp(num).status !== 'not_started'">{{ num }}</span>
            <span class="ep-title">{{ (episodeTitles && episodeTitles[num]) || `Серия ${num}` }}</span>
          </div>

          <!-- Прогресс-бар серии (in_progress) -->
          <div v-if="getEp(num).status === 'in_progress' && getEp(num).progress_percent > 0" class="ep-bar-wrap">
            <div class="ep-bar-track">
              <div class="ep-bar-fill" :style="{ width: getEp(num).progress_percent + '%' }" />
            </div>
            <span class="ep-bar-pct">{{ getEp(num).progress_percent }}%</span>
          </div>

          <!-- Метки -->
          <span v-if="getEp(num).status === 'skipped'" class="ep-tag skipped-tag">Пропущено</span>
          <span v-if="num === currentEpisode" class="ep-tag current-tag">Сейчас</span>
        </div>

        <!-- Кнопки -->
        <div class="ep-actions">
          <button
            v-if="getEp(num).status === 'watched'"
            class="ep-btn unmark"
            @click.stop="$emit('undo-mark', num)"
            title="Снять отметку"
          >↩</button>
          <button
            v-else
            class="ep-btn mark"
            @click.stop="$emit('mark-watched', num)"
            title="Отметить просмотренной"
          >✓</button>
          <button
            v-if="getEp(num).status !== 'watched' && getEp(num).status !== 'skipped'"
            class="ep-btn skip"
            @click.stop="$emit('skip-episode', num)"
            title="Пропустить"
          >⏭</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EpisodeProgressItem } from '@/composables/useEpisodeProgress'

const props = defineProps<{
  totalEpisodes: number
  currentEpisode: number
  episodes: Map<number, EpisodeProgressItem>
  watchedCount: number
  progressPercent: number
  nextEpisode: number | null
  episodeTitles?: Record<number, string>
}>()

defineEmits<{
  (e: 'select-episode', num: number): void
  (e: 'mark-watched', num: number): void
  (e: 'undo-mark', num: number): void
  (e: 'skip-episode', num: number): void
  (e: 'open-sync'): void
}>()

const episodeNumbers = computed(() =>
  Array.from({ length: props.totalEpisodes }, (_, i) => i + 1)
)

const getEp = (num: number): EpisodeProgressItem =>
  props.episodes.get(num) ?? {
    episode_number: num,
    status: 'not_started',
    last_position: 0,
    duration: null,
    progress_percent: 0,
    is_manually_marked: false,
    watched_at: null,
  }
</script>

<style scoped>
.episode-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Прогресс аниме ─────────────────────────────── */
.anime-progress-bar {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
  padding: 0.875rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.apb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.apb-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #6b7280;
  font-weight: 700;
}

.apb-stats {
  font-size: 0.82rem;
  color: #9ca3af;
}

.apb-pct {
  margin-left: 0.35rem;
  font-weight: 700;
  color: #3b82f6;
}

.apb-track {
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  overflow: hidden;
}

.apb-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.apb-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.apb-completed {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.completed-badge {
  font-size: 0.8rem;
  color: #22c55e;
  font-weight: 600;
}

.apb-btn {
  padding: 0.375rem 0.75rem;
  border-radius: 7px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .2s;
  white-space: nowrap;
}

.continue-btn {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: #fff;
  flex: 1;
}
.continue-btn:hover { opacity: 0.88; }

.sync-btn {
  background: rgba(255,255,255,0.07);
  color: #9ca3af;
  border: 1px solid rgba(255,255,255,0.1);
}
.sync-btn:hover { background: rgba(255,255,255,0.12); color: #fff; }

/* ── Скролл-список ──────────────────────────────── */
.episodes-scroll {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 480px;
  overflow-y: auto;
  padding-right: 2px;
}

.episodes-scroll::-webkit-scrollbar { width: 3px; }
.episodes-scroll::-webkit-scrollbar-track { background: transparent; }
.episodes-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

/* Строка серии */
.ep-row {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem 0.6rem;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: background .12s;
}

.ep-row:hover { background: rgba(255,255,255,0.04); }

.ep-row.is-current {
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.25);
}

.ep-row.watched { opacity: 0.6; }
.ep-row.skipped { opacity: 0.45; }

/* Левая часть — статус */
.ep-left {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ep-status-wrap {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ep-status-icon {
  font-size: 0.75rem;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.ep-status-icon.watched {
  background: rgba(34,197,94,0.18);
  color: #22c55e;
}

.ep-status-icon.skipped {
  background: rgba(245,158,11,0.15);
  color: #f59e0b;
}

.ep-status-icon.in-progress {
  background: rgba(59,130,246,0.18);
  color: #60a5fa;
}

.ep-num-plain {
  font-size: 0.82rem;
  font-weight: 700;
  color: #6b7280;
  min-width: 22px;
  text-align: center;
}

/* Центральная часть */
.ep-center {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.ep-title-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}

.ep-num-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: #6b7280;
  flex-shrink: 0;
}

.ep-title {
  font-size: 0.85rem;
  color: #d1d5db;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ep-row.is-current .ep-title { color: #fff; font-weight: 600; }

/* Прогресс-бар серии */
.ep-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.ep-bar-track {
  flex: 1;
  height: 3px;
  background: rgba(255,255,255,0.08);
  border-radius: 2px;
  overflow: hidden;
}

.ep-bar-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width .3s;
}

.ep-bar-pct {
  font-size: 0.65rem;
  color: #6b7280;
  flex-shrink: 0;
  min-width: 26px;
  text-align: right;
}

/* Теги */
.ep-tag {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.05rem 0.35rem;
  border-radius: 3px;
  line-height: 1.4;
}

.skipped-tag {
  background: rgba(245,158,11,0.12);
  color: #f59e0b;
}

.current-tag {
  background: rgba(59,130,246,0.2);
  color: #60a5fa;
}

/* Кнопки действий */
.ep-actions {
  display: flex;
  gap: 0.25rem;
  align-items: center;
  flex-shrink: 0;
}

.ep-btn {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: #6b7280;
  font-size: 0.72rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .12s;
  flex-shrink: 0;
}

.ep-btn:hover { color: #fff; border-color: rgba(255,255,255,0.2); }

.ep-btn.mark:hover  { background: rgba(34,197,94,0.2); color: #22c55e; border-color: rgba(34,197,94,0.35); }
.ep-btn.unmark:hover { background: rgba(107,114,128,0.2); color: #d1d5db; }
.ep-btn.skip:hover  { background: rgba(245,158,11,0.18); color: #f59e0b; border-color: rgba(245,158,11,0.35); }
</style>
