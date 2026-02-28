<template>
  <div class="anime-dna-indicator">
    <!-- Вращающиеся линии -->
    <svg
      class="dna-lines"
      viewBox="0 0 44 44"
      @click="togglePanel"
      @mouseenter="onHover"
      @mouseleave="onLeave"
    >
      <!-- Внешняя линия (розовая) -->
      <circle
        class="dna-line-outer"
        cx="22"
        cy="22"
        r="20"
        fill="none"
        stroke="url(#gradient-outer)"
        stroke-width="2"
        stroke-dasharray="126"
        stroke-dashoffset="0"
      />
      
      <!-- Средняя линия (бирюзовая) -->
      <circle
        class="dna-line-middle"
        cx="22"
        cy="22"
        r="14"
        fill="none"
        stroke="url(#gradient-middle)"
        stroke-width="2"
        stroke-dasharray="88"
        stroke-dashoffset="0"
      />
      
      <!-- Внутренняя линия (голубая) -->
      <circle
        class="dna-line-inner"
        cx="22"
        cy="22"
        r="8"
        fill="none"
        stroke="url(#gradient-inner)"
        stroke-width="2"
        stroke-dasharray="50"
        stroke-dashoffset="0"
      />
      
      <!-- Градиенты -->
      <defs>
        <linearGradient id="gradient-outer" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#FF2A6D;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#8B5CF6;stop-opacity:1" />
        </linearGradient>
        
        <linearGradient id="gradient-middle" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#00D4AA;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#3A86FF;stop-opacity:1" />
        </linearGradient>
        
        <linearGradient id="gradient-inner" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#3A86FF;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#00D4AA;stop-opacity:1" />
        </linearGradient>
      </defs>
    </svg>
    
    <!-- Тултип -->
    <div class="dna-tooltip" v-show="showTooltip">
      Профиль
    </div>
    
    <!-- Панель Аниме-ДНК -->
    <transition name="slide-right">
      <div v-if="showPanel" class="dna-panel" @click.stop>
        <div class="dna-panel-header">
          <h3 class="dna-panel-title">Профиль</h3>
          <button class="dna-panel-close" @click="togglePanel" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div class="dna-panel-divider"></div>
        
        <!-- Тип личности -->
        <div class="dna-section">
          <div class="dna-type-header">
            <div class="dna-type-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/>
                <path d="M12 8v8"/>
                <path d="M8 12h8"/>
              </svg>
            </div>
            <div class="dna-type-info">
              <p class="dna-type-label">Тип личности</p>
              <p class="dna-type-value">{{ dnaData.type || 'Не определён' }}</p>
            </div>
          </div>
        </div>
        
        <!-- Шкалы характеристик -->
        <div class="dna-section">
          <p class="dna-section-title">Основные характеристики</p>
          <div class="dna-scales">
            <div v-for="scale in dnaData.scales" :key="scale.name" class="dna-scale">
              <div class="dna-scale-header">
                <span class="dna-scale-name">{{ scale.name }}</span>
                <span class="dna-scale-value">{{ scale.value }}%</span>
              </div>
              <div class="dna-scale-bar">
                <div 
                  class="dna-scale-fill"
                  :style="{ width: scale.value + '%', backgroundColor: scale.color }"
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Последние предсказания -->
        <div v-if="dnaData.predictions && dnaData.predictions.length" class="dna-section">
          <p class="dna-section-title">Последние предсказания</p>
          <div class="dna-predictions">
            <div 
              v-for="prediction in dnaData.predictions.slice(0, 3)" 
              :key="prediction.animeId"
              class="dna-prediction"
            >
              <div class="dna-prediction-info">
                <p class="dna-prediction-anime">{{ prediction.animeTitle }}</p>
                <p class="dna-prediction-ratings">
                  <span class="predicted">Предсказано: {{ prediction.predictedRating }}</span>
                  <span class="actual">Факт: {{ prediction.actualRating || '—' }}</span>
                </p>
              </div>
              <div v-if="prediction.isAccurate" class="dna-prediction-accurate">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Прогресс заполнения профиля -->
        <div class="dna-section">
          <div class="dna-progress-header">
            <p class="dna-progress-label">Профиль заполнен на {{ dnaData.profileCompletion }}%</p>
          </div>
          <div class="dna-progress-bar">
            <div 
              class="dna-progress-fill"
              :style="{ width: dnaData.profileCompletion + '%' }"
            ></div>
          </div>
          <p v-if="dnaData.completionTip" class="dna-progress-tip">
            {{ dnaData.completionTip }}
          </p>
        </div>
        
        <!-- Участие во фракции -->
        <div v-if="dnaData.faction" class="dna-section">
          <p class="dna-section-title">Фракция</p>
          <div class="dna-faction">
            <div class="dna-faction-icon">
              {{ dnaData.faction.icon }}
            </div>
            <div class="dna-faction-info">
              <p class="dna-faction-name">{{ dnaData.faction.name }}</p>
              <p class="dna-faction-rank">{{ dnaData.faction.rank }}</p>
            </div>
          </div>
        </div>
        
        <!-- Быстрые действия -->
        <div class="dna-actions">
          <button class="dna-action-btn" @click="handleUpdateTest" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
              <path d="M16 16h5v5"/>
            </svg>
            Обновить тест
          </button>
          <button class="dna-action-btn" @click="handleCompareWithFriend" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Сравнить с другом
          </button>
          <button class="dna-action-btn primary" @click="handleViewRecommendations" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Смотреть рекомендации
          </button>
        </div>
      </div>
    </transition>
    
    <!-- Оверлей для закрытия панели -->
    <div 
      v-if="showPanel" 
      class="dna-panel-overlay"
      @click="togglePanel"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

