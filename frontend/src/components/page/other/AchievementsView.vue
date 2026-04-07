<template>
  <div class="achievements-page">
    <div class="page-header">
      <h1>Достижения {{ username ? `@${username}` : '' }}</h1>
      <div class="stats">
        <div class="stat-item">
          <span class="stat-value">{{ unlockedCount }}</span>
          <span class="stat-label">Получено</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ totalCount }}</span>
          <span class="stat-label">Всего</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ progressPercentage }}%</span>
          <span class="stat-label">Прогресс</span>
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
        @click="activeTab = 'unlocked'"
        :class="['tab-btn', { active: activeTab === 'unlocked' }]"
      >
        Полученные
        <span class="badge">{{ unlockedCount }}</span>
      </button>
      <button
        @click="activeTab = 'in_progress'"
        :class="['tab-btn', { active: activeTab === 'in_progress' }]"
      >
        В процессе
        <span class="badge">{{ inProgressCount }}</span>
      </button>
    </div>

    <!-- Фильтр по категориям -->
    <div class="category-filter">
      <select v-model="selectedCategory" class="category-select">
        <option value="">Все категории</option>
        <option value="basic">Основные</option>
        <option value="social">Социальные</option>
        <option value="collection">Коллекционные</option>
        <option value="contest">Конкурсные</option>
        <option value="special">Специальные</option>
      </select>
    </div>

    <!-- Список достижений -->
    <div v-if="!loading" class="achievements-list">
      <div
        v-for="category in groupedAchievements"
        :key="category.name"
        class="category-group"
      >
        <h2 class="category-title">{{ category.name }}</h2>
        <div class="achievements-grid">
          <div
            v-for="achievement in category.achievements"
            :key="achievement.id"
            :class="['achievement-card', {
              unlocked: achievement.is_unlocked,
              locked: !achievement.is_unlocked
            }]"
            @click="openAchievementDetail(achievement)"
          >
            <div class="icon">
              <img
                :src="achievement.achievement.icon_url || '/default-achievement.png'"
                :alt="achievement.achievement.name"
              />
              <div :class="['level-badge', achievement.achievement.level]">
                {{ getLevelIcon(achievement.achievement.level) }}
              </div>
            </div>
            <div class="info">
              <h3>{{ achievement.achievement.name }}</h3>
              <p>{{ achievement.achievement.description }}</p>
              <div class="progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: achievement.progress_percentage + '%' }"
                  ></div>
                </div>
                <span class="progress-text">
                  {{ achievement.progress }}/{{ achievement.achievement.condition_value }}
                </span>
              </div>
              <div v-if="achievement.is_unlocked" class="unlocked-date">
                Получено: {{ formatDate(achievement.unlocked_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <!-- Пусто -->
    <div v-if="!loading && filteredAchievements.length === 0" class="empty">
      <p>Достижения не найдены</p>
    </div>

    <!-- Модальное окно детализации -->
    <Modal v-if="selectedAchievement" @close="selectedAchievement = null">
      <div class="achievement-detail">
        <div class="detail-header">
          <div class="icon-large">
            <img
              :src="selectedAchievement.achievement.icon_url || '/default-achievement.png'"
              :alt="selectedAchievement.achievement.name"
            />
            <div :class="['level-badge', selectedAchievement.achievement.level]">
              {{ getLevelIcon(selectedAchievement.achievement.level) }}
            </div>
          </div>
          <div class="header-info">
            <h2>{{ selectedAchievement.achievement.name }}</h2>
            <p class="category">{{ getCategoryName(selectedAchievement.achievement.category) }}</p>
          </div>
        </div>
        <div class="detail-content">
          <p class="description">{{ selectedAchievement.achievement.description }}</p>

          <div class="condition">
            <h3>Условие получения</h3>
            <p>{{ getConditionText(selectedAchievement.achievement) }}</p>
          </div>

          <div class="progress-section">
            <h3>Прогресс</h3>
            <div class="progress-bar-large">
              <div
                class="progress-fill"
                :style="{ width: selectedAchievement.progress_percentage + '%' }"
              ></div>
            </div>
            <p class="progress-text">
              {{ selectedAchievement.progress }} / {{ selectedAchievement.achievement.condition_value }}
              ({{ selectedAchievement.progress_percentage }}%)
            </p>
          </div>

          <div v-if="selectedAchievement.is_unlocked" class="unlocked-info">
            <h3>Получено</h3>
            <p>{{ formatDate(selectedAchievement.unlocked_at) }}</p>
          </div>

          <div class="stats">
            <h3>Статистика</h3>
            <p>Получили: {{ selectedAchievement.achievement.unlocked_count }} пользователей</p>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import Modal from '@/components/ui/Modal.vue'
import api from '@/api'

const route = useRoute()

const username = ref(route.params.username || '')
const activeTab = ref('all')
const selectedCategory = ref('')
const loading = ref(false)
const achievements = ref([])
const selectedAchievement = ref(null)

const categoryNames = {
  basic: 'Основные',
  social: 'Социальные',
  collection: 'Коллекционные',
  contest: 'Конкурсные',
  special: 'Специальные',
}

const levelIcons = {
  bronze: '🥉',
  silver: '🏅',
  gold: '🏅',
  legendary: '👑',
}

const filteredAchievements = computed(() => {
  let result = achievements.value

  if (activeTab.value === 'unlocked') {
    result = result.filter(a => a.is_unlocked)
  } else if (activeTab.value === 'in_progress') {
    result = result.filter(a => !a.is_unlocked && a.progress > 0)
  }

  if (selectedCategory.value) {
    result = result.filter(a => a.achievement.category === selectedCategory.value)
  }

  return result
})

const groupedAchievements = computed(() => {
  const groups = {}
  filteredAchievements.value.forEach(achievement => {
    const category = achievement.achievement.category
    if (!groups[category]) {
      groups[category] = {
        name: categoryNames[category] || category,
        achievements: [],
      }
    }
    groups[category].achievements.push(achievement)
  })

  return Object.values(groups)
})

const unlockedCount = computed(() => {
  return achievements.value.filter(a => a.is_unlocked).length
})

const inProgressCount = computed(() => {
  return achievements.value.filter(a => !a.is_unlocked && a.progress > 0).length
})

const totalCount = computed(() => {
  return achievements.value.length
})

const progressPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((unlockedCount.value / totalCount.value) * 100)
})

const loadAchievements = async () => {
  loading.value = true
  try {
    const params = {}
    if (username.value) {
      // Загружаем достижения другого пользователя
      const userResponse = await api.get(`/users/search/?search=${username.value}`)
      if (userResponse.data.length > 0) {
        params.user_id = userResponse.data[0].id
      }
    }

    const response = await api.get('/social/user-achievements/all/', { params })
    achievements.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки достижений:', error)
  } finally {
    loading.value = false
  }
}

const getLevelIcon = (level) => {
  return levelIcons[level] || '🏅'
}

const getCategoryName = (category) => {
  return categoryNames[category] || category
}

const getConditionText = (achievement) => {
  const conditionTexts = {
    posts_count: `Создать ${achievement.condition_value} постов`,
    followers_count: `Получить ${achievement.condition_value} подписчиков`,
    following_count: `Подписаться на ${achievement.condition_value} пользователей`,
    likes_received: `Получить ${achievement.condition_value} лайков`,
    reposts_count: `Сделать ${achievement.condition_value} репостов`,
    reposts_received: `Получить ${achievement.condition_value} репостов`,
    comments_count: `Оставить ${achievement.condition_value} комментариев`,
    registration_days: `Быть на сайте ${achievement.condition_value} дней`,
    profile_completed: `Заполнить профиль на ${achievement.condition_value}%`,
  }
  return conditionTexts[achievement.condition_type] || achievement.condition_type
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

const openAchievementDetail = (achievement) => {
  selectedAchievement.value = achievement
}

onMounted(() => {
  loadAchievements()
})
</script>

<style scoped>
.achievements-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: var(--color-text);
}

.stats {
  display: flex;
  gap: 30px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: var(--color-accent);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--color-divider);
  padding-bottom: 10px;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: transparent;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
  color: var(--color-text-secondary);
}

