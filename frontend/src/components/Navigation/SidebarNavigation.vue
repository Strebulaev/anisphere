<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Логотип -->
    <div class="sidebar-header">
      <router-link to="/" class="sidebar-logo">
        <span class="logo-text">{{ isCollapsed ? 'A' : 'Anisphere' }}</span>
        <span class="logo-tagline"></span>
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

      <router-link 
        to="/reactor" 
        class="nav-item"
        :class="{ active: isActiveRoute('/reactor') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        <span>Reactor</span>
      </router-link>

      <router-link 
        to="/playlists" 
        class="nav-item"
        :class="{ active: isActiveRoute('/playlists') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
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

      <router-link 
        to="/chats" 
        class="nav-item"
        :class="{ active: isActiveRoute('/chats') }"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
        <span>Чаты</span>
      </router-link>

      <router-link 
        to="/online" 
        class="nav-item"
        :class="{ active: isActiveRoute('/online') }"
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
        to="/profile" 
        class="nav-item"
        :class="{ active: isActiveRoute('/profile') }"
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
      </router-link>

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
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'

const route = useRoute()
const { isCollapsed, toggleSidebar } = useSidebar()

const isActiveRoute = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  // Точное совпадение для /feed чтобы не пересекалось с /feed/...
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background-color: var(--surface-2);
  border-right: 1px solid var(--border-subtle);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-slow) var(--ease-out);
  overflow: hidden;
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
}

.sidebar-logo {
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  overflow: hidden;
}

.logo-text {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: 0.03em;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-height: 28px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  flex-shrink: 0;
  margin-left: -28px;  /* ← добавить эту строку */
}

.collapse-btn:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.collapse-btn svg {
  transition: transform var(--duration-base) var(--ease-out);
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
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 500;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.nav-item.active {
  background-color: var(--accent-subtle);
  color: var(--accent);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  background-color: var(--accent);
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
}

.nav-item svg {
  flex-shrink: 0;
  opacity: 0.8;
  transition: opacity var(--duration-base) var(--ease-out);
}

.nav-item:hover svg,
.nav-item.active svg {
  opacity: 1;
}

/* ── Разделитель ───────────────────────────────────────────── */
.sidebar-divider {
  height: 1px;
  background-color: var(--border-subtle);
  margin: var(--space-2) var(--space-2);
  flex-shrink: 0;
}

/* ── Вторичная навигация ───────────────────────────────────── */
.sidebar-nav-secondary {
  padding: var(--space-2) var(--space-2) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.nav-item-secondary {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  color: var(--text-tertiary);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  white-space: nowrap;
  overflow: hidden;
}

.nav-item-secondary:hover {
  background-color: var(--surface-4);
  color: var(--text-secondary);
}

.nav-item-secondary.active {
  background-color: var(--accent-subtle);
  color: var(--accent);
}

.nav-item-secondary svg {
  flex-shrink: 0;
  opacity: 0.7;
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
  right: -13px;
  background-color: var(--surface-3);
  border-color: var(--border-default);
  z-index: 10;
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

/* ── Адаптивность ──────────────────────────────────────────── */
@media (max-width: 1023px) {
  .sidebar {
    display: none;
  }
}
</style>
