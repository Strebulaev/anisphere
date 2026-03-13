<template>
  <div class="playlists-page">
    <!-- Шапка -->
    <div class="page-header">
      <div class="header-top">
        <h1 class="page-title">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18V5l12-2v13"/>
            <circle cx="6" cy="18" r="3"/>
            <circle cx="18" cy="16" r="3"/>
          </svg>
          Плейлисты
        </h1>
        <button class="btn-create" @click="router.push('/playlists/create')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Создать плейлист
        </button>
      </div>

      <!-- Основные вкладки -->
      <div class="tabs-row">
        <button
          v-for="tab in mainTabs"
          :key="tab.id"
          @click="switchMainTab(tab.id)"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Подвкладки «Мои плейлисты» -->
      <transition name="subtabs">
        <div v-if="activeTab === 'my'" class="subtabs-row">
          <button
            v-for="sub in mySubTabs"
            :key="sub.id"
            @click="switchMySubTab(sub.id)"
            :class="['subtab-btn', { active: mySubTab === sub.id }]"
          >
            <span :class="['vis-dot', `dot-${sub.id}`]"></span>
            {{ sub.label }}
            <span v-if="sub.count !== undefined" class="subtab-count">{{ sub.count }}</span>
          </button>
        </div>
      </transition>
    </div>

    <!-- Поиск и сортировка -->
    <div class="filters-bar">
      <div class="search-wrapper">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon-svg">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input v-model="searchQuery" type="text" placeholder="Поиск по плейлистам..." class="search-input" />
        <button v-if="searchQuery" @click="searchQuery = ''" class="search-clear-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="sort-wrapper">
        <select v-model="sortBy" class="sort-select">
          <option value="-updated_at">По дате обновления</option>
          <option value="-created_at">По дате создания</option>
          <option value="title">По названию (А-Я)</option>
          <option value="-title">По названию (Я-А)</option>
          <option value="-favorites_count">По популярности</option>
        </select>
      </div>
    </div>

    <!-- Скелетоны -->
    <div v-if="loading" class="playlists-grid">
      <div v-for="n in 8" :key="n" class="skeleton-card">
        <div class="skeleton-cover"></div>
        <div class="skeleton-info">
          <div class="skeleton-line w-70"></div>
          <div class="skeleton-line w-40"></div>
          <div class="skeleton-line w-55"></div>
        </div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="empty-state">
      <div class="empty-icon">⚠️</div>
      <h3>Не удалось загрузить плейлисты</h3>
      <p>{{ error }}</p>
      <button @click="loadPlaylists" class="btn-retry">Попробовать снова</button>
    </div>

    <!-- Пустой список -->
    <div v-else-if="playlists.length === 0" class="empty-state">
      <div class="empty-icon">{{ emptyIcon }}</div>
      <h3>{{ emptyTitle }}</h3>
      <p>{{ emptyMessage }}</p>
      <button v-if="activeTab === 'my'" @click="router.push('/playlists/create')" class="btn-create-empty">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Создать первый плейлист
      </button>
    </div>

    <!-- Сетка плейлистов -->
    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        :current-user-id="currentUserId"
        :is-favorite="playlist.is_favorited"
        @click="goToPlaylist"
        @favoriteToggle="handleFavoriteToggle"
        @share="handleShare"
        @edit="handleEdit"
        @delete="handleDelete"
      />
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
      <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1" class="page-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <div class="page-numbers">
        <button
          v-for="p in visiblePages"
          :key="p"
          @click="p !== '...' && changePage(p as number)"
          :class="['page-num', { active: p === currentPage, dots: p === '...' }]"
        >{{ p }}</button>
      </div>
      <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages" class="page-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMessage" class="toast-notification">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ toastMessage }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import playlistsApi, { type Playlist, type PlaylistVisibility } from '@/api/playlists'
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'

const router = useRouter()
const authStore = useAuthStore()

