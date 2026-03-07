<template>
  <AnimePosterCard
    :id="animeId"
    :title="title"
    :poster="poster"
    :year="year || null"
    :score="rating"
    :status="animeStatus"
    :genres="genres"
    :rank="rank"
    :is-franchise-member="isFranchise"
    :franchise-id="franchiseId"
    :show-overlay="true"
    :show-score="!!rating"
    :show-status="!!status"
    :show-progress="false"
    :show-meta="false"
    :show-genres="!!genres?.length"
    :max-genres="2"
    :overlay-config="{ play: true, more: true }"
    @click="handleClick"
    @play="handleClick"
    @more="handleAddToCollection"
  >
    <template #info>
      <button class="action-btn" @click.stop="handleAddToCollection">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        В коллекцию
      </button>
    </template>
  </AnimePosterCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AnimePosterCard from './AnimePosterCard.vue'

interface Props {
  animeId: number
  title: string
  poster: string
  genres: string[]
  rating: number | null
  ratingCount: number
  status: string
  year: number | null
  rank?: number
  franchiseId?: number | null
  isFranchise?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [id: number]
  'add-to-collection': [id: number]
}>()

const router = useRouter()

const animeStatus = computed(() => {
  const map: Record<string, string> = {
    ongoing: 'ongoing',
    finished: 'finished',
    announced: 'announced',
    released: 'released'
  }
  return props.status ? map[props.status] || props.status : null
})

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

const handleAddToCollection = () => {
  emit('add-to-collection', props.animeId)
}
</script>

<style scoped>
.recommend-card {
  flex: 1 1 auto;
  min-width: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  width: 100%;
  padding: 6px var(--space-2);
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  min-height: 30px;
}

.action-btn:hover {
  background: var(--accent);
  color: var(--text-on-accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

@media (max-width: 767px) {
  .recommend-card { flex: 0 0 140px; width: 140px; }
}
</style>
