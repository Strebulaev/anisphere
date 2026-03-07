<template>
  <div class="ong">

    <!-- ══ Панель фильтров ════════════════════════════════════ -->
    <div class="ong-bar">
      <div class="ong-bar-top">
        <!-- Поиск -->
        <div class="ong-search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="search"
            type="text"
            placeholder="Поиск онгоинга..."
            class="ong-search-input"
          />
          <button v-if="search" @click="search = ''" class="ong-search-clear" type="button">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Сортировка -->
        <select v-model="sortBy" class="ong-sort">
          <option value="-score">По рейтингу ↓</option>
          <option value="score">По рейтингу ↑</option>
          <option value="-year">По году ↓</option>
          <option value="year">По году ↑</option>
          <option value="title">По названию</option>
        </select>

        <!-- Обновить + счётчик -->
        <div class="ong-bar-right">
          <span v-if="!loading" class="ong-counter">{{ sortedAnime.length }} аниме</span>
          <button class="ong-refresh" @click="emits('refresh')" :disabled="loading" type="button">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
              <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Жанры -->
      <GenreFilter v-model="genre" />
    </div>

    <!-- ══ Скелетон ══════════════════════════════════════════ -->
    <div v-if="loading" class="ong-grid">
      <div v-for="i in 24" :key="i" class="ong-skel">
        <div class="ong-skel-poster"></div>
        <div class="ong-skel-line"></div>
        <div class="ong-skel-line short"></div>
      </div>
    </div>

    <!-- ══ Ошибка ════════════════════════════════════════════ -->
    <div v-else-if="error" class="ong-message ong-error">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="ong-msg-title">Не удалось загрузить онгоинги</p>
        <button @click="emits('refresh')" class="ong-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- ══ Пусто ════════════════════════════════════════════ -->
    <div v-else-if="sortedAnime.length === 0" class="ong-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <div>
        <p class="ong-msg-title" v-if="search || genre.length">Ничего не найдено</p>
        <p class="ong-msg-title" v-else>Онгоинги не найдены</p>
        <button v-if="search || genre.length" @click="resetFilters" class="ong-retry" type="button">Сбросить фильтры</button>
      </div>
    </div>

    <!-- ══ Сетка ════════════════════════════════════════════ -->
    <div v-else class="ong-grid">
      <router-link
        v-for="a in sortedAnime"
        :key="a.id"
        :to="`/anime/${a.id}`"
        class="ong-card"
      >
        <!-- Постер -->
        <div class="ong-poster">
          <img v-if="poster(a)" :src="poster(a)!" :alt="title(a)" loading="lazy" />
          <div v-else class="ong-ph">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/><path d="M12 2v20M2 12h20"/>
            </svg>
          </div>

          <!-- Оверлей -->
          <div class="ong-overlay">
            <div class="ong-play">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </div>
          </div>

          <!-- Бейдж "X смотрят" - показывается только если есть активные зрители -->
          <span v-if="viewersCount(a) > 0" class="ong-badge-viewers">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            {{ viewersCount(a) }}
          </span>

          <!-- Рейтинг -->
          <span v-if="score(a)" class="ong-score">
            <svg width="9" height="9" viewBox="0 0 24 24" fill="#fbbf24" stroke="none">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            {{ score(a) }}
          </span>
        </div>

        <!-- Инфо -->
        <div class="ong-info">
          <p class="ong-name">{{ title(a) }}</p>
          <p class="ong-meta">{{ a.year }}{{ episodes(a) }}</p>
          <div v-if="genreList(a).length" class="ong-tags">
            <span v-for="g in genreList(a).slice(0, 2)" :key="g" class="ong-tag">{{ g }}</span>
          </div>
        </div>
      </router-link>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import GenreFilter from '@/components/Cards/GenreFilter.vue'

interface Props { anime: any[]; loading: boolean; error: string | null; viewersMap?: Record<number, number> }
const props = defineProps<Props>()
const emits = defineEmits<{ refresh: [] }>()

const viewersCount = (a: any): number => props.viewersMap?.[a.id] ?? 0

// ── Фильтры ───────────────────────────────────────────────
const search   = ref('')
const sortBy   = ref('-score')
const genre    = ref<string[]>([])

// ── Хелперы ───────────────────────────────────────────────
const poster    = (a: any): string | null => a.poster_image_url || a.poster_url || a.poster || null
const title     = (a: any): string        => a.title_ru || a.title_en || a.title || 'Без названия'
const score     = (a: any): string | null => a.score ? parseFloat(a.score).toFixed(1) : null
const episodes  = (a: any): string        => { const ep = a.episodes || a.episodes_count; return ep ? ` · ${ep} эп.` : '' }
const genreList = (a: any): string[] => {
  const raw = a.genres
  if (!raw) return []
  // Массив объектов [{id,name,slug}] или строк
  if (Array.isArray(raw)) return raw.map((g: any) => (typeof g === 'object' && g !== null ? g.name : String(g))).filter(Boolean)
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed)
        ? parsed.map((g: any) => (typeof g === 'object' && g !== null ? g.name : String(g))).filter(Boolean)
        : [raw]
    } catch { return raw.split(',').map((g: string) => g.trim()).filter(Boolean) }
  }
  return []
}