type MainTab = 'my' | 'public' | 'favorites'
type MySubTab = 'all' | 'public' | 'private' | 'link'

const playlists = ref<Playlist[]>([])
const loading = ref(false)
const error = ref('')
const activeTab = ref<MainTab>('my')
const mySubTab = ref<MySubTab>('all')
const searchQuery = ref('')
const sortBy = ref('-updated_at')
const currentPage = ref(1)
const totalCount = ref(0)
const pageSize = 12
const currentUserId = ref<number | undefined>(undefined)
const toastMessage = ref('')

// Счётчики для вкладок
const myAllCount = ref(0)
const myPublicCount = ref(0)
const myPrivateCount = ref(0)
const myLinkCount = ref(0)
const favCount = ref(0)

let searchTimeout: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))

const mainTabs = computed(() => [
  { id: 'my', label: 'Мои плейлисты', icon: '📁', count: myAllCount.value },
  { id: 'public', label: 'Публичные', icon: '🌍', count: undefined },
  { id: 'favorites', label: 'Избранное', icon: '⭐', count: favCount.value },
])

const mySubTabs = computed(() => [
  { id: 'all', label: 'Все', count: myAllCount.value },
  { id: 'public', label: 'Публичные', count: myPublicCount.value },
  { id: 'private', label: 'Приватные', count: myPrivateCount.value },
  { id: 'link', label: 'По ссылке', count: myLinkCount.value },
])

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})

// Пустое состояние
const emptyIcon = computed(() => {
  if (activeTab.value === 'favorites') return '⭐'
  if (activeTab.value === 'public') return '🌍'
  if (mySubTab.value === 'private') return '🔒'
  if (mySubTab.value === 'link') return '🔗'
  return '📁'
})
const emptyTitle = computed(() => {
  if (searchQuery.value) return 'Ничего не найдено'
  if (activeTab.value === 'favorites') return 'Нет избранных плейлистов'
  if (activeTab.value === 'public') return 'Нет публичных плейлистов'
  if (mySubTab.value === 'private') return 'Нет приватных плейлистов'
  if (mySubTab.value === 'link') return 'Нет плейлистов «по ссылке»'
  return 'У вас пока нет плейлистов'
})
const emptyMessage = computed(() => {
  if (searchQuery.value) return 'Попробуйте изменить запрос'
  if (activeTab.value === 'favorites') return 'Добавляйте понравившиеся плейлисты в избранное'
  if (activeTab.value === 'public') return 'Пока никто не создал публичных плейлистов'
  return 'Создайте первый плейлист и добавьте любимое аниме'
})

const buildParams = () => {
  const params: Record<string, any> = {
    page: currentPage.value,
    page_size: pageSize,
    ordering: sortBy.value,
  }
  if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
  return params
}

const loadPlaylists = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = buildParams()
    let response: any

    if (activeTab.value === 'my') {
      // Только плейлисты пользователя, с подфильтром по visibility
      const myParams: any = { ...params, my: true }
      if (mySubTab.value !== 'all') {
        myParams.visibility = mySubTab.value
      }
      response = await playlistsApi.getAllPlaylists(myParams)

    } else if (activeTab.value === 'public') {
      // ВСЕ публичные от всех пользователей
      response = await playlistsApi.getAllPlaylists({ ...params, is_public: true })

    } else {
      // Избранное — все плейлисты из избранного (любая видимость)
      response = await playlistsApi.getAllPlaylists({ ...params, favorites: true })
    }

    const data = response.data
    playlists.value = data.results || data
    totalCount.value = data.count || playlists.value.length
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Не удалось загрузить плейлисты'
  } finally {
    loading.value = false
  }
}

