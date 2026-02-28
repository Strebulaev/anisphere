<template>
  <div class="playlist-detail">
    <div class="playlist-header">
      <div v-if="playlist.cover_urls?.original" class="playlist-cover">
        <img :src="playlist.cover_urls.original" :alt="playlist.title" />
      </div>

      <div class="playlist-info">
        <h1>{{ playlist.title }}</h1>
        <p v-if="playlist.description" class="description">{{ playlist.description }}</p>

        <div class="playlist-meta">
          <span v-if="playlist.user">👤 {{ playlist.user.username }}</span>
          <span>📊 {{ playlist.items_count || playlist.items?.length || 0 }} аниме</span>
          <span>❤️ {{ playlist.favorites_count || 0 }} в избранном</span>
        </div>

        <div class="playlist-actions" v-if="currentUserId">
          <button
            @click="$emit('toggle-favorite', playlist)"
            :class="['action-btn', 'favorite-btn', { active: playlist.is_favorited }]"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            {{ playlist.is_favorited ? 'В избранном' : 'В избранное' }}
          </button>

          <button @click="$emit('duplicate', playlist)" class="action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            Копировать
          </button>

          <template v-if="currentUserId === playlist.user_id">
            <button @click="$emit('add-anime', playlist)" class="action-btn primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              Добавить аниме
            </button>

            <button @click="$emit('edit', playlist)" class="action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Редактировать
            </button>

            <button @click="$emit('delete', playlist)" class="action-btn danger">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              Удалить
            </button>

            <button @click="$emit('toggle-privacy', playlist)" class="action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {{ playlist.is_public ? 'Сделать приватным' : 'Сделать публичным' }}
            </button>

            <button @click="$emit('update-cover', playlist)" class="action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
              Обновить обложку
            </button>
          </template>
        </div>
      </div>
    </div>

    <div v-if="playlist.items && playlist.items.length > 0" class="playlist-items">
      <h2>Аниме в плейлисте</h2>
      <div class="items-list">
        <div
          v-for="item in playlist.items"
          :key="item.id"
          class="playlist-item"
        >
          <img
            v-if="item.anime?.poster_image_url"
            :src="item.anime.poster_image_url"
            :alt="item.anime.title_ru || item.anime.title_en"
            class="item-poster"
          />
          <div class="item-info">
            <h3>{{ item.anime?.title_ru || item.anime?.title_en }}</h3>
            <p v-if="item.notes" class="item-notes">{{ item.notes }}</p>
          </div>
          <div class="item-position">#{{ item.position + 1 }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Playlist {
  id: number
  title: string
  description?: string
  user_id: number
  user?: {
    id: number
    username: string
  }
  items_count?: number
  items?: any[]
  favorites_count?: number
  is_favorited?: boolean
  is_public?: boolean
  cover_urls?: {
    original?: string
    thumbnail?: string
  }
}

interface Props {
  playlist: Playlist
  currentUserId?: number
}

defineProps<Props>()

defineEmits<{
  'toggle-favorite': [playlist: Playlist]
  'duplicate': [playlist: Playlist]
  'add-anime': [playlist: Playlist]
  'edit': [playlist: Playlist]
  'delete': [playlist: Playlist]
  'update-cover': [playlist: Playlist]
  'toggle-privacy': [playlist: Playlist]
  'item-notes-change': [item: any]
  'reorder': [items: any[]]
}>()
</script>

<style scoped>
.playlist-detail {
  background: var(--color-background-surface);
  border-radius: 1rem;
  overflow: hidden;
}

.playlist-header {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.playlist-cover {
  width: 200px;
  height: 200px;
  flex-shrink: 0;
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--color-background-secondary);
}

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-info {
  flex: 1;
}

.playlist-info h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
}

.description {
  color: var(--color-text-secondary);
  margin: 0 0 1rem 0;
  line-height: 1.6;
}

.playlist-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.playlist-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--color-background-hover);
}

.action-btn.primary {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
}

.action-btn.primary:hover {
  background: var(--color-accent-dark);
}

.action-btn.danger {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.3);
}

.action-btn.danger:hover {
  background: rgba(220, 38, 38, 0.2);
}

.action-btn.favorite-btn.active {
  color: var(--color-accent-pink);
  background: rgba(255, 42, 109, 0.1);
  border-color: rgba(255, 42, 109, 0.3);
}

.playlist-items {
  padding: 1.5rem;
}

.playlist-items h2 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.playlist-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--color-background);
  border-radius: 0.5rem;
  transition: background 0.2s;
}

.playlist-item:hover {
  background: var(--color-background-hover);
}

.item-poster {
  width: 60px;
  height: 90px;
  object-fit: cover;
  border-radius: 0.375rem;
}

.item-info {
  flex: 1;
}

.item-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.item-notes {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.item-position {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
}

@media (max-width: 768px) {
  .playlist-header {
    flex-direction: column;
  }

  .playlist-cover {
    width: 100%;
    height: 200px;
  }
}
</style>
