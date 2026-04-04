<template>
  <nav class="navbar">
    <div class="navbar-content">
      <!-- Поисковая строка -->
      <div class="navbar-search">
        <SearchBar
          variant="header"
          placeholder="Поиск..."
          :categories="searchCategories"
          :min-query-length="3"
          :debounce-time="400"
          @search="handleSearch"
        />
      </div>

      <!-- Навигация по секциям -->
      <div class="navbar-navigation">
        <button
          v-for="item in navigationItems"
          :key="item.key"
          @click="navigateToSection(item)"
          :class="['nav-link', { loading: item.key === 'random' && randomLoading }]"
          :disabled="item.key === 'random' && randomLoading"
          type="button"
        >
          <span class="nav-icon" :class="{ spin: item.key === 'random' && randomLoading }">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </div>

      <!-- Правая часть -->
      <div class="navbar-actions">
        <!-- Поддержать -->
        <router-link to="/donate" class="donate-btn" title="Поддержать проект">
          <span class="donate-icon">💝</span>
          <span class="donate-label">Поддержать</span>
        </router-link>

        <!-- Уведомления -->
        <div class="navbar-notifications" v-if="isAuthenticated">
          <button
            :class="['navbar-icon-btn', { 'bell-ringing': notificationStore.isBellRinging }]"
            title="Уведомления"
            type="button"
            @click="toggleNotifications"
          >
            <svg
              width="20" height="20" viewBox="0 0 24 24" fill="none"
              :stroke="notificationStore.isBellRinging ? 'var(--danger, #ef4444)' : 'currentColor'"
              stroke-width="2"
              :class="{ 'bell-svg-ring': notificationStore.isBellRinging }"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <!-- Кружок пульсации во время звонка -->
            <span
              v-if="notificationStore.isBellRinging"
              class="bell-pulse-ring"
            />
            <span v-if="notificationStore.hasUnread" class="notification-dot">
              {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
            </span>
          </button>

          <!-- Дропдаун уведомлений -->
          <Transition name="dropdown">
            <div v-if="showNotifications" class="notifications-dropdown" @click.stop>
              <div class="notif-header">
                <span class="notif-title">Уведомления</span>
                <div class="notif-header-actions">
                  <button
                    v-if="notificationStore.hasUnread"
                    @click="notificationStore.markAllRead()"
                    class="mark-all-read-btn"
                    type="button"
                  >
                    ✓ Все
                  </button>
                    <!-- <router-link to="/notifications/settings" class="notif-settings-btn" @click="showNotifications = false" title="Настройки">
                    ⚙️
                  </router-link> -->
                </div>
              </div>
              <div class="notif-list" v-if="notificationStore.recentNotifications.length > 0">
                <div
                  v-for="notif in notificationStore.recentNotifications"
                  :key="notif.id"
                  :class="['notif-item', { unread: !notif.is_read }]"
                  @click="handleNotificationClick(notif)"
                >
                  <div class="notif-icon">
                    {{ getNotifIcon(notif) }}
                  </div>
                  <div class="notif-content">
                    <div class="notif-text">{{ getNotifText(notif) }}</div>
                    <div class="notif-time">{{ formatNotifTime(notif.created_at) }}</div>
                  </div>
                  <div v-if="!notif.is_read" class="notif-unread-dot"></div>
                </div>
              </div>
              <div v-else class="notif-empty">
                <span>Нет уведомлений</span>
              </div>
              <router-link to="/notifications" class="notif-footer" @click="showNotifications = false">
                Все уведомления →
              </router-link>
            </div>
          </Transition>
        </div>

        <!-- Профиль пользователя -->
        <div class="navbar-profile">
          <router-link to="/profile" class="profile-link">
            <div class="profile-avatar">
              <OptimizedImage v-if="userAvatar" :src="userAvatar" alt="Avatar" class="avatar-image" />
              <div v-else class="avatar-placeholder">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div v-if="isOnline" class="online-indicator"></div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSidebar } from '@/composables/useSidebar'
import { useNotificationStore } from '@/stores/notifications'
import SearchBar from '@/components/Search/SearchBar.vue'
import remindersApi from '@/api/reminders'
import apiClient from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const { toggleSidebar } = useSidebar()
const notificationStore = useNotificationStore()

const showNotifications = ref(false)
let reminderCheckInterval: ReturnType<typeof setInterval> | null = null
let originalTitle = document.title
let titleBlinkInterval: ReturnType<typeof setInterval> | null = null

const searchCategories = [
  { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 5 },
  { id: 'users', name: 'Пользователи', icon: 'users', enabled: true, limit: 3 },
  { id: 'playlists', name: 'Плейлисты', icon: 'playlists', enabled: true, limit: 3 }
]

