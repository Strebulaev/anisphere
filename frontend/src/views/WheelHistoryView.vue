<template>
  <div class="wheel-history-view">
    <div class="page-header">
      <router-link to="/wheel" class="btn-back">← Назад к колесу</router-link>
      <h1>📊 История кручений</h1>
      <button class="btn-export" @click="exportHistory">
        📥 Экспорт
      </button>
    </div>

    <!-- Фильтры -->
    <div class="filters-section">
      <div class="filter-group">
        <label>Период:</label>
        <select v-model="filters.period" @change="loadHistory">
          <option value="all">За всё время</option>
          <option value="today">Сегодня</option>
          <option value="week">За 7 дней</option>
          <option value="month">За 30 дней</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Тип:</label>
        <select v-model="filters.type" @change="loadHistory">
          <option value="all">Все</option>
          <option value="single">Одиночные</option>
          <option value="multiple">Множественные</option>
          <option value="marathon">Марафоны</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Поиск:</label>
        <input
          v-model="filters.search"
          type="text"
          placeholder="Поиск по названию..."
          @input="debouncedSearch"
        >
      </div>
    </div>

    <!-- Статистика -->
    <div v-if="statistics" class="statistics-section">
      <div class="stat-card">
        <div class="stat-icon">🎲🎲🎲</div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.total_spins }}</div>
          <div class="stat-label">Всего кручений</div>
        </div>
      </div>

      <div class="stat-card highlight">
        <div class="stat-icon">👑</div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.most_spun_count }}</div>
          <div class="stat-label">
            Самое частое: {{ getAnimeTitle(statistics.most_spun_anime_id) }}
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.unique_anime_spun }}</div>
          <div class="stat-label">Уникальных аниме</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-info">
          <div class="stat-value">{{ statistics.last_7_days_spins }}</div>
          <div class="stat-label">За последние 7 дней</div>
        </div>
      </div>
    </div>

    <!-- История по дням -->
    <div class="history-section">
      <div
        v-for="(group, date) in groupedHistory"
        :key="date"
        class="history-day"
      >
        <h3 class="day-header">
          <span class="day-date">{{ formatDate(date) }}</span>
          <span class="day-count">{{ group.length }} кручений</span>
        </h3>

        <div class="history-list">
          <div
            v-for="item in group"
            :key="item.id"
            class="history-item"
          >
            <div class="item-time">
              {{ formatTime(item.created_at) }}
            </div>

            <div class="item-type">
              <span v-if="item.spin_type === 'single'" class="type-badge single">
                🎲 Одиночное
              </span>
              <span v-else-if="item.spin_type === 'multiple'" class="type-badge multiple">
                🎲🎲 Множественное ({{ item.items_count }})
              </span>
              <span v-else class="type-badge marathon">
                🏃 Марафон ({{ item.items_count }})
              </span>
            </div>

            <div class="item-content">
              <div v-if="item.spin_type === 'single' && item.winner" class="single-result">
                <img
                  v-if="item.winner.anime_poster"
                  :src="item.winner.anime_poster"
                  :alt="item.winner.anime_title"
                  class="result-poster"
                >
                <div class="result-info">
                  <h4>{{ item.winner.anime_title }}</h4>
                </div>
              </div>

              <div v-else-if="item.winners && item.winners.length > 0" class="multiple-results">
                <div
                  v-for="winner in item.winners"
                  :key="winner.id"
                  class="mini-card"
                >
                  <img
                    v-if="winner.anime_poster"
                    :src="winner.anime_poster"
                    :alt="winner.anime_title"
                  >
                  <span>{{ winner.anime_title }}</span>
                </div>
              </div>
            </div>

            <div class="item-actions">
              <button
                :class="['btn-action', { active: item.is_favorite }]"
                @click="toggleFavorite(item)"
                :title="item.is_favorite ? 'Убрать из избранного' : 'В избранное'"
              >
                {{ item.is_favorite ? '⭐' : '☆' }}
              </button>
              <button class="btn-action" @click="copyResult(item)" title="Копировать">
                📋
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Пустое состояние -->
      <div v-if="Object.keys(groupedHistory).length === 0 && !isLoading" class="empty-state">
        <div class="empty-icon">📊</div>
        <h2>История пуста</h2>
        <p>Покрутите колесо, чтобы увидеть историю</p>
        <router-link to="/wheel" class="btn-primary">
          🎡 К колесу
        </router-link>
      </div>

      <!-- Загрузка -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка...</p>
      </div>

      <!-- Загрузить ещё -->
      <button
        v-if="hasMore && !isLoading"
        class="btn-load-more"
        @click="loadMore"
      >
        Загрузить ещё
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { rouletteApi, type SpinHistory, type RouletteStatistics, type RouletteItem } from '@/api/roulette'
import { useToast } from '@/composables/useToast'
// Простая реализация debounce
const useDebounceFn = (fn: Function, delay: number) => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  return (...args: any[]) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

