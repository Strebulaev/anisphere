<template>
  <div class="anime-view">
    <NavBar />

    <div class="container">
      <!-- Заголовок страницы -->
      <PageTitle
        :title="pageTitle"
        :count="currentSection === 'catalog' ? catalogTotalCount : undefined"
        :description="pageDescription"
      />

      <!-- Навигация по секциям -->
      <div class="section-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="switchSection(tab.key)"
          :class="['tab-btn', { active: currentSection === tab.key }]"
          type="button"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <!-- Содержимое секций -->
      <div class="section-content">
        <!-- Секция: Каталог -->
        <transition name="fade" mode="out-in">
          <div v-if="currentSection === 'catalog'" key="catalog" class="catalog-section">
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
              @refresh="fetchCatalog"
              @filter-change="handleCatalogFilterChange"
              @shuffle="shuffleCatalog"
              @unshuffle="unshuffleCatalog"
              @anime-click="goToDetail"
              @watch-anime="startWatching"
            />
          </div>

          <!-- Секция: Онгоинги -->
          <div v-else-if="currentSection === 'ongoings'" key="ongoings" class="ongoings-section">
            <AnimeSection
              type="ongoings"
              title="Онгоинги"
              :anime-list="ongoings"
              :loading="ongoingsLoading"
              :error="ongoingsError"
              :show-shuffle="true"
              :show-filters="true"
              :is-shuffled="isShuffled.ongoings"
              @refresh="fetchOngoings"
              @shuffle="shuffleOngoings"
              @unshuffle="unshuffleOngoings"
              @anime-click="goToDetail"
              @watch-anime="startWatching"
            />
          </div>

          <!-- Секция: Рекомендации -->
          <div v-else-if="currentSection === 'recommendations'" key="recommendations" class="recommendations-section">
            <RecommendationsView />
          </div>

          <!-- Секция: Анонсы -->
          <div v-else-if="currentSection === 'announcements'" key="announcements" class="announcements-section">
            <AnimeSection
              type="announcements"
              title="Анонсы"
              :anime-list="announcements"
              :loading="announcementsLoading"
              :error="announcementsError"
              :show-shuffle="true"
              :show-filters="true"
              :is-shuffled="isShuffled.announcements"
              @refresh="fetchAnnouncements"
              @shuffle="shuffleAnnouncements"
              @unshuffle="unshuffleAnnouncements"
              @anime-click="goToDetail"
              @watch-anime="startWatching"
            />
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '@/components/Navigation/NavBar.vue'
import { PageTitle } from '@/components/Info'
import { AnimeSection } from '@/components/AnimeSections'
import CatalogView from './CatalogView.vue'
import RecommendationsView from './RecommendationsView.vue'
import { useAnimeSections, type AnimeSection as SectionType } from '@/composables/useAnimeSections'
import type { Anime } from '@/types'

const router = useRouter()

const {
  currentSection,
  catalogAnime,
  ongoings,
  recommendations,
  announcements,
  catalogLoading,
  ongoingsLoading,
  announcementsLoading,
  recommendationsLoading,
  catalogError,
  ongoingsError,
  announcementsError,
  recommendationsError,
  catalogPage,
  catalogTotalPages,
  catalogTotalCount,
  isShuffled,
  switchSection,
  fetchCatalog,
  fetchOngoings,
  fetchRecommendations,
  fetchAnnouncements
} = useAnimeSections()

// Текущие фильтры каталога
const currentCatalogFilters = ref<any>({})

// Функции перемешивания для каждой секции
const shuffleOngoings = () => {
  if (ongoings.value.length > 0) {
    const shuffled = [...ongoings.value].sort(() => Math.random() - 0.5)
    ongoings.value = shuffled
    isShuffled.value.ongoings = true
  }
}

const unshuffleOngoings = () => {
  isShuffled.value.ongoings = false
  fetchOngoings()
}

const shuffleRecommendations = () => {
  if (recommendations.value.length > 0) {
    const shuffled = [...recommendations.value].sort(() => Math.random() - 0.5)
    recommendations.value = shuffled
    isShuffled.value.recommendations = true
  }
}

