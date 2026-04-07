<template>
  <div class="home-page">

    <!-- ══ Шапка ══════════════════════════════════════════════ -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h1 class="welcome-title">
          Добро пожаловать<span v-if="userName">, {{ userName }}</span>!
        </h1>
        <p class="welcome-subtitle">Что хотите посмотреть сегодня?</p>
      </div>
      <div class="welcome-actions">
        <button class="quick-btn" @click="router.push('/anime')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          Каталог
        </button>
      </div>
    </div>

    <!-- ══ Глобальная загрузка ══════════════════════════════ -->
    <template v-if="loading">
      <div v-for="n in 2" :key="n" class="skeleton-section">
        <div class="skeleton-header">
          <div class="skeleton-title-bar"></div>
        </div>
        <div class="skeleton-track">
          <div v-for="i in 6" :key="i" class="skeleton-card">
            <div class="skeleton-poster"></div>
            <div class="skeleton-info">
              <div class="skeleton-line w80"></div>
              <div class="skeleton-line w55"></div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ══ Ошибка ════════════════════════════════════════════ -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <p class="error-title">Не удалось загрузить контент</p>
      <p class="error-sub">Проверьте соединение и попробуйте ещё раз</p>
      <button class="retry-btn" @click="loadHomeData">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        Повторить
      </button>
    </div>

    <!-- ══ Контент ════════════════════════════════════════════ -->
    <div v-else class="home-content">

      <!-- <SakuraIcon name="play" /> Продолжить просмотр -->
      <section v-if="homeData.continue_watching?.length > 0" class="home-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-icon"> <SakuraIcon name="play" /> </span>
            <h2 class="section-title">Продолжить просмотр</h2>
            <span class="section-count">{{ homeData.continue_watching.length }}</span>
          </div>
        </div>
        <div class="carousel-wrapper">
          <button v-if="!continueAtStart" class="carousel-arrow left" @click="scrollCarousel('continue', -1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <div class="carousel-track" ref="continueTrack" @scroll="updateArrows('continue')">
            <ContinueWatchingCard
              v-for="item in homeData.continue_watching"
              :key="item.anime_id"
              :anime-id="item.anime_id"
              :title="item.title"
              :poster="item.poster"
              :current-episode="item.current_episode"
              :total-episodes="item.total_episodes || 1"
              :progress-percent="item.progress_percent"
            />
          </div>
          <button v-if="!continueAtEnd" class="carousel-arrow right" @click="scrollCarousel('continue', 1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
      </section>

      <!-- <SakuraIcon name="refresh" /> Пересмотреть -->
      <section v-if="homeData.rewatch?.length > 0" class="home-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-icon"> <SakuraIcon name="refresh" /> </span>
            <h2 class="section-title">Пересмотреть</h2>
            <span class="section-count">{{ homeData.rewatch.length }}</span>
          </div>
        </div>
        <div class="carousel-wrapper">
          <button v-if="!rewatchAtStart" class="carousel-arrow left" @click="scrollCarousel('rewatch', -1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <div class="carousel-track" ref="rewatchTrack" @scroll="updateArrows('rewatch')">
            <RewatchCard
              v-for="item in homeData.rewatch"
              :key="item.anime_id"
              :anime-id="item.anime_id"
              :title="item.title"
              :poster="item.poster"
              :completed-date="item.completed_date"
              :user-rating="item.user_rating"
            />
          </div>
          <button v-if="!rewatchAtEnd" class="carousel-arrow right" @click="scrollCarousel('rewatch', 1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
      </section>

      <!-- <SakuraIcon name="target" /> Рекомендации -->
      <section class="home-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-icon"> <SakuraIcon name="target" /> </span>
            <h2 class="section-title">Рекомендации для вас</h2>
          </div>
          <button class="view-all-btn" @click="router.push('/anime')">
            Все
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>

        <div v-if="!homeData.recommendations?.length" class="section-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
          <p>Добавляем рекомендации — <button @click="router.push('/anime')">посмотрите каталог</button></p>
        </div>
        <div v-else class="carousel-wrapper">
          <button v-if="!recsAtStart" class="carousel-arrow left" @click="scrollCarousel('recs', -1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <div class="carousel-track" ref="recsTrack" @scroll="updateArrows('recs')">
            <RecommendationCard
              v-for="item in homeData.recommendations"
              :key="item.anime_id"
              :anime-id="item.anime_id"
              :title="item.title"
              :poster="item.poster"
              :genres="item.genres || []"
              :rating="item.rating"
              :rating-count="item.rating_count || 0"
              :status="item.status || ''"
              :year="item.year"
            />
          </div>
          <button v-if="!recsAtEnd" class="carousel-arrow right" @click="scrollCarousel('recs', 1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
      </section>

      <!-- <SakuraIcon name="fire" /> Популярное -->
      <section class="home-section">
        <div class="section-header">
          <div class="section-title-wrap">
            <span class="section-icon"> <SakuraIcon name="fire" /> </span>
            <h2 class="section-title">Популярное на этой неделе</h2>
          </div>
          <button class="view-all-btn" @click="router.push('/anime?ordering=-score')">
            Все
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </button>
        </div>

        <div v-if="!homeData.trending?.length" class="section-empty">
          <div class="spinner-sm"></div>
          <p>Загружаем популярное...</p>
        </div>
        <div v-else class="carousel-wrapper">
          <button v-if="!trendAtStart" class="carousel-arrow left" @click="scrollCarousel('trend', -1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <div class="carousel-track" ref="trendTrack" @scroll="updateArrows('trend')">
            <RecommendationCard
              v-for="(item, idx) in homeData.trending"
              :key="item.anime_id"
              :anime-id="item.anime_id"
              :title="item.title"
              :poster="item.poster"
              :genres="item.genres || []"
              :rating="item.rating"
              :rating-count="item.rating_count || 0"
              :status="item.status || ''"
              :year="item.year"
              :rank="idx + 1"
            />
          </div>
          <button v-if="!trendAtEnd" class="carousel-arrow right" @click="scrollCarousel('trend', 1)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
      </section>

    </div><!-- /home-content -->


  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { animeApi } from '@/api/anime'
