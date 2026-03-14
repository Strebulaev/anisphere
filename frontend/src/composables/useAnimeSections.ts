import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import animeApi from '@/api/anime'
import type { Anime } from '@/types'

export type AnimeSection = 'catalog' | 'ongoings' | 'recommendations' | 'announcements' | 'random' | 'currently_watching'

// Флаг для отслеживания первого открытия каталога в сессии
let catalogInitialShuffleApplied = false

export function useAnimeSections() {
  const route = useRoute()
  const router = useRouter()

  const SECTION_STORAGE_KEY = 'anime_active_section'
  const currentSection = ref<AnimeSection>('catalog')
  
  const originalCatalogAnime = ref<Anime[]>([])
  const originalOngoings = ref<Anime[]>([])
  const originalAnnouncements = ref<Anime[]>([])
  const originalRecommendations = ref<Anime[]>([])
  const originalRandomAnimeList = ref<Anime[]>([])
  
  const catalogAnime = ref<Anime[]>([])
  const ongoings = ref<Anime[]>([])
  const announcements = ref<Anime[]>([])
  const recommendations = ref<Anime[]>([])
  const randomAnimeList = ref<Anime[]>([])
  
  const catalogLoading = ref(false)
  const ongoingsLoading = ref(false)
  const announcementsLoading = ref(false)
  const recommendationsLoading = ref(false)
  const randomLoading = ref(false)

  const catalogError = ref<string | null>(null)
  const ongoingsError = ref<string | null>(null)
  const announcementsError = ref<string | null>(null)
  const recommendationsError = ref<string | null>(null)
  const randomError = ref<string | null>(null)

  const catalogPage = ref(1)
  const catalogTotalPages = ref(1)
  const catalogTotalCount = ref(0)

  const isShuffled = ref<Record<AnimeSection, boolean>>({
    catalog: false,
    ongoings: false,
    recommendations: false,
    announcements: false,
    random: false,
    currently_watching: false
  })

  const shuffleArray = <T>(array: T[]): T[] => {
    const shuffled: T[] = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j] as T, shuffled[i] as T]
    }
    return shuffled
  }

  const shuffleCurrentSection = () => {
    const section = currentSection.value
    const map: Record<AnimeSection, { get: () => Anime[], set: (v: Anime[]) => void }> = {
      catalog:         { get: () => catalogAnime.value,      set: v => { catalogAnime.value = v } },
      ongoings:        { get: () => ongoings.value,          set: v => { ongoings.value = v } },
      recommendations: { get: () => recommendations.value,   set: v => { recommendations.value = v } },
      announcements:   { get: () => announcements.value,     set: v => { announcements.value = v } },
      random:          { get: () => randomAnimeList.value,   set: v => { randomAnimeList.value = v } },
      currently_watching: { get: () => [], set: () => {} },
    }
    const entry = map[section]
    if (entry.get().length > 0) {
      entry.set(shuffleArray(entry.get()))
      isShuffled.value[section] = true
    }
  }

  const unshuffleCurrentSection = () => {
    const section = currentSection.value
    const origMap: Record<AnimeSection, { get: () => Anime[], set: (v: Anime[]) => void }> = {
      catalog:         { get: () => originalCatalogAnime.value,      set: v => { catalogAnime.value = v } },
      ongoings:        { get: () => originalOngoings.value,          set: v => { ongoings.value = v } },
      recommendations: { get: () => originalRecommendations.value,   set: v => { recommendations.value = v } },
      announcements:   { get: () => originalAnnouncements.value,     set: v => { announcements.value = v } },
      random:          { get: () => originalRandomAnimeList.value,   set: v => { randomAnimeList.value = v } },
      currently_watching: { get: () => [], set: () => {} },
    }
    origMap[section].set([...origMap[section].get()])
    isShuffled.value[section] = false
  }

  const currentSectionIsShuffled = computed(() => isShuffled.value[currentSection.value])

  const fetchOngoings = async () => {
    ongoingsLoading.value = true
    ongoingsError.value = null
    try {
      const data = (await animeApi.getOngoings()) as any
      ongoings.value = data
      originalOngoings.value = [...data]
    } catch (err: any) {
      ongoingsError.value = err.message || 'Не удалось загрузить онгоинги'
      ongoings.value = []
      originalOngoings.value = []
    } finally {
      ongoingsLoading.value = false
    }
  }

  const fetchAnnouncements = async () => {
    announcementsLoading.value = true
    announcementsError.value = null
    try {
      const data = (await animeApi.getAnnouncements()) as any
      announcements.value = data
      originalAnnouncements.value = [...data]
    } catch (err: any) {
      announcementsError.value = err.message || 'Не удалось загрузить анонсы'
      announcements.value = []
      originalAnnouncements.value = []
    } finally {
      announcementsLoading.value = false
    }
  }

  const fetchRecommendations = async () => {
    recommendationsLoading.value = true
    recommendationsError.value = null
    try {
      // Используем только реальные поля модели для сортировки
      const response = await animeApi.list({ ordering: '-score', page_size: 12 })
      recommendations.value = (response.results || []) as any
      originalRecommendations.value = [...(response.results || [])]
    } catch (err: any) {
      recommendationsError.value = err.message || 'Не удалось загрузить рекомендации'
      recommendations.value = []
      originalRecommendations.value = []
    } finally {
      recommendationsLoading.value = false
    }
  }

  const fetchRandomAnimeList = async (limit: number = 6) => {
    randomLoading.value = true
    randomError.value = null
    try {
      const data = (await animeApi.getRandomAnimeList(limit)) as any
      randomAnimeList.value = data
      originalRandomAnimeList.value = [...data]
    } catch (err: any) {
      randomError.value = err.message || 'Не удалось загрузить случайные аниме'
      randomAnimeList.value = []
      originalRandomAnimeList.value = []
    } finally {
      randomLoading.value = false
    }
  }

  const catalogFilters = ref<any>({})
  const catalogShuffle = ref(false)

  const fetchCatalog = async (page: number = 1, filters?: any) => {
    catalogLoading.value = true
    catalogError.value = null

    if (filters) {
      catalogFilters.value = filters
    }

    try {
      const f = catalogFilters.value
      const response = await animeApi.list({
        page,
        page_size:     f.page_size     || 50,
        ordering:      (f.ordering      || '-score') as any,
        search:        f.search,
        genres:        f.genres,
        genre_logic:   f.genre_logic   as any,
        year_from:     f.year_from,
        year_to:       f.year_to,
        status:        f.status,
        type:          f.type,
        episodes_from: f.episodes_from,
        episodes_to:   f.episodes_to,
        score_from:    f.score_from,
        score_to:      f.score_to,
        studio:        f.studio,
        shuffle:       catalogShuffle.value,
      })
      catalogAnime.value = (response.results || []) as any
      if (page === 1) originalCatalogAnime.value = [...(response.results || [])]
      catalogTotalPages.value = response.total_pages || 1
      catalogTotalCount.value = response.count || 0
      catalogPage.value = page
    } catch (err: any) {
      catalogError.value = err.message || 'Не удалось загрузить каталог'
      catalogAnime.value = []
    } finally {
      catalogLoading.value = false
    }
  }

  const switchSection = (section: AnimeSection) => {
    currentSection.value = section
    // Сохраняем выбранную вкладку
    try { localStorage.setItem(SECTION_STORAGE_KEY, section) } catch {}
    router.replace({ path: route.path, query: { section } })
    switch (section) {
      case 'ongoings':        if (!ongoings.value.length)        fetchOngoings();        break
      case 'recommendations': if (!recommendations.value.length) fetchRecommendations(); break
      case 'announcements':   if (!announcements.value.length)   fetchAnnouncements();   break
      case 'random':          if (!randomAnimeList.value.length) fetchRandomAnimeList(6);break
      case 'catalog':
        if (!catalogAnime.value.length) {
          // Автоматически применяем shuffle при первом открытии каталога в сессии
          if (!catalogInitialShuffleApplied) {
            catalogShuffle.value = true
            isShuffled.value.catalog = true
            catalogInitialShuffleApplied = true
          }
          fetchCatalog(1)
        }
        break
    }
  }

  const refreshCurrentSection = () => {
    switch (currentSection.value) {
      case 'ongoings':        fetchOngoings();         break
      case 'recommendations': fetchRecommendations();  break
      case 'announcements':   fetchAnnouncements();    break
      case 'random':          fetchRandomAnimeList(6); break
      case 'catalog':         fetchCatalog(catalogPage.value); break
    }
  }

  const currentData = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':        return ongoings.value
      case 'recommendations': return recommendations.value
      case 'announcements':   return announcements.value
      case 'random':          return randomAnimeList.value
      case 'catalog':         return catalogAnime.value
      default:                return []
    }
  })

  const currentLoading = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':        return ongoingsLoading.value
      case 'recommendations': return recommendationsLoading.value
      case 'announcements':   return announcementsLoading.value
      case 'random':          return randomLoading.value
      case 'catalog':         return catalogLoading.value
      default:                return false
    }
  })

  const currentError = computed(() => {
    switch (currentSection.value) {
      case 'ongoings':        return ongoingsError.value
      case 'recommendations': return recommendationsError.value
      case 'announcements':   return announcementsError.value
      case 'random':          return randomError.value
      case 'catalog':         return catalogError.value
      default:                return null
    }
  })

  const loadAllSections = async () => {
    await Promise.all([
      fetchOngoings(),
      fetchRecommendations(),
      fetchAnnouncements(),
      fetchRandomAnimeList(6),
      fetchCatalog(1)
    ])
  }

  const ALL_SECTIONS: string[] = ['catalog','ongoings','recommendations','announcements','random','currently_watching']

  onMounted(() => {
    // Приоритет: URL-параметр > localStorage > по умолчанию (catalog)
    const sectionParam = route.query.section as string
    if (sectionParam && ALL_SECTIONS.includes(sectionParam)) {
      currentSection.value = sectionParam as AnimeSection
      // Сохраняем в localStorage для консистентности
      try { localStorage.setItem(SECTION_STORAGE_KEY, sectionParam) } catch {}
    } else {
      try {
        const saved = localStorage.getItem(SECTION_STORAGE_KEY) as AnimeSection | null
        if (saved && ALL_SECTIONS.includes(saved)) {
          currentSection.value = saved
        }
      } catch {}
    }
    // Вкладку 'currently_watching' загружает AnimeView.vue,
    // здесь пропускаем вызов switchSection для неё
    if (currentSection.value !== 'currently_watching') {
      switchSection(currentSection.value)
    }
  })

  watch(() => route.query.section, (newSection) => {
    const s = newSection as AnimeSection
    if (s && ['catalog','ongoings','recommendations','announcements','random'].includes(s)) {
      currentSection.value = s
      switchSection(s)
    }
  })

  const enableCatalogShuffle = () => {
    catalogShuffle.value = true
    isShuffled.value.catalog = true
    fetchCatalog(1)
  }

  const disableCatalogShuffle = () => {
    catalogShuffle.value = false
    isShuffled.value.catalog = false
    fetchCatalog(1)
  }

  return {
    currentSection, currentData, currentLoading, currentError,
    catalogAnime, ongoings, announcements, recommendations, randomAnimeList,
    catalogLoading, ongoingsLoading, announcementsLoading, recommendationsLoading, randomLoading,
    catalogError, ongoingsError, announcementsError, recommendationsError, randomError,
    catalogPage, catalogTotalPages, catalogTotalCount,
    isShuffled, currentSectionIsShuffled, catalogShuffle,
    shuffleCurrentSection, unshuffleCurrentSection,
    enableCatalogShuffle, disableCatalogShuffle,
    switchSection, refreshCurrentSection,
    fetchCatalog, fetchOngoings, fetchAnnouncements, fetchRecommendations, fetchRandomAnimeList,
    loadAllSections
  }
}
