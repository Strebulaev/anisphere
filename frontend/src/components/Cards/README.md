# Компоненты карточек

## AnimeCard

Карточка аниме с полной информацией и действиями.

### Props

| Prop | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| anime | AnimeCardProps | - | Объект аниме |
| showActions | boolean | true | Показывать кнопки действий |
| hasLiveCover | boolean | false | Живая обложка |
| watchStatus | 'watching' \| 'completed' \| 'planned' \| 'dropped' \| 'onhold' | - | Статус в коллекции |
| watchProgress | number | 0 | Прогресс просмотра |
| totalEpisodes | number | - | Общее количество эпизодов |
| showGenres | boolean | true | Показывать жанры |
| showProgress | boolean | true | Показывать прогресс |
| maxGenres | number | 2 | Максимальное количество жанров для отображения |

### Emits

| Событие | Параметры | Описание |
|---------|-----------|----------|
| click | anime: AnimeCardProps | При клике на карточку |
| favorite-toggle | isFavorite: boolean | При переключении избранного |
| set-reminder | animeId: number | При установке напоминания |

### Использование

```vue
<AnimeCard
  :anime="anime"
  :collection="collectionInfo"
  :show-genres="true"
  :show-progress="true"
  :max-genres="2"
  :is-favorite="isFavorite"
  @click="goToAnime"
  @favorite-toggle="toggleFavorite"
  @add-to-playlist="openPlaylistModal"
  @set-reminder="openReminderModal"
/>
```

---

## PlaylistCard

Карточка плейлиста с превью и статистикой.

### Props

| Prop | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| playlist | Playlist | - | Объект плейлиста |
| currentUserId | number | undefined | ID текущего пользователя |
| isFavorite | boolean | false | В избранном |
| maxPreviewItems | number | 3 | Максимальное количество превью |

### Emits

| Событие | Параметры | Описание |
|---------|-----------|----------|
| click | playlist: Playlist | При клике на карточку |
| favorite-toggle | playlistId: number, isFavorite: boolean | При переключении избранного |
| share | playlistId: number | При копировании ссылки |
| edit | playlist: Playlist | При редактировании |
| delete | playlist: Playlist | При удалении |

### Использование

```vue
<PlaylistCard
  :playlist="playlist"
  :current-user-id="currentUserId"
  :is-favorite="isFavorite"
  @click="openPlaylist"
  @favorite-toggle="toggleFavorite"
  @share="sharePlaylist"
  @edit="editPlaylist"
  @delete="deletePlaylist"
/>
```

---

## UserCard

Карточка пользователя с информацией и действиями.

### Props

| Prop | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| user | User | - | Объект пользователя |
| achievements | Achievement[] | [] | Достижения |
| isCurrentUser | boolean | false | Текущий пользователь |
| maxBadges | number | 2 | Максимальное количество значков |

### Emits

| Событие | Параметры | Описание |
|---------|-----------|----------|
| click | user: User | При клике на карточку |
| follow | userId: number | При подписке |
| unfollow | userId: number | При отписке |
| message | user: User | При отправке сообщения |

### Использование

```vue
<UserCard
  :user="user"
  :achievements="achievements"
  :is-current-user="isCurrentUser"
  @click="goToProfile"
  @follow="followUser"
  @unfollow="unfollowUser"
  @message="openChat"
/>
```

---

## Примеры использования

### Сетка аниме

```vue
<template>
  <div class="anime-grid">
    <AnimeCard
      v-for="anime in animeList"
      :key="anime.id"
      :anime="anime"
      :collection="getCollection(anime.id)"
      :show-genres="true"
      :show-progress="true"
      @click="goToAnime(anime.id)"
      @favorite-toggle="toggleFavorite(anime.id)"
      @add-to-playlist="openPlaylistModal(anime.id)"
      @set-reminder="setReminder(anime.id)"
    />
  </div>
</template>

<script setup lang="ts">
import AnimeCard from '@/components/Cards/AnimeCard.vue'

const animeList = ref([])
const collections = ref({})

const getCollection = (animeId: number) => {
  return collections.value[animeId]
}

const toggleFavorite = (animeId: number) => {
  // Логика переключения избранного
}

const openPlaylistModal = (animeId: number) => {
  // Открытие модалки выбора плейлиста
}

const setReminder = (animeId: number) => {
  // Установка напоминания
}
</script>
```