const loadCounts = async () => {
  try {
    const [allRes, pubRes, privRes, linkRes, favRes] = await Promise.allSettled([
      playlistsApi.getAllPlaylists({ my: true, page_size: 1 }),
      playlistsApi.getAllPlaylists({ my: true, visibility: 'public', page_size: 1 }),
      playlistsApi.getAllPlaylists({ my: true, visibility: 'private', page_size: 1 }),
      playlistsApi.getAllPlaylists({ my: true, visibility: 'link', page_size: 1 }),
      playlistsApi.getAllPlaylists({ favorites: true, page_size: 1 }),
    ])
    if (allRes.status === 'fulfilled') myAllCount.value = allRes.value.data.count || 0
    if (pubRes.status === 'fulfilled') myPublicCount.value = pubRes.value.data.count || 0
    if (privRes.status === 'fulfilled') myPrivateCount.value = privRes.value.data.count || 0
    if (linkRes.status === 'fulfilled') myLinkCount.value = linkRes.value.data.count || 0
    if (favRes.status === 'fulfilled') favCount.value = favRes.value.data.count || 0
  } catch {}
}

const switchMainTab = (tab: string) => {
  activeTab.value = tab as MainTab
  currentPage.value = 1
}

const switchMySubTab = (sub: string) => {
  mySubTab.value = sub as MySubTab
  currentPage.value = 1
  loadPlaylists()
}

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const goToPlaylist = (playlist: Playlist | { id: number }) => {
  router.push(`/playlist/${playlist.id}`)
}

const handleFavoriteToggle = async (playlistId: number, isFavorite: boolean) => {
  const playlist = playlists.value.find(p => p.id === playlistId)
  if (!playlist) return
  try {
    if (isFavorite) {
      await playlistsApi.addPlaylistToFavorites(playlistId)
      playlist.is_favorited = true
      playlist.favorites_count++
      showToast('Плейлист добавлен в избранное')
    } else {
      await playlistsApi.removePlaylistFromFavorites(playlistId)
      playlist.is_favorited = false
      playlist.favorites_count = Math.max(0, playlist.favorites_count - 1)
      showToast('Плейлист убран из избранного')
      if (activeTab.value === 'favorites') {
        playlists.value = playlists.value.filter(p => p.id !== playlistId)
        totalCount.value = Math.max(0, totalCount.value - 1)
      }
    }
    loadCounts()
  } catch {}
}

const handleShare = async (playlistId: number) => {
  const playlist = playlists.value.find(p => p.id === playlistId)
  if (!playlist) return

  try {
    if (playlist.visibility === 'link' || playlist.share_token) {
      // Генерируем/обновляем share-ссылку
      const res = await playlistsApi.generateShareLink(playlistId)
      const url = res.data.share_url || `${window.location.origin}/playlist/shared/${res.data.token}`
      await navigator.clipboard.writeText(url)
      showToast('Ссылка скопирована в буфер обмена')
    } else {
      // Публичный — обычная ссылка
      const url = `${window.location.origin}/playlist/${playlistId}`
      await navigator.clipboard.writeText(url)
      showToast('Ссылка скопирована в буфер обмена')
    }
  } catch {
    const url = `${window.location.origin}/playlist/${playlistId}`
    navigator.clipboard.writeText(url)
    showToast('Ссылка скопирована')
  }
}

const handleEdit = (playlist: Playlist | { id: number }) => {
  router.push(`/playlist/${playlist.id}`)
}

const handleDelete = async (playlist: Playlist | { id: number; title?: string }) => {
  const title = (playlist as any).title || 'плейлист'
  if (!confirm(`Удалить «${title}»?`)) return
  try {
    await playlistsApi.deletePlaylist(playlist.id)
    playlists.value = playlists.value.filter(p => p.id !== playlist.id)
    totalCount.value = Math.max(0, totalCount.value - 1)
    loadCounts()
    showToast('Плейлист удалён')
  } catch {}
}

const showToast = (msg: string) => {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

watch(activeTab, () => {
  currentPage.value = 1
  loadPlaylists()
})

watch(sortBy, () => {
  currentPage.value = 1
  loadPlaylists()
})

watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadPlaylists()
  }, 350)
})