import type { HomeData } from '@/types'
import ContinueWatchingCard from '@/components/Cards/ContinueWatchingCard.vue'
import RewatchCard from '@/components/Cards/RewatchCard.vue'
import RecommendationCard from '@/components/Cards/RecommendationCard.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading  = ref(true)
const error    = ref(false)

const homeData = ref<HomeData>({
  continue_watching: [],
  rewatch: [],
  recommendations: [],
  trending: []
})

// ── Карусели: refs + состояние стрелок ──────────────────────
const continueTrack = ref<HTMLElement | null>(null)
const rewatchTrack  = ref<HTMLElement | null>(null)
const recsTrack     = ref<HTMLElement | null>(null)
const trendTrack    = ref<HTMLElement | null>(null)

const continueAtStart = ref(true);  const continueAtEnd = ref(false)
const rewatchAtStart  = ref(true);  const rewatchAtEnd  = ref(false)
const recsAtStart     = ref(true);  const recsAtEnd     = ref(false)
const trendAtStart    = ref(true);  const trendAtEnd    = ref(false)

const CARD_W = 236   // 220 + 16 gap

type TrackKey = 'continue' | 'rewatch' | 'recs' | 'trend'
const trackMap: Record<TrackKey, { el: () => HTMLElement | null; atStart: any; atEnd: any }> = {
  continue: { el: () => continueTrack.value, atStart: continueAtStart, atEnd: continueAtEnd },
  rewatch:  { el: () => rewatchTrack.value,  atStart: rewatchAtStart,  atEnd: rewatchAtEnd  },
  recs:     { el: () => recsTrack.value,     atStart: recsAtStart,     atEnd: recsAtEnd     },
  trend:    { el: () => trendTrack.value,    atStart: trendAtStart,    atEnd: trendAtEnd    },
}

const updateArrows = (key: TrackKey) => {
  const el = trackMap[key].el()
  if (!el) return
  trackMap[key].atStart.value = el.scrollLeft <= 4
  trackMap[key].atEnd.value   = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4
}

const scrollCarousel = (key: TrackKey, dir: 1 | -1) => {
  const el = trackMap[key].el()
  if (!el) return
  el.scrollBy({ left: dir * CARD_W * 3, behavior: 'smooth' })
}

// ── Данные ───────────────────────────────────────────────────
const userName = computed(() => {
  const user = authStore.user as any
  return user?.display_name || user?.username || null
})

const loadHomeData = async () => {
  loading.value = true
  error.value = false
  try {
    const data = await animeApi.getHomeData()
    homeData.value = data
    await nextTick()
    ;(['continue', 'rewatch', 'recs', 'trend'] as TrackKey[]).forEach(k => updateArrows(k))
  } catch (e) {
    console.error('Ошибка загрузки главной страницы:', e)
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => loadHomeData())
</script>

<style scoped>
/* ═══ Страница ══════════════════════════════════════════════ */
.home-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* ═══ Шапка ═════════════════════════════════════════════════ */
.welcome-section {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-10);
  flex-wrap: wrap;
}

