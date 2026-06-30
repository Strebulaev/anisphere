import { ref, computed, onMounted } from 'vue'
import animeApi from '@/api/anime'
import type { Anime } from '@/types'


export type RecommendationType = 
  | 'watched'      
  | 'liked'        
  | 'favorites'    
  | 'similar_users' 
  | 'new_genres'   
  | 'seasonal'     
  | 'classic'      
  | 'last_watched' 


export interface RecommendationSettings {
  includeAge: boolean           
  preferLength: 'short' | 'medium' | 'long' | 'any' 
  preferYear: 'new' | 'classic' | 'mixed' 
  riskLevel: 'conservative' | 'balanced' | 'experimental' 
  excludeWatched: boolean       
  voicePriority: 'yes' | 'no' | 'any' 
}


export interface DisplaySettings {
  viewMode: 'horizontal' | 'grid' | 'new' | 'classic'
  limit: number
  showTypes: RecommendationType[]
}

interface UserAnimeData {
  watched: Anime[]
  liked: Anime[]      
  favorites: Anime[]
  planned: Anime[]
  ratings: Map<number, number>
  lastWatched: Anime | null
}

export function useRecommendations() {
  
  const recommendations = ref<Record<RecommendationType, Anime[]>>({
    watched: [],
    liked: [],
    favorites: [],
    similar_users: [],
    new_genres: [],
    seasonal: [],
    classic: [],
    last_watched: []
  })
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  
  const userAnimeData = ref<UserAnimeData>({
    watched: [],
    liked: [],
    favorites: [],
    planned: [],
    ratings: new Map(),
    lastWatched: null
  })
  
  
  const settings = ref<RecommendationSettings>({
    includeAge: true,
    preferLength: 'any',
    preferYear: 'mixed',
    riskLevel: 'balanced',
    excludeWatched: true,
    voicePriority: 'any'
  })
  
  
  const displaySettings = ref<DisplaySettings>({
    viewMode: 'horizontal',
    limit: 12,
    showTypes: ['watched', 'liked', 'favorites', 'seasonal', 'classic']
  })
  
  
  const currentYear = new Date().getFullYear()
  const currentSeason = computed(() => {
    const month = new Date().getMonth()
    if (month >= 2 && month <= 4) return 'spring'
    if (month >= 5 && month <= 7) return 'summer'
    if (month >= 8 && month <= 10) return 'fall'
    return 'winter'
  })
  
  
  const fetchUserAnimeData = async () => {
    try {
      
      const watchedResponse = await animeApi.list({
        page_size: 100,
        ordering: '-created_at' as any
      })
      userAnimeData.value.watched = (watchedResponse.results || []) as Anime[]
      
      
      if (userAnimeData.value.watched.length > 0) {
        userAnimeData.value.lastWatched = userAnimeData.value.watched[0] || null
      }
      
      
      const favoritesResponse = await animeApi.list({
        page_size: 50
      })
      userAnimeData.value.favorites = (favoritesResponse.results || []) as Anime[]
      
      
      const allRatings = (favoritesResponse.results || []) as Anime[]
      userAnimeData.value.liked = allRatings.filter(a => (a as any).score >= 8)
      
      
      const plannedResponse = await animeApi.list({
        page_size: 50
      })
      userAnimeData.value.planned = (plannedResponse.results || []) as Anime[]
      
    } catch (err) {
      console.error('Ошибка загрузки данных пользователя:', err)
    }
  }
  
  
  const calculateGenreWeights = (animeList: Anime[]): Map<string, number> => {
    const weights = new Map<string, number>()
    const total = animeList.length
    
    if (total === 0) return weights
    
    animeList.forEach(anime => {
      if (anime.genres) {
        anime.genres.forEach((genre: any) => {
          const genreStr = String(genre)
          weights.set(genreStr, (weights.get(genreStr) || 0) + 1)
        })
      }
    })
    
    
    weights.forEach((value, key) => {
      weights.set(key, value / total)
    })
    
    return weights
  }
  
  
  const fetchWatchedBased = async (): Promise<Anime[]> => {
    const watched = userAnimeData.value.watched
    if (watched.length === 0) return []
    
    const genreWeights = calculateGenreWeights(watched)
    const topGenres = Array.from(genreWeights.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([genre]) => genre)
    
    try {
      const response = await animeApi.list({
        genres: topGenres as any,
        genre_logic: 'OR',
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      
      results = applySettings(results)
      
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchLikedBased = async (): Promise<Anime[]> => {
    const liked = userAnimeData.value.liked
    if (liked.length < 3) return []
    
    const genreWeights = calculateGenreWeights(liked)
    const topGenres = Array.from(genreWeights.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([genre]) => genre)
    
    try {
      const response = await animeApi.list({
        genres: topGenres as any,
        genre_logic: 'OR',
        page_size: displaySettings.value.limit * 2,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      
      if (settings.value.excludeWatched) {
        const excludeIds = new Set([
          ...userAnimeData.value.watched.map(a => a.id),
          ...userAnimeData.value.liked.map(a => a.id)
        ])
        results = results.filter(a => !excludeIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchFavoritesBased = async (): Promise<Anime[]> => {
    const favorites = userAnimeData.value.favorites
    if (favorites.length === 0) return []
    
    const genreWeights = calculateGenreWeights(favorites)
    const topGenres = Array.from(genreWeights.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([genre]) => genre)
    
    try {
      const response = await animeApi.list({
        genres: topGenres as any,
        genre_logic: 'OR',
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      if (settings.value.excludeWatched) {
        const excludeIds = new Set([
          ...userAnimeData.value.watched.map(a => a.id),
          ...userAnimeData.value.favorites.map(a => a.id)
        ])
        results = results.filter(a => !excludeIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchSimilarUsers = async (): Promise<Anime[]> => {
    
    try {
      const response = await animeApi.list({
        year_from: currentYear - 1,
        page_size: displaySettings.value.limit,
        ordering: '-favorites,-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(userAnimeData.value.watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchNewGenres = async (): Promise<Anime[]> => {
    const watchedGenres = new Set<string>()
    userAnimeData.value.watched.forEach(anime => {
      anime.genres?.forEach((g: any) => watchedGenres.add(String(g)))
    })
    
    
    const allGenres = ['Экшен', 'Приключения', 'Комедия', 'Драма', 'Фэнтези', 'Магия', 
      'Сёнен', 'Сёдзё', 'Повседневность', 'Научная фантастика', 'Меха',
      'Ужасы', 'Мистика', 'Психология', 'Романтика', 'Музыка', 'Спорт',
      'Триллер', 'Школа', 'Сверхъестественное', 'Детектив', 'Военное',
      'Космос', 'Исторический', 'Детское']
    
    
    const newGenres = allGenres.filter(g => !watchedGenres.has(g))
    
    if (newGenres.length === 0) return []
    
    
    const shuffled = newGenres.sort(() => Math.random() - 0.5)
    const selectedGenres = shuffled.slice(0, Math.min(3, newGenres.length))
    
    try {
      const response = await animeApi.list({
        genres: selectedGenres as any,
        genre_logic: 'OR',
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(userAnimeData.value.watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchSeasonal = async (): Promise<Anime[]> => {
    try {
      const response = await animeApi.list({
        status: 'ongoing',
        season: currentSeason.value,
        season_year: currentYear,
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(userAnimeData.value.watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchClassic = async (): Promise<Anime[]> => {
    const favoriteGenres = calculateGenreWeights(userAnimeData.value.liked.length > 0 
      ? userAnimeData.value.liked 
      : userAnimeData.value.watched)
    
    const topGenre = Array.from(favoriteGenres.entries())
      .sort((a, b) => b[1] - a[1])[0]?.[0]
    
    if (!topGenre) return []
    
    try {
      const response = await animeApi.list({
        genres: topGenre as any,
        year_to: 2010,
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(userAnimeData.value.watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const fetchLastWatchedSimilar = async (): Promise<Anime[]> => {
    const lastWatched = userAnimeData.value.lastWatched
    if (!lastWatched || !lastWatched.genres || lastWatched.genres.length === 0) return []
    
    try {
      const response = await animeApi.list({
        genres: lastWatched.genres.slice(0, 2) as any,
        genre_logic: 'AND',
        page_size: displaySettings.value.limit,
        ordering: '-score' as any
      })
      
      let results = (response.results || []) as Anime[]
      
      
      results = results.filter(a => a.id !== lastWatched.id)
      
      if (settings.value.excludeWatched) {
        const watchedIds = new Set(userAnimeData.value.watched.map(a => a.id))
        results = results.filter(a => !watchedIds.has(a.id))
      }
      
      results = applySettings(results)
      return results.slice(0, displaySettings.value.limit)
    } catch {
      return []
    }
  }
  
  
  const applySettings = (animeList: Anime[]): Anime[] => {
    let results = [...animeList]
    
    
    switch (settings.value.preferYear) {
      case 'new':
        results = results.filter(a => a.year && a.year >= currentYear - 2)
        break
      case 'classic':
        results = results.filter(a => a.year && a.year <= 2010)
        break
      
    }
    
    
    switch (settings.value.preferLength) {
      case 'short':
        results = results.filter(a => a.episodes && a.episodes <= 24)
        break
      case 'medium':
        results = results.filter(a => a.episodes && a.episodes > 24 && a.episodes <= 50)
        break
      case 'long':
        results = results.filter(a => a.episodes && a.episodes > 50)
        break
    }
    
    return results
  }
  
  
  const fetchRecommendations = async () => {
    loading.value = true
    error.value = null
    
    try {
      
      await fetchUserAnimeData()
      
      
      const [
        watched,
        liked,
        favorites,
        similarUsers,
        newGenres,
        seasonal,
        classic,
        lastWatched
      ] = await Promise.all([
        fetchWatchedBased(),
        fetchLikedBased(),
        fetchFavoritesBased(),
        fetchSimilarUsers(),
        fetchNewGenres(),
        fetchSeasonal(),
        fetchClassic(),
        fetchLastWatchedSimilar()
      ])
      
      recommendations.value = {
        watched,
        liked,
        favorites,
        similar_users: similarUsers,
        new_genres: newGenres,
        seasonal,
        classic,
        last_watched: lastWatched
      }
      
    } catch (err: any) {
      console.error('Ошибка загрузки рекомендаций:', err)
      error.value = err.message || 'Не удалось загрузить рекомендации'
    } finally {
      loading.value = false
    }
  }
  
  
  const refreshRecommendationType = async (type: RecommendationType) => {
    let result: Anime[] = []
    
    switch (type) {
      case 'watched':
        result = await fetchWatchedBased()
        break
      case 'liked':
        result = await fetchLikedBased()
        break
      case 'favorites':
        result = await fetchFavoritesBased()
        break
      case 'similar_users':
        result = await fetchSimilarUsers()
        break
      case 'new_genres':
        result = await fetchNewGenres()
        break
      case 'seasonal':
        result = await fetchSeasonal()
        break
      case 'classic':
        result = await fetchClassic()
        break
      case 'last_watched':
        result = await fetchLastWatchedSimilar()
        break
    }
    
    recommendations.value[type] = result
  }
  
  
  const updateSettings = (newSettings: Partial<RecommendationSettings>) => {
    settings.value = { ...settings.value, ...newSettings }
    fetchRecommendations()
  }
  
  
  const updateDisplaySettings = (newDisplaySettings: Partial<DisplaySettings>) => {
    displaySettings.value = { ...displaySettings.value, ...newDisplaySettings }
  }
  
  
  const hasUserData = computed(() => {
    return userAnimeData.value.watched.length > 0 || 
           userAnimeData.value.liked.length > 0 || 
           userAnimeData.value.favorites.length > 0
  })
  
  const availableTypes = computed(() => {
    const types: RecommendationType[] = []
    const data = userAnimeData.value
    
    if (data.watched.length > 0) types.push('watched', 'last_watched')
    if (data.liked.length >= 3) types.push('liked')
    if (data.favorites.length > 0) types.push('favorites')
    if (data.watched.length > 5) types.push('similar_users', 'new_genres')
    
    types.push('seasonal', 'classic')
    
    return types
  })
  
  
  onMounted(() => {
    fetchRecommendations()
  })
  
  return {
    
    recommendations,
    loading,
    error,
    
    
    userAnimeData,
    
    
    settings,
    displaySettings,
    
    
    hasUserData,
    availableTypes,
    
    
    fetchRecommendations,
    refreshRecommendationType,
    updateSettings,
    updateDisplaySettings
  }
}
