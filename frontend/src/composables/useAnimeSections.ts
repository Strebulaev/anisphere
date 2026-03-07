import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import animeApi from '@/api/anime'
import type { Anime } from '@/types'

export type AnimeSection = 'catalog' | 'ongoings' | 'recommendations' | 'announcements' | 'random'

export function useAnimeSections() {
  const route = useRoute()
  const router = useRouter()

  const currentSection = ref<AnimeSection>('catalog')
  
  // Оригинальные данные секций (для сброса после перемешивания)
  const originalCatalogAnime = ref<Anime[]>([])
  const originalOngoings = ref<Anime[]>([])
  const originalAnnouncements = ref<Anime[]>([])
  const originalRecommendations = ref<Anime[]>([])
  const originalRandomAnimeList = ref<Anime[]>([])
  
  // Данные секций (могут быть перемешаны)
  const catalogAnime = ref<Anime[]>([])
  const ongoings = ref<Anime[]>([])
  const announcements = ref<Anime[]>([])
  const recommendations = ref<Anime[]>([])
  const randomAnimeList = ref<Anime[]>([])
  
  // Состояния загрузки
  const catalogLoading = ref(false)
  const ongoingsLoading = ref(false)
  const announcementsLoading = ref(false)
  const recommendationsLoading = ref(false)
  const randomLoading = ref(false)

  // Ошибки
  const catalogError = ref<string | null>(null)
  const ongoingsError = ref<string | null>(null)
  const announcementsError = ref<string | null>(null)
  const recommendationsError = ref<string | null>(null)
  const randomError = ref<string | null>(null)

  // Пагинация для каталога
  const catalogPage = ref(1)
  const catalogTotalPages = ref(1)
  const catalogTotalCount = ref(0)

  // Состояние перемешивания для каждой секции
  const isShuffled = ref<Record<AnimeSection, boolean>>({
    catalog: false,
    ongoings: false,
    recommendations: false,
    announcements: false,
    random: false
  })

  // Функция перемешивания массива (алгоритм Фишера-Йетса)
  const shuffleArray = <T>(array: T[]): T[] => {
    const shuffled: T[] = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const temp = shuffled[i];
      if (temp !== undefined) {
        shuffled[i] = shuffled[j] as T;
        if (shuffled[j] !== undefined) {
          shuffled[j] = temp;
        }
      }
    }
    return shuffled
  }

  // Перемешать текущую секцию
  const shuffleCurrentSection = () => {
    const section = currentSection.value
    let displayArray: Anime[] = []

    switch (section) {
      case 'catalog':
        displayArray = catalogAnime.value
        break
      case 'ongoings':
        displayArray = ongoings.value
        break
      case 'recommendations':
        displayArray = recommendations.value
        break
      case 'announcements':
        displayArray = announcements.value
        break
      case 'random':
        displayArray = randomAnimeList.value
        break
    }

    if (displayArray.length > 0) {
      const shuffled = shuffleArray(displayArray)
      
      switch (section) {
        case 'catalog':
          catalogAnime.value = shuffled
          break
        case 'ongoings':
          ongoings.value = shuffled
          break
        case 'recommendations':
          recommendations.value = shuffled
          break
        case 'announcements':
          announcements.value = shuffled
          break
        case 'random':
          randomAnimeList.value = shuffled
          break
      }
      
      isShuffled.value[section] = true
    }
  }

  // Сбросить перемешивание для текущей секции
  const unshuffleCurrentSection = () => {
    const section = currentSection.value
    
    switch (section) {
      case 'catalog':
        catalogAnime.value = [...originalCatalogAnime.value]
        break
      case 'ongoings':
        ongoings.value = [...originalOngoings.value]
        break
      case 'recommendations':
        recommendations.value = [...originalRecommendations.value]
        break
      case 'announcements':
        announcements.value = [...originalAnnouncements.value]
        break
      case 'random':
        randomAnimeList.value = [...originalRandomAnimeList.value]
        break
    }
    
    isShuffled.value[section] = false
  }

  // Проверка, перемешана ли текущая секция
  const currentSectionIsShuffled = computed(() => {
    return isShuffled.value[currentSection.value]
  })

  // Загрузить онгоинги
  const fetchOngoings = async () => {
    ongoingsLoading.value = true
    ongoingsError.value = null

    try {
      const data = (await animeApi.getOngoings()) as any
      ongoings.value = data
      originalOngoings.value = [...data]
    } catch (err: any) {
      console.error('Ошибка загрузки онгоингов:', err)
      ongoingsError.value = err.message || 'Не удалось загрузить онгоинги'
      ongoings.value = []
      originalOngoings.value = []
    } finally {
      ongoingsLoading.value = false
    }
  }

  // Загрузить анонсы
  const fetchAnnouncements = async () => {
    announcementsLoading.value = true
    announcementsError.value = null

    try {
      const data = (await animeApi.getAnnouncements()) as any
      announcements.value = data
      originalAnnouncements.value = [...data]
    } catch (err: any) {
      console.error('Ошибка загрузки анонсов:', err)
      announcementsError.value = err.message || 'Не удалось загрузить анонсы'
      announcements.value = []
      originalAnnouncements.value = []
    } finally {
      announcementsLoading.value = false
    }
  }

  // Загрузить рекомендации
  const fetchRecommendations = async () => {
    recommendationsLoading.value = true
    recommendationsError.value = null

    try {
      const response = await animeApi.list({
        ordering: '-score,-favorites' as any,
        page_size: 12
      })
      recommendations.value = (response.results || []) as any
      originalRecommendations.value = [...(response.results || [])]
    } catch (err: any) {
      console.error('Ошибка загрузки рекомендаций:', err)
      recommendationsError.value = err.message || 'Не удалось загрузить рекомендации'
      recommendations.value = []
      originalRecommendations.value = []
    } finally {
      recommendationsLoading.value = false
    }
  }

  // Загрузить случайные аниме
  const fetchRandomAnimeList = async (limit: number = 6) => {
    randomLoading.value = true
    randomError.value = null

    try {
      const data = (await animeApi.getRandomAnimeList(limit)) as any
      randomAnimeList.value = data
      originalRandomAnimeList.value = [...data]
    } catch (err: any) {
      console.error('Ошибка загрузки случайных аниме:', err)
      randomError.value = err.message || 'Не удалось загрузить случайные аниме'
      randomAnimeList.value = []
      originalRandomAnimeList.value = []
    } finally {
      randomLoading.value = false
    }
  }

  // Текущие фильтры каталога
  const catalogFilters = ref<any>({})

  // Загрузить каталог
  const fetchCatalog = async (page: number = 1, filters?: any) => {
    catalogLoading.value = true
    catalogError.value = null

    // Обновляем фильтры если переданы
    if (filters) {
      catalogFilters.value = filters
    }

    try {
      const response = await animeApi.list({
        page,
        page_size: catalogFilters.value.page_size || 50,
        ordering: catalogFilters.value.ordering || '-score',
        search: catalogFilters.value.search,
        genres: catalogFilters.value.genres,
        genre_logic: catalogFilters.value.genre_logic,
        year_from: catalogFilters.value.year_from,
        year_to: catalogFilters.value.year_to,
        status: catalogFilters.value.status,
        type: catalogFilters.value.type,
        episodes_from: catalogFilters.value.episodes_from,
        episodes_to: catalogFilters.value.episodes_to,
        score_from: catalogFilters.value.score_from,
        score_to: catalogFilters.value.score_to,
        studio: catalogFilters.value.studio,
        country: catalogFilters.value.country,
        rus_translation: catalogFilters.value.rus_translation,
        age_rating: catalogFilters.value.age_rating,
        has_awards: catalogFilters.value.has_awards,
        duration_from: catalogFilters.value.duration_from,
        duration_to: catalogFilters.value.duration_to,
        author: catalogFilters.value.author,
        director: catalogFilters.value.director,
        composer: catalogFilters.value.composer,
        season: catalogFilters.value.season,
        season_year: catalogFilters.value.season_year,
        popularity_from: catalogFilters.value.popularity_from,
        popularity_to: catalogFilters.value.popularity_to,
        added_from: catalogFilters.value.added_from,
        added_to: catalogFilters.value.added_to
      })
      catalogAnime.value = (response.results || []) as any
      if (page === 1) {
        originalCatalogAnime.value = [...(response.results || [])]
      }
      catalogTotalPages.value = response.total_pages || 1
      catalogTotalCount.value = response.count || 0
      catalogPage.value = page
    } catch (err: any) {
      console.error('Ошибка загрузки каталога:', err)
      catalogError.value = err.message || 'Не удалось загрузить каталог'
      catalogAnime.value = []
    } finally {
      catalogLoading.value = false
    }
  }

  // Переключить секцию
  const switchSection = (section: AnimeSection) => {
    currentSection.value = section
    
    router.replace({
      path: route.path,
      query: { section }
    })

    switch (section) {
      case 'ongoings':
        if (ongoings.value.length === 0) {
          fetchOngoings()
        }
        break
      case 'recommendations':
        if (recommendations.value.length === 0) {
          fetchRecommendations()
        }
        break
      case 'announcements':
        if (announcements.value.length === 0) {
          fetchAnnouncements()
        }
        break
      case 'random':
        if (randomAnimeList.value.length === 0) {
          fetchRandomAnimeList(6)
        }
        break
      case 'catalog':
        if (catalogAnime.value.length === 0) {
          fetchCatalog(1)
        }
        break
    }
  }

  // Обновить текущую секцию
  const refreshCurrentSection = () => {
    switch (currentSection.value) {
      case 'ongoings':
        fetchOngoings()
        break
      case 'recommendations':
        fetchRecommendations()
        break
      case 'announcements':
        fetchAnnouncements()
        break
      case 'random':
        fetchRandomAnimeList(6)
        break
      case 'catalog':
        fetchCatalog(catalogPage.value)
        break
    }
  }

  // Получить данные для текущей секции
  const currentData = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':
        return ongoings.value
      case 'recommendations':
        return recommendations.value
      case 'announcements':
        return announcements.value
      case 'random':
        return randomAnimeList.value
      case 'catalog':
        return catalogAnime.value
      default:
        return []
    }
  })

  // Получить состояние загрузки для текущей секции
  const currentLoading = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':
        return ongoingsLoading.value
      case 'recommendations':
        return recommendationsLoading.value
      case 'announcements':
        return announcementsLoading.value
      case 'random':
        return randomLoading.value
      case 'catalog':
        return catalogLoading.value
      default:
        return false
    }
  })

  // Получить ошибку для текущей секции
  const currentError = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':
        return ongoingsError.value
      case 'recommendations':
        return recommendationsError.value
      case 'announcements':
        return announcementsError.value
      case 'random':
        return randomError.value
      case 'catalog':
        return catalogError.value
      default:
        return null
    }
  })

  // Загрузить все секции (для предзагрузки)
  const loadAllSections = async () => {
    await Promise.all([
      fetchOngoings(),
      fetchRecommendations(),
      fetchAnnouncements(),
      fetchRandomAnimeList(6),
      fetchCatalog(1)
    ])
  }

  // Инициализация при монтировании
  onMounted(() => {
    const sectionParam = route.query.section as AnimeSection
    if (sectionParam && ['catalog', 'ongoings', 'recommendations', 'announcements', 'random'].includes(sectionParam)) {
      currentSection.value = sectionParam
    }

    switchSection(currentSection.value)
  })

  watch(() => route.query.section, (newSection) => {
    const sectionParam = newSection as AnimeSection
    if (sectionParam && ['catalog', 'ongoings', 'recommendations', 'announcements', 'random'].includes(sectionParam)) {
      currentSection.value = sectionParam
      switchSection(sectionParam)
    }
  })

  return {
    currentSection,
    currentData,
    currentLoading,
    currentError,
    
    // Данные секций
    catalogAnime,
    ongoings,
    announcements,
    recommendations,
    randomAnimeList,
    
    // Состояния загрузки
    catalogLoading,
    ongoingsLoading,
    announcementsLoading,
    recommendationsLoading,
    randomLoading,
    
    // Ошибки
    catalogError,
    ongoingsError,
    announcementsError,
    recommendationsError,
    randomError,
    
    // Пагинация каталога
    catalogPage,
    catalogTotalPages,
    catalogTotalCount,
    
    // Перемешивание
    isShuffled,
    currentSectionIsShuffled,
    shuffleCurrentSection,
    unshuffleCurrentSection,
    
    // Методы
    switchSection,
    refreshCurrentSection,
    fetchCatalog,
    fetchOngoings,
    fetchAnnouncements,
    fetchRecommendations,
    fetchRandomAnimeList,
    loadAllSections
  }
}
