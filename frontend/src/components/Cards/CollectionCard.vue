<template>
  <div class="col-card" :class="statusClass">

    <!-- Постер -->
    <div class="card-poster" @click="goToAnime">
      <img
        v-if="posterUrl"
        :src="posterUrl"
        :alt="item.anime_title_ru"
        class="poster-img"
        @error="posterError = true"
      />
      <div v-else class="poster-placeholder">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2"/>
          <path d="M12 2v20M2 12h20"/>
        </svg>
      </div>

      <!-- Бейдж статуса -->
      <div class="status-badge" :style="{ background: statusColor }">
        {{ statusIcon }}
      </div>

      <!-- Избранное -->
      <button
        class="fav-btn"
        :class="{ active: item.is_favorite }"
        @click.stop="toggleFavorite"
        :title="item.is_favorite ? 'Убрать из избранного' : 'В избранное'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" :fill="item.is_favorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      </button>

      <!-- Прогресс бар -->
      <div v-if="showProgress" class="progress-bar">
        <div class="progress-fill" :style="{ width: item.progress_percentage + '%' }"></div>
      </div>

      <!-- Оверлей при наведении -->
      <div class="poster-overlay">
        <button class="overlay-btn primary" @click.stop="primaryAction" :title="primaryLabel">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <polygon v-if="item.status === 'planned' || item.status === 'completed'" points="5 3 19 12 5 21 5 3"/>
            <polygon v-else points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
        <button class="overlay-btn" @click.stop="openMenu" title="Действия">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Инфо -->
    <div class="card-info">
      <h3 class="card-title" @click="goToAnime">{{ item.anime_title_ru || item.anime_title_en }}</h3>

      <!-- Прогресс (только для started / on_hold) -->
      <div v-if="showProgress" class="episode-info">
        <span class="ep-text">
          {{ item.current_episode }} / {{ item.anime_episodes_count || '?' }} эп.
        </span>
        <span class="ep-pct">{{ item.progress_percentage }}%</span>
      </div>

      <!-- Оценка -->
      <div v-if="item.rating" class="rating-row">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="var(--warning)" stroke="none">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span class="rating-val">{{ item.rating }}/10</span>
      </div>

      <!-- Дата -->
      <div class="date-row">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span class="date-text">{{ dateLabel }}</span>
      </div>

      <!-- Кнопки быстрых действий -->
      <div class="quick-actions">
        <button class="qa-btn primary" @click.stop="primaryAction" :title="primaryLabel">
          {{ primaryLabel }}
        </button>
        <button v-if="item.status === 'started'" class="qa-btn" @click.stop="markCompleted" title="Просмотрено">
          ✓
        </button>
        <button class="qa-btn menu" @click.stop="openMenu" title="Ещё">
          ⋯
        </button>
      </div>
    </div>

    <!-- Контекстное меню -->
    <Teleport to="body">
      <div v-if="menuOpen" class="ctx-backdrop" @click="menuOpen = false"></div>
      <div v-if="menuOpen" class="ctx-menu" :style="menuStyle">
        <button class="ctx-item" @click="goToAnime">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
          Страница аниме
        </button>
        <button class="ctx-item" @click="watchNow">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Смотреть
        </button>
        <div class="ctx-divider"></div>
        <template v-for="tab in statusMenuItems" :key="tab.key">
          <button
            class="ctx-item"
            :class="{ current: item.status === tab.key }"
            @click="changeStatus(tab.key)"
          >
            {{ tab.icon }} {{ tab.label }}
          </button>
        </template>
        <div class="ctx-divider"></div>
        <button class="ctx-item" @click="openEdit">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 1 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Редактировать
        </button>
        <button class="ctx-item danger" @click="deleteItem">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
          </svg>
          Удалить из коллекции
        </button>
      </div>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { libraryApi, type LibraryItem, type LibraryStatus } from '@/api/library'
import { getMediaUrl } from '@/api/client'

const props = defineProps<{ item: LibraryItem }>()
const emit = defineEmits<{
  statusChanged: []
  deleted: []
  rated: []
  edit: [item: LibraryItem]
}>()

