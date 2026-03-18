<template>
  <div class="rc">
    <!-- Заголовок -->
    <div class="rc-header">
      <div class="rc-meta">
        <span class="rc-icon">{{ icon }}</span>
        <div class="rc-texts">
          <h3 class="rc-title">{{ title }}</h3>
          <p v-if="description" class="rc-desc">{{ description }}</p>
        </div>
      </div>
      <button v-if="hasViewAll" class="rc-view-all" @click="$emit('view-all')" type="button">
        Смотреть все
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </button>
    </div>

    <!-- Скелетон -->
    <div v-if="loading" class="rc-track">
      <div v-for="i in 8" :key="i" class="rc-skel">
        <div class="rc-skel-poster"></div>
        <div class="rc-skel-line"></div>
        <div class="rc-skel-line short"></div>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="!anime.length" class="rc-empty">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M8 15s1.5 2 4 2 4-2 4-2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/>
        <line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
      Нет аниме для этого блока
    </div>

    <!-- Карусель -->
    <div v-else class="rc-carousel-wrap">
      <!-- Стрелка влево -->
      <button
        v-if="!atStart"
        class="rc-arrow rc-arrow-left"
        @click="scroll(-1)"
        type="button"
        aria-label="Назад"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>

      <div class="rc-track" ref="trackRef" @scroll="updateArrows">
        <div class="rc-card-wrap" v-for="a in anime" :key="a.id">
          <AnimeCard
            :anime="toCardAnime(a)"
            :show-actions="true"
            :show-genres="false"
            :show-progress="false"
            @click="router.push(`/anime/${a.id}`)"
          />
        </div>
      </div>

      <!-- Стрелка вправо -->
      <button
        v-if="!atEnd"
        class="rc-arrow rc-arrow-right"
        @click="scroll(1)"
        type="button"
        aria-label="Вперёд"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
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

const props = defineProps<{
  title: string
  description?: string
  icon?: string
  anime: AnimeItem[]
  loading?: boolean
  hasViewAll?: boolean
}>()

defineEmits<{ 'view-all': [] }>()

const router   = useRouter()
const trackRef = ref<HTMLElement | null>(null)

const atStart = ref(true)
const atEnd   = ref(false)

const CARD_W = 196 // 180px + 16px gap

const updateArrows = () => {
  const el = trackRef.value
  if (!el) return
  atStart.value = el.scrollLeft <= 4
  atEnd.value   = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4
}

const scroll = (dir: 1 | -1) => {
  const el = trackRef.value
  if (!el) return
  el.scrollBy({ left: dir * CARD_W * 3, behavior: 'smooth' })
}

watch(() => props.anime, async () => {
  await nextTick()
  updateArrows()
})

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
.rc {
  margin-bottom: var(--space-8);
}

/* ── Заголовок ─────────────────────────────────────────────── */
.rc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  gap: var(--space-4);
}

.rc-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.rc-icon { font-size: 22px; line-height: 1; flex-shrink: 0; }

.rc-texts { min-width: 0; }

.rc-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.015em;
}

.rc-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin: 3px 0 0;
}

.rc-view-all {
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
.rc-view-all:hover { background: var(--accent-subtle); }

/* ── Пусто ─────────────────────────────────────────────────── */
.rc-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  background: var(--surface-2);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
}

/* ── Карусель ──────────────────────────────────────────────── */
.rc-carousel-wrap {
  position: relative;
}

/* Затухание по краям */
.rc-carousel-wrap::before,
.rc-carousel-wrap::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 4px;
  width: 48px;
  z-index: 1;
  pointer-events: none;
}
.rc-carousel-wrap::before {
  left: 0;
  background: linear-gradient(to right, var(--surface-1, #0c0c0f), transparent);
}
.rc-carousel-wrap::after {
  right: 0;
  background: linear-gradient(to left, var(--surface-1, #0c0c0f), transparent);
}

.rc-track {
  display: flex;
  gap: var(--space-4);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 4px;
}
.rc-track::-webkit-scrollbar { display: none; }

.rc-card-wrap {
  flex: 0 0 180px;
  width: 180px;
  scroll-snap-align: start;
}

/* Стрелки */
.rc-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(calc(-50% - 2px));
  z-index: 100;
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
  pointer-events: auto;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-out),
              background-color var(--duration-base) var(--ease-out),
              transform var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.4));
}

.rc-carousel-wrap:hover .rc-arrow { opacity: 1; }

.rc-arrow:hover {
  background: var(--accent);
  border-color: var(--accent);
  transform: translateY(calc(-50% - 2px)) scale(1.08);
}

.rc-arrow-left  { left:  -12px; }
.rc-arrow-right { right: -12px; }

/* ── Скелетон ──────────────────────────────────────────────── */
.rc-skel {
  flex: 0 0 180px;
  width: 180px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rc-skel-poster {
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.rc-skel-line {
  height: 12px; width: 85%;
  border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: sk 1.4s ease-in-out infinite;
}
.rc-skel-line.short { width: 60%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

/* ── Адаптив ───────────────────────────────────────────────── */
@media (max-width: 767px) {
  .rc-card-wrap { flex: 0 0 140px; width: 140px; }
  .rc-skel { flex: 0 0 140px; width: 140px; }
  .rc-arrow { display: none; }
}
</style>
