/**
 * Гибкая нормализация поискового запроса
 * Совместима с backend normalize_search_string()
 * 
 * Примеры:
 * "Ван-пис" → "ван пис"
 * "Ван:пис" → "ван пис"
 * "Ван  пис" → "ван пис"
 * "ВанПис" → "ванпис"
 */
export function normalizeSearchQuery(query: string, mode: 'compact' | 'split' = 'split'): string {
  const lower = query.toLowerCase()
  
  if (mode === 'compact') {
    
    return lower
      .replace(/[-_:/\\|,.!?@#$%^&*(){}\[\]<>~`'"\s]+/g, '')
      .replace(/[^а-яa-z0-9]/g, '')
  } else {
    
    return lower
      .replace(/[-_:/\\|,.!?@#$%^&*(){}\[\]<>~`'"]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }
}

/**
 * Разбивает нормализованный запрос на слова (минимум 2 символа)
 */
export function getSearchWords(query: string): string[] {
  const normalized = normalizeSearchQuery(query, 'split')
  if (!normalized) return []
  
  return normalized
    .split(' ')
    .filter(word => word.length >= 2)
}

/**
 * Проверка соответствия поисковому запросу
 * Поддерживает поиск и слитно, и по словам
 * 
 * Примеры:
 * "ван-пис" находит: "Ван-пис", "Ванпис", "Ван пис"
 * "ван пис" находит: "Ван-пис", "Ванпис", "Ван пис"
 */
export function matchesSearchQuery(text: string, query: string): boolean {
  if (!query.trim()) return true
  if (!text) return false
  
  const queryCompact = normalizeSearchQuery(query, 'compact')
  const querySplit = normalizeSearchQuery(query, 'split')
  const searchWords = getSearchWords(query)
  
  const textCompact = normalizeSearchQuery(text, 'compact')
  const textSplit = normalizeSearchQuery(text, 'split')
  
  
  if (queryCompact.length >= 2 && textCompact.includes(queryCompact)) {
    return true
  }
  
  
  if (searchWords.length > 0) {
    const allWordsFound = searchWords.every(word => textSplit.includes(word))
    if (allWordsFound) {
      return true
    }
  }
  
  return false
}

/**
 * Фильтрация массива аниме по названию
 * Поддерживает поиск и слитно, и по словам
 */
export function filterAnimeByTitle<T extends { title_ru?: string; title_en?: string; title_jp?: string }>(
  animeList: T[],
  query: string
): T[] {
  if (!query.trim()) return animeList
  
  const queryCompact = normalizeSearchQuery(query, 'compact')
  const searchWords = getSearchWords(query)
  
  return animeList.filter(anime => {
    const titles = [
      anime.title_ru,
      anime.title_en,
      anime.title_jp
    ].filter(Boolean) as string[]
    
    
    return titles.some(title => {
      
      if (queryCompact.length >= 2) {
        const titleCompact = normalizeSearchQuery(title, 'compact')
        if (titleCompact.includes(queryCompact)) {
          return true
        }
      }
      
      
      if (searchWords.length > 0) {
        const titleSplit = normalizeSearchQuery(title, 'split')
        if (searchWords.every(word => titleSplit.includes(word))) {
          return true
        }
      }
      
      return false
    })
  })
}
