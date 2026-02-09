<template>
  <nav class="navbar">
    <div class="navbar-content">
      <!-- Логотип -->
      <div class="navbar-logo">
        <router-link to="/" class="logo-link">
          <span class="logo-text">AnimeCore</span>
        </router-link>
      </div>

      <!-- Поисковая строка -->
      <div class="navbar-search">
        <SearchBar />
      </div>

      <!-- Правая часть -->
      <div class="navbar-actions">
        <!-- Индикатор Аниме-ДНК -->
        <AnimeDNAIndicator />

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
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import SearchBar from './SearchBar.vue'
import AnimeDNAIndicator from './AnimeDNAIndicator.vue'

const route = useRoute()
const authStore = useAuthStore()

const userAvatar = computed(() => {
  return authStore.user?.avatar
})

const isOnline = computed(() => {
  return authStore.user?.is_online ?? false
})

const hasNotifications = computed(() => {
  return (authStore.user as any)?.unread_notifications_count ?? 0 > 0
})
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
  display: box;
  align-items: center;
}

.navbar-content {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  width: 100%;
}

/* Логотип */
.navbar-logo {
  display: none;
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

/* Поиск */
.navbar-search {
  flex: 1;
  max-width: 400px;
  margin: 0 24px;
}

/* Правая часть */
.navbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
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
  color: var(--color-text);
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
@media (max-width: 1023px) {
  .navbar {
    left: 0;
  }

  .navbar-logo {
    display: block;
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