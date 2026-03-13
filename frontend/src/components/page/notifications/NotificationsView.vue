<template>
  <div class="notif-page">
    <div class="notif-container">

      <!-- Заголовок -->
      <div class="page-header">
        <h1>🔔 Уведомления</h1>
        <div class="header-actions">
          <router-link to="/notifications/settings" class="btn-action btn-dim" title="Настройки">⚙️ Настройки</router-link>
          <button
            v-if="store.unreadCount > 0"
            class="btn-action btn-green"
            @click="handleMarkAllRead"
            :disabled="store.loading"
          >
            ✓ Все прочитано
          </button>
          <button
            class="btn-action btn-dim"
            @click="handleCleanRead"
            title="Удалить все прочитанные"
          >
            🗑 Прочитанные
          </button>
          <button
            class="btn-action btn-danger"
            @click="confirmDeleteAll"
            title="Удалить все (кроме важных)"
          >
            🗑 Все
          </button>
        </div>
      </div>

      <!-- Диалог подтверждения -->
      <div v-if="showDeleteConfirm" class="confirm-overlay" @click.self="showDeleteConfirm = false">
        <div class="confirm-box">
          <p>Удалить все уведомления? Важные (⭐) сохранятся.</p>
          <div class="confirm-btns">
            <button class="btn-action btn-danger" @click="executeDeleteAll">Удалить</button>
            <button class="btn-action btn-dim" @click="showDeleteConfirm = false">Отмена</button>
          </div>
        </div>
      </div>

      <!-- Табы -->
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.key"
          :class="['tab', { active: activeTab === t.key }]"
          @click="switchTab(t.key)"
        >
          {{ t.label }}
          <span v-if="t.key === 'unread' && store.unreadCount > 0" class="tab-badge">
            {{ store.unreadCount }}
          </span>
          <span v-if="t.key === 'reminders' && activeRemindersCount > 0" class="tab-badge reminder">
            {{ activeRemindersCount }}
          </span>
        </button>
      </div>

      <!-- Фильтры типов (только для уведомлений) -->
      <div v-if="activeTab !== 'reminders'" class="filter-bar">
        <button
          v-for="f in notificationFilters"
          :key="f.key"
          :class="['filter-btn', { active: activeFilter === f.key }]"
          @click="activeFilter = f.key"
        >
          {{ f.icon }} {{ f.label }}
        </button>
      </div>

      <!-- Контент -->
      <div class="content-box" ref="contentRef">

        <div v-if="store.loading && shownList.length === 0" class="state-empty">
          <div class="spinner" />
          <p>Загрузка...</p>
        </div>

        <div v-else-if="shownList.length === 0" class="state-empty">
          <div class="empty-icon">{{ activeTab === 'reminders' ? '⏰' : '🔔' }}</div>
          <h3>{{ emptyLabel }}</h3>
          <p>{{ emptyHint }}</p>
        </div>

        <div v-else class="notif-list">

          <!-- ═══ Напоминания ═══ -->
          <template v-if="activeTab === 'reminders'">
            <div
              v-for="r in store.reminders"
              :key="`rem-${r.id}`"
              :class="['notif-row', 'reminder-row', {
                inactive: !r.is_active,
                'reminder-ringing': store.ringingReminderIds.has(r.id)
              }]"
            >
              <div class="notif-avatar" style="background: rgba(245,158,11,0.15)">
                <span class="avatar-icon">⏰</span>
              </div>

              <div class="notif-body">
                <div class="notif-top">
                  <router-link :to="`/anime/${r.anime_detail?.id}`" class="notif-title-link">
                    {{ r.anime_detail?.title_ru || 'Аниме' }}
                  </router-link>
                  <span v-if="r.repeat_weekly" class="badge badge-weekly">еженедельно</span>
                  <span v-if="!r.is_active" class="badge badge-off">выкл</span>
                </div>
                <p class="notif-text" v-if="r.comment">{{ r.comment }}</p>
                <div class="notif-meta">
                  <span class="notif-time">🗓 {{ formatDateTime(r.reminder_time) }}</span>
                  <span class="notif-time">{{ formatTimeAgo(r.reminder_time) }}</span>
                </div>
              </div>

              <div class="notif-actions">
                <router-link :to="`/anime/${r.anime_detail?.id}/watch`" class="action-btn watch-btn" title="Смотреть">▶</router-link>
                <button
                  v-if="r.is_active"
                  class="action-btn deact-btn"
                  @click="store.deactivateReminder(r.id)"
                  title="Деактивировать"
                >✕</button>
                <button
                  class="action-btn del-btn"
                  @click="store.deleteReminder(r.id)"
                  title="Удалить"
                >🗑</button>
              </div>
            </div>
          </template>

          <!-- ═══ Уведомления ═══ -->
          <template v-else>
            <!-- Группировка по дате -->
            <template v-for="group in groupedList" :key="group.label">
              <div class="date-separator">{{ group.label }}</div>
              <div
                v-for="n in group.items"
                :key="n.id"
                :class="['notif-row', { unread: !n.is_read, important: n.is_important }]"
                @click="handleNotifClick(n)"
              >
                <div class="notif-avatar" :style="iconStyle(n.type)">
                  <span class="avatar-icon">{{ n.icon || getIcon(n.type) }}</span>
                </div>

                <div class="notif-body">
                  <div class="notif-top">
                    <p class="notif-title">{{ n.title }}</p>
                    <span v-if="!n.is_read" class="unread-dot" />
                    <span v-if="n.is_important" class="star-badge" title="Важное">⭐</span>
                  </div>
                  <p v-if="n.content" class="notif-text">{{ n.content }}</p>
                  <span class="notif-time">{{ formatTimeAgo(n.created_at) }}</span>
                </div>

                <div class="notif-actions" @click.stop>
                  <button
                    v-if="!n.is_read"
                    class="action-btn read-btn"
                    @click.stop="store.markRead(n.id)"
                    title="Отметить прочитанным"
                  >✓</button>
                  <button
                    class="action-btn star-btn"
                    :class="{ 'is-important': n.is_important }"
                    @click.stop="store.toggleImportant(n.id)"
                    title="Важное"
                  >⭐</button>
                  <button
                    class="action-btn del-btn"
                    @click.stop="store.deleteNotification(n.id)"
                    title="Удалить"
                  >🗑</button>
                </div>
              </div>
            </template>

            <!-- Загрузка ещё -->
            <div v-if="store.loadingMore" class="loading-more">
              <div class="spinner small" />
              <span>Загрузка...</span>
            </div>
            <div v-else-if="store.hasMore && filteredList.length > 0" class="load-more-btn">
              <button @click="loadMore">Загрузить ещё</button>
            </div>
            <div v-else-if="filteredList.length > 0 && !store.hasMore" class="end-of-list">
              Все уведомления загружены
            </div>
          </template>

        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNotificationStore } from '@/stores/notifications'
