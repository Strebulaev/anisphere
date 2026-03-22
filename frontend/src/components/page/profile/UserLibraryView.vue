<template>
  <div class="library-page">

    <!-- ══ ШАПКА ══════════════════════════════════════════════ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Моя коллекция</h1>
        <p class="page-subtitle">Ваша личная библиотека аниме</p>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg class="search-ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="searchQuery" class="search-input" placeholder="Поиск по коллекции..." @input="debouncedSearch" />
          <button v-if="searchQuery" class="search-clear" @click="clearSearch">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <select class="sort-select" v-model="ordering" @change="loadItems">
          <option value="-updated_at">Недавно обновлённые</option>
          <option value="-added_at">Недавно добавленные</option>
          <option value="-rating">По оценке</option>
          <option value="current_episode">По прогрессу</option>
        </select>
      </div>
    </div>

    <!-- ══ СТАТУСНЫЕ ВКЛАДКИ ═══════════════════════════════════ -->
    <div class="tabs-row" v-if="stats">
      <button
        v-for="tab in tabs" :key="tab.key"
        class="tab-btn" :class="{ active: activeTab === tab.key }"
        @click="setTab(tab.key)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span class="tab-count">{{ getCount(tab.key) }}</span>
      </button>
    </div>
    <div class="tabs-row" v-else>
      <div v-for="n in 7" :key="n" class="tab-btn-skel"></div>
    </div>

    <!-- ══ СТАТИСТИКА (только «Все») ══════════════════════════ -->
    <Transition name="fade">
      <div v-if="activeTab === '' && stats && !loading && stats.total > 0" class="summary-card">

        <!-- Главные числа -->
        <div class="summary-numbers">
          <div class="sn-item">
            <span class="sn-val">{{ stats.total }}</span>
            <span class="sn-key">аниме</span>
          </div>
          <div class="sn-sep"></div>
          <div class="sn-item">
            <span class="sn-val">{{ (stats.episodes_watched ?? 0).toLocaleString('ru') }}</span>
            <span class="sn-key">серий</span>
          </div>
          <div class="sn-sep"></div>
          <div class="sn-item" :title="watchHoursDetailed">
            <span class="sn-val">{{ watchHoursFormatted }}</span>
            <span class="sn-key">просмотрено</span>
          </div>
          <template v-if="remainingHoursFormatted">
            <div class="sn-sep"></div>
            <div class="sn-item sn-item--muted">
              <span class="sn-val sn-val--muted">{{ remainingHoursFormatted }}</span>
              <span class="sn-key">осталось</span>
            </div>
          </template>
          <template v-if="stats.avg_score">
            <div class="sn-sep"></div>
            <div class="sn-item">
              <span class="sn-val">★ {{ Number(stats.avg_score).toFixed(1) }}</span>
              <span class="sn-key">ср. оценка</span>
            </div>
          </template>
        </div>

        <!-- Полоса статусов -->
        <div class="summary-bar">
          <div
            v-for="seg in statusSegments" :key="seg.key"
            class="bar-seg"
            :style="{ width: seg.pct + '%', background: seg.color }"
            :title="seg.label + ': ' + seg.count"
          ></div>
        </div>
        <div class="summary-legend">
          <span v-for="seg in statusSegments" :key="seg.key" class="leg-item">
            <span class="leg-dot" :style="{ background: seg.color }"></span>
            {{ seg.label }} · {{ seg.count }}
            <span class="leg-pct">({{ Math.round(seg.count / stats.total * 100) }}%)</span>
          </span>
        </div>
      </div>
    </Transition>

    <!-- ══ СКЕЛЕТОН ════════════════════════════════════════════ -->
    <div v-if="loading" class="cards-grid">
      <div v-for="n in 16" :key="n" class="card-skel">
        <div class="skel-poster"></div>
        <div class="skel-body">
          <div class="skel-line w70"></div>
          <div class="skel-line w45"></div>
        </div>
      </div>
    </div>

    <!-- ══ ОШИБКА ══════════════════════════════════════════════ -->
    <div v-else-if="error" class="state-box">
      <span class="state-icon">⚠️</span>
      <p class="state-title">Не удалось загрузить коллекцию</p>
      <button class="state-btn" @click="loadItems">Повторить</button>
    </div>

    <!-- ══ ПУСТО ════════════════════════════════════════════════ -->
    <div v-else-if="items.length === 0" class="state-box">
      <span class="state-icon">{{ currentTab?.icon ?? '📚' }}</span>
      <p class="state-title">{{ emptyMessage }}</p>
      <p class="state-sub">Добавляйте аниме прямо на их страницах</p>
      <button class="state-btn accent" @click="router.push('/anime')">Найти аниме</button>
    </div>

    <!-- ══ КАРТОЧКИ ════════════════════════════════════════════ -->
    <div v-else class="cards-grid">
      <LibraryCard
        v-for="item in items" :key="item.id"
        :item="item" @updated="onUpdated" @deleted="onDeleted"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import LibraryCard from '@/components/Cards/LibraryCard.vue'

