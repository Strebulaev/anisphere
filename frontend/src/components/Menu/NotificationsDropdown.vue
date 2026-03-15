<template>
  <div class="notif-wrap" ref="wrapRef">

    <!-- Кнопка колокольчик -->
    <button :class="['bell-btn', { ringing: store.isBellRinging }]" @click="toggle">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span v-if="store.unreadCount > 0" class="bell-badge">
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
    </button>

    <!-- Дропдаун -->
    <Transition name="dropdown">
      <div v-if="open" class="dropdown">

        <!-- Хедер -->
        <div class="dh">
          <span class="dh-title">Уведомления</span>
          <div class="dh-actions">
            <button class="dh-btn" @click="store.markAllRead()" title="Все прочитано">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Прочитать все
            </button>
          </div>
        </div>

        <!-- Табы -->
        <div class="tabs">
          <button
            v-for="t in tabs" :key="t.key"
            :class="['tab', { active: activeTab === t.key }]"
            @click="activeTab = t.key"
          >
            {{ t.label }}
            <span v-if="t.key === 'unread' && store.unreadCount > 0" class="tab-badge">
              {{ store.unreadCount }}
            </span>
          </button>
        </div>

        <!-- Список -->
        <div class="list">
          <div v-if="store.loading" class="list-empty">
            <div class="spinner" />
          </div>

          <template v-else-if="shownItems.length > 0">
            <!-- Напоминания (только на вкладке "все") -->
            <template v-if="activeTab === 'all' && store.upcomingReminders.length > 0">
              <div class="section-label">⏰ Напоминания</div>
              <div
                v-for="r in store.upcomingReminders"
                :key="`rem-${r.id}`"
                :class="['notif-item reminder-item', { 
                  flashing: store.isReminderRinging(r.id),
                  triggered: r.is_triggered 
                }]"
                @click="goToAnime(r)"
              >
                <div class="notif-icon" :style="store.isReminderRinging(r.id) ? 'background: rgba(239,68,68,0.2); color: #ef4444;' : r.is_triggered ? 'background: rgba(107,114,128,0.2); color: #6b7280;' : 'background: rgba(245,158,11,0.2); color: #f59e0b;'">
                  {{ store.isReminderRinging(r.id) ? '🔔' : r.is_triggered ? '🔔' : '⏰' }}
                </div>
                <div class="notif-body">
                  <p class="notif-title">{{ store.isReminderRinging(r.id) ? '⏰ Сработало напоминание!' : r.is_triggered ? 'Напоминание сработало' : 'Напоминание о просмотре' }}</p>
                  <p class="notif-text">
                    {{ r.anime_detail?.title_ru || 'Аниме' }}
                    <span v-if="r.comment"> — {{ r.comment }}</span>
                  </p>
                  <span class="notif-time">{{ formatTime(r.reminder_time) }}</span>
                </div>
                <button v-if="!r.is_triggered && !store.isReminderRinging(r.id)" class="notif-del" @click.stop="store.deactivateReminder(r.id)" title="Отклонить">✕</button>
              </div>
              <div class="section-label">🔔 Уведомления</div>
            </template>

            <!-- Обычные уведомления -->
            <div
              v-for="n in filteredNotifications"
              :key="n.id"
              :class="['notif-item', { unread: !n.is_read, flashing: n.is_flashing }]"
              @click="handleClick(n)"
            >
              <div class="notif-icon" :style="iconStyle(n.type)">{{ getIcon(n.type) }}</div>
              <div class="notif-body">
                <p class="notif-title">{{ n.title }}</p>
                <p class="notif-text">{{ n.content }}</p>
                <span class="notif-time">{{ formatTime(n.created_at) }}</span>
              </div>
              <button class="notif-del" @click.stop="store.deleteNotification(n.id)" title="Удалить">✕</button>
            </div>
          </template>

          <div v-else class="list-empty">
            <span>{{ activeTab === 'unread' ? 'Нет непрочитанных' : 'Нет уведомлений' }}</span>
          </div>
        </div>

        <!-- Футер -->
        <router-link to="/notifications" class="dfoot" @click="open = false">
          Все уведомления →
        </router-link>

      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notifications'
import type { Notification, Reminder } from '@/stores/notifications'

const store  = useNotificationStore()
const router = useRouter()

const open      = ref(false)
const wrapRef   = ref<HTMLElement | null>(null)
const activeTab = ref<'all' | 'unread'>('all')

const tabs: { key: 'all' | 'unread'; label: string }[] = [
  { key: 'all',    label: 'Все' },
  { key: 'unread', label: 'Непрочитанные' },
]

// Объединяем уведомления и напоминания для счётчика "показываемых"
const filteredNotifications = computed(() =>
  activeTab.value === 'unread'
    ? store.notifications.filter(n => !n.is_read)
    : store.notifications
)

const shownItems = computed(() => [
  ...store.upcomingReminders,
  ...filteredNotifications.value,
])

