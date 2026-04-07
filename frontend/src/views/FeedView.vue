<template>
  <div class="feed-page-container">
    <!-- Main Tabs -->
    <div class="main-tabs">
      <button
        v-for="tab in mainTabs"
        :key="tab.id"
        class="main-tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="feed-layout">
      <!-- Лента и контент -->
      <div class="feed-main">

    <!-- ==================== ЛЕНТА ==================== -->
    <template v-if="activeTab === 'feed'">
      <!-- Feed Type Sub-tabs -->
      <div class="feed-subtabs">
        <button
          v-for="tab in feedSubTabs"
          :key="tab.type"
          class="tab-btn"
          :class="{ active: feedStore.feedType === tab.type }"
          @click="switchFeed(tab.type)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Create Post -->
      <div class="create-post-area" @click="showCreatePost = true">
        <img :src="currentUser?.avatar_url || defaultAvatar" class="user-avatar" alt="Аватар" />
        <span class="placeholder">Что у вас нового?</span>
        <button class="btn-post" @click.stop="showCreatePost = true">Написать</button>
      </div>

      <!-- Filters -->
      <FeedFilters v-model="filters" @apply="onFiltersApply" />

      <!-- New Posts Indicator -->
      <transition name="slide-down">
        <button
          v-if="feedStore.newPostsAvailable"
          class="new-posts-indicator"
          @click="reloadFeed"
        >
          ↑ Новые посты
        </button>
      </transition>

      <!-- Feed List -->
      <div class="feed-list" ref="feedListRef">
        <template v-if="feedStore.loading">
          <div v-for="i in 3" :key="i" class="post-skeleton">
            <div class="skeleton-header">
              <div class="skeleton-avatar"></div>
              <div class="skeleton-meta">
                <div class="skeleton-line short"></div>
                <div class="skeleton-line shorter"></div>
              </div>
            </div>
            <div class="skeleton-body">
              <div class="skeleton-line"></div>
              <div class="skeleton-line"></div>
              <div class="skeleton-line short"></div>
            </div>
          </div>
        </template>

        <template v-else-if="feedStore.posts.length > 0">
          <PostCard
            v-for="post in feedStore.posts"
            :key="post.id"
            :post="post"
            :show-comments-preview="true"
            @like="handleLike"
            @dislike="handleDislike"
            @comment="openComments"
            @repost="openRepost"
            @bookmark="handleBookmark"
            @share="handleShare"
            @menu="openPostMenu"
          />
        </template>

        <div v-else-if="feedStore.isEmpty" class="empty-feed">
          <span class="empty-icon">📭</span>
          <p class="empty-title">Лента пуста</p>
          <p class="empty-desc">
            <template v-if="feedStore.feedType === 'followers'">
              Подписывайтесь на пользователей, чтобы видеть их посты
            </template>
            <template v-else>Здесь пока нет постов</template>
          </p>
          <button v-if="feedStore.feedType === 'followers'" class="btn-explore" @click="switchFeed('weighted')">
            Смотреть популярное
          </button>
        </div>

        <div v-else-if="feedStore.error" class="error-state">
          <span class="error-icon"><SakuraIcon name="warning" />️</span>
          <p>{{ feedStore.error }}</p>
          <button class="btn-retry" @click="feedStore.loadFeed(feedStore.feedType)">Повторить</button>
        </div>

        <div ref="loadMoreRef" class="load-more-trigger">
          <div v-if="feedStore.loadingMore" class="loading-more">
            <div class="spinner"></div>
          </div>
          <div v-else-if="!feedStore.hasMore && feedStore.posts.length > 0" class="end-of-feed">
            Вы посмотрели всё 👀
          </div>
        </div>
      </div>
    </template>

    <!-- ==================== ПОДПИСКИ ==================== -->
    <template v-else-if="activeTab === 'subscriptions'">
      <!-- Sub-tabs: Профили / Избранные посты -->
      <div class="sub-tabs">
        <button class="sub-tab-btn" :class="{ active: subTab === 'profiles' }" @click="subTab = 'profiles'">
          <SakuraIcon name="users" /> Профили
        </button>
        <button class="sub-tab-btn" :class="{ active: subTab === 'bookmarks' }" @click="switchSubTab('bookmarks')">
          <SakuraIcon name="star" /> Избранные посты
        </button>
      </div>

      <!-- Профили -->
      <template v-if="subTab === 'profiles'">
        <div class="tab-toolbar">
          <input
            v-model="subSearch"
            placeholder="Поиск по подпискам..."
            class="search-input"
            @input="loadSubscriptions(true)"
          />
          <select v-model="subSort" @change="loadSubscriptions(true)" class="sort-select">
            <option value="date">По дате</option>
            <option value="name">По имени</option>
          </select>
        </div>

        <div v-if="subLoading && subscriptions.length === 0" class="loading-center">
          <div class="spinner"></div>
        </div>
        <div v-else-if="subscriptions.length === 0" class="empty-feed">
          <span class="empty-icon"> <SakuraIcon name="users" /> </span>
          <p class="empty-title">Нет подписок</p>
          <p class="empty-desc">Вы пока ни на кого не подписаны</p>
        </div>
        <div v-else class="cards-list">
          <SubscriptionCard
            v-for="user in filteredSubscriptions"
            :key="user.id"
            :user="user"
            @unfollowed="onUnfollowed"
          />
        </div>
        <div v-if="subHasMore" class="load-more-wrap">
          <button class="btn-load-more" @click="loadSubscriptions()" :disabled="subLoading">
            {{ subLoading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </template>

      <!-- Избранные посты -->
      <template v-else-if="subTab === 'bookmarks'">
        <div v-if="bookmarksLoading && bookmarkedPosts.length === 0" class="loading-center">
          <div class="spinner"></div>
        </div>
        <div v-else-if="bookmarkedPosts.length === 0" class="empty-feed">
          <span class="empty-icon"> <SakuraIcon name="star" /> </span>
          <p class="empty-title">Нет сохранённых постов</p>
          <p class="empty-desc">Сохраняйте посты через ☆ или меню поста</p>
        </div>
        <div v-else class="feed-list">
          <PostCard
            v-for="post in bookmarkedPosts"
            :key="post.id"
            :post="post"
            @like="handleLike"
            @dislike="handleDislike"
            @comment="openComments"
            @repost="openRepost"
            @bookmark="handleBookmark"
            @share="handleShare"
            @menu="openPostMenu"
          />
        </div>
        <div v-if="bookmarksHasMore" class="load-more-wrap">
          <button class="btn-load-more" @click="loadBookmarks()" :disabled="bookmarksLoading">
            {{ bookmarksLoading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </template>
    </template>

    <!-- ==================== НЕ ИНТЕРЕСНО ==================== -->
    <template v-else-if="activeTab === 'not_interested'">
      <!-- Sub-tabs: Профили / Посты -->
      <div class="sub-tabs">
        <button class="sub-tab-btn" :class="{ active: niTab === 'profiles' }" @click="niTab = 'profiles'">
          <SakuraIcon name="user" /> Профили
        </button>
        <button class="sub-tab-btn" :class="{ active: niTab === 'posts' }" @click="switchNiTab('posts')">
          <SakuraIcon name="newspaper" /> Посты
        </button>
      </div>

      <!-- Скрытые профили -->
      <template v-if="niTab === 'profiles'">
        <div class="tab-toolbar">
          <input
            v-model="niSearch"
            placeholder="Поиск скрытых профилей..."
            class="search-input"
          />
        </div>
        <div v-if="niLoading && notInterested.length === 0" class="loading-center">
          <div class="spinner"></div>
        </div>
        <div v-else-if="notInterested.length === 0" class="empty-feed">
          <span class="empty-icon"> <SakuraIcon name="eye-off" /> </span>
          <p class="empty-title">Список пуст</p>
          <p class="empty-desc">Вы не скрывали ни одного профиля</p>
        </div>
        <div v-else class="cards-list">
          <NotInterestedCard
            v-for="user in filteredNotInterested"
            :key="user.id"
            :user="user"
            @removed="onNiRemoved"
          />
        </div>
        <div v-if="niHasMore" class="load-more-wrap">
          <button class="btn-load-more" @click="loadNotInterested()" :disabled="niLoading">
            {{ niLoading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </template>

      <!-- Скрытые посты -->
      <template v-else-if="niTab === 'posts'">
        <div v-if="hiddenPostsLoading && hiddenPosts.length === 0" class="loading-center">
          <div class="spinner"></div>
        </div>
        <div v-else-if="hiddenPosts.length === 0" class="empty-feed">
          <span class="empty-icon">📭</span>
          <p class="empty-title">Нет скрытых постов</p>
          <p class="empty-desc">Посты скрытые через «Не интересно» появятся здесь</p>
        </div>
        <div v-else class="feed-list">
          <div v-for="post in hiddenPosts" :key="post.id" class="hidden-post-item">
            <div class="hidden-post-info" @click="goToPost(post.id)">
              <img :src="post.author_avatar || defaultAvatar" class="hp-avatar" alt="">
              <div class="hp-meta">
                <span class="hp-author">{{ post.author_display_name || post.author_username }}</span>
                <span class="hp-text">{{ (post.text || '').slice(0, 80) }}{{ (post.text || '').length > 80 ? '...' : '' }}</span>
              </div>
            </div>
            <button class="btn-unblock-post" @click="unhidePost(post.id)" title="Показывать снова"> <SakuraIcon name="eye" /> </button>
          </div>
        </div>
        <div v-if="hiddenPostsHasMore" class="load-more-wrap">
          <button class="btn-load-more" @click="loadHiddenPosts()" :disabled="hiddenPostsLoading">
            {{ hiddenPostsLoading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
      </template>
    </template>

    <!-- ==================== ЖАЛОБЫ (Модераторы) ==================== -->
    <template v-else-if="activeTab === 'reports'">
      <ReportsTab />
    </template>
      </div>

      <!-- Боковая панель: Популярное -->
      <!-- <aside class="feed-sidebar" v-if="activeTab === 'feed'">
        <div class="sidebar-title"><SakuraIcon name="fire" /> Популярное</div>
        <div v-if="popularLoading" class="popular-loading">
          <div class="spinner-sm"></div>
        </div>
        <div v-else-if="popularPosts.length === 0" class="popular-empty">
          Пока нет популярных постов
        </div>
        <div v-else class="popular-list">
          <div 
            v-for="post in popularPosts" 
            :key="post.id" 
            class="popular-item"
            @click="goToPost(post.id)"
          >
            <div class="popular-header">
              <img :src="post.author_avatar || defaultAvatar" class="popular-avatar" alt="">
              <span class="popular-author">{{ post.author_display_name || post.author_username }}</span>
            </div>
            <div class="popular-text">{{ truncateText(post.text, 80) }}</div>
            <div class="popular-stats">
              <span><SakuraIcon name="heart" /> {{ post.likes_count }}</span>
              <span>💭 {{ post.comments_count }}</span>
            </div>
          </div>
        </div>
      </aside> -->
    </div>
  </div>

  <!-- ==================== MODALS ==================== -->
  <CreatePostModal v-if="showCreatePost" @close="showCreatePost = false" @created="onPostCreated" />

  <CommentsModal v-if="activeCommentPost" :post="activeCommentPost" @close="activeCommentPost = null" />

  <RepostModal
    v-if="activeRepostPost"
    :post="activeRepostPost"
    @close="activeRepostPost = null"
    @reposted="onReposted"
  />

  <PostMenu
    v-if="activeMenuPost"
    :post="activeMenuPost"
    @close="activeMenuPost = null"
    @delete="(p) => onPostDeleted(p.id)"
    @hide="(p) => onPostHidden(p.id)"
    @hideAuthor="(p) => onHideAuthor(p)"
    @bookmark="(p) => handleBookmark(p)"
    @repost="(p) => openRepost(p)"
    @forward="(p) => openForward(p)"
    @reported="activeMenuPost = null"
    @followed="onFollowToggled"
  />

  <ForwardModal
    v-if="activeForwardPost"
    :post="activeForwardPost"
    @close="activeForwardPost = null"
    @forwarded="activeForwardPost = null"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFeedStore } from '@/stores/feed'
import { useAuthStore } from '@/stores/auth'
import { subscriptionsApi } from '@/api/feed'
import type { FeedPost, SubscriptionUser, NotInterestedUser } from '@/api/feed'
import PostCard from '@/components/feed/PostCard.vue'
import CreatePostModal from '@/components/feed/CreatePostModal.vue'
import CommentsModal from '@/components/feed/CommentsModal.vue'
import RepostModal from '@/components/feed/RepostModal.vue'
import PostMenu from '@/components/feed/PostMenu.vue'
import ForwardModal from '@/components/feed/ForwardModal.vue'
import FeedFilters from '@/components/feed/FeedFilters.vue'
import SubscriptionCard from '@/components/feed/SubscriptionCard.vue'
import NotInterestedCard from '@/components/feed/NotInterestedCard.vue'
import ReportsTab from '@/components/feed/ReportsTab.vue'
import apiClient from '@/api/client'

interface LocalFeedFilters {
  myPosts: boolean; following: boolean; fromGroups: boolean; withAnime: boolean
  period: 'all' | 'month' | 'week' | 'day'; sort: 'new' | 'old' | 'best' | 'discussed'
}

type FeedType = 'weighted' | 'followers' | 'hot' | 'top' | 'trending'

const feedStore = useFeedStore()
const authStore = useAuthStore()
const router = useRouter()
const currentUser = computed(() => authStore.user)

const isModerator = computed(() => {
  const u = authStore.user as any
  return u?.is_staff || u?.is_superuser || u?.role === 'moderator' || u?.role === 'admin'
})

const defaultAvatar = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%23333'/%3E%3Ccircle cx='20' cy='15' r='6' fill='%23666'/%3E%3Cpath d='M8 36c0-6.627 5.373-12 12-12s12 5.373 12 12' fill='%23666'/%3E%3C/svg%3E`

// ==================== TABS ====================
const mainTabs = computed(() => {
  const tabs = [
    { id: 'feed', label: '📰 Лента' },
    { id: 'subscriptions', label: '👭 Подписки' },
    { id: 'not_interested', label: '🙊 Не интересно' },
  ]
  if (isModerator.value) tabs.push({ id: 'reports', label: '🚨 Жалобы' })
  return tabs
})

const activeTab = ref('feed')

const feedSubTabs = [
  { type: 'weighted' as FeedType, label: '✨ Для вас' },
  { type: 'followers' as FeedType, label: '👭 Подписки' },
  { type: 'popular' as FeedType, label: '🌠 Популярное' },
  { type: 'trending' as FeedType, label: '💹 Тренды' },
  { type: 'hot' as FeedType, label: '🔥 Горячее' },
]

// ==================== FEED ====================
const feedListRef = ref<HTMLElement | null>(null)
const loadMoreRef = ref<HTMLElement | null>(null)
const showCreatePost = ref(false)
const activeCommentPost = ref<FeedPost | null>(null)
const activeRepostPost = ref<FeedPost | null>(null)
const activeMenuPost = ref<FeedPost | null>(null)
const activeForwardPost = ref<FeedPost | null>(null)

const filters = ref<LocalFeedFilters>({
  myPosts: false, following: false, fromGroups: false, withAnime: false,
  period: 'all', sort: 'new',
})

let intersectionObserver: IntersectionObserver | null = null

function setupInfiniteScroll() {
  intersectionObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && feedStore.hasMore && !feedStore.loadingMore) {
        feedStore.loadMore()
      }
    },
    { rootMargin: '200px' }
  )
  if (loadMoreRef.value) intersectionObserver.observe(loadMoreRef.value)
}

async function switchFeed(type: FeedType) {
  await feedStore.loadFeed(type, true)
}

async function reloadFeed() {
  feedStore.newPostsAvailable = false
  await feedStore.loadFeed(feedStore.feedType, true)
  feedListRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

function onFiltersApply(f: LocalFeedFilters) {
  feedStore.loadFeed(feedStore.feedType, true, {
    myPosts: f.myPosts,
    following: f.following,
    fromGroups: f.fromGroups,
    withAnime: f.withAnime,
    period: f.period,
    sort: f.sort,
  })
}

function handleLike(post: any) { feedStore.likePost(post.id) }
function handleDislike(post: any) { feedStore.dislikePost(post.id) }
function openComments(post: any) { activeCommentPost.value = post }
function openRepost(post: any) { activeRepostPost.value = post }
function openForward(post: any) { activeForwardPost.value = post }
function handleBookmark(post: any) { feedStore.bookmarkPost(post.id) }
function handleShare(post: any) {
  const url = `${window.location.origin}/post/${post.id}`
  if (navigator.clipboard) navigator.clipboard.writeText(url)
}
function openPostMenu(post: any) { activeMenuPost.value = post }

function goToPost(postId: number) {
  router.push(`/post/${postId}`)
}

function onPostCreated(post: any) {
  feedStore.addNewPost(post)
  showCreatePost.value = false
}

function onReposted() { activeRepostPost.value = null }

function onPostDeleted(postId: any) {
  feedStore.deletePost(postId)
  activeMenuPost.value = null
}

function onPostHidden(postId: any) {
  const idx = feedStore.posts.findIndex(p => p.id === postId)
  if (idx !== -1) feedStore.posts.splice(idx, 1)
  activeMenuPost.value = null
}

async function onHideAuthor(post: any) {
  try {
    await subscriptionsApi.addNotInterested(post.author)
    feedStore.posts = feedStore.posts.filter(p => p.author !== post.author)
  } catch (e) { console.error(e) }
  activeMenuPost.value = null
}

function onFollowToggled(userId: number, following: boolean) {
  // обновляем is_following у всех постов этого автора
  feedStore.posts.forEach(p => {
    if ((p as any).author === userId) (p as any).is_following = following
  })
}

// ==================== SUBSCRIPTIONS ====================
const subTab = ref<'profiles' | 'bookmarks'>('profiles')
const subscriptions = ref<SubscriptionUser[]>([])
const subLoading = ref(false)
const subSearch = ref('')
const subSort = ref('date')
const subPage = ref(1)
const subHasMore = ref(false)

const filteredSubscriptions = computed(() => {
  let list = [...subscriptions.value]
  if (subSearch.value) {
    const q = subSearch.value.toLowerCase()
    list = list.filter(u =>
      u.username.toLowerCase().includes(q) || (u.display_name || '').toLowerCase().includes(q)
    )
  }
  if (subSort.value === 'name') {
    list.sort((a, b) => (a.display_name || a.username).localeCompare(b.display_name || b.username))
  }
  return list
})

const loadSubscriptions = async (reset = false) => {
  if (reset) { subPage.value = 1; subscriptions.value = [] }
  subLoading.value = true
  try {
    const { data } = await subscriptionsApi.getSubscriptions(subPage.value, subSearch.value, subSort.value)
    if (reset) subscriptions.value = data.results as any
    else subscriptions.value.push(...(data.results as any))
    subHasMore.value = !!data.next
    subPage.value++
  } catch (e) { console.error(e) }
  finally { subLoading.value = false }
}

const onUnfollowed = (userId: number) => {
  subscriptions.value = subscriptions.value.filter(u => u.id !== userId)
}

// Bookmarks
const bookmarkedPosts = ref<FeedPost[]>([])
const bookmarksLoading = ref(false)
const bookmarksPage = ref(1)
const bookmarksHasMore = ref(false)

const loadBookmarks = async (reset = false) => {
  if (reset) { bookmarksPage.value = 1; bookmarkedPosts.value = [] }
  bookmarksLoading.value = true
  try {
    const { data } = await apiClient.get('/social/bookmarks/', { params: { page: bookmarksPage.value } })
    const posts = (data.results || data || [])
    if (reset) bookmarkedPosts.value = posts
    else bookmarkedPosts.value.push(...posts)
    bookmarksHasMore.value = !!data.next
    bookmarksPage.value++
  } catch (e) { console.error(e) }
  finally { bookmarksLoading.value = false }
}

const switchSubTab = (tab: 'profiles' | 'bookmarks') => {
  subTab.value = tab
  if (tab === 'bookmarks' && bookmarkedPosts.value.length === 0) loadBookmarks(true)
}

// ==================== NOT INTERESTED ====================
const niTab = ref<'profiles' | 'posts'>('profiles')
const notInterested = ref<NotInterestedUser[]>([])
const niLoading = ref(false)
const niSearch = ref('')
const niPage = ref(1)
const niHasMore = ref(false)

const filteredNotInterested = computed(() => {
  if (!niSearch.value) return notInterested.value
  const q = niSearch.value.toLowerCase()
  return notInterested.value.filter(u =>
    u.username.toLowerCase().includes(q) || (u.display_name || '').toLowerCase().includes(q)
  )
})

const loadNotInterested = async (reset = false) => {
  if (reset) { niPage.value = 1; notInterested.value = [] }
  niLoading.value = true
  try {
    const { data } = await subscriptionsApi.getNotInterested(niPage.value)
    if (reset) notInterested.value = data.results as any
    else notInterested.value.push(...(data.results as any))
    niHasMore.value = !!data.next
    niPage.value++
  } catch (e) { console.error(e) }
  finally { niLoading.value = false }
}

const onNiRemoved = (userId: number) => {
  notInterested.value = notInterested.value.filter(u => u.id !== userId)
}

// Скрытые посты
const hiddenPosts = ref<any[]>([])
const hiddenPostsLoading = ref(false)
const hiddenPostsPage = ref(1)
const hiddenPostsHasMore = ref(false)

const loadHiddenPosts = async (reset = false) => {
  if (reset) { hiddenPostsPage.value = 1; hiddenPosts.value = [] }
  hiddenPostsLoading.value = true
  try {
    const { data } = await apiClient.get('/social/feed/hidden/', { params: { page: hiddenPostsPage.value } })
    const posts = data.results || data || []
    if (reset) hiddenPosts.value = posts
    else hiddenPosts.value.push(...posts)
    hiddenPostsHasMore.value = !!data.next
    hiddenPostsPage.value++
  } catch (e) { console.error(e) }
  finally { hiddenPostsLoading.value = false }
}

const switchNiTab = (tab: 'profiles' | 'posts') => {
  niTab.value = tab
  if (tab === 'posts' && hiddenPosts.value.length === 0) loadHiddenPosts(true)
}

const unhidePost = async (postId: number) => {
  try {
    await apiClient.post(`/social/posts/${postId}/unhide/`)
    hiddenPosts.value = hiddenPosts.value.filter(p => p.id !== postId)
  } catch (e) { console.error(e) }
}

// ==================== TAB LOADING ====================
watch(activeTab, (tab) => {
  if (tab === 'subscriptions' && subscriptions.value.length === 0) loadSubscriptions(true)
  if (tab === 'not_interested' && notInterested.value.length === 0) loadNotInterested(true)
  if (tab === 'feed' && popularPosts.value.length === 0) loadPopularPosts()
})

// ==================== POPULAR POSTS ====================
const popularPosts = ref<FeedPost[]>([])
const popularLoading = ref(false)

const loadPopularPosts = async () => {
  popularLoading.value = true
  try {
    const { data } = await apiClient.get('/social/feed/popular/', { params: { page_size: 10 } })
    popularPosts.value = (data.results || data || []).slice(0, 10)
  } catch (e) {
    console.error('Error loading popular posts:', e)
    // Fallback
    try {
      const { data } = await apiClient.get('/social/feed/top/', { params: { days: 7, limit: 10 } })
      popularPosts.value = Array.isArray(data) ? data.slice(0, 10) : (data.results || []).slice(0, 10)
    } catch (e2) {
      console.error('Fallback failed:', e2)
    }
  } finally {
    popularLoading.value = false
  }
}

const truncateText = (text: string | null | undefined, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

onMounted(async () => {
  await feedStore.loadFeed('weighted')
  setupInfiniteScroll()
  await loadPopularPosts()
})

onUnmounted(() => { intersectionObserver?.disconnect() })
</script>

<style scoped>
.feed-page-container {
  max-width: 1200px; margin: 0 auto; padding: 1rem;
  display: flex; flex-direction: column; gap: 1rem;
}

.feed-layout {
  display: flex; gap: 1.5rem;
}

.feed-main {
  flex: 1;
  max-width: 680px;
  min-width: 0;
}

/* Sidebar - Popular */
.feed-sidebar {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .feed-sidebar { display: none; }
}

.sidebar-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  padding: 0.75rem 1rem;
  background: #111;
  border-radius: 12px;
  border: 1px solid #222;
}

.popular-loading {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.spinner-sm {
  width: 24px;
  height: 24px;
  border: 2px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.popular-empty {
  color: #555;
  text-align: center;
  padding: 2rem 1rem;
  background: #111;
  border-radius: 12px;
  font-size: 0.9rem;
}

.popular-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.popular-item {
  background: #111;
  border: 1px solid #222;
  border-radius: 12px;
  padding: 0.875rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.popular-item:hover {
  border-color: #667eea;
  background: #161616;
}

.popular-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.popular-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.popular-author {
  color: #aaa;
  font-size: 0.85rem;
  font-weight: 500;
}

.popular-text {
  color: #888;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.popular-stats {
  display: flex;
  gap: 1rem;
  color: #555;
  font-size: 0.75rem;
}

/* Main Tabs */
.main-tabs {
  display: flex; gap: 0.25rem; background: #111;
  border-radius: 12px; padding: 0.375rem;
}
.main-tab-btn {
  flex: 1; background: none; border: none; color: #666;
  padding: 0.625rem 0.75rem; border-radius: 8px; cursor: pointer;
  font-size: 0.85rem; transition: all 0.2s; white-space: nowrap;
}
.main-tab-btn:hover { background: #1a1a1a; color: #aaa; }
.main-tab-btn.active { background: #667eea; color: #fff; }

/* Feed Sub-tabs */
.feed-subtabs {
  display: flex; gap: 0.5rem; overflow-x: auto;
  padding-bottom: 0.25rem; scrollbar-width: none;
}
.feed-subtabs::-webkit-scrollbar { display: none; }
.tab-btn {
  background: #1a1a1a; color: #888; border: 1px solid #2a2a2a;
  padding: 0.5rem 1rem; border-radius: 20px; cursor: pointer;
  font-size: 0.875rem; white-space: nowrap; transition: all 0.2s;
}
.tab-btn:hover { background: #222; color: #aaa; }
.tab-btn.active { background: #667eea; color: #fff; border-color: #667eea; }

/* Sub-tabs (подписки/не интересно) */
.sub-tabs {
  display: flex; gap: 0.5rem;
  border-bottom: 1px solid #1a1a1a; padding-bottom: 0.5rem;
}
.sub-tab-btn {
  background: none; border: none; color: #666; padding: 0.5rem 1rem;
  cursor: pointer; font-size: 0.9rem; border-radius: 8px; transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.sub-tab-btn:hover { color: #aaa; background: #1a1a1a; }
.sub-tab-btn.active { color: #fff; border-bottom-color: #667eea; }

/* Create Post */
.create-post-area {
  display: flex; align-items: center; gap: 0.75rem;
  background: #111; border: 1px solid #222; border-radius: 12px;
  padding: 0.875rem 1rem; cursor: pointer; transition: border-color 0.2s;
}
.create-post-area:hover { border-color: #667eea; }
.user-avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.placeholder { flex: 1; color: #555; font-size: 0.9rem; }
.btn-post {
  background: #667eea; color: white; border: none;
  padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.875rem; cursor: pointer;
}

/* New Posts */
.new-posts-indicator {
  background: #667eea; color: white; border: none;
  padding: 0.6rem 1.5rem; border-radius: 20px; cursor: pointer;
  font-size: 0.875rem; align-self: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); transition: transform 0.2s;
}
.new-posts-indicator:hover { transform: translateY(-1px); }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.3s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-20px); }

/* Feed */
.feed-list { display: flex; flex-direction: column; gap: 1rem; }

/* Skeletons */
.post-skeleton { background: #111; border-radius: 12px; padding: 1rem; }
.skeleton-header { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; }
.skeleton-avatar { width: 44px; height: 44px; border-radius: 50%; background: #1f1f1f; animation: pulse 1.5s infinite; flex-shrink: 0; }
.skeleton-meta { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; justify-content: center; }
.skeleton-body { display: flex; flex-direction: column; gap: 0.5rem; }
.skeleton-line { height: 14px; background: #1f1f1f; border-radius: 4px; animation: pulse 1.5s infinite; }
.skeleton-line.short { width: 60%; }
.skeleton-line.shorter { width: 40%; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* Empty / Error */
.empty-feed {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.75rem; padding: 3rem 1rem; text-align: center;
}
.empty-icon { font-size: 3rem; }
.empty-title { color: #fff; font-size: 1.2rem; font-weight: 600; margin: 0; }
.empty-desc { color: #666; margin: 0; }
.btn-explore { background: #667eea; color: white; border: none; padding: 0.6rem 1.5rem; border-radius: 8px; cursor: pointer; margin-top: 0.5rem; }
.error-state { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 2rem; text-align: center; color: #888; }
.error-icon { font-size: 2rem; }
.btn-retry { background: #333; color: #fff; border: none; padding: 0.5rem 1.25rem; border-radius: 8px; cursor: pointer; }
.load-more-trigger { padding: 1rem 0; display: flex; justify-content: center; }
.loading-more { display: flex; justify-content: center; padding: 1rem; }
.end-of-feed { color: #555; font-size: 0.875rem; padding: 1rem; }

/* Tabs toolbar */
.tab-toolbar { display: flex; gap: 0.5rem; }
.search-input {
  flex: 1; background: #111; border: 1px solid #2a2a2a;
  border-radius: 8px; padding: 0.625rem 0.875rem;
  color: #ddd; font-size: 0.875rem;
}
.search-input:focus { outline: none; border-color: #667eea; }
.sort-select {
  background: #111; border: 1px solid #2a2a2a; color: #aaa;
  padding: 0.625rem 0.75rem; border-radius: 8px; font-size: 0.875rem; cursor: pointer;
}

/* Cards */
.cards-list { display: flex; flex-direction: column; gap: 0.5rem; }
.loading-center { display: flex; justify-content: center; padding: 3rem; }
.spinner {
  width: 28px; height: 28px; border: 2px solid #333;
  border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.load-more-wrap { display: flex; justify-content: center; }
.btn-load-more {
  background: #1a1a1a; border: 1px solid #2a2a2a; color: #888;
  padding: 0.75rem 2rem; border-radius: 8px; cursor: pointer;
  font-size: 0.875rem; transition: all 0.2s;
}
.btn-load-more:hover:not(:disabled) { background: #222; color: #aaa; }
.btn-load-more:disabled { opacity: 0.5; cursor: not-allowed; }

/* Hidden posts */
.hidden-post-item {
  display: flex; align-items: center; gap: 0.75rem;
  background: #111; border-radius: 10px; padding: 0.75rem 1rem;
  transition: background 0.2s;
}
.hidden-post-item:hover { background: #161616; }
.hidden-post-info {
  display: flex; align-items: center; gap: 0.75rem;
  flex: 1; cursor: pointer; min-width: 0;
}
.hp-avatar { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; flex-shrink: 0; filter: grayscale(40%); }
.hp-meta { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.hp-author { color: #aaa; font-size: 0.85rem; font-weight: 600; }
.hp-text { color: #555; font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-unblock-post {
  background: #1a1a1a; border: 1px solid #2a2a2a; color: #667eea;
  padding: 0.4rem 0.75rem; border-radius: 8px; cursor: pointer;
  font-size: 0.875rem; flex-shrink: 0; transition: all 0.2s;
}
.btn-unblock-post:hover { background: #222; border-color: #667eea; }
</style>