const router = useRouter()
const route  = useRoute()

// ── Состояние ────────────────────────────────────────────────
const items       = ref<any[]>([])
const stats       = ref<any>(null)
const loading     = ref(true)
const error       = ref(false)
const searchQuery = ref('')
const ordering    = ref('-updated_at')
const activeTab   = ref<string>('')

// ── Вкладки ──────────────────────────────────────────────────
const tabs = [
  { key: '',          label: 'Все',           icon: '📚' },
  { key: 'started',   label: 'В процессе',    icon: '▶️' },
  { key: 'completed', label: 'Просмотрено',   icon: '✅' },
  { key: 'planned',   label: 'Запланировано', icon: '📅' },
  { key: 'on_hold',   label: 'Отложено',      icon: '⏸️' },
  { key: 'dropped',   label: 'Брошено',       icon: '❌' },
  { key: 'favorite',  label: 'Избранное',     icon: '⭐' },
]

const currentTab = computed(() => tabs.find(t => t.key === activeTab.value))

const getCount = (key: string): number => {
  if (!stats.value) return 0
  if (key === '') return stats.value.total ?? 0
  if (key === 'favorite') return stats.value.favorites ?? 0
  return stats.value[key] ?? 0
}

const emptyMessage = computed(() => {
  const map: Record<string, string> = {
    '': 'Коллекция пока пуста',
    started: 'Нет аниме в процессе', completed: 'Нет завершённых',
    planned: 'Нет запланированных', on_hold: 'Нет отложенных',
    dropped: 'Нет брошенных', favorite: 'Нет избранных',
  }
  return map[activeTab.value] ?? 'Ничего не найдено'
})

// ── Форматирование времени ────────────────────────────────────
const AVG_EP_MINUTES = 24  // fallback если API не вернул watch_hours

const formatHours = (totalMinutes: number): string => {
  if (totalMinutes <= 0) return '0 мин'
  const days  = Math.floor(totalMinutes / (60 * 24))
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60)
  const mins  = Math.round(totalMinutes % 60)
  if (days > 0)  return `${days} д ${hours} ч`
  if (hours > 0) return `${hours} ч ${mins} мин`
  return `${mins} мин`
}

// Если API вернул watch_hours — используем его, иначе считаем из серий
const watchMinutes = computed((): number => {
  if (!stats.value) return 0
  if (stats.value.watch_hours != null) return Math.round(stats.value.watch_hours * 60)
  return (stats.value.episodes_watched ?? 0) * AVG_EP_MINUTES
})

const remainingMinutes = computed((): number => {
  if (!stats.value) return 0
  if (stats.value.remaining_hours != null) return Math.round(stats.value.remaining_hours * 60)
  return (stats.value.episodes_remaining ?? 0) * AVG_EP_MINUTES
})

const watchHoursFormatted  = computed(() => formatHours(watchMinutes.value))
const remainingHoursFormatted = computed(() => {
  if (remainingMinutes.value <= 0) return ''
  return formatHours(remainingMinutes.value)
})
const watchHoursDetailed = computed(() => {
  const h = Math.floor(watchMinutes.value / 60)
  const m = watchMinutes.value % 60
  return `${h} ч ${m} мин (≈ ${Math.round(h / 24)} д)`
})

// ── Сегменты прогресс-бара ────────────────────────────────────
const statusSegments = computed(() => {
  if (!stats.value || !stats.value.total) return []
  const s = stats.value, total = s.total
  return [
    { key: 'started',   label: 'В процессе',  count: s.started   ?? 0, color: 'var(--accent)' },
    { key: 'completed', label: 'Просмотрено', count: s.completed ?? 0, color: '#22c55e' },
    { key: 'planned',   label: 'Планирую',    count: s.planned   ?? 0, color: '#a78bfa' },
    { key: 'on_hold',   label: 'Отложено',    count: s.on_hold   ?? 0, color: '#f59e0b' },
    { key: 'dropped',   label: 'Брошено',     count: s.dropped   ?? 0, color: '#ef4444' },
  ].filter(x => x.count > 0)
   .map(x => ({ ...x, pct: Math.max(1, Math.round(x.count / total * 100)) }))
})

