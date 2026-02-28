<template>
  <div class="recommendations-view">
    <!-- Настройки отображения -->
    <div class="settings-bar">
      <div class="view-modes">
        <button
          v-for="mode in viewModes"
          :key="mode.value"
          @click="setViewMode(mode.value)"
          :class="['mode-btn', { active: displaySettings.viewMode === mode.value }]"
          type="button"
          :title="mode.label"
        >
          <span v-html="mode.icon"></span>
        </button>
      </div>
      
      <div class="settings-actions">
        <button @click="toggleSettingsPanel" class="settings-btn" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Настройки
        </button>
        <button @click="refreshAll" class="refresh-btn" type="button" :disabled="loading">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spin: loading }">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Панель настроек -->
    <transition name="slide">
      <div v-if="showSettingsPanel" class="settings-panel">
        <h3>Настройки рекомендаций</h3>
        
        <div class="setting-group">
          <label>Исключать просмотренное</label>
          <label class="toggle">
            <input type="checkbox" v-model="localSettings.excludeWatched" @change="applySettings" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        
        <div class="setting-group">
          <label>Предпочитаемый год</label>
          <select v-model="localSettings.preferYear" @change="applySettings">
            <option value="mixed">Смешанно</option>
            <option value="new">Только новинки</option>
            <option value="classic">Только классика</option>
          </select>
        </div>
        
        <div class="setting-group">
          <label>Предпочитаемая длина</label>
          <select v-model="localSettings.preferLength" @change="applySettings">
            <option value="any">Любая</option>
            <option value="short">Короткие (до 24 эп.)</option>
            <option value="medium">Средние (24-50)</option>
            <option value="long">Длинные (50+)</option>
          </select>
        </div>
        
        <div class="setting-group">
          <label>Степень риска</label>
          <select v-model="localSettings.riskLevel" @change="applySettings">
            <option value="conservative">Консервативно</option>
            <option value="balanced">Сбалансированно</option>
            <option value="experimental">Экспериментально</option>
          </select>
        </div>
        
        <div class="setting-group">
          <label>Приоритет озвучки</label>
          <select v-model="localSettings.voicePriority" @change="applySettings">
            <option value="any">Не важно</option>
            <option value="yes">С русской озвучкой</option>
            <option value="no">Без озвучки</option>
          </select>
        </div>
      </div>
    </transition>

    <!-- Состояние загрузки -->
    <div v-if="loading" class="loading-state">
      <LoadingState type="skeleton" :count="12" />
    </div>

    <!-- Состояние ошибки -->
    <div v-else-if="error" class="error-state">
      <ErrorState
        title="Не удалось загрузить рекомендации"
        :message="error"
        :show-retry="true"
        @retry="refreshAll"
      />
    </div>

    <!-- Нет данных для рекомендаций -->
    <div v-else-if="!hasUserData" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>Нужно больше данных</h3>
      <p>Для персонализации рекомендаций нам нужно больше информации о ваших предпочтениях.</p>
      <p>Начните добавлять аниме в коллекцию и оценивать понравившиеся!</p>
      <button @click="goToCatalog" class="action-btn">Перейти в каталог</button>
    </div>

    <!-- Режим: Горизонтальные ленты -->
    <div v-else-if="displaySettings.viewMode === 'horizontal'" class="horizontal-view">
      <div v-for="type in availableTypes" :key="type" class="recommendation-row">
        <div class="row-header">
          <h3>{{ getTypeLabel(type) }}</h3>
          <p>{{ getTypeDescription(type) }}</p>
        </div>
        
        <div v-if="recommendations[type]?.length > 0" class="anime-scroller">
          <AnimeCard
            v-for="anime in recommendations[type]"
            :key="anime.id"
            :anime="anime as any"
            @click="goToDetail(anime)"
          />
        </div>
        <div v-else class="no-results">
          Не удалось загрузить рекомендации
        </div>
      </div>
    </div>

    <!-- Режим: Сетка -->
    <div v-else-if="displaySettings.viewMode === 'grid'" class="grid-view">
      <div class="all-recommendations">
        <div class="grid-header">
          <h3>Все рекомендации</h3>
          <span>{{ allRecommendations.length }} аниме</span>
        </div>
        <div class="anime-grid">
          <AnimeCard
            v-for="anime in allRecommendations"
            :key="anime.id"
            :anime="anime as any"
            @click="goToDetail(anime)"
          />
        </div>
      </div>
    </div>

    <!-- Режим: Только новинки -->
    <div v-else-if="displaySettings.viewMode === 'new'" class="new-view">
      <div class="section-header">
        <h3>Новинки для вас</h3>
        <p>Аниме за последние 2 года</p>
      </div>
      <div class="anime-grid">
        <AnimeCard
          v-for="anime in newAnime"
          :key="anime.id"
          :anime="anime as any"
          @click="goToDetail(anime)"
        />
      </div>
    </div>

    <!-- Режим: Только классика -->
    <div v-else-if="displaySettings.viewMode === 'classic'" class="classic-view">
      <div class="section-header">
        <h3>Классика жанра</h3>
        <p>Легендарные аниме до 2010 года</p>
      </div>
      <div class="anime-grid">
        <AnimeCard
          v-for="anime in classicAnime"
          :key="anime.id"
          :anime="anime as any"
          @click="goToDetail(anime)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AnimeCard from '@/components/Cards/AnimeCard.vue'
import { LoadingState, ErrorState } from '@/components/Info'
import { useRecommendations, type RecommendationType, type RecommendationSettings, type DisplaySettings } from '@/composables/useRecommendations'
import type { Anime } from '@/types'

