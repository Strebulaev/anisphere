/**
 * Утилита для проверки отсутствующих аватарок озвучек
 * Используется для отладки и создания списка аватарок, которые нужно добавить
 */

import { normalizeTranslationName } from './translationAvatars'

/**
 * Проверяет список озвучек и возвращает те, у которых нет аватарок
 * @param translations - список озвучек
 * @returns список озвучек без аватарок
 */
export function listMissingAvatars(translations: any[]): Array<{ name: string, filename: string }> {
  const missing: Array<{ name: string, filename: string }> = []

  for (const translation of translations) {
    if (!translation.logo) {
      const filename = `${normalizeTranslationName(translation.name)}.png`
      missing.push({
        name: translation.name,
        filename
      })
    }
  }

  return missing
}

/**
 * Генерирует скрипт для создания структуры папок и файлов аватарок
 * @param translations - список озвучек
 * @returns скрипт для создания файлов
 */
export function generateAvatarFilesScript(translations: any[]): string {
  const missing = listMissingAvatars(translations)

  let script = '# Список аватарок для создания\n\n'
  script += 'Поместите следующие файлы в папку `frontend/src/assets/translation-avatars/`:\n\n'

  for (const item of missing) {
    script += `- ${item.filename}  # для озвучки "${item.name}"\n`
  }

  return script
}
