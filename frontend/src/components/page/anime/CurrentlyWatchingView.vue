<template>
  <div class="cw">

    <!-- Заголовок -->
    <div class="cw-header">
      <div>
        <h2 class="cw-title">👁 Сейчас смотрят</h2>
        <p class="cw-subtitle">Аниме, которые активно смотрят прямо сейчас на сайте</p>
      </div>
      <button class="cw-refresh" @click="$emit('refresh')" :disabled="loading" type="button">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          :class="{ spin: loading }">
          <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        Обновить
      </button>
    </div>

    <!-- Скелетон -->
    <div v-if="loading" class="cw-grid">
      <div v-for="i in 12" :key="i" class="cw-skel">
        <div class="cw-skel-poster"></div>
        <div class="cw-skel-line"></div>
        <div class="cw-skel-line short"></div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="cw-message cw-error">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="cw-msg-title">Не удалось загрузить данные</p>
        <button @click="$emit('refresh')" class="cw-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="!anime.length" class="cw-message">
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      <div>
        <p class="cw-msg-title">Никто ничего не смотрит прямо сейчас</p>
        <p class="cw-msg-sub">Попробуйте обновить через несколько минут</p>
      </div>
    </div>

    <!-- Сетка -->
    <div v-else class="cw-grid">
      <router-link
        v-for="a in anime"
        :key="a.id"
        :to="`/anime/${a.id}`"
        class="cw-card"
      >
        <div class="cw-poster">
          <img v-if="poster(a)" :src="poster(a)!" :alt="title(a)" loading="lazy" />
          <div v-else class="cw-ph">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/><path d="M12 2v20M2 12h20"/>
            </svg>
          </div>

          <!-- Оверлей -->
          <div class="cw-overlay">
            <div class="cw-play">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </div>
          </div>

          <!-- Счётчик зрителей -->
          <div class="cw-viewers" v-if="a.viewers_count">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            {{ a.viewers_count }}
          </div>

          <!-- Рейтинг -->
          <span v-if="score(a)" class="cw-score">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="#fbbf24" stroke="none">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            {{ score(a) }}
          </span>
        </div>

        <div class="cw-info">
          <p class="cw-name">{{ title(a) }}</p>
          <p class="cw-meta">{{ a.year }}{{ episodes(a) }}</p>
        </div>
      </router-link>
    </div>

  </div>
</template>

<script setup lang="ts">
interface Props { anime: any[]; loading: boolean; error: string | null }
defineProps<Props>()
defineEmits<{ refresh: [] }>()

const poster    = (a: any): string | null => a.poster_image_url || a.poster_url || a.poster || null
const title     = (a: any): string        => a.title_ru || a.title_en || a.title || 'Без названия'
const score     = (a: any): string | null => a.score ? parseFloat(a.score).toFixed(1) : null
const episodes  = (a: any): string        => { const ep = a.episodes || a.episodes_count; return ep ? ` · ${ep} эп.` : '' }
</script>

<style scoped>
.cw-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding: var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.cw-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.02em;
}

.cw-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

.cw-refresh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}
.cw-refresh:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.cw-refresh:disabled { opacity: .5; cursor: not-allowed; }

.cw-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-4);
}

.cw-skel { display: flex; flex-direction: column; gap: 8px; }
.cw-skel-poster {
  aspect-ratio: 2/3; border-radius: var(--radius-card);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line {
  height: 13px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line.short { width: 52%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.cw-message {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 60px var(--space-8); color: var(--text-tertiary);
}
.cw-message svg { opacity: .5; flex-shrink: 0; }
.cw-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-1); }
.cw-msg-sub   { font-size: var(--text-sm); margin: 0; }
.cw-error svg { color: var(--danger); opacity: 1; }
.cw-retry {
  background: none; border: none; color: var(--accent);
  font-size: var(--text-sm); cursor: pointer; padding: 0; text-decoration: underline;
}

.cw-card {
  text-decoration: none; border-radius: var(--radius-card);
  overflow: hidden; cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}
.cw-card:hover { transform: translateY(-3px); }

.cw-poster {
  position: relative; aspect-ratio: 2/3;
  background: var(--surface-4); border-radius: var(--radius-card); overflow: hidden;
}
.cw-poster img { width: 100%; height: 100%; object-fit: cover; transition: transform .3s; }
.cw-card:hover .cw-poster img { transform: scale(1.06); }

.cw-ph {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center; color: var(--text-tertiary);
}

.cw-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out);
  z-index: 10;
}
.cw-card:hover .cw-overlay { opacity: 1; }

/* Квадратная синяя кнопка с анимацией распыления */
.cw-play {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: none;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding-left: 4px;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: scale(0.6);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}
.cw-card:hover .cw-play {
  transform: scale(1);
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}
.cw-play:hover {
  transform: scale(1.15) !important;
  background: var(--accent-hover);
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.cw-viewers {
  position: absolute; top: 8px; left: 8px;
  display: flex; align-items: center; gap: 4px;
  height: 22px; padding: 0 8px;
  background: rgba(0,0,0,.82); backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700; color: #38bdf8;
}

.cw-score {
  position: absolute; bottom: 8px; right: 8px;
  display: flex; align-items: center; gap: 3px;
  height: 22px; padding: 0 7px;
  background: rgba(0,0,0,.82); backdrop-filter: blur(8px);
  border-radius: var(--radius-full); font-size: 11px; font-weight: 700; color: #fbbf24;
}

.cw-info { padding: var(--space-2) var(--space-1) 0; display: flex; flex-direction: column; gap: 3px; }
.cw-name {
  font-size: var(--text-sm); font-weight: 600; color: var(--text-primary);
  margin: 0; line-height: 1.35;
  display: -webkit-box; line-clamp: 2; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.cw-meta { font-size: var(--text-xs); color: var(--text-tertiary); margin: 0; }

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 767px) {
  .cw-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
}
</style>
