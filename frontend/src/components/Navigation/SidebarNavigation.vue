<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Декorative лепестки сакуры -->
    <div class="sakura-decor">
      <span class="petal petal-1"> <SakuraIcon name="flower" /> </span>
      <span class="petal petal-2"> <SakuraIcon name="flower" /> </span>
    </div>

    <!-- Логотип -->
    <div class="sidebar-header">
      <router-link to="/" class="sidebar-logo">
        <img src="../../../public/sakura.png" alt="Sakura" class="logo-icon" />
        <span class="logo-text">{{ isCollapsed ? '' : 'Anisphere' }}</span>
        <!-- <span class="logo-tagline">{{ isCollapsed ? '' : 'Sakura Bloom' }}</span> -->
      </router-link>
      <button @click="toggleSidebar" class="collapse-btn" type="button" :title="isCollapsed ? 'Развернуть' : 'Свернуть'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: isCollapsed }">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
    </div>

    <!-- Навигационные ссылки -->
    <nav class="sidebar-nav">
      <router-link 
        to="/" 
        class="nav-item"
        :class="{ active: isActiveRoute('/') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/>
          <rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/>
          <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        <span>Главная</span>
      </router-link>

      <router-link 
        to="/feed" 
        class="nav-item"
        :class="{ active: isActiveRoute('/feed') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>Лента</span>
      </router-link>

      <router-link
        to="/anime" 
        class="nav-item"
        :class="{ active: isActiveRoute('/anime') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/>
          <line x1="7" y1="2" x2="7" y2="22"/>
          <line x1="17" y1="2" x2="17" y2="22"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <line x1="2" y1="7" x2="7" y2="7"/>
          <line x1="2" y1="17" x2="7" y2="17"/>
          <line x1="17" y1="17" x2="22" y2="17"/>
          <line x1="17" y1="7" x2="22" y2="7"/>
        </svg>
        <span>Аниме</span>
      </router-link>

      <!-- <router-link 
        to="/reactor" 
        class="nav-item"
        :class="{ active: isActiveRoute('/reactor') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        <span>Reactor</span>
      </router-link> -->

      <router-link
        to="/playlists" 
        class="nav-item"
        :class="{ active: isActiveRoute('/playlists') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
        <span>Плейлисты</span>
      </router-link>

      <router-link
        to="/library" 
        class="nav-item"
        :class="{ active: isActiveRoute('/library') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        <span>Моя коллекция</span>
      </router-link>

      <!-- <router-link 
        to="/wheel" 
        class="nav-item"
        :class="{ active: isActiveRoute('/wheel') }"
      >
        <span class="nav-icon-emoji"> <SakuraIcon name="wheel" /> </span>
        <span>Колесо фортуны</span>
      </router-link> -->

      <router-link 
        to="/chats" 
        class="nav-item"
        :class="{ active: isActiveRoute('/chats') }"
      >
        <div class="nav-item-icon-wrapper">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
          </svg>
          <!-- Бейдж с непрочитанными -->
          <span v-if="unreadCount > 0" class="unread-badge">
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </div>
        <span>Чаты</span>
      </router-link>

      <router-link 
        to="/people" 
        class="nav-item"
        :class="{ active: isActiveRoute('/people') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <!-- Основной человек (в центре) -->
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          
          <!-- Человек на заднем плане (справа) -->
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <span>Люди</span>
      </router-link>

      <router-link 
        to="/studios" 
        class="nav-item"
        :class="{ active: isActiveRoute('/studios') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="7" width="20" height="14" rx="2"/>
          <path d="M16 7V5a2 2 0 0 0-4 0v2"/>
          <line x1="12" y1="12" x2="12" y2="16"/>
          <line x1="10" y1="14" x2="14" y2="14"/>
        </svg>
        <span>Студии</span>
      </router-link>

      <router-link 
        :to="profileLink" 
        class="nav-item"
        :class="{ active: isProfileActive }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <span>Профиль</span>
      </router-link>
    </nav>

    <!-- Разделитель -->
    <div class="sidebar-divider"></div>

    <!-- Дополнительные ссылки -->
    <nav class="sidebar-nav-secondary">
      <!-- <router-link 
        to="/search" 
        class="nav-item-secondary"
        :class="{ active: isActiveRoute('/search') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span>Поиск</span>
      </router-link> -->

      <router-link
        to="/donate"
        class="nav-item-secondary"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <span>Донаты</span>
      </router-link>

      <!-- <router-link 
        to="/competitions" 
        class="nav-item-secondary"
        :class="{ active: isActiveRoute('/competitions') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
          <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
          <path d="M4 22h16"/>
          <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
          <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
          <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
        </svg>
        <span>Квесты</span>
      </router-link> -->

      <router-link
        to="/settings" 
        class="nav-item-secondary"
        :class="{ active: isActiveRoute('/settings') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>Настройки</span>
      </router-link>

      <!-- Подписка -->
      <router-link
        to="/subscription"
        class="nav-item-secondary nav-item-premium"
        :class="{ active: isActiveRoute('/subscription') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M2.5 2v6h6M21.5 22v-6h-6"/>
          <path d="M22 11.5A10 10 0 0 0 3.2 7.2M2 12.5a10 10 0 0 0 18.8 4.2"/>
        </svg>
        <span>Подписка</span>
      </router-link>

      <!-- Админская панель — только для админа -->
      <router-link
        v-if="isAdmin"
        to="/admin"
        class="nav-item-secondary nav-item-admin"
        :class="{ active: isActiveRoute('/admin') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span>Админ</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { useChatExtrasStore } from '@/stores/chatExtras'