import type { NotificationItem } from '@/api/notifications'

const store  = useNotificationStore()
const router = useRouter()
const route  = useRoute()

const activeTab    = ref<'all' | 'unread' | 'important' | 'reminders'>('all')
const activeFilter = ref<string>('all')
const showDeleteConfirm = ref(false)
const contentRef = ref<HTMLElement | null>(null)

const tabs = [
  { key: 'all',       label: 'Все' },
  { key: 'unread',    label: 'Непрочитанные' },
  { key: 'important', label: 'Важные' },
  { key: 'reminders', label: 'Напоминания' },
] as const

const notificationFilters = [
  { key: 'all',             icon: '🔔', label: 'Все' },
  { key: 'like',            icon: '❤️', label: 'Лайки' },
  { key: 'comment',         icon: '💬', label: 'Комментарии' },
  { key: 'follow',          icon: '👥', label: 'Подписки' },
  { key: 'mention',         icon: '@',  label: 'Упоминания' },
  { key: 'contest_win',     icon: '👑', label: 'Конкурсы' },
  { key: 'system',          icon: '⚙️', label: 'Системные' },
  { key: 'warning',         icon: '⚠️', label: 'Предупреждения' },
]

const activeRemindersCount = computed(() =>
  store.reminders.filter(r => r.is_active).length
)

