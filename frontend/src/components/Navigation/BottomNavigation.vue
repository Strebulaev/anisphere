<template>
  <nav class="bottom-nav">
    <div class="nav-items">
      <!-- Главная -->
      <router-link
        to="/"
        class="nav-item"
        :class="{ active: isActiveRoute('/') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/>
          <rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/>
          <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        <span>Главная</span>
      </router-link>

      <!-- Лента -->
      <router-link
        to="/feed"
        class="nav-item"
        :class="{ active: isActiveRoute('/feed') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>Лента</span>
      </router-link>

      <!-- Аниме -->
      <router-link
        to="/anime"
        class="nav-item"
        :class="{ active: isActiveRoute('/anime') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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

      <!-- Чаты -->
      <router-link
        to="/chats"
        class="nav-item"
        :class="{ active: isActiveRoute('/chats') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
        <span>Чаты</span>
      </router-link>

      <!-- Профиль -->
      <router-link
        to="/profile"
        class="nav-item"
        :class="{ active: isActiveRoute('/profile') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <span>Профиль</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const isActiveRoute = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--bottom-nav-height);
  background-color: var(--surface-2);
  backdrop-filter: var(--blur-nav);
  -webkit-backdrop-filter: var(--blur-nav);
  border-top: 1px solid var(--border-subtle);
  z-index: var(--z-navbar);
  box-shadow: 0 -1px 0 var(--border-subtle), 0 -8px 24px rgba(0,0,0,0.4);
}

.nav-items {
  display: flex;
  height: 100%;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: var(--space-2) 0;
  color: var(--text-tertiary);
  text-decoration: none;
  transition:
    color var(--duration-base) var(--ease-out),
    background-color var(--duration-base) var(--ease-out);
  cursor: pointer;
  position: relative;
  -webkit-tap-highlight-color: transparent;
}

.nav-item svg {
  flex-shrink: 0;
  transition: transform var(--duration-base) var(--ease-spring);
}

.nav-item span {
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1;
}

.nav-item:hover {
  color: var(--text-secondary);
}

.nav-item.active {
  color: var(--accent);
}

.nav-item.active svg {
  transform: scale(1.1) translateY(-1px);
}

/* Точка-индикатор сверху активного */
.nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 2px;
  background-color: var(--accent);
  border-radius: 0 0 var(--radius-xs) var(--radius-xs);
}

@media (min-width: 768px) {
  .bottom-nav {
    display: none;
  }
}
</style>