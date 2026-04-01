<template>
  <div class="profile-view">
    <!-- Back button for mobile -->
    <button v-if="showBackButton" class="back-button" @click="goBack">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      Назад
    </button>

    <!-- Blocked user state -->
    <div v-if="isBlocked" class="blocked-user">
      <div class="blocked-content">
        <div class="blocked-icon">🚫</div>
        <h2>Этот пользователь вами заблокирован</h2>
        <p>Вы не видите его контент и не получаете уведомления.</p>
        <button class="btn-primary" @click="handleUnblock">Разблокировать</button>
      </div>
    </div>

    <!-- User not found -->
    <div v-else-if="!user && !loading" class="user-not-found">
      <div class="not-found-content">
        <div class="not-found-icon">👤</div>
        <h2>Пользователь не найден</h2>
        <p>Пользователь с таким никнеймом не существует или был удалён.</p>
        <router-link to="/feed" class="btn-primary">Вернуться в ленту</router-link>
      </div>
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка профиля...</p>
    </div>

    <!-- Profile content -->
    <template v-else-if="user">
      <!-- Profile Header -->
      <ProfileHeader
        :user="user"
        :is-following="isFollowing"
        @edit-profile="showEditModal = true"
        @show-followers="showFollowers = true"
        @show-following="showFollowing = true"
        @go-to-playlists="activeTab = 'playlists'"
        @show-stats="showStatsModal = true"
        @privacy-settings="openPrivacySettings"
        @archive="openArchive"
        @logout="handleLogout"
        @follow="handleFollow"
        @manage-subscription="showSubscriptionMenu = true"
        @message="handleMessage"
        @report="handleReport"
        @block="handleBlock"
      />

      <!-- Profile Search -->
      <ProfileSearch
        :user="user"
        :anime-library="animeLibrary"
        :playlists="playlists"
        :videos="videos"
      />

      <!-- Profile Tabs -->
      <ProfileTabs
        :active-tab="activeTab"
        @tab-change="activeTab = $event"
      />

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Feed Tab -->
        <ProfileFeedTab
          v-if="activeTab === 'feed'"
          :user="user"
          :activities="activities"
        />

        <!-- Anime Tab -->
        <ProfileAnimeTab
          v-else-if="activeTab === 'anime'"
          :user="user"
          :anime-library="animeLibrary"
          :active-filter="animeFilter"
          @filter-change="animeFilter = $event"
          @remove-anime="handleRemoveAnime"
        />

        <!-- Playlists Tab -->
        <ProfilePlaylistsTab
          v-else-if="activeTab === 'playlists'"
          :user="user"
          :playlists="playlists"
          @filter-change="handlePlaylistFilter"
          @create-playlist="createPlaylist"
          @open-playlist="openPlaylist"
          @edit-playlist="editPlaylist"
          @duplicate-playlist="duplicatePlaylist"
          @export-playlist="exportPlaylist"
          @toggle-visibility="togglePlaylistVisibility"
          @delete-playlist="deletePlaylist"
        />

        <!-- Shorts Tab -->
        <ProfileShortsTab
          v-else-if="activeTab === 'shorts'"
          :user="user"
          :videos="videos"
          @upload-video="uploadVideo"
        />

        <!-- Dubs Tab -->
        <ProfileDubsTab
          v-else-if="activeTab === 'dubs'"
          :user="user"
          :dub-memberships="dubMemberships"
          :studio-data="studioData"
          :is-studio="isStudio"
          @create-dub-profile="createDubProfile"
          @manage-studio="manageStudio"
          @view-studio="viewStudio"
        />
      </div>
    </template>

    <!-- Edit Profile Modal -->
    <EditProfileModal
      v-if="showEditModal"
      :is-visible="showEditModal"
      :user="authStore.user"
      @close="showEditModal = false"
      @save="handleProfileSave"
    />

    <!-- Avatar Editor Modal -->
    <AvatarEditorModal
      v-if="showAvatarEditor"
      :show="showAvatarEditor"
      @update:show="showAvatarEditor = false"
      @avatar-updated="handleAvatarUpdated"
    />

    <!-- Followers Modal -->
    <FollowersModal
      :show="showFollowers"
      :users="followers"
      :is-followers="true"
      :loading="followersLoading"
      @update:show="showFollowers = false"
      @follow="handleFollowUser"
      @unfollow="handleUnfollowUser"
    />

    <!-- Following Modal -->
    <FollowersModal
      :show="showFollowing"
      :users="following"
      :is-followers="false"
      :loading="followingLoading"
      @update:show="showFollowing = false"
      @follow="handleFollowUser"
      @unfollow="handleUnfollowUser"
    />

    <!-- Achievements Modal -->
    <AchievementsModal
      :show="showAchievements"
      :user="user!"
      :achievements="achievements"
      :loading="achievementsLoading"
      @update:show="showAchievements = false"
    />

    <!-- Profile Stats Modal -->
    <ProfileStatsModal
      :show="showStatsModal"
      :user="user!"
      :stats="profileStats"
      :loading="statsLoading"
      @update:show="showStatsModal = false"
    />

    <!-- Subscription Menu -->
    <div v-if="showSubscriptionMenu" class="dropdown-overlay" @click="showSubscriptionMenu = false">
      <div class="dropdown-menu" @click.stop>
        <h4>Управление подпиской</h4>
        <div class="menu-item" @click="togglePostNotifications">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          Уведомления о постах
          <span v-if="postNotifications" class="check">✓</span>
        </div>
        <div class="menu-item" @click="toggleHideFromFeed">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
          </svg>
          Скрыть из ленты
          <span v-if="hideFromFeed" class="check">✓</span>
        </div>
        <div class="menu-divider"></div>
        <div class="menu-item menu-item-danger" @click="handleUnfollow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          🔴 Отписаться
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAvatar } from '@/composables/useAvatar'
import apiClient from '@/api/client'
import ProfileHeader from '@/components/profile/ProfileHeader.vue'
import ProfileTabs from '@/components/profile/ProfileTabs.vue'
import ProfileFeedTab from '@/components/profile/ProfileFeedTab.vue'
import ProfileAnimeTab from '@/components/profile/ProfileAnimeTab.vue'
import ProfilePlaylistsTab from '@/components/profile/ProfilePlaylistsTab.vue'
import ProfileShortsTab from '@/components/profile/ProfileShortsTab.vue'
import ProfileDubsTab from '@/components/profile/ProfileDubsTab.vue'
import ProfileSearch from '@/components/profile/ProfileSearch.vue'
import EditProfileModal from '@/components/modal/profile/EditProfileModal.vue'
import AvatarEditorModal from '@/components/modal/profile/AvatarEditorModal.vue'
import FollowersModal from '@/components/modal/profile/FollowersModal.vue'
import AchievementsModal from '@/components/modal/profile/AchievementsModal.vue'
import ProfileStatsModal from '@/components/modal/profile/ProfileStatsModal.vue'
import type { User, Activity, AnimeLibrary, Playlist, Video, DubMember, DubStudio, Achievement, ProfileStats } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { getAvatarUrl, getUserInitials } = useAvatar()

