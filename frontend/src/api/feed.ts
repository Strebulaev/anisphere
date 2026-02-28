import apiClient from './client'

export interface FeedPost {
  id: number
  author: number
  author_username: string
  author_display_name: string | null
  author_avatar: string | null
  title: string
  post_type: 'text' | 'image' | 'video' | 'playlist' | 'anime' | 'repost' | 'system'
  status: 'published' | 'draft' | 'deleted' | 'moderated'
  visibility: 'public' | 'followers' | 'friends' | 'private'
  text: string
  image_url: string | null
  video_url: string | null
  anime: AnimeCard | null
  anime_rating: number | null
  playlist: PlaylistCard | null
  reactor_post: ReactorCard | null
  group: GroupCard | null
  original_post: FeedPost | null
  repost_comment: string
  likes_count: number
  dislikes_count: number
  comments_count: number
  reposts_count: number
  views_count: number
  shares_count: number
  is_pinned: boolean
  is_deleted: boolean
  is_spoiler: boolean
  allow_comments: boolean
  created_at: string
  updated_at: string
  edited_at: string | null
  published_at: string | null
  media_files: MediaFile[]
  hashtags: string[]
  is_liked: boolean
  is_disliked: boolean
  is_bookmarked: boolean
  can_edit: boolean
  can_delete: boolean
  system_type?: string | null
}

export interface MediaFile {
  id: number
  media_type: 'image' | 'video'
  url: string
  thumbnail?: string
  caption?: string
  order: number
  width?: number
  height?: number
  duration?: number
}

export interface AnimeCard {
  id: number
  title_ru: string
  title_en?: string
  poster_url?: string
}

export interface PlaylistCard {
  id: number
  title: string
  anime_count: number
  anime?: AnimeCard[]
}

export interface ReactorCard {
  id: number
  title?: string
  video_url: string
  duration?: number
  likes_count: number
  comments_count: number
  user?: { username: string }
}

export interface GroupCard {
  id: number
  name: string
  slug: string
}

export interface PostComment {
  id: number
  post: number
  author: number
  author_username: string
  author_display_name: string | null
  author_avatar: string | null
  parent: number | null
  content: string
  is_edited: boolean
  is_deleted: boolean
  likes_count: number
  dislikes_count: number
  replies_count: number
  level: number
  created_at: string
  updated_at: string
  is_liked: boolean
  is_disliked: boolean
  replies?: PostComment[]
}

export interface FeedPage {
  results: FeedPost[]
  count: number
  next: number | null
  previous: number | null
}

// ==================== FEED ====================

export const feedApi = {
  getWeightedFeed: (page = 1, pageSize = 20) =>
    apiClient.get<FeedPage>('/social/feed/weighted/', { params: { page, page_size: pageSize } }),

  getFollowersFeed: (page = 1, pageSize = 20) =>
    apiClient.get<FeedPage>('/social/feed/followers/', { params: { page, page_size: pageSize } }),

  getHotFeed: (hours = 24, limit = 20) =>
    apiClient.get<FeedPost[]>('/social/feed/hot/', { params: { hours, limit } }),

  getTopFeed: (days = 7, limit = 20) =>
    apiClient.get<FeedPost[]>('/social/feed/top/', { params: { days, limit } }),

  getTrendingFeed: (hours = 6, limit = 20) =>
    apiClient.get<FeedPost[]>('/social/feed/trending/', { params: { hours, limit } }),
}

// ==================== POSTS ====================

export const postsApi = {
  getPost: (id: number) =>
    apiClient.get<FeedPost>(`/social/posts/${id}/`),

  getPosts: (params?: { author?: number; group?: number; anime?: number; page?: number }) =>
    apiClient.get<FeedPage>('/social/posts/', { params }),

  createPost: (data: FormData | Record<string, unknown>) => {
    const isFormData = data instanceof FormData
    return apiClient.post<FeedPost>('/social/posts/', data, {
      headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : {}
    })
  },

  updatePost: (id: number, data: Partial<FeedPost>) =>
    apiClient.patch<FeedPost>(`/social/posts/${id}/`, data),

  deletePost: (id: number) =>
    apiClient.delete(`/social/posts/${id}/`),

  likePost: (id: number) =>
    apiClient.post<{ liked: boolean; likes_count: number; dislikes_count?: number }>(`/social/posts/${id}/like/`),

  dislikePost: (id: number) =>
    apiClient.post<{ disliked: boolean; dislikes_count: number; likes_count?: number }>(`/social/posts/${id}/dislike/`),

  repostPost: (id: number, comment?: string) =>
    apiClient.post(`/social/posts/${id}/repost/action/`, { comment }),

  bookmarkPost: (id: number) =>
    apiClient.post(`/social/posts/${id}/bookmark/`),

  removeBookmark: (id: number) =>
    apiClient.post(`/social/posts/${id}/bookmark/remove/`),

  viewPost: (id: number) =>
    apiClient.post(`/social/posts/${id}/view/`),

  pinPost: (id: number) =>
    apiClient.post(`/social/posts/${id}/pin/`),

  unpinPost: (id: number) =>
    apiClient.post(`/social/posts/${id}/unpin/`),

  reportPost: (id: number, reason: string, comment?: string) =>
    apiClient.post(`/social/posts/${id}/report/`, { reason, comment }),

  hidePost: (id: number) =>
    apiClient.post(`/social/posts/${id}/hide/`),

  notInterestedPost: (id: number) =>
    apiClient.post(`/social/posts/${id}/not-interested/`),

  getLikers: (id: number) =>
    apiClient.get(`/social/posts/${id}/likers/`),

  getUserPosts: (userId: number, page = 1) =>
    apiClient.get<FeedPage>(`/social/users/${userId}/posts/`, { params: { page } }),
}

// ==================== COMMENTS ====================

export const commentsApi = {
  getComments: (postId: number, sort = 'best', page = 1) =>
    apiClient.get<{ results: PostComment[]; count: number; next: number | null }>(`/social/posts/${postId}/comments/`, {
      params: { sort, page }
    }),

  createComment: (postId: number, content: string, parentId?: number) =>
    apiClient.post<PostComment>(`/social/posts/${postId}/comments/`, {
      content,
      parent: parentId || null
    }),

  updateComment: (postId: number, commentId: number, content: string) =>
    apiClient.put<PostComment>(`/social/posts/${postId}/comments/${commentId}/`, { content }),

  deleteComment: (postId: number, commentId: number) =>
    apiClient.delete(`/social/posts/${postId}/comments/${commentId}/`),

  getReplies: (commentId: number) =>
    apiClient.get<PostComment[]>(`/social/comments/${commentId}/replies/`),

  likeComment: (commentId: number) =>
    apiClient.post<{ liked: boolean; likes_count: number }>(`/social/comments/${commentId}/like/`),

  dislikeComment: (commentId: number) =>
    apiClient.post<{ disliked: boolean; dislikes_count: number }>(`/social/comments/${commentId}/dislike/`),

  reportComment: (commentId: number, reason: string) =>
    apiClient.post(`/social/comments/${commentId}/report/`, { reason }),
}

// ==================== FOLLOWS ====================

export const followsApi = {
  toggleFollow: (userId: number) =>
    apiClient.post<{ following: boolean; message: string }>(`/social/follow/toggle/${userId}/`),

  getFollowers: (userId: number, page = 1) =>
    apiClient.get(`/social/follows/`, { params: { following: userId, page } }),

  getFollowing: (userId: number, page = 1) =>
    apiClient.get(`/social/follows/`, { params: { follower: userId, page } }),
}
