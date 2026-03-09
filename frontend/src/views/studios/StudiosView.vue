<template>
  <div class="studios-page">
    <!-- Заголовок -->
    <div class="page-header">
      <h1 class="page-title">🏢 Студии</h1>
      <p class="page-subtitle">Каталог аниме-студий — {{ totalCount }} студий</p>
    </div>

    <!-- Карусель популярных -->
    <section v-if="popularStudios.length > 0" class="popular-section">
      <h2 class="section-title">🔥 Популярные студии</h2>
      <div class="carousel-wrapper">
        <div class="carousel" ref="carouselEl">
          <router-link
            v-for="studio in popularStudios"
            :key="studio.id"
            :to="`/studios/${studio.slug}`"
            class="carousel-card"
          >
            <div class="carousel-logo">
              <img
                v-if="studio.logo_image_url"
                :src="studio.logo_image_url"
                :alt="studio.name"
                class="logo-img"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="logo-placeholder">{{ studio.name.slice(0, 2) }}</div>
            </div>
            <div class="carousel-name">{{ studio.name }}</div>
            <div class="carousel-rating">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
              {{ studio.average_rating?.toFixed(1) || '—' }}
            </div>
            <div class="carousel-count">{{ studio.total_anime }} аниме</div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Фильтры -->
    <section class="filters-section">
      <div class="filter-row">
        <div class="search-wrap">
          <svg class="search-ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input
            v-model="filters.search"
            @input="debouncedFetch"
            type="text"
            placeholder="Поиск по названию студии..."
            class="search-input"
          />
          <button v-if="filters.search" @click="clearSearch" class="search-clear-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>
      <div class="filter-row filter-selects">
        <div class="filter-group">
          <label class="filter-label">📊 Рейтинг</label>
          <select v-model="filters.min_rating" @change="applyFilters" class="filter-select">
            <option value="">Любой</option>
            <option value="4.5">4.5+</option>
            <option value="4.0">4.0+</option>
            <option value="3.5">3.5+</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">🌍 Страна</label>
          <select v-model="filters.country" @change="applyFilters" class="filter-select">
            <option value="">Все страны</option>
            <option value="Япония">Япония</option>
            <option value="Корея">Корея</option>
            <option value="Китай">Китай</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">📈 Сортировка</label>
          <select v-model="filters.ordering" @change="applyFilters" class="filter-select">
            <option value="-average_rating">По рейтингу ↓</option>
            <option value="average_rating">По рейтингу ↑</option>
            <option value="-total_anime">По кол-ву работ ↓</option>
            <option value="-subscribers_count">По подписчикам ↓</option>
            <option value="-founded_year">Новые сначала</option>
            <option value="founded_year">Старые сначала</option>
            <option value="name">По названию</option>
          </select>
        </div>
        <button @click="resetFilters" class="reset-btn">Сбросить</button>
      </div>
    </section>

    <!-- Список студий -->
    <section class="studios-list-section">
      <div class="list-header">
        <h2 class="section-title">📋 Все студии ({{ totalCount }})</h2>
      </div>

      <!-- Скелетон загрузки -->
      <div v-if="isLoading" class="skeleton-list">
        <div v-for="i in 8" :key="i" class="skeleton-item">
          <div class="sk-logo"></div>
          <div class="sk-info">
            <div class="sk-title"></div>
            <div class="sk-meta"></div>
            <div class="sk-rating"></div>
          </div>
        </div>
      </div>

      <!-- Список -->
      <div v-else-if="studios.length > 0" class="studios-list">
        <div
          v-for="studio in studios"
          :key="studio.id"
          class="studio-item"
        >
          <router-link :to="`/studios/${studio.slug}`" class="studio-item-logo-link">
            <div class="studio-logo">
              <img
                v-if="studio.logo_image_url"
                :src="studio.logo_image_url"
                :alt="studio.name"
                class="studio-logo-img"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="studio-logo-placeholder">{{ studio.name.slice(0, 2) }}</div>
            </div>
          </router-link>

          <div class="studio-info">
            <div class="studio-info-top">
              <router-link :to="`/studios/${studio.slug}`" class="studio-name-link">
                <h3 class="studio-name">{{ studio.name }}</h3>
                <span v-if="studio.is_verified" class="verified-badge" title="Верифицирована">✓</span>
              </router-link>
              <div class="studio-actions">
                <button
                  @click.prevent="toggleSubscribe(studio)"
                  :class="['subscribe-btn', { subscribed: studio.is_subscribed }]"
                >
                  {{ studio.is_subscribed ? '✓ Подписан' : '+ Подписаться' }}
                </button>
                <span class="watchers">
                  👁 {{ formatCount(studio.subscribers_count) }}
                </span>
              </div>
            </div>

            <div class="studio-meta">
              <span>🌍 {{ studio.country }}</span>
              <span v-if="studio.founded_year">📅 {{ studio.founded_year }}</span>
              <span>🎬 {{ studio.total_anime }} аниме</span>
            </div>

            <div class="studio-rating">
              <div class="stars-row">
                <span v-for="s in 5" :key="s" class="star" :class="{ filled: s <= Math.round(studio.average_rating) }">★</span>
              </div>
              <span class="rating-value">{{ studio.average_rating?.toFixed(1) || '—' }}</span>
            </div>

            <div v-if="studio.notable_works?.length" class="studio-known">
              <span class="known-label">Известна:</span>
              <span class="known-works">{{ studio.notable_works.slice(0, 3).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Пусто -->
      <div v-else class="empty-state">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
        <p>Студии не найдены</p>
        <button @click="resetFilters" class="reset-btn">Сбросить фильтры</button>
      </div>

      <!-- Пагинация -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          v-for="p in visiblePages"
          :key="p"
          @click="loadPage(p)"
          :class="['page-btn', { active: p === currentPage, ellipsis: p === '...' }]"
          :disabled="p === '...'"
        >{{ p }}</button>
        <button v-if="hasNext" @click="loadMore" class="load-more-btn">
          Загрузить ещё ▼
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import studiosApi, { type Studio } from '@/api/studios'

const router = useRouter()

const studios = ref<Studio[]>([])
const popularStudios = ref<Studio[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const totalCount = ref(0)
const pageSize = 20

const filters = ref({
  search: '',
  country: '',
  min_rating: '',
  ordering: '-average_rating',
})

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))
const hasNext = computed(() => currentPage.value < totalPages.value)

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (cur > 3) pages.push('...')
    for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
    if (cur < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})