const router = useRouter()
const menuOpen   = ref(false)
const menuStyle  = ref({})
const posterError = ref(false)

// ── Постер ────────────────────────────────────────────────────
const posterUrl = computed(() => {
  if (posterError.value || !props.item.anime_poster) return null
  return getMediaUrl(props.item.anime_poster)
})

// ── Статусы ───────────────────────────────────────────────────
const statusConfig: Record<string, { icon: string; color: string; label: string }> = {
  started:   { icon: '▶️', color: 'var(--accent)',  label: 'В процессе'    },
  completed: { icon: '✅', color: '#22c55e',          label: 'Просмотрено'   },
  planned:   { icon: '📅', color: '#a78bfa',          label: 'Запланировано' },
  on_hold:   { icon: '⏸️', color: '#f59e0b',          label: 'Отложено'      },
  dropped:   { icon: '❌', color: '#ef4444',          label: 'Брошено'       },
  favorite:  { icon: '⭐', color: '#f59e0b',          label: 'Избранное'     },
}

const statusIcon  = computed(() => statusConfig[props.item.status]?.icon  ?? '📚')
const statusColor = computed(() => statusConfig[props.item.status]?.color ?? 'var(--surface-5)')
const statusClass = computed(() => `status-${props.item.status}`)

const showProgress = computed(() =>
  props.item.status === 'started' || props.item.status === 'on_hold'
)

// ── Первичное действие ────────────────────────────────────────
const primaryLabel = computed(() => {
  if (props.item.status === 'planned')   return 'Начать'
  if (props.item.status === 'completed') return 'Пересмотреть'
  return 'Продолжить'
})

const primaryAction = () => {
  const ep = props.item.status === 'completed' ? 1 : (props.item.current_episode || 1)
  router.push(`/anime/${props.item.anime}/watch?episode=${ep}`)
}

const watchNow = () => {
  menuOpen.value = false
  primaryAction()
}

// ── Дата ──────────────────────────────────────────────────────
const dateLabel = computed(() => {
  const fmtDate = (d: string | null) => {
    if (!d) return null
    const date = new Date(d)
    const today = new Date()
    const diff  = Math.floor((today.getTime() - date.getTime()) / 86400000)
    if (diff === 0) return 'сегодня'
    if (diff === 1) return 'вчера'
    if (diff < 7)  return `${diff} дн. назад`
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
  }

  if (props.item.status === 'completed' && props.item.completed_at) {
    return 'Завершено ' + fmtDate(props.item.completed_at)
  }
  if (props.item.status === 'started' && props.item.updated_at) {
    return 'Смотрел ' + fmtDate(props.item.updated_at)
  }
  return 'Добавлено ' + (fmtDate(props.item.added_at) ?? '—')
})

// ── Меню ──────────────────────────────────────────────────────
const statusMenuItems = [
  { key: 'started'  as LibraryStatus, icon: '▶️', label: 'В процессе'    },
  { key: 'completed'as LibraryStatus, icon: '✅', label: 'Просмотрено'   },
  { key: 'planned'  as LibraryStatus, icon: '📅', label: 'Запланировано' },
  { key: 'on_hold'  as LibraryStatus, icon: '⏸️', label: 'Отложено'      },
  { key: 'dropped'  as LibraryStatus, icon: '❌', label: 'Брошено'       },
]

const openMenu = (e: MouseEvent) => {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  menuStyle.value = {
    top:  Math.min(rect.bottom + 6, window.innerHeight - 340) + 'px',
    left: Math.min(rect.left, window.innerWidth - 220) + 'px',
  }
  menuOpen.value = true
}

// ── Действия ─────────────────────────────────────────────────
const goToAnime = () => router.push(`/anime/${props.item.anime}`)

const markCompleted = async () => {
  try {
    await libraryApi.updateLibraryItem(props.item.id, { status: 'completed' })
    emit('statusChanged')
  } catch (e) { console.error(e) }
}

const changeStatus = async (status: LibraryStatus) => {
  menuOpen.value = false
  try {
    await libraryApi.updateLibraryItem(props.item.id, { status })
    emit('statusChanged')
  } catch (e) { console.error(e) }
}