interface DNAPrediction {
  animeId: number
  animeTitle: string
  predictedRating: number
  actualRating?: number
  isAccurate: boolean
}

interface DNAData {
  type: string
  scales: Array<{
    name: string
    value: number
    color: string
  }>
  predictions?: DNAPrediction[]
  profileCompletion: number
  completionTip?: string
  faction?: {
    name: string
    rank: string
    icon: string
  }
}

const emit = defineEmits<{
  'update-test': []
  'compare-friend': []
  'view-recommendations': []
}>()

const showTooltip = ref(false)
const showPanel = ref(false)

const dnaData = reactive<DNAData>({
  type: 'Аналитик-Идеалист',
  scales: [
    { name: 'Романтика', value: 80, color: '#FF2A6D' },
    { name: 'Стратегия', value: 65, color: '#3A86FF' },
    { name: 'Цинизм', value: 20, color: '#888888' },
  ],
  predictions: [
    {
      animeId: 1,
      animeTitle: 'Ванпанчмен',
      predictedRating: 8.7,
      actualRating: 9.0,
      isAccurate: true,
    },
    {
      animeId: 2,
      animeTitle: 'Атака титанов',
      predictedRating: 8.5,
      actualRating: 8.2,
      isAccurate: true,
    },
  ],
  profileCompletion: 65,
  completionTip: 'Добавьте ещё 5 оценок для улучшения точности',
  faction: {
    name: 'Созерцатели',
    rank: 'Мастер',
    icon: '👁️',
  },
})

const onHover = () => {
  showTooltip.value = true
}

const onLeave = () => {
  showTooltip.value = false
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
}

const handleUpdateTest = () => {
  emit('update-test')
}

const handleCompareWithFriend = () => {
  emit('compare-friend')
}

const handleViewRecommendations = () => {
  emit('view-recommendations')
}
</script>

