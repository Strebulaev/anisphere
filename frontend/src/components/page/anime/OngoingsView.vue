<template>
  <div class="ong">

    <AnimeFilterBar
      :show-status="false"
      :show-advanced="true"
      :show-shuffle="false"
      :results-count="sortedAnime.length"
      search-placeholder="Поиск онгоинга..."
      :sort-options="[
        { value: '-score',   label: 'Рейтинг ↓'  },
        { value: 'score',    label: 'Рейтинг ↑'  },
        { value: '-year',    label: 'Год: новее'  },
        { value: 'year',     label: 'Год: старее' },
        { value: 'title_ru', label: 'А → Я'       },
      ]"
      @change="onFilterChange"
      @refresh="$emit('refresh')"
    />

    <!-- Скелетон -->
    <div v-if="loading" class="ong-grid">
      <div v-for="i in 24" :key="i" class="ong-skel">
        <div class="ong-skel-poster"></div>
        <div class="ong-skel-line"></div>
        <div class="ong-skel-line short"></div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="ong-message ong-error">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="ong-msg-title">Не удалось загрузить онгоинги</p>
        <button @click="$emit('refresh')" class="ong-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="sortedAnime.length === 0" class="ong-message">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <div>
        <p class="ong-msg-title">Онгоинги не найдены</p>
      </div>
    </div>

    <!-- Сетка -->
    <div v-else>
      <p class="ong-count">{{ sortedAnime.length }} аниме</p>
      <div class="ong-grid">
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

interface Props { anime: any[]; loading: boolean; error: string | null; viewersMap?: Record<number, number> }
const props = defineProps<Props>()
const emits = defineEmits<{ refresh: [] }>()

const router  = useRouter()
const goToAnime = (anime: any) => router.push(`/anime/${anime?.id ?? anime}`)

// Текущие фильтры
const filters = ref<FilterState>({})

const onFilterChange = (f: FilterState) => {
  filters.value = f
}

// Хелперы
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
  status: a.status || '',
  episodes: a.episodes || a.episodes_count || null,
  score: a.score ? parseFloat(a.score) : null,
  poster_url: a.poster_url || null,
  poster_image_url: a.poster_image_url || null,
  poster: a.poster || null,
  type: a.type || a.kind || '',
  genres: genreList(a),
})

// Клиентская фильтрация
const sortedAnime = computed(() => {
  let list = [...props.anime]

  const { search, genres, type, year_from, year_to, score_from, score_to, episodes_from, episodes_to, ordering } = filters.value

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
  if (episodes_from) list = list.filter(a => (a.episodes || 0) >= episodes_from)
  if (episodes_to)   list = list.filter(a => (a.episodes || 0) <= episodes_to)

  // Сортировка
  switch (ordering || '-score') {
    case '-score':   return list.sort((a, b) => parseFloat(b.score||0) - parseFloat(a.score||0))
    case 'score':    return list.sort((a, b) => parseFloat(a.score||0) - parseFloat(b.score||0))
    case '-year':    return list.sort((a, b) => (b.year||0) - (a.year||0))
    case 'year':     return list.sort((a, b) => (a.year||0) - (b.year||0))
    case 'title_ru': return list.sort((a, b) => title(a).localeCompare(title(b)))
    default: return list
  }
})

watch(() => props.anime, v => { if (!v.length && !props.loading) emits('refresh') }, { immediate: true })
</script>

<style scoped>
.ong {}

.ong-count { font-size: var(--text-sm); color: var(--text-secondary); margin-bottom: var(--space-4); }

.ong-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.ong-skel { display: flex; flex-direction: column; gap: 8px; }
.ong-skel-poster {
  aspect-ratio: 2/3; border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ong-skel-line {
  height: 12px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.ong-skel-line.short { width: 55%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.ong-message {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 60px var(--space-6); color: var(--text-tertiary);
}
.ong-message svg { opacity: .4; flex-shrink: 0; }
.ong-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-2); }
.ong-error svg { color: var(--danger); opacity: 1; }
.ong-retry {
  background: none; border: none; color: var(--accent);
  font-size: var(--text-sm); cursor: pointer; padding: 0; text-decoration: underline;
}

@media (max-width: 767px) {
  .ong-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
}
</style>