watch(currentPage, loadPlaylists)

onMounted(async () => {
  if (authStore.user) currentUserId.value = authStore.user.id
  await loadPlaylists()
  loadCounts()
})
</script>

<style scoped>
.playlists-page {
  padding: 2rem 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

/* ─── Шапка ─── */
.page-header { margin-bottom: 1.25rem; }
.header-top {
  display: flex; align-items: center;
  justify-content: space-between; gap: 1rem;
  margin-bottom: 1rem;
}
.page-title {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 1.6rem; font-weight: 800; color: var(--color-text); margin: 0;
}
.btn-create {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.65rem 1.1rem;
  background: var(--color-accent); color: #fff;
  border: none; border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.85rem; font-weight: 700; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
}
.btn-create:hover { background: var(--color-accent-hover); transform: translateY(-1px); }

/* ─── Основные вкладки ─── */
.tabs-row {
  display: flex; gap: 0.25rem;
  border-bottom: 1px solid var(--color-divider);
  padding-bottom: 0;
}
.tab-btn {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.65rem 1rem;
  background: transparent; border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.875rem; font-weight: 600;
  color: var(--color-text-secondary); cursor: pointer;
  transition: all 0.15s; margin-bottom: -1px; white-space: nowrap;
}
.tab-btn:hover { color: var(--color-text); }
.tab-btn.active { color: var(--color-accent); border-bottom-color: var(--color-accent); }
.tab-icon { font-size: 0.95rem; }
.tab-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 4px;
  background: var(--color-background-active); border-radius: 999px;
  font-size: 0.67rem; font-weight: 700; color: var(--color-text-tertiary);
}
.tab-btn.active .tab-count { background: rgba(58,134,255,0.15); color: var(--color-accent); }

/* ─── Подвкладки «Мои» ─── */
.subtabs-row {
  display: flex; gap: 0.4rem;
  padding: 0.6rem 0 0;
  flex-wrap: wrap;
}
.subtab-btn {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.3rem 0.75rem;
  background: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 999px;
  font-size: 0.8rem; font-weight: 600;
  color: var(--color-text-secondary); cursor: pointer;
  transition: all 0.15s;
}
.subtab-btn:hover { border-color: var(--color-accent); color: var(--color-text); }
.subtab-btn.active {
  background: var(--color-accent); color: #fff;
  border-color: var(--color-accent);
}
.subtab-count {
  font-size: 0.65rem; opacity: 0.75;
  background: rgba(255,255,255,0.15); border-radius: 999px;
  padding: 0 4px; min-width: 14px; text-align: center;
}
.subtab-btn:not(.active) .subtab-count {
  background: var(--color-background-surface);
  color: var(--color-text-tertiary);
}

