<template>
  <div class="rec-card-wrap">
    <AnimeCard
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

const handleClick = () => {
  router.push(`/anime/${props.animeId}`)
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
