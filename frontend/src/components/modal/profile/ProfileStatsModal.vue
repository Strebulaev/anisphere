<template>
  <BaseModal
    :show="props.show"
    :title="`📊 СТАТИСТИКА ПРОФИЛЯ\n@${username}`"
    @update:show="emit('update:show', false)"
    size="large"
  >
    <div class="stats-modal">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка статистики...</p>
      </div>

      <div v-else-if="stats" class="stats-content">
        <div class="stats-section">
          <h3 class="section-title">ПОСЕЩАЕМОСТЬ</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.profile_views) }}</div>
              <div class="stat-label">Просмотры профиля</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.unique_visitors) }}</div>
              <div class="stat-label">Уникальные посетители</div>
            </div>
          </div>
          <div class="chart-container">
            <div class="chart-label">График за неделю:</div>
            <div class="weekly-chart">
              <div
                v-for="(value, index) in stats.weekly_views"
                :key="index"
                class="chart-bar"
                :style="{ height: `${getBarHeight(value)}%` }"
                :title="getDayLabel(index) + ': ' + value + ' просмотров'"
              >
                <span class="bar-value">{{ value }}</span>
              </div>
            </div>
            <div class="chart-labels">
              <span v-for="(_, index) in 7" :key="index" class="day-label">
                {{ getDayLabel(index) }}
              </span>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3 class="section-title">ПОДПИСЧИКИ</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value positive">+{{ stats.new_followers }}</div>
              <div class="stat-label">Новые подписчики</div>
            </div>
            <div class="stat-card">
              <div class="stat-value negative">-{{ stats.unfollowed_count }}</div>
              <div class="stat-label">Отписалось</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.total_followers) }}</div>
              <div class="stat-label">Всего</div>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3 class="section-title">ВЗАИМОДЕЙСТВИЯ</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.post_likes) }}</div>
              <div class="stat-label">Лайки на постах</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.comments) }}</div>
              <div class="stat-label">Комментарии</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(stats.reposts) }}</div>
              <div class="stat-label">Репосты</div>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3 class="section-title">ПОПУЛЯРНЫЙ КОНТЕНТ</h3>
          <div v-if="stats.popular_content && stats.popular_content.length > 0" class="popular-list">
            <div
              v-for="(item, index) in stats.popular_content"
              :key="item.id"
              class="popular-item"
            >
              <div class="popular-rank">{{ index + 1 }}</div>
              <div class="popular-info">
                <h4 class="popular-title">{{ item.title }}</h4>
                <p class="popular-stats">
                  {{ formatNumber(item.views) }} просмотров · 
                  {{ formatNumber(item.likes) }} лайков
                </p>
              </div>
            </div>
          </div>
          <div v-else class="empty-content">
            <p>Пока нет данных</p>
          </div>
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import type { ProfileStats, User } from '@/types'

interface Props {
  show: boolean
  user: User
  stats: ProfileStats | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const username = computed(() => props.user.nickname || props.user.username)

const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

const getBarHeight = (value: number) => {
  const max = Math.max(...(props.stats?.weekly_views || [1]))
  if (max === 0) return 0
  return (value / max) * 100
}

const getDayLabel = (index: number) => {
  const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
  return days[index] || ''
}
</script>

<style scoped>
.stats-modal {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-height: 600px;
  overflow-y: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
  color: var(--color-text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.stat-card {
  padding: 1rem;
  background: var(--color-background);
  border-radius: 0.75rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.negative {
  color: #ef4444;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.chart-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.weekly-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 120px;
  padding: 0.5rem 0;
  background: var(--color-background);
  border-radius: 0.5rem;
}

.chart-bar {
  flex: 1;
  margin: 0 0.25rem;
  background: var(--color-accent);
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 4px;
  transition: height 0.3s ease;
}

.chart-bar:hover {
  opacity: 0.8;
}

.bar-value {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.7rem;
  color: var(--color-text-primary);
  font-weight: 600;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 0.25rem;
}

.day-label {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  flex: 1;
  text-align: center;
}

.popular-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.popular-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 0.5rem;
  align-items: center;
}

.popular-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-orange);
  color: var(--color-text);
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}

.popular-info {
  flex: 1;
  min-width: 0;
}

.popular-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.25rem 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.popular-stats {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.empty-content {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-tertiary);
}

.empty-content p {
  margin: 0;
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .weekly-chart {
    height: 100px;
  }

  .bar-value {
    font-size: 0.6rem;
  }
}
</style>