.welcome-title {
  font-size: var(--text-4xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.025em;
  line-height: 1.1;
}

.welcome-title span { color: var(--accent); }

.welcome-subtitle {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
}

.welcome-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.quick-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}

.quick-btn:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.quick-btn.accent {
  background: var(--accent-subtle);
  color: var(--accent);
  border-color: transparent;
}

.quick-btn.accent:hover {
  background: var(--accent);
  color: var(--text-on-accent);
}

/* ═══ Контент ═══════════════════════════════════════════════ */
.home-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

/* ═══ Секция ════════════════════════════════════════════════ */
/* .home-section {} */

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.section-icon {
  font-size: 18px;
  line-height: 1;
}

.section-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.section-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  background: var(--surface-4);
  color: var(--text-tertiary);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
}

.view-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--accent);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: background-color var(--duration-base) var(--ease-out);
}

.view-all-btn:hover { background: var(--accent-subtle); }

/* ═══ Карусель ══════════════════════════════════════════════ */
.carousel-wrapper {
  position: relative;
}

.carousel-track {
  display: flex;
  gap: var(--space-4);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 4px;
}

.carousel-track::-webkit-scrollbar { display: none; }

/* Плавное появление на краях */
.carousel-wrapper::before,
.carousel-wrapper::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 4px;
  width: 40px;
  z-index: 2;
  pointer-events: none;
  transition: opacity var(--duration-base);
}

.carousel-wrapper::before {
  left: 0;
  background: linear-gradient(to right, var(--surface-1) 0%, transparent 100%);
  width: 20px;
}

.carousel-wrapper::after {
  right: 0;
  background: linear-gradient(to left, var(--surface-1), transparent);
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(calc(-50% - 2px));
  z-index: 3;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-default);
  background: var(--surface-3);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out),
              background-color var(--duration-base) var(--ease-out),
              transform var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-md);
}

.carousel-wrapper:hover .carousel-arrow { opacity: 1; }

.carousel-arrow:hover {
  background: var(--accent);
  border-color: var(--accent);
  transform: translateY(calc(-50% - 2px)) scale(1.08);
}

.carousel-arrow.left  { left: -12px; }
.carousel-arrow.right { right: -12px; }

/* ═══ Пустое / Ошибка ═══════════════════════════════════════ */
.section-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-10) var(--space-6);
  background: var(--surface-2);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
  color: var(--text-tertiary);
  text-align: center;
}

.section-empty p { margin: 0; font-size: var(--text-sm); }
.section-empty button {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: inherit;
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: text-decoration-color var(--duration-base);
}
.section-empty button:hover { text-decoration-color: var(--accent); }

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: 80px var(--space-6);
  color: var(--text-secondary);
  text-align: center;
}

.error-icon { color: var(--danger); opacity: 0.7; }
.error-title { font-size: var(--text-lg); font-weight: 600; color: var(--text-primary); margin: 0; }
.error-sub   { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; }

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 38px;
  padding: 0 var(--space-5);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out);
}

.retry-btn:hover { background: var(--accent-hover); }

/* ═══ Скелетоны ═════════════════════════════════════════════ */
.skeleton-section { margin-bottom: var(--space-10); }

.skeleton-header { margin-bottom: var(--space-4); }

.skeleton-title-bar {
  height: 22px;
  width: 200px;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

.skeleton-track {
  display: flex;
  gap: var(--space-4);
  overflow: hidden;
}

.skeleton-card { flex: 0 0 220px; }

.skeleton-poster {
  width: 100%;
  height: 240px;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-2);
}

.skeleton-info { display: flex; flex-direction: column; gap: var(--space-1); }

.skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-xs);
}

.skeleton-line.w80 { width: 80%; }
.skeleton-line.w55 { width: 55%; }

.spinner-sm {
  width: 24px;
  height: 24px;
  border: 2.5px solid var(--border-strong);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ═══ Адаптив ═══════════════════════════════════════════════ */
@media (max-width: 767px) {
  .home-page {
    padding: var(--space-4) var(--space-3);
  }

  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: var(--space-7);
  }

  .welcome-title { font-size: var(--text-2xl); }

  .carousel-arrow { display: none; }

  .skeleton-poster { height: 190px; }
  .skeleton-card   { flex: 0 0 155px; }
}

