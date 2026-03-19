<template>
  <div class="collection-page">

    <!-- ══ Шапка ══════════════════════════════════════════════ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          Моя коллекция
        </h1>
        <p class="page-subtitle">Все аниме, которые вы смотрели, смотрите или планируете</p>
      </div>
      <div class="header-right">
        <div class="search-box">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="searchQuery"
            class="search-input"
            placeholder="Поиск по коллекции..."
            @input="debouncedSearch"
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''; loadItems()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="sort-wrap">
          <select class="sort-select" v-model="ordering" @change="loadItems">
            <option value="-updated_at">Недавно обновлённые</option>
            <option value="-added_at">Недавно добавленные</option>
            <option value="-rating">По оценке</option>
            <option value="current_episode">По прогрессу</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ══ Статистика ══════════════════════════════════════════ -->
    <div class="stats-bar" v-if="stats">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="stat-chip"
        :class="{ active: activeTab === tab.key }"
        @click="setTab(tab.key)"
      >
        <span class="stat-icon">{{ tab.icon }}</span>
        <span class="stat-label">{{ tab.label }}</span>
        <span class="stat-num">{{ getStatCount(tab.key) }}</span>
      </div>
    </div>

    <!-- Скелетон статистики -->
    <div class="stats-bar" v-else>
      <div v-for="n in 7" :key="n" class="stat-chip skeleton-chip"></div>
    </div>

    <!-- ══ Сводная статистика ══════════════════════════════════ -->
    <div v-if="activeTab === '' && stats && !loading" class="summary-block">
      <div class="summary-numbers">
        <div class="summary-item">
          <span class="summary-val">{{ stats.total }}</span>
          <span class="summary-key">всего аниме</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-val">{{ stats.episodes_watched.toLocaleString('ru') }}</span>
          <span class="summary-key">серий просмотрено</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-val">{{ stats.hours_watched?.toFixed(1) ?? Math.round(stats.episodes_watched * 24 / 60) }}</span>
          <span class="summary-key">часов просмотрено</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-val">{{ stats.hours_remaining?.toFixed(1) ?? '—' }}</span>
          <span class="summary-key">часов осталось</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-item">
          <span class="summary-val">{{ stats.avg_rating?.toFixed(1) ?? '—' }}</span>
          <span class="summary-key">средняя оценка</span>
        </div>
      </div>
      <div class="summary-bar">
        <div
          class="summary-bar-seg"
          v-for="seg in statusSegments"
          :key="seg.key"
          :style="{ width: seg.pct + '%', background: seg.color }"
          :title="seg.label + ': ' + seg.count"
        ></div>
      </div>
      <div class="summary-legend">
        <span v-for="seg in statusSegments" :key="seg.key" class="legend-item">
          <span class="legend-dot" :style="{ background: seg.color }"></span>
          {{ seg.label }}: {{ seg.count }}
        </span>
      </div>
    </div>

    <!-- ══ Состояние загрузки ══════════════════════════════════ -->
    <div v-if="loading" class="grid-skeleton">
      <div v-for="n in 12" :key="n" class="card-skeleton">
        <div class="skel-poster"></div>
        <div class="skel-body">
          <div class="skel-line w70"></div>
          <div class="skel-line w45"></div>
          <div class="skel-bar"></div>
        </div>
      </div>
    </div>

    <!-- ══ Ошибка ══════════════════════════════════════════════ -->
    <div v-else-if="error" class="empty-state">
      <div class="empty-icon">⚠️</div>
      <p class="empty-title">Не удалось загрузить коллекцию</p>
      <button class="empty-btn" @click="loadItems">Повторить</button>
    </div>

    <!-- ══ Пусто ════════════════════════════════════════════════ -->
    <div v-else-if="!loading && items.length === 0" class="empty-state">
      <div class="empty-icon">{{ currentTab?.icon }}</div>
      <p class="empty-title">{{ emptyMessage }}</p>
      <p class="empty-sub">Добавляйте аниме в коллекцию прямо на их страницах</p>
      <button class="empty-btn accent" @click="router.push('/anime')">Найти аниме</button>
    </div>

    <!-- ══ Карточки ════════════════════════════════════════════ -->
    <div v-else class="cards-grid">
      <CollectionCard
        v-for="item in items"
        :key="item.id"
        :item="item"
        @status-changed="onStatusChanged"
        @deleted="onDeleted"
        @rated="onRated"
      />
    </div>

    <!-- ══ Модалка редактирования ══════════════════════════════ -->
    <EditLibraryModal
      v-if="editItem"
      :item="editItem"
      @close="editItem = null"
      @saved="onSaved"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { libraryApi, type LibraryItem, type LibraryStatus, type LibraryStats, type CollectionTab } from '@/api/library'
