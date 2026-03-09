<template>
  <div class="rwc-wrap">
    <AnimeCard
      :anime="cardAnime"
      :show-actions="true"
      :show-genres="false"
      :show-progress="false"
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
  completedDate: string | null
  userRating: number | null
}

const props = defineProps<Props>()

const router = useRouter()

const cardAnime = computed(() => ({
  id: props.animeId,
  title_ru: props.title,
  title_en: '',
  year: null,
  status: 'finished',
  episodes: null,
  score: props.userRating,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null as any,
  type: '',
  genres: [],
}))

// Клик на карточку — пересмотр с 1-й серии
const handleClick = () => {
  router.push(`/anime/${props.animeId}/watch?episode=1`)
}
</script>

<style scoped>
.rwc-wrap {
  flex: 0 0 220px;
  width: 220px;
  scroll-snap-align: start;
}

@media (max-width: 767px) {
  .rwc-wrap { flex: 0 0 155px; width: 155px; }
}
</style>
