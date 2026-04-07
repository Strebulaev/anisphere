<template>
  <BaseModal
    :show="props.show"
    :title="`🏆 ДОСТИЖЕНИЯ @${username}`"
    @update:show="emit('update:show', false)"
    size="large"
  >
    <div class="achievements-modal">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка достижений...</p>
      </div>

      <div v-else>
        <div v-if="groupedAchievements.basic.length > 0" class="achievement-section">
          <h3 class="section-title">ОСНОВНЫЕ</h3>
          <div class="achievements-grid">
            <AchievementCard
              v-for="achievement in groupedAchievements.basic"
              :key="achievement.id"
              :achievement="achievement"
              @click="showDetail(achievement)"
            />
          </div>
        </div>

        <div v-if="groupedAchievements.contest.length > 0" class="achievement-section">
          <h3 class="section-title">КОНКУРСНЫЕ</h3>
          <div class="achievements-grid">
            <AchievementCard
              v-for="achievement in groupedAchievements.contest"
              :key="achievement.id"
              :achievement="achievement"
              @click="showDetail(achievement)"
            />
          </div>
        </div>

        <div v-if="groupedAchievements.social.length > 0" class="achievement-section">
          <h3 class="section-title">СОЦИАЛЬНЫЕ</h3>
          <div class="achievements-grid">
            <AchievementCard
              v-for="achievement in groupedAchievements.social"
              :key="achievement.id"
              :achievement="achievement"
              @click="showDetail(achievement)"
            />
          </div>
        </div>

        <div v-if="groupedAchievements.special.length > 0" class="achievement-section">
          <h3 class="section-title">СПЕЦИАЛЬНЫЕ</h3>
          <div class="achievements-grid">
            <AchievementCard
              v-for="achievement in groupedAchievements.special"
              :key="achievement.id"
              :achievement="achievement"
              @click="showDetail(achievement)"
            />
          </div>
        </div>

        <div v-if="allAchievements.length === 0" class="empty-state">
          <div class="empty-icon"> <SakuraIcon name="trophy" /> </div>
          <h3>Пока нет достижений</h3>
          <p>Выполняйте активности, чтобы получать достижения!</p>
        </div>
      </div>
    </div>
  </BaseModal>

  <BaseModal
    :show="showDetailModal"
    :title="selectedAchievement?.name"
    @update:show="showDetailModal = false"
  >
    <div v-if="selectedAchievement" class="achievement-detail">
      <div class="detail-icon">{{ selectedAchievement.icon || '🏆' }}</div>
      <p class="detail-description">{{ selectedAchievement.description }}</p>
      
      <div v-if="selectedAchievement.requirement" class="detail-requirement">
        <h4>Требование:</h4>
        <p>{{ selectedAchievement.requirement }}</p>
      </div>

      <div v-if="selectedAchievement.reward_xp" class="detail-reward">
        <h4>Награда:</h4>
        <ul>
          <li v-if="selectedAchievement.reward_xp">{{ selectedAchievement.reward_xp }} опыта</li>
          <li>Специальный значок в профиле</li>
        </ul>
      </div>

      <div v-if="selectedAchievement.progress !== undefined" class="detail-progress">
        <h4>Прогресс:</h4>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${progressPercentage}%` }"
          ></div>
        </div>
        <p class="progress-text">
          {{ selectedAchievement.progress }} / {{ selectedAchievement.max_progress }}
          ({{ progressPercentage }}%)
        </p>
      </div>

      <div v-if="selectedAchievement.unlocked_at" class="detail-unlocked">
        <p>Получено: {{ formatDate(selectedAchievement.unlocked_at) }}</p>
      </div>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import AchievementCard from './AchievementCard.vue'
import type { Achievement, User } from '@/types'

interface Props {
  show: boolean
  user: User
  achievements: Achievement[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const showDetailModal = ref(false)
const selectedAchievement = ref<Achievement | null>(null)

const username = computed(() => props.user.nickname || props.user.username)

const groupedAchievements = computed(() => {
  const groups = {
    basic: [] as Achievement[],
    contest: [] as Achievement[],
    social: [] as Achievement[],
    special: [] as Achievement[]
  }

  props.achievements.forEach(achievement => {
    if (groups[achievement.category]) {
      groups[achievement.category].push(achievement)
    }
  })

  return groups
})

const allAchievements = computed(() => props.achievements)

const progressPercentage = computed(() => {
  if (!selectedAchievement.value || 
      selectedAchievement.value.progress === undefined || 
      !selectedAchievement.value.max_progress) {
    return 0
  }
  return Math.round(
    (selectedAchievement.value.progress / selectedAchievement.value.max_progress) * 100
  )
})

const showDetail = (achievement: Achievement) => {
  selectedAchievement.value = achievement
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}
</script>

<style scoped>
.achievements-modal {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.achievement-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.25rem;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.empty-state p {
  font-size: 0.95rem;
  margin: 0;
}

.achievement-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem;
}

.detail-icon {
  font-size: 4rem;
}

.detail-description {
  font-size: 1.1rem;
  color: var(--color-text-primary);
  text-align: center;
  margin: 0;
  line-height: 1.5;
}

.detail-requirement,
.detail-reward,
.detail-progress,
.detail-unlocked {
  width: 100%;
  text-align: left;
}

.detail-requirement h4,
.detail-reward h4,
.detail-progress h4 {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-requirement p,
.detail-reward ul {
  font-size: 0.95rem;
  color: var(--color-text-primary);
  margin: 0;
}

.detail-reward ul {
  padding-left: 1.5rem;
}

.detail-reward li {
  margin: 0.25rem 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--color-divider);
  border-radius: 4px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.detail-unlocked p {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin: 0;
}

@media (max-width: 640px) {
  .achievements-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
  }
}
</style>
