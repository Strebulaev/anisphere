<template>
  <transition name="suggestions">
    <div v-if="show" class="search-suggestions" @click.stop>
      <div v-if="isLoading" class="suggestions-loading">
        <div class="loading-spinner"></div>
        <span>Поиск...</span>
      </div>

      <template v-else>
        <div
          v-for="category in enabledCategories"
          :key="category.id"
          v-show="results[category.id as keyof SearchResults]?.length"
          class="suggestions-section"
        >
          <div class="suggestions-section-title">
            <component :is="getCategoryIcon(category.id)" width="12" height="12" class="section-icon" />
            {{ category.name }}
          </div>

          <div
            v-for="(item, index) in results[category.id as keyof SearchResults]"
            :key="item.id"
            :class="['suggestion-item', { active: selectedIndex === getGlobalIndex(category.id, index) }]"
            @click="handleSelect(category.id, item)"
            @mouseenter="selectedIndex = getGlobalIndex(category.id, index)"
          >
            <component
              :is="getSuggestionItem(category.id)"
              :item="item"
              :category="category"
            />
          </div>
        </div>

        <div v-if="!hasResults" class="suggestions-empty">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p>Ничего не найдено</p>
        </div>
      </template>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, h } from 'vue'
import { getMediaUrl } from '@/api/client'
import {
  type SearchResults,
  type SearchCategory,
  type AnimeResult,
  type UserResult,
  type PlaylistResult,
  type GroupResult
} from '@/composables/useSearch'

interface Props {
  show: boolean
  results: SearchResults
  isLoading: boolean
  categories?: SearchCategory[]
}

const props = withDefaults(defineProps<Props>(), {
  categories: () => []
})

const emit = defineEmits<{
  close: []
  select: [type: string, item: any]
}>()

const selectedIndex = ref(-1)

const enabledCategories = computed(() => {
  return props.categories.filter(cat => cat.enabled)
})

const hasResults = computed(() => {
  return Object.values(props.results).some(arr => arr && arr.length > 0)
})

const totalItems = computed(() => {
  return enabledCategories.value.reduce((total, cat) => {
    return total + (props.results[cat.id as keyof SearchResults]?.length || 0)
  }, 0)
})

const getGlobalIndex = (categoryId: string, index: number) => {
  let globalIndex = 0
  for (const cat of enabledCategories.value) {
    if (cat.id === categoryId) {
      return globalIndex + index
    }
    globalIndex += props.results[cat.id as keyof SearchResults]?.length || 0
  }
  return index
}

const getCategoryIcon = (categoryId: string) => {
  const icons: Record<string, any> = {
    anime: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
      h('rect', { x: 2, y: 2, width: 20, height: 20, rx: 2 }),
      h('path', { d: 'M12 2v20M2 12h20' })
    ]),
    users: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
      h('path', { d: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2' }),
      h('circle', { cx: 12, cy: 7, r: 4 })
    ]),
    playlists: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
      h('path', { d: 'M9 18V5l12-2v13' }),
      h('circle', { cx: 6, cy: 18, r: 3 }),
      h('circle', { cx: 18, cy: 16, r: 3 })
    ]),
    groups: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
      h('path', { d: 'M17 21v-2a4 4 0 0 0-3-5.74' }),
      h('path', { d: 'M9 21v-2a4 4 0 0 1 4-4' }),
      h('circle', { cx: 9, cy: 7, r: 4 }),
      h('circle', { cx: 17, cy: 5, r: 2 })
    ])
  }
  return icons[categoryId] || icons.anime
}

const getSuggestionItem = (categoryId: string) => {
  const components: Record<string, any> = {
    anime: AnimeSuggestionItem,
    users: UserSuggestionItem,
    playlists: PlaylistSuggestionItem,
    groups: GroupSuggestionItem
  }
  return components[categoryId] || AnimeSuggestionItem
}

const handleSelect = (category: string, item: any) => {
  emit('select', category, item)
  emit('close')
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!props.show) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, totalItems.value - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
  } else if (e.key === 'Enter' && selectedIndex.value >= 0) {
    e.preventDefault()
    let currentIndex = 0
    for (const cat of enabledCategories.value) {
      const items = props.results[cat.id as keyof SearchResults]
      if (items && currentIndex + items.length > selectedIndex.value) {
        handleSelect(cat.id, items[selectedIndex.value - currentIndex])
        return
      }
      currentIndex += items?.length || 0
    }
  } else if (e.key === 'Escape') {
    emit('close')
  }
}