const loading = ref(true)
const user = ref<User | null>(null)
const isBlocked = ref(false)
const activeTab = ref('feed')
const animeFilter = ref('all')

const activities = ref<Activity[]>([])
const animeLibrary = ref<AnimeLibrary[]>([])
const playlists = ref<Playlist[]>([])
const videos = ref<Video[]>([])
const dubMemberships = ref<DubMember[]>([])
const studioData = ref<DubStudio | null>(null)
const isStudio = ref(false)

const followers = ref<User[]>([])
const following = ref<User[]>([])
const followersLoading = ref(false)
const followingLoading = ref(false)

const achievements = ref<Achievement[]>([])
const achievementsLoading = ref(false)
const profileStats = ref<ProfileStats | null>(null)
const statsLoading = ref(false)

const showEditModal = ref(false)
const showAvatarEditor = ref(false)
const showFollowers = ref(false)
const showFollowing = ref(false)
const showAchievements = ref(false)
const showStatsModal = ref(false)
const showSubscriptionMenu = ref(false)

const postNotifications = ref(false)
const hideFromFeed = ref(false)

const username = computed(() => route.params.username as string)

const showBackButton = computed(() => {
  return window.history.length > 1
})

const isCurrentUser = computed(() => {
  return authStore.user?.id === user.value?.id
})