// Фильтрованный список уведомлений
const filteredList = computed(() => {
  let list = store.notifications

  if (activeTab.value === 'unread')    list = list.filter(n => !n.is_read)
  if (activeTab.value === 'important') list = list.filter(n => n.is_important)

  if (activeFilter.value !== 'all') {
    list = list.filter(n => {
      if (activeFilter.value === 'contest_win') {
        return ['contest', 'contest_vote', 'contest_results', 'contest_win'].includes(n.type)
      }
      return n.type === activeFilter.value
    })
  }

  return list
})

// Группировка по дате
const groupedList = computed(() => {
  const groups: { label: string; items: NotificationItem[] }[] = []
  const today     = new Date(); today.setHours(0,0,0,0)
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)

  const todayItems:     NotificationItem[] = []
  const yesterdayItems: NotificationItem[] = []
  const olderItems:     NotificationItem[] = []

  for (const n of filteredList.value) {
    const d = new Date(n.created_at)
    d.setHours(0,0,0,0)
    if (d.getTime() === today.getTime())     todayItems.push(n)
    else if (d.getTime() === yesterday.getTime()) yesterdayItems.push(n)
    else olderItems.push(n)
  }

  if (todayItems.length)     groups.push({ label: 'Сегодня',  items: todayItems })
  if (yesterdayItems.length) groups.push({ label: 'Вчера',    items: yesterdayItems })
  if (olderItems.length)     groups.push({ label: 'Ранее',    items: olderItems })

  return groups
})

const shownList = computed(() => {
  if (activeTab.value === 'reminders') return store.reminders as any[]
  return filteredList.value as any[]
})

const emptyLabel = computed(() => {
  if (activeTab.value === 'reminders') return 'Нет напоминаний'
  if (activeTab.value === 'unread')    return 'Всё прочитано'
  if (activeTab.value === 'important') return 'Нет важных'
  return 'Нет уведомлений'
})
const emptyHint = computed(() => {
  if (activeTab.value === 'reminders') return 'Добавляйте напоминания на страницах аниме'
  if (activeTab.value === 'unread')    return 'Новые уведомления появятся здесь'
  if (activeTab.value === 'important') return 'Помечайте уведомления звёздочкой ⭐'
  return 'Когда появятся уведомления, они будут здесь'
})

// ── Handlers ──────────────────────────────────────────────────────

const switchTab = async (tab: string) => {
  activeTab.value = tab as any
  activeFilter.value = 'all'
  if (tab === 'reminders') {
    await store.fetchReminders()
  } else {
    await store.fetchNotifications(true)
  }
}

const handleNotifClick = (n: NotificationItem) => {
  if (!n.is_read) store.markRead(n.id)
  if (n.link) router.push(n.link)
}

const handleMarkAllRead  = () => store.markAllRead()
const handleCleanRead    = () => store.cleanReadNotifications()
const confirmDeleteAll   = () => { showDeleteConfirm.value = true }
const executeDeleteAll   = async () => {
  showDeleteConfirm.value = false
  await store.deleteAllNotifications()
}

const loadMore = () => store.loadMoreNotifications()

// Бесконечный скролл
let scrollTimeout: ReturnType<typeof setTimeout> | null = null
const handleScroll = () => {
  if (scrollTimeout) clearTimeout(scrollTimeout)
  scrollTimeout = setTimeout(() => {
    if (store.loadingMore || !store.hasMore) return
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement
    if (scrollTop + clientHeight >= scrollHeight - 200) loadMore()
  }, 100)
}

