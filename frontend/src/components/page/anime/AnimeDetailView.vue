<template>
  <div class="anime-detail">
    <!-- Modal for adding/editing dubs -->
    <AddDubModal
      :show="showAddDubModal"
      :anime-id="anime?.id || 0"
      :editing-dub="editingDub"
      @close="showAddDubModal = false"
      @dub-added="onDubAdded"
    />
    
    <div class="container detail-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner-container">
          <div class="spinner"></div>
          <div class="spinner-ring"></div>
        </div>
        <p>Загрузка информации об аниме...</p>
      </div>
    
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p class="error-message">{{ error }}</p>
        <router-link to="/anime" class="btn btn-primary back-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Назад к списку
        </router-link>
      </div>
    
      <div v-else-if="anime" class="anime-detail-card">
        <!-- Заголовок и навигация -->
        <div class="detail-header">
          <router-link to="/anime" class="back-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Все аниме
          </router-link>
          <h1 class="anime-title">{{ anime.title_ru || anime.title_en }}</h1>
          <p class="anime-title-en" v-if="anime.title_en && anime.title_en !== anime.title_ru">
            {{ anime.title_en }}
          </p>
        </div>
    
        <!-- Основная информация -->
        <div class="anime-main-info">
          <!-- Постер -->
          <div class="anime-poster-large">
            <img 
              v-if="anime.poster_url" 
              :src="anime.poster_url" 
              :alt="anime.title_ru || anime.title_en"
              class="poster-image"
            />
            <div v-else class="poster-placeholder-large">🎌</div>
          </div>
    
          <!-- Детали -->
          <div class="anime-details">
            <!-- Рейтинг и статистика -->
            <div class="rating-section" v-if="anime.score || anime.rank || anime.popularity">
              <div class="rating-badge" v-if="anime.score">
                <div class="rating-stars"></div>
                <div class="rating-value">{{ anime.score.toFixed(1) }}</div>
              </div>
              <div class="stats-badges">
                <span v-if="anime.rank" class="stat-badge rank-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                  #{{ anime.rank }} ранг
                </span>
                <span v-if="anime.popularity" class="stat-badge popularity-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                  </svg>
                  #{{ anime.popularity }} популярность
                </span>
              </div>
            </div>
            
            <div class="detail-row">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                Год:
              </span>
              <span class="detail-value">{{ anime.year || 'Не указан' }}</span>
            </div>
            
            <div class="detail-row">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                Статус:
              </span>
              <span :class="['detail-value', 'status-badge', getStatusClass(anime.status)]">
                {{ getStatusText(anime.status) }}
              </span>
            </div>
            
            <div class="detail-row">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                </svg>
                Эпизодов:
              </span>
              <span class="detail-value">{{ anime.episodes || 'Не указано' }}</span>
            </div>
    
            <!-- Жанры -->
            <div class="detail-row">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                  <line x1="7" y1="7" x2="7.01" y2="7"/>
                </svg>
                Жанры:
              </span>
              <div class="genres-list">
                <span
                  v-for="genre in anime.genres"
                  :key="genre.id"
                  class="genre-tag-large"
                >
                  {{ genre.name }}
                </span>
              </div>
            </div>
    
            <!-- Студии -->
            <div class="detail-row" v-if="anime.studios && anime.studios.length > 0">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 21h18"/>
                  <path d="M5 21V7l8-4 8 4v14"/>
                  <path d="M13 11V7"/>
                  <path d="M13 15v-2"/>
                  <path d="M13 19v-2"/>
                </svg>
                Студия:
              </span>
              <div class="studios-list">
                <span
                  v-for="studio in anime.studios"
                  :key="studio.id"
                  class="studio-tag"
                >
                  {{ studio.name }}
                </span>
              </div>
            </div>

            <!-- Внешние ссылки -->
            <div class="detail-row" v-if="anime.shikimori_id || anime.mal_id">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                Источник:
              </span>
              <div class="external-links">
                <a
                  v-if="anime.shikimori_id"
                  :href="`https://shikimori.one/animes/${anime.shikimori_id}`"
                  target="_blank"
                  class="external-link shikimori"
                >
                  Shikimori
                </a>
                <a
                  v-if="anime.mal_id"
                  :href="`https://myanimelist.net/anime/${anime.mal_id}`"
                  target="_blank"
                  class="external-link mal"
                >
                  MyAnimeList
                </a>
              </div>
            </div>

            <!-- Трейлер -->
            <div class="detail-row" v-if="trailerEmbedUrl">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="23 7 16 12 23 17 23 7"/>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
                Трейлер:
              </span>
              <a :href="anime.trailer_url || undefined" target="_blank" class="trailer-link">
                📺 Смотреть трейлер
              </a>
            </div>
    
            <!-- Кнопка просмотра -->
            <div class="detail-row" v-if="canWatch">
              <span class="detail-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Просмотр:
              </span>
              <button @click="startWatching" class="watch-button">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Смотреть
              </button>
            </div>
    
            <!-- Действия -->
            <div class="action-buttons">
              <button class="btn btn-outline" @click="showPlaylistModal = true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
                В плейлист
              </button>
              <button class="btn btn-outline discuss-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                </svg>
                Обсудить
              </button>
              <AddToFavoriteButton
                :anime-id="anime.id"
                :anime-title="anime.title_ru"
                :anime-poster="anime.poster_url || undefined"
              />
            </div>
          </div>
        </div>

        <!-- Модальное окно выбора плейлиста -->
        <PlaylistSelectModal
          :show="showPlaylistModal"
          :anime="anime as any"
          @close="showPlaylistModal = false"
          @save="onAddedToPlaylist"
          @create-playlist="showPlaylistModal = false"
        />

        <!-- Описание -->
        <div class="anime-description-section">
          <h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            Описание
          </h3>
          <p class="anime-description-full">
            {{ anime.description || 'Описание отсутствует' }}
          </p>
        </div>

        <!-- Скриншоты -->
        <div class="anime-screenshots-section" v-if="anime.screenshots && anime.screenshots.length > 0">
          <h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            Скриншоты
          </h3>
          <div class="screenshots-grid">
            <div
              v-for="(screenshot, index) in anime.screenshots"
              :key="index"
              class="screenshot-wrapper"
              @click="openLightbox(screenshot.url)"
            >
              <img
                :src="screenshot.url"
                :alt="`Скриншот ${index + 1}`"
                class="screenshot-image"
              >
              <div class="screenshot-overlay">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Разделы -->
        <div class="anime-sections">
          <!-- Где смотреть -->
          <div class="section">
            <h3>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Где смотреть?
            </h3>
            <p class="section-placeholder" v-if="!anime.playlists || anime.playlists.length === 0">
              Плейлисты с этим аниме появятся здесь
            </p>
            <div v-else class="playlists-list">
              <div 
                v-for="playlist in anime.playlists" 
                :key="playlist.id"
                class="playlist-card"
              >
                <span class="playlist-title">{{ playlist.title }}</span>
                <span class="playlist-author">@{{ playlist.user?.username }}</span>
              </div>
            </div>
          </div>
          
          <!-- Озвучки -->
          <div class="section dubs-section">
            <DubsList
              :dubs="formattedDubs"
              :loading="loadingDubs"
              :can-add-dub="true"
              :anime-id="anime?.id"
              @add-dub="addDub"
              @select-dub="selectDub"
              @play-dub="playDub"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import apiClient from '@/api/client'
  import AddDubModal from '@/components/modal/anime/AddDubModal.vue'
  import DubsList from '@/components/Dubs/DubsList.vue'
  import NavBar from '@/components/Navigation/NavBar.vue'
  import { PlaylistSelectModal } from '@/components/Modals'
  import { AddToFavoriteButton } from '@/components/Buttons'
  
  interface Dub {
    id: number
    group: {
      id: number
      name: string
      slug: string
      logo_url: string | null
    } | null
    dub_type: string
    dub_type_display?: string
    quality: string
    episodes_done: number
    total_episodes: number | null
    is_complete: boolean
    average_rating: number | null
    ratings_count: number
    external_url: string | null
    created_by?: {
      id: number
      username: string
    } | null
  }
  
  interface Playlist {
    id: number
    title: string
    user?: {
      username: string
    }
  }
  
  interface Genre {
    id: number
    name: string
    slug: string
  }
  
  interface Anime {
    id: number
    title_ru: string
    title_en: string
    title_jp: string
    description: string
    year: number | null
    status: string
    episodes: number | null
    score: number | null
    rank: number | null
    popularity: number | null
    poster_url: string | null
    poster_file?: string | null
    created_at?: string
    trailer_url: string | null
    screenshots: {url: string}[] | null
    genres: Genre[]
    studios?: Studio[]
    playlists?: Playlist[]
    shikimori_id?: number
    mal_id?: number
    data_source?: string
  }

  interface Studio {
    id: number
    name: string
    slug: string
  }

  interface DubGroup {
    id: number
    name: string
    slug: string
    description: string
    logo_url: string | null
    works_count: number
    followers_count: number
    status: string
    is_verified: boolean
    has_dub: boolean
    dub_info: Dub
  }
  
  const route = useRoute()
  const router = useRouter()
  const anime = ref<Anime | null>(null)
  const dubs = ref<Dub[]>([])
  const dubGroups = ref<DubGroup[]>([])
  const showAddDubModal = ref(false)
  const showPlaylistModal = ref(false)
  const editingDub = ref<Dub | null>(null)
  const currentUser = ref<{id: number, username: string} | null>(null)
  const loading = ref(true)
  const loadingDubs = ref(false)
  const error = ref<string | null>(null)
  const dubsError = ref<string | null>(null)

  const canWatch = computed(() => {
    if (!anime.value) return false
    return !!(anime.value.shikimori_id || anime.value.episodes)
  })

  const formattedDubs = computed(() => {
    return dubs.value.map(dub => ({
      id: dub.id,
      studio: dub.group?.name || 'Неизвестная студия',
      logo: dub.group?.logo_url || null,
      type: dub.dub_type,
      voiceActors: [],
      verified: false,
      is_official: dub.dub_type === 'official',
      latestEpisode: dub.episodes_done?.toString() || null,
      qualityRating: dub.average_rating || 0,
      external_url: dub.external_url,
      episodes_done: dub.episodes_done,
      total_episodes: dub.total_episodes,
      is_complete: dub.is_complete
    }))
  })

  const trailerEmbedUrl = computed(() => {
    if (!anime.value?.trailer_url) return null
    const url = anime.value.trailer_url
    if (url.includes('youtube.com/watch?v=')) {
      const videoId = url.split('v=')[1]?.split('&')[0]
      if (videoId) return `https://www.youtube.com/embed/${videoId}`
    } else if (url.includes('youtu.be/')) {
      const videoId = url.split('youtu.be/')[1]?.split('?')[0]
      if (videoId) return `https://www.youtube.com/embed/${videoId}`
    }
    return url
  })
  
  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      'ongoing': 'Онгоинг',
      'finished': 'Завершён',
      'announced': 'Анонсирован',
      'released': 'Вышедший'
    }
    return map[status] || status
  }
  
  const getStatusClass = (status: string) => {
    const map: Record<string, string> = {
      'ongoing': 'status-ongoing',
      'finished': 'status-finished',
      'announced': 'status-announced',
      'released': 'status-released'
    }
    return map[status] || ''
  }
  
  const getInitials = (name: string | undefined | null) => {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  }
  
  const fetchAnime = async () => {
    console.log('=== fetchAnime: начало загрузки ===')
    try {
      const animeId = route.params.id
      console.log('=== fetchAnime: запрашиваем ID:', animeId)
      
      const urlsToTry = [
        `/anime/${animeId}/`,
        `/anime/anime/${animeId}/`
      ]
      
      for (const url of urlsToTry) {
        try {
          console.log('Пробуем URL:', url)
          const response = await apiClient.get(url)
          console.log('Успех! Ответ от', url)
          anime.value = response.data
          loading.value = false
          return
        } catch (err: any) {
          console.log('Ошибка для URL', url, ':', err.response?.status)
        }
      }
      
      throw new Error('Не удалось загрузить аниме')
      
    } catch (err: any) {
      console.error('Ошибка загрузки аниме:', err)
      error.value = err.response?.data?.detail || 'Не удалось загрузить аниме'
      loading.value = false
    }
  }
    
  const fetchDubs = async () => {
    try {
      const animeId = anime.value?.id
      if (!animeId) return
      const response = await apiClient.get(`/dubs/anime/${animeId}/dubs/`)
      dubs.value = response.data
    } catch (err: any) {
      console.error('Ошибка загрузки озвучек:', err)
    }

    const animeId = anime.value?.id
    if (!animeId) return
    const response = await apiClient.get(`/dubs/anime/${animeId}/groups/`)
    dubGroups.value = response.data
  }
  
  const addDub = () => {
    showAddDubModal.value = true
  }

  const canEditDub = (dub: Dub) => {
    return currentUser.value && dub.created_by && dub.created_by.id === currentUser.value.id
  }

  const editDub = (dub: Dub) => {
    editingDub.value = dub
    showAddDubModal.value = true
  }

  const selectDub = (dub: Dub) => {
    console.log('Selected dub:', dub)
  }

  const playDub = (dub: Dub) => {
    if (dub.external_url) {
      window.open(dub.external_url, '_blank')
    } else {
      console.log('No external URL for dub:', dub)
    }
  }

  const onDubAdded = () => {
    fetchDubs()
    editingDub.value = null
  }

  const openLightbox = (url: string) => {
    window.open(url, '_blank')
  }
  
  const startWatching = () => {
    if (!anime.value) return
    router.push(`/anime/${anime.value.id}/watch`)
  }

  const onAddedToPlaylist = () => {
    showPlaylistModal.value = false
  }

  onMounted(async () => {
    await fetchAnime()
    if (anime.value) {
      await fetchDubs()
    }
  })
