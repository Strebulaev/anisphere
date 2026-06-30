import { ref, watch } from 'vue'

/**
 * Composable для сохранения состояния активной вкладки в localStorage
 * @param storageKey - уникальный ключ для хранения в localStorage
 * @param defaultTab - значение вкладки по умолчанию
 */
export function useTabState(storageKey: string, defaultTab: string) {
  
  const STORAGE_PREFIX = 'anisphere_tab_'
  const key = STORAGE_PREFIX + storageKey

  
  const getStoredTab = (): string => {
    try {
      const stored = localStorage.getItem(key)
      return stored || defaultTab
    } catch {
      return defaultTab
    }
  }

  
  const activeTab = ref(getStoredTab())

  
  watch(activeTab, (newTab) => {
    try {
      localStorage.setItem(key, newTab)
    } catch (e) {
      console.warn('Failed to save tab state to localStorage:', e)
    }
  })

  
  const resetTab = () => {
    activeTab.value = defaultTab
    try {
      localStorage.removeItem(key)
    } catch {
      
    }
  }

  return {
    activeTab,
    setTab: (tab: string) => { activeTab.value = tab },
    resetTab
  }
}
