<template>
  <div class="online-users-page">
    <div class="page-header">
      <h1>Пользователи</h1>
      <div class="header-actions">
        <div class="search-bar">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск пользователей..."
            @input="debouncedSearch"
          />
        </div>
      </div>
    </div>

    <!-- Табы -->
    <div class="tabs">
      <button
        @click="activeTab = 'all'"
        :class="['tab-btn', { active: activeTab === 'all' }]"
      >
        Все
      </button>
      <button
        @click="activeTab = 'online'"
        :class="['tab-btn', { active: activeTab === 'online' }]"
      >
        Онлайн
        <span v-if="onlineCount" class="badge">{{ onlineCount }}</span>
      </button>
      <button
        @click="activeTab = 'offline'"
        :class="['tab-btn', { active: activeTab === 'offline' }]"
      >
        Офлайн
      </button>
    </div>

    <!-- Фильтры и сортировка -->
    <div class="filters">
      <select v-model="sortBy" class="sort-select" @change="loadUsers">
        <option value="last_seen">По активности</option>
        <option value="username">По имени</option>
        <option value="followers">По подписчикам</option>
      </select>
    </div>

    <!-- Список пользователей -->
    <div v-if="!loading" class="users-list">
      <div
        v-for="user in filteredUsers"
        :key="user.id"
        class="user-card"
        @click="openProfile(user.id)"
      >
        <div class="avatar" @click.stop="openProfile(user.id)">
          <img :src="user.avatar_url || user.avatar || '/img/default-avatar.svg'" :alt="user.username" />
          <div :class="['status-dot', { online: user.is_online }]"></div>
        </div>
        <div class="user-info" @click.stop="openProfile(user.id)">
          <h3>{{ user.display_name || user.username }}</h3>
          <p class="username">@{{ user.username }}</p>
          <p class="stats">{{ user.followers_count }} подписчиков</p>
          <p class="last-seen">
            {{ user.is_online ? '🟢 В сети' : getLastSeenText(user.last_seen) }}
          </p>
        </div>
        <div class="actions">
          <button
            v-if="user.id !== currentUser.id && !user.is_following"
            @click.stop="toggleFollow(user.id)"
            class="btn-follow"
          >
            Подписаться
          </button>
          <button
            v-if="user.id !== currentUser.id && user.is_following"
            @click.stop="toggleFollow(user.id)"
            class="btn-unfollow"
          >
            Подписан
          </button>
          <button
            @click.stop="openChat(user.id)"
            class="btn-message"
          >
            <ChatBubbleLeftIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пусто -->
    <div v-if="!loading && filteredUsers.length === 0" class="empty">
      <p>Пользователи не найдены</p>
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="prevPage"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        Назад
      </button>
      <span>Страница {{ currentPage }} из {{ totalPages }}</span>
      <button
        @click="nextPage"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Вперёд
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ChatBubbleLeftIcon } from '@heroicons/vue/24/outline'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('all')
const searchQuery = ref('')
const sortBy = ref('last_seen')
const loading = ref(false)
const users = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

let searchTimeout = null

const currentUser = computed(() => authStore.user)

const filteredUsers = computed(() => {
  let result = users.value

  if (activeTab.value === 'online') {
    result = result.filter(user => user.is_online)
  } else if (activeTab.value === 'offline') {
    result = result.filter(user => !user.is_online)
  }

  return result
})

const onlineCount = computed(() => {
  return users.value.filter(user => user.is_online).length
})

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      sort: sortBy.value,
    }

    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }

    const response = await api.get('/users/online/', { params })
    // Ответ идёт в формате { results: [...], count: N }
    users.value = response.data.results || response.data.users || []
    total.value = response.data.count || response.data.total || users.value.length
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadUsers()
  }, 300)
}

const openProfile = (userId) => {
  router.push(`/profile/${userId}`)
}

const openChat = async (userId) => {
  try {
    const response = await api.post('/chats/private/', { user_id: userId })
    router.push(`/chats/${response.data.id}`)
  } catch (error) {
    console.error('Ошибка создания чата:', error)
  }
}

const toggleFollow = async (userId) => {
  try {
    const response = await api.post(`/social/follow/toggle/${userId}/`)
    const user = users.value.find(u => u.id === userId)
    if (user) {
      user.is_following = response.data.following
    }
  } catch (error) {
    console.error('Ошибка подписки:', error)
  }
}

const getLastSeenText = (lastSeen) => {
  if (!lastSeen) return '⚫ Не был в сети'
  const now = new Date()
  const diff = Math.floor((now - new Date(lastSeen)) / 1000)

  if (diff < 60) return '⚫ Только что'
  if (diff < 3600) return `⚫ ${Math.floor(diff / 60)} мин. назад`
  if (diff < 86400) return `⚫ ${Math.floor(diff / 3600)} ч. назад`
  return `⚫ ${Math.floor(diff / 86400)} дн. назад`
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadUsers()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadUsers()
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.online-users-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
}

.search-bar {
  flex: 1;
  max-width: 400px;
}

.search-bar input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: #f5f5f5;
}

.tab-btn.active {
  background: #667eea;
  color: white;
}

.badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: 5px;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.sort-select {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
  cursor: pointer;
}

.user-card:hover {
  transform: translateY(-2px);
}

.avatar {
  position: relative;
  width: 60px;
  height: 60px;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.status-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background: #999;
  border: 2px solid white;
  border-radius: 50%;
}

.status-dot.online {
  background: #4caf50;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-info h3 {
  margin: 0 0 4px;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.username {
  margin: 0 0 4px;
  font-size: 14px;
  color: #999;
}

.stats {
  margin: 0 0 4px;
  font-size: 13px;
  color: #666;
}

.last-seen {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-follow {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-follow:hover {
  background: #5568d3;
}

.btn-unfollow {
  padding: 8px 16px;
  background: #e0e0e0;
  color: #666;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-unfollow:hover {
  background: #d0d0d0;
}

.btn-message {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-message:hover {
  background: #e0e0e0;
}

.loading,
.empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
}

.pagination-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.pagination-btn:hover:not(:disabled) {
  background: #5568d3;
}

.pagination-btn:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
}
</style>
