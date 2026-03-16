<template>
  <ChatSettingsModalNew
    v-if="isOpen"
    :chat-id="chatId"
    :chat-type="isGroup ? 'group' : 'private'"
    :is-owner="isOwner"
    @close="$emit('close')"
    @settings-changed="$emit('updated')"
  />
</template>

<script setup lang="ts">
import ChatSettingsModalNew from '@/components/Chats/ChatSettingsModal.vue'

interface Props {
  isOpen: boolean
  chatId: number
  isGroup: boolean
  isOwner?: boolean
}

defineProps<Props>()
defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()
</script>
