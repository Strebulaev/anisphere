<template>
  <div class="dubs-list-container">
    <!-- Заголовок с информацией о количестве -->
    <div class="list-header">
      <h2 class="list-title">
        Русские озвучки
        <span v-if="totalCount > 0" class="counter">({{ totalCount }})</span>
      </h2>
      
      <!-- Фильтры и поиск на мобильных устройствах -->
      <div class="mobile-controls">
        <button 
          class="filter-btn"
          @click="toggleFilters"
          aria-label="Фильтры"
        >
          <svg class="icon" viewBox="0 0 24 24">
            <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
          </svg>
          Фильтры
        </button>
        
        <div class="search-wrapper">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Найти озвучку..."
            class="search-input"
            @input="handleSearch"
          />
          <svg class="search-icon" viewBox="0 0 24 24">
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- Панель фильтров (показывается при нажатии на кнопку фильтров) -->
    <div v-if="showFilters" class="filters-panel">
      <div class="filter-group">
        <h3 class="filter-title">Тип</h3>
        <div class="filter-options">
          <button
            v-for="type in dubTypes"
            :key="type.value"
            :class="['filter-option', { active: selectedType === type.value }]"
            @click="selectType(type.value)"
          >
            {{ type.label }}
          </button>
        </div>
      </div>
      
      <div class="filter-group">
        <h3 class="filter-title">Статус</h3>
        <div class="filter-options">
          <button
            v-for="status in verificationStatuses"
            :key="status.value"
            :class="['filter-option', { active: selectedStatus === status.value }]"
            @click="selectStatus(status.value)"
          >
            <span class="status-indicator" :class="status.value"></span>
            {{ status.label }}
          </button>
        </div>
      </div>
      
      <div class="filter-actions">
        <button class="clear-filters" @click="clearFilters">
          Сбросить
        </button>
        <button class="apply-filters" @click="applyFilters">
          Применить
        </button>
      </div>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загружаем озвучки...</p>
    </div>

    <!-- Состояние пустого результата -->
    <div v-else-if="filteredDubs.length === 0" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
      </svg>
      <h3>Ничего не найдено</h3>
      <p v-if="searchQuery">
        Попробуйте изменить поисковый запрос или сбросить фильтры
      </p>
      <p v-else>
        Ещё никто не добавил озвучки для этого аниме. Будьте первым!
      </p>
      <button 
        v-if="canAddDub"
        class="add-dub-btn"
        @click="$emit('add-dub')"
      >
        <svg class="icon" viewBox="0 0 24 24">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
        Добавить озвучку
      </button>
    </div>

    <!-- Список озвучек -->
    <div v-else class="dubs-grid">
      <div
        v-for="dub in filteredDubs"
        :key="dub.id"
        class="dub-card"
        @click="$emit('select-dub', dub)"
      >
        <!-- Верхняя часть карточки -->
        <div class="card-header">
          <!-- Логотип студии -->
          <div class="dub-logo">
            <img
              v-if="dub.logo"
              :src="getLogoUrl(dub.logo)"
              :alt="dub.studio"
              class="logo-image"
            />
            <div v-else class="logo-placeholder">
              {{ getInitials(dub.studio) }}
            </div>
          </div>
          
          <!-- Информация о статусе -->
          <div class="dub-meta">
            <span 
              v-if="dub.verified" 
              class="verified-badge"
              title="Проверенная озвучка"
            >
              <svg class="verified-icon" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </span>
            <span v-if="dub.is_official" class="official-tag">
              Официальная
            </span>
          </div>
        </div>

        <!-- Основная информация -->
        <div class="card-body">
          <h3 class="dub-title">{{ dub.studio }}</h3>
          
          <div v-if="dub.voiceActors.length > 0" class="voice-actors">
            <span class="actors-label">Актёры:</span>
            <div class="actors-list">
              <span 
                v-for="actor in dub.voiceActors.slice(0, 3)"
                :key="actor.id"
                class="actor-tag"
              >
                {{ actor.name }}
              </span>
              <span v-if="dub.voiceActors.length > 3" class="more-actors">
                +{{ dub.voiceActors.length - 3 }}
              </span>
            </div>
          </div>

          <div v-if="dub.latestEpisode" class="latest-episode">
            <svg class="episode-icon" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5l-4-4 1.41-1.41L11 14.67l6.59-6.59L19 9.5l-8 7z"/>
            </svg>
            <span>Последняя серия: {{ dub.latestEpisode }}</span>
          </div>
        </div>

        <!-- Нижняя часть с действиями -->
        <div class="card-footer">
          <div class="quality-rating">
            <div class="stars">
              <span 
                v-for="n in 5"
                :key="n"
                :class="['star', { filled: n <= Math.round(dub.qualityRating) }]"
              >
                ★
              </span>
            </div>
            <span class="rating-text">{{ dub.qualityRating.toFixed(1) }}</span>
          </div>
          
          <div class="action-buttons">
            <button 
              class="play-btn"
              @click.stop="$emit('play-dub', dub)"
              aria-label="Смотреть с этой озвучкой"
            >
              <svg class="play-icon" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
            
            <button 
              class="details-btn"
              @click.stop="$emit('select-dub', dub)"
              aria-label="Подробнее"
            >
              Подробнее
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Кнопка добавления в конце списка (если есть озвучки) -->
    <div v-if="canAddDub && filteredDubs.length > 0" class="add-dub-footer">
      <button class="add-dub-floating-btn" @click="$emit('add-dub')">
        <svg class="icon" viewBox="0 0 24 24">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>
        Добавить ещё одну озвучку
      </button>
    </div>

    <!-- Пагинация (если нужно) -->
    <div v-if="showPagination" class="pagination">
      <button 
        class="pagination-btn"
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        Назад
      </button>
      
      <div class="page-numbers">
        <span 
          v-for="page in visiblePages"
          :key="page"
          :class="['page-number', { active: page === currentPage }]"
          @click="goToPage(page)"
        >
          {{ page }}
        </span>
      </div>
      
      <button 
        class="pagination-btn"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        Вперёд
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getMediaUrl } from '@/api/client'

