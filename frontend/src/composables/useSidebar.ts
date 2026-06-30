import { ref, watch } from 'vue'

const isCollapsed = ref(false)
const isMobileMenuOpen = ref(false)


const loadState = () => {
  const saved = localStorage.getItem('sidebarCollapsed')
  if (saved !== null) {
    isCollapsed.value = saved === 'true'
  }
}


const saveState = () => {
  localStorage.setItem('sidebarCollapsed', String(isCollapsed.value))
}


loadState()


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
