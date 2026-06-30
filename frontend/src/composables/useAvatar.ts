export function useAvatar() {
  const getAvatarUrl = (avatarPath: string | null | undefined, userId?: number): string => {
    if (!avatarPath || avatarPath.trim() === '') {
      if (userId !== undefined) {
        return `/media/def_avatars/${userId % 10 + 1}.jpg`
      }
      return '/media/def_avatars/1.jpg'
    }
    
    if (avatarPath.startsWith('http')) return avatarPath
    if (avatarPath.startsWith('/media/')) {
      return `${import.meta.env.VITE_API_BASE_URL || 'https://anisphere.org'}${avatarPath}`
    }
    return `${import.meta.env.VITE_API_BASE_URL || 'https://anisphere.org'}/media/${avatarPath}`
  }

  const getUserInitials = (user: { display_name?: string; username: string }): string => {
    const name = user.display_name || user.username || ''
    return name.charAt(0).toUpperCase()
  }

  const getInitialsFromName = (name: string): string => {
    if (!name) return '?'
    return name.charAt(0).toUpperCase()
  }

  const getInitialsColor = (name: string): string => {
    if (!name || name.length === 0) return '#667eea'
    const colors = [
      '#667eea', '#764ba2', '#f093fb', '#f5576c',
      '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
    ]
    const index = name.charCodeAt(0) % colors.length
    return colors[index]!
  }

  return {
    getAvatarUrl,
    getUserInitials,
    getInitialsFromName,
    getInitialsColor
  }
}