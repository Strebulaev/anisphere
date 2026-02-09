<template>
  <div class="app">
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
import { onMounted } from 'vue'
import NavBar from '@/components/NavBar.vue'
import SidebarNavigation from '@/components/SidebarNavigation.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

onMounted(() => {
  console.log('AnimeCore App mounted')
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background-color: var(--color-background);
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding-top: 120px;
  padding-bottom: var(--height-nav-mobile);
}

@media (min-width: 768px) {
  .main-content {
    padding-bottom: 0;
    padding-left: 240px;
    padding-top: 120px;
  }
}

@media (min-width: 1024px) {
  .main-content {
    padding-top: 72px;
  }
}
</style>