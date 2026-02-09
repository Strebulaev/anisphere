import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

interface UserSettings {
  theme: 'light' | 'dark' | 'auto'
  ui_style: 'modern' | 'classic' | 'minimal' | 'dark'
  text_size: 'small' | 'medium' | 'large'
  push_notifications: boolean
  email_notifications: boolean
  message_notifications: boolean
  contest_notifications: boolean
  show_in_search: boolean
  show_online_status: boolean
  show_stats: boolean
  personalized_recommendations: boolean
  selected_interests: string[]
}

const defaultSettings: UserSettings = {
  theme: 'light',
  ui_style: 'modern',
  text_size: 'medium',
  push_notifications: true,
  email_notifications: true,
  message_notifications: true,
  contest_notifications: false,
  show_in_search: true,
  show_online_status: true,
  show_stats: true,
  personalized_recommendations: true,
  selected_interests: ['action', 'romance']
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<UserSettings>({ ...defaultSettings })

  // Применение темы к документу
  const applyTheme = (theme: string) => {
    const body = document.body

    // Удаляем предыдущие классы тем
    body.classList.remove('theme-light', 'theme-dark', 'theme-auto')

    // Добавляем новый класс темы
    body.classList.add(`theme-${theme}`)

    // Для автоматической темы проверяем системные настройки
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      body.classList.add(prefersDark ? 'theme-dark' : 'theme-light')
    }

    // Сохраняем текущую тему в localStorage для persistence
    localStorage.setItem('currentTheme', theme)
  }

  // Применение размера текста
  const applyTextSize = (size: string) => {
    const body = document.body

    // Удаляем предыдущие классы размеров
    body.classList.remove('text-small', 'text-medium', 'text-large')

    // Добавляем новый класс размера
    body.classList.add(`text-${size}`)
  }

  // Применение стиля интерфейса
  const applyUIStyle = (style: string) => {
    const body = document.body

    // Удаляем предыдущие классы стилей
    body.classList.remove('ui-modern', 'ui-classic', 'ui-minimal', 'ui-dark')

    // Добавляем новый класс стиля
    body.classList.add(`ui-${style}`)

    // Сохраняем стиль в localStorage
    localStorage.setItem('currentUIStyle', style)
  }

  // Применение всех настроек
  const applySettings = () => {
    applyTheme(settings.value.theme)
    applyTextSize(settings.value.text_size)
    applyUIStyle(settings.value.ui_style)

    // Сохраняем все текущие настройки в localStorage
    localStorage.setItem('currentSettings', JSON.stringify({
      theme: settings.value.theme,
      textSize: settings.value.text_size,
      uiStyle: settings.value.ui_style
    }))
  }

  // Загрузка настроек из localStorage
  const loadSettings = () => {
    const saved = localStorage.getItem('userSettings')
    if (saved) {
      try {
        const parsedSettings = JSON.parse(saved)
        settings.value = { ...defaultSettings, ...parsedSettings }
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    }

    // Применяем текущие настройки к UI
    applySettings()

    // Также восстанавливаем сохраненные UI настройки
    const savedUISettings = localStorage.getItem('currentSettings')
    if (savedUISettings) {
      try {
        const uiSettings = JSON.parse(savedUISettings)
        if (uiSettings.theme) applyTheme(uiSettings.theme)
        if (uiSettings.textSize) applyTextSize(uiSettings.textSize)
        if (uiSettings.uiStyle) applyUIStyle(uiSettings.uiStyle)
      } catch (error) {
        console.error('Error loading UI settings:', error)
      }
    }
  }

  // Сохранение настроек в localStorage
  const saveSettings = () => {
    localStorage.setItem('userSettings', JSON.stringify(settings.value))
  }

  // Обновление конкретной настройки
  const updateSetting = <K extends keyof UserSettings>(key: K, value: UserSettings[K]) => {
    settings.value[key] = value
    saveSettings()

    // Применяем изменения сразу
    if (key === 'theme') applyTheme(value as string)
    else if (key === 'text_size') applyTextSize(value as string)
    else if (key === 'ui_style') applyUIStyle(value as string)
  }

  // Обновление всех настроек
  const updateSettings = (newSettings: Partial<UserSettings>) => {
    settings.value = { ...settings.value, ...newSettings }
    saveSettings()
    applySettings()
  }

  // Слушатель для автоматической темы
  const setupAutoThemeListener = () => {
    if (settings.value.theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = () => {
        if (settings.value.theme === 'auto') {
          applyTheme('auto')
        }
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }

  // Инициализация
  const init = () => {
    loadSettings()
    setupAutoThemeListener()
  }

  return {
    settings,
    applySettings,
    loadSettings,
    saveSettings,
    updateSetting,
    updateSettings,
    init
  }
})