<template>
  <div class="shared-playlist-page">
    <!-- Загрузка -->
    <div v-if="loading" class="state-center">
      <div class="spinner"></div>
      <p>Загрузка плейлиста...</p>
    </div>

    <!-- Ошибка / истекла ссылка -->
    <div v-else-if="error" class="state-center error-state">
      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <h2>{{ errorTitle }}</h2>
      <p>{{ error }}</p>
      <router-link to="/playlists" class="btn-back">К плейлистам</router-link>
    </div>

    <!-- Плейлист -->
    <div v-else-if="playlist" class="playlist-view">
      <!-- Шапка -->
      <div class="playlist-header">
        <div class="cover-wrap">
          <!-- Вертикальные постеры -->
          <div class="cover-strips" v-if="coverPosters.length">
            <div v-for="(p, i) in coverPosters" :key="i" class="cover-strip">
              <img v-if="p.url" :src="p.url" :alt="p.title" />
              <div v-else class="strip-ph">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/><path d="M8 12l3 3 5-5"/>
                </svg>
              </div>
              <div v-if="i < coverPosters.length - 1" class="strip-divider" />
            </div>
          </div>
          <div v-else class="cover-empty">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
            </svg>
          </div>
        </div>

        <div class="header-info">
          <div class="visibility-badge" :class="`vis-${playlist.visibility}`">
            <svg v-if="playlist.visibility === 'link'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
            {{ visibilityLabel }}
          </div>
          <h1 class="playlist-title">{{ playlist.title }}</h1>
          <p v-if="playlist.description" class="playlist-desc">{{ playlist.description }}</p>

          <div class="meta-row">
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              {{ playlist.items_count }} аниме
            </span>
            <span class="meta-sep">·</span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              {{ playlist.favorites_count }}
            </span>
          </div>

          <div class="author-row">
            <img v-if="authorAvatar" :src="authorAvatar" class="author-avatar" />
            <div v-else class="author-avatar-ph">{{ (playlist.user_username || '?')[0]?.toUpperCase() ?? '?' }}</div>
            <span class="author-name">@{{ playlist.user_username }}</span>
          </div>
        </div>
      </div>

      <!-- Список аниме -->
      <div class="items-list">
        <div
          v-for="item in playlist.items"
          :key="item.id"
          class="anime-item"
          @click="goToAnime(item)"
        >
          <div class="anime-poster">
            <img v-if="item.anime_poster" :src="item.anime_poster" :alt="item.anime_title" />
            <div v-else class="poster-ph">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="2" width="20" height="20" rx="2"/>
              </svg>
            </div>
          </div>
          <div class="anime-info">
            <div class="anime-title">{{ item.anime_title }}</div>
            <div class="anime-meta">
              <span v-if="item.anime_year">{{ item.anime_year }}</span>
              <span v-if="item.anime_year && item.anime_score">·</span>
              <span v-if="item.anime_score" class="anime-score"><SakuraIcon name="star" /> {{ item.anime_score }}</span>
            </div>
            <div v-if="item.notes" class="anime-notes">{{ item.notes }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import playlistsApi, { type Playlist } from '@/api/playlists'
import { getMediaUrl } from '@/api/client'

const props = defineProps<{ token: string }>()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const errorTitle = ref('Ошибка')
const playlist = ref<Playlist | null>(null)

const authorAvatar = computed(() => {
  const url = playlist.value?.user_avatar
  return url ? getMediaUrl(url) : null
})

const visibilityLabel = computed(() => {
  if (playlist.value?.visibility === 'link') return 'По ссылке'
  if (playlist.value?.visibility === 'private') return 'Приватный'
  return 'Публичный'
})

const coverPosters = computed(() => {
  if (!playlist.value) return []
  const items = playlist.value.items?.slice(0, 3) || []
  if (items.length) {
    return items.map(item => ({
      url: item.anime_poster ? getMediaUrl(item.anime_poster) : null,
      title: item.anime_title || ''
    }))
  }
  const urls = playlist.value.cover_urls?.slice(0, 3) || []
  return urls.map((url, i) => ({ url: getMediaUrl(url), title: `Аниме ${i + 1}` }))
})

const goToAnime = (item: any) => {
  const id = item.anime_id || (typeof item.anime === 'number' ? item.anime : item.anime?.id)
  if (id) router.push(`/anime/${id}`)
}

onMounted(async () => {
  try {
    const res = await playlistsApi.getPlaylistByToken(props.token)
    playlist.value = res.data
  } catch (err: any) {
    const status = err.response?.status
    if (status === 410) {
      errorTitle.value = 'Ссылка истекла'
      error.value = 'Эта ссылка больше не действительна — срок действия истёк или ссылка была отозвана.'
    } else if (status === 404) {
      errorTitle.value = 'Ссылка не найдена'
      error.value = 'Плейлист по этой ссылке не существует или был удалён.'
    } else if (status === 403) {
      errorTitle.value = 'Нет доступа'
      error.value = 'Этот плейлист приватный.'
    } else {
      errorTitle.value = 'Ошибка'
      error.value = 'Не удалось загрузить плейлист.'
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.shared-playlist-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  min-height: 100vh;
}

.state-center {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  min-height: 60vh; gap: 1rem;
  text-align: center; color: var(--color-text-secondary);
}
.state-center p { margin: 0; font-size: 0.95rem; }
.error-state svg { color: var(--color-text-tertiary); }
.error-state h2 { font-size: 1.4rem; font-weight: 700; color: var(--color-text); margin: 0; }

.spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.btn-back {
  display: inline-flex; align-items: center;
  padding: 0.6rem 1.2rem;
  background: var(--color-accent); color: #fff;
  border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600;
  text-decoration: none; transition: background 0.2s;
}
.btn-back:hover { background: var(--color-accent-hover); }

/* ─── Шапка ─── */
.playlist-header {
  display: flex; gap: 1.5rem; margin-bottom: 2rem; align-items: flex-start;
}

.cover-wrap {
  width: 160px; min-width: 160px; height: 200px;
  border-radius: 10px; overflow: hidden;
  background: var(--color-background-active);
  flex-shrink: 0;
}
.cover-strips {
  display: flex; flex-direction: column;
  width: 100%; height: 100%;
}
.cover-strip {
  position: relative; flex: 1; overflow: hidden;
  background: var(--color-background-active);
}
.cover-strip img { width: 100%; height: 100%; object-fit: cover; display: block; }
.strip-ph { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--color-text-tertiary); opacity: 0.4; }
.strip-divider { position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: rgba(255,255,255,0.5); z-index: 2; }
.cover-empty { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--color-text-tertiary); }

.header-info { flex: 1; }

.visibility-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; margin-bottom: 0.5rem;
}
.vis-public { background: rgba(34,197,94,0.15); color: #22c55e; }
.vis-private { background: rgba(239,68,68,0.15); color: #ef4444; }
.vis-link { background: rgba(58,134,255,0.15); color: #3a86ff; }

.playlist-title { font-size: 1.5rem; font-weight: 800; color: var(--color-text); margin: 0 0 0.5rem; }
.playlist-desc { font-size: 0.9rem; color: var(--color-text-secondary); margin: 0 0 0.75rem; line-height: 1.5; }

.meta-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; color: var(--color-text-tertiary); margin-bottom: 0.75rem; }
.meta-item { display: flex; align-items: center; gap: 0.3rem; }
.meta-sep { opacity: 0.5; }

.author-row { display: flex; align-items: center; gap: 0.4rem; }
.author-avatar { width: 22px; height: 22px; border-radius: 50%; object-fit: cover; }
.author-avatar-ph {
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--color-accent); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700;
}
.author-name { font-size: 0.8rem; color: var(--color-text-secondary); }

/* ─── Список ─── */
.items-list { display: flex; flex-direction: column; gap: 0.5rem; }
.anime-item {
  display: flex; gap: 0.75rem; align-items: center;
  padding: 0.6rem 0.75rem; border-radius: 8px;
  cursor: pointer; transition: background 0.15s;
}
.anime-item:hover { background: var(--color-background-surface); }

.anime-poster {
  width: 40px; height: 56px; border-radius: 4px;
  overflow: hidden; flex-shrink: 0;
  background: var(--color-background-active);
}
.anime-poster img { width: 100%; height: 100%; object-fit: cover; display: block; }
.poster-ph { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--color-text-tertiary); opacity: 0.4; }

.anime-info { flex: 1; min-width: 0; }
.anime-title { font-size: 0.9rem; font-weight: 600; color: var(--color-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.anime-meta { font-size: 0.75rem; color: var(--color-text-tertiary); display: flex; gap: 0.35rem; align-items: center; margin-top: 2px; }
.anime-score { color: var(--color-accent-orange); font-weight: 600; }
.anime-notes { font-size: 0.75rem; color: var(--color-text-secondary); margin-top: 3px; font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 600px) {
  .playlist-header { flex-direction: column; }
  .cover-wrap { width: 100%; min-width: unset; height: 140px; }
}
</style>