const toggle = () => {
  open.value = !open.value
  if (open.value) {
    // Загружаем уведомления, если пусто
    if (store.notifications.length === 0) {
      store.fetchNotifications()
    }
    // Загружаем напоминания, если пусто
    if (store.reminders.length === 0) {
      store.fetchReminders()
    }
  }
}

const handleClick = async (n: Notification) => {
  if (!n.is_read) await store.markRead(n.id)
  open.value = false
}

const goToAnime = (r: Reminder) => {
  // Останавливаем сверкание при клике и помечаем как просмотренное
  store.acknowledgeReminder(r.id)
  if (r.anime_detail?.id) router.push(`/anime/${r.anime_detail.id}`)
  open.value = false
}

// ── Форматирование времени (без "Invalid Date") ──────────
const formatTime = (raw: string | null | undefined): string => {
  if (!raw) return ''
  // Нормализуем строку: добавляем Z если нет timezone
  const normalized = raw.includes('Z') || raw.includes('+') || raw.includes('-', 10)
    ? raw
    : raw + 'Z'
  const date = new Date(normalized)
  if (isNaN(date.getTime())) return raw

  const diff = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diff < 60)       return 'только что'
  if (diff < 3600)     return `${Math.floor(diff / 60)} мин. назад`
  if (diff < 86400)    return `${Math.floor(diff / 3600)} ч. назад`
  if (diff < 604800)   return `${Math.floor(diff / 86400)} дн. назад`
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

// ── Иконки и цвета ───────────────────────────────────────
const ICONS: Record<string, string> = {
  like: '❤️', dislike: '👎', comment: '💬', mention: '@',
  follow: '👥', repost: '🔁', message: '✉️', group_message: '👥',
  achievement: '🏆', contest: '🏅', system: '⚙️', group_invite: '📨',
  reminder_episode: '🔔', reminder_event: '📅', reminder_contest: '⏳',
}
const COLORS: Record<string, string> = {
  like: 'rgba(244,67,54,0.2)', dislike: 'rgba(158,158,158,0.2)',
  comment: 'rgba(33,150,243,0.2)', mention: 'rgba(255,152,0,0.2)',
  follow: 'rgba(76,175,80,0.2)', repost: 'rgba(156,39,176,0.2)',
  message: 'rgba(0,188,212,0.2)', achievement: 'rgba(255,193,7,0.2)',
  system: 'rgba(96,125,139,0.2)', reminder_episode: 'rgba(245,158,11,0.2)',
}
const TEXT_COLORS: Record<string, string> = {
  like: '#f44336', dislike: '#9e9e9e', comment: '#2196f3', mention: '#ff9800',
  follow: '#4caf50', repost: '#9c27b0', message: '#00bcd4',
  achievement: '#ffc107', system: '#607d8b', reminder_episode: '#f59e0b',
}

const getIcon  = (type: string) => ICONS[type] || '🔔'
const iconStyle = (type: string) => ({
  background: COLORS[type] || 'rgba(102,126,234,0.2)',
  color: TEXT_COLORS[type] || '#667eea',
})

// ── Клик вне компонента ──────────────────────────────────
const onOutsideClick = (e: MouseEvent) => {
  if (wrapRef.value && !wrapRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

// ── Polling напоминаний каждые 30 сек ────────────────────
let pollTimer: ReturnType<typeof setInterval> | null = null
let triggerTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  document.addEventListener('click', onOutsideClick)
  store.fetchNotifications()
  store.fetchReminders()

  // Сразу проверяем сработавшие напоминания
  store.checkAndTriggerReminders()

  // Проверка срабатывания напоминаний каждые 10 сек
  triggerTimer = setInterval(() => {
    store.checkAndTriggerReminders()
  }, 10_000)

  // Обновление уведомлений каждую минуту
  pollTimer = setInterval(() => {
    store.fetchRecent()
  }, 60_000)
})

onUnmounted(() => {
  document.removeEventListener('click', onOutsideClick)
  if (pollTimer) clearInterval(pollTimer)
  if (triggerTimer) clearInterval(triggerTimer)
})
</script>

<style scoped>
.notif-wrap { position: relative; }

/* Кнопка */
.bell-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  color: var(--color-text-secondary, #9ca3af);
  transition: all .2s;
}
.bell-btn:hover {
  background: rgba(255,255,255,0.07);
  color: #fff;
}

/* Сверкающий колокольчик */
.bell-btn.ringing {
  color: #ef4444;
  animation: bell-shake 0.5s ease-in-out infinite;
  position: relative;
}

/* Волны звука вокруг колокольчика */
.bell-btn.ringing::before,
.bell-btn.ringing::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid #ef4444;
  animation: sound-wave 1s ease-out infinite;
}

.bell-btn.ringing::before {
  width: 50px;
  height: 50px;
  animation-delay: 0s;
}

.bell-btn.ringing::after {
  width: 65px;
  height: 65px;
  animation-delay: 0.3s;
}

