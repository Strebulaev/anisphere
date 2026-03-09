<template>
  <div class="rb">
    <!-- Заголовок блока -->
    <div class="rb-header">
      <div class="rb-meta">
        <span class="rb-icon">{{ icon }}</span>
        <div class="rb-texts">
          <h3 class="rb-title">{{ title }}</h3>
          <p v-if="description" class="rb-desc">{{ description }}</p>
        </div>
      </div>
      <button v-if="hasViewAll" class="rb-view-all" @click="$emit('view-all')" type="button">
        Смотреть все
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </button>
    </div>

    <!-- Скелетон -->
    <div v-if="loading" class="rb-grid">
      <div v-for="i in 8" :key="i" class="rb-skeleton">
        <div class="rb-sk-poster"></div>
        <div class="rb-sk-line"></div>
        <div class="rb-sk-line short"></div>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="!anime.length" class="rb-empty">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M8 15s1.5 2 4 2 4-2 4-2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/>
        <line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
      Нет аниме для этого блока
    </div>

    <!-- Сетка карточек -->
    <div v-else class="rb-grid">
      <AnimeCard
        v-for="a in anime"
        :key="a.id"
        :anime="toCardAnime(a)"
        :show-actions="true"
        :show-genres="false"
        :show-progress="false"
        @click="(ev: any) => router.push(`/anime/${a.id}`)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AnimeCard from './AnimeCard.vue'

interface AnimeItem {
  id: number
  title: string
  poster: string | null
  year?: number | null
  score?: string | null
  genres?: string[]
  status?: string
  type?: string
}

defineProps<{
  title: string
  description?: string
  icon?: string
  anime: AnimeItem[]
  loading?: boolean
  hasViewAll?: boolean
}>()

defineEmits<{ 'view-all': [] }>()

const router = useRouter()

const toCardAnime = (a: AnimeItem) => ({
  id: a.id,
  title_ru: a.title || '',
  title_en: '',
  year: a.year ?? null,
  status: a.status || '',
  episodes: null,
  score: a.score ? parseFloat(a.score) : null,
  poster_url: a.poster || null,
  poster_image_url: a.poster || null,
  poster: null,
  type: a.type || '',
  genres: [],
})
</script>

<style scoped>
.rb {
  margin-bottom: var(--space-8);
}

/* ── Заголовок ────────────────────────────────────────────── */
.rb-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  gap: var(--space-4);
}

.rb-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.rb-icon {
  font-size: 22px;
  line-height: 1;
  flex-shrink: 0;
}

.rb-texts { min-width: 0; }

.rb-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.015em;
}

.rb-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 3px 0 0;
}

.rb-view-all {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--accent);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  transition: background-color var(--duration-base) var(--ease-out);
  white-space: nowrap;
  flex-shrink: 0;
}
.rb-view-all:hover { background: var(--accent-subtle); }

/* ── Пусто ────────────────────────────────────────────────── */
.rb-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-5);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  background: var(--surface-2);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
}

/* ── Сетка ───────────────────────────────────────────────── */
.rb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

/* ── Скелетон ─────────────────────────────────────────────── */
.rb-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rb-sk-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-card);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.rb-sk-line {
  height: 13px;
  width: 85%;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.rb-sk-line.short { width: 55%; }

@keyframes sk {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

/* ── Адаптив ──────────────────────────────────────────────── */
@media (max-width: 767px) {
  .rb-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
  }
}
</style>
