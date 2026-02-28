<template>
  <div class="playlist-detail-page">
    <PlaylistDetail
      v-if="playlist"
      :playlist="playlist as any"
      :current-user-id="currentUserId"
      @toggle-favorite="(pl: any) => toggleFavorite(pl)"
      @duplicate="(pl: any) => duplicatePlaylist(pl)"
      @add-anime="(pl: any) => handleAddAnime(pl)"
      @edit="(pl: any) => handleEdit(pl)"
      @delete="(pl: any) => handleDelete(pl)"
      @update-cover="(pl: any) => handleUpdateCover(pl)"
      @item-notes-change="handleItemNotesChange"
      @reorder="handleReorder"
      @toggle-privacy="(pl: any) => handleTogglePrivacy(pl)"
    />
    <div v-else-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>  
    </div>
    <div v-else class="error">
      <p>Плейлист не найден</p>
      <router-link to="/playlists">Вернуться к плейлистам</router-link>
    </div>

    <!-- Модальное окно добавления аниме -->
    <AddAnimeToPlaylistModal
      v-if="showAddAnimeModal && playlist"
      :show="showAddAnimeModal"
      :playlist-id="playlist.id"
      @close="showAddAnimeModal = false"
      @added="handleAnimeAdded"
    />

    <!-- Модальное окно редактирования плейлиста -->
    <EditPlaylistModal
      v-if="showEditModal && playlist"
      :show="showEditModal"
      :playlist="playlist"
      @close="showEditModal = false"
      @saved="handlePlaylistSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import playlistsApi, { type Playlist } from '@/api/playlists'
import PlaylistDetail from '@/components/Playlists/PlaylistDetail.vue'
import AddAnimeToPlaylistModal from '@/components/modal/anime/AddAnimeToPlaylistModal.vue'
import EditPlaylistModal from '@/components/modal/playlists/EditPlaylistModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const playlist = ref<Playlist | null>(null)
const currentUserId = ref<number | undefined>(undefined)
const loading = ref(true)
const showAddAnimeModal = ref(false)
const showEditModal = ref(false)

const loadPlaylist = async () => {
  const id = route.params.id
  if (!id || typeof id !== 'string') return

  try {
    const response = await playlistsApi.getPlaylist(parseInt(id))
    playlist.value = response.data

    // Получаем ID текущего пользователя из auth store
    if (authStore.user) {
      currentUserId.value = authStore.user.id
      console.log('Текущий пользователь ID:', currentUserId.value)
      console.log('ID владельца плейлиста:', response.data.user_id)
      console.log('Я владелец?', currentUserId.value === response.data.user_id)
    } else {
      console.warn('Пользователь не авторизован')
    }
  } catch (error) {
    console.error('Ошибка загрузки плейлиста:', error)
  } finally {
    loading.value = false
  }
}

const toggleFavorite = async (pl: Playlist) => {
  try {
    if (pl.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(pl.id)
      if (playlist.value) {
        playlist.value.is_favorited = false
        playlist.value.favorites_count = Math.max(0, playlist.value.favorites_count - 1)
      }
    } else {
      await playlistsApi.addPlaylistToFavorites(pl.id)
      if (playlist.value) {
        playlist.value.is_favorited = true
        playlist.value.favorites_count++
      }
    }
  } catch (error) {
    console.error('Ошибка изменения избранного:', error)
  }
}

const duplicatePlaylist = async (pl: Playlist) => {
  try {
    const response = await playlistsApi.duplicatePlaylist(pl.id)
    router.push(`/playlist/${response.data.id}`)
  } catch (error) {
    console.error('Ошибка копирования плейлиста:', error)
    alert('Не удалось скопировать плейлист')
  }
}

const handleAddAnime = (pl: Playlist) => {
  // Открываем модальное окно добавления аниме
  showAddAnimeModal.value = true
}

const handleEdit = (pl: Playlist) => {
  // Открываем модальное окно редактирования плейлиста
  showEditModal.value = true
}

const handleDelete = async (pl: Playlist) => {
  if (confirm('Удалить плейлист?')) {
    try {
      await playlistsApi.deletePlaylist(pl.id)
      router.push('/playlists')
    } catch (error) {
      console.error('Ошибка удаления плейлиста:', error)
      alert('Не удалось удалить плейлист')
    }
  }
}

const handleUpdateCover = async (pl: Playlist) => {
  try {
    const response = await playlistsApi.updatePlaylistCover(pl.id)
    if (playlist.value && response.data) {
      playlist.value.cover_image = response.data.cover_image
      playlist.value.cover_urls = response.data.cover_urls
    }
  } catch (error) {
    console.error('Ошибка обновления обложки:', error)
    alert('Не удалось обновить обложку')
  }
}

const handleItemNotesChange = async (item: any) => {
  if (!playlist.value) return

  try {
    const response = await playlistsApi.updatePlaylistItemNotes(
      playlist.value.id,
      item.id,
      item.notes
    )

    // Обновляем элемент в списке
    const index = playlist.value.items.findIndex((i: any) => i.id === item.id)
    if (index !== -1) {
      playlist.value.items[index] = response.data
    }
  } catch (error) {
    console.error('Ошибка обновления заметок:', error)
    alert('Не удалось обновить заметки')
  }
}

const handleReorder = async (items: any[]) => {
  if (!playlist.value) return

  try {
    await playlistsApi.reorderPlaylistItems(playlist.value.id, items)

    // Обновляем позиции в локальном состоянии
    items.forEach((item, index) => {
      const localItem = playlist.value!.items.find((i: any) => i.id === item.id)
      if (localItem) {
        localItem.position = index
      }
    })
  } catch (error) {
    console.error('Ошибка изменения порядка:', error)
    alert('Не удалось изменить порядок')
  }
}

const handleTogglePrivacy = async (pl: Playlist) => {
  try {
    const newPrivacy = !pl.is_public
    await playlistsApi.updatePlaylist(pl.id, {
      is_public: newPrivacy
    })
    if (playlist.value) {
      playlist.value.is_public = newPrivacy
    }
  } catch (error) {
    console.error('Ошибка изменения приватности:', error)
    alert('Не удалось изменить приватность')
  }
}

const handleAnimeAdded = () => {
  showAddAnimeModal.value = false
  // Перезагружаем плейлист, чтобы получить обновленный список
  loadPlaylist()
}

const handlePlaylistSaved = (updatedPlaylist: Playlist) => {
  if (playlist.value) {
    Object.assign(playlist.value, updatedPlaylist)
  }
  showEditModal.value = false
}

onMounted(() => {
  loadPlaylist()
})
</script>

<style scoped>
.playlist-detail-page {
  padding: 1.5rem;
  max-width: 900px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 4rem 1rem;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--color-text-tertiary);
}

.error {
  text-align: center;
  padding: 4rem 1rem;
}

.error p {
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
  margin-bottom: 1rem;
}

.error a {
  color: var(--color-accent);
  text-decoration: none;
}

.error a:hover {
  text-decoration: underline;
}
</style>