.tab-btn:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

.tab-btn.active {
  background: var(--color-accent);
  color: var(--color-text);
}

.badge {
  background: var(--color-background-active);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: 5px;
}

.category-filter {
  margin-bottom: 20px;
}

.category-select {
  padding: 10px 16px;
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  font-size: 14px;
  background: var(--color-background-surface);
  color: var(--color-text);
}

.category-group {
  margin-bottom: 40px;
}

.category-title {
  font-size: 20px;
  margin-bottom: 20px;
  color: var(--color-text);
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.achievement-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--color-background-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all 0.15s ease;
}

.achievement-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.achievement-card.locked {
  opacity: 0.6;
  filter: grayscale(0.5);
}

.achievement-card.unlocked {
  border: 2px solid var(--color-accent-orange);
}

.icon {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.level-badge {
  position: absolute;
  bottom: -5px;
  right: -5px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 16px;
  background: var(--color-background-surface);
  box-shadow: var(--shadow-card);
}

.level-badge.bronze { border: 2px solid #cd7f32; }
.level-badge.silver { border: 2px solid #c0c0c0; }
.level-badge.gold { border: 2px solid #ffd700; }
.level-badge.legendary {
  border: 2px solid #9b59b6;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.info {
  flex: 1;
}

.info h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text);
}

.info p {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.progress {
  margin-bottom: 12px;
}

.progress-bar {
  height: 6px;
  background: var(--color-background);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.unlocked-date {
  font-size: 11px;
  color: var(--color-accent-teal);
  font-weight: bold;
}

.loading,
.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-tertiary);
}

.achievement-detail {
  padding: 30px;
  max-width: 600px;
}

.detail-header {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.icon-large {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.icon-large img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.icon-large .level-badge {
  width: 48px;
  height: 48px;
  font-size: 24px;
}

.header-info h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: var(--color-text);
}

.category {
  margin: 0;
  color: var(--color-text-tertiary);
}

.detail-content > * {
  margin-bottom: 24px;
}

.detail-content h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text);
}

.description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.condition p {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.progress-bar-large {
  height: 12px;
  background: var(--color-background);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar-large .progress-fill {
  height: 100%;
}

.progress-section .progress-text {
  font-size: 14px;
}

.unlocked-info p {
  font-size: 14px;
  color: var(--color-accent-teal);
}

.stats p {
  font-size: 14px;
  color: var(--color-text-secondary);
}
</style>
