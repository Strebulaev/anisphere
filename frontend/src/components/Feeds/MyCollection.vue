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
  padding: 20px;
}

.collection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.status-tabs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: #f5f5f5;
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: #e0e0e0;
}

.tab-btn.active {
  background: #667eea;
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
  margin-bottom: 20px;
}

.search-bar input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.anime-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.anime-card:hover {
  transform: translateY(-5px);
}

.poster {
  position: relative;
  aspect-ratio: 2/3;
  overflow: hidden;
  cursor: pointer;
}

.poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.status-badge.started { background: #4caf50; }
.status-badge.completed { background: #2196f3; }
.status-badge.on_hold { background: #ff9800; }
.status-badge.dropped { background: #f44336; }
.status-badge.planned { background: #9c27b0; }

.favorite-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.favorite-btn:hover {
  transform: scale(1.1);
}

.favorite-btn.active {
  color: #ffc107;
}

.info {
  padding: 12px;
}

.info h3 {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
}

.episodes {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.progress-bar {
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.actions {
  display: flex;
  gap: 8px;
}

.status-select {
  flex: 1;
  padding: 6px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 12px;
}

.episode-btn {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.btn-primary {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 20px;
}

.episode-selector {
  padding: 20px;
}

.episode-selector h3 {
  margin: 0 0 20px;
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.episode-grid .episode-btn {
  padding: 12px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
}

.episode-grid .episode-btn.current {
  background: #667eea;
  color: white;
  border-color: #667eea;
}
</style>
