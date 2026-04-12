/**
 * Kodik AdBlocker для премиум-пользователей
 * Полная блокировка рекламы в плеере Kodik
 * 
 * Методы блокировки:
 * 1. Перехват и блокировка рекламных postMessage событий от iframe
 * 2. Инъекция CSS для скрытия рекламных элементов
 * 3. Блокировка рекламных network запросов (fetch/XHR)
 * 4. Наблюдение за DOM и удаление рекламных элементов
 * 5. Переопределение рекламных методов плеера
 * 6. Автоматический пропуск рекламных видео
 */

import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'

// Расширяем тип Window для kodikPlayer
declare global {
  interface Window {
    kodikPlayer?: any
    KodikPlayer?: any
    KODIK_AD_BLOCKER_ACTIVE?: boolean
  }
}

// Глобальные паттерны рекламных доменов и URL
const AD_PATTERNS = [
  // Рекламные сети
  'doubleclick',
  'googlesyndication',
  'googleadservices',
  'googletagservices',
  'google-analytics',
  'adservice.google',
  'adsystem',
  'adserver',
  
  // Специфичные для видео рекламы
  'moatads',
  'adnxs',
  'adform',
  'criteo',
  'teads',
  'outbrain',
  'taboola',
  'yieldmo',
  'advertising.com',
  'adsrvr',
  'adcolony',
  'admob',
  'adswizz',
  'adtech',
  'adtilt',
  'adup-tech',
  
  // Российские рекламные сети
  'adfox',
  'yandex.ru/clck',
  'mc.yandex.ru',
  'yandex.ru/ads',
  'mytarget.ru',
  'target.my.com',
  'ads.mail.ru',
  'top.mail.ru',
  'counter.yadro.ru',
  
  // Общие паттерны
  '/ad/',
  '/ads/',
  '/advert/',
  '/advertisement/',
  '/banner/',
  '/banners/',
  '/sponsor/',
  '/promo/',
  '/tracking/',
  '/analytics/',
  
  // Kodik специфичные
  'kodik_advert',
  'kodik_ad',
  'kodik_banner',
  'kodik_promo',
]

// CSS селекторы рекламных элементов в плеере
const AD_ELEMENT_SELECTORS = [
  // Общие рекламные классы
  '.advert',
  '.advertisement',
  '.ad-banner',
  '.ad-container',
  '.ad-overlay',
  '.ad-wrapper',
  '.ad-break',
  '.ad-message',
  '.ad-text',
  '.adsbygoogle',
  '.google-ad',
  '.banner',
  '.sponsor',
  '.promo-overlay',
  '.promotional',
  
  // Kodik специфичные
  '.kodik-ad',
  '.kodik-advert',
  '.kodik-banner',
  '.kodik-promo',
  '.player-ad',
  '.player-ads',
  '.video-ad',
  '.video-ads',
  '.pre-roll',
  '.mid-roll',
  '.post-roll',
  
  // Оверлеи и попупы
  '.overlay-ad',
  '.popup-ad',
  '.interstitial',
  '.takeover',
  
  // Кнопки и призывы к действию
  '.ad-close',
  '.ad-skip',
  '[class*="ad-"]',
  '[id*="ad-"]',
  '[class*="advert"]',
  '[id*="advert"]',
]

// События postMessage связанные с рекламой
const AD_MESSAGE_KEYS = [
  'kodik_player_advert_started',
  'kodik_player_advert_ended',
  'kodik_player_advert_skipped',
  'kodik_player_advert_click',
  'kodik_player_ad',
  'kodik_player_banner',
  'kodik_player_promo',
  'advert_started',
  'advert_ended',
  'advert_click',
  'ad_start',
  'ad_end',
  'ad_loaded',
  'ad_play',
  'ad_pause',
  'ad_skip',
  'banner_show',
  'banner_hide',
  'promo_show',
  'promo_hide',
]

// ============================================================================
// ==================== КОММЕНТАРИЙ: ПОДПИСКА ОТКЛЮЧЕНА =======================
// ============================================================================
// Весь функционал теперь бесплатный. AdBlocker доступен всем пользователям.
// Код подписки сохранён для возможного использования в будущем.
// ============================================================================

