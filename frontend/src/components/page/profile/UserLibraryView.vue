<template>
  <div class="user-library-page">
    <div class="library-header">
      <h1>Моя коллекция</h1>
    </div>

    <div class="library-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-button"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="tab.icon"></svg>
        {{ tab.name }}
        <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <div class="library-content">
      <!-- Хочу посмотреть -->
      <div v-if="activeTab === 'want_to_watch'" class="tab-content">
        <div class="tab-actions">
          <button @click="showAddAnimeModal = true" class="btn btn-primary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Добавить аниме
          </button>
        </div>

        <div v-if="loading" class="loading-container">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <div v-else-if="wantToWatchList.length === 0" class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>Список пуст</h3>
          <p>Добавьте аниме, которые хотите посмотреть</p>
        </div>

        <div v-else class="anime-grid">
          <div
            v-for="item in wantToWatchList"
            :key="item.anime.id"
            class="anime-card"
          >
            <div class="anime-poster-wrapper">
              <router-link :to="`/anime/${item.anime.id}`" class="anime-poster-link">
                <img :src="item.anime.poster_url" :alt="item.anime.title_ru" class="anime-poster">
                <div class="anime-overlay">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                </div>
              </router-link>
              <button @click="removeFromLibrary(item.id)" class="remove-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="anime-info">
              <router-link :to="`/anime/${item.anime.id}`" class="anime-title">
                {{ item.anime.title_ru || item.anime.title_en }}
              </router-link>
              <div class="anime-meta">
                <span v-if="item.anime.year" class="meta-item">{{ item.anime.year }}</span>
                <span class="meta-item">{{ item.anime.episodes }} эп.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- В процессе просмотра -->
      <div v-if="activeTab === 'watching'" class="tab-content">
        <div v-if="loading" class="loading-container">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <div v-else-if="watchingList.length === 0" class="empty-state">
          <div class="empty-icon">🎬</div>
          <h3>Ничего не смотрите</h3>
          <p>Начните смотреть аниме, и оно появится здесь</p>
        </div>

        <div v-else class="watching-list">
          <div
            v-for="item in watchingList"
            :key="item.anime.id"
            class="watching-item"
          >
            <div class="watching-poster">
              <router-link :to="`/anime/${item.anime.id}/watch`">
                <img :src="item.anime.poster_url" :alt="item.anime.title_ru">
                <div class="play-overlay">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                </div>
              </router-link>
            </div>
            <div class="watching-info">
              <router-link :to="`/anime/${item.anime.id}/watch`" class="watching-title">
                {{ item.anime.title_ru || item.anime.title_en }}
              </router-link>
              <div class="watching-progress">
                <div class="progress-info">
                  <span class="episode-info">Серия {{ item.last_episode }} из {{ item.anime.episodes }}</span>
                  <span class="progress-percent">{{ Math.round((item.watched_episodes / item.anime.episodes) * 100) }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: (item.watched_episodes / item.anime.episodes) * 100 + '%' }"></div>
                </div>
              </div>
              <div class="watching-actions">
                <button @click="continueWatching(item)" class="btn btn-primary btn-sm">
                  Продолжить
                </button>
                <button @click="removeFromLibrary(item.id)" class="btn btn-outline btn-sm">
                  Удалить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Просмотрено -->
      <div v-if="activeTab === 'completed'" class="tab-content">
        <div v-if="loading" class="loading-container">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <div v-else-if="completedList.length === 0" class="empty-state">
          <div class="empty-icon">✅</div>
          <h3>Пока пусто</h3>
          <p>Здесь будут аниме, которые вы посмотрели</p>
        </div>

        <div v-else class="anime-grid">
          <div
            v-for="item in completedList"
            :key="item.anime.id"
            class="anime-card completed"
          >
            <div class="anime-poster-wrapper">
              <router-link :to="`/anime/${item.anime.id}`" class="anime-poster-link">
                <img :src="item.anime.poster_url" :alt="item.anime.title_ru" class="anime-poster">
                <div class="completed-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              </router-link>
            </div>
            <div class="anime-info">
              <router-link :to="`/anime/${item.anime.id}`" class="anime-title">
                {{ item.anime.title_ru || item.anime.title_en }}
              </router-link>
              <div class="anime-meta">
                <span v-if="item.anime.year" class="meta-item">{{ item.anime.year }}</span>
                <span class="meta-item">{{ item.anime.episodes }} эп.</span>
                <span class="meta-item rating">{{ item.anime.score?.toFixed(1) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления аниме -->
    <AddToLibraryModal
      :show="showAddAnimeModal"
      @close="showAddAnimeModal = false"
      @added="onAnimeAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import AddToLibraryModal from '@/components/modal/anime/AddToLibraryModal.vue'

const router = useRouter()

const activeTab = ref('want_to_watch')
const loading = ref(false)
const showAddAnimeModal = ref(false)

const library = ref<any[]>([])
const wantToWatchList = computed(() => library.value.filter(item => item.status === 'want_to_watch'))
const watchingList = computed(() => library.value.filter(item => item.status === 'watching'))
const completedList = computed(() => library.value.filter(item => item.status === 'completed'))

const tabs = computed(() => [
  {
    id: 'want_to_watch',
    name: 'Хочу посмотреть',
    icon: '<path d="M12 1l3 6h6l-5 4 2 6-6-4-6 4 2-6-5-4h6z"/>',
    count: wantToWatchList.value.length
  },
  {
    id: 'watching',
    name: 'Смотрю сейчас',
    icon: '<circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>',
    count: watchingList.value.length
  },
  {
    id: 'completed',
    name: 'Просмотрено',
    icon: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    count: completedList.value.length
  }
])

const loadLibrary = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/library/')
    library.value = response.data.library || []
  } catch (err) {
    console.error('Ошибка загрузки библиотеки:', err)
  } finally {
    loading.value = false
  }
}