// ── Icons / Colors ─────────────────────────────────────────────────

const ICONS: Record<string, string> = {
  like: '❤️', dislike: '👎', heart: '💖',
  comment: '💬', reply: '↩️', mention: '@',
  follow: '👥', repost: '🔁',
  message: '✉️', group_message: '👥', group_invite: '📨',
  achievement: '🏆', contest: '🏅', contest_vote: '🗳️',
  contest_results: '📊', contest_win: '👑',
  reminder_episode: '⏰', reminder_event: '📅', reminder_contest: '⏳',
  system: '⚙️', warning: '⚠️', security: '🔒',
}
const COLORS: Record<string, string> = {
  like: 'rgba(244,67,54,0.15)',    dislike: 'rgba(158,158,158,0.15)',
  heart: 'rgba(236,72,153,0.15)',  comment: 'rgba(33,150,243,0.15)',
  reply: 'rgba(33,150,243,0.15)',  mention: 'rgba(255,152,0,0.15)',
  follow: 'rgba(76,175,80,0.15)',  repost: 'rgba(156,39,176,0.15)',
  message: 'rgba(0,188,212,0.15)', achievement: 'rgba(255,193,7,0.15)',
  contest_win: 'rgba(255,193,7,0.15)', warning: 'rgba(245,158,11,0.15)',
  security: 'rgba(239,68,68,0.15)', system: 'rgba(96,125,139,0.15)',
}

const getIcon   = (type: string) => ICONS[type] || '🔔'
const iconStyle = (type: string) => ({ background: COLORS[type] || 'rgba(102,126,234,0.15)' })

// ── Date formatting ────────────────────────────────────────────────

const normalizeDate = (raw: string): Date | null => {
  if (!raw) return null
  const s = raw.includes('Z') || raw.includes('+') || /T.*-\d{2}:\d{2}$/.test(raw)
    ? raw : raw.replace(' ', 'T') + 'Z'
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

const formatTimeAgo = (raw: string): string => {
  const d = normalizeDate(raw)
  if (!d) return ''
  const diff = Math.floor((Date.now() - d.getTime()) / 1000)
  if (diff < 60)     return 'только что'
  if (diff < 3600)   return `${Math.floor(diff / 60)} мин. назад`
  if (diff < 86400)  return `${Math.floor(diff / 3600)} ч. назад`
  if (diff < 604800) return `${Math.floor(diff / 86400)} дн. назад`
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const formatDateTime = (raw: string): string => {
  const d = normalizeDate(raw)
  if (!d) return ''
  return d.toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  // Читаем query-параметр tab (например, переход из дропдауна по клику на напоминание)
  const queryTab = route.query.tab as string | undefined
  const validTabs = ['all', 'unread', 'important', 'reminders']
  if (queryTab && validTabs.includes(queryTab)) {
    activeTab.value = queryTab as any
  }

  if (activeTab.value === 'reminders') {
    await store.fetchReminders()
  } else {
    store.fetchNotifications(true)
    store.fetchReminders() // загружаем фоном для счётчика таба
  }

  window.addEventListener('scroll', handleScroll)
})
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  if (scrollTimeout) clearTimeout(scrollTimeout)
})
</script>

<style scoped>
.notif-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
  color: #fff;
  padding: 2rem 1.5rem;
}