// ── Drop rate ─────────────────────────────────────────────────
const dropRate = computed((): number | null => {
  if (!stats.value) return null
  const dropped   = stats.value.dropped   ?? 0
  const completed = stats.value.completed ?? 0
  const denom = completed + dropped
  if (denom === 0) return null
  return Math.round((dropped / denom) * 100)
})

// ── Поиск с debounce ─────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout>
const debouncedSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadItems(), 350)
}
const clearSearch = () => { searchQuery.value = ''; loadItems() }

// ── Загрузка данных ──────────────────────────────────────────
const loadItems = async () => {
  loading.value = true; error.value = false
  try {
    const params: any = { ordering: ordering.value }
    if (activeTab.value === 'favorite') params.is_favorite = 'true'
    else if (activeTab.value) params.status = activeTab.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
    const res = await apiClient.get('/users/library/', { params })
    items.value = Array.isArray(res.data) ? res.data : (res.data.results ?? [])
  } catch (e) { console.error(e); error.value = true }
  finally { loading.value = false }
}

const loadStats = async () => {
  try {
    const res = await apiClient.get('/users/library/statistics/')
    stats.value = res.data
  } catch (e) { console.error('Ошибка статистики', e) }
}

const setTab = (key: string) => {
  activeTab.value = key
  loadItems()
  router.replace({ query: key ? { status: key } : {} })
}

const onUpdated = () => { loadItems(); loadStats() }
const onDeleted = () => { loadItems(); loadStats() }

onMounted(() => {
  const p = route.query.status as string
  if (p && tabs.find(t => t.key === p)) activeTab.value = p
  loadStats()
  loadItems()
})
</script>

<style scoped>
.library-page {
  max-width: 1440px; margin: 0 auto;
  padding: var(--space-6) var(--space-5);
  display: flex; flex-direction: column; gap: var(--space-6);
}
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: var(--space-4); flex-wrap: wrap;
}
.page-title {
  font-size: clamp(22px,3vw,32px); font-weight: 800; color: var(--text-primary);
  margin: 0 0 4px; letter-spacing: -.03em;
}
.page-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }
.header-right { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.search-box { position: relative; display: flex; align-items: center; flex: 1; min-width: 200px; max-width: 280px; }
.search-ic { position: absolute; left: 11px; color: var(--text-tertiary); pointer-events: none; }
.search-input {
  height: 36px; width: 100%; padding: 0 32px 0 34px;
  background: var(--surface-3); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full); color: var(--text-primary);
  font-size: var(--text-sm); outline: none; transition: border-color var(--duration-base);
}
.search-input:focus { border-color: var(--accent); }
.search-input::placeholder { color: var(--text-tertiary); }
.search-clear {
  position: absolute; right: 10px; background: none; border: none;
  color: var(--text-tertiary); cursor: pointer; display: flex; align-items: center; padding: 2px;
}
.search-clear:hover { color: var(--text-primary); }
.sort-select {
  height: 36px; padding: 0 var(--space-3);
  background: var(--surface-3); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); color: var(--text-secondary);
  font-size: var(--text-sm); cursor: pointer; outline: none; white-space: nowrap;
}

/* Вкладки */
.tabs-row { display: flex; gap: 8px; flex-wrap: wrap; }
.tab-btn {
  display: inline-flex; align-items: center; gap: 6px; height: 34px;
  padding: 0 var(--space-4); background: var(--surface-3);
  border: 1px solid var(--border-subtle); border-radius: var(--radius-full);
  font-size: var(--text-sm); color: var(--text-secondary); cursor: pointer;
  transition: all var(--duration-base) var(--ease-out); user-select: none;
}
.tab-btn:hover { background: var(--surface-4); color: var(--text-primary); border-color: var(--border-default); }
.tab-btn.active { background: var(--accent-subtle); border-color: var(--accent); color: var(--accent); }
.tab-icon { font-size: 13px; line-height: 1; }
.tab-label { font-weight: 500; }
.tab-count {
  min-width: 18px; height: 18px; padding: 0 5px; background: var(--surface-5);
  border-radius: 99px; font-size: 10px; font-weight: 700; color: var(--text-tertiary);
  display: inline-flex; align-items: center; justify-content: center;
}
.tab-btn.active .tab-count { background: var(--accent); color: white; }
.tab-btn-skel {
  width: 110px; height: 34px; border-radius: var(--radius-full); background: var(--surface-3);
  animation: shimmer 1.4s ease-in-out infinite;
  background-image: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
}

