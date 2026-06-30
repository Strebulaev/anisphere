import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import animeApi from '@/api/anime'
import type { Anime } from '@/types'

export function useRandomAnime() {
  const router = useRouter()
  const randomAnime = ref<Anime | null>(null)
  const randomAnimeList = ref<Anime[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchRandomAnime = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      randomAnime.value = (await animeApi.getRandomAnime()) as Anime | null
    } catch (err: any) {
      console.error('Ошибка загрузки случайного аниме:', err)
      error.value = err.message || 'Не удалось загрузить случайное аниме'
      randomAnime.value = null
    } finally {
      loading.value = false
    }
  }

  const fetchRandomAnimeList = async (limit: number = 6): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      randomAnimeList.value = (await animeApi.getRandomAnimeList(limit)) as Anime[]
    } catch (err: any) {
      console.error('Ошибка загрузки случайных аниме:', err)
      error.value = err.message || 'Не удалось загрузить случайные аниме'
      randomAnimeList.value = []
    } finally {
      loading.value = false
    }
  }

  
  const goToRandomAnime = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const anime = await animeApi.getRandomAnime()
      router.push(`/anime/${anime.id}`)
    } catch (err: any) {
      console.error('Ошибка загрузки случайного аниме:', err)
      error.value = err.message || 'Не удалось загрузить случайное аниме'
    } finally {
      loading.value = false
    }
  }

  
  const goToAnime = (anime: Anime) => {
    router.push(`/anime/${anime.id}`)
  }

  
  const refresh = () => {
    fetchRandomAnime()
  }

  
  const refreshList = () => {
    fetchRandomAnimeList()
  }

  return {
    randomAnime: computed(() => randomAnime.value),
    randomAnimeList: computed(() => randomAnimeList.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchRandomAnime,
    fetchRandomAnimeList,
    goToRandomAnime,
    goToAnime,
    refresh,
    refreshList
  }
}
