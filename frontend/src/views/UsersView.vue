<template>
  <div class="people-page">
    <!-- Заголовок -->
    <div class="page-header">
      <h1 class="page-title">Люди</h1>
      <p class="page-subtitle">Пользователи сообщества AnimeCore</p>
    </div>

    <!-- Фильтры и поиск -->
    <div class="filters-section">
      <!-- Табы -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="['tab-btn', { active: activeTab === tab.value }]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Поиск -->
      <div class="search-section">
        <div class="search-input-wrap">
          <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            type="text"
            placeholder="Поиск по имени..."
            class="search-input"
          />
          <button v-if="searchQuery" @click="clearSearch" class="search-clear">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton-grid">
        <div v-for="i in 12" :key="i" class="skeleton-card">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-name"></div>
          <div class="skeleton-role"></div>
        </div>
      </div>
    </div>

    <!-- Сетка карточек -->
    <div v-else-if="people.length > 0" class="people-grid">
      <router-link
        v-for="person in people"
        :key="person.id"
        :to="`/profile/${person.id}`"
        class="person-card"
      >
        <!-- Статус онлайн -->
        <div v-if="person.is_online" class="online-indicator" title="Онлайн"></div>
        
        <div class="person-avatar">
          <img
            v-if="person.avatar"
            :src="getMediaUrl(person.avatar)"
            :alt="person.display_name || person.username"
            class="avatar-image"
            @error="handleImageError"
          />
          <div v-else class="avatar-placeholder">
            {{ (person.display_name || person.username || '?')[0]?.toUpperCase() }}
          </div>
        </div>
        <div class="person-info">
          <h3 class="person-name">{{ person.display_name || person.username }}</h3>
          <p v-if="person.nickname" class="person-nickname">@{{ person.nickname }}</p>
          <div class="person-roles">
            <span class="role-tag" :class="{ online: person.is_online }">
              {{ person.is_online ? 'Онлайн' : 'Офлайн' }}
            </span>
            <span v-if="person.level" class="role-tag level">
              Уровень {{ person.level }}
            </span>
          </div>
          <p class="person-works">{{ person.playlists_count || 0 }} плейлистов</p>
        </div>
      </router-link>
    </div>

    <!-- Пустое состояние -->
    <div v-else class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
      <p>Пользователи не найдены</p>
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="loadPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <span class="pagination-info">Страница {{ currentPage }} из {{ totalPages }}</span>
      <button
        @click="loadPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getMediaUrl } from '@/api/client'
import apiClient from '@/api/client'

interface User {
  id: number
  username: string
  display_name: string | null
  nickname: string | null
  avatar: string | null
  is_online: boolean
  level: number
  playlists_count: number
  created_at: string
}

const tabs = [
  { value: '', label: 'Все' },
  { value: 'online', label: 'Онлайн' },
  { value: 'offline', label: 'Офлайн' }
]

const activeTab = ref('')
const searchQuery = ref('')
const people = ref<User[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)

let searchTimer: ReturnType<typeof setTimeout> | null = null
const pageSize = 24

const fetchPeople = async () => {
  isLoading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize,
    }

    if (activeTab.value) {
      params.status = activeTab.value
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await apiClient.get<{
      results: User[]
      count: number
    }>('/users/users/', { params })
    
    people.value = response.data.results || []
    totalCount.value = response.data.count || 0
    totalPages.value = Math.ceil(totalCount.value / pageSize)
  } catch (error) {
    console.error('Error fetching people:', error)
    people.value = []
  } finally {
    isLoading.value = false
  }
}

const loadPage = (page: number) => {
  currentPage.value = page
  fetchPeople()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    fetchPeople()
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchPeople()
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

watch(activeTab, () => {
  currentPage.value = 1
  fetchPeople()
})

onMounted(() => {
  fetchPeople()
})
</script>

<style scoped>
.people-page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Заголовок */
.page-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.25rem;
}

.page-subtitle {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Фильтры */
.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: center;
  justify-content: space-between;
}

.tabs {
  display: flex;
  gap: 0.25rem;
  background: var(--color-background-active);
  padding: 0.25rem;
  border-radius: 0.5rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--color-text);
}

.tab-btn.active {
  background: var(--color-accent);
  color: #fff;
}

.search-section {
  flex-shrink: 0;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.875rem;
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 280px;
  padding: 0.625rem 2.5rem 0.625rem 2.5rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background-surface);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.search-clear {
  position: absolute;
  right: 0.5rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.search-clear:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

/* Сетка */
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.person-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  text-decoration: none;
  transition: all 0.2s;
}

.person-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: var(--color-accent);
}

/* Индикатор онлайн */
.online-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 12px;
  height: 12px;
  background: #22c55e;
  border: 2px solid var(--color-background-surface);
  border-radius: 50%;
  z-index: 1;
}

.person-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 0.75rem;
  background: var(--color-background-active);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
}

.person-info {
  text-align: center;
  width: 100%;
}

.person-name {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.person-nickname {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0 0 0.5rem;
}

.person-roles {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.role-tag {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  background: var(--color-background-active);
  color: var(--color-text-secondary);
  border-radius: 9999px;
  font-weight: 500;
}

.role-tag.online {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.role-tag.level {
  background: rgba(58, 134, 255, 0.1);
  color: var(--color-accent);
}

.person-works {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Загрузка */
.loading-state {
  padding: 1rem 0;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.skeleton-card {
  padding: 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
}

.skeleton-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--color-background-active);
  margin: 0 auto 0.75rem;
  animation: pulse 1.5s infinite;
}

.skeleton-name {
  height: 18px;
  width: 80%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin: 0 auto 0.5rem;
  animation: pulse 1.5s infinite;
}

.skeleton-role {
  height: 14px;
  width: 50%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin: 0 auto;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Пустое состояние */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
}

.empty-state p {
  margin: 1rem 0 0;
  font-size: 1rem;
}

/* Пагинация */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-divider-light);
}

.pagination-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Адаптивность */
@media (max-width: 768px) {
  .people-page {
    padding: 1rem;
  }

  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }

  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .search-input-wrap {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .people-grid,
  .skeleton-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }

  .person-avatar {
    width: 80px;
    height: 80px;
  }
}
</style>
