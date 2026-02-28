// Composable для работы с аватарками пользователей
export function useAvatar() {
  // Получить полный URL аватарки
  const getAvatarUrl = (avatarPath: string | null | undefined): string => {
    if (!avatarPath) return ''
    if (avatarPath.startsWith('http')) return avatarPath
    if (avatarPath.startsWith('/media/')) {
      return `${import.meta.env.VITE_API_BASE_URL || 'https://anisphere.ru'}${avatarPath}`
    }
    return `${import.meta.env.VITE_API_BASE_URL || 'https://anisphere.ru'}/media/${avatarPath}`
  }

  // Получить инициалы пользователя для placeholder
  const getUserInitials = (user: { display_name?: string; username: string }): string => {
    const name = user.display_name || user.username || ''
    return name.charAt(0).toUpperCase()
  }

  // Получить инициалы по имени
  const getInitialsFromName = (name: string): string => {
    if (!name) return '?'
    return name.charAt(0).toUpperCase()
  }

  // Получить цвет для инициалов (простой хэш имени)
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