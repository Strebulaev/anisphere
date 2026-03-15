<template>
  <div class="franchise-page">

    <!-- Скелетон загрузки -->
    <template v-if="loading">
      <div class="franchise-hero skeleton-hero">
        <div class="sk sk-poster"></div>
        <div class="sk-info">
          <div class="sk sk-title"></div>
          <div class="sk sk-meta"></div>
          <div class="sk sk-desc"></div>
          <div class="sk sk-desc w60"></div>
        </div>
      </div>
      <div class="entries-grid">
        <div v-for="n in 4" :key="n" class="entry-card sk-card">
          <div class="sk sk-card-poster"></div>
          <div class="sk-card-info">
            <div class="sk sk-line w80"></div>
            <div class="sk sk-line w50"></div>
          </div>
        </div>
      </div>
    </template>

    <!-- Ошибка -->
    <div v-else-if="error" class="state-error">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <p class="state-title">Не удалось загрузить франшизу</p>
      <button class="btn-accent" @click="load">Повторить</button>
    </div>

    <!-- Контент -->
    <template v-else-if="franchise">

      <!-- Hero-блок -->
      <div class="franchise-hero" :style="heroBg">
        <div class="hero-backdrop"></div>
        <div class="hero-content">
          <!-- Постер -->
          <div class="hero-poster">
            <img
              v-if="franchise.poster_image_url"
              :src="getMediaUrl(franchise.poster_image_url)"
              :alt="franchise.name"
              class="poster-img"
            />
            <div v-else class="poster-placeholder">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="2" width="20" height="20" rx="2"/>
                <path d="M12 2v20M2 12h20"/>
              </svg>
            </div>
          </div>

          <!-- Мета -->
          <div class="hero-info">
            <div class="hero-badge">Франшиза</div>
            <h1 class="hero-title">{{ franchise.name }}</h1>

            <div class="hero-meta">
              <span v-if="franchise.year_range && franchise.year_range !== '—'">
                {{ franchise.year_range }}
              </span>
              <span v-else-if="franchise.year_start">
                {{ franchise.year_start }}{{ franchise.year_end && franchise.year_end !== franchise.year_start ? ' — ' + franchise.year_end : '' }}
              </span>
              <span class="dot">·</span>
              <span>{{ franchise.parts_count || franchise.entries?.length || 0 }} частей</span>
              <template v-if="franchise.avg_score || franchise.score">
                <span class="dot">·</span>
                <span class="score-badge">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                  {{ Number(franchise.avg_score || franchise.score).toFixed(1) }}
                </span>
              </template>
            </div>

            <!-- Жанры -->
            <div v-if="franchise.all_genres && franchise.all_genres.length > 0" class="hero-genres">
              <span 
                v-for="(genre, index) in franchise.all_genres.slice(0, 6)" 
                :key="index" 
                class="genre-tag"
              >
                {{ genre }}
              </span>
              <span v-if="franchise.all_genres.length > 6" class="genre-more">
                +{{ franchise.all_genres.length - 6 }}
              </span>
            </div>

            <p v-if="franchise.description" class="hero-desc">{{ franchise.description }}</p>
          </div>
        </div>
      </div>

      <!-- Список частей -->
      <div class="entries-section">
        <h2 class="entries-title">Все части</h2>

        <div class="entries-grid">
          <div
            v-for="entry in sortedEntries"
            :key="entry.id"
            class="entry-card"
            @click="goToAnime(entry.id)"
          >
            <!-- Постер -->
            <div class="entry-poster">
              <img
                v-if="entry.poster_image_url || entry.poster_url"
                :src="getMediaUrl(entry.poster_image_url || entry.poster_url)"
                :alt="entry.title_ru || entry.title_en"
                class="entry-poster-img"
                @error="onImgError"
              />
              <div v-else class="entry-poster-placeholder">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                </svg>
              </div>

              <!-- Оверлей -->
              <div class="entry-overlay">
                <div class="play-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                </div>
              </div>

              <!-- Бейдж типа -->
              <span class="kind-badge" :class="`kind-${entry.kind}`">{{ kindLabel(entry.kind) }}</span>

              <!-- Рейтинг -->
              <span v-if="entry.score" class="score-pill">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                {{ Number(entry.score).toFixed(1) }}
              </span>
            </div>

            <!-- Инфо -->
            <div class="entry-info">
              <h3 class="entry-title">{{ entry.title_ru || entry.title_en || '—' }}</h3>
              <div class="entry-meta">
                <span v-if="entry.year">{{ entry.year }}</span>
                <span v-if="entry.year && entry.episodes" class="dot">·</span>
                <span v-if="entry.episodes">{{ entry.episodes }} эп.</span>
                <span v-if="entry.status" class="dot">·</span>
                <span v-if="entry.status" :class="`status-${entry.status}`">{{ statusLabel(entry.status) }}</span>
              </div>
              <button class="entry-watch-btn" @click.stop="goToWatch(entry)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Смотреть
              </button>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient, { getMediaUrl } from '@/api/client'

