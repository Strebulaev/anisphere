<template>
  <div class="playlist-detail">
    <div class="playlist-info">
      <div class="header">
        <div class="titles">
          <h1 class="title">{{ playlist.title }}</h1>
          <p v-if="playlist.description" class="description">{{ playlist.description }}</p>
        </div>
        <div class="actions" v-if="isOwner">
          <button class="edit-btn" @click="$emit('edit', playlist)">
            ✏️ Изменить
          </button>
          <button class="delete-btn" @click="deletePlaylist">
            🗑️ Удалить
          </button>
        </div>
        <div class="actions" v-else-if="!isOwner && playlist.is_public">
          <button
            class="favorite-btn"
            :class="{ active: playlist.is_favorited }"
            @click="$emit('toggle-favorite', playlist)"
          >
            {{ playlist.is_favorited ? '♥ В избранном' : '♡ В избранное' }}
          </button>
          <button class="duplicate-btn" @click="$emit('duplicate', playlist)">
            📋 Копировать
          </button>
        </div>
      </div>

      <div class="meta">
        <span class="meta-item">
          👤 {{ playlist.user_username }}
        </span>
        <span class="meta-item">
          📺 {{ playlist.items_count }} аниме
        </span>
        <span class="meta-item">
          📅 {{ formatDate(playlist.created_at) }}
        </span>
        <span v-if="playlist.favorites_count" class="meta-item favorite-count">
          ♥ {{ playlist.favorites_count }}
        </span>
      </div>
    </div>

    <div class="playlist-items" v-if="playlist.items.length > 0">
      <div class="items-header">
        <h2>Список аниме ({{ playlist.items.length }})</h2>
        <div class="sort-controls" v-if="isOwner">
          <select v-model="sortBy" class="sort-select">
            <option value="created_at">По дате добавления</option>
            <option value="anime__title_ru">По названию</option>
          </select>
        </div>
      </div>

      <div class="items-list">
        <div
          v-for="item in sortedItems"
          :key="item.id"
          class="item-card"
        >
          <img
            v-if="item.anime_poster"
            :src="item.anime_poster"
            :alt="item.anime_title"
            class="item-poster"
          />
          <div v-else class="item-poster placeholder">🎌</div>

          <div class="item-info">
            <h3 class="item-title">{{ item.anime_title }}</h3>
            <div v-if="item.episode_number" class="item-episode">
              Эпизод: {{ item.episode_number }}
            </div>
            <div v-if="item.source_url" class="item-source">
              <a :href="item.source_url" target="_blank" rel="noopener">
                🔗 Смотреть
              </a>
            </div>
            <div v-if="item.notes" class="item-notes">
              {{ item.notes }}
            </div>
          </div>

          <div class="item-actions" v-if="isOwner">
            <button class="remove-btn" @click="removeItem(item.id)">
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <span class="icon">📭</span>
      <p>В этом плейлисте пока нет аниме</p>
      <button v-if="isOwner" class="add-btn" @click="$emit('add-anime')">
        + Добавить аниме
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Playlist, PlaylistItem } from '@/api/playlists'
import playlistsApi from '@/api/playlists'

interface Props {
  playlist: Playlist
  currentUserId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'edit': [playlist: Playlist]
  'delete': [playlist: Playlist]
  'duplicate': [playlist: Playlist]
  'toggle-favorite': [playlist: Playlist]
  'add-anime': []
  'removed': []
}>()

const sortBy = ref('created_at')

const isOwner = computed(() => {
  return props.currentUserId && props.playlist.user === props.currentUserId
})

const sortedItems = computed(() => {
  const items = [...props.playlist.items]
  if (sortBy.value === 'anime__title_ru') {
    return items.sort((a, b) => a.anime_title.localeCompare(b.anime_title))
  }
  return items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

const removeItem = async (itemId: number) => {
  if (!confirm('Удалить аниме из плейлиста?')) return

  try {
    await playlistsApi.removeFromPlaylist(props.playlist.id, itemId)
    emit('removed')
  } catch (error) {
    console.error('Ошибка удаления:', error)
    alert('Не удалось удалить элемент')
  }
}

const deletePlaylist = async () => {
  if (!confirm('Удалить плейлист? Это действие нельзя отменить.')) return

  try {
    await playlistsApi.deletePlaylist(props.playlist.id)
    emit('delete', props.playlist)
  } catch (error) {
    console.error('Ошибка удаления плейлиста:', error)
    alert('Не удалось удалить плейлист')
  }
}
</script>

<style scoped>
.playlist-detail {
  background: var(--color-background);
  min-height: 100vh;
  padding-bottom: 2rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: var(--color-background-surface);
  border-radius: 0.5rem;
  color: var(--color-text-tertiary);
  text-decoration: none;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  transition: all 0.2s;
}

.back-link:hover {
  color: var(--color-accent);
  background: var(--color-background-active);
}

.header {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.poster {
  width: 180px;
  height: 180px;
  object-fit: cover;
  border-radius: 0.75rem;
  flex-shrink: 0;
}

.poster.placeholder {
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  color: white;
}

.info {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.private-badge {
  padding: 0.25rem 0.625rem;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.description {
  color: var(--color-text-tertiary);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  background: var(--color-background);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(58, 134, 255, 0.1);
}

.delete-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.favorite-btn.active {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.duplicate-btn:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.favorite-count {
  color: #ef4444;
}

.items-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.items-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.sort-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background: var(--color-background);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.item-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.75rem;
  transition: all 0.2s;
}

.item-card:hover {
  border-color: var(--color-accent);
}

.item-poster {
  width: 60px;
  height: 85px;
  object-fit: cover;
  border-radius: 0.375rem;
  flex-shrink: 0;
}

.item-poster.placeholder {
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.375rem 0;
}

.item-episode,
.item-source,
.item-notes {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

.item-source a {
  color: var(--color-accent);
  text-decoration: none;
}

.item-source a:hover {
  text-decoration: underline;
}

.item-actions {
  flex-shrink: 0;
}

.remove-btn {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-divider);
  border-radius: 0.375rem;
  background: var(--color-background);
  color: var(--color-text-disabled);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
}

.empty-state .icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-state p {
  color: var(--color-text-tertiary);
  margin-bottom: 1.5rem;
}

.add-btn {
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover {
  background: var(--color-accent-hover);
}
</style>