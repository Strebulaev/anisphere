<template>
  <div class="anime-detail">
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
              v-if="anime.poster" 
              :src="getPosterUrl(anime.poster)" 
              :alt="anime.title_ru || anime.title_en"
              class="poster-image"
            />
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
                  class="genre-tag-large clickable"
                  @click="navigateToGenre(genre)"
                  :title="`Смотреть аниме в жанре ${genre.name}`"
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
                </svg>
                Студия:
              </span>
              <div class="studios-list">
                <router-link
                  v-for="studio in anime.studios"
                  :key="studio.id"
                  :to="`/studios/${studio.slug}`"
                  class="studio-tag studio-tag-link"
                  :title="`Перейти на страницу студии ${studio.name}`"
                >
                  🏢 {{ studio.name }}
                </router-link>
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
              <button class="btn btn-outline" @click="openPlaylistModal">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                </svg>
                В плейлист
              </button>
              <button class="btn btn-outline discuss-btn" @click="handleDiscuss" :disabled="discussLoading">
                <svg v-if="discussLoading" class="spin-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                {{ discussLoading ? 'Загрузка...' : 'Обсудить' }}
              </button>
              <AddToFavoriteButton
                :anime-id="anime.id"
                :anime-title="anime.title_ru"
                :anime-poster="anime.poster || undefined"
              />
            </div>
          </div>
        </div>

        <PlaylistSelectModal
          :show="showPlaylistModal"
          :anime="anime as any"
          :playlists="userPlaylists"
          :is-loading="loadingPlaylists"
          @close="showPlaylistModal = false"
          @save="onAddedToPlaylist"
          @create-playlist="handleCreatePlaylist"
        />

        <!-- Модалка создания плейлиста -->
        <Teleport to="body">
          <Transition name="psm-anim">
            <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false" style="position:fixed;inset:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;z-index:10001;padding:1rem;">
              <div style="background:var(--surface-2);border-radius:1rem;max-width:420px;width:100%;padding:1.5rem;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);display:flex;flex-direction:column;gap:1rem;">
                <h3 style="margin:0;font-size:1.1rem;font-weight:700;color:var(--text-primary);">Новый плейлист</h3>
                <input
                  v-model="newPlaylistTitle"
                  placeholder="Название плейлиста"
                  @keydown.enter="saveNewPlaylist"
                  style="height:38px;padding:0 12px;background:var(--surface-3);border:1px solid var(--border-subtle);border-radius:var(--radius-md);color:var(--text-primary);font-size:var(--text-sm);outline:none;width:100%;box-sizing:border-box;"
                />
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:var(--text-sm);color:var(--text-secondary);">
                  <input type="checkbox" v-model="newPlaylistPublic" />
                  Публичный
                </label>
                <div style="display:flex;gap:8px;justify-content:flex-end;">
                  <button @click="showCreateModal = false" style="height:36px;padding:0 16px;background:var(--surface-4);color:var(--text-secondary);border:1px solid var(--border-subtle);border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);">Отмена</button>
                  <button @click="saveNewPlaylist" :disabled="!newPlaylistTitle.trim() || creatingPlaylist" style="height:36px;padding:0 16px;background:var(--accent);color:white;border:none;border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);font-weight:600;" :style="{ opacity: !newPlaylistTitle.trim() || creatingPlaylist ? '0.5' : '1' }">{{ creatingPlaylist ? 'Создание...' : 'Создать' }}</button>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>

        <ImageLightbox
          :show="showLightbox"
          :images="lightboxImages"
          :initial-index="lightboxInitialIndex"
          @close="closeLightbox"
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
            >
              <img
                :src="getMediaUrl(screenshot.url) || screenshot.url"
                :alt="`Скриншот ${index + 1}`"
                class="screenshot-image"
                @click.stop="openLightbox(index)"
              >
              <div class="screenshot-overlay" @click.stop="openLightbox(index)">
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

        <!-- Франшиза: другие части -->
        <div v-if="franchise" class="franchise-section">
          <h3 class="franchise-section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="8" height="8"/><rect x="14" y="2" width="8" height="8"/>
              <rect x="2" y="14" width="8" height="8"/><rect x="14" y="14" width="8" height="8"/>
            </svg>
            Франшиза «{{ franchise.name }}»
            <router-link :to="`/franchise/${franchise.id}`" class="franchise-link-all">Все части →</router-link>
          </h3>
          <div class="franchise-entries">
            <div
              v-for="entry in franchise.entries"
              :key="entry.id"
              :class="['franchise-entry', { 'is-current': entry.id === anime!.id }]"
              @click="entry.id !== anime!.id && $router.push(`/anime/${entry.id}`)"
            >
              <div class="fe-poster">
                <img
                  v-if="entry.poster_image_url || entry.poster_url"
                  :src="getMediaUrl(entry.poster_image_url) || getMediaUrl(entry.poster_url)"
                  :alt="entry.title_ru"
                  class="fe-poster-img"
                />
                <div v-else class="fe-poster-empty">?</div>
                <span class="fe-kind" :class="`fek-${entry.kind}`">{{ kindLabel(entry.kind) }}</span>
                <div v-if="entry.id === anime!.id" class="fe-current-badge">Сейчас</div>
              </div>
              <div class="fe-info">
                <span class="fe-title">{{ entry.title_ru || entry.title_en }}</span>
                <span class="fe-meta">
                  <span v-if="entry.year">{{ entry.year }}</span>
                  <span v-if="entry.score" class="fe-score">★ {{ Number(entry.score).toFixed(1) }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ══════════════════════════════════════════════
             СЕКЦИЯ ОЗВУЧЕК
        ══════════════════════════════════════════════ -->
        <div class="dubs-section">
          <div class="dubs-header">
            <h3 class="dubs-title">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              Озвучки
              <span v-if="!loadingDubs && filteredTranslations.length > 0" class="dubs-count">{{ filteredTranslations.length }}</span>
            </h3>

            <!-- Фильтры по типу -->
            <div class="dubs-filters">
              <button
                v-for="f in dubFilters"
                :key="f.value"
                class="dubs-filter-btn"
                :class="{ active: dubFilter === f.value }"
                @click="dubFilter = f.value"
              >
                {{ f.label }}
                <span v-if="f.value !== 'all'" class="filter-count">{{ getDubCount(f.value) }}</span>
              </button>
            </div>
          </div>

          <!-- Загрузка -->
          <div v-if="loadingDubs" class="dubs-loading">
            <div class="dub-skeleton" v-for="i in 4" :key="i"></div>
          </div>

          <!-- Список озвучек -->
          <div v-else-if="filteredTranslations.length > 0" class="dubs-list">
            <div
              v-for="t in filteredTranslations"
              :key="t.id"
              class="dub-item"
              @click="startWatchingWithTranslation(t)"
            >
              <div class="dub-avatar">
                <img v-if="getTranslationAvatar(t)" :src="getTranslationAvatar(t)" :alt="t.name" />
                <span v-else>{{ getInitials(t.name) }}</span>
              </div>
              <div class="dub-info">
                <span class="dub-name">{{ t.name }}</span>
                <div class="dub-meta">
                  <span class="dub-tag" :class="`tag-${t.type}`">{{ getTypeLabel(t.type) }}</span>
                  <span v-if="t.quality" class="dub-tag tag-quality">{{ t.quality }}</span>
                  <span v-if="t.episodes_done" class="dub-tag tag-ep">{{ t.episodes_done }} эп.</span>
                </div>
              </div>
              <div class="dub-action">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- Пусто -->
          <div v-else-if="!loadingDubs" class="dubs-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
            <p>{{ dubFilter === 'all' ? 'Озвучки не найдены' : 'По этому фильтру ничего нет' }}</p>
            <button v-if="dubFilter !== 'all'" class="dubs-reset-btn" @click="dubFilter = 'all'">Сбросить фильтр</button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import apiClient, { getMediaUrl } from '@/api/client'
  import { PlaylistSelectModal, ImageLightbox } from '@/components/Modals'
  import { AddToFavoriteButton } from '@/components/Buttons'
  import playlistsApi from '@/api/playlists'
  import { getTranslationAvatarUrl } from '@/utils/translationAvatars'
  import { animeDiscussionsApi } from '@/api/animeDiscussions'
  import { useToast } from '@/composables/useToast'
  
  interface Genre {
    id: number
    name: string
    slug: string
  }

  interface Studio {
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
    poster: string | null
    poster_url: string | null
    trailer_url: string | null
    screenshots: {url: string}[] | null
    genres: Genre[]
    studios?: Studio[]
    shikimori_id?: number
    mal_id?: number
  }

  interface FranchiseEntry {
    id: number
    title_ru: string
    title_en: string
    kind: string
    year: number | null
    score: number | null
    poster_url: string
    poster_image_url: string
    franchise_order: number
  }
  interface FranchiseDetail {
    id: number
    name: string
    entries: FranchiseEntry[]
  }

  interface Translation {
    id: number | string
    name: string
    type: string
    quality: string
    episodes_done: number
    kodik_link?: string
    is_custom?: boolean
  }

  const route = useRoute()
  const router = useRouter()

  const anime = ref<Anime | null>(null)
  const franchise = ref<FranchiseDetail | null>(null)
  const translations = ref<Translation[]>([])

  const showPlaylistModal = ref(false)
  const showCreateModal = ref(false)
  const newPlaylistTitle = ref('')
  const newPlaylistPublic = ref(false)
  const creatingPlaylist = ref(false)
  const discussLoading = ref(false)
  const showLightbox = ref(false)
  const lightboxImages = ref<string[]>([])
  const lightboxInitialIndex = ref(0)
  const loading = ref(true)
  const loadingDubs = ref(false)
  const loadingPlaylists = ref(false)
  const userPlaylists = ref<any[]>([])
  const error = ref<string | null>(null)

  // Фильтрация озвучек
  type DubFilterType = 'all' | 'voice' | 'subtitles' | 'raw'
  const dubFilter = ref<DubFilterType>('all')
  const dubFilters: { value: DubFilterType; label: string }[] = [
    { value: 'all',       label: 'Все' },
    { value: 'voice',     label: 'Озвучка' },
    { value: 'subtitles', label: 'Субтитры' },
    { value: 'raw',       label: 'Оригинал' },
  ]

  const filteredTranslations = computed(() => {
    if (dubFilter.value === 'all') return translations.value
    return translations.value.filter(t => t.type === dubFilter.value)
  })

  const getDubCount = (type: string) => {
    return translations.value.filter(t => t.type === type).length
  }

  const canWatch = computed(() => {
    if (!anime.value) return false
    return !!(anime.value.shikimori_id || anime.value.episodes)
  })

  const getTypeLabel = (type: string) => ({
    voice: 'Озвучка',
    subtitles: 'Субтитры',
    raw: 'Оригинал',
  }[type] || type)

  const getTranslationAvatar = (t: Translation): string | undefined => {
    return getTranslationAvatarUrl(t.name)
  }

  const getInitials = (name: string | undefined | null) => {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  }

  const getStatusText = (status: string) => ({
    'ongoing': 'Онгоинг',
    'finished': 'Завершён',
    'announced': 'Анонсирован',
    'released': 'Вышедший'
  }[status] || status)
  
  const getStatusClass = (status: string) => ({
    'ongoing': 'status-ongoing',
    'finished': 'status-finished',
    'announced': 'status-announced',
    'released': 'status-released'
  }[status] || '')
  
  const fetchAnime = async () => {
    try {
      const animeId = route.params.id
      const response = await apiClient.get(`/anime/${animeId}/`)
      anime.value = response.data
      loading.value = false
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Не удалось загрузить аниме'
      loading.value = false
    }
  }
    
  const fetchDubs = async () => {
    if (!anime.value?.id) return
    loadingDubs.value = true
    try {
      // Kodik-переводы
      const response = await apiClient.get(`/anime/${anime.value.id}/kodik_translations/`)
      const kodikTranslations = (response.data.translations || []).map((t: any) => ({ ...t, is_custom: false }))

      // Пользовательские дабы
      let customDubs: any[] = []
      try {
        const customRes = await apiClient.get(`/anime/${anime.value.id}/custom_dubs/`)
        customDubs = (customRes.data.dubs || []).map((d: any) => ({
          ...d,
          is_custom: true,
          type: 'voice',
        }))
      } catch { /* нет пользовательских */ }

      translations.value = [...kodikTranslations, ...customDubs]
    } catch (err) {
      console.error('Ошибка загрузки озвучек:', err)
      translations.value = []
    } finally {
      loadingDubs.value = false
    }
  }

  const navigateToGenre = (genre: Genre) => {
    router.push({ path: '/anime', query: { section: 'catalog', genre_name: genre.name } })
  }

  const handleDiscuss = async () => {
    if (!anime.value || discussLoading.value) return
    discussLoading.value = true
    try {
      let discussionGroup
      try {
        discussionGroup = await animeDiscussionsApi.getDiscussionGroup(anime.value.id)
      } catch (error: any) {
        if (error.response?.status === 404) {
          discussionGroup = await animeDiscussionsApi.createDiscussionGroup(anime.value.id)
        } else {
          throw error
        }
      }
      if (!discussionGroup.user_joined) {
        discussionGroup = await animeDiscussionsApi.joinDiscussionGroup(anime.value.id)
      }
      router.push(`/chats/${discussionGroup.id}`)
    } catch (error: any) {
      console.error('Error handling discuss:', error)
    } finally {
      discussLoading.value = false
    }
  }

  const startWatching = () => {
    if (!anime.value) return
    router.push(`/anime/${anime.value.id}/watch`)
  }

  const startWatchingWithTranslation = (t: Translation) => {
    if (!anime.value) return
    router.push(`/anime/${anime.value.id}/watch`)
  }

  const openLightbox = (index: number) => {
    if (!anime.value?.screenshots) return
    lightboxImages.value = anime.value.screenshots.map(s => getMediaUrl(s.url) || s.url)
    lightboxInitialIndex.value = index
    showLightbox.value = true
  }
  
  const closeLightbox = () => {
    showLightbox.value = false
  }

  const openPlaylistModal = async () => {
    showPlaylistModal.value = true
    await fetchUserPlaylists()
  }

  const fetchUserPlaylists = async () => {
    loadingPlaylists.value = true
    try {
      const response = await playlistsApi.getMyPlaylists()
      userPlaylists.value = response.data
    } catch (e) {
      console.error('Ошибка загрузки плейлистов:', e)
    } finally {
      loadingPlaylists.value = false
    }
  }

  const onAddedToPlaylist = async (data: { animeId: number; playlistIds: number[]; note?: string }) => {
    try {
      for (const playlistId of data.playlistIds) {
        await playlistsApi.addToPlaylist({
          anime_id: data.animeId,
          playlist_id: playlistId,
          notes: data.note || ''
        })
      }
      showPlaylistModal.value = false
    } catch (e: any) {
      alert(e?.response?.data?.error || 'Ошибка при добавлении в плейлист')
    }
  }

  const handleCreatePlaylist = () => {
    showPlaylistModal.value = false
    newPlaylistTitle.value = ''
    newPlaylistPublic.value = false
    showCreateModal.value = true
  }

  const saveNewPlaylist = async () => {
    if (!newPlaylistTitle.value.trim() || creatingPlaylist.value) return
    creatingPlaylist.value = true
    try {
      await playlistsApi.createPlaylist({
        title: newPlaylistTitle.value.trim(),
        is_public: newPlaylistPublic.value
      })
      showCreateModal.value = false
      // Обновляем список и возвращаемся к модалке выбора
      await fetchUserPlaylists()
      showPlaylistModal.value = true
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Не удалось создать плейлист')
    } finally {
      creatingPlaylist.value = false
    }
  }

  const fetchFranchise = async (franchiseId: number) => {
    try {
      const res = await apiClient.get(`/anime/franchises/${franchiseId}/`)
      franchise.value = {
        id: res.data.id,
        name: res.data.name,
        entries: (res.data.entries || []).sort(
          (a: FranchiseEntry, b: FranchiseEntry) =>
            a.franchise_order - b.franchise_order || (a.year || 0) - (b.year || 0)
        )
      }
    } catch (e) {
      console.error('Ошибка загрузки франшизы:', e)
    }
  }

  const kindLabel = (kind: string) => ({
    tv: 'TV', movie: 'Фильм', ova: 'OVA', ona: 'ONA', special: 'Спешл', music: 'Клип'
  }[kind] || kind.toUpperCase())

  const getPosterUrl = (url: string | null | undefined): string | undefined => {
    if (!url) return undefined
    return getMediaUrl(url)
  }

  onMounted(async () => {
    await fetchAnime()
    if (anime.value) {
      await fetchDubs()
      const fid = (anime.value as any).franchise_id
      if (fid) await fetchFranchise(fid)
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

@keyframes spin { to { transform: rotate(360deg); } }

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
  border-radius: 1.5rem;
}

.error-icon { font-size: 4rem; margin-bottom: 1rem; }
.error-message { font-size: 1.125rem; color: #dc2626; margin-bottom: 1.5rem; font-weight: 500; }

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
  text-decoration: none;
}

/* Detail Card */
.anime-detail-card {
  background: var(--color-background-surface);
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
  transition: all 0.2s;
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
}

.rating-stars { font-size: 1.5rem; }
.rating-value { font-size: 1.5rem; font-weight: 800; color: #78350f; }

.stats-badges { display: flex; gap: 0.75rem; flex-wrap: wrap; }

.stat-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.rank-badge { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); color: #78350f; }
.popularity-badge { background: var(--color-primary); color: white; }

/* Detail Rows */
.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
}

.detail-row:last-child { border-bottom: none; }

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

.detail-value { font-size: 1rem; color: var(--color-text-primary); font-weight: 500; }

.status-badge {
  padding: 0.375rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-ongoing  { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.status-finished { background: rgba(156, 163, 175, 0.2); color: #9ca3af; }
.status-announced { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.status-released { background: rgba(34, 197, 94, 0.2); color: #22c55e; }

/* Genres */
.genres-list { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.genre-tag-large {
  padding: 0.5rem 1rem;
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.2s;
}

.genre-tag-large.clickable {
  cursor: pointer;
  user-select: none;
}

.genre-tag-large.clickable:hover {
  background: rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}

.genre-tag-large.clickable:active {
  transform: translateY(0);
}

/* Studios */
.studios-list { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.studio-tag {
  padding: 0.5rem 1rem;
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.studio-tag-link {
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.studio-tag-link:hover {
  background: rgba(139, 92, 246, 0.4);
  color: #c4b5fd;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);
}

/* External Links */
.external-links { display: flex; gap: 0.75rem; flex-wrap: wrap; }

.external-link {
  display: inline-flex;
  align-items: center;
  padding: 0.625rem 1.25rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.external-link.shikimori { background: #10b981; color: white; }
.external-link.mal { background: var(--color-primary); color: white; }

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
  transition: all 0.2s;
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
  transition: all 0.2s;
  background: var(--color-background-surface);
  color: var(--color-text-primary);
}

.btn-outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
}

.discuss-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

@keyframes spin-anim { to { transform: rotate(360deg); } }
.spin-icon { animation: spin-anim 1s linear infinite; }

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
  transition: all 0.2s;
}

.screenshot-wrapper:hover { transform: translateY(-4px); }

.screenshot-image { width: 100%; height: 100%; object-fit: cover; }

.screenshot-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.2s;
  color: white;
}

.screenshot-wrapper:hover .screenshot-overlay { opacity: 1; }

/* ══════════════════════════════════════════════
   ФРАНШИЗА
══════════════════════════════════════════════ */
.franchise-section {
  padding: 2rem;
  border-top: 1px solid var(--color-border);
}

.franchise-section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.franchise-link-all {
  margin-left: auto;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-primary);
  text-decoration: none;
  padding: 0.375rem 0.875rem;
  border: 1px solid var(--color-primary);
  border-radius: 0.75rem;
  transition: all 0.2s;
}
.franchise-link-all:hover { background: var(--color-primary); color: white; }

.franchise-entries {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  scrollbar-width: thin;
}

.franchise-entry {
  flex: 0 0 130px;
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--color-background);
  border: 2px solid transparent;
}

.franchise-entry:hover:not(.is-current) { transform: translateY(-4px); border-color: var(--color-primary); }
.franchise-entry.is-current { cursor: default; border-color: rgba(99,102,241,0.6); }

.fe-poster {
  position: relative;
  width: 100%;
  padding-bottom: 140%;
  background: var(--color-border);
  overflow: hidden;
  border-radius: 0.5rem 0.5rem 0 0;
}

.fe-poster-img {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.franchise-entry:hover .fe-poster-img { transform: scale(1.05); }

.fe-poster-empty {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; color: var(--color-text-muted);
}

.fe-kind {
  position: absolute; top: 0.375rem; left: 0.375rem;
  padding: 2px 6px;
  font-size: 10px; font-weight: 700;
  border-radius: 4px;
  background: rgba(0,0,0,0.75); color: var(--color-text-secondary);
  text-transform: uppercase;
}
.fe-kind.fek-tv     { background: var(--color-primary); color: white; }
.fe-kind.fek-movie  { background: #f59e0b; color: #000; }
.fe-kind.fek-ova    { background: #22c55e; color: white; }
.fe-kind.fek-special { background: #a855f7; color: white; }

.fe-current-badge {
  position: absolute; bottom: 0.375rem; right: 0.375rem;
  padding: 2px 7px;
  background: rgba(99,102,241,0.9); color: white;
  font-size: 10px; font-weight: 700;
  border-radius: 4px; text-transform: uppercase;
}

.fe-info { padding: 0.5rem 0.5rem 0.625rem; display: flex; flex-direction: column; gap: 0.25rem; }

.fe-title {
  font-size: 0.75rem; font-weight: 600; color: var(--color-text-primary);
  overflow: hidden;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.fe-meta { display: flex; align-items: center; gap: 0.375rem; font-size: 0.7rem; color: var(--color-text-muted); }
.fe-score { color: #fbbf24; font-weight: 600; }

/* ══════════════════════════════════════════════
   СЕКЦИЯ ОЗВУЧЕК
══════════════════════════════════════════════ */
.dubs-section {
  padding: 2rem;
  border-top: 1px solid var(--color-border);
}

.dubs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.dubs-title {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.dubs-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  background: var(--color-primary);
  color: white;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
}

/* Фильтры */
.dubs-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.dubs-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.4rem 0.875rem;
  border: 1.5px solid var(--color-border);
  border-radius: 2rem;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.dubs-filter-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.dubs-filter-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.filter-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: rgba(255,255,255,0.25);
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
}

.dubs-filter-btn:not(.active) .filter-count {
  background: var(--color-border);
  color: var(--color-text-muted);
}

/* Список озвучек */
.dubs-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.dub-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1rem;
  background: var(--color-background);
  border: 1.5px solid var(--color-border);
  border-radius: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.dub-item:hover {
  border-color: var(--color-primary);
  background: rgba(58, 134, 255, 0.05);
  transform: translateX(4px);
}

.dub-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary), #1d4ed8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  overflow: hidden;
  flex-shrink: 0;
}

.dub-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.dub-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.dub-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dub-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-wrap: wrap;
}

.dub-tag {
  padding: 0.15rem 0.5rem;
  border-radius: 5px;
  font-size: 0.72rem;
  font-weight: 600;
  background: var(--color-border);
  color: var(--color-text-muted);
}

.dub-tag.tag-voice     { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.dub-tag.tag-subtitles { background: rgba(34, 197, 94, 0.15);  color: #22c55e; }
.dub-tag.tag-raw       { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.dub-tag.tag-quality   { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
.dub-tag.tag-ep        { background: rgba(99, 102, 241, 0.12); color: #818cf8; }

.dub-action {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(58, 134, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
  transition: all 0.2s;
}

.dub-item:hover .dub-action {
  background: var(--color-primary);
  color: white;
}

/* Скелетон загрузки */
.dubs-loading {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.dub-skeleton {
  height: 64px;
  border-radius: 0.875rem;
  background: var(--color-background);
  border: 1.5px solid var(--color-border);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Пустой список */
.dubs-empty {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.dubs-empty svg { opacity: 0.4; }
.dubs-empty p { font-size: 0.95rem; margin: 0; }

.dubs-reset-btn {
  padding: 0.5rem 1.25rem;
  border: 1.5px solid var(--color-border);
  border-radius: 0.75rem;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}
.dubs-reset-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }

/* ══════════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════════ */
@media (max-width: 1024px) {
  .anime-main-info { grid-template-columns: 1fr; }
  .anime-poster-large { max-width: 350px; margin: 0 auto; }
}

@media (max-width: 768px) {
  .anime-detail { padding: 1rem 0.5rem 3rem; }
  .detail-header, .anime-main-info, .anime-description-section,
  .anime-screenshots-section, .franchise-section, .dubs-section { padding: 1.5rem; }
  .anime-title { font-size: 1.5rem; }
  .screenshots-grid { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
  .dubs-header { flex-direction: column; align-items: flex-start; }
}

@media (max-width: 480px) {
  .anime-title { font-size: 1.25rem; }
  .detail-row { flex-direction: column; gap: 0.5rem; }
  .detail-label { min-width: auto; }
  .screenshots-grid { grid-template-columns: 1fr; }
  .action-buttons .btn { flex: 1; justify-content: center; }
}
</style>
