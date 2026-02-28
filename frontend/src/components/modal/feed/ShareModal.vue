<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Поделиться</h3>
      
      <div class="modal-share-options">
        <button class="share-option" @click="shareTo('telegram')">
          <span class="icon">📱</span>
          <span>Telegram</span>
        </button>
        <button class="share-option" @click="shareTo('vk')">
          <span class="icon">🔵</span>
          <span>VK</span>
        </button>
        <button class="share-option" @click="shareTo('whatsapp')">
          <span class="icon">💬</span>
          <span>WhatsApp</span>
        </button>
        <button class="share-option" @click="shareTo('twitter')">
          <span class="icon">🐦</span>
          <span>Twitter</span>
        </button>
        <button class="share-option" @click="copyLink">
          <span class="icon">🔗</span>
          <span>Скопировать ссылку</span>
        </button>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  close: []
  share: [platform: string]
  copyLink: []
}>()

const shareTo = (platform: string) => {
  emit('share', platform)
}

const copyLink = () => {
  emit('copyLink')
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
  max-width: 350px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}

.modal-share-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.share-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px;
  border: 1px solid var(--border-color);
  background: var(--bg-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.share-option:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.share-option .icon {
  font-size: 24px;
}

.share-option span {
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}
</style>
