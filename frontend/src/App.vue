<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- Боковая навигация (десктоп) -->
    <SidebarNavigation />
    
    <!-- Верхняя панель навигации (десктоп) -->
    <NavBar />
    
    <!-- Основной контент -->
    <main class="main-content">
      <router-view />
    </main>
    
    <!-- Нижняя панель навигации (мобильная) -->
    <BottomNavigation />

    <!-- Тост-уведомления (глобально) -->
    <ToastContainer />

    <!-- PWA: уведомление о новой версии -->
    <PwaUpdateNotification />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import NavBar from '@/components/Navigation/NavBar.vue'
import SidebarNavigation from '@/components/Navigation/SidebarNavigation.vue'
import BottomNavigation from '@/components/Navigation/BottomNavigation.vue'
import ToastContainer from '@/components/Notifications/ToastContainer.vue'
import PwaUpdateNotification from '@/components/Notifications/PwaUpdateNotification.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { initGlobalWebSocket } from '@/composables/useGlobalWebSocket'
import { useNotificationStore } from '@/stores/notifications'
import { useReminderNotifier } from '@/composables/useReminderNotifier'
import { usePresence } from '@/composables/usePresence'

const { isCollapsed } = useSidebar()
const authStore = useAuthStore()
const notifStore = useNotificationStore()

// Запускаем нотифайер напоминаний (только если авторизован)
if (authStore.isAuthenticated) {
  useReminderNotifier()
}

// Запускаем постоянный heartbeat онлайн-статуса
// Пингует /api/users/heartbeat/ каждые 2 минуты
usePresence()

onMounted(() => {
  if (authStore.isAuthenticated) {
    initGlobalWebSocket()
    notifStore.fetchNotifications()
    notifStore.fetchReminders()
  }
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background-color: var(--surface-1);
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  /* мобиль: navbar сверху + bottom-nav снизу */
  padding-top: var(--bottom-nav-height);
  padding-bottom: var(--bottom-nav-height);
  min-height: 100vh;
}

@media (min-width: 768px) {
  .main-content {
    padding-bottom: 0;
    padding-left: var(--sidebar-width);
    padding-top: var(--navbar-height);
    transition: padding-left var(--duration-slow) var(--ease-out);
  }

  .app.sidebar-collapsed .main-content {
    padding-left: var(--sidebar-width-collapsed);
  }
}

@media (min-width: 1024px) {
  .main-content {
    padding-top: var(--navbar-height);
  }
}
</style>