/* ═══ АДАПТИВНЫЕ СТИЛИ HOME ═══ */

/* xs: 320px */
@media (max-width: 374px) {
  .home-page {
    padding: 0.5rem;
  }
  
  .home-header {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .home-logo {
    font-size: 1.25rem;
  }
  
  .home-search {
    height: 2.5rem;
    padding: 0 0.75rem;
    font-size: 0.875rem;
  }
  
  .home-nav {
    gap: 0.25rem;
    padding: 0.25rem;
    overflow-x: auto;
  }
  
  .home-nav-item {
    padding: 0.375rem 0.5rem;
    font-size: 0.75rem;
    white-space: nowrap;
  }
  
  .home-section {
    margin-bottom: 1rem;
  }
  
  .home-section-header {
    padding: 0.5rem;
    margin-bottom: 0.25rem;
  }
  
  .home-section-title {
    font-size: 1rem;
  }
  
  .home-section-more {
    font-size: 0.75rem;
  }
  
  .home-carousel {
    padding: 0.5rem;
  }
  
  .home-carousel-track {
    gap: 0.5rem;
  }
  
  .home-carousel-item {
    min-width: 130px;
  }
  
  .home-poster {
    height: 185px;
    border-radius: 0.375rem;
  }
  
  .home-poster-overlay {
    padding: 0.375rem;
  }
  
  .home-poster-title {
    font-size: 0.75rem;
  }
  
  .home-poster-meta {
    font-size: 0.625rem;
    gap: 0.25rem;
  }
  
  .home-poster-rating {
    font-size: 0.625rem;
    padding: 0.125rem 0.25rem;
  }
  
  .home-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    padding: 0.5rem;
  }
  
  .home-grid-item {
    min-width: 0;
  }
  
  .home-grid-poster {
    aspect-ratio: 2/3;
    border-radius: 0.375rem;
  }
  
  .home-grid-title {
    font-size: 0.75rem;
    margin-top: 0.25rem;
  }
  
  .home-grid-meta {
    font-size: 0.625rem;
  }
  
  .home-banner {
    height: 150px;
    border-radius: 0.5rem;
    margin: 0.5rem;
  }
  
  .home-banner-title {
    font-size: 1rem;
  }
  
  .home-banner-text {
    font-size: 0.75rem;
  }
  
  .home-banner-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
  
  .home-skeleton {
    padding: 0.5rem;
  }
  
  .home-skeleton-track {
    gap: 0.5rem;
  }
  
  .home-skeleton-card {
    min-width: 130px;
  }
  
  .home-skeleton-poster {
    height: 185px;
    border-radius: 0.375rem;
  }
  
  .home-skeleton-title {
    height: 0.75rem;
    margin-top: 0.375rem;
    border-radius: 0.25rem;
  }
  
  .home-skeleton-meta {
    height: 0.625rem;
    width: 60%;
    margin-top: 0.25rem;
    border-radius: 0.25rem;
  }
  
  .home-loading-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  
  .home-loading-card {
    border-radius: 0.375rem;
  }
  
  .home-loading-poster {
    aspect-ratio: 2/3;
    border-radius: 0.375rem;
  }
  
  .home-loading-title {
    height: 0.75rem;
    margin-top: 0.375rem;
    border-radius: 0.25rem;
  }
  
  .home-loading-meta {
    height: 0.625rem;
    width: 50%;
    margin-top: 0.25rem;
    border-radius: 0.25rem;
  }
  
  .home-empty {
    padding: 2rem 1rem;
    text-align: center;
  }
  
  .home-empty-icon {
    width: 3rem;
    height: 3rem;
    margin-bottom: 0.5rem;
  }
  
  .home-empty-title {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }
  
  .home-empty-text {
    font-size: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .home-empty-btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .home-error {
    padding: 2rem 1rem;
    text-align: center;
  }
  
  .home-error-icon {
    width: 3rem;
    height: 3rem;
    margin-bottom: 0.5rem;
  }
  
  .home-error-title {
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }
  
  .home-error-text {
    font-size: 0.75rem;
    margin-bottom: 0.75rem;
  }
  
  .home-error-btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
}

/* sm: 375px */
@media (min-width: 375px) and (max-width: 767px) {
  .home-page {
    padding: 0.75rem;
  }
  
  .home-search {
    height: 2.75rem;
  }
  
  .home-carousel-item {
    min-width: 140px;
  }
  
  .home-poster {
    height: 200px;
  }
  
  .home-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  .home-banner {
    height: 180px;
    margin: 0.75rem;
  }
  
  .home-banner-title {
    font-size: 1.25rem;
  }
  
  .home-skeleton-card {
    min-width: 140px;
  }
  
  .home-skeleton-poster {
    height: 200px;
  }
}

/* md: 768px+ */
@media (min-width: 768px) {
  .home-page {
    padding: 1rem;
  }
  
  .home-header {
    padding: 1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .home-logo {
    font-size: 1.5rem;
  }
  
  .home-search {
    height: 3rem;
    padding: 0 1rem;
    max-width: 400px;
  }
  
  .home-nav {
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    overflow-x: auto;
  }
  
  .home-nav-item {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .home-section {
    margin-bottom: 1.5rem;
  }
  
  .home-section-header {
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
  }
  
  .home-section-title {
    font-size: 1.25rem;
  }
  
  .home-section-more {
    font-size: 0.875rem;
  }
  
  .home-carousel {
    padding: 0.75rem 1rem;
  }
  
  .home-carousel-item {
    min-width: 150px;
  }
  
  .home-poster {
    height: 215px;
    border-radius: 0.5rem;
  }
  
  .home-poster-overlay {
    padding: 0.5rem;
  }
  
  .home-poster-title {
    font-size: 0.875rem;
  }
  
  .home-poster-meta {
    font-size: 0.75rem;
  }
  
  .home-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    padding: 1rem;
  }
  
  .home-banner {
    height: 200px;
    margin: 1rem;
    border-radius: 0.75rem;
  }
  
  .home-banner-title {
    font-size: 1.5rem;
  }
  
  .home-banner-text {
    font-size: 0.875rem;
  }
  
  .home-skeleton-card {
    min-width: 150px;
  }
  
  .home-skeleton-poster {
    height: 215px;
  }
  
  .home-loading-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }
  
  .home-empty,
  .home-error {
    padding: 3rem 2rem;
  }
  
  .home-empty-icon,
  .home-error-icon {
    width: 4rem;
    height: 4rem;
  }
  
  .home-empty-title,
  .home-error-title {
    font-size: 1.25rem;
  }
  
  .home-empty-text,
  .home-error-text {
    font-size: 0.875rem;
  }
}

/* tablet-lg: 1024px+ */
@media (min-width: 1024px) {
  .home-page {
    padding: 1.25rem;
  }
  
  .home-carousel-item {
    min-width: 160px;
  }
  
  .home-poster {
    height: 230px;
  }
  
  .home-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .home-banner {
    height: 220px;
  }
  
  .home-skeleton-card {
    min-width: 160px;
  }
  
  .home-skeleton-poster {
    height: 230px;
  }
  
  .home-loading-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .home-page {
    padding: 1.5rem;
  }
  
  .home-header {
    padding: 1.25rem 1.5rem;
  }
  
  .home-logo {
    font-size: 1.75rem;
  }
  
  .home-search {
    height: 3.25rem;
    max-width: 500px;
  }
  
  .home-nav {
    gap: 0.75rem;
    padding: 0.75rem 1.5rem;
  }
  
  .home-nav-item {
    padding: 0.625rem 1.25rem;
    font-size: 1rem;
  }
  
  .home-section {
    margin-bottom: 2rem;
  }
  
  .home-section-title {
    font-size: 1.5rem;
  }
  
  .home-carousel-item {
    min-width: 170px;
  }
  
  .home-poster {
    height: 245px;
  }
  
  .home-poster-title {
    font-size: 1rem;
  }
  
  .home-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
  }
  
  .home-banner {
    height: 240px;
  }
  
  .home-banner-title {
    font-size: 1.75rem;
  }
  
  .home-skeleton-card {
    min-width: 170px;
  }
  
  .home-skeleton-poster {
    height: 245px;
  }
  
  .home-loading-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* desktop: 1536px+ */
@media (min-width: 1536px) {
  .home-page {
    padding: 2rem;
  }
  
  .home-carousel-item {
    min-width: 180px;
  }
  
  .home-poster {
    height: 260px;
  }
  
  .home-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 1.5rem;
  }
  
  .home-banner {
    height: 260px;
  }
  
  .home-skeleton-card {
    min-width: 180px;
  }
  
  .home-skeleton-poster {
    height: 260px;
  }
  
  .home-loading-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>
