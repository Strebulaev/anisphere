import { ref } from 'vue'
import { defineStore } from 'pinia'
import { postsApi, commentsApi, type FeedPost, type PostComment } from '@/api/feed'
import { normalizeComment } from '@/utils/normalizers'

export const usePostStore = defineStore('post', () => {
  const currentPost = ref<FeedPost | null>(null)
  const comments = ref<PostComment[]>([])
  const loadingPost = ref(false)
  const loadingComments = ref(false)
  const loadingMoreComments = ref(false)
  const commentsPage = ref(1)
  const commentsHasMore = ref(true)
  const commentsSort = ref<'best' | 'newest' | 'oldest'>('best')
  const error = ref<string | null>(null)

  async function fetchPost(id: number) {
    loadingPost.value = true
    error.value = null
    try {
      const { data } = await postsApi.getPost(id)
      currentPost.value = data
      // Record view
      postsApi.viewPost(id).catch(() => {})
    } catch {
      error.value = 'Пост не найден'
    } finally {
      loadingPost.value = false
    }
  }

  async function fetchComments(postId: number, sort = commentsSort.value, reset = true) {
    if (reset) {
      comments.value = []
      commentsPage.value = 1
      commentsHasMore.value = true
    }

    commentsSort.value = sort
    loadingComments.value = true

    try {
      const { data } = await commentsApi.getComments(postId, sort, 1)
      comments.value = data.results
      if (data.next === null) commentsHasMore.value = false
    } catch {
      // ignore
    } finally {
      loadingComments.value = false
    }
  }

  async function loadMoreComments(postId: number) {
    if (loadingMoreComments.value || !commentsHasMore.value) return

    loadingMoreComments.value = true
    const nextPage = commentsPage.value + 1

    try {
      const { data } = await commentsApi.getComments(postId, commentsSort.value, nextPage)
      comments.value.push(...data.results)
      commentsPage.value = nextPage
      if (data.next === null) commentsHasMore.value = false
    } catch {
      // ignore
    } finally {
      loadingMoreComments.value = false
    }
  }

  async function addComment(postId: number, content: string, parentId?: number) {
    try {
      const { data } = await commentsApi.createComment(postId, content, parentId)
      // ensure necessary fields are present (author info/timestamp)
      const normalized = normalizeComment(data)

      if (parentId) {
        // Add as reply to parent
        const parent = findComment(comments.value, parentId)
        if (parent) {
          if (!parent.replies) parent.replies = []
          parent.replies.push(normalized)
          parent.replies_count++
        }
      } else {
        comments.value.unshift(normalized)
      }

      if (currentPost.value) {
        currentPost.value.comments_count++
      }

      return normalized
    } catch (err: unknown) {
      throw err
    }
  }

  async function deleteComment(postId: number, commentId: number) {
    try {
      await commentsApi.deleteComment(postId, commentId)
      removeComment(comments.value, commentId)
      if (currentPost.value) {
        currentPost.value.comments_count = Math.max(0, currentPost.value.comments_count - 1)
      }
    } catch {
      // ignore
    }
  }

  async function likeComment(commentId: number) {
    const comment = findComment(comments.value, commentId)
    if (!comment) return

    const wasLiked = comment.is_liked
    const wasDisliked = comment.is_disliked

    // Optimistic
    if (wasLiked) {
      comment.is_liked = false
      comment.likes_count--
    } else {
      if (wasDisliked) {
        comment.is_disliked = false
        comment.dislikes_count--
      }
      comment.is_liked = true
      comment.likes_count++
    }

    try {
      const { data } = await commentsApi.likeComment(commentId)
      comment.is_liked = data.liked
      comment.likes_count = data.likes_count
    } catch {
      comment.is_liked = wasLiked
      comment.is_disliked = wasDisliked
      if (wasLiked) comment.likes_count++
      else comment.likes_count--
    }
  }

  async function dislikeComment(commentId: number) {
    const comment = findComment(comments.value, commentId)
    if (!comment) return

    const wasLiked = comment.is_liked
    const wasDisliked = comment.is_disliked

    if (wasDisliked) {
      comment.is_disliked = false
      comment.dislikes_count--
    } else {
      if (wasLiked) {
        comment.is_liked = false
        comment.likes_count--
      }
      comment.is_disliked = true
      comment.dislikes_count++
    }

    try {
      const { data } = await commentsApi.dislikeComment(commentId)
      comment.is_disliked = data.disliked
      comment.dislikes_count = data.dislikes_count
    } catch {
      comment.is_liked = wasLiked
      comment.is_disliked = wasDisliked
    }
  }

  function clear() {
    currentPost.value = null
    comments.value = []
    error.value = null
  }

  return {
    currentPost,
    comments,
    loadingPost,
    loadingComments,
    loadingMoreComments,
    commentsHasMore,
    commentsSort,
    error,
    fetchPost,
    fetchComments,
    loadMoreComments,
    addComment,
    deleteComment,
    likeComment,
    dislikeComment,
    clear,
  }
})

// Helpers
function findComment(comments: PostComment[], id: number): PostComment | null {
  for (const c of comments) {
    if (c.id === id) return c
    if (c.replies) {
      const found = findComment(c.replies, id)
      if (found) return found
    }
  }
  return null
}

function removeComment(comments: PostComment[], id: number): boolean {
  for (let i = 0; i < comments.length; i++) {
    const c = comments[i]
    if (!c) continue

    if (c.id === id) {
      comments.splice(i, 1)
      return true
    }
    if (c.replies && removeComment(c.replies, id)) {
      return true
    }
  }
  return false
}