const isFollowing = computed(() => {
  return (authStore.user as any)?.following?.includes(user.value?.id || 0) || false
})

const hasDubs = computed(() => {
  return dubMemberships.value.length > 0 || isStudio.value
})

const fetchUserProfile = async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/users/@${username.value}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.status === 404) {
      user.value = null
      return
    }

    if (response.status === 403) {
      isBlocked.value = true
      return
    }

    if (!response.ok) {
      throw new Error('Failed to fetch user profile')
    }

    const data = await response.json()
    user.value = data
  } catch (error) {
    console.error('Error fetching user profile:', error)
    user.value = null
  } finally {
    loading.value = false
  }
}

const fetchActivities = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/activities`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      activities.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching activities:', error)
  }
}

const fetchAnimeLibrary = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/anime`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      animeLibrary.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching anime library:', error)
  }
}

const fetchPlaylists = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/playlists`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      playlists.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching playlists:', error)
  }
}

const fetchVideos = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/videos`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      videos.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching videos:', error)
  }
}

const fetchDubMemberships = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/dubs`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      dubMemberships.value = data.memberships || []
      studioData.value = data.studio || null
      isStudio.value = data.is_studio || false
    }
  } catch (error) {
    console.error('Error fetching dub memberships:', error)
  }
}

const fetchFollowers = async () => {
  if (!user.value) return
  followersLoading.value = true
  try {
    const response = await fetch(`/api/users/@${username.value}/followers`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      followers.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching followers:', error)
  } finally {
    followersLoading.value = false
  }
}

const fetchFollowing = async () => {
  if (!user.value) return
  followingLoading.value = true
  try {
    const response = await fetch(`/api/users/@${username.value}/following`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      following.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching following:', error)
  } finally {
    followingLoading.value = false
  }
}

const fetchAchievements = async () => {
  if (!user.value) return
  achievementsLoading.value = true
  try {
    const response = await fetch(`/api/users/@${username.value}/achievements`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      achievements.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching achievements:', error)
  } finally {
    achievementsLoading.value = false
  }
}

const fetchProfileStats = async () => {
  if (!user.value || !isCurrentUser.value) return
  statsLoading.value = true
  try {
    const response = await fetch(`/api/users/@${username.value}/stats`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      profileStats.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching profile stats:', error)
  } finally {
    statsLoading.value = false
  }
}

const goBack = () => {
  router.back()
}

const handleFollow = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/follow`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await authStore.fetchUser()
      user.value.followers_count = (user.value.followers_count || 0) + 1
    }
  } catch (error) {
    console.error('Error following user:', error)
  }
}

const handleUnfollow = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/follow`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await authStore.fetchUser()
      user.value.followers_count = Math.max(0, (user.value.followers_count || 0) - 1)
      showSubscriptionMenu.value = false
    }
  } catch (error) {
    console.error('Error unfollowing user:', error)
  }
}

const handleFollowUser = async (userId: number) => {
  try {
    const response = await fetch(`/api/users/${userId}/follow`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await fetchFollowers()
      await fetchFollowing()
    }
  } catch (error) {
    console.error('Error following user:', error)
  }
}

const handleUnfollowUser = async (userId: number) => {
  try {
    const response = await fetch(`/api/users/${userId}/follow`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await fetchFollowers()
      await fetchFollowing()
    }
  } catch (error) {
    console.error('Error unfollowing user:', error)
  }
}

const handleBlock = async () => {
  if (!user.value) return
  if (!confirm(`Вы уверены, что хотите заблокировать @${username.value}?`)) return

  try {
    const response = await fetch(`/api/users/@${username.value}/block`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      isBlocked.value = true
    }
  } catch (error) {
    console.error('Error blocking user:', error)
  }
}

const handleUnblock = async () => {
  if (!user.value) return
  try {
    const response = await fetch(`/api/users/@${username.value}/block`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      isBlocked.value = false
      await fetchUserProfile()
    }
  } catch (error) {
    console.error('Error unblocking user:', error)
  }
}

const handleMessage = () => {
  if (!user.value) return
  router.push(`/chats/${user.value.id}`)
}

const handleReport = async () => {
  if (!user.value) return
  const reason = prompt('Укажите причину жалобы:')
  if (reason) {
    try {
      const response = await apiClient.post('/social/reports/', {
        target_type: 'user',
        target_id: user.value.id,
        reason: reason
      })
      alert('Жалоба успешно отправлена')
    } catch (error: any) {
      console.error('Error submitting report:', error)
      alert(error.response?.data?.detail || 'Ошибка при отправке жалобы')
    }
  }
}

const handleProfileSave = async (updatedProfile: any) => {
  try {
    await authStore.updateProfile(updatedProfile)
    await fetchUserProfile()
    showEditModal.value = false
  } catch (error) {
    console.error('Error saving profile:', error)
    alert('Ошибка при сохранении профиля')
  }
}

const handleAvatarUpdated = (avatarUrl: string) => {
  if (user.value) {
    user.value.avatar_url = avatarUrl
  }
}

const handleRemoveAnime = async (libraryId: number) => {
  if (!confirm('Удалить это аниме из коллекции?')) return

  try {
    const response = await fetch(`/api/anime-library/${libraryId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      animeLibrary.value = animeLibrary.value.filter(item => item.id !== libraryId)
    }
  } catch (error) {
    console.error('Error removing anime:', error)
  }
}