<style scoped>
.anime-dna-indicator {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* SVG с линиями */
.dna-lines {
  width: 44px;
  height: 44px;
  cursor: pointer;
  transition: transform 0.2s var(--transition-smooth);
}

.dna-lines:hover {
  transform: scale(1.1);
}

.dna-lines:active {
  transform: scale(0.95);
}

/* Вращающиеся линии */
.dna-line-inner {
  animation: spin-slow 6s linear infinite reverse;
  transform-origin: center;
}

.dna-line-middle {
  animation: spin-medium 8s linear infinite;
  transform-origin: center;
}

.dna-line-outer {
  animation: spin-fast 10s linear infinite reverse;
  transform-origin: center;
}

.dna-lines:hover .dna-line-inner,
.dna-lines:hover .dna-line-middle,
.dna-lines:hover .dna-line-outer {
  animation-duration: 3s, 4s, 5s;
}

/* Тултип */
.dna-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  padding: 8px 12px;
  background-color: var(--color-background-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-divider);
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 100;
}

.dna-tooltip::after {
  content: '';
  position: absolute;
  top: -4px;
  right: 12px;
  width: 8px;
  height: 8px;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-bottom: none;
  border-right: none;
  transform: rotate(45deg);
}

/* Панель */
.dna-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background-color: var(--color-background-secondary);
  box-shadow: var(--shadow-modal);
  z-index: 1000;
  overflow-y: auto;
  padding: 24px;
}

.dna-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.dna-panel-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.dna-panel-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--color-text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
  border: none;
}

.dna-panel-close:hover {
  background-color: var(--color-background-surface);
  color: var(--color-text);
}

.dna-panel-divider {
  height: 1px;
  background-color: var(--color-divider);
  margin-bottom: 24px;
}

/* Секции панели */
.dna-section {
  margin-bottom: 24px;
}

.dna-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  margin: 0 0 12px 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Тип личности */
.dna-type-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dna-type-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-pink) 100%);
  border-radius: 12px;
  color: var(--color-text);
}

.dna-type-info {
  flex: 1;
}

.dna-type-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0 0 4px 0;
}

.dna-type-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

/* Шкалы */
.dna-scales {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dna-scale {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dna-scale-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dna-scale-name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.dna-scale-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.dna-scale-bar {
  height: 8px;
  background-color: var(--color-background-active);
  border-radius: 4px;
  overflow: hidden;
}

.dna-scale-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s var(--transition-smooth);
}

/* Предсказания */
.dna-predictions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dna-prediction {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: var(--color-background-surface);
  border-radius: 8px;
}

.dna-prediction-info {
  flex: 1;
}

.dna-prediction-anime {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.dna-prediction-ratings {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
  display: flex;
  gap: 12px;
}

.dna-prediction-accurate {
  color: var(--color-accent-teal);
}

/* Прогресс */
.dna-progress-header {
  margin-bottom: 8px;
}

.dna-progress-label {
  font-size: 14px;
  color: var(--color-text-primary);
  margin: 0;
}

.dna-progress-bar {
  height: 8px;
  background-color: var(--color-background-active);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.dna-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent) 0%, var(--color-accent-pink) 100%);
  border-radius: 4px;
  transition: width 0.5s var(--transition-smooth);
}

.dna-progress-tip {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin: 0;
}

/* Фракция */
.dna-faction {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: var(--color-background-surface);
  border-radius: 12px;
}

.dna-faction-icon {
  font-size: 32px;
}

.dna-faction-info {
  flex: 1;
}

.dna-faction-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.dna-faction-rank {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Кнопки действий */
.dna-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 32px;
}

.dna-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
}

.dna-action-btn:hover {
  background-color: var(--color-background-surface);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.dna-action-btn.primary {
  background-color: var(--color-accent);
  color: var(--color-text);
  border-color: var(--color-accent);
}

.dna-action-btn.primary:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

/* Оверлей */
.dna-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 999;
}

/* Анимации */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s var(--transition-smooth);
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
}

/* Адаптивность */
@media (max-width: 767px) {
  .dna-panel {
    width: 100%;
  }
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes spin-medium {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes spin-fast {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
