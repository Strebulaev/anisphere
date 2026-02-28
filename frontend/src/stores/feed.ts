import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { feedApi, postsApi, type FeedPost, type FeedPage } from '@/api/feed'

type FeedType = 'weighted' | 'followers' | 'hot' | 'top' | 'trending'

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

  // Computed
  const isEmpty = computed(() => !loading.value && posts.value.length === 0)

  // Actions
  async function loadFeed(type: FeedType = 'weighted', reset = true) {
    if (reset) {
      posts.value = []
      currentPage.value = 1
      hasMore.value = true
      error.value = null
    }

    feedType.value = type
    loading.value = true

    try {
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
          data = (await feedApi.getTopFeed()).data
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
      posts.value = results
      currentPage.value = 1

      if (!Array.isArray(data) && data.next === null) {
        hasMore.value = false
      }
    } catch (err: unknown) {
      error.value = 'Не удалось загрузить ленту'
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (loadingMore.value || !hasMore.value) return
    if (feedType.value === 'hot' || feedType.value === 'top' || feedType.value === 'trending') return

    loadingMore.value = true
    const nextPage = currentPage.value + 1

    try {
      let data: FeedPage

      switch (feedType.value) {
        case 'followers':
          data = (await feedApi.getFollowersFeed(nextPage)).data
          break
        default:
          data = (await feedApi.getWeightedFeed(nextPage)).data
      }

      posts.value.push(...data.results)
      currentPage.value = nextPage

      if (data.next === null) {
        hasMore.value = false
      }
    } catch (err: unknown) {
      // silently fail on pagination
    } finally {
      loadingMore.value = false
    }
  }

  // Optimistic like
  function optimisticLike(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    if (post.is_liked) {
      post.is_liked = false
      post.likes_count--
    } else {
      if (post.is_disliked) {
        post.is_disliked = false
        post.dislikes_count--
      }
      post.is_liked = true
      post.likes_count++
    }
  }

  // Optimistic dislike
  function optimisticDislike(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    if (post.is_disliked) {
      post.is_disliked = false
      post.dislikes_count--
    } else {
      if (post.is_liked) {
        post.is_liked = false
        post.likes_count--
      }
      post.is_disliked = true
      post.dislikes_count++
    }
  }

  // Revert optimistic update
  function revertPost(postId: number, snapshot: Partial<FeedPost>) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return
    Object.assign(post, snapshot)
  }

  async function likePost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    const snapshot = {
      is_liked: post.is_liked,
      is_disliked: post.is_disliked,
      likes_count: post.likes_count,
      dislikes_count: post.dislikes_count,
    }

    optimisticLike(postId)

    try {
      const { data } = await postsApi.likePost(postId)
      post.likes_count = data.likes_count
      post.is_liked = data.liked
      if (data.dislikes_count !== undefined) {
        post.dislikes_count = data.dislikes_count
        post.is_disliked = false
      }
    } catch {
      revertPost(postId, snapshot)
    }
  }

  async function dislikePost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    const snapshot = {
      is_liked: post.is_liked,
      is_disliked: post.is_disliked,
      likes_count: post.likes_count,
      dislikes_count: post.dislikes_count,
    }

    optimisticDislike(postId)

    try {
      const { data } = await postsApi.dislikePost(postId)
      post.dislikes_count = data.dislikes_count
      post.is_disliked = data.disliked
      if (data.likes_count !== undefined) {
        post.likes_count = data.likes_count
        post.is_liked = false
      }
    } catch {
      revertPost(postId, snapshot)
    }
  }

  async function bookmarkPost(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    const wasBookmarked = post.is_bookmarked
    post.is_bookmarked = !wasBookmarked

    try {
      if (wasBookmarked) {
        await postsApi.removeBookmark(postId)
      } else {
        await postsApi.bookmarkPost(postId)
      }
    } catch {
      post.is_bookmarked = wasBookmarked
    }
  }

  async function deletePost(postId: number) {
    try {
      await postsApi.deletePost(postId)
      posts.value = posts.value.filter(p => p.id !== postId)
    } catch {
      // ignore
    }
  }

  function addNewPost(post: FeedPost) {
    posts.value.unshift(post)
  }

  function updatePost(updatedPost: FeedPost) {
    const idx = posts.value.findIndex(p => p.id === updatedPost.id)
    if (idx !== -1) {
      posts.value[idx] = updatedPost
    }
  }

  function incrementCommentCount(postId: number) {
    const post = posts.value.find(p => p.id === postId)
    if (post) post.comments_count++
  }

  return {
    posts,
    loading,
    loadingMore,
    hasMore,
    feedType,
    error,
    isEmpty,
    newPostsAvailable,
    loadFeed,
    loadMore,
    likePost,
    dislikePost,
    bookmarkPost,
    deletePost,
    addNewPost,
    updatePost,
    incrementCommentCount,
  }
})
