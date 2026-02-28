<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import playlistsApi, { type Playlist } from '@/api/playlists'
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'

const authStore = useAuthStore()
const router = useRouter()

const playlists = ref<Playlist[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const currentUserId = ref<number | undefined>(undefined)

// Фильтры
const searchQuery = ref('')
const sortBy = ref<'created' | 'updated' | 'name' | 'animes' | 'favorites'>('updated')
const sortOrder = ref<'asc' | 'desc'>('desc')

// Отфильтрованные плейлисты
const filteredPlaylists = computed(() => {
  let result = [...playlists.value]

  // Фильтр по поиску
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => 
      p.title.toLowerCase().includes(query) ||
      (p.description && p.description.toLowerCase().includes(query)) ||
      (p.user && p.user.username.toLowerCase().includes(query))
    )
  }

  // Сортировка
  result.sort((a, b) => {
    let comparison = 0
    
    switch (sortBy.value) {
      case 'created':
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        break
      case 'updated':
        comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
        break
      case 'name':
        comparison = a.title.localeCompare(b.title)
        break
      case 'animes':
        comparison = (a.animes_count || 0) - (b.animes_count || 0)
        break
      case 'favorites':
        comparison = (a.favorites_count || 0) - (b.favorites_count || 0)
        break
    }

    return sortOrder.value === 'asc' ? comparison : -comparison
  })

  return result
})

const loadPlaylists = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await playlistsApi.getPublicPlaylists()
    playlists.value = response.data.results || []

    // Получаем ID текущего пользователя из auth store
    if (authStore.user) {
      currentUserId.value = authStore.user.id
    }
  } catch (err: any) {
    console.error('Ошибка загрузки публичных плейлистов:', err)
    error.value = err.response?.data?.detail || 'Не удалось загрузить плейлисты'
  } finally {
    loading.value = false
  }
}

const goToPlaylist = (playlist: Playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const toggleFavorite = async (playlist: Playlist) => {
  try {
    if (playlist.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(playlist.id)
      playlist.is_favorited = false
      playlist.favorites_count = Math.max(0, playlist.favorites_count - 1)
    } else {
      await playlistsApi.addPlaylistToFavorites(playlist.id)
      playlist.is_favorited = true
      playlist.favorites_count++
    }
  } catch (error) {
    console.error('Ошибка изменения избранного:', error)
  }
}

onMounted(() => {
  loadPlaylists()
})
</script>

<template>
  <div class="public-playlists-page">
    <header class="page-header">
      <h1>Публичные плейлисты</h1>
      <p class="subtitle">Подборки аниме от сообщества</p>
    </header>

    <!-- Фильтры -->
    <div class="filters-container">
      <div class="filters">
        <div class="search-filter">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input 
            type="text" 
            placeholder="Поиск по названию, описанию или автору..." 
            v-model="searchQuery"
            class="search-input"
          />
        </div>

        <div class="sort-filter">
          <select v-model="sortBy" class="sort-select">
            <option value="updated">По дате обновления</option>
            <option value="created">По дате создания</option>
            <option value="favorites">По популярности</option>
            <option value="animes">По количеству аниме</option>
            <option value="name">По названию</option>
          </select>
          <button 
            class="sort-order-btn" 
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            :title="sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <polyline :points="sortOrder === 'asc' ? '19 12 12 5 5 12' : '19 5 12 12 5 5'"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Содержимое -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadPlaylists">Попробовать снова</button>
    </div>

    <div v-else-if="filteredPlaylists.length === 0" class="empty-state">
      <span class="icon">🌐</span>
      <h3>{{ playlists.length === 0 ? 'Нет публичных плейлистов' : 'Ничего не найдено' }}</h3>
      <p>{{ playlists.length === 0 ? 'Пока никто не создал публичный плейлист' : 'Попробуйте изменить параметры поиска' }}</p>
    </div>

    <div v-else class="playlists-grid">
      <PlaylistCard
        v-for="playlist in filteredPlaylists"
        :key="playlist.id"
        :playlist="playlist as any"
        :current-user-id="currentUserId"
        :show-favorite="true"
        @click="goToPlaylist as any"
        @toggle-favorite="toggleFavorite as any"
      />
    </div>
  </div>
</template>

<style scoped>
.public-playlists-page {
  padding: 2rem 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
}

.subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Фильтры */
.filters-container {
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-filter {
  flex: 1;
  min-width: 250px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
}

.search-icon {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text);
  font-size: 0.95rem;
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.sort-filter {
  display: flex;
  gap: 0.5rem;
}

.sort-select {
  padding: 0.75rem 1rem;
  background: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  color: var(--color-text);
  font-size: 0.95rem;
  cursor: pointer;
}

.sort-order-btn {
  padding: 0.75rem;
  background: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
}

.sort-order-btn:hover {
  background: var(--color-background-surface);
}

.loading {
  text-align: center;
  padding: 4rem 1rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e5e7eb;
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--color-text-tertiary);
}

.error {
  text-align: center;
  padding: 4rem 1rem;
}

.error p {
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
  margin-bottom: 1rem;
}

.btn-retry {
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover {
  background: var(--color-accent-hover);
}

.empty-state {
  text-align: center;
  padding: 6rem 1rem;
}

.empty-state .icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1.5rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.75rem 0;
}

.empty-state p {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: 2rem;
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }

  .search-filter {
    min-width: 100%;
  }

  .playlists-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }
}
</style>
