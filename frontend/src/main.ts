import './assets/main.css'
import './assets/css/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Initialize auth check
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
authStore.checkAuth()

// Initialize settings
import { useSettingsStore } from '@/stores/settings'
const settingsStore = useSettingsStore()
settingsStore.init()

app.mount('#app')
