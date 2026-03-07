<template>
  <div class="my-collection">
    <div class="collection-header">
      <h2>Моя коллекция</h2>
      <div class="stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">Всего</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.episodes_watched }}</span>
          <span class="stat-label">Эпизодов</span>
        </div>
      </div>
    </div>

    <!-- Табы статусов -->
    <div class="status-tabs">
      <button
        v-for="status in statuses"
        :key="status.value"
        @click="activeStatus = status.value"
        :class="['tab-btn', { active: activeStatus === status.value }]"
      >
        {{ status.label }}
        <span v-if="stats[status.key]" class="count">{{ stats[status.key] }}</span>
      </button>
    </div>

    <!-- Поиск -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск по коллекции..."
        @input="debouncedSearch"
      />
    </div>

    <!-- Сетка аниме -->
    <div v-if="!loading" class="anime-grid">
      <div
        v-for="item in filteredAnime"
        :key="item.id"
        class="anime-card"
      >
        <div class="poster" @click="openAnime(item.anime.id)">
          <img :src="item.anime.poster" :alt="item.anime.title_ru" />
          <div class="status-badge" :class="item.status">
            {{ getStatusLabel(item.status) }}
          </div>
          <button
            @click.stop="toggleFavorite(item)"
            :class="['favorite-btn', { active: item.is_favorite }]"
          >
            <StarIcon class="w-5 h-5" />
          </button>
          <!-- Оверлей при наведении -->
          <div class="poster-overlay">
            <button class="overlay-play" @click.stop="openAnime(item.anime.id)">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="info">
          <h3>{{ item.anime.title_ru }}</h3>
          <p class="episodes">
            {{ item.current_episode }}/{{ item.anime.episodes_count }} эпизодов
          </p>
          <div class="progress-bar">
            <div class="progress" :style="{ width: item.progress_percentage + '%' }"></div>
          </div>
          <div class="actions">
            <select
              v-model="item.status"
              @change="updateStatus(item)"
              class="status-select"
            >
              <option value="planned">В планах</option>
              <option value="started">В процессе</option>
              <option value="completed">Просмотрено</option>
              <option value="on_hold">Отложено</option>
              <option value="dropped">Брошено</option>
            </select>
            <button @click="openEpisodeSelector(item)" class="episode-btn">
              {{ item.current_episode + 1 }} эп.
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пусто -->
    <div v-if="!loading && filteredAnime.length === 0" class="empty">
      <p>Аниме с таким статусом нет</p>
      <button @click="searchAnime" class="btn-primary">
        Добавить аниме
      </button>
    </div>

    <!-- Селектор эпизодов -->
    <Modal v-if="showEpisodeSelector" @close="showEpisodeSelector = false">
      <div class="episode-selector">
        <h3>Выберите эпизод</h3>
        <div class="episode-grid">
          <button
            v-for="ep in totalEpisodes"
            :key="ep"
            @click="updateProgress(ep)"
            :class="['episode-btn', { current: ep === selectedItem?.current_episode }]"
          >
            {{ ep }}
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { StarIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import Modal from '@/components/ui/Modal.vue'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const statuses = [
  { value: 'all', label: 'Всё', key: 'total' },
  { value: 'started', label: 'В процессе', key: 'started' },
  { value: 'completed', label: 'Просмотрено', key: 'completed' },
  { value: 'on_hold', label: 'Отложено', key: 'on_hold' },
  { value: 'dropped', label: 'Брошено', key: 'dropped' },
  { value: 'planned', label: 'В планах', key: 'planned' },
  { value: 'favorites', label: 'Любимое', key: 'favorites' },
]

const activeStatus = ref('all')
const searchQuery = ref('')
const loading = ref(false)
const library = ref([])
const stats = ref({})
const showEpisodeSelector = ref(false)
const selectedItem = ref(null)
const totalEpisodes = ref(0)

let searchTimeout = null

const filteredAnime = computed(() => {
  let result = library.value

  if (activeStatus.value !== 'all') {
    if (activeStatus.value === 'favorites') {
      result = result.filter(item => item.is_favorite)
    } else {
      result = result.filter(item => item.status === activeStatus.value)
    }
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(item =>
      item.anime.title_ru.toLowerCase().includes(query) ||
      item.anime.title_en.toLowerCase().includes(query)
    )
  }

  return result
})

const getStatusLabel = (status) => {
  const statusMap = {
    started: 'В процессе',
    completed: 'Просмотрено',
    on_hold: 'Отложено',
    dropped: 'Брошено',
    planned: 'В планах',
  }
  return statusMap[status] || status
}

const loadLibrary = async () => {
  loading.value = true
  try {
    const response = await api.get('/users/library/')
    library.value = response.data

    // Загружаем статистику
    const statsResponse = await api.get('/users/library/statistics/')
    stats.value = statsResponse.data
  } catch (error) {
    console.error('Ошибка загрузки коллекции:', error)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // Поиск уже происходит через computed
  }, 300)
}

