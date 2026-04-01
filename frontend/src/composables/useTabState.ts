import { ref, watch } from 'vue'

/**
 * Composable для сохранения состояния активной вкладки в localStorage
 * @param storageKey - уникальный ключ для хранения в localStorage
 * @param defaultTab - значение вкладки по умолчанию
 */
export function useTabState(storageKey: string, defaultTab: string) {
  // Ключ для localStorage
  const STORAGE_PREFIX = 'animecore_tab_'
  const key = STORAGE_PREFIX + storageKey

  // Получаем сохранённую вкладку или значение по умолчанию
  const getStoredTab = (): string => {
    try {
      const stored = localStorage.getItem(key)
      return stored || defaultTab
    } catch {
      return defaultTab
    }
  }

  // Активная вкладка
  const activeTab = ref(getStoredTab())

  // Сохраняем вкладку при изменении
  watch(activeTab, (newTab) => {
    try {
      localStorage.setItem(key, newTab)
    } catch (e) {
      console.warn('Failed to save tab state to localStorage:', e)
    }
  })

  // Функция для сброса на значение по умолчанию
  const resetTab = () => {
    activeTab.value = defaultTab
    try {
      localStorage.removeItem(key)
    } catch {
      // ignore
    }
  }

  return {
    activeTab,
    setTab: (tab: string) => { activeTab.value = tab },
    resetTab
  }
}
