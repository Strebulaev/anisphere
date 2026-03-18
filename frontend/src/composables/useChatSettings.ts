/**
 * useChatSettings — composable для управления настройками чата
 * Загружает обои, тему и применяет CSS переменные к DOM
 */

import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '@/api/client'

export interface ChatWallpaper {
  id?: number
  wallpaper_type: 'solid' | 'gradient' | 'pattern' | 'image'
  wallpaper_color: string
  wallpaper_color2?: string
  wallpaper_intensity?: number
  wallpaper_blur?: number
  wallpaper_motion?: string
  gradient_angle?: number
  pattern_type?: string
  pattern_color?: string
  pattern_opacity?: number
  wallpaper_image_url?: string
  css?: string
}

export interface ChatTheme {
  id?: number
  theme: string
  message_color_mine: string
  message_color_other: string
  message_text_color_mine: string
  message_text_color_other: string
  bubble_style: string
  bubble_border_radius: number
  bubble_shadow: boolean
  font_family: string
  font_size: string
  font_size_px: number
  font_weight: number
  line_height: number
  time_format: string
  time_color: string
  background_color: string
  header_color: string
  input_color: string
  input_text_color: string
  accent_color: string
  link_color: string
  message_animation: string
  reaction_animation: string
  typing_animation: string
  emoji_set: string
  emoji_size: string
  show_avatars: boolean
  show_usernames: boolean
  compact_mode: boolean
  show_read_status: boolean
  show_typing_indicator: boolean
  message_grouping: boolean
  custom_css: string
  css_vars?: Record<string, string>
}

export interface ChatAllSettings {
  wallpaper: ChatWallpaper | null
  theme: ChatTheme
  css_vars: Record<string, string>
}

const DEFAULT_THEME: ChatTheme = {
  theme: 'default',
  message_color_mine: '#3b82f6',
  message_color_other: '#1e1e32',
  message_text_color_mine: '#ffffff',
  message_text_color_other: '#e2e8f0',
  bubble_style: 'modern',
  bubble_border_radius: 18,
  bubble_shadow: false,
  font_family: 'system',
  font_size: 'medium',
  font_size_px: 14,
  font_weight: 400,
  line_height: 1.5,
  time_format: '24h',
  time_color: 'rgba(255,255,255,0.5)',
  background_color: '#0f0f1a',
  header_color: '#1a1a2e',
  input_color: '#1e1e32',
  input_text_color: '#e2e8f0',
  accent_color: '#3b82f6',
  link_color: '#60a5fa',
  message_animation: 'slide',
  reaction_animation: 'bounce',
  typing_animation: 'dots',
  emoji_set: 'default',
  emoji_size: 'medium',
  show_avatars: true,
  show_usernames: true,
  compact_mode: false,
  show_read_status: true,
  show_typing_indicator: true,
  message_grouping: true,
  custom_css: '',
}

// ── Кэш настроек (в памяти) ──
const settingsCache = new Map<string, ChatAllSettings>()

