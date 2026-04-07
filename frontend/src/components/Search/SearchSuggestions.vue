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

// Перевод типов аниме на русский
const animeKindMap: Record<string, string> = {
  tv: 'ТВ',
  movie: 'Фильм',
  ova: 'OVA',
  special: 'Спешл',
  ona: 'ONA',
  music: 'Музыка',
  cm: 'CM',
  tv_special: 'ТВ спешл',
}

const AnimeSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: AnimeResult }) {
    const kindText = computed(() => {
      if (!props.item.kind) return null
      return animeKindMap[props.item.kind] || props.item.kind
    })
    
    return () => h('div', { class: 'suggestion-content anime-suggestion' }, [
      // Постер как в плейлисте - 44x62
      h('div', { class: 'suggestion-poster' }, [
        props.item.poster_url
          ? h('img', { 
              src: getMediaUrl(props.item.poster_url), 
              alt: props.item.title_ru || props.item.title_en,
              class: 'poster-img'
            })
          : h('div', { class: 'poster-placeholder' }, [
              h('svg', { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                h('rect', { x: 2, y: 2, width: 20, height: 20, rx: 2 })
              ])
            ])
      ]),
      h('div', { class: 'suggestion-info' }, [
        h('div', { class: 'suggestion-title' }, props.item.title_ru || props.item.title_en),
        // Meta как в плейлисте: Год · Тип · Эпизоды · Рейтинг
        h('div', { class: 'suggestion-meta' }, [
          props.item.year ? h('span', { class: 'meta-chip' }, props.item.year) : null,
          kindText.value ? h('span', { class: 'meta-chip kind' }, kindText.value) : null,
          props.item.episodes ? h('span', { class: 'meta-chip' }, `${props.item.episodes} эп.`) : null,
          props.item.score ? h('span', { class: 'meta-chip score' }, `🌠 ${Number(props.item.score).toFixed(1)}`) : null
        ].filter(Boolean))
      ])
    ])
  }
}

const UserSuggestionItem = {
  props: ['item', 'category'],
  setup(props: { item: UserResult }) {
    return () => h('div', { class: 'suggestion-content user-suggestion' }, [
      // Аватар как постер - 36x50
      h('div', { class: 'suggestion-avatar' }, [
        props.item.avatar_url
          ? h('img', { 
              src: getMediaUrl(props.item.avatar_url), 
              alt: props.item.display_name || props.item.username,
              class: 'avatar-img'
            })
          : h('div', { class: 'avatar-placeholder' }, 
              (props.item.display_name || props.item.username)?.[0]?.toUpperCase() || '?'
            )
      ]),
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
    return () => h('div', { class: 'suggestion-content playlist-suggestion' }, [
      // Мини постеры как в плейлисте
      h('div', { class: 'suggestion-poster playlist-mini' }, [
        h('div', { class: 'playlist-mini-posters' }, [
          ...(props.item.items?.slice(0, 4).map((anime: any) =>
            h('div', { class: 'mini-poster' }, [
              anime.poster_url 
                ? h('img', { 
                    src: getMediaUrl(anime.poster_url), 
                    alt: anime.title_ru || anime.title_en,
                    class: 'poster-img'
                  }) 
                : h('div', { class: 'poster-placeholder-sm' })
            ])
          ) || [])
        ])
      ]),
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
    return () => h('div', { class: 'suggestion-content group-suggestion' }, [
      // Аватар группы как постер - 36x50
      h('div', { class: 'suggestion-avatar' }, [
        props.item.avatar_url
          ? h('img', { 
              src: getMediaUrl(props.item.avatar_url), 
              alt: props.item.name,
              class: 'avatar-img'
            })
          : h('div', { class: 'avatar-placeholder group' }, 
              props.item.name?.[0]?.toUpperCase() || '?'
            )
      ]),
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
  left: 0;
  right: 0;
  width: 100%;
  min-width: 280px;
  max-width: 360px;
  background-color: var(--color-background-secondary);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  box-shadow: var(--shadow-card-hover);
  max-height: 400px;
  overflow-y: auto;
  z-index: 1000;
}

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
  padding: 6px 10px;
  cursor: pointer;
  transition: background-color 0.1s;
  min-height: 40px;
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

/* Аниме карточка - точно как в плейлисте */
.anime-suggestion .suggestion-poster {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}

.anime-suggestion .poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.anime-suggestion .poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-active);
  color: var(--color-text-tertiary);
}

.anime-suggestion .poster-placeholder svg {
  width: 18px;
  height: 18px;
}

/* Пользователь - карточка как аниме */
.user-suggestion .suggestion-avatar {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-suggestion .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.user-suggestion .avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  font-size: 0.875rem;
  font-weight: 700;
}

/* Для остальных типов (playlists, groups) - старый стиль */
.suggestion-thumbnail {
  width: 28px;
  height: 28px;
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

/* Плейлист мини постеры - как в плейлисте */
.playlist-suggestion .suggestion-poster {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
}

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

.mini-poster .poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder-sm {
  width: 100%;
  height: 100%;
  background-color: var(--color-background-active);
}

/* Группа - карточка как аниме */
.group-suggestion .suggestion-avatar {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}

.group-suggestion .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.group-suggestion .avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
  font-size: 0.875rem;
  font-weight: 700;
}

.group-suggestion .avatar-placeholder.group {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.suggestion-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggestion-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.suggestion-meta {
  font-size: 0.72rem;
  color: var(--color-text-tertiary);
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
  line-height: 1.2;
}

/* Meta chips как в плейлисте */
.meta-chip {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  background: var(--color-background-active);
}

.meta-chip.kind {
  text-transform: uppercase;
  font-weight: 600;
  font-size: 10px;
  background: var(--color-background-surface);
}

.meta-chip.score {
  background: transparent;
  color: #f59e0b;
  font-weight: 600;
  padding: 0;
}

.suggestion-rating {
  color: #f59e0b;
  font-weight: 600;
}

.suggestion-kind {
  background: var(--color-background-active);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 10px;
  text-transform: uppercase;
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