/* Сводка */
.summary-card {
  background: var(--surface-2); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl); padding: var(--space-5) var(--space-6);
  display: flex; flex-direction: column; gap: var(--space-4);
}
.summary-numbers { display: flex; align-items: center; gap: var(--space-6); flex-wrap: wrap; }
.sn-item { display: flex; flex-direction: column; gap: 1px; }
.sn-item--muted { opacity: .65; }
.sn-val {
  font-size: clamp(20px,2.5vw,28px); font-weight: 800;
  color: var(--text-primary); letter-spacing: -.03em; line-height: 1;
}
.sn-val--muted { color: var(--text-tertiary); font-size: clamp(16px,2vw,22px); }
.sn-key { font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: .06em; }
.sn-sep { width: 1px; height: 36px; background: var(--border-subtle); }
.summary-bar { display: flex; height: 7px; gap: 2px; border-radius: var(--radius-full); overflow: hidden; }
.bar-seg { border-radius: var(--radius-full); }
.summary-legend { display: flex; gap: var(--space-4); flex-wrap: wrap; }
.leg-item { display: flex; align-items: center; gap: 5px; font-size: var(--text-xs); color: var(--text-secondary); }
.leg-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.leg-pct { color: var(--text-tertiary); }

/* Доп. статистика */
.extra-stats {
  display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);
  padding-top: var(--space-4); border-top: 1px solid var(--border-subtle);
}
.es-group { display: flex; flex-direction: column; gap: 6px; }
.es-title {
  font-size: var(--text-xs); font-weight: 700; color: var(--text-tertiary);
  text-transform: uppercase; letter-spacing: .06em; margin-bottom: 4px;
}
.es-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: var(--text-sm); color: var(--text-secondary);
}
.es-row--highlight { background: var(--surface-3); border-radius: 6px; padding: 4px 8px; }
.es-val { font-weight: 600; color: var(--text-primary); }
.es-val--muted { color: var(--text-tertiary); font-weight: 400; }
.es-val--warn { color: #ef4444; }
.es-label { display: flex; align-items: center; gap: 6px; }
.es-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* Сетка */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.5rem; }
.card-skel { display: flex; flex-direction: column; gap: var(--space-2); }
.skel-poster {
  width: 100%; aspect-ratio: 2/3; border-radius: var(--radius-lg);
  animation: shimmer 1.4s ease-in-out infinite;
  background-image: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
}
.skel-body { display: flex; flex-direction: column; gap: 6px; padding: 2px; }
.skel-line {
  height: 11px; border-radius: 4px;
  animation: shimmer 1.4s ease-in-out infinite;
  background-image: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
}
.skel-line.w70 { width: 70%; } .skel-line.w45 { width: 45%; }

/* Состояния */
.state-box { display: flex; flex-direction: column; align-items: center; gap: var(--space-3); padding: 80px var(--space-6); text-align: center; }
.state-icon { font-size: 52px; line-height: 1; }
.state-title { font-size: var(--text-xl); font-weight: 600; color: var(--text-primary); margin: 0; }
.state-sub { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; }
.state-btn {
  display: inline-flex; align-items: center; height: 38px; padding: 0 var(--space-6);
  background: var(--surface-4); color: var(--text-secondary); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); font-size: var(--text-sm); font-weight: 500; cursor: pointer;
  transition: all var(--duration-base);
}
.state-btn.accent { background: var(--accent); color: var(--text-on-accent); border-color: transparent; }
.state-btn:hover { opacity: .85; }

@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
.fade-enter-active, .fade-leave-active { transition: opacity .2s, transform .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 767px) {
  .library-page { padding: var(--space-4) var(--space-3); gap: var(--space-4); }
  .page-header { flex-direction: column; align-items: flex-start; }
  .header-right { width: 100%; }
  .search-box { max-width: 100%; flex: 1; }
  .cards-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: var(--space-3); }
  .extra-stats { grid-template-columns: 1fr; }
}
</style>
