<template>
  <div class="sort-dropdown" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      class="sort-button"
      type="button"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <polyline points="19 12 12 19 5 12"/>
      </svg>
      <span class="sort-label">Сортировка:</span>
      <span class="sort-value">{{ currentSortLabel }}</span>
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        :class="{ rotated: isOpen }"
      >
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <transition name="dropdown">
      <div v-if="isOpen" class="sort-menu">
        <div class="sort-options">
          <button
            v-for="option in sortOptions"
            :key="option.value"
            @click="selectSort(option.value)"
            :class="['sort-option', { active: currentValue === option.value }]"
            type="button"
          >
            <span class="option-label">{{ option.label }}</span>
            <svg
              v-if="currentValue === option.value"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="check-icon"
            >
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </button>
        </div>

        <div class="sort-direction">
          <span class="direction-label">Направление:</span>
          <div class="direction-buttons">
            <button
              @click="setDirection('asc')"
              :class="['direction-btn', { active: direction === 'asc' }]"
              type="button"
              title="По возрастанию"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="19" x2="12" y2="5"/>
                <polyline points="5 12 12 5 19 12"/>
              </svg>
              <span>А-Я</span>
            </button>
            <button
              @click="setDirection('desc')"
              :class="['direction-btn', { active: direction === 'desc' }]"
              type="button"
              title="По убыванию"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <polyline points="19 12 12 19 5 12"/>
              </svg>
              <span>Я-А</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface SortOption {
  value: string
  label: string
}

interface Props {
  modelValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '-score'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const dropdownRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)

const sortOptions: SortOption[] = [
  { value: 'score', label: 'По рейтингу' },
  { value: 'year', label: 'По дате выхода' },
  { value: 'title_ru', label: 'По названию (рус.)' },
  { value: 'title_en', label: 'По названию (англ.)' },
  { value: 'episodes', label: 'По количеству серий' },
  { value: 'created_at', label: 'По дате добавления' },
  { value: 'popularity', label: 'По популярности' }
]

const currentValue = computed(() => {
  return props.modelValue.replace(/^-/, '')
})

const direction = computed(() => {
  return props.modelValue.startsWith('-') ? 'desc' : 'asc'
})

const currentSortLabel = computed(() => {
  const option = sortOptions.find(opt => opt.value === currentValue.value)
  return option ? option.label : 'Сортировка'
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectSort = (value: string) => {
  const newDirection = direction.value === 'desc' ? '-' : ''
  emit('update:modelValue', newDirection + value)
  isOpen.value = false
}

const setDirection = (newDirection: 'asc' | 'desc') => {
  const prefix = newDirection === 'desc' ? '-' : ''
  emit('update:modelValue', prefix + currentValue.value)
}

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.sort-dropdown {
  position: relative;
}

.sort-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  white-space: nowrap;
}

.sort-button:hover {
  border-color: var(--color-accent);
  background-color: var(--color-background-active);
}

.sort-button svg:first-child {
  color: var(--color-text-tertiary);
}

.sort-button svg:last-child {
  transition: transform 0.3s var(--transition-smooth);
}

.sort-button svg:last-child.rotated {
  transform: rotate(180deg);
}

.sort-label {
  color: var(--color-text-secondary);
}

.sort-value {
  color: var(--color-accent);
}

.sort-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 240px;
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-card-hover);
  z-index: 100;
  overflow: hidden;
}

.sort-options {
  padding: 0.5rem;
  border-bottom: 1px solid var(--color-divider-light);
}

.sort-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.625rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
  text-align: left;
}

.sort-option:hover {
  background-color: var(--color-background-surface);
}

.sort-option.active {
  background-color: rgba(58, 134, 255, 0.1);
  color: var(--color-accent);
  font-weight: 600;
}

.option-label {
  flex: 1;
}

.check-icon {
  color: var(--color-accent);
}

.sort-direction {
  padding: 0.75rem 0.5rem;
}

.direction-label {
  display: block;
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.direction-buttons {
  display: flex;
  gap: 0.5rem;
}

.direction-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.direction-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.direction-btn.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s var(--transition-smooth);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 768px) {
  .sort-menu {
    right: -8px;
    left: -8px;
    min-width: auto;
  }

  .sort-button {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }

  .sort-label {
    display: none;
  }
}
</style>