interface FranchiseEntry {
  id: number
  title_ru: string
  title_en: string
  title_jp: string
  kind: string
  episodes: number | null
  year: number | null
  score: number | null
  status: string
  poster_url: string
  poster_image_url: string
  franchise_order: number
  kodik_link: string
}

interface FranchiseDetail {
  id: number
  name: string
  slug: string
  description: string
  poster_url: string
  poster_image_url: string
  score: number | null
  year_start: number | null
  year_end: number | null
  year_range?: string
  parts_count?: number
  avg_score?: number | null
  all_genres?: string[]
  all_posters?: string[]
  entries: FranchiseEntry[]
}

const route  = useRoute()
const router = useRouter()

const franchise = ref<FranchiseDetail | null>(null)
const loading   = ref(true)
const error     = ref(false)

const sortedEntries = computed(() =>
  [...(franchise.value?.entries || [])].sort(
    (a, b) => a.franchise_order - b.franchise_order || (a.year || 0) - (b.year || 0)
  )
)

const heroBg = computed(() => {
  const url = franchise.value?.poster_image_url || franchise.value?.poster_url
  if (!url) return {}
  return {
    '--hero-bg': `url(${getMediaUrl(url)})`
  }
})

const kindLabel = (kind: string) => {
  const map: Record<string, string> = {
    tv: 'TV', movie: 'Фильм', ova: 'OVA', ona: 'ONA',
    special: 'Спешл', music: 'Клип', franchise: 'Франшиза',
  }
  return map[kind] || kind.toUpperCase()
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = {
    ongoing: 'Онгоинг', finished: 'Завершено', announced: 'Анонс',
  }
  return map[status] || status
}

const load = async () => {
  loading.value = true
  error.value   = false
  try {
    const id  = route.params.id
    console.log('Loading franchise:', id)
    const res = await apiClient.get(`/anime/franchises/${id}/`)
    console.log('Franchise data:', res.data)
    franchise.value = res.data
  } catch (e) {
    console.error('Error loading franchise:', e)
    error.value = true
  } finally {
    loading.value = false
  }
}

const goToAnime = (id: number) => router.push(`/anime/${id}`)

const goToWatch = (entry: FranchiseEntry) => {
  if (entry.kodik_link) {
    router.push(`/anime/${entry.id}/watch`)
  } else {
    router.push(`/anime/${entry.id}`)
  }
}

const onImgError = (e: Event) => {
  (e.target as HTMLImageElement).style.display = 'none'
}

onMounted(load)
</script>

<style scoped>
/* ── Страница ────────────────────────────────────────────── */
.franchise-page {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) var(--space-10);
}

/* ── Hero ────────────────────────────────────────────────── */
.franchise-hero {
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: var(--space-10);
  background: var(--surface-2);
  min-height: 300px;
}

.franchise-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: var(--hero-bg);
  background-size: cover;
  background-position: center;
  filter: blur(24px) brightness(0.3);
  transform: scale(1.1);
}

.hero-content {
  position: relative;
  display: flex;
  gap: var(--space-8);
  padding: var(--space-8);
  align-items: flex-start;
}

.hero-poster {
  flex-shrink: 0;
  width: 180px;
  height: 252px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  box-shadow: var(--shadow-xl);
}

.poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.hero-info { flex: 1; min-width: 0; }

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  background: var(--accent-subtle);
  color: var(--accent);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: var(--space-3);
}

.hero-title {
  font-size: var(--text-4xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-3);
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.dot { color: var(--text-tertiary); }

.score-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--warning);
  font-weight: 700;
}