export function useAdBlocker() {
  const authStore = useAuthStore()
  
  // Хранилище подписки для проверки премиум статуса
  let subscriptionStore: ReturnType<typeof useSubscriptionStore> | null = null
  
  try {
    subscriptionStore = useSubscriptionStore()
  } catch (e) {
    // Pinia store может быть не инициализирован
    console.warn('[AdBlock] Subscription store not available')
  }

  /**
   * Проверка премиум статуса пользователя
   * ТЕПЕРЬ ВСЕГДА ВОЗВРАЩАЕТ TRUE - весь функционал бесплатный
   */
  const isPremium = (): boolean => {
    // ========================================================================
    // ИЗМЕНЕНО: Теперь все пользователи имеют премиум доступ
    // ========================================================================
    
    // Проверка через auth store (резерв)
    if (authStore.user?.is_premium === true) {
      return true
    }
    
    // Проверка через subscription store (резерв)
    if (subscriptionStore?.isActive) {
      return true
    }
    
    // Проверка через localStorage (резерв)
    try {
      const userData = localStorage.getItem('user')
      if (userData) {
        const user = JSON.parse(userData)
        if (user?.is_premium === true) {
          return true
        }
      }
    } catch (e) {
      // Игнорируем ошибки парсинга
    }
    
    // ВСЕГДА ВОЗВРАЩАЕМ TRUE - весь функционал бесплатный
    return true
  }

  /**
   * Проверка, является ли URL рекламным
   */
  const isAdUrl = (url: string): boolean => {
    const urlLower = url.toLowerCase()
    return AD_PATTERNS.some(pattern => urlLower.includes(pattern))
  }

  /**
   * Проверка, является ли сообщение рекламным
   */
  const isAdMessage = (data: any): boolean => {
    if (!data || typeof data !== 'object') return false
    
    const key = data.key || data.type || ''
    const keyLower = String(key).toLowerCase()
    
    return AD_MESSAGE_KEYS.some(adKey => keyLower.includes(adKey))
  }

  /**
   * Перехват и блокировка рекламных fetch запросов
   * Блокирует загрузку рекламных ресурсов на уровне network
   */
  const blockFetch = () => {
    if (!window.fetch) {
      console.warn('[AdBlock] Fetch API not available')
      return
    }

    const originalFetch = window.fetch.bind(window) as any
    
    window.fetch = function(input: any, init?: any): Promise<Response> {
      const urlStr = typeof input === 'string' 
        ? input 
        : (input?.url || input?.toString?.() || '')
      
      if (urlStr && isAdUrl(urlStr)) {
        console.log('[AdBlock] 🚫 Blocked fetch request:', urlStr)
        // Возвращаем фейковый успешный ответ вместо реального запроса
        return Promise.resolve(new Response('', { 
          status: 200, 
          statusText: 'Blocked by AdBlock' 
        }))
      }
      
      return originalFetch(input, init)
    }
    
    console.log('[AdBlock] ✅ Fetch interception enabled')
  }

  /**
   * Перехват и блокировка рекламных XHR запросов
   * Блокирует XMLHttpRequest для старых библиотек
   */
  const blockXHR = () => {
    if (!window.XMLHttpRequest?.prototype?.open) {
      console.warn('[AdBlock] XMLHttpRequest not available')
      return
    }
    
    const originalOpen = XMLHttpRequest.prototype.open
    const originalSend = XMLHttpRequest.prototype.send
    
    XMLHttpRequest.prototype.open = function(method: string, url: string, async?: boolean, user?: string | null, password?: string | null) {
      // Сохраняем URL для проверки в send
      (this as any)._adBlockUrl = url
      
      if (typeof url === 'string' && isAdUrl(url)) {
        console.log('[AdBlock] 🚫 Blocked XHR open:', url)
        // Прерываем открытие соединения
        return
      }
      
      return originalOpen.call(this, method, url, async ?? true, user, password)
    }
    
    XMLHttpRequest.prototype.send = function(body?: Document | XMLHttpRequestBodyInit | null) {
      const url = (this as any)._adBlockUrl
      if (url && isAdUrl(url)) {
        console.log('[AdBlock] 🚫 Blocked XHR send:', url)
        return
      }
      return originalSend.call(this, body)
    }
    
    console.log('[AdBlock] ✅ XHR interception enabled')
  }

  /**
   * Инъекция CSS для скрытия рекламных элементов
   * Создаёт стиль который скрывает все известные рекламные селекторы
   */
  const injectAdBlockCSS = () => {
    // Проверяем, не был ли уже добавлен стиль
    if (document.getElementById('adblocker-styles')) {
      console.log('[AdBlock] CSS already injected')
      return
    }
    
    const style = document.createElement('style')
    style.id = 'adblocker-styles'
    style.type = 'text/css'
    
    // Генерируем CSS для всех рекламных селекторов
    const cssRules = AD_ELEMENT_SELECTORS.map(selector => 
      `${selector} { display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; }`
    ).join('\n')
    
    // Дополнительные правила для iframe и оверлеев
    const extraRules = `
      /* Блокировка рекламных iframe */
      iframe[src*="ad"],
      iframe[src*="advert"],
      iframe[src*="banner"],
      iframe[src*="promo"] {
        display: none !important;
      }
      
      /* Блокировка оверлеев с рекламой */
      div[style*="position: absolute"][class*="ad"],
      div[style*="position: fixed"][class*="ad"] {
        display: none !important;
      }
      
      /* Принудительное скрытие элементов с рекламными атрибутами */
      [data-ad],
      [data-advertisement],
      [data-banner],
      [data-promo] {
        display: none !important;
      }
    `
    
    style.textContent = cssRules + '\n' + extraRules
    document.head.appendChild(style)
    
    console.log('[AdBlock] ✅ CSS injection complete')
  }

  /**
   * Наблюдатель за DOM для удаления рекламных элементов
   * Отслеживает добавление новых элементов и скрывает рекламу
   */
  const initDOMObserver = () => {
    const observer = new MutationObserver((mutations) => {
      let adsFound = 0
      
      mutations.forEach((mutation) => {
        if (mutation.type !== 'childList') return
        
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType !== Node.ELEMENT_NODE) return
          
          const el = node as HTMLElement
          
          // Рекурсивная проверка элемента и всех его детей
          const checkElement = (element: HTMLElement) => {
            const id = element.id?.toLowerCase() || ''
            const className = element.className?.toLowerCase() || ''
            const tagName = element.tagName?.toLowerCase() || ''
            
            // Проверка по ID
            if (id && (id.includes('ad') || id.includes('advert') || id.includes('banner') || id.includes('promo'))) {
              element.style.display = 'none'
              element.style.visibility = 'hidden'
              adsFound++
              return
            }
            
            // Проверка по классам
            if (className && (className.includes('ad-') || className.includes('advert') || className.includes('banner') || className.includes('sponsor'))) {
              element.style.display = 'none'
              element.style.visibility = 'hidden'
              adsFound++
              return
            }
            
            // Проверка iframe
            if (tagName === 'iframe') {
              const src = (element as HTMLIFrameElement).src?.toLowerCase() || ''
              if (src && isAdUrl(src)) {
                element.style.display = 'none'
                adsFound++
                return
              }
            }
            
            // Рекурсивная проверка детей
            Array.from(element.children).forEach(child => {
              checkElement(child as HTMLElement)
            })
          }
          
          checkElement(el)
        })
      })
      
      if (adsFound > 0) {
        console.log(`[AdBlock] 🚫 Hidden ${adsFound} ad element(s)`)
      }
    })

    // Начинаем наблюдение после загрузки DOM
    if (document.body) {
      observer.observe(document.body, {
        childList: true,
        subtree: true
      })
      console.log('[AdBlock] ✅ DOM observer started')
    } else {
      // Ждём загрузки DOM
      document.addEventListener('DOMContentLoaded', () => {
        observer.observe(document.body, {
          childList: true,
          subtree: true
        })
        console.log('[AdBlock] ✅ DOM observer started (after DOMContentLoaded)')
      })
    }
  }

  /**
   * Перехват и блокировка рекламных postMessage событий
   * Блокирует сообщения между iframe плеера и основным окном
   */
  const blockPostMessage = () => {
    const originalPostMessage = window.postMessage.bind(window)
    
    window.postMessage = function(message: any, targetOrigin?: any, transfer?: any) {
      if (isAdMessage(message)) {
        console.log('[AdBlock] 🚫 Blocked postMessage:', message.key || message.type)
        return
      }
      return originalPostMessage(message, targetOrigin, transfer)
    }
    
    console.log('[AdBlock] ✅ postMessage interception enabled')
  }

  /**
   * Перехват входящих сообщений от iframe плеера
   * Блокирует рекламные события от Kodik
   */
  const blockMessageListener = () => {
    window.addEventListener('message', (event) => {
      if (!event.data || typeof event.data !== 'object') return
      
      const data = event.data as { key?: string; type?: string; source?: string }
      
      // Проверяем, что сообщение от Kodik плеера
      const key = data.key || ''
      if (!key.includes('kodik_player')) return
      
      if (isAdMessage(data)) {
        console.log('[AdBlock] 🚫 Blocked incoming ad message:', key)
        
        // Предотвращаем всплытие события
        event.stopImmediatePropagation()
        event.preventDefault()
      }
    }, true) // Используем capturing phase для перехвата раньше
    
    console.log('[AdBlock] ✅ Message listener enabled')
  }

  /**
   * Блокировка рекламных методов плеера Kodik
   * Переопределяет методы показа рекламы в объекте плеера
   */
  const blockPlayerMethods = () => {
    const checkInterval = setInterval(() => {
      // Ищем объект плеера в window
      const playerObj = window.kodikPlayer || window.KodikPlayer
      
      if (playerObj) {
        clearInterval(checkInterval)
        console.log('[AdBlock] ✅ Found player object, patching methods')
        
        // Блокируем методы на уровне prototype если есть
        if (playerObj.prototype) {
          const methodsToBlock = [
            'showAd', 'loadAd', 'playAd', 'displayAd', 
            'initAd', 'loadBanner', 'showBanner', 
            'showPromo', 'loadPromo', 'advert'
          ]
          
          methodsToBlock.forEach(methodName => {
            if (typeof playerObj.prototype[methodName] === 'function') {
              playerObj.prototype[methodName] = function() {
                console.log(`[AdBlock] 🚫 Blocked player method: ${methodName}`)
                return Promise.resolve()
              }
            }
          })
        }
        
        // Также блокируем на уровне экземпляра если это объект
        if (typeof playerObj === 'object') {
          const methodsToBlock = [
            'showAd', 'loadAd', 'playAd', 'displayAd', 
            'initAd', 'loadBanner', 'showBanner',
            'showPromo', 'loadPromo', 'advert'
          ]
          
          methodsToBlock.forEach(methodName => {
            if (typeof (playerObj as any)[methodName] === 'function') {
              (playerObj as any)[methodName] = function() {
                console.log(`[AdBlock] 🚫 Blocked instance method: ${methodName}`)
                return Promise.resolve()
              }
            }
          })
        }
      }
    }, 500)
    
    // Очищаем интервал через 10 секунд если плеер не найден
    setTimeout(() => clearInterval(checkInterval), 10000)
  }

  /**
   * Автоматический пропуск рекламных видео
   * Находит видео элементы и пропускает короткие ролики (рекламу)
   */
  const skipVideoAds = () => {
    const checkVideos = () => {
      const videos = document.querySelectorAll('video')
      
      videos.forEach((video) => {
        // Помечаем видео чтобы не обрабатывать повторно
        if ((video as any)._adBlockProcessed) return
        ;(video as any)._adBlockProcessed = true
        
        // Блокируем стандартные рекламные события
        video.addEventListener('adsready', (e) => {
          e.stopImmediatePropagation()
          console.log('[AdBlock] 🚫 Blocked adsready event')
        }, true)
        
        video.addEventListener('adstart', (e) => {
          e.stopImmediatePropagation()
          console.log('[AdBlock] 🚫 Blocked adstart event')
          // Пытаемся пропустить рекламу
          if (video.duration && video.duration < 60) {
            video.currentTime = video.duration
          }
        }, true)
        
        video.addEventListener('adloaded', (e) => {
          e.stopImmediatePropagation()
          console.log('[AdBlock] 🚫 Blocked adloaded event')
        }, true)
        
        // Автоматическая перемотка если видео похоже на рекламу
        video.addEventListener('timeupdate', function() {
          // Если видео короткое (<30 сек) и это не основной контент
          if (video.duration && video.duration < 30 && video.currentTime > 2) {
            const parent = video.parentElement
            const parentClass = parent?.className?.toLowerCase() || ''
            
            // Если родитель не похож на основной плеер
            if (!parentClass.includes('main') && !parentClass.includes('player')) {
              console.log('[AdBlock] 🚫 Skipping short video (possible ad)')
              video.currentTime = video.duration
            }
          }
        })
      })
    }
    
    // Проверяем сразу и затем каждые 2 секунды
    checkVideos()
    setInterval(checkVideos, 2000)
    
    console.log('[AdBlock] ✅ Video ad skip enabled')
  }

  /**
   * Инъекция скрипта в iframe плеера
   * Пытается внедрить скрипт блокировки рекламы напрямую в iframe
   */
  const injectIntoIframe = (iframe: HTMLIFrameElement) => {
    try {
      // Работает только если iframe на том же домене (CORS ограничение)
      const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
      
      if (!iframeDoc) {
        console.warn('[AdBlock] Cannot access iframe document (CORS)')
        return
      }
      
      const style = iframeDoc.createElement('style')
      style.textContent = `
        .advert, .ad, .banner, .promo, .sponsor {
          display: none !important;
        }
      `
      iframeDoc.head.appendChild(style)
      
      console.log('[AdBlock] ✅ Injected styles into iframe')
    } catch (e) {
      // Ожидаемая ошибка из-за CORS
      console.log('[AdBlock] ⚠️ Cannot inject into iframe (CORS restriction)')
    }
  }

  /**
   * Наблюдение за iframe плеера и инъекция при загрузке
   */
  const watchIframes = () => {
    const observer = new MutationObserver(() => {
      const iframes = document.querySelectorAll('iframe')
      iframes.forEach(iframe => {
        const src = iframe.src?.toLowerCase() || ''
        if (src.includes('kodik') && !(iframe as any)._adBlockWatched) {
          ;(iframe as any)._adBlockWatched = true
          
          iframe.addEventListener('load', () => {
            injectIntoIframe(iframe)
          })
        }
      })
    })
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    })
    
    console.log('[AdBlock] ✅ Iframe watcher enabled')
  }

  /**
   * Основная функция инициализации AdBlocker
   * Запускает все методы блокировки рекламы
   * ТЕПЕРЬ ДОСТУПНО ВСЕМ ПОЛЬЗОВАТЕЛЯМ БЕСПЛАТНО
   */
  const init = () => {
    // ========================================================================
    // ИЗМЕНЕНО: Проверка отключена - AdBlocker доступен всем
    // ========================================================================
    // if (!isPremium()) {
    //   console.log('[AdBlock] ⚠️ User is not premium, ad block disabled')
    //   window.KODIK_AD_BLOCKER_ACTIVE = false
    //   return
    // }

    console.log('[AdBlock] 🛡️ === ACTIVATING AD BLOCKER (FREE FOR ALL) ===')
    window.KODIK_AD_BLOCKER_ACTIVE = true
    
    // 1. Инъекция CSS (самый надёжный метод)
    injectAdBlockCSS()
    
    // 2. Наблюдатель за DOM
    initDOMObserver()
    
    // 3. Перехват postMessage
    blockPostMessage()
    
    // 4. Перехват входящих сообщений
    blockMessageListener()
    
    // 5. Блокировка fetch (с задержкой чтобы не ломать другие запросы)
    setTimeout(blockFetch, 100)
    
    // 6. Блокировка XHR
    setTimeout(blockXHR, 100)
    
    // 7. Блокировка методов плеера
    blockPlayerMethods()
    
    // 8. Пропуск видео рекламы
    skipVideoAds()
    
    // 9. Наблюдение за iframe
    setTimeout(watchIframes, 500)
    
    console.log('[AdBlock] 🛡️ === AD BLOCKER FULLY ACTIVATED ===')
  }

  /**
   * Деактивация AdBlocker
   * Может понадобиться если пользователь потерял премиум статус
   */
  const deactivate = () => {
    console.log('[AdBlock] ❌ Deactivating ad blocker')
    window.KODIK_AD_BLOCKER_ACTIVE = false
    
    // Удаляем CSS
    const style = document.getElementById('adblocker-styles')
    if (style) {
      style.remove()
    }
  }

  return {
    init,
    deactivate,
    isPremium,
    isAdUrl,
    isAdMessage
  }
}
