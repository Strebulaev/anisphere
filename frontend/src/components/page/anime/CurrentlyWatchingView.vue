<template>
  <div class="cw">

    <!-- Заголовок -->
    <div class="cw-header">
      <div>
        <h2 class="cw-title">👁 Сейчас смотрят</h2>
        <p class="cw-subtitle">Аниме, которые активно смотрят прямо сейчас на сайте</p>
      </div>
      <button class="cw-refresh" @click="$emit('refresh')" :disabled="loading" type="button">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          :class="{ spin: loading }">
          <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        Обновить
      </button>
    </div>

    <!-- Скелетон -->
    <div v-if="loading" class="cw-grid">
      <div v-for="i in 12" :key="i" class="cw-skel">
        <div class="cw-skel-poster"></div>
        <div class="cw-skel-line"></div>
        <div class="cw-skel-line short"></div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="cw-message cw-error">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div>
        <p class="cw-msg-title">Не удалось загрузить данные</p>
        <button @click="$emit('refresh')" class="cw-retry" type="button">Попробовать снова</button>
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="!anime.length" class="cw-message">
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      <div>
        <p class="cw-msg-title">Никто ничего не смотрит прямо сейчас</p>
        <p class="cw-msg-sub">Попробуйте обновить через несколько минут</p>
      </div>
    </div>

    <!-- Сетка -->
    <div v-else class="cw-grid">
      <AnimeCard
        v-for="a in anime"
        :key="a.id"
        :anime="toCardAnime(a)"
        :show-actions="true"
        :show-genres="false"
        :show-progress="false"
        @click="goToAnime(a.id)"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AnimeCard from '@/components/Cards/AnimeCard.vue'

interface Props { anime: any[]; loading: boolean; error: string | null }
defineProps<Props>()
defineEmits<{ refresh: [] }>()

const router = useRouter()

const goToAnime = (anime: any) => router.push(`/anime/${anime?.id ?? anime}`)

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
  genres: [],
})
</script>

<style scoped>
.cw-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding: var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.cw-title {
  font-size: var(--text-2xl);
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: -0.02em;
}

.cw-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin: 0; }

.cw-refresh {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}
.cw-refresh:hover:not(:disabled) { background: var(--surface-5); color: var(--text-primary); }
.cw-refresh:disabled { opacity: .5; cursor: not-allowed; }

.cw-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.cw-skel { display: flex; flex-direction: column; gap: 8px; }
.cw-skel-poster {
  aspect-ratio: 2/3; border-radius: var(--radius-card);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line {
  height: 13px; width: 80%; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%; animation: sk 1.4s ease-in-out infinite;
}
.cw-skel-line.short { width: 52%; }
@keyframes sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.cw-message {
  display: flex; align-items: center; gap: var(--space-5);
  padding: 60px var(--space-8); color: var(--text-tertiary);
}
.cw-message svg { opacity: .5; flex-shrink: 0; }
.cw-msg-title { font-size: var(--text-lg); color: var(--text-secondary); margin: 0 0 var(--space-1); }
.cw-msg-sub   { font-size: var(--text-sm); margin: 0; }
.cw-error svg { color: var(--danger); opacity: 1; }
.cw-retry {
  background: none; border: none; color: var(--accent);
  font-size: var(--text-sm); cursor: pointer; padding: 0; text-decoration: underline;
}

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 767px) {
  .cw-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
}
</style>