.hero-genres {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.genre-tag {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  backdrop-filter: blur(4px);
}

.genre-more {
  padding: 4px 10px;
  background: rgba(124, 92, 252, 0.2);
  border: 1px solid rgba(124, 92, 252, 0.3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--accent);
}

.hero-desc {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.6;
  margin: 0;
  max-width: 600px;
  display: -webkit-box;
  line-clamp: 4;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Секция частей ───────────────────────────────────────── */
/* .entries-section { } */

.entries-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-6);
  letter-spacing: -0.01em;
}

.entries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-5);
}

/* ── Карточка части ─────────────────────────────────────── */
.entry-card {
  cursor: pointer;
  transition: transform var(--duration-slow) var(--ease-out);
}
.entry-card:hover { transform: translateY(-4px); }

.entry-poster {
  position: relative;
  width: 100%;
  padding-bottom: 140%;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  margin-bottom: var(--space-2);
}

.entry-poster-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}
.entry-card:hover .entry-poster-img { transform: scale(1.05); }

.entry-poster-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Оверлей */
.entry-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out);
  z-index: 2;
}
.entry-card:hover .entry-overlay { opacity: 1; }

.play-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  padding-left: 3px;
  transform: scale(0.6);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.4s;
}
.entry-card:hover .play-icon {
  transform: scale(1);
  box-shadow: 0 0 28px 4px rgba(124,92,252,.5);
}

/* Бейджи */
.kind-badge {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  backdrop-filter: blur(6px);
  z-index: 3;
  background: rgba(0,0,0,0.75);
  color: var(--text-secondary);
}
.kind-badge.kind-tv     { background: var(--accent); color: white; }
.kind-badge.kind-movie  { background: #f59e0b; color: #000; }
.kind-badge.kind-ova    { background: #22c55e; color: white; }
.kind-badge.kind-special { background: #a855f7; color: white; }

.score-pill {
  position: absolute;
  bottom: var(--space-2);
  left: var(--space-2);
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  background: rgba(0,0,0,0.85);
  color: var(--warning);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(6px);
  z-index: 3;
}

/* Инфо под карточкой */
.entry-info { display: flex; flex-direction: column; gap: var(--space-1); }

.entry-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.entry-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-wrap: wrap;
}

.status-ongoing  { color: #22c55e; }
.status-finished { color: var(--text-tertiary); }
.status-announced { color: #a855f7; }

.entry-watch-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  margin-top: var(--space-1);
  padding: 6px var(--space-2);
  background: transparent;
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
}
.entry-watch-btn:hover {
  background: var(--accent);
  color: white;
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

/* ── Кнопки ─────────────────────────────────────────────── */
.btn-accent {
  padding: 10px var(--space-6);
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background-color var(--duration-base);
}
.btn-accent:hover { background: var(--accent-hover); }

/* ── Ошибка ─────────────────────────────────────────────── */
.state-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: 80px 0;
  color: var(--text-secondary);
  text-align: center;
}
.state-title { font-size: var(--text-lg); font-weight: 600; color: var(--text-primary); margin: 0; }

/* ── Скелетоны ───────────────────────────────────────────── */
.sk {
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-sm);
}
@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.skeleton-hero {
  display: flex;
  gap: var(--space-8);
  padding: var(--space-8);
  min-height: 300px;
}
.sk-poster { flex-shrink: 0; width: 180px; height: 252px; border-radius: var(--radius-lg); }
.sk-info   { flex: 1; display: flex; flex-direction: column; gap: var(--space-3); padding-top: var(--space-2); }
.sk-title  { height: 40px; width: 50%; }
.sk-meta   { height: 16px; width: 35%; }
.sk-desc   { height: 14px; }
.w60       { width: 60%; }
.sk-card   { cursor: default; }
.sk-card:hover { transform: none; }
.sk-card-poster { width: 100%; padding-bottom: 140%; border-radius: var(--radius-lg); }
.sk-card-info   { padding-top: var(--space-2); display: flex; flex-direction: column; gap: var(--space-1); }
.sk-line   { height: 12px; }
.w80       { width: 80%; }
.w50       { width: 50%; }

/* ── Адаптив ─────────────────────────────────────────────── */
@media (max-width: 767px) {
  .franchise-page { padding: var(--space-4) var(--space-3) var(--space-8); }
  .hero-content   { flex-direction: column; padding: var(--space-5); gap: var(--space-4); }
  .hero-poster    { width: 120px; height: 168px; }
  .hero-title     { font-size: var(--text-2xl); }
  .entries-grid   { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
  .skeleton-hero  { flex-direction: column; padding: var(--space-5); }
  .sk-poster      { width: 120px; height: 168px; }
}
</style>
