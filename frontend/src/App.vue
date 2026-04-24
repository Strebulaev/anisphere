<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- Эффект падающих лепестков сакуры -->
    <SakuraOverlay />

    <!-- Боковая навигация (десктоп) -->
    <SidebarNavigation />
    
    <!-- Верхняя панель навигации (десктоп) -->
    <NavBar />
    
    <!-- Основной контент -->
    <main class="main-content">
      <router-view />
    </main>
    
    <!-- Мобильная навигация (бургер-меню) -->
    <MobileNavigation />

    <!-- Тост-уведомления (глобально) -->
    <ToastContainer />

    <!-- PWA: уведомление о новой версии -->
    <PwaUpdateNotification />

    <!-- Глобальный плавающий плеер -->
    <FloatingPlayer
      :visible="floatingPlayerState.show"
      :anime-id="floatingPlayerState.animeId"
      :anime-title="floatingPlayerState.animeTitle"
      :episode="floatingPlayerState.episode"
      :season="floatingPlayerState.season"
      :player-link="floatingPlayerState.playerLink"
      :translation-id="floatingPlayerState.translationId"
      :start-time="floatingPlayerState.startTime"
      @close="closeFloatingPlayer"
    />

    <!-- Мини-чат поддержки -->
    <MiniSupportChat />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, reactive } from 'vue'
import NavBar from '@/components/Navigation/NavBar.vue'
import SidebarNavigation from '@/components/Navigation/SidebarNavigation.vue'
import MobileNavigation from '@/components/Navigation/MobileNavigation.vue'
import ToastContainer from '@/components/Notifications/ToastContainer.vue'
import PwaUpdateNotification from '@/components/Notifications/PwaUpdateNotification.vue'
import FloatingPlayer from '@/components/Players/FloatingPlayer.vue'
import MiniSupportChat from '@/components/Chat/MiniSupportChat.vue'
import SakuraOverlay from '@/components/effects/SakuraOverlay.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { initGlobalWebSocket } from '@/composables/useGlobalWebSocket'
import { useNotificationStore } from '@/stores/notifications'
import { useReminderNotifier } from '@/composables/useReminderNotifier'
import { usePresence } from '@/composables/usePresence'

const { isCollapsed } = useSidebar()
const authStore = useAuthStore()
const notifStore = useNotificationStore()

// Глобальное состояние плавающего плеера
const floatingPlayerState = reactive({
  show: false,
  animeId: 0,
  animeTitle: '',
  episode: 1,
  season: 1,
  playerLink: '',
  translationId: null as number | string | null,
  startTime: 0
})

// Слушаем изменения из localStorage (событие синхронизации между вкладками)
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'floating_player_open') {
      const data = localStorage.getItem('floating_player_data')
      if (data) {
        try {
          const parsed = JSON.parse(data)
          Object.assign(floatingPlayerState, parsed, { show: true })
        } catch {}
      } else {
        floatingPlayerState.show = false
      }
    }
  })

  // Проверяем при загрузке
  const savedData = localStorage.getItem('floating_player_data')
  if (savedData) {
    try {
      const parsed = JSON.parse(savedData)
      Object.assign(floatingPlayerState, parsed, { show: true })
    } catch {}
  }
}

const closeFloatingPlayer = (returnTime?: number) => {
  // Если есть время возврата, обновляем startTime для синхронизации
  if (returnTime !== undefined && returnTime > 0) {
    floatingPlayerState.startTime = returnTime
  }
  
  floatingPlayerState.show = false
  localStorage.removeItem('floating_player_data')
  localStorage.setItem('floating_player_open', '')
  setTimeout(() => localStorage.removeItem('floating_player_open'), 100)
}

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
  background: var(--surface-1);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Фоновый узор сакуры */
.app::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(255,126,179,0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(168,197,226,0.03) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(212,165,201,0.02) 0%, transparent 40%);
  pointer-events: none;
  z-index: 0;
}

.main-content {
  flex: 1;
  min-height: 100vh;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

/* Десктоп: отступ для навбара */
@media (min-width: 768px) {
  .main-content {
    padding-bottom: 0;
    padding-left: var(--sidebar-width);
    padding-top: var(--navbar-height);
    transition: padding-left var(--duration-slow) var(--ease-petal);
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

/* Мобильные устройства: отступ для мобильного меню */
@media (max-width: 767px) {
  .main-content {
    padding: 54px 0 0 0;
  }
  
  /* Все страницы должны иметь отступ сверху */
  .main-content > * {
    margin-top: 0 !important;
  }
}
</style>