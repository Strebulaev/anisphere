import { ref, watch } from 'vue'

const isCollapsed = ref(false)
const isMobileMenuOpen = ref(false)

// Загружаем состояние из localStorage
const loadState = () => {
  const saved = localStorage.getItem('sidebarCollapsed')
  if (saved !== null) {
    isCollapsed.value = saved === 'true'
  }
}

// Сохраняем состояние в localStorage
const saveState = () => {
  localStorage.setItem('sidebarCollapsed', String(isCollapsed.value))
}

// Инициализация
loadState()

// Следим за изменениями и сохраняем
watch(isCollapsed, saveState)

export function useSidebar() {
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const collapseSidebar = () => {
    isCollapsed.value = true
  }

  const expandSidebar = () => {
    isCollapsed.value = false
  }

  const toggleMobileMenu = () => {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  }

  const closeMobileMenu = () => {
    isMobileMenuOpen.value = false
  }

  return {
    isCollapsed,
    isMobileMenuOpen,
    toggleSidebar,
    collapseSidebar,
    expandSidebar,
    toggleMobileMenu,
    closeMobileMenu
  }
}