const fetchStudios = async (append = false) => {
  isLoading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize,
      ordering: filters.value.ordering,
    }
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.country) params.country = filters.value.country
    if (filters.value.min_rating) params.min_rating = filters.value.min_rating

    const res = await studiosApi.getStudios(params)
    if (append) {
      studios.value.push(...(res.data.results || []))
    } else {
      studios.value = res.data.results || []
    }
    totalCount.value = res.data.count || 0
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const fetchPopular = async () => {
  try {
    const res = await studiosApi.getPopular()
    popularStudios.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {}
}

const loadPage = (page: number | string) => {
  if (typeof page !== 'number') return
  currentPage.value = page
  fetchStudios()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const loadMore = () => {
  currentPage.value++
  fetchStudios(true)
}

const applyFilters = () => {
  currentPage.value = 1
  fetchStudios()
}

const debouncedFetch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 300)
}

const clearSearch = () => {
  filters.value.search = ''
  applyFilters()
}

const resetFilters = () => {
  filters.value = { search: '', country: '', min_rating: '', ordering: '-average_rating' }
  applyFilters()
}

const toggleSubscribe = async (studio: Studio) => {
  try {
    if (studio.is_subscribed) {
      await studiosApi.unsubscribe(studio.slug)
      studio.is_subscribed = false
      studio.subscribers_count = Math.max(0, studio.subscribers_count - 1)
    } else {
      await studiosApi.subscribe(studio.slug)
      studio.is_subscribed = true
      studio.subscribers_count++
    }
  } catch (e) {}
}

