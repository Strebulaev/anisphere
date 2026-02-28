/**
 * Утилита для получения аватарки озвучки
 */

/**
 * Нормализует название озвучки для поиска файла
 * @param name - название озвучки
 * @returns нормализованное название для поиска файла
 */
export function normalizeTranslationName(name: string): string {
  if (!name) return ''

  return name
    .toLowerCase()
    .trim()
    .replace(/[а-яё]/g, (char) => {
      // Транслитерация для кириллицы
      const map: Record<string, string> = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
      }
      return map[char] || char
    })
    .replace(/[^a-z0-9]/g, '-') // заменяем всё кроме букв и цифр на дефис
    .replace(/-+/g, '-') // заменяем множественные дефисы на один
    .replace(/^-|-$/g, '') // удаляем дефисы в начале и конце
}

/**
 * Популярные озвучки и их нормализованные названия
 * Используется для кэширования и ускорения поиска
 */
const POPULAR_TRANSLATIONS = new Set([
  'anilibria',
  'studio-band',
  'fanvadub',
  'jamlub',
  'animedub',
  'shiza-project',
  'coldfilm',
  'kansai',
  'ani-dub',
  'ani-lib',
  'zendub',
  'timedub',
  'caramba',
  'jellem',
  'dub',
  'sub',
])

/**
 * Получает URL аватарки для озвучки
 * @param name - название озвучки
 * @returns URL аватарки или undefined, если аватарка не найдена
 */
export function getTranslationAvatarUrl(name: string): string | undefined {
  if (!name) return undefined

  const normalizedName = normalizeTranslationName(name)

  // Список поддерживаемых расширений
  const extensions = ['svg', 'png', 'jpg', 'jpeg', 'webp']

  // Проверяем каждое расширение
  for (const ext of extensions) {
    try {
      // Пытаемся создать URL (ошибка НЕ выбрасывается, если файл не найден в рантайме)
      const url = new URL(`../assets/translation-avatars/${normalizedName}.${ext}`, import.meta.url)
      
      // В Vite/Webpack проверка существования файла происходит на этапе сборки
      // Если файл есть, URL будет валидным, если нет - конструктор НЕ выбрасывает ошибку
      // Поэтому просто возвращаем URL
      return url.href
    } catch (e) {
      // Ошибка может быть только если URL некорректен (например, недопустимые символы)
      console.warn(`[TranslationAvatar] Invalid URL for ${normalizedName}.${ext}:`, e)
      continue
    }
  }

  // Если файл не найден, пробуем популярные альтернативные названия
  const alternativeNames = getAlternativeNames(normalizedName)
  for (const altName of alternativeNames) {
    for (const ext of extensions) {
      try {
        const url = new URL(`../assets/translation-avatars/${altName}.${ext}`, import.meta.url)
        return url.href
      } catch (e) {
        continue
      }
    }
  }

  return undefined
}

/**
 * Получает альтернативные названия для поиска аватарки
 * @param name - нормализованное название
 * @returns список альтернативных названий
 */
function getAlternativeNames(name: string): string[] {
  const alternatives: string[] = [name]

  // Удаляем суффиксы
  const withoutSuffix = name
    .replace(/-dub$/, '')
    .replace(/-team$/, '')
    .replace(/-project$/, '')
    .replace(/-studio$/, '')

  if (withoutSuffix !== name) {
    alternatives.push(withoutSuffix)
  }

  // Удаляем префиксы
  const withoutPrefix = name
    .replace(/^dub-/, '')
    .replace(/^sub-/, '')
    .replace(/^studio-/, '')

  if (withoutPrefix !== name) {
    alternatives.push(withoutPrefix)
  }

  // Добавляем вариант с подчёркиваниями вместо дефисов
  alternatives.push(name.replace(/-/g, '_'))

  // Добавляем вариант без дефисов
  alternatives.push(name.replace(/-/g, ''))

  // Для популярных озвучек добавляем основные варианты
  if (POPULAR_TRANSLATIONS.has(name)) {
    if (name === 'anilibria') {
      alternatives.push('anilibria', 'ani-lib')
    }
    if (name === 'shiza-project') {
      alternatives.push('shiza', 'shiza_project')
    }
    if (name === 'ani-dub') {
      alternatives.push('anidub', 'ani_dub')
    }
  }

  // Убираем дубликаты
  return [...new Set(alternatives)]
}

/**
 * Проверяет, существует ли аватарка для озвучки
 * @param name - название озвучки
 * @returns true, если аватарка существует
 */
export function hasTranslationAvatar(name: string): boolean {
  return getTranslationAvatarUrl(name) !== undefined
}

/**
 * Кэш для хранения уже найденных аватарок
 */
const avatarCache = new Map<string, string>()

/**
 * Получает URL аватарки с кэшированием
 * @param name - название озвучки
 * @returns URL аватарки или undefined
 */
export function getCachedTranslationAvatarUrl(name: string): string | undefined {
  if (!name) return undefined
  
  if (avatarCache.has(name)) {
    return avatarCache.get(name)
  }
  
  const url = getTranslationAvatarUrl(name)
  if (url) {
    avatarCache.set(name, url)
  }
  
  return url
}

/**
 * Предзагружает популярные аватарки для ускорения работы
 */
export function preloadPopularAvatars(): void {
  POPULAR_TRANSLATIONS.forEach(name => {
    getCachedTranslationAvatarUrl(name)
  })
}