import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import autoprefixer from 'autoprefixer'
import tailwindcss from 'tailwindcss'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    VitePWA({
      registerType: 'autoUpdate',
      strategies: 'generateSW',
      includeAssets: ['favicon.ico', 'sakura.png', 'mask-icon.svg'],
      manifest: {
        name: 'AniSphere',
        short_name: 'AniSphere',
        description: 'Социальная сеть для анимешников',
        theme_color: '#7c5cfc',
        background_color: '#080809',
        display: 'standalone',
        icons: [
          {
            src: 'sakura.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'sakura.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'sakura.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        navigateFallback: null,
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        globIgnores: [
          '**/*.jpg', 
          '**/*.jpeg', 
          '**/*.png',  
          '**/*.webp', 
          '**/*.gif', 
          '**/*.avif'
        ],
        runtimeCaching: [
          {
            urlPattern: /\.(?:jpg|jpeg|png|gif|webp|avif|svg)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 50,         
                maxAgeSeconds: 60 * 60 * 24 * 7
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /\.(?:woff|woff2|ttf|otf)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 30 
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
  server: {
    proxy: {
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
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