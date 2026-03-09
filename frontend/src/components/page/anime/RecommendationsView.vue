<template>
  <div class="rec-view">

    <!-- ══ Шапка ════════════════════════════════════════════ -->
    <div class="rec-header">
      <div class="rec-header-row">
        <div>
          <h2 class="rec-title">⭐ Для вас</h2>
          <p class="rec-subtitle">Подборки на основе вашего вкуса — персональные советы и лучшее аниме</p>
        </div>
        <button class="rec-refresh-btn" @click="loadAll" :disabled="globalLoading" type="button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            :class="{ spin: globalLoading }">
            <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Обновить всё
        </button>
      </div>
    </div>

    <!-- ══ Блоки-карусели ════════════════════════════════════ -->
    <div class="rec-blocks">
      <RecCarousel
        v-for="block in blocks"
        :key="block.key"
        :title="block.title"
        :description="block.desc"
        :icon="block.icon"
        :anime="blockData[block.key]"
        :loading="blockLoading[block.key]"
        :has-view-all="!!block.route"
        @view-all="goToViewAll(block)"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import RecCarousel from '@/components/Cards/RecCarousel.vue'

type BlockKey = 'top_rated' | 'new_season' | 'classics' | 'based_on_watched'
  | 'explore_new' | 'short' | 'movies' | 'seasonal'

interface Block { key: BlockKey; title: string; desc: string; icon: string; route?: string }

const router    = useRouter()
const authStore = useAuthStore()

const blocks: Block[] = [
  { key: 'top_rated',        title: 'Топ аниме',               desc: 'Лучшее по рейтингу сообщества',                icon: '🏆', route: '/anime?ordering=-score'              },
  { key: 'new_season',       title: 'Новинки',                  desc: 'Аниме за последние 2 года',                   icon: '🆕', route: '/anime?ordering=-year'               },
  { key: 'based_on_watched', title: 'На основе просмотренного', desc: 'Похожее на то, что вы уже смотрели',          icon: '🎯'                                            },
  { key: 'seasonal',         title: 'Сезонное',                 desc: 'Онгоинги текущего сезона',                    icon: '🌸', route: '/anime?status=ongoing'               },
  { key: 'classics',         title: 'Классика',                 desc: 'Легендарные тайтлы до 2010 года',             icon: '📜', route: '/anime?ordering=-score&year_to=2010' },
  { key: 'explore_new',      title: 'Откройте новое',           desc: 'Неожиданные находки с рейтингом выше 7',      icon: '🔭'                                            },
  { key: 'short',            title: 'Короткие аниме',           desc: 'До 13 серий — идеально для старта',           icon: '⚡'                                            },
  { key: 'movies',           title: 'Полнометражные',           desc: 'Фильмы и OVA с высоким рейтингом',            icon: '🎬'                                            },
]

const blockData:    Record<BlockKey, any[]>   = reactive({} as any)
const blockLoading: Record<BlockKey, boolean> = reactive({} as any)
blocks.forEach(b => { blockData[b.key] = []; blockLoading[b.key] = false })

const globalLoading = computed(() => Object.values(blockLoading).some(Boolean))

// ── Нормализация жанров ───────────────────────────────────
const toNames = (raw: any): string[] => {
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map((g: any) => typeof g === 'object' && g ? g.name : String(g)).filter(Boolean)
  if (typeof raw === 'string') {
    try {
      const p = JSON.parse(raw)
      return Array.isArray(p) ? p.map((g: any) => typeof g === 'object' && g ? g.name : String(g)).filter(Boolean) : [raw]
    } catch { return raw.split(',').map((s: string) => s.trim()).filter(Boolean) }
  }
  return []
}

const norm = (a: any) => ({
  id:     a.id,
  title:  a.title_ru || a.title_en || 'Без названия',
  poster: a.poster_image_url || a.poster_url || a.poster || null,
  year:   a.year,
  score:  a.score ? parseFloat(a.score).toFixed(1) : null,
  genres: toNames(a.genres),
  status: a.status,
  type:   a.kind || a.type,
})

// ── Загрузка блока ────────────────────────────────────────
const loadBlock = async (key: BlockKey, params: Record<string, any>) => {
  blockLoading[key] = true
  try {
    const res = await apiClient.get('/anime/', { params: { page_size: 24, ordering: '-score', ...params } })
    blockData[key] = (res.data.results || []).map(norm)
  } catch (e) {
    console.error(`[Recs] loadBlock ${key}:`, e)
    blockData[key] = []
  } finally {
    blockLoading[key] = false
  }
}

// ── Персональные рекомендации (на основе истории) ─────────
const loadBasedOnWatched = async () => {
  blockLoading['based_on_watched'] = true
  try {
    if (!authStore.isAuthenticated) {
      // Не авторизован — показываем топ
      await loadBlock('based_on_watched', { ordering: '-score', score_from: 7 })
      return
    }

    // Берём библиотеку пользователя
    let topGenres: string[] = []
    let watchedIds: number[] = []
    try {
      const libRes = await apiClient.get('/users/library/', { params: { page_size: 200 } })
      const items: any[] = libRes.data?.results || libRes.data?.library || []
      watchedIds = items.map((it: any) => it.anime?.id || it.anime).filter(Boolean)

      // Считаем самые частые жанры
      const genreMap: Record<string, number> = {}
      items.forEach((it: any) => {
        const genres = it.anime?.genres || it.genres || []
        toNames(genres).forEach((g: string) => { genreMap[g] = (genreMap[g] || 0) + 1 })
      })
      topGenres = Object.entries(genreMap)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(e => e[0])
    } catch { /* не авторизован */ }

    if (topGenres.length) {
      // Загружаем по топ жанрам, исключаем уже просмотренные клиентски
      const res = await apiClient.get('/anime/', {
        params: { page_size: 48, ordering: '-score', genres: topGenres.join(','), genre_logic: 'OR', score_from: 6 }
      })
      const results = (res.data.results || [])
        .filter((a: any) => !watchedIds.includes(a.id))
        .slice(0, 24)
        .map(norm)
      blockData['based_on_watched'] = results
    } else {
      await loadBlock('based_on_watched', { ordering: '-score', score_from: 7 })
    }
  } catch {
    await loadBlock('based_on_watched', { ordering: '-score' })
  } finally {
    blockLoading['based_on_watched'] = false
  }
}