const route = useRoute()
const { isCollapsed, toggleSidebar } = useSidebar()
const authStore = useAuthStore()
const chatExtrasStore = useChatExtrasStore()

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return false
  return u.is_admin || u.is_staff || u.username === 'kaiden812'
})

const isActiveRoute = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  // Точное совпадение для /feed чтобы не пересекалось с /feed/...
  return route.path === path || route.path.startsWith(path + '/')
}

// Ссылка на профиль текущего пользователя
const profileLink = computed(() => {
  const userId = authStore.user?.id
  return userId ? `/profile/${userId}` : '/profile'
})

// Проверка активности для профиля
const isProfileActive = computed(() => {
  return route.path.startsWith('/profile/') || route.path === '/profile'
})

// Количество непрочитанных сообщений
const unreadCount = computed(() => chatExtrasStore.totalUnreadCount || 0)

// Загружаем непрочитанные при монтировании
onMounted(() => {
  chatExtrasStore.loadUnreadChats()
  
  // Периодическое обновление непрочитанных (каждые 30 секунд)
  const interval = setInterval(() => {
    chatExtrasStore.loadUnreadChats()
  }, 30000)
  
  // Очищаем интервал при размонтировании
  return () => clearInterval(interval)
})
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface-1) 100%);
  border-right: 1px solid var(--border-subtle);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-slow) var(--ease-petal);
  overflow: hidden;
}

/* ── Декорация сакуры ─────────────────────────────────────── */
.sakura-decor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  opacity: 0.15;
}

.petal {
  position: absolute;
  font-size: 12px;
  animation: floatPetal 8s ease-in-out infinite;
  filter: blur(0.5px);
}

.petal-1 {
  top: 20%;
  right: 10%;
  animation-delay: -2s;
}

.petal-2 {
  top: 60%;
  right: 5%;
  animation-delay: -4s;
  font-size: 10px;
}

@keyframes floatPetal {
  0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.1; }
  25% { transform: translateY(-8px) rotate(5deg); opacity: 0.2; }
  50% { transform: translateY(-4px) rotate(-3deg); opacity: 0.15; }
  75% { transform: translateY(-10px) rotate(2deg); opacity: 0.1; }
}

/* ── Заголовок ─────────────────────────────────────────────── */
.sidebar-header {
  height: var(--navbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  gap: var(--space-2);
  position: relative;
  z-index: 1;
}

.sidebar-logo {
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  overflow: hidden;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  object-fit: contain;
  transition: transform var(--duration-slow) var(--ease-petal);
}

.sidebar-logo:hover .logo-icon {
  transform: rotate(15deg) scale(1.05);
}

.sidebar-logo:hover .logo-icon svg {
  transform: rotate(15deg) scale(1.05);
}

.logo-text {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--text-primary);
  white-space: nowrap;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-bright) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-tagline {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-height: 28px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
  border-color: var(--accent);
  box-shadow: var(--shadow-glow-sm);
}

