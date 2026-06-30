import './assets/main.scss'
import './assets/css/main.css'
import './assets/styles/themes.css'
import './assets/styles/fonts.css'
import './assets/styles/modals-mobile.css'
import './assets/styles/mobile.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import '@/utils/debugAuth'

import OptimizedImage from '@/components/common/OptimizedImage.vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'
import EmojiReplacer from '@/components/ui/EmojiReplacer.vue'
import StarRating from '@/components/ui/StarRating.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

import { sakuraEmoji } from '@/directives/sakuraEmoji'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.component('OptimizedImage', OptimizedImage)
app.component('SakuraIcon', SakuraIcon)
app.component('EmojiReplacer', EmojiReplacer)
app.component('StarRating', StarRating)
app.component('StatusBadge', StatusBadge)

app.directive('sakura-emoji', sakuraEmoji)

import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()

authStore.checkAuth()

import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
settingsStore.init()

const CACHE_STORAGE_LIMIT_MB = 200 

async function cleanupCacheStorage() {
  if (!navigator.storage || !navigator.storage.estimate) {
    console.warn('🔧 Cache cleanup: Storage API not supported')
    return
  }

  try {
    const estimate = await navigator.storage.estimate()
    const usedMB = (estimate.usage || 0) / (1024 * 1024)
    const quotaMB = (estimate.quota || 0) / (1024 * 1024)

    console.log(`💾 Cache Storage: ${usedMB.toFixed(2)} MB / ${quotaMB.toFixed(2)} MB`)

    if (usedMB > CACHE_STORAGE_LIMIT_MB) {
      console.warn(`🧹 Cache cleanup: Превышен лимит ${CACHE_STORAGE_LIMIT_MB} MB (текущее ${usedMB.toFixed(2)} MB). Очищаем кэши...`)

      const cacheNames = await caches.keys()
      
      for (const cacheName of cacheNames) {
        try {
          const cache = await caches.open(cacheName)
          const requests = await cache.keys()
          
          const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000)
          let deletedCount = 0

          for (const request of requests) {
            const response = await cache.match(request)
            if (response) {
              const dateHeader = response.headers.get('date')
              if (dateHeader) {
                const responseDate = new Date(dateHeader).getTime()
                if (responseDate < oneDayAgo) {
                  await cache.delete(request)
                  deletedCount++
                }
              }
            }
          }

          if (deletedCount > 0) {
            console.log(`🗑️ Cache "${cacheName}": удалено ${deletedCount} старых записей`)
          }
        } catch (e) {
          console.warn(`⚠️ Не удалось очистить кэш "${cacheName}":`, e)
        }
      }

      const newEstimate = await navigator.storage.estimate()
      const newUsedMB = (newEstimate.usage || 0) / (1024 * 1024)
      console.log(`✅ После очистки: ${newUsedMB.toFixed(2)} MB (освобождено ${(usedMB - newUsedMB).toFixed(2)} MB)`)
    }
  } catch (error) {
    console.error('❌ Ошибка при очистке Cache Storage:', error)
  }
}

cleanupCacheStorage()

app.mount('#app')
