<template>
  <nav class="bottom-nav">
    <div class="nav-items">
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

      <!-- Reactor -->
      <router-link
        to="/reactor"
        class="nav-item"
        :class="{ active: isActiveRoute('/reactor') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        <span>Reactor</span>
      </router-link>

      <!-- Плейлисты -->
      <router-link
        to="/playlists"
        class="nav-item"
        :class="{ active: isActiveRoute('/playlists') }"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
        <span>Плейлисты</span>
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
  return route.path.startsWith(path)
}
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--height-nav-mobile);
  background-color: var(--color-background-secondary);
  backdrop-filter: blur(var(--blur-nav));
  border-top: 1px solid var(--color-divider);
  z-index: 100;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.5);
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
  gap: 4px;
  padding: 8px 0;
  color: var(--color-text-tertiary);
  text-decoration: none;
  transition: all 0.15s var(--transition-smooth);
  cursor: pointer;
}

.nav-item svg {
  flex-shrink: 0;
  transition: all 0.15s var(--transition-smooth);
}

.nav-item span {
  font-size: 10px;
  font-weight: 500;
  transition: all 0.15s var(--transition-smooth);
}

.nav-item:hover {
  color: var(--color-text-secondary);
}

.nav-item.active {
  color: var(--color-accent);
}

.nav-item.active svg {
  transform: scale(1.1);
}

/* Активный индикатор */
.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  width: 32px;
  height: 2px;
  background-color: var(--color-accent);
  border-radius: 2px 2px 0 0;
}

/* Адаптивность */
@media (min-width: 768px) {
  .bottom-nav {
    display: none;
  }
}
</style>