const handlePlaylistFilter = (filters: any) => {
  console.log('Playlist filters:', filters)
}

const createPlaylist = () => {
  router.push('/playlists/create')
}

const openPlaylist = (playlistId: number) => {
  router.push(`/playlists/${playlistId}`)
}

const editPlaylist = (playlistId: number) => {
  router.push(`/playlists/${playlistId}/edit`)
}

const duplicatePlaylist = async (playlistId: number) => {
  try {
    const response = await fetch(`/api/playlists/${playlistId}/duplicate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      await fetchPlaylists()
      alert('Плейлист дублирован')
    }
  } catch (error) {
    console.error('Error duplicating playlist:', error)
  }
}

const exportPlaylist = async (playlistId: number) => {
  try {
    const response = await fetch(`/api/playlists/${playlistId}/export`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `playlist-${playlistId}.json`
      a.click()
    }
  } catch (error) {
    console.error('Error exporting playlist:', error)
  }
}

const togglePlaylistVisibility = async (playlistId: number) => {
  try {
    const playlist = playlists.value.find(p => p.id === playlistId)
    if (!playlist) return

    const response = await fetch(`/api/playlists/${playlistId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_public: !playlist.is_public })
    })

    if (response.ok) {
      playlist.is_public = !playlist.is_public
    }
  } catch (error) {
    console.error('Error toggling playlist visibility:', error)
  }
}

