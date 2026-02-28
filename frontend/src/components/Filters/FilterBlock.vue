<template>
  <div class="filter-block" :class="{ collapsed: isCollapsed }">
    <div class="filter-header">
      <h3 class="filter-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
        Фильтры
      </h3>
      <div class="filter-actions">
        <button
          @click="toggleCollapse"
          class="filter-toggle-btn"
          type="button"
          :title="isCollapsed ? 'Развернуть' : 'Свернуть'"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            :class="{ rotated: !isCollapsed }"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      </div>
    </div>

    <transition name="filter-content">
      <div v-show="!isCollapsed" class="filter-content">
        <slot></slot>

        <div class="filter-footer">
          <button @click="handleApply" class="btn btn-primary apply-btn" type="button">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Применить
          </button>
          <button @click="handleReset" class="btn btn-outline reset-btn" type="button">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            Сбросить все
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface Props {
  collapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false
})

const emit = defineEmits<{
  apply: []
  reset: []
}>()

const STORAGE_KEY = 'filter-block-collapsed'
const isCollapsed = ref(props.collapsed)

const loadState = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved !== null) {
      isCollapsed.value = saved === 'true'
    }
  } catch (e) {
    console.error('Failed to load filter state:', e)
  }
}

const saveState = () => {
  try {
    localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
  } catch (e) {
    console.error('Failed to save filter state:', e)
  }
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  saveState()
}

const handleApply = () => {
  emit('apply')
}

const handleReset = () => {
  emit('reset')
}

onMounted(() => {
  loadState()
})

watch(isCollapsed, saveState)
</script>

<style scoped>
.filter-block {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  border: 1px solid var(--color-divider);
  overflow: hidden;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-divider);
  background-color: var(--color-background-surface);
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
}

.filter-toggle-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.filter-toggle-btn:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.filter-toggle-btn svg {
  transition: transform 0.3s var(--transition-smooth);
}

.filter-toggle-btn svg.rotated {
  transform: rotate(180deg);
}

.filter-content {
  padding: 1.25rem;
}

.filter-footer {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-outline {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.btn-outline:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent-pink);
  color: var(--color-accent-pink);
}

.filter-content-enter-active,
.filter-content-leave-active {
  transition: all 0.3s var(--transition-smooth);
  max-height: 1000px;
  overflow: hidden;
}

.filter-content-enter-from,
.filter-content-leave-to {
  max-height: 0;
  opacity: 0;
}

@media (max-width: 768px) {
  .filter-header {
    padding: 0.875rem 1rem;
  }

  .filter-content {
    padding: 1rem;
  }

  .filter-footer {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
