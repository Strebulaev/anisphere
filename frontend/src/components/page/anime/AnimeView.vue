<template>
  <div class="anime-view">
    <NavBar />
    <div class="av-container">

      <!-- ══ Табы ═══════════════════════════════════════════════ -->
      <div class="av-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['av-tab', { active: currentSection === tab.key }]"
          @click="tab.key === 'currently_watching' ? switchCurrentlyWatching() : handleSwitchSection(tab.key)"
          type="button"
        >
          <span class="av-tab-icon">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
          <span v-if="tab.key === 'ongoings' && ongoingCount" class="av-tab-badge">{{ ongoingCount }}</span>
        </button>
      </div>

      <!-- ══ Контент ════════════════════════════════════════════ -->
      <transition name="av-fade" mode="out-in">

        <!-- 📚 Каталог -->
        <div v-if="currentSection === 'catalog'" key="catalog">
          <CatalogView
            :anime-list="catalogAnime"
            :loading="catalogLoading"
            :error="catalogError"
            :page="catalogPage"
            :total-pages="catalogTotalPages"
            :total-count="catalogTotalCount"
            :show-shuffle="true"
            :is-shuffled="isShuffled.catalog"
            @page-change="handlePageChange"
            @refresh="fetchCatalog(1)"
            @filter-change="handleCatalogFilterChange"
            @shuffle="shuffleCatalog"
            @unshuffle="unshuffleCatalog"
            @anime-click="goToDetail"
            @watch-anime="startWatching"
          />
        </div>

        <!-- 🔥 Онгоинги -->
        <div v-else-if="currentSection === 'ongoings'" key="ongoings">
          <OngoingsView
            :anime="ongoings"
            :loading="ongoingsLoading"
            :error="ongoingsError"
            :viewers-map="viewersMap"
            @refresh="fetchOngoings"
          />
        </div>

        <!-- ⭐ Рекомендации -->
        <div v-else-if="currentSection === 'recommendations'" key="recommendations">
          <RecommendationsView />
        </div>

        <!-- 📢 Анонсы -->
        <div v-else-if="currentSection === 'announcements'" key="announcements">
          <AnnouncementsView
            :anime="announcements"
            :loading="announcementsLoading"
            :error="announcementsError"
            @refresh="fetchAnnouncements"
          />
        </div>

        <!-- 👁 Сейчас смотрят -->
        <div v-else-if="(currentSection as string) === 'currently_watching'" key="currently_watching">
          <CurrentlyWatchingView
            :anime="currentlyWatching"
            :loading="currentlyWatchingLoading"
            :error="currentlyWatchingError"
            @refresh="fetchCurrentlyWatching"
          />
        </div>

      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NavBar from '@/components/Navigation/NavBar.vue'
import CatalogView from './CatalogView.vue'
import OngoingsView from './OngoingsView.vue'
import RecommendationsView from './RecommendationsView.vue'
import AnnouncementsView from './AnnouncementsView.vue'
import CurrentlyWatchingView from './CurrentlyWatchingView.vue'
import { useAnimeSections, type AnimeSection as SectionType } from '@/composables/useAnimeSections'
import type { FilterState } from '@/components/Filters/AnimeFilterBar.vue'
import apiClient from '@/api/client'
import type { Anime } from '@/types'

const router = useRouter()
const route = useRoute()

const {
  currentSection,
  catalogAnime, ongoings, announcements,
  catalogLoading, ongoingsLoading, announcementsLoading,
  catalogError, ongoingsError, announcementsError,
  catalogPage, catalogTotalPages, catalogTotalCount,
  isShuffled,
  switchSection, fetchCatalog, fetchOngoings, fetchAnnouncements,
} = useAnimeSections()

const ongoingCount = computed(() => ongoings.value.length || null)

// Вкладка "Сейчас смотрят"
const currentlyWatching = ref<any[]>([])
const currentlyWatchingLoading = ref(false)
const currentlyWatchingError = ref<string | null>(null)

const fetchCurrentlyWatching = async () => {
  currentlyWatchingLoading.value = true
  currentlyWatchingError.value = null
  try {
    const res = await apiClient.get('/anime/currently-watching/')
    currentlyWatching.value = res.data?.results || []
  } catch (e: any) {
    currentlyWatchingError.value = 'Не удалось загрузить'
    currentlyWatching.value = []
  } finally {
    currentlyWatchingLoading.value = false
  }
}

// Авто-обновление «Сейчас смотрят» каждые 30 сек пока вкладка активна
let cwRefreshTimer: ReturnType<typeof setInterval> | null = null