// ── Фильтрация ────────────────────────────────────────────
const filtered = computed(() => {
  let list = [...props.anime]
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(a => title(a).toLowerCase().includes(q) || (a.title_en || '').toLowerCase().includes(q))
  }
  if (genre.value.length) {
    list = list.filter(a =>
      genre.value.every(sel =>
        genreList(a).some(g => g.toLowerCase() === sel.toLowerCase())
      )
    )
  }
  return list
})

const sortedAnime = computed(() => {
  const list = [...filtered.value]
  switch (sortBy.value) {
    case '-score':  return list.sort((a, b) => (parseFloat(b.score||0) - parseFloat(a.score||0)))
    case 'score':   return list.sort((a, b) => (parseFloat(a.score||0) - parseFloat(b.score||0)))
    case '-year':   return list.sort((a, b) => (b.year || 0) - (a.year || 0))
    case 'year':    return list.sort((a, b) => (a.year || 0) - (b.year || 0))
    case 'title':   return list.sort((a, b) => title(a).localeCompare(title(b)))
    default: return list
  }
})

const resetFilters = () => { search.value = ''; genre.value = [] }

// Автозагрузка при маунте если данных нет
watch(() => props.anime, v => { if (!v.length && !props.loading) emits('refresh') }, { immediate: true })
</script>

<style scoped>
/* ── Панель фильтров ─────────────────────────────────────── */
.ong-bar {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-5);
}

.ong-bar-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* Поиск */
.ong-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.ong-search svg:first-child {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}
.ong-search-input {
  width: 100%;
  height: 38px;
  padding: 0 34px 0 34px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color .15s;
}
.ong-search-input:focus { border-color: var(--accent); }
.ong-search-input::placeholder { color: var(--text-tertiary); }
.ong-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-tertiary); cursor: pointer;
  padding: 3px; display: flex; transition: color .15s;
}
.ong-search-clear:hover { color: var(--text-primary); }

/* Сортировка */
.ong-sort {
  height: 38px;
  padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  outline: none;
  min-width: 168px;
  transition: border-color .15s;
}
.ong-sort:focus { border-color: var(--accent); }

/* Правая часть */
.ong-bar-right { display: flex; align-items: center; gap: var(--space-3); margin-left: auto; }

.ong-counter {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.ong-refresh {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all .15s;
}
.ong-refresh:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.ong-refresh:disabled { opacity: .5; cursor: not-allowed; }

/* ── Скелетон ─────────────────────────────────────────────── */
.ong-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-4);
}
.ong-skel { display: flex; flex-direction: column; gap: 8px; }
.ong-skel-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-card);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ong-skel-line {
  height: 13px; width: 80%;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ong-skel-line.short { width: 52%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* ── Сообщения ────────────────────────────────────────────── */
.ong-message {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: 60px var(--space-8);
  color: var(--text-tertiary);
}
.ong-message svg { opacity: .5; flex-shrink: 0; }
.ong-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-2); }
.ong-error svg { color: var(--danger); opacity: 1; }
.ong-retry {
  background: none; border: none; color: var(--accent);
  font-size: var(--text-sm); cursor: pointer; padding: 0;
  text-decoration: underline;
}

/* ── Карточка ─────────────────────────────────────────────── */
.ong-card {
  text-decoration: none;
  border-radius: var(--radius-card);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}
.ong-card:hover { transform: translateY(-3px); }

.ong-poster {
  position: relative;
  aspect-ratio: 2/3;
  background: var(--surface-4);
  border-radius: var(--radius-card);
  overflow: hidden;
}
.ong-poster img { width: 100%; height: 100%; object-fit: cover; transition: transform var(--duration-slow) var(--ease-out); }
.ong-card:hover .ong-poster img { transform: scale(1.04); }

.ong-ph {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-tertiary);
}

.ong-overlay {
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
.ong-card:hover .ong-overlay { opacity: 1; }

/* Квадратная синяя кнопка с анимацией распыления */
.ong-play {
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
.ong-card:hover .ong-play {
  transform: scale(1);
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}
.ong-play:hover {
  transform: scale(1.15) !important;
  background: var(--accent-hover);
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.ong-badge-viewers {
  position: absolute; top: 8px; left: 8px;
  display: flex; align-items: center; gap: 4px;
  height: 22px; padding: 0 8px;
  background: rgba(0,0,0,.82); backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700; color: #38bdf8;
}

.ong-score {
  position: absolute; bottom: 8px; right: 8px;
  display: flex; align-items: center; gap: 3px;
  height: 22px; padding: 0 7px;
  background: rgba(0,0,0,.82);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700; color: #fbbf24;
}

.ong-info { padding: var(--space-2) var(--space-1) 0; display: flex; flex-direction: column; gap: 3px; }
.ong-name {
  font-size: var(--text-sm); font-weight: 600; color: var(--text-primary);
  margin: 0; line-height: 1.35;
  display: -webkit-box; line-clamp: 2; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.ong-meta { font-size: var(--text-xs); color: var(--text-tertiary); margin: 0; }

.ong-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.ong-tag {
  height: 18px; padding: 0 6px;
  background: var(--surface-3);
  border-radius: var(--radius-xs);
  font-size: 10px; color: var(--text-tertiary);
}

/* ── Адаптив ──────────────────────────────────────────────── */
@media (max-width: 767px) {
  .ong-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
  .ong-bar-top { gap: var(--space-2); }
  .ong-search { min-width: 150px; }
  .ong-sort { min-width: 140px; }
}

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
