/**
 * Генерация и управление аватарами по умолчанию
 */

export const DEFAULT_AVATAR_COUNT = 10

export function getDefaultAvatarUrl(userId: number): string {
  const avatarIndex = (userId % DEFAULT_AVATAR_COUNT) + 1
  return `/def_ava/avatar_${avatarIndex}.png`
}

export function getDefaultAvatarForUser(userId: number): string {
  return getDefaultAvatarUrl(userId)
}

export function getRandomDefaultAvatarUrl(): string {
  const randomIndex = Math.floor(Math.random() * DEFAULT_AVATAR_COUNT) + 1
  return `/def_ava/avatar_${randomIndex}.png`
}

export function getAvatarIndex(userId: number): number {
  return (userId % DEFAULT_AVATAR_COUNT) + 1
}

export function preloadDefaultAvatars(): void {
  for (let i = 1; i <= DEFAULT_AVATAR_COUNT; i++) {
    const img = new Image()
    img.src = `/def_ava/avatar_${i}.png`
  }
}