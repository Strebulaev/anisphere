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
import { computed, ref } from 'vue'
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
  { key: 'ongoings',         label: 'Онгоинги',    icon: '🔥', to: '/anime?section=ongoings'         },
  { key: 'recommendations', label: 'Рекомендации', icon: '⭐', to: '/anime?section=recommendations' },
  { key: 'announcements',   label: 'Анонсы',       icon: '📢', to: '/anime?section=announcements'   },
  { key: 'random',          label: 'Рандом',        icon: '🎲', to: null },
]

const randomLoading = ref(false)

const navigateToSection = async (item: any) => {
  // Рандом — запрашиваем бэкенд и переходим на страницу аниме
  if (item.key === 'random') {
    if (randomLoading.value) return
    randomLoading.value = true
    try {
      const { default: apiClient } = await import('@/api/client')
      const res = await apiClient.get('/anime/random/')
      const id = res.data?.id || res.data?.[0]?.id
      if (id) router.push(`/anime/${id}`)
    } catch (e) {
      console.error('Random anime error:', e)
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
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  height: var(--navbar-height);
  background-color: var(--surface-2);
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-navbar);
  display: flex;
  align-items: center;
  transition: left var(--duration-slow) var(--ease-out);
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
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-weight: 500;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  white-space: nowrap;
  cursor: pointer;
  min-height: 32px;
}

.nav-link:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
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

/* ── Действия ───────────────────────────────────────────── */
.navbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-left: auto;
}

.navbar-icon-btn {
  width: 34px;
  height: 34px;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--text-tertiary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    background-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  position: relative;
  border: none;
}

.navbar-icon-btn:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
}

.notification-dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 7px;
  height: 7px;
  background-color: var(--danger);
  border-radius: 50%;
  border: 2px solid var(--surface-2);
}

/* ── Профиль ─────────────────────────────────────────────── */
.navbar-profile {
  display: flex;
  align-items: center;
}

.profile-link {
  text-decoration: none;
}

.profile-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--surface-4);
  border: 2px solid var(--border-default);
  overflow: hidden;
  position: relative;
  cursor: pointer;
  transition: border-color var(--duration-base) var(--ease-out);
}

.profile-avatar:hover {
  border-color: var(--accent);
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
  width: 9px;
  height: 9px;
  background-color: var(--success);
  border-radius: 50%;
  border: 2px solid var(--surface-2);
}

/* ── Адаптивность ──────────────────────────────────────────── */
@media (max-width: 1400px) {
  .navbar-navigation { gap: 0; }
  .nav-link { padding: var(--space-2); }
  .nav-label { display: none; }
  .nav-icon { font-size: var(--text-xl); }
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