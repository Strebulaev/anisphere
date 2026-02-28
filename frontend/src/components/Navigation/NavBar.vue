<template>
  <nav class="navbar">
    <div class="navbar-content">
      <!-- Кнопка бургер-меню (для сворачивания/разворачивания сайдбара) -->
      <!-- <button @click="toggleSidebar" class="burger-btn" type="button" title="Меню">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button> -->

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
          class="nav-link"
          type="button"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </div>

      <!-- Правая часть -->
      <div class="navbar-actions">
        <!-- Индикатор Аниме-ДНК -->
        <!-- <AnimeDNAIndicator /> -->

        <!-- Уведомления -->
        <button class="navbar-icon-btn" title="Уведомления" type="button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span v-if="hasNotifications" class="notification-dot"></span>
        </button>

        <!-- Профиль пользователя -->
        <div class="navbar-profile">
          <router-link to="/profile" class="profile-link">
            <div class="profile-avatar">
              <img v-if="userAvatar" :src="userAvatar" alt="Avatar" class="avatar-image" />
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSidebar } from '@/composables/useSidebar'
import SearchBar from '@/components/Search/SearchBar.vue'
import AnimeDNAIndicator from '@/components/Indicators/AnimeDNAIndicator.vue'

const router = useRouter()
const authStore = useAuthStore()
const { toggleSidebar } = useSidebar()

const searchCategories = [
  { id: 'anime', name: 'Аниме', icon: 'anime', enabled: true, limit: 5 },
  { id: 'users', name: 'Пользователи', icon: 'users', enabled: true, limit: 3 },
  { id: 'playlists', name: 'Плейлисты', icon: 'playlists', enabled: true, limit: 3 }
]

const navigationItems = [
  { key: 'ongoings', label: 'Онгоинги', icon: '🔥', to: '/anime?section=ongoings' },
  { key: 'recommendations', label: 'Рекомендации', icon: '⭐', to: '/anime?section=recommendations' },
  { key: 'announcements', label: 'Анонсы', icon: '📢', to: '/anime?section=announcements' },
  { key: 'random', label: 'Рандом', icon: '🎲', to: '/anime?section=random' },
]

const navigateToSection = (item: any) => {
  const [path, queryStr] = item.to.split('?')
  const params = new URLSearchParams(queryStr)
  const query: Record<string, string> = {}
  params.forEach((value, key) => {
    query[key] = value
  })
  router.replace({ path, query })
}

const userAvatar = computed(() => {
  return authStore.user?.avatar
})

const isOnline = computed(() => {
  return authStore.user?.is_online ?? false
})

const hasNotifications = computed(() => {
  return (authStore.user as any)?.unread_notifications_count ?? 0 > 0
})

const handleSearch = (query: string) => {
  router.push({ path: '/anime', query: { q: query } })
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 1px;
  left: 240px;
  right: 0;
  height: 72px;
  background-color: var(--color-background-secondary);
  z-index: 100;
  display: flex;
  align-items: center;
  transition: left 0.3s ease;
}

.sidebar-collapsed .navbar {
  left: 72px;
}

.navbar-content {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 24px;
  width: 100%;
  gap: 12px;
}

/* Кнопка бургер-меню */
.burger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.burger-btn:hover {
  background-color: var(--color-background-active);
  color: var(--color-text);
  border-color: var(--color-accent);
}

/* Логотип */
.navbar-logo {
  flex-shrink: 0;
}

.logo-link {
  text-decoration: none;
}

.logo-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(90deg, var(--color-accent) 0%, var(--color-accent-teal) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Навигация */
.navbar-navigation {
  display: flex;
  gap: 30px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s var(--transition-smooth);
  white-space: nowrap;
  cursor: pointer;
}

.nav-link:hover {
  background-color: var(--color-background-active);
  color: var(--color-text);
}

.nav-icon {
  font-size: 1rem;
}

.nav-label {
  font-size: 0.875rem;
}

/* Поиск */
.navbar-search {
  width: 400px;
  flex-shrink: 0;
  position: relative;
  z-index: 1001;
}

/* Правая часть */
.navbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

.navbar-icon-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #222222;
  color: var(--color-text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
  position: relative;
  border: none;
}

.navbar-icon-btn:hover {
  background-color: var(--color-background-surface);
  color: #888888;
}

.notification-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background-color: var(--color-accent-pink);
  border-radius: 50%;
  border: 2px solid var(--color-background-secondary);
}

/* Профиль */
.navbar-profile {
  display: flex;
  align-items: center;
}

.profile-link {
  text-decoration: none;
}

.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--color-background-surface);
  border: 2px solid var(--color-divider);
  overflow: hidden;
  position: relative;
  cursor: pointer;
  transition: border-color 0.15s var(--transition-smooth);
}

.profile-avatar:hover {
  border-color: var(--color-accent);
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
  color: var(--color-text-tertiary);
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background-color: var(--color-accent-teal);
  border-radius: 50%;
  border: 2px solid var(--color-background-secondary);
}

/* Адаптивность */
@media (max-width: 1400px) {
  .navbar-navigation {
    gap: 4px;
  }

  .nav-link {
    padding: 8px 12px;
  }

  .nav-label {
    display: none;
  }

  .nav-icon {
    font-size: 1.25rem;
  }
}

@media (max-width: 1023px) {
  .navbar {
    left: 0;
  }

  .navbar-logo {
    display: block;
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