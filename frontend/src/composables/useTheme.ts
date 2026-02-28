import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import * as settingsApi from '@/api/settings'

// Определение цветов для тем
const THEME_COLORS = {
  dark: {
    '--primary-color': '#0084FF',
    '--secondary-color': '#00C853',
    '--background-color': '#0f0f0f',
    '--card-bg': '#1a1a1a',
    '--hover-bg': '#2d2d2d',
    '--text-color': '#ffffff',
    '--secondary-text': '#b0b0b0',
    '--border-color': '#404040',
  },
  light: {
    '--primary-color': '#0084FF',
    '--secondary-color': '#00C853',
    '--background-color': '#ffffff',
    '--card-bg': '#f5f5f5',
    '--hover-bg': '#e8e8e8',
    '--text-color': '#000000',
    '--secondary-text': '#666666',
    '--border-color': '#d0d0d0',
  },
  blue: {
    '--primary-color': '#2196F3',
    '--secondary-color': '#1976D2',
    '--background-color': '#0a1929',
    '--card-bg': '#132f4c',
    '--hover-bg': '#1a3a5c',
    '--text-color': '#ffffff',
    '--secondary-text': '#b0bec5',
    '--border-color': '#263238',
  },
  green: {
    '--primary-color': '#4CAF50',
    '--secondary-color': '#388E3C',
    '--background-color': '#0d2b12',
    '--card-bg': '#1b3a1f',
    '--hover-bg': '#2d5a31',
    '--text-color': '#ffffff',
    '--secondary-text': '#a5d6a7',
    '--border-color': '#1b3a1f',
  },
}

