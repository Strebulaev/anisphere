export const KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'
// export const KODIK_API_TOKEN = 'KODIK_API' (почта кодик support@kodikres.com)

export const KODIK_API_BASE    = 'https://kodik-api.com' 
export const KODIK_PLAYER_BASE = 'https://kodikplayer.com' 
export const KODIK_DB_BASE        = 'https://bd.kodikres.com'
export const KODIK_SCREENSHOTS_BASE = 'https://i.kodikres.com' 
export const KODIK_SOCIAL_BASE = 'https://kodikonline.com' 

const KODIK_OLD_PLAYER_DOMAINS = ['kodik.cc', 'kodik.info']

export function normalizeKodikPlayerLink(link: string): string {
  if (!link) return link

  let url = link
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