.collapse-btn svg {
  transition: transform var(--duration-base) var(--ease-petal);
}

.collapse-btn svg.rotated {
  transform: rotate(180deg);
}

/* ── Основная навигация ────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  padding: var(--space-3) var(--space-2);
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  z-index: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  transition:
    all var(--duration-base) var(--ease-petal);
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  transition: width var(--duration-base) var(--ease-petal);
  opacity: 0;
}

.nav-item:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, var(--accent-subtle) 0%, var(--accent-2-subtle) 100%);
  color: var(--accent);
}

.nav-item.active::before {
  width: 4px;
  opacity: 1;
}

.nav-item-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-item svg {
  flex-shrink: 0;
  opacity: 0.7;
  transition: all var(--duration-base) var(--ease-petal);
}

/* Бейдж непрочитанных сообщений */
.unread-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  font-size: 10px;
  font-weight: 700;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--surface-2);
  white-space: nowrap;
  z-index: 1;
  box-shadow: var(--shadow-petal-sm);
}

.sidebar.collapsed .unread-badge {
  top: -4px;
  right: -4px;
  min-width: 14px;
  height: 14px;
  font-size: 9px;
  padding: 0 3px;
}

.nav-item:hover svg,
.nav-item.active svg {
  opacity: 1;
  color: var(--accent);
}

.nav-icon-emoji {
  font-size: 20px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ── Разделитель ───────────────────────────────────────────── */
.sidebar-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--border-subtle) 50%, transparent 100%);
  margin: var(--space-3) var(--space-4);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

/* ── Вторичная навигация ───────────────────────────────────── */
.sidebar-nav-secondary {
  padding: var(--space-2) var(--space-2) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.nav-item-secondary {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  color: var(--text-tertiary);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  transition:
    all var(--duration-base) var(--ease-petal);
  white-space: nowrap;
  overflow: hidden;
}

.nav-item-secondary:hover {
  background-color: var(--surface-4);
  color: var(--text-secondary);
  transform: translateX(4px);
}

.nav-item-secondary.active {
  background: var(--accent-subtle);
  color: var(--accent);
}

.nav-item-admin {
  color: var(--danger) !important;
}

.nav-item-premium {
  color: #FFD700 !important;
}

.nav-item-premium:hover {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.1)) !important;
  color: #FFD700 !important;
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.15);
}

.nav-item-premium.active {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 165, 0, 0.15)) !important;
  color: #FFD700 !important;
}

.nav-item-admin:hover {
  background: var(--danger-subtle) !important;
  color: var(--danger) !important;
  box-shadow: 0 0 12px rgba(255,138,138,0.15);
}

.nav-item-admin.active {
  background: var(--danger-subtle) !important;
  color: var(--danger) !important;
}

.nav-item-secondary svg {
  flex-shrink: 0;
  opacity: 0.6;
}

.nav-item-secondary:hover svg,
.nav-item-secondary.active svg {
  opacity: 1;
}

/* ── Свёрнутое состояние ───────────────────────────────────── */
.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0 var(--space-2);
}

.sidebar.collapsed .sidebar-logo {
  display: none;
}

.sidebar.collapsed .collapse-btn {
  position: absolute;
  right: 16px;
  background: var(--surface-3);
  border-color: var(--border-default);
  z-index: 10;
  box-shadow: var(--shadow-md);
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: var(--space-3);
}

.sidebar.collapsed .nav-item span {
  display: none;
}

.sidebar.collapsed .nav-item.active::before {
  display: none;
}

.sidebar.collapsed .nav-item-secondary {
  justify-content: center;
  padding: var(--space-2);
}

.sidebar.collapsed .nav-item-secondary span {
  display: none;
}

.sidebar.collapsed .sidebar-divider {
  margin: var(--space-2) var(--space-1);
}

.sidebar.collapsed .sakura-decor {
  opacity: 0.05;
}

/* ── Адаптивность ──────────────────────────────────────────── */
@media (max-width: 1023px) {
  .sidebar {
    overflow-y: auto;
    /* display: flex; уже есть */
  }
}
</style>