const startCwPolling = () => {
  stopCwPolling()
  cwRefreshTimer = setInterval(() => {
    if ((currentSection.value as string) === 'currently_watching') {
      fetchCurrentlyWatching()
    }
  }, 30_000)
}

const stopCwPolling = () => {
  if (cwRefreshTimer !== null) {
    clearInterval(cwRefreshTimer)
    cwRefreshTimer = null
  }
}

const switchCurrentlyWatching = () => {
  currentSection.value = 'currently_watching' as any
  // Сохраняем в localStorage и обновляем URL
  try { localStorage.setItem('anime_active_section', 'currently_watching') } catch {}
  router.replace({ path: route.path, query: { section: 'currently_watching' } })
  fetchCurrentlyWatching()
  startCwPolling()
}

// Останавливаем поллинг при переходе на другую вкладку
const origSwitchSection = switchSection
const handleSwitchSection = (key: any) => {
  stopCwPolling()
  origSwitchSection(key)
  // Обновляем URL для всех вкладок кроме currently_watching (она обновляет сама)
  if (key !== 'currently_watching') {
    router.replace({ path: route.path, query: { section: key } })
  }
}

import { onUnmounted } from 'vue'
onUnmounted(() => stopCwPolling())

onMounted(() => {
  // Если сохранённая вкладка — «Сейчас смотрят», загружаем данные сразу
  if ((currentSection.value as string) === 'currently_watching') {
    fetchCurrentlyWatching()
    startCwPolling()
  }
})

// viewersMap для онгоингов — { [anime_id]: viewers_count }
const viewersMap = computed<Record<number, number>>(() => {
  const map: Record<number, number> = {}
  for (const a of currentlyWatching.value) {
    if (a.id && a.viewers_count) map[a.id] = a.viewers_count
  }
  return map
})

const tabs = [
  { key: 'catalog'           as SectionType, label: 'Каталог',         icon: '📚' },
  { key: 'ongoings'          as SectionType, label: 'Онгоинги',        icon: '🔥' },
  { key: 'recommendations'   as SectionType, label: 'Для вас',         icon: '⭐' },
  { key: 'announcements'     as SectionType, label: 'Анонсы',          icon: '📢' },
  { key: 'currently_watching' as any,        label: 'Сейчас смотрят',  icon: '👁' },
]

// Каталог
const currentCatalogFilters = ref<FilterState>({})
const handlePageChange = (page: number) => fetchCatalog(page, currentCatalogFilters.value)
const handleCatalogFilterChange = (filters: FilterState) => {
  currentCatalogFilters.value = filters
  fetchCatalog(1, filters)
}

// Применение начального фильтра по жанру из URL
onMounted(() => {
  const genreName = route.query.genre_name as string
  if (genreName) {
    currentCatalogFilters.value = { genres: [genreName] }
    fetchCatalog(1, currentCatalogFilters.value)
  }
})
const shuffleCatalog = () => {
  if (catalogAnime.value.length) {
    catalogAnime.value = [...catalogAnime.value].sort(() => Math.random() - 0.5)
    isShuffled.value.catalog = true
  }
}
const unshuffleCatalog = () => {
  isShuffled.value.catalog = false
  fetchCatalog(1)
}

const goToDetail = (anime: Anime) => {
  // Если аниме часть франшизы — идём на страницу франшизы
  if ((anime as any).franchise_id) {
    router.push(`/franchise/${(anime as any).franchise_id}`)
  } else {
    router.push(`/anime/${anime.id}`)
  }
}
const startWatching = (anime: Anime) => router.push(`/anime/${anime.id}/watch`)
</script>

<style scoped>
.anime-view {
  min-height: 100vh;
  background: var(--surface-1);
}

.av-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) var(--space-16);
}

/* ── Табы ─────────────────────────────────────────────────── */
.av-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.av-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 40px;
  padding: 0 var(--space-5);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  position: relative;
}

.av-tab:hover {
  background: var(--surface-4);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.av-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.av-tab-icon { font-size: 16px; line-height: 1; }

.av-tab-badge {
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  background: rgba(255,255,255,0.25);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.av-tab:not(.active) .av-tab-badge {
  background: var(--surface-5);
  color: var(--text-tertiary);
}

/* ── Переходы ─────────────────────────────────────────────── */
.av-fade-enter-active,
.av-fade-leave-active { transition: opacity .2s; }
.av-fade-enter-from,
.av-fade-leave-to { opacity: 0; }

@media (max-width: 767px) {
  .av-container { padding: var(--space-4) var(--space-3) var(--space-10); }
  .av-tab { flex: 1; justify-content: center; min-width: calc(50% - var(--space-1)); }
}
</style>