import CollectionCard from '@/components/Cards/CollectionCard.vue'
import EditLibraryModal from '@/components/Modals/EditLibraryModal.vue'

const router = useRouter()
const route  = useRoute()

// ── Состояние ────────────────────────────────────────────────
const items      = ref<LibraryItem[]>([])
const stats      = ref<LibraryStats | null>(null)
const loading    = ref(true)
const error      = ref(false)
const searchQuery= ref('')
const ordering   = ref('-updated_at')
const editItem   = ref<LibraryItem | null>(null)
const activeTab  = ref<CollectionTab | ''>('')

// ── Вкладки ──────────────────────────────────────────────────
const tabs = [
  { key: '' as const,          label: 'Все',           icon: '📚' },
  { key: 'started' as const,   label: 'В процессе',    icon: '▶️' },
  { key: 'completed' as const, label: 'Просмотрено',   icon: '✅' },
  { key: 'planned' as const,   label: 'Запланировано', icon: '📅' },
  { key: 'on_hold' as const,   label: 'Отложено',      icon: '⏸️' },
  { key: 'dropped' as const,   label: 'Брошено',       icon: '❌' },
  { key: 'favorite' as const,  label: 'Избранное',     icon: '⭐' },
]

const currentTab = computed(() => tabs.find(t => t.key === activeTab.value))

// ── Статусные сегменты ────────────────────────────────────────
const statusSegments = computed(() => {
  if (!stats.value || !stats.value.total) return []
  const s = stats.value
  const seg = [
    { key: 'started',   label: 'В процессе',    count: s.started,   color: 'var(--accent)' },
    { key: 'completed', label: 'Просмотрено',   count: s.completed, color: '#22c55e' },
    { key: 'planned',   label: 'Запланировано', count: s.planned,   color: '#a78bfa' },
    { key: 'on_hold',   label: 'Отложено',      count: s.on_hold,   color: '#f59e0b' },
    { key: 'dropped',   label: 'Брошено',       count: s.dropped,   color: '#ef4444' },
  ]
  return seg.filter(x => x.count > 0).map(x => ({ ...x, pct: Math.max(1, Math.round(x.count / s.total * 100)) }))
})

const getStatCount = (key: string): number => {
  if (!stats.value) return 0
  if (key === '') return stats.value.total
  if (key === 'favorite') return stats.value.favorites
  return (stats.value as any)[key] ?? 0
}

const emptyMessage = computed(() => {
  const msgs: Record<string, string> = {
    '': 'Ваша коллекция пока пуста',
    started:   'Нет аниме в процессе просмотра',
    completed: 'Нет завершённых аниме',
    planned:   'Нет запланированных аниме',
    on_hold:   'Нет отложенных аниме',
    dropped:   'Нет брошенных аниме',
    favorite:  'Нет избранных аниме',
  }
  return msgs[activeTab.value] ?? 'Ничего не найдено'
})

// ── Поиск с debounce ─────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout>
const debouncedSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadItems(), 350)
}

// ── Загрузка ─────────────────────────────────────────────────
const loadItems = async () => {
  loading.value = true
  error.value = false
  try {
    const params: any = { ordering: ordering.value }
    if (activeTab.value === 'favorite') {
      params.is_favorite = true
    } else if (activeTab.value) {
      params.status = activeTab.value
    }
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    items.value = await libraryApi.getLibrary(params)
  } catch (e) {
    console.error(e)
    error.value = true
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    stats.value = await libraryApi.getStatistics()
  } catch (e) {
    console.error('Ошибка статистики', e)
  }
}

const setTab = (key: CollectionTab | '') => {
  activeTab.value = key
  loadItems()
  // Обновляем query param для bookmark
  router.replace({ query: key ? { status: key } : {} })
}

