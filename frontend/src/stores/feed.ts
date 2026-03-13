import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { feedApi, postsApi, extendedFeedApi, type FeedPost, type FeedPage } from '@/api/feed'
import { normalizePost } from '@/utils/normalizers'
import apiClient from '@/api/client'

type FeedType = 'weighted' | 'followers' | 'hot' | 'top' | 'trending'

export interface FeedFiltersState {
  myPosts: boolean
  following: boolean
  fromGroups: boolean
  withAnime: boolean
  period: 'all' | 'month' | 'week' | 'day'
  sort: 'new' | 'old' | 'best' | 'discussed'
}

export const useFeedStore = defineStore('feed', () => {
  // State
  const posts = ref<FeedPost[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const currentPage = ref(1)
  const hasMore = ref(true)
  const feedType = ref<FeedType>('weighted')
  const error = ref<string | null>(null)
  const newPostsAvailable = ref(false)
  const activeFilters = ref<FeedFiltersState>({
    myPosts: false, following: false, fromGroups: false,
    withAnime: false, period: 'all', sort: 'new',
  })

  // Computed
  const isEmpty = computed(() => !loading.value && posts.value.length === 0)

  // Actions
  async function loadFeed(type: FeedType = 'weighted', reset = true, filters?: Partial<FeedFiltersState>) {
    if (reset) {
      posts.value = []
      currentPage.value = 1
      hasMore.value = true
      error.value = null
    }

    if (filters) activeFilters.value = { ...activeFilters.value, ...filters }

    feedType.value = type
    loading.value = true

    try {
      const hasActiveFilters = activeFilters.value.myPosts || activeFilters.value.following
        || activeFilters.value.fromGroups || activeFilters.value.withAnime
        || activeFilters.value.period !== 'all' || activeFilters.value.sort !== 'new'

      // Если есть фильтры — используем расширенный endpoint
      if (hasActiveFilters) {
        const params: Record<string, any> = {
          page: 1, page_size: 20,
          sort: activeFilters.value.sort,
          date_range: activeFilters.value.period,
        }
        if (activeFilters.value.myPosts) params.my_posts = true
        if (activeFilters.value.following) params.subscriptions = true
        if (activeFilters.value.fromGroups) params.groups = true
        if (activeFilters.value.withAnime) params.with_anime = true

        try {
          const { data } = await apiClient.get('/social/feed/extended/', { params })
          const results = data.results || data || []
          posts.value = results.map(normalizePost)
          hasMore.value = !!data.next
        } catch {
          // fallback to regular
          await _loadRegularFeed(type)
        }
      } else {
        await _loadRegularFeed(type)
      }

      currentPage.value = 1
    } catch (err: unknown) {
      error.value = 'Не удалось загрузить ленту'
    } finally {
      loading.value = false
    }
  }

  async function _loadRegularFeed(type: FeedType) {
    let data: FeedPost[] | FeedPage

    switch (type) {
      case 'weighted':
        data = (await feedApi.getWeightedFeed(1)).data
        break
      case 'followers':
        data = (await feedApi.getFollowersFeed(1)).data
        break
      case 'hot':
        data = (await feedApi.getHotFeed()).data
        hasMore.value = false
        break
      case 'top':
        // Топ по лайкам
        try {
          const { data: topData } = await apiClient.get('/social/feed/top/', { params: { days: 30, limit: 50 } })
          const results = Array.isArray(topData) ? topData : topData.results || []
          posts.value = results.map(normalizePost)
          hasMore.value = false
          return
        } catch {
          data = (await feedApi.getTopFeed()).data
        }
        hasMore.value = false
        break
      case 'trending':
        data = (await feedApi.getTrendingFeed()).data
        hasMore.value = false
        break
      default:
        data = (await feedApi.getWeightedFeed(1)).data
    }

    const results = Array.isArray(data) ? data : data.results
    posts.value = results.map(normalizePost)

    if (!Array.isArray(data) && (data as FeedPage).next === null) {
      hasMore.value = false
    }
  }

  async function loadMore() {
    if (loadingMore.value || !hasMore.value) return
    if (feedType.value === 'hot' || feedType.value === 'top' || feedType.value === 'trending') return

    loadingMore.value = true
    const nextPage = currentPage.value + 1

    try {
      const hasActiveFilters = activeFilters.value.myPosts || activeFilters.value.following
        || activeFilters.value.fromGroups || activeFilters.value.withAnime
        || activeFilters.value.period !== 'all' || activeFilters.value.sort !== 'new'

      if (hasActiveFilters) {
        const params: Record<string, any> = {
          page: nextPage, page_size: 20,
          sort: activeFilters.value.sort, date_range: activeFilters.value.period,
        }
        if (activeFilters.value.myPosts) params.my_posts = true
        if (activeFilters.value.following) params.subscriptions = true
        if (activeFilters.value.fromGroups) params.groups = true
        if (activeFilters.value.withAnime) params.with_anime = true

        const { data } = await apiClient.get('/social/feed/extended/', { params })
        const results = data.results || []
        posts.value.push(...results.map(normalizePost))
        hasMore.value = !!data.next
      } else {
        let data: FeedPage
        switch (feedType.value) {
          case 'followers':
            data = (await feedApi.getFollowersFeed(nextPage)).data
            break
          default:
            data = (await feedApi.getWeightedFeed(nextPage)).data
        }
        posts.value.push(...data.results.map(normalizePost))
        if (data.next === null) hasMore.value = false
      }

      currentPage.value = nextPage
    } catch (err: unknown) {
      // silently fail
    } finally {
      loadingMore.value = false
    }
  }

  // Optimistic like
  function optimisticLike(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    if (post.is_liked) { post.is_liked = false; post.likes_count-- }
    else {
      if (post.is_disliked) { post.is_disliked = false; post.dislikes_count-- }
      post.is_liked = true; post.likes_count++
    }
  }

  function optimisticDislike(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    if (post.is_disliked) { post.is_disliked = false; post.dislikes_count-- }
    else {
      if (post.is_liked) { post.is_liked = false; post.likes_count-- }
      post.is_disliked = true; post.dislikes_count++
    }
  }

  function revertPost(postId: number, snapshot: Partial<FeedPost>) {
    const post = posts.value.find(p => p.id === postId)
    if (post) Object.assign(post, snapshot)
  }

  async function likePost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    const snapshot = { is_liked: post.is_liked, is_disliked: post.is_disliked, likes_count: post.likes_count, dislikes_count: post.dislikes_count }
    optimisticLike(postId)
    try {
      const { data } = await postsApi.likePost(postId)
      post.likes_count = data.likes_count; post.is_liked = data.liked
      if (data.dislikes_count !== undefined) { post.dislikes_count = data.dislikes_count; post.is_disliked = false }
    } catch { revertPost(postId, snapshot) }
  }

  async function dislikePost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    const snapshot = { is_liked: post.is_liked, is_disliked: post.is_disliked, likes_count: post.likes_count, dislikes_count: post.dislikes_count }
    optimisticDislike(postId)
    try {
      const { data } = await postsApi.dislikePost(postId)
      post.dislikes_count = data.dislikes_count; post.is_disliked = data.disliked
      if (data.likes_count !== undefined) { post.likes_count = data.likes_count; post.is_liked = false }
    } catch { revertPost(postId, snapshot) }
  }

  async function bookmarkPost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    const wasBookmarked = post.is_bookmarked
    post.is_bookmarked = !wasBookmarked
    try {
      if (wasBookmarked) await postsApi.removeBookmark(postId)
      else await postsApi.bookmarkPost(postId)
    } catch { post.is_bookmarked = wasBookmarked }
  }

  async function deletePost(postId: number) {
    try {
      await postsApi.deletePost(postId)
      posts.value = posts.value.filter(p => p.id !== postId)
    } catch {}
  }

  function addNewPost(post: FeedPost) {
    posts.value.unshift(normalizePost(post))
  }

  function updatePost(updatedPost: FeedPost) {
    const idx = posts.value.findIndex(p => p.id === updatedPost.id)
    if (idx !== -1) posts.value[idx] = updatedPost
  }

  function incrementCommentCount(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (post) post.comments_count++
  }

  return {
    posts, loading, loadingMore, hasMore, feedType, error, isEmpty,
    newPostsAvailable, activeFilters,
    loadFeed, loadMore, likePost, dislikePost, bookmarkPost,
    deletePost, addNewPost, updatePost, incrementCommentCount,
  }
})