const toast = useToast()

const history = ref<SpinHistory[]>([])
const statistics = ref<RouletteStatistics | null>(null)
const animeTitles = ref<Map<number, string>>(new Map())
const isLoading = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const currentRouletteId = ref('')

const filters = ref({
  period: 'all',
  type: 'all',
  search: ''
})

// Группировка истории по дням
const groupedHistory = computed(() => {
  const grouped: Record<string, SpinHistory[]> = {}

  // Фильтрация по поиску
  let filtered = history.value
  if (filters.value.search) {
    const query = filters.value.search.toLowerCase()
    filtered = filtered.filter(item => {
      if (item.winner?.anime_title?.toLowerCase().includes(query)) return true
      if (item.winners?.some(w => w.anime_title?.toLowerCase().includes(query))) return true
      return false
    })
  }

  // Группировка по дате
  filtered.forEach(item => {
    const date = new Date(item.created_at).toDateString()
    if (!grouped[date]) {
      grouped[date] = []
    }
    grouped[date].push(item)
  })

  return grouped
})

// Дебаунс для поиска
const debouncedSearch = useDebounceFn(() => {
  loadHistory()
}, 300)

// Загрузка рулетки
const loadRoulette = async () => {
  try {
    const { data } = await rouletteApi.getRoulettes()
    if (data.length > 0 && data[0]) {
      currentRouletteId.value = data[0].id
      await loadHistory()
      await loadStatistics()
    }
  } catch (error) {
    console.error('Failed to load roulette:', error)
  }
}

// Загрузка истории
const loadHistory = async () => {
  if (!currentRouletteId.value) return

  isLoading.value = true

  try {
    const params: any = {}

    // Фильтр по периоду
    if (filters.value.period !== 'all') {
      const now = new Date()
      let dateFrom: Date

      switch (filters.value.period) {
        case 'today':
          dateFrom = new Date(now.setHours(0, 0, 0, 0))
          break
        case 'week':
          dateFrom = new Date(now.setDate(now.getDate() - 7))
          break
        case 'month':
          dateFrom = new Date(now.setDate(now.getDate() - 30))
          break
        default:
          dateFrom = new Date(0)
      }

      params.date_from = dateFrom.toISOString()
    }

    // Фильтр по типу
    if (filters.value.type !== 'all') {
      params.spin_type = filters.value.type
    }

    params.limit = 50

    const { data } = await rouletteApi.getHistory(currentRouletteId.value, params)
    history.value = data

    // Сохраняем названия аниме для статистики
    data.forEach((item: SpinHistory) => {
      if (item.winner) {
        animeTitles.value.set(item.winner.anime_id, item.winner.anime_title)
      }
      if (item.winners) {
        item.winners.forEach((w: RouletteItem) => {
          animeTitles.value.set(w.anime_id, w.anime_title)
        })
      }
    })

    hasMore.value = data.length >= 50
  } catch (error) {
    console.error('Failed to load history:', error)
    toast.error('Ошибка загрузки истории')
  } finally {
    isLoading.value = false
  }
}

// Загрузка ещё
const loadMore = async () => {
  // TODO: Реализовать пагинацию
  toast.info('Загрузка...')
}