const props = defineProps({
  dubs: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  canAddDub: {
    type: Boolean,
    default: false
  },
  animeId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits([
  'select-dub',
  'play-dub',
  'add-dub',
  'filter-changed'
])

// Реактивные данные
const searchQuery = ref('')
const selectedType = ref('all')
const selectedStatus = ref('all')
const showFilters = ref(false)
const currentPage = ref(1)
const itemsPerPage = ref(10)

// Фильтры
const dubTypes = [
  { value: 'all', label: 'Все' },
  { value: 'studio', label: 'Студии' },
  { value: 'independent', label: 'Независимые' },
  { value: 'official', label: 'Официальные' }
]

const verificationStatuses = [
  { value: 'all', label: 'Все' },
  { value: 'verified', label: 'Проверенные' },
  { value: 'unverified', label: 'Непроверенные' }
]

// Вычисляемые свойства
const totalCount = computed(() => props.dubs.length)

const filteredDubs = computed(() => {
  let result = [...props.dubs]
  
  // Поиск по названию студии и актёрам
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(dub => 
      dub.studio.toLowerCase().includes(query) ||
      dub.voiceActors.some(actor => 
        actor.name.toLowerCase().includes(query)
      )
    )
  }
  
  // Фильтрация по типу
  if (selectedType.value !== 'all') {
    result = result.filter(dub => {
      switch (selectedType.value) {
        case 'studio': return dub.type === 'studio'
        case 'independent': return dub.type === 'independent'
        case 'official': return dub.is_official
        default: return true
      }
    })
  }
  
  // Фильтрация по статусу
  if (selectedStatus.value !== 'all') {
    result = result.filter(dub => {
      if (selectedStatus.value === 'verified') return dub.verified
      if (selectedStatus.value === 'unverified') return !dub.verified
      return true
    })
  }
  
  // Сортировка: сначала проверенные, потом по рейтингу
  result.sort((a, b) => {
    if (a.verified !== b.verified) return b.verified - a.verified
    return b.qualityRating - a.qualityRating
  })
  
  return result
})

const totalPages = computed(() => 
  Math.ceil(filteredDubs.value.length / itemsPerPage.value)
)

const paginatedDubs = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredDubs.value.slice(start, end)
})