const formatCount = (n: number) => {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

onMounted(() => {
  fetchStudios()
  fetchPopular()
})
</script>

<style scoped>
.studios-page {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
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

/* Sections */
.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 1rem;
}
.popular-section { margin-bottom: 2rem; }

/* Carousel */
.carousel-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  padding-bottom: 0.5rem;
}
.carousel {
  display: flex;
  gap: 0.75rem;
  min-width: max-content;
}
.carousel-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 1rem 0.75rem;
  width: 130px;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.carousel-card:hover {
  transform: translateY(-3px);
  border-color: var(--color-accent);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.carousel-logo {
  width: 60px;
  height: 60px;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-img { width: 100%; height: 100%; object-fit: contain; }
.logo-placeholder {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--color-accent);
}
.carousel-name {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--color-text);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 110px;
}
.carousel-rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}
.carousel-count {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Filters */
.filters-section {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.filter-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}
.search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.search-ico {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.625rem 2.25rem 0.625rem 2.25rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.search-input:focus { border-color: var(--color-accent); }
.search-clear-btn {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
}
.filter-selects { flex-wrap: wrap; }
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.filter-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}
.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background);
  outline: none;
  cursor: pointer;
}
.reset-btn {
  margin-top: auto;
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-end;
}
.reset-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }

/* Studios list */
.studios-list-section { }
.list-header { margin-bottom: 1rem; }

.studios-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  overflow: hidden;
}
.studio-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--color-background-surface);
  border-bottom: 1px solid var(--color-divider-light);
  transition: background 0.15s;
}
.studio-item:last-child { border-bottom: none; }
.studio-item:hover { background: var(--color-background-active); }

.studio-item-logo-link { flex-shrink: 0; }
.studio-logo {
  width: 64px;
  height: 64px;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.studio-logo-img { width: 100%; height: 100%; object-fit: contain; }
.studio-logo-placeholder {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--color-accent);
}

.studio-info { flex: 1; min-width: 0; }
.studio-info-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.375rem;
}
.studio-name-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  text-decoration: none;
}
.studio-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.studio-name-link:hover .studio-name { color: var(--color-accent); }
.verified-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--color-accent);
  color: #fff;
  border-radius: 50%;
  font-size: 0.625rem;
  font-weight: 700;
}
.studio-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}
.subscribe-btn {
  padding: 0.3125rem 0.875rem;
  border: 1px solid var(--color-accent);
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-accent);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.subscribe-btn:hover { background: var(--color-accent); color: #fff; }
.subscribe-btn.subscribed {
  background: var(--color-background-active);
  border-color: var(--color-divider);
  color: var(--color-text-secondary);
}
.subscribe-btn.subscribed:hover { background: #ef444422; border-color: #ef4444; color: #ef4444; }
.watchers {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.studio-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.375rem;
  flex-wrap: wrap;
}

.studio-rating {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}
.stars-row { display: flex; gap: 1px; }
.star { font-size: 1rem; color: var(--color-divider); transition: color 0.1s; }
.star.filled { color: #f59e0b; }
.rating-value { font-size: 0.875rem; font-weight: 700; color: var(--color-text); }

.studio-known {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.known-label { font-weight: 600; margin-right: 0.25rem; }
.known-works { color: var(--color-text-tertiary); }

/* Skeleton */
.skeleton-list { display: flex; flex-direction: column; gap: 1px; }
.skeleton-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--color-background-surface);
  border-bottom: 1px solid var(--color-divider-light);
}
.sk-logo {
  width: 64px;
  height: 64px;
  border-radius: 0.5rem;
  background: var(--color-background-active);
  flex-shrink: 0;
  animation: pulse 1.5s infinite;
}
.sk-info { flex: 1; }
.sk-title {
  height: 20px;
  width: 40%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin-bottom: 0.5rem;
  animation: pulse 1.5s infinite;
}
.sk-meta {
  height: 14px;
  width: 60%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin-bottom: 0.5rem;
  animation: pulse 1.5s infinite;
}
.sk-rating {
  height: 14px;
  width: 30%;
  background: var(--color-background-active);
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
  gap: 0.75rem;
}
.empty-state p { font-size: 1rem; margin: 0; }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}
.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) { border-color: var(--color-accent); color: var(--color-accent); }
.page-btn.active { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
.page-btn.ellipsis { cursor: default; border-color: transparent; background: transparent; }
.load-more-btn {
  padding: 0.5rem 1.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.load-more-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }

/* Responsive */
@media (max-width: 768px) {
  .studios-page { padding: 1rem; }
  .studio-item { padding: 0.875rem 1rem; }
  .studio-actions { flex-wrap: wrap; }
  .filter-row { flex-direction: column; align-items: stretch; }
  .search-wrap { min-width: unset; }
}
</style>
