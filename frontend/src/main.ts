import './assets/main.scss'
import './assets/css/main.css'
import './assets/styles/themes.css'
import './assets/styles/fonts.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// Import debug utils
import '@/utils/debugAuth'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Initialize auth check
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()

// Skip auth check in local development mode
const isLocalDevelopment = () => {
  const hostname = window.location.hostname
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1'
}

if (!isLocalDevelopment()) {
  authStore.checkAuth()
} else {
  console.log('🔓 Local development mode: Skipping initial auth check')
}

// Initialize settings
import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
settingsStore.init()

app.mount('#app')
