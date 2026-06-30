/**
 * Глобальный toast — импортируй useToast() в любом компоненте.
 * Не требует добавления <div> в шаблон — рендерится через teleport в <body>.
 */
import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration: number
  title?: string
  action?: { label: string; handler: () => void }
  onClick?: () => void
}

interface ToastOptions {
  duration?: number
  title?: string
  action?: { label: string; handler: () => void }
  onClick?: () => void
}

type ToastType = 'success' | 'error' | 'info' | 'warning'

const toasts = ref<ToastItem[]>([])
let idCounter = 0

export function useToast() {
  const addToast = (
    message: string, 
    type: ToastType = 'success',
    options?: ToastOptions
  ): number => {
    const id = ++idCounter
    const duration = options?.duration ?? 3000
    
    const toast: ToastItem = { 
      id, 
      message, 
      type, 
      duration,
      title: options?.title,
      action: options?.action,
      onClick: options?.onClick
    }
    
    toasts.value.push(toast)

    setTimeout(() => {
      removeToast(id)
    }, duration)

    return id
  }

  const removeToast = (id: number) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  
  const show = (
    message: string, 
    typeOrOptions?: ToastType | ToastOptions | number,
    ms?: number
  ): number => {
    if (typeof typeOrOptions === 'string') {
      return addToast(message, typeOrOptions, ms ? { duration: ms } : undefined)
    } else if (typeof typeOrOptions === 'number') {
      return addToast(message, 'success', { duration: typeOrOptions })
    } else if (typeof typeOrOptions === 'object') {
      return addToast(message, 'success', typeOrOptions)
    }
    return addToast(message)
  }

  const success = (message: string, optionsOrMs?: ToastOptions | number): number => {
    if (typeof optionsOrMs === 'number') {
      return addToast(message, 'success', { duration: optionsOrMs })
    }
    return addToast(message, 'success', optionsOrMs)
  }

  const error = (message: string, optionsOrMs?: ToastOptions | number): number => {
    if (typeof optionsOrMs === 'number') {
      return addToast(message, 'error', { duration: optionsOrMs })
    }
    return addToast(message, 'error', optionsOrMs)
  }

  const info = (message: string, optionsOrMs?: ToastOptions | number): number => {
    if (typeof optionsOrMs === 'number') {
      return addToast(message, 'info', { duration: optionsOrMs })
    }
    return addToast(message, 'info', optionsOrMs)
  }

  const warning = (message: string, optionsOrMs?: ToastOptions | number): number => {
    if (typeof optionsOrMs === 'number') {
      return addToast(message, 'warning', { duration: optionsOrMs })
    }
    return addToast(message, 'warning', optionsOrMs)
  }

  return { 
    toasts, 
    removeToast, 
    show, 
    success, 
    error, 
    info, 
    warning 
  }
}