// ── Топ на основе истории: берём жанры и фильтруем ────────
// Сезонное — онгоинги, похожие на просмотренное
const loadSeasonal = async () => {
  blockLoading['seasonal'] = true
  try {
    let genreParam = ''
    if (authStore.isAuthenticated) {
      try {
        const libRes = await apiClient.get('/users/library/', { params: { page_size: 100 } })
        const items: any[] = libRes.data?.results || libRes.data?.library || []
        const genreMap: Record<string, number> = {}
        items.forEach((it: any) => {
          toNames(it.anime?.genres || it.genres || []).forEach((g: string) => { genreMap[g] = (genreMap[g] || 0) + 1 })
        })
        const top = Object.entries(genreMap).sort((a, b) => b[1] - a[1]).slice(0, 3).map(e => e[0])
        genreParam = top.join(',')
      } catch {}
    }
    await loadBlock('seasonal', genreParam
      ? { status: 'ongoing', ordering: '-score', genres: genreParam, genre_logic: 'OR' }
      : { status: 'ongoing', ordering: '-score' }
    )
  } finally { blockLoading['seasonal'] = false }
}

// Классика на основе любимых жанров
const loadClassics = async () => {
  blockLoading['classics'] = true
  try {
    let genreParam = ''
    if (authStore.isAuthenticated) {
      try {
        const libRes = await apiClient.get('/users/library/', { params: { page_size: 100 } })
        const items: any[] = libRes.data?.results || libRes.data?.library || []
        const genreMap: Record<string, number> = {}
        items.forEach((it: any) => {
          toNames(it.anime?.genres || it.genres || []).forEach((g: string) => { genreMap[g] = (genreMap[g] || 0) + 1 })
        })
        const top = Object.entries(genreMap).sort((a, b) => b[1] - a[1]).slice(0, 3).map(e => e[0])
        genreParam = top.join(',')
      } catch {}
    }
    await loadBlock('classics', genreParam
      ? { ordering: '-score', year_to: 2010, score_from: 7, genres: genreParam, genre_logic: 'OR' }
      : { ordering: '-score', year_to: 2010, score_from: 7 }
    )
  } finally { blockLoading['classics'] = false }
}

// Откройте новое — жанры которых ещё не смотрели
const loadExploreNew = async () => {
  blockLoading['explore_new'] = true
  try {
    if (authStore.isAuthenticated) {
      try {
        const libRes = await apiClient.get('/users/library/', { params: { page_size: 200 } })
        const items: any[] = libRes.data?.results || libRes.data?.library || []
        const seenGenres = new Set<string>()
        items.forEach((it: any) => {
          toNames(it.anime?.genres || it.genres || []).forEach((g: string) => seenGenres.add(g))
        })
        // Берём случайную страницу чтобы не повторяться
        const page = Math.floor(Math.random() * 5) + 1
        const res = await apiClient.get('/anime/', {
          params: { page_size: 48, ordering: '-score', score_from: 6.5, page }
        })
        const watched_ids = items.map((it: any) => it.anime?.id || it.anime).filter(Boolean)
        const newItems = (res.data.results || [])
          .filter((a: any) => !watched_ids.includes(a.id))
          .filter((a: any) => {
            // Отдаём предпочтение аниме с жанрами которых не смотрели
            const aGenres = toNames(a.genres)
            return aGenres.some(g => !seenGenres.has(g))
          })
          .slice(0, 24)
          .map(norm)
        blockData['explore_new'] = newItems.length ? newItems : (res.data.results || []).slice(0, 24).map(norm)
        return
      } catch {}
    }
    await loadBlock('explore_new', { ordering: '-score', score_from: 6, page: Math.floor(Math.random() * 5) + 1 })
  } finally { blockLoading['explore_new'] = false }
}

// ── Загрузка всех ─────────────────────────────────────────
const loadAll = async () => {
  const y = new Date().getFullYear()

  await Promise.all([
    loadBlock('top_rated',  { ordering: '-score' }),
    loadBlock('new_season', { ordering: '-year', year_from: y - 2 }),
    loadBlock('short',      { ordering: '-score', episodes_to: 13, score_from: 6 }),
    loadBlock('movies',     { ordering: '-score', type: 'movie' }),
    loadBasedOnWatched(),
    loadSeasonal(),
    loadClassics(),
    loadExploreNew(),
  ])
}

const goToViewAll = (block: Block) => { if (block.route) router.push(block.route) }

onMounted(() => loadAll())
</script>

<style scoped>
.rec-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
  padding: var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.rec-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.rec-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.02em;
}

.rec-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

.rec-refresh-btn {
  display: inline-flex; align-items: center; gap: var(--space-2);
  height: 36px; padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm); font-weight: 500;
  cursor: pointer; transition: all var(--duration-base);
  flex-shrink: 0;
}
.rec-refresh-btn:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.rec-refresh-btn:disabled { opacity: .5; cursor: not-allowed; }

.rec-blocks { display: flex; flex-direction: column; gap: var(--space-2); }

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