.notif-container {
  max-width: 740px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ── Заголовок ─────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.page-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 800;
}
.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.btn-action {
  padding: .45rem 1rem;
  border-radius: 10px;
  font-size: .82rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all .2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: .35rem;
}
.btn-green {
  border-color: rgba(34,197,94,0.4);
  background: rgba(34,197,94,0.1);
  color: #22c55e;
}
.btn-green:hover { background: rgba(34,197,94,0.2); }
.btn-dim {
  border-color: rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.06);
  color: #9ca3af;
}
.btn-dim:hover { color: #d1d5db; }
.btn-danger {
  border-color: rgba(239,68,68,0.4);
  background: rgba(239,68,68,0.08);
  color: #ef4444;
}
.btn-danger:hover { background: rgba(239,68,68,0.18); }
.btn-action:disabled { opacity: .5; cursor: not-allowed; }

/* ── Подтверждение удаления ─────────────────────────────── */
.confirm-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.confirm-box {
  background: #1e1e30;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  padding: 1.5rem 2rem;
  max-width: 340px;
  text-align: center;
}
.confirm-box p { margin: 0 0 1rem; color: #d1d5db; }
.confirm-btns { display: flex; gap: .75rem; justify-content: center; }

/* ── Табы ───────────────────────────────────────────────── */
.tabs {
  display: flex;
  gap: .4rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: .35rem;
}
.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .35rem;
  padding: .5rem .6rem;
  border: none;
  background: transparent;
  border-radius: 9px;
  color: #6b7280;
  font-size: .855rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
}
.tab:hover { color: #d1d5db; }
.tab.active { background: rgba(59,130,246,0.2); color: #3b82f6; font-weight: 700; }
.tab-badge {
  padding: 1px 6px;
  background: #3b82f6;
  color: #fff;
  border-radius: 8px;
  font-size: .7rem;
  font-weight: 700;
}
.tab-badge.reminder { background: #f59e0b; }

/* ── Фильтры ────────────────────────────────────────────── */
.filter-bar {
  display: flex;
  gap: .4rem;
  flex-wrap: wrap;
}
.filter-btn {
  padding: .3rem .7rem;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: #6b7280;
  font-size: .78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
}
.filter-btn:hover { border-color: rgba(255,255,255,0.18); color: #d1d5db; }
.filter-btn.active {
  background: rgba(59,130,246,0.15);
  border-color: rgba(59,130,246,0.3);
  color: #3b82f6;
}

/* ── Контент ────────────────────────────────────────────── */
.content-box {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  overflow: hidden;
}

/* ── Пусто / загрузка ───────────────────────────────────── */
.state-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .75rem;
  padding: 4rem 2rem;
  color: #6b7280;
  text-align: center;
}
.empty-icon { font-size: 3rem; }
.state-empty h3 { margin: 0; font-size: 1.2rem; color: #9ca3af; }
.state-empty p  { margin: 0; font-size: .88rem; }
.spinner {
  width: 32px; height: 32px;
  border: 3px solid rgba(255,255,255,0.08);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
.spinner.small { width: 20px; height: 20px; border-width: 2px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Список ─────────────────────────────────────────────── */
.notif-list { display: flex; flex-direction: column; }

.date-separator {
  padding: .5rem 1.25rem;
  font-size: .72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #4b5563;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  background: rgba(0,0,0,0.15);
}

/* ── Строка ─────────────────────────────────────────────── */
.notif-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: .9rem 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  cursor: pointer;
  position: relative;
  transition: background .15s;
}
.notif-row:last-child { border-bottom: none; }
.notif-row:hover { background: rgba(255,255,255,0.03); }

.notif-row.unread {
  background: rgba(59,130,246,0.05);
}
.notif-row.unread::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
}
.notif-row.important {
  background: rgba(245,158,11,0.04);
}
.notif-row.important::before {
  background: #f59e0b;
}
.notif-row.reminder-row {
  background: rgba(245,158,11,0.03);
  cursor: default;
}
.notif-row.inactive { opacity: .45; }

/* Сверкающая строка напоминания */
.notif-row.reminder-ringing {
  animation: reminder-row-flash 0.7s ease-in-out infinite;
}
.notif-row.reminder-ringing::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: #f59e0b;
  border-radius: 0 2px 2px 0;
  animation: reminder-bar-flash 0.7s ease-in-out infinite;
}
@keyframes reminder-row-flash {
  0%, 100% { background: rgba(245,158,11,0.03); }
  50%       { background: rgba(245,158,11,0.15); }
}
@keyframes reminder-bar-flash {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 1; }
}

/* ── Аватар ─────────────────────────────────────────────── */
.notif-avatar {
  width: 40px; height: 40px;
  flex-shrink: 0;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.avatar-icon { font-size: 1.15rem; }

/* ── Тело ───────────────────────────────────────────────── */
.notif-body { flex: 1; min-width: 0; }
.notif-top {
  display: flex;
  align-items: center;
  gap: .4rem;
  margin-bottom: 2px;
  flex-wrap: wrap;
}
.notif-title {
  margin: 0;
  font-size: .875rem;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-title-link { color: inherit; text-decoration: none; }
.notif-title-link:hover { color: #3b82f6; }
.unread-dot {
  width: 7px; height: 7px;
  background: #3b82f6;
  border-radius: 50%;
  flex-shrink: 0;
}
.star-badge { font-size: .85rem; flex-shrink: 0; }
.notif-text {
  margin: 0 0 4px;
  font-size: .82rem;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-meta { display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; }
.notif-time { font-size: .73rem; color: #4b5563; }

.badge {
  padding: 1px 7px;
  border-radius: 6px;
  font-size: .7rem;
  font-weight: 600;
  flex-shrink: 0;
}
.badge-weekly { background: rgba(59,130,246,0.15); color: #3b82f6; }
.badge-off    { background: rgba(156,163,175,0.15); color: #9ca3af; }

/* ── Кнопки действий ────────────────────────────────────── */
.notif-actions {
  display: flex;
  gap: .35rem;
  align-items: center;
  flex-shrink: 0;
}
.action-btn {
  width: 29px; height: 29px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.04);
  color: #6b7280;
  font-size: .78rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all .15s;
}
.action-btn:hover { border-color: rgba(255,255,255,0.2); color: #d1d5db; }
.read-btn:hover  { background: rgba(34,197,94,0.15); color: #22c55e; border-color: rgba(34,197,94,0.3); }
.del-btn:hover   { background: rgba(239,68,68,0.15);  color: #ef4444; border-color: rgba(239,68,68,0.3); }
.deact-btn:hover { background: rgba(245,158,11,0.15); color: #f59e0b; border-color: rgba(245,158,11,0.3); }
.watch-btn:hover { background: rgba(59,130,246,0.15); color: #3b82f6; border-color: rgba(59,130,246,0.3); }
.star-btn        { font-size: .75rem; }
.star-btn.is-important { background: rgba(245,158,11,0.15); border-color: rgba(245,158,11,0.3); color: #f59e0b; }

/* ── Загрузка ещё / конец ───────────────────────────────── */
.loading-more,
.load-more-btn,
.end-of-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  padding: 1.5rem;
  color: #6b7280;
  font-size: .875rem;
}
.load-more-btn button {
  padding: .45rem 1.5rem;
  border-radius: 8px;
  border: 1px solid rgba(59,130,246,0.3);
  background: rgba(59,130,246,0.1);
  color: #3b82f6;
  font-size: .875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
}
.load-more-btn button:hover { background: rgba(59,130,246,0.2); }
.end-of-list { font-size: .78rem; color: #4b5563; border-top: 1px solid rgba(255,255,255,0.05); }

/* ── Адаптив ────────────────────────────────────────────── */
@media (max-width: 640px) {
  .notif-page { padding: 1rem; }
  .page-header h1 { font-size: 1.4rem; }
  .notif-row { padding: .8rem 1rem; }
  .tabs { gap: .2rem; }
  .tab { font-size: .78rem; padding: .4rem .45rem; }
  .filter-bar { gap: .3rem; }
  .filter-btn { font-size: .73rem; padding: .28rem .55rem; }
  .header-actions { gap: .35rem; }
  .btn-action { padding: .38rem .75rem; font-size: .78rem; }
}
</style>