const navigationItems = [
  { key: 'ongoings',         label: 'Онгоинги',    icon: '🔥', to: '/anime?section=ongoings'         },
  { key: 'recommendations', label: 'Рекомендации', icon: '⭐', to: '/anime?section=recommendations' },
  { key: 'announcements',   label: 'Анонсы',       icon: '📢', to: '/anime?section=announcements'   },
  { key: 'random',          label: 'Рандом',        icon: '🎲', to: null },
]

const randomLoading = ref(false)

const navigateToSection = async (item: any) => {
  if (item.key === 'random') {
    if (randomLoading.value) return
    randomLoading.value = true
    try {
      const response = await apiClient.get('/anime/random/')
      const animeId = response.data?.id
      if (animeId) {
        // Перезагружаем страницу с новым URL
        window.location.href = `/anime/${animeId}`
      }
    } catch (e) {
      console.error('Failed to get random anime:', e)
    } finally {
      randomLoading.value = false
    }
    return
  }
  const [path, queryStr] = item.to.split('?')
  const params = new URLSearchParams(queryStr)
  const query: Record<string, string> = {}
  params.forEach((value, key) => { query[key] = value })
  router.replace({ path, query })
}

const userAvatar = computed(() => authStore.user?.avatar)
const isOnline = computed(() => authStore.user?.is_online ?? false)
const isAuthenticated = computed(() => authStore.isAuthenticated)

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    notificationStore.fetchRecent()
  }
}

const handleSearch = (query: string) => {
  router.push({ path: '/anime', query: { q: query } })
}

// Закрываем дропдаун при клике вне
const handleOutsideClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.navbar-notifications')) {
    showNotifications.value = false
  }
}

const getNotifIcon = (notif: any) => {
  // If backend already sent an icon emoji, use it
  if (notif.icon && notif.icon.length <= 4) return notif.icon
  const icons: Record<string, string> = {
    like: '❤️', dislike: '👎', heart: '💖',
    comment: '💬', reply: '↩️', mention: '@',
    follow: '👥', repost: '🔁',
    message: '✉️', group_message: '👥', group_invite: '📨',
    achievement: '🏆', contest: '🏅', contest_vote: '🗳️',
    contest_results: '📊', contest_win: '👑',
    reminder_episode: '⏰', reminder_event: '📅', reminder_contest: '⏳',
    reminder: '⏰', system: '⚙️', warning: '⚠️', security: '🔒',
  }
  return icons[notif.type || notif.kind] || '🔔'
}

const getNotifText = (notif: any) => {
  return notif.title || notif.text || 'Уведомление'
}

const formatNotifTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'только что'
  if (mins < 60) return `${mins} мин назад`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} ч назад`
  return date.toLocaleDateString('ru', { day: 'numeric', month: 'short' })
}

const handleNotificationClick = (notif: any) => {
  notificationStore.markRead(notif.id)
  showNotifications.value = false

  const type = notif.type || notif.kind || ''
  const isReminder = type.startsWith('reminder') || type === 'reminder'

  if (isReminder) {
    // Напоминания открывают страницу уведомлений на табе "Напоминания"
    router.push({ path: '/notifications', query: { tab: 'reminders' } })
    return
  }

  const dest = notif.link || notif.url
  if (dest) {
    router.push(dest)
  } else {
    // Если нет конкретной ссылки — открываем страницу уведомлений
    router.push('/notifications')
  }
}

// Моргание вкладки при напоминании
const startTabBlink = (message: string) => {
  if (titleBlinkInterval) return // уже мигает
  let blink = false
  titleBlinkInterval = setInterval(() => {
    document.title = blink ? message : originalTitle
    blink = !blink
  }, 1000)
  
  // Останавливаем через 30 секунд
  setTimeout(() => stopTabBlink(), 30000)
}

const stopTabBlink = () => {
  if (titleBlinkInterval) {
    clearInterval(titleBlinkInterval)
    titleBlinkInterval = null
  }
  document.title = originalTitle
}

// Добавляет уведомление в store, запускает сверкание колокольчика на 1 минуту
const triggerReminderNotification = (reminderId: number, animeName: string, comment?: string) => {
  const notifId = Date.now()
  const text = `⏰ Напоминание: ${animeName}${comment ? ` — ${comment}` : ''}`

  // Добавляем уведомление в store (попадает в дропдаун и в список)
  notificationStore.addNotification({
    id: notifId,
    kind: 'reminder',
    type: 'reminder',
    title: `Напоминание: ${animeName}`,
    text: `Пора смотреть${comment ? ` — ${comment}` : ''}`,
    content: text,
    is_read: false,
    created_at: new Date().toISOString(),
    icon: '⏰',
  } as any)

  // Запускаем сверкание колокольчика на 1 минуту
  notificationStore.startRinging(reminderId)

  // Моргаем вкладкой тоже 1 минуту
  startTabBlink(`⏰ ${animeName}`)
}

// Проверяем напоминания каждую минуту
const checkReminders = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const response = await remindersApi.getUpcomingReminders()
    const reminders = response.data
    const now = new Date()
    
    for (const reminder of reminders) {
      const reminderTime = new Date(reminder.reminder_time)
      const diffMs = reminderTime.getTime() - now.getTime()
      
      // Срабатываем если напоминание в пределах 1 минуты
      if (diffMs <= 60000 && diffMs > -60000) {
        const animeName = reminder.anime_detail?.title_ru || 
                          reminder.anime_detail?.title_en || 
                          'Аниме'
        triggerReminderNotification(reminder.id, animeName, reminder.comment)
        
        // Деактивируем напоминание если не повторяющееся
        if (!reminder.repeat_weekly) {
          await remindersApi.deactivateReminder(reminder.id)
        }
      }
    }
  } catch (e) {
    // Игнорируем ошибки проверки
  }
}

// Получить токен для WS из localStorage (стандарт для DRF SimpleJWT)
const getAccessToken = (): string | null => {
  try {
    return localStorage.getItem('access_token') || localStorage.getItem('token') || null
  } catch {
    return null
  }
}

// Обработчик события newNotification от useGlobalWebSocket
const handleNewNotificationEvent = (e: Event) => {
  const notif = (e as CustomEvent).detail
  if (notif) {
    notificationStore.addNotification(notif)
  } else {
    notificationStore.fetchRecent()
    notificationStore.fetchCount()
  }
}

onMounted(async () => {
  document.addEventListener('click', handleOutsideClick)
  window.addEventListener('newNotification', handleNewNotificationEvent)

  if (authStore.isAuthenticated) {
    // Загружаем недавние уведомления и счётчик
    await notificationStore.fetchCount()
    notificationStore.fetchRecent()

    // Подключаем WS для realtime
    const token = getAccessToken()
    if (token) notificationStore.connectWS(token)

    // Проверка напоминаний каждую минуту
    checkReminders()
    reminderCheckInterval = setInterval(checkReminders, 60000)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  window.removeEventListener('newNotification', handleNewNotificationEvent)
  if (reminderCheckInterval) clearInterval(reminderCheckInterval)
  stopTabBlink()
  notificationStore.disconnectWS()
})
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  height: var(--navbar-height);
  background: linear-gradient(180deg, var(--surface-2) 0%, rgba(15,11,26,0.95) 100%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-navbar);
  display: flex;
  align-items: center;
  transition: left var(--duration-slow) var(--ease-petal);
}

.sidebar-collapsed .navbar {
  left: var(--sidebar-width-collapsed);
}

.navbar-content {
  display: flex;
  align-items: center;
  padding: 0 var(--space-5);
  width: 100%;
  height: 100%;
  gap: var(--space-3);
}

/* ── Навигация ───────────────────────────────────────────── */
.navbar-navigation {
  display: flex;
  gap: var(--space-1);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-lg);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-weight: 500;
  transition:
    all var(--duration-base) var(--ease-petal);
  white-space: nowrap;
  cursor: pointer;
  min-height: 34px;
  position: relative;
  overflow: hidden;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  border-radius: var(--radius-full);
  transition: transform var(--duration-base) var(--ease-petal);
}

.nav-link:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.nav-link:hover::after {
  transform: translateX(-50%) scaleX(1);
}

.nav-icon { font-size: var(--text-md); display: inline-block; }
.nav-link.loading { opacity: .6; cursor: not-allowed; }
.spin { animation: nb-spin .7s linear infinite; }
@keyframes nb-spin { to { transform: rotate(360deg); } }
.nav-label { font-size: var(--text-base); }

/* ── Поиск ──────────────────────────────────────────────── */
.navbar-search {
  width: 360px;
  flex-shrink: 0;
  position: relative;
  z-index: calc(var(--z-navbar) + 1);
}

/* ── Кнопка поддержки ───────────────────────────────────── */
.donate-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 600;
  transition: all var(--duration-base) var(--ease-petal);
  white-space: nowrap;
  box-shadow: var(--shadow-petal-sm);
}

.donate-btn:hover {
  background: linear-gradient(135deg, var(--accent-hover) 0%, var(--accent) 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px var(--accent-glow);
}

.donate-icon {
  font-size: var(--text-base);
}

.donate-label {
  display: inline;
}

/* ── Действия ───────────────────────────────────────────── */
.navbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
}

.navbar-icon-btn {
  width: 36px;
  height: 36px;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--text-tertiary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition:
    all var(--duration-base) var(--ease-petal);
  position: relative;
  border: none;
}

.navbar-icon-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
  box-shadow: var(--shadow-glow-sm);
}

.notification-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: linear-gradient(135deg, var(--danger) 0%, #ff6b6b 100%);
  border-radius: var(--radius-full);
  border: 2px solid var(--surface-2);
  font-size: 9px;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: 0 2px 8px rgba(255,138,138,0.3);
}

/* ── Сверкание колокольчика при напоминании ───────────────── */
.bell-ringing {
  animation: bell-flash 0.6s ease-in-out infinite;
}

.bell-svg-ring {
  animation: bell-shake 0.5s ease-in-out infinite;
  transform-origin: top center;
}

/* Пульсирующее кольцо */
.bell-pulse-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid var(--danger);
  animation: bell-pulse 1s ease-out infinite;
  pointer-events: none;
}

@keyframes bell-flash {
  0%, 100% { background-color: transparent; }
  50% { background-color: rgba(255,138,138, 0.18); }
}

@keyframes bell-shake {
  0%, 100% { transform: rotate(0deg); }
  15%       { transform: rotate(12deg); }
  30%       { transform: rotate(-10deg); }
  45%       { transform: rotate(8deg); }
  60%       { transform: rotate(-6deg); }
  75%       { transform: rotate(4deg); }
  90%       { transform: rotate(-2deg); }
}

@keyframes bell-pulse {
  0%   { opacity: 0.8; transform: scale(0.85); }
  70%  { opacity: 0; transform: scale(1.7); }
  100% { opacity: 0; transform: scale(1.7); }
}

/* ── Уведомления дропдаун ─────────────────────────────── */
.navbar-notifications {
  position: relative;
}

.notifications-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  z-index: calc(var(--z-navbar) + 10);
  overflow: hidden;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(180deg, var(--surface-3) 0%, var(--surface-2) 100%);
}

.notif-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
}

.mark-all-read-btn {
  font-size: 0.75rem;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
  transition: opacity 0.15s;
}

.mark-all-read-btn:hover { opacity: 0.8; }

.notif-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.notif-settings-btn {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  text-decoration: none;
  display: flex;
  align-items: center;
  transition: color 0.15s;
}
.notif-settings-btn:hover { color: var(--text-primary); }

.notif-list {
  max-height: 380px;
  overflow-y: auto;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border-subtle);
  transition: all 0.15s;
  position: relative;
}

.notif-item:hover { 
  background: var(--surface-3); 
}

.notif-item.unread { 
  background: linear-gradient(90deg, var(--accent-subtle) 0%, transparent 100%);
}

.notif-item:last-child { border-bottom: none; }

.notif-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.notif-content { flex: 1; min-width: 0; }

.notif-text {
  font-size: 0.8125rem;
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notif-time {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}

.notif-unread-dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
  box-shadow: var(--shadow-glow-sm);
}

.notif-empty {
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.notif-footer {
  display: block;
  padding: 0.875rem 1rem;
  text-align: center;
  font-size: 0.8125rem;
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  border-top: 1px solid var(--border-subtle);
  background: var(--surface-3);
  transition: all 0.15s;
}

.notif-footer:hover { 
  background: var(--surface-4); 
}

/* ── Анимация дропдауна ──── */
.dropdown-enter-active { transition: all 0.2s var(--ease-petal); }
.dropdown-leave-active { transition: all 0.15s var(--ease-in); }
.dropdown-enter-from,
.dropdown-leave-to { opacity: 0; transform: translateY(-8px) scale(0.98); }

/* ── Профиль ─────────────────────────────────────────────── */
.navbar-profile {
  display: flex;
  align-items: center;
}

.profile-link {
  text-decoration: none;
}

.profile-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--surface-4) 0%, var(--surface-5) 100%);
  border: 2px solid var(--border-default);
  overflow: hidden;
  position: relative;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.profile-avatar:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow-sm);
  transform: scale(1.05);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, var(--success) 0%, #6ed396 100%);
  border-radius: 50%;
  border: 2px solid var(--surface-2);
  box-shadow: 0 0 8px rgba(142,212,168,0.4);
}

/* ── Адаптивность ──────────────────────────────────────────── */
@media (max-width: 1400px) {
  .navbar-navigation { gap: 0; }
  .nav-link { padding: var(--space-2); }
  .nav-label { display: none; }
  .nav-icon { font-size: var(--text-xl); }
  .donate-label { display: none; }
}

@media (max-width: 1023px) {
  .navbar {
    left: 0;
  }

  .navbar-navigation {
    order: 3;
    margin-left: auto;
  }

  .navbar-search {
    display: none;
  }
}

@media (max-width: 767px) {
  .navbar {
    display: none;
  }
}
</style>
