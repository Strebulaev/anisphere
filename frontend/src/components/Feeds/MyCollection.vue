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

    <!-- Сетка аниме через CollectionCard (с 4 кнопками) -->
    <div v-if="!loading" class="anime-grid">
      <CollectionCard
        v-for="item in filteredAnime"
        :key="item.id"
        :item="toLibraryItem(item)"
        @status-changed="loadLibrary"
        @deleted="loadLibrary"
        @rated="loadLibrary"
      />
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пусто -->
    <div v-if="!loading && filteredAnime.length === 0" class="empty">
      <p>Аниме с таким статусом нет</p>
      <button @click="router.push('/anime')" class="btn-primary">
        Добавить аниме
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import CollectionCard from '@/components/Cards/CollectionCard.vue'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const statuses = [
  { value: 'all',       label: 'Всё',          key: 'total'     },
  { value: 'started',   label: 'В процессе',   key: 'started'   },
  { value: 'completed', label: 'Просмотрено',  key: 'completed' },
  { value: 'on_hold',   label: 'Отложено',     key: 'on_hold'   },
  { value: 'dropped',   label: 'Брошено',      key: 'dropped'   },
  { value: 'planned',   label: 'В планах',     key: 'planned'   },
  { value: 'favorites', label: 'Любимое',      key: 'favorites' },
]

const activeStatus = ref('all')
const searchQuery  = ref('')
const loading      = ref(false)
const library      = ref<any[]>([])
const stats        = ref<any>({})

let searchTimeout: ReturnType<typeof setTimeout> | null = null

const filteredAnime = computed(() => {
  let result = library.value

  if (activeStatus.value !== 'all') {
    if (activeStatus.value === 'favorites') {
      result = result.filter((item: any) => item.is_favorite)
    } else {
      result = result.filter((item: any) => item.status === activeStatus.value)
    }
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter((item: any) =>
      (item.anime?.title_ru || '').toLowerCase().includes(query) ||
      (item.anime?.title_en || '').toLowerCase().includes(query)
    )
  }

  return result
})

// Преобразуем элемент из старого API в формат LibraryItem для CollectionCard
const toLibraryItem = (item: any) => ({
  id: item.id,
  anime: item.anime?.id ?? item.anime_id,
  anime_title_ru:       item.anime?.title_ru   ?? item.anime_title_ru   ?? '',
  anime_title_en:       item.anime?.title_en   ?? item.anime_title_en   ?? '',
  anime_poster:         item.anime?.poster     ?? item.anime?.poster_image_url ?? item.anime_poster ?? null,
  anime_episodes_count: item.anime?.episodes_count ?? item.anime_episodes_count ?? null,
  anime_status_display: item.anime_status_display ?? '',
  status:               item.status,
  current_episode:      item.current_episode  ?? 0,
  episodes_watched:     item.episodes_watched ?? 0,
  progress_percentage:  item.progress_percentage ?? 0,
  is_favorite:          item.is_favorite ?? false,
  rating:               item.rating      ?? null,
  added_at:             item.added_at    ?? new Date().toISOString(),
  updated_at:           item.updated_at  ?? new Date().toISOString(),
  completed_at:         item.completed_at ?? null,
  started_at:           item.started_at  ?? null,
  notes:                item.notes       ?? '',
  rewatch_count:        item.rewatch_count ?? 0,
})

const loadLibrary = async () => {
  loading.value = true
  try {
    const response = await api.get('/users/library/')
    library.value = response.data?.results ?? response.data ?? []

    const statsResponse = await api.get('/users/library/statistics/')
    stats.value = statsResponse.data
  } catch (error) {
    console.error('Ошибка загрузки коллекции:', error)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // поиск через computed
  }, 300)
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

.stat-item { text-align: center; }

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

/* Табы */
.status-tabs {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-5);
  scrollbar-width: none;
}
.status-tabs::-webkit-scrollbar { display: none; }

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
  flex-shrink: 0;
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

/* Поиск */
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
  box-sizing: border-box;
}

.search-bar input:focus { border-color: var(--accent); }
.search-bar input::placeholder { color: var(--text-tertiary); }

/* Сетка — аналогично MyCollectionView */
.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
  gap: var(--space-5);
}

/* Состояния */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-secondary);
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

.btn-primary:hover { background: var(--accent-hover); }

@media (max-width: 767px) {
  .my-collection { padding: var(--space-3); }
  .anime-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: var(--space-3); }
}
</style>
