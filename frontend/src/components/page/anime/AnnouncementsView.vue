<template>
  <div class="ann">

    <AnimeFilterBar
      :show-status="false"
      :show-advanced="true"
      :show-shuffle="false"
      :results-count="sortedAnime.length"
      search-placeholder="Поиск анонса..."
      :sort-options="[
        { value: '-year',    label: 'Год выхода ↓'  },
        { value: 'year',     label: 'Год выхода ↑'  },
        { value: '-score',   label: 'По ожидаемости' },
        { value: 'title_ru', label: 'По названию'    },
      ]"
      @change="onFilterChange"
      @refresh="$emit('refresh')"
    />

    <!-- Скелетон -->
    <div v-if="loading" class="ann-grid">
      <div v-for="i in 24" :key="i" class="ann-skel">
        <div class="ann-skel-poster"></div>
        <div class="ann-skel-line"></div>
        <div class="ann-skel-line short"></div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="ann-message ann-err">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="ann-msg-title">Не удалось загрузить анонсы</p>
        <button @click="$emit('refresh')" class="ann-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="sortedAnime.length === 0" class="ann-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M18 8h1a4 4 0 0 1 0 8h-1"/>
        <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
        <line x1="6" y1="1" x2="6" y2="4"/>
        <line x1="10" y1="1" x2="10" y2="4"/>
        <line x1="14" y1="1" x2="14" y2="4"/>
      </svg>
      <div>
        <p class="ann-msg-title">Анонсов пока нет</p>
        <p class="ann-msg-sub">Здесь появятся анонсы предстоящих аниме</p>
      </div>
    </div>

    <!-- Сетка -->
    <div v-else>
      <p class="ann-count">{{ sortedAnime.length }} аниме</p>
      <div class="ann-grid">
        <AnimeCard
          v-for="a in sortedAnime"
          :key="a.id"
          :anime="toCardAnime(a)"
          :show-actions="true"
          :show-genres="true"
          :show-progress="false"
          @click="goToAnime(a.id)"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AnimeFilterBar from '@/components/Filters/AnimeFilterBar.vue'
import type { FilterState } from '@/components/Filters/AnimeFilterBar.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'

interface Props { anime: any[]; loading: boolean; error: string | null }
const props = defineProps<Props>()
const emits = defineEmits<{ refresh: [] }>()

const router    = useRouter()
const goToAnime = (anime: any) => router.push(`/anime/${anime?.id ?? anime}`)

const filters = ref<FilterState>({})
const onFilterChange = (f: FilterState) => { filters.value = f }

const title     = (a: any): string => a.title_ru || a.title_en || a.title || 'Без названия'
const genreList = (a: any): any[] => {
  const raw = a.genres
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map((g: any) => typeof g === 'object' && g !== null ? g : { id: g, name: String(g), slug: String(g) })
  if (typeof raw === 'string') {
    try { const p = JSON.parse(raw); return Array.isArray(p) ? p : [] }
    catch { return raw.split(',').map((g: string, i: number) => ({ id: i, name: g.trim(), slug: g.trim() })) }
  }
  return []
}

const toCardAnime = (a: any) => ({
  id: a.id,
  title_ru: a.title_ru || a.title || '',
  title_en: a.title_en || '',
  year: a.year ?? null,
  status: a.status || 'announced',
  episodes: a.episodes || a.episodes_count || null,
  score: a.score ? parseFloat(a.score) : null,
  poster_url: a.poster_url || null,
  poster_image_url: a.poster_image_url || null,
  poster: a.poster || null,
  type: a.type || a.kind || '',
  genres: genreList(a),
})

const sortedAnime = computed(() => {
  let list = [...props.anime]
  const { search, genres, type, year_from, year_to, score_from, score_to, ordering } = filters.value

  if (search?.trim()) {
    const q = search.toLowerCase()
    list = list.filter(a => title(a).toLowerCase().includes(q) || (a.title_en || '').toLowerCase().includes(q))
  }
  if (genres?.length) {
    list = list.filter(a => genres.every(sg => genreList(a).some((g: any) => (typeof g === 'object' ? g.name : g).toLowerCase() === sg.toLowerCase())))
  }
  if (type?.length) {
    list = list.filter(a => type.includes((a.type || a.kind || '').toLowerCase()))
  }
  if (year_from) list = list.filter(a => (a.year || 0) >= year_from)
  if (year_to)   list = list.filter(a => (a.year || 0) <= year_to)
  if (score_from) list = list.filter(a => parseFloat(a.score || 0) >= score_from)
  if (score_to)   list = list.filter(a => parseFloat(a.score || 0) <= score_to)

  switch (ordering || '-year') {
    case '-year':    return list.sort((a, b) => (b.year || 0) - (a.year || 0))
    case 'year':     return list.sort((a, b) => (a.year || 0) - (b.year || 0))
    case '-score':   return list.sort((a, b) => parseFloat(b.score || 0) - parseFloat(a.score || 0))
    case 'title_ru': return list.sort((a, b) => title(a).localeCompare(title(b)))
    default: return list
  }
})

// Запрашиваем данные только один раз при маунте, если список пуст
import { onMounted } from 'vue'
onMounted(() => { if (!props.anime.length && !props.loading) emits('refresh') })
</script>

<style scoped>
.ann {}
.ann-count { font-size: var(--text-sm); color: var(--text-secondary); margin-bottom: var(--space-4); }

.ann-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}
.ann-skel { display: flex; flex-direction: column; gap: 8px; }
.ann-skel-poster {
  aspect-ratio: 2/3; border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line {
  height: 12px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.ann-skel-line.short { width: 55%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.ann-message {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 60px var(--space-6); color: var(--text-tertiary);
}
.ann-message svg { opacity: .4; flex-shrink: 0; }
.ann-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-2); }
.ann-msg-sub   { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0; }
.ann-err svg   { color: var(--danger); opacity: 1; }
.ann-retry { background: none; border: none; color: var(--accent); font-size: var(--text-sm); cursor: pointer; padding: 0; text-decoration: underline; }

@media (max-width: 767px) {
  .ann-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
}
</style>
