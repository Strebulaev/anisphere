<template>
  <div v-if="reactions.length > 0" class="message-reactions" :class="{ 'has-many-reactions': uniqueReactions.length > 4 }">
    <div
      v-for="(reaction, index) in uniqueReactions"
      :key="index"
      :class="['reaction-item', 'reaction-badge', { 'user-reacted': hasReacted(reaction.emoji), 'reaction-collapsed': index >= 4 }]"
      @click="toggleReaction(reaction.emoji)"
    >
      <span class="reaction-emoji">{{ reaction.emoji }}</span>
      <span class="reaction-count">{{ reaction.count }}</span>
    </div>

    <button class="add-reaction-btn" @click="showEmojiPicker = !showEmojiPicker" title="Добавить реакцию">
      😊
    </button>

    <div v-if="showEmojiPicker" class="emoji-picker" @click.stop>
      <div
        v-for="emoji in commonEmojis"
        :key="emoji"
        :class="['emoji-option', { 'selected': hasReacted(emoji) }]"
        @click="toggleReaction(emoji)"
      >
        {{ emoji }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useAuthStore } from '@/stores/auth'

interface Props {
  messageId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'reaction-toggled', data: { reacted: boolean; emoji: string }): void
}>()

const chatExtrasStore = useChatExtrasStore()
const authStore = useAuthStore()

const showEmojiPicker = ref(false)

const commonEmojis = [
  '❤️', '👍', '👎', '😂', '😮', '😢', '😡', '🔥', '🎉', '👏',
  '🤔', '😍', '🥳', '😎', '🤗', '😱', '🙏', '💯', '✨', '💪'
]

const reactions = computed(() => {
  return chatExtrasStore.getReactionsForMessage(props.messageId)
})

const uniqueReactions = computed(() => {
  const emojiMap = new Map<string, { emoji: string; count: number }>()
  reactions.value.forEach((reaction) => {
    const existing = emojiMap.get(reaction.emoji)
    if (existing) {
      existing.count++
    } else {
      emojiMap.set(reaction.emoji, { emoji: reaction.emoji, count: 1 })
    }
  })
  return Array.from(emojiMap.values())
})

const hasReacted = (emoji: string) => {
  return chatExtrasStore.hasUserReacted(
    props.messageId,
    emoji,
    authStore.user?.id || 0
  )
}

const toggleReaction = async (emoji: string) => {
  try {
    const result = await chatExtrasStore.toggleReaction(props.messageId, emoji)
    showEmojiPicker.value = false
    emit('reaction-toggled', result)
  } catch (error) {
    console.error('Error toggling reaction:', error)
  }
}

onMounted(() => {
  chatExtrasStore.loadMessageReactions(props.messageId)
})

document.addEventListener('click', () => {
  showEmojiPicker.value = false
})
</script>

<style scoped>
.message-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.5rem;
  position: relative;
}

.reaction-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.reaction-item:hover {
  background: var(--color-background-active);
  transform: translateY(-1px);
}

.reaction-item.user-reacted {
  background: rgba(58, 134, 255, 0.1);
  border-color: rgba(58, 134, 255, 0.3);
}

.reaction-emoji {
  font-size: 1rem;
}

.reaction-count {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.add-reaction-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.add-reaction-btn:hover {
  background: var(--color-background-active);
  transform: scale(1.1);
}

.emoji-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.25rem;
  padding: 0.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider);
  border-radius: 0.75rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  margin-bottom: 0.5rem;
}

.emoji-option {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.25rem;
}

.emoji-option:hover {
  background: var(--color-background-active);
  transform: scale(1.1);
}

.emoji-option.selected {
  background: rgba(58, 134, 255, 0.1);
}
</style>
