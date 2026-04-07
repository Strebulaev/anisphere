<template>
  <div class="kodik-import-page">
    <div class="page-header">
      <h1><SakuraIcon name="package" /> Импорт аниме из Kodik</h1>
      <p class="page-description">Импортируйте все аниме из базы Kodik API в вашу базу данных</p>
    </div>

    <!-- Статистика -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon"> <SakuraIcon name="chart" /> </div>
        <div class="stat-info">
          <div class="stat-label">Всего аниме в базе</div>
          <div class="stat-value">{{ stats.total_anime }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon"> <SakuraIcon name="play" /> </div>
        <div class="stat-info">
          <div class="stat-label">Аниме из Kodik</div>
          <div class="stat-value">{{ stats.kodik_anime }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon"> <SakuraIcon name="hourglass" /> </div>
        <div class="stat-info">
          <div class="stat-label">Последнее обновление</div>
          <div class="stat-value">{{ stats.last_update }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon"> <SakuraIcon name="check" /> </div>
        <div class="stat-info">
          <div class="stat-label">Статус</div>
          <div class="stat-value status-ok">OK</div>
        </div>
      </div>
    </div>

    <!-- Панель управления -->
    <div class="control-panel">
      <h2><SakuraIcon name="gamepad" /> Управление импортом</h2>
      
      <div class="import-options">
        <div class="option-group">
          <label class="option-label">
            <input type="checkbox" v-model="options.limitImport" />
            Ограничить количество
          </label>
          <input 
            v-if="options.limitImport" 
            type="number" 
            v-model="options.limit" 
            min="1" 
            max="1000"
            class="limit-input"
          />
        </div>
        
        <div class="option-group">
          <label class="option-label">
            <input type="checkbox" v-model="options.updateExisting" />
            Обновлять существующие
          </label>
        </div>
        
        <div class="option-group">
          <label class="option-label">
            <input type="checkbox" v-model="options.importImages" />
            Загружать постеры
          </label>
        </div>
      </div>
      
      <div class="action-buttons">
        <button 
          @click="startImport" 
          :disabled="importing"
          class="btn btn-primary"
        >
          <span v-if="!importing"><SakuraIcon name="rocket" /> Начать импорт</span>
          <span v-else><SakuraIcon name="hourglass" /> Импорт...</span>
        </button>
        
        <button 
          @click="loadFilters" 
          :disabled="loadingFilters"
          class="btn btn-secondary"
        >
          <span v-if="!loadingFilters"><SakuraIcon name="import" /> Загрузить фильтры</span>
          <span v-else><SakuraIcon name="hourglass" /> Загрузка...</span>
        </button>
      </div>
    </div>

    <!-- Прогресс импорта -->
    <div v-if="importing || progress.total > 0" class="progress-section">
      <div class="progress-header">
        <h3><SakuraIcon name="chart" /> Прогресс импорта</h3>
        <div class="progress-stats">
          <span>{{ progress.current }} / {{ progress.total }}</span>
          <span>{{ Math.round((progress.current / progress.total) * 100) }}%</span>
        </div>
      </div>
      
      <div class="progress-bar-container">
        <div 
          class="progress-bar-fill" 
          :style="{ width: (progress.current / progress.total) * 100 + '%' }"
        ></div>
      </div>
      
      <div class="progress-status">
        <p>{{ progress.status }}</p>
        <p class="progress-anime-title">{{ progress.animeTitle }}</p>
      </div>
      
      <div class="progress-details">
        <div class="detail-item">
          <span class="detail-label">Создано:</span>
          <span class="detail-value success">{{ progress.created }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Обновлено:</span>
          <span class="detail-value warning">{{ progress.updated }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Ошибок:</span>
          <span class="detail-value error">{{ progress.errors }}</span>
        </div>
      </div>
      
      <div v-if="progress.errorList.length > 0" class="error-list">
        <h4>Ошибки:</h4>
        <ul>
          <li v-for="(error, index) in progress.errorList.slice(0, 10)" :key="index">
            <strong>{{ error.title }}:</strong> {{ error.message }}
          </li>
          <li v-if="progress.errorList.length > 10">
            ... и ещё {{ progress.errorList.length - 10 }} ошибок
          </li>
        </ul>
      </div>
    </div>

    <!-- Фильтры -->
    <div v-if="filtersLoaded && filters.genres.length > 0" class="filters-section">
      <h2><SakuraIcon name="palette" /> Доступные фильтры</h2>
      
      <div class="filters-grid">
        <div class="filter-card">
          <h3>Жанры</h3>
          <div class="filter-list">
            <div v-for="genre in filters.genres.slice(0, 20)" :key="genre.title" class="filter-item">
              {{ genre.title }} <span class="count">({{ genre.count }})</span>
            </div>
          </div>
        </div>
        
        <div class="filter-card">
          <h3>Годы</h3>
          <div class="filter-list">
            <div v-for="year in filters.years.slice(0, 20)" :key="year.year" class="filter-item">
              {{ year.year }} <span class="count">({{ year.count }})</span>
            </div>
          </div>
        </div>
        
        <div class="filter-card">
          <h3>Студии</h3>
          <div class="filter-list">
            <div v-for="studio in filters.studios.slice(0, 20)" :key="studio.title" class="filter-item">
              {{ studio.title }} <span class="count">({{ studio.count }})</span>
            </div>
          </div>
        </div>
        
        <div class="filter-card">
          <h3>Переводы</h3>
          <div class="filter-list">
            <div v-for="translation in filters.translations.slice(0, 20)" :key="translation.id" class="filter-item">
              {{ translation.title }} <span class="count">({{ translation.count }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Логи -->
    <div class="logs-section">
      <h2><SakuraIcon name="history" /> Логи</h2>
      <div class="logs-container">
        <div 
          v-for="(log, index) in logs.slice(-20)" 
          :key="index"
          :class="['log-entry', `log-${log.type}`]"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

interface Log {
  time: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
}

const stats = ref({
  total_anime: 0,
  kodik_anime: 0,
  last_update: 'Нет данных'
})

const options = ref({
  limitImport: false,
  limit: 100,
  updateExisting: true,
  importImages: false
})

const importing = ref(false)
const loadingFilters = ref(false)
const filtersLoaded = ref(false)

const progress = ref({
  current: 0,
  total: 0,
  status: '',
  animeTitle: '',
  created: 0,
  updated: 0,
  errors: 0,
  errorList: [] as { title: string; message: string }[]
})

const filters = ref({
  genres: [] as { title: string; count: number }[],
  years: [] as { year: number; count: number }[],
  studios: [] as { title: string; count: number }[],
  translations: [] as { id: number; title: string; count: number }[]
})

const logs = ref<Log[]>([])

const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
  const now = new Date()
  const time = now.toLocaleTimeString('ru-RU')
  logs.value.push({ time, type, message })
}

const loadStats = async () => {
  try {
    const response = await apiClient.get('/anime/')
    stats.value.total_anime = response.data.count || 0
    stats.value.kodik_anime = response.data.results?.filter((a: any) => a.data_source === 'kodik').length || 0
    
    const now = new Date()
    stats.value.last_update = now.toLocaleDateString('ru-RU')
    
    addLog('info', `Загружена статистика: ${stats.value.total_anime} аниме в базе`)
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
    addLog('error', 'Ошибка загрузки статистики')
  }
}

const loadFilters = async () => {
  loadingFilters.value = true
  addLog('info', 'Загрузка фильтров из Kodik...')
  
  try {
    const response = await apiClient.get('/anime/kodik-filters/')
    filters.value = response.data
    filtersLoaded.value = true
    
    addLog('success', `Загружено фильтров: ${filters.value.genres.length} жанров, ${filters.value.years.length} лет`)
  } catch (error) {
    console.error('Ошибка загрузки фильтров:', error)
    addLog('error', 'Ошибка загрузки фильтров')
  } finally {
    loadingFilters.value = false
  }
}

const startImport = async () => {
  importing.value = true
  progress.value = {
    current: 0,
    total: 0,
    status: 'Подготовка...',
    animeTitle: '',
    created: 0,
    updated: 0,
    errors: 0,
    errorList: []
  }
  
  addLog('info', 'Начинаем импорт аниме из Kodik...')
  
  try {
    const payload = {
      limit: options.value.limitImport ? options.value.limit : 0
    }
    
    const response = await apiClient.post('/anime/import-from-kodik/', payload)
    
    const data = response.data
    
    progress.value.current = data.imported || 0
    progress.value.total = data.total_processed || 0
    progress.value.created = data.imported || 0
    progress.value.updated = data.updated || 0
    progress.value.errors = data.errors?.length || 0
    progress.value.errorList = data.errors || []
    progress.value.status = 'Импорт завершен'
    
    addLog('success', `Импорт завершен: ${data.imported} создано, ${data.updated} обновлено`)
    
    if (data.errors && data.errors.length > 0) {
      addLog('warning', `${data.errors.length} ошибок при импорте`)
    }
    
    // Обновляем статистику
    await loadStats()
    
  } catch (error: any) {
    console.error('Ошибка импорта:', error)
    addLog('error', `Ошибка импорта: ${error.message}`)
    progress.value.status = 'Ошибка'
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  addLog('info', 'Страница импорта загружена')
  loadStats()
})
</script>

<style scoped>
.kodik-import-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.page-description {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.stat-value.status-ok {
  color: #10b981;
}

.control-panel {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.control-panel h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1.5rem 0;
}

.import-options {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
}

.limit-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.progress-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.progress-stats {
  display: flex;
  gap: 1rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.progress-bar-container {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
  transition: width 0.3s ease;
}

.progress-status {
  margin-bottom: 1rem;
}

.progress-status p {
  margin: 0;
  color: #374151;
  font-size: 0.875rem;
}

.progress-anime-title {
  color: #6b7280;
  font-size: 0.875rem;
  font-style: italic;
}

.progress-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #222222;
  border-radius: 0.375rem;
}

.detail-label {
  color: #6b7280;
  font-size: 0.875rem;
}

.detail-value {
  font-weight: 600;
  font-size: 0.875rem;
}

.detail-value.success {
  color: #10b981;
}

.detail-value.warning {
  color: #f59e0b;
}

.detail-value.error {
  color: #ef4444;
}

.error-list {
  margin-top: 1rem;
  padding: 1rem;
  background: #fef2f2;
  border-radius: 0.375rem;
  border: 1px solid #fee2e2;
}

.error-list h4 {
  color: #dc2626;
  font-size: 0.875rem;
  margin: 0 0 0.75rem 0;
}

.error-list ul {
  margin: 0;
  padding-left: 1.25rem;
}

.error-list li {
  color: #991b1b;
  font-size: 0.875rem;
  margin-bottom: 0.375rem;
}

.filters-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.filters-section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1.5rem 0;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.filter-card {
  background: #222222;
  border-radius: 0.5rem;
  padding: 1rem;
}

.filter-card h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
}

.filter-list {
  max-height: 200px;
  overflow-y: auto;
}

.filter-item {
  font-size: 0.875rem;
  color: #374151;
  padding: 0.375rem 0;
  display: flex;
  justify-content: space-between;
}

.filter-item .count {
  color: #9ca3af;
}

.logs-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.logs-section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 1rem 0;
}

.logs-container {
  background: #1f2937;
  border-radius: 0.5rem;
  padding: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  gap: 0.75rem;
  padding: 0.375rem 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  border-bottom: 1px solid #374151;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #9ca3af;
  min-width: 80px;
}

.log-message {
  color: #e5e7eb;
}

.log-info .log-message {
  color: #60a5fa;
}

.log-success .log-message {
  color: #34d399;
}

.log-warning .log-message {
  color: #fbbf24;
}

.log-error .log-message {
  color: #f87171;
}

@media (max-width: 768px) {
  .kodik-import-page {
    padding: 1rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .import-options {
    flex-direction: column;
    gap: 1rem;
  }

  .action-buttons {
    flex-direction: column;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }
}
</style>
