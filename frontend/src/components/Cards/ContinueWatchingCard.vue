<template>
  <div class="cwc-wrap">
    <AnimeCard
      :anime="cardAnime"
      :show-actions="true"
      :show-genres="false"
      :show-progress="true"
      :watch-progress="currentEpisode"
      :total-episodes="totalEpisodes"
      @click="handleClick"
    />
    <!-- Прогресс-бар поверх — встроен в AnimeCard через watch-progress -->
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
  currentEpisode: number
  totalEpisodes: number
  progressPercent: number
}

const props = defineProps<Props>()

const router = useRouter()

const cardAnime = computed(() => ({
  id: props.animeId,
  title_ru: props.title,
  title_en: '',
  year: null,
  status: 'ongoing',
  episodes: props.totalEpisodes || null,
  score: null,
  poster_url: props.poster || null,
  poster_image_url: props.poster || null,
  poster: null as any,
  type: '',
  genres: [],
}))

const handleClick = () => {
  router.push(`/anime/${props.animeId}/watch?episode=${props.currentEpisode}`)
}
</script>

<style scoped>
.cwc-wrap {
  flex: 0 0 220px;
  width: 220px;
  scroll-snap-align: start;
}

@media (max-width: 767px) {
  .cwc-wrap { flex: 0 0 155px; width: 155px; }
}
</style>
