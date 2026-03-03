<template>
  <div class="feed-filters">
    <!-- Toggle Button -->
    <div class="filters-header" @click="isOpen = !isOpen">
      <span class="filters-title">
        🔧 Фильтры
        <span v-if="activeCount > 0" class="active-badge">{{ activeCount }}</span>
      </span>
      <span class="toggle-icon">{{ isOpen ? '▲' : '▼' }}</span>
    </div>

    <!-- Filters Panel -->
    <transition name="expand">
      <div v-if="isOpen" class="filters-panel">
        <!-- Checkboxes -->
        <div class="filter-section">
          <div class="checkbox-grid">
            <label class="checkbox-item">
              <input type="checkbox" v-model="localFilters.myPosts" />
              <span>Мои посты</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="localFilters.following" />
              <span>Подписки</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="localFilters.fromGroups" />
              <span>Посты из групп</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="localFilters.withAnime" />
              <span>С аниме</span>
            </label>
          </div>
        </div>

        <!-- Date Filter -->
        <div class="filter-section">
          <span class="section-label">Период</span>
          <div class="btn-group">
            <button
              v-for="period in periods"
              :key="period.value"
              class="period-btn"
              :class="{ active: localFilters.period === period.value }"
              @click="localFilters.period = period.value"
            >{{ period.label }}</button>
          </div>
        </div>

        <!-- Sort -->
        <div class="filter-section">
          <span class="section-label">Сортировка</span>
          <div class="btn-group">
            <button
              v-for="sort in sortOptions"
              :key="sort.value"
              class="sort-btn"
              :class="{ active: localFilters.sort === sort.value }"
              @click="localFilters.sort = sort.value"
            >{{ sort.label }}</button>
          </div>
        </div>

        <!-- Actions -->
        <div class="filter-actions">
          <button class="btn-reset" @click="resetFilters">Сбросить</button>
          <button class="btn-apply" @click="applyFilters">Применить</button>
        </div>
      </div>
    </transition>

    <!-- Active Filter Tags -->
    <div v-if="activeTags.length > 0" class="active-tags">
      <span
        v-for="tag in activeTags"
        :key="tag.key"
        class="filter-tag"
        @click="removeFilter(tag.key)"
      >
        {{ tag.label }} ✕
      </span>
      <button class="clear-all" @click="resetFilters">Сбросить всё</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

export interface FeedFilters {
  myPosts: boolean
  following: boolean
  fromGroups: boolean
  withAnime: boolean
  period: 'all' | 'month' | 'week' | 'day'
  sort: 'new' | 'old' | 'best' | 'discussed'
}

export type FeedFiltersType = FeedFilters

const props = defineProps<{
  modelValue: FeedFilters
}>()

const emit = defineEmits<{
  'update:modelValue': [filters: FeedFilters]
  apply: [filters: FeedFilters]
}>()

const isOpen = ref(false)

const defaultFilters: FeedFilters = {
  myPosts: false,
  following: false,
  fromGroups: false,
  withAnime: false,
  period: 'all',
  sort: 'new',
}

const localFilters = ref<FeedFilters>({ ...props.modelValue })

const periods: { value: 'all' | 'month' | 'week' | 'day'; label: string }[] = [
  { value: 'all', label: 'Всё время' },
  { value: 'month', label: 'Месяц' },
  { value: 'week', label: 'Неделя' },
  { value: 'day', label: 'День' },
]

const sortOptions: { value: 'new' | 'old' | 'best' | 'discussed'; label: string }[] = [
  { value: 'new', label: 'Новые' },
  { value: 'old', label: 'Старые' },
  { value: 'best', label: 'Лучшие' },
  { value: 'discussed', label: 'Обсуждаемые' },
]

const activeCount = computed(() => {
  let c = 0
  if (localFilters.value.myPosts) c++
  if (localFilters.value.following) c++
  if (localFilters.value.fromGroups) c++
  if (localFilters.value.withAnime) c++
  if (localFilters.value.period !== 'all') c++
  if (localFilters.value.sort !== 'new') c++
  return c
})

const activeTags = computed(() => {
  const tags: { key: string; label: string }[] = []
  if (localFilters.value.myPosts) tags.push({ key: 'myPosts', label: 'Мои посты' })
  if (localFilters.value.following) tags.push({ key: 'following', label: 'Подписки' })
  if (localFilters.value.fromGroups) tags.push({ key: 'fromGroups', label: 'Из групп' })
  if (localFilters.value.withAnime) tags.push({ key: 'withAnime', label: 'С аниме' })
  if (localFilters.value.period !== 'all') {
    const p = periods.find(x => x.value === localFilters.value.period)
    if (p) tags.push({ key: 'period', label: p.label as string })
  }
  if (localFilters.value.sort !== 'new') {
    const s = sortOptions.find(x => x.value === localFilters.value.sort)
    if (s) tags.push({ key: 'sort', label: s.label as string })
  }
  return tags
})

const removeFilter = (key: string) => {
  if (key === 'period') localFilters.value.period = 'all'
  else if (key === 'sort') localFilters.value.sort = 'new'
  else (localFilters.value as any)[key] = false
  applyFilters()
}

const resetFilters = () => {
  localFilters.value = { ...defaultFilters }
  applyFilters()
}

const applyFilters = () => {
  emit('update:modelValue', { ...localFilters.value })
  emit('apply', { ...localFilters.value })
}
</script>

<style scoped>
.feed-filters {
  background: #111;
  border-radius: 12px;
  overflow: hidden;
}

.filters-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.filters-header:hover {
  background: #161616;
}

.filters-title {
  color: #aaa;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.active-badge {
  background: #667eea;
  color: white;
  font-size: 0.7rem;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.toggle-icon {
  color: #555;
  font-size: 0.75rem;
}

.filters-panel {
  border-top: 1px solid #1a1a1a;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-label {
  color: #666;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #aaa;
  font-size: 0.875rem;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"] {
  accent-color: #667eea;
  width: 14px;
  height: 14px;
}

.btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.period-btn,
.sort-btn {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.period-btn.active,
.sort-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.period-btn:hover:not(.active),
.sort-btn:hover:not(.active) {
  background: #222;
  color: #aaa;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-reset {
  background: none;
  border: 1px solid #333;
  color: #666;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-apply {
  background: #667eea;
  border: none;
  color: white;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
}

/* Active Tags */
.active-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem 1rem 0.75rem;
  border-top: 1px solid #1a1a1a;
}

.filter-tag {
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.3);
  color: #8b9ef5;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tag:hover {
  background: rgba(102, 126, 234, 0.25);
}

.clear-all {
  background: none;
  border: none;
  color: #555;
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
}

.clear-all:hover {
  color: #888;
}

/* Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 400px;
  opacity: 1;
}
</style>