const deletePlaylist = async (playlistId: number) => {
  if (!confirm('Удалить этот плейлист?')) return

  try {
    const response = await fetch(`/api/playlists/${playlistId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (response.ok) {
      playlists.value = playlists.value.filter(p => p.id !== playlistId)
    }
  } catch (error) {
    console.error('Error deleting playlist:', error)
  }
}

const uploadVideo = () => {
  router.push('/reactor/upload')
}

const createDubProfile = () => {
  router.push('/dubs/create')
}

const manageStudio = () => {
  router.push('/dubs/manage')
}

const viewStudio = (studioId: number) => {
  router.push(`/dubs/${studioId}`)
}

const openPrivacySettings = () => {
  router.push('/settings/privacy')
}

const openArchive = () => {
  router.push('/archive')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const togglePostNotifications = () => {
  postNotifications.value = !postNotifications.value
}

const toggleHideFromFeed = () => {
  hideFromFeed.value = !hideFromFeed.value
}

watch(username, () => {
  fetchUserProfile()
})

watch(() => showFollowers.value, (val) => {
  if (val) fetchFollowers()
})

watch(() => showFollowing.value, (val) => {
  if (val) fetchFollowing()
})

onMounted(async () => {
  await fetchUserProfile()
  
  if (user.value) {
    await Promise.all([
      fetchActivities(),
      fetchAnimeLibrary(),
      fetchPlaylists(),
      fetchVideos(),
      fetchDubMemberships()
    ])
  }
})
</script>

<style scoped>
.profile-view {
  min-height: 100vh;
  background-color: var(--color-background);
  padding: 1rem;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  color: var(--color-text-primary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 1rem;
}

.back-button:hover {
  background: var(--color-background-hover);
}

.blocked-user,
.user-not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.blocked-content,
.not-found-content {
  text-align: center;
  max-width: 400px;
}

.blocked-icon,
.not-found-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.blocked-content h2,
.not-found-content h2 {
  font-size: 1.5rem;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
}

.blocked-content p,
.not-found-content p {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 1.5rem 0;
}

.btn-primary {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.15s ease;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
  color: var(--color-text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-divider);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tab-content {
  margin-top: 2rem;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 1rem;
}

.dropdown-menu {
  background: var(--color-background-surface);
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 250px;
  padding: 0.5rem;
  margin-top: 4rem;
}

.dropdown-menu h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 0.5rem 0;
  padding: 0.5rem 0.75rem 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-primary);
  transition: background-color 0.15s ease;
}

.menu-item:hover {
  background-color: var(--color-background-hover);
}

.menu-item-danger {
  color: var(--color-error);
}

.menu-item-danger:hover {
  background-color: rgba(220, 38, 38, 0.1);
}

.check {
  margin-left: auto;
  color: var(--color-primary);
}

.menu-divider {
  height: 1px;
  background-color: var(--color-divider);
  margin: 0.25rem 0;
}

@media (max-width: 640px) {
  .profile-view {
    padding: 0.5rem;
  }

  .dropdown-overlay {
    padding: 0;
    align-items: flex-end;
    justify-content: center;
  }

  .dropdown-menu {
    width: 100%;
    max-width: 400px;
    margin: 0;
    border-radius: 0.5rem 0.5rem 0 0;
  }
}

/* ═══ АДАПТИВНЫЕ СТИЛИ ПРОФИЛЯ ═══ */

/* xs: 320px */
@media (max-width: 374px) {
  .profile-view {
    padding: 0.25rem;
  }
  
  .profile-cover {
    height: 6rem;
  }
  
  .profile-avatar {
    width: 3.5rem;
    height: 3.5rem;
    bottom: -1.5rem;
    left: 0.75rem;
    border-width: 3px;
  }
  
  .profile-info {
    margin-top: 2rem;
    padding: 0 0.5rem;
  }
  
  .profile-name {
    font-size: 1.125rem;
  }
  
  .profile-stats {
    gap: 0.5rem;
    font-size: 0.75rem;
  }
  
  .profile-stats span {
    font-size: 0.75rem;
  }
  
  .profile-tabs {
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    overflow-x: auto;
  }
  
  .profile-tab {
    padding: 0.5rem;
    font-size: 0.75rem;
  }
  
  .profile-content {
    padding: 0.5rem;
  }
  
  .profile-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
  
  .profile-section-title {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .profile-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
  
  .profile-settings-grid {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .profile-setting-item {
    padding: 0.75rem;
    font-size: 0.875rem;
  }
  
  .profile-setting-label {
    font-size: 0.75rem;
  }
  
  .profile-setting-value {
    font-size: 0.75rem;
  }
}

/* sm: 375px */
@media (min-width: 375px) and (max-width: 767px) {
  .profile-cover {
    height: 7rem;
  }
  
  .profile-avatar {
    width: 4rem;
    height: 4rem;
    bottom: -1.75rem;
  }
  
  .profile-info {
    margin-top: 2.25rem;
  }
  
  .profile-name {
    font-size: 1.25rem;
  }
  
  .profile-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
}

/* md: 768px+ */
@media (min-width: 768px) {
  .profile-cover {
    height: 9rem;
  }
  
  .profile-avatar {
    width: 5rem;
    height: 5rem;
    bottom: -2rem;
    left: 1rem;
  }
  
  .profile-info {
    margin-top: 2.5rem;
    padding: 0 1rem;
  }
  
  .profile-name {
    font-size: 1.5rem;
  }
  
  .profile-stats {
    gap: 1rem;
    font-size: 0.875rem;
  }
  
  .profile-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }
  
  .profile-tabs {
    gap: 0.5rem;
    padding: 0.5rem 1rem;
  }
  
  .profile-tab {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .profile-cover {
    height: 10rem;
  }
  
  .profile-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* desktop: 1536px+ */
@media (min-width: 1536px) {
  .profile-cover {
    height: 12rem;
  }
  
  .profile-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>
