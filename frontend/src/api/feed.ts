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
  image_file: string | null
  video_url: string | null
  video_file: string | null
  is_following: boolean
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
  url: string | null
  file_url: string | null
  thumbnail?: string | null
  thumbnail_url?: string | null
  caption?: string | null
  order: number
  width?: number
  height?: number
  duration?: number
}

export interface AnimeCard {
  id: number
  title_ru: string
  title_en?: string
  poster_url?: string  // URL Shikimori (не использовать)
  poster?: string | null  // Локальный путь к файлу (приоритетный)
}

export interface PlaylistCard {
  id: number
  title: string
  anime_count: number
  items_count?: number  // Альтернативное поле
  description?: string
  anime?: (AnimeCard & { poster?: string | null })[]
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

  // Популярные посты (по лайкам)
  getPopularFeed: (page = 1, pageSize = 20, period = 'week') =>
    apiClient.get<FeedPage>('/social/feed/popular/', { 
      params: { page, page_size: pageSize, period } 
    }),
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
  getComments: (postId: number, page = 1) =>
    apiClient.get<{ results: PostComment[]; count: number; next: number | null }>(`/social/posts/${postId}/comments/`, {
      params: { page }
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

// ==================== SUBSCRIPTIONS ====================

export interface SubscriptionUser {
  id: number
  username: string
  display_name: string | null
  avatar_url: string | null
  avatar?: string | null
  followers_count: number
  is_online: boolean
  followed_at: string
}

export interface NotInterestedUser {
  id: number
  username: string
  display_name: string | null
  avatar_url: string | null
  avatar?: string | null
  hidden_at: string
}

export interface HiddenPost {
  id: number
  post_id: number
  post_preview: string
  hidden_at: string
}

export interface ReportItem {
  id: number
  reporter: number
  reporter_username: string
  content_type: 'post' | 'comment'
  content_id: number
  reason: string
  comment: string
  status: 'pending' | 'resolved' | 'rejected'
  resolved_by: number | null
  resolved_at: string | null
  created_at: string
  content_preview?: string
  content_author?: string
  moderation_comment?: string
}

export const subscriptionsApi = {
  // Подписки
  getSubscriptions: (page = 1, search?: string, sort = 'date') =>
    apiClient.get<{ results: SubscriptionUser[]; count: number; next: number | null }>('/social/subscriptions/', {
      params: { page, search, sort }
    }),

  unfollow: (userId: number) =>
    apiClient.delete<{ success: boolean; message: string }>(`/social/subscriptions/${userId}/unfollow/`),

  // Скрытые профили
  getNotInterested: (page = 1, search?: string) =>
    apiClient.get<{ results: NotInterestedUser[]; count: number; next: number | null }>('/social/not-interested/', {
      params: { page, search }
    }),

  // Скрытые посты
  getHiddenPosts: (page = 1) =>
    apiClient.get<{ results: HiddenPost[]; count: number; next: number | null }>('/social/hidden-posts/', {
      params: { page }
    }),

  restoreHiddenPost: (postId: number) =>
    apiClient.delete<{ success: boolean; message: string }>(`/social/hidden-posts/${postId}/restore/`),

  removeNotInterested: (userId: number) =>
    apiClient.delete<{ hidden: boolean; message: string }>(`/social/not-interested/${userId}/`),

  addNotInterested: (userId: number) =>
    apiClient.post<{ success: boolean; message: string }>(`/social/users/${userId}/hide/`),

  // Жалобы
  getReports: (params?: { status?: string; content_type?: string; reason?: string; page?: number }) =>
    apiClient.get<{ results: ReportItem[]; count: number; next: number | null }>('/social/moderation/reports/', { params }),

  resolveReport: (id: number, action: string, comment?: string) =>
    apiClient.patch<ReportItem>(`/social/moderation/reports/${id}/`, { status: action === 'reject' ? 'rejected' : 'resolved', action, moderator_comment: comment }),

  rejectReport: (id: number, comment?: string) =>
    apiClient.patch<ReportItem>(`/social/moderation/reports/${id}/`, { status: 'rejected', moderator_comment: comment }),
}

// ==================== BOOKMARKS ====================

export const bookmarksApi = {
  getPosts: (page = 1) =>
    apiClient.get<{ results: FeedPost[]; count: number; next: number | null }>('/social/bookmarks/posts/', {
      params: { page }
    }),
}

// ==================== CHATS FOR FORWARD ====================

export interface ForwardChat {
  id: number
  type: 'private' | 'group'
  name: string
  avatar: string | null
  is_online?: boolean
  members_count?: number
}

export const chatsApi = {
  getChatsForForward: (search?: string) =>
    apiClient.get<ForwardChat[]>('/social/chats/for-forward/', { params: { search } }),

  forwardPost: (chatId: number, postId: number, message?: string) =>
    apiClient.post<{ success: boolean; message_id: number }>(`/social/chats/${chatId}/forward/`, {
      post_id: postId,
      message
    }),
}

// ==================== EXTENDED FEED ====================

export interface ExtendedFeedParams {
  page?: number
  page_size?: number
  sort?: 'new' | 'old' | 'best' | 'discussed'
  anime_id?: number
  my_posts?: boolean
  subscriptions?: boolean
  groups?: boolean
  tags?: string[]
  date_range?: 'all' | 'month' | 'week' | 'day'
}

export const extendedFeedApi = {
  getFeed: (params: ExtendedFeedParams = {}) =>
    apiClient.get<{ results: FeedPost[]; count: number; next: number | null; previous: number | null }>(
      '/social/feed/extended/',
      { params }
    ),
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
