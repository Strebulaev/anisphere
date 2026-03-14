import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '@/components/page/other/HomeView.vue'
import LoginView from '@/components/page/auth/LoginView.vue'
import RegisterView from '@/components/page/auth/RegisterView.vue'
import AnimeView from '@/components/page/anime/AnimeView.vue'
import AnimeDetailView from '@/components/page/anime/AnimeDetailView.vue'
import FranchiseView from '@/components/page/anime/FranchiseView.vue'
import AnimeWatchView from '@/components/page/anime/AnimeWatchView.vue'
import OwnProfileView from '@/components/page/profile/OwnProfileView.vue'
import UserProfileView from '@/components/page/profile/UserProfileView.vue'
import FeedView from '@/components/page/feed/FeedView.vue'
import ChatsView from '@/components/page/chats/ChatsView.vue'
import PlaylistsView from '@/components/page/playlists/PlaylistsView.vue'
import PlaylistDetailView from '@/components/page/playlists/PlaylistDetailView.vue'
import MyPlaylistsView from '@/components/page/playlists/MyPlaylistsView.vue'
import CreatePlaylistView from '@/components/page/playlists/CreatePlaylistView.vue'
import PublicPlaylistsView from '@/components/page/playlists/PublicPlaylistsView.vue'
import FavoritesView from '@/components/page/other/FavoritesView.vue'
import NotificationsView from '@/components/page/notifications/NotificationsView.vue'
import NotificationSettingsView from '@/components/page/notifications/NotificationSettingsView.vue'
import SettingsView from '@/components/page/settings/SettingsView.vue'
import ReactorView from '@/components/page/feed/ReactorView.vue'
import CompetitionsView from '@/components/page/admin/CompetitionsView.vue'
import CompetitionResultsView from '@/components/page/admin/CompetitionResultsView.vue'
import ChatDetailView from '@/components/page/chats/ChatDetailView.vue'
import SearchView from '@/components/page/search/SearchView.vue'
import KodikImport from '@/components/page/admin/KodikImport.vue'
import UserLibraryView from '@/components/page/profile/UserLibraryView.vue'
import OnlineUsers from '@/components/page/other/OnlineUsers.vue'
import AchievementsView from '@/components/page/other/AchievementsView.vue'
import PeopleView from '@/views/PeopleView.vue'
import PeopleDetailView from '@/views/PeopleDetailView.vue'
import UsersView from '@/views/UsersView.vue'
import StudiosView from '@/views/studios/StudiosView.vue'
import StudioDetailView from '@/views/studios/StudioDetailView.vue'
import SharedPlaylistView from '@/components/page/playlists/SharedPlaylistView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '',
      name: 'home',
      component: HomeView
    },
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
      name: 'anime-catalog',
      component: AnimeView
    },
    {
      path: '/anime/:id',
      name: 'anime-detail',
      component: AnimeDetailView,
      props: true
    },
    {
      path: '/franchise/:id',
      name: 'franchise-detail',
      component: FranchiseView,
      props: true
    },
    {
      path: '/anime/:id/watch',
      name: 'anime-watch',
      component: AnimeWatchView,
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
      component: OwnProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/profile/:id',
      name: 'user-profile',
      component: UserProfileView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/online',
      name: 'online',
      component: OnlineUsers,
      meta: { requiresAuth: true }
    },
    {
      path: '/achievements',
      name: 'achievements',
      component: AchievementsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/feed',
      name: 'feed',
      component: FeedView,
      meta: { requiresAuth: true }
    },
    {
      path: '/post/:id',
      name: 'post-detail',
      component: FeedView,
      props: true,
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
      path: '/reactor/competitions/:id/results',
      name: 'competition-results',
      component: CompetitionResultsView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chats/:id',
      name: 'chat-detail',
      component: ChatsView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/chat/:id',
      name: 'chat-detail-view',
      component: ChatsView,
      props: true
    },
    {
      path: '/playlists',
      name: 'playlists',
      component: PlaylistsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/playlists/create',
      name: 'create-playlist',
      component: CreatePlaylistView,
      meta: { requiresAuth: true }
    },
    {
      path: '/my-playlists',
      name: 'my-playlists',
      component: MyPlaylistsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/public-playlists',
      name: 'public-playlists',
      component: PublicPlaylistsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: FavoritesView,
      meta: { requiresAuth: true }
    },
    {
      path: '/library',
      name: 'library',
      component: UserLibraryView,
      meta: { requiresAuth: true }
    },
    {
      path: '/playlist/:id',
      name: 'playlist-detail',
      component: PlaylistDetailView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      // Share-ссылка — доступна без авторизации
      path: '/playlist/shared/:token',
      name: 'playlist-shared',
      component: SharedPlaylistView,
      props: true
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications/settings',
      name: 'notification-settings',
      component: NotificationSettingsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/kodik-import',
      name: 'kodik-import',
      component: KodikImport,
      meta: { requiresAuth: true }
    },
    {
      path: '/people',
      name: 'people',
      component: PeopleView
    },
    {
      path: '/users',
      name: 'users',
      component: UsersView
    },
    {
      path: '/people/:id',
      name: 'people-detail',
      component: PeopleDetailView,
      props: true
    },
    {
      path: '/studios',
      name: 'studios',
      component: StudiosView
    },
    {
      path: '/studios/:slug',
      name: 'studio-detail',
      component: StudioDetailView,
      props: true
    }
  ]
})

// Check if running in local development mode
const isLocalDevelopment = () => {
  const hostname = window.location.hostname
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1'
}

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Skip auth checks in local development mode
  if (isLocalDevelopment()) {
    console.log('🔓 Local development mode: Auth checks skipped')
    next()
    return
  }

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