watch(() => props.show, (newShow) => {
  if (newShow) {
    selectedIndex.value = -1
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Единый компонент для миниатюры любого типа
const SuggestionThumbnail = {
  props: ['item', 'type'],
  setup(props: { item: any, type: string }) {
    return () => {
      const { item, type } = props
      
      // Для аниме
      if (type === 'anime') {
        return h('div', { class: 'suggestion-thumbnail' }, [
          item.poster_url
            ? h('img', { 
                src: getMediaUrl(item.poster_url), 
                alt: item.title_ru || item.title_en,
                class: 'thumbnail-img'
              })
            : h('div', { class: 'thumbnail-placeholder' }, [
                h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                  h('rect', { x: 2, y: 2, width: 20, height: 20, rx: 2 })
                ])
              ])
        ])
      }
      
      // Для пользователей
      if (type === 'users') {
        return h('div', { class: 'suggestion-thumbnail rounded-full' }, [
          item.avatar_url
            ? h('img', { 
                src: getMediaUrl(item.avatar_url), 
                alt: item.display_name || item.username,
                class: 'thumbnail-img'
              })
            : h('div', { class: 'thumbnail-placeholder' }, (item.display_name || item.username)?.[0]?.toUpperCase())
        ])
      }
      
      // Для групп
      if (type === 'groups') {
        return h('div', { class: 'suggestion-thumbnail rounded' }, [
          item.avatar_url
            ? h('img', { 
                src: getMediaUrl(item.avatar_url), 
                alt: item.name,
                class: 'thumbnail-img'
              })
            : h('div', { class: 'thumbnail-placeholder' }, item.name?.[0]?.toUpperCase())
        ])
      }
      
      // Для плейлистов
      if (type === 'playlists') {
        return h('div', { class: 'suggestion-thumbnail playlist' }, [
          h('div', { class: 'playlist-mini-posters' }, [
            ...(item.items?.slice(0, 4).map((anime: any) =>
              h('div', { class: 'mini-poster' }, [
                anime.poster_url 
                  ? h('img', { 
                      src: getMediaUrl(anime.poster_url), 
                      alt: anime.title_ru || anime.title_en,
                      class: 'thumbnail-img'
                    }) 
                  : null
              ])
            ) || [])
          ])
        ])
      }
      
      return null
    }
  }
}

const AnimeSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: AnimeResult }) {
    return () => h('div', { class: 'suggestion-content' }, [
      h(SuggestionThumbnail, { item: props.item, type: 'anime' }),
      h('div', { class: 'suggestion-info' }, [
        h('div', { class: 'suggestion-title' }, props.item.title_ru || props.item.title_en),
        h('div', { class: 'suggestion-meta' }, [
          props.item.year ? h('span', {}, props.item.year.toString()) : null,
          props.item.episodes ? h('span', {}, `${props.item.episodes} эп.`) : null,
          props.item.score ? h('span', { class: 'suggestion-rating' }, `★ ${props.item.score}`) : null
        ].filter(Boolean))
      ])
    ])
  }
}

const UserSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: UserResult }) {
    return () => h('div', { class: 'suggestion-content' }, [
      h(SuggestionThumbnail, { item: props.item, type: 'users' }),
      h('div', { class: 'suggestion-info' }, [
        h('div', { class: 'suggestion-title' }, props.item.display_name || props.item.username),
        h('div', { class: 'suggestion-meta' }, `@${props.item.username}`)
      ])
    ])
  }
}

const PlaylistSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: PlaylistResult }) {
    return () => h('div', { class: 'suggestion-content' }, [
      h(SuggestionThumbnail, { item: props.item, type: 'playlists' }),
      h('div', { class: 'suggestion-info' }, [
        h('div', { class: 'suggestion-title' }, props.item.title),
        h('div', { class: 'suggestion-meta' }, `${props.item.items?.length || 0} аниме`)
      ])
    ])
  }
}

const GroupSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: GroupResult }) {
    return () => h('div', { class: 'suggestion-content' }, [
      h(SuggestionThumbnail, { item: props.item, type: 'groups' }),
      h('div', { class: 'suggestion-info' }, [
        h('div', { class: 'suggestion-title' }, props.item.name),
        h('div', { class: 'suggestion-meta' }, `${props.item.members_count || 0} участников`)
      ])
    ])
  }
}
</script>

<style scoped>
.search-suggestions {
  position: absolute;
  top: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  max-width: 90vw;
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-card-hover);
  max-height: 450px;
  overflow-y: auto;
  z-index: 1000;
}

/* Если поисковая строка имеет определенную ширину, можно сделать так:
.parent-search-container {
  position: relative;
}
.search-suggestions {
  width: min(400px, calc(100vw - 32px));
}
*/

.suggestions-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.suggestions-section {
  padding: 4px 0;
}

.suggestions-section:not(:last-child) {
  border-bottom: 1px solid var(--color-divider-light);
}

.suggestions-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-icon {
  opacity: 0.6;
  width: 14px;
  height: 14px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.1s;
  min-height: 48px;
}

.suggestion-item:hover,
.suggestion-item.active {
  background-color: var(--color-background-surface);
}

.suggestion-content {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

/* Единый размер для всех миниатюр - 32x32 */
.suggestion-thumbnail {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}

.suggestion-thumbnail.rounded-full {
  border-radius: 50%;
}

.suggestion-thumbnail.rounded {
  border-radius: 6px;
}

.suggestion-thumbnail.playlist {
  background: transparent;
  padding: 0;
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  color: var(--color-text-tertiary);
  font-size: 14px;
  font-weight: 600;
}

.thumbnail-placeholder svg {
  width: 18px;
  height: 18px;
}

/* Плейлист мини постеры */
.playlist-mini-posters {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 1px;
  width: 100%;
  height: 100%;
}

.mini-poster {
  width: 100%;
  height: 100%;
  background-color: var(--color-background-surface);
  overflow: hidden;
}

.mini-poster .thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.suggestion-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggestion-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.suggestion-meta {
  font-size: 11px;
  color: var(--color-text-tertiary);
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
  line-height: 1.3;
}

.suggestion-rating {
  color: var(--color-accent-orange);
  font-weight: 600;
}

.suggestions-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  color: var(--color-text-tertiary);
  text-align: center;
}

.suggestions-empty svg {
  opacity: 0.4;
  width: 32px;
  height: 32px;
}

.suggestions-empty p {
  margin: 0;
  font-size: 13px;
}

.suggestions-enter-active,
.suggestions-leave-active {
  transition: all 0.15s var(--transition-smooth);
}

.suggestions-enter-from,
.suggestions-leave-to {
  opacity: 0;
  transform: translateY(-4px) translateX(-50%);
}
</style>