const showPagination = computed(() => totalPages.value > 1)

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  const end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Методы
const getInitials = (studioName) => {
  return studioName
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

const getLogoUrl = (logo) => {
  if (!logo) return undefined
  return getMediaUrl(logo)
}

const toggleFilters = () => {
  showFilters.value = !showFilters.value
}

const selectType = (type) => {
  selectedType.value = type
}

const selectStatus = (status) => {
  selectedStatus.value = status
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedType.value = 'all'
  selectedStatus.value = 'all'
}

const applyFilters = () => {
  showFilters.value = false
  currentPage.value = 1
  emitFilterChange()
}

const handleSearch = () => {
  currentPage.value = 1
  emitFilterChange()
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const emitFilterChange = () => {
  emit('filter-changed', {
    search: searchQuery.value,
    type: selectedType.value,
    status: selectedStatus.value,
    page: currentPage.value
  })
}

// Наблюдатели
watch([searchQuery, selectedType, selectedStatus], () => {
  currentPage.value = 1
})

// Инициализация
onMounted(() => {
  // Здесь может быть загрузка данных, если не переданы через props
})
</script>

<style scoped>
.dubs-list-container {
  width: 100%;
  margin: 0 auto;
  padding: var(--space-lg);
}

.list-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.list-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.counter {
  color: #666;
  font-weight: normal;
  font-size: 0.9em;
}

.mobile-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}

.filter-btn:hover {
  background: #e0e0e0;
}

.filter-btn .icon {
  width: 18px;
  height: 18px;
  fill: #666;
}

.search-wrapper {
  flex: 1;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.9rem;
  background: #444444;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  fill: #999;
}

.filters-panel {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filter-group {
  margin-bottom: 16px;
}

.filter-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #555;
  margin: 0 0 8px 0;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-option {
  padding: 6px 12px;
  background: #333333;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-option.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.filter-option .status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.filter-option .status-indicator.verified {
  background: #28a745;
}

.filter-option .status-indicator.unverified {
  background: #ffc107;
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.clear-filters,
.apply-filters {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-filters {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
}

.apply-filters {
  background: #007bff;
  color: white;
}

.clear-filters:hover {
  background: #e9ecef;
}

.apply-filters:hover {
  background: #0056b3;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty-icon {
  width: 64px;
  height: 64px;
  fill: #ccc;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.add-dub-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.add-dub-btn:hover {
  background: #0056b3;
}

.add-dub-btn .icon {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.add-dub-header-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
  font-size: 0.9rem;
}

.add-dub-header-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.add-dub-header-btn .icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.add-dub-footer {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.add-dub-floating-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 50px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  font-size: 0.95rem;
}

.add-dub-floating-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.add-dub-floating-btn .icon {
  width: 20px;
  height: 20px;
  fill: currentColor;
}

.dubs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.dub-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
  cursor: pointer;
}

.dub-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #007bff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.dub-logo {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  background: #f8f9fa;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
  font-size: 1rem;
}

.dub-meta {
  display: flex;
  gap: 6px;
}

.verified-badge {
  width: 24px;
  height: 24px;
  background: #28a745;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.verified-icon {
  width: 16px;
  height: 16px;
  fill: white;
}

.official-tag {
  padding: 2px 6px;
  background: #ffc107;
  color: #333;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

.card-body {
  margin-bottom: 16px;
}

.dub-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.voice-actors {
  margin-bottom: 8px;
}

.actors-label {
  font-size: 0.8rem;
  color: #666;
  margin-right: 4px;
}

.actors-list {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
}

.actor-tag {
  padding: 2px 6px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #333;
}

.more-actors {
  font-size: 0.75rem;
  color: #999;
}

.latest-episode {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: #666;
}

.episode-icon {
  width: 16px;
  height: 16px;
  fill: #28a745;
}

.card-footer {
  border-top: 1px solid #e9ecef;
  padding-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quality-rating {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stars {
  display: flex;
  gap: 2px;
}

.star {
  font-size: 0.9rem;
  color: #ccc;
}

.star.filled {
  color: #ffc107;
}

.rating-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.play-btn {
  background: #007bff;
  aspect-ratio: 1;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  font-weight: bold;
}

.play-btn:hover {
  background: #0056b3;
}

.play-icon {
  width: 20px;
  height: 20px;
  fill: white;
}

.details-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid ;
  color: #007bff;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.details-btn:hover {
  background: #007bff;
  color: white;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination-btn {
  padding: 8px 16px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn:not(:disabled):hover {
  background: #e9ecef;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-number:hover {
  background: #f0f0f0;
}

.page-number.active {
  background: #007bff;
  color: white;
}

/* Responsive design */
@media (max-width: 640px) {
  .dubs-list-container {
    padding: var(--space-sm);
  }

  .list-header {
    margin-bottom: var(--space-lg);
    gap: var(--space-md);
  }

  .list-title {
    font-size: 1.25rem;
    margin-bottom: var(--space-sm);
  }

  .counter {
    font-size: 0.8em;
  }

  .mobile-controls {
    flex-direction: column;
    gap: var(--space-sm);
    align-items: stretch;
    margin-bottom: var(--space-lg);
  }

  .search-wrapper {
    flex: none;
  }

  .filter-btn {
    justify-content: center;
    padding: var(--space-sm) var(--space-md);
    font-size: 0.85rem;
  }

  .filter-btn .icon {
    width: 16px;
    height: 16px;
  }

  .search-input {
    padding: var(--space-sm) var(--space-sm) var(--space-sm) 36px;
    font-size: 0.85rem;
  }

  .search-icon {
    width: 16px;
    height: 16px;
    left: var(--space-sm);
  }

  .filters-panel {
    padding: var(--space-md);
    margin-bottom: var(--space-lg);
  }

  .filter-group {
    margin-bottom: var(--space-md);
  }

  .filter-options {
    gap: var(--space-xs);
  }

  .filter-option {
    padding: 4px var(--space-sm);
    font-size: 0.8rem;
  }

  .filter-actions {
    margin-top: var(--space-lg);
    gap: var(--space-sm);
  }

  .dubs-grid {
    grid-template-columns: 1fr;
    gap: var(--space-md);
  }

  .dub-card {
    padding: var(--space-md);
  }

  .card-header {
    margin-bottom: var(--space-sm);
  }

  .dub-logo {
    width: 40px;
    height: 40px;
  }

  .logo-placeholder {
    font-size: 0.9rem;
  }

  .dub-meta {
    gap: 4px;
  }

  .verified-badge {
    width: 20px;
    height: 20px;
  }

  .verified-icon {
    width: 14px;
    height: 14px;
  }

  .official-tag {
    font-size: 0.65rem;
    padding: 1px 4px;
  }

  .card-body {
    margin-bottom: var(--space-md);
  }

  .dub-title {
    font-size: 1rem;
  }

  .voice-actors,
  .latest-episode {
    font-size: 0.8rem;
  }

  .actors-label {
    font-size: 0.75rem;
  }

  .actor-tag {
    font-size: 0.7rem;
    padding: 1px 4px;
  }

  .card-footer {
    padding-top: var(--space-sm);
    flex-direction: column;
    gap: var(--space-sm);
    align-items: stretch;
  }

  .quality-rating {
    justify-content: center;
  }

  .action-buttons {
    justify-content: center;
    gap: var(--space-md);
  }

  .play-btn {
    width: 36px;
    height: 36px;
  }

  .play-icon {
    width: 18px;
    height: 18px;
  }

  .details-btn {
    padding: 6px var(--space-md);
    font-size: 0.8rem;
  }
}

@media (min-width: 641px) and (max-width: 767px) {
  .dubs-list-container {
    padding: var(--space-md);
  }

  .dubs-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-lg);
  }

  .dub-card {
    padding: var(--space-lg);
  }
}

@media (min-width: 768px) {
  .mobile-controls {
    flex-direction: row;
    align-items: center;
    width: auto;
    margin-bottom: 0;
  }

  .filter-btn {
    order: 1;
  }

  .search-wrapper {
    order: 2;
    max-width: 300px;
  }

  .dubs-grid {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--space-xl);
  }

  .filters-panel {
    padding: var(--space-lg);
  }

  .filter-actions {
    flex-direction: row;
    gap: var(--space-md);
  }
}

@media (min-width: 1024px) {
  .list-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .list-title {
    margin-bottom: 0;
  }

  .dubs-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }

  .dub-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .dub-card:hover {
    transform: translateY(-2px);
  }
}

@media (min-width: 1280px) {
  .dubs-list-container {
    max-width: var(--container-5xl);
  }

  .dubs-grid {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
}
</style>