const toggleFavorite = async () => {
  try {
    await libraryApi.toggleFavorite(props.item.id)
    emit('statusChanged')
  } catch (e) { console.error(e) }
}

const deleteItem = async () => {
  menuOpen.value = false
  if (!confirm(`Удалить "${props.item.anime_title_ru}" из коллекции?`)) return
  try {
    await libraryApi.deleteLibraryItem(props.item.id)
    emit('deleted')
  } catch (e) { console.error(e) }
}

const openEdit = () => {
  menuOpen.value = false
  emit('edit', props.item)
}
</script>

<style scoped>
/* ═══ Карточка ══════════════════════════════════════════════ */
.col-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: transform var(--duration-slow) var(--ease-out);
}

.col-card:hover { transform: translateY(-3px); }

/* ═══ Постер ════════════════════════════════════════════════ */
.card-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  cursor: pointer;
}

.poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.col-card:hover .poster-img { transform: scale(1.05); }

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* ── Статус-бейдж ─────────────────────────────────────────── */
.status-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 14px;
  line-height: 1;
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

/* ── Избранное ───────────────────────────────────────────────  */
.fav-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.55);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--duration-base), color var(--duration-base);
  backdrop-filter: blur(4px);
}

.col-card:hover .fav-btn { opacity: 1; }
.fav-btn.active { color: #f59e0b; opacity: 1; }

/* ── Прогресс ────────────────────────────────────────────────  */
.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0,0,0,0.4);
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}

/* ── Оверлей ─────────────────────────────────────────────────  */
.poster-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity var(--duration-base);
}

.col-card:hover .poster-overlay { opacity: 1; }

.overlay-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background var(--duration-base), transform var(--duration-base);
}

.overlay-btn:hover { background: rgba(255,255,255,0.3); transform: scale(1.1); }
.overlay-btn.primary {
  background: var(--accent);
  width: 48px;
  height: 48px;
  padding-left: 3px;
}
.overlay-btn.primary:hover { background: var(--accent-hover); }

/* ═══ Инфо ══════════════════════════════════════════════════ */
.card-info {
  padding: 0 2px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
  cursor: pointer;
}

.card-title:hover { color: var(--accent); }

.episode-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.ep-text { font-size: var(--text-xs); color: var(--text-secondary); }
.ep-pct  { font-size: 10px; color: var(--accent); font-weight: 600; }

.rating-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-val { font-size: var(--text-xs); color: var(--warning); font-weight: 600; }

.date-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.date-text {
  font-size: 10px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Быстрые действия ────────────────────────────────────────  */
.quick-actions {
  display: flex;
  gap: 4px;
  margin-top: 2px;
}

.qa-btn {
  flex: 1;
  height: 28px;
  padding: 0 var(--space-2);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qa-btn.primary {
  background: var(--accent-subtle);
  border-color: transparent;
  color: var(--accent);
  font-weight: 600;
}

.qa-btn.menu { flex: 0 0 28px; padding: 0; }
.qa-btn:hover { background: var(--surface-5); color: var(--text-primary); }
.qa-btn.primary:hover { background: var(--accent); color: white; }

/* ═══ Контекстное меню ══════════════════════════════════════ */
.ctx-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
}

.ctx-menu {
  position: fixed;
  z-index: 1001;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-1);
  min-width: 200px;
  box-shadow: var(--shadow-lg);
  animation: menu-in 0.12s var(--ease-out);
}

@keyframes menu-in {
  from { opacity: 0; transform: scale(0.95) translateY(-4px); }
  to   { opacity: 1; transform: none; }
}

.ctx-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  height: 36px;
  padding: 0 var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  transition: all var(--duration-base);
}

.ctx-item:hover { background: var(--surface-4); color: var(--text-primary); }
.ctx-item.current { color: var(--accent); background: var(--accent-subtle); }
.ctx-item.danger  { color: var(--danger); }
.ctx-item.danger:hover { background: rgba(239,68,68,0.1); }

.ctx-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: var(--space-1) 0;
}
</style>