const removeFromLibrary = async (itemId: number) => {
  if (!confirm('Удалить аниме из коллекции?')) return
  
  try {
    await apiClient.delete(`/library/${itemId}/`)
    library.value = library.value.filter(item => item.id !== itemId)
  } catch (err) {
    console.error('Ошибка удаления:', err)
    alert('Не удалось удалить аниме')
  }
}

const continueWatching = (item: any) => {
  router.push(`/anime/${item.anime.id}/watch`)
}

const onAnimeAdded = () => {
  showAddAnimeModal.value = false
  loadLibrary()
}

onMounted(() => {
  loadLibrary()
})
</script>

<style scoped>
.user-library-page {
  min-height: 100vh;
  background-color: var(--color-background);
  padding: 2rem;
  color: var(--color-text);
}

.library-header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.library-header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0;
  color: var(--color-text);
}

/* Табы */
.library-tabs {
  display: flex;
  gap: 1rem;
  max-width: 1400px;
  margin: 0 auto 2rem;
  border-bottom: 1px solid var(--color-divider);
  padding-bottom: 0;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--color-text-secondary);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-button:hover {
  color: var(--color-text);
}

.tab-button.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

.tab-count {
  padding: 0.125rem 0.5rem;
  background: var(--color-background-active);
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-accent);
}

/* Контент */
.library-content {
  max-width: 1400px;
  margin: 0 auto;
}

.tab-content {
  min-height: 400px;
}

.tab-actions {
  margin-bottom: 2rem;
  display: flex;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-button);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.btn-primary {
  background: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-divider);
  color: var(--color-text);
}

.btn-outline:hover {
  background: var(--color-background-active);
  border-color: var(--color-divider-light);
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

/* Загрузка */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--color-text-secondary);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Пустое состояние */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  color: var(--color-text);
}

.empty-state p {
  margin: 0;
  color: var(--color-text-secondary);
}

/* Сетка аниме */
.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.5rem;
}

.anime-card {
  background: var(--color-background-surface);
  border-radius: var(--radius-card);
  overflow: hidden;
  transition: all 0.15s ease;
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card);
}

.anime-card.completed {
  opacity: 0.8;
}

.anime-poster-wrapper {
  position: relative;
  aspect-ratio: 2/3;
  overflow: hidden;
}

.anime-poster-link {
  display: block;
  width: 100%;
  height: 100%;
}

.anime-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.15s ease;
}

.anime-card:hover .anime-poster {
  transform: scale(1.05);
}

.anime-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.anime-card:hover .anime-overlay {
  opacity: 1;
}

.anime-overlay svg {
  color: var(--color-text);
  transform: scale(0.8);
  transition: transform 0.15s ease;
}

.anime-card:hover .anime-overlay svg {
  transform: scale(1);
}

.remove-btn {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 32px;
  height: 32px;
  background: var(--color-accent-pink);
  border: none;
  border-radius: var(--radius-button);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s ease;
}

.anime-card:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: var(--color-accent-pink-hover);
  transform: scale(1.1);
}

.completed-badge {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  width: 32px;
  height: 32px;
  background: var(--color-accent-teal);
  border-radius: var(--radius-button);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.anime-info {
  padding: 1rem;
}

.anime-title {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.anime-title:hover {
  color: var(--color-accent);
}

.anime-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
  padding: 0.125rem 0.5rem;
  background: var(--color-background);
  border-radius: 4px;
}

.meta-item.rating {
  color: var(--color-accent-orange);
  background: var(--color-background-active);
}

/* Список "Смотрю сейчас" */
.watching-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.watching-item {
  display: flex;
  gap: 1.5rem;
  background: var(--color-background-surface);
  border-radius: var(--radius-card);
  padding: 1rem;
  transition: all 0.15s ease;
}

.watching-item:hover {
  background: var(--color-background-active);
  transform: translateX(4px);
}

.watching-poster {
  position: relative;
  width: 120px;
  flex-shrink: 0;
  aspect-ratio: 2/3;
  border-radius: var(--radius-button);
  overflow: hidden;
}

.watching-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.watching-poster:hover .play-overlay {
  opacity: 1;
}

.play-overlay svg {
  color: var(--color-text);
}

.watching-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.watching-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  margin-bottom: 0.75rem;
}

.watching-title:hover {
  color: var(--color-accent);
}

.watching-progress {
  margin-bottom: 1rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.episode-info {
  color: var(--color-text-secondary);
}

.progress-percent {
  color: var(--color-accent);
  font-weight: 600;
}

.progress-bar {
  height: 6px;
  background: var(--color-background);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.watching-actions {
  display: flex;
  gap: 0.75rem;
}

/* Адаптивность */
@media (max-width: 1024px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .watching-item {
    flex-direction: column;
  }

  .watching-poster {
    width: 100%;
    max-width: 200px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .user-library-page {
    padding: 1rem;
  }

  .library-header h1 {
    font-size: 1.75rem;
  }

  .library-tabs {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tab-button {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 1rem;
  }

  .watching-actions {
    flex-direction: column;
  }

  .watching-actions .btn {
    width: 100%;
  }
}
</style>
