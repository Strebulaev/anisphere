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
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import NavBar from '@/components/Navigation/NavBar.vue'
import SidebarNavigation from '@/components/Navigation/SidebarNavigation.vue'
import BottomNavigation from '@/components/Navigation/BottomNavigation.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { initGlobalWebSocket } from '@/composables/useGlobalWebSocket'

const { isCollapsed } = useSidebar()
const authStore = useAuthStore()

onMounted(() => {
  console.log('anisphere App mounted')
  
  // Инициализировать WebSocket после авторизации
  if (authStore.isAuthenticated) {
    initGlobalWebSocket()
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