@keyframes bell-shake {
  0%, 100% { transform: rotate(0deg); }
  10% { transform: rotate(15deg); }
  20% { transform: rotate(-15deg); }
  30% { transform: rotate(12deg); }
  40% { transform: rotate(-12deg); }
  50% { transform: rotate(8deg); }
  60% { transform: rotate(-8deg); }
  70% { transform: rotate(4deg); }
  80% { transform: rotate(-4deg); }
  90% { transform: rotate(2deg); }
}

@keyframes sound-wave {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0;
  }
}

.bell-badge {
  position: absolute;
  top: 3px; right: 3px;
  min-width: 17px; height: 17px;
  padding: 0 4px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.bell-btn.ringing .bell-badge {
  animation: badge-pulse 0.8s ease-in-out infinite;
  background: #dc2626;
}

@keyframes badge-pulse {
  0%, 100% { 
    transform: scale(1); 
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  50% { 
    transform: scale(1.15); 
    box-shadow: 0 0 12px 4px rgba(239, 68, 68, 0.5);
  }
}

/* Дропдаун */
.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 540px;
  background: #1a1a2e;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  overflow: hidden;
  z-index: 9000;
  display: flex;
  flex-direction: column;
}

/* Хедер */
.dh {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.125rem 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.dh-title {
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
}
.dh-actions { display: flex; gap: .5rem; }
.dh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: .3rem .7rem;
  border-radius: 7px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #9ca3af;
  font-size: .75rem;
  cursor: pointer;
  transition: all .15s;
}
.dh-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

/* Табы */
.tabs {
  display: flex;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .4rem;
  padding: .6rem;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: .85rem;
  cursor: pointer;
  transition: all .15s;
  border-bottom: 2px solid transparent;
}
.tab:hover { color: #d1d5db; }
.tab.active { color: #3b82f6; border-bottom-color: #3b82f6; }

.tab-badge {
  padding: 1px 6px;
  background: #3b82f6;
  color: #fff;
  border-radius: 8px;
  font-size: .7rem;
  font-weight: 700;
}

/* Список */
.list {
  flex: 1;
  overflow-y: auto;
  min-height: 80px;
  max-height: 400px;
}
.list::-webkit-scrollbar { width: 3px; }
.list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6b7280;
  font-size: .875rem;
}

.spinner {
  width: 24px; height: 24px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Метки секций */
.section-label {
  padding: .4rem 1rem;
  font-size: .7rem;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #4b5563;
  font-weight: 600;
  background: rgba(255,255,255,0.02);
}

/* Строка уведомления */
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: .75rem;
  padding: .75rem 1rem;
  cursor: pointer;
  position: relative;
  transition: background .15s;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.notif-item:last-child { border-bottom: none; }
.notif-item:hover { background: rgba(255,255,255,0.04); }

.notif-item.unread {
  background: rgba(59,130,246,0.06);
}
.notif-item.unread::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
}

/* Сверкающее уведомление */
.notif-item.flashing {
  animation: item-flash 1s ease-in-out infinite;
  background: rgba(251, 191, 36, 0.1);
}

@keyframes item-flash {
  0%, 100% { background: rgba(251, 191, 36, 0.1); }
  50% { background: rgba(251, 191, 36, 0.2); }
}

.reminder-item { background: rgba(245,158,11,0.04); }
.reminder-item:hover { background: rgba(245,158,11,0.08); }

/* Сработавшее напоминание - более тусклое */
.reminder-item.triggered { 
  background: rgba(107,114,128,0.04); 
  opacity: 0.8;
}
.reminder-item.triggered:hover { background: rgba(107,114,128,0.08); }

/* Иконка */
.notif-icon {
  width: 36px; height: 36px;
  flex-shrink: 0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

/* Тело */
.notif-body { flex: 1; min-width: 0; }

.notif-title {
  margin: 0 0 2px;
  font-size: .85rem;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notif-text {
  margin: 0 0 3px;
  font-size: .8rem;
  color: #6b7280;
  line-height: 1.4;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: .72rem;
  color: #4b5563;
}

/* Кнопка удалить */
.notif-del {
  width: 22px; height: 22px;
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: #4b5563;
  font-size: .75rem;
  cursor: pointer;
  border-radius: 5px;
  opacity: 0;
  transition: all .15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.notif-item:hover .notif-del { opacity: 1; }
.notif-del:hover { background: rgba(239,68,68,0.15); color: #ef4444; }

/* Футер */
.dfoot {
  display: block;
  text-align: center;
  padding: .7rem;
  border-top: 1px solid rgba(255,255,255,0.07);
  color: #3b82f6;
  font-size: .82rem;
  font-weight: 500;
  text-decoration: none;
  transition: background .15s;
}
.dfoot:hover { background: rgba(59,130,246,0.08); }

/* Анимация */
.dropdown-enter-active, .dropdown-leave-active {
  transition: opacity .2s ease, transform .2s ease;
}
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(.97);
}

@media (max-width: 480px) {
  .dropdown {
    width: calc(100vw - 1rem);
    right: -1rem;
  }
}
</style>
