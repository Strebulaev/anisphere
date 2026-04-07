<script setup lang="ts">
import { computed } from 'vue'
import { getIconName } from '@/utils/emojiToIcon'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

const props = withDefaults(defineProps<{
  text: string
  size?: number
  inline?: boolean
}>(), {
  size: 16,
  inline: true
})

// Заменяет эмодзи в тексте на компоненты иконок
const processedContent = computed(() => {
  if (!props.text) return []
  
  const result: Array<{ type: 'text' | 'emoji'; content: string; iconName?: string }> = []
  let currentText = ''
  
  // Регулярное выражение для поиска эмодзи
  const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu
  
  let lastIndex = 0
  let match
  
  while ((match = emojiRegex.exec(props.text)) !== null) {
    // Добавляем текст до эмодзи
    if (match.index > lastIndex) {
      currentText += props.text.slice(lastIndex, match.index)
    }
    
    const emoji = match[0]
    const iconName = getIconName(emoji)
    
    if (currentText) {
      result.push({ type: 'text', content: currentText })
      currentText = ''
    }
    
    if (iconName) {
      result.push({ type: 'emoji', content: emoji, iconName })
    } else {
      // Если иконка не найдена, оставляем эмодзи как есть
      result.push({ type: 'text', content: emoji })
    }
    
    lastIndex = match.index + emoji.length
  }
  
  // Добавляем оставшийся текст
  if (lastIndex < props.text.length) {
    currentText += props.text.slice(lastIndex)
  }
  
  if (currentText) {
    result.push({ type: 'text', content: currentText })
  }
  
  return result
})
</script>

<template>
  <span :class="['emoji-replacer', { 'emoji-inline': inline }]">
    <template v-for="(item, index) in processedContent" :key="index">
      <SakuraIcon
        v-if="item.type === 'emoji' && item.iconName"
        :name="item.iconName"
        :size="size"
      />
      <span v-else>{{ item.content }}</span>
    </template>
  </span>
</template>

<style scoped>
.emoji-replacer {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.emoji-inline {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
