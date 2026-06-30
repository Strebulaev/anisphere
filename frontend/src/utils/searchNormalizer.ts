/**
 * Нормализует поисковый запрос для консистентного поиска
 * - Удаляет лишние пробелы
 * - Приводит к нижнему регистру
 * - Удаляет специальные символы
 * - Транслитерирует русский текст в латиницу
 */

const translitMap: Record<string, string> = {
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
  'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
  'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
  'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
  'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
  'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
  'э': 'e', 'ю': 'yu', 'я': 'ya'
}

export function normalizeSearchQuery(query: string): string {
  if (!query) return ''
  
  return query
    .trim()
    .toLowerCase()
    .split('')
    .map(char => translitMap[char] || char)
    .join('')
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ')
}

export function containsCyrillic(text: string): boolean {
  return /[\u0400-\u04FF]/.test(text)
}

export function transliterate(text: string): string {
  return text
    .toLowerCase()
    .split('')
    .map(char => translitMap[char] || char)
    .join('')
}