// ── Callbacks от карточек ────────────────────────────────────
const onStatusChanged = () => {
  loadItems()
  loadStats()
}

const onDeleted = () => {
  loadItems()
  loadStats()
}

const onRated = () => {
  loadItems()
}

const onSaved = () => {
  editItem.value = null
  loadItems()
  loadStats()
}

// ── Инициализация ─────────────────────────────────────────────
onMounted(() => {
  // Читаем статус из URL если есть
  const statusParam = route.query.status as string
  if (statusParam && tabs.find(t => t.key === statusParam)) {
    activeTab.value = statusParam as LibraryStatus
  }
  loadStats()
  loadItems()
})
</script>

<style scoped>
/* ═══ Страница ══════════════════════════════════════════════ */
.collection-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* ═══ Шапка ═════════════════════════════════════════════════ */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-3xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.025em;
}

.title-icon { font-size: 28px; line-height: 1; }

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

/* ── Поиск ────────────────────────────────────────────── */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-tertiary);
  pointer-events: none;
  flex-shrink: 0;
}

.search-input {
  height: 38px;
  padding: 0 36px 0 36px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: var(--text-sm);
  width: 240px;
  transition: border-color var(--duration-base), width var(--duration-base);
  outline: none;
}

.search-input:focus {
  border-color: var(--accent);
  width: 280px;
}

.search-input::placeholder { color: var(--text-tertiary); }

.search-clear {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 2px;
  border-radius: 3px;
}

.search-clear:hover { color: var(--text-primary); }

.sort-select {
  height: 38px;
  padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  outline: none;
}

/* ═══ Статистика-табы ════════════════════════════════════════ */
.stats-bar {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  user-select: none;
}

.stat-chip:hover {
  background: var(--surface-4);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.stat-chip.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.stat-icon { font-size: 14px; line-height: 1; }
.stat-label { font-weight: 500; }
.stat-num {
  background: var(--surface-5);
  border-radius: var(--radius-full);
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-tertiary);
}

.stat-chip.active .stat-num {
  background: var(--accent);
  color: white;
}

.skeleton-chip {
  width: 110px;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  pointer-events: none;
}

/* ═══ Сводная статистика ════════════════════════════════════ */
.summary-block {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.summary-numbers {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-val {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.025em;
  line-height: 1;
}

.summary-key {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-divider {
  width: 1px;
  height: 40px;
  background: var(--border-subtle);
}

.summary-bar {
  display: flex;
  height: 8px;
  border-radius: var(--radius-full);
  overflow: hidden;
  gap: 2px;
}

.summary-bar-seg {
  border-radius: var(--radius-full);
  transition: flex var(--duration-slow);
}

.summary-legend {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ═══ Скелетоны карточек ════════════════════════════════════ */
.grid-skeleton,
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
  gap: var(--space-5);
}

.card-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.skel-poster {
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.skel-body { display: flex; flex-direction: column; gap: 6px; padding: 4px 2px; }

.skel-line {
  height: 12px;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.skel-bar {
  height: 4px;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.skel-line.w70 { width: 70%; }
.skel-line.w45 { width: 45%; }

/* ═══ Пусто / ошибка ════════════════════════════════════════ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: 80px var(--space-6);
  color: var(--text-secondary);
  text-align: center;
}

.empty-icon { font-size: 56px; line-height: 1; }
.empty-title { font-size: var(--text-xl); font-weight: 600; color: var(--text-primary); margin: 0; }
.empty-sub { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; }

.empty-btn {
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 var(--space-6);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}

.empty-btn.accent {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: transparent;
}

.empty-btn:hover { opacity: 0.85; }

/* ═══ Анимации ══════════════════════════════════════════════ */
@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

/* ═══ Адаптив ═══════════════════════════════════════════════ */
@media (max-width: 767px) {
  .collection-page { padding: var(--space-4) var(--space-3); }
  .page-header { flex-direction: column; align-items: flex-start; }
  .page-title { font-size: var(--text-2xl); }
  .header-right { width: 100%; }
  .search-input { width: 100% !important; flex: 1; }
  .search-box { flex: 1; }
  .cards-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
}
</style>