// Загрузка статистики
const loadStatistics = async () => {
  if (!currentRouletteId.value) return

  try {
    const { data } = await rouletteApi.getStatistics(currentRouletteId.value)
    statistics.value = data
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

// Получить название аниме по ID
const getAnimeTitle = (animeId: number | null) => {
  if (!animeId) return 'N/A'
  return animeTitles.value.get(animeId) || `Аниме ${animeId}`
}

// Переключить избранное
const toggleFavorite = async (item: SpinHistory) => {
  item.is_favorite = !item.is_favorite
  // TODO: Сохранить на бэкенде
  toast.success(item.is_favorite ? 'Добавлено в избранное' : 'Удалено из избранного')
}

// Копировать результат
const copyResult = (item: SpinHistory) => {
  let text = ''

  if (item.spin_type === 'single' && item.winner) {
    text = `🎡 Колесо фортуны: ${item.winner.anime_title}`
  } else if (item.winners && item.winners.length > 0) {
    text = `🎡 Колесо фортуны (${item.items_count} аниме):\n${item.winners.map(w => `• ${w.anime_title}`).join('\n')}`
  }

  navigator.clipboard.writeText(text)
  toast.success('Скопировано')
}

// Экспорт истории
const exportHistory = () => {
  const data = JSON.stringify(history.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `wheel-history-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('История экспортирована')
}

// Форматирование даты
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = date.toDateString() === yesterday.toDateString()

  if (isToday) {
    return 'Сегодня'
  } else if (isYesterday) {
    return 'Вчера'
  } else {
    return date.toLocaleDateString('ru-RU', {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    })
  }
}

// Форматирование времени
const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadRoulette()
})
</script>

<style scoped>
.wheel-history-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.btn-back {
  color: #888;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.btn-back:hover {
  color: #fff;
}

.page-header h1 {
  color: #fff;
  font-size: 1.5rem;
  margin: 0;
  flex: 1;
}

.btn-export {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-export:hover {
  background: #3a3a3a;
  border-color: #667eea;
}

.filters-section {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  color: #888;
  font-size: 0.9rem;
}

.filter-group select,
.filter-group input {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: #667eea;
}

.statistics-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-card.highlight {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  border: 1px solid #667eea;
}

.stat-icon {
  font-size: 2rem;
}

.stat-value {
  color: #fff;
  font-size: 1.5rem;
  font-weight: 700;
}

.stat-label {
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.history-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.history-day {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

.day-header {
  background: #0f0f0f;
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
}

.day-date {
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  text-transform: capitalize;
}

.day-count {
  color: #888;
  font-size: 0.85rem;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #0a0a0a;
  display: grid;
  grid-template-columns: auto auto 1fr auto;
  gap: 1rem;
  align-items: center;
}

.history-item:last-child {
  border-bottom: none;
}

.item-time {
  color: #666;
  font-size: 0.85rem;
  min-width: 60px;
}

.type-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  white-space: nowrap;
}

.type-badge.single {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.type-badge.multiple {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.type-badge.marathon {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.item-content {
  flex: 1;
}

.single-result {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.result-poster {
  width: 50px;
  height: 71px;
  object-fit: cover;
  border-radius: 6px;
}

.result-info h4 {
  color: #fff;
  font-size: 0.95rem;
  margin: 0;
}

.multiple-results {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.mini-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #0a0a0a;
  padding: 0.5rem;
  border-radius: 6px;
}

.mini-card img {
  width: 30px;
  height: 42px;
  object-fit: cover;
  border-radius: 4px;
}

.mini-card span {
  color: #fff;
  font-size: 0.85rem;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  width: 32px;
  height: 32px;
  background: #2a2a2a;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-action:hover {
  background: #3a3a3a;
}

.btn-action.active {
  background: #fbbf24;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h2 {
  color: #fff;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #888;
  margin-bottom: 2rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  display: inline-block;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.loading-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #2a2a2a;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-load-more {
  width: 100%;
  background: #2a2a2a;
  border: none;
  color: #888;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-load-more:hover {
  background: #3a3a3a;
  color: #fff;
}

@media (max-width: 768px) {
  .wheel-history-view {
    padding: 1rem;
  }

  .filters-section {
    flex-direction: column;
    gap: 1rem;
  }

  .statistics-section {
    grid-template-columns: 1fr 1fr;
  }

  .history-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .item-time,
  .item-type {
    order: 1;
  }

  .item-content {
    order: 2;
  }

  .item-actions {
    order: 3;
    justify-content: flex-end;
  }
}
</style>
