import { ref, computed, type Ref } from 'vue'
import { getIconName } from '../utils/emojiToIcon'

export interface TextPart {
  type: 'text' | 'emoji'
  content: string
  iconName?: string
  key: string
}

export function useEmojiReplacer(text: Ref<string> | string) {
  const textRef = typeof text === 'string' ? ref(text) : text

  const parts = computed<TextPart[]>(() => {
    const input = textRef.value
    if (!input) return []

    const result: TextPart[] = []
    let currentText = ''
    let keyCounter = 0

    // Регулярное выражение для поиска эмодзи (включая расширенные)
    const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu

    let lastIndex = 0
    let match

    while ((match = emojiRegex.exec(input)) !== null) {
      // Добавляем текст до эмодзи
      if (match.index > lastIndex) {
        const textContent = input.slice(lastIndex, match.index)
        if (textContent) {
          currentText += textContent
        }
      }

      const emoji = match[0]
      const iconName = getIconName(emoji)

      if (currentText) {
        result.push({
          type: 'text',
          content: currentText,
          key: `text-${keyCounter++}`
        })
        currentText = ''
      }

      if (iconName) {
        result.push({
          type: 'emoji',
          content: emoji,
          iconName,
          key: `emoji-${keyCounter++}`
        })
      } else {
        // Если иконка не найдена, оставляем эмодзи как есть
        result.push({
          type: 'text',
          content: emoji,
          key: `text-${keyCounter++}`
        })
      }

      lastIndex = match.index + emoji.length
    }

    // Добавляем оставшийся текст
    if (lastIndex < input.length) {
      currentText += input.slice(lastIndex)
    }

    if (currentText) {
      result.push({
        type: 'text',
        content: currentText,
        key: `text-${keyCounter++}`
      })
    }

    return result
  })

  const hasEmoji = computed(() => {
    return parts.value.some(part => part.type === 'emoji')
  })

  return {
    parts,
    hasEmoji
  }
}

/**
 * Простая функция для проверки, содержит ли текст эмодзи
 */
export function containsEmoji(text: string): boolean {
  const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/u
  return emojiRegex.test(text)
}

/**
 * Функция для удаления всех эмодзи из текста
 */
export function removeEmoji(text: string): string {
  const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu
  return text.replace(emojiRegex, '')
}

/**
 * Функция для замены всех эмодзи на указанную строку
 */
export function replaceEmoji(text: string, replacement: string): string {
  const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu
  return text.replace(emojiRegex, replacement)
}