const router = useRouter()

const {
  recommendations,
  loading,
  error,
  hasUserData,
  availableTypes,
  settings,
  displaySettings,
  fetchRecommendations,
  updateSettings,
  updateDisplaySettings
} = useRecommendations()

// Локальное состояние UI
const showSettingsPanel = ref(false)
const localSettings = reactive<RecommendationSettings>({
  includeAge: true,
  preferLength: 'any',
  preferYear: 'mixed',
  riskLevel: 'balanced',
  excludeWatched: true,
  voicePriority: 'any'
})

// Режимы отображения
const viewModes = [
  { value: 'horizontal' as const, label: 'Ленты', icon: '📊' },
  { value: 'grid' as const, label: 'Сетка', icon: '⊞' },
  { value: 'new' as const, label: 'Новинки', icon: '🆕' },
  { value: 'classic' as const, label: 'Классика', icon: '🏆' }
]

// Вычисляемые свойства
const allRecommendations = computed(() => {
  const all: Anime[] = []
  Object.values(recommendations.value).forEach(list => {
    all.push(...list)
  })
  // Убираем дубликаты по id
  const unique = new Map()
  all.forEach(a => unique.set(a.id, a))
  return Array.from(unique.values())
})

const newAnime = computed(() => {
  const currentYear = new Date().getFullYear()
  return allRecommendations.value.filter(a => a.year && a.year >= currentYear - 2)
})

const classicAnime = computed(() => {
  return allRecommendations.value.filter(a => a.year && a.year <= 2010)
})

// Методы
const getTypeLabel = (type: RecommendationType): string => {
  const labels: Record<RecommendationType, string> = {
    watched: 'На основе просмотренного',
    liked: 'Вам понравятся',
    favorites: 'Похожее на избранное',
    similar_users: 'Популярное у похожих',
    new_genres: 'Откройте новое',
    seasonal: 'Сезонные',
    classic: 'Классика жанра',
    last_watched: 'После ' + (useRecommendations().userAnimeData.value.lastWatched?.title_ru || 'просмотренного')
  }
  return labels[type]
}

const getTypeDescription = (type: RecommendationType): string => {
  const descriptions: Record<RecommendationType, string> = {
    watched: 'Мы рекомендуем это на основе того, что вы смотрели',
    liked: 'Аниме, похожее на то, что вы оценили высоко',
    favorites: 'Потому что вам понравилось в избранном',
    similar_users: 'То, что смотрят люди с похожими вкусами',
    new_genres: 'Попробуйте жанры, которые вы ещё не смотрели',
    seasonal: 'Сезонные новинки и онгоинги',
    classic: 'Must-watch тайтлы в любимых жанрах',
    last_watched: 'Похожее на последнее, что вы смотрели'
  }
  return descriptions[type]
}

const toggleSettingsPanel = () => {
  showSettingsPanel.value = !showSettingsPanel.value
}

const applySettings = () => {
  updateSettings(localSettings)
}

const setViewMode = (mode: DisplaySettings['viewMode']) => {
  updateDisplaySettings({ viewMode: mode })
}

const refreshAll = () => {
  fetchRecommendations()
}

const goToDetail = (anime: Anime) => {
  router.push(`/anime/${anime.id}`)
}

const goToCatalog = () => {
  router.push('/anime?section=catalog')
}

// Синхронизация настроек при загрузке
onMounted(() => {
  Object.assign(localSettings, settings.value)
})
</script>

<style scoped>
.recommendations-view {
  width: 100%;
}

.settings-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background-color: var(--color-background-surface);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
}

.view-modes {
  display: flex;
  gap: 0.5rem;
}

.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 1.125rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: var(--color-accent);
}

.mode-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
}

.settings-actions {
  display: flex;
  gap: 0.5rem;
}

.settings-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.settings-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.settings-panel {
  padding: 1.5rem;
  background-color: var(--color-background-elevated);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
}

.settings-panel h3 {
  margin: 0 0 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
}

.setting-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-divider);
}

.setting-group:last-child {
  border-bottom: none;
}

.setting-group label {
  font-size: 0.875rem;
  color: var(--color-text);
}

.setting-group select {
  padding: 0.5rem 0.75rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
}

.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-divider);
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle input:checked + .toggle-slider {
  background-color: var(--color-accent);
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.5rem;
}

.empty-state p {
  color: var(--color-text-secondary);
  margin: 0.5rem 0;
}

.action-btn {
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  background-color: var(--color-accent);
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: var(--color-accent-hover);
}

/* Горизонтальные ленты */
.horizontal-view {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.recommendation-row {
  width: 100%;
}

.row-header {
  margin-bottom: 1rem;
}

.row-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.25rem;
}

.row-header p {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.anime-scroller {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  scroll-behavior: smooth;
}

.anime-scroller::-webkit-scrollbar {
  height: 8px;
}

.anime-scroller::-webkit-scrollbar-track {
  background: var(--color-background-surface);
  border-radius: 4px;
}

.anime-scroller::-webkit-scrollbar-thumb {
  background: var(--color-divider);
  border-radius: 4px;
}

.anime-scroller::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

.no-results {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-secondary);
  background-color: var(--color-background-surface);
  border-radius: 0.5rem;
}

/* Сетка */
.grid-view .grid-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.grid-view .grid-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.grid-view .grid-header span {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

/* Режимы new и classic */
.new-view .section-header,
.classic-view .section-header {
  margin-bottom: 1.5rem;
}

.new-view .section-header h3,
.classic-view .section-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.25rem;
}

.new-view .section-header p,
.classic-view .section-header p {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
