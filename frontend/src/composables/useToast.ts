import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastAction {
  label: string
  handler: () => void
}

export interface Toast {
  id: number
  type: ToastType
  title?: string
  message: string
  duration: number
  action?: ToastAction
  onClick?: () => void
}

let toastId = 0
const toasts = ref<Toast[]>([])

export function useToast() {
  const addToast = (
    message: string,
    type: ToastType = 'info',
    options: {
      title?: string
      duration?: number
      action?: ToastAction
      onClick?: () => void
    } = {}
  ) => {
    const id = ++toastId
    const toast: Toast = {
      id,
      type,
      message,
      title: options.title,
      duration: options.duration ?? 4000,
      action: options.action,
      onClick: options.onClick
    }

    toasts.value.push(toast)

    if (toast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, toast.duration)
    }

    return id
  }

  const removeToast = (id: number) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  type ToastOptions = {
    title?: string
    duration?: number
    action?: ToastAction
    onClick?: () => void
  }

  const success = (message: string, options?: ToastOptions) => {
    return addToast(message, 'success', options)
  }

  const error = (message: string, options?: ToastOptions) => {
    return addToast(message, 'error', options)
  }

  const warning = (message: string, options?: ToastOptions) => {
    return addToast(message, 'warning', options)
  }

  const info = (message: string, options?: ToastOptions) => {
    return addToast(message, 'info', options)
  }

  const clear = () => {
    toasts.value = []
  }

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
    clear
  }
}
