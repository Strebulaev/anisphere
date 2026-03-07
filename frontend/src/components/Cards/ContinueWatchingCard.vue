<template>
  <AnimePosterCard
    :id="animeId"
    :title="title"
    :poster="poster"
    :current-episode="currentEpisode"
    :episodes="totalEpisodes"
    :progress-percent="progressPercent"
    :show-overlay="true"
    :show-score="false"
    :show-status="false"
    :show-progress="true"
    :show-meta="false"
    :show-favorite-btn="false"
    :overlay-config="{ play: true, more: true }"
    play-label="Продолжить"
    @click="handleClick"
    @play="handleAction"
    @more="handleAction"
  >
    <template #info>
      <div class="card-extra">
        <p class="card-episode">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          Серия {{ currentEpisode }} из {{ totalEpisodes }}
        </p>
        <button class="action-btn" @click.stop="handleAction">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Продолжить
        </button>
      </div>
    </template>
  </AnimePosterCard>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AnimePosterCard from './AnimePosterCard.vue'

interface Props {
  animeId: number
  title: string
  poster: string
  currentEpisode: number
  totalEpisodes: number
  progressPercent: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [id: number]
  action: [id: number]
}>()

const router = useRouter()

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

const handleAction = () => {
  router.push(`/anime/${props.animeId}/watch?episode=${props.currentEpisode}`)
  emit('action', props.animeId)
}
</script>

<style scoped>
.continue-card {
  flex: 1 1 auto;
  min-width: 0;
}

.card-extra {
  padding: var(--space-2) var(--space-1) var(--space-1);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.card-episode {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  width: 100%;
  padding: 6px var(--space-2);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background-color var(--duration-base) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
  min-height: 30px;
}

.action-btn:hover {
  background: var(--accent-hover);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

@media (max-width: 767px) {
  .continue-card { flex: 0 0 140px; width: 140px; }
}
</style>