export function useChatSettings(chatType: 'group' | 'private', chatId: number) {
  const loading = ref(false)
  const wallpaper = ref<ChatWallpaper | null>(null)
  const theme = ref<ChatTheme>({ ...DEFAULT_THEME })
  const cssVars = ref<Record<string, string>>({})

  const cacheKey = `${chatType}:${chatId}`

  // ── Computed стили ──
  const bubbleRadiusPx = computed(() => {
    const map: Record<string, number> = { modern: 18, classic: 4, rounded: 24, flat: 8, minimal: 2 }
    return map[theme.value.bubble_style] ?? theme.value.bubble_border_radius
  })

  const fontFamilyCSS = computed(() => {
    const map: Record<string, string> = {
      system: 'system-ui,-apple-system,sans-serif',
      inter: 'Inter,sans-serif',
      roboto: 'Roboto,sans-serif',
      nunito: 'Nunito,sans-serif',
      montserrat: 'Montserrat,sans-serif',
      opensans: '"Open Sans",sans-serif',
    }
    return map[theme.value.font_family] || 'system-ui'
  })

  const chatContainerStyle = computed(() => ({
    background: wallpaper.value ? getWallpaperCSS(wallpaper.value) : theme.value.background_color,
    fontFamily: fontFamilyCSS.value,
    fontSize: theme.value.font_size_px + 'px',
    '--msg-mine-bg': theme.value.message_color_mine,
    '--msg-other-bg': theme.value.message_color_other,
    '--msg-mine-text': theme.value.message_text_color_mine,
    '--msg-other-text': theme.value.message_text_color_other,
    '--chat-bg': theme.value.background_color,
    '--chat-header-bg': theme.value.header_color,
    '--chat-input-bg': theme.value.input_color,
    '--chat-accent': theme.value.accent_color,
    '--msg-font-size': theme.value.font_size_px + 'px',
    '--msg-border-radius': bubbleRadiusPx.value + 'px',
    '--msg-font-weight': String(theme.value.font_weight),
    '--msg-line-height': String(theme.value.line_height),
    '--msg-time-color': theme.value.time_color,
    '--chat-link': theme.value.link_color,
  } as Record<string, string>))

  const mineBubbleStyle = computed(() => ({
    background: theme.value.message_color_mine,
    color: theme.value.message_text_color_mine,
    borderRadius: bubbleRadiusPx.value + 'px',
    fontFamily: fontFamilyCSS.value,
    fontSize: theme.value.font_size_px + 'px',
    fontWeight: String(theme.value.font_weight),
    lineHeight: String(theme.value.line_height),
    boxShadow: theme.value.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
  }))

  const otherBubbleStyle = computed(() => ({
    background: theme.value.message_color_other,
    color: theme.value.message_text_color_other,
    borderRadius: bubbleRadiusPx.value + 'px',
    fontFamily: fontFamilyCSS.value,
    fontSize: theme.value.font_size_px + 'px',
    fontWeight: String(theme.value.font_weight),
    lineHeight: String(theme.value.line_height),
    boxShadow: theme.value.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
  }))

  const headerStyle = computed(() => ({
    background: theme.value.header_color,
  }))

  const inputStyle = computed(() => ({
    background: theme.value.input_color,
    color: theme.value.input_text_color,
  }))

  // ── Загрузка ──
  async function loadSettings() {
    // Проверяем кэш
    const cached = settingsCache.get(cacheKey)
    if (cached) {
      applySettings(cached)
      return
    }

    loading.value = true
    try {
      const { data } = await apiClient.get<ChatAllSettings>(
        `/social/chat-settings/${chatType}/${chatId}/all/`
      )
      settingsCache.set(cacheKey, data)
      applySettings(data)
    } catch (err) {
      console.warn('useChatSettings: не удалось загрузить настройки, используем дефолтные')
    } finally {
      loading.value = false
    }
  }

  function applySettings(data: ChatAllSettings) {
    if (data.wallpaper) {
      wallpaper.value = data.wallpaper
    }
    if (data.theme) {
      theme.value = { ...DEFAULT_THEME, ...data.theme }
    }
    if (data.css_vars) {
      cssVars.value = data.css_vars
    }
    applyToDom()
  }

  function applyToDom() {
    // Применяем CSS переменные, специфичные для чата
    const root = document.documentElement
    const prefix = `--chat-${chatType}-${chatId}`
    const t = theme.value

    root.style.setProperty(`${prefix}-msg-mine`, t.message_color_mine)
    root.style.setProperty(`${prefix}-msg-other`, t.message_color_other)
    root.style.setProperty(`${prefix}-msg-mine-text`, t.message_text_color_mine)
    root.style.setProperty(`${prefix}-msg-other-text`, t.message_text_color_other)
    root.style.setProperty(`${prefix}-bg`, t.background_color)
    root.style.setProperty(`${prefix}-header`, t.header_color)
    root.style.setProperty(`${prefix}-input`, t.input_color)
    root.style.setProperty(`${prefix}-accent`, t.accent_color)
    root.style.setProperty(`${prefix}-font-size`, t.font_size_px + 'px')
    root.style.setProperty(`${prefix}-radius`, bubbleRadiusPx.value + 'px')
    root.style.setProperty(`${prefix}-font-family`, fontFamilyCSS.value)

    // Применяем кастомный CSS
    if (t.custom_css) {
      injectCustomCSS(t.custom_css, chatType, chatId)
    }
  }

  function injectCustomCSS(css: string, type: string, id: number) {
    const styleId = `chat-custom-css-${type}-${id}`
    let el = document.getElementById(styleId) as HTMLStyleElement | null
    if (!el) {
      el = document.createElement('style')
      el.id = styleId
      document.head.appendChild(el)
    }
    // Скопируем CSS внутри scope
    el.textContent = `.chat-window[data-chat="${type}-${id}"] { ${css} }`
  }

  // ── Вычисление wallpaper CSS ──
  function getWallpaperCSS(wp: ChatWallpaper): string {
    if (wp.css) return wp.css
    switch (wp.wallpaper_type) {
      case 'solid': return wp.wallpaper_color
      case 'gradient': {
        const c2 = wp.wallpaper_color2 || wp.wallpaper_color
        const angle = wp.gradient_angle ?? 135
        return `linear-gradient(${angle}deg, ${wp.wallpaper_color}, ${c2})`
      }
      case 'image':
        return wp.wallpaper_image_url
          ? `url(${wp.wallpaper_image_url}) center/cover no-repeat`
          : wp.wallpaper_color
      default:
        return wp.wallpaper_color
    }
  }

  // ── Получить объект стиля для контейнера чата ──
  function getChatContainerStyle(): Record<string, string> {
    const style: Record<string, string> = {}

    // Фон
    if (wallpaper.value) {
      const bgCSS = getWallpaperCSS(wallpaper.value)
      if (wallpaper.value.wallpaper_type === 'image') {
        style['background-image'] = `url(${wallpaper.value.wallpaper_image_url})`
        style['background-size'] = 'cover'
        style['background-position'] = 'center'
        if (wallpaper.value.wallpaper_blur) {
          style['filter'] = `blur(${wallpaper.value.wallpaper_blur}px)`
        }
      } else {
        style['background'] = bgCSS
      }
    } else {
      style['background'] = theme.value.background_color
    }

    // Шрифт
    style['font-family'] = fontFamilyCSS.value
    style['font-size'] = theme.value.font_size_px + 'px'

    return style
  }

  // ── Обновление кэша при изменении настроек ──
  function invalidateCache() {
    settingsCache.delete(cacheKey)
  }

  function updateCache(newSettings: Partial<ChatAllSettings>) {
    const existing = settingsCache.get(cacheKey)
    if (existing) {
      settingsCache.set(cacheKey, { ...existing, ...newSettings })
    }
  }

  // ── Применить новую тему без перезагрузки ──
  function applyTheme(newTheme: Partial<ChatTheme>) {
    theme.value = { ...theme.value, ...newTheme }
    updateCache({ theme: theme.value })
    applyToDom()
  }

  // ── Применить новые обои без перезагрузки ──
  function applyWallpaper(newWallpaper: ChatWallpaper | null) {
    wallpaper.value = newWallpaper
    updateCache({ wallpaper: newWallpaper })
  }

  // ── Получить CSS-строку для data-атрибута ──
  function getCSSDataAttr(): string {
    return `${chatType}-${chatId}`
  }

  onMounted(() => {
    loadSettings()
  })

  return {
    loading,
    wallpaper,
    theme,
    cssVars,
    chatContainerStyle,
    mineBubbleStyle,
    otherBubbleStyle,
    headerStyle,
    inputStyle,
    bubbleRadiusPx,
    fontFamilyCSS,
    loadSettings,
    applySettings,
    applyTheme,
    applyWallpaper,
    invalidateCache,
    getChatContainerStyle,
    getCSSDataAttr,
    getWallpaperCSS,
  }
}