const unshuffleRecommendations = () => {
  isShuffled.value.recommendations = false
  fetchRecommendations()
}

const shuffleAnnouncements = () => {
  if (announcements.value.length > 0) {
    const shuffled = [...announcements.value].sort(() => Math.random() - 0.5)
    announcements.value = shuffled
    isShuffled.value.announcements = true
  }
}

const unshuffleAnnouncements = () => {
  isShuffled.value.announcements = false
  fetchAnnouncements()
}

const shuffleCatalog = () => {
  if (catalogAnime.value.length > 0) {
    const shuffled = [...catalogAnime.value].sort(() => Math.random() - 0.5)
    catalogAnime.value = shuffled
    isShuffled.value.catalog = true
  }
}

const unshuffleCatalog = () => {
  isShuffled.value.catalog = false
  fetchCatalog(1)
}

const tabs = [
  { key: 'catalog' as SectionType, label: 'Каталог', icon: '📚' },
  { key: 'ongoings' as SectionType, label: 'Онгоинги', icon: '🔥' },
  { key: 'recommendations' as SectionType, label: 'Рекомендации', icon: '⭐' },
  { key: 'announcements' as SectionType, label: 'Анонсы', icon: '📢' }
]

// Переход на случайное аниме при клике на вкладку
const handleRandomClick = async () => {
  try {
    const animeApi = (await import('@/api/anime')).default
    const randomAnime = await animeApi.getRandomAnime()
    if (randomAnime) {
      router.push(`/anime/${randomAnime.id}`)
    }
  } catch (err) {
    console.error('Ошибка при получении случайного аниме:', err)
  }
}

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    catalog: 'Каталог аниме',
    ongoings: 'Онгоинги',
    recommendations: 'Рекомендации',
    announcements: 'Анонсы'
  }
  return titles[currentSection.value] || 'Каталог аниме'
})

const pageDescription = computed(() => {
  const descriptions: Record<string, string> = {
    catalog: 'Исследуйте весь каталог аниме с фильтрами и сортировкой',
    ongoings: 'Аниме, которые сейчас выходят',
    recommendations: 'Персональные рекомендации на основе ваших предпочтений',
    announcements: 'Предстоящие релизы аниме'
  }
  return descriptions[currentSection.value] || 'Исследуйте каталог аниме'
})

const handlePageChange = (page: number) => {
  fetchCatalog(page, currentCatalogFilters.value)
}

const handleCatalogFilterChange = (filters: any) => {
  currentCatalogFilters.value = filters
  fetchCatalog(1, filters)
}

const goToDetail = (anime: Anime) => {
  router.push(`/anime/${anime.id}`)
}

const handleAnimeClick = (anime: Anime) => {
  goToDetail(anime)
}

const startWatching = (anime: Anime) => {
  router.push(`/anime/${anime.id}/watch`)
}
</script>

<style scoped>
.anime-view {
  min-height: 100vh;
  background-color: var(--color-background);
  padding-top: 5px;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}

.section-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.tab-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background-color: var(--color-background-active);
}

.tab-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.random-tab {
  background: linear-gradient(135deg, #9333ea, var(--color-accent));
  border-color: transparent;
  color: white;
}

.random-tab:hover {
  background: linear-gradient(135deg, var(--color-accent), #9333ea);
  border-color: transparent;
  color: white;
  transform: scale(1.02);
}

.tab-icon {
  font-size: 1.125rem;
}

.tab-label {
  font-size: 0.9375rem;
}

.section-content {
  min-height: 600px;
}

.catalog-section,
.ongoings-section,
.recommendations-section,
.announcements-section {
  width: 100%;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s var(--transition-smooth);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .container {
    padding: 1.5rem 1rem 3rem;
  }

  .section-tabs {
    gap: 0.375rem;
    margin-bottom: 1.5rem;
  }

  .tab-btn {
    padding: 0.75rem 1.125rem;
    font-size: 0.875rem;
    flex: 1;
    min-width: calc(50% - 0.1875rem);
  }

  .tab-label {
    font-size: 0.8125rem;
  }
}

@media (max-width: 480px) {
  .tab-btn {
    min-width: 100%;
  }
}
</style>
