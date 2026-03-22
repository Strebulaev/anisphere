import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import autoprefixer from 'autoprefixer'
import tailwindcss from 'tailwindcss'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    VitePWA({
      registerType: 'autoUpdate',
      strategies: 'generateSW',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'AnimeCore',
        short_name: 'AnimeCore',
        description: 'Социальная сеть для анимешников',
        theme_color: '#7c5cfc',
        background_color: '#080809',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        navigateFallback: null,
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        // НЕ кэшируем API запросы - они должны идти напрямую
        runtimeCaching: [
          {
            // Кэширование изображений по расширению
            urlPattern: /\.(?:jpg|jpeg|png|gif|webp|svg|woff|woff2)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 500,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 дней
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          // Убрали кэширование API - пусть идёт напрямую
        ]
      }
    }),
  ],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-core':      ['vue', 'vue-router', 'pinia'],
          'chat-stores':   ['@/stores/privateChat', '@/stores/groupChat', '@/stores/chatExtras'],
          'notifications': ['@/stores/notifications'],
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  css: {
    postcss: {
      plugins: [
        tailwindcss(),
        autoprefixer({
          overrideBrowserslist: ['> 1%', 'last 2 versions']
        })
      ],
    },
  },
})