<template>
  <div class="ann">

    <!-- ══ Панель фильтров ════════════════════════════════════ -->
    <div class="ann-bar">
      <div class="ann-bar-top">
        <div class="ann-search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="search" type="text" placeholder="Поиск анонса..." class="ann-search-input" />
          <button v-if="search" @click="search = ''" class="ann-search-clear" type="button">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <select v-model="sortBy" class="ann-sort">
          <option value="-year">По году выхода ↓</option>
          <option value="year">По году выхода ↑</option>
          <option value="-score">По ожидаемости</option>
          <option value="title">По названию</option>
        </select>

        <div class="ann-bar-right">
          <span v-if="!loading" class="ann-counter">{{ sortedAnime.length }} аниме</span>
          <button class="ann-refresh" @click="emits('refresh')" :disabled="loading" type="button">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
              <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
        </div>
      </div>

      <GenreFilter v-model="genre" />
    </div>

    <!-- ══ Скелетон ══════════════════════════════════════════ -->
    <div v-if="loading" class="ann-grid">
      <div v-for="i in 24" :key="i" class="ann-skel">
        <div class="ann-skel-poster"></div>
        <div class="ann-skel-line"></div>
        <div class="ann-skel-line short"></div>
      </div>
    </div>

    <!-- ══ Ошибка ════════════════════════════════════════════ -->
    <div v-else-if="error" class="ann-message ann-err">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="ann-msg-title">Не удалось загрузить анонсы</p>
        <button @click="emits('refresh')" class="ann-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- ══ Пусто ════════════════════════════════════════════ -->
    <div v-else-if="sortedAnime.length === 0" class="ann-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
        <line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>
      </svg>
      <div>
        <p class="ann-msg-title" v-if="search || genre.length">Ничего не найдено по фильтрам</p>
        <p class="ann-msg-title" v-else>Анонсов пока нет</p>
        <p class="ann-msg-sub" v-if="!search && !genre.length">Здесь появятся анонсы предстоящих аниме</p>
        <button v-if="search || genre.length" @click="resetFilters" class="ann-retry" type="button">Сбросить фильтры</button>
      </div>
    </div>

    <!-- ══ Сетка ════════════════════════════════════════════ -->
    <div v-else class="ann-grid">
      <router-link
        v-for="a in sortedAnime"
        :key="a.id"
        :to="`/anime/${a.id}`"
        class="ann-card"
      >
        <!-- Постер -->
        <div class="ann-poster">
          <img v-if="poster(a)" :src="poster(a)!" :alt="title(a)" loading="lazy" />
          <div v-else class="ann-ph">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="2" width="20" height="20" rx="2"/><path d="M12 2v20M2 12h20"/>
            </svg>
          </div>

          <!-- Оверлей «скоро» -->
          <div class="ann-overlay">
            <div class="ann-soon-badge">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              Скоро
            </div>
          </div>

          <!-- Анонс-бейдж -->
          <span class="ann-badge">◆ АНОНС</span>

          <!-- Год -->
          <span v-if="a.year" class="ann-year">{{ a.year }}</span>
        </div>

        <!-- Инфо -->
        <div class="ann-info">
          <p class="ann-name">{{ title(a) }}</p>
          <p class="ann-meta">
            <span v-if="a.year">{{ a.year }}</span>
            <span v-if="episodes(a)">{{ episodes(a) }}</span>
          </p>
          <div v-if="genreList(a).length" class="ann-tags">
            <span v-for="g in genreList(a).slice(0, 2)" :key="g" class="ann-tag">{{ g }}</span>
          </div>
        </div>
      </router-link>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import GenreFilter from '@/components/Cards/GenreFilter.vue'

interface Props { anime: any[]; loading: boolean; error: string | null }
const props = defineProps<Props>()
const emits = defineEmits<{ refresh: [] }>()

const search = ref('')
const sortBy = ref('-year')
const genre  = ref<string[]>([])

const poster    = (a: any): string | null => a.poster_image_url || a.poster_url || a.poster || null
const title     = (a: any): string        => a.title_ru || a.title_en || a.title || 'Без названия'
const episodes  = (a: any): string        => { const ep = a.episodes || a.episodes_count; return ep ? ` · ${ep} эп.` : '' }
const genreList = (a: any): string[] => {
  const raw = a.genres
  if (!raw) return []
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

const filtered = computed(() => {
  let list = [...props.anime]
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(a => title(a).toLowerCase().includes(q) || (a.title_en || '').toLowerCase().includes(q))
  }
  if (genre.value.length) {
    list = list.filter(a =>
      genre.value.every(sel => genreList(a).some(g => g.toLowerCase() === sel.toLowerCase()))
    )
  }
  return list
})

