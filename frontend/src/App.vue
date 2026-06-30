<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed }">
    <SakuraOverlay />

    <SidebarNavigation />
    
    <NavBar />
    
    <main class="main-content" :style="{ paddingLeft: sidebarPadding }">
      <router-view />
    </main>
    
    <MobileNavigation />

    <ToastContainer />

    <PwaUpdateNotification />
    
    <!-- Плавающий плеер -->
    <Teleport to="body">
      <FloatingPlayer
        v-if="floatingPlayerState.show"
        :visible="floatingPlayerState.show"
        :anime-id="floatingPlayerState.animeId ?? undefined"
        :anime-title="floatingPlayerState.animeTitle"
        :episode="floatingPlayerState.episode ?? undefined"
        :season="floatingPlayerState.season ? Number(floatingPlayerState.season) : undefined"
        :player-link="floatingPlayerState.playerLink"
        :translation-id="floatingPlayerState.translationId ?? undefined"
        :start-time="floatingPlayerState.startTime"
        @close="closeFloatingPlayer"
      />
    </Teleport>
    
    <!-- Чат поддержки -->
    <!-- <MiniSupportChat /> -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, provide, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useFloatingPlayerStore } from '@/stores/floating-player'
import { useSidebar } from '@/composables/useSidebar'
import SakuraOverlay from '@/components/effects/SakuraOverlay.vue'
import NavBar from '@/components/Navigation/NavBar.vue'
import SidebarNavigation from '@/components/Navigation/SidebarNavigation.vue'
import MobileNavigation from '@/components/Navigation/MobileNavigation.vue'
import ToastContainer from '@/components/Notifications/ToastContainer.vue'
import PwaUpdateNotification from '@/components/Notifications/PwaUpdateNotification.vue'
import FloatingPlayer from '@/components/Players/FloatingPlayer.vue'
import MiniSupportChat from '@/components/Chat/MiniSupportChat.vue'

const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const floatingPlayerStore = useFloatingPlayerStore()
const { isCollapsed } = useSidebar()

const route = useRoute()

const sidebarPadding = computed(() => {
  if (window.innerWidth <= 767) {
    return '0px'
  }
  const collapsedWidth = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width-collapsed').trim() || '64px'
  const normalWidth = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width').trim() || '248px'
  return isCollapsed.value ? collapsedWidth : normalWidth
})

const floatingPlayerState = ref({
  show: false,
  animeId: null as number | null,
  animeTitle: '',
  episode: null as number | null,
  season: null as string | null,
  playerLink: '',
  translationId: null as number | null,
  startTime: 0
})

watch(() => floatingPlayerStore.currentAnime, (anime) => {
  if (anime) {
    floatingPlayerState.value = {
      show: true,
      animeId: anime.anime_id,
      animeTitle: anime.anime_title,
      episode: anime.episode,
      season: anime.season,
      playerLink: anime.player_link,
      translationId: anime.translation_id,
      startTime: anime.start_time || 0
    }
  }
}, { immediate: true })

const closeFloatingPlayer = () => {
  floatingPlayerStore.clearCurrentAnime()
  floatingPlayerState.value.show = false
}

provide('auth', authStore)
provide('settings', settingsStore)

const handleResize = () => {
  if (window.innerWidth <= 1023) {
    // сайдбар скрывается через display:none
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}

.app {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.main-content {
  flex: 1;
  width: 100%;
  padding-top: var(--navbar-height, 64px);
  transition: padding-left 0.3s ease;
}
</style>