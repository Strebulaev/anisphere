// ═══════════════════════════════════════════════════════════════
// KODIK DOMAINS CONFIG
// Обновляй только здесь — все компоненты и API используют эти константы
// ═══════════════════════════════════════════════════════════════

export const KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'

// Актуальные домены (обновлено после инцидента с регистратором)
export const KODIK_API_BASE    = 'https://kodik-api.com'    // API
export const KODIK_PLAYER_BASE = 'https://kodikplayer.com'  // Плеер (было: kodik.cc / kodik.info)
export const KODIK_DB_BASE        = 'https://bd.kodikres.com'   // База данных
export const KODIK_SCREENSHOTS_BASE = 'https://i.kodikres.com'   // Скриншоты
export const KODIK_SOCIAL_BASE = 'https://kodikonline.com'  // Плеер для соцсетей

// Старые домены которые могут встречаться в сохранённых ссылках
const KODIK_OLD_PLAYER_DOMAINS = ['kodik.cc', 'kodik.info']

/**
 * Нормализует ссылку на плеер Kodik:
 * заменяет старые домены (kodik.cc, kodik.info) на актуальный kodikplayer.com.
 * Безопасно вызывать для любой ссылки — если домен уже новый, ссылка не изменится.
 */
export function normalizeKodikPlayerLink(link: string): string {
  if (!link) return link

  let url = link
  // Добавляем схему если отсутствует
  if (url.startsWith('//')) {
    url = 'https:' + url
  } else if (!url.startsWith('http')) {
    url = 'https://' + url
  }

  for (const oldDomain of KODIK_OLD_PLAYER_DOMAINS) {
    if (url.includes(oldDomain)) {
      url = url.replace(oldDomain, 'kodikplayer.com')
      break
    }
  }

  return url
}