const updateStatus = async (item) => {
  try {
    await api.patch(`/users/library/${item.id}/`, { status: item.status })
  } catch (error) {
    console.error('Ошибка обновления статуса:', error)
  }
}

const openEpisodeSelector = (item) => {
  selectedItem.value = item
  totalEpisodes.value = item.anime.episodes_count
  showEpisodeSelector.value = true
}

const updateProgress = async (episode) => {
  try {
    const response = await api.post(`/users/library/${selectedItem.value.id}/update_progress/`, {
      episode: episode
    })

    // Обновляем данные
    const index = library.value.findIndex(item => item.id === selectedItem.value.id)
    if (index !== -1) {
      library.value[index] = response.data
    }

    showEpisodeSelector.value = false
  } catch (error) {
    console.error('Ошибка обновления прогресса:', error)
  }
}

const toggleFavorite = async (item) => {
  try {
    const response = await api.post(`/users/library/${item.id}/mark_favorite/`)
    item.is_favorite = response.data.is_favorite
  } catch (error) {
    console.error('Ошибка обновления избранного:', error)
  }
}

const openAnime = (animeId) => {
  router.push(`/anime/${animeId}`)
}

const searchAnime = () => {
  router.push('/anime')
}

onMounted(() => {
  loadLibrary()
})
</script>

<style scoped>
.my-collection {
  padding: var(--space-5);
}

.collection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.collection-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.stats {
  display: flex;
  gap: var(--space-5);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.status-tabs {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-5);
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  border: none;
  background: var(--surface-3);
  border-radius: var(--radius-full);
  cursor: pointer;
  white-space: nowrap;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  transition: all var(--duration-base);
}

.tab-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--accent);
  color: white;
}

.count {
  background: rgba(0, 0, 0, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: 5px;
}

.search-bar {
  margin-bottom: var(--space-5);
}

.search-bar input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  background: var(--surface-2);
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--duration-base);
}

.search-bar input:focus {
  border-color: var(--accent);
}

.search-bar input::placeholder {
  color: var(--text-tertiary);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-4);
}

.anime-card {
  background: var(--surface-3);
  border-radius: var(--radius-card);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  transition: transform var(--duration-slow) var(--ease-out), box-shadow var(--duration-slow) var(--ease-out);
}

.anime-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.poster {
  position: relative;
  aspect-ratio: 2/3;
  overflow: hidden;
  cursor: pointer;
  background: var(--surface-4);
}

.poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.anime-card:hover .poster img {
  transform: scale(1.04);
}

/* Оверлей при наведении */
.poster-overlay {
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
  transition: opacity var(--duration-base) var(--ease-out);
  z-index: 10;
}

.anime-card:hover .poster-overlay {
  opacity: 1;
}

/* Квадратная синяя кнопка с анимацией распыления */
.overlay-play {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  background: var(--accent);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding-left: 4px;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: scale(0.6);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}

.anime-card:hover .overlay-play {
  transform: scale(1);
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}

.overlay-play:hover {
  transform: scale(1.15) !important;
  background: var(--accent-hover);
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.status-badge {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  color: white;
}

.status-badge.started { background: var(--status-watching); }
.status-badge.completed { background: var(--status-completed); }
.status-badge.on_hold { background: var(--status-onhold); }
.status-badge.dropped { background: var(--status-dropped); }
.status-badge.planned { background: var(--status-planned); }

.favorite-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  width: 32px;
  height: 32px;
  background: rgba(8, 8, 9, 0.8);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base);
  backdrop-filter: blur(8px);
  color: var(--text-tertiary);
}

.favorite-btn:hover {
  transform: scale(1.1);
  background: var(--accent);
}

.favorite-btn.active {
  color: var(--warning);
  background: rgba(251, 191, 36, 0.2);
}

.info {
  padding: var(--space-2) var(--space-3) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.info h3 {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episodes {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.progress-bar {
  height: 3px;
  background: var(--surface-5);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress {
  height: 100%;
  background: var(--accent);
  transition: width var(--duration-slow) var(--ease-out);
}

.actions {
  display: flex;
  gap: var(--space-2);
}

.status-select {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  background: var(--surface-4);
  color: var(--text-primary);
}

.episode-btn {
  padding: 6px 12px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--duration-base);
}

.episode-btn:hover {
  background: var(--accent-hover);
}

.empty {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.btn-primary {
  padding: var(--space-3) var(--space-6);
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  margin-top: var(--space-5);
  transition: background var(--duration-base);
}

.btn-primary:hover {
  background: var(--accent-hover);
}

.episode-selector {
  padding: var(--space-5);
}

.episode-selector h3 {
  margin: 0 0 var(--space-5);
  color: var(--text-primary);
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: var(--space-2);
  max-height: 400px;
  overflow-y: auto;
}

.episode-grid .episode-btn {
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.episode-grid .episode-btn:hover {
  background: var(--surface-4);
}

.episode-grid .episode-btn.current {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}
</style>
