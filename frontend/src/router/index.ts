import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import AnimeView from '@/views/AnimeView.vue'
import AnimeDetailView from '@/views/AnimeDetailView.vue'
import ProfileView from '@/views/ProfileView.vue'
import FeedView from '@/views/FeedView.vue'
import ChatsView from '@/views/ChatsView.vue'
import PlaylistsView from '@/views/PlaylistsView.vue'
import NotificationsView from '@/views/NotificationsView.vue'
import SettingsView from '@/views/SettingsView.vue'
import ReactorView from '@/views/ReactorView.vue'
import CompetitionsView from '@/views/CompetitionsView.vue'
import ChatDetailView from '@/views/ChatDetailView.vue'
import SearchView from '@/views/SearchView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresGuest: true }
    },
    {
      path: '/anime',
      name: 'anime',
      component: AnimeView
    },
    {
      path: '/anime/:id',
      name: 'anime-detail',
      component: AnimeDetailView,
      props: true
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/feed',
      name: 'feed',
      component: FeedView,
      meta: { requiresAuth: true }
    },
    {
      path: '/reactor',
      name: 'reactor',
      component: ReactorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/reactor/competitions',
      name: 'reactor-competitions',
      component: CompetitionsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chat/:id',
      name: 'chat-detail-view',
      component: ChatDetailView,
      props: true
    },
    {
      path: '/playlists',
      name: 'playlists',
      component: PlaylistsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      // Try to check authentication status
      try {
        await authStore.checkAuth()
        if (!authStore.isAuthenticated) {
          next('/login')
          return
        }
      } catch (error) {
        next('/login')
        return
      }
    }
  }
  
  // Check if route requires guest (not authenticated)
  if (to.matched.some(record => record.meta.requiresGuest)) {
    if (authStore.isAuthenticated) {
      next('/anime')
      return
    }
  }
  
  next()
})

export default router