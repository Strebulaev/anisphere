import { useAuthStore } from '@/stores/auth'
import { getMediaBaseUrl } from '@/api/client'

function toAbsoluteUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const base = getMediaBaseUrl()
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`
}


function ensureUserFields(obj: any, user: any) {
  if (!user) return obj
  if (obj.author === undefined || obj.author === null) obj.author = user.id
  if (!obj.author_username) obj.author_username = user.username
  if (obj.author_display_name === undefined || obj.author_display_name === null) obj.author_display_name = user.display_name || null
  if (obj.author_avatar === undefined || obj.author_avatar === null) obj.author_avatar = user.avatar || null
  return obj
}

export function normalizePost(post: any) {
  const authStore = useAuthStore()
  const user = authStore.user

  ensureUserFields(post, user)

  if (!post.created_at) {
    post.created_at = new Date().toISOString()
  }
  if (!post.published_at) {
    post.published_at = post.created_at
  }

  if (post.anime_data && typeof post.anime !== 'object') {
    post.anime = post.anime_data
  } else if (post.anime && typeof post.anime === 'object' && !post.anime.poster_url && post.anime_data) {
    post.anime = post.anime_data
  }

  if (post.anime && typeof post.anime === 'object') {
    post.anime.poster_url = toAbsoluteUrl(post.anime.poster_url) ?? post.anime.poster_url
  }

  if (post.playlist_data && typeof post.playlist !== 'object') {
    post.playlist = post.playlist_data
  }
  if (post.group_data && typeof post.group !== 'object') {
    post.group = post.group_data
  }

  return post
}

export function normalizeComment(comment: any) {
  const authStore = useAuthStore()
  const user = authStore.user

  ensureUserFields(comment, user)

  if (!comment.created_at) {
    comment.created_at = new Date().toISOString()
  }

  return comment
}

export function normalizeMessage(message: any) {
  const authStore = useAuthStore()
  const user = authStore.user

  ensureUserFields(message, user)

  if (!message.created_at) {
    message.created_at = new Date().toISOString()
  }

  return message
}
