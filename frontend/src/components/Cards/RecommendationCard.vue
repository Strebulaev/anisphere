<template>
  <div class="rec-card-wrap">
    <!-- Франшиза -->
    <FranchiseCard
      v-if="isFranchise && franchiseData"
      :franchise="franchiseData"
      :show-actions="true"
      @click="handleFranchiseClick"
    />
    <!-- Обычное аниме -->
    <AnimeCard
      v-else
      :anime="cardAnime"
      :show-actions="true"
      :show-genres="!!genres?.length"
      :show-progress="false"
      :max-genres="2"
      @click="handleClick"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from './AnimeCard.vue'
import FranchiseCard from './FranchiseCard.vue'

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
  franchiseName?: string
  franchisePartsCount?: number
  franchiseYearStart?: number | null
  franchiseYearEnd?: number | null
  franchiseScore?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  click: [id: number]
  'add-to-collection': [id: number]
}>()

const router = useRouter()

const cardAnime = computed(() => ({
  id: props.animeId,
  title_ru: props.title,
  title_en: '',
  year: props.year ?? null,
  status: props.status || '',
  episodes: null,
  score: props.rating,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null as any,
  type: '',
  genres: (props.genres || []).map((g, i) => ({ id: i, name: g, slug: g })),
}))

const franchiseData = computed(() => {
  if (!props.isFranchise || !props.franchiseId) return null
  return {
    id: props.franchiseId,
    name: props.franchiseName || props.title,
    poster_url: props.poster || null,
    poster_image_url: props.poster || null,
    poster: null as any,
    parts_count: props.franchisePartsCount || 1,
    year_start: props.franchiseYearStart || null,
    year_end: props.franchiseYearEnd || null,
    score: props.franchiseScore || props.rating,
    all_genres: props.genres || [],
    all_posters: props.poster ? [props.poster] : [],
  }
})

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
}

const handleFranchiseClick = () => {
  if (props.franchiseId) {
    router.push(`/franchise/${props.franchiseId}`)
  }
}
</script>

<style scoped>
.rec-card-wrap {
  flex: 0 0 220px;
  width: 220px;
  scroll-snap-align: start;
}

@media (max-width: 767px) {
  .rec-card-wrap { flex: 0 0 155px; width: 155px; }
}
</style>
