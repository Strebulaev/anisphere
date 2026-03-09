<template>
  <div class="catalog">

    <AnimeFilterBar
      :show-status="true"
      :show-advanced="true"
      :show-shuffle="showShuffle"
      :is-shuffled="isShuffled"
      :results-count="totalCount"
      :show-page-size="true"
      search-placeholder="Поиск аниме по названию..."
      @change="onFilterChange"
      @shuffle="$emit('shuffle')"
      @unshuffle="$emit('unshuffle')"
      @refresh="$emit('refresh')"
    />

    <!-- Загрузка -->
    <div v-if="loading" class="catalog-grid">
      <div v-for="n in 24" :key="n" class="catalog-skel">
        <div class="skel-poster"></div>
        <div class="skel-line"></div>
        <div class="skel-line short"></div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="catalog-msg catalog-err">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="catalog-msg-title">Не удалось загрузить каталог</p>
        <p class="catalog-msg-sub">{{ error }}</p>
        <button @click="$emit('refresh')" class="catalog-retry" type="button">Повторить</button>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="deduplicatedList.length === 0" class="catalog-msg">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <div>
        <p class="catalog-msg-title">Ничего не найдено</p>
        <p class="catalog-msg-sub">Попробуйте изменить параметры поиска или сбросить фильтры</p>
      </div>
    </div>

    <!-- Результат -->
    <div v-else>
      <p class="catalog-info">Показано {{ deduplicatedList.length }} из {{ totalCount }} аниме</p>
      <div class="catalog-grid">
        <AnimeCard
          v-for="anime in deduplicatedList"
          :key="(anime as any).franchise_id ? 'f' + (anime as any).franchise_id : anime.id"
          :anime="anime as any"
          @click="handleClick(anime)"
        />
      </div>
      <div v-if="totalPages > 1" class="catalog-pagination">
        <Pagination
          :current-page="page"
          :total-pages="totalPages"
          :total-items="totalCount"
          :items-per-page="50"
          @update:current-page="handlePageChange"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AnimeFilterBar from '@/components/Filters/AnimeFilterBar.vue'
import type { FilterState } from '@/components/Filters/AnimeFilterBar.vue'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import { Pagination } from '@/components/Navigation'
import type { Anime } from '@/types'

interface Props {
  animeList: Anime[]
  loading: boolean
  error: string | null
  page: number
  totalPages: number
  totalCount: number
  showShuffle?: boolean
  isShuffled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showShuffle: false,
  isShuffled: false,
})

const emit = defineEmits<{
  pageChange: [page: number]
  refresh: []
  shuffle: []
  unshuffle: []
  animeClick: [anime: Anime]
  watchAnime: [anime: Anime]
  filterChange: [filters: FilterState]
}>()

const deduplicatedList = computed(() => {
  const seen = new Map<string, any>()
  for (const a of props.animeList) {
    const fid = (a as any).franchise_id
    if (fid) {
      const key = `franchise_${fid}`
      const existing = seen.get(key)
      if (!existing || ((a as any).score || 0) > ((existing as any).score || 0)) {
        seen.set(key, {
          ...a,
          title_ru:         (a as any).franchise_name                  || (a as any).title_ru,
          poster_image_url: (a as any).franchise_poster_image_url       || (a as any).poster_image_url,
          poster_url:       (a as any).franchise_poster_image_url       || (a as any).poster_url,
        })
      }
    } else {
      seen.set(`anime_${a.id}`, a)
    }
  }
  return Array.from(seen.values())
})

const onFilterChange = (filters: FilterState) => {
  emit('filterChange', filters)
}

const handleClick = (anime: Anime) => emit('animeClick', anime)

const handlePageChange = (newPage: number) => {
  emit('pageChange', newPage)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.catalog {}

.catalog-info {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

/* Скелетоны */
.catalog-skel { display: flex; flex-direction: column; gap: 8px; }
.skel-poster {
  aspect-ratio: 2/3; border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.skel-line {
  height: 12px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.skel-line.short { width: 55%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* Сообщения */
.catalog-msg {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 80px var(--space-6);
  color: var(--text-tertiary);
}
.catalog-msg svg { opacity: .4; flex-shrink: 0; }
.catalog-err svg { color: var(--danger); opacity: 1; }
.catalog-msg-title { font-size: var(--text-lg); font-weight: 600; color: var(--text-secondary); margin: 0 0 var(--space-1); }
.catalog-msg-sub   { font-size: var(--text-sm); color: var(--text-tertiary); margin: 0 0 var(--space-3); }
.catalog-retry {
  background: none; border: 1px solid var(--accent);
  border-radius: var(--radius-md); padding: var(--space-2) var(--space-4);
  color: var(--accent); font-size: var(--text-sm); cursor: pointer;
  transition: all .15s;
}
.catalog-retry:hover { background: var(--accent); color: white; }

.catalog-pagination { margin-top: var(--space-6); padding-top: var(--space-4); border-top: 1px solid var(--border-subtle); }

@media (max-width: 767px) {
  .catalog-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
}
</style>
