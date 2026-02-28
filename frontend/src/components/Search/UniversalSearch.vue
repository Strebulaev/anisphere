<template>
  <div class="universal-search" ref="searchRef">
    <div class="search-input-wrapper">
      <MagnifyingGlassIcon class="search-icon" />
      <input
        ref="inputRef"
        v-model="searchQuery"
        type="text"
        :placeholder="placeholder"
        @focus="showResults = true"
        @blur="handleBlur"
        @keydown="handleKeydown"
        @input="handleInput"
      />
      <button v-if="searchQuery" @click="clearSearch" class="clear-btn">
        <XMarkIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Результаты поиска -->
    <div v-if="showResults && (loading || hasResults)" class="search-results">
      <!-- Загрузка -->
      <div v-if="loading" class="loading">
        <LoadingSpinner />
      </div>

      <!-- Результаты -->
      <div v-else-if="hasResults" class="results-content">
        <!-- Категории результатов -->
        <div v-for="category in resultCategories" :key="category.type" class="result-category">
          <div class="category-header">
            <span class="category-icon">{{ category.icon }}</span>
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">({{ category.results.length }})</span>
          </div>

          <div class="category-results">
            <div
              v-for="item in category.results"
              :key="item.id"
              @click="selectItem(item, category.type)"
              class="result-item"
            >
              <img
                v-if="item.poster || item.avatar"
                :src="item.poster || item.avatar"
                class="result-image"
              />
              <div v-else class="result-placeholder">
                {{ category.type === 'user' ? '👤' : '🎬' }}
              </div>
              <div class="result-info">
                <span class="result-title">{{ item.title_ru || item.display_name || item.username || item.name }}</span>
                <span class="result-subtitle">
                  {{ getSubtitle(item, category.type) }}
                </span>
              </div>
              <ChevronRightIcon class="w-5 h-5 result-arrow" />
            </div>
          </div>
        </div>

        <!-- Ссылка "Все результаты" -->
        <div v-if="showAllResultsLink" class="all-results-link">
          <router-link :to="`/search?q=${encodeURIComponent(searchQuery)}`" @click="showResults = false">
            Все результаты для "{{ searchQuery }}"
          </router-link>
        </div>
      </div>

      <!-- Пусто -->
      <div v-else class="empty">
        <p>Ничего не найдено</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ChevronRightIcon
} from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import api from '@/api'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Поиск...'
  },
  categories: {
    type: Array,
    default: () => ['anime', 'users', 'posts', 'playlists']
  },
  limit: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits(['search', 'select'])

const router = useRouter()

const searchQuery = ref('')
const loading = ref(false)
const showResults = ref(false)
const results = ref({})
const searchRef = ref(null)
const inputRef = ref(null)

let searchTimeout = null

const resultCategories = computed(() => {
  const categories = []

  const categoryConfig = {
    anime: { icon: '🎬', name: 'Аниме' },
    users: { icon: '👤', name: 'Пользователи' },
    posts: { icon: '📝', name: 'Посты' },
    playlists: { icon: '📁', name: 'Плейлисты' },
    groups: { icon: '👥', name: 'Группы' },
  }

  props.categories.forEach(type => {
    if (results.value[type] && results.value[type].length > 0) {
      categories.push({
        type,
        ...categoryConfig[type],
        results: results.value[type].slice(0, props.limit)
      })
    }
  })

  return categories
})

const hasResults = computed(() => {
  return Object.values(results.value).some(arr => arr && arr.length > 0)
})

const showAllResultsLink = computed(() => {
  return hasResults.value && searchQuery.value.length >= 2
})

const handleInput = () => {
  clearTimeout(searchTimeout)

  if (searchQuery.value.length < 2) {
    results.value = {}
    showResults.value = false
    return
  }

  searchTimeout = setTimeout(() => {
    performSearch()
  }, 300)
}

const performSearch = async () => {
  if (searchQuery.value.length < 2) return

  loading.value = true
  results.value = {}

  try {
    const promises = []

    if (props.categories.includes('anime')) {
      promises.push(
        api.get('/anime/', { params: { search: searchQuery.value, limit: props.limit } })
          .then(res => ({ type: 'anime', data: res.data.results || res.data }))
      )
    }

    if (props.categories.includes('users')) {
      promises.push(
        api.get('/users/search/', { params: { search: searchQuery.value } })
          .then(res => ({ type: 'users', data: res.data }))
      )
    }

    if (props.categories.includes('posts')) {
      promises.push(
        api.get('/social/posts/', { params: { search: searchQuery.value, limit: props.limit } })
          .then(res => ({ type: 'posts', data: res.data.results || res.data }))
      )
    }

    if (props.categories.includes('playlists')) {
      promises.push(
        api.get('/playlists/', { params: { search: searchQuery.value, limit: props.limit } })
          .then(res => ({ type: 'playlists', data: res.data.results || res.data }))
      )
    }

    const responses = await Promise.all(promises)

    responses.forEach(({ type, data }) => {
      results.value[type] = data
    })

    emit('search', { query: searchQuery.value, results: results.value })
  } catch (error) {
    console.error('Ошибка поиска:', error)
  } finally {
    loading.value = false
  }
}

const selectItem = (item, type) => {
  emit('select', { item, type })

  // Переходим к элементу
  const routes = {
    anime: `/anime/${item.id}`,
    users: `/profile/${item.id}`,
    posts: `/posts/${item.id}`,
    playlists: `/playlists/${item.id}`,
    groups: `/groups/${item.id}`,
  }

  const route = routes[type]
  if (route) {
    router.push(route)
  }

  showResults.value = false
  searchQuery.value = ''
}

const getSubtitle = (item, type) => {
  switch (type) {
    case 'anime':
      return `${item.year} • ${item.genres?.slice(0, 2).join(', ') || 'Аниме'}`
    case 'users':
      return `@${item.username}`
    case 'posts':
      return item.text?.substring(0, 50) + '...' || 'Без текста'
    case 'playlists':
      return `${item.anime_count || 0} аниме`
    case 'groups':
      return `${item.members_count || 0} участников`
    default:
      return ''
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  results.value = {}
  showResults.value = false
  inputRef.value?.focus()
}

const handleBlur = () => {
  // Задержка чтобы успеть кликнуть по результату
  setTimeout(() => {
    showResults.value = false
  }, 200)
}

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    showResults.value = false
  }
}

const focus = () => {
  inputRef.value?.focus()
}

// Экспортируем метод для родительского компонента
defineExpose({ focus })
</script>

<style scoped>
.universal-search {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  transition: all 0.3s;
}

.search-input-wrapper:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: #999;
  margin-right: 12px;
}

.search-input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
}

.clear-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #999;
  transition: all 0.3s;
}

.clear-btn:hover {
  background: #e0e0e0;
  color: #666;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-height: 500px;
  overflow-y: auto;
  z-index: 1000;
}

.loading,
.empty {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.results-content {
  padding: 8px 0;
}

.result-category {
  border-bottom: 1px solid #f0f0f0;
}

.result-category:last-child {
  border-bottom: none;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f9f9f9;
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.category-count {
  margin-left: auto;
  font-size: 12px;
}

.category-results {
  max-height: 250px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.3s;
}

.result-item:hover {
  background: #f5f5f5;
}

.result-image {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
}

.result-placeholder {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 8px;
  font-size: 20px;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  display: block;
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-subtitle {
  display: block;
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-arrow {
  color: #ccc;
  flex-shrink: 0;
}

.all-results-link {
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

.all-results-link a {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.3s;
}

.all-results-link a:hover {
  color: #5568d3;
}
</style>
