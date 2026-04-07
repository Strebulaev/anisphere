<template>
  <div class="mobile-nav" v-if="!isDesktop">
    <!-- Бургер кнопка -->
    <button class="burger-btn" @click="toggleMenu" aria-label="Меню">
      <svg v-if="!menuOpen" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
      <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- Заголовок / Логотип -->
    <router-link to="/" class="mobile-logo">
      Anisphere
    </router-link>

    <!-- Кнопка профиля (справа) -->
    <router-link to="/profile" class="profile-btn" aria-label="Профиль">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    </router-link>

    <!-- Выпадающее меню -->
    <Transition name="menu">
      <div v-if="menuOpen" class="mobile-menu" @click="menuOpen = false">
        <nav class="menu-items" @click.stop>
          <!-- Главная -->
          <router-link to="/" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            <span>Главная</span>
          </router-link>

          <!-- Лента -->
          <router-link to="/feed" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <span>Лента</span>
          </router-link>

          <!-- Аниме -->
          <router-link to="/anime" class="menu-item" @click="menuOpen = false">
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

          <!-- Плейлисты -->
          <router-link to="/playlists" class="menu-item" @click="menuOpen = false">
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

          <!-- Моя коллекция -->
          <router-link to="/library" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            <span>Моя коллекция</span>
          </router-link>

          <!-- Чаты -->
          <router-link to="/chats" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
            </svg>
            <span>Чаты</span>
          </router-link>

          <!-- Люди -->
          <router-link to="/people" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <span>Люди</span>
          </router-link>

          <!-- Студии -->
          <router-link to="/studios" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2"/>
              <path d="M16 7V5a2 2 0 0 0-4 0v2"/>
              <line x1="12" y1="12" x2="12" y2="16"/>
              <line x1="10" y1="14" x2="14" y2="14"/>
            </svg>
            <span>Студии</span>
          </router-link>

          <!-- Донаты -->
          <router-link to="/donate" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            <span>Донаты</span>
          </router-link>

          <!-- Настройки -->
          <router-link to="/settings" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <span>Настройки</span>
          </router-link>

          <!-- Админ (если есть права) -->
          <router-link v-if="isAdmin" to="/admin" class="menu-item" @click="menuOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>Админ</span>
          </router-link>
        </nav>
      </div>
    </Transition>

    <!-- Оверлей -->
    <Transition name="overlay">
      <div v-if="menuOpen" class="menu-overlay" @click="menuOpen = false"></div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const menuOpen = ref(false)

const isAdmin = computed(() => {
  const u = authStore.user
  if (!u) return false
  return u.is_admin || u.is_staff || u.username === 'kaiden812'
})

// Определяем десктоп (скрываем бургер-меню)
const isDesktop = ref(false)

const checkDesktop = () => {
  isDesktop.value = window.innerWidth >= 768
}

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

// Закрыть меню при изменении маршрута
onMounted(() => {
  checkDesktop()
  window.addEventListener('resize', checkDesktop)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDesktop)
})
</script>

<style scoped>
.mobile-nav {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100vw;
  max-width: 100vw;
  height: 54px;
  background: linear-gradient(180deg, var(--surface-2) 0%, rgba(15,11,26,0.98) 100%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-navbar);
  padding: 0 var(--space-3);
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
}

@media (max-width: 767px) {
  .mobile-nav {
    display: flex;
  }
}

.burger-btn,
.profile-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-petal);
}

.burger-btn:hover,
.profile-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.burger-btn:active,
.profile-btn:active {
  transform: scale(0.95);
}

.mobile-logo {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-bright) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-decoration: none;
  margin-left: var(--space-2);
}

.mobile-menu {
  position: fixed;
  top: 54px;
  left: 0;
  right: 0;
  width: 100vw;
  max-width: 100vw;
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface-1) 100%);
  border-bottom: 1px solid var(--border-default);
  max-height: calc(100vh - 54px);
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
  z-index: calc(var(--z-navbar) + 10);
  box-sizing: border-box;
}

.menu-items {
  display: flex;
  flex-direction: column;
  padding: var(--space-3);
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-petal);
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  background: linear-gradient(180deg, var(--accent) 0%, var(--accent-2) 100%);
  border-radius: 0 var(--radius-full) var(--radius-full) 0;
  transition: width var(--duration-base) var(--ease-petal);
  opacity: 0;
}

.menu-item:hover {
  background: var(--surface-4);
  color: var(--text-primary);
  transform: translateX(4px);
}

.menu-item.router-link-active {
  background: linear-gradient(135deg, var(--accent-subtle) 0%, var(--accent-2-subtle) 100%);
  color: var(--accent);
}

.menu-item.router-link-active::before {
  width: 4px;
  opacity: 1;
}

.menu-item svg {
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity var(--duration-base) var(--ease-petal);
}

.menu-item:hover svg,
.menu-item.router-link-active svg {
  opacity: 1;
  color: var(--accent);
}

.menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5,4,8,0.7);
  backdrop-filter: blur(4px);
  z-index: calc(var(--z-navbar) + 5);
}

/* Transitions */
.menu-enter-active,
.menu-leave-active {
  transition: all 0.25s var(--ease-petal);
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