</script>

<style scoped>
.anime-detail {
  min-height: 100vh;
  background: var(--color-background);
  padding: 2rem 1rem 4rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-background-surface);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.spinner-container {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
}

.spinner {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring {
  position: absolute;
  width: 70%;
  height: 70%;
  top: 15%;
  left: 15%;
  border: 4px solid transparent;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1.5s linear infinite reverse;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Error State */
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--color-background-surface);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-message {
  font-size: 1.125rem;
  color: #dc2626;
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 2rem;
  background: var(--color-primary);
  border: none;
  border-radius: 1rem;
  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(58, 134, 255, 0.4);
}

/* Detail Card */
.anime-detail-card {
  background: var(--color-background-surface);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

/* Detail Header */
.detail-header {
  padding: 2rem;
  background: var(--color-background-surface);
  border-bottom: 1px solid var(--color-border);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: rgba(58, 134, 255, 0.1);
  border-radius: 0.75rem;
  color: var(--color-primary);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.back-link:hover {
  background: rgba(58, 134, 255, 0.2);
  transform: translateX(-4px);
}

.anime-title {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
  line-height: 1.2;
}

.anime-title-en {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Main Info */
.anime-main-info {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
  padding: 2rem;
}

/* Poster */
.anime-poster-large {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  aspect-ratio: 2/3;
  background: var(--color-primary);
}

.poster-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder-large {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
  color: white;
  opacity: 0.8;
}

/* Details */
.anime-details {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Rating Section */
.rating-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 1rem;
  border: 2px solid rgba(251, 191, 36, 0.2);
}

.rating-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  border-radius: 0.75rem;
  box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3);
}

.rating-stars {
  font-size: 1.5rem;
}

.rating-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #78350f;
}

.stats-badges {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.stat-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.rank-badge {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #78350f;
}

.popularity-badge {
  background: var(--color-primary);
  color: white;
}

/* Detail Rows */
.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 140px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  font-size: 1rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* Status Badge */
.status-badge {
  padding: 0.375rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-ongoing {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-finished {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.status-announced {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.status-released {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

/* Genres */
.genres-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.genre-tag-large {
  padding: 0.5rem 1rem;
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.genre-tag-large:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

/* Studios */
.studios-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.studio-tag {
  padding: 0.5rem 1rem;
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.studio-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

/* External Links */
.external-links {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.external-link {
  display: inline-flex;
  align-items: center;
  padding: 0.625rem 1.25rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}

.external-link.shikimori {
  background: #10b981;
  color: white;
}

.external-link.shikimori:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.external-link.mal {
  background: var(--color-primary);
  color: white;
}

.external-link.mal:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.4);
}

/* Trailer Link */
.trailer-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: #ef4444;
  color: white;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.trailer-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

/* Watch Button */
.watch-button {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 2rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 1rem;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.watch-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: 2px solid var(--color-border);
  border-radius: 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--color-background-surface);
  color: var(--color-text-primary);
}

.btn-outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.2);
}

/* Description Section */
.anime-description-section {
  padding: 2rem;
  border-top: 1px solid var(--color-border);
}

.anime-description-section h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1rem;
}

.anime-description-full {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

/* Screenshots Section */
.anime-screenshots-section {
  padding: 2rem;
  border-top: 1px solid var(--color-border);
}

.anime-screenshots-section h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.screenshot-wrapper {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  aspect-ratio: 16/9;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.screenshot-wrapper:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.screenshot-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.screenshot-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.3s ease;
  color: white;
}

.screenshot-wrapper:hover .screenshot-overlay {
  opacity: 1;
}

/* Sections */
.anime-sections {
  padding: 2rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section {
  background: var(--color-background);
  border-radius: 1rem;
  padding: 1.5rem;
}

.section h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1rem;
}

.section-placeholder {
  color: var(--color-text-muted);
  font-style: italic;
  text-align: center;
  padding: 2rem;
}

/* Playlists List */
.playlists-list {
  display: grid;
  gap: 0.75rem;
}

.playlist-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--color-background-surface);
  border-radius: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.playlist-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.playlist-title {
  font-weight: 600;
  color: var(--color-text-primary);
}

.playlist-author {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

/* Responsive */
@media (max-width: 1024px) {
  .anime-main-info {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .anime-poster-large {
    max-width: 350px;
    margin: 0 auto;
  }
  
  .anime-details {
    align-items: stretch;
  }
}

@media (max-width: 768px) {
  .anime-detail {
    padding: 1rem 0.5rem 3rem;
  }
  
  .detail-header {
    padding: 1.5rem;
  }
  
  .anime-title {
    font-size: 1.5rem;
  }
  
  .anime-title-en {
    font-size: 1rem;
  }
  
  .anime-main-info {
    padding: 1.5rem;
  }
  
  .anime-poster-large {
    max-width: 100%;
  }
  
  .detail-label {
    min-width: 120px;
    font-size: 0.85rem;
  }
  
  .rating-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .rating-badge {
    justify-content: center;
  }
  
  .stats-badges {
    justify-content: center;
  }
  
  .action-buttons {
    width: 100%;
  }
  
  .btn {
    flex: 1;
    justify-content: center;
  }
  
  .watch-button {
    width: 100%;
    justify-content: center;
  }
  
  .anime-description-section,
  .anime-screenshots-section,
  .anime-sections {
    padding: 1.5rem;
  }
  
  .screenshots-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (max-width: 480px) {
  .anime-title {
    font-size: 1.25rem;
  }
  
  .detail-row {
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-label {
    min-width: auto;
  }

  .screenshots-grid {
    grid-template-columns: 1fr;
  }
}
</style>