import { computed } from 'vue'

/**
 * Генерирует стабильный цвет для ника на основе username
 * Использует HSL для создания приятных цветов
 */
export function useColoredNickname() {
  const stringToColor = (str: string): string => {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    
    const hue = hash % 360
    const saturation = 65 + (hash % 20) 
    const lightness = 45 + (hash % 15)  
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`
  }

  const getColoredNameStyle = (username: string) => {
    return {
      color: stringToColor(username)
    }
  }

  return {
    stringToColor,
    getColoredNameStyle
  }
}