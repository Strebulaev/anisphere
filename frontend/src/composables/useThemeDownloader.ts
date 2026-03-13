/**
 * useThemeDownloader
 *
 * Скачивает произвольный отрезок из текущей серии аниме в формате MP4.
 * Нарезка происходит на сервере через ffmpeg — никакого ffmpeg.wasm в браузере.
 *
 * GET /api/anime/<id>/clip/?episode=1&season=1&translation_id=610&start=60&end=150&label=clip
 */

import { ref } from 'vue'
import apiClient from '@/api/client'

export type ThemeKind = 'opening' | 'ending'

export interface DownloadState {
  loading: boolean
  progress: number   // 0 или 100
  error: string
  done: boolean
}

export interface CustomSegmentOpts {
  animeId: number
  episode: number
  season?: number
  translationId?: string | number
  startSec: number
  stopSec: number
  label?: string
  animeTitle?: string
}

// ── Composable ────────────────────────────────────────────────────
export function useThemeDownloader() {
  const openingState = ref<DownloadState>({ loading: false, progress: 0, error: '', done: false })
  const endingState  = ref<DownloadState>({ loading: false, progress: 0, error: '', done: false })
  const customState  = ref<DownloadState>({ loading: false, progress: 0, error: '', done: false })

  // Скачивает опенинг или эндинг текущей серии
  async function downloadTheme(opts: {
    animeId: number
    kind: ThemeKind
    episode: number
    season?: number
    translationId?: string | number
    animeTitle?: string
  }) {
    const state = opts.kind === 'opening' ? openingState : endingState
    if (state.value.loading) return
    state.value = { loading: true, progress: 10, error: '', done: false }
    try {
      const { animeId, kind, episode, season = 1, translationId, animeTitle = '' } = opts

      // 1. Получаем тайминги темы
      const themeParams: Record<string, string> = {
        episode: String(episode),
        season:  String(season),
      }
      if (translationId) themeParams.translation_id = String(translationId)

      const themeRes = await apiClient.get(`/anime/${animeId}/themes/`, { params: themeParams })
      const theme = themeRes.data?.[kind]
      if (!theme || theme.start == null || theme.stop == null) {
        throw new Error(`Тайминги ${kind === 'opening' ? 'опенинга' : 'эндинга'} не найдены`)
      }

      state.value.progress = 25

      // 2. Нарезаем через /clip/
      const clipParams: Record<string, string> = {
        episode: String(episode),
        season:  String(season),
        start:   String(Math.floor(theme.start)),
        end:     String(Math.ceil(theme.stop)),
        label:   kind === 'opening' ? 'Opening' : 'Ending',
      }
      if (translationId) clipParams.translation_id = String(translationId)

      const response = await apiClient.get(`/anime/${animeId}/clip/`, {
        params: clipParams,
        responseType: 'blob',
        timeout: 360_000,
        onDownloadProgress: (evt) => {
          if (evt.total && evt.total > 0) {
            state.value.progress = 25 + Math.round((evt.loaded / evt.total) * 70)
          } else {
            state.value.progress = Math.min(92, state.value.progress + 5)
          }
        },
      })

      state.value.progress = 97

      const label = kind === 'opening' ? 'Opening' : 'Ending'
      const disposition = response.headers['content-disposition'] || ''
      let filename = `${animeTitle || 'anime'} - Ep${episode} - ${label}.mp4`
      const fnMatch = disposition.match(/filename\*=UTF-8''([^;\n]+)/)
        || disposition.match(/filename="?([^";\n]+)"?/)
      if (fnMatch) filename = decodeURIComponent(fnMatch[1])

      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 5000)

      state.value = { loading: false, progress: 100, error: '', done: true }
      setTimeout(() => { state.value.done = false }, 3000)

    } catch (err: any) {
      let message = err?.message || 'Ошибка скачивания'
      if (err?.response?.data instanceof Blob) {
        try { message = JSON.parse(await err.response.data.text()).error || message } catch { /* ignore */ }
      }
      state.value = { loading: false, progress: 0, error: message, done: false }
    }
  }

  async function downloadSegment(opts: CustomSegmentOpts) {
    if (customState.value.loading) return
    customState.value = { loading: true, progress: 10, error: '', done: false }

    try {
      const { animeId, episode, season = 1, translationId, startSec, stopSec, label = 'clip', animeTitle = '' } = opts

      if (stopSec <= startSec) throw new Error('Конец должен быть позже начала')
      // Формируем параметры
      const params: Record<string, string> = {
        episode: String(episode),
        season:  String(season),
        start:   String(Math.floor(startSec)),
        end:     String(Math.ceil(stopSec)),
        label:   label.slice(0, 40),
      }
      if (translationId) params.translation_id = String(translationId)

      customState.value.progress = 20

      // Запрос к бэкенду — сервер нарезает и отдаёт файл
      const response = await apiClient.get(`/anime/${animeId}/clip/`, {
        params,
        responseType: 'blob',
        timeout: 360_000, // 6 минут — ffmpeg может работать долго
        onDownloadProgress: (evt) => {
          if (evt.total && evt.total > 0) {
            customState.value.progress = 20 + Math.round((evt.loaded / evt.total) * 75)
          } else {
            // Нет Content-Length — просто показываем анимацию
            customState.value.progress = Math.min(90, customState.value.progress + 5)
          }
        },
      })

      customState.value.progress = 97

      // Определяем имя файла из заголовка или генерируем
      const disposition = response.headers['content-disposition'] || ''
      let filename = `${animeTitle || 'anime'} - Ep${episode} - ${label}.mp4`
      const fnMatch = disposition.match(/filename\*=UTF-8''([^;\n]+)/)
        || disposition.match(/filename="?([^";\n]+)"?/)
      if (fnMatch) {
        filename = decodeURIComponent(fnMatch[1])
      }

      // Скачиваем blob
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 5000)

      customState.value = { loading: false, progress: 100, error: '', done: true }
      setTimeout(() => { customState.value.done = false }, 3000)

    } catch (err: any) {
      // Axios получил blob с ошибкой — читаем текст
      let message = err?.message || 'Ошибка скачивания'
      if (err?.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text()
          const parsed = JSON.parse(text)
          message = parsed.error || message
        } catch { /* ignore */ }
      }
      customState.value = { loading: false, progress: 0, error: message, done: false }
    }
  }

  return {
    openingState,
    endingState,
    customState,
    downloadTheme,
    downloadSegment,
  }
}