### Список плейлистов

```vue
<template>
  <div class="playlists-list">
    <PlaylistCard
      v-for="playlist in playlists"
      :key="playlist.id"
      :playlist="playlist"
      :current-user-id="currentUserId"
      :is-favorite="favoritePlaylists.includes(playlist.id)"
      @click="goToPlaylist(playlist.id)"
      @favorite-toggle="toggleFavorite(playlist.id)"
      @share="sharePlaylist(playlist.id)"
      @edit="editPlaylist(playlist.id)"
      @delete="deletePlaylist(playlist.id)"
    />
  </div>
</template>

<script setup lang="ts">
import PlaylistCard from '@/components/Cards/PlaylistCard.vue'

const playlists = ref([])
const favoritePlaylists = ref([])
const currentUserId = ref(0)

const toggleFavorite = (playlistId: number) => {
  // Логика переключения избранного
}

const sharePlaylist = (playlistId: number) => {
  // Копирование ссылки
}

const editPlaylist = (playlistId: number) => {
  // Открытие редактора
}

const deletePlaylist = (playlistId: number) => {
  // Удаление плейлиста
}
</script>
```

### Список пользователей

```vue
<template>
  <div class="users-list">
    <UserCard
      v-for="user in users"
      :key="user.id"
      :user="user"
      :achievements="getAchievements(user.id)"
      :is-current-user="user.id === currentUserId"
      @click="goToProfile(user.id)"
      @follow="followUser(user.id)"
      @unfollow="unfollowUser(user.id)"
      @message="openChat(user.id)"
    />
  </div>
</template>

<script setup lang="ts">
import UserCard from '@/components/Cards/UserCard.vue'

const users = ref([])
const currentUserId = ref(0)

const getAchievements = (userId: number) => {
  // Получение достижений пользователя
}

const followUser = (userId: number) => {
  // Подписка на пользователя
}

const unfollowUser = (userId: number) => {
  // Отписка от пользователя
}

const openChat = (userId: number) => {
  // Открытие чата
}
</script>
```

---

## Стили и адаптивность

Все компоненты карточек адаптивны и поддерживают мобильные устройства:

- **AnimeCard**: Автоматически подстраивается под сетку, кнопки уменьшаются на мобильных
- **PlaylistCard**: Превью адаптируется, кнопки действий становятся компактнее
- **UserCard**: На мобильных устройствах переключается на вертикальную компоновку

### Медиа-запросы

```css
@media (max-width: 640px) {
  /* Компактные кнопки */
  .action-btn {
    width: 32px;
    height: 32px;
  }
  
  /* Уменьшенные шрифты */
  .anime-title,
  .playlist-title,
  .user-name {
    font-size: 13px;
  }
}
```

---

## Интеграция с API

### AnimeCard

```typescript
interface AnimeCardProps {
  id: number
  title_ru: string
  title_en?: string
  poster_url?: string
  year?: number
  type?: string
  episodes?: number
  score?: number
  status?: string
  genres?: Array<{ id: number; name: string }>
}
```

### PlaylistCard

```typescript
interface Playlist {
  id: number
  title: string
  description?: string
  is_public: boolean
  is_private: boolean
  is_link_only: boolean
  items_count: number
  likes_count: number
  updated_at: string
  user: {
    id: number
    username: string
    display_name?: string
    avatar_url?: string
  }
  items?: Array<{
    id: number
    anime?: {
      id: number
      title_ru?: string
      title_en?: string
      poster_url?: string
    }
  }>
  cover_urls?: string[]
}
```

### UserCard

```typescript
interface User {
  id: number
  username: string
  display_name?: string
  nickname?: string
  avatar_url?: string
  followers_count?: number
  is_online?: boolean
  last_seen?: string
  badges?: Array<{
    id: number
    name: string
    icon: string
    description?: string
  }>
}

interface Achievement {
  id: number
  name: string
  icon?: string
  description?: string
}
```