export function useTheme() {
  const authStore = useAuthStore()
  const currentTheme = ref('dark')
  const accentColor = ref('#0084FF')
  const customTheme = ref<Record<string, string>>({})

  // Вычисляемое свойство для определения светлой темы
  const isLightTheme = computed(() => currentTheme.value === 'light')

  // Применить тему к документу
  const applyTheme = (theme: string, accent?: string) => {
    const colors = THEME_COLORS[theme as keyof typeof THEME_COLORS] || THEME_COLORS.dark

    // Применяем базовые цвета темы
    Object.entries(colors).forEach(([key, value]) => {
      document.documentElement.style.setProperty(key, value)
    })

    // Применяем акцентный цвет
    const finalAccent = accent || accentColor.value
    document.documentElement.style.setProperty('--primary-color', finalAccent)

    // Устанавливаем data-атрибут для CSS
    document.documentElement.setAttribute('data-theme', theme)

    // Сохраняем в localStorage
    localStorage.setItem('theme', theme)
    localStorage.setItem('accent-color', finalAccent)
  }

  // Переключить тему
  const toggleTheme = () => {
    const newTheme = isLightTheme.value ? 'dark' : 'light'
    setTheme(newTheme)
  }

  // Установить конкретную тему
  const setTheme = async (theme: 'light' | 'dark' | 'system' | 'blue' | 'green') => {
    currentTheme.value = theme
    applyTheme(theme)

    try {
      await settingsApi.updateProfileSettings({
        theme,
      })
    } catch (error) {
      console.error('Error saving theme:', error)
    }
  }

  // Установить акцентный цвет
  const setAccentColor = async (color: string) => {
    accentColor.value = color
    applyTheme(currentTheme.value, color)

    try {
      await settingsApi.updateProfileSettings({
        accent_color: color,
      })
    } catch (error) {
      console.error('Error saving accent color:', error)
    }
  }

  // Загрузить настройки темы из API
  const fetchThemeSettings = async () => {
    try {
      const data = await settingsApi.getProfileSettings()
      currentTheme.value = data.theme || 'dark'
      accentColor.value = data.accent_color || '#0084FF'

      applyTheme(currentTheme.value, accentColor.value)
    } catch (error) {
      console.error('Error fetching theme settings:', error)
    }
  }

  const applyFontSettings = (settings: {
    font_family?: string
    font_size?: number
    interface_scale?: number
    line_height?: number
    density?: string
    bold_headings?: boolean
    increase_line_height?: boolean
    monospace_code?: boolean
    reduce_motion?: boolean
    high_contrast_mode?: boolean
  }) => {
    const htmlElement = document.documentElement as HTMLElement

    if (settings.font_family) {
      htmlElement.style.setProperty('--font-family', getFontFamily(settings.font_family))
    }

    if (settings.font_size) {
      htmlElement.style.setProperty('--font-size', `${settings.font_size}px`)
      htmlElement.style.fontSize = `${settings.font_size}px`
    }

    if (settings.interface_scale) {
      const scale = settings.interface_scale / 100
      htmlElement.style.setProperty('--interface-scale', scale.toString())
    }

    if (settings.line_height) {
      htmlElement.style.setProperty('--line-height', settings.line_height.toString())
    }

    if (settings.density) {
      htmlElement.setAttribute('data-density', settings.density)
    }

    if (settings.bold_headings !== undefined) {
      htmlElement.style.setProperty('--heading-font-weight', settings.bold_headings ? '600' : '400')
    }

    if (settings.reduce_motion !== undefined) {
      if (settings.reduce_motion) {
        htmlElement.style.setProperty('--transition-duration', '0s')
      } else {
        htmlElement.style.removeProperty('--transition-duration')
      }
    }

    if (settings.high_contrast_mode !== undefined) {
      htmlElement.setAttribute('data-high-contrast', settings.high_contrast_mode.toString())
    }
  }

  // Получить семейство шрифтов
  const getFontFamily = (font: string): string => {
    switch (font) {
      case 'Inter': return "'Inter', sans-serif"
      case 'Roboto': return "'Roboto', sans-serif"
      case 'Open Sans': return "'Open Sans', sans-serif"
      case 'Montserrat': return "'Montserrat', sans-serif"
      case 'anime': return "'Noto Sans JP', sans-serif"
      default: return 'system-ui, -apple-system, sans-serif'
    }
  }

  // Загрузить настройки шрифтов
  const fetchFontSettings = async () => {
    try {
      const data = await fetch('/api/users/font-settings/').then(r => r.json())
      applyFontSettings(data)
    } catch (error) {
      console.error('Error fetching font settings:', error)
    }
  }

  const applyChatBackground = (settings: {
    background_type?: string
    solid_color?: string
    gradient_colors?: Record<string, string>
    custom_image?: string
    effects?: Record<string, any>
  }) => {
    const chatContainer = document.querySelector('.chat-container') as HTMLElement
    if (!chatContainer) return

    chatContainer.style.background = ''
    chatContainer.style.backgroundImage = ''
    chatContainer.style.filter = ''

    if (settings.background_type === 'solid' && settings.solid_color) {
      chatContainer.style.background = settings.solid_color
    } else if (settings.background_type === 'gradient' && settings.gradient_colors) {
      const { start, end } = settings.gradient_colors
      chatContainer.style.background = `linear-gradient(135deg, ${start} 0%, ${end} 100%)`
    } else if (settings.background_type === 'image' && settings.custom_image) {
      chatContainer.style.backgroundImage = `url(${settings.custom_image})`
      chatContainer.style.backgroundSize = 'cover'
      chatContainer.style.backgroundPosition = 'center'
    }

    if (settings.effects) {
      const filters = []
      if (settings.effects.blur) filters.push('blur(2px)')
      if (settings.effects.darken) filters.push('brightness(0.7)')
      if (filters.length > 0) {
        chatContainer.style.filter = filters.join(' ')
      }
    }
  }

  const fetchChatBackgroundSettings = async () => {
    try {
      const data = await settingsApi.getPrivacySettings()
      applyChatBackground({
        background_type: (data as any).background_type,
        solid_color: (data as any).solid_color,
        gradient_colors: (data as any).gradient_colors,
        custom_image: (data as any).custom_image,
        effects: (data as any).background_effects,
      })
    } catch (error) {
      console.error('Error fetching chat background settings:', error)
    }
  }

  // Инициализация при монтировании
  onMounted(() => {
    // Сначала пробуем загрузить из localStorage для быстрого отображения
    const savedTheme = localStorage.getItem('theme') || 'dark'
    const savedAccent = localStorage.getItem('accent-color') || '#0084FF'

    currentTheme.value = savedTheme
    accentColor.value = savedAccent

    applyTheme(savedTheme, savedAccent)

    // Затем загружаем актуальные настройки с сервера
    fetchThemeSettings()
    fetchFontSettings()
    fetchChatBackgroundSettings()
  })

  return {
    currentTheme,
    accentColor,
    isLightTheme,
    toggleTheme,
    setTheme,
    setAccentColor,
    applyTheme,
    applyFontSettings,
    applyChatBackground,
    fetchThemeSettings,
    fetchFontSettings,
    fetchChatBackgroundSettings,
  }
}
