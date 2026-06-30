/**
 * Маппинг статусов аниме
 * 
 * На фронтенде используется "Завершён" (finished),
 * но на бэкенде есть два статуса для завершённых аниме:
 * - finished (завершён)
 * - released (вышел/завершён)
 * 
 * Этот файл преобразует frontend статусы в backend для корректного поиска.
 */

/**
 * Преобразует frontend статусы в backend статусы
 * @param frontendStatuses - Статусы из frontend фильтра
 * @returns Массив статусов для backend запроса
 */
export function mapFrontendStatusesToBackend(frontendStatuses: string[]): string[] {
  const backendStatuses: string[] = []
  
  for (const status of frontendStatuses) {
    if (status === 'finished') {
      
      backendStatuses.push('finished', 'released')
    } else if (status === 'released') {
      
      backendStatuses.push('released')
    } else {
      
      backendStatuses.push(status)
    }
  }
  
  
  return [...new Set(backendStatuses)]
}

/**
 * Преобразует backend статусы в frontend для отображения
 * @param backendStatuses - Статусы из backend
 * @returns Массив статусов для frontend отображения
 */
export function mapBackendStatusesToFrontend(backendStatuses: string[]): string[] {
  return backendStatuses.map(status => {
    
    if (status === 'released') {
      return 'finished'
    }
    return status
  })
}
