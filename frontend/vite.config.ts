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
        // ИСКЛЮЧАЕМ изображения из пре-кэша - они будут кэшироваться динамически
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        // Исключаем изображения из прекэша явно
        globIgnores: ['**/*.jpg', '**/*.jpeg', '**/*.webp', '**/*.gif', '**/*.avif'],
        runtimeCaching: [
          {
            // Динамическое кэширование изображений с ЖЁСТКИМИ ЛИМИТАМИ
            urlPattern: /\.(?:jpg|jpeg|png|gif|webp|avif|svg)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 50,           // Не более 50 файлов
                maxAgeSeconds: 60 * 60 * 24 * 7 // 7 дней
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          // Шрифты - тоже с лимитами
          {
            urlPattern: /\.(?:woff|woff2|ttf|otf)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 дней
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
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