/* Цветные точки видимости */
.vis-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.dot-public { background: #22c55e; }
.dot-private { background: #ef4444; }
.dot-link { background: #3a86ff; }
.dot-all { background: var(--color-text-tertiary); }
.subtab-btn.active .vis-dot { background: rgba(255,255,255,0.8); }

/* Анимация подвкладок */
.subtabs-enter-active, .subtabs-leave-active { transition: all 0.2s; }
.subtabs-enter-from, .subtabs-leave-to { opacity: 0; transform: translateY(-6px); }

/* ─── Фильтры ─── */
.filters-bar {
  display: flex; gap: 0.75rem; margin-bottom: 1.25rem; align-items: center;
}
.search-wrapper {
  flex: 1; position: relative; display: flex; align-items: center;
}
.search-icon-svg { position: absolute; left: 0.75rem; color: var(--color-text-tertiary); pointer-events: none; }
.search-input {
  width: 100%; padding: 0.65rem 2.25rem 0.65rem 2.5rem;
  border: 1px solid var(--color-divider-light); border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.875rem; color: var(--color-text);
  background: var(--color-background-surface); outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.search-input:focus { border-color: var(--color-accent); box-shadow: 0 0 0 3px rgba(58,134,255,0.1); }
.search-clear-btn {
  position: absolute; right: 0.65rem; width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none;
  color: var(--color-text-tertiary); cursor: pointer;
  border-radius: 50%; transition: all 0.15s;
}
.search-clear-btn:hover { background: var(--color-background-active); color: var(--color-text); }
.sort-select {
  padding: 0.65rem 0.875rem;
  border: 1px solid var(--color-divider-light); border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.85rem; color: var(--color-text);
  background: var(--color-background-surface); outline: none; cursor: pointer;
}
.sort-select:focus { border-color: var(--color-accent); }

/* ─── Сетка ─── */
.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.1rem;
}

/* ─── Скелетоны ─── */
.skeleton-card { background: var(--color-background-surface); border-radius: var(--radius-card); overflow: hidden; animation: shimmer 1.5s infinite; }
.skeleton-cover { width: 100%; padding-bottom: 66%; background: var(--color-background-active); }
.skeleton-info { padding: 0.75rem; display: flex; flex-direction: column; gap: 0.45rem; }
.skeleton-line { height: 11px; background: var(--color-background-active); border-radius: 6px; }
.w-70 { width: 70%; } .w-40 { width: 40%; } .w-55 { width: 55%; }
@keyframes shimmer { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* ─── Пустое состояние ─── */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 4rem 2rem;
  text-align: center; gap: 0.65rem;
}
.empty-icon { font-size: 3.5rem; margin-bottom: 0.25rem; }
.empty-state h3 { font-size: 1.25rem; font-weight: 700; color: var(--color-text); margin: 0; }
.empty-state p { font-size: 0.9rem; color: var(--color-text-secondary); margin: 0 0 0.75rem; }
.btn-retry, .btn-create-empty {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.65rem 1.25rem;
  background: var(--color-accent); color: #fff;
  border: none; border-radius: var(--radius-lg); font-size: 0.875rem;
  font-weight: 700; cursor: pointer; transition: all 0.2s;
}
.btn-retry:hover, .btn-create-empty:hover { background: var(--color-accent-hover); transform: translateY(-1px); }

/* ─── Пагинация ─── */
.pagination { display: flex; align-items: center; justify-content: center; gap: 0.4rem; margin-top: 2rem; padding-top: 1.25rem; border-top: 1px solid var(--color-divider); }
.page-btn {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  background: var(--color-background-surface); border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem; color: var(--color-text); cursor: pointer; transition: all 0.2s;
}
.page-btn:hover:not(:disabled) { border-color: var(--color-accent); color: var(--color-accent); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-numbers { display: flex; gap: 0.2rem; }
.page-num {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  background: var(--color-background-surface); border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600;
  color: var(--color-text-secondary); cursor: pointer; transition: all 0.2s;
}
.page-num:hover:not(.dots) { border-color: var(--color-accent); color: var(--color-accent); }
.page-num.active { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
.page-num.dots { cursor: default; border: none; background: transparent; }

/* ─── Toast ─── */
.toast-notification {
  position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 0.45rem;
  padding: 0.65rem 1.1rem;
  background: var(--color-background-surface); border: 1px solid var(--color-divider-light);
  border-radius: 2rem; font-size: 0.85rem; font-weight: 600; color: var(--color-text);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3); z-index: 9999; white-space: nowrap;
}
.toast-notification svg { color: #22c55e; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(20px); }
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

/* ─── Responsive ─── */
@media (max-width: 767px) {
  .playlists-page { padding: 1rem; }
  .header-top { flex-direction: column; align-items: stretch; }
  .btn-create { justify-content: center; }
  .page-title { font-size: 1.3rem; }
  .tabs-row { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .filters-bar { flex-direction: column; }
  .sort-select { width: 100%; }
  .playlists-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem; }
}
</style>
