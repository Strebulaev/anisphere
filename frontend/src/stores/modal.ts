import { ref } from 'vue'
import { defineStore } from 'pinia'

interface ModalConfig {
  component?: any
  props?: Record<string, any>
  events?: Record<string, Function>
}

export const useModalStore = defineStore('modal', () => {
  const isAuthModalOpen = ref(false)
  const activeModal = ref<string | null>(null)
  const modalConfig = ref<ModalConfig>({})

  const openAuthModal = () => {
    isAuthModalOpen.value = true
  }

  const closeAuthModal = () => {
    isAuthModalOpen.value = false
  }

  const openModal = (modalName: string, config: ModalConfig = {}) => {
    activeModal.value = modalName
    modalConfig.value = config
  }

  const closeModal = () => {
    activeModal.value = null
    modalConfig.value = {}
  }

  return {
    isAuthModalOpen,
    activeModal,
    modalConfig,
    openAuthModal,
    closeAuthModal,
    openModal,
    closeModal,
  }
})
