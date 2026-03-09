<template>
  <div class="cw">

    <!-- Заголовок со статистикой -->
    <div class="cw-header">
      <div class="cw-header-left">
        <div class="cw-live-dot"></div>
        <div>
          <h2 class="cw-title">Сейчас смотрят</h2>
          <p class="cw-subtitle">
            <span v-if="!loading && anime.length">
              {{ totalViewers }} {{ viewersWord(totalViewers) }} смотрят {{ anime.length }} аниме прямо сейчас
            </span>
            <span v-else>Аниме, которые активно смотрят на сайте</span>
          </p>
        </div>
      </div>
      <button class="cw-refresh" @click="$emit('refresh')" :disabled="loading" type="button">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
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

    <!-- Сетка с AnimeCard -->
    <div v-else class="cw-grid">
      <div
        v-for="a in anime"
        :key="a.id"
        class="cw-card-wrap"
      >
        <AnimeCard
          :anime="normalizeAnime(a)"
          :show-actions="true"
          :show-genres="false"
          :show-progress="false"
          @click="goToAnime(a)"
        />
        <!-- Строка зрителей под карточкой -->
        <div v-if="a.viewers_count" class="cw-viewers-row">
          <span class="cw-viewers-pulse"></span>
          <span class="cw-viewers-text">{{ a.viewers_count }} {{ viewersWord(a.viewers_count) }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '@/components/Cards/AnimeCard.vue'

interface Props { anime: any[]; loading: boolean; error: string | null }
const props = defineProps<Props>()
defineEmits<{ refresh: [] }>()

const router = useRouter()
const goToAnime = (a: any) => router.push(`/anime/${a?.id ?? a}`)

const totalViewers = computed(() =>
  props.anime.reduce((sum, a) => sum + (a.viewers_count || 0), 0)
)

/** Нормализует объект из /currently-watching/ в формат AnimeCard */
const normalizeAnime = (a: any) => ({
  id: a.id,
  title_ru: a.title_ru || a.title || '',
  title_en: a.title_en || a.title_orig || '',
  title_jp: a.title_jp || '',
  year: a.year ?? null,
  status: a.status || 'ongoing',
  episodes: a.episodes ?? a.episodes_total ?? null,
  score: a.score ? Number(a.score) : null,
  poster_url: a.poster_url || null,
  poster_image_url: a.poster_image_url || null,
  poster_file: a.poster_file || null,
  poster: a.poster || null,
  type: a.kind || a.type || 'tv',
  genres: a.genres || [],
})

const viewersWord = (n: number): string => {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 19) return 'человек'
  if (mod10 === 1) return 'человек'
  if (mod10 >= 2 && mod10 <= 4) return 'человека'
  return 'человек'
}
</script>

<style scoped>
/* ── Хедер ─────────────────────────────────────────────────── */
.cw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding: var(--space-5) var(--space-6);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.cw-header-left { display: flex; align-items: center; gap: var(--space-4); }

/* Живая точка */
.cw-live-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  animation: live-pulse 2s infinite;
}
@keyframes live-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(34,197,94,.4); }
  70%  { box-shadow: 0 0 0 8px rgba(34,197,94,0); }
  100% { box-shadow: 0 0 0 0 rgba(34,197,94,0); }
}

.cw-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px;
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
  transition: all .15s;
  flex-shrink: 0;
}
.cw-refresh:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.cw-refresh:disabled { opacity: .5; cursor: not-allowed; }
.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Сетка ─────────────────────────────────────────────────── */
.cw-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

/* ── Обёртка карточки (AnimeCard + строка зрителей) ─────────── */
.cw-card-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Строка зрителей под карточкой */
.cw-viewers-row {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 var(--space-1);
}
.cw-viewers-pulse {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
  animation: live-pulse 2s infinite;
}
.cw-viewers-text {
  font-size: var(--text-xs);
  font-weight: 600;
  color: #22c55e;
}

/* ── Скелетон ──────────────────────────────────────────────── */
.cw-skel { display: flex; flex-direction: column; gap: 8px; }
.cw-skel-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line {
  height: 13px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line.short { width: 52%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* ── Сообщения ─────────────────────────────────────────────── */
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

/* ── Адаптив ───────────────────────────────────────────────── */
@media (max-width: 767px) {
  .cw-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
  .cw-header { padding: var(--space-4); }
  .cw-title { font-size: var(--text-xl); }
}
</style>
