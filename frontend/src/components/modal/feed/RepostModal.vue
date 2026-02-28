<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Поделиться постом</h3>
      
      <p>Выберите чат для репоста:</p>
      
      <div class="modal-chats">
        <div
          v-for="chat in chats"
          :key="chat.id"
          class="chat-item"
          @click="repostTo(chat)"
        >
          <div class="chat-avatar">
            <img v-if="chat.avatar" :src="chat.avatar" />
            <span v-else class="placeholder">{{ chat.name[0] }}</span>
          </div>
          <div class="chat-info">
            <span class="chat-name">{{ chat.name }}</span>
            <span v-if="chat.type === 'group'" class="chat-type">Группа</span>
            <span v-else class="chat-type">Личный</span>
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Chat {
  id: number
  name: string
  avatar?: string
  type: 'group' | 'private'
}

defineProps<{
  show: boolean
  chats: Chat[]
}>()

const emit = defineEmits<{
  close: []
  repost: [chat: Chat]
}>()

const repostTo = (chat: Chat) => {
  emit('repost', chat)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.modal p {
  margin-bottom: 20px;
  color: var(--secondary-text);
}

.modal-chats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.chat-item:hover {
  background: var(--bg-color);
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.chat-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-avatar .placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
}

.chat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-name {
  font-weight: 500;
}

.chat-type {
  font-size: 12px;
  color: var(--secondary-text);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}
</style>
