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

  
  const applyTheme = (theme: string) => {
    const body = document.body

    
    body.classList.remove('theme-light', 'theme-dark', 'theme-auto')

    
    body.classList.add(`theme-${theme}`)

    
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      body.classList.add(prefersDark ? 'theme-dark' : 'theme-light')
    }

    
    localStorage.setItem('currentTheme', theme)
  }

  
  const applyTextSize = (size: string) => {
    const body = document.body

    
    body.classList.remove('text-small', 'text-medium', 'text-large')

    
    body.classList.add(`text-${size}`)
  }

  
  const applyUIStyle = (style: string) => {
    const body = document.body

    
    body.classList.remove('ui-modern', 'ui-classic', 'ui-minimal', 'ui-dark')

    
    body.classList.add(`ui-${style}`)

    
    localStorage.setItem('currentUIStyle', style)
  }

  
  const applySettings = () => {
    applyTheme(settings.value.theme)
    applyTextSize(settings.value.text_size)
    applyUIStyle(settings.value.ui_style)

    
    localStorage.setItem('currentSettings', JSON.stringify({
      theme: settings.value.theme,
      textSize: settings.value.text_size,
      uiStyle: settings.value.ui_style
    }))
  }

  
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

    
    applySettings()

    
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

  
  const saveSettings = () => {
    localStorage.setItem('userSettings', JSON.stringify(settings.value))
  }

  
  const updateSetting = <K extends keyof UserSettings>(key: K, value: UserSettings[K]) => {
    settings.value[key] = value
    saveSettings()

    
    if (key === 'theme') applyTheme(value as string)
    else if (key === 'text_size') applyTextSize(value as string)
    else if (key === 'ui_style') applyUIStyle(value as string)
  }

  
  const updateSettings = (newSettings: Partial<UserSettings>) => {
    settings.value = { ...settings.value, ...newSettings }
    saveSettings()
    applySettings()
  }

  
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