const sortedAnime = computed(() => {
  const list = [...filtered.value]
  switch (sortBy.value) {
    case '-year':   return list.sort((a, b) => (b.year || 0) - (a.year || 0))
    case 'year':    return list.sort((a, b) => (a.year || 0) - (b.year || 0))
    case '-score':  return list.sort((a, b) => (parseFloat(b.score || 0) - parseFloat(a.score || 0)))
    case 'title':   return list.sort((a, b) => title(a).localeCompare(title(b)))
    default: return list
  }
})

const resetFilters = () => { search.value = ''; genre.value = [] }

// Автозагрузка если нет данных
watch(() => props.anime, v => { if (!v.length && !props.loading) emits('refresh') }, { immediate: true })
</script>

<style scoped>
/* ── Панель фильтров ─────────────────────────────────────── */
.ann-bar {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-5);
}

.ann-bar-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.ann-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.ann-search svg:first-child {
  position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
  color: var(--text-tertiary); pointer-events: none;
}
.ann-search-input {
  width: 100%; height: 38px;
  padding: 0 34px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color .15s;
}
.ann-search-input:focus { border-color: var(--accent); }
.ann-search-input::placeholder { color: var(--text-tertiary); }
.ann-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 3px; display: flex;
}

.ann-sort {
  height: 38px; padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer; outline: none; min-width: 185px;
}

.ann-bar-right { display: flex; align-items: center; gap: var(--space-3); margin-left: auto; }
.ann-counter { font-size: var(--text-sm); color: var(--text-tertiary); white-space: nowrap; }
.ann-refresh {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer; transition: all .15s;
}
.ann-refresh:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.ann-refresh:disabled { opacity: .5; cursor: not-allowed; }

/* ── Скелетон ─────────────────────────────────────────────── */
.ann-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-4);
}
.ann-skel { display: flex; flex-direction: column; gap: 8px; }
.ann-skel-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-card);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line {
  height: 13px; width: 80%;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line.short { width: 52%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* ── Сообщения ────────────────────────────────────────────── */
.ann-message {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 60px var(--space-8);
  color: var(--text-tertiary);
}
.ann-message svg { opacity: .4; flex-shrink: 0; }
.ann-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-2); }
.ann-msg-sub   { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; }
.ann-err svg   { color: var(--danger); opacity: 1; }
.ann-retry { background: none; border: none; color: var(--accent); font-size: var(--text-sm); cursor: pointer; padding: 0; text-decoration: underline; }

/* ── Карточка ─────────────────────────────────────────────── */
.ann-card {
  text-decoration: none;
  border-radius: var(--radius-card);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}
.ann-card:hover { transform: translateY(-3px); }

.ann-poster {
  position: relative; aspect-ratio: 2/3;
  background: var(--surface-4);
  border-radius: var(--radius-card);
  overflow: hidden;
}
.ann-poster img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
  filter: brightness(.88) saturate(.9);
}
.ann-card:hover .ann-poster img { transform: scale(1.04); filter: brightness(.95) saturate(1); }

.ann-ph { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); }

.ann-overlay {
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
.ann-card:hover .ann-overlay { opacity: 1; }

.ann-soon-badge {
  display: flex; align-items: center; gap: 6px;
  padding: var(--space-2) var(--space-4);
  background: rgba(168,85,247,.85);
  backdrop-filter: blur(10px);
  border-radius: var(--radius-md);
  color: white;
  font-size: var(--text-sm);
  font-weight: 600;
}

.ann-badge {
  position: absolute; top: 8px; left: 8px;
  height: 20px; padding: 0 7px;
  background: #a855f7;
  border-radius: var(--radius-full);
  font-size: 9px; font-weight: 800;
  color: white; letter-spacing: .06em;
  display: flex; align-items: center;
}

.ann-year {
  position: absolute; bottom: 8px; right: 8px;
  height: 22px; padding: 0 7px;
  background: rgba(0,0,0,.82);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700; color: #e2e8f0;
  display: flex; align-items: center;
}

.ann-info { padding: var(--space-2) var(--space-1) 0; display: flex; flex-direction: column; gap: 3px; }
.ann-name {
  font-size: var(--text-sm); font-weight: 600; color: var(--text-primary);
  margin: 0; line-height: 1.35;
  display: -webkit-box; line-clamp: 2; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.ann-meta { font-size: var(--text-xs); color: var(--text-tertiary); margin: 0; }
.ann-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.ann-tag { height: 18px; padding: 0 6px; background: var(--surface-3); border-radius: var(--radius-xs); font-size: 10px; color: var(--text-tertiary); }

@media (max-width: 767px) {
  .ann-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
  .ann-bar-top { gap: var(--space-2); }
  .ann-search { min-